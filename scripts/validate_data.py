"""Fail publication on malformed data and fail live health checks on total scan failure."""
import argparse
import datetime as dt
import json
import re
from scripts.check_sources import ROOT
from scripts.registration import instant
from scripts.discovery_engine import clean_url
from scripts.racing_scope import load_policy,event_scope_reason

def validate(root=ROOT,live=False):
    data=json.loads((root/'site/events.json').read_text());events=data['events'];seen=set()
    policy=load_policy(root)
    assert events,'No races published'
    for event in events:
        assert not event_scope_reason(event,policy),'Out-of-scope event: '+event['name']
        assert event['id'] not in seen,'Duplicate event ID: '+event['id'];seen.add(event['id'])
        start=dt.date.fromisoformat(event['start']);end=dt.date.fromisoformat(event['end'])
        assert start<=end,'End precedes start: '+event['name']
        assert (end-start).days<=12,'Implausible event duration: '+event['name']
        assert event['name'].strip() and event['organizer'].strip(),'Missing event identity'
        assert event['country'] in ('Canada','USA','Mexico'),'Unsupported country'
        assert clean_url(event['source']),'Invalid source: '+event['source']
        for field in ('registration_url','registration_evidence','schedule_url','rules_url','track_map_url'):
            if event.get(field):assert clean_url(event[field]),'Invalid '+field
        assert event.get('status','scheduled') in ('scheduled','cancelled','postponed'),'Unknown lifecycle status'
    for event in events:
        for field in ('registration_deadline','registration_opens_at','registration_checked_at'):
            if event.get(field):assert instant(event[field]),'Invalid timezone-aware '+field
        if event.get('registration_deadline') or event.get('registration_opens_at') or event.get('registration_status') in ('open','closed','sold_out'):
            assert event.get('registration_evidence') and instant(event.get('registration_checked_at')),'Registration claims require dated source evidence'
        if event.get('registration_status'):assert event['registration_status'] in ('open','closed','sold_out','not_announced','unknown','disabled'),'Invalid registration status'
        for alias in event.get('alias_ids',[]):
            assert isinstance(alias,str) and alias and alias not in seen,'Conflicting saved-race alias: '+str(alias)
            seen.add(alias)
    for event in events:
        if event.get('curated_id'):assert event['curated_id'] in seen,'Stale curated event mapping: '+event['curated_id']
    for duplicate_id,review in policy.get('duplicate_events',{}).items():
        assert clean_url(review['evidence']),'Missing duplicate identity evidence'
        dt.date.fromisoformat(review['reviewed_on'])
        canonical=next((e for e in events if e['id']==review['canonical_id']),None)
        assert canonical and duplicate_id in canonical.get('alias_ids',[]),'Missing reviewed saved-race alias'
    registration_config=root/'data/registration_sources.json'
    if registration_config.exists():
        for source in json.loads(registration_config.read_text())['sources']:
            assert source['event_id'] in seen,'Unknown registration event mapping'
            assert clean_url(source['url']) and clean_url(source['event_url']),'Invalid registration source URL'
    registry_path=root/'data/organizers.json'
    if registry_path.exists():
        organizers=json.loads(registry_path.read_text())['organizers'];ids=set();bindings=set();aliases={}
        configured={s['id'] for s in json.loads((root/'data/monitor_sources.json').read_text())['sources']}
        for organizer in organizers:
            assert organizer['id'] not in ids,'Duplicate organizer ID';ids.add(organizer['id'])
            assert organizer['scope_status'] in ('eligible','needs_review','excluded'),'Invalid organizer scope'
            for alias in [organizer['name']]+organizer.get('aliases',[]):
                token=re.sub(r'\W','',alias.casefold())
                assert not token in aliases or aliases[token]==organizer['id'],'Ambiguous organizer alias: '+alias
                aliases[token]=organizer['id']
            for source_id in organizer.get('source_ids',[]):
                assert source_id in configured,'Unknown organizer source: '+source_id
                assert source_id not in bindings,'Source bound to multiple organizers: '+source_id
                bindings.add(source_id)
            for declaration in organizer.get('season_declarations',[]):
                assert clean_url(declaration['evidence']),'Missing season evidence'
                dt.date.fromisoformat(declaration['reviewed_on'])
        assert bindings==configured,'Configured organizer source is missing a registry binding'
    if live:
        report=json.loads((root/'reports/discovery.json').read_text())
        assert any(s['trusted'] and s['pages'] for s in report['sources']),'No trusted organizer sources reached'
        age=dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(report['checked_at'])
        assert age.total_seconds()<48*3600,'Discovery report is stale'
    print(f"Validated {len(events)} races"+(' and live discovery health' if live else ''))
    return True

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args();validate(live=args.live)
