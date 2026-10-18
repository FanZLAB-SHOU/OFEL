// Direct visits to directory index files use the same clean URL as navigation.
if (location.pathname.endsWith('/index.html')) {
  history.replaceState(null, '', location.pathname.slice(0, -10) + location.search + location.hash);
}
const page = document.body.dataset.page;
const legacyRoutes = {
  '#research': 'research/themes/', '#people': 'members/fan-zhang/', '#principal-investigator': 'members/fan-zhang/',
  '#current-members': 'members/', '#alumni': 'members/alumni/', '#publications': 'publications/',
  '#publications-lab': 'publications/#publications-lab', '#publications-fan-zhang': 'publications/#publications-fan-zhang',
  '#contact': 'contact/', '#join-us': 'contact/#join-us'
};
if (page === 'index' && legacyRoutes[location.hash]) {
  const target = new URL(legacyRoutes[location.hash], location.href);
  target.search = location.search;
  location.replace(target.href);
}

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

function initNewsFilters() {
  const list = document.querySelector('#news-list');
  if (!list) return;
  const controls = document.querySelector('.news-filters');
  const buttons = [...controls.querySelectorAll('[data-news-filter]')];
  const items = [...list.querySelectorAll('[data-news-category]')];
  const count = document.querySelector('.news-count');
  const empty = document.querySelector('.news-empty');
  const categories = new Set(buttons.map(button => button.dataset.newsFilter));
  function fromUrl() { return new URL(location.href).searchParams.get('category') || 'all'; }
  function select(value, updateUrl = false) {
    if (!categories.has(value)) value = 'all';
    let visible = 0;
    items.forEach(item => {
      item.hidden = value !== 'all' && item.dataset.newsCategory !== value;
      if (!item.hidden) visible++;
    });
    buttons.forEach(button => {
      const active = button.dataset.newsFilter === value;
      button.setAttribute('aria-pressed', String(active));
      button.classList.toggle('is-active', active);
    });
    count.textContent = `${visible} news item${visible === 1 ? '' : 's'}`;
    empty.hidden = visible > 0;
    if (updateUrl) {
      const url = new URL(location.href);
      if (value === 'all') url.searchParams.delete('category');
      else url.searchParams.set('category', value);
      history.replaceState(null, '', url.pathname + url.search + url.hash);
    }
  }
  buttons.forEach(button => button.addEventListener('click', () => select(button.dataset.newsFilter, true)));
  window.addEventListener('popstate', () => select(fromUrl()));
  controls.hidden = false;
  select(fromUrl());
}
initNewsFilters();

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
  const search = document.querySelector('#publication-search');
  const yearSelect = document.querySelector('#publication-year');
  const reset = document.querySelector('#publication-reset');
  const normalize = text => text.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
  const searchText = new Map(papers.map(paper => [paper, normalize(paper.dataset.search)]));
  let collection = 'lab', topic = 'all', expanded = false, year = 'all';
  function inCollection(paper) { return collection === 'lab' ? paper.dataset.lab === 'true' : paper.dataset.fanZhang === 'true'; }
  function syncYears() {
    const years = [...new Set(papers.filter(inCollection).map(paper => paper.dataset.year))].sort((a, b) => Number(b) - Number(a));
    if (!years.includes(year)) year = 'all';
    yearSelect.replaceChildren();
    ['all', ...years].forEach(value => {
      const option = document.createElement('option');
      option.value = value; option.textContent = value === 'all' ? 'All years' : value;
      yearSelect.append(option);
    });
    yearSelect.value = year;
  }
  function render() {
    const all = papers.filter(inCollection);
    const terms = normalize(search.value).split(/\s+/).filter(Boolean);
    const unfiltered = topic === 'all' && year === 'all' && terms.length === 0;
    const matching = all.filter(p => (topic === 'all' || p.dataset.topic === topic)
      && (year === 'all' || p.dataset.year === year)
      && terms.every(term => searchText.get(p).includes(term)));
    const limited = unfiltered && !expanded;
    papers.forEach(p => { p.hidden = true; });
    matching.forEach((p, index) => { p.hidden = limited && index >= 6; });
    const visible = limited ? Math.min(6, matching.length) : matching.length;
    count.textContent = visible < matching.length ? `Showing ${visible} of ${matching.length} publications` : `${visible} publication${visible === 1 ? '' : 's'}`;
    note.textContent = collection === 'lab'
      ? 'Research from the Oceanic Fisheries Ecosystem Laboratory. Some papers also appear in Fan Zhang’s collection.'
      : 'Selected publications co-authored by Fan Zhang, including lab research and collaborations.';
    empty.hidden = matching.length > 0;
    empty.textContent = all.length === 0 && collection === 'lab' ? 'The lab publication collection is being curated.' : 'No publications match your search and filters in this collection.';
    expandContainer.hidden = !unfiltered || matching.length <= 6;
    reset.disabled = !search.value && topic === 'all' && year === 'all';
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
    syncYears();
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
  search.addEventListener('input', () => { expanded = false; render(); });
  yearSelect.addEventListener('change', () => { year = yearSelect.value; expanded = false; render(); });
  reset.addEventListener('click', () => {
    search.value = ''; year = 'all'; topic = 'all'; expanded = false;
    yearSelect.value = 'all'; render(); search.focus();
  });
  syncYears();
  document.querySelector('.publication-discovery').hidden = false;
  render();
  return { select };
}
publications = initPublications();

