"""Bounded public-source discovery and provenance-aware event reconciliation.

Only configured organizer sources publish automatically. Directory/link discoveries
are scanned, but stay in a review queue until their ownership and location are verified.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import html
import ipaddress
import json
import re
import socket
import unicodedata
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from http.client import HTTPException
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener, getproxies
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from scripts.schedule_tables import row_event
from scripts.check_sources import AGENT, LIMIT, CANCEL_TERMS, RACE_TERMS, EXCLUDED, normalized_ics, visible_text, ROOT

COUNTRIES={'CA':'Canada','CANADA':'Canada','US':'USA','USA':'USA','UNITED STATES':'USA','UNITED STATES OF AMERICA':'USA','MX':'Mexico','MEXICO':'Mexico','MÉXICO':'Mexico'}
REGIONS=json.loads((ROOT/'data/regions.json').read_text())

def region_code(value,country):
    def folded(text):
        text=unicodedata.normalize('NFKD',str(text)).encode('ascii','ignore').decode().casefold()
        return re.sub(r'[^a-z0-9]','',text)
    text=str(value).strip();key=folded(text)
    aliases={'Mexico':{'mexicostate':'MEX','stateofmexico':'MEX','cdmx':'CMX','distritofederal':'CMX','ciudaddemexico':'CMX'},
        'Canada':{'colombiebritannique':'BC','nouveaubrunswick':'NB','nouvelleecosse':'NS','ileduprinceedouard':'PE','terreneuveetlabrador':'NL'}}
    if key in aliases.get(country,{}):return aliases[country][key]
    for code,name in REGIONS.get(country,{}).items():
        if key in (folded(code),folded(name)):return code
    return text

RACING=re.compile(RACE_TERMS.pattern+r'|\b(carrera|campeonato|copa|course|courses|championnat|coupe|manche|enduro)\b',re.I)
OMIT=re.compile(EXCLUDED.pattern+r'|\b(pratique|entraînement|entrenamiento|práctica|academy|esports?|simulator|iracing|virtual|swap meet|trade show)\b',re.I)
CALENDAR=re.compile(r'calendar|schedule|events?|racing|calendrier|calendario|eventos|carreras|championnat',re.I)
BAD_HOSTS={'facebook.com','instagram.com','youtube.com','twitter.com','x.com','google.com','google.ca','squarespace.com','wix.com','amazon.com','paypal.com'}

def host(url):
    return (urlsplit(url).hostname or '').lower().removeprefix('www.')

def clean_url(url, base=''):
    try:
        u=urlsplit(urljoin(base,str(url)))
        if u.scheme not in ('https','http') or not u.hostname or u.username or u.password or u.port not in (None,80,443):return ''
        h=u.hostname.lower()
        if '.' not in h or h.endswith(('.local','.internal','.localhost')):return ''
        try:
            if not ipaddress.ip_address(h).is_global:return ''
        except ValueError:pass
        return urlunsplit((u.scheme,u.netloc.lower(),u.path or '/',u.query,''))
    except (ValueError,TypeError):return ''

def feed_url(url):
    u=urlsplit(url);q=parse_qs(u.query.lower())
    return u.path.lower().endswith('.ics') or q.get('ical')==['1'] or q.get('format')==['ical'] or q.get('ical')==['true']

def dump(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temp.replace(path)

class PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        newurl=clean_url(newurl,req.full_url)
        if not newurl or host(newurl)!=host(req.full_url):raise ValueError('Cross-domain redirect requires source review')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class PublicClient:
    """One request at a time per host, robots enforcement, bounded size/time/redirects."""
    def __init__(self,delay=.5):
        self.delay=delay;self.locks={};self.guard=threading.Lock();self.robots={};self.last={};self.cache={}
    def _read(self,url,limit=LIMIT):
        # Reject private destinations even when a publicly named lead resolves internally.
        # Managed HTTP proxies resolve remote names themselves. In direct mode,
        # also reject private DNS resolutions; literal private IPs are always rejected.
        if not getproxies().get(urlsplit(url).scheme):
            for result in socket.getaddrinfo(urlsplit(url).hostname,None):
                if not ipaddress.ip_address(result[4][0]).is_global:raise ValueError('Non-public network destination')
        req=Request(url,headers={'User-Agent':AGENT,'Accept':'text/calendar,application/ld+json,text/html;q=0.9'})
        with build_opener(PublicRedirect()).open(req,timeout=12) as r:
            content=r.read(limit+1)
            if len(content)>limit:raise ValueError('Response exceeds size limit')
            kind=r.headers.get_content_type()
            if kind not in ('text/html','text/calendar','text/plain','application/json','application/ld+json','application/octet-stream'):
                raise ValueError('Unsupported content type: '+kind)
            return content.decode(r.headers.get_content_charset() or 'utf-8','replace')
    def __call__(self,url):
        url=clean_url(url)
        if not url:raise ValueError('Invalid public URL')
        origin='{0.scheme}://{0.netloc}'.format(urlsplit(url))
        with self.guard:lock=self.locks.setdefault(host(url),threading.Lock())
        with lock:
            if url in self.cache:return self.cache[url]
            if origin not in self.robots:
                try:
                    rp=RobotFileParser();rp.parse(self._read(origin+'/robots.txt',200000).splitlines());self.robots[origin]=rp
                except HTTPError as exc:
                    if exc.code not in (404,410):raise
                    self.robots[origin]=True
            rule=self.robots[origin]
            if rule is not True and not rule.can_fetch(AGENT,url):raise ValueError('robots.txt disallows retrieval')
            delay=self.delay if rule is True else max(self.delay,rule.crawl_delay(AGENT) or 0)
            if delay>120:raise ValueError('robots crawl-delay exceeds scan budget')
            time.sleep(max(0,delay-(time.monotonic()-self.last.get(host(url),0))))
            try:raw=self._read(url)
            finally:self.last[host(url)]=time.monotonic()
            self.cache[url]=raw
            return raw

class Parser(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.events=[];self.jsonld=None;self.anchor=None;self.card=None;self.card_depth=0;self.title=False;self.title_text='';self.heading=None;self.schedule_year=None;self.table_year=None;self.table=False;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);classes=a.get('class','').split()
        if tag=='title':self.title=True
        if tag in ('h1','h2','h3'):self.heading=[]
        if tag=='table':self.table=True;self.table_year=self.schedule_year
        if self.table and tag=='tr':self.row=[]
        if self.row is not None and tag in ('td','th'):self.cell=[]
        if tag=='script' and 'ld+json' in a.get('type','').lower():self.jsonld=[]
        if tag=='article' and 'eventlist-event' in classes:
            self.card={'@type':'Event','_parser':'squarespace','_links':[]};self.card_depth=1
        elif self.card is not None and tag=='article':self.card_depth+=1
        if self.card is not None:
            if tag=='a' and 'eventlist-title-link' in classes:
                self.card['url']=a.get('href','');self.card['_name']=True;self.card['name']=''
            if tag=='time' and a.get('datetime'):
                if 'startDate' not in self.card:self.card['startDate']=a['datetime']
                if 'event-time-localized-end' in classes or 'event-date-end' in classes:self.card['endDate']=a['datetime']
        if tag in ('a','link') and a.get('href'):
            link={'url':a['href'],'label':'','type':a.get('type',''),'rel':a.get('rel','')}
            self.links.append(link)
            if tag=='a':self.anchor=link
            if self.card is not None:self.card['_links'].append(link)
    def handle_data(self,data):
        if self.title:self.title_text+=data
        if self.heading is not None:self.heading.append(data)
        if self.cell is not None:self.cell.append(data)
        if self.jsonld is not None:self.jsonld.append(data)
        if self.anchor is not None:self.anchor['label']+=data
        if self.card is not None and self.card.get('_name'):self.card['name']+=data
    def handle_endtag(self,tag):
        if tag=='title':self.title=False
        if tag in ('h1','h2','h3') and self.heading is not None:
            heading=''.join(self.heading);years=re.findall(r'\b(20\d{2})\b',heading)
            if len(set(years))==1 and CALENDAR.search(heading):self.schedule_year=int(years[0])
            self.heading=None
        if tag in ('td','th') and self.cell is not None:
            self.row.append(''.join(self.cell));self.cell=None
        if tag=='tr' and self.row is not None:
            event=row_event(self.row,self.table_year)
            if event:self.events.append(event)
            self.row=None
        if tag=='table':self.table=False
        if tag=='script' and self.jsonld is not None:
            try:self.collect(json.loads(''.join(self.jsonld)))
            except (ValueError,TypeError,RecursionError):pass
            self.jsonld=None
        if tag=='a':
            self.anchor=None
            if self.card is not None:self.card['_name']=False
        if tag=='article' and self.card is not None:
            self.card_depth-=1
            if self.card_depth==0:self.events.append(self.card);self.card=None
    def collect(self,obj,depth=0):
        if depth>30:return
        if isinstance(obj,list):
            for v in obj:self.collect(v,depth+1)
        elif isinstance(obj,dict):
            types=obj.get('@type',[])
            if isinstance(types,str):types=[types]
            if not isinstance(types,list):types=[]
            if any(str(t).rsplit('/',1)[-1] in ('Event','SportsEvent') for t in types):self.events.append(obj)
            for v in obj.values():
                if isinstance(v,(dict,list)):self.collect(v,depth+1)

def normalize_event(e, source, today):
    if not isinstance(e.get('name'),str):return None
    name=html.unescape(e['name']).strip()
    if not name or not RACING.search(name) or OMIT.search(name):return None
    if any(re.search(r'\b'+re.escape(term)+r'\b',name,re.I) for term in source.get('excluded_series',[])):return None
    try:
        start=dt.date.fromisoformat(str(e.get('startDate',''))[:10]);end=dt.date.fromisoformat(str(e.get('endDate') or start)[:10])
    except ValueError:return None
    if end<start or (end-start).days>12 or end<today or start>today+dt.timedelta(days=550):return None
    status=str(e.get('eventStatus','')).rsplit('/',1)[-1]
    if CANCEL_TERMS.search(name):state='cancelled';status='EventCancelled'
    elif status=='EventPostponed':state='postponed'
    elif status=='EventCancelled':state='cancelled'
    elif status in ('','EventScheduled','EventRescheduled'):state='scheduled'
    else:return None
    fallback=source if source.get('trusted',True) else {}
    location=e.get('location') or {}
    if isinstance(location,list):location=location[0] if location else {}
    if not isinstance(location,dict):location={'name':str(location)}
    address=location.get('address') or {}
    if not isinstance(address,dict):address={}
    country=address.get('addressCountry') or fallback.get('country','')
    if isinstance(country,dict):country=country.get('name','')
    country=COUNTRIES.get(str(country).upper(),'')
    link=clean_url(e.get('url') or e.get('@id') or '',source['url']) or source['url']
    identity_name=CANCEL_TERMS.sub('',name).strip(' -–—:').casefold()
    uid=str(e.get('@id') or e.get('url') or (source['url']+'#'+identity_name))
    if not e.get('@id') and not e.get('url') and re.fullmatch(r'(?:club |championship )?race(?: day)?',name,re.I):uid+='|'+str(start)
    record={'name':name[:180],'start':str(start),'end':str(end),'organizer':source['club'],
        'venue':str(location.get('name') or fallback.get('venue',''))[:180],
        'city':str(address.get('addressLocality') or fallback.get('city','')),
        'region':region_code(address.get('addressRegion') or fallback.get('region',''),country),'country':country,
        'source':link,'uid':uid,'feed_id':source['id'],'status':state,'status_explicit':bool(status),
        'format':'Endurance' if re.search('endur',name,re.I) else 'Sprint',
        'level':source.get('level','Club'),'verification':'Automated','classes':'',
        'notes':'Imported from structured organizer data. Confirm rules and registration with the organizer.',
        'discovered_from':source['url'],'parser':e.get('_parser','jsonld'),'location_needs_review':bool(e.get('_location_ambiguous'))}
    for a in e.get('_links',[]):
        if re.search(r'\bregistration|register|inscription|inscripci',a['label'],re.I):
            url=clean_url(a['url'],source['url'])
            if url:record['registration_url']=url;break
    return record

def extract_page(raw,source,today):
    p=Parser();p.feed(raw)
    events=[r for e in p.events if (r:=normalize_event(e,source,today))] if not re.search(r'esports?|iracing|simracing',source['url'],re.I) else []
    links=[];feeds=[];leads=[];documents=[]
    for a in p.links:
        url=clean_url(a['url'],source['url'])
        if not url:continue
        if host(url)==host(source['url']):
            if feed_url(url) or a['type']=='text/calendar':feeds.append(url)
            elif urlsplit(url).path.lower().endswith('.pdf'):documents.append(url)
            elif not re.search(r'/feed/?$|\.rss$',urlsplit(url).path,re.I) and CALENDAR.search(urlsplit(url).path+' '+a['label']) and not re.search(r'\.(jpg|png|css|js|zip)$',urlsplit(url).path,re.I):links.append(url)
        elif source.get('directory') and re.search(r'kart|raceway|speedway|motorplex',a['label']+' '+host(url),re.I):
            if not any(host(url)==h or host(url).endswith('.'+h) for h in BAD_HOSTS):
                leads.append({'url':url,'club':a['label'].strip()[:180] or host(url),'found_on':source['url'],
                    'country':source.get('country',''),'status':'unverified_organizer_source'})
    return {'events':events,'feeds':list(dict.fromkeys(feeds)),'links':list(dict.fromkeys(links)),
            'leads':leads,'documents':list(dict.fromkeys(documents)),'title':p.title_text.strip()}

def event_reference(event):
    url=clean_url(event.get('source',''))
    path=urlsplit(url).path.rstrip('/')
    tail=path.rsplit('/',1)[-1].lower()
    if ('/events/' in path or '/event/' in path or event.get('parser')=='squarespace') and tail not in ('list','events','calendar','schedule') and not tail.endswith('.ics'):
        return urlunsplit(('https',host(url),path,'',''))
    return ''

def identity(event):
    uid=event_reference(event) or event.get('uid') or event.get('source') or event['name'].casefold()
    return 'auto-'+hashlib.sha256((host(event.get('discovered_from') or event['source'])+'|'+uid).encode()).hexdigest()[:16]

def reconcile(stored, observations, now):
    """Explicit changes update stable IDs; missing events/fetch failures never cancel races."""
    existing={};canonical_ids={};changes=[]
    for record in stored:
        canonical=identity(record)
        if canonical in canonical_ids:continue
        existing[record['id']]=dict(record);canonical_ids[canonical]=record['id']
    # Multiple representations of one event can disagree (a listing card may
    # remain after a feed cancellation). Prefer explicit non-scheduled status.
    unique={}
    for observation in observations:
        ident=identity(observation)
        if ident not in unique or observation.get('status') in ('cancelled','postponed'):
            unique[ident]=dict(unique.get(ident,{}),**observation)
        else:
            for field in ('registration_url','rules_url','schedule_url','track_map_url'):
                if observation.get(field):unique[ident].setdefault(field,observation[field])
    for event in unique.values():
        e=dict(event);e['id']=identity(e)
        old=existing.get(e['id']) or existing.get(canonical_ids.get(identity(e)))
        if old:e['id']=old['id']
        if old is None:
            old=next((v for v in existing.values() if v.get('uid')==e.get('uid') and v.get('feed_id')==e.get('feed_id')),None)
            if old:e['id']=old['id']
        if not old and e.get('status') in ('cancelled','postponed'):continue
        e['first_seen']=old.get('first_seen',now) if old else now
        e['last_seen']=now;e['last_verified']=now
        if old:
            for field in ('registration_url','rules_url','schedule_url','track_map_url'):
                if not e.get(field) and old.get(field):e[field]=old[field]
            if old.get('status') in ('cancelled','postponed') and e.get('status')=='scheduled' and not e.get('status_explicit'):
                e['status']=old['status']
            fields=('start','end','name','venue','city','region','country','status','registration_url')
            delta={f:{'before':old.get(f),'after':e.get(f)} for f in fields if old.get(f)!=e.get(f)}
            if delta:
                change={'id':e['id'],'name':e['name'],'source':e['source'],'at':now,'fields':delta}
                changes.append(change);e['history']=(old.get('history',[])+[change])[-20:]
            elif old.get('history'):e['history']=old['history']
        else:changes.append({'id':e['id'],'name':e['name'],'source':e['source'],'at':now,'new':True})
        existing[e['id']]=e;canonical_ids[identity(e)]=e['id']
    return sorted(existing.values(),key=lambda e:(e['start'],e['name'])),changes

def scan_source(source,fetcher,today,max_pages=5):
    queue=[source['url']];seen=set();events=[];leads=[];feeds=[];errors=[];documents=[];pages=[]
    # Roots first, then feeds and calendar/detail links. Strict page budget per source.
    while queue and len(seen)<max_pages:
        url=queue.pop(0)
        if url in seen:continue
        seen.add(url);local=dict(source,url=url)
        try:
            raw=fetcher(url)
            if 'BEGIN:VCALENDAR' in raw[:500]:
                if 'END:VCALENDAR' not in raw:raise ValueError('Truncated calendar')
                extracted=normalized_ics(raw,local,today,include_cancelled=True)
                extracted=[e for e in extracted if not any(re.search(r'\b'+re.escape(term)+r'\b',e['name'],re.I) for term in source.get('excluded_series',[]))]
                for e in extracted:
                    e.update(discovered_from=url,parser='ics')
                    if not clean_url(e['source']):e['source']=url
                events.extend(extracted);pages.append({'url':url,'parser':'ics','events':len(extracted),'digest':hashlib.sha256(raw.encode()).hexdigest()})
            else:
                result=extract_page(raw,local,today)
                if re.search(r'^(just a moment|one moment, please|access denied|attention required)',result['title'],re.I):raise ValueError('Access challenge page; no usable schedule data')
                if not result['events'] and len(visible_text(raw))<80:raise ValueError('Page contains too little usable text')
                events.extend(result['events']);leads.extend(result['leads']);documents.extend(result['documents'])
                pages.append({'url':url,'parser':'html','events':len(result['events']),'digest':hashlib.sha256(visible_text(raw).encode()).hexdigest()})
                feeds.extend(result['feeds'])
                # Feed links for race-named paths first; avoid using the budget on meetings.
                candidates=sorted(result['feeds'],key=lambda u:0 if RACING.search(urlsplit(u).path.replace('-',' ')) else 1)
                queue.extend(u for u in candidates+result['links'] if u not in seen and u not in queue)
        except (OSError,ValueError,UnicodeError,HTTPException) as exc:errors.append({'url':url,'error':f'{type(exc).__name__}: {exc}'[:240]})
    print(f"Scan {source['id']}: {len(pages)}/{len(seen)} pages, {len(events)} race observations, {len(errors)} errors",flush=True)
    return {'source_id':source['id'],'club':source['club'],'url':source['url'],'trusted':bool(source.get('trusted')),
        'country':source.get('country',''),'region':source.get('region',''),'attempted':len(seen),
        'pages':pages,'events':events,'leads':leads,'feeds':list(dict.fromkeys(feeds)),
        'documents':list(dict.fromkeys(documents)),'errors':errors,'remaining_links':len(set(queue)-seen)}

def run(root=ROOT,fetcher=None,today=None,workers=6):
    today=today or dt.datetime.now(dt.timezone.utc).date();now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    config=json.loads((root/'data/monitor_sources.json').read_text())
    sources=[dict(s,trusted=True) for s in config['sources'] if not urlsplit(s['url']).path.lower().endswith('.pdf')]
    extras=root/'data/discovery_sources.json'
    settings=json.loads(extras.read_text()) if extras.exists() else {}
    sources.extend(settings.get('sources',[]))
    known={clean_url(s['url']) for s in sources};known_hosts={host(s['url']) for s in sources if s.get('trusted')}
    directory=json.loads((root/'data/clubs.json').read_text()).get('clubs',[])
    for c in directory:
        url=clean_url(c.get('schedule_url',''))
        if not url or url in known:continue
        known.add(url)
        sources.append({'id':'lead-'+c['id'],'club':c['name'],'url':url,'venue':c.get('venue',''),
            'city':c.get('city',''),'region':c.get('region',''),'country':c.get('country',''),
            'trusted':False,'directory':host(url)=='forums.kartpulse.com'})
    leads_path=root/'data/discovered_sources.json'
    prior=json.loads(leads_path.read_text()).get('sources',[]) if leads_path.exists() else []
    # Rotation prevents a large lead inventory from starving later entries.
    ordered=sorted(prior,key=lambda x:(x.get('last_checked',''),x['url']))
    for lead in ordered[:settings.get('lead_scan_limit',40)]:
        url=clean_url(lead['url'])
        if not url or url in known:continue
        known.add(url);sources.append(dict(lead,id='found-'+hashlib.sha1(url.encode()).hexdigest()[:12],trusted=False))
    client=fetcher or PublicClient()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results=list(pool.map(lambda s:scan_source(s,client,today,settings.get('max_pages_per_source',5)),sources))
    observations=[];candidates=[];lead_index={clean_url(l['url']):dict(l) for l in prior};feed_candidates=[]
    for r in results:
        for lead in r['leads']:
            url=clean_url(lead['url'])
            if host(url) in known_hosts:continue
            old=lead_index.get(url,{})
            lead_index[url]=dict(lead,first_seen=old.get('first_seen',now),last_seen=now,**({'last_checked':old['last_checked']} if old.get('last_checked') else {}))
        if r['url'] in lead_index:lead_index[r['url']]['last_checked']=now
        for e in r['events']:
            if r['trusted'] and not e.get('location_needs_review') and not e.get('timezone_needs_review') and e.get('country') in ('Canada','USA','Mexico') and e.get('region') and e.get('venue') not in ('','Various'):
                observations.append(e)
            else:candidates.append(dict(e,status='needs_review',reason='Organizer ownership or event location needs verification'))
        feed_candidates.extend({'url':f,'club':r['club'],'found_on':r['url'],'status':'scanned' if any(p['url']==f for p in r['pages']) else 'budget_deferred'} for f in r['feeds'])
    auto_path=root/'data/automated_events.json';auto=json.loads(auto_path.read_text())
    exclusions={s['id']:s.get('excluded_series',[]) for s in sources}
    retained=[e for e in auto.get('events',[]) if not any(re.search(r'\b'+re.escape(term)+r'\b',e['name'],re.I) for term in exclusions.get(e.get('feed_id'),[]))]
    auto['events'],changes=reconcile(retained,observations,now);auto['updated']=now
    dump(auto_path,auto);dump(leads_path,{'updated':now,'sources':list(lead_index.values())})
    previous_path=root/'reports/discovery.json'
    previous=json.loads(previous_path.read_text()) if previous_path.exists() else {}
    state_path=root/'data/source_state.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else {}
    page_state=state.setdefault('discovery_pages',{})
    old_digests={p['url']:p.get('digest') for s in previous.get('sources',[]) for p in s['pages']}
    old_digests.update({url:value['digest'] for url,value in page_state.items()})
    content_changes=[]
    for result in results:
        for item in result['pages']:
            old=old_digests.get(item['url'])
            if item.get('digest'):page_state[item['url']]={'digest':item['digest'],'last_success':now}
            if old and old!=item.get('digest'):
                content_changes.append({'url':item['url'],'club':result['club'],'race_observations':item['events'],
                    'note':'Page content changed; changes outside supported structured fields need review.'})
    dump(state_path,state)
    public_results=[{k:v for k,v in r.items() if k not in ('events','leads')} for r in results]
    report={'checked_at':now,'sources_checked':sum(bool(r['pages']) for r in results),'sources_attempted':len(sources),
        'event_candidates':candidates,'calendar_feed_candidates':feed_candidates,'organizer_source_candidates':list(lead_index.values()),
        'changes':changes,'content_changes':content_changes,'observations':len(observations),'sources':public_results,'errors':[e for r in results for e in r['errors']]}
    dump(root/'reports/discovery.json',report)
    print(f"Discovery: reached {report['sources_checked']}/{len(sources)} sources; {len(observations)} publishable observations; {len(candidates)} review candidates; {len(lead_index)} organizer leads")
    return report

if __name__=='__main__':run()
