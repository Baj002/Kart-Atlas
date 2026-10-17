(() => {
  const $ = s => document.querySelector(s);
  const esc = s => String(s||'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
  let clubs=[];
  const selectRegion=()=>{
    const v=$('#club-region').value, country=$('#club-country').value;
    const vals=[...new Set(clubs.filter(c=>!country||c.country===country).map(c=>c.region).filter(Boolean))].sort();
    $('#club-region').replaceChildren(new Option('All regions',''),...vals.map(x=>new Option(x,x)));
    if(vals.includes(v))$('#club-region').value=v;
  };
  const display=()=>{
    const q=$('#club-query').value.trim().toLowerCase(),country=$('#club-country').value,region=$('#club-region').value,only=$('#only-tracked').checked;
    const a=clubs.filter(c=>(!country||c.country===country)&&(!region||c.region===region)&&(!only||!!c.monitor_id)&&(!q||[c.name,c.venue,c.city,c.region,c.country].join(' ').toLowerCase().includes(q)));
    $('#display-clubs').textContent=a.length;
    $('#clubs-empty').classList.toggle('hidden',a.length!==0);
    const root=$('#club-grid');root.replaceChildren();
    for(const c of a){
      const card=document.createElement('article');card.className='club-card';
      const url=/^https?:\/\//i.test(c.schedule_url)?c.schedule_url:'';
      card.innerHTML=`<div class="club-overline">${esc(c.country)} · ${esc(c.region)} <span class="club-flag ${c.monitor_id?'tracking':'lead'}">${c.monitor_id?'Tracked URL':'Discovery lead'}</span></div><h2>${esc(c.name)}</h2><p>${esc(c.venue)}${c.city?' · '+esc(c.city):''}</p><p class="club-note">${esc(c.research_status)}</p>${url?`<a class="source-btn" rel="noopener noreferrer" target="_blank" href="${esc(url)}">Open source ↗</a>`:'<span class="club-note">Organizer URL not established</span>'}`;
      root.append(card);
    }
  };
  fetch('/clubs.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw Error(r.status);return r.json();}).then(doc=>{
    clubs=doc.clubs||[];$('#total-clubs').textContent=clubs.length;$('#track-clubs').textContent=clubs.filter(c=>c.monitor_id).length;
    selectRegion();display();
    ['#club-query','#club-country','#club-region','#only-tracked'].forEach(sel=>$(sel).addEventListener(sel==='#club-query'?'input':'change',()=>{if(sel==='#club-country')selectRegion();display();}));
  }).catch(err=>{$('#directory-results .directory-note').textContent='Unable to load the club directory. Please reload the page.';console.error(err);});
  if('serviceWorker' in navigator)navigator.serviceWorker.register('/sw.js').catch(()=>{});
})();
