import { CASES, R, F, calculateCell, copy, parseStudy, makeStudy } from './cell-state.js';

const element = (id) => document.getElementById(id);
const fields = [
  { id: 'c-left', key: 'cLeft', label: 'Left concentration' },
  { id: 'c-right', key: 'cRight', label: 'Right concentration' },
  { id: 'gamma-left', key: 'gammaLeft', label: 'Left activity coefficient' },
  { id: 'gamma-right', key: 'gammaRight', label: 'Right activity coefficient' },
];
let current = null;
let cases = [];
let revision = 0;
let importRequest = 0;
let originalContext = null;

function format(value, digits = 6) {
  if (value === null || !Number.isFinite(value)) return 'Outside displayed numeric range';
  if (value === 0) return '0';
  return Number(value.toPrecision(digits)).toString();
}

function signed(value) {
  return value > 0 ? `+${format(value)}` : format(value);
}

function setText(id, text) {
  const target = element(id);
  if (target) target.textContent = text;
}

function hideError() {
  element('form-error').hidden = true;
  element('form-error').replaceChildren();
}

function showError(message, includeOriginalLink = false) {
  const error = element('form-error');
  error.replaceChildren(document.createTextNode(message));
  if (includeOriginalLink) {
    const link = document.createElement('a');
    link.href = '../labs/electrochemistry.html#ec-experiment';
    link.textContent = 'Open the original Lab 13';
    error.append(document.createTextNode(' '), link);
  }
  error.hidden = false;
}

function clearFieldError(field) {
  element(field.id).removeAttribute('aria-invalid');
  const error = element(`error-${field.id}`);
  if (error) {
    error.textContent = '';
    error.hidden = true;
  }
}

function readValues() {
  const values = {};
  const invalid = [];
  for (const field of fields) {
    const input = element(field.id);
    const value = Number(input.value);
    clearFieldError(field);
    if (!input.value.trim() || !Number.isFinite(value) || value <= 0) {
      const message = `Enter a ${field.label.toLowerCase()} greater than zero.`;
      input.setAttribute('aria-invalid', 'true');
      const error = element(`error-${field.id}`);
      if (error) {
        error.textContent = message;
        error.hidden = false;
      }
      invalid.push(field);
    }
    values[field.key] = value;
  }
  if (invalid.length) {
    showError('Check the highlighted values, then calculate again.');
    const list = document.createElement('ul');
    for (const field of invalid) {
      const item = document.createElement('li');
      const link = document.createElement('a');
      link.href = `#${field.id}`;
      link.textContent = `${field.label}: enter a number greater than zero.`;
      link.addEventListener('click', (event) => {
        event.preventDefault();
        const input = element(field.id);
        input.closest('details')?.setAttribute('open', '');
        input.focus();
      });
      item.append(link);
      list.append(item);
    }
    element('form-error').append(list);
    const input = element(invalid[0].id);
    input.closest('details')?.setAttribute('open', '');
    input.focus();
    return null;
  }
  return values;
}

function invalidate(message = 'Inputs changed. Predict the sign and calculate this case.') {
  revision += 1;
  current = null;
  element('results').hidden = true;
  element('result-placeholder').hidden = false;
  element('result-placeholder').textContent = message;
  element('save-case').disabled = true;
  element('export-study').disabled = true;
  setText('cell-direction', 'Calculate to see the direction of metal transfer.');
  setText('activity-left', '—');
  setText('activity-right', '—');
  hideError();
}

function loadValues(values) {
  for (const field of fields) {
    element(field.id).value = values[field.key];
    clearFieldError(field);
  }
}

function loadCase(key) {
  const selected = CASES[key];
  if (!selected) return;
  loadValues(selected);
  element('case-name').value = selected.name;
  element('prediction').value = '';
  originalContext = null;
  invalidate('Starting values loaded. Predict the sign, then calculate.');
  for (const button of document.querySelectorAll('[data-case]')) {
    button.setAttribute('aria-pressed', String(button.dataset.case === key));
  }
  setText('status', `${selected.name} loaded. Saved comparisons and your explanation are retained.`);
}

function signOf(value) {
  if (Math.abs(value) < 1e-10) return 'zero';
  return value > 0 ? 'positive' : 'negative';
}

