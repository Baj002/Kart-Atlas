(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $all = (s, root = document) => [...root.querySelectorAll(s)];
  const el = (type, cls, text) => { const node=document.createElement(type);if(cls)node.className=cls;if(text!==undefined)node.textContent=text;return node;};
  let events=[], snapshot='', count=25, mode='list', month=new Date(new Date().getFullYear(),new Date().getMonth(),1), selectedDay='';
  let deferredInstall = null;
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
    for(const [id,value] of [['list-view','list'],['month-view','month']]){$('#'+id).onclick=()=>{mode=value;selectedDay='';$all('.view-btn').forEach(b=>{b.classList.toggle('active',b.id===id);b.setAttribute('aria-pressed',String(b.id===id));});refresh();};}
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
