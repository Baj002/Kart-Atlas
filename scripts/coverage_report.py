"""Measured scan coverage, explicitly distinct from unknowable total event recall."""
import datetime as dt
import json
from scripts.check_sources import ROOT
from scripts.discovery_engine import dump, host, REGIONS
from scripts.coverage_audit import regional_coverage,date_conflicts

def build(root=ROOT,today=None):
    today=today or dt.datetime.now(dt.timezone.utc).date()
    report=json.loads((root/'reports/discovery.json').read_text())
    races=json.loads((root/'site/events.json').read_text())['events']
    clubs=json.loads((root/'data/clubs.json').read_text())['clubs']
    sources=report.get('sources',[])
    monitors=json.loads((root/'data/monitor_sources.json').read_text())['sources']
    countries={}
    for country in ('Canada','USA','Mexico'):
        local=[s for s in sources if s.get('country')==country]
        future=[e for e in races if e['country']==country and e['end']>=str(today) and e.get('status') not in ('cancelled','postponed')]
        countries[country]={'sources_attempted':len(local),'sources_reached':sum(bool(s['pages']) for s in local),
            'trusted_sources':sum(s['trusted'] for s in local),'future_races':len(future),
            'regions_with_races':sorted({e['region'] for e in future if e['region'] in REGIONS[country]}),'unresolved_region_races':sum(e['region'] not in REGIONS[country] for e in future),'directory_leads':sum(c['country']==country for c in clubs)}
    def club_monitored(club):
        for source in sources:
            if not source['trusted'] or host(source['url'])!=host(club['schedule_url']):continue
            if source['club'].casefold()==club['name'].casefold():return True
            metadata=next((m for m in monitors if m['id']==source['source_id']),{})
            if metadata.get('city')==club['city'] and metadata.get('region')==club['region']:return True
        return False
    unmonitored=[{'id':c['id'],'club':c['name'],'region':c['region'],'country':c['country'],'url':c['schedule_url']}
        for c in clubs if not club_monitored(c)]
    reached=sum(bool(s['pages']) for s in sources);attempted=len(sources)
    adapters={}
    for source in sources:
        for page in source['pages']:
            kind=page['parser'];entry=adapters.setdefault(kind,{'responses':0,'race_observations':0,'review_notices':0})
            entry['responses']+=1;entry['race_observations']+=page['events'];entry['review_notices']+=bool(page.get('notice'))
    regions=regional_coverage(races,clubs,sources,today)
    conflicts=date_conflicts(races,report['event_candidates'])
    payload={'date_conflicts':conflicts,'by_region':regions,'regional_gaps':[r for r in regions if r['directory_leads'] and not r['upcoming_races']],
        'adapters':adapters,'excluded_asset_leads':len(report.get('rejected_organizer_leads',[])),'generated_at':report['checked_at'],'scope':'Canada, USA, Mexico',
        'coverage_note':'Source reach measures this scan only. Directory leads are not a census of active clubs; race recall is unknown.',
        'sources_attempted':attempted,'sources_reached':reached,'unique_hosts_attempted':len({host(s['url']) for s in sources}),'unique_hosts_reached':len({host(s['url']) for s in sources if s['pages']}),
        'source_reach_percent':round(100*reached/attempted,1) if attempted else 0,
        'trusted_sources_reached':sum(s['trusted'] and bool(s['pages']) for s in sources),
        'pages_reached':sum(len(s['pages']) for s in sources),'errors':len(report['errors']),
        'changed_pages':report.get('content_changes',[]),'event_candidates':len(report['event_candidates']),'organizer_leads':len(report['organizer_source_candidates']),
        'deferred_links':sum(s['remaining_links'] for s in sources),
        'future_races':sum(x['future_races'] for x in countries.values()),'by_country':countries,
        'unmonitored_clubs':unmonitored,'sources':sources}
    dump(root/'reports/coverage.json',payload);dump(root/'site/coverage.json',payload)
    dump(root/'site/monitor_status.json',{'last_attempt':report['checked_at'],'checked':reached,'total':attempted,
        'feed_additions':sum(c.get('new',False) for c in report['changes']),'errors':len(report['errors']),'is_complete':False,
        'future_races':payload['future_races'],'trusted_sources_reached':payload['trusted_sources_reached']})
    print(f"Coverage: reached {reached}/{attempted} sources; {payload['future_races']} upcoming indexed races")
    return payload

if __name__=='__main__':build()
