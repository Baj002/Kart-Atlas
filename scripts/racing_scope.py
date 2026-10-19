"""Competition circuit karting scope, shared by every publication path.

Missing engine/class information is not an exclusion. Track names such as
Road America and Langley Speedway are not event disciplines.
"""
import json
import re
from urllib.parse import urlsplit,unquote

TITLE_RULES=[
    ('oval_or_dirt',r'\b(?:oval|dirt|flat[ -]?kart|speedway racing)\b'),
    ('vintage',r'\b(?:vintage(?!\s+(?:cw|ccw|layout|configuration)\b)|historic kart)\b'),
    ('rental',r'\b(?:rentals?|concession kart|arrive[ -]?(?:and|&|n)[ -]?drive|mini indy|sodi world series|sws league)\b'),
    ('other_motorsport',r'\b(?:motorcycles?|mini[ -]?moto|supermoto|motocross|stock car|autocross|hpde|drag racing|drifting|sprint cars?|formula [1-4]|sim[ -]?racing|esports|iracing)\b'),
    ('long_circuit_road_racing',r'\broad[ -]?rac(?:e|es|ing)\b'),
]
OWNER_CLASSES=re.compile(r'\b(?:lo\s*206|briggs|rotax|rok|shifter|iame|ka\s*100|x30|micro swift|mini swift|kid kart|kart owners?|owner[ -]kart)\b',re.I)
RENTAL_DESCRIPTION=re.compile(r'\b(?:concession karts?|rental karts?|arrive[ -]?(?:and|&|n)[ -]?drive)\b',re.I)


def load_policy(root):
    path=root/'data/racing_scope.json'
    return json.loads(path.read_text()) if path.exists() else {}


def event_scope_reason(event,policy=None):
    policy=policy or {}
    if event.get('id') in policy.get('excluded_events',{}):return policy['excluded_events'][event['id']]['reason']
    def event_url(value):
        try:parsed=urlsplit(str(value or ''))
        except ValueError:return None
        if not re.search(r'/events?/',parsed.path,re.I):return None
        return (str(parsed.hostname or '').lower().removeprefix('www.'),unquote(parsed.path).rstrip('/'))
    urls={u for field in ('source','registration_url') if (u:=event_url(event.get(field)))}
    for exclusion in policy.get('excluded_events',{}).values():
        if event_url(exclusion.get('evidence')) in urls:return exclusion['reason']
    if event.get('feed_id') in policy.get('excluded_sources',{}):return policy['excluded_sources'][event['feed_id']]['reason']
    title=' '.join(str(event.get(k) or '') for k in ('name','format','organizer','classes'))
    for reason,pattern in TITLE_RULES:
        if re.search(pattern,title,re.I):return reason
    description=str(event.get('description') or '')
    # A mixed owner-kart championship can offer a rental class. Do not discard
    # its LO206/Rotax races; a rental-only event title is still excluded above.
    if RENTAL_DESCRIPTION.search(description) and not OWNER_CLASSES.search(title+' '+description):return 'rental'
    return None


def source_scope_reason(source,policy=None):
    policy=policy or {}
    if source.get('id') in policy.get('excluded_sources',{}):return policy['excluded_sources'][source['id']]['reason']
    if source.get('id') in policy.get('excluded_clubs',{}):return policy['excluded_clubs'][source['id']]['reason']
    url=source.get('url') or source.get('schedule_url','')
    for excluded in policy.get('excluded_sources',{}).values():
        if url and url.rstrip('/')==excluded.get('url','').rstrip('/'):return excluded['reason']
    reason=event_scope_reason({'name':source.get('name') or source.get('club',''),'format':source.get('format','')})
    if reason:return reason
    try:path=unquote(urlsplit(str(source.get('url') or source.get('schedule_url',''))).path)
    except ValueError:path=''
    if re.search(r'(?:/|[-_])(?:road-rac(?:ing|e)|vintage|dirt|oval|daytona-kartweek-road)(?:/|[-_]|$)',path,re.I):return 'excluded_discipline_source'
    return None


def apply_reviewed_override(event,policy):
    review=policy.get('event_overrides',{}).get(event['id'],{})
    override=review.get('fields',{})
    allowed={'name','start','end','format','source','notes','classes','registration_url','venue','city','region','country'}
    assert set(override)<=allowed,'Unsupported reviewed event override'
    result=dict(event,**override)
    if review.get('reviewed_on'):result['last_verified']=review['reviewed_on']
    return result
