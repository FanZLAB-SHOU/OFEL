// Check the real motion controller's pause, visibility and reduced-motion behavior.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const code = fs.readFileSync(path.join(root, 'script.js'), 'utf8')
  .match(/function initTeamSpace\(\) \{[\s\S]*?\n\}\ninitTeamSpace\(\);/)[0];
const events = {};
const classes = new Set();
const cards = Array.from({length: 11}, () => ({values: {}, style: {}}));
cards.forEach(card => { card.style.setProperty = (key, value) => { card.values[key] = value; }; });
const button = {hidden: true, attrs: {}, setAttribute(key, value) { this.attrs[key] = value; },
  addEventListener(type, fn) { events[type] = fn; }};
const motion = {matches: false, addEventListener(type, fn) { events.motion = fn; }};
const hero = {querySelectorAll: () => cards, querySelector: () => button,
  classList: {add: c => classes.add(c), toggle: (c, on) => on ? classes.add(c) : classes.delete(c)}};
const document = {hidden: false, querySelector: () => hero,
  addEventListener(type, fn) { events[type] = fn; }};
let intersection;
const window = {matchMedia: () => motion,
  IntersectionObserver: class { constructor(fn) { intersection = fn; } observe(value) { assert.equal(value, hero); } }};
vm.runInNewContext(code, {window, document, Math});
assert(classes.has('is-moving'));
assert.equal(button.hidden, false);
for (const card of cards) {
  for (let point = 1; point <= 3; point++) {
    assert(Math.abs(parseFloat(card.values[`--float-x${point}`])) <= 16);
    assert(Math.abs(parseFloat(card.values[`--float-y${point}`])) <= 12);
    assert(Math.abs(parseFloat(card.values[`--float-r${point}`])) <= 2.5);
  }
  assert(parseFloat(card.values['--float-duration']) >= 18);
}
events.click(); assert(!classes.has('is-moving')); assert.equal(button.attrs['aria-pressed'], 'true');
intersection([{isIntersecting: true}]); assert(!classes.has('is-moving'), 'Visibility must not undo a manual pause');
events.click(); assert(classes.has('is-moving'));
intersection([{isIntersecting: false}]); assert(!classes.has('is-moving'));
intersection([{isIntersecting: true}]); assert(classes.has('is-moving'));
document.hidden = true; events.visibilitychange(); assert(!classes.has('is-moving'));
document.hidden = false; events.visibilitychange(); assert(classes.has('is-moving'));
motion.matches = true; events.motion(); assert(!classes.has('is-moving')); assert(button.hidden);
motion.matches = false; events.motion(); assert(classes.has('is-moving'));
vm.runInNewContext(code, {document: {querySelector: () => null}});

// Validate photograph bounds and the empty central title space at narrow and wide sizes.
const css = fs.readFileSync(path.join(root, 'assets/styles/site-ui.css'), 'utf8');
const slots = [...css.matchAll(/\.team-space-card:nth-child\((\d+)\) \{ --photo-x: ([\d.]+)%; --photo-y: ([\d.]+)%; --photo-size: ([\d.]+)%; \}/g)];
assert.equal(slots.length, 22);
for (const width of [320, 390, 700, 768, 1024, 1440, 1920, 2560]) {
  const mobile = width <= 700, stageWidth = Math.min(width, 1600), height = mobile ? 720 : 760;
  for (const [, , x, y, size] of slots.slice(mobile ? 11 : 0, mobile ? 22 : 11)) {
    const w = Math.min(mobile ? 116 : 190, Math.max(mobile ? 42 : 60, stageWidth * Number(size) / 100));
    const h = w * 1.25, angle = 2.5 * Math.PI / 180;
    const halfW = (w * Math.cos(angle) + h * Math.sin(angle)) / 2 + (mobile ? 7.2 : 16);
    const halfH = (h * Math.cos(angle) + w * Math.sin(angle)) / 2 + (mobile ? 5.4 : 12);
    const cx = Number(x) / 100 * stageWidth, cy = Number(y) / 100 * height;
    assert(cx - halfW >= 0 && cx + halfW <= stageWidth, `Horizontal bounds at ${width}px`);
    assert(cy - halfH >= 0 && cy + halfH <= height, `Vertical bounds at ${width}px`);
    const reserve = mobile ? [.26, .74, .36, .60] : [.30, .70, .38, .58];
    assert(cx + halfW <= stageWidth * reserve[0] || cx - halfW >= stageWidth * reserve[1]
      || cy + halfH <= height * reserve[2] || cy - halfH >= height * reserve[3], `Title must stay clear at ${width}px`);
  }
}
console.log('Passed floating photo bounds, title clearance, pause controls, visibility and reduced-motion checks.');
