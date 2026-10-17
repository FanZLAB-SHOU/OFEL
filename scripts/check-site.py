"""Check built HTML links, fragments, images and shared assets without a server."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids = set()
        self.links = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        self.links.extend(attrs[key] for key in ('href', 'src') if attrs.get(key))
        if attrs.get('srcset'):
            self.links.extend(entry.strip().split()[0] for entry in attrs['srcset'].split(','))


def main():
    paths = list(ROOT.glob('*.html'))
    for folder in ('news', 'members', 'resources'):
        paths.extend((ROOT / folder).glob('*.html'))
    pages = {path.resolve(): Page(path) for path in paths}
    errors = []
    references = 0
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
