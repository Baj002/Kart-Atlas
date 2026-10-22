// No client-supplied dates, links or names enter a notification plan.
export function normalizePreferences(value={}) {
 const saved=value.saved;
 if(!Array.isArray(saved)||saved.length>300||saved.some(id=>typeof id!=='string'||!id||id.length>200))throw Error('Choose at most 300 saved races.');
 if(![1,24,72,168].includes(value.hours))throw Error('Invalid reminder lead time.');
 return {saved:[...new Set(saved)].sort(),hours:value.hours};
}
export function planReminders(events,preferences,since,now=Date.now()) {
 const saved=new Set(preferences.saved),jobs=[];
 for(const event of events) {
  if(![event.id,...(event.alias_ids||[])].some(id=>saved.has(id)))continue;
  if(['cancelled','postponed'].includes(event.status)||['closed','sold_out'].includes(event.registration_status))continue;
  if(event.end&&Date.parse(event.end+'T23:59:59-12:00')<now)continue;
  if(!/^https?:\/\//i.test(event.registration_evidence||'')||!/^\d{4}-\d\d-\d\dT.*(?:Z|[+-]\d\d:?\d\d)$/.test(event.registration_deadline||''))continue;
  const deadline=Date.parse(event.registration_deadline);if(!Number.isFinite(deadline))continue;
  for(const hours of [preferences.hours,0]) {
   const due=deadline-hours*3600000;
   // Never backfill reminders from before opt-in. Retry a due alert for up to
   // 30 minutes, but never send a lead-time alert after registration closes.
   const expires=Math.min(due+30*60000,hours?deadline:Infinity);
   if(due<since||expires<=now)continue;
   jobs.push({key:JSON.stringify([event.id,deadline,hours]),eventId:event.id,deadline,due,expires,hours,name:String(event.name||'Saved race').slice(0,160)});
  }
 }
 return jobs.sort((a,b)=>a.due-b.due||a.key.localeCompare(b.key));
}
export function messageFor(job) {
 return {title:'Kart Atlas registration reminder',body:job.name+(job.hours?' — registration closes in '+(job.hours>=24?job.hours/24+' day'+(job.hours===24?'':'s'):job.hours+' hour')+'.':' — published registration deadline is now.'),eventId:job.eventId,key:job.key,deadline:job.deadline,expires:job.expires};
}
export function validSubscription(value) {
 try {
  const url=new URL(value.endpoint);
  const hosts=['fcm.googleapis.com','web.push.apple.com','push.services.mozilla.com','notify.windows.com'];
  if(url.protocol!=='https:'||url.username||url.password||url.port||url.hash||value.endpoint.length>4096||!hosts.some(host=>url.hostname===host||url.hostname.endsWith('.'+host)))return false;
  const decode=s=>{if(typeof s!=='string'||!/^[A-Za-z0-9_-]+$/.test(s))return null;return Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')),c=>c.charCodeAt(0));};
  const publicKey=decode(value.keys?.p256dh),auth=decode(value.keys?.auth);
  return publicKey?.length===65&&publicKey[0]===4&&auth?.length===16;
 } catch{return false;}
}
export async function hash(value){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value))),b=>b.toString(16).padStart(2,'0')).join('');}
