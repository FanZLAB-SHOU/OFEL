"""Build the static multipage lab website; no runtime framework is required."""

import hashlib
import importlib.util
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from icons import expand, icon  # noqa: E402
from species import italicize  # noqa: E402
from site_paths import PAGE_PATHS, clean_url, legacy_routes, write_legacy_redirects, write_page  # noqa: E402
from page_metadata import render_head, write_sitemap  # noqa: E402
TEMPLATES = ROOT / 'templates'
BASE = 'https://fanzhang-lab-shou.github.io/OFEL/'
PAGES = {
    'index': ('OFEL | Oceanic Fisheries Ecosystem Laboratory', 'Research on fish populations, fisheries data and marine life at Shanghai Ocean University.', 'home'),
    'research': ('Research Themes | OFEL', 'Population dynamics and stock assessment, AI and fishing-vessel behavior, and fish biology and DNA research.', 'research'),
    'collaborators': ('Collaborators | OFEL', 'Research collaborators of the Oceanic Fisheries Ecosystem Laboratory.', 'research'),
    'fan-zhang': ('Fan Zhang | OFEL', 'Fan Zhang, Professor and Doctoral Supervisor at the College of Marine Living Resource Sciences and Management, Shanghai Ocean University; Chief Scientist for China at ICCAT; principal investigator of OFEL.', 'people'),
    'members': ('Current Members | OFEL', 'Meet the faculty, postdoctoral researchers, PhD students and master’s students of OFEL.', 'people'),
    'alumni': ('Alumni | OFEL', 'The Oceanic Fisheries Ecosystem Laboratory alumni community.', 'people'),
    'publications': ('Publications | OFEL', 'Verified publications by OFEL members and alumni, with lab and Fan Zhang collections, research-topic filters and citation downloads.', 'publications'),
    'blog': ('News | OFEL', 'News, research updates and life in the Oceanic Fisheries Ecosystem Laboratory.', 'news'),
    'contact': ('Contact & Join Us | OFEL', 'Contact the Oceanic Fisheries Ecosystem Laboratory at Shanghai Ocean University about research, visits and collaboration.', 'info'),
    'more': ('More | OFEL', 'Explore world clocks, current weather and the OFEL website’s visit statistics in one interactive view.', 'info'),
    'reference-materials': ('Reference Materials | OFEL', 'FishBase, Global Fishing Watch, FAO, and regional fisheries management organizations: resources for fish biology, vessel tracking, and fisheries management.', 'resources'),
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
    papers = []
    for doi in item.get('publications', []):
        paper = papers_by_doi[doi.lower()]
        origin = 'Lab research' if publications.is_lab_paper(paper) else 'Fan Zhang & collaborators'
        attribution = paper.get('attribution', {})
        if attribution.get('exclude_from_lab') and 'external_collaboration' in attribution.get('relationships', []):
            origin = 'External collaboration'
        papers.append(f'<li><a class="research-paper" href="{esc(paper["source"])}" target="_blank" rel="noopener noreferrer">'
                      f'<span class="research-paper-meta">{paper["year"]} · {esc(paper["journal"])}</span>'
                      f'<strong>{italicize(esc(paper["title"]))}</strong><span class="sr-only"> (opens in a new tab)</span></a>'
                      f'<span class="research-paper-origin">{esc(origin)}</span></li>')
    evidence = (f'<section class="research-evidence" aria-labelledby="{esc(item["slug"])}-papers">'
                f'<h3 id="{esc(item["slug"])}-papers">Selected publications</h3><ol class="research-publications">'
                + ''.join(papers) + '</ol>') if papers else ''
    if item.get('software'):
        tool = item['software']
        evidence += f'<a class="research-software" href="{esc(tool["href"])}">{icon("paper")}{esc(tool["label"])}{icon("right")}</a>'
    if papers:
        evidence += '</section>'
    return (
        f'          <article class="research-item{kind}" id="{esc(item["slug"])}">'
        f'<div class="research-art"><img src="{esc(item["image"])}" alt="{esc(item["alt"])}" '
        'width="1536" height="1024" loading="lazy"></div>'
        f'<div class="research-copy"><span class="research-number">{esc(item["label"])}</span>'
        f'<h2>{esc(item["title"])}</h2><p>{esc(item["description"])}</p>{tag}'
        + (f'</div>{evidence}</article>' if secondary else f'{evidence}</div></article>')
    )


directions = json.loads((ROOT / 'assets/research.json').read_text())['directions']
core = [item for item in directions if item['primary']]
priority = 'fetchpriority="high"'
lazy = 'loading="lazy"'
def reel_cards(copy):
    # Copies exist only to keep the loop seamless; they are hidden from keyboard and screen readers.
    hidden = ' tabindex="-1"' if copy else ''
    return ''.join(
        f'<a class="reel-card" href="research/themes.html#{esc(item["slug"])}"{hidden} '
        f'aria-label="Explore {esc(item["title"])}"><img class="home-research-image" src="{esc(item["image"])}" alt="{"" if copy else esc(item["alt"])}" '
        f'width="1536" height="1024" sizes="(max-width: 700px) max(calc(125vw - 80px), 540px), (max-width: 1292px) max(60vw, 540px), 775px" {lazy}>'
        f'<div class="reel-card-copy"><span>{esc(item["label"])}</span><h3>{esc(item["title"])}</h3></div></a>'
        for n, item in enumerate(directions)
    )


carousel = ('          <div class="reel-marquee">\n'
            f'            <div class="reel-group">{reel_cards(False)}</div>\n'
            + ''.join(f'            <div class="reel-group reel-copy" aria-hidden="true" inert>{reel_cards(True)}</div>\n'
                      for _ in range(1))
            + '          </div>')
blog = json.loads((ROOT / 'assets/blog.json').read_text())
posts = sorted(blog['posts'], key=lambda p: p['date'], reverse=True)
news_categories = blog['categories']
for post in posts:
    if post.get('category') not in news_categories:
        raise ValueError(f'Choose one news category for {post["slug"]}')
category_counts = {key: sum(post['category'] == key for post in posts) for key in news_categories}
news_filters = ''.join(
    f'<button type="button" class="news-filter{" is-active" if key == "all" else ""}" data-news-filter="{esc(key)}" '
    f'aria-pressed="{str(key == "all").lower()}" aria-controls="news-list">{esc(label)} <span>{count}</span></button>'
    for key, label, count in [('all', 'All news', len(posts))]
    + [(key, label, category_counts[key]) for key, label in news_categories.items() if category_counts[key]]
)


def pretty_date(iso):
    import datetime
    return datetime.date.fromisoformat(iso).strftime('%-d %B %Y')


def slug_of(name):
    import re
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def post_url(post):
    return f'news/{post["slug"]}.html'


blog_posts = '\n'.join(
    f'        <article class="blog-post" data-news-category="{esc(post["category"])}"><a class="blog-post-link" href="{esc(post_url(post))}">'
    + (f'<img src="{esc(post.get("thumbnail") or post["image"])}" alt="" width="1536" height="1024" loading="lazy" sizes="(max-width: 700px) calc(100vw - 40px), 320px" style="object-position: {esc(post.get("thumbnail_position", post.get("image_position", "55% 78%")))}">' if post.get('thumbnail') or post.get('image')
       else '<span class="blog-post-placeholder" aria-hidden="true"><img src="assets/ofel-mark.png" alt="" width="96" height="96"></span>')
    + f'<div><p class="eyebrow"><time datetime="{esc(post["date"])}">{esc(pretty_date(post["date"]))}</time></p>'
    f'<h2>{italicize(esc(post["title"]))}</h2><p>{italicize(esc(post.get("summary", "")))}</p>'
    f'<span class="news-category">{esc(news_categories[post["category"]])}</span></div></a></article>'
    for post in posts
) if posts else '<div class="directory-empty"><p>Lab updates will appear here.</p><a class="text-link" href="research/themes.html">' + icon('fish') + 'Explore our research</a></div>'


def post_page(post):
    """Article page for one news post."""
    NT = '<span class="sr-only"> (opens in a new tab)</span>'
    def block(item):
        if isinstance(item, str):
            return f'<p>{italicize(esc(item))}</p>'
        if 'heading' in item:
            return f'<h2>{esc(item["heading"])}</h2>'
        if 'details' in item:
            return '<dl class="news-event-details">' + ''.join(
                f'<div><dt>{esc(row["label"])}</dt><dd>{esc(row["value"])}</dd></div>'
                for row in item['details']) + '</dl>'
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
    image = (f'<figure class="news-figure"><img src="{esc(post["image"])}" alt="{esc(post.get("image_alt", ""))}" width="1536" height="1024" style="{image_style}">'
             + (f'<figcaption>{esc(post["image_caption"])}</figcaption>' if post.get('image_caption') else '')
             + '</figure>') if post.get('image') else ''
    return (
        '    <article class="section detail-page news-article" aria-labelledby="news-title">\n'
        '      <div class="container news-container">\n'
        f'        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="news/index.html">News</a><span aria-hidden="true">/</span>'
        f'<span aria-current="page"><time datetime="{esc(post["date"])}">{esc(pretty_date(post["date"]))}</time></span></nav>\n'
        f'        <h1 id="news-title">{italicize(esc(post["title"]))}</h1>\n'
        f'        <p class="news-summary">{italicize(esc(post.get("summary", "")))}</p>\n'
        f'        <a class="news-category news-category-link" href="news/index.html?category={esc(post["category"])}">{esc(news_categories[post["category"]])}</a>\n'
        + (f'        <p class="news-people">Lab members: {people_links}</p>\n' if people_links else '')
        + f'        {image}\n        <div class="news-body">{body}</div>\n'
        + (f'        {paper_html}\n' if paper_html else '')
        + (f'        {source_html}\n' if source_html else '')
        + '      </div>\n    </article>\n'
    )


# Homepage navigation cards combine cover images with short content previews.
_spec = importlib.util.spec_from_file_location('publications', ROOT / 'scripts/build-publications.py')
publications = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(publications)
pubs = publications.page_records()
papers_by_doi = {publications.paper_key(paper): paper for paper in pubs}
selected_dois = set()
for direction in directions:
    for doi in direction.get('publications', []):
        key = doi.lower()
        if key not in papers_by_doi:
            raise ValueError(f'Unknown selected publication for {direction["slug"]}: {doi}')
        if key in selected_dois:
            raise ValueError(f'Select each publication under only one research direction: {doi}')
        selected_dois.add(key)
lab_pubs = [p for p in pubs if publications.is_lab_paper(p)]
recent = lab_pubs or sorted(pubs, key=lambda p: (p['year'], p.get('date', '')), reverse=True)


def short(text, limit):
    return text if len(text) <= limit else text[:limit].rsplit(' ', 1)[0] + '…'


# Homepage News always follows publication/event dates; backfilled posts never override newer news.
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
    ('contact.html', 'Contact &amp; Join Us', 'Graduate study, research visits, and collaboration with Fan Zhang.', 'assets/contact/shou-campus-collaboration.png', '50% 50%', 'right',
     '<div class="mock-panel mock-paper" style="align-self: end"><span class="mock-label">Start a conversation</span>'
     '<strong>Research visits &amp; collaboration</strong><small>f-zhang@shou.edu.cn</small></div>'),
]
gateway_cards = '\n'.join(
    f'          <a class="gateway-card{" gateway-card-journal" if href == "publications.html" and latest_cover else ""}" href="{href + "#publications-all" if href == "publications.html" else href}" data-reveal style="--reveal-delay: {n * .1:.1f}s">'
    f'<img class="gateway-bg" src="{img}" alt="" width="1536" height="1024" loading="lazy" style="object-position: {pos}">'
    f'<div class="gateway-copy"><h3>{title}</h3><p>{desc}</p></div>'
    f'<div class="gateway-visual" aria-hidden="true">{visual}</div>'
    f'<span class="gateway-go" aria-hidden="true">{icon(ic)}</span></a>'
    for n, (href, title, desc, img, pos, ic, visual) in enumerate(gateways)
)

