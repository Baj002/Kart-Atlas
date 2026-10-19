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
from scripts.pdf_schedules import extract_pdf
from scripts.platform_calendars import extract_raceselect
from scripts.text_schedules import extract_text_schedule
from scripts.racing_scope import load_policy,event_scope_reason,source_scope_reason
from scripts.source_health import update_health
from scripts.check_sources import AGENT, LIMIT, CANCEL_TERMS, RACE_TERMS, EXCLUDED, normalized_ics, mapping_in_window, visible_text, ROOT

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
BAD_HOSTS={'smugmug.com','wixstatic.com','squarespace-cdn.com','assets.kartpulse.com','facebook.com','instagram.com','youtube.com','twitter.com','x.com','google.com','google.ca','squarespace.com','wix.com','amazon.com','paypal.com'}

def host(url):
    return (urlsplit(url).hostname or '').lower().removeprefix('www.')

NON_EVENT_PATH=re.compile(r'/(?:evententries|entrylist|entry-list|participants|attendees|lineup|account)(?:/|$)',re.I)
ASSET_PATH=re.compile(r'\.(?:jpe?g|png|gif|webp|svg|ico|avif|mp4|mov|mp3|zip|css|js|woff2?|pdf)(?:$)',re.I)

def organizer_url(url):
    return bool(clean_url(url) and not ASSET_PATH.search(urlsplit(url).path) and
        not any(host(url)==h or host(url).endswith('.'+h) for h in BAD_HOSTS))

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
    return u.path.lower().endswith('.ics') or q.get('ical')==['1'] or q.get('format')==['ical'] or q.get('ical')==['true'] or (q.get('option')==['com_dpcalendar'] and q.get('task')==['ical.download'])

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
        req=Request(url,headers={'User-Agent':AGENT,'Accept':'text/calendar,application/pdf,application/ld+json,text/html;q=0.9'})
        with build_opener(PublicRedirect()).open(req,timeout=12) as r:
            if re.search(r'/(?:account/)?(?:login|sign-?in)(?:/|$)',urlsplit(r.geturl()).path,re.I):raise ValueError('Sign-in required; public retrieval stopped')
            content=r.read(limit+1)
            if len(content)>limit:raise ValueError('Response exceeds size limit')
            kind=r.headers.get_content_type()
            if kind=='application/pdf' or content.startswith(b'%PDF'):
                if not content.startswith(b'%PDF'):raise ValueError('Invalid PDF response')
                return content
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
        super().__init__();self.links=[];self.events=[];self.jsonld=None;self.anchor=None;self.card=None;self.card_depth=0;self.title=False;self.title_text='';self.heading=None;self.last_heading='';self.schedule_year=None;self.table_year=None;self.table=False;self.row=None;self.cell=None;self.table_columns=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);classes=a.get('class','').split()
        if tag=='title':self.title=True
        if tag in ('h1','h2','h3'):self.heading=[]
        if tag=='table':self.table=True;self.table_year=self.schedule_year;self.table_columns=None
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
                elif 'event-date' in classes or 'event-time-localized-end' in classes or 'event-date-end' in classes:self.card['endDate']=a['datetime']
            if tag=='li' and 'eventlist-meta-address' in classes:self.card['_venue_text']=[]
        if tag in ('iframe','embed','object'):
            embedded=a.get('src') or a.get('data','')
            if urlsplit(embedded).path.lower().endswith('.pdf'):self.links.append({'url':embedded,'label':'Embedded schedule','type':'application/pdf','rel':''})
        if tag in ('a','link') and a.get('href'):
            link={'url':a['href'],'label':a.get('aria-label') or a.get('title',''),'type':a.get('type',''),'rel':a.get('rel',''),'context':self.last_heading}
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
        if self.card is not None and '_venue_text' in self.card and self.anchor is None:self.card['_venue_text'].append(data)
    def handle_endtag(self,tag):
        if tag=='title':self.title=False
        if tag in ('h1','h2','h3') and self.heading is not None:
            heading=''.join(self.heading);years=re.findall(r'\b(20\d{2})\b',heading)
            self.last_heading=' '.join(heading.split())[:180]
            if len(set(years))==1 and CALENDAR.search(heading):self.schedule_year=int(years[0])
            self.heading=None
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(self.cell));self.cell=None
        if tag=='tr' and self.row is not None:
            labels=[c.strip().lower() for c in self.row]
            date_columns=[i for i,c in enumerate(labels) if c in ('date','dates','fecha','jour/date')]
            event_columns=[i for i,c in enumerate(labels) if c in ('event','race','round','race / event','événement','evento')]
            if date_columns and event_columns:self.table_columns={'date':date_columns[0],'event':event_columns[0]}
            event=row_event(self.row,self.table_year,self.table_columns)
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
        if tag=='li' and self.card is not None and '_venue_text' in self.card:
            self.card['location']={'name':' '.join(''.join(self.card.pop('_venue_text')).split())}
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
    if source.get('event_name_pattern') and not re.search(source['event_name_pattern'],name,re.I):return None
    if event_scope_reason({'name':name,'organizer':source.get('club',''),'format':source.get('format',''),'description':e.get('description','')}):return None
    table_key=e.get('_table_key','')
    mapping=next((value for label,value in source.get('table_events',{}).items() if table_key==label or table_key.startswith(label+' ')),{})
    if mapping.get('name'):name=mapping['name']
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
    venue_alias=source.get('venue_aliases',{}).get(str(location.get('name') or '').strip())
    if venue_alias:location=venue_alias
    address=location.get('address') or {}
    if not isinstance(address,dict):address={}
    country=address.get('addressCountry') or fallback.get('country','')
    if isinstance(country,dict):country=country.get('name','')
    country=COUNTRIES.get(str(country).upper(),'')
    link=clean_url(e.get('url') or e.get('@id') or '',source['url']) or source['url']
    identity_name=CANCEL_TERMS.sub('',name).strip(' -–—:').casefold()
    uid=str(e.get('@id') or e.get('url') or (source['url']+'#'+identity_name))
    if not e.get('@id') and not e.get('url') and re.fullmatch(r'(?:club |championship )?race(?: day)?',name,re.I):uid+='|'+str(start)
    if mapping:uid=source['url']+'#'+mapping['name']+('' if mapping_in_window(source,'table',start) else '|'+str(start.year))
    record={'name':name[:180],'start':str(start),'end':str(end),'organizer':source['club'],
        'venue':str(location.get('name') or fallback.get('venue',''))[:180],
        'city':str(address.get('addressLocality') or fallback.get('city','')),
        'region':region_code(address.get('addressRegion') or fallback.get('region',''),country),'country':country,
        'source':link,'uid':uid,'feed_id':source['id'],'status':state,'status_explicit':bool(status),
        'format':'Dirt oval' if re.search(r'\bdirt\s+oval\b',name,re.I) else 'Endurance' if re.search('endur',name,re.I) else source.get('format','Sprint'),
        'level':source.get('level','Club'),'verification':'Automated','classes':'',
        'notes':'Imported from structured organizer data. Confirm rules and registration with the organizer.',
        'discovered_from':source['url'],'parser':e.get('_parser','jsonld'),'location_needs_review':bool(e.get('_location_ambiguous')),'publication_needs_review':bool(e.get('_publication_needs_review'))}
    if e.get('_shared_url'):record['shared_source_url']=True
    if source.get('event_notes'):record['notes']+=' '+source['event_notes']
    if source.get('require_venue_alias') and not venue_alias and e.get('_parser')=='squarespace':record['location_needs_review']=True
    if mapping.get('curated_id') and mapping_in_window(source,'table',start):record['curated_id']=mapping['curated_id']
    if e.get('_registration_status'):record['registration_status']=e['_registration_status']
    if e.get('_registration_url'):record['registration_url']=clean_url(e['_registration_url'],source['url'])
    if host(source['url'])=='raceselect.com' and not source.get('platform_venue_verified'):record['publication_needs_review']=True
    if e.get('_pdf_page'):record['pdf_page']=e['_pdf_page']
    for a in e.get('_links',[]):
        if re.search(r'\bregistration|register|inscription|inscripci',a['label'],re.I):
            url=clean_url(a['url'],source['url'])
            if url:record['registration_url']=url;break
    return record

