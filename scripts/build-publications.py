"""Build the static publication list and BibTeX from verified local metadata."""

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
records = json.loads((ROOT / 'assets/publications.json').read_text())['publications']
articles = []
bib = []
lab_bib = []
relationship_labels = {
    'external_collaboration': 'External collaboration',
    'external_supervision': 'Supervised research · external student',
    'prior_work': 'Earlier work',
}
for paper in records:
    topics = paper.get('topics')
    if not isinstance(topics, list) or len(topics) != 1 or topics[0] not in {'assessment', 'ecosystems', 'vessels', 'biology'}:
        raise ValueError(f'Each publication needs exactly one primary topic: {paper["doi"]}')
    attribution = paper.get('attribution', {})
    if attribution.get('lab_publication') is not None and type(attribution['lab_publication']) is not bool:
        raise ValueError(f'Invalid lab attribution for {paper["doi"]}')
    relationships = attribution.get('relationships', [])
    if not isinstance(relationships, list) or any(r not in relationship_labels for r in relationships):
        raise ValueError(f'Invalid research relationship for {paper["doi"]}')
    if (attribution.get('lab_publication') is not None or relationships) and not attribution.get('confirmed_by'):
        raise ValueError(f'Attribution needs a confirmation source for {paper["doi"]}')
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
    attribution = paper.get('attribution', {})
    is_lab = attribution.get('lab_publication') is True
    is_fan_zhang = any(a['given'] == 'Fan' and a['family'] == 'Zhang' for a in paper['authors'])
    badges = ['Lab research'] if is_lab else []
    badges += [relationship_labels[r] for r in attribution.get('relationships', [])]
    badges_html = ('<p class="publication-attribution">' + ''.join(
        f'<span>{html.escape(label)}</span>' for label in badges) + '</p>') if badges else ''
    articles.append(
        f'          <article class="publication" data-topic="{paper["topics"][0]}" '
        f'data-fan-zhang="{str(is_fan_zhang).lower()}" data-lab="{str(is_lab).lower()}">'
        f'<span class="publication-year">{paper["year"]}</span><div>'
        f'<p class="journal">{html.escape(paper["journal"])} <span>{html.escape(details)}</span></p>'
        f'<h3><a href="{doi_url}" target="_blank" rel="noopener noreferrer">{title}'
        '<span class="sr-only"> (opens in a new tab)</span></a></h3>'
        f'<p class="authors">{", ".join(authors)}</p>{badges_html}</div>'
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
    citation = f'@article{{{key},\n{body}\n}}'
    if is_fan_zhang:
        bib.append(citation)
    if is_lab:
        lab_bib.append(citation)

page = ROOT / 'publications.html'
source = page.read_text()
start_marker = '        <div class="publication-list" id="publication-list">'
start = source.index(start_marker) + len(start_marker)
end = source.index('\n        </div>', start)
source = source[:start] + '\n' + '\n'.join(articles) + source[end:]
source = re.sub(r'(<span class="publication-count"[^>]*>).*?(</span>)',
                rf'\g<1>{len(records)} publications\g<2>', source)
page.write_text(source)
(ROOT / 'assets/selected-publications.bib').write_text('\n\n'.join(bib) + '\n')
(ROOT / 'assets/lab-publications.bib').write_text('\n\n'.join(lab_bib) + ('\n' if lab_bib else ''))
print(f'Built {len(records)} publications and matching BibTeX entries.')
