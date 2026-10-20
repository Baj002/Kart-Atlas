export function notificationPlan(events,saved,options={},now=Date.now()){
 const ids=new Set(saved),muted=new Set(options.muted||[]),hours=[1,24,72,168].includes(Number(options.hours))?Number(options.hours):24;
 if(!options.enabled)return [];
 const date=new Date(now),localDay=[date.getFullYear(),String(date.getMonth()+1).padStart(2,'0'),String(date.getDate()).padStart(2,'0')].join('-');
 const result=[];
 for(const event of events){
  const aliases=[event.id,...(event.alias_ids||[])];
  if(!aliases.some(id=>ids.has(id))||aliases.some(id=>muted.has(id)))continue;
  if(event.end&&event.end<localDay)continue;
  if(['cancelled','postponed'].includes(event.status)||['closed','sold_out'].includes(event.registration_status))continue;
  if(!event.registration_evidence||!/^https?:\/\//.test(event.registration_evidence))continue;
  if(!/T.*(?:Z|[+-]\d{2}:?\d{2})$/.test(event.registration_deadline||''))continue;
  const deadline=Date.parse(event.registration_deadline);if(!Number.isFinite(deadline)||deadline<=now)continue;
  for(const offset of [hours*3600000,0]){
   const at=deadline-offset;if(at<=now+1000)continue;
   const seed=[event.id,event.name,deadline,offset].join('|');let hash=2166136261;
   for(const char of seed)hash=Math.imul(hash^char.charCodeAt(0),16777619);
   result.push({id:(hash>>>0)%2147483646+1,title:'Kart Atlas registration reminder',body:event.name+(offset?' — deadline approaching.':' — published deadline is now.'),schedule:{at:new Date(at)},channelId:'kart-registration',isExactNotification:false,extra:{kartAtlas:true,eventId:event.id,deadline:event.registration_deadline}});
  }
 }
 result.sort((a,b)=>a.schedule.at-b.schedule.at||a.id-b.id);
 const used=new Set();for(const item of result){while(used.has(item.id))item.id=item.id%2147483646+1;used.add(item.id);}
 // iOS supports at most 64 pending local notifications; reserve four slots.
 return result.slice(0,60);
}
