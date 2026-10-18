/* Public GoatCounter counts are visits, not a globally ordered visitor register. */
const MoreData = (() => {
  'use strict';
  const TTL=600000;
  const iso=date=>date.toISOString().slice(0,10);
  function dates(now=Date.now()) {
    const instant=new Date(now),today=new Date(Date.UTC(instant.getUTCFullYear(),instant.getUTCMonth(),instant.getUTCDate()));
    const day=offset=>new Date(today.getTime()+offset*86400000);
    return {key:iso(today),days:Array.from({length:14},(_,i)=>iso(day(i-13))),week:iso(day(-6)),end:iso(day(1))};
  }
  function parseCount(data) {
    const value=data?.count;
    if(typeof value!=='number'&&(typeof value!=='string'||!/^\d[\d,\s]*$/.test(value.trim())))throw Error('Invalid visit count');
    const number=Number(typeof value==='string'?value.replace(/[,\s]/g,''):value);
    if(!Number.isSafeInteger(number)||number<0)throw Error('Invalid visit count');
    return number;
  }
  function counterURL(base,path,start,end) {
    const url=new URL(`${base}/counter/${path==='TOTAL'?'TOTAL':encodeURIComponent(path)}.json`);
    if(start)url.searchParams.set('start',start);if(end)url.searchParams.set('end',end);return url.href;
  }
  async function pool(tasks,size=4) {
    const result=new Array(tasks.length);let next=0;
    await Promise.all(Array.from({length:Math.min(size,tasks.length)},async()=>{
      while(next<tasks.length){const index=next++;try{result[index]=await tasks[index]();}catch{result[index]=null;}}
    }));return result;
  }
  class StatsClient {
    constructor(base,pages,fetcher,storage=null,now=()=>Date.now()) {Object.assign(this,{base,pages,fetcher,storage,now});}
    async count(path,start,end) {
      const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),9000);
      try {
        const response=await this.fetcher(counterURL(this.base,path,start,end),{signal:controller.signal});
        if(response.status===404&&path!=='TOTAL')return 0;
        if(!response.ok)throw Error('Counter unavailable');
        return parseCount(await response.json());
      }finally{clearTimeout(timer);}
    }
    async load({force=false,onTotal=()=>{}}={}) {
      const calendar=dates(this.now()),key='ofel-more-stats-v2',fingerprint=JSON.stringify(this.pages.map(p=>p.path));
      try {
        const entry=JSON.parse(this.storage?.getItem(key)||'null'),age=this.now()-entry?.fetchedAt;
        if(!force&&entry&&entry.day===calendar.key&&entry.fingerprint===fingerprint&&age>=0&&age<TTL&&Number.isSafeInteger(entry.total)&&entry.total>=0&&entry.days?.length===14&&entry.pages?.length===this.pages.length){onTotal(entry.total,entry.fetchedAt,true);return {...entry,cached:true};}
      }catch{}
      const empty={day:calendar.key,total:null,week:null,days:Array(14).fill(null),pages:Array(this.pages.length).fill(null),fetchedAt:this.now(),fingerprint};
      let total;
      try{total=await this.count('TOTAL');}catch{return empty;}
      onTotal(total,this.now(),false);
      const tasks=[()=>this.count('TOTAL',calendar.week,calendar.end),...calendar.days.map((day,i)=>()=>this.count('TOTAL',day,i===13?calendar.end:calendar.days[i+1])),...this.pages.map(page=>()=>this.count(page.path))];
      const result=await pool(tasks),data={...empty,total,week:result[0],days:result.slice(1,15),pages:result.slice(15),fetchedAt:this.now()};
      // Retry incomplete snapshots on the next visit instead of caching failed requests.
      if(result.every(value=>value!==null))try{this.storage?.setItem(key,JSON.stringify(data));}catch{}
      return data;
    }
  }
  function frameHeight(event,origin,source) {
    const height=event.data?.height;
    return event.origin===origin&&event.source===source&&event.data?.type==='ofel-world-height'&&Number.isFinite(height)&&height>=320&&height<=20000?Math.ceil(height):null;
  }
  function reelDigits(number) {
    if(!Number.isSafeInteger(number)||number<0)return null;
    return String(number).padStart(6,'0').split('').map(Number);
  }
  return {TTL,dates,parseCount,counterURL,pool,StatsClient,frameHeight,reelDigits};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=MoreData;
