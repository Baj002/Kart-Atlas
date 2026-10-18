const CACHE_NAME = 'kart-atlas-automated-v6';
const PRECACHE = ['/','/index.html','/clubs.html','/styles.css?v=event1','/app.js?v=overview1','/clubs.js','/events.json','/clubs.json','/manifest.webmanifest','/icon-192.png','/icon-512.png'];
self.addEventListener('install', e=>e.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll(PRECACHE)).then(()=>self.skipWaiting())));
self.addEventListener('activate', e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch', e=>{
 const r=e.request;if(r.method!=='GET'||new URL(r.url).origin!==self.location.origin)return;
 // Network-first so installed apps pick up changes without a new package/install.
 e.respondWith(fetch(r).then(res=>{if(res.ok){const copy=res.clone();e.waitUntil(caches.open(CACHE_NAME).then(c=>c.put(r,copy)));}return res;}).catch(()=>caches.match(r)));
});
