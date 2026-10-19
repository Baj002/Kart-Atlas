#!/usr/bin/env python3
"""Respectfully monitor organizer calendars; auto-import only allowlisted official ICS events.

No bypasses, headless scraping, paid APIs or undocumented platform endpoints.
Pages/PDFs without a verified parser are WATCH ONLY, and generate review signals.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,html,json,re,sys,time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT=Path(__file__).resolve().parents[1]
AGENT='KartAtlasPublicCalendar/0.2 (public race directory; no paywall bypass)'
LIMIT=2_000_000
START_WINDOW_DAYS=550
RACE_TERMS=re.compile(r'\b(race|races|championship|cup|grand prix|enduro|endurance|national|regional|carrera|campeonato|copa|course|courses|championnat|coupe|manche|supernats|supercup|grand finals|kartweek|prix|challenge|supernationals)\b',re.I)
EXCLUDED=re.compile(r'(arrive[ -]?(?:and|&|n)[ -]?drive|a/d\b|mini indy|lap(?:ping)?\b|practice|training|test\s*&\s*tune|track closed|private event|birthday|meeting|banquet|maintenance|school|academy|esports?|simulator|iracing|virtual|rentals?|party|corporate)',re.I)

class PageText(HTMLParser):
    def __init__(self): super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript','svg'):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript','svg') and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip and data.strip():self.parts.append(data.strip())

def visible_text(data):
    parser=PageText();parser.feed(data);return ' '.join(' '.join(parser.parts).split())[:100000]

def unfold_ics(ics):
    return re.sub(r'\r?\n[ \t]', '', ics.replace('\r\n','\n'))

def unescape_ics(v):
    return v.replace('\\n',' ').replace('\\N',' ').replace('\\,',',').replace('\\;',';').replace('\\\\','\\').strip()

def parse_ics(raw):
    events=[];current=None
    for line in unfold_ics(raw).split('\n'):
        if line.strip()=='BEGIN:VEVENT':current={}
        elif line.strip()=='END:VEVENT':
            if current is not None:events.append(current)
            current=None
        elif current is not None and ':' in line:
            original_key,value=line.split(':',1);key=original_key.upper()
            # Preserve VALUE=DATE on DTSTART/DTEND to distinguish exclusive all-day end.
            item=key.split(';',1)[0]
            if item in ('SUMMARY','UID','DESCRIPTION','LOCATION','URL','STATUS','DTSTART','DTEND','RRULE','RECURRENCE-ID'):
                current[item]=unescape_ics(value)
                if item in ('DTSTART','DTEND'):
                    current[item+'_IS_DATE']='VALUE=DATE' in key
                    tz=re.search(r'TZID=([^;:]+)',key,re.I)
                    if tz:current[item+'_TZID']=re.search(r'TZID=([^;:]+)',original_key,re.I).group(1)
    return events

def ics_date(raw,field,source):
    value=raw[field]
    if value.endswith('Z') and source.get('timezone'):
        moment=dt.datetime.strptime(value,'%Y%m%dT%H%M%SZ').replace(tzinfo=dt.timezone.utc)
        return moment.astimezone(ZoneInfo(source['timezone'])).date()
    return dt.datetime.strptime(value[:8],'%Y%m%d').date()

def normalized_ics(ics,source,today=None,include_cancelled=False):
    today=today or dt.date.today()
    results=[]
    for raw in parse_ics(ics):
        name=html.unescape(raw.get('SUMMARY','')).strip()
        if not name or not RACE_TERMS.search(name) or EXCLUDED.search(name):continue
        if (raw.get('STATUS','').upper()=='CANCELLED' and not include_cancelled) or raw.get('RRULE') or raw.get('RECURRENCE-ID'):continue
        if re.search(r'instructor.led lapping',raw.get('DESCRIPTION',''),re.I):continue
        if not re.match(r'^\d{8}',raw.get('DTSTART','')):continue
        try:
            start=ics_date(raw,'DTSTART',source)
            end=start
            endstr=raw.get('DTEND','')
            if re.match(r'^\d{8}',endstr):
                end=ics_date(raw,'DTEND',source)
                if raw.get('DTEND_IS_DATE') or len(endstr)==8:end-=dt.timedelta(days=1)
                if end<start:end=start
        except ValueError:continue
        if end<today or start>today+dt.timedelta(days=START_WINDOW_DAYS) or (end-start).days>12:continue
        uid=raw.get('UID') or f'{start.isoformat()}|{name}'
        token=f"{source['id']}|{uid}"
        link=raw.get('URL','')
        if not link.startswith(('https://','http://')):link=source['url'].split('?')[0]
        results.append({'id':'auto-'+hashlib.sha1(token.encode()).hexdigest()[:12],
           'uid':uid,'feed_id':source['id'],'start':start.isoformat(),'end':end.isoformat(),
           'name':name[:180],'organizer':source['club'],'venue':source.get('venue',''),
           'city':source.get('city',''),'region':source.get('region',''),'country':source.get('country',''),
           'level':source.get('level','Club'),'format':'Endurance' if re.search('endur',name,re.I) else 'Sprint','verification':'Automated',
           'status':'cancelled' if raw.get('STATUS','').upper()=='CANCELLED' else 'scheduled',
           'status_explicit':raw.get('STATUS','').upper() in ('CANCELLED','CONFIRMED'),
           'timezone_needs_review':raw.get('DTSTART','').endswith('Z') and not bool(source.get('timezone')),
           'classes':'','source':link,'notes':'Imported from organizer calendar feed; check official rules, classes and date before travel.'})
    return results

def is_allowed_by_robots(url,cache):
    u=urlsplit(url);host=f'{u.scheme}://{u.netloc}'
    if host not in cache:
        rp=RobotFileParser()
        rp.set_url(host+'/robots.txt')
        try:
            request=Request(host+'/robots.txt',headers={'User-Agent':AGENT})
            with urlopen(request,timeout=10) as r:
                data=r.read(200000).decode('utf-8','replace')
            rp.parse(data.splitlines());cache[host]=rp
        except HTTPError as e:
            # Missing robots file => no robots rules. Other responses => fail closed.
            cache[host]=(True if e.code in (404,410) else False)
        except (URLError,TimeoutError,OSError):
            cache[host]=False
    rule=cache[host]
    return rule.can_fetch(AGENT,url) if isinstance(rule,RobotFileParser) else bool(rule)

def fetch(url):
    req=Request(url,headers={'User-Agent':AGENT,'Accept':'text/calendar,text/html;q=0.9,*/*;q=0.5'})
    with urlopen(req,timeout=16) as result:
        response=result.read(LIMIT+1)
        if len(response)>LIMIT:raise ValueError('Response exceeds 2 MB safe limit')
        enc=result.headers.get_content_charset() or 'utf-8'
    return response.decode(enc,'replace')

def run(root=ROOT,fetcher=fetch,robots_checker=None,clock=None):
    now=clock or dt.datetime.now(dt.timezone.utc)
    today=now.date()
    sources=json.loads((root/'data/monitor_sources.json').read_text())['sources']
    state=json.loads((root/'data/source_state.json').read_text())
    stored=state.setdefault('sources',{})
    auto=json.loads((root/'data/automated_events.json').read_text())
    existing={e['id']:e for e in auto.setdefault('events',[])}
    report={'last_run':now.isoformat(timespec='seconds'),'successful':0,'attempted':len(sources),'watch_changes':[],'new_races':[],'possible_date_changes':[],'errors':[],'baseline_sources':[]}
    robotcache={}
    for item in sources:
        ident=item['id']
        old=stored.get(ident,{})
        try:
            if robots_checker is not None:
                allowed=robots_checker(item['url'])
            elif fetcher is fetch:
                allowed=is_allowed_by_robots(item['url'],robotcache)
            else:
                allowed=True  # Fixtures/tests don't need network robots lookups.
            if not allowed:
                raise ValueError('robots.txt disallows or could not verify automated retrieval')
            raw=fetcher(item['url'])
            if item['mode']=='ics':
                if 'BEGIN:VCALENDAR' not in raw or 'BEGIN:VEVENT' not in raw:
                    raise ValueError('Calendar feed empty/invalid; no updates applied')
                extracted=normalized_ics(raw,item,today)
                canonical='\n'.join(sorted(f"{e['uid']}|{e['start']}|{e['end']}|{e['name']}" for e in extracted))
            else:
                canonical=visible_text(raw)
                if len(canonical)<80:raise ValueError('Page contains too little usable schedule text')
                extracted=[]
            digest=hashlib.sha256(canonical.encode()).hexdigest()
            previous=old.get('digest')
            if previous is None:report['baseline_sources'].append(ident)
            elif previous != digest:report['watch_changes'].append({'source_id':ident,'club':item['club'],'url':item['url'],'note':'Organizer page/feed changed. Review dates; generic HTML changes are not automatically interpreted as races.'})
            stored[ident]={'digest':digest,'url':item['url'],'mode':item['mode'],'last_success':now.isoformat(timespec='seconds'),'last_error':None}
            report['successful']+=1
            if item.get('auto_import'):
                for e in extracted:
                    previous_e=existing.get(e['id'])
                    if previous_e is None:
                        existing[e['id']]=e
                        report['new_races'].append({'name':e['name'],'date':e['start'],'club':item['club'],'source':e['source']})
                    elif (previous_e['start'],previous_e['end'],previous_e['name'])!=(e['start'],e['end'],e['name']):
                        # Preserve original published entry until changed date is reviewed.
                        report['possible_date_changes'].append({'name':e['name'],'original_start':previous_e['start'],'new_start':e['start'],'source':e['source']})
            print(f"OK {ident}: {len(extracted)} race candidates")
        except (HTTPError,URLError,TimeoutError,OSError,ValueError,UnicodeError) as exc:
            error=f'{type(exc).__name__}: {str(exc)[:180]}'
            report['errors'].append({'source_id':ident,'url':item['url'],'error':error})
            print(f'WARN {ident}: {error}',file=sys.stderr)
            # Preserve previous successful digest and events on failure. Don't treat failure as cancellation.
            if old:stored[ident]=old
    auto['events']=sorted(existing.values(),key=lambda x:(x['start'],x['name']))
    auto['updated']=now.isoformat(timespec='seconds') if report['new_races'] else auto.get('updated')
    (root/'data/source_state.json').write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n')
    (root/'data/automated_events.json').write_text(json.dumps(auto,indent=2,ensure_ascii=False)+'\n')
    (root/'reports/latest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    (root/'site/monitor_status.json').write_text(json.dumps({'last_attempt':report['last_run'],'checked':report['successful'],'total':report['attempted'],'feed_additions':len(report['new_races']),'errors':len(report['errors']),'is_complete':False},indent=2)+'\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default=str(ROOT))
    a=p.parse_args()
    summary=run(Path(a.root))
    print(f"Monitored {summary['successful']}/{summary['attempted']} sources. New events {len(summary['new_races'])}, manual review changes {len(summary['watch_changes'])}, errors {len(summary['errors'])}")
