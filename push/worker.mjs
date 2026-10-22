import {buildPushPayload} from '@block65/webcrypto-web-push';
import {normalizePreferences,planReminders,messageFor,validSubscription,hash} from './plan.mjs';
const DATA='https://raw.githubusercontent.com/Baj002/Kart-Atlas/main/site/';
const DAY=86400000;
const json=(body,status=200)=>Response.json(body,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}});
const ready=env=>Boolean(env.DB&&env.VAPID_PUBLIC_KEY&&env.VAPID_PRIVATE_KEY&&/^https:\/\//.test(env.SITE_ORIGIN||'')&&/^(mailto:|https:\/\/)/.test(env.VAPID_SUBJECT||''));
async function identity(request){const token=request.headers.get('Authorization')?.match(/^Bearer ([A-Za-z0-9_-]{43})$/)?.[1];return token?hash(token):null;}
async function readBody(request){
 if(!request.headers.get('Content-Type')?.startsWith('application/json'))throw Error('Expected JSON.');
 if(Number(request.headers.get('Content-Length')||0)>20000)throw Error('Request too large.');
 const reader=request.body?.getReader();if(!reader)throw Error('Missing request.');
 let length=0,chunks=[];
 while(true){const {done,value}=await reader.read();if(done)break;length+=value.length;if(length>20000){await reader.cancel();throw Error('Request too large.');}chunks.push(value);}
 const bytes=new Uint8Array(length);let at=0;for(const chunk of chunks){bytes.set(chunk,at);at+=chunk.length;}
 return JSON.parse(new TextDecoder().decode(bytes));
}
export async function api(request,env) {
 const path=new URL(request.url).pathname;
 if(path==='/api/push/config'&&request.method==='GET')return json({enabled:ready(env),publicKey:ready(env)?env.VAPID_PUBLIC_KEY:null});
 if(!ready(env))return json({error:'Notifications are not enabled for this website yet.'},503);
 if(path!=='/api/push/subscription')return json({error:'Not found.'},404);
 if(!['GET','PUT','DELETE'].includes(request.method))return json({error:'Method not allowed.'},405);
 // Same-origin only; no credentials or push endpoints are exposed through CORS.
 if(request.headers.get('Origin')!==env.SITE_ORIGIN)return json({error:'Wrong website origin.'},403);
 const id=await identity(request);if(!id)return json({error:'Missing device authorization.'},401);
 if(env.PUSH_RATE_LIMIT&&!(await env.PUSH_RATE_LIMIT.limit({key:id})).success)return json({error:'Too many changes. Try again shortly.'},429);
 const now=Date.now();
 if(request.method==='GET') {
  const row=await env.DB.prepare('SELECT updated_at FROM subscriptions WHERE id=?').bind(id).first();
  return json({enabled:Boolean(row),updatedAt:row?.updated_at||null});
 }
 if(request.method==='DELETE') {
  await env.DB.batch([env.DB.prepare('DELETE FROM jobs WHERE subscription_id=?').bind(id),env.DB.prepare('DELETE FROM subscriptions WHERE id=?').bind(id)]);
  return json({enabled:false});
 }
 let body,preferences;
 try{body=await readBody(request);preferences=normalizePreferences(body.preferences);if(!validSubscription(body.subscription))throw Error('Unsupported or invalid push subscription.');}catch(error){return json({error:error.message||'Invalid request.'},400);}
 // Limit new registrations too; a caller can otherwise rotate device tokens.
 const previous=await env.DB.prepare('SELECT preferences,subscription FROM subscriptions WHERE id=?').bind(id).first();
 if(!previous&&env.PUSH_RATE_LIMIT&&!(await env.PUSH_RATE_LIMIT.limit({key:'new:'+request.headers.get('CF-Connecting-IP')})).success)return json({error:'Too many new devices. Try again shortly.'},429);
 const subscription={endpoint:body.subscription.endpoint,keys:{p256dh:body.subscription.keys.p256dh,auth:body.subscription.keys.auth}};
 const owner=await env.DB.prepare('SELECT id FROM subscriptions WHERE endpoint=?').bind(subscription.endpoint).first();
 if(owner&&owner.id!==id)return json({error:'Reconnect notifications on this device.'},409);
 const prefs=JSON.stringify(preferences),sub=JSON.stringify(subscription);
 const revision=crypto.randomUUID();
 const queries=[env.DB.prepare(`INSERT INTO subscriptions (id,endpoint,subscription,preferences,created_at,updated_at,revision) VALUES (?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET endpoint=excluded.endpoint,subscription=excluded.subscription,preferences=excluded.preferences,updated_at=excluded.updated_at,revision=excluded.revision`).bind(id,subscription.endpoint,sub,prefs,now,now,revision)];
 if(previous&&(previous.preferences!==prefs||previous.subscription!==sub))queries.push(env.DB.prepare("DELETE FROM jobs WHERE subscription_id=? AND state!='sent'").bind(id));
 await env.DB.batch(queries);
 return json({enabled:true,savedCount:preferences.saved.length});
}
async function directory(fetcher=fetch) {
 const response=await fetcher(DATA+'events.json',{cache:'no-store',signal:AbortSignal.timeout(15000)});
 if(!response.ok)throw Error('Directory fetch failed.');
 const data=await response.json();
 if(!Array.isArray(data.events)||!data.events.length||!data.events.every(e=>typeof e.id==='string'))throw Error('Invalid directory.');
 // Fail closed when automation has stopped; do not notify from a stale snapshot.
 const updated=Date.parse(data.updated?.length===10?data.updated+'T00:00:00Z':data.updated);
 if(!Number.isFinite(updated)||Date.now()-updated>3*DAY||updated>Date.now()+DAY)throw Error('Directory snapshot is stale.');
 return data.events;
}
async function removeDevice(db,id){await db.batch([db.prepare('DELETE FROM jobs WHERE subscription_id=?').bind(id),db.prepare('DELETE FROM subscriptions WHERE id=?').bind(id)]);}
export async function deliver(db,env,events,job,now,send=sendPush) {
 const sub=await db.prepare('SELECT * FROM subscriptions WHERE id=?').bind(job.subscription_id).first();
 if(!sub)return 'removed';
 const desired=planReminders(events,JSON.parse(sub.preferences),sub.created_at,now).find(item=>item.key===job.event_key);
 if(!desired||desired.due>now){await db.prepare('DELETE FROM jobs WHERE id=?').bind(job.id).run();return 'obsolete';}
 const claimed=await db.prepare(`UPDATE jobs SET state='sending',lease_until=?,attempts=attempts+1 WHERE id=? AND state!='sent' AND lease_until<=? RETURNING id`).bind(now+120000,job.id,now).first();
 if(!claimed)return 'claimed';
 // A saved-race edit can race with reconciliation: check its revision before send.
 const current=await db.prepare('SELECT revision FROM subscriptions WHERE id=?').bind(sub.id).first();
 if(current?.revision!==sub.revision){await db.prepare('DELETE FROM jobs WHERE id=? AND state!=?').bind(job.id,'sent').run();return 'changed';}
 let status;
 try{status=await send(JSON.parse(sub.subscription),messageFor(desired),env,Math.max(0,Math.floor((desired.expires-now)/1000)));}catch{status=503;}
 if(status===404||status===410){await removeDevice(db,sub.id);return 'expired';}
 if(status>=200&&status<300){await db.prepare("UPDATE jobs SET state='sent',lease_until=0 WHERE id=?").bind(job.id).run();return 'sent';}
 const attempts=job.attempts+1;
 const retry=now+Math.min(15*60000,60000*2**Math.min(attempts,4));
 // Authentication errors remain visible in aggregate diagnostics; retry only
 // transient/provider failures, never log endpoints, tokens or payloads.
 const permanent=status>=400&&status<500&&![408,429].includes(status);
 await db.prepare("UPDATE jobs SET state=?,lease_until=0,retry_at=? WHERE id=?").bind(permanent?'failed':'pending',retry,job.id).run();
 return permanent?'failed':'retry';
}
export async function sendPush(subscription,payload,env,ttl) {
 const request=await buildPushPayload({data:JSON.stringify(payload),options:{ttl,urgency:'normal',topic:(await hash(payload.key)).slice(0,32)}},subscription,{subject:env.VAPID_SUBJECT,publicKey:env.VAPID_PUBLIC_KEY,privateKey:env.VAPID_PRIVATE_KEY});
 const response=await fetch(subscription.endpoint,{...request,redirect:'error',signal:AbortSignal.timeout(10000)});
 await response.body?.cancel();return response.status;
}
export async function scheduled(env,{fetcher=fetch,send=sendPush,now=Date.now()}={}) {
 if(!ready(env))throw Error('Push delivery is not configured.');
 const db=env.DB;
 const events=await directory(fetcher); // A failed fetch sends nothing; retry next tick.
 const summary={checked:0,sent:0,retry:0,expired:0,obsolete:0,failed:0};
 // Round-robin reconciliation adds newly announced deadlines even if the user
 // has not reopened Kart Atlas. Existing jobs are checked against live data too.
 const cursor=await db.prepare("SELECT value FROM state WHERE key='cursor'").first();
 let rows=(await db.prepare('SELECT * FROM subscriptions WHERE id>? ORDER BY id LIMIT 100').bind(cursor?.value||'').all()).results;
 if(!rows.length)rows=(await db.prepare('SELECT * FROM subscriptions ORDER BY id LIMIT 100').all()).results;
 for(const sub of rows) {
  if(sub.updated_at<now-180*DAY){await removeDevice(db,sub.id);continue;}
  const jobs=planReminders(events,JSON.parse(sub.preferences),sub.created_at,now);
  const queries=jobs.map(job=>db.prepare(`INSERT OR IGNORE INTO jobs (id,subscription_id,event_id,event_key,deadline,due,expires,offset_hours) SELECT ?,?,?,?,?,?,?,? WHERE EXISTS (SELECT 1 FROM subscriptions WHERE id=? AND revision=?)`).bind(sub.id+'|'+job.key,sub.id,job.eventId,job.key,job.deadline,job.due,job.expires,job.hours,sub.id,sub.revision));
  // Guard insertion with the revision: edits must not resurrect deleted jobs.
  if(queries.length)for(let at=0;at<queries.length;at+=50)await db.batch(queries.slice(at,at+50));
  summary.checked++;
 }
 await db.prepare("INSERT INTO state(key,value) VALUES('cursor',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").bind(rows.at(-1)?.id||'').run();
 const backlog=await db.prepare("SELECT count(*) AS queuedDue,min(due) AS oldestDue FROM jobs WHERE state IN ('pending','sending') AND due<=? AND expires>?").bind(now,now).first();
 summary.queuedDue=backlog?.queuedDue||0;summary.oldestDue=backlog?.oldestDue||null;
 const due=(await db.prepare("SELECT * FROM jobs WHERE state IN ('pending','sending') AND due<=? AND expires>? AND retry_at<=? AND lease_until<=? ORDER BY due,id LIMIT 25").bind(now,now,now,now).all()).results;
 for(let at=0;at<due.length;at+=4)await Promise.all(due.slice(at,at+4).map(async job=>{const result=await deliver(db,env,events,job,now,send);if(result in summary)summary[result]++;}));
 await db.batch([
  db.prepare('DELETE FROM jobs WHERE expires<?').bind(now-30*DAY),
  db.prepare("INSERT INTO state(key,value) VALUES('last_run',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").bind(JSON.stringify({at:now,...summary}))
 ]);
 console.log('push_delivery',JSON.stringify(summary));return summary;
}
export default {
 async fetch(request,env) {
  const url=new URL(request.url);
  if(url.pathname.startsWith('/api/')){try{return await api(request,env);}catch{return json({error:'Notification service temporarily unavailable.'},503);}}
  if(['/coverage.html','/coverage.js','/coverage.json','/monitor_status.json'].includes(url.pathname))return new Response('Not found',{status:404});
  if(['/events.json','/clubs.json'].includes(url.pathname)) {
   try{const response=await fetch(DATA+url.pathname.slice(1),{signal:AbortSignal.timeout(12000),cf:{cacheTtl:60}});if(response.ok)return new Response(response.body,{headers:{'Content-Type':'application/json','Cache-Control':'public, max-age=60'}});}catch{}
  }
  const response=await env.ASSETS.fetch(request);const headers=new Headers(response.headers);
  headers.set('X-Content-Type-Options','nosniff');headers.set('Referrer-Policy','strict-origin-when-cross-origin');
  if(url.pathname==='/sw.js')headers.set('Cache-Control','no-cache');
  return new Response(response.body,{status:response.status,headers});
 },
 async scheduled(controller,env){await scheduled(env);}
};
