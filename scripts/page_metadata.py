"""Shared page-head metadata and a sitemap of canonical content pages."""
import html
import hashlib
import json
import mimetypes
from pathlib import Path
import xml.etree.ElementTree as ET

from responsive_images import current
from site_paths import BASE, clean_url, source_paths

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = 'assets/social-card.png'


def share_image(source=None):
    source = source or DEFAULT_IMAGE
    manifest = ROOT / 'assets/share/manifest.json'
    images = json.loads(manifest.read_text()) if manifest.exists() else {}
    entry = images.get(source)
    if entry and current(source, entry['sha256']):
        return entry
    # New or changed source material can build before optional JPEG preparation.
    if not (ROOT / source).is_file():
        raise ValueError(f'Missing sharing image: {source}')
    return {'src':source, 'type':mimetypes.guess_type(source)[0] or 'image/jpeg'}


def render_head(title, description, canonical, asset_version, *, image=None, image_alt=None, kind='website'):
    picture = share_image(image)
    image_url = BASE + picture['src']
    alt = image_alt or ('OFEL laboratory banner' if not image else 'Image for ' + title)
    values = {
        'og:title':title, 'og:description':description, 'og:type':kind,
        'og:url':canonical, 'og:site_name':'Oceanic Fisheries Ecosystem Laboratory',
        'og:image':image_url, 'og:image:secure_url':image_url, 'og:image:type':picture['type'],
        'og:image:alt':alt,
    }
    if picture.get('width') and picture.get('height'):
        values.update({'og:image:width':str(picture['width']), 'og:image:height':str(picture['height'])})
    values.update({'twitter:card':'summary' if kind=='profile' else 'summary_large_image',
                   'twitter:title':title,'twitter:description':description,'twitter:image':image_url,'twitter:image:alt':alt})
    tags = '\n'.join(f'  <meta {"property" if key.startswith("og:") else "name"}="{key}" content="{html.escape(value,quote=True)}">'
                     for key,value in values.items())
    head = (ROOT / 'templates/head.html').read_text()
    for token,value in {'{{title}}':title,'{{description}}':description,'{{canonical}}':canonical,
                        '{{asset_version}}':asset_version,
                        '{{ui_version}}':hashlib.sha256((ROOT/'assets/styles/site-ui.css').read_bytes()).hexdigest()[:10],
                        '{{sitemap}}':BASE+'sitemap.xml'}.items():
        head = head.replace(token,html.escape(value,quote=True))
    return head.replace('{{share_metadata}}',tags)


def write_sitemap():
    namespace = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('',namespace)
    root = ET.Element(f'{{{namespace}}}urlset')
    for source in sorted(source_paths(), key=clean_url):
        item = ET.SubElement(root,f'{{{namespace}}}url')
        ET.SubElement(item,f'{{{namespace}}}loc').text = BASE + clean_url(source)
    ET.indent(root,space='  ')
    ET.ElementTree(root).write(ROOT/'sitemap.xml',encoding='utf-8',xml_declaration=True)