function renderResult() {
  const { result, values, prediction } = current;
  setText('result-E', signed(result.E));
  setText('result-Q', format(result.Q));
  setText('result-K', format(result.K));
  setText('result-dG', signed(result.deltaG / 1000));
  const leftActivity = result.net.find((item) => item.compartment === 'L' && item.name === 'M2+');
  const rightActivity = result.net.find((item) => item.compartment === 'R' && item.name === 'M2+');
  setText('activity-left', format(Math.exp(leftActivity.lnActivity)));
  setText('activity-right', format(Math.exp(rightActivity.lnActivity)));

  const sign = signOf(result.E);
  const directions = {
    positive: ['Q < K. The written reaction is favored: metal dissolves on the left and deposits on the right.', 'Metal dissolves on the left → metal deposits on the right.'],
    negative: ['Q > K. The reverse reaction is favored: metal dissolves on the right and deposits on the left.', 'Metal dissolves on the right → metal deposits on the left.'],
    zero: ['Q = K. The complete cell reaction is at equilibrium within numerical tolerance.', 'Equal activities give no net metal transfer at cell equilibrium.'],
  };
  setText('result-direction', directions[sign][0]);
  setText('cell-direction', directions[sign][1]);
  const feedback = element('prediction-feedback');
  feedback.hidden = !prediction;
  if (prediction) {
    feedback.textContent = prediction === sign
      ? `Your ${prediction} prediction matches the calculated potential.`
      : `You predicted ${prediction}. The calculated potential is ${sign}; compare Q with K to explain the sign.`;
  }

  const coefficient = R * result.input.T / (result.n * F);
  const gibbsCheck = R * result.input.T * (result.lnQ - result.lnK);
  const steps = [
    `Left activity: aL = γL cL/c° = ${format(values.gammaLeft)} × ${format(values.cLeft)}/1 = ${format(Math.exp(leftActivity.lnActivity))}.`,
    `Right activity: aR = γR cR/c° = ${format(values.gammaRight)} × ${format(values.cRight)}/1 = ${format(Math.exp(rightActivity.lnActivity))}.`,
    `For left oxidation and right reduction, Q = aL/aR = ${format(result.Q)}. The identical standard couples give E°cell = 0 V and K = 1.`,
    `Nernst equation: E = −(RT/nF) ln Q = −${format(coefficient)} × (${format(result.lnQ)}) = ${signed(result.E)} V.`,
    `Independent Gibbs-energy check: RT ln(Q/K) = ${format(R, 8)} × ${format(result.input.T)} × (${format(result.lnQ)} − ${format(result.lnK)}) = ${signed(gibbsCheck)} J/mol = ${signed(gibbsCheck / 1000)} kJ/mol. Compare with ΔrG = −nFE above.`,
  ];
  element('calc-steps').replaceChildren(...steps.map((text) => {
    const item = document.createElement('li');
    item.textContent = text;
    return item;
  }));
  element('results').hidden = false;
  element('result-placeholder').hidden = true;
  element('save-case').disabled = false;
  element('export-study').disabled = false;
}

function calculate() {
  hideError();
  const values = readValues();
  if (!values) return;
  try {
    current = {
      name: element('case-name').value.trim() || 'Custom case',
      values: copy(values),
      prediction: element('prediction').value,
      result: calculateCell(values),
    };
    renderResult();
    setText('status', `Calculated E = ${signed(current.result.E)} V. ${element('result-direction').textContent} You can add this result to the comparison.`);
    if (element('results').getBoundingClientRect().top >= window.innerHeight) {
      const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      element('results').scrollIntoView({ block: 'start', behavior: reducedMotion ? 'auto' : 'smooth' });
    }
  } catch (error) {
    invalidate('Correct the values and calculate again.');
    showError(error.message);
  }
}

