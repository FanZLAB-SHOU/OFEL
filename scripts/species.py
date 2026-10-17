"""Scientific (Latin) names that must be set in italics wherever they appear on the site.

Add new species here (genus and species, as written in titles). Full names and the
abbreviated form (e.g. "D. gigas") are both italicized.
"""

import re

SPECIES = [
    'Diaphus watasei',
    'Dosidicus gigas',
    'Euphausia superba',
    'Sthenoteuthis oualaniensis',
    'Thunnus alalunga',
    'Trichiurus japonicus',
]


def _pattern():
    names = []
    for name in SPECIES:
        genus, epithet = name.split()
        names += [re.escape(name), re.escape(f'{genus[0]}. {epithet}')]
    return re.compile(r'(?<![\w>])(' + '|'.join(sorted(names, key=len, reverse=True)) + r')(?![\w<])')


PATTERN = _pattern()


def italicize(escaped_html):
    """Wrap species names in <em> in text that has already been HTML-escaped."""
    return PATTERN.sub(r'<em>\1</em>', escaped_html)


def italicize_bibtex(text):
    return PATTERN.sub(r'\\textit{\1}', text)
