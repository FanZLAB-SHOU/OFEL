/* Visit statistics from Busuanzi: live running totals plus one nightly snapshot (00:00 Beijing time).
   Each snapshot reading is itself counted by Busuanzi, so the cumulative `reads` are subtracted. */
const MoreData = (() => {
  'use strict';
  const DAY=86400000,BEIJING=8*3600000;
  const beijingDate=ms=>new Date(ms+BEIJING).toISOString().slice(0,10);
  const shift=(date,days)=>new Date(Date.parse(date+'T00:00:00Z')+days*DAY).toISOString().slice(0,10);
  const isCount=value=>Number.isSafeInteger(value)&&value>=0;
  function snapshots(store) {
    const list=Array.isArray(store?.snapshots)?store.snapshots:[];
    return list.filter(s=>/^\d{4}-\d{2}-\d{2}$/.test(s?.date)&&isCount(s.site_pv)&&isCount(s.site_uv)&&isCount(s.reads)).sort((a,b)=>a.date<b.date?-1:a.date>b.date?1:0);
  }
  function parseLive(text) {
    const clean=String(text??'').replace(/[,\s]/g,'');
    return /^\d+$/.test(clean)&&Number.isSafeInteger(Number(clean))?Number(clean):null;
  }
  // Fourteen Beijing dates ending today; past days come from consecutive snapshots, today from the live total.
  function series(store,live,now=Date.now()) {
    const list=snapshots(store),byDate=new Map(list.map(s=>[s.date,s])),today=beijingDate(now);
    const days=Array.from({length:14},(_,i)=>shift(today,i-13));
    const real=s=>s.site_pv-s.reads,last=list.at(-1);
    const liveReal=isCount(live)&&last&&live>=last.site_pv?live-last.reads:null;
    const values=days.map(day=>{
      const s=byDate.get(day);if(!s)return null;
      if(day===today)return liveReal===null?null:Math.max(0,liveReal-real(s));
      const next=byDate.get(shift(day,1));return next?Math.max(0,real(next)-real(s)):null;
    });
    // Past 7 days = today plus the six days before it; while tracking is newer than that, count from the first snapshot.
    const start=list.find(s=>s.date>=days[7]&&s.date<=today);
    const week=liveReal!==null&&start?Math.max(0,liveReal-real(start)):null;
    return {today,days,values,todayVisits:values[13],week,tracking:list.length?list[0].date:null};
  }
  function frameHeight(event,origin,source) {
    const height=event.data?.height;
    return event.origin===origin&&event.source===source&&event.data?.type==='ofel-world-height'&&Number.isFinite(height)&&height>=320&&height<=20000?Math.ceil(height):null;
  }
  function reelDigits(number) {
    if(!Number.isSafeInteger(number)||number<0)return null;
    return String(number).padStart(6,'0').split('').map(Number);
  }
  return {beijingDate,shift,snapshots,parseLive,series,frameHeight,reelDigits};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=MoreData;
