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
from species import italicize  # noqa: E402
from site_paths import PAGE_PATHS, legacy_routes, write_page  # noqa: E402
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
    'reference-materials': ('Reference Materials | OFEL', 'Reference materials from the Oceanic Fisheries Ecosystem Laboratory.', 'resources'),
    'software': ('Software | OFEL', 'ALSCL: R and TMB tools for fisheries stock assessment using survey length data.', 'resources'),
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
    return f'news/{post["slug"]}.html'


blog_posts = '\n'.join(
    f'        <article class="blog-post"><a class="blog-post-link" href="{esc(post_url(post))}">'
    + (f'<img src="{esc(post["image"])}" alt="" width="1536" height="1024" loading="lazy" style="object-position: {esc(post.get("image_position", "55% 78%"))}">' if post.get('image')
       else '<span class="blog-post-placeholder" aria-hidden="true"><img src="assets/ofel-mark.png" alt="" width="96" height="96"></span>')
    + f'<div><p class="eyebrow"><time datetime="{esc(post["date"])}">{esc(pretty_date(post["date"]))}</time></p>'
    f'<h2>{italicize(esc(post["title"]))}</h2><p>{italicize(esc(post.get("summary", "")))}</p></div></a></article>'
    for post in posts
) if posts else '<div class="directory-empty"><p>Lab updates will appear here.</p><a class="text-link" href="research.html">' + icon('fish') + 'Explore our research</a></div>'


def post_page(post):
    """Article page for one news post."""
    NT = '<span class="sr-only"> (opens in a new tab)</span>'
    def block(item):
        if isinstance(item, str):
            return f'<p>{italicize(esc(item))}</p>'
        if 'heading' in item:
            return f'<h2>{esc(item["heading"])}</h2>'
        return (f'<figure class="news-inline-figure"><a href="{esc(item["figure"])}" target="_blank" rel="noopener noreferrer">'
                f'<img src="{esc(item["figure"])}" alt="{esc(item["alt"])}" width="{item["width"]}" height="{item["height"]}" loading="lazy">'
                f'<span class="sr-only"> (open full image in a new tab)</span></a>'
                f'<figcaption>{italicize(esc(item["caption"]))}<span>{esc(item["credit"])}</span></figcaption></figure>')
    body = ''.join(block(item) for item in post['body'])
    people_links = ''.join(
        f'<a href="members/{"fan-zhang" if name == "Fan Zhang" else slug_of(name)}.html">{esc(name)}</a>' for name in post.get('people', []))
    paper = post.get('paper')
    if paper and paper.get('cover'):
        cover = f'<img class="news-paper-cover" src="{esc(paper["cover"])}" alt="{esc(paper["journal"])} cover" width="240" height="315">'
    elif paper and paper.get('logo'):
        import re as _re
        box = _re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', (ROOT / paper['logo']).read_text())
        lw, lh = (box.group(1), box.group(2)) if box else ('300', '32')
        cover = f'<span class="news-paper-logo"><img src="{esc(paper["logo"])}" alt="{esc(paper["journal"])}" width="{lw}" height="{lh}"></span>'
    else:
        cover = icon('paper')
    paper_html = (f'<div class="news-paper"><span class="eyebrow">Read the paper</span>'
                  f'<a href="{esc(paper["url"])}" target="_blank" rel="noopener noreferrer">{cover}'
                  f'<span><strong>{italicize(esc(paper["title"]))}</strong>'
                  + (f'<small>{esc(paper["citation"])}</small>' if paper.get('citation') else '')
                  + f'<em>{esc(paper["journal"])}</em>'
                  + (f'<small>{esc(paper["issue"])}</small>' if paper.get('issue') else '')
                  + f'<span class="news-paper-go">Read on the journal website</span></span>{NT}</a></div>') if paper else ''
    source = post.get('source')
    source_html = (f'<p class="news-source">Source: <a href="{esc(source["url"])}" target="_blank" rel="noopener noreferrer">'
                   f'{esc(source["label"])}{NT}</a><br><span>{esc(source["url"])}</span></p>') if source else ''
    image_style = f'object-position: {esc(post.get("image_position", "55% 78%"))}'
    if post.get('image_aspect_ratio'):
        image_style += f'; aspect-ratio: {esc(post["image_aspect_ratio"])}'
    image = (f'<figure class="news-figure"><img src="{esc(post["image"])}" alt="" width="1536" height="1024" style="{image_style}"></figure>' if post.get('image') else '')
    return (
        '    <article class="section detail-page news-article" aria-labelledby="news-title">\n'
        '      <div class="container news-container">\n'
        f'        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="news/index.html">News</a><span aria-hidden="true">/</span>'
        f'<span aria-current="page"><time datetime="{esc(post["date"])}">{esc(pretty_date(post["date"]))}</time></span></nav>\n'
        f'        <h1 id="news-title">{italicize(esc(post["title"]))}</h1>\n'
        f'        <p class="news-summary">{italicize(esc(post.get("summary", "")))}</p>\n'
        + (f'        <p class="news-people">Lab members: {people_links}</p>\n' if people_links else '')
        + f'        {image}\n        <div class="news-body">{body}</div>\n        {paper_html}\n        {source_html}\n'
        '      </div>\n    </article>\n'
    )


