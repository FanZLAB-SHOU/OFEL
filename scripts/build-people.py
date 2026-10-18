"""Build member cards, alumni tiles and one profile page per person from assets/people.json."""

import hashlib
import html
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'templates'
BASE = 'https://fanzhang-lab-shou.github.io/OFEL/'
RESERVED = {'index', 'research', 'fan-zhang', 'members', 'alumni', 'publications', 'blog', 'contact'}
data = json.loads((ROOT / 'assets/people.json').read_text())
groups = data['groups']
alumni = data.get('alumni', [])


def seniority(member):
    """Senior year first (from 'Year N' in the role), then alphabetical by name as written."""
    year = re.search(r'Year (\d+)', member.get('role', ''))
    return (-int(year.group(1)) if year else 0, member['name'].lower())


for group in groups:
    group['members'].sort(key=seniority)
for cohort in alumni:
    cohort['members'].sort(key=seniority)

import sys  # noqa: E402
sys.path.insert(0, str(ROOT / 'scripts'))
from icons import expand, icon  # noqa: E402
from site_paths import clean_url, output_path, rebase_links, write_page  # noqa: E402
from responsive_images import responsive_images  # noqa: E402
from page_metadata import render_head  # noqa: E402

spec = importlib.util.spec_from_file_location('publications', ROOT / 'scripts/build-publications.py')
publications = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publications)
for paper in publications.records:
    publications.validate(paper)
# Papers found per member that are not confirmed lab publications; shown on profiles only.
member_records = publications.member_records
known = {p['doi'].lower() for p in publications.records}
for paper in member_records:
    publications.validate(paper)
    if paper['doi'].lower() in known:
        raise ValueError(f'{paper["doi"]} is already in publications.json; remove it from member-publications.json')
all_records = publications.records + member_records

icons = {
    'website': icon('globe'),
    'researchgate': icon('researchgate'),
    'email': '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 6 8 7 8-7"/></svg>',
    'github': '<svg viewBox="0 0 24 24" aria-hidden="true" class="github-icon"><path d="M12 .8A11.2 11.2 0 0 0 8.46 22.63c.56.1.77-.24.77-.54v-2.08c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.68.08-.68 1.13.08 1.73 1.16 1.73 1.16 1 1.72 2.64 1.22 3.28.93.1-.73.4-1.22.71-1.5-2.5-.28-5.13-1.25-5.13-5.57 0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.43.11-2.98 0 0 .94-.3 3.08 1.15A10.76 10.76 0 0 1 12 6.13c.95 0 1.9.13 2.79.38 2.14-1.45 3.08-1.15 3.08-1.15.61 1.55.23 2.7.11 2.98.72.79 1.16 1.8 1.16 3.03 0 4.33-2.64 5.29-5.15 5.57.4.35.76 1.03.76 2.08v3.07c0 .3.2.65.77.54A11.2 11.2 0 0 0 12 .8Z"/></svg>',
}
placeholder = ('<div class="member-photo-placeholder" aria-hidden="true"><svg viewBox="0 0 80 100">'
               '<circle cx="40" cy="34" r="14"/><path d="M15 88V78c0-15 11-24 25-24s25 9 25 24v10"/></svg></div>')


def esc(value):
    return html.escape(value, quote=True)


def asset_version():
    """Short content hash of the stylesheet and script, appended to their URLs to bust browser caches."""
    digest = hashlib.sha256((ROOT / 'styles.css').read_bytes() + (ROOT / 'script.js').read_bytes())
    return digest.hexdigest()[:10]


def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def checked_email(member):
    value = member['email']
    if any(c in value for c in '\r\n') or '@' not in value:
        raise ValueError(f'Invalid email for {member["name"]}')
    return value


def checked_github(member):
    parsed = urlparse(member['github'])
    if parsed.scheme != 'https' or parsed.netloc != 'github.com':
        raise ValueError(f'Invalid GitHub URL for {member["name"]}')
    return member['github']


def checked_website(member):
    parsed = urlparse(member['website'])
    if parsed.scheme != 'https' or not parsed.netloc:
        raise ValueError(f'Invalid website URL for {member["name"]}')
    return member['website']


def checked_researchgate(member):
    parsed = urlparse(member['researchgate'])
    if parsed.scheme != 'https' or parsed.netloc not in {'www.researchgate.net', 'researchgate.net'}:
        raise ValueError(f'Invalid ResearchGate URL for {member["name"]}')
    return member['researchgate']


