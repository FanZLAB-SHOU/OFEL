/* Pure time/weather helpers, shared by the browser and the small regression suite. */
const WorldWeather = (() => {
  const TTL = 10 * 60 * 1000;
  const cities = [
    {id:'shanghai',name:'Shanghai',country:'China',lat:31.2304,lon:121.4737,zone:'Asia/Shanghai'},
    {id:'seattle',name:'Seattle',country:'United States',lat:47.6062,lon:-122.3321,zone:'America/Los_Angeles'},
    {id:'st-johns',name:'St. John’s',country:'Canada',lat:47.5615,lon:-52.7126,zone:'America/St_Johns'},
    {id:'madrid',name:'Madrid',country:'Spain',lat:40.4168,lon:-3.7038,zone:'Europe/Madrid'},
    {id:'lima',name:'Lima',country:'Peru',lat:-12.0464,lon:-77.0428,zone:'America/Lima'},
    {id:'cape-town',name:'Cape Town',country:'South Africa',lat:-33.9249,lon:18.4241,zone:'Africa/Johannesburg'},
    {id:'noumea',name:'Nouméa',country:'New Caledonia',lat:-22.2758,lon:166.458,zone:'Pacific/Noumea'},
    {id:'hobart',name:'Hobart',country:'Australia',lat:-42.8821,lon:147.3272,zone:'Australia/Hobart'}
  ];
  const formatters = new Map();
  function formatter(zone, options) {
    const key = zone + JSON.stringify(options);
    if (!formatters.has(key)) formatters.set(key,new Intl.DateTimeFormat('en-GB',{timeZone:zone,...options}));
    return formatters.get(key);
  }
  function format(zone, options, instant = Date.now()) { return formatter(zone,options).format(new Date(instant)); }
  function validZone(zone) {
    if (typeof zone !== 'string' || !zone) return false;
    try { format(zone,{hour:'2-digit'});return true; } catch { return false; }
  }
  function clock(zone, instant = Date.now(), seconds = false) {
    return format(zone,{hour:'2-digit',minute:'2-digit',...(seconds?{second:'2-digit'}:{}),hourCycle:'h23'},instant);
  }
  function dateLabel(zone, instant = Date.now()) { return format(zone,{weekday:'short',day:'numeric',month:'short'},instant); }
  function offsetMinutes(zone, instant = Date.now()) {
    const parts = formatter(zone,{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date(instant));
    const p=Object.fromEntries(parts.filter(p=>p.type!=='literal').map(p=>[p.type,Number(p.value)]));
    return Math.round((Date.UTC(p.year,p.month-1,p.day,p.hour,p.minute,p.second)-Math.floor(instant/1000)*1000)/60000);
  }
  function offsetLabel(zone, instant = Date.now()) {
    const m=offsetMinutes(zone,instant);
    if(m===0)return 'UTC';
    const n=Math.abs(m);return `UTC${m<0?'−':'+'}${Math.floor(n/60)}${n%60?':'+String(n%60).padStart(2,'0'):''}`;
  }
  function difference(zone, instant=Date.now()) {
    const minutes=offsetMinutes(zone,instant)-offsetMinutes('Asia/Shanghai',instant);
    if(minutes===0)return 'Same time as Shanghai';
    const n=Math.abs(minutes),hours=Math.floor(n/60),rest=n%60;
    return `${hours?hours+'h ':''}${rest?rest+'m ':''}${minutes<0?'behind':'ahead of'} Shanghai`;
  }
  function coordinates(lat,lon) {
    return `${Math.abs(lat).toFixed(2)}° ${lat<0?'S':'N'} · ${Math.abs(lon).toFixed(2)}° ${lon<0?'W':'E'}`;
  }
  function project(lon,lat) { return [(lon+180)/360*1200,(90-lat)/180*600]; }
  function unproject(x,y) { return {lat:Math.max(-89.9,Math.min(89.9,90-y/600*180)),lon:Math.max(-180,Math.min(180,x/1200*360-180))}; }
  function weatherKind(code,isDay) {
    if(!Number.isFinite(code))return {label:'Conditions unavailable',icon:'cloud'};
    if(code===0||code===1)return {label:code===0?'Clear':'Mostly clear',icon:isDay===false?'moon':'sun'};
    if(code===2)return {label:'Patchy cloud',icon:'cloud'};
    if(code===3)return {label:'Cloudy',icon:'cloud'};
    if(code===45||code===48)return {label:'Foggy',icon:'fog'};
    if(code>=51&&code<=57)return {label:'Drizzle',icon:'rain'};
    if(code===66||code===67)return {label:'Icy rain',icon:'snow'};
    if((code>=61&&code<=65)||(code>=80&&code<=82))return {label:'Rain',icon:'rain'};
    if((code>=71&&code<=77)||code===85||code===86)return {label:'Snow',icon:'snow'};
    if(code>=95&&code<=99)return {label:'Thunderstorms',icon:'storm'};
    return {label:'Conditions unavailable',icon:'cloud'};
  }
  function weatherURL(location) {
    if(!Number.isFinite(location.lat)||!Number.isFinite(location.lon)||Math.abs(location.lat)>90||Math.abs(location.lon)>180)throw Error('Invalid coordinates');
    const url=new URL('https://api.open-meteo.com/v1/forecast');
    url.search=new URLSearchParams({latitude:location.lat,longitude:location.lon,current:'temperature_2m,apparent_temperature,relative_humidity_2m,is_day,precipitation,weather_code,wind_speed_10m',timezone:'auto',timeformat:'unixtime',forecast_days:'1',temperature_unit:'celsius',wind_speed_unit:'kmh',precipitation_unit:'mm'}).toString();
    return url.href;
  }
  function parseWeather(data) {
    const c=data?.current;
    if(!c||!validZone(data.timezone)||!Number.isFinite(c.time)||typeof c.temperature_2m!=='number'||!Number.isFinite(c.temperature_2m))throw Error('Incomplete weather response');
    return {zone:data.timezone,time:c.time*1000,temperature:c.temperature_2m,feels:c.apparent_temperature,humidity:c.relative_humidity_2m,wind:c.wind_speed_10m,precipitation:c.precipitation,code:c.weather_code,isDay:c.is_day===1?true:c.is_day===0?false:null};
  }
  class WeatherClient {
    constructor(fetcher,storage=null,now=()=>Date.now()) { this.fetcher=fetcher;this.storage=storage;this.now=now;this.memory=new Map(); }
    key(location) { return `ofel-weather-v1:${location.lat.toFixed(4)},${location.lon.toFixed(4)}`; }
    async get(location,{signal,force=false}={}) {
      const key=this.key(location);let entry=this.memory.get(key);
      if(!entry) { try {entry=JSON.parse(this.storage?.getItem(key)||'null');} catch {} }
      const age=this.now()-(entry?.savedAt||0);
      if(!force&&entry&&age>=0&&age<TTL) {
        try {return {...parseWeather(entry.raw),savedAt:entry.savedAt,cached:true};} catch {}
      }
      const response=await this.fetcher(weatherURL(location),{signal});
      if(!response.ok)throw Error('Weather request failed');
      const raw=await response.json(),weather=parseWeather(raw);
      entry={savedAt:this.now(),raw};this.memory.set(key,entry);
      try { this.storage?.setItem(key,JSON.stringify(entry)); } catch {}
      return {...weather,savedAt:entry.savedAt,cached:false};
    }
  }
  function searchLocation(item) {
    if(!Number.isFinite(item.latitude)||!Number.isFinite(item.longitude)||!validZone(item.timezone))return null;
    return {id:'search-'+item.id,name:String(item.name||'Selected city'),country:[item.admin1,item.country].filter(Boolean).join(', '),lat:item.latitude,lon:item.longitude,zone:item.timezone};
  }
  return {TTL,cities,clock,dateLabel,validZone,offsetMinutes,offsetLabel,difference,coordinates,project,unproject,weatherKind,weatherURL,parseWeather,WeatherClient,searchLocation};
})();
if(typeof module!=='undefined'&&module.exports)module.exports=WorldWeather;
