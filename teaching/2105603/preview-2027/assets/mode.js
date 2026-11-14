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

/** Concept questions: the explanation opens after the student has written an answer. */
const MIN_ANSWER = 30;
export function gateConceptAnswers() {
  for (const q of document.querySelectorAll('.concept-question')) {
    const text = q.querySelector('textarea'), details = q.querySelector('details'), summary = details?.querySelector('summary');
    if (!text || !summary || details.dataset.gated) continue;
    details.dataset.gated = 'true';
    const hint = document.createElement('p'); hint.className = 'concept-gate'; hint.setAttribute('role', 'status');
    details.after(hint);
    summary.addEventListener('click', event => {
      if (details.open) { hint.textContent = ''; return; }
      if (text.value.trim().length < MIN_ANSWER) {
        event.preventDefault();
        hint.textContent = 'Write your own answer first (at least one full sentence), then compare with the explanation.';
        text.focus();
      } else hint.textContent = '';
    });
    text.addEventListener('input', () => { if (text.value.trim().length >= MIN_ANSWER) hint.textContent = ''; });
  }
}

initMode();
gateConceptAnswers();
