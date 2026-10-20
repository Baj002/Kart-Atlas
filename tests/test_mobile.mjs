import assert from 'node:assert/strict';
import {readFile,access} from 'node:fs/promises';
import {notificationPlan} from '../mobile/reminder-plan.mjs';
const now=Date.parse('2026-10-20T12:00:00Z');
const event={id:'new',alias_ids:['old'],name:'Example Cup',registration_evidence:'https://example.com',registration_deadline:'2026-10-22T12:00:00Z'};
const options={enabled:true,hours:24};
const plan=notificationPlan([event],['old'],options,now);assert.equal(plan.length,2);assert.equal(plan[0].schedule.at.toISOString(),'2026-10-21T12:00:00.000Z');
assert(plan.every(n=>n.extra.kartAtlas&&n.id>0&&!n.isExactNotification));
assert.equal(notificationPlan([event],[],options,now).length,0);
assert.equal(notificationPlan([{...event,end:'2026-10-01'}],['old'],options,now).length,0);
assert.equal(notificationPlan([event],['old'],{...options,enabled:false},now).length,0);
assert.equal(notificationPlan([event],['old'],{...options,muted:['old']},now).length,0);
assert.equal(notificationPlan([{...event,status:'cancelled'}],['old'],options,now).length,0);
assert.equal(notificationPlan([{...event,registration_deadline:'2026-10-21'}],['old'],options,now).length,0);
assert.equal(notificationPlan([{...event,registration_deadline:'2026-10-19T12:00:00Z'}],['old'],options,now).length,0);
assert.notDeepEqual(notificationPlan([{...event,registration_deadline:'2026-10-23T12:00:00Z'}],['old'],options,now).map(n=>n.id),plan.map(n=>n.id));
const many=Array.from({length:100},(_,i)=>({...event,id:'race-'+i,alias_ids:[]}));
const limited=notificationPlan(many,many.map(e=>e.id),options,now);assert.equal(limited.length,60);assert.equal(new Set(limited.map(n=>n.id)).size,60);
for(const name of ['index.html','clubs.html']){
 const html=await readFile('dist/mobile/'+name,'utf8');assert(html.includes('/native.js'));assert(html.indexOf('/native.js')<html.indexOf(name==='index.html'?'/app.js':'/clubs.js'));assert(!html.includes('unpkg.com'));assert(html.includes('Content-Security-Policy'));
}
await access('dist/mobile/vendor/leaflet.js');await access('dist/mobile/events.json');
try{await access('dist/mobile/coverage.json');assert.fail('Internal coverage must not ship');}catch(error){assert.equal(error.code,'ENOENT');}
const config=JSON.parse(await readFile('capacitor.config.json','utf8'));assert.equal(config.server.url,undefined,'Native app loads bundled code, not a remote website');
assert.equal(config.webDir,'dist/mobile');
console.log('Mobile asset packaging and native reminder lifecycle tests passed.');
