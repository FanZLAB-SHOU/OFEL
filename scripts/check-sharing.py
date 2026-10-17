"""Verify sitemap coverage, per-page social metadata and all preview image files."""
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote
import xml.etree.ElementTree as ET

from page_metadata import DEFAULT_IMAGE, share_image
from site_paths import BASE, clean_url, output_path, slugify, source_paths

ROOT = Path(__file__).resolve().parents[1]


class Head(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.metadata = {}
        self.counts = Counter()
        self.links = {}
        self.feed(markup.split('</head>',1)[0])

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = attrs.get('property') or attrs.get('name')
            if key:
                self.metadata[key] = attrs.get('content','')
                self.counts[key] += 1
        if tag == 'link':
            self.links[attrs.get('rel')] = attrs.get('href')


def main():
    namespace = {'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    sitemap = ET.parse(ROOT/'sitemap.xml')
    urls = [e.text for e in sitemap.findall('s:url/s:loc',namespace)]
    expected = {BASE + clean_url(path) for path in source_paths()}
    assert set(urls)==expected and len(urls)==len(expected), 'Sitemap must contain each canonical content page exactly once'
    assert all(u.endswith('/') and '#' not in u and '?' not in u and '.html' not in u for u in urls)
    overrides = {'members/fan-zhang.html':('assets/people/fan-zhang.jpg','profile')}
    for post in json.loads((ROOT/'assets/blog.json').read_text())['posts']:
        overrides[f'news/{post["slug"]}.html'] = (post.get('image'),'article')
    people = json.loads((ROOT/'assets/people.json').read_text())
    for group in people['groups'] + people.get('alumni',[]):
        for person in group['members']:
            if not person.get('profile_ref'):
                overrides[f'members/{slugify(person["name"])}.html'] = (person.get('photo'),'profile')
    images = set()
    required = ['description','og:title','og:description','og:type','og:url','og:image','og:image:alt',
                'og:image:type','twitter:card','twitter:title','twitter:description','twitter:image','twitter:image:alt']
    for source in source_paths():
        markup = (ROOT/output_path(source)).read_text()
        assert '{{' not in markup, f'Unresolved template in {source}'
        head = Head(markup)
        for key in required:
            assert head.counts[key]==1 and head.metadata[key], f'{source}: missing/duplicate/empty {key}'
        canonical = BASE + clean_url(source)
        assert head.links['canonical']==head.metadata['og:url']==canonical
        assert head.links['sitemap']==BASE+'sitemap.xml'
        original, kind = overrides.get(source,(None,'website'))
        image = BASE + share_image(original)['src']
        assert head.metadata['og:image']==head.metadata['twitter:image']==image, f'{source}: incorrect preview image'
        assert head.metadata['og:type']==kind
        assert head.metadata['description']==head.metadata['og:description']==head.metadata['twitter:description']
        assert head.metadata['og:title']==head.metadata['twitter:title']
        assert image.startswith(BASE) and (ROOT/unquote(image[len(BASE):])).is_file()
        assert head.metadata['og:image:type'] in {'image/png','image/jpeg','image/webp'}
        images.add(image)
    assert Head((ROOT/'index.html').read_text()).metadata['og:image']==BASE+DEFAULT_IMAGE
    print(f'Checked {len(urls)} sitemap URLs, per-page metadata and {len(images)} preview images.')


if __name__=='__main__':
    main()