def reference_card(item, professional=False):
    kind = ' reference-card-featured' if professional else ''
    logo_kind = ' reference-logo-dark' if item.get('dark_logo') else ''
    heading = 'h3' if professional else 'h4'
    return (
        f'<a class="reference-card{kind}" href="{esc(item["url"])}" target="_blank" rel="noopener noreferrer">'
        f'<div class="reference-logo{logo_kind}"><img src="{esc(item["image"])}" alt="" loading="lazy"></div>'
        '<div class="reference-card-content">'
        f'<span class="reference-scope">{esc(item["scope"])}</span>'
        f'<{heading}>{esc(item["name"])}</{heading}>'
        f'<p class="reference-full-name">{esc(item["title"])}</p>'
        f'<p class="reference-description">{esc(item["description"])}</p>'
        f'<div class="reference-card-footer"><span>{esc(item["domain"])}</span>'
        f'<span class="reference-card-arrow" aria-hidden="true">{icon("right")}</span></div>'
        '<span class="sr-only"> (opens in a new tab)</span></div></a>'
    )


reference_materials = json.loads((ROOT / 'assets/reference-materials.json').read_text())

# A short, deliberately selected profile list; bibliographic details stay in the publication dataset.
faculty_dois = ['10.1111/faf.70077', '10.1111/1365-2664.70572', '10.1111/faf.12673']
faculty_papers = []
for doi in faculty_dois:
    paper = papers_by_doi[doi]
    if not publications.has_fan_zhang(paper):
        raise ValueError(f'Fan Zhang must be an author of profile selection: {doi}')
    if not (publications.has_lab_first_author(paper) or publications.is_author(paper['authors'][0], 'Fan', 'Zhang')):
        raise ValueError(f'Profile selection requires a lab first author or Fan Zhang as first author: {doi}')
    faculty_papers.append(
        f'<li><a class="faculty-paper" href="{esc(paper["source"])}" target="_blank" rel="noopener noreferrer">'
        f'<span class="faculty-paper-meta">{paper["year"]} · {esc(paper["journal"])}</span>'
        f'<h4>{italicize(esc(paper["title"]))}</h4><span class="faculty-paper-read">Read paper {icon("right")}</span>'
        '<span class="sr-only"> (opens in a new tab)</span></a></li>')
