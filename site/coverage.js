(async()=>{
  const node=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
  const link=(url,label)=>{try{const u=new URL(url);if(!['https:','http:'].includes(u.protocol))return node('span',label);const a=node('a',label);a.href=u.href;a.rel='noopener noreferrer';a.target='_blank';return a;}catch{return node('span',label);}};
  try{
    const response=await fetch('/coverage.json',{cache:'no-store'});if(!response.ok)throw Error('report unavailable');const d=await response.json();
    document.querySelector('#coverage-status').textContent=`Last scan: ${new Date(d.generated_at).toLocaleString()}. Reached ${d.sources_reached}/${d.sources_attempted} sources (${d.source_reach_percent}%). ${d.event_candidates} race candidates await verification; ${d.organizer_leads} new website leads. ${d.deferred_links} links deferred by scan limits. ${(d.changed_pages||[]).length} pages changed since the previous scan.`;
    for(const [country,c]of Object.entries(d.by_country)){const row=node('tr','');[country,`${c.sources_reached}/${c.sources_attempted}`,String(c.future_races),c.regions_with_races.join(', ')||'None indexed'].forEach(v=>row.append(node('td',v)));document.querySelector('#countries').append(row);}
    for(const s of d.sources){const details=node('details','');details.append(node('summary',`${s.club} — ${s.pages.length?'reached':'not reached'} · ${s.trusted?'organizer source':'research lead'}`));details.append(link(s.url,s.url));details.append(node('p',`${s.pages.length}/${s.attempted} pages reached; ${s.pages.reduce((n,p)=>n+p.events,0)} race observations; ${s.remaining_links} deferred links.`));for(const e of s.errors){const p=node('p',e.error+' — '+e.url);p.className='coverage-error';details.append(p);}if(s.documents.length)details.append(node('p',`${s.documents.length} linked PDF documents need review.`));document.querySelector('#sources').append(details);}
    document.querySelector('#unmonitored-heading').textContent=`${d.unmonitored_clubs.length} directory entries without a verified monitored website`;
    for(const c of d.unmonitored_clubs){const li=node('li','');li.append(link(c.url,`${c.club} · ${c.region}, ${c.country}`));document.querySelector('#unmonitored').append(li);}
  }catch{document.querySelector('#coverage-status').textContent='The coverage report is unavailable. Try again when connected.';}
})();
