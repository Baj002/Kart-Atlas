"""Internal organizer/season registry audit; no guessed complete-season claims."""
import datetime as dt
import json
import re
from collections import Counter
from scripts.racing_scope import source_scope_reason,load_policy


def name_key(value):return re.sub(r'\W','',str(value).casefold())


def audit(organizers,monitors,results,health,races,candidates,today,now,policy=None):
    configured={s['id']:s for s in monitors};scanned={s['source_id']:s for s in results}
    rows=[];unmatched=[];matched=set()
    def fresh(event):
        value=event.get('last_verified')
        if not value:return False
        try:
            moment=dt.datetime.fromisoformat(value)
            if moment.tzinfo is None:moment=moment.replace(tzinfo=dt.timezone.utc)
            return 0<=(dt.datetime.fromisoformat(now)-moment).total_seconds()<=48*3600
        except (TypeError,ValueError):return False
    for organizer in organizers:
        aliases={name_key(n) for n in [organizer['name']]+organizer.get('aliases',[])}
        local=[e for e in races if name_key(e['organizer']) in aliases]
        matched.update(e['id'] for e in local)
        review=[e for e in candidates if name_key(e['organizer']) in aliases]
        ids=[sid for sid in organizer.get('source_ids',[]) if sid in configured and configured[sid].get('source_kind')!='document_reference' and not source_scope_reason(configured[sid],policy)]
        reached=[sid for sid in ids if scanned.get(sid,{}).get('pages')]
        unhealthy=[sid for sid in ids if health.get(sid,{}).get('status') in ('unreachable','unexpected_empty','observation_drop')]
        stale=[]
        for sid in ids:
            success=health.get(sid,{}).get('last_success')
            if success and (dt.datetime.fromisoformat(now)-dt.datetime.fromisoformat(success)).total_seconds()>48*3600:stale.append(sid)
        seasons=[]
        for year in (today.year,today.year+1):
            events=[e for e in local if e['start'].startswith(str(year))]
            upcoming=[e for e in events if e['end']>=str(today) and e.get('status','scheduled')=='scheduled']
            declaration=next((d for d in organizer.get('season_declarations',[]) if d['year']==year),None)
            if organizer.get('scope_status')=='excluded':status='outside_scope'
            elif upcoming:status='indexed_future_events'
            elif declaration:
                stale_declaration=declaration['status']=='not_announced' and (today-dt.date.fromisoformat(declaration['reviewed_on'])).days>7
                status='declaration_stale' if stale_declaration else declaration['status']
            elif events:status='past_events_only'
            elif review:status='review_required'
            elif not ids:status='no_source_configured'
            elif reached:status='no_dates_verified'
            else:status='source_unreachable'
            seasons.append({'year':year,'status':status,'indexed_events':len(events),'upcoming_events':len(upcoming),
                'recently_verified_upcoming':sum(fresh(e) for e in upcoming),
                'unconfirmed_future_event_ids':[e['id'] for e in upcoming if not fresh(e)],
                'declaration':declaration,'event_ids':[e['id'] for e in events]})
        rows.append({'organizer_id':organizer['id'],'name':organizer['name'],'country':organizer.get('country',''),
            'scope_status':organizer.get('scope_status','needs_review'),'source_ids':ids,'sources_reached':reached,
            'unhealthy_sources':unhealthy,'stale_sources':stale,'review_candidates':len(review),'seasons':seasons})
    unmatched=[{'id':e['id'],'organizer':e['organizer'],'source':e['source']} for e in races if e['id'] not in matched]
    scope=Counter(r['scope_status'] for r in rows)
    priorities=[]
    for row in rows:
        if row['scope_status']=='excluded':continue
        active=sum(s['upcoming_events'] for s in row['seasons'])
        if row['unhealthy_sources']:reason='source_health';priority=1 if active else 2
        elif not row['source_ids']:reason='source_not_configured';priority=2
        elif row['review_candidates']:reason='event_review';priority=2
        elif any(s['unconfirmed_future_event_ids'] for s in row['seasons']):reason='published_dates_need_reverification';priority=2
        elif row['scope_status']=='needs_review':reason='organizer_scope_review';priority=3
        elif any(s['status']=='no_dates_verified' for s in row['seasons']):reason='season_dates_not_verified';priority=3
        else:continue
        priorities.append({'organizer_id':row['organizer_id'],'name':row['name'],'priority':priority,'reason':reason,'upcoming_events':active})
    return {'generated_at':now,'scope':'Competition circuit karting; unknown classes are not excluded',
        'coverage_note':'Registry entries are research targets, not a census. No future dates does not establish season completion or non-announcement.',
        'summary':{'organizers':len(rows),'by_scope':dict(scope),'with_configured_sources':sum(bool(r['source_ids']) for r in rows),
            'with_reached_sources':sum(bool(r['sources_reached']) for r in rows),'with_health_issues':sum(bool(r['unhealthy_sources']) for r in rows),
            'unmatched_races':len(unmatched)},'organizers':rows,'priorities':sorted(priorities,key=lambda r:(r['priority'],-r['upcoming_events'],r['name'])),
        'unmatched_races':unmatched}


def build(root,report,races,today):
    path=root/'data/organizers.json'
    if not path.exists():return None
    organizers=json.loads(path.read_text())['organizers']
    monitors=json.loads((root/'data/monitor_sources.json').read_text())['sources']
    states={s['source_id']:s for s in report.get('source_health',[])}
    result=audit(organizers,monitors,report['sources'],states,races,report['event_candidates'],today,report['checked_at'],load_policy(root))
    (root/'reports/organizer_coverage.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    return result
