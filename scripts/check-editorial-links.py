"""Check News categories and one-direction-only representative publication links."""
from html.parser import HTMLParser
import html
import importlib.util
import json
from pathlib import Path
from site_paths import output_path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('publications',ROOT/'scripts/build-publications.py')
pubs=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pubs)
papers={p['doi'].lower():p for p in pubs.page_records()}
news=json.loads((ROOT/'assets/blog.json').read_text())
directions=json.loads((ROOT/'assets/research.json').read_text())['directions']


class Themes(HTMLParser):
    def __init__(self,markup):
        super().__init__();self.current=None;self.links={};self.software=[];self.origins=[];self.in_origin=False;self.feed(markup)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);classes=a.get('class','').split()
        if tag=='article' and 'research-item' in classes:
            self.current=a['id'];self.links[self.current]=[]
        if tag=='a' and 'research-paper' in classes:self.links[self.current].append(a['href'])
        if tag=='a' and 'research-software' in classes:self.software.append(a['href'])
        if 'research-paper-origin' in classes:self.in_origin=True
    def handle_data(self,data):
        if self.in_origin:self.origins.append(data)
    def handle_endtag(self,tag):
        if tag=='article':self.current=None
        if tag=='span':self.in_origin=False


assert all(p.get('category') in news['categories'] for p in news['posts'])
for post in news['posts']:
    markup=(ROOT/output_path(f'news/{post["slug"]}.html')).read_text()
    assert f'?category={post["category"]}' in markup
    assert news['categories'][post['category']] in html.unescape(markup)
index=(ROOT/'index.html').read_text()
assert 'class="news-filters"' not in index and 'class="news-category"' not in index
themes=Themes((ROOT/output_path('research/themes.html')).read_text())
seen=set();external=0
for direction in directions:
    dois=direction['publications']
    assert 2<=len(dois)<=3
    assert themes.links[direction['slug']]==[papers[d.lower()]['source'] for d in dois]
    for doi in dois:
        key=doi.lower();assert key not in seen;seen.add(key)
        pubs.validate(papers[key])
        if not pubs.is_lab_paper(papers[key]):external+=1
assert len(themes.software)==1 and themes.software[0].endswith('resources/software/')
assert themes.origins.count('Fan Zhang & collaborators')==external
assert len(themes.origins)==len(seen)
print(f'Checked {len(news["posts"])} categorized news items and {len(seen)} distinct representative papers across {len(directions)} themes; homepage categories remain absent.')
