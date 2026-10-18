(() => {
  'use strict';
  const root=document.querySelector('[data-more-stats]');if(!root)return;
  const M=MoreData,pages=JSON.parse(root.dataset.statsPages||'[]'),fmt=value=>value===null||value===undefined?'—':value.toLocaleString('en-US');
  let storage;try{storage=sessionStorage;}catch{}
  const client=new M.StatsClient(root.dataset.goatcounter,pages,(...args)=>fetch(...args),storage);
  const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
  const counter=root.querySelector('[data-visit-reels]'),counterText=root.querySelector('[data-visit-accessible]');
  let lastTotal;
  // Worldwide totals come from Busuanzi (it fills the hidden spans); GoatCounter only stands in if Busuanzi never answers.
  const worldPV=root.querySelector('[data-worldwide-total]'),worldUV=root.querySelector('[data-worldwide-visitors]');
  const readCount=element=>{const text=String(element?.textContent??'').replace(/[,\s]/g,'');return /^\d+$/.test(text)?Number(text):null;};
  let worldTotal=null,goatTotal=null,worldTries=0;
  const worldGaveUp=()=>worldTries>16;
  function animateTotal(total) {
    root.querySelector('[data-stat="total"]').textContent=fmt(total);
    if(total===lastTotal)return;lastTotal=total;
    counter.replaceChildren();counterText.textContent=total===null?'Visit count unavailable':`${fmt(total)} recorded visits to OFEL`;
    const digits=M.reelDigits(total);
    if(!digits){counter.textContent='—';return;}
    counter.style.setProperty('--digit-count',digits.length);
    digits.forEach((value,index)=>{
      const reel=document.createElement('span');reel.className='visit-reel';
      const strip=document.createElement('span');strip.className='visit-strip';
      for(let n=0;n<20;n++){const digit=document.createElement('span');digit.textContent=String(n%10);strip.append(digit);}
      reel.append(strip);counter.append(reel);
      if(motion.matches)strip.style.transform=`translateY(-${value*1.15}em)`;
      else requestAnimationFrame(()=>requestAnimationFrame(()=>{strip.style.transition=`transform ${1250+index*85}ms cubic-bezier(.18,.76,.23,1)`;strip.style.transform=`translateY(-${(10+value)*1.15}em)`;}));
    });
  }
  function updateClock(){root.querySelector('[data-observatory-clock]').textContent=new Intl.DateTimeFormat('en-GB',{timeZone:'Asia/Shanghai',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(new Date());}
  updateClock();setInterval(updateClock,1000);
  (function pollWorldwide(){
    const pv=readCount(worldPV);
    if(pv!==null){worldTotal=pv;animateTotal(pv);root.querySelector('[data-stat="visitors"]').textContent=fmt(readCount(worldUV));root.querySelector('[data-counter-state]').textContent='Visits from around the world, including mainland China.';return;}
    if(++worldTries<=16)setTimeout(pollWorldwide,500);else if(goatTotal!==null)animateTotal(goatTotal);
  })();
  const frame=root.querySelector('[data-world-frame]');
  window.addEventListener('message',event=>{const height=M.frameHeight(event,location.origin,frame.contentWindow);if(height!==null)frame.style.height=`${height}px`;});
  const requestHeight=()=>frame.contentWindow.postMessage({type:'ofel-world-request-height'},location.origin);
  frame.addEventListener('load',requestHeight);requestHeight();
  const tooltip=root.querySelector('.pulse-tooltip');
  function showTip(element,value,date) {
    tooltip.querySelector('strong').textContent=value;tooltip.querySelector('span').textContent=date;tooltip.hidden=false;
    const a=element.getBoundingClientRect(),b=root.getBoundingClientRect();
    tooltip.style.left=`${Math.max(8,Math.min(a.left-b.left+a.width/2-tooltip.offsetWidth/2,b.width-tooltip.offsetWidth-8))}px`;
    tooltip.style.top=`${a.top-b.top-tooltip.offsetHeight-8}px`;
  }
  const hideTip=()=>{tooltip.hidden=true;};
  function renderDaily(data) {
    const calendar=M.dates(new Date(data.day+'T12:00:00Z').getTime());
    const chart=root.querySelector('[data-stats-daily]'),table=root.querySelector('[data-stats-daily-table]');chart.replaceChildren();table.replaceChildren();
    const label=day=>new Date(day+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'});
    const max=Math.max(1,...data.days.filter(value=>value!==null)),step=10**Math.floor(Math.log10(max)),top=Math.ceil(max/step)*step;
    const cols=document.createElement('div');cols.className='pulse-cols';
    for(const value of [top/2,top].filter(Number.isInteger)){
      const line=document.createElement('span');line.className='pulse-gridline';line.style.bottom=`${value/top*100}%`;const text=document.createElement('small');text.textContent=fmt(value);line.append(text);cols.append(line);
    }
    data.days.forEach((value,index)=>{
      const col=document.createElement('button');col.type='button';col.className='pulse-col'+(value===null?' is-missing':'');
      const description=value===null?'Data unavailable':`${fmt(value)} visit${value===1?'':'s'}`;
      col.setAttribute('aria-label',`${label(calendar.days[index])}: ${description}`);
      const bar=document.createElement('span');bar.className='pulse-bar';bar.style.height=value===null?'3px':`${value/top*100}%`;col.append(bar);
      const show=()=>showTip(col,description,label(calendar.days[index]));
      col.addEventListener('pointerenter',show);col.addEventListener('focus',show);col.addEventListener('click',show);col.addEventListener('pointerleave',hideTip);col.addEventListener('blur',hideTip);cols.append(col);
      const tr=document.createElement('tr');for(const text of [calendar.days[index],fmt(value)]){const cell=document.createElement('td');cell.textContent=text;tr.append(cell);}table.append(tr);
    });
    const axis=document.createElement('div');axis.className='pulse-axis';for(const index of [0,7,13]){const text=document.createElement('span');text.textContent=label(calendar.days[index]);axis.append(text);}chart.append(cols,axis);
  }
  function renderPages(values) {
    const list=root.querySelector('[data-stats-pages-list]');list.replaceChildren();
    const rows=pages.map((page,index)=>({...page,count:values[index]})).filter(page=>page.count>0).sort((a,b)=>b.count-a.count).slice(0,5);
    if(!rows.length){const item=document.createElement('li');item.className='pulse-empty';item.textContent=values.every(value=>value===null)?'Page statistics are temporarily unavailable.':'No visits recorded for these sections yet.';list.append(item);return;}
    rows.forEach((page,index)=>{
      const item=document.createElement('li'),rank=document.createElement('span'),link=document.createElement('a'),count=document.createElement('strong'),track=document.createElement('span'),fill=document.createElement('span');
      rank.className='pulse-rank';rank.textContent=String(index+1).padStart(2,'0');link.href=page.path;link.textContent=page.title;count.textContent=fmt(page.count);track.className='pulse-track';fill.style.width=`${page.count/rows[0].count*100}%`;track.append(fill);item.append(rank,link,count,track);list.append(item);
    });
  }
  const refresh=root.querySelector('[data-refresh-stats]'),status=root.querySelector('[data-stats-status]');
  async function load(force=false) {
    refresh.disabled=true;root.querySelector('[data-pulse-panels]').setAttribute('aria-busy','true');
    status.textContent='Reading the latest published statistics…';
    try {
      const data=await client.load({force,onTotal:total=>{goatTotal=total;if(worldTotal===null&&worldGaveUp()){animateTotal(total);root.querySelector('[data-counter-state]').textContent='Recorded visits · thank you for being part of them.';}}});
      goatTotal=data.total;if(worldTotal===null&&(worldGaveUp()||data.total===null))animateTotal(data.total);root.querySelector('[data-stat="week"]').textContent=fmt(data.week);root.querySelector('[data-stat="today"]').textContent=fmt(data.days[13]);
      renderDaily(data);renderPages(data.pages);
      const fetched=new Date(data.fetchedAt).toLocaleTimeString('en-GB',{timeZone:'UTC',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
      const partial=data.total===null||data.week===null||data.days.includes(null)||data.pages.includes(null);
      status.textContent=data.total===null?'Trend statistics are temporarily unavailable. Totals, world clocks and weather still work.':`${data.cached?'Saved snapshot':'Snapshot checked'} at ${fetched} UTC.${partial?' Some statistics are unavailable.':''} Public counters may take up to four hours to update.`;
      if(data.total===null&&worldTotal===null)root.querySelector('[data-counter-state]').textContent='The counter is taking a moment. You’re always welcome here.';
    }catch{if(worldTotal===null)animateTotal(null);status.textContent='Statistics are temporarily unavailable. Please try again shortly.';root.querySelector('[data-counter-state]').textContent='You’re always welcome here.';}
    finally{refresh.disabled=false;root.querySelector('[data-pulse-panels]').setAttribute('aria-busy','false');}
  }
  refresh.addEventListener('click',()=>load(true));load();
})();
