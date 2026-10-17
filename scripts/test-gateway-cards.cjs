// Exercise the real controller with scroll geometry, without browser dependencies.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const code = fs.readFileSync(path.join(__dirname, '../script.js'), 'utf8')
  .match(/function initGatewayCards\(\) \{[\s\S]*?\n\}\ninitGatewayCards\(\);/)[0];
function element() {
  return {events: {}, attrs: {}, textContent: '', children: [],
    addEventListener(type, cb) { this.events[type] = cb; },
    setAttribute(key, value) { this.attrs[key] = value; },
    removeAttribute(key) { delete this.attrs[key]; },
    append(child) { this.children.push(child); }};
}
const mobile = {...element(), matches: true}, motion = {matches: false};
const cards = ['News', 'People', 'Publications', 'Contact & Join Us'].map((name, index) =>
  ({offsetLeft: 20 + index * 314, querySelector() { return {textContent: name}; }}));
const dots = element(), previous = element(), next = element(), status = element(), controls = element();
controls.querySelector = s => ({'.gateway-dots': dots, '[data-gateway-step="-1"]': previous,
  '[data-gateway-step="1"]': next, '.gateway-position': status})[s];
const track = {...element(), clientWidth: 360, scrollWidth: 1282, scrollLeft: 0,
  querySelectorAll() { return cards; },
  scrollTo(options) { this.lastScroll = options; this.scrollLeft = options.left; this.events.scroll(); }};
let callback;
vm.runInNewContext(code, {
  document: {querySelector(s) { return s === '#gateway-track' ? track : controls; }, createElement: element},
  window: {matchMedia(s) { return s.includes('max-width') ? mobile : motion; }, addEventListener() {}},
  requestAnimationFrame(cb) { callback = cb; return 1; }
});
function flush() { const cb = callback; callback = null; if (cb) cb(); }
assert.equal(dots.children.length, 4);
assert.equal(controls.hidden, false);
assert.equal(previous.disabled, true);
assert.equal(next.disabled, false);
next.events.click(); flush();
assert.equal(track.scrollLeft, 314);
assert.equal(track.lastScroll.behavior, 'smooth');
assert.equal(dots.children[1].attrs['aria-current'], 'true');
assert.equal(status.textContent, 'People · 2 of 4');
dots.children[3].events.click(); flush();
assert.equal(track.scrollLeft, 922, 'final card clamps to the reachable end');
assert.equal(next.disabled, true);
assert.equal(dots.children[3].attrs['aria-current'], 'true');
track.scrollLeft = 628; track.events.scroll(); flush();
assert.equal(status.textContent, 'Publications · 3 of 4', 'manual swipes update pagination');
motion.matches = true;
let prevented = false;
track.events.keydown({key: 'Home', target: track, preventDefault() { prevented = true; }}); flush();
assert.equal(prevented, true);
assert.equal(track.scrollLeft, 0);
assert.equal(track.lastScroll.behavior, 'auto');
track.events.keydown({key: 'End', target: {}, preventDefault() { throw Error('must leave link keys alone'); }});
mobile.matches = false; mobile.events.change();
assert.equal(controls.hidden, true);
assert.equal(track.attrs.tabindex, undefined);
mobile.matches = true; track.scrollWidth = track.clientWidth; mobile.events.change();
assert.equal(controls.hidden, true, 'no controls are needed without overflow');
vm.runInNewContext(code, {document: {querySelector() { return null; }}});
console.log('Passed mobile arrows/dots, swipe sync, clamped end, keyboard, reduced motion, desktop and empty-page checks.');
