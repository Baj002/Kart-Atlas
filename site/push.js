/* Optional website push. Permission is requested only from Enable's click. */
(function(root){
 'use strict';
 const KEY='kart-atlas-web-push',TOKEN='kart-atlas-web-push-token';
 const api='/api/push/',listeners=()=>root.dispatchEvent(new Event('kart-atlas-push-change'));
 let state={enabled:false,available:false,pending:false,message:'Checking notification support…'},config,registration,latest={saved:[],hours:24},timer,queue=Promise.resolve(),lastSync=0,lastSignature='';
 const read=k=>{try{return localStorage.getItem(k);}catch{return null;}};
 const write=(k,v)=>{localStorage.setItem(k,v);};
 state.enabled=read(KEY)==='true';
 const token=()=>{let value=read(TOKEN);if(!value){value=b64(crypto.getRandomValues(new Uint8Array(32)));write(TOKEN,value);}return value;};
 const b64=bytes=>btoa(String.fromCharCode(...bytes)).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
 const bytes=value=>Uint8Array.from(atob(value.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));
 async function request(method,body){
  const response=await fetch(api+'subscription',{method,headers:{'Content-Type':'application/json',Authorization:'Bearer '+token()},body:body?JSON.stringify(body):undefined,cache:'no-store',signal:AbortSignal.timeout(15000)});
  const data=await response.json();if(!response.ok)throw Error(data.error||'Notification settings could not sync.');return data;
 }
 async function init(){
  if(root.KartNative?.isNative)return;
  const ios=/iPad|iPhone|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  if(ios&&!root.matchMedia('(display-mode: standalone)').matches&&!navigator.standalone){state.message='On iPhone or iPad, use Share → Add to Home Screen, then open Kart Atlas from its icon to enable notifications.';listeners();return;}
  if(!root.isSecureContext||!('serviceWorker' in navigator)||!('PushManager' in root)||!('Notification' in root)){state.message='This browser does not support website notifications. Calendar reminders are available below.';listeners();return;}
  try{
   const response=await fetch(api+'config',{cache:'no-store',signal:AbortSignal.timeout(10000)});if(!response.ok)throw Error();config=await response.json();if(!config.enabled)throw Error();
   registration=await navigator.serviceWorker.register('/sw.js');await navigator.serviceWorker.ready;
   state.available=true;state.message=state.enabled?'Website notifications are on for this device.':'Get registration alerts even when Kart Atlas is closed.';
   if(Notification.permission==='denied'){state.message='Notifications are blocked. Allow them in your browser or phone settings.';state.available=false;}
   if(read(KEY)==='delete'){try{await request('DELETE');write(KEY,'false');}catch{state.message='Notification removal will retry when connected.';}}
   if(state.enabled)sync(latest.saved,{hours:latest.hours,muted:[]},true);
  }catch{state.message='Website notifications are not connected yet, or the service is unavailable. Calendar reminders still work.';}
  listeners();
 }
 async function flush(){
  if(!state.enabled||!state.available||!registration)return;
  const preferences={...latest};const signature=JSON.stringify(preferences);
  if(signature===lastSignature&&Date.now()-lastSync<15*60000)return;
  state.pending=true;listeners();
  try{
   const subscription=await registration.pushManager.getSubscription();
   if(!subscription||Notification.permission!=='granted'){state.enabled=false;write(KEY,'false');state.message='Notifications need to be reconnected. Tap Enable to reconnect.';return;}
   await request('PUT',{subscription:subscription.toJSON(),preferences});
   lastSignature=signature;lastSync=Date.now();state.message='Notifications on · '+preferences.saved.length+' saved races synced.';
  }catch(error){state.message='Changes have not synced: '+error.message+' Reconnect to update your alerts.';}
  finally{state.pending=false;listeners();}
 }
 function sync(saved,settings={},force=false){
  const muted=new Set(settings.muted||[]);latest={saved:[...new Set(saved)].filter(id=>!muted.has(id)).sort(),hours:settings.hours||24};
  if(!state.enabled)return;
  clearTimeout(timer);if(force)lastSignature='';timer=setTimeout(()=>{queue=queue.catch(()=>{}).then(flush);},400);
 }
 async function enable(){
  if(!state.available||!config||!registration)throw Error(state.message);
  // Must happen before any network await to preserve Safari's user gesture.
  const permission=await Notification.requestPermission();
  if(permission!=='granted')throw Error('Allow notifications in your browser or phone settings to enable alerts.');
  await queue.catch(()=>{});
  if(read(KEY)==='delete')await request('DELETE');
  let subscription=await registration.pushManager.getSubscription();
  // A browser subscription without its device token cannot safely be reclaimed.
  if(subscription&&!read(TOKEN)){await subscription.unsubscribe();subscription=null;}
  token();
  if(!subscription)subscription=await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:bytes(config.publicKey)});
  await request('PUT',{subscription:subscription.toJSON(),preferences:latest});
  write(KEY,'true');state.enabled=true;lastSignature=JSON.stringify(latest);lastSync=Date.now();state.message='Notifications on · '+latest.saved.length+' saved races synced.';listeners();
 }
 async function disable(){
  state.enabled=false;write(KEY,'delete');clearTimeout(timer);
  await queue.catch(()=>{});
  const subscription=await registration?.pushManager.getSubscription();if(subscription)await subscription.unsubscribe();
  try{await request('DELETE');write(KEY,'false');state.message='Website notifications are off. Device subscription deleted.';}
  catch{state.message='Notifications are off in this browser. Server removal will retry when connected.';}
  state.pending=false;listeners();
 }
 root.KartPush={init,sync,enable,disable,status:()=>({...state})};
 root.addEventListener('online',()=>{if(read(KEY)==='delete'||!state.available)init();else sync(latest.saved,{hours:latest.hours},true);});
 if(typeof module!=='undefined'&&module.exports)module.exports=root.KartPush;
})(typeof globalThis!=='undefined'?globalThis:this);
