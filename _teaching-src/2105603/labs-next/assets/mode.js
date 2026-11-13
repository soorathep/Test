/** Core / Graduate view switch shared by the 2027 labs.
 * Core shows the concept route; Graduate adds the investigation section.
 * The choice is kept in the URL (?mode=graduate) and, when allowed, in localStorage. */
const KEY = 'skh-thermo-2027-mode';
const MODES = ['core', 'graduate'];

function stored() {
  try { return localStorage.getItem(KEY); } catch { return null; }
}
function store(mode) {
  try { localStorage.setItem(KEY, mode); } catch { /* private mode: the URL still carries the choice */ }
}

export function currentMode() { return document.body.dataset.mode || 'core'; }

export function applyMode(mode, { remember = true } = {}) {
  if (!MODES.includes(mode)) mode = 'core';
  document.body.dataset.mode = mode;
  for (const input of document.querySelectorAll('input[name="lab-mode"]')) input.checked = input.value === mode;
  const url = new URL(location.href);
  if (mode === 'graduate') url.searchParams.set('mode', 'graduate'); else url.searchParams.delete('mode');
  history.replaceState(history.state, '', url);
  if (remember) store(mode);
  document.dispatchEvent(new CustomEvent('labmodechange', { detail: { mode } }));
}

export function initMode() {
  const fromUrl = new URLSearchParams(location.search).get('mode');
  applyMode(MODES.includes(fromUrl) ? fromUrl : MODES.includes(stored()) ? stored() : 'core', { remember: MODES.includes(fromUrl) });
  for (const input of document.querySelectorAll('input[name="lab-mode"]')) {
    input.addEventListener('change', () => { if (input.checked) applyMode(input.value); });
  }
  for (const link of document.querySelectorAll('[data-show-mode]')) {
    link.addEventListener('click', () => applyMode(link.dataset.showMode));
  }
}

initMode();
