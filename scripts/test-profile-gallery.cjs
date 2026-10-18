const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(path.join(__dirname, '../script.js'), 'utf8');
const code = source.match(/function initProfileGallery\(\) \{[\s\S]*?\n\}\ninitProfileGallery\(\);/)[0];
function element() { return {events: {}, addEventListener(type, fn) { this.events[type] = fn; }}; }
const image = {}, caption = {}, count = {}, close = element(), prev = element(), next = element();
const links = Array.from({length: 5}, (_, i) => ({...element(), href: `photo-${i}.jpg`, dataset: {galleryCaption: `Caption ${i}`},
  querySelector: () => ({alt: `Description ${i}`}), focus() { this.focused = true; }}));
const selectors = {'[data-gallery-full]': image, '[data-gallery-caption]': caption, '[data-gallery-count]': count,
  '[data-gallery-close]': close, '[data-gallery-prev]': prev, '[data-gallery-next]': next};
const dialog = {...element(), querySelector: s => selectors[s], showModal() { this.open = true; },
  close() { this.open = false; this.events.close(); }};
const gallery = {querySelectorAll: () => links, querySelector: () => dialog};
vm.runInNewContext(code, {document: {querySelectorAll: () => [gallery]}});
let prevented = false;
links[2].events.click({button: 0, preventDefault() { prevented = true; }});
assert(prevented && dialog.open); assert.equal(image.src, 'photo-2.jpg'); assert.equal(image.alt, 'Description 2'); assert.equal(count.textContent, '3 / 5');
next.events.click(); assert.equal(image.src, 'photo-3.jpg');
dialog.events.keydown({key: 'ArrowRight', preventDefault() {}}); assert.equal(image.src, 'photo-4.jpg');
next.events.click(); assert.equal(image.src, 'photo-0.jpg');
prev.events.click(); assert.equal(image.src, 'photo-4.jpg');
close.events.click(); assert(!dialog.open); assert(links[2].focused);
prevented = false; links[0].events.click({button: 0, ctrlKey: true, preventDefault() { prevented = true; }}); assert(!prevented);
links[1].events.click({button: 0, preventDefault() {}}); dialog.events.click({target: image}); assert(dialog.open);
dialog.events.click({target: dialog}); assert(!dialog.open); assert(links[1].focused);
const fallback = {...element(), href: 'original.jpg'};
vm.runInNewContext(code, {document: {querySelectorAll: () => [{querySelectorAll: () => [fallback], querySelector: () => ({})}]}});
assert.equal(fallback.events.click, undefined, 'Unsupported dialogs must preserve direct image links');
vm.runInNewContext(code, {document: {querySelectorAll: () => []}});
console.log('Passed photo opening, captions, wraparound navigation, keyboard, close/focus return and fallback checks.');