def build_embedded_weather():
    """Derive a dark-first frame from the standalone tool; keep one implementation."""
    folder = ROOT / 'demos/world-weather'
    markup = (folder / 'index.html').read_text()
    markup = markup.replace('<html lang="en">', '<html lang="en" data-embed="more" style="background:#081b2c;color-scheme:dark">')
    markup = markup.replace('<body>', '<body data-embed="more" data-map-src="../land.geojson" style="background:#081b2c">')
    def relative_asset(match):
        attr, value = match.groups()
        if not value or value.startswith(('#', '/', 'https:', 'http:', 'data:', 'mailto:')):
            return match.group(0)
        return f'{attr}="../{value}"'
    markup = re.sub(r'(?<![\w-])(href|src)="([^"]*)"', relative_asset, markup)
    destination = folder / 'embed/index.html'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(markup)
    digest = hashlib.sha256(markup.encode())
    for asset in ('weather.css', 'embed.js', 'model.js', 'app.js', 'land.geojson'):
        digest.update((folder / asset).read_bytes())
    return digest.hexdigest()[:10]


stats_pages = ([{'path': '/OFEL/' + clean_url(PAGE_PATHS[name]), 'title': 'Home' if name == 'index' else title.split(' | ')[0]}
                for name, (title, _, _) in PAGES.items()]
               + [{'path': '/OFEL/' + clean_url(post_url(post)), 'title': post['title']} for post in posts])
