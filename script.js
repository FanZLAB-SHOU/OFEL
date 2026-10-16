const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#main-nav');

function setMenu(open) {
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
  navigation.classList.toggle('is-open', open);
}

menuButton.addEventListener('click', () => {
  setMenu(menuButton.getAttribute('aria-expanded') !== 'true');
});
navigation.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => setMenu(false));
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
    setMenu(false);
    menuButton.focus();
  }
});
document.addEventListener('click', event => {
  if (!event.target.closest('.site-header')) setMenu(false);
});
window.matchMedia('(min-width: 701px)').addEventListener('change', event => {
  if (event.matches) setMenu(false);
});

const filters = document.querySelectorAll('.filter-button');
const papers = [...document.querySelectorAll('.publication')];
const count = document.querySelector('.publication-count');
const expandContainer = document.querySelector('.publication-expand');
const expandButton = document.querySelector('#publication-toggle');
const previewCount = 6;
let selectedTopic = 'all';
let expanded = false;

function renderPublications() {
  const matching = papers.filter(paper => selectedTopic === 'all' || paper.dataset.topics.split(' ').includes(selectedTopic));
  const limited = selectedTopic === 'all' && !expanded;
  papers.forEach(paper => { paper.hidden = true; });
  matching.forEach((paper, index) => { paper.hidden = limited && index >= previewCount; });
  const visible = limited ? Math.min(previewCount, matching.length) : matching.length;
  count.textContent = visible < matching.length
    ? `Showing ${visible} of ${matching.length} publications`
    : `${visible} publication${visible === 1 ? '' : 's'}`;
  expandContainer.hidden = selectedTopic !== 'all' || matching.length <= previewCount;
  expandButton.setAttribute('aria-expanded', String(expanded));
  expandButton.textContent = expanded ? 'Show recent publications ↑' : `Show all ${papers.length} publications ↓`;
}

filters.forEach(button => {
  button.addEventListener('click', () => {
    selectedTopic = button.dataset.filter;
    expanded = false;
    filters.forEach(filter => {
      const selected = filter === button;
      filter.classList.toggle('is-active', selected);
      filter.setAttribute('aria-pressed', String(selected));
    });
    renderPublications();
  });
});
expandButton.addEventListener('click', () => {
  expanded = !expanded;
  renderPublications();
  if (!expanded) document.querySelector('#publications-title').scrollIntoView();
});
renderPublications();

if ('IntersectionObserver' in window) {
  const links = [...navigation.querySelectorAll('a')];
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      links.forEach(link => {
        if (link.hash === `#${entry.target.id}`) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    });
  }, { rootMargin: '-15% 0px -55% 0px', threshold: 0 });
  document.querySelectorAll('main > section[id]').forEach(section => observer.observe(section));
}

document.querySelector('#copyright-year').textContent = new Date().getFullYear();
