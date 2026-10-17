"""Output paths and relative links shared by the static page builders.

Templates and generated fragments use paths relative to the site root. Only
the output writer converts them to paths relative to the destination page.
"""

import html
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
PAGE_PATHS = {
    'index': 'index.html',
    'research': 'research.html',
    'fan-zhang': 'members/fan-zhang.html',
    'members': 'members/index.html',
    'alumni': 'members/alumni.html',
    'publications': 'publications.html',
    'blog': 'news/index.html',
    'contact': 'contact.html',
}


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def legacy_routes():
    routes = {name + '.html': path for name, path in PAGE_PATHS.items() if path != name + '.html'}
    people = json.loads((ROOT / 'assets/people.json').read_text())
    for group in people['groups'] + people.get('alumni', []):
        for person in group['members']:
            slug = slugify(person['name'])
            routes[slug + '.html'] = f'members/{slug}.html'
    posts = json.loads((ROOT / 'assets/blog.json').read_text())['posts']
    routes.update({f'news-{post["slug"]}.html': f'news/{post["slug"]}.html' for post in posts})
    return routes


def rebase_links(markup, destination):
    parent = posixpath.dirname(destination) or '.'

    def relative(value):
        parts = urlsplit(html.unescape(value))
        if parts.scheme or parts.netloc or not parts.path or parts.path.startswith('/'):
            return value
        path = posixpath.relpath(parts.path, parent)
        return html.escape(urlunsplit(('', '', path, parts.query, parts.fragment)), quote=True)

    def attribute(match):
        attribute, quote, value = match.groups()
        if attribute.lower() == 'srcset':
            entries = []
            for entry in value.split(','):
                url, *descriptor = entry.strip().split()
                entries.append(' '.join([relative(url)] + descriptor))
            value = ', '.join(entries)
        else:
            value = relative(value)
        return f'{attribute}={quote}{value}{quote}'

    return re.sub(r'\b(href|src|srcset)=([\"\'])(.*?)\2', attribute, markup, flags=re.I)


def write_page(destination, markup):
    path = ROOT / destination
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rebase_links(markup, destination))