def extract_page(raw,source,today):
    p=Parser();p.feed(raw)
    p.events.extend(extract_raceselect(raw,source))
    p.events.extend(extract_text_schedule(raw,source))
    # Some organizers assign every round the same series URL. Preserve distinct
    # rounds even when they are duplicated in desktop/mobile JSON-LD graphs.
    shared={}
    for event in p.events:
        url=clean_url(event.get('url',''),source['url'])
        if url:shared.setdefault(url,set()).add((str(event.get('name','')),str(event.get('startDate',''))[:10],str(event.get('@id',''))))
    for event in p.events:
        url=clean_url(event.get('url',''),source['url'])
        if len(shared.get(url,()))>1:
            if not event.get('@id'):
                name=str(event.get('name',''))
                repeated=len({date for n,date,uid in shared[url] if n==name})>1
                token=str(event.get('startDate',''))[:10 if repeated else 4]
                event['@id']=url+'#'+token+'|'+name.casefold()
            event['_shared_url']=True
    events=[r for e in p.events if (r:=normalize_event(e,source,today))] if not re.search(r'esports?|iracing|simracing',source['url'],re.I) else []
    links=[];feeds=[];leads=[];documents=[];schedule_documents=[]
    for a in p.links:
        url=clean_url(a['url'],source['url'])
        if not url or NON_EVENT_PATH.search(urlsplit(url).path):continue
        if source_scope_reason({'url':url}):continue
        label=a['label'].strip()
        if re.fullmatch(r'site\s*web|web\s*site|website',label,re.I):label=a.get('context') or label
        if host(url)==host(source['url']):
            if feed_url(url) or a['type']=='text/calendar' or (urlsplit(url).path.endswith('.raw') and re.search(r'outlook|ics|ical',a['label'],re.I)):feeds.append(url)
            elif urlsplit(url).path.lower().endswith('.pdf'):
                documents.append(url)
                if CALENDAR.search(a['label']+' '+urlsplit(url).path) or (source.get('pdf_profile') and CALENDAR.search(urlsplit(source['url']).path)):
                    if not re.search(r'waiver|consent|regulations?|rulebook|rules|tech.?sheet|results?|standings|pit.?map|configuration',url+' '+a['label'],re.I):schedule_documents.append(url)
            elif not (host(source['url'])=='raceselect.com' and urlsplit(url).path.lower().endswith('/eventdetails')) and not re.search(r'/feed/?$|\.rss$',urlsplit(url).path,re.I) and CALENDAR.search(urlsplit(url).path+' '+a['label']) and not re.search(r'\.(jpg|png|css|js|zip)$',urlsplit(url).path,re.I):links.append(url)
        elif source.get('directory') and re.search(r'kart|raceway|speedway|motorplex',label+' '+host(url),re.I):
            if organizer_url(url):
                leads.append({'url':url,'club':label[:180] or host(url),'found_on':source['url'],
                    'country':source.get('country',''),'status':'unverified_organizer_source'})
    return {'events':events,'feeds':list(dict.fromkeys(feeds)),'links':list(dict.fromkeys(links)),
            'leads':leads,'documents':list(dict.fromkeys(documents)),'schedule_documents':list(dict.fromkeys(schedule_documents)),'title':p.title_text.strip()}

