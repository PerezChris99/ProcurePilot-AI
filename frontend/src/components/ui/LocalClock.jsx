import {useEffect,useState} from 'react';
import {Clock3} from 'lucide-react';

function browserTime(now){
  const localZone=Intl.DateTimeFormat().resolvedOptions().timeZone||'UTC';
  const language=typeof navigator==='undefined'?'en-GB':navigator.language||'en-GB';
  const clock=new Intl.DateTimeFormat(language,{
    hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false,timeZone:localZone,
  }).format(now);
  const date=new Intl.DateTimeFormat(language,{
    weekday:'short',day:'2-digit',month:'short',year:'numeric',timeZone:localZone,
  }).format(now);
  const offsetParts=new Intl.DateTimeFormat('en-US',{
    timeZone:localZone,timeZoneName:'longOffset',
  }).formatToParts(now);
  const offset=offsetParts.find(part=>part.type==='timeZoneName')?.value||'GMT';
  return {clock,date,zone:localZone,offset};
}

/** This clock intentionally reflects the visitor's browser clock and time zone. */
export default function LocalClock(){
  const [now,setNow]=useState(()=>new Date());
  useEffect(()=>{
    const refresh=()=>setNow(new Date());
    const timer=window.setInterval(refresh,1000);
    document.addEventListener('visibilitychange',refresh);
    window.addEventListener('focus',refresh);
    return ()=>{
      window.clearInterval(timer);
      document.removeEventListener('visibilitychange',refresh);
      window.removeEventListener('focus',refresh);
    };
  },[]);
  const {clock,date,zone,offset}=browserTime(now);
  return <div className="workspace-clock" aria-label={'Local date and time: '+date+', '+clock+', '+zone+' '+offset}
      title="Live time from this device. Check your operating-system time settings for accuracy.">
    <Clock3 size={17} aria-hidden="true"/>
    <div className="workspace-clock-values">
      <time dateTime={now.toISOString()} className="workspace-clock-time">{clock}</time>
      <span className="workspace-clock-date">{date}</span>
      <span className="workspace-clock-zone">{zone} · {offset}</span>
    </div>
  </div>;
}
