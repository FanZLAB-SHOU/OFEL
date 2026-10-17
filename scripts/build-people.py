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


def contact(member, kind):
    name = esc(member['name'])
    label = 'Email' if kind == 'email' else 'GitHub'
    if not member.get(kind):
        return (f'<span class="member-link is-placeholder" role="img" '
                f'aria-label="{label} not yet listed for {name}" title="{label} not yet listed">{icons[kind]}</span>')
    if kind == 'email':
        value = checked_email(member)
        href, description, extra = 'mailto:' + value, f'Email {member["name"]}: {value}', ''
    else:
        value = href = checked_github(member)
        description = f'{member["name"]} on GitHub (opens in a new tab)'
        extra = ' target="_blank" rel="noopener noreferrer"'
    return (f'<a class="member-link" href="{esc(href)}"{extra} '
            f'aria-label="{esc(description)}" title="{esc(value)}">{icons[kind]}</a>')


def photo(member, cls, width, height):
    if not member.get('photo'):
        return placeholder
    return (f'<img class="{cls}" src="{esc(member["photo"])}" alt="{esc(member["name"])}" '
            f'width="{width}" height="{height}" loading="lazy">')


def fill(page, marker, sections):
    source = page.read_text()
    start_marker = f'          <!-- {marker}:start -->'
    end_marker = f'          <!-- {marker}:end -->'
    start = source.index(start_marker) + len(start_marker)
    end = source.index(end_marker, start)
    page.write_text(source[:start] + '\n' + '\n'.join(sections) + '\n' + source[end:])


# One ordered list of everyone: current members by group, then alumni by graduation year.
people = []
for group in groups:
    for member in group['members']:
        people.append({**member, 'context': group['heading'], 'back': ('members.html', 'Current Members')})
for cohort in alumni:
    label = f'{cohort["year"]} {cohort["degree"]} Graduate'
    for member in cohort['members']:
        people.append({**member, 'role': label, 'context': 'Alumni', 'back': ('alumni.html', 'Alumni')})
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
        name, href = esc(member['name']), esc(by_name[member['name']]['slug'] + '.html')
        email = f'<p class="member-email">{esc(member["email"])}</p>' if member.get('email') else ''
        cards.append(
            f'                  <article class="member-card"><a class="member-photo-link" href="{href}" tabindex="-1" aria-hidden="true">'
            f'{photo(member, "member-photo", 108, 144)}</a><div class="member-details">'
            f'<h3><a href="{href}">{name}</a></h3><p class="member-role">{esc(member["role"])}</p>{email}'
            f'<div class="member-links" role="group" aria-label="Contact {name}">'
            f'{contact(member, "email")}{contact(member, "github")}</div></div></article>'
        )
    group_id = esc(group['id'])
    sections.append(
        f'            <section class="member-group" aria-labelledby="{group_id}-title">\n'
        f'              <h2 id="{group_id}-title">{esc(group["heading"])}</h2>\n'
        f'              <div class="member-cards">\n' + '\n'.join(cards) + '\n              </div>\n            </section>'
    )
fill(ROOT / 'members.html', 'member-groups', sections)

# Alumni page: square photo tiles with the name over the photo, grouped by graduation year.
sections = []
for cohort in alumni:
    tiles = []
    for member in cohort['members']:
        tiles.append(
            f'                <li><a class="alumni-tile" href="{esc(by_name[member["name"]]["slug"])}.html">'
            f'{photo(member, "alumni-photo", 400, 400)}<span class="alumni-name">{esc(member["name"])}</span></a></li>'
        )
    year = cohort['year']
    sections.append(
        f'            <section class="member-group" aria-labelledby="alumni-{year}-title">\n'
        f'              <h2 id="alumni-{year}-title">{year} {esc(cohort["degree"])} Graduates</h2>\n'
        f'              <ul class="alumni-grid">\n' + '\n'.join(tiles) + '\n              </ul>\n            </section>'
    )
fill(ROOT / 'alumni.html', 'alumni-groups', sections)

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
    links_html = f'<div class="pi-links">{"".join(links)}</div>' if links else ''
    bio = ''.join(f'<p>{esc(par)}</p>' for par in person['bio'].split('\n\n')) if person.get('bio') else \
        '<p class="profile-empty">Profile coming soon.</p>'
    pager = []
    if n > 0:
        prev = people[n - 1]
        pager.append(f'<a class="profile-prev" rel="prev" href="{esc(prev["slug"])}.html">'
                     f'<span class="pager-badge" aria-hidden="true">OFEL</span><span class="pager-text">'
                     f'<span class="pager-dir">{icon("left")}Previous</span><span class="pager-name">{esc(prev["name"])}</span></span></a>')
    if n < len(people) - 1:
        nxt = people[n + 1]
        pager.append(f'<a class="profile-next" rel="next" href="{esc(nxt["slug"])}.html"><span class="pager-text">'
                     f'<span class="pager-dir">Next{icon("right")}</span><span class="pager-name">{esc(nxt["name"])}</span></span>'
                     f'<span class="pager-badge" aria-hidden="true">OFEL</span></a>')
    back_href, back_label = person['back']
    content = (
        f'    <section class="people section detail-page profile-page" aria-labelledby="profile-title">\n'
        f'      <div class="container">\n'
        f'        <nav class="breadcrumb" aria-label="Breadcrumb"><a href="{back_href}">{back_label}</a>'
        f'<span aria-hidden="true">/</span><span aria-current="page">{name}</span></nav>\n'
        f'        <div class="profile-grid">\n'
        f'          <div class="profile-photo">{photo(person, "profile-img", 600, 800)}</div>\n'
        f'          <div class="profile-content"><p class="eyebrow teal">{esc(person["context"])}</p>'
        f'<h1 id="profile-title">{name}</h1><p class="pi-role">{esc(person["role"])}</p>{links_html}'
        f'<div class="profile-bio">{bio}</div></div>\n'
        f'        </div>\n'
        f'        <section class="profile-publications" aria-labelledby="profile-publications-title">'
        f'<h2 id="profile-publications-title">Publications</h2>\n        {paper_list}\n        </section>\n'
        f'        <nav class="profile-pager" aria-label="Browse people">{"".join(pager)}</nav>\n'
        f'      </div>\n    </section>\n'
    )
    title = f'{person["name"]} | OFEL'
    description = f'{person["name"]}, {person["role"]} at the Oceanic Fisheries Ecosystem Laboratory, Shanghai Ocean University.'
    head = (TEMPLATES / 'head.html').read_text().replace('{{asset_version}}', asset_version())
    for token, value in {'{{title}}': title, '{{description}}': description, '{{canonical}}': BASE + person['slug'] + '.html'}.items():
        head = head.replace(token, esc(value))
    (ROOT / f'{person["slug"]}.html').write_text(
        head + '<body id="top" data-page="profile" data-nav-section="people">\n'
        '  <a class="skip-link" href="#main">Skip to content</a>\n' + header
        + '\n  <main id="main">\n' + content + '  </main>\n\n' + footer + '</body>\n</html>\n'
    )

current = sum(len(g['members']) for g in groups)
print(f'Built {current} member cards, {len(people) - current} alumni tiles and {len(people)} profile pages.')
