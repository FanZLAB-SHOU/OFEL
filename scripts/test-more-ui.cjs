/* Exercise the actual UI scripts with a minimal DOM; this is not browser visual QA. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {pathToFileURL,fileURLToPath}=require('node:url'),path=require('node:path');
// The embedded page must be dark before JavaScript executes, with working rebased assets.
const embeddedFile=path.resolve('demos/world-weather/embed/index.html'),embeddedSource=fs.readFileSync(embeddedFile,'utf8');
assert.match(embeddedSource,/<html[^>]*data-embed="more"[^>]*style="[^"]*background:#081b2c/);
assert.match(embeddedSource,/<body[^>]*data-embed="more"[^>]*data-map-src="\.\.\/land.geojson"[^>]*style="background:#081b2c"/);
assert.match(fs.readFileSync('more/index.html','utf8'),/src="[^\"]*demos\/world-weather\/embed\/\?embed=more&amp;v=[0-9a-f]{10}"/);
for(const [,value] of embeddedSource.matchAll(/\b(?:href|src)="([^"]*)"/g)){
 const url=new URL(value.replaceAll('&amp;','&'),pathToFileURL(embeddedFile));if(url.protocol==='file:')assert.ok(fs.existsSync(fileURLToPath(url)),value);
}
assert.ok(fs.existsSync(fileURLToPath(new URL('../land.geojson',pathToFileURL(embeddedFile)))));
class Element {
 constructor(){this.children=[];this.textContent='';this.hidden=false;this.disabled=false;this.events={};this.attrs={};this.style={setProperty:(k,v)=>this.style[k]=v};}
 append(...children){this.children.push(...children);}replaceChildren(...children){this.children=children;}
 setAttribute(k,v){this.attrs[k]=String(v);}addEventListener(k,fn){this.events[k]=fn;}
 getBoundingClientRect(){return {left:0,top:100,width:1000,height:900};}
 click(){return this.events.click?.();}
}
const flush=async()=>{for(let i=0;i<5;i++)await new Promise(resolve=>setImmediate(resolve));};
// Nightly Busuanzi snapshots (00:00 Beijing time); the last one is "today" in the fixed clock below.
const STORE={snapshots:[{date:'2026-10-22',site_pv:100,site_uv:40,reads:1},{date:'2026-10-23',site_pv:131,site_uv:50,reads:2},{date:'2026-10-24',site_pv:150,site_uv:58,reads:3}]};
const NOW=Date.UTC(2026,9,24,4);
class FixedDate extends Date{constructor(...args){super(...(args.length?args:[NOW]));}static now(){return NOW;}}
function boot({offline=false,reduced=false,world=null}={}){
 const nodes=new Map(),get=selector=>{if(!nodes.has(selector))nodes.set(selector,new Element());return nodes.get(selector);},root=new Element();
 // Busuanzi fills these hidden spans site-wide; the snapshot file gives the daily figures.
 if(world){get('[data-worldwide-total]').textContent=world.pv;get('[data-worldwide-visitors]').textContent=world.uv;}
 get('[data-stats-source]').href='https://fanzhang-lab-shou.github.io/OFEL/assets/stats/busuanzi-daily.json';
 root.querySelector=get;root.dataset={};
 get('.pulse-tooltip').querySelector=selector=>get('tooltip '+selector);
 get('[data-world-frame]').contentWindow={postMessage(){}};
 const events={},requests=[],window={matchMedia:()=>({matches:reduced}),addEventListener:(name,fn)=>events[name]=fn};
 const origin='https://fanzhang-lab-shou.github.io';
 const fetcher=async url=>{requests.push(url);return offline?{ok:false,status:503}:{ok:true,status:200,json:async()=>STORE};};
 const context=vm.createContext({document:{querySelector:()=>root,createElement:()=>new Element()},window,location:{origin},Intl,Date:FixedDate,URL,URLSearchParams,AbortController,setTimeout,clearTimeout,setInterval(){},requestAnimationFrame:fn=>fn(),fetch:fetcher});
 vm.runInContext(fs.readFileSync('assets/scripts/more-model.js','utf8'),context);vm.runInContext(fs.readFileSync('assets/scripts/more.js','utf8'),context);
 return {get,root,requests,events,origin};
}
(async()=>{
 const ui=boot({world:{pv:'160',uv:'61'}});await flush();
 assert.equal(ui.get('[data-stat="total"]').textContent,'160','headline totals come from Busuanzi');assert.equal(ui.get('[data-stat="visitors"]').textContent,'61');
 assert.equal(ui.get('[data-stat="today"]').textContent,'10','live 160 minus the 00:00 total 150');
 assert.equal(ui.get('[data-stat="week"]').textContent,String((160-3)-(100-1)),'snapshot readings are subtracted');
 assert.equal(ui.get('[data-visit-reels]').children.length,6);assert.ok(Math.abs(Number(ui.get('[data-visit-reels]').children.at(-1).children[0].style.transform.match(/-([\d.]+)em/)[1])-11.5)<1e-8,'rolling digits must stop on the actual count');
 assert.match(ui.get('[data-visit-accessible]').textContent,/160 recorded visits/);
 const rows=ui.get('[data-stats-daily-table]').children;assert.equal(rows.length,14);
 assert.deepEqual(rows.slice(-3).map(row=>row.children.map(cell=>cell.textContent)),[['2026-10-22','30'],['2026-10-23','18'],['2026-10-24','10']]);
 assert.equal(ui.get('[data-stats-daily]').children[0].children.filter(node=>/^pulse-col\b/.test(node.className)).length,14);assert.equal(ui.get('[data-stats-daily]').children[0].children.filter(node=>node.className==='pulse-col').length,3,'only recorded days get bars');
 assert.match(ui.get('[data-stats-status]').textContent,/00:00 Beijing time since 22 Oct/);assert.equal(ui.get('[data-refresh-stats]').disabled,false);
 assert.ok(ui.requests.every(url=>url.includes('/assets/stats/busuanzi-daily.json')),'only the same-origin snapshot file is requested');
 ui.events.message({origin:ui.origin,source:ui.get('[data-world-frame]').contentWindow,data:{type:'ofel-world-height',height:1500}});assert.equal(ui.get('[data-world-frame]').style.height,'1500px');
 ui.events.message({origin:'https://untrusted.example',source:ui.get('[data-world-frame]').contentWindow,data:{type:'ofel-world-height',height:3000}});assert.equal(ui.get('[data-world-frame]').style.height,'1500px');
 const count=ui.requests.length;await ui.get('[data-refresh-stats]').click();await flush();assert.ok(ui.requests.length>count);assert.match(ui.requests.at(-1),/\?t=\d+/,'refresh bypasses the cache');
 const offline=boot({offline:true,world:{pv:'160',uv:'61'}});await flush();assert.equal(offline.get('[data-stat="total"]').textContent,'160','live totals survive a snapshot outage');assert.match(offline.get('[data-stats-status]').textContent,/temporarily unavailable/);assert.equal(offline.get('[data-stats-daily-table]').children[0].children[1].textContent,'—');assert.equal(offline.requests.length,1);
 const silent=boot();await new Promise(resolve=>setTimeout(resolve,10600));assert.equal(silent.get('[data-visit-reels]').textContent,'—','no fake count when Busuanzi never answers');assert.match(silent.get('[data-visit-accessible]').textContent,/unavailable/);
 const reduced=boot({reduced:true,world:{pv:'160',uv:'61'}});await flush();assert.equal(reduced.get('[data-visit-reels]').children.at(-1).children[0].style.transition,undefined);
 const messages=[],listeners={};const parent={postMessage:(data,target)=>messages.push({data,target})},body={dataset:{},getBoundingClientRect:()=>({height:1800})};
 const html={dataset:{}};
 const window={parent,addEventListener:(name,fn)=>listeners[name]=fn};const embed=vm.createContext({window,location:{origin:ui.origin,search:'?embed=more'},document:{body,documentElement:html},URLSearchParams,ResizeObserver:class{observe(){}},requestAnimationFrame:fn=>fn()});
 vm.runInContext(fs.readFileSync('demos/world-weather/embed.js','utf8'),embed);assert.equal(body.dataset.embed,'more');assert.equal(html.dataset.embed,'more','the iframe root canvas must receive the dark theme too');assert.equal(messages[0].data.height,1800);assert.equal(messages[0].target,ui.origin);
 listeners.message({origin:'https://untrusted.example',source:parent,data:{type:'ofel-world-request-height'}});assert.equal(messages.length,1);
 listeners.message({origin:ui.origin,source:parent,data:{type:'ofel-world-request-height'}});assert.equal(messages.length,2);
 console.log('Passed Busuanzi totals with nightly-snapshot daily figures, real counter rendering, animated final digits, charts/tables, refresh, outages, reduced motion and same-origin frame handshake.');
})().catch(error=>{console.error(error);process.exitCode=1;});