tokens = {
    '{{world_weather_version}}': build_embedded_weather(),
    '{{stats_pages}}': esc(json.dumps(stats_pages, ensure_ascii=False)),
    '{{faculty_selected_papers}}': '\n'.join(faculty_papers),
    '{{news_filters}}': news_filters,
    '{{news_count}}': str(len(posts)),
    '{{professional_links}}': '\n'.join(reference_card(item, True) for item in reference_materials['professional_links']),
    '{{international_organizations}}': '\n'.join(reference_card(item) for item in reference_materials['international_organizations']),
    '{{gateway_cards}}': gateway_cards,
    '{{blog_posts}}': blog_posts,
    '{{research_carousel}}': carousel,
    '{{research_primary}}': '\n'.join(direction_card(item) for item in core),
    '{{research_secondary}}': '\n'.join(direction_card(item) for item in directions if not item['primary']),
}
header = expand((TEMPLATES / 'header.html').read_text())
footer = expand((TEMPLATES / 'footer.html').read_text())
for name, (title, description, nav) in PAGES.items():
    head = render_head(title, description, BASE + clean_url(PAGE_PATHS[name]), asset_version(),
                       **({'image':'assets/people/fan-zhang.jpg','image_alt':'Fan Zhang at an outdoor venue','kind':'profile'}
                          if name=='fan-zhang' else {}))
    if name == 'more':
        extras = []
        for asset in ('assets/styles/more.css', 'assets/scripts/more-model.js', 'assets/scripts/more.js'):
            version = hashlib.sha256((ROOT / asset).read_bytes()).hexdigest()[:10]
            extras.append(f'  <link rel="stylesheet" href="{asset}?v={version}">' if asset.endswith('.css')
                          else f'  <script src="{asset}?v={version}" defer></script>')
        head = head.replace('</head>', '\n'.join(extras) + '\n</head>')
    content = expand((TEMPLATES / PAGE_PATHS[name]).read_text())
    for token, value in tokens.items():
        content = content.replace(token, value)
    write_page(PAGE_PATHS[name],
        head + f'<body id="top" data-page="{name}" data-nav-section="{nav}">\n'
        '  <a class="skip-link" href="#main">Skip to content</a>\n' + header
        + '\n  <main id="main">\n' + content + '  </main>\n\n' + footer + '</body>\n</html>\n'
    )

for post in posts:
    head = render_head(post['title'] + ' | OFEL News', post.get('summary', post['title']),
                       BASE + clean_url(post_url(post)), asset_version(), image=post.get('image'),
                       image_alt=post.get('image_alt') or ('Cover image for ' + post['title']), kind='article')
    write_page(post_url(post),
        head + '<body id="top" data-page="news-post" data-nav-section="news">\n'
        '  <a class="skip-link" href="#main">Skip to content</a>\n' + header
        + '\n  <main id="main">\n' + post_page(post) + '  </main>\n\n' + footer + '</body>\n</html>\n'
    )

for builder in ('build-people.py', 'build-publications.py'):
    subprocess.run([sys.executable, str(ROOT / 'scripts' / builder)], check=True)
print(f'Built {len(PAGES)} static pages and {len(posts)} news articles with shared navigation and footer.')

# Current HTML URLs get direct redirects; the 404 fallback handles older flat URLs.
print(f'Built {write_legacy_redirects()} legacy HTML redirects to clean directory URLs.')
write_page('404.html', (TEMPLATES / '404.html').read_text().replace('{{legacy_routes}}', json.dumps(legacy_routes(), ensure_ascii=True)))
write_sitemap()
print('Built sitemap.xml with canonical directory URLs.')