function initCitationCopy() {
  document.querySelectorAll('.copy-citation').forEach(button => {
    const tools = button.closest('.publication-citation');
    const text = tools.querySelector('.citation-text');
    const manual = tools.querySelector('.citation-manual');
    const status = tools.querySelector('.citation-status');
    button.hidden = false;
    button.addEventListener('click', async () => {
      button.disabled = true; status.textContent = '';
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(text.value);
        status.textContent = 'Citation copied.';
      } catch {
        manual.open = true; text.focus(); text.select();
        status.textContent = 'Citation selected. Use your device’s Copy command.';
      } finally { button.disabled = false; }
    });
  });
}
initCitationCopy();
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
  const marquee = track.querySelector('.reel-marquee');
  const firstGroup = track.querySelector('.reel-group');
  const speed = 45; // pixels per second
  // One loop moves the strip by one group (half its width), so the duration keeps the speed constant at any screen size.
  function setDuration() { marquee.style.setProperty('--reel-duration', `${firstGroup.offsetWidth / speed}s`); }
  if ('ResizeObserver' in window) new ResizeObserver(setDuration).observe(firstGroup);
  setDuration();
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

// Member introductions float the shared header over the image, then restore the light header below it.
function initMemberIntro() {
  const hero = document.querySelector('[data-member-intro]');
  const header = document.querySelector('.site-header');
  if (!hero || !header) return;
  const update = () => header.classList.toggle('is-past-member', hero.getBoundingClientRect().bottom <= header.offsetHeight);
  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  update();
}
initMemberIntro();

// Homepage header floats over the hero; give it a background once the page scrolls.
if (document.body.dataset.page === 'index') {
  const header = document.querySelector('.site-header');
  const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 24);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}
initResearchReel();

