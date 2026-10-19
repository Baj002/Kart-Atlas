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
from scripts.discovery_engine import event_reference, region_code
from difflib import SequenceMatcher
from scripts.racing_scope import load_policy,event_scope_reason,source_scope_reason,apply_reviewed_override

FIELDS={'Start Date':'start','End Date':'end','Race / Event':'name','Club / Series':'organizer','Track / Venue':'venue','City':'city','State / Province':'region','Country':'country','Level':'level','Race Format':'format','Verification':'verification','Classes':'classes','Source URL':'source','Notes':'notes'}
ROOT=Path(__file__).resolve().parents[1]

def key(e):
    return '|'.join([e.get('start',''),e.get('name','').casefold().strip(),e.get('venue','').casefold().strip()])
def precise_match(e,p):
    refs={e.get('source'),e.get('registration_url')}-{None,''}
    refs2={p.get('source'),p.get('registration_url')}-{None,''}
    return bool(event_reference(e) and (event_reference(e)==event_reference(p) or refs.intersection(refs2)))

def merge_curated_duplicates(events):
    """Merge punctuation-only copies on identical official dates/venue/source.

    Retain every former ID as an alias so saved races survive the correction.
    Organizer shorthand alone is not evidence; the official source must agree.
    """
    result=[];seen={}
    for event in events:
        venue=event['venue'].casefold().strip()
        token=(event['country'],event['region'],event['start'],event['end'],venue,
            re.sub(r'\W','',event['name'].casefold()),event['source'])
        existing=seen.get(token) if venue not in ('','various','tba') else None
        if existing:
            if event['id']!=existing['id']:existing.setdefault('alias_ids',[]).append(event['id'])
        else:result.append(event);seen[token]=event
    return result

def merge_reviewed_duplicates(events, policy):
    """Merge only explicit reviewed identities, including unknown-venue copies."""
    records={event['id']:dict(event) for event in events}
    reviews=policy.get('duplicate_events',{})
    for duplicate_id,review in reviews.items():
        canonical_id=review['canonical_id']
        assert duplicate_id!=canonical_id and canonical_id not in reviews,'Cyclic or chained duplicate mapping'
        assert canonical_id in records,'Missing canonical race: '+canonical_id
        if duplicate_id not in records:continue
        duplicate=records[duplicate_id];canonical=records[canonical_id]
        assert duplicate['country']==canonical['country'] and duplicate['organizer']==canonical['organizer'],'Reviewed duplicate organizer mismatch'
        canonical['alias_ids']=list(dict.fromkeys(canonical.get('alias_ids',[])+[duplicate_id]+duplicate.get('alias_ids',[])))
        del records[duplicate_id]
    return list(records.values())

def is_dup(e,existing):
    for p in existing:
        if e['country']!=p['country'] or e['region']!=p['region']:continue
        # A specific event URL identifies a changed date. A shared schedule URL does not.
        specific=bool(event_reference(e))
        if (e.get('curated_id') and e['curated_id']==p.get('id')) or (specific and precise_match(e,p)):return True
        if e['start']!=p['start']:continue
        names=SequenceMatcher(None,re.sub(r'[^a-z0-9]','',e['name'].lower()),re.sub(r'[^a-z0-9]','',p['name'].lower())).ratio()
        venue=(e.get('venue') or '').casefold().strip()
        same_venue=bool(venue and venue not in ('various','tba') and venue==(p.get('venue') or '').casefold().strip())
        same_organizer=e.get('organizer','').casefold()==p.get('organizer','').casefold()
        if same_venue and names>=.82 and same_organizer:return True
        if same_venue and e['name'].casefold()==p['name'].casefold():return True
    return False

def build(root=ROOT):
    original=[];excluded=[];policy=load_policy(root)
    with (root/'data/races.csv').open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            e={v:(r.get(k) or '').strip() for k,v in FIELDS.items()}
            if not e['name'] or not e['start']:continue
            e['region']=region_code(e['region'],e['country'])
            date.fromisoformat(e['start']); e['end']=e['end'] or e['start'];date.fromisoformat(e['end'])
            e['id']=hashlib.sha1(key(e).encode()).hexdigest()[:12]
            e=apply_reviewed_override(e,policy)
            reason=event_scope_reason(e,policy)
            if reason:excluded.append(dict(e,scope_reason=reason));continue
            original.append(e)
    originals={(key(e)):e for e in original}; curated=merge_reviewed_duplicates(merge_curated_duplicates(list(originals.values())),policy)
    auto=json.loads((root/'data/automated_events.json').read_text()).get('events',[])
    imported=[]
    for e in auto:
        e=dict(e,region=region_code(e['region'],e['country']))
        reason=event_scope_reason(e,policy)
        if reason:excluded.append(dict(e,scope_reason=reason));continue
        matches=[p for p in curated if e.get('curated_id') in [p['id']]+p.get('alias_ids',[]) or is_dup(e,[p])]
        if matches:
            p=matches[0]
            # Exact event-source agreement permits official lifecycle updates while
            # retaining the curated ID (and therefore saved races on user devices).
            specific=bool(event_reference(e))
            if (e.get('curated_id') and e['curated_id'] in [p['id']]+p.get('alias_ids',[])) or (specific and precise_match(e,p)):
                for field in ('start','end','status','last_verified','history','registration_url','registration_status'):
                    if field in e:p[field]=e[field]
                if e.get('curated_id') and not e.get('location_needs_review'):
                    for field in ('venue','city','region','country'):
                        if e.get(field):p[field]=e[field]
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
    excluded_clubs=[dict(c,scope_reason=source_scope_reason(c,policy)) for c in directory['clubs'] if source_scope_reason(c,policy)]
    directory['clubs']=[c for c in directory['clubs'] if not source_scope_reason(c,policy)]
    monitors=json.loads((root/'data/monitor_sources.json').read_text())['sources']
    for c in directory['clubs']:
        for s in monitors:
            if c['name'].casefold()==s['club'].casefold() or (c['country']==s['country'] and c['region']==s['region'] and c['schedule_url'].split('?')[0] == s['url'].split('?')[0]):
                c['monitor_id']=s['id']; break
    (root/'site/clubs.json').write_text(json.dumps(directory,ensure_ascii=False,indent=2)+'\n')
    (root/'reports').mkdir(exist_ok=True)
    (root/'reports/scope_audit.json').write_text(json.dumps({'scope':policy.get('scope','Competition circuit karting'),
        'excluded_events':excluded,'excluded_clubs':excluded_clubs,'reviewed_corrections':list(policy.get('event_overrides',{})),'reviewed_duplicates':policy.get('duplicate_events',{})},indent=2,ensure_ascii=False)+'\n')
    print(f"Built {len(races)} races ({len(curated)} curated + {len(imported)} automated), {len(directory['clubs'])} leads")
    return snap
if __name__=='__main__':build()
