"""Build the static multipage lab website; no runtime framework is required."""

import hashlib
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from icons import expand, icon  # noqa: E402
TEMPLATES = ROOT / 'templates'
BASE = 'https://fanzhang-lab-shou.github.io/OFEL/'
PAGES = {
    'index': ('OFEL | Oceanic Fisheries Ecosystem Laboratory', 'Research on fish populations, fisheries data and marine life at Shanghai Ocean University.', 'home'),
    'research': ('Research | OFEL', 'Population dynamics and stock assessment, AI and fishing-vessel behavior, and fish biology and DNA research.', 'research'),
    'fan-zhang': ('Fan Zhang | OFEL', 'Fan Zhang, Professor and Doctoral Supervisor at Shanghai Ocean University and principal investigator of OFEL.', 'people'),
    'members': ('Current Members | OFEL', 'Meet the faculty, postdoctoral researchers, PhD students and master’s students of OFEL.', 'people'),
    'alumni': ('Alumni | OFEL', 'The Oceanic Fisheries Ecosystem Laboratory alumni community.', 'people'),
    'publications': ('Publications | OFEL', 'Selected lab publications and publications co-authored by Fan Zhang, with research-topic filters and citation downloads.', 'publications'),
    'blog': ('Lab Blog | OFEL', 'News, research updates and life in the Oceanic Fisheries Ecosystem Laboratory.', 'info'),
    'contact': ('Contact & Join Us | OFEL', 'Contact the Oceanic Fisheries Ecosystem Laboratory at Shanghai Ocean University about research, visits and collaboration.', 'info'),
}


def esc(value):
    return html.escape(value, quote=True)


def asset_version():
    """Short content hash of the stylesheet and script, appended to their URLs to bust browser caches."""
    digest = hashlib.sha256((ROOT / 'styles.css').read_bytes() + (ROOT / 'script.js').read_bytes())
    return digest.hexdigest()[:10]


def direction_card(item):
    secondary = not item['primary']
    kind = ' research-item-secondary' if secondary else ''
    tag = f'<span class="research-tag">{esc(item["tag"])}</span>' if item.get('tag') else ''
    return (
        f'          <article class="research-item{kind}" id="{esc(item["slug"])}">'
        f'<div class="research-art"><img src="{esc(item["image"])}" alt="{esc(item["alt"])}" '
        'width="1536" height="1024" loading="lazy"></div>'
        f'<div class="research-copy"><span class="research-number">{esc(item["label"])}</span>'
        f'<h2>{esc(item["title"])}</h2><p>{esc(item["description"])}</p>{tag}</div></article>'
    )


directions = json.loads((ROOT / 'assets/research.json').read_text())['directions']
core = [item for item in directions if item['primary']]
priority = 'fetchpriority="high"'
lazy = 'loading="lazy"'
carousel = '\n'.join(
    f'          <a class="reel-card" href="research.html#{esc(item["slug"])}" '
    f'aria-label="Explore {esc(item["title"])}"><img src="{esc(item["image"])}" alt="{esc(item["alt"])}" '
    f'width="1536" height="1024" {priority if n == 0 else lazy}>'
    f'<div class="reel-card-copy"><span>{esc(item["label"])}</span><h3>{esc(item["title"])}</h3>'
    '<span class="reel-card-arrow">' + icon('fish') + '</span></div></a>'
    for n, item in enumerate(core)
)
posts = json.loads((ROOT / 'assets/blog.json').read_text())['posts']
blog_posts = '\n'.join(
    f'<article class="blog-post"><p class="eyebrow">{esc(post.get("date", "Lab news"))}</p>'
    f'<h2><a href="{esc(post["url"])}">{esc(post["title"])}</a></h2><p>{esc(post.get("summary", ""))}</p></article>'
    for post in posts
) if posts else '<div class="directory-empty"><p>Lab updates will appear here.</p><a class="text-link" href="research.html">' + icon('fish') + 'Explore our research</a></div>'
tokens = {
    '{{blog_posts}}': blog_posts,
    '{{research_carousel}}': carousel,
    '{{research_primary}}': '\n'.join(direction_card(item) for item in core),
    '{{research_secondary}}': '\n'.join(direction_card(item) for item in directions if not item['primary']),
}
header = expand((TEMPLATES / 'header.html').read_text())
footer = expand((TEMPLATES / 'footer.html').read_text())
for name, (title, description, nav) in PAGES.items():
    head = (TEMPLATES / 'head.html').read_text().replace('{{asset_version}}', asset_version())
    for token, value in {'{{title}}': title, '{{description}}': description, '{{canonical}}': BASE + ('' if name == 'index' else name + '.html')}.items():
        head = head.replace(token, esc(value))
    content = expand((TEMPLATES / f'{name}.html').read_text())
    for token, value in tokens.items():
        content = content.replace(token, value)
    (ROOT / f'{name}.html').write_text(
        head + f'<body id="top" data-page="{name}" data-nav-section="{nav}">\n'
        '  <a class="skip-link" href="#main">Skip to content</a>\n' + header
        + '\n  <main id="main">\n' + content + '  </main>\n\n' + footer + '</body>\n</html>\n'
    )

for builder in ('build-people.py', 'build-publications.py'):
    subprocess.run([sys.executable, str(ROOT / 'scripts' / builder)], check=True)
print(f'Built {len(PAGES)} static pages with shared navigation and footer.')
