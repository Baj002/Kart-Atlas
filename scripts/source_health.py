"""Persist scan health independently of website reach and race retention."""
import re


def update_health(results,previous,known_events,today,now,key=lambda e:e.get('uid') or e.get('id')):
    states=dict(previous);alerts=[]
    known_by_key={key(e):e for e in known_events}
    for result in results:
        source_id=result['source_id'];old=states.get(source_id,{})
        observed={key(e):e for e in result.get('events',[]) if e.get('end','')>=str(today)}
        baseline=old.get('last_observed_events') or [
            {'key':key(e),'end':e['end']} for e in known_events if e.get('feed_id')==source_id and e.get('status','scheduled')=='scheduled']
        expected={e['key'] for e in baseline if e['end']>=str(today)}
        reached=bool(result['pages']);failures=0 if reached else old.get('consecutive_failures',0)+1
        represented=set(observed)
        for expected_key in expected-represented:
            old_event=known_by_key.get(expected_key,{})
            # A specific numbered round may be listed both on a series page
            # and a detail page. Losing one representation is not losing a race.
            if re.search(r'\b(?:round\s*\d|race\s*#\s*\d)',old_event.get('name',''),re.I):
                fields=('name','start','end','venue')
                if all(old_event.get(f) for f in fields) and any(all(str(old_event[f]).casefold()==str(e.get(f,'')).casefold() for f in fields) for e in observed.values()):represented.add(expected_key)
        missing=sorted(str(k) for k in expected-represented)
        status='healthy' if observed else 'reachable_no_supported_events'
        kinds=[]
        if not reached:status='unreachable';kinds.append('fetch_failure')
        elif expected and not observed:status='unexpected_empty';kinds.append('unexpected_empty')
        elif expected and len(missing)>=max(1,len(expected)/2):status='observation_drop';kinds.append('observation_drop')
        if result.get('errors') and reached:kinds.append('partial_fetch_failure')
        if any(p.get('notice') for p in result['pages']):kinds.append('parser_review_required')
        state=dict(old,source_id=source_id,last_attempt=now,status=status,
            consecutive_failures=failures,observed_events=len(observed),expected_events=len(expected),
            missing_event_keys=missing,last_errors=result.get('errors',[])[:5])
        if reached:state['last_success']=now
        # Empty pages and fetch failures never replace the last known event set.
        # Explicit cancellations still count as observations and are not missing.
        if observed:
            remembered={e['key']:e for e in baseline if e['end']>=str(today)}
            for k,e in observed.items():
                if e.get('status','scheduled')=='scheduled':remembered[k]={'key':k,'end':e['end']}
                else:remembered.pop(k,None)
            state['last_observed_events']=list(remembered.values())
            state['last_nonzero_at']=now
        state['history']=(old.get('history',[])+[{'at':now,'status':status,'events':len(observed),'reached':reached}])[-20:]
        states[source_id]=state
        for kind in kinds:alerts.append({'source_id':source_id,'club':result['club'],'url':result['url'],
            'trusted':bool(result.get('trusted')),
            'kind':kind,'consecutive_failures':failures,'expected_events':len(expected),
            'observed_events':len(observed),'missing_event_keys':missing,
            'action':'Review source or parser; retained races are not cancelled by absence.'})
    return states,alerts
