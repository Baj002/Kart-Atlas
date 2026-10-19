"""Coverage priorities and date discrepancies; unknown coverage never means no races."""
import re
from scripts.discovery_engine import REGIONS,region_code

def regional_coverage(races,clubs,sources,today):
    output=[]
    for country,regions in REGIONS.items():
        for code,name in regions.items():
            active=[e for e in races if e['country']==country and region_code(e['region'],country)==code and e['end']>=str(today) and e.get('status') not in ('cancelled','postponed')]
            leads=[c for c in clubs if c['country']==country and region_code(c['region'],country)==code]
            local=[s for s in sources if s['trusted'] and s.get('country')==country and region_code(s.get('region',''),country)==code]
            output.append({'country':country,'region':code,'name':name,'upcoming_races':len(active),
                'directory_leads':len(leads),'organizer_sources':len(local),'organizer_sources_reached':sum(bool(s['pages']) for s in local)})
    return output

def date_conflicts(races,candidates):
    def name(value):return re.sub(r'[^a-z0-9]','',re.sub(r'^20\d{2}\s+','',value).casefold())
    conflicts=[];seen=set()
    for candidate in candidates:
        for race in races:
            if candidate['country']!=race['country'] or candidate['region']!=race['region']:continue
            if candidate['organizer'].casefold()!=race['organizer'].casefold():continue
            if name(candidate['name'])!=name(race['name']):continue
            if (candidate['start'],candidate['end'])==(race['start'],race['end']):continue
            key=(race['id'],candidate['source'],candidate['start'],candidate['end'])
            if key in seen:continue
            seen.add(key);conflicts.append({'id':race['id'],'name':race['name'],'published_start':race['start'],
                'published_end':race['end'],'observed_start':candidate['start'],'observed_end':candidate['end'],
                'published_source':race['source'],'observed_source':candidate['source'],
                'note':'Date windows differ. Verify event activities and race dates before changing the listing.'})
    return conflicts
