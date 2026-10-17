"""Build the static multipage lab website; no runtime framework is required."""

import hashlib
import importlib.util
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
    'fan-zhang': ('Fan Zhang | OFEL', 'Fan Zhang, Professor and Doctoral Supervisor at the College of Marine Living Resource Sciences and Management, Shanghai Ocean University; Chief Scientist for China at ICCAT; principal investigator of OFEL.', 'people'),
    'members': ('Current Members | OFEL', 'Meet the faculty, postdoctoral researchers, PhD students and master’s students of OFEL.', 'people'),
    'alumni': ('Alumni | OFEL', 'The Oceanic Fisheries Ecosystem Laboratory alumni community.', 'people'),
    'publications': ('Publications | OFEL', 'Selected lab publications and publications co-authored by Fan Zhang, with research-topic filters and citation downloads.', 'publications'),
    'blog': ('News | OFEL', 'News, research updates and life in the Oceanic Fisheries Ecosystem Laboratory.', 'news'),
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
def reel_cards(copy):
    # Copies exist only to keep the loop seamless; they are hidden from keyboard and screen readers.
    hidden = ' tabindex="-1"' if copy else ''
    return ''.join(
        f'<a class="reel-card" href="research.html#{esc(item["slug"])}"{hidden} '
        f'aria-label="Explore {esc(item["title"])}"><img src="{esc(item["image"])}" alt="{"" if copy else esc(item["alt"])}" '
        f'width="1536" height="1024" {priority if n == 0 and not copy else lazy}>'
        f'<div class="reel-card-copy"><span>{esc(item["label"])}</span><h3>{esc(item["title"])}</h3></div></a>'
        for n, item in enumerate(directions)
    )


carousel = ('          <div class="reel-marquee">\n'
            f'            <div class="reel-group">{reel_cards(False)}</div>\n'
            + ''.join(f'            <div class="reel-group reel-copy" aria-hidden="true" inert>{reel_cards(True)}</div>\n'
                      for _ in range(1))
            + '          </div>')
posts = sorted(json.loads((ROOT / 'assets/blog.json').read_text())['posts'], key=lambda p: p['date'], reverse=True)


def pretty_date(iso):
    import datetime
    return datetime.date.fromisoformat(iso).strftime('%-d %B %Y')


def slug_of(name):
    import re
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def post_url(post):
    return f'news-{post["slug"]}.html'


blog_posts = '\n'.join(
    f'        <article class="blog-post"><a class="blog-post-link" href="{esc(post_url(post))}">'
    + (f'<img src="{esc(post["image"])}" alt="" width="1536" height="1024" loading="lazy">' if post.get('image') else '')
    + f'<div><p class="eyebrow"><time datetime="{esc(post["date"])}">{esc(pretty_date(post["date"]))}</time></p>'
    f'<h2>{esc(post["title"])}</h2><p>{esc(post.get("summary", ""))}</p></div></a></article>'
    for post in posts
) if posts else '<div class="directory-empty"><p>Lab updates will appear here.</p><a class="text-link" href="research.html">' + icon('fish') + 'Explore our research</a></div>'


def post_page(post):
    """Article page for one news post."""
    NT = '<span class="sr-only"> (opens in a new tab)</span>'
    body = ''.join(f'<p>{esc(par)}</p>' for par in post['body'])
    people_links = ''.join(
        f'<a href="{"fan-zhang" if name == "Fan Zhang" else slug_of(name)}.html">{esc(name)}</a>' for name in post.get('people', []))
    paper = post.get('paper')
    paper_html = (f'<div class="news-paper"><span class="eyebrow">Read the paper</span>'
                  f'<a href="{esc(paper["url"])}" target="_blank" rel="noopener noreferrer">{icon("paper")}'
                  f'<span><strong>{esc(paper["title"])}</strong><em>{esc(paper["journal"])}</em></span>{NT}</a></div>') if paper else ''
    source = post.get('source')
    source_html = (f'<p class="news-source">Source: <a href="{esc(source["url"])}" target="_blank" rel="noopener noreferrer">'
                   f'{esc(source["label"])}{NT}</a><br><span>{esc(source["url"])}</span></p>') if source else ''
    image = (f'<figure class="news-figure"><img src="{esc(post["image"])}" alt="" width="1536" height="1024"></figure>' if post.get('image') else '')
    return (
        '    <article class="section detail-page news-article" aria-labelledby="news-title">\n'
        '      <div class="container news-container">\n'
        f'        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="blog.html">News</a><span aria-hidden="true">/</span>'
        f'<span aria-current="page"><time datetime="{esc(post["date"])}">{esc(pretty_date(post["date"]))}</time></span></nav>\n'
        f'        <h1 id="news-title">{esc(post["title"])}</h1>\n'
        f'        <p class="news-summary">{esc(post.get("summary", ""))}</p>\n'
        + (f'        <p class="news-people">Lab members: {people_links}</p>\n' if people_links else '')
        + f'        {image}\n        <div class="news-body">{body}</div>\n        {paper_html}\n        {source_html}\n'
        '      </div>\n    </article>\n'
    )


