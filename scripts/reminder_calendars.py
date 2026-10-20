"""Publish stable calendar subscriptions for verified registration deadlines."""
import datetime as dt
import json
from pathlib import Path
from scripts.registration import instant


def escape(value):
    return str(value or '').replace('\\','\\\\').replace('\n','\\n').replace(';','\\;').replace(',','\\,').replace('\r','')


def fold(line):
    # RFC 5545 limits content lines to 75 octets; never split a UTF-8 character.
    lines=[];chunk=''
    for character in line:
        if len((chunk+character).encode())>75:lines.append(chunk);chunk=' '+character
        else:chunk+=character
    return '\r\n'.join(lines+[chunk])


def calendar(event,deadline,now,cancelled=False):
    stamp=lambda value:value.astimezone(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Kart Atlas//Registration Reminders//EN','CALSCALE:GREGORIAN',
           'X-WR-CALNAME:'+escape('Kart Atlas: '+event['name']), 'BEGIN:VEVENT',
           'UID:registration-'+escape(event['id'])+'@kartatlas.local','DTSTAMP:'+stamp(now),'LAST-MODIFIED:'+stamp(now),'SEQUENCE:'+str(event.get('sequence',0)),
           'DTSTART:'+stamp(deadline),'DTEND:'+stamp(deadline+dt.timedelta(minutes=5)),
           'SUMMARY:'+escape('Registration deadline: '+event['name']),'TRANSP:TRANSPARENT',
           'STATUS:'+('CANCELLED' if cancelled else 'CONFIRMED'),
           'DESCRIPTION:'+escape('Published online registration deadline. Confirm entry availability, class capacity and late-entry rules with the organizer. Calendar refresh and alert delivery depend on your calendar app. '+(event.get('registration_url') or event['source']))]
    url=event.get('registration_url') or event['source']
    if url.startswith(('https://','http://')) and not any(c.isspace() for c in url):lines.append('URL:'+url)
    if not cancelled:
        for trigger in ('-P1D','-PT1H','PT0S'):
            lines.extend(['BEGIN:VALARM','ACTION:DISPLAY','TRIGGER:'+trigger,'DESCRIPTION:'+escape('Registration deadline: '+event['name']),'END:VALARM'])
    return '\r\n'.join(fold(line) for line in lines+['END:VEVENT','END:VCALENDAR'])+'\r\n'


def build(root,events,now=None):
    now=now or dt.datetime.now(dt.timezone.utc)
    path=root/'data/reminder_state.json';previous=json.loads(path.read_text()).get('events',{}) if path.exists() else {}
    state=dict(previous);directory=root/'site/reminders';directory.mkdir(parents=True,exist_ok=True)
    current={e['id']:e for e in events}
    aliases={alias:e for e in events for alias in e.get('alias_ids',[])}
    for event in events:
        deadline=instant(event.get('registration_deadline'))
        if deadline and event.get('registration_evidence'):
            state[event['id']]={k:event.get(k,'') for k in ('id','name','source','registration_url','registration_deadline')}
        elif event.get('end','')>=now.date().isoformat() and event['id'] not in state:
            state[event['id']]={k:event.get(k,'') for k in ('id','name','source','registration_url','registration_deadline')}
    for ident,record in state.items():
        event=current.get(ident) or aliases.get(ident)
        old=previous.get(ident,{})
        if event and instant(event.get('registration_deadline')):
            record={k:event.get(k,'') for k in ('name','source','registration_url','registration_deadline')}
            record['id']=ident
        deadline=instant(record['registration_deadline'])
        cancelled=not event or event.get('status') in ('cancelled','postponed') or event.get('registration_status') in ('closed','sold_out') or not instant(event.get('registration_deadline'))
        changed=any(record.get(k)!=old.get(k) for k in ('name','registration_url','registration_deadline')) or cancelled!=old.get('cancelled',False)
        record['sequence']=old.get('sequence',0)+int(changed)
        record['cancelled']=cancelled;state[ident]=record
        content=calendar(record,deadline,now,cancelled) if deadline else '\r\n'.join(['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Kart Atlas//Registration Reminders//EN','CALSCALE:GREGORIAN',fold('X-WR-CALNAME:'+escape('Kart Atlas: '+record['name'])),'END:VCALENDAR',''])
        (directory/(ident+'.ics')).write_text(content,newline='')
        if event:
            if ident==event['id']:event['registration_reminder_url']='/reminders/'+ident+'.ics'
    path.write_text(json.dumps({'events':state},indent=2,ensure_ascii=False)+'\n')
