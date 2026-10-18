"""Use pre-generated responsive derivatives while keeping source content unchanged."""

import hashlib
import html
import json
from functools import lru_cache
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def manifest():
    path = ROOT / 'assets/optimized/manifest.json'
    return json.loads(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=None)
def current(source, digest):
    path = ROOT / source
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest


def responsive_images(markup):
    def image(match):
        tag = match.group()
        attrs = {key: html.unescape(value) for key, _, value in re.findall(r'([\w-]+)=([\"\'])(.*?)\2', tag)}
        source = attrs.get('src')
        info = manifest().get(source)
        if not info or 'srcset' in attrs or not current(source, info['sha256']):
            return tag
        variants = info['variants']
        classes = attrs.get('class', '').split()
        if 'home-research-image' in classes:
            # Large cover crops on retina screens use the original at full size,
            # avoiding another lossy WebP encoding of the research artwork.
            variants = [v for v in variants if v['width'] < info['width']] + [
                {'width': info['width'], 'src': source}]
        fallback = next((v for v in variants if v['width'] >= 960), variants[-1])
        sizes = attrs.get('sizes')
        if not sizes:
            if 'gateway-bg' in classes:
                # Tall cover cards crop landscape images: budget for cover height,
                # not just the narrow card width, to keep faces sharp on retina screens.
                ratio = info['width'] / info['height']
                sizes = (f'(max-width: 700px) max(84vw, {round(520 * ratio)}px), '
                         f'(max-width: 1100px) max(46vw, {round(540 * ratio)}px), '
                         f'max(24vw, {round(580 * ratio)}px)')
            elif 'member-photo' in classes:
                sizes = '(max-width: 700px) 90px, 108px'
            elif 'alumni-photo' in classes:
                sizes = '(max-width: 700px) 44vw, 300px'
            elif 'profile-img' in classes or source.startswith('assets/people/'):
                sizes = '(max-width: 700px) calc(100vw - 40px), 560px'
            elif attrs.get('width', '').isdigit() and int(attrs['width']) <= 300:
                sizes = attrs['width'] + 'px'
            else:
                sizes = '(max-width: 700px) calc(100vw - 40px), 960px'
        replacements = {'src': fallback['src'], 'width': str(info['width']), 'height': str(info['height'])}
        for key, value in replacements.items():
            pattern = rf'\b{key}=([\"\'])(.*?)\1'
            if key in attrs:
                tag = re.sub(pattern, f'{key}="{html.escape(value, quote=True)}"', tag, count=1)
        extra = {'srcset': ', '.join(f'{v["src"]} {v["width"]}w' for v in variants),
                 'data-image-original': source, 'decoding': 'async'}
        if 'sizes' not in attrs:
            extra['sizes'] = sizes
        addition = ''.join(f' {key}="{html.escape(value, quote=True)}"' for key, value in extra.items() if key not in attrs)
        return tag[:-1] + addition + '>'
    return re.sub(r'<img\b[^>]*>', image, markup)
