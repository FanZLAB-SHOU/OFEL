"""Build the homepage hero wallpaper: the lab's research illustrations redrawn as glowing line art on deep ocean blue.

Needs Pillow and numpy. Usage: python scripts/make-hero-wallpaper.py assets assets/hero/ocean-2560.webp
(then resize to assets/hero/ocean-1280.webp for small screens).
"""
import sys
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance
assets, out = sys.argv[1], sys.argv[2]
W, H = 2560, 1440
INK = np.array([22, 55, 90], float)
PAPER = np.array([247, 245, 239], float)


def sketch(name, box, scale):
    im = Image.open(f'{assets}/research/{name}.webp').convert('L').crop(box)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.3)
    g = np.asarray(im, float)
    blur = np.asarray(ImageOps.invert(im).filter(ImageFilter.GaussianBlur(7)), float)
    dodge = np.clip(g * 255 / np.maximum(1, 255 - blur), 0, 255)
    # Keep line work, drop faint texture: light greys fade to paper.
    d = dodge / 255
    d = np.clip((d - 0.55) / 0.40, 0, 1)
    return 1 - (1 - d) ** 1.0  # 0 = ink, 1 = paper


def feather(w, h, edge=0.28):
    # Rounded-rectangle feather: fully opaque centre, soft fade toward every edge.
    x = np.minimum(np.arange(w) / (w * edge), (w - 1 - np.arange(w)) / (w * edge))
    y = np.minimum(np.arange(h) / (h * edge), (h - 1 - np.arange(h)) / (h * edge))
    m = np.clip(np.minimum.outer(np.clip(y, 0, 1), np.clip(x, 0, 1)), 0, 1)
    return m * m * (3 - 2 * m)  # smoothstep


ink = np.zeros((H, W))  # 0 = paper, 1 = full ink
placements = [
    ('vessel-ai', (0, 0, 1200, 1000), 1.12, (-60, 120)),           # AIS network + vessel, left
    ('biology-dna', (1070, 0, 1536, 1024), 1.3, (W - 640, 90)),   # shell + DNA helix, right
    ('population-assessment', (60, 300, 1400, 1000), 1.22, (430, 780)),  # tuna, low centre
]
for name, box, scale, (x, y) in placements:
    s = 1 - sketch(name, box, scale)  # ink amount
    h, w = s.shape
    s *= feather(w, h)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    part = s[y0 - y:y1 - y, x0 - x:x1 - x]
    ink[y0:y1, x0:x1] = np.maximum(ink[y0:y1, x0:x1], part)
# Deep-ocean colouring: light falls from the surface, darkening with depth; lines glow pale blue.
yy = np.linspace(0, 1, H)[:, None]
xx = np.linspace(-1, 1, W)[None, :]
top, deep = np.array([14, 52, 92], float), np.array([2, 10, 24], float)
depth = np.clip(yy ** 0.8, 0, 1)
glow = np.clip(1 - np.sqrt((xx * 0.75) ** 2 + (yy * 1.6) ** 2), 0, 1) ** 2  # light from above, centre
bg = top * (1 - depth[..., None]) + deep * depth[..., None]
bg = bg + glow[..., None] * np.array([28, 60, 82], float)
line = np.array([168, 214, 240], float)
ink = np.clip(ink * 0.9, 0, 1)
rgb = bg * (1 - ink[..., None]) + line * ink[..., None]
Image.fromarray(rgb.astype('uint8')).save(out, quality=84, method=6)
print('saved', out)
