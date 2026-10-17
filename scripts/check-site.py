"""Check built HTML links, fragments, images and shared assets without a server."""

from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit
from site_paths import BASE, output_path

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = set()
        self.links = []
        self.page_links = []
        self.is_redirect = False
        self.canonical = None
        self.news_dates = []
        self.home_news_image = None
        self.home_news_text = []
        self._in_home_news = False
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'refresh':
            self.is_redirect = True
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href')
        if tag == 'a' and attrs.get('href'):
            self.page_links.append(attrs['href'])
        if tag == 'a' and 'gateway-card' in attrs.get('class', '').split() and attrs.get('href') == 'news/':
            self._in_home_news = True
        if self._in_home_news and tag == 'img' and 'gateway-bg' in attrs.get('class', '').split():
            self.home_news_image = attrs.get('src')
        if tag == 'time' and attrs.get('datetime'):
            self.news_dates.append(attrs['datetime'])
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        self.links.extend(attrs[key] for key in ('href', 'src', 'poster') if attrs.get(key))
        if attrs.get('srcset'):
            self.links.extend(entry.strip().split()[0] for entry in attrs['srcset'].split(','))

    def handle_data(self, text):
        if self._in_home_news:
            self.home_news_text.append(text)

    def handle_endtag(self, tag):
        if tag == 'a':
            self._in_home_news = False


def main():
    paths = list(ROOT.glob('*.html'))
    for folder in ('news', 'members', 'resources', 'research', 'publications', 'contact'):
        paths.extend((ROOT / folder).rglob('*.html'))
    pages = {path.resolve(): Page(path) for path in paths}
    errors = []
    references = 0
    for path, page in pages.items():
        if page.is_redirect or path.name == '404.html':
            continue
        expected_canonical = BASE + path.relative_to(ROOT).as_posix().removesuffix('index.html')
        if page.canonical != expected_canonical:
            errors.append(f'{path.relative_to(ROOT)}: canonical URL must use its clean directory path')
        for link in page.page_links:
            parts = urlsplit(link)
            internal = not (parts.scheme or parts.netloc) or link.startswith(BASE)
            if internal and parts.path.endswith('.html'):
                errors.append(f'{path.relative_to(ROOT)}: navigation must use clean URLs: {link}')
    posts = json.loads((ROOT / 'assets/blog.json').read_text())['posts']
    expected_dates = sorted((post['date'] for post in posts), reverse=True)
    if pages[(ROOT / output_path('news/index.html')).resolve()].news_dates != expected_dates:
        errors.append('news/index.html: news must appear newest first by date')
    if posts:
        newest = max(posts, key=lambda post: post['date'])
        home = pages[(ROOT / 'index.html').resolve()]
        home_text = ' '.join(''.join(home.home_news_text).split())
        if home.home_news_image != newest.get('image') or ' '.join(newest['title'].split()) not in home_text:
            errors.append('index.html: homepage News must show the newest dated news, including its title and cover')
    for path, page in pages.items():
        for link in page.links:
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            references += 1
            target = (path.parent / unquote(parts.path)).resolve() if parts.path else path
            if not target.is_relative_to(ROOT):
                errors.append(f'{path.relative_to(ROOT)}: path outside site: {link}')
                continue
            if target.is_dir():
                target /= 'index.html'
            if not target.is_file():
                errors.append(f'{path.relative_to(ROOT)}: missing file: {link}')
            elif parts.fragment and target in pages and unquote(parts.fragment) not in pages[target].ids:
                errors.append(f'{path.relative_to(ROOT)}: missing anchor: {link}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Checked {len(pages)} pages and {references} local references; all links, anchors and assets exist.')


if __name__ == '__main__':
    main()
