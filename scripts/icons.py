"""Inline SVG line icons used in place of arrow glyphs; templates reference them as {{icon:name}}."""

import re

PATHS = {
    'mail': '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    'globe': '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    'researchgate': ('<g fill="currentColor" stroke="none"><text x="1" y="21" font-family="Georgia, serif" '
                     'font-size="21" font-weight="700">R</text><text x="14" y="9" font-family="Georgia, serif" '
                     'font-size="10" font-weight="700">G</text></g>'),
    'paper': ('<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
              '<path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>'),
    'id': ('<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="8" cy="11" r="2"/><path d="M5 16a3.5 3.5 0 0 1 6 0"/>'
           '<path d="M14 10h4"/><path d="M14 14h4"/>'),
    'people': ('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>'
               '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'),
    'book': '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    'school': ('<path d="M21.42 10.92a1 1 0 0 0-.02-1.84L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.83l8.57 3.91a2 2 0 0 0 1.66 0z"/>'
               '<path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>'),
    'left': '<path d="m15 18-6-6 6-6"/>',
    'right': '<path d="m9 18 6-6-6-6"/>',
    'down': '<path d="m6 9 6 6 6-6"/>',
    'top': '<circle cx="12" cy="12" r="10"/><path d="m8 14 4-4 4 4"/>',
    'fish': ('<path d="M6.5 12c.94-3.46 4.94-6 8.5-6 3.56 0 6.06 2.54 7 6-.94 3.47-3.44 6-7 6s-7.56-2.53-8.5-6Z"/>'
             '<path d="M18 12v.5"/><path d="M16 17.93a9.77 9.77 0 0 1 0-11.86"/>'
             '<path d="M7 10.67C7 8 5.58 5.97 2.73 5.5c-1 1.5-1 5 .23 6.5-1.24 1.5-1.24 5-.23 6.5C5.58 18.03 7 16 7 13.33"/>'),
}
GITHUB = ('<path d="M12 .8A11.2 11.2 0 0 0 8.46 22.63c.56.1.77-.24.77-.54v-2.08c-3.13.68-3.79-1.33-3.79-1.33-.51-1.3-1.25-1.65-1.25-1.65'
          '-1.02-.7.08-.68.08-.68 1.13.08 1.73 1.16 1.73 1.16 1 1.72 2.64 1.22 3.28.93.1-.73.4-1.22.71-1.5-2.5-.28-5.13-1.25-5.13-5.57 '
          '0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.43.11-2.98 0 0 .94-.3 3.08 1.15A10.76 10.76 0 0 1 12 6.13c.95 0 1.9.13 2.79.38 '
          '2.14-1.45 3.08-1.15 3.08-1.15.61 1.55.23 2.7.11 2.98.72.79 1.16 1.8 1.16 3.03 0 4.33-2.64 5.29-5.15 5.57.4.35.76 1.03.76 '
          '2.08v3.07c0 .3.2.65.77.54A11.2 11.2 0 0 0 12 .8Z"/>')


def icon(name):
    if name == 'github':
        return f'<svg class="icon icon-fill" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{GITHUB}</svg>'
    return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{PATHS[name]}</svg>'


def expand(text):
    """Replace every {{icon:name}} token with its SVG."""
    return re.sub(r'\{\{icon:([a-z]+)\}\}', lambda m: icon(m.group(1)), text)