function initGatewayCards() {
  const track = document.querySelector('#gateway-track');
  const controls = document.querySelector('.gateway-controls');
  if (!track || !controls) return;
  const cards = [...track.querySelectorAll('.gateway-card')];
  const dots = controls.querySelector('.gateway-dots');
  const previous = controls.querySelector('[data-gateway-step="-1"]');
  const next = controls.querySelector('[data-gateway-step="1"]');
  const position = controls.querySelector('.gateway-position');
  const mobile = window.matchMedia('(max-width: 700px)');
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let active = 0, frame = null;
  const labels = cards.map(card => card.querySelector('h3').textContent);
  const buttons = cards.map((card, index) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'gateway-dot';
    button.setAttribute('aria-label', `Show ${labels[index]}`);
    button.setAttribute('aria-controls', 'gateway-track');
    button.addEventListener('click', () => goTo(index));
    dots.append(button);
    return button;
  });
  // The final card cannot align all the way left; use its actual reachable offset.
  function offsets() {
    const max = Math.max(0, track.scrollWidth - track.clientWidth);
    return cards.map(card => Math.min(max, card.offsetLeft - cards[0].offsetLeft));
  }
  function update() {
    frame = null;
    const enabled = mobile.matches && track.scrollWidth > track.clientWidth + 1;
    controls.hidden = !enabled;
    if (!enabled) { track.removeAttribute('tabindex'); return; }
    track.setAttribute('tabindex', '0');
    const targets = offsets();
    active = targets.reduce((best, offset, index) =>
      Math.abs(offset - track.scrollLeft) < Math.abs(targets[best] - track.scrollLeft) ? index : best, 0);
    buttons.forEach((button, index) => button.setAttribute('aria-current', String(index === active)));
    previous.disabled = active === 0;
    next.disabled = active === cards.length - 1;
    const label = `${labels[active]} · ${active + 1} of ${cards.length}`;
    if (position.textContent !== label) position.textContent = label;
  }
  function goTo(index) {
    index = Math.max(0, Math.min(cards.length - 1, index));
    track.scrollTo({left: offsets()[index], behavior: motion.matches ? 'auto' : 'smooth'});
  }
  previous.addEventListener('click', () => goTo(active - 1));
  next.addEventListener('click', () => goTo(active + 1));
  track.addEventListener('scroll', () => {
    if (frame === null) frame = requestAnimationFrame(update);
  }, {passive: true});
  track.addEventListener('keydown', event => {
    if (!mobile.matches || event.target !== track) return;
    const target = {ArrowLeft: active - 1, ArrowRight: active + 1, Home: 0, End: cards.length - 1}[event.key];
    if (target === undefined) return;
    event.preventDefault(); goTo(target);
  });
  mobile.addEventListener('change', update);
  if ('ResizeObserver' in window) new ResizeObserver(update).observe(track);
  else window.addEventListener('resize', update);
  update();
}
initGatewayCards();

function initLabFilm() {
  const player = document.querySelector('.home-film-player');
  const trigger = document.querySelector('[data-play-film]');
  if (!player || !trigger) return;
  // Keep the native anchor scroll and controls; request media only after a click.
  trigger.addEventListener('click', event => {
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0) return;
    const playback = player.play();
    // If the browser declines playback, its native play control remains available.
    if (playback) playback.catch(() => {});
  });
  player.addEventListener('error', () => {
    document.querySelector('.home-film-error').hidden = false;
  }, true);
}
initLabFilm();

