/* Only this standalone demo loads this controller. No geolocation or background tracking. */
(() => {
  'use strict';
  const M=WorldWeather,$=id=>document.getElementById(id),NS='http://www.w3.org/2000/svg';
  const svg=$('world-map'),markers=$('city-markers'),picked=$('picked-marker');
  let selected={...M.cities[0]},weather=null,weatherSequence=0,weatherController=null,searchController=null,searchSequence=0;
  let lastAttempt=0,view={x:0,y:0,w:1200,h:600},zoom=1;
  let storage;try {storage=sessionStorage;}catch{}
  const client=new M.WeatherClient((...args)=>fetch(...args),storage);
  const cardNodes=new Map(),pinNodes=new Map();
  function node(tag,attrs={},text) { const n=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));if(text!==undefined)n.textContent=text;return n; }
  function set(id,text) { $(id).textContent=text; }
  function value(n,unit,digits=0) { return typeof n==='number'&&Number.isFinite(n)?`${n.toFixed(digits)}${unit}`:'—'; }
  const iconPaths={
    sun:'<circle cx="24" cy="24" r="8"/><path d="M24 4v5m0 30v5M4 24h5m30 0h5M10 10l4 4m20 20 4 4M10 38l4-4m20-20 4-4"/>',
    moon:'<path d="M34 32A17 17 0 0 1 17 9a17 17 0 1 0 23 23 17 17 0 0 1-6 0Z"/>',
    cloud:'<path d="M13 35a9 9 0 1 1 1-18 12 12 0 0 1 23 3 7.5 7.5 0 0 1-1 15Z"/>',
    rain:'<path d="M12 29a8 8 0 1 1 2-16 11 11 0 0 1 21 3 6.5 6.5 0 0 1-1 13Z"/><path d="m15 35-3 6m13-6-3 6m13-6-3 6"/>',
    snow:'<path d="M12 28a8 8 0 1 1 2-16 11 11 0 0 1 21 3 6.5 6.5 0 0 1-1 13Z"/><path d="M15 34v9m-4-7 8 5m0-5-8 5m21-7v9m-4-7 8 5m0-5-8 5"/>',
    fog:'<path d="M13 27a8 8 0 1 1 1-16 11 11 0 0 1 21 3 6.5 6.5 0 0 1-1 13Z"/><path d="M8 34h32M12 40h24"/>',
    storm:'<path d="M12 28a8 8 0 1 1 2-16 11 11 0 0 1 21 3 6.5 6.5 0 0 1-1 13Z"/><path d="m25 29-7 10h8l-5 8"/>'
  };
  function icon(kind) { $('weather-icon').innerHTML=`<svg viewBox="0 0 48 48" aria-hidden="true">${iconPaths[kind]||iconPaths.cloud}</svg>`; }
  function updateClock() {
    const now=Date.now();set('utc-clock',M.clock('UTC',now,true));
    if(M.validZone(selected.zone)) {
      set('local-clock',M.clock(selected.zone,now,true));set('local-date',M.dateLabel(selected.zone,now));
      set('zone-name',selected.zone);set('utc-offset',M.offsetLabel(selected.zone,now));
      set('time-difference',selected.id==='shanghai'?'Shanghai reference time':M.difference(selected.zone,now));
    } else {set('local-clock','—');set('local-date','Resolving local time…');set('zone-name','Timezone pending');set('utc-offset','—');set('time-difference','');}
    for(const city of M.cities) {
      const refs=cardNodes.get(city.id);refs.time.textContent=M.clock(city.zone,now);refs.offset.textContent=M.offsetLabel(city.zone,now);refs.date.textContent=M.dateLabel(city.zone,now);
    }
  }
  function paintWeather(data) {
    const condition=M.weatherKind(data.code,data.isDay);
    set('temperature',value(data.temperature,'°C'));set('feels-like',value(data.feels,'°C'));
    set('humidity',value(data.humidity,'%'));set('wind',value(data.wind,' km/h'));set('precipitation',value(data.precipitation,' mm',1));
    set('weather-description',condition.label);icon(condition.icon);
    const day=$('day-state');day.hidden=data.isDay===null;day.textContent=data.isDay?'Daytime':'Nighttime';day.classList.toggle('is-night',data.isDay===false);
    set('weather-update','Data time '+M.clock(data.zone,data.time));set('weather-status','');
  }
  async function loadWeather(force=false) {
    const sequence=++weatherSequence,location={...selected};
    weatherController?.abort();const controller=new AbortController();weatherController=controller;
    const timer=setTimeout(()=>controller.abort(),12000);lastAttempt=Date.now();
    $('weather-block').setAttribute('aria-busy','true');$('refresh-weather').disabled=true;
    set('weather-status','');
    try {
      const data=await client.get(location,{signal:controller.signal,force});
      if(sequence!==weatherSequence)return;
      weather=data;selected.zone=data.zone;paintWeather(data);updateClock();
    } catch(error) {
      if(sequence!==weatherSequence)return;
      if(weather) {set('weather-status','Refresh unavailable. Showing the last weather update.');}
      else {set('weather-description','Weather unavailable');set('weather-update','Try refreshing shortly');set('weather-status','Could not reach the weather service. Available city clocks still work.');icon('cloud');}
    } finally {
      clearTimeout(timer);
      if(sequence===weatherSequence){$('weather-block').setAttribute('aria-busy','false');$('refresh-weather').disabled=false;}
    }
  }
  function select(location,focusMap=false) {
    selected={...location};weather=null;
    set('location-name',selected.name);set('location-region',selected.country||'Map selection');set('location-coordinates',M.coordinates(selected.lat,selected.lon));
    for(const id of ['temperature','feels-like','humidity','wind','precipitation'])set(id,'—');
    set('weather-description','Loading weather…');set('weather-update','Fetching current conditions');$('day-state').hidden=true;icon('cloud');
    cardNodes.forEach((refs,id)=>refs.button.setAttribute('aria-pressed',String(id===selected.id)));
    pinNodes.forEach((pin,id)=>pin.classList.toggle('is-selected',id===selected.id));
    picked.replaceChildren();
    if(!pinNodes.has(selected.id))picked.append(makePin(selected,true));
    if(focusMap) { if(zoom===1)zoom=1.7;const [x,y]=M.project(selected.lon,selected.lat);view.w=1200/zoom;view.h=600/zoom;view.x=x-view.w/2;view.y=y-view.h/2;setView(); }
    updateClock();loadWeather();
  }
  function makePin(city,custom=false) {
    const [x,y]=M.project(city.lon,city.lat),g=node('g',{class:'city-pin'+(custom||city.id===selected.id?' is-selected':''),transform:`translate(${x} ${y})`,tabindex:'0',role:'button','aria-label':`Show time and weather for ${city.name}`});
    g.append(node('title',{},city.name),node('circle',{r:17,class:'pin-hit'}),node('circle',{r:12,class:'pin-halo'}),node('circle',{r:4.7,class:'pin-dot'}));
    const end=x>1040;g.append(node('text',{x:end?-13:13,y:-12,'text-anchor':end?'end':'start',class:'pin-label'},city.name));
    g.addEventListener('click',event=>{event.stopPropagation();select(city);});
    g.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.stopPropagation();select(city);}});
    return g;
  }
  function cityCards() {
    for(const city of M.cities) {
      const button=document.createElement('button');button.type='button';button.className='city-clock';button.setAttribute('aria-pressed',String(city.id===selected.id));
      const row=document.createElement('span'),name=document.createElement('strong'),offset=document.createElement('small'),time=document.createElement('time'),date=document.createElement('small');
      name.className='city-name';name.textContent=city.name;offset.className='city-offset';time.className='city-time';date.className='city-date';row.append(name,offset);button.append(row,time,date);button.addEventListener('click',()=>select(city));$('city-clocks').append(button);
      cardNodes.set(city.id,{button,time,offset,date});const pin=makePin(city);pinNodes.set(city.id,pin);markers.append(pin);
    }
  }
  function setView() {
    view.x=Math.max(0,Math.min(1200-view.w,view.x));view.y=Math.max(0,Math.min(600-view.h,view.y));
    svg.setAttribute('viewBox',`${view.x} ${view.y} ${view.w} ${view.h}`);$('zoom-out').disabled=zoom<=1;$('zoom-in').disabled=zoom>=5;
  }
  function changeZoom(factor) {
    const cx=view.x+view.w/2,cy=view.y+view.h/2;zoom=Math.max(1,Math.min(5,zoom*factor));view.w=1200/zoom;view.h=600/zoom;view.x=cx-view.w/2;view.y=cy-view.h/2;setView();
  }
  function point(event) {const p=svg.createSVGPoint();p.x=event.clientX;p.y=event.clientY;return p.matrixTransform(svg.getScreenCTM().inverse());}
  function setupMap() {
    for(const lon of [-120,-60,0,60,120]){const [x]=M.project(lon,0);$('graticule').append(node('line',{x1:x,x2:x,y1:0,y2:600,class:'grid-line'}));}
    for(const lat of [-60,-30,0,30,60]){const [,y]=M.project(0,lat);$('graticule').append(node('line',{x1:0,x2:1200,y1:y,y2:y,class:'grid-line'}));}
    fetch('land.geojson').then(r=>{if(!r.ok)throw Error('Map unavailable');return r.json();}).then(data=>{
      for(const feature of data.features){const polygons=feature.geometry.type==='Polygon'?[feature.geometry.coordinates]:feature.geometry.coordinates;const d=polygons.map(p=>p.map(r=>r.map((c,i)=>{const [x,y]=M.project(c[0],c[1]);return `${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`;}).join('')+'Z').join('')).join('');$('land').append(node('path',{d,'fill-rule':'evenodd'}));}
      set('map-status','Explore places across the oceans.');
    }).catch(()=>set('map-status','Map outline unavailable. City clocks still work.'));
    $('zoom-in').addEventListener('click',()=>changeZoom(1.5));$('zoom-out').addEventListener('click',()=>changeZoom(1/1.5));
    $('reset-map').addEventListener('click',()=>{zoom=1;view={x:0,y:0,w:1200,h:600};setView();});
    let drag=null;
    svg.addEventListener('pointerdown',event=>{
      if(event.button!==0||event.target.closest('.city-pin'))return;
      drag={id:event.pointerId,x:event.clientX,y:event.clientY,view:{...view},point:point(event),moved:false};svg.setPointerCapture(event.pointerId);
    });
    svg.addEventListener('pointermove',event=>{
      if(!drag||drag.id!==event.pointerId)return;
      if(Math.hypot(event.clientX-drag.x,event.clientY-drag.y)>6)drag.moved=true;
      if(drag.moved){svg.classList.add('is-dragging');const p=point(event);view.x+=drag.point.x-p.x;view.y+=drag.point.y-p.y;setView();}
    });
    svg.addEventListener('pointerup',event=>{
      if(!drag||drag.id!==event.pointerId)return;
      const state=drag;drag=null;svg.classList.remove('is-dragging');if(svg.hasPointerCapture(event.pointerId))svg.releasePointerCapture(event.pointerId);
      if(!state.moved){const p=point(event);if(p.x>=0&&p.x<=1200&&p.y>=0&&p.y<=600){const loc=M.unproject(p.x,p.y);select({id:'point',name:'Selected location',country:'Map selection',...loc,zone:null});}}
    });
    function cancel(){drag=null;svg.classList.remove('is-dragging');}
    svg.addEventListener('pointercancel',cancel);svg.addEventListener('lostpointercapture',cancel);
    svg.addEventListener('keydown',event=>{
      if(event.target!==svg)return;
      if(['+','=','-','Home','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))event.preventDefault();
      if(event.key==='+'||event.key==='=')changeZoom(1.5);if(event.key==='-')changeZoom(1/1.5);
      if(event.key==='Home')$('reset-map').click();
      const move={ArrowLeft:[-view.w*.15,0],ArrowRight:[view.w*.15,0],ArrowUp:[0,-view.h*.15],ArrowDown:[0,view.h*.15]}[event.key];
      if(move){view.x+=move[0];view.y+=move[1];setView();}
    });
    setView();
  }
  $('city-search').addEventListener('submit',async event=>{
    event.preventDefault();const query=$('city-query').value.trim();if(query.length<2)return;
    const sequence=++searchSequence;searchController?.abort();const controller=new AbortController();searchController=controller;
    const timer=setTimeout(()=>controller.abort(),10000);$('search-button').disabled=true;$('search-results').replaceChildren();$('search-results').hidden=true;set('search-status','Searching…');
    try {
      const url=new URL('https://geocoding-api.open-meteo.com/v1/search');url.search=new URLSearchParams({name:query,count:'5',language:'en',format:'json'});
      const response=await fetch(url,{signal:controller.signal});if(!response.ok)throw Error('Search unavailable');const data=await response.json();if(sequence!==searchSequence)return;
      const results=(data.results||[]).map(M.searchLocation).filter(Boolean);
      set('search-status',results.length?`${results.length} matching ${results.length===1?'place':'places'}`:'No cities found. Try another spelling.');
      results.forEach(location=>{const li=document.createElement('li'),button=document.createElement('button'),name=document.createElement('span'),region=document.createElement('small');button.type='button';name.textContent=location.name;region.textContent=location.country;button.append(name,region);li.append(button);$('search-results').append(li);button.addEventListener('click',()=>{select(location,true);$('search-results').hidden=true;set('search-status','');$('city-query').value=location.name;$('location-name').setAttribute('tabindex','-1');$('location-name').focus({preventScroll:true});});});
      $('search-results').hidden=!results.length;
    } catch(error) {if(sequence===searchSequence)set('search-status','Search is unavailable. Choose a city below or click the map.');}
    finally {clearTimeout(timer);if(sequence===searchSequence)$('search-button').disabled=false;}
  });
  $('city-query').addEventListener('input',()=>{++searchSequence;searchController?.abort();$('search-button').disabled=false;$('search-results').hidden=true;set('search-status','');});
  document.addEventListener('keydown',event=>{if(event.key==='Escape')$('search-results').hidden=true;});
  document.addEventListener('click',event=>{if(!event.target.closest('.search-area'))$('search-results').hidden=true;});
  $('refresh-weather').addEventListener('click',()=>loadWeather(true));
  function autoRefresh(){if(!document.hidden&&Date.now()-lastAttempt>=M.TTL)loadWeather();}
  document.addEventListener('visibilitychange',()=>{if(!document.hidden){updateClock();autoRefresh();}});
  cityCards();setupMap();updateClock();icon('cloud');loadWeather();setInterval(updateClock,1000);setInterval(autoRefresh,60000);
})();
