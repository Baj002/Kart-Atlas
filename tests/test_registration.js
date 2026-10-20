const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {registrationInfo:info}=require('../site/registration.js');
const now=new Date('2026-10-20T12:00:00Z');
const known={end:'2026-11-20',registration_url:'https://entry.example/race',registration_status:'open',registration_checked_at:now.toISOString(),registration_evidence:'https://organizer.example/race'};
assert.equal(info({},now).label,'Not announced');
assert.equal(info({registration_url:known.registration_url},now).label,'Check status','A link is not evidence of availability');
assert.equal(info(known,now).label,'Open');
assert.equal(info({...known,registration_deadline:'2026-10-27T12:00:00Z'},now).label,'Closing soon');
assert.equal(info({...known,registration_deadline:'2026-10-27T12:00:01Z'},now).label,'Open');
assert.equal(info({...known,registration_deadline:now.toISOString()},now).label,'Deadline passed');
assert.equal(info({...known,registration_status:'sold_out'},now).label,'Sold out');
assert.equal(info({...known,registration_status:'closed'},now).label,'Closed');
assert.equal(info({...known,registration_opens_at:'2026-10-25T09:00:00-06:00'},now).label,'Opens soon');
assert.equal(info({...known,status:'cancelled'},now).label,'Event cancelled');
assert.equal(info({...known,status:'postponed'},now).label,'Event postponed');
assert.equal(info({...known,end:'2026-10-01'},now).label,'Event ended');
assert.equal(info({...known,registration_checked_at:'2026-10-17T12:00:00Z'},now).label,'Check status','Cached open statuses expire after 48 hours');
assert.equal(info({...known,registration_checked_at:'2026-10-21T12:00:00Z'},now).label,'Check status','A future check timestamp is not trusted');
assert.equal(info({...known,registration_evidence:undefined},now).label,'Check status');
assert.equal(info({...known,registration_deadline:'2026-10-20'},now).deadline,null,'No timezone is invented for date-only deadlines');
assert.equal(info({...known,registration_deadline:'garbage'},now).deadline,null);
assert.equal(info({registration_url:'javascript:alert(1)'},now).url,null);
assert.equal(info({registration_url:'https://user:password@example.com'},now).url,null);
assert.equal(info({...known,registration_deadline:'2026-10-20T07:00:00-06:00'},now).status,'closing_soon','Offset dates compare as instants');
// Exercise the actual card renderer with a small DOM; verify visible status,
// deadline and direct entry action are present without requiring Leaflet.
class Node{constructor(type,cls='',text=''){this.type=type;this.className=cls;this.textContent=text;this.children=[];}append(...nodes){this.children.push(...nodes);}setAttribute(key,value){this[key]=value;}}
const source=fs.readFileSync('site/app.js','utf8');
const block=source.slice(source.indexOf('  function makeCard('),source.indexOf('  function icsEscape('));
const makeCard=vm.runInNewContext(block+'\nmakeCard',{
 el:(type,cls,text)=>new Node(type,cls,text),ymd:s=>new Date(s+'T12:00:00'),monthNames:['Jan'],makeTag:(text,cls)=>new Node('span',cls,text),registrationInfo:e=>info(e,now),isSaved:()=>false,addButton:()=>new Node('button'),safeURL:u=>/^https:\/\//.test(u),fmtRange:()=>'',
});
const card=makeCard({...known,id:'race',start:'2026-11-20',name:'Example Cup',registration_deadline:'2026-10-25T12:00:00Z'});
function flatten(node){return [node,...node.children.flatMap(flatten)];}
assert(flatten(card).some(n=>n.textContent==='Registration: Closing soon'));
assert(flatten(card).some(n=>n.className==='registration-deadline'&&n.textContent.startsWith('Deadline: ')));
assert(flatten(card).some(n=>n.type==='a'&&n.href===known.registration_url&&n.textContent==='Register ↗'));
const index=fs.readFileSync('site/index.html','utf8');
assert(index.indexOf('/registration.js')<index.indexOf('/app.js'),'Registration logic loads before app');
assert(fs.readFileSync('site/sw.js','utf8').includes('/registration.js?v=1'),'Registration logic is available offline');
console.log('Registration states, timezone boundaries, stale data, safe links, cards and offline loading passed.');