function renderComparisons() {
  const rows = cases.map((saved, index) => {
    const row = document.createElement('tr');
    const cells = [saved.name, saved.values.cLeft, saved.values.cRight, saved.values.gammaLeft,
      saved.values.gammaRight, saved.result.Q, saved.result.E, saved.result.deltaG / 1000];
    cells.forEach((value, column) => {
      const cell = document.createElement('td');
      cell.textContent = column === 0 ? value : format(value);
      row.append(cell);
    });
    const action = document.createElement('td');
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Load case';
    button.setAttribute('aria-label', `Load ${saved.name}, comparison ${index + 1}`);
    button.addEventListener('click', () => {
      loadValues(saved.values);
      element('case-name').value = saved.name;
      element('prediction').value = saved.prediction;
      invalidate('Saved inputs loaded. Calculate to reproduce this comparison.');
      for (const preset of document.querySelectorAll('[data-case]')) preset.setAttribute('aria-pressed', 'false');
      setText('status', `${saved.name} inputs loaded. Calculate to check the stored result.`);
      element('calculate').focus();
    });
    action.append(button);
    row.append(action);
    return row;
  });
  element('comparison-body').replaceChildren(...rows);
  element('comparison-empty').hidden = cases.length > 0;
  const wrapper = element('comparison-table-wrap');
  if (wrapper) wrapper.hidden = cases.length === 0;
}

function saveCase() {
  if (!current) return;
  current.name = element('case-name').value.trim() || 'Custom case';
  cases.push(copy(current));
  revision += 1;
  renderComparisons();
  setText('status', `${current.name} saved. ${cases.length} comparison ${cases.length === 1 ? 'case' : 'cases'} in this study.`);
}

function downloadStudy() {
  if (!current) return;
  current.name = element('case-name').value.trim() || 'Custom case';
  const reflection = element('reflection')?.value || '';
  const study = makeStudy(current, cases, reflection, originalContext);
  const url = URL.createObjectURL(new Blob([JSON.stringify(study, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'thermodynamics-lab13-2027-study.json';
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  setText('status', 'Study downloaded with the current calculation, saved comparisons and your explanation.');
}

async function openStudy(event) {
  const file = event.target.files[0];
  if (!file) return;
  const request = ++importRequest;
  const startedAt = revision;
  hideError();
  try {
    const opened = parseStudy(await file.text());
    if (request !== importRequest) return;
    if (revision !== startedAt) {
      throw new Error('The study changed while the file was opening. Choose the file again to restore it.');
    }
    loadValues(opened.values);
    element('case-name').value = opened.name;
    element('prediction').value = opened.prediction;
    if (element('reflection')) element('reflection').value = opened.reflection;
    cases = opened.cases;
    originalContext = opened.originalContext;
    current = {
      name: opened.name,
      prediction: opened.prediction,
      values: copy(opened.values),
      result: opened.result,
    };
    revision += 1;
    for (const preset of document.querySelectorAll('[data-case]')) preset.setAttribute('aria-pressed', 'false');
    renderComparisons();
    renderResult();
    setText('status', `Study opened and recalculated. ${cases.length} saved comparison ${cases.length === 1 ? 'case' : 'cases'} restored.`);
  } catch (error) {
    if (request === importRequest) {
      showError(`Could not open this study. ${error.message}`, error.message.includes('original Lab 13'));
      setText('status', 'The current study has been retained.');
    }
  } finally {
    if (request === importRequest) event.target.value = '';
  }
}

for (const button of document.querySelectorAll('[data-case]')) {
  button.addEventListener('click', () => loadCase(button.dataset.case));
}
const restore = element('restore-baseline');
if (restore && !restore.dataset.case) restore.addEventListener('click', () => loadCase('baseline'));
for (const field of fields) {
  element(field.id).addEventListener('input', () => {
    clearFieldError(field);
    if (Object.values(CASES).some((preset) => preset.name === element('case-name').value)) {
      element('case-name').value = 'Custom case';
    }
    element('prediction').value = '';
    for (const preset of document.querySelectorAll('[data-case]')) preset.setAttribute('aria-pressed', 'false');
    invalidate();
  });
}
element('prediction').addEventListener('change', () => invalidate('Prediction recorded. Calculate to compare it with the cell potential.'));
for (const id of ['case-name', 'reflection']) {
  element(id)?.addEventListener('input', () => { revision += 1; });
}
element('calculate').addEventListener('click', calculate);
element('cell-form').addEventListener('submit', (event) => {
  event.preventDefault();
  calculate();
});
element('cell-form').addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && event.target.matches('input[type="number"]')) {
    event.preventDefault();
    calculate();
  }
});
element('save-case').addEventListener('click', saveCase);
element('export-study').addEventListener('click', downloadStudy);
element('import-study').addEventListener('change', openStudy);
loadCase('baseline');
renderComparisons();