# Homepage navigation cards combine cover images with short content previews.
_spec = importlib.util.spec_from_file_location('publications', ROOT / 'scripts/build-publications.py')
publications = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(publications)
pubs = publications.page_records()
lab_pubs = [p for p in pubs if publications.is_lab_paper(p)]
recent = lab_pubs or sorted(pubs, key=lambda p: (p['year'], p.get('date', '')), reverse=True)


def short(text, limit):
    return text if len(text) <= limit else text[:limit].rsplit(' ', 1)[0] + '…'


latest_news = posts[0] if posts else None
news_background = latest_news.get('image') if latest_news else None
news_visual = (
    f'<div class="mock-panel mock-paper" style="align-self: end">'
    f'<span class="mock-label">Latest news · {esc(pretty_date(latest_news["date"]))}</span>'
    f'<strong>{esc(latest_news["title"])}</strong></div>'
) if latest_news else ''
# Editorially selected homepage feature: Runze Wang's Fish and Fisheries paper.
latest = next(p for p in pubs if p['doi'].lower() == '10.1111/faf.70077')
latest_authors = ', '.join(f"{a['given'][0]}. {a['family']}" for a in latest['authors'][:3]) + (' et al.' if len(latest['authors']) > 3 else '')
latest_cover = next((post['paper']['cover'] for post in posts
                     if post.get('paper', {}).get('cover')
                     and latest['doi'].lower() in post['paper'].get('url', '').lower()), None)
gateways = [
    ('news/index.html', 'News', 'Lab updates, new papers, and life in the laboratory.', news_background or 'assets/research/climate-ecosystems.webp', latest_news.get('image_position', '50% 50%') if latest_news else '30% 50%', 'book',
     news_visual),
    ('members/index.html', 'People', 'Meet the faculty, postdoctoral researchers, and students behind our work.', 'assets/people/fan-zhang.jpg', '70% 50%', 'people',
     '<div class="mock-panel mock-paper" style="align-self: end"><span class="mock-label">Our community</span>'
     '<strong>Faculty, postdocs &amp; graduate students</strong></div>'),
    ('publications.html', 'Publications', 'Peer-reviewed research on stock assessment, ecosystems, vessels, and fish biology.', latest_cover or 'assets/research/population-assessment.webp', '50% 0%' if latest_cover else '40% 50%', 'paper',
     f'<div class="mock-panel mock-paper gateway-publication-preview"><span class="mock-label">{esc(latest["journal"])} · {latest["year"]}</span>'
     f'<strong>{italicize(esc(short(latest["title"], 80)))}</strong><small>{esc(latest_authors)}</small>'
     f'<small class="gateway-publication-meta">{len(pubs)} publications · BibTeX available</small></div>'),
    ('contact.html', 'Contact &amp; Join Us', 'Graduate study, research visits, and collaboration with Fan Zhang.', 'assets/research/vessel-ai.webp', '55% 45%', 'mail',
     '<div class="mock-panel mock-mail"><span class="mock-label">New message</span>'
     '<div class="mock-field"><em>To</em>f-zhang@shou.edu.cn</div><div class="mock-field"><em>Subject</em>Research enquiry</div>'
     '<div class="mock-lines"><i></i><i></i></div><span class="mock-send">Send</span></div>'
     '<div class="mock-pills"><span>Graduate study</span><span>Research visits</span><span>Collaboration</span></div>'),
]
gateway_cards = '\n'.join(
    f'          <a class="gateway-card{" gateway-card-journal" if href == "publications.html" and latest_cover else ""}" href="{href}" data-reveal style="--reveal-delay: {n * .1:.1f}s">'
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
    for token, value in {'{{title}}': title, '{{description}}': description, '{{canonical}}': BASE + ('' if name == 'index' else PAGE_PATHS[name])}.items():
        head = head.replace(token, esc(value))
    content = expand((TEMPLATES / PAGE_PATHS[name]).read_text())
    for token, value in tokens.items():
        content = content.replace(token, value)
    write_page(PAGE_PATHS[name],
        head + f'<body id="top" data-page="{name}" data-nav-section="{nav}">\n'
        '  <a class="skip-link" href="#main">Skip to content</a>\n' + header
        + '\n  <main id="main">\n' + content + '  </main>\n\n' + footer + '</body>\n</html>\n'
    )

for post in posts:
    head = (TEMPLATES / 'head.html').read_text().replace('{{asset_version}}', asset_version())
    for token, value in {'{{title}}': post['title'] + ' | OFEL News', '{{description}}': post.get('summary', post['title']),
                         '{{canonical}}': BASE + post_url(post)}.items():
        head = head.replace(token, esc(value))
    write_page(post_url(post),
        head + '<body id="top" data-page="news-post" data-nav-section="news">\n'
        '  <a class="skip-link" href="#main">Skip to content</a>\n' + header
        + '\n  <main id="main">\n' + post_page(post) + '  </main>\n\n' + footer + '</body>\n</html>\n'
    )

for builder in ('build-people.py', 'build-publications.py'):
    subprocess.run([sys.executable, str(ROOT / 'scripts' / builder)], check=True)
print(f'Built {len(PAGES)} static pages and {len(posts)} news articles with shared navigation and footer.')

# A single GitHub Pages fallback preserves bookmarked URLs without keeping dozens of root-level stubs.
write_page('404.html', (TEMPLATES / '404.html').read_text().replace('{{legacy_routes}}', json.dumps(legacy_routes(), ensure_ascii=True)))