def contact(member, kind):
    name = esc(member['name'])
    label = {'email': 'Email', 'github': 'GitHub', 'website': 'Website', 'researchgate': 'ResearchGate'}[kind]
    if not member.get(kind):
        return (f'<span class="member-link is-placeholder" role="img" '
                f'aria-label="{label} not yet listed for {name}" title="{label} not yet listed">{icons[kind]}</span>')
    if kind == 'email':
        value = checked_email(member)
        href, description, extra = 'mailto:' + value, f'Email {member["name"]}: {value}', ''
    elif kind == 'website':
        value = href = checked_website(member)
        description = f'{member["name"]}: {member.get("website_label", "Website")} (opens in a new tab)'
        extra = ' target="_blank" rel="noopener noreferrer"'
    elif kind == 'researchgate':
        value = href = checked_researchgate(member)
        description = f'{member["name"]} on ResearchGate (opens in a new tab)'
        extra = ' target="_blank" rel="noopener noreferrer"'
    else:
        value = href = checked_github(member)
        description = f'{member["name"]} on GitHub (opens in a new tab)'
        extra = ' target="_blank" rel="noopener noreferrer"'
    mark = icon(member.get('website_icon', 'globe')) if kind == 'website' else icons[kind]
    return (f'<a class="member-link" href="{esc(href)}"{extra} '
            f'aria-label="{esc(description)}" title="{esc(value)}">{mark}</a>')


def photo(member, cls, width, height, priority=False):
    if not member.get('photo'):
        return placeholder
    styles = []
    if cls == 'profile-img' and member.get('profile_photo_aspect_ratio'):
        styles.append(f'aspect-ratio: {esc(member["profile_photo_aspect_ratio"])}')
    if member.get('photo_position'):
        styles.append(f'object-position: {esc(member["photo_position"])}')
    style = f' style="{"; ".join(styles)}"' if styles else ''
    loading = ('fetchpriority="high" sizes="(max-width: 760px) calc(100vw - 40px), '
               '(max-width: 1280px) 46vw, 620px"') if priority else 'loading="lazy"'
    return (f'<img class="{cls}" src="{esc(member["photo"])}" alt="{esc(member.get("photo_alt", member["name"]))}" '
            f'width="{width}" height="{height}" {loading}{style}>')


def fill(page, marker, sections):
    source = page.read_text()
    start_marker = f'          <!-- {marker}:start -->'
    end_marker = f'          <!-- {marker}:end -->'
    start = source.index(start_marker) + len(start_marker)
    end = source.index(end_marker, start)
    page.write_text(source[:start] + '\n' + rebase_links(responsive_images('\n'.join(sections)), page.relative_to(ROOT).as_posix()) + '\n' + source[end:])


# One ordered list of everyone: current members by group, then alumni by graduation year.
people = []
for group in groups:
    for member in group['members']:
        people.append({**member, 'context': group['heading'], 'back': ('members/index.html', 'Current Members')})
for cohort in alumni:
    label = f'{cohort["year"]} {cohort["degree"]} Graduate'
    for member in cohort['members']:
        if member.get('profile_ref'):
            continue  # Graduates still in the lab keep their existing current-member profile.
        people.append({**member, 'role': label, 'context': 'Alumni', 'back': ('members/alumni.html', 'Alumni')})
for person in people:
    person['slug'] = slugify(person['name'])
slugs = [p['slug'] for p in people]
clash = RESERVED.intersection(slugs) or {s for s in slugs if slugs.count(s) > 1}
if clash:
    raise ValueError(f'Profile page names clash with existing pages or each other: {sorted(clash)}')
by_name = {p['name']: p for p in people}

# Members page: cards whose photo and name open the profile page.
sections = []
for group in groups:
    cards = []
    for member in group['members']:
        name, href = esc(member['name']), esc('members/' + by_name[member['name']]['slug'] + '.html')
        web_kinds = [kind for kind in ('github', 'website', 'researchgate') if member.get(kind)]
        contact_links = contact(member, 'email') + ''.join(contact(member, kind) for kind in web_kinds)
        email = f'<p class="member-email">{esc(member["email"])}</p>' if member.get('email') else ''
        cards.append(
            f'                  <article class="member-card"><a class="member-photo-link" href="{href}" tabindex="-1" aria-hidden="true">'
            f'{photo(member, "member-photo", 108, 144)}</a><div class="member-details">'
            f'<h3><a href="{href}">{name}</a></h3><p class="member-role">{esc(member["role"])}</p>{email}'
            f'<div class="member-links" role="group" aria-label="Contact {name}">'
            f'{contact_links}</div></div></article>'
        )
    group_id = esc(group['id'])
    sections.append(
        f'            <section class="member-group" aria-labelledby="{group_id}-title">\n'
        f'              <h2 id="{group_id}-title">{esc(group["heading"])}</h2>\n'
        f'              <div class="member-cards">\n' + '\n'.join(cards) + '\n              </div>\n            </section>'
    )
