// Test the real controller against the generated publication metadata.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const js = fs.readFileSync(path.join(root, 'script.js'), 'utf8');
function element() {
  return {events: {}, attrs: {}, children: [], dataset: {}, value: '', textContent: '', hidden: false,
    classList: {toggle() {}}, addEventListener(type, fn) { this.events[type] = fn; },
    setAttribute(key, value) { this.attrs[key] = value; },
    append(child) { this.children.push(child); }, replaceChildren() { this.children = []; },
    focus() { this.focused = true; }, select() { this.selected = true; }, scrollIntoView() {}};
}
const decode = text => text.replace(/&quot;/g, '"').replace(/&#x27;/g, "'").replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
const html = fs.readFileSync(path.join(root, 'publications/index.html'), 'utf8');
const papers = [...html.matchAll(/<article class="publication"([^>]+)>/g)].map(match => {
  const p = element();
  for (const attr of match[1].matchAll(/data-([\w-]+)="([^"]*)"/g)) p.dataset[attr[1].replace(/-([a-z])/g, (_, c) => c.toUpperCase())] = decode(attr[2]);
  return p;
});
const filters = ['all','assessment','ecosystems','vessels','biology'].map(topic => ({...element(),dataset:{filter:topic}}));
const collections = ['lab','fan-zhang'].map(value => ({...element(),dataset:{collection:value}}));
const ids = ['#publication-list','.publication-count','#publication-collection-note','.publication-empty',
  '#publication-citations','.publication-expand','#publication-toggle','#publication-search','#publication-year',
  '#publication-reset','.publication-discovery','#publications-title'];
const nodes = Object.fromEntries(ids.map(id => [id,element()]));
const context = {
  document: {body:{dataset:{}},querySelector(s){return nodes[s];},createElement:element,
    querySelectorAll(s){return ({'.filter-button':filters,'.collection-button':collections,'.publication':papers})[s];}},
  updateNavigation(){},history:{replaceState(){}}
};
vm.runInNewContext(js.match(/function initPublications\(\) \{[\s\S]*?\n\}\npublications = initPublications\(\);/)[0],context);
const visible = () => papers.filter(p=>!p.hidden);
const query = value => { nodes['#publication-search'].value=value;nodes['#publication-search'].events.input(); };
const year = value => {nodes['#publication-year'].value=value;nodes['#publication-year'].events.change();};
const clear = () => nodes['#publication-reset'].events.click();
assert.equal(papers.length,20);
assert.equal(visible().length,6);
assert.ok(visible().every(p=>p.dataset.lab==='true'));
query('Runze Wang');
assert.equal(visible().length,1);assert.match(visible()[0].dataset.search,/Diversity and Subjectivity/);
query('diversity subjectivity');assert.equal(visible().length,1);
query('ANDRE PUNT');const noAccent=visible().length;
assert.ok(noAccent>0);query('André Punt');assert.equal(visible().length,noAccent);
query('not-a-real-publication-987654');assert.equal(visible().length,0);assert.equal(nodes['.publication-empty'].hidden,false);
clear();assert.equal(visible().length,6);assert.equal(nodes['#publication-reset'].disabled,true);
year('2025');assert.equal(visible().length,5);assert.ok(visible().every(p=>p.dataset.year==='2025'));
filters[4].events.click();assert.equal(visible().length,2);assert.ok(visible().every(p=>p.dataset.topic==='biology'));
query('Dong');assert.equal(visible().length,2, 'search includes co-authors, not just first authors');
clear();context.publications.select('fan-zhang',true);year('2022');
assert.equal(visible().length,1);assert.match(visible()[0].dataset.search,/age[-‐] and length[-‐]structured/i);
context.publications.select('lab',true);assert.equal(nodes['#publication-year'].value,'all');
assert.equal(visible().length,6);assert.ok(nodes['#publication-citations'].href.endsWith('lab-publications.bib'));
nodes['#publication-toggle'].events.click();assert.equal(visible().length,13);
query('tuna');assert.ok(nodes['.publication-expand'].hidden);assert.ok(visible().length>0);
assert.ok(nodes['#publication-year'].children.every((o,i,a)=>i===0||o.value==='all'||Number(a[i-1].value)>=Number(o.value)||i===1));

async function clipboardTest(clipboard) {
  const button=element(),text={...element(),value:'Wang, R. (2026). Example. https://doi.org/test'},manual=element(),status=element();
  const tools={querySelector(s){return ({'.citation-text':text,'.citation-manual':manual,'.citation-status':status})[s];}};
  button.closest=()=>tools;button.hidden=true;
  vm.runInNewContext(js.match(/function initCitationCopy\(\) \{[\s\S]*?\n\}\ninitCitationCopy\(\);/)[0],{
    document:{querySelectorAll(){return [button];}},navigator:{clipboard}
  });
  assert.equal(button.hidden,false);
  await button.events.click();
  assert.equal(button.disabled,false);
  return {text,manual,status};
}
(async()=>{
  let copied;
  const success=await clipboardTest({async writeText(value){copied=value;}});
  assert.equal(copied,success.text.value);assert.equal(success.status.textContent,'Citation copied.');
  for(const clipboard of [undefined,{async writeText(){throw Error('Denied');}}]){
    const result=await clipboardTest(clipboard);
    assert.equal(result.manual.open,true);assert.ok(result.text.focused&&result.text.selected);
  }
  vm.runInNewContext(js.match(/function initPublications\(\) \{[\s\S]*?\n\}\npublications = initPublications\(\);/)[0],{document:{querySelector(){return null;}}});
  console.log('Passed author/title search, accent handling, combined year/topic/collection filters, reset, expansion and clipboard success/fallback.');
})().catch(error=>{console.error(error);process.exitCode=1;});
