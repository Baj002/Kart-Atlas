#!/usr/bin/env python3
"""Discover potential new kart race events and calendar feeds on known public organizer pages.

This is a review queue, not an unverified auto-publisher. Obeys robots.txt and
never follows off-domain links or guesses race dates.
"""
from __future__ import annotations
import datetime as dt
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from scripts.check_sources import ROOT, fetch, is_allowed_by_robots, RACE_TERMS, EXCLUDED

class DiscoverParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.events = []
        self._jsonld = False
        self._buffer = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        if tag == 'script' and 'ld+json' in a.get('type','').lower():
            self._jsonld = True
            self._buffer = []
    def handle_data(self, data):
        if self._jsonld:
            self._buffer.append(data)
    def handle_endtag(self, tag):
        if tag == 'script' and self._jsonld:
            self._jsonld = False
            try:
                obj = json.loads(''.join(self._buffer))
                self._collect(obj)
            except (ValueError,TypeError):
                pass
    def _collect(self, obj):
        if isinstance(obj,list):
            for x in obj: self._collect(x)
        elif isinstance(obj,dict):
            typ=obj.get('@type',[])
            if isinstance(typ,str): typ=[typ]
            if 'Event' in typ or 'SportsEvent' in typ:
                self.events.append(obj)
            for k in ('@graph','mainEntity','itemListElement'):
                if k in obj: self._collect(obj[k])

def extract(raw, source, today=None):
    today = today or dt.date.today()
    p = DiscoverParser()
    p.feed(raw)
    origin = urlsplit(source['url'])
    feeds=[]
    for href in p.links:
        url=urljoin(source['url'],href)
        u=urlsplit(url)
        if u.scheme not in ('https','http') or u.hostname != origin.hostname: continue
        if not (re.search(r'\.ics(?:$|\?)',url,re.I) or 'ical=1' in u.query.lower()):continue
        if url not in feeds: feeds.append(url)
    events=[]
    for e in p.events:
        name=str(e.get('name') or '').strip()
        start=str(e.get('startDate') or '')[:10]
        if not name or not RACE_TERMS.search(name) or EXCLUDED.search(name): continue
        try: day=dt.date.fromisoformat(start)
        except ValueError: continue
        if not today <= day <= today+dt.timedelta(days=550):continue
        url=str(e.get('url') or source['url'])
        parsed=urlsplit(url)
        if parsed.scheme not in ('https','http'):url=source['url']
        loc=e.get('location') or {}
        if isinstance(loc,list):loc=loc[0] if loc else {}
        if not isinstance(loc,dict):loc={}
        venue=str(loc.get('name') or source.get('venue',''))
        events.append({'name':name[:180],'start':start,'organizer':source['club'],
                       'venue':venue,'city':source.get('city',''),'region':source.get('region',''),
                       'country':source.get('country',''),'source':url,'discovered_from':source['url'],
                       'status':'needs_review'})
    return {'feeds':feeds,'events':events}

def run(root=ROOT, fetcher=fetch, robots_checker=None, today=None):
    today=today or dt.date.today()
    sources=json.loads((root/'data/monitor_sources.json').read_text())['sources']
    known={s['url'] for s in sources}
    races=json.loads((root/'site/events.json').read_text()).get('events',[])
    existing={(r['start'],re.sub(r'[^a-z0-9]','',r['name'].lower())) for r in races}
    # Inventory club directory websites not yet included in the monitored sources.
    # These are research leads only; a directory URL is not proof of ownership.
    clubs_path=root/'data/clubs.json'
    organizer_leads=[]
    if clubs_path.exists():
        directory=json.loads(clubs_path.read_text()).get('clubs',[])
        monitored_hosts={urlsplit(u).hostname for u in known}
        seen_hosts=set()
        for club in directory:
            url=club.get('schedule_url') or ''
            u=urlsplit(url)
            if u.scheme not in ('https','http') or not u.hostname:continue
            host=u.hostname.lower().removeprefix('www.')
            if any(host == (h or '').lower().removeprefix('www.') for h in monitored_hosts):continue
            if host in seen_hosts:continue
            seen_hosts.add(host)
            organizer_leads.append({'club':club.get('name',''),'city':club.get('city',''),
              'region':club.get('region',''),'country':club.get('country',''),
              'url':url,'status':'unverified_organizer_source'})
    candidates=[];feeds=[];errors=[];checked=0;cache={}
    for source in sources:
        if source.get('mode')!='watch' or source['url'].lower().split('?')[0].endswith('.pdf'):continue
        try:
            allowed=robots_checker(source['url']) if robots_checker else (is_allowed_by_robots(source['url'],cache) if fetcher is fetch else True)
            if not allowed:continue
            raw=fetcher(source['url'])
            result=extract(raw,source,today)
            checked+=1
            for f in result['feeds']:
                if f not in known and f not in [x['url'] for x in feeds]:
                    feeds.append({'url':f,'club':source['club'],'found_on':source['url'],'status':'needs_review'})
            for e in result['events']:
                key=(e['start'],re.sub(r'[^a-z0-9]','',e['name'].lower()))
                if key not in existing and key not in {(x['start'],re.sub(r'[^a-z0-9]','',x['name'].lower())) for x in candidates}:
                    candidates.append(e)
        except (OSError,ValueError,UnicodeError) as exc:
            errors.append({'source':source['id'],'error':str(exc)[:160]})
    report={'checked_at':dt.datetime.now(dt.timezone.utc).isoformat(),'sources_checked':checked,
            'event_candidates':candidates,'calendar_feed_candidates':feeds,'organizer_source_candidates':organizer_leads,'errors':errors}
    (root/'reports/discovery.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(f"Discovery: {checked} sources, {len(candidates)} new event candidates, {len(feeds)} feed candidates, {len(organizer_leads)} organizer leads")
    return report

if __name__=='__main__':run()
