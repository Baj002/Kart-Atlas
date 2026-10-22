/* Kept separate so browser notification behavior can be tested independently. */
self.addEventListener('push',event=>{
 event.waitUntil((async()=>{
  let data;try{data=event.data.json();}catch{return;}
  if(!data||typeof data.eventId!=='string'||data.eventId.length>200||typeof data.key!=='string'||data.key.length>600||!Number.isFinite(data.expires)||data.expires<=Date.now())return;
  // Persist receipt IDs across service-worker restarts to suppress a retry after
  // an ambiguous provider timeout. No subscription secrets enter this database.
  const database=await new Promise((resolve,reject)=>{const req=indexedDB.open('kart-atlas-push-receipts',1);req.onupgradeneeded=()=>req.result.createObjectStore('seen');req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);}).catch(()=>null);
  try {
   if(database){
    const seen=await new Promise((resolve,reject)=>{const req=database.transaction('seen').objectStore('seen').get(data.key);req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);});if(seen)return;
   }
   await self.registration.showNotification('Kart Atlas registration reminder',{body:String(data.body||'A saved race has a registration deadline approaching.').slice(0,240),icon:'/icon-192.png',badge:'/icon-192.png',tag:data.key,renotify:false,data:{eventId:data.eventId}});
   if(database)await new Promise((resolve,reject)=>{const tx=database.transaction('seen','readwrite'),store=tx.objectStore('seen');store.put(data.expires,data.key);const cursor=store.openCursor();cursor.onsuccess=()=>{const row=cursor.result;if(row){if(row.value<Date.now()-30*86400000)row.delete();row.continue();}};tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});
  } finally{database?.close();}
 })());
});
self.addEventListener('notificationclick',event=>{
 event.notification.close();const id=event.notification.data?.eventId;if(typeof id!=='string')return;
 const target=new URL('/?race='+encodeURIComponent(id),self.location.origin).href;
 event.waitUntil((async()=>{const windows=await self.clients.matchAll({type:'window',includeUncontrolled:true});for(const client of windows){if(new URL(client.url).origin===self.location.origin){await client.navigate(target);await client.focus();return;}}await self.clients.openWindow(target);})());
});