function initContactEmail() {
  const options = document.querySelector('[data-email-options]');
  if (!options) return;
  const button = options.querySelector('[data-copy-email]');
  const manual = options.querySelector('.contact-email-manual');
  const address = manual.querySelector('input');
  const status = options.querySelector('.contact-email-status');
  button.hidden = false;
  button.addEventListener('click', async () => {
    button.disabled = true;
    status.textContent = '';
    try {
      if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(address.value);
      manual.hidden = true;
      status.textContent = 'Email address copied.';
    } catch {
      manual.hidden = false;
      address.focus();
      address.select();
      status.textContent = 'Address selected. Use your device’s Copy command.';
    } finally { button.disabled = false; }
  });
}
initContactEmail();
// The portrait occupies the left half; the right workspace lays out controls and cards in normal flow.
function facultyPortraitGeometry(width, height, headerHeight, viewportHeight = height) {
  const compact = width < 1000 || width / height < 1.2;
  const imageHeight = compact ? Math.min(viewportHeight * .68, 600, width * 1.1) : Math.min(height, width * .60);
  const imageWidth = imageHeight * 4 / 3;
  const headX = width * (compact ? .5 : .28);
  const left = headX - .39 * imageWidth;
  const top = compact ? headerHeight + 120 - .223 * imageHeight : height - imageHeight;
  return { compact, width: imageWidth, height: imageHeight, left, top, headX,
    headTop: top + .223 * imageHeight, faceLeft: left + .29 * imageWidth,
    personLeft: left + .11 * imageWidth, personRight: left + .65 * imageWidth,
    bottom: top + imageHeight };
}
function initFacultyHero() {
  const hero = document.querySelector('[data-fz-hero]');
  if (!hero) return;
  const bubbleBox = hero.querySelector('.fz-bubble');
  function layout() {
    const W = hero.clientWidth, H = hero.clientHeight;
    const headerH = document.querySelector('.site-header').offsetHeight;
    const g = facultyPortraitGeometry(W, H, headerH, window.innerHeight);
    hero.classList.toggle('is-compact', g.compact);
    hero.querySelectorAll('.fz-stage-front .fz-layer').forEach(img => {
      Object.assign(img.style, { left: `${g.left}px`, top: `${g.top}px`, width: `${g.width}px`, height: `${g.height}px`, right: 'auto', bottom: 'auto', objectFit: 'fill' });
    });
    hero.style.setProperty('--header-height', `${headerH}px`);
    hero.style.setProperty('--fz-portrait-bottom', `${g.bottom + 24}px`);
    hero.style.setProperty('--fz-card-max', g.compact ? '55svh' : '100%');
    const bubbleWidth = g.compact ? Math.min(300, W - 40) : Math.max(160, Math.min(300, g.faceLeft - 40));
    bubbleBox.style.width = `${bubbleWidth}px`;
    const bh = bubbleBox.offsetHeight;
    const left = g.compact ? (W - bubbleWidth) / 2 : Math.max(16, g.faceLeft - bubbleWidth - 24);
    const top = g.compact ? Math.max(headerH + 8, g.headTop - bh - 18) : Math.max(headerH + 16, g.top + .34 * g.height - bh * .6);
    bubbleBox.classList.toggle('is-left', !g.compact);
    bubbleBox.style.left = `${left}px`; bubbleBox.style.top = `${top}px`;
  }
  layout(); addEventListener('resize', layout);
  new ResizeObserver(layout).observe(bubbleBox);
  const header = document.querySelector('.site-header');
  const past = () => header.classList.toggle('is-past', hero.getBoundingClientRect().bottom <= header.offsetHeight + 1);
  addEventListener('scroll', past, { passive: true }); past();
  // Speech bubble: a short introduction; each topic gets a one-line reply.
  const bubble = hero.querySelector('[data-fz-bubble]');
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const INTRO = 'Hi, I’m Fan Zhang.';
  const REPLY = { research: 'My work: population dynamics, stock assessment and fisheries management.',
                  publications: 'Here are a few of my recent papers.',
                  education: 'I did my PhD in Integrative Biology at the University of Guelph.',
                  service: 'I’m China’s Chief Scientist at ICCAT and an associate editor of CJFAS.',
                  contact: 'Thinking of joining or visiting the lab? Email me.' };
  let typing = 0;
  function say(text) {
    const id = ++typing;
    if (still) { bubble.textContent = text; layout(); return; }
    let i = 0; bubble.textContent = '';
    const step = () => { if (id !== typing) return; bubble.textContent = text.slice(0, ++i); layout(); if (i < text.length) setTimeout(step, 24); };
    step();
  }
  setTimeout(() => say(INTRO), still ? 0 : 900);
  // Cards are built from the sections further down, so there is one source of truth.
  const q = s => document.querySelector(s);
  const clone = s => { const el = q(s); return el ? el.cloneNode(true) : null; };
  const link = (href, text) => { const a = document.createElement('a'); a.className = 'fz-card-more'; a.href = href; a.textContent = text + ' →'; return a; };
  const para = text => { const p = document.createElement('p'); p.textContent = text; return p; };
  const cards = {
    research: { kicker: 'Research', title: 'Populations, assessment & management', build: () => {
      const intro = q('.faculty-research-intro'); const out = [];
      if (intro) { out.push(para(intro.querySelector('p:not(.eyebrow)').textContent)); out.push(clone('.faculty-interests')); }
      out.push(link(q('.faculty-research-intro .text-link').getAttribute('href'), 'Explore the lab’s research')); return out; } },
    publications: { kicker: 'Publications', title: 'Selected papers', build: () => {
      const list = clone('.faculty-paper-list'); [...list.children].slice(3).forEach(li => li.remove());
      return [list, link(q('.faculty-work-heading a').getAttribute('href'), 'All publications')]; } },
    education: { kicker: 'Education', title: 'Academic training', build: () => [clone('.faculty-education-list')] },
    service: { kicker: 'Professional roles', title: 'Academic service', build: () => [clone('.faculty-role-list')] },
    contact: { kicker: 'Contact', title: 'Get in touch', build: () => {
      const a = document.createElement('a'); a.href = 'mailto:f-zhang@shou.edu.cn'; a.textContent = 'f-zhang@shou.edu.cn';
      const p = para('Graduate study, research visits and collaboration: '); p.append(a);
      return [p, clone('.faculty-profile-links'), link(q('.faculty-contact').getAttribute('href'), 'Contact & visits')]; } },
  };
  const layer = hero.querySelector('[data-fz-layer]'), card = hero.querySelector('[data-fz-card]');
  let opener = null;
  function open(key, from) {
    const c = cards[key]; if (!c) return;
    hero.querySelector('[data-fz-kicker]').textContent = c.kicker;
    hero.querySelector('[data-fz-title]').textContent = c.title;
    const body = hero.querySelector('[data-fz-body]'); body.replaceChildren(...c.build().filter(Boolean));
    body.querySelectorAll('[id]').forEach(el => el.removeAttribute('id'));
    opener = from || document.activeElement; layer.hidden = false; say(REPLY[key]);
    hero.querySelectorAll('[data-fz-open]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.fzOpen === key)));
    card.style.animation = 'none'; card.offsetWidth; card.style.animation = '';
    card.focus({ preventScroll: true });
  }
  function close() { if (layer.hidden) return; layer.hidden = true; say(INTRO); hero.querySelectorAll('[data-fz-open]').forEach(b => b.setAttribute('aria-pressed', 'false')); if (opener) opener.focus({ preventScroll: true }); }
  hero.querySelectorAll('[data-fz-open]').forEach(b => b.addEventListener('click', () => open(b.dataset.fzOpen, b)));
  hero.querySelector('[data-fz-close]').addEventListener('click', close);
  document.addEventListener('pointerdown', e => { if (!layer.hidden && !card.contains(e.target) && !e.target.closest('[data-fz-open], [data-fz-search]')) close(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !layer.hidden) close(); });
  // Search: match words to a topic; Enter opens it.
  const words = { research: ['research', 'population', 'dynamic', 'stock', 'assess', 'management', 'fish', 'tuna', 'model'],
                  publications: ['paper', 'publication', 'article', 'journal', 'doi', 'cite'],
                  education: ['education', 'phd', 'degree', 'guelph', 'ocean university', 'study', 'master', 'bachelor', 'training'],
                  service: ['iccat', 'editor', 'board', 'service', 'role', 'scientist', 'cjfas'],
                  contact: ['contact', 'email', 'mail', 'visit', 'join', 'student', 'collaborat'] };
  const input = hero.querySelector('[data-fz-input]'), chips = [...hero.querySelectorAll('[data-fz-open]')];
  const match = v => { v = v.toLowerCase().trim(); if (!v) return null;
    return Object.keys(words).find(k => words[k].some(w => v.includes(w) || w.startsWith(v))) || null; };
  input.addEventListener('input', () => { const m = match(input.value); chips.forEach(c => c.classList.toggle('is-match', c.dataset.fzOpen === m)); });
  hero.querySelector('[data-fz-search]').addEventListener('submit', e => { e.preventDefault(); open(match(input.value) || 'research', input); });
  // Rotating placeholder prompts.
  const prompts = ['Ask about research, publications, education…', 'Try “stock assessment”', 'Try “ICCAT”', 'Try “PhD at Guelph”'];
  let pi = 0; if (!still) setInterval(() => { if (document.activeElement !== input && !input.value) input.placeholder = prompts[pi = (pi + 1) % prompts.length]; }, 3200);
}
initFacultyHero();

document.querySelector('#copyright-year').textContent = new Date().getFullYear();
