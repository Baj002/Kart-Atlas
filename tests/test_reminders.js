const assert=require('node:assert/strict');
const fs=require('node:fs');
require('../site/registration.js');
const {entries,calendar}=require('../site/reminders.js');
const now=Date.parse('2026-10-20T12:00:00Z');
const event={id:'canonical',alias_ids:['old'],name:'Race, with; unicode 🏁',end:'2026-11-05',registration_deadline:'2026-10-21T12:00:00Z',registration_evidence:'https://organizer.example/race',registration_url:'https://register.example/race'};
let rows=entries([event],new Set(['old']),{hours:24},now);
assert.equal(rows.length,1);assert(rows[0].active&&rows[0].due,'Saved aliases receive reminders');
assert.equal(entries([event],new Set(),{},now).length,0,'Unsave removes in-app reminders and exports');
assert.equal(entries([event],new Set(['old']),{muted:['canonical']},now)[0].active,false);
assert.equal(entries([event],new Set(['old']),{muted:['old']},now)[0].active,false);
for(const status of ['cancelled','postponed'])assert.equal(entries([{...event,status}],new Set(['old']),{},now)[0].active,false);
for(const status of ['closed','sold_out'])assert.equal(entries([{...event,registration_status:status}],new Set(['old']),{},now)[0].active,false);
assert.equal(entries([{...event,end:'2026-10-01'}],new Set(['old']),{},now)[0].active,false);
assert.equal(entries([{...event,registration_deadline:'2026-10-19T12:00:00Z'}],new Set(['old']),{},now)[0].active,false);
assert.equal(entries([{...event,registration_deadline:'2026-10-21'}],new Set(['old']),{},now)[0].active,false);
assert.equal(entries([{...event,registration_evidence:''}],new Set(['old']),{},now)[0].message,'Waiting for a verified deadline');
const changed=entries([{...event,registration_deadline:'2026-10-22T12:00:00Z'}],new Set(['old']),{},now)[0];
assert.notEqual(changed.key,rows[0].key);assert.equal(changed.due,false,'A moved deadline replaces the old reminder');
let ics=calendar(rows,now-1000);
assert(ics.includes('DTSTART:20261021T120000Z'));
assert(ics.includes('TRIGGER:-PT24H'));assert(ics.includes('TRIGGER:PT0S'));
assert(ics.includes('Race\\, with\\; unicode 🏁'));
assert(!ics.replace(/\r\n/g,'').includes('\n'),'Calendar uses CRLF line endings');
assert(ics.split('\r\n').every(line=>Buffer.byteLength(line)<=75));
const near=entries([{...event,registration_deadline:'2026-10-20T13:00:00Z'}],new Set(['old']),{hours:24},now);
ics=calendar(near,now);assert(!ics.includes('-PT24H'),'Past alarm triggers are omitted');assert(ics.includes('TRIGGER:PT0S'));
assert(!calendar(entries([event],new Set(['old']),{muted:['old']},now),now).includes('BEGIN:VEVENT'));
const dangerous=entries([{...event,name:'Test\nBEGIN:VEVENT',registration_url:'javascript:alert(1)'}],new Set(['old']),{},now);
ics=calendar(dangerous,now);assert(!ics.includes('URL:javascript:'));assert(!ics.includes('\r\nBEGIN:VEVENT\r\nBEGIN:VEVENT'));
const app=fs.readFileSync('site/app.js','utf8'),index=fs.readFileSync('site/index.html','utf8'),sw=fs.readFileSync('site/sw.js','utf8');
assert(index.indexOf('/reminders.js')<index.indexOf('/app.js'));
assert(sw.includes('/reminders.js?v=1'));
assert(app.includes('In-app reminders appear when Kart Atlas is open.'));
assert(app.includes('reminderSettings.enabled=enabled.checked'));
console.log('Saved deadline reminders: aliases, opt-outs, cancellations, rescheduling, UTC alarms, calendar safety and offline loading passed.');
// Exercise the real reminder dialog, not just the deadline model.
const vm=require('node:vm');
class Node{constructor(type,cls='',text=''){this.type=type;this.tagName=type;this.className=cls;this.textContent=text;this.children=[];}append(...items){this.children.push(...items);}setAttribute(k,v){this[k]=v;}addEventListener(){}showModal(){this.open=true;}remove(){}close(){this.open=false;}}
const body=new Node('body'),settings={enabled:false,hours:24,muted:[]};let writes=0;
const dialogBlock=app.slice(app.indexOf('  function showReminders(){'),app.indexOf('  function getFilters()'));
const show=vm.runInNewContext(dialogBlock+'\nshowReminders',{
 $:()=>null,el:(type,cls,text)=>new Node(type,cls,text),document:{body},location:{protocol:'https:',host:'kart.example'},Option:function(text,value){return {text,value};},
 reminderSettings:settings,persistReminders:()=>writes++,renderReminderSummary:()=>{},registrationInfo:e=>global.KartRegistration.registrationInfo(e,new Date(now)),
 reminderRows:()=>entries([{...event,registration_reminder_url:'/reminders/canonical.ics'}],new Set(['old']),settings,now),KartReminders:global.KartReminders,
});
show();
const flatten=n=>[n,...(n.children||[]).flatMap(flatten)];
const nodes=flatten(body),dialog=nodes.find(n=>n.type==='dialog');assert(dialog.open);
const checkboxes=nodes.filter(n=>n.tagName==='input');
const globalToggle=checkboxes[0];globalToggle.checked=true;globalToggle.onchange();assert(settings.enabled);assert(writes>0);
const select=nodes.find(n=>n.type==='select');select.value='72';select.onchange();assert.equal(settings.hours,72);
const raceToggle=checkboxes[1];raceToggle.checked=false;raceToggle.onchange();assert.deepEqual(settings.muted,['canonical']);
assert(nodes.some(n=>n.href==='webcal://kart.example/reminders/canonical.ics'));
assert(nodes.some(n=>n.type==='button'&&n.textContent.includes('Add saved deadlines')&&n.disabled),'Opting out disables the calendar export');
console.log('Real reminder dialog: persisted enablement, lead time, per-race opt-out and subscription links passed.');
