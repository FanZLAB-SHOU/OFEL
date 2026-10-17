"""Usage: python scripts/make-campus-map.py <tile-cache-dir> assets/contact/campus-map.webp (needs Pillow).

Render a small static campus map from OpenStreetMap tiles, tinted to the site's navy, with a pin."""
import io, math, sys, time, urllib.request
from PIL import Image, ImageDraw, ImageOps, ImageFilter
lat, lon, z = 30.88475, 121.89311, 15
W, H = 960, 720
tiles_dir, out = sys.argv[1], sys.argv[2]
def to_px(lat, lon, z):
    n = 2 ** z * 256
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return x, y
cx, cy = to_px(lat, lon, z)
x0, y0 = cx - W / 2, cy - H / 2
canvas = Image.new('RGB', (W, H))
for tx in range(int(x0 // 256), int((x0 + W) // 256) + 1):
    for ty in range(int(y0 // 256), int((y0 + H) // 256) + 1):
        path = f'{tiles_dir}/{z}_{tx}_{ty}.png'
        try:
            data = open(path, 'rb').read()
        except FileNotFoundError:
            req = urllib.request.Request(f'https://tile.openstreetmap.org/{z}/{tx}/{ty}.png', headers={'User-Agent': 'OFEL-lab-website-static-map/1.0 (one-time render)'})
            data = urllib.request.urlopen(req, timeout=30).read(); open(path, 'wb').write(data); time.sleep(0.5)
        canvas.paste(Image.open(io.BytesIO(data)).convert('RGB'), (int(tx * 256 - x0), int(ty * 256 - y0)))
# Navy tint: invert luminance so land is dark and roads light, then colourise.
g = ImageOps.invert(ImageOps.grayscale(canvas))
g = ImageOps.autocontrast(g, cutoff=1)
tinted = ImageOps.colorize(g, black=(14, 40, 72), white=(190, 222, 245), mid=(52, 98, 140))
d = ImageDraw.Draw(tinted, 'RGBA')
px, py = W / 2, H / 2
for r, a in ((28, 45), (18, 80)):
    d.ellipse((px - r, py - r, px + r, py + r), fill=(124, 195, 245, a))
d.ellipse((px - 8, py - 8, px + 8, py + 8), fill=(255, 255, 255, 255))
d.ellipse((px - 4.5, py - 4.5, px + 4.5, py + 4.5), fill=(11, 74, 134, 255))
tinted.save(out, quality=84, method=6)
print('saved', out, tinted.size)
