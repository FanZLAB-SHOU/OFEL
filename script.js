const page = document.body.dataset.page;
const legacyRoutes = {
  '#research': 'research.html', '#people': 'fan-zhang.html', '#principal-investigator': 'fan-zhang.html',
  '#current-members': 'members.html', '#alumni': 'alumni.html', '#publications': 'publications.html',
  '#publications-lab': 'publications.html#publications-lab', '#publications-fan-zhang': 'publications.html#publications-fan-zhang',
  '#contact': 'contact.html', '#join-us': 'contact.html#join-us'
};
if (page === 'index' && legacyRoutes[location.hash]) location.replace(legacyRoutes[location.hash]);

const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#main-nav');
const navGroups = [...navigation.querySelectorAll('.nav-group')];
function setDropdown(group, open) {
  group.querySelector('.nav-dropdown-toggle').setAttribute('aria-expanded', String(open));
  group.querySelector('.nav-submenu').hidden = !open;
}
function closeDropdowns() { navGroups.forEach(group => setDropdown(group, false)); }
function setMenu(open) {
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  navigation.classList.toggle('is-open', open);
  closeDropdowns();
}
function updateNavigation() {
  const section = document.body.dataset.navSection;
  navigation.querySelectorAll('[data-nav-section]').forEach(item => item.classList.toggle('is-current', item.dataset.navSection === section));
  navigation.querySelectorAll('a').forEach(link => {
    const url = new URL(link.href);
    let active = url.pathname === location.pathname;
    if (active && link.dataset.publicationCollection) active = link.dataset.publicationCollection === (document.body.dataset.collection || 'lab');
    else if (active && section === 'info') active = location.hash === '#join-us' ? url.hash === '#join-us' : !url.hash;
    if (active) link.setAttribute('aria-current', url.hash ? 'location' : 'page');
    else link.removeAttribute('aria-current');
  });
}
menuButton.addEventListener('click', () => setMenu(menuButton.getAttribute('aria-expanded') !== 'true'));
navGroups.forEach(group => {
  const toggle = group.querySelector('.nav-dropdown-toggle');
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    closeDropdowns(); setDropdown(group, open);
  });
  toggle.addEventListener('keydown', event => {
    if (!['ArrowDown', 'ArrowUp'].includes(event.key)) return;
    event.preventDefault(); closeDropdowns(); setDropdown(group, true);
    const links = group.querySelectorAll('.nav-submenu a');
    links[event.key === 'ArrowDown' ? 0 : links.length - 1].focus();
  });
});
let publications = null;
navigation.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
    setMenu(false);
    const url = new URL(link.href);
    if (url.pathname !== location.pathname || !url.hash) return;
    const isCollection = link.dataset.publicationCollection && publications;
    const target = isCollection ? document.querySelector('#publications') : document.getElementById(url.hash.slice(1));
    if (!target) return;
    event.preventDefault();
    if (isCollection) publications.select(link.dataset.publicationCollection, true);
    if (location.hash !== url.hash) history.pushState(null, '', url.hash);
    target.scrollIntoView({ block: 'start' });
    updateNavigation();
    const heading = target.querySelector('h1, h2, h3') || target;
    heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true });
    heading.addEventListener('blur', () => heading.removeAttribute('tabindex'), { once: true });
  });
});
document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  const open = navGroups.find(group => group.querySelector('.nav-dropdown-toggle').getAttribute('aria-expanded') === 'true');
  if (open) { setDropdown(open, false); open.querySelector('.nav-dropdown-toggle').focus(); }
  else if (menuButton.getAttribute('aria-expanded') === 'true') { setMenu(false); menuButton.focus(); }
});
document.addEventListener('focusin', event => { if (!event.target.closest('.site-header')) setMenu(false); });
document.addEventListener('click', event => {
  if (!event.target.closest('.site-header')) setMenu(false);
  else if (!event.target.closest('#main-nav')) closeDropdowns();
});
window.matchMedia('(min-width: 701px)').addEventListener('change', () => setMenu(false));

