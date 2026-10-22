import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {DatabaseSync} from 'node:sqlite';
import {createECDH,hkdfSync,createDecipheriv} from 'node:crypto';
import {api,scheduled,deliver,sendPush} from '../push/worker.mjs';
import {planReminders,normalizePreferences,validSubscription,hash} from '../push/plan.mjs';
const now=Date.now(),deadline=now+24*3600000-60000;
const event={id:'race',alias_ids:['old'],name:'Example race',registration_deadline:new Date(deadline).toISOString(),registration_evidence:'https://example.com/registration'};
const prefs={saved:['old'],hours:24};
assert.equal(planReminders([event],prefs,now-2*60000,now).length,2);
assert.equal(planReminders([event],prefs,now,now).length,1,'No backfill before opting in');
for(const changed of [{status:'cancelled'},{status:'postponed'},{registration_status:'sold_out'},{registration_status:'closed'},{registration_evidence:''},{registration_deadline:'2026-10-30'},{end:'2020-01-01'}])assert.equal(planReminders([{...event,...changed}],prefs,now-2*60000,now).length,0);
assert.equal(planReminders([event],{...prefs,saved:[]},0,now).length,0);
assert.throws(()=>normalizePreferences({saved:[],hours:2}));assert.throws(()=>normalizePreferences({saved:Array(301).fill('a'),hours:24}));
const receiver=createECDH('prime256v1');receiver.generateKeys();
const subscription={endpoint:'https://fcm.googleapis.com/fcm/send/example',keys:{p256dh:receiver.getPublicKey().toString('base64url'),auth:Buffer.alloc(16,4).toString('base64url')}};
assert(validSubscription(subscription));
for(const endpoint of ['https://localhost/send','http://fcm.googleapis.com/a','https://fcm.googleapis.com.evil.test/send','https://fcm.googleapis.com:444/a','https://user@fcm.googleapis.com/a','https://127.0.0.1/a'])assert(!validSubscription({...subscription,endpoint}));
assert(!validSubscription({...subscription,keys:{...subscription.keys,auth:'x'}}));
const raw=new DatabaseSync(':memory:');raw.exec(await readFile('push/migrations/0001_push.sql','utf8'));
const db={prepare(sql){return {values:[],bind(...values){this.values=values;return this;},async first(){return raw.prepare(sql).get(...this.values)||null;},async all(){return {results:raw.prepare(sql).all(...this.values)};},async run(){return raw.prepare(sql).run(...this.values);}};},async batch(queries){raw.exec('BEGIN');try{const results=[];for(const query of queries)results.push(await query.run());raw.exec('COMMIT');return results;}catch(error){raw.exec('ROLLBACK');throw error;}}};
const signing=createECDH('prime256v1');signing.generateKeys();
const env={DB:db,SITE_ORIGIN:'https://kart.example',VAPID_SUBJECT:'mailto:owner@example.com',VAPID_PUBLIC_KEY:signing.getPublicKey().toString('base64url'),VAPID_PRIVATE_KEY:signing.getPrivateKey().toString('base64url'),PUSH_RATE_LIMIT:{limit:async()=>({success:true})}};
const token=Buffer.alloc(32,3).toString('base64url'),id=await hash(token);
function request(method,body,headers={}){return new Request('https://kart.example/api/push/subscription',{method,headers:{Origin:env.SITE_ORIGIN,Authorization:'Bearer '+token,'Content-Type':'application/json',...headers},...(body?{body:JSON.stringify(body)}:{})});}
assert.equal((await api(request('PUT',{subscription,preferences:prefs},{Origin:'https://evil.test'}),env)).status,403);
assert.equal((await api(request('GET',null,{Authorization:''}),env)).status,401);
assert.equal((await api(request('PUT',{subscription:{...subscription,endpoint:'https://127.0.0.1/a'},preferences:prefs}),env)).status,400);
assert.equal((await api(request('PUT',{subscription,preferences:prefs}),env)).status,200);
assert(raw.prepare('SELECT id FROM subscriptions').get());
const created=now-2*60000;raw.prepare('UPDATE subscriptions SET created_at=?').run(created);
const fetcher=async()=>Response.json({updated:new Date().toISOString(),events:[event]});
let sends=0;
const send=async(sub,payload)=>{assert.equal(sub.endpoint,subscription.endpoint);assert.equal(payload.eventId,'race');sends++;return 201;};
const result=await scheduled(env,{fetcher,send,now});assert.equal(result.sent,1);assert.equal(sends,1);
await scheduled(env,{fetcher,send,now:now+1000});assert.equal(sends,1,'Repeated cron must not duplicate alerts');
const sent=raw.prepare("SELECT * FROM jobs WHERE state='sent'").get();
assert.equal(await deliver(db,env,[event],sent,now+1000,send),'claimed');assert.equal(sends,1);
// Deadline edits invalidate queued jobs and create a different delivery key.
const moved={...event,registration_deadline:new Date(deadline+3600000).toISOString()};
const queued=raw.prepare("SELECT * FROM jobs WHERE state='pending'").get();
assert.equal(await deliver(db,env,[moved],queued,deadline,send),'obsolete');assert.equal(sends,1);
// Unsave cancels queued alerts immediately, even before the next scheduled scan.
await api(request('PUT',{subscription,preferences:{saved:[],hours:24}}),env);
assert.equal(raw.prepare("SELECT count(*) AS n FROM jobs WHERE state!='sent'").get().n,0);
await scheduled(env,{fetcher,send,now:deadline});assert.equal(sends,1);
// A previously unknown deadline becomes schedulable without reopening the site.
await api(request('PUT',{subscription,preferences:prefs}),env);raw.prepare('UPDATE subscriptions SET created_at=?').run(created);
raw.prepare('DELETE FROM jobs').run();
let transient=0;
const failed=await scheduled(env,{fetcher,send:async()=>{transient++;return 503;},now});assert.equal(failed.retry,1);
assert.equal(raw.prepare("SELECT attempts FROM jobs WHERE due<=?").get(now).attempts,1);
await scheduled(env,{fetcher,send,now:now+1000});assert.equal(sends,1,'Retry backoff is honored');
await scheduled(env,{fetcher,send,now:now+3*60000});assert.equal(sends,2);
// Cancelled and closed races are checked again immediately before delivery.
raw.prepare('DELETE FROM jobs').run();
await scheduled(env,{fetcher:async()=>Response.json({updated:new Date().toISOString(),events:[{...event,status:'cancelled'}]}),send,now});assert.equal(sends,2);
// A failed or stale source must never send from old queued data.
await assert.rejects(()=>scheduled(env,{fetcher:async()=>Response.json({updated:'2020-01-01',events:[event]}),send,now}));
await assert.rejects(()=>scheduled(env,{fetcher:async()=>new Response('',{status:503}),send,now}));
// Expired push-service subscriptions are removed along with their queued jobs.
await scheduled(env,{fetcher,send:async()=>410,now});assert.equal(raw.prepare('SELECT count(*) AS n FROM subscriptions').get().n,0);assert.equal(raw.prepare('SELECT count(*) AS n FROM jobs').get().n,0);
await api(request('PUT',{subscription,preferences:prefs}),env);
assert.equal((await api(request('DELETE'),env)).status,200);assert.equal(raw.prepare('SELECT count(*) AS n FROM subscriptions').get().n,0);
// Exercise the real VAPID/encryption library, then decrypt with independent Node
// crypto to ensure the exact JSON that reaches a browser has the expected shape.
const originalFetch=globalThis.fetch;let outgoing;
globalThis.fetch=async(url,options)=>{outgoing=options;return new Response('',{status:201});};
const message={eventId:'race',key:'unique',body:'Reminder',expires:now+60000};
try{assert.equal(await sendPush(subscription,message,env,60),201);}finally{globalThis.fetch=originalFetch;}
assert.equal(outgoing.headers['content-encoding'],'aes128gcm');assert(outgoing.headers.authorization.startsWith('vapid t='));assert.equal(outgoing.redirect,'error');
const wire=Buffer.from(outgoing.body),salt=wire.subarray(0,16),server=wire.subarray(21,86),cipher=wire.subarray(86);
const shared=receiver.computeSecret(server);
const derive=(ikm,salt,info,n)=>Buffer.from(hkdfSync('sha256',ikm,salt,info,n));
const ikm=derive(shared,Buffer.from(subscription.keys.auth,'base64url'),Buffer.concat([Buffer.from('WebPush: info\0'),receiver.getPublicKey(),server]),32);
const cek=derive(ikm,salt,Buffer.from('Content-Encoding: aes128gcm\0'),16),iv=derive(ikm,salt,Buffer.from('Content-Encoding: nonce\0'),12);
const decipher=createDecipheriv('aes-128-gcm',cek,iv);decipher.setAuthTag(cipher.subarray(-16));
const padded=Buffer.concat([decipher.update(cipher.subarray(0,-16)),decipher.final()]);let end=padded.length-1;while(padded[end]===0)end--;assert.equal(padded[end],2);assert.deepEqual(JSON.parse(padded.subarray(0,end).toString()),message);
raw.close();console.log('Web push: permissions API, private storage, deadline scheduling, aliases, cancellation, retries, deduplication, stale-data safety and encrypted delivery passed.');
