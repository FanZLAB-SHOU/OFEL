(() => {
  'use strict';
  const root=document.querySelector('[data-more-stats]');if(!root)return;
  const M=MoreData,fmt=value=>value===null||value===undefined?'—':value.toLocaleString('en-US');
  const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
  const counter=root.querySelector('[data-visit-reels]'),counterText=root.querySelector('[data-visit-accessible]');
  let lastTotal;
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
  const label=day=>new Date(day+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',timeZone:'UTC'});
  function renderDaily(stats) {
    const chart=root.querySelector('[data-stats-daily]'),table=root.querySelector('[data-stats-daily-table]');chart.replaceChildren();table.replaceChildren();
    const max=Math.max(1,...stats.values.filter(value=>value!==null)),step=10**Math.floor(Math.log10(max)),top=Math.ceil(max/step)*step;
    const cols=document.createElement('div');cols.className='pulse-cols';
    for(const value of [top/2,top].filter(Number.isInteger)){
      const line=document.createElement('span');line.className='pulse-gridline';line.style.bottom=`${value/top*100}%`;const text=document.createElement('small');text.textContent=fmt(value);line.append(text);cols.append(line);
    }
    stats.values.forEach((value,index)=>{
      const day=stats.days[index],col=document.createElement('button');col.type='button';col.className='pulse-col'+(value===null?' is-missing':'');
      const description=value===null?(stats.tracking&&day>=stats.tracking?'Not recorded yet':'Before tracking began'):`${fmt(value)} visit${value===1?'':'s'}${index===13?' so far today':''}`;
      col.setAttribute('aria-label',`${label(day)}: ${description}`);
      const bar=document.createElement('span');bar.className='pulse-bar';bar.style.height=value===null?'3px':`${value/top*100}%`;col.append(bar);
      const show=()=>showTip(col,description,label(day));
      col.addEventListener('pointerenter',show);col.addEventListener('focus',show);col.addEventListener('click',show);col.addEventListener('pointerleave',hideTip);col.addEventListener('blur',hideTip);cols.append(col);
      const tr=document.createElement('tr');for(const text of [day,fmt(value)]){const cell=document.createElement('td');cell.textContent=text;tr.append(cell);}table.append(tr);
    });
    const axis=document.createElement('div');axis.className='pulse-axis';for(const index of [0,7,13]){const text=document.createElement('span');text.textContent=label(stats.days[index]);axis.append(text);}chart.append(cols,axis);
  }
  // Worldwide totals arrive from the Busuanzi script into hidden spans; nightly snapshots give the daily figures.
  const worldPV=root.querySelector('[data-worldwide-total]'),worldUV=root.querySelector('[data-worldwide-visitors]');
  const source=root.querySelector('[data-stats-source]').href;
  const status=root.querySelector('[data-stats-status]'),refresh=root.querySelector('[data-refresh-stats]');
  let live=null,store=null,storeFailed=false;
  function render() {
    const stats=M.series(store,live);
    root.querySelector('[data-stat="week"]').textContent=fmt(stats.week);root.querySelector('[data-stat="today"]').textContent=fmt(stats.todayVisits);
    renderDaily(stats);
    status.textContent=storeFailed?'Daily figures are temporarily unavailable. Live totals, world clocks and weather still work.'
      :!stats.tracking?'Daily figures begin with the first nightly snapshot at 00:00 Beijing time.'
      :`Daily figures from snapshots taken at 00:00 Beijing time since ${label(stats.tracking)}.${live===null?' Waiting for the live total…':''}`;
  }
  async function loadStore(force=false) {
    refresh.disabled=true;root.querySelector('[data-pulse-panels]').setAttribute('aria-busy','true');
    try{const response=await fetch(force?`${source}?t=${Date.now()}`:source,{cache:force?'no-store':'default'});if(!response.ok)throw Error('Snapshots unavailable');store=await response.json();storeFailed=false;}
    catch{storeFailed=true;}
    finally{refresh.disabled=false;root.querySelector('[data-pulse-panels]').setAttribute('aria-busy','false');}
    render();
  }
  let tries=0;
  (function pollLive(){
    const pv=M.parseLive(worldPV?.textContent);
    if(pv!==null){live=pv;animateTotal(pv);root.querySelector('[data-stat="visitors"]').textContent=fmt(M.parseLive(worldUV?.textContent));root.querySelector('[data-counter-state]').textContent='Visits from around the world, including mainland China.';render();return;}
    if(++tries<=20)setTimeout(pollLive,500);
    else{animateTotal(null);root.querySelector('[data-counter-state]').textContent='The counter is taking a moment. You’re always welcome here.';}
  })();
  refresh.addEventListener('click',()=>loadStore(true));loadStore();
})();
