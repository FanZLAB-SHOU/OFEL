// Compact JPEG copies for link previews; source photographs/covers stay unchanged.
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const sharp = require('sharp');
const root = path.resolve(__dirname, '..');
async function main() {
  const people = JSON.parse(await fs.readFile(path.join(root, 'assets/people.json'), 'utf8'));
  const posts = JSON.parse(await fs.readFile(path.join(root, 'assets/blog.json'), 'utf8')).posts;
  const sources = new Set(['assets/people/fan-zhang.jpg',
    ...people.groups.concat(people.alumni || []).flatMap(g => g.members.map(p => p.photo)),
    ...posts.map(p => p.image)]);
  const folder = path.join(root, 'assets/share');
  await fs.mkdir(folder, {recursive: true});
  const manifest = {};
  for (const source of [...sources].filter(Boolean).sort()) {
    const bytes = await fs.readFile(path.join(root, source));
    const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
    const version = crypto.createHash('sha256').update(sha256 + 'jpeg86-inside1200-v1').digest('hex').slice(0,12);
    const stem = path.basename(source, path.extname(source)).replace(/[^a-z0-9-]/gi, '-');
    const src = `assets/share/${stem}-${version}.jpg`;
    const dest = path.join(root, src);
    try { await fs.access(dest); }
    catch {
      await sharp(bytes).rotate().resize({width:1200, height:1200, fit:'inside', withoutEnlargement:true})
        .flatten({background:'#f2f6fb'}).jpeg({quality:86, mozjpeg:true}).toFile(dest);
    }
    const meta = await sharp(dest).metadata();
    manifest[source] = {sha256, src, width:meta.width, height:meta.height, type:'image/jpeg', bytes:(await fs.stat(dest)).size};
  }
  const defaultSource = 'assets/social-card.png';
  const bytes = await fs.readFile(path.join(root,defaultSource));
  const meta = await sharp(bytes).metadata();
  manifest[defaultSource] = {sha256:crypto.createHash('sha256').update(bytes).digest('hex'),
    src:defaultSource,width:meta.width,height:meta.height,type:'image/png',bytes:bytes.length};
  await fs.writeFile(path.join(folder,'manifest.json'), JSON.stringify(manifest,null,2)+'\n');
  console.log(`Prepared ${Object.keys(manifest).length-1} individual sharing images and the existing homepage banner.`);
}
main().catch(error=>{console.error(error);process.exitCode=1;});
