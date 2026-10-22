import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFile,access} from 'node:fs/promises';
const source=await readFile('site/push.js','utf8');
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
function client({ios=false,standalone=true,configured=true}={}){
 const memory=new Map(),requests=[],listeners=new Map();let permissionCalls=0,current=null,fail=false;
 const sub={toJSON:()=>({endpoint:'https://fcm.googleapis.com/fake',keys:{}}),unsubscribe:async()=>{current=null;return true;}};
 const reg={pushManager:{getSubscription:async()=>current,subscribe:async options=>{assert.equal(options.userVisibleOnly,true);current=sub;return sub;}}};
 const context={console,Event,Uint8Array,crypto,AbortSignal,btoa,atob,setTimeout,clearTimeout,isSecureContext:true,PushManager:function(){},matchMedia:()=>({matches:standalone}),
  Notification:{permission:'granted',requestPermission:()=>{permissionCalls++;return Promise.resolve('granted');}},
  localStorage:{getItem:k=>memory.get(k)||null,setItem:(k,v)=>memory.set(k,v)},
  navigator:{userAgent:ios?'iPhone':'Android',platform:'Linux',serviceWorker:{register:async()=>reg,ready:Promise.resolve(reg)}},
  addEventListener:(name,fn)=>listeners.set(name,fn),dispatchEvent:()=>{},
  fetch:async(url,options={})=>{requests.push({url,options});if(fail)throw Error('offline');return Response.json(url.endsWith('/config')?{enabled:configured,publicKey:Buffer.alloc(65,3).toString('base64url')}:{enabled:options.method!=='DELETE'});}
 };
 vm.createContext(context);vm.runInContext(source,context);
 return {api:context.KartPush,context,memory,requests,permissionCalls:()=>permissionCalls,fail:value=>{fail=value;},listeners};
}
const c=client();await c.api.init();assert(c.api.status().available);assert.equal(c.permissionCalls(),0,'Never prompt during startup');
c.api.sync(['saved','muted'],{hours:72,muted:['muted']});
const enabled=c.api.enable();assert.equal(c.permissionCalls(),1,'Prompt synchronously from user action');await enabled;
assert.equal(c.memory.get('kart-atlas-web-push'),'true');
let puts=c.requests.filter(r=>r.options.method==='PUT');assert.deepEqual(JSON.parse(puts.at(-1).options.body).preferences,{saved:['saved'],hours:72});
assert.match(puts[0].options.headers.Authorization,/^Bearer [A-Za-z0-9_-]{43}$/);
c.api.sync([],{hours:24});await pause(450);
puts=c.requests.filter(r=>r.options.method==='PUT');assert.deepEqual(JSON.parse(puts.at(-1).options.body).preferences.saved,[],'Unsave updates server watch list');
// Requests are serialized; rapid updates coalesce to the latest selection.
c.api.sync(['first'],{hours:24});c.api.sync(['last'],{hours:1});await pause(450);
puts=c.requests.filter(r=>r.options.method==='PUT');assert.deepEqual(JSON.parse(puts.at(-1).options.body).preferences,{saved:['last'],hours:1});
c.fail(true);c.api.sync(['offline'],{hours:24});await pause(450);assert.match(c.api.status().message,/not synced/);
await c.api.disable();assert.equal(c.api.status().enabled,false);assert.equal(c.memory.get('kart-atlas-web-push'),'delete','Offline server deletion remains pending');
c.fail(false);await c.api.init();assert.equal(c.memory.get('kart-atlas-web-push'),'false');assert(c.requests.some(r=>r.options.method==='DELETE'));
const iphone=client({ios:true,standalone:false});await iphone.api.init();assert.match(iphone.api.status().message,/Add to Home Screen/);assert.equal(iphone.permissionCalls(),0);assert.equal(iphone.requests.length,0);
const unconfigured=client({configured:false});await unconfigured.api.init();assert(!unconfigured.api.status().available);assert.equal(unconfigured.permissionCalls(),0);
const denied=client();denied.context.Notification.permission='denied';await denied.api.init();assert.match(denied.api.status().message,/blocked/);assert(!denied.api.status().available);
// Run service-worker handlers with a persistent, minimal IndexedDB adapter.
const receipts=new Map(),swListeners=new Map(),shown=[],navigated=[];
const database={createObjectStore(){},close(){},transaction(name,mode){const tx={objectStore:()=>({
 get(key){const req={};queueMicrotask(()=>{req.result=receipts.get(key);req.onsuccess();});return req;},
 put(value,key){receipts.set(key,value);},
 openCursor(){const req={};queueMicrotask(()=>{req.result=null;req.onsuccess();queueMicrotask(()=>tx.oncomplete?.());});return req;}
})};return tx;}};
const sw={self:{addEventListener:(name,fn)=>swListeners.set(name,fn),registration:{showNotification:async(title,options)=>shown.push({title,options})},location:{origin:'https://kart.example'},clients:{matchAll:async()=>[{url:'https://kart.example/',navigate:async url=>navigated.push(url),focus:async()=>{}}],openWindow:async url=>navigated.push(url)}},URL,Date,Promise,indexedDB:{open(){const req={};queueMicrotask(()=>{req.result=database;req.onsuccess();});return req;}}};
vm.createContext(sw);vm.runInContext(await readFile('site/push-sw.js','utf8'),sw);
async function push(data){let work;swListeners.get('push')({data:{json:()=>data},waitUntil:promise=>{work=promise;}});await work;}
const payload={eventId:'race',key:'race|deadline|24',body:'Registration approaching',expires:Date.now()+60000};
await push(payload);assert.equal(shown.length,1);await push(payload);assert.equal(shown.length,1,'Duplicate provider deliveries are suppressed after receipt');
await push({...payload,key:'expired',expires:Date.now()-1});assert.equal(shown.length,1);
await push({url:'https://evil.test/'});assert.equal(shown.length,1);
let click;swListeners.get('notificationclick')({notification:{close(){},data:{eventId:'https://evil.test/?x=1'}},waitUntil:p=>{click=p;}});await click;
assert.equal(new URL(navigated[0]).origin,'https://kart.example');assert.equal(new URL(navigated[0]).searchParams.get('race'),'https://evil.test/?x=1');
// API fetches bypass the cache entirely, including offline fallbacks.
const mainListeners=new Map(),main={self:{addEventListener:(name,fn)=>mainListeners.set(name,fn),location:{origin:'https://kart.example'}},importScripts:path=>assert.equal(path,'/push-sw.js'),URL};vm.createContext(main);vm.runInContext(await readFile('site/sw.js','utf8'),main);
let cached=false;mainListeners.get('fetch')({request:new Request('https://kart.example/api/push/config'),respondWith:()=>{cached=true;}});assert.equal(cached,false);
for(const file of ['site/push.js','site/push-sw.js','site/notification-privacy.html'])await access(file);
console.log('Browser push: explicit permissions, iPhone installation guidance, saved-race syncing, offline deletion, duplicate suppression, safe notification taps and private API cache exclusion passed.');
