"""Internal Canadian 2027 race coverage audit; never equates missing dates with an unpublished season.

Generated only from published repository evidence. No unverified event dates are invented.
"""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
from scripts.check_sources import ROOT


def build(root=ROOT, today=None):
    today = today or dt.datetime.now(dt.timezone.utc).date()
    regions = json.loads((root / 'data/regions.json').read_text())['Canada']
    events = json.loads((root / 'site/events.json').read_text())['events']
    sources = json.loads((root / 'data/monitor_sources.json').read_text())['sources']
    organizers = json.loads((root / 'data/organizers.json').read_text())['organizers']
    discovery_path = root / 'reports/discovery.json'
    discovery = json.loads(discovery_path.read_text()) if discovery_path.exists() else {}
    observed = {s['source_id']: s for s in discovery.get('sources', [])}
    canadian_events = [e for e in events if e.get('country') == 'Canada' and str(e.get('start', '')).startswith('2027')]
    rows = []
    for code, name in regions.items():
        regional_sources = [s for s in sources if s.get('country') == 'Canada' and s.get('region') == code]
        reached = [s for s in regional_sources if observed.get(s['id'], {}).get('pages')]
        local = [e for e in canadian_events if e.get('region') == code]
        official = [e for e in local if e.get('verification') == 'Official']
        automated = [e for e in local if e.get('verification') == 'Automated']
        other = [e for e in local if e.get('verification') not in ('Official', 'Automated')]
        reviewed = [o for o in organizers if o.get('country') == 'Canada'
                    and o.get('region') == code and o.get('scope_status') == 'eligible']
        leads = [o for o in organizers if o.get('country') == 'Canada'
                 and o.get('region') == code and o.get('scope_status') == 'needs_review']
        declarations = []
        for o in reviewed:
            for d in o.get('season_declarations', []):
                if d.get('year') == 2027:
                    declarations.append({'organizer': o['name'], **d})
        current_not_announced = [d for d in declarations if d.get('status') == 'not_announced'
                                 and (today - dt.date.fromisoformat(d['reviewed_on'])).days <= 7]
        if official or automated:
            state = 'organizer_dates_indexed'
        elif other:
            state = 'secondary_dates_only'
        elif not regional_sources:
            state = 'no_monitored_source'
        elif not discovery.get('checked_at'):
            state = 'scan_not_available'
        elif not reached:
            state = 'monitored_sources_unreachable'
        else:
            state = 'no_2027_dates_verified'
        rows.append({
            'region': code, 'name': name, 'state': state,
            'monitored_sources': len(regional_sources), 'sources_reached': len(reached),
            'reviewed_competition_organizers': len(reviewed), 'unverified_organizer_leads': len(leads),
            'official_2027_events': len(official), 'automated_2027_events': len(automated),
            'secondary_2027_events': len(other),
            'explicit_not_announced_organizers': current_not_announced,
            'events': [{'name': e['name'], 'start': e['start'], 'end': e['end'],
                        'verification': e.get('verification'), 'source': e['source']} for e in local]
        })
    unknown = [e for e in canadian_events if e.get('region') not in regions]
    report = {
        'as_of': today.isoformat(), 'scan_checked_at': discovery.get('checked_at'),
        'season': 2027, 'scope': 'Canadian competitive circuit karting',
        'interpretation': ('No verified 2027 race in a region does NOT establish that the organizer '
                           'has not published a schedule. Only a dated, explicit organizer statement '
                           'can establish not-announced status, and it becomes stale after seven days.'),
        'complete': False,
        'regions_checked': len(rows),
        'regions_with_official_or_automated_dates': sum(bool(r['official_2027_events'] or r['automated_2027_events']) for r in rows),
        'regions_with_only_secondary_dates': sum(r['state'] == 'secondary_dates_only' for r in rows),
        'regions_without_monitored_sources': [r['region'] for r in rows if not r['monitored_sources']],
        'regions_with_unreachable_sources': [r['region'] for r in rows if r['state'] == 'monitored_sources_unreachable'],
        'unresolved_region_events': [{'name': e['name'], 'region': e.get('region'), 'source': e['source']} for e in unknown],
        'regions': rows
    }
    out = root / 'reports/canada_2027.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print('Canadian 2027 coverage:', report['regions_checked'], 'regions audited;',
          report['regions_with_official_or_automated_dates'], 'with verified organizer dates')
    return report


if __name__ == '__main__':
    build()