# Homepage "Discover the lab" cards: illustration background, copy, and a floating mockup built from lab data.
people = json.loads((ROOT / 'assets/people.json').read_text())
members = [m for g in people['groups'] for m in g['members']]
alumni_count = sum(len(c['members']) for c in people.get('alumni', []))
_spec = importlib.util.spec_from_file_location('publications', ROOT / 'scripts/build-publications.py')
publications = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(publications)
pubs = publications.page_records()
lab_pubs = [p for p in pubs if publications.is_lab_paper(p)]
recent = lab_pubs or sorted(pubs, key=lambda p: (p['year'], p.get('date', '')), reverse=True)


def short(text, limit):
    return text if len(text) <= limit else text[:limit].rsplit(' ', 1)[0] + '…'


def initials(name):
    return ''.join(part[0] for part in name.split()[:2]).upper()


news_items = ''.join(
    f'<div class="mock-news" style="--i:{n}"><span class="mock-tag">New paper · {p["year"]}</span>'
    f'<strong>{esc(short(p["title"], 64))}</strong><small>{esc(p["journal"])}</small></div>'
    for n, p in enumerate(recent[:3])
)
avatars = ''.join(f'<span class="mock-avatar" style="--i:{n}">{esc(initials(m["name"]))}</span>' for n, m in enumerate(members[:8]))
latest = recent[0]
latest_authors = ', '.join(f"{a['given'][0]}. {a['family']}" for a in latest['authors'][:3]) + (' et al.' if len(latest['authors']) > 3 else '')
journal_chips = ''.join(f'<span>{esc(j)}</span>' for j in list(dict.fromkeys(p['journal'] for p in recent))[:3])
gateways = [
    ('blog.html', 'News', 'Lab updates, new papers, and life in the laboratory.', 'assets/research/climate-ecosystems.webp', '30% 50%', 'book',
     f'<div class="mock-stack">{news_items}</div>'),
    ('members.html', 'People', 'Meet the faculty, postdoctoral researchers, and students behind our work.', 'assets/research/adaptive-management.webp', '45% 60%', 'people',
     f'<div class="mock-panel mock-team"><span class="mock-label">Our team</span><div class="mock-avatars">{avatars}</div>'
     f'<div class="mock-lines"><i></i><i></i></div></div>'
     f'<span class="mock-chip mock-chip-a">{len(members)} current members</span>'
     f'<span class="mock-chip mock-chip-b">{alumni_count} alumni</span>'),
    ('publications.html', 'Publications', 'Peer-reviewed research on stock assessment, ecosystems, vessels, and fish biology.', 'assets/research/population-assessment.webp', '40% 50%', 'paper',
     f'<div class="mock-panel mock-paper"><span class="mock-label">{esc(latest["journal"])} · {latest["year"]}</span>'
     f'<strong>{esc(short(latest["title"], 80))}</strong><small>{esc(latest_authors)}</small>'
     f'<div class="mock-lines"><i></i><i></i><i></i></div></div>'
     f'<span class="mock-chip mock-chip-a">{len(pubs)} publications</span>'
     f'<span class="mock-chip mock-chip-b">BibTeX</span>'),
    ('contact.html', 'Contact &amp; Join Us', 'Graduate study, research visits, and collaboration with Fan Zhang.', 'assets/research/vessel-ai.webp', '55% 45%', 'mail',
     '<div class="mock-panel mock-mail"><span class="mock-label">New message</span>'
     '<div class="mock-field"><em>To</em>f-zhang@shou.edu.cn</div><div class="mock-field"><em>Subject</em>Research enquiry</div>'
     '<div class="mock-lines"><i></i><i></i></div><span class="mock-send">Send</span></div>'
     '<div class="mock-pills"><span>Graduate study</span><span>Research visits</span><span>Collaboration</span></div>'),
]
gateway_cards = '\n'.join(
    f'          <a class="gateway-card" href="{href}" data-reveal style="--reveal-delay: {n * .1:.1f}s">'
    f'<img class="gateway-bg" src="{img}" alt="" width="1536" height="1024" loading="lazy" style="object-position: {pos}">'
    f'<div class="gateway-copy"><h3>{title}</h3><p>{desc}</p></div>'
    f'<div class="gateway-visual" aria-hidden="true">{visual}</div>'
    f'<span class="gateway-go" aria-hidden="true">{icon(ic)}</span></a>'
    for n, (href, title, desc, img, pos, ic, visual) in enumerate(gateways)
)

tokens = {
    '{{gateway_cards}}': gateway_cards,
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

for post in posts:
    head = (TEMPLATES / 'head.html').read_text().replace('{{asset_version}}', asset_version())
    for token, value in {'{{title}}': post['title'] + ' | OFEL News', '{{description}}': post.get('summary', post['title']),
                         '{{canonical}}': BASE + post_url(post)}.items():
        head = head.replace(token, esc(value))
    (ROOT / post_url(post)).write_text(
        head + '<body id="top" data-page="news-post" data-nav-section="news">\n'
        '  <a class="skip-link" href="#main">Skip to content</a>\n' + header
        + '\n  <main id="main">\n' + post_page(post) + '  </main>\n\n' + footer + '</body>\n</html>\n'
    )

for builder in ('build-people.py', 'build-publications.py'):
    subprocess.run([sys.executable, str(ROOT / 'scripts' / builder)], check=True)
print(f'Built {len(PAGES)} static pages and {len(posts)} news articles with shared navigation and footer.')
