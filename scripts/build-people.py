"""Build member cards from user-supplied names, roles and contact details."""

import html
import json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
groups = json.loads((ROOT / 'assets/people.json').read_text())['groups']
icons = {
    'email': '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 6 8 7 8-7"/></svg>',
    'github': '<svg viewBox="0 0 24 24" aria-hidden="true" class="github-icon"><path d="M12 .8A11.2 11.2 0 0 0 8.46 22.63c.56.1.77-.24.77-.54v-2.08c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.65-1.25-1.65-1.02-.7.08-.68.08-.68 1.13.08 1.73 1.16 1.73 1.16 1 1.72 2.64 1.22 3.28.93.1-.73.4-1.22.71-1.5-2.5-.28-5.13-1.25-5.13-5.57 0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.43.11-2.98 0 0 .94-.3 3.08 1.15A10.76 10.76 0 0 1 12 6.13c.95 0 1.9.13 2.79.38 2.14-1.45 3.08-1.15 3.08-1.15.61 1.55.23 2.7.11 2.98.72.79 1.16 1.8 1.16 3.03 0 4.33-2.64 5.29-5.15 5.57.4.35.76 1.03.76 2.08v3.07c0 .3.2.65.77.54A11.2 11.2 0 0 0 12 .8Z"/></svg>',
}


def contact(member, kind):
    name = html.escape(member['name'], quote=True)
    value = member.get(kind)
    label = 'Email' if kind == 'email' else 'GitHub'
    if not value:
        return (f'<span class="member-link is-placeholder" role="img" '
                f'aria-label="{label} not yet listed for {name}" title="{label} not yet listed">{icons[kind]}</span>')
    if kind == 'email':
        if any(c in value for c in '\r\n') or '@' not in value:
            raise ValueError(f'Invalid email for {member["name"]}')
        href = 'mailto:' + value
        description = f'Email {member["name"]}: {value}'
        extra = ''
    else:
        parsed = urlparse(value)
        if parsed.scheme != 'https' or parsed.netloc != 'github.com':
            raise ValueError(f'Invalid GitHub URL for {member["name"]}')
        href = value
        description = f'{member["name"]} on GitHub (opens in a new tab)'
        extra = ' target="_blank" rel="noopener noreferrer"'
    return (f'<a class="member-link" href="{html.escape(href, quote=True)}"{extra} '
            f'aria-label="{html.escape(description, quote=True)}" title="{html.escape(value, quote=True)}">{icons[kind]}</a>')


sections = []
for group in groups:
    cards = []
    for member in group['members']:
        name = html.escape(member['name'])
        if member.get('photo'):
            avatar = f'<img class="member-photo" src="{html.escape(member["photo"], quote=True)}" alt="{name}" width="108" height="144" loading="lazy">'
        else:
            avatar = '<div class="member-photo-placeholder" aria-hidden="true"><svg viewBox="0 0 80 100"><circle cx="40" cy="34" r="14"/><path d="M15 88V78c0-15 11-24 25-24s25 9 25 24v10"/></svg></div>'
        email = f'<p class="member-email">{html.escape(member["email"])}</p>' if member.get('email') else ''
        cards.append(
            f'                  <article class="member-card">{avatar}<div class="member-details">'
            f'<h3>{name}</h3><p class="member-role">{html.escape(member["role"])}</p>{email}'
            f'<div class="member-links" role="group" aria-label="Contact {name}">'
            f'{contact(member, "email")}{contact(member, "github")}</div></div></article>'
        )
    group_id = html.escape(group['id'], quote=True)
    sections.append(
        f'            <section class="member-group" aria-labelledby="{group_id}-title">\n'
        f'              <h2 id="{group_id}-title">{html.escape(group["heading"])}</h2>\n'
        f'              <div class="member-cards">\n' + '\n'.join(cards) + '\n              </div>\n            </section>'
    )

page = ROOT / 'members.html'
source = page.read_text()
start_marker = '          <!-- member-groups:start -->'
end_marker = '          <!-- member-groups:end -->'
start = source.index(start_marker) + len(start_marker)
end = source.index(end_marker, start)
page.write_text(source[:start] + '\n' + '\n'.join(sections) + '\n' + source[end:])
print(f'Built {sum(len(group["members"]) for group in groups)} member cards in {len(groups)} role groups.')
