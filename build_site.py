#!/usr/bin/env python3
"""Build web app data from curated CSV + validated auto-imports (no network needed)."""
from __future__ import annotations
import csv,hashlib,json,re,argparse
from datetime import date
from pathlib import Path
from difflib import SequenceMatcher

FIELDS={'Start Date':'start','End Date':'end','Race / Event':'name','Club / Series':'organizer','Track / Venue':'venue','City':'city','State / Province':'region','Country':'country','Level':'level','Race Format':'format','Verification':'verification','Classes':'classes','Source URL':'source','Notes':'notes'}
ROOT=Path(__file__).resolve().parents[1]

def key(e):
    return '|'.join([e.get('start',''),e.get('name','').casefold().strip(),e.get('venue','').casefold().strip()])
def is_dup(e,existing):
    for p in existing:
        if e['start']!=p['start'] or e['country']!=p['country'] or e['region']!=p['region']: continue
        names=SequenceMatcher(None,re.sub(r'[^a-z0-9]','',e['name'].lower()),re.sub(r'[^a-z0-9]','',p['name'].lower())).ratio()
        venues=(e.get('venue') or '').lower().strip() == (p.get('venue') or '').lower().strip()
        if venues and names >= .72:return True
        if e['name'].casefold()==p['name'].casefold():return True
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
        if not is_dup(e,curated) and not is_dup(e,imported):imported.append(e)
    races=sorted(curated+imported,key=lambda e:(e['start'],e['name']))
    snap={'updated':'2026-10-16','coverage_note':'Research snapshot, not a complete list of North American kart races. Automated additions come only from identified organizer calendar feeds; check organizer before travel.', 'auto_imported':len(imported),'events':races}
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