fill(ROOT / output_path('members/index.html'), 'member-groups', sections)

# Alumni page: square photo tiles with the name over the photo, grouped by graduation year.
sections = []
for cohort in alumni:
    tiles = []
    for member in cohort['members']:
        reference = member.get('profile_ref', member['name'])
        if reference not in by_name:
            raise ValueError(f'Unknown alumni profile reference: {reference}')
        linked_person = by_name[reference]
        display = {**linked_person, **member}
        tiles.append(
            f'                <li><a class="alumni-tile" href="members/{esc(linked_person["slug"])}.html">'
            f'{photo(display, "alumni-photo", 400, 400)}<span class="alumni-name">{esc(member["name"])}</span></a></li>'
        )
    year = cohort['year']
    cohort_id = f'alumni-{year}-{slugify(cohort["degree"])}'
    sections.append(
        f'            <section class="member-group" aria-labelledby="{cohort_id}-title">\n'
        f'              <h2 id="{cohort_id}-title">{year} {esc(cohort["degree"])} Graduates</h2>\n'
        f'              <ul class="alumni-grid">\n' + '\n'.join(tiles) + '\n              </ul>\n            </section>'
    )
fill(ROOT / output_path('members/alumni.html'), 'alumni-groups', sections)

# Profile pages: name, role, contact, bio, publications, then previous/next person.
header = expand((TEMPLATES / 'header.html').read_text())
footer = expand((TEMPLATES / 'footer.html').read_text())
for n, person in enumerate(people):
    name = esc(person['name'])
    given, family = person['name'].split()[0], person['name'].split()[-1]
    papers = sorted((p for p in all_records if any(publications.is_author(a, given, family) for a in p['authors'])),
                    key=lambda p: p['year'], reverse=True)
    paper_list = ('<div class="publication-list profile-publication-list">\n'
                  + '\n'.join(publications.article_html(p, highlight=(given, family)) for p in papers)
                  + '\n        </div>') if papers else '<p class="profile-empty">No publications listed yet.</p>'
    links = []
    if person.get('email'):
        value = checked_email(person)
        links.append(f'<a class="text-link" href="mailto:{esc(value)}">{icon("mail")}{esc(value)}</a>')
    if person.get('github'):
        links.append(f'<a class="text-link" href="{esc(checked_github(person))}" target="_blank" rel="noopener noreferrer">' + icon('github') + 'GitHub'
                     '<span class="sr-only"> (opens in a new tab)</span></a>')
    if person.get('website'):
        links.append(f'<a class="text-link" href="{esc(checked_website(person))}" target="_blank" rel="noopener noreferrer">'
                     + icon(person.get('website_icon', 'globe')) + esc(person.get('website_label', 'Website'))
                     + '<span class="sr-only"> (opens in a new tab)</span></a>')
    if person.get('researchgate'):
        links.append(f'<a class="text-link" href="{esc(checked_researchgate(person))}" target="_blank" rel="noopener noreferrer">'
                     + icon('researchgate') + 'ResearchGate'
                     + '<span class="sr-only"> (opens in a new tab)</span></a>')
    links_html = f'<div class="pi-links">{"".join(links)}</div>' if links else ''
    bio = ''.join(f'<p>{esc(par)}</p>' for par in person['bio'].split('\n\n')) if person.get('bio') else \
        '<p class="profile-empty">Profile coming soon.</p>'
    if person.get('bio_zh'):
        original = ''.join(f'<p>{esc(par)}</p>' for par in person['bio_zh'].split('\n\n'))
        bio += ('<details class="profile-bio-original"><summary>中文原文 / Original Chinese</summary>'
                f'<div lang="zh-CN">{original}</div></details>')
    pager = []
    if n > 0:
        prev = people[n - 1]
        pager.append(f'<a class="profile-prev" rel="prev" href="members/{esc(prev["slug"])}.html">'
                     f'<span class="pager-badge" aria-hidden="true">OFEL</span><span class="pager-text">'
                     f'<span class="pager-dir">{icon("left")}Previous</span><span class="pager-name">{esc(prev["name"])}</span></span></a>')
    if n < len(people) - 1:
        nxt = people[n + 1]
        pager.append(f'<a class="profile-next" rel="next" href="members/{esc(nxt["slug"])}.html"><span class="pager-text">'
                     f'<span class="pager-dir">Next{icon("right")}</span><span class="pager-name">{esc(nxt["name"])}</span></span>'
                     f'<span class="pager-badge" aria-hidden="true">OFEL</span></a>')
    back_href, back_label = person['back']
    breadcrumb = (f'<nav class="breadcrumb" aria-label="Breadcrumb"><a href="{back_href}">{back_label}</a>'
                  f'<span aria-hidden="true">/</span><span aria-current="page">{name}</span></nav>')
    # Only current members with supplied photos get the large introduction.
    # Keep the full existing profile below it, including bilingual bios and papers.
    has_intro = bool(person.get('photo')) and back_href == 'members/index.html'
    intro = ''
    if has_intro:
        first_paragraph = (person.get('bio') or '').split('\n\n')[0]
        summary = f'<p class="member-intro-summary">{esc(first_paragraph)}</p>' if first_paragraph else ''
        intro = (
            '    <section class="member-intro" aria-labelledby="profile-title"><div class="container">'
            f'{breadcrumb}<div class="member-intro-card">'
            f'<img class="member-intro-wash" src="{esc(person["photo"])}" alt="" aria-hidden="true" '
            'width="640" height="800" sizes="640px" fetchpriority="low">'
            f'<div class="member-intro-portrait">{photo(person, "member-intro-photo", 720, 900, priority=True)}</div>'
            f'<div class="member-intro-glass"><p class="member-intro-context">{esc(person["context"])}</p>'
            '<div class="member-intro-copy">'
            f'<h1 id="profile-title">{name}</h1><p class="member-intro-role">{esc(person["role"])}</p>'
            f'{summary}{links_html}'
            f'<a class="member-intro-more" href="#member-details">Full profile{icon("down")}</a>'
            '</div></div></div></div></section>\n'
        )
    details_id = 'member-details' if has_intro else 'profile-title'
    heading = (f'<h2 class="member-details-heading" id="member-details">{name}</h2>' if has_intro
               else f'<h1 id="profile-title">{name}</h1>')
    breadcrumb_html = '' if has_intro else f'        {breadcrumb}\n'
    content = (
        intro + f'    <section class="people section detail-page profile-page" aria-labelledby="{details_id}">\n'
        f'      <div class="container">\n'
        f'{breadcrumb_html}'
        f'        <div class="profile-grid">\n'
        f'          <div class="profile-photo">{photo(person, "profile-img", 600, 800)}</div>\n'
        f'          <div class="profile-content"><p class="eyebrow teal">{esc(person["context"])}</p>'
        f'{heading}<p class="pi-role">{esc(person["role"])}</p>{links_html}'
        f'<div class="profile-bio">{bio}</div></div>\n'
        f'        </div>\n'
        f'        <section class="profile-publications" aria-labelledby="profile-publications-title">'
        f'<h2 id="profile-publications-title">Publications</h2>\n        {paper_list}\n        </section>\n'
        f'        <nav class="profile-pager" aria-label="Browse people">{"".join(pager)}</nav>\n'
        f'      </div>\n    </section>\n'
    )
    title = f'{person["name"]} | OFEL'
    description = f'{person["name"]}, {person["role"]} at the Oceanic Fisheries Ecosystem Laboratory, Shanghai Ocean University.'
    head = render_head(title, description, BASE + clean_url('members/' + person['slug'] + '.html'), asset_version(),
                       image=person.get('photo'), image_alt=person.get('photo_alt') or (person['name'] + ' profile photo' if person.get('photo') else None), kind='profile')
    write_page(f'members/{person["slug"]}.html',
        head + '<body id="top" data-page="profile" data-nav-section="people">\n'
        '  <a class="skip-link" href="#main">Skip to content</a>\n' + header
        + '\n  <main id="main">\n' + content + '  </main>\n\n' + footer + '</body>\n</html>\n'
    )

current = sum(len(g['members']) for g in groups)
alumni_tiles = sum(len(cohort['members']) for cohort in alumni)
print(f'Built {current} member cards, {alumni_tiles} alumni tiles and {len(people)} profile pages.')
