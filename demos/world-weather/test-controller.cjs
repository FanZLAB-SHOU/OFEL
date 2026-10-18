/* Run the actual browser controller with a small DOM/network harness. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element {
 constructor(tag='div'){this.tag=tag;this.attrs={};this.events={};this.children=[];this.textContent='';this.hidden=false;this.disabled=false;this.value='';this.className='';this.classList={toggle:(name,on)=>{const s=new Set(this.className.split(' ').filter(Boolean));if(on)s.add(name);else s.delete(name);this.className=[...s].join(' ');},add:name=>this.classList.toggle(name,true),remove:name=>this.classList.toggle(name,false)};}
 setAttribute(k,v){this.attrs[k]=String(v);if(k==='class')this.className=String(v);}
 getAttribute(k){return this.attrs[k];}
 addEventListener(k,f){this.events[k]=f;}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this.children=[...nodes];}
 focus(){this.focused=true;}
 click(){return this.events.click?.({target:this,button:0,preventDefault(){},stopPropagation(){}});}
}
const html=fs.readFileSync(__dirname+'/index.html','utf8');
const nodes=Object.fromEntries([...html.matchAll(/<([\w-]+)[^>]*\bid="([^"]+)"/g)].map(m=>[m[2],new Element(m[1])]));
const document={hidden:false,events:{},getElementById:id=>nodes[id],createElement:t=>new Element(t),createElementNS:(ns,t)=>new Element(t),addEventListener(k,f){this.events[k]=f;}};
let now=Date.UTC(2026,9,17,12);class TestDate extends Date {constructor(v){super(v===undefined?now:v);}static now(){return now;}}
const requests=[],intervals=[],storage=new Map();
const fetcher=(url,options={})=>{
 if(url==='land.geojson')return Promise.resolve({ok:true,json:async()=>JSON.parse(fs.readFileSync(__dirname+'/land.geojson','utf8'))});
 return new Promise(resolve=>requests.push({url,signal:options.signal,resolve}));
};
const context=vm.createContext({document,fetch:fetcher,Date:TestDate,Intl,URL,URLSearchParams,AbortController,sessionStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},setTimeout:()=>1,clearTimeout(){},setInterval:(fn,ms)=>intervals.push({fn,ms})});
vm.runInContext(fs.readFileSync(__dirname+'/model.js','utf8'),context);
vm.runInContext(fs.readFileSync(__dirname+'/app.js','utf8'),context);
const flush=async()=>{for(let i=0;i<5;i++)await new Promise(resolve=>setImmediate(resolve));};
const weather=(zone,temp)=>({timezone:zone,current:{time:Math.floor(now/1000),temperature_2m:temp,apparent_temperature:temp+1,relative_humidity_2m:60,is_day:1,precipitation:0,weather_code:2,wind_speed_10m:10}});
const finish=(index,data,ok=true)=>requests[index].resolve({ok,json:async()=>data});
(async()=>{
 assert.equal(nodes['city-clocks'].children.length,8);assert.equal(nodes['city-markers'].children.length,8);
 assert.equal(requests.length,1);finish(0,weather('Asia/Shanghai',20));await flush();
 assert.equal(nodes.temperature.textContent,'20°C');assert.equal(nodes['weather-block'].attrs['aria-busy'],'false');assert.equal(nodes.land.children.length,127);
 nodes['city-clocks'].children[1].click();nodes['city-clocks'].children[3].click();
 assert.equal(requests[1].signal.aborted,true);
 finish(2,weather('Europe/Madrid',10));await flush();finish(1,weather('America/Los_Angeles',99));await flush();
 assert.equal(nodes['location-name'].textContent,'Madrid');assert.equal(nodes.temperature.textContent,'10°C','late responses must not overwrite the current city');
 nodes['city-clocks'].children[4].click();finish(3,{},false);await flush();
 assert.equal(nodes['location-name'].textContent,'Lima');assert.match(nodes['local-clock'].textContent,/:/);assert.equal(nodes.temperature.textContent,'—');assert.match(nodes['weather-status'].textContent,/Could not reach/);
 nodes['refresh-weather'].click();finish(4,weather('America/Lima',15));await flush();assert.equal(nodes.temperature.textContent,'15°C');
 nodes['city-query'].value='Tokyo';const search=nodes['city-search'].events.submit({preventDefault(){}});
 assert.match(String(requests[5].url),/geocoding-api/);finish(5,{results:[{id:1,name:'Tokyo',country:'Japan',latitude:35.68,longitude:139.69,timezone:'Asia/Tokyo'}]});await search;await flush();
 assert.equal(nodes['search-results'].children.length,1);nodes['search-results'].children[0].children[0].click();
 assert.equal(nodes['location-name'].textContent,'Tokyo');assert.equal(nodes['search-results'].hidden,true);assert.equal(nodes['picked-marker'].children.length,1);
 finish(6,weather('Asia/Tokyo',22));await flush();assert.equal(nodes.temperature.textContent,'22°C');
 assert.ok(Number(nodes['world-map'].attrs.viewBox.split(' ')[2])<1200);nodes['reset-map'].click();assert.equal(nodes['world-map'].attrs.viewBox,'0 0 1200 600');
 nodes['city-query'].value='No such place';nodes['city-query'].events.input();const empty=nodes['city-search'].events.submit({preventDefault(){}});finish(7,{results:[]});await empty;await flush();assert.match(nodes['search-status'].textContent,/No cities found/);
 now+=11*60*1000;document.hidden=true;intervals.find(i=>i.ms===60000).fn();assert.equal(requests.length,8,'hidden pages should not fetch weather');
 document.hidden=false;document.events.visibilitychange();assert.equal(requests.length,9);finish(8,weather('Asia/Tokyo',23));await flush();assert.equal(nodes.temperature.textContent,'23°C');
 for(const city of [{query:'hongkong',canonical:'Hong Kong',code:'HK',zone:'Asia/Hong_Kong',lat:22.27832,lon:114.17469},{query:'澳門',canonical:'Macao',code:'MO',zone:'Asia/Macau',lat:22.20056,lon:113.54611}]){
  nodes['city-query'].value=city.query;const index=requests.length,search=nodes['city-search'].events.submit({preventDefault(){}});
  assert.equal(new URL(requests[index].url).searchParams.get('name'),city.canonical);
  finish(index,{results:[{id:index,name:city.canonical,country_code:city.code,latitude:city.lat,longitude:city.lon,timezone:city.zone}]});await search;await flush();
  assert.equal(nodes['search-results'].children[0].children[0].children[1].textContent,city.canonical+', China');
  nodes['search-results'].children[0].children[0].click();assert.equal(nodes['location-region'].textContent,city.canonical+', China');
  assert.equal(Number(new URL(requests[index+1].url).searchParams.get('latitude')),city.lat);
  finish(index+1,weather(city.zone,25));await flush();assert.equal(nodes.temperature.textContent,'25°C');assert.equal(nodes['zone-name'].textContent,city.zone);
 }
 console.log('Passed demo boot, marker/card selection, stale-response protection, offline clock fallback, refresh, search, custom pin, map reset, empty search, visibility-aware refresh and Hong Kong/Macao search-to-weather flows.');
})().catch(e=>{console.error(e);process.exitCode=1;});
