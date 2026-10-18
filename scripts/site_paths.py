"""Clean public URLs, static output paths, and backwards-compatible redirects.

Templates keep their original source filenames. Builders publish directory index
pages and convert root-authored links to clean URLs relative to each output page.
"""

import html
import json
import posixpath
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://fanzhang-lab-shou.github.io/OFEL/'
PAGE_PATHS = {
    'index': 'index.html',
    'research': 'research/themes.html',
    'collaborators': 'research/collaborators.html',
    'fan-zhang': 'members/fan-zhang.html',
    'members': 'members/index.html',
    'alumni': 'members/alumni.html',
    'publications': 'publications.html',
    'blog': 'news/index.html',
    'contact': 'contact.html',
    'more': 'more.html',
    'reference-materials': 'resources/reference-materials.html',
    'software': 'resources/software.html',
}


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def directory_url(path):
    if path == '404.html':
        return path
    if path == 'index.html':
        return ''
    if path.endswith('/index.html'):
        return path[:-10]
    return path[:-5] + '/' if path.endswith('.html') else path


@lru_cache(maxsize=1)
def source_paths():
    paths = set(PAGE_PATHS.values())
    people = json.loads((ROOT / 'assets/people.json').read_text())
    for group in people['groups'] + people.get('alumni', []):
        for person in group['members']:
            paths.add(f'members/{slugify(person.get("profile_ref", person["name"]))}.html')
    posts = json.loads((ROOT / 'assets/blog.json').read_text())['posts']
    paths.update(f'news/{post["slug"]}.html' for post in posts)
    return tuple(sorted(paths))


@lru_cache(maxsize=1)
def legacy_routes():
    routes = {source: directory_url(source) for source in source_paths()}
    routes.update({name + '.html': directory_url(path) for name, path in PAGE_PATHS.items()})
    for source in source_paths():
        if source.startswith('members/') and not source.endswith('/index.html'):
            routes[source.removeprefix('members/')] = directory_url(source)
        elif source.startswith('news/') and not source.endswith('/index.html'):
            routes['news-' + source.removeprefix('news/')] = directory_url(source)
    return routes


def clean_url(path):
    return legacy_routes().get(path, directory_url(path))


def output_path(source):
    if source == '404.html':
        return source
    return clean_url(source) + 'index.html'


def rebase_links(markup, destination):
    parent = posixpath.dirname(destination) or '.'

    def relative(value):
        parts = urlsplit(html.unescape(value))
        if parts.scheme or parts.netloc:
            if value.startswith(BASE):
                tail = urlsplit(html.unescape(value[len(BASE):]))
                return html.escape(BASE + urlunsplit(('', '', clean_url(tail.path), tail.query, tail.fragment)), quote=True)
            return value
        if not parts.path or parts.path.startswith('/'):
            return value
        target = clean_url(parts.path)
        path = posixpath.relpath(target or '.', parent)
        if not target or target.endswith('/'):
            path += '/'
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
    from responsive_images import responsive_images
    destination = output_path(destination)
    path = ROOT / destination
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rebase_links(responsive_images(markup), destination))


def write_legacy_redirects():
    """Keep former nested HTML URLs as small, direct redirects, never duplicate content."""
    count = 0
    for source in source_paths():
        destination = output_path(source)
        if source == destination:
            continue
        public = clean_url(source)
        target = posixpath.relpath(public or '.', posixpath.dirname(source) or '.') + '/'
        link = html.escape(target, quote=True)
        canonical = html.escape(BASE + public, quote=True)
        markup = (
            '<!doctype html>\n<html lang="en"><head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="robots" content="noindex">\n'
            f'<link rel="canonical" href="{canonical}">\n'
            f'<meta http-equiv="refresh" content="0; url={link}">\n'
            '<title>Page moved | OFEL</title>\n'
            '<script>const target = new URL(' + json.dumps(target) + ', location.href); '
            'target.search = location.search; target.hash = location.hash; location.replace(target.href);</script>\n'
            f'</head><body><p>This page has moved. <a href="{link}">Continue to OFEL</a>.</p></body></html>\n'
        )
        path = ROOT / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markup)
        count += 1
    return count
