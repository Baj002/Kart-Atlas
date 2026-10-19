#!/usr/bin/env python3
"""Build web app data from curated CSV + validated auto-imports (no network needed)."""
from __future__ import annotations
import csv,hashlib,json,re,argparse
from datetime import date, datetime, timezone
from urllib.parse import urlsplit
import sys
from pathlib import Path
if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.discovery_engine import event_reference
from difflib import SequenceMatcher

FIELDS={'Start Date':'start','End Date':'end','Race / Event':'name','Club / Series':'organizer','Track / Venue':'venue','City':'city','State / Province':'region','Country':'country','Level':'level','Race Format':'format','Verification':'verification','Classes':'classes','Source URL':'source','Notes':'notes'}
ROOT=Path(__file__).resolve().parents[1]

def key(e):
    return '|'.join([e.get('start',''),e.get('name','').casefold().strip(),e.get('venue','').casefold().strip()])
def precise_match(e,p):
    refs={e.get('source'),e.get('registration_url')}-{None,''}
    refs2={p.get('source'),p.get('registration_url')}-{None,''}
    return bool(event_reference(e) and (event_reference(e)==event_reference(p) or refs.intersection(refs2)))

def is_dup(e,existing):
    for p in existing:
        if e['country']!=p['country'] or e['region']!=p['region']:continue
        # A specific event URL identifies a changed date. A shared schedule URL does not.
        specific=bool(event_reference(e))
        if specific and precise_match(e,p):return True
        if e['start']!=p['start']:continue
        names=SequenceMatcher(None,re.sub(r'[^a-z0-9]','',e['name'].lower()),re.sub(r'[^a-z0-9]','',p['name'].lower())).ratio()
        venue=(e.get('venue') or '').casefold().strip()
        same_venue=bool(venue and venue not in ('various','tba') and venue==(p.get('venue') or '').casefold().strip())
        same_organizer=e.get('organizer','').casefold()==p.get('organizer','').casefold()
        if same_venue and names>=.82 and same_organizer:return True
        if same_venue and e['name'].casefold()==p['name'].casefold():return True
    return False

def build(root=ROOT):
    original=[]
    with (root/'data/races.csv').open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            e={v:(r.get(k) or '').strip() for k,v in FIELDS.items()}
            if not e['name'] or not e['start']:continue
            date.fromisoformat(e['start']); e['end']=e['end'] or e['start'];date.fromisoformat(e['end'])
            e['id']=hashlib.sha1(key(e).encode()).hexdigest()[:12]
            original.append(e)
    originals={(key(e)):e for e in original}; curated=list(originals.values())
    auto=json.loads((root/'data/automated_events.json').read_text()).get('events',[])
    imported=[]
    for e in auto:
        matches=[p for p in curated if is_dup(e,[p])]
        if matches:
            p=matches[0]
            # Exact event-source agreement permits official lifecycle updates while
            # retaining the curated ID (and therefore saved races on user devices).
            specific=bool(event_reference(e))
            if specific and precise_match(e,p):
                for field in ('start','end','status','last_verified','history','registration_url'):
                    if field in e:p[field]=e[field]
            continue
        if not is_dup(e,imported):imported.append(e)
    enrichment_path=root/'data/event_enrichment.json'
    enrich=json.loads(enrichment_path.read_text()).get('records',{}) if enrichment_path.exists() else {}
    for e in curated+imported:
        info=enrich.get(key(e),{})
        if info.get('status')=='matched':
            for field in ('registration_url','schedule_url','rules_url','track_map_url'):
                if info.get(field):e[field]=info[field]
            e['enrichment_source']='MotorsportReg'
            e['enrichment_checked_at']=info.get('checked_at','')
    races=sorted(curated+imported,key=lambda e:(e['start'],e['name']))
    snap={'updated':datetime.now(timezone.utc).date().isoformat(),'curated_snapshot':'2026-10-16','coverage_note':'Coverage is expanding across Canada, USA and Mexico. Automated listings come from structured organizer calendars and event pages; check official details before travel.', 'auto_imported':len(imported),'events':races}
    (root/'site/events.json').write_text(json.dumps(snap,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    directory=json.loads((root/'data/clubs.json').read_text())
    monitors=json.loads((root/'data/monitor_sources.json').read_text())['sources']
    for c in directory['clubs']:
        for s in monitors:
            if c['name'].casefold()==s['club'].casefold() or (c['country']==s['country'] and c['region']==s['region'] and c['schedule_url'].split('?')[0] == s['url'].split('?')[0]):
                c['monitor_id']=s['id']; break
    (root/'site/clubs.json').write_text(json.dumps(directory,ensure_ascii=False,indent=2)+'\n')
    print(f"Built {len(races)} races ({len(curated)} curated + {len(imported)} automated), {len(directory['clubs'])} leads")
    return snap
if __name__=='__main__':build()
