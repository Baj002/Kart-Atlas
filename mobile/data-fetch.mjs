export function directoryFetch({fetch,storage,dataBaseUrl,onData=()=>{}}){
 const originalFetch=fetch;
 const responseFor=data=>new Response(JSON.stringify(data),{headers:{'Content-Type':'application/json'}});
 const network=async(path,options)=>{
  const response=await originalFetch(new URL(path.slice(1),dataBaseUrl),{...options,credentials:'omit',signal:AbortSignal.timeout(12000)});
  if(!response.ok)throw Error(response.status);const data=await response.json();
  const records=path==='/events.json'?data.events:data.clubs;if(!Array.isArray(records)||!records.length)throw Error('Invalid directory');
  try{storage.setItem('kart-atlas-data:'+path,JSON.stringify(data));}catch{}
  onData(path,data);
  return responseFor(data);
 };
 return async(input,options)=>{
  const path=typeof input==='string'?input:'';
  if(!['/events.json','/clubs.json'].includes(path))return originalFetch(input,options);
  const fallback=async()=>{
   try{const cached=JSON.parse(storage.getItem('kart-atlas-data:'+path)||'null');const records=path==='/events.json'?cached?.events:cached?.clubs;if(Array.isArray(records)&&records.length)return responseFor(cached);}catch{}
   return originalFetch(input,options);
  };
  if(options?.cache==='no-store'){try{return await network(path,options);}catch{return fallback();}}
  // Cold launch renders cached/bundled data immediately, without an offline timeout.
  network(path,options).catch(()=>{});
  return fallback();
 };
}
