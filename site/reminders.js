/* Deadline alerts use local saved races. Calendar files carry background alarms. */
(function(root){
 'use strict';
 const instant=value=>typeof value==='string'&&/T.*(?:Z|[+-]\d{2}:?\d{2})$/.test(value)&&Number.isFinite(Date.parse(value))?Date.parse(value):null;
 const escape=value=>String(value||'').replace(/\\/g,'\\\\').replace(/\r/g,'').replace(/\n/g,'\\n').replace(/;/g,'\\;').replace(/,/g,'\\,');
 const stamp=value=>new Date(value).toISOString().replace(/[-:]/g,'').replace(/\.\d{3}Z$/,'Z');
 const savedEvent=(event,saved)=>[event.id,...(event.alias_ids||[])].some(id=>saved.has(id));
 function entries(events,saved,options={},now=Date.now()){
  const hours=[1,24,72,168].includes(Number(options.hours))?Number(options.hours):24;
  const muted=new Set(options.muted||[]);
  return events.filter(e=>savedEvent(e,saved)).map(event=>{
   const deadline=instant(event.registration_deadline);
   const disabled=muted.has(event.id)||(event.alias_ids||[]).some(id=>muted.has(id));
   const date=new Date(now),day=[date.getFullYear(),String(date.getMonth()+1).padStart(2,'0'),String(date.getDate()).padStart(2,'0')].join('-');
   const ended=event.end&&event.end<day;
   const stopped=ended||['cancelled','postponed'].includes(event.status)||['closed','sold_out'].includes(event.registration_status);
   const known=deadline!==null&&Boolean(event.registration_evidence);
   const active=known&&!disabled&&!stopped&&deadline>now;
   const due=active&&deadline-now<=hours*3600000;
   return {event,deadline,active,due,disabled,subscriptionAllowed:!disabled&&!stopped&&(!known||deadline>now),key:event.id+'|'+deadline+'|'+hours,
    message:disabled?'Reminder off':stopped?'Registration unavailable':!known?'Waiting for a verified deadline':deadline<=now?'Deadline passed':due?'Registration deadline approaching':'Reminder ready',hours};
  }).sort((a,b)=>(a.deadline??Infinity)-(b.deadline??Infinity));
 }
 function fold(line){
  const encoder=new TextEncoder();let chunk='',lines=[];
  for(const character of line){if(encoder.encode(chunk+character).length>75){lines.push(chunk);chunk=' '+character;}else chunk+=character;}
  return [...lines,chunk].join('\r\n');
 }
 function calendar(rows,now=Date.now()){
  const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Kart Atlas//Saved Race Reminders//EN','CALSCALE:GREGORIAN','X-WR-CALNAME:Kart Atlas registration reminders'];
  for(const item of rows.filter(r=>r.active&&r.deadline>now)){
   const e=item.event,url=root.KartRegistration.registrationInfo(e,new Date(now)).url;
   lines.push('BEGIN:VEVENT','UID:registration-'+escape(e.id)+'@kartatlas.local','DTSTAMP:'+stamp(now),'DTSTART:'+stamp(item.deadline),'DTEND:'+stamp(item.deadline+300000),'TRANSP:TRANSPARENT','STATUS:CONFIRMED','SUMMARY:'+escape('Registration deadline: '+e.name),'DESCRIPTION:'+escape('Confirm entry availability with the organizer. This downloaded calendar is a snapshot; replace it if the deadline changes. '+(url||'')));
   if(url)lines.push('URL:'+url);
   // Skip alarms whose chosen lead time already passed; retain a deadline alarm.
   const offsets=[item.hours*3600000,0].filter(offset=>item.deadline-offset>now);
   for(const offset of offsets)lines.push('BEGIN:VALARM','ACTION:DISPLAY','TRIGGER:'+(offset?'-PT'+offset/3600000+'H':'PT0S'),'DESCRIPTION:'+escape('Registration deadline: '+e.name),'END:VALARM');
   lines.push('END:VEVENT');
  }
  return [...lines,'END:VCALENDAR'].map(fold).join('\r\n')+'\r\n';
 }
 root.KartReminders={entries,calendar,savedEvent};
 if(typeof module!=='undefined'&&module.exports)module.exports=root.KartReminders;
})(typeof globalThis!=='undefined'?globalThis:this);
