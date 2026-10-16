"""Build the static publication list and BibTeX from verified local metadata."""

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'assets/publications.json').read_text())['publications']
articles = []
bib = []
for paper in records:
    authors = []
    for author in paper['authors']:
        name = html.escape(f"{author['given']} {author['family']}")
        if author['given'] == 'Fan' and author['family'] == 'Zhang':
            name = f'<strong>{name}</strong>'
        authors.append(name)
    details = paper['volume']
    if paper['issue']:
        details += f"({paper['issue']})"
    location = paper['article_number'] or paper['pages']
    if location:
        details += (', ' if details else '') + location.replace('-', '–')
    if not details:
        details = 'Published online'
    doi_url = html.escape(paper['source'], quote=True)
    title = html.escape(paper['title'])
    articles.append(
        f'          <article class="publication" data-topics="{" ".join(paper["topics"])}">'
        f'<span class="publication-year">{paper["year"]}</span><div>'
        f'<p class="journal">{html.escape(paper["journal"])} <span>{html.escape(details)}</span></p>'
        f'<h3><a href="{doi_url}" target="_blank" rel="noopener noreferrer">{title}'
        '<span class="sr-only"> (opens in a new tab)</span></a></h3>'
        f'<p class="authors">{", ".join(authors)}</p></div>'
        f'<a class="paper-arrow" href="{doi_url}" target="_blank" rel="noopener noreferrer" '
        f'aria-label="Read {title} in a new tab">↗</a></article>'
    )
    key = re.sub('[^a-zA-Z0-9]', '', paper['authors'][0]['family']).lower()
    key += str(paper['year']) + re.sub('[^a-zA-Z0-9]', '', paper['doi'].split('/')[-1])
    fields = {
        'author': ' and '.join(f"{a['family']}, {a['given']}" for a in paper['authors']),
        'title': '{' + paper['title'] + '}',
        'journal': paper['journal'],
        'year': str(paper['year']),
        'volume': paper['volume'],
        'number': paper['issue'],
        'pages': (paper['article_number'] or paper['pages']).replace('-', '--'),
        'doi': paper['doi'],
    }
    # Escape the journal ampersand for BibTeX/LaTeX consumers.
    body = ',\n'.join(f'  {k} = {{{v.replace(chr(38), chr(92) + chr(38))}}}' for k, v in fields.items() if v)
    bib.append(f'@article{{{key},\n{body}\n}}')

page = ROOT / 'index.html'
source = page.read_text()
start_marker = '        <div class="publication-list" id="publication-list">'
start = source.index(start_marker) + len(start_marker)
end = source.index('\n        </div>', start)
source = source[:start] + '\n' + '\n'.join(articles) + source[end:]
source = re.sub(r'(<span class="publication-count"[^>]*>).*?(</span>)',
                rf'\g<1>{len(records)} publications\g<2>', source)
page.write_text(source)
(ROOT / 'assets/selected-publications.bib').write_text('\n\n'.join(bib) + '\n')
print(f'Built {len(records)} publications and matching BibTeX entries.')
