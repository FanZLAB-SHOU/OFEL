// Keep the faculty portrait clear of the right workspace and reveal profile sections on approach.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../script.js'), 'utf8');
function functionSource(name) {
  const start = source.indexOf(`function ${name}(`);
  assert(start >= 0, `Missing ${name}`);
  return source.slice(start, source.indexOf('\n}', start) + 2);
}
const scope = {};
vm.runInNewContext(functionSource('facultyPortraitGeometry'), scope);
for (const [width, height] of [[375, 812], [414, 896], [768, 1024], [1024, 768], [1280, 720], [1440, 900], [1512, 982], [1867, 925], [2560, 1080], [1200, 1300]]) {
  const g = scope.facultyPortraitGeometry(width, height, 80);
  assert(g.headTop >= 80, 'Portrait head must remain below the navigation');
  assert(g.personLeft >= 0, 'The visible body should remain inside the screen');
  if (!g.compact) {
    assert(g.personRight <= width * .5, 'Portrait must fit in the left half');
    assert(width * .52 - g.personRight >= 20, 'Right workspace needs a gap from the body');
  } else {
    assert(g.personRight <= width, 'Compact portrait should remain inside the screen');
    // Adding a card changes hero height, but must not keep pushing the portrait and controls down.
    const expanded = scope.facultyPortraitGeometry(width, height + 700, 80, height);
    assert.equal(expanded.bottom, g.bottom);
  }
}
let scroll, ready = false;
const sections = [100, 1100, 2100].map(top => ({ top, visible: false,
  getBoundingClientRect() { return {top: this.top}; }, classList: {add() {}} }));
sections.forEach(section => section.classList.add = () => { section.visible = true; });
const window = {innerHeight: 800, matchMedia: () => ({matches: false}),
  addEventListener(type, fn) { if (type === 'scroll') scroll = fn; }, removeEventListener() {}};
const document = {querySelectorAll: () => sections, documentElement: {classList: {add() { ready = true; }}}};
vm.runInNewContext(functionSource('initReveal') + '\ninitReveal();', {window, document});
assert(ready && sections[0].visible && !sections[1].visible && !sections[2].visible);
sections.forEach(s => { s.top -= 800; }); scroll();
assert(sections[1].visible && !sections[2].visible);
window.matchMedia = () => ({matches: true}); ready = false;
vm.runInNewContext(functionSource('initReveal') + '\ninitReveal();', {window, document});
assert(!ready, 'Reduced motion must not hide sections behind an animation gate');
console.log('Passed left-half portrait geometry, compact layout stability, progressive section reveals and reduced-motion checks.');
