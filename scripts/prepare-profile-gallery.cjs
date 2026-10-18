// Prepare only explicitly supplied profile galleries; originals remain untouched.
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const sharp = require('sharp');
const root = path.resolve(__dirname, '..');
async function main() {
  const data = JSON.parse(await fs.readFile(path.join(root, 'assets/people.json'), 'utf8'));
  const manifestPath = path.join(root, 'assets/optimized/manifest.json');
  const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
  let count = 0;
  for (const person of data.groups.flatMap(group => group.members)) {
    for (const photo of person.gallery || []) {
      const bytes = await fs.readFile(path.join(root, photo.image));
      const meta = await sharp(bytes).rotate().metadata();
      const rotated = [5, 6, 7, 8].includes(meta.orientation);
      const width = rotated ? meta.height : meta.width, height = rotated ? meta.width : meta.height;
      const digest = crypto.createHash('sha256').update(bytes).digest('hex');
      const version = crypto.createHash('sha256').update(digest + 'gallery-webp-90-v1').digest('hex').slice(0, 12);
      const stem = photo.image.split('/').slice(-2).join('-').replace(/\.jpg$/i, '');
      const variants = [];
      for (const size of [...new Set([480, 960, 1440, 1920, 2560, Math.min(width, 2560)].filter(w => w <= width))].sort((a, b) => a - b)) {
        const src = `assets/optimized/${stem}-${version}-${size}.webp`;
        const dest = path.join(root, src);
        try { await fs.access(dest); }
        catch { await sharp(bytes).rotate().resize({width: size, withoutEnlargement: true}).webp({quality: 90, effort: 6}).toFile(dest); }
        variants.push({width: size, src, bytes: (await fs.stat(dest)).size});
      }
      manifest[photo.image] = {sha256: digest, bytes: bytes.length, width, height, variants};
      count++;
    }
  }
  await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  console.log(`Prepared ${count} profile gallery photographs.`);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
