import {Capacitor} from '@capacitor/core';
import {App} from '@capacitor/app';
import {Browser} from '@capacitor/browser';
import {Filesystem,Directory,Encoding} from '@capacitor/filesystem';
import {Share} from '@capacitor/share';
import {LocalNotifications} from '@capacitor/local-notifications';
import {notificationPlan} from './reminder-plan.mjs';
import release from './release.json';

const isNative=Capacitor.isNativePlatform();
let enabled=false;try{enabled=localStorage.getItem('kart-atlas-phone-reminders')==='true';}catch{}
let queue=Promise.resolve();
async function reconcile(events,saved,options){
 const plan=notificationPlan(events,saved,{...options,enabled});
 const pending=(await LocalNotifications.getPending()).notifications.filter(n=>n.extra?.kartAtlas);
 const wanted=new Set(plan.map(n=>n.id));const removed=pending.filter(n=>!wanted.has(n.id)).map(n=>({id:n.id}));
 if(removed.length)await LocalNotifications.cancel({notifications:removed});
 if(!enabled)return 0;
 const permission=await LocalNotifications.checkPermissions();if(permission.display!=='granted')return 0;
 if(Capacitor.getPlatform()==='android')await LocalNotifications.createChannel({id:'kart-registration',name:'Registration deadlines',importance:4,description:'Reminders for saved race registration deadlines'});
 const existing=new Set(pending.map(n=>n.id)),added=plan.filter(n=>!existing.has(n.id));
 if(added.length)await LocalNotifications.schedule({notifications:added});
 return plan.length;
}
const native={
 isNative,phoneRemindersEnabled:()=>enabled,
 async setPhoneReminders(value){
  if(value){const permission=await LocalNotifications.requestPermissions();if(permission.display!=='granted')return false;}
  enabled=Boolean(value);try{localStorage.setItem('kart-atlas-phone-reminders',String(enabled));}catch{}
  return enabled;
 },
 syncReminders(events,saved,options){queue=queue.catch(()=>{}).then(()=>reconcile(events,saved,options));return queue;},
 async saveFile(name,content,mime){
  const safe=name.replace(/[^a-z0-9._-]/gi,'-');
  const file=await Filesystem.writeFile({path:safe,data:content,directory:Directory.Cache,encoding:Encoding.UTF8});
  await Share.share({title:name,files:[file.uri],dialogTitle:'Save or share '+name});
 },
 async openLink(url){const parsed=new URL(url);if(!['https:','http:'].includes(parsed.protocol)||parsed.username||parsed.password)throw Error('Unsupported link');await Browser.open({url:parsed.href});}
};
globalThis.KartNative=native;
if(isNative){
 document.documentElement.classList.add('native-app');
 // Bundle remains usable offline; remote data is cached separately from app code.
 const originalFetch=globalThis.fetch.bind(globalThis);
 globalThis.fetch=async(input,options)=>{
  const path=typeof input==='string'?input:'';
  if(!['/events.json','/clubs.json'].includes(path))return originalFetch(input,options);
  const key='kart-atlas-data:'+path;
  try{
   const response=await originalFetch(new URL(path.slice(1),release.dataBaseUrl),{...options,credentials:'omit',signal:AbortSignal.timeout(12000)});
   if(!response.ok)throw Error(response.status);const data=await response.json();
   const records=path==='/events.json'?data.events:data.clubs;if(!Array.isArray(records)||!records.length)throw Error('Invalid directory');
   const text=JSON.stringify(data);try{localStorage.setItem(key,text);}catch{}
   return new Response(text,{headers:{'Content-Type':'application/json'}});
  }catch{
   try{const cached=localStorage.getItem(key);if(cached)return new Response(cached,{headers:{'Content-Type':'application/json'}});}catch{}
   return originalFetch(input,options);
  }
 };
 document.addEventListener('click',event=>{
  const anchor=event.target.closest?.('a[href]');if(!anchor||anchor.download)return;
  if(/^https?:\/\//i.test(anchor.href)&&new URL(anchor.href).origin!==location.origin){event.preventDefault();native.openLink(anchor.href).catch(()=>{});}
 });
 App.addListener('backButton',({canGoBack})=>{const dialog=document.querySelector('dialog[open]');if(dialog)dialog.close();else if(location.pathname.includes('clubs'))location.href='/';else if(canGoBack)history.back();else App.exitApp();});
 App.addListener('appStateChange',({isActive})=>{if(isActive)window.dispatchEvent(new Event('kart-atlas-resume'));});
 LocalNotifications.addListener('localNotificationActionPerformed',({notification})=>{
  const id=notification.extra?.eventId;if(typeof id!=='string')return;
  if(location.pathname!=='/'&&!location.pathname.endsWith('/index.html')){location.href='/?race='+encodeURIComponent(id);return;}
  globalThis.KartAtlasPendingRace=id;window.dispatchEvent(new CustomEvent('kart-atlas-open-event',{detail:id}));
 });
}
