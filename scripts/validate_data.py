"""Fail publication on malformed data and fail live health checks on total scan failure."""
import argparse
import datetime as dt
import json
from scripts.check_sources import ROOT
from scripts.discovery_engine import clean_url

def validate(root=ROOT,live=False):
    data=json.loads((root/'site/events.json').read_text());events=data['events'];seen=set()
    assert events,'No races published'
    for event in events:
        assert event['id'] not in seen,'Duplicate event ID: '+event['id'];seen.add(event['id'])
        start=dt.date.fromisoformat(event['start']);end=dt.date.fromisoformat(event['end'])
        assert start<=end,'End precedes start: '+event['name']
        assert (end-start).days<=12,'Implausible event duration: '+event['name']
        assert event['name'].strip() and event['organizer'].strip(),'Missing event identity'
        assert event['country'] in ('Canada','USA','Mexico'),'Unsupported country'
        assert clean_url(event['source']),'Invalid source: '+event['source']
        for field in ('registration_url','schedule_url','rules_url','track_map_url'):
            if event.get(field):assert clean_url(event[field]),'Invalid '+field
        assert event.get('status','scheduled') in ('scheduled','cancelled','postponed'),'Unknown lifecycle status'
    for event in events:
        if event.get('curated_id'):assert event['curated_id'] in seen,'Stale curated event mapping: '+event['curated_id']
    if live:
        report=json.loads((root/'reports/discovery.json').read_text())
        assert any(s['trusted'] and s['pages'] for s in report['sources']),'No trusted organizer sources reached'
        age=dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(report['checked_at'])
        assert age.total_seconds()<48*3600,'Discovery report is stale'
    print(f"Validated {len(events)} races"+(' and live discovery health' if live else ''))
    return True

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args();validate(live=args.live)
