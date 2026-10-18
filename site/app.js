(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $all = (s, root = document) => [...root.querySelectorAll(s)];
  const el = (type, cls, text) => { const node=document.createElement(type);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;};
  let events=[], snapshot='', count=25, mode='list', month=new Date(new Date().getFullYear(),new Date().getMonth(),1), selectedDay='';
  let deferredInstall = null, raceMap=null, mapLayer=null;
  const CITY_COORDS={
    'strathmore|AB':[51.05,-113.39],'warburg|AB':[53.18,-114.32],'chilliwack|BC':[49.16,-121.95],'oliver|BC':[49.18,-119.55],'quesnel|BC':[52.98,-122.49],'martensville|SK':[52.29,-106.67],'regina|SK':[50.45,-104.62],
    'mont-saint-hilaire|QC':[45.56,-73.19],'trois-rivières|QC':[46.34,-72.55],'mont-tremblant|QC':[46.12,-74.60],'saint-célestin|QC':[46.20,-72.40],'mirabel|QC':[45.65,-74.08],
    'orlando|FL':[28.54,-81.38],'sebring|FL':[27.50,-81.44],'mooresville|NC':[35.58,-80.81],'lorain|OH':[41.45,-82.18],'shelbyville|TN':[35.48,-86.46],'las vegas|NV':[36.17,-115.14],'pahrump|NV':[36.21,-115.98],
    'winchester|CA':[33.71,-117.08],'sonoma|CA':[38.29,-122.46],'erda|UT':[40.61,-112.31],'whiteland|IN':[39.55,-86.08],'batavia|OH':[39.08,-84.18],
    'phoenix|AZ':[33.45,-112.07],'glendale|AZ':[33.54,-112.19],'denton|TX':[33.21,-97.13],'portland|OR':[45.52,-122.68],'spanaway|WA':[47.10,-122.43],
    'uxbridge|ON':[44.11,-79.12],'mount hope|ON':[43.16,-79.92],'ottawa|ON':[45.42,-75.69],'gimli|MB':[50.63,-96.99],
    'new castle|IN':[39.93,-85.37],'indianapolis|IN':[39.77,-86.16],'charlotte|NC':[35.23,-80.84],'daytona beach|FL':[29.21,-81.02],'homestead|FL':[25.47,-80.48],'tucson|AZ':[32.22,-110.97],'dallas|TX':[32.78,-96.80],'austin|TX':[30.27,-97.74],'houston|TX':[29.76,-95.37],
    'los angeles|CA':[34.05,-118.24],'san diego|CA':[32.72,-117.16],'sacramento|CA':[38.58,-121.49],'denver|CO':[39.74,-104.99],'salt lake city|UT':[40.76,-111.89],'new york|NY':[40.71,-74.01],'atlanta|GA':[33.75,-84.39],'chicago|IL':[41.88,-87.63]
  };
  const coordinates=e=>{if(Number.isFinite(Number(e.lat))&&Number.isFinite(Number(e.lng))&&e.lat!==undefined&&e.lng!==undefined)return [Number(e.lat),Number(e.lng)];return CITY_COORDS[`${String(e.city||'').trim().toLowerCase()}|${e.region}`]||null;};
  function renderMap(data){
    if(!window.L){$('#map-note').textContent='Map tiles could not load. Check your internet connection; List view remains available.';return;}
    if(!raceMap){raceMap=L.map('race-map',{scrollWheelZoom:false}).setView([40,-98],4);L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'© OpenStreetMap contributors'}).addTo(raceMap);mapLayer=L.layerGroup().addTo(raceMap);}
    mapLayer.clearLayers();const bounds=[];let mapped=0;
    for(const e of data){const xy=coordinates(e);if(!xy)continue;mapped++;bounds.push(xy);const marker=L.marker(xy).addTo(mapLayer);const popup=document.createElement('div');const title=document.createElement('strong');title.textContent=e.name;const details=document.createElement('p');details.textContent=`${fmtRange(e)} · ${e.venue||'Venue TBA'} · ${e.city}, ${e.region}`;popup.append(title,details);if(safeURL(e.source)){const a=document.createElement('a');a.href=e.source;a.target='_blank';a.rel='noopener noreferrer';a.textContent='Organizer page ↗';popup.append(a);}const more=document.createElement('button');more.type='button';more.textContent='Event details →';more.style.cssText='display:block;margin-top:9px;cursor:pointer';more.onclick=()=>{raceMap.closePopup();showEvent(e);};popup.append(more);marker.bindPopup(popup);}
    $('#map-note').textContent=`${mapped} of ${data.length} matching races mapped. Pins show approximate city centers unless coordinates are provided, not verified track entrances. Unmapped races remain available in List view.`;
    setTimeout(()=>{raceMap.invalidateSize();if(bounds.length)raceMap.fitBounds(bounds,{padding:[30,30],maxZoom:10});else raceMap.setView([40,-98],4);},30);
  }
  const today = () => { const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; };
  let saved = new Set();
  try { saved=new Set(JSON.parse(localStorage.getItem('kart-atlas-favorites')||'[]')); } catch {}
  const monthNames=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const safeURL = s => /^https?:\/\//i.test(s) ? s : '';
  const ymd = s => { const [y,m,d]=s.split('-').map(Number);return new Date(y,m-1,d); };
  const sameDay = e => e.end === e.start;
  const fmtDate = s => {const d=ymd(s);return d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});};
  const fmtRange = e => sameDay(e) ? fmtDate(e.start) : `${fmtDate(e.start)} – ${fmtDate(e.end)}`;
  const sortRegion = (a,b) => a.localeCompare(b,undefined,{sensitivity:'base'});
  function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('show');clearTimeout(toast._id);toast._id=setTimeout(()=>t.classList.remove('show'),2300);}
  function persist(){try{localStorage.setItem('kart-atlas-favorites',JSON.stringify([...saved]));}catch{toast('Saved races cannot persist in this browser.');}}
  function getFilters(){return {
    q:$('#search').value.trim().toLowerCase(),country:$('#country').value,region:$('#region').value,level:$('#level').value,
    from:$('#from').value,to:$('#to').value,upcoming:$('#upcoming').checked,official:$('#official').checked,
    favorites:$('#favorites').checked,kartClass:$('#class-filter').value,sort:$('#sort').value
  };}
  const CLASS_PATTERNS={briggs:/\b(briggs|lo\s*206|206|four[ -]?cycle|4[ -]?cycle)\b/i,rotax:/\brotax\b|\b(dd2|max\s*challenge)\b/i,rok:/\brok\b/i,iame:/\b(iame|x30|ka100|ka 100)\b/i,shifter:/\b(shifter|kz2?|icc|125\s*cc\s*gearbox)\b/i,kid:/\b(kid\s*kart|bambino|micro\s*swift)\b/i};
  function classMatch(e,value){const classes=String(e.classes||'').trim();if(!classes)return false;if(value==='other')return !Object.values(CLASS_PATTERNS).some(re=>re.test(classes));return !!(CLASS_PATTERNS[value]&&CLASS_PATTERNS[value].test(classes));}
  function filtered(){const f=getFilters();let a=events.filter(e=>{
    if(f.q&&!([e.name,e.organizer,e.venue,e.city,e.region,e.classes,e.format].join(' ').toLowerCase().includes(f.q)))return false;
    if(f.country && e.country!==f.country)return false;
    if(f.region && e.region!==f.region)return false;
    if(f.level && e.level!==f.level)return false;
    if(f.kartClass && !classMatch(e,f.kartClass))return false;
    if(f.from && e.end<f.from)return false;
    if(f.to && e.start>f.to)return false;
    if(f.upcoming && e.end<today())return false;
    if(f.official && e.verification!=='Official')return false;
    if(f.favorites&&!saved.has(e.id))return false;
    if(mode==='month'){const first=`${month.getFullYear()}-${String(month.getMonth()+1).padStart(2,'0')}-01`;const lastDate=new Date(month.getFullYear(),month.getMonth()+1,0);const last=`${month.getFullYear()}-${String(month.getMonth()+1).padStart(2,'0')}-${String(lastDate.getDate()).padStart(2,'0')}`;if(e.end<first||e.start>last)return false;}
    if(selectedDay && !(e.start<=selectedDay && e.end>=selectedDay))return false;
    return true;
  });
  if(f.sort==='name')a.sort((a,b)=>a.name.localeCompare(b.name));
  if(f.sort==='latest')a.sort((a,b)=>b.start.localeCompare(a.start));
  if(f.sort==='date')a.sort((a,b)=>a.start.localeCompare(b.start));
  return a;}
  const REGIONS={
    Canada:{AB:'Alberta',BC:'British Columbia',MB:'Manitoba',NB:'New Brunswick',NL:'Newfoundland and Labrador',NT:'Northwest Territories',NS:'Nova Scotia',NU:'Nunavut',ON:'Ontario',PE:'Prince Edward Island',QC:'Quebec',SK:'Saskatchewan',YT:'Yukon'},
    USA:{AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming',DC:'District of Columbia'},
    Mexico:{AGU:'Aguascalientes',BCN:'Baja California',BCS:'Baja California Sur',CAM:'Campeche',CHP:'Chiapas',CHH:'Chihuahua',COA:'Coahuila',COL:'Colima',DUR:'Durango',GUA:'Guanajuato',GRO:'Guerrero',HID:'Hidalgo',JAL:'Jalisco',MEX:'Estado de México',MIC:'Michoacán',MOR:'Morelos',NAY:'Nayarit',NLE:'Nuevo León',OAX:'Oaxaca',PUE:'Puebla',QUE:'Querétaro',ROO:'Quintana Roo',SLP:'San Luis Potosí',SIN:'Sinaloa',SON:'Sonora',TAB:'Tabasco',TAM:'Tamaulipas',TLA:'Tlaxcala',VER:'Veracruz',YUC:'Yucatán',ZAC:'Zacatecas',CMX:'Mexico City'}
  };
  function regionOptions(){const choose=$('#region'),val=choose.value,country=$('#country').value;
    const options=[];
    for(const nation of (country?[country]:['Canada','USA','Mexico'])){
      const known=REGIONS[nation]||{};
      for(const [code,name] of Object.entries(known))options.push({code,label:country?name+' ('+code+')':name+' ('+code+', '+nation+')',country:nation});
    }
    const regions=[...new Set(events.filter(e=>!country||e.country===country).map(e=>e.region).filter(x=>x&&x!=='TBA'&&x!=='Multi'))];
    for(const code of regions)if(!options.some(o=>o.code===code&&(country||o.country===country)))options.push({code,label:code,country:country||''});
    options.sort((a,b)=>sortRegion(a.label,b.label));
    choose.replaceChildren(new Option('All states / provinces',''),...options.map(o=>new Option(o.label,o.code)));
    choose.value=options.some(o=>o.code===val)?val:'';
  }
  function makeTag(name,extra){return el('span',`tag ${extra||''}`,name);}
  function addButton(title,symbol,handler,cls){const b=el('button','icon-btn '+(cls||''),symbol);b.type='button';b.setAttribute('aria-label',title);b.title=title;b.onclick=handler;return b;}
  function downloadOverview(e){
    const escapeHTML=value=>String(value||'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
    const link=(url,label)=>safeURL(url)?'<a href="'+escapeHTML(url)+'">'+escapeHTML(label)+'</a>':'Not published / not verified';
    const row=(label,value)=>'<div class="field"><span>'+escapeHTML(label)+'</span><strong>'+value+'</strong></div>';
    const organizer=link(e.source,'View organizer source ↗');
    const html='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escapeHTML(e.name)+' — Kart Atlas overview</title><style>'+
      '@page{size:letter;margin:13mm}*{box-sizing:border-box}body{font-family:Arial,sans-serif;color:#182634;max-width:850px;margin:0 auto;padding:25px;line-height:1.4}header{border-bottom:4px solid #80bb2e;padding-bottom:13px;margin-bottom:16px}.brand{font-size:15px;font-weight:900;letter-spacing:2px;color:#477a19}h1{font-size:25px;line-height:1.15;margin:8px 0}.subtitle{font-size:13px;color:#45586a}h2{font-size:13px;text-transform:uppercase;letter-spacing:1px;color:#3b6722;margin:17px 0 7px}.field{display:grid;grid-template-columns:145px 1fr;gap:10px;padding:7px 0;border-bottom:1px solid #e1e6eb;font-size:12px}.field span{color:#657484}.field strong{font-weight:600;overflow-wrap:anywhere}a{color:#205e86}.note{background:#f1f5f7;padding:10px;font-size:11px;border-left:3px solid #80bb2e}.footer{border-top:1px solid #dce2e6;margin-top:20px;padding-top:9px;color:#697b87;font-size:10px}.actions{margin:0 0 20px;display:flex;gap:8px}.actions button{padding:10px 16px;background:#243c2c;color:white;border:0;border-radius:5px;cursor:pointer}@media print{body{padding:0}.actions{display:none}a{color:#205e86;text-decoration:underline}h2{break-after:avoid}.field{break-inside:avoid}}'+
      '</style></head><body><div class="actions"><button onclick="window.print()">Print / Save as PDF</button></div><header><div class="brand">KART ATLAS · RACE INFORMATION</div><h1>'+escapeHTML(e.name)+'</h1><div class="subtitle">'+escapeHTML(fmtRange(e))+' · '+escapeHTML([e.city,e.region,e.country].filter(Boolean).join(', '))+'</div></header>'+
      '<h2>Event at a glance</h2>'+row('Organizer',escapeHTML(e.organizer||'Not confirmed'))+row('Track / venue',escapeHTML(e.venue||'Not confirmed'))+row('Racing level',escapeHTML(e.level||'Not confirmed'))+row('Classes',escapeHTML(e.classes||'Not yet confirmed'))+
      '<h2>Registration</h2>'+row('Entry / payment',e.registration_url?link(e.registration_url,'Organizer registration ↗'):'Registration link and entry fees not yet verified')+
      '<h2>Race-day preparation</h2>'+row('Detailed timetable',e.schedule_url?link(e.schedule_url,'Race-day schedule ↗'):'Not yet published or verified')+row('Event / club rules',e.rules_url?link(e.rules_url,'Rules and regulations ↗'):'Not yet published or verified')+row('Track / paddock map',e.track_map_url?link(e.track_map_url,'Track map ↗'):'Not yet published or verified')+
      '<h2>Official information</h2>'+row('Organizer website',organizer)+(e.notes?'<p class="note">'+escapeHTML(e.notes)+'</p>':'')+
      '<p class="footer">Compiled by Kart Atlas from its indexed event listing. This is not an official race bulletin. Confirm dates, eligibility, rules and fees with the organizer before attending. Generated '+escapeHTML(new Date().toLocaleDateString())+'.</p></body></html>';
    const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'}));
    const a=el('a');a.href=url;a.download='kart-atlas-race-overview-'+e.id+'.html';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);
    toast('One-page race overview downloaded');
  }
  function showEvent(e){
    const old=document.querySelector('#event-dialog');if(old)old.remove();
    const dialog=el('dialog','event-dialog');dialog.id='event-dialog';
    const head=el('div','event-dialog-head');
    const heading=el('h2','',e.name);const close=el('button','event-close','✕');close.type='button';close.setAttribute('aria-label','Close event details');close.onclick=()=>dialog.close();
    head.append(heading,close);dialog.append(head);
    const body=el('div','event-dialog-body');
    const intro=el('p','event-intro',fmtRange(e)+' · '+[e.venue,e.city,e.region,e.country].filter(Boolean).join(', '));body.append(intro);
    const meta=el('div','event-detail-tags');[e.level,e.format,e.classes?'Classes: '+e.classes:'Classes not confirmed'].filter(Boolean).forEach(x=>meta.append(makeTag(x)));body.append(meta);
    const section=(title,description,link,label)=>{
      const box=el('section','event-detail-section');box.append(el('h3','',title),el('p','',description));
      if(safeURL(link)){const a=el('a','source-btn',label||'View organizer information ↗');a.href=link;a.target='_blank';a.rel='noopener noreferrer';box.append(a);}
      body.append(box);
    };
    section('Registration & entry fees',e.registration_url?'Registration information from organizer.':'Online registration through Kart Atlas is not available yet. Confirm entry fees and registration with the organizer.',e.registration_url||e.source,e.registration_url?'Open registration ↗':'Check organizer page ↗');
    section('Race-day schedule',e.schedule_url?'Organizer schedule available.':'Detailed session times have not been added for this event. Check the organizer for the latest timetable.',e.schedule_url||e.source,e.schedule_url?'View race schedule ↗':'Check organizer schedule ↗');
    section('Rules & regulations',e.rules_url?'Organizer regulations available.':'Event-specific and club regulations have not been verified in Kart Atlas. Always consult the organizer before competing.',e.rules_url||e.source,e.rules_url?'View regulations ↗':'Check organizer rules ↗');
    section('Track & paddock maps',e.track_map_url?'Track map provided by organizer.':'A verified downloadable track or paddock map has not been added for this event.',e.track_map_url,e.track_map_url?'Open track map ↗':'');
    if(e.notes)section('Additional information',e.notes);
    if(safeURL(e.source))section('Original event source',e.verification==='Official'?'Organizer source used for this listing. Reconfirm details before travel.':'Listing source. Details require confirmation.',e.source,'Open event source ↗');
    const foot=el('div','event-dialog-foot');const overview=el('button','primary-btn','↓ Download 1-page overview');overview.type='button';overview.onclick=()=>downloadOverview(e);foot.append(overview);const cal=el('button','primary-btn','Add to calendar ↓');cal.onclick=()=>downloadICS(e);foot.append(cal);body.append(foot);
    dialog.append(body);document.body.append(dialog);dialog.addEventListener('close',()=>dialog.remove(),{once:true});dialog.showModal();
  }
  function makeCard(e){
    const card=el('article','event-card');const date=el('div','date-box');const dt=ymd(e.start);
    date.append(el('span','',monthNames[dt.getMonth()]+' '+dt.getFullYear()),el('b','',String(dt.getDate()).padStart(2,'0')));
    const main=el('div','event-main');const badges=el('div','event-badges');
    badges.append(makeTag(e.level,(e.level||'').toLowerCase()),makeTag(e.verification==='Official'?'Reviewed organizer source':e.verification==='Automated'?'Organizer feed · unreviewed':'Secondary listing',e.verification==='Official'?'official':e.verification==='Automated'?'automated':'secondary'));
    if(e.format && e.format!=='Sprint')badges.append(makeTag(e.format));
    const name=el('h3','',e.name);const venue=el('div','venue',`${e.venue || 'Venue TBA'}${e.city?' · '+e.city:''}${e.region?', '+e.region:''}`);
    const meta=el('div','meta');meta.append(el('span','',fmtRange(e)),el('span','',e.organizer || 'Organizer not listed'));
    main.append(badges,name,venue,meta);
    if(e.classes)main.append(el('p','details',`Classes: ${e.classes}`));
    const actions=el('div','event-actions');
    const detail=el('button','source-btn','Event details →');detail.type='button';detail.onclick=()=>showEvent(e);actions.append(detail);
    const fav=addButton(saved.has(e.id)?'Remove from saved races':'Save race','★',()=>{if(saved.has(e.id))saved.delete(e.id);else saved.add(e.id);persist();refresh();toast(saved.has(e.id)?'Race saved on this device':'Race removed from saved list');},saved.has(e.id)?'saved':'');
    fav.setAttribute('aria-pressed',String(saved.has(e.id)));actions.append(fav);
    actions.append(addButton('Add this race to my calendar','▦',()=>downloadICS(e)));
    if(safeURL(e.source)){
      const source=el('a','source-btn','Official page ↗');source.href=e.source;source.target='_blank';source.rel='noopener noreferrer';
      if(e.verification!=='Official')source.textContent='Check source ↗';
      source.setAttribute('aria-label',`View original source for ${e.name}`);actions.append(source);
    }
    card.append(date,main,actions);return card;
  }
  function icsEscape(s){return (s||'').replace(/\\/g,'\\\\').replace(/\n/g,'\\n').replace(/,/g,'\\,').replace(/;/g,'\\;');}
  function dateAfter(s){const d=ymd(s);d.setDate(d.getDate()+1);return `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}`;}
  function downloadICS(e){
    const loc=[e.venue,e.city,e.region,e.country].filter(Boolean).join(', ');
    const url=safeURL(e.source);
    const desc=`Verify event date and classes with organizer. ${e.organizer||''}${url?' | '+url:''}`;
    const out=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Kart Atlas//Race Finder//EN','CALSCALE:GREGORIAN','BEGIN:VEVENT',
      `UID:${e.id}@kartatlas.local`,`DTSTART;VALUE=DATE:${e.start.replace(/-/g,'')}`,`DTEND;VALUE=DATE:${dateAfter(e.end)}`,
      `SUMMARY:${icsEscape(e.name)}`,`LOCATION:${icsEscape(loc)}`,`DESCRIPTION:${icsEscape(desc)}`,
      ...(url?[`URL:${url}`]:[]),'END:VEVENT','END:VCALENDAR'].join('\r\n')+'\r\n';
    const a=el('a');a.href=URL.createObjectURL(new Blob([out],{type:'text/calendar;charset=utf-8'}));a.download=`kart-atlas-${e.id}.ics`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),30000);
    toast('Race calendar file downloaded');
  }
  function calendarView(data){
    const shell=$('#calendar');shell.replaceChildren();const nav=el('div','month-nav');
    const prev=el('button','','←');prev.type='button';prev.setAttribute('aria-label','Previous month');
    const next=el('button','','→');next.type='button';next.setAttribute('aria-label','Next month');
    prev.onclick=()=>{month.setMonth(month.getMonth()-1);selectedDay='';refresh();};
    next.onclick=()=>{month.setMonth(month.getMonth()+1);selectedDay='';refresh();};
    const label=el('strong','',month.toLocaleDateString('en-US',{month:'long',year:'numeric'}));nav.append(prev,label,next);shell.append(nav);
    const grid=el('div','month-grid');for(const t of ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'])grid.append(el('div','week-head',t));
    const start=new Date(month.getFullYear(),month.getMonth(),1),ndays=new Date(month.getFullYear(),month.getMonth()+1,0).getDate();
    for(let i=0;i<start.getDay();i++)grid.append(el('div','day blank'));
    // Visible counts reflect all matching filters except selected day, so dates remain discoverable.
    const savedDay=selectedDay;selectedDay='';const counts=filtered();selectedDay=savedDay;
    for(let day=1;day<=ndays;day++){
      const str=`${month.getFullYear()}-${String(month.getMonth()+1).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
      const n=counts.filter(e=>e.start<=str&&e.end>=str).length;
      const b=el('button','day'+(n?' has-event':'')+(selectedDay===str?' selected':''));b.type='button';b.setAttribute('aria-label',`${fmtDate(str)}: ${n} listed race${n===1?'':'s'}`);b.append(el('strong','',String(day)));
      if(n)b.append(el('span','dot',String(n)+' race'+(n===1?'':'s')));
      b.onclick=()=>{selectedDay=selectedDay===str?'':str;count=25;refresh();};
      grid.append(b);
    }
    shell.append(grid,el('p','month-hint','Tap a date to show races happening that day. Tap it again to clear the selection.'));
  }
  function refresh(){
    const a=filtered();$('#result-count').textContent=a.length;$('#result-context').textContent=(selectedDay?`Selected day: ${fmtDate(selectedDay)} · `:'')+`${a.length} matching races · Listings checked against organizer sources where available · Not a complete North American inventory`;
    $('#cards').replaceChildren(...a.slice(0,count).map(makeCard));
    $('#empty').classList.toggle('hidden',a.length!==0);
    if(!a.length)$('#empty').querySelector('p').textContent='No races currently indexed for these filters. This does not mean there are no races in this location; coverage is still expanding.';
    $('#more').classList.toggle('hidden',a.length<=count);
    $('#more').textContent=`Show more races (${Math.min(a.length-count,25)} of ${a.length-count} remaining) ↓`;
    $('#calendar').classList.toggle('hidden',mode!=='month');
    $('#map-panel').classList.toggle('hidden',mode!=='map');
    $('#cards').classList.toggle('hidden',mode==='map');
    $('#more').classList.toggle('hidden',mode==='map'||a.length<=count);
    if(mode==='map')renderMap(a);
    if(mode==='month')calendarView(a);
  }
  function reset(){
    $('#search').value='';$('#country').value='';$('#region').value='';$('#level').value='';$('#class-filter').value='';$('#from').value='';$('#to').value='';$('#upcoming').checked=true;$('#official').checked=false;$('#favorites').checked=false;$('#sort').value='date';selectedDay='';count=25;regionOptions();refresh();
  }
  async function start(){
    let data;
    try{
      const doc=window.__KART_ATLAS_EMBEDDED__ || (async () => { const r=await fetch('/events.json',{cache:'no-cache'});if(!r.ok)throw Error(r.status);return r.json(); })();
      data=await doc;events=data.events||[];snapshot=data.updated||'';
    }catch(err){$('#result-context').textContent='Could not load the event directory. Please check your connection and reload.';console.error(err);return;}
    $('#stat-races').textContent=events.length;
    $('#stat-tracks').textContent=new Set(events.map(e=>e.venue).filter(Boolean)).size;
    $('#stat-countries').textContent=new Set(events.map(e=>e.country).filter(Boolean)).size;
    $('#stat-upcoming').textContent=events.filter(e=>e.end>=today()).length;
    $('#snapshot').textContent=`Original research: ${snapshot} · Auto-imported feed events: ${data.auto_imported||0}. Other clubs require review.`;
    fetch('/monitor_status.json',{cache:'no-cache'}).then(r=>r.ok?r.json():null).then(status=>{if(status&&status.last_attempt){const date=new Date(status.last_attempt).toLocaleDateString();$('#snapshot').textContent+=` Last monitored: ${date} · ${status.checked}/${status.total} sources reached.`;}}).catch(()=>{});
    regionOptions();
    for(const id of ['search','country','region','level','class-filter','from','to','upcoming','official','favorites','sort']){
      const element=$('#'+id);element.addEventListener(id==='search'?'input':'change',()=>{if(id==='country')regionOptions();count=25;selectedDay='';refresh();});
    }
    $('#reset').onclick=reset;$('#empty-reset').onclick=reset;
    $('#more').onclick=()=>{count+=25;refresh();};
    for(const [id,value] of [['list-view','list'],['month-view','month'],['map-view','map']]){$('#'+id).onclick=()=>{mode=value;selectedDay='';$all('.view-btn').forEach(b=>{b.classList.toggle('active',b.id===id);b.setAttribute('aria-pressed',String(b.id===id));});refresh();};}
    refresh();
  }
  window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredInstall=e;$('#install-btn').classList.remove('hidden');});
  $('#install-btn').onclick=async()=>{if(!deferredInstall)return;deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null;$('#install-btn').classList.add('hidden');};
  if('serviceWorker'in navigator && location.protocol==='https:')window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
  start().catch(err => {
    console.error('Kart Atlas calendar initialization failed:', err);
    const context = document.querySelector('#result-context');
    if (context) context.textContent = 'Calendar display error: ' + (err && err.message ? err.message : String(err)) + '. Please send this message to the site administrator.';
  });
})();