def event_reference(event):
    if event.get('shared_source_url'):return ''
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

def scan_source(source,fetcher,today,max_pages=5,page_last_checked=None):
    page_last_checked=page_last_checked or {}
    queue=[source['url']];seen=set();events=[];leads=[];feeds=[];errors=[];documents=[];pages=[]
    # Roots first, then feeds and calendar/detail links. Strict page budget per source.
    while queue and len(seen)<max_pages:
        url=queue.pop(0)
        if url in seen:continue
        seen.add(url);local=dict(source,url=url)
        try:
            raw=fetcher(url)
            if urlsplit(url).path.lower().endswith('.pdf') and not isinstance(raw,bytes):raise ValueError('PDF URL returned non-PDF content')
            if isinstance(raw,bytes):
                result=extract_pdf(raw,local)
                extracted=[e for item in result['events'] if (e:=normalize_event(item,local,today))]
                events.extend(extracted)
                pages.append({'url':url,'parser':'pdf-text','events':len(extracted),'pdf_pages':result['pages'],'notice':result['notice'],'digest':hashlib.sha256(raw).hexdigest()})
            elif 'BEGIN:VCALENDAR' in raw[:500]:
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
                candidates=sorted(result['schedule_documents']+result['feeds']+result['links'],key=lambda u:(page_last_checked.get(u,''),0 if u in result['feeds'] or re.search(r'/calendar/[^/]+_20\d{6}',urlsplit(u).path) else 1))
                immediate=[u for u in candidates if u in result['feeds'] or u in result['schedule_documents']]
                ordinary=[u for u in candidates if u not in immediate]
                # A discovered export must get a turn before the remaining root
                # navigation links consume the whole bounded crawl.
                queue=[u for u in immediate if u not in seen]+[u for u in queue if u not in immediate]
                queue.extend(u for u in ordinary if u not in seen and u not in queue)
        except (OSError,ValueError,UnicodeError,HTTPException) as exc:errors.append({'url':url,'error':f'{type(exc).__name__}: {exc}'[:240]})
    print(f"Scan {source['id']}: {len(pages)}/{len(seen)} pages, {len(events)} race observations, {len(errors)} errors",flush=True)
    return {'source_id':source['id'],'club':source['club'],'url':source['url'],'trusted':bool(source.get('trusted')),
        'country':source.get('country',''),'region':source.get('region',''),'attempted':len(seen),
        'pages':pages,'events':events,'leads':leads,'feeds':list(dict.fromkeys(feeds)),
        'documents':list(dict.fromkeys(documents)),'errors':errors,'remaining_links':len(set(queue)-seen)}

