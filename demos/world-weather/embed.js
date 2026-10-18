/* Same-origin embed: keep the standalone tool and its saved clocks as one implementation. */
(() => {
  'use strict';
  if(window.parent===window||new URLSearchParams(location.search).get('embed')!=='more')return;
  document.documentElement.dataset.embed='more';
  document.body.dataset.embed='more';
  const report=()=>window.parent.postMessage({type:'ofel-world-height',height:Math.max(320,Math.ceil(document.body.getBoundingClientRect().height))},location.origin);
  window.addEventListener('message',event=>{if(event.origin===location.origin&&event.source===window.parent&&event.data?.type==='ofel-world-request-height')report();});
  if(typeof ResizeObserver!=='undefined')new ResizeObserver(report).observe(document.body);
  window.addEventListener('load',report);window.addEventListener('resize',report);
  document.fonts?.ready.then(report);requestAnimationFrame(report);
})();
