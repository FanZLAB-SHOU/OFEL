// Exercise the real category controller against generated News entries.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'news/index.html'),'utf8');
const posts=JSON.parse(fs.readFileSync(path.join(root,'assets/blog.json'),'utf8')).posts;
function element(){return {events:{},attrs:{},dataset:{},hidden:false,textContent:'',classList:{toggle(){}},
  addEventListener(t,cb){this.events[t]=cb;},setAttribute(k,v){this.attrs[k]=v;}};}
const items=[...html.matchAll(/<article class="blog-post" data-news-category="([^"]+)">([\s\S]*?)<\/article>/g)]
  .map(m=>({...element(),dataset:{newsCategory:m[1]},date:m[2].match(/datetime="([^"]+)"/)[1]}));
const buttons=[...html.matchAll(/data-news-filter="([^"]+)"/g)]
  .map(m=>({...element(),dataset:{newsFilter:m[1]}}));
const controls={...element(),querySelectorAll(){return buttons;}};
const count=element(),empty=element();
const nodes={'#news-list':{querySelectorAll(){return items;}},'.news-filters':controls,'.news-count':count,'.news-empty':empty};
const location={href:'https://fanzhang-lab-shou.github.io/OFEL/news/?category=research&from=qr#news'};
const events={};
const context={document:{querySelector(s){return nodes[s];}},window:{addEventListener(t,cb){events[t]=cb;}},URL,location,
  history:{replaceState(a,b,url){location.href=new URL(url,location.href).href;}}};
const code=fs.readFileSync(path.join(root,'script.js'),'utf8').match(/function initNewsFilters\(\) \{[\s\S]*?\n\}\ninitNewsFilters\(\);/)[0];
vm.runInNewContext(code,context);
const visible=()=>items.filter(i=>!i.hidden);
const expected=c=>posts.filter(p=>c==='all'||p.category===c).length;
assert.equal(visible().length,expected('research'));
assert.equal(controls.hidden,false);
for(const button of buttons){
 button.events.click();
 const category=button.dataset.newsFilter;
 assert.equal(visible().length,expected(category));
 assert.equal(button.attrs['aria-pressed'],'true');
 assert.equal(new URL(location.href).searchParams.get('from'),'qr');
 assert.equal(new URL(location.href).hash,'#news');
 const dates=visible().map(i=>i.date);assert.deepEqual(dates,[...dates].sort().reverse());
 assert.equal(new URL(location.href).searchParams.get('category'),category==='all'?null:category);
}
location.href='https://fanzhang-lab-shou.github.io/OFEL/news/?category=exchange';events.popstate();
assert.equal(visible().length,expected('exchange'));
location.href='https://fanzhang-lab-shou.github.io/OFEL/news/?category=unknown';events.popstate();
assert.equal(visible().length,posts.length);
assert.equal(empty.hidden,true);
vm.runInNewContext(code,{document:{querySelector(){return null;}}});
console.log('Passed category filters, direct category links, history, query/hash preservation, chronological order and other-page checks.');