def run(root=ROOT,fetcher=None,today=None,workers=6):
    today=today or dt.datetime.now(dt.timezone.utc).date();now=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    config=json.loads((root/'data/monitor_sources.json').read_text())
    policy=load_policy(root)
    sources=[dict(s,trusted=True) for s in config['sources'] if s.get('source_kind')!='document_reference' and not source_scope_reason(s,policy)]
    extras=root/'data/discovery_sources.json'
    settings=json.loads(extras.read_text()) if extras.exists() else {}
    sources.extend(s for s in settings.get('sources',[]) if not source_scope_reason(s,policy))
    known={clean_url(s['url']) for s in sources};known_hosts={host(s['url']) for s in sources if s.get('trusted')}
    directory=json.loads((root/'data/clubs.json').read_text()).get('clubs',[])
    for c in directory:
        if source_scope_reason(c,policy):continue
        url=clean_url(c.get('schedule_url',''))
        if not url or url in known:continue
        known.add(url)
        sources.append({'id':'lead-'+c['id'],'club':c['name'],'url':url,'venue':c.get('venue',''),
            'city':c.get('city',''),'region':c.get('region',''),'country':c.get('country',''),
            'trusted':False,'directory':host(url)=='forums.kartpulse.com'})
    leads_path=root/'data/discovered_sources.json'
    inventory=json.loads(leads_path.read_text()) if leads_path.exists() else {}
    prior=inventory.get('sources',[])
    rejected_leads=inventory.get('rejected_sources',[])+[dict(lead,rejection_reason='Asset or media host; not an organizer website') for lead in prior if not organizer_url(lead['url'])]
    prior=[lead for lead in prior if organizer_url(lead['url']) and not source_scope_reason(lead,policy)]
    # Rotation prevents a large lead inventory from starving later entries.
    ordered=sorted(prior,key=lambda x:(x.get('last_checked',''),x['url']))
    for lead in ordered[:settings.get('lead_scan_limit',40)]:
        url=clean_url(lead['url'])
        if not url or url in known:continue
        known.add(url);sources.append(dict(lead,id='found-'+hashlib.sha1(url.encode()).hexdigest()[:12],trusted=False))
    client=fetcher or PublicClient()
    state_path=root/'data/source_state.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else {}
    page_state=state.setdefault('discovery_pages',{})
    last_checked={url:value.get('last_attempt',value.get('last_success','')) for url,value in page_state.items()}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results=list(pool.map(lambda s:scan_source(s,client,today,settings.get('max_pages_per_source',5),last_checked),sources))
    observations=[];candidates=[];lead_index={clean_url(l['url']):dict(l) for l in prior};feed_candidates=[]
    for r in results:
        for lead in r['leads']:
            if source_scope_reason(lead,policy):continue
            url=clean_url(lead['url'])
            if host(url) in known_hosts:continue
            old=lead_index.get(url,{})
            lead_index[url]=dict(lead,first_seen=old.get('first_seen',now),last_seen=now,**({'last_checked':old['last_checked']} if old.get('last_checked') else {}))
        if r['url'] in lead_index:lead_index[r['url']]['last_checked']=now
        for e in r['events']:
            if event_scope_reason(e,policy):continue
            if r['trusted'] and not e.get('publication_needs_review') and not e.get('location_needs_review') and not e.get('timezone_needs_review') and e.get('country') in ('Canada','USA','Mexico') and e.get('region') and e.get('venue') not in ('','Various'):
                observations.append(e)
            else:candidates.append(dict(e,status='needs_review',reason='Organizer ownership or event location needs verification'))
        feed_candidates.extend({'url':f,'club':r['club'],'found_on':r['url'],'status':'scanned' if any(p['url']==f for p in r['pages']) else 'budget_deferred'} for f in r['feeds'])
    auto_path=root/'data/automated_events.json';auto=json.loads(auto_path.read_text())
    health,health_alerts=update_health(results,state.get('discovery_health',{}),auto.get('events',[]),today,now,identity)
    state['discovery_health']=health
    exclusions={s['id']:s.get('excluded_series',[]) for s in sources}
    removed=[dict(e,scope_reason=event_scope_reason(e,policy)) for e in auto.get('events',[]) if event_scope_reason(e,policy)]
    if removed:auto['excluded_events']=list({e['id']:e for e in auto.get('excluded_events',[])+removed}.values())
    retained=[e for e in auto.get('events',[]) if not event_scope_reason(e,policy) and not any(re.search(r'\b'+re.escape(term)+r'\b',e['name'],re.I) for term in exclusions.get(e.get('feed_id'),[]))]
    auto['events'],changes=reconcile(retained,observations,now);auto['updated']=now
    dump(auto_path,auto);dump(leads_path,{'updated':now,'sources':list(lead_index.values()),'rejected_sources':list({l['url']:l for l in rejected_leads}.values())})
    previous_path=root/'reports/discovery.json'
    previous=json.loads(previous_path.read_text()) if previous_path.exists() else {}
    old_digests={p['url']:p.get('digest') for s in previous.get('sources',[]) for p in s['pages']}
    old_digests.update({url:value['digest'] for url,value in page_state.items() if value.get('digest')})
    content_changes=[]
    for result in results:
        for item in result['pages']:
            old=old_digests.get(item['url'])
            if item.get('digest'):page_state[item['url']]={'digest':item['digest'],'last_success':now,'last_attempt':now}
            if old and old!=item.get('digest'):
                content_changes.append({'url':item['url'],'club':result['club'],'race_observations':item['events'],
                    'note':'Page content changed; changes outside supported structured fields need review.'})
    for result in results:
        for error in result['errors']:
            page_state.setdefault(error['url'],{})['last_attempt']=now
    dump(state_path,state)
    public_results=[{k:v for k,v in r.items() if k not in ('events','leads')} for r in results]
    report={'checked_at':now,'sources_checked':sum(bool(r['pages']) for r in results),'sources_attempted':len(sources),
        'event_candidates':candidates,'calendar_feed_candidates':feed_candidates,'organizer_source_candidates':list(lead_index.values()),'rejected_organizer_leads':rejected_leads,
        'changes':changes,'content_changes':content_changes,'observations':len(observations),'sources':public_results,'errors':[e for r in results for e in r['errors']],
        'source_health':[health[r['source_id']] for r in results],'health_alerts':health_alerts}
    dump(root/'reports/discovery.json',report)
    print(f"Discovery: reached {report['sources_checked']}/{len(sources)} sources; {len(observations)} publishable observations; {len(candidates)} review candidates; {len(lead_index)} organizer leads")
    return report

if __name__=='__main__':run()
