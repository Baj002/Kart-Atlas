/* Registration is evaluated in the browser so deadlines also work offline. */
(function(root){
  'use strict';
  const timestamp=value=>typeof value==='string' && /T.*(?:Z|[+-]\d{2}:?\d{2})$/.test(value) && Number.isFinite(Date.parse(value))?Date.parse(value):null;
  const safeLink=value=>{try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password?u.href:null;}catch{return null;}};
  function registrationInfo(event,now=new Date()){
    const clock=now.getTime(),deadline=timestamp(event.registration_deadline),opens=timestamp(event.registration_opens_at),checked=timestamp(event.registration_checked_at);
    const fresh=checked!==null && clock-checked>=-300000 && clock-checked<=48*3600000;
    const url=safeLink(event.registration_url),evidence=safeLink(event.registration_evidence);
    const verified=fresh&&Boolean(evidence),raw=event.registration_status;
    let status='not_announced',label='Not announced',message='No verified registration announcement in Kart Atlas yet.';
    const localDay=[now.getFullYear(),String(now.getMonth()+1).padStart(2,'0'),String(now.getDate()).padStart(2,'0')].join('-');
    if(event.status==='cancelled'||event.status==='postponed'){
      status='unavailable';label=event.status==='cancelled'?'Event cancelled':'Event postponed';message='Check the organizer before entering.';
    }else if(event.end && event.end<localDay){status='closed';label='Event ended';message='This event has already finished.';
    }else if(deadline!==null&&evidence&&deadline<=clock){status='closed';label='Deadline passed';message='The published online deadline has passed. Ask the organizer about late entries.';
    }else if(verified&&raw==='sold_out'){status='closed';label='Sold out';message='Check the organizer for a waiting list.';
    }else if(verified&&raw==='closed'){status='closed';label='Closed';message='The registration provider reports entries closed.';
    }else if(verified&&opens!==null&&opens>clock){status='not_open';label='Opens soon';message='Registration has a published opening date.';
    }else if(verified&&raw==='open'){
      status=deadline!==null&&deadline-clock<=7*86400000?'closing_soon':'open';label=status==='closing_soon'?'Closing soon':'Open';message=status==='closing_soon'?'Online registration closes within 7 days.':'The registration provider reports entries open.';
    }else if(url||deadline!==null||checked!==null){status='unconfirmed';label='Check status';message=checked!==null&&!fresh?'Registration status needs a fresh check. Confirm with the organizer.':'A registration page is available; entry availability is not confirmed.';}
    const format=value=>new Intl.DateTimeFormat(undefined,{year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(value));
    return {status,label,message,url,evidence,fresh:verified,deadline:deadline!==null?format(deadline):null,opens:opens!==null?format(opens):null,checked:checked!==null?format(checked):null,action:status==='open'||status==='closing_soon'?'Register ↗':'Registration page ↗'};
  }
  root.KartRegistration={registrationInfo};
  if(typeof module!=='undefined'&&module.exports)module.exports=root.KartRegistration;
})(typeof globalThis!=='undefined'?globalThis:this);