function initPublications() {
  if (!document.querySelector('#publication-list')) return null;
  const filters = [...document.querySelectorAll('.filter-button')];
  const collections = [...document.querySelectorAll('.collection-button')];
  const papers = [...document.querySelectorAll('.publication')];
  const count = document.querySelector('.publication-count');
  const note = document.querySelector('#publication-collection-note');
  const empty = document.querySelector('.publication-empty');
  const citations = document.querySelector('#publication-citations');
  const expandContainer = document.querySelector('.publication-expand');
  const expandButton = document.querySelector('#publication-toggle');
  let collection = 'lab', topic = 'all', expanded = false;
  function render() {
    const all = papers.filter(p => collection === 'lab' ? p.dataset.lab === 'true' : p.dataset.fanZhang === 'true');
    const matching = all.filter(p => topic === 'all' || p.dataset.topic === topic);
    const limited = topic === 'all' && !expanded;
    papers.forEach(p => { p.hidden = true; });
    matching.forEach((p, index) => { p.hidden = limited && index >= 6; });
    const visible = limited ? Math.min(6, matching.length) : matching.length;
    count.textContent = visible < matching.length ? `Showing ${visible} of ${matching.length} publications` : `${visible} publication${visible === 1 ? '' : 's'}`;
    note.textContent = collection === 'lab'
      ? 'Research from the Oceanic Fisheries Ecosystem Laboratory. Some papers also appear in Fan Zhang’s collection.'
      : 'Selected publications co-authored by Fan Zhang, including lab research and collaborations.';
    empty.hidden = matching.length > 0;
    empty.textContent = all.length === 0 && collection === 'lab' ? 'The lab publication collection is being curated.' : 'No publications match this topic in the selected collection.';
    expandContainer.hidden = topic !== 'all' || matching.length <= 6;
    expandButton.setAttribute('aria-expanded', String(expanded));
    expandButton.textContent = expanded ? 'Show recent publications ↑' : `Show all ${matching.length} publications ↓`;
    citations.hidden = all.length === 0;
    citations.href = collection === 'lab' ? 'assets/lab-publications.bib' : 'assets/selected-publications.bib';
    document.body.dataset.collection = collection;
    collections.forEach(button => {
      const active = button.dataset.collection === collection;
      button.classList.toggle('is-active', active); button.setAttribute('aria-pressed', String(active));
    });
    filters.forEach(button => {
      const active = button.dataset.filter === topic;
      button.classList.toggle('is-active', active); button.setAttribute('aria-pressed', String(active));
    });
    updateNavigation();
  }
  function select(value, resetTopic = false) {
    collection = value; expanded = false;
    if (resetTopic) topic = 'all';
    render();
  }
  filters.forEach(button => button.addEventListener('click', () => { topic = button.dataset.filter; expanded = false; render(); }));
  collections.forEach(button => button.addEventListener('click', () => {
    select(button.dataset.collection); history.replaceState(null, '', `#publications-${collection}`);
  }));
  expandButton.addEventListener('click', () => {
    expanded = !expanded; render();
    if (!expanded) document.querySelector('#publications-title').scrollIntoView();
  });
  render();
  return { select };
}
publications = initPublications();
function applyHash() {
  if (page === 'index' && legacyRoutes[location.hash]) { location.replace(legacyRoutes[location.hash]); return; }
  const hashes = { '#publications-lab': 'lab', '#publications-fan-zhang': 'fan-zhang' };
  if (publications && hashes[location.hash]) {
    publications.select(hashes[location.hash], true);
    requestAnimationFrame(() => document.querySelector('#publications').scrollIntoView({ block: 'start' }));
  }
  updateNavigation();
}
window.addEventListener('hashchange', applyHash);
applyHash();

function initResearchReel() {
  const track = document.querySelector('.research-track');
  if (!track) return;
  const section = track.closest('.home-research');
  const marquee = track.querySelector('.reel-marquee');
  const firstGroup = track.querySelector('.reel-group');
  const pause = section.querySelector('[data-reel="pause"]');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const speed = 45; // pixels per second
  let paused = false;
  section.querySelector('.reel-controls').hidden = motion.matches;
  function updatePause() {
    pause.textContent = paused ? 'Play' : 'Pause';
    pause.setAttribute('aria-pressed', String(paused));
    track.classList.toggle('is-paused', paused);
  }
  // One loop moves the strip by one group (half its width), so the duration keeps the speed constant at any screen size.
  function setDuration() { marquee.style.setProperty('--reel-duration', `${firstGroup.offsetWidth / speed}s`); }
  pause.addEventListener('click', () => { paused = !paused; updatePause(); });
  motion.addEventListener('change', event => { section.querySelector('.reel-controls').hidden = event.matches; });
  if ('ResizeObserver' in window) new ResizeObserver(setDuration).observe(firstGroup);
  setDuration();
  updatePause();
}

function initReveal() {
  let items = [...document.querySelectorAll('[data-reveal]')];
  if (!items.length || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.documentElement.classList.add('reveal-ready');
  // Position checks on load and scroll; no dependence on animation frames, so content never stays hidden.
  function check() {
    const limit = window.innerHeight * 0.92;
    items = items.filter(item => {
      if (item.getBoundingClientRect().top > limit) return true;
      item.classList.add('is-revealed');
      return false;
    });
    if (!items.length) ['scroll', 'resize'].forEach(type => window.removeEventListener(type, check));
  }
  ['scroll', 'resize'].forEach(type => window.addEventListener(type, check, { passive: true }));
  check();
}
initReveal();
initResearchReel();
document.querySelector('#copyright-year').textContent = new Date().getFullYear();
