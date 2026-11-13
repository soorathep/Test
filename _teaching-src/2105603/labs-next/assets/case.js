import {
  DEFAULT_INPUTS, copy, validateData, normalizeInputs, observation, analyze,
  fitStudy, makeStudy, parseStudy,
} from './case-state.js?v=graduate-1';
import { palette } from '../../labs/assets/palette.js';
import { normalizeGraduateCase, analyzeGraduateCase, observationSensitivity, alphaSensitivity } from './case-graduate.js';

const element = (id) => document.getElementById(id);
let data;
let current = null;
let retainedFit = null;
let cases = [];
let revision = 0;
let importRequest = 0;
let plotRevision = 0;
let busy = false;
let manualCaseName = false;
let importedPrediction = '';
let graduate = normalizeGraduateCase();
let graduateAnalysis = { sensitivity: null, alpha: null };

function text(id, value) {
  if (element(id)) element(id).textContent = value;
}

const MATH_NS = 'http://www.w3.org/1998/Math/MathML';
const notation = {
  'P₁sat': ['P', '1', 'sat'], 'P₂sat': ['P', '2', 'sat'], 'Pᵢsat': ['P', 'i', 'sat'],
  Psat: ['P', null, 'sat'],
  'τ₁₂': ['τ', '12'], 'τ₂₁': ['τ', '21'], 'τᵢⱼ': ['τ', 'ij'],
  'a₁₂': ['a', '12'], 'a₂₁': ['a', '21'], 'aᵢⱼ': ['a', 'ij'],
  'b₁₂': ['b', '12'], 'b₂₁': ['b', '21'], 'bᵢⱼ': ['b', 'ij'],
  'γ₁': ['γ', '1'], 'γ₂': ['γ', '2'], 'γᵢ': ['γ', 'i'],
  'x₁': ['x', '1'], 'x₂': ['x', '2'], 'xᵢ': ['x', 'i'],
  'y₁': ['y', '1'], 'y₂': ['y', '2'], 'yᵢ': ['y', 'i'],
  'r₁': ['r', '1'], 'r₂': ['r', '2'], 'rᵢ': ['r', 'i'],
};
const notationPattern = new RegExp(Object.keys(notation).sort((a, b) => b.length - a.length).join('|'), 'gu');

function mathNode(tag, ...children) {
  const node = document.createElementNS(MATH_NS, tag);
  for (const child of children) node.append(typeof child === 'string' ? document.createTextNode(child) : child);
  return node;
}

function scriptToken(value) {
  const [base, subscript, superscript] = notation[value];
  const symbol = mathNode('mi', base);
  const sub = subscript ? mathNode(/^\d+$/.test(subscript) ? 'mn' : 'mi', subscript) : null;
  const sup = superscript ? mathNode('mi', superscript) : null;
  if (sup) sup.setAttribute('mathvariant', 'normal');
  const body = sub && sup ? mathNode('msubsup', symbol, sub, sup)
    : sub ? mathNode('msub', symbol, sub) : mathNode('msup', symbol, sup);
  const math = mathNode('math', body);
  math.classList.add('inline-math');
  math.setAttribute('aria-label', base + (subscript ? ' subscript ' + subscript : '')
    + (superscript ? ' superscript ' + superscript : ''));
  return math;
}

/** Recognize only fixed scientific tokens. All file-supplied text remains text. */
function mathText(target, value) {
  const node = typeof target === 'string' ? element(target) : target;
  if (!node) return;
  const source = String(value);
  const fragment = document.createDocumentFragment();
  let cursor = 0;
  notationPattern.lastIndex = 0;
  for (const match of source.matchAll(notationPattern)) {
    fragment.append(document.createTextNode(source.slice(cursor, match.index)), scriptToken(match[0]));
    cursor = match.index + match[0].length;
  }
  fragment.append(document.createTextNode(source.slice(cursor)));
  node.replaceChildren(fragment);
}

function antoineEquation() {
  const upright = (value) => {
    const node = mathNode('mi', value);
    node.setAttribute('mathvariant', 'normal');
    return node;
  };
  const pressure = mathNode('msup', mathNode('mi', 'P'), upright('sat'));
  const math = mathNode('math', mathNode('mrow',
    mathNode('msub', upright('log'), mathNode('mn', '10')),
    mathNode('mo', '('), mathNode('mfrac', pressure, upright('bar')), mathNode('mo', ')'),
    mathNode('mo', '='), mathNode('mi', 'A'), mathNode('mo', '−'),
    mathNode('mfrac', mathNode('mi', 'B'), mathNode('mrow', mathNode('mi', 'T'), mathNode('mo', '+'), mathNode('mi', 'C')))));
  math.setAttribute('display', 'block');
  math.classList.add('display-math');
  math.setAttribute('aria-label', 'Base ten logarithm of saturation pressure in bar equals A minus B divided by the quantity T plus C.');
  const wrapper = document.createElement('div');
  wrapper.className = 'math-scroll';
  wrapper.tabIndex = 0;
  wrapper.append(math);
  return wrapper;
}

function show(id, visible) {
  if (element(id)) element(id).hidden = !visible;
}

function format(value, digits = 6) {
  if (value === null || !Number.isFinite(value)) return 'Not available';
  if (value === 0) return '0';
  return Number(value.toPrecision(digits)).toString();
}

function optionLabel(id) {
  return element(id)?.selectedOptions?.[0]?.textContent || '';
}

function answers() {
  return Object.fromEntries(['psat1', 'psat2', 'gamma1', 'gamma2'].map((key) => (
    [key, element('answer-' + key)?.value || '']
  )));
}

function writeAnswers(values = {}) {
  for (const key of ['psat1', 'psat2', 'gamma1', 'gamma2']) {
    if (element('answer-' + key)) element('answer-' + key).value = values[key] || '';
  }
  text('answer-feedback', '');
}

function graduateNotes() {
  return Object.fromEntries(['assumptions', 'uncertainty', 'evidence', 'decision'].map((key) =>
    [key, element('g2-note-' + key)?.value || '']));
}

function readGraduate() {
  const candidate = copy(graduate);
  candidate.notes = graduateNotes();
  for (const key of ['T', 'P', 'x', 'y']) {
    const field = element('g2-bound-' + key);
    const source = field.value.trim();
    const value = Number(source);
    field.removeAttribute('aria-invalid');
    if (!source || !Number.isFinite(value) || value < 0 || value > Number(field.max)) {
      field.setAttribute('aria-invalid', 'true');
      const issue = new Error('Enter an assumed ' + key + ' bound from 0 to ' + field.max
        + ' in the stated unit.');
      issue.field = field;
      throw issue;
    }
    candidate.bounds[key] = value;
  }
  return normalizeGraduateCase(candidate);
}

function graduateSnapshot() {
  return normalizeGraduateCase({ ...graduate, notes: graduateNotes() });
}

function clearGraduate(sensitivity = true, alpha = true, message = '') {
  graduate.notes = graduateNotes();
  if (sensitivity) {
    graduate.run.sensitivity = false;
    graduateAnalysis.sensitivity = null;
    show('g2-sensitivity-results', false);
    text('g2-sensitivity-status', message || 'Observation or assumptions changed. Run the scenarios again before interpreting their ranges.');
  }
  if (alpha) {
    graduate.run.alpha = false;
    graduateAnalysis.alpha = null;
    show('g2-alpha-results', false);
    text('g2-alpha-status', message || 'Fitting or checking context changed. Run the conditional alpha comparison again.');
  }
}

function graduateRows(id, rows) {
  element(id).replaceChildren(...rows.map((values) => {
    const row = document.createElement('tr');
    values.forEach((value) => {
      const cell = document.createElement('td');
      if (typeof value === 'number') cell.textContent = format(value, 7);
      else mathText(cell, value === null || value === undefined ? 'Unavailable' : value);
      row.append(cell);
    });
    return row;
  }));
}

function renderGraduate() {
  const set = data?.datasets.find((item) => item.pressureKPa === Number(element('dataset').value));
  if (set) {
    const uncertainty = set.averageExpandedUncertainty;
    text('g2-paper-uncertainty', 'Article reference at ' + set.pressureKPa + ' kPa: average expanded uncertainties U(T) = '
      + uncertainty.T + ' K, U(P) = ' + uncertainty.PkPa + ' kPa, U(x) = ' + uncertainty.x
      + ' and U(y) = ' + uncertainty.y + ', with coverage factor k = ' + set.coverageFactor
      + '. These dataset averages are not independent pointwise standard deviations. They do not provide the covariance needed for automatic statistical weights.');
  }
  const sensitivity = graduateAnalysis.sensitivity;
  show('g2-sensitivity-results', !!sensitivity);
  if (sensitivity) {
    const counts = sensitivity.counts;
    text('g2-sensitivity-status', counts.valid + ' of ' + counts.attempted
      + ' joint corners supplied finite activity pairs; ' + counts.unavailable
      + ' were unavailable and ' + counts.failed + ' failed. All 8 one-factor scenarios were attempted.');
    const row = sensitivity.context.row;
    text('g2-sensitivity-context', 'Inspected control: ' + sensitivity.context.inspect + ' kPa, row '
      + (sensitivity.context.selectedRow + 1) + ', T = ' + row.T + ' K, x = ' + row.x + ', y = ' + row.y
      + '. Source observations and Antoine constants are unchanged. The figures below summarize accepted sampled corners only.');
    graduateRows('g2-range-body', [
      ['γ₁', sensitivity.baseline.gamma[0], sensitivity.ranges.gamma[0]?.min, sensitivity.ranges.gamma[0]?.max],
      ['γ₂', sensitivity.baseline.gamma[1], sensitivity.ranges.gamma[1]?.min, sensitivity.ranges.gamma[1]?.max],
      ['ln γ₁', sensitivity.baseline.ln[0], sensitivity.ranges.ln[0]?.min, sensitivity.ranges.ln[0]?.max],
      ['ln γ₂', sensitivity.baseline.ln[1], sensitivity.ranges.ln[1]?.min, sensitivity.ranges.ln[1]?.max],
    ]);
    const names = { T: 'Temperature T', P: 'Pressure P', x: 'Liquid composition x₁', y: 'Vapor composition y₁' };
    graduateRows('g2-oat-body', sensitivity.ranking.map((item) => [names[item.factor],
      item.valid + ' / ' + item.attempted, item.maxAbsDeltaLn?.[0], item.maxAbsDeltaLn?.[1]]));
    graduateRows('g2-corner-body', [...sensitivity.oneAtATime, ...sensitivity.corners].map((item) => [item.name, item.row.T,
      item.row.PkPa, item.row.x, item.row.y, item.ln?.[0], item.ln?.[1],
      item.status === 'valid' ? 'Accepted scenario' : item.status + ': ' + item.reason]));
  }
  const alpha = graduateAnalysis.alpha;
  show('g2-alpha-results', !!alpha);
  if (alpha) {
    const training = alpha.context.pressures.map((pressure) => pressure + ' kPa').join(' + ');
    text('g2-alpha-status', alpha.rows.filter((row) => row.status === 'valid').length
      + ' of 3 conditional fits completed. The retained model and original measurements are unchanged.');
    text('g2-alpha-context', 'Training observations: ' + training + '. Checking pressure: '
      + alpha.context.evaluate + ' kPa. ' + (alpha.heldOut
        ? 'This pressure was excluded from each two-parameter fit. If used to choose alpha, it becomes model-selection data and is not an untouched final test.'
        : 'This pressure was included in training; these checking errors are in-sample agreement, not held-out validation.'));
    graduateRows('g2-alpha-body', alpha.rows.map((row) => row.status !== 'valid'
      ? [row.alpha, null, null, null, null, 'No', null, null, row.reason]
      : [row.alpha, row.tau12, row.tau21, row.trainingRMSE, row.checkingRMSE,
        row.converged ? 'Yes' : 'No', row.atBound ? 'Yes' : 'No', row.minSampledScaledCurvature,
        row.minSampledScaledCurvature <= 0
          ? 'Nonpositive sampled curvature at 350 K; homogeneous model candidates may be unstable. Investigate Lab 04.'
          : 'Positive on the sampled grid at 350 K; not a global stability proof.']));
  }
}

function restoreGraduate(saved, analysis, inputs) {
  graduate = normalizeGraduateCase(saved);
  for (const key of ['T', 'P', 'x', 'y']) {
    element('g2-bound-' + key).value = graduate.bounds[key];
    element('g2-bound-' + key).removeAttribute('aria-invalid');
  }
  for (const [key, value] of Object.entries(graduate.notes)) element('g2-note-' + key).value = value;
  graduateAnalysis = analysis || analyzeGraduateCase(data, inputs || readInputs(), graduate);
  renderGraduate();
  if (!graduateAnalysis.sensitivity) text('g2-sensitivity-status', 'Choose a valid interior observation and run the scenario analysis.');
  if (!graduateAnalysis.alpha) text('g2-alpha-status', 'Establish the baseline model, then compare three conditional fits.');
}

function runGraduateSensitivity() {
  clearError();
  try {
    const inputs = readInputs();
    if (!inputs) return;
    const candidate = readGraduate();
    const sensitivity = observationSensitivity(data, inputs, candidate);
    graduate = candidate;
    graduate.run.sensitivity = true;
    graduateAnalysis.sensitivity = sensitivity;
    revision += 1;
    renderGraduate();
    text('status', 'Graduate observation sensitivity recalculated. Download the study after completing your defended conclusion.');
  } catch (issue) {
    clearGraduate(true, false);
    text('g2-sensitivity-status', issue.message);
    issue.field?.focus();
  }
}

async function runGraduateAlpha() {
  if (busy) return;
  clearError();
  const inputs = readInputs();
  if (!inputs) return;
  if (!current) {
    text('g2-alpha-status', 'Establish a baseline model in Step 3 before comparing the three conditional fits.');
    element('fit-button').focus();
    return;
  }
  const started = revision;
  busy = true;
  element('g2-run-alpha').disabled = true;
  text('g2-alpha-status', 'Fitting three alpha assumptions to the same training observations…');
  await new Promise((resolve) => requestAnimationFrame(resolve));
  try {
    if (started !== revision) return;
    const candidate = readGraduate();
    const alpha = alphaSensitivity(data, inputs);
    if (started !== revision) return;
    graduate = candidate;
    graduate.run.alpha = true;
    graduateAnalysis.alpha = alpha;
    revision += 1;
    renderGraduate();
    text('status', 'Three conditional alpha fits completed without replacing the retained model.');
  } catch (issue) {
    clearGraduate(false, true);
    text('g2-alpha-status', issue.message);
    issue.field?.focus();
  } finally {
    busy = false;
    element('g2-run-alpha').disabled = false;
  }
}

function clearError() {
  element('form-error').replaceChildren();
  element('form-error').hidden = true;
  element('alpha').removeAttribute('aria-invalid');
  show('error-alpha', false);
}

function error(message) {
  const box = element('form-error');
  box.replaceChildren(document.createTextNode(message));
  if (message.includes('original Lab 02')) {
    const link = document.createElement('a');
    link.href = '../labs/case-study.html#case-experiment';
    link.textContent = 'Open the original Lab 02';
    box.append(document.createTextNode(' '), link);
  }
  box.hidden = false;
  box.focus();
}

function readInputs() {
  clearError();
  const alphaText = element('alpha').value.trim();
  const alpha = Number(alphaText);
  if (!alphaText || !Number.isFinite(alpha) || alpha < 0.1 || alpha > 0.6) {
    const message = 'Enter a dimensionless α from 0.1 to 0.6.';
    element('alpha').setAttribute('aria-invalid', 'true');
    text('error-alpha', message);
    show('error-alpha', true);
    error(message);
    element('alpha').closest('details')?.setAttribute('open', '');
    element('alpha').focus();
    return null;
  }
  try {
    return normalizeInputs({
      inspect: Number(element('dataset').value),
      selectedRow: Number(element('observation').value),
      train: element('training-pressure').value,
      evaluate: Number(element('evaluation-pressure').value),
      alpha,
      model: element('case-model').value,
      chart: element('case-chart').value,
    }, data);
  } catch (issue) {
    error(issue.message);
    return null;
  }
}

function setObservationOptions(pressure, selected = 6) {
  const dataset = data.datasets.find((set) => set.pressureKPa === Number(pressure));
  if (!dataset) throw new Error('Choose one of the supplied experimental pressures.');
  element('observation').replaceChildren(...dataset.rows.map((row, index) => (
    new Option('Row ' + (index + 1) + ' · liquid fraction = ' + format(row.x, 5), String(index))
  )));
  element('observation').value = String(Math.min(Math.max(0, selected), dataset.rows.length - 1));
}

function writeInputs(input) {
  element('dataset').value = String(input.inspect);
  setObservationOptions(input.inspect, input.selectedRow);
  element('training-pressure').value = input.train;
  element('evaluation-pressure').value = String(input.evaluate);
  element('alpha').value = input.alpha;
  element('case-model').value = input.model;
  element('case-chart').value = input.chart;
}

function inspect() {
  return observation(data, Number(element('dataset').value), Number(element('observation').value));
}

function renderPropertyRecords() {
  const container = element('property-records');
  if (!container) return;
  container.replaceChildren(...data.properties.map((property) => {
    const section = document.createElement('article');
    const heading = document.createElement('h4');
    heading.textContent = property.name;
    const equation = document.createElement('div');
    equation.className = 'property-equation';
    equation.append(antoineEquation());
    const constants = document.createElement('p');
    constants.textContent = 'A = ' + format(property.A, 12) + ', B = '
      + format(property.B, 12) + ', C = ' + format(property.C, 12) + '.';
    const units = document.createElement('p');
    mathText(units, 'Use T in K. The equation returns Psat in bar; multiply by 100 for kPa. Valid from '
      + property.rangeK.join(' to ') + ' K.');
    section.append(heading, equation, constants, units);
    if (typeof property.source === 'string' && /^https?:\/\//i.test(property.source)) {
      const link = document.createElement('a');
      link.href = property.source;
      link.textContent = 'NIST source · ' + property.name;
      section.append(link);
    }
    return section;
  }));
  const sourceNote = element('source-note');
  if (sourceNote) {
    sourceNote.replaceChildren(document.createTextNode(data.title
      + '. Numerical observations from Tables 4 and 5. Component 1 is '
      + data.components[0] + '; component 2 is ' + data.components[1] + '. '));
    if (typeof data.source === 'string' && /^https?:\/\//i.test(data.source)) {
      const link = document.createElement('a');
      link.href = data.source;
      link.textContent = 'Read the article';
      sourceNote.append(link);
    }
  }
}

function renderObservation() {
  const selected = inspect();
  const { row } = selected;
  text('obs-T', format(row.T, 7));
  text('obs-P', format(row.PkPa));
  text('obs-x', format(row.x));
  text('obs-y', format(row.y));
  text('psat1-value', selected.psat ? format(selected.psat[0]) : 'Not available');
  text('psat2-value', selected.psat ? format(selected.psat[1]) : 'Not available');
  text('gamma1-value', selected.gamma ? format(selected.gamma[0]) : 'Not inferred');
  text('gamma2-value', selected.gamma ? format(selected.gamma[1]) : 'Not inferred');
  text('exclusion-note', selected.reason || 'This observation supplies both inferred log-activity values.');
  const all = data.datasets.find((set) => set.pressureKPa === Number(element('dataset').value));
  text('observation-count', all.rows.length + ' reported observations at ' + all.pressureKPa + ' kPa.');
  const rows = all.rows.map((item, index) => observation(data, all.pressureKPa, index));
  if (element('observations-body')) {
    element('observations-body').replaceChildren(...rows.map((item, index) => {
      const tr = document.createElement('tr');
      if (index === selected.rowIndex) tr.setAttribute('aria-current', 'true');
      for (const value of [index + 1, item.row.PkPa, item.row.T, item.row.x, item.row.y,
        item.reason || 'Included']) {
        const cell = document.createElement('td');
        cell.textContent = typeof value === 'number' ? format(value, 7) : value;
        tr.append(cell);
      }
      return tr;
    }));
  }
  const steps = selected.ln && selected.psat ? [
    'Read row ' + (selected.rowIndex + 1) + ' at ' + format(row.PkPa) + ' kPa: T = '
      + format(row.T) + ' K, x₁ = ' + format(row.x) + ', y₁ = ' + format(row.y) + '.',
    'Use each Antoine equation at this measured T. Convert bar to kPa: P₁sat = '
      + format(selected.psat[0]) + ' kPa and P₂sat = ' + format(selected.psat[1]) + ' kPa.',
    'With ideal vapor and negligible pressure corrections, γ₁ = y₁P/(x₁P₁sat) = ('
      + format(row.y) + ' × ' + format(row.PkPa) + ')/('
      + format(row.x) + ' × ' + format(selected.psat[0]) + ') = '
      + format(selected.gamma[0]) + '.',
    'For component 2, x₂ = ' + format(1 - row.x) + ' and y₂ = ' + format(1 - row.y)
      + '. Then γ₂ = y₂P/(x₂P₂sat) = ' + format(selected.gamma[1]) + '.',
    'Take natural logarithms for fitting: ln γ₁ = ' + format(selected.ln[0])
      + ' and ln γ₂ = ' + format(selected.ln[1]) + '. Both are dimensionless.',
  ] : [selected.reason || 'The selected row cannot supply a usable pair of log-activity values.'];
  if (element('observation-steps')) {
    element('observation-steps').replaceChildren(...steps.map((step) => {
      const li = document.createElement('li');
      mathText(li, step);
      return li;
    }));
  }
}

function checkObservation() {
  const selected = inspect();
  const expected = {
    psat1: selected.psat?.[0], psat2: selected.psat?.[1],
    gamma1: selected.gamma?.[0], gamma2: selected.gamma?.[1],
  };
  const labels = { psat1: 'P₁sat', psat2: 'P₂sat', gamma1: 'γ₁', gamma2: 'γ₂' };
  const messages = [];
  let supplied = 0;
  let invalid = null;
  for (const [key, source] of Object.entries(answers())) {
    const field = element('answer-' + key);
    field?.removeAttribute('aria-invalid');
    if (!source.trim()) continue;
    supplied += 1;
    const value = Number(source);
    if (!Number.isFinite(value) || value <= 0) {
      field?.setAttribute('aria-invalid', 'true');
      invalid ||= field;
      messages.push(labels[key] + ' needs a positive finite value.');
    } else if (!Number.isFinite(expected[key])) {
      messages.push(labels[key] + ' cannot be checked for this excluded observation.');
    } else {
      const within = Math.abs(value - expected[key]) <= 0.01 * Math.abs(expected[key]);
      messages.push(labels[key] + (within ? ' agrees within 1%.'
        : ' differs by more than 1%. Check the equation, temperature and pressure units.'));
    }
  }
  mathText('answer-feedback', supplied ? messages.join(' ')
    : 'Enter at least one calculated value, then check it. This check uses a 1% relative tolerance.');
  invalid?.focus();
  revision += 1;
}

function clearChart() {
  plotRevision += 1;
  if (globalThis.Plotly && element('case-plot')) globalThis.Plotly.purge(element('case-plot'));
  element('case-plot')?.replaceChildren();
  element('curve-head')?.replaceChildren();
  element('curve-body')?.replaceChildren();
  element('case-legend')?.replaceChildren();
  text('plot-note', 'Fit the training data to calculate this comparison.');
  show('plot-panel', false);
}

function invalidate(message) {
  clearGraduate(true, true);
  revision += 1;
  current = null;
  retainedFit = null;
  clearError();
  show('results', false);
  show('result-placeholder', true);
  text('result-placeholder', message || 'The fitting conditions changed. Fit again before comparing scores.');
  element('save-case').disabled = true;
  element('export-study').disabled = true;
  const fitOption = element('case-model').querySelector('option[value="fit"]');
  if (fitOption) fitOption.disabled = true;
  element('case-model').value = 'article';
  clearChart();
  text('status', message || 'The previous fit has been cleared. Saved comparisons are retained.');
}

function summaryRole(analysis) {
  if (analysis.evaluation.role === 'reference') {
    return 'Article reference: agreement with the supplied observations. The article used a wider data collection; this is not a new held-out validation.';
  }
  if (analysis.evaluation.heldOut) {
    return analysis.evaluation.pressure + ' kPa was not used in this teaching fit. Its score checks the retained model on held-out observations.';
  }
  return analysis.evaluation.pressure + ' kPa was included in fitting. This score is in-sample agreement, not a held-out validation.';
}

function renderResult() {
  if (!current) return;
  const { inputs, fit, analysis: a } = current;
  const p = a.parameters;
  text('train-score', format(a.train.rmse, 5));
  text('eval-score', format(a.evaluation.rmse, 5));
  text('train-score-label', inputs.model === 'fit' ? 'Fitting-data RMSE in ln γ' : 'Selected-data RMSE in ln γ');
  text('eval-score-label', inputs.model === 'fit' ? 'Checking-data RMSE in ln γ' : 'Checking-data RMSE in ln γ · reference');
  text('train-count', a.train.count);
  text('eval-count', a.evaluation.count);
  text('fit-count-note', a.train.count + ' of ' + a.train.total + ' observations supply log-activity pairs at '
    + a.train.label + '. ' + a.train.excluded + ' excluded. At ' + a.evaluation.pressure + ' kPa, '
    + a.evaluation.count + ' of ' + a.evaluation.total + ' are usable and ' + a.evaluation.excluded + ' are excluded.');
  text('validation-role', summaryRole(a));
  mathText('fit-parameters', inputs.model === 'fit'
    ? 'Teaching fit: τ₁₂ = ' + format(p.a12, 7) + ', τ₂₁ = ' + format(p.a21, 7)
      + ', α = ' + format(p.alpha) + '. All three are dimensionless. Both τ values are held constant across the fitted temperature range.'
    : 'Article reference: τᵢⱼ = aᵢⱼ + bᵢⱼ/T. a₁₂ = ' + format(p.a12, 9)
      + ', a₂₁ = ' + format(p.a21, 9) + ', b₁₂ = ' + format(p.b12, 9)
      + ' K, b₂₁ = ' + format(p.b21, 9) + ' K; α = ' + format(p.alpha) + '.');
  text('fit-status', inputs.model === 'fit' && fit
    ? 'Numerical fit converged using ' + fit.points + ' usable pairs from ' + fit.label
      + '. ' + (fit.atBound ? 'A fitted parameter reached its bound. Inspect the model and residuals.'
        : 'Neither fitted parameter is at its bound.')
    : 'The published temperature-dependent NRTL parameters are shown without refitting them to this exercise.');
  const prediction = element('prediction')?.value;
  text('interpretation', (inputs.model === 'fit'
    ? 'Use the training score to judge agreement with fitted observations, then use the evaluation role below to interpret the other score.'
    : 'Inspect this published reference, then fit two constant τ values to the selected training observations.')
    + (prediction ? ' Your prediction was “' + optionLabel('prediction') + '”. Compare it with the two scores.' : ''));
  text('model-assumptions', a.limits.join(' '));
  const check = a.modelCheck;
  text('model-check-note', 'At fixed ' + format(check.fixedTK || 350)
    + ' K, the sampled Gibbs–Duhem derivative residual is '
    + format(check.maxGibbsDuhemResidual, 3) + '. Minimum sampled scaled liquid curvature is '
    + format(check.minSampledScaledCurvature, 4) + '. '
    + (check.minSampledScaledCurvature > 0 ? 'Positive on the sampled grid; this is not a global stability proof.'
      : 'Nonpositive curvature was detected. Homogeneous bubble-curve points may be unstable; this lab does not solve LLE.')
    + ' This checks the model equation and does not certify the experimental data.');
  const steps = [
    'Infer ln γ₁ and ln γ₂ only for interior observations within both Antoine ranges. Keep every original measurement visible in the data table.',
    (inputs.model === 'fit' ? 'Fit two constant τ values using only ' + a.train.label
      + ' and α = ' + format(inputs.alpha) + '.'
      : 'Evaluate the article parameters at each measured temperature. They have not been refitted here.'),
    'At each usable state, subtract inferred ln γᵢ from model ln γᵢ. Square both component residuals, sum across N observations, divide by 2N, and take the square root. The score is dimensionless.',
    'At ' + a.train.label + ', N = ' + a.train.count + ' and RMSE = ' + format(a.train.rmse, 6)
      + '. At ' + a.evaluation.pressure + ' kPa, N = ' + a.evaluation.count
      + ' and RMSE = ' + format(a.evaluation.rmse, 6) + '.',
    summaryRole(a),
    'A small fitting error, numerical convergence and thermodynamic consistency answer different questions. Continue to Lab 03 for consistency-test applicability.',
  ];
  element('score-steps')?.replaceChildren(...steps.map((step) => {
    const li = document.createElement('li');
    mathText(li, step);
    return li;
  }));
  show('results', true);
  show('result-placeholder', false);
  element('save-case').disabled = false;
  element('export-study').disabled = false;
  const fitOption = element('case-model').querySelector('option[value="fit"]');
  if (fitOption) fitOption.disabled = !retainedFit;
}

function numericalTable(headers, rows) {
  if (element('curve-head')) {
    const tr = document.createElement('tr');
    headers.forEach((value) => {
      const th = document.createElement('th');
      th.scope = 'col';
      mathText(th, value);
      tr.append(th);
    });
    element('curve-head').replaceChildren(tr);
  }
  element('curve-body')?.replaceChildren(...rows.map((values) => {
    const tr = document.createElement('tr');
    values.forEach((value) => {
      const td = document.createElement('td');
      td.textContent = typeof value === 'number' ? format(value, 7) : value ?? 'Outside property range';
      tr.append(td);
    });
    return tr;
  }));
}

function plotNote(message, analysis) {
  const note = element('plot-note');
  if (!note) return;
  note.replaceChildren(document.createTextNode(message));
  const unstable = analysis.modelCheck.minSampledScaledCurvature <= 0;
  note.classList.toggle('scope-note', unstable);
  if (unstable) {
    note.append(document.createTextNode(' Nonpositive liquid curvature was detected on the sampled grid at 350 K. These are homogeneous model candidates and may not be stable equilibrium branches. '));
    const link = document.createElement('a');
    link.href = '../labs/stability.html#lle-experiment';
    link.textContent = 'Investigate liquid stability in Lab 04';
    note.append(link);
  }
}

async function renderChart() {
  const epoch = ++plotRevision;
  const saved = current;
  if (!saved) return;
  show('plot-panel', true);
  const { inputs, analysis: a } = saved;
  const measured = a.evaluation.rows;
  const valid = measured.filter((row) => row.ln);
  const curve = a.curve;
  const modelName = inputs.model === 'fit' ? 'Teaching fit' : 'Article reference';
  const line = (x, y, name, color, dash = 'solid', mode = 'lines') => ({
    x, y, name, mode, type: 'scatter', connectgaps: false,
    line: { color, width: 2, dash }, marker: { color, size: 7 },
  });
  let traces, xTitle = 'Liquid mole fraction · x<sub>1</sub>', yTitle, note;
  if (inputs.chart === 'gamma') {
    traces = [
      line(valid.map((r) => r.x), valid.map((r) => Math.exp(r.ln[0])), 'Inferred γ<sub>1</sub>', palette.teal, 'solid', 'markers'),
      line(valid.map((r) => r.x), valid.map((r) => Math.exp(r.ln[1])), 'Inferred γ<sub>2</sub>', palette.teal, 'dot', 'markers'),
      line(valid.map((r) => r.x), valid.map((r) => Math.exp(r.modelLn[0])), modelName + ' γ<sub>1</sub>', palette.amber),
      line(valid.map((r) => r.x), valid.map((r) => Math.exp(r.modelLn[1])), modelName + ' γ<sub>2</sub>', palette.amber, 'dash'),
    ];
    traces[1].marker.symbol = 'diamond-open';
    yTitle = 'Activity coefficient · γ';
    note = 'Each model value uses the measured T and x of that observation. This is an isobaric path with changing temperature.';
    numericalTable(['T / K', 'Liquid x₁', 'Inferred γ₁', 'Inferred γ₂', 'Model γ₁', 'Model γ₂'],
      valid.map((r) => [r.T, r.x, Math.exp(r.ln[0]), Math.exp(r.ln[1]), Math.exp(r.modelLn[0]), Math.exp(r.modelLn[1])]));
  } else if (inputs.chart === 'residual') {
    traces = [
      line(valid.map((r) => r.x), valid.map((r) => r.modelLn[0] - r.ln[0]), 'ln γ<sub>1</sub> residual', palette.amber, 'solid', 'markers'),
      line(valid.map((r) => r.x), valid.map((r) => r.modelLn[1] - r.ln[1]), 'ln γ<sub>2</sub> residual', palette.amber, 'dash', 'markers'),
    ];
    traces[1].marker.symbol = 'diamond-open';
    yTitle = 'Model − inferred ln γ · dimensionless';
    note = 'Residuals use the measured temperature and composition. A small residual does not establish experimental thermodynamic consistency.';
    numericalTable(['T / K', 'Liquid x₁', 'ln γ₁ residual', 'ln γ₂ residual'],
      valid.map((r) => [r.T, r.x, r.modelLn[0] - r.ln[0], r.modelLn[1] - r.ln[1]]));
  } else {
    traces = [
      line(measured.map((r) => r.x), measured.map((r) => r.T), 'Measured liquid', palette.teal, 'solid', 'markers'),
      line(measured.map((r) => r.y), measured.map((r) => r.T), 'Measured vapor', palette.teal, 'dot', 'markers'),
      line(curve.map((r) => r.x), curve.map((r) => r.T), modelName + ' bubble', palette.amber),
      line(curve.map((r) => r.y), curve.map((r) => r.T), modelName + ' dew', palette.amber, 'dash'),
    ];
    traces[1].marker.symbol = 'diamond-open';
    xTitle = '2-propanol mole fraction · x<sub>1</sub> or y<sub>1</sub>';
    yTitle = 'Temperature / K';
    note = 'All ' + a.evaluation.total + ' original observations at ' + a.evaluation.pressure
      + ' kPa are shown. Calculated curves have gaps where no root exists inside '
      + a.domainK.join(' to ') + ' K. No extrapolation is made.';
    numericalTable(['Point', 'P / kPa', 'T / K', 'Liquid x₁', 'Vapor y₁'], [
      ...measured.map((r) => ['Measured', r.PkPa, r.T, r.x, r.y]),
      ...curve.map((r) => ['Calculated', a.evaluation.pressure, r.T, r.x, r.y]),
    ]);
  }
  if (element('case-legend')) {
    const labels = inputs.chart === 'gamma'
      ? ['Inferred γ₁', 'Inferred γ₂', modelName + ' γ₁', modelName + ' γ₂']
      : inputs.chart === 'residual' ? ['ln γ₁ residual', 'ln γ₂ residual']
        : ['Measured liquid', 'Measured vapor', modelName + ' bubble', modelName + ' dew'];
    element('case-legend').replaceChildren(...traces.map((trace, index) => {
      const label = document.createElement('span');
      const swatch = document.createElement('i');
      swatch.setAttribute('aria-hidden', 'true');
      swatch.className = 'legend-swatch' + (trace.mode === 'markers' ? ' legend-point' : '');
      swatch.style.borderColor = trace.line.color;
      if (trace.mode === 'markers') {
        if (trace.marker.symbol === 'diamond-open') swatch.classList.add('legend-diamond');
        else swatch.style.background = trace.line.color;
      } else swatch.style.borderTopStyle = trace.line.dash === 'dash' ? 'dashed' : 'solid';
      const wording = document.createElement('span');
      mathText(wording, labels[index]);
      label.append(swatch, wording);
      return label;
    }));
  }
  plotNote(a.evaluation.pressure + ' kPa · ' + modelName + '. ' + note, a);
  if (!globalThis.Plotly) {
    plotNote('The optional chart library is unavailable. Numerical scores, observations and curve data remain available. ' + note, a);
    return;
  }
  try {
    await globalThis.Plotly.react(element('case-plot'), traces, {
      margin: { t: 24, r: 20, b: 75, l: 68 },
      font: { family: 'Source Sans 3, sans-serif', size: 14, color: palette.graphite },
      paper_bgcolor: 'white', plot_bgcolor: 'white',
      xaxis: { title: { text: xTitle }, range: [0, 1], gridcolor: palette.mist },
      yaxis: { title: { text: yTitle }, gridcolor: palette.mist, zerolinecolor: palette.graphite },
      showlegend: false,
      hovermode: 'closest',
    }, { responsive: true, displaylogo: false, displayModeBar: false });
    if (epoch !== plotRevision || current !== saved) return;
  } catch (issue) {
    if (epoch === plotRevision) plotNote('The plot could not be drawn. Use the numerical scores and data table. ' + issue.message, a);
  }
}

function attachWorkspace(calculated, input) {
  return {
    ...calculated,
    inputs: input || calculated.inputs,
    data,
    name: element('case-name').value.trim() || 'Experimental VLE comparison',
    prediction: element('prediction')?.value || importedPrediction,
    answers: answers(),
    solutionOpen: !!element('observation-solution')?.open,
    graduate: graduateSnapshot(),
  };
}

function applyPrediction(value = '') {
  const field = element('prediction');
  const known = [...field.options].some((option) => option.value === value);
  field.value = known ? value : '';
  importedPrediction = known ? '' : value;
  let note = element('recorded-prediction');
  if (!note) {
    note = document.createElement('p');
    note.id = 'recorded-prediction';
    note.className = 'input-help';
    field.closest('.prediction-row').after(note);
  }
  note.textContent = importedPrediction ? 'Recorded prediction from the opened study: ' + importedPrediction : '';
  note.hidden = !importedPrediction;
}

function updateName(inputs) {
  if (manualCaseName) return;
  element('case-name').value = inputs.model === 'article' ? 'Article reference, check ' + inputs.evaluate + ' kPa'
    : 'Fit ' + (inputs.train === 'both' ? 'both pressures' : inputs.train + ' kPa') + ', check ' + inputs.evaluate + ' kPa';
}

function recalculate(allowReference = false) {
  if (!retainedFit && !current && !allowReference) return;
  const inputs = readInputs();
  if (!inputs) return;
  try {
    const prior = current?.inputs;
    if (prior && ['inspect', 'selectedRow', 'train', 'evaluate', 'alpha', 'model'].some((key) => prior[key] !== inputs[key])) {
      const fitContextChanged = ['train', 'evaluate', 'alpha', 'model'].some((key) => prior[key] !== inputs[key]);
      clearGraduate(true, fitContextChanged);
    }
    updateName(inputs);
    current = attachWorkspace({ inputs, fit: retainedFit, analysis: analyze(data, inputs, retainedFit) });
    revision += 1;
    renderResult();
    renderChart();
    text('status', 'Model retained. Comparison recalculated for ' + inputs.evaluate + ' kPa.');
  } catch (issue) {
    error(issue.message);
  }
}

async function fitNow() {
  if (busy) return;
  const inputs = readInputs();
  if (!inputs) return;
  const started = revision;
  busy = true;
  element('fit-button').disabled = true;
  text('fit-status', 'Fitting the selected training observations…');
  text('status', 'Fitting two constant NRTL τ values. Evaluation observations are not added to the fit.');
  await new Promise((resolve) => requestAnimationFrame(resolve));
  try {
    if (revision !== started) return;
    const fitted = fitStudy(data, inputs);
    if (revision !== started) return;
    retainedFit = fitted.fit;
    element('case-model').querySelector('option[value="fit"]').disabled = false;
    element('case-model').value = 'fit';
    clearGraduate(true, true, 'Baseline model recalculated. Run the graduate investigations again for this context.');
    updateName(fitted.inputs);
    current = attachWorkspace(fitted);
    revision += 1;
    renderResult();
    renderChart();
    text('status', 'Teaching fit complete. ' + summaryRole(current.analysis));
    const panel = element('results').closest('section') || element('results');
    const top = panel.getBoundingClientRect().top;
    if (top < 0 || top > innerHeight - 100) {
      panel.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    }
  } catch (issue) {
    invalidate('The fit could not be completed. Check the fitting conditions and try again.');
    error(issue.message);
  } finally {
    busy = false;
    element('fit-button').disabled = false;
  }
}

function renderComparisons() {
  element('comparison-body').replaceChildren(...cases.map((saved, index) => {
    const tr = document.createElement('tr');
    const a = saved.analysis;
    const p = a.parameters;
    const values = [saved.name, saved.inputs.model === 'fit' ? 'Teaching fit' : 'Article reference',
      a.train.label, a.evaluation.pressure + ' kPa', p.alpha,
      saved.inputs.model === 'fit' ? p.a12 : 'a + b/T',
      saved.inputs.model === 'fit' ? p.a21 : 'a + b/T', a.train.rmse, a.evaluation.rmse];
    values.forEach((value) => {
      const td = document.createElement('td');
      td.textContent = typeof value === 'number' ? format(value, 6) : value;
      tr.append(td);
    });
    const td = document.createElement('td');
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Load case';
    button.setAttribute('aria-label', 'Load ' + saved.name + ', comparison ' + (index + 1));
    button.addEventListener('click', () => {
      clearError();
      data = copy(saved.data || data);
      retainedFit = saved.fit ? copy(saved.fit) : null;
      current = copy(saved);
      const fitOption = element('case-model').querySelector('option[value="fit"]');
      fitOption.disabled = !retainedFit;
      writeInputs(saved.inputs);
      element('case-name').value = saved.name;
      manualCaseName = true;
      applyPrediction(saved.prediction);
      writeAnswers(saved.answers);
      element('observation-solution').open = !!saved.solutionOpen;
      current.analysis = analyze(data, saved.inputs, retainedFit);
      restoreGraduate(saved.graduate, null, saved.inputs);
      renderPropertyRecords();
      renderObservation();
      renderResult();
      renderChart();
      revision += 1;
      text('status', saved.name + ' reopened and recalculated from its saved scientific context.');
    });
    td.append(button);
    tr.append(td);
    return tr;
  }));
  show('comparison-empty', cases.length === 0);
  show('comparison-table-wrap', cases.length > 0);
}

function saveCase() {
  if (!current) return;
  try {
    graduate = readGraduate();
    current = attachWorkspace(current);
    cases.push(copy(current));
    revision += 1;
    renderComparisons();
    text('status', current.name + ' saved. ' + cases.length + ' comparison cases in this study, including graduate settings and conclusions.');
  } catch (issue) { error(issue.message); issue.field?.focus(); }
}

function downloadStudy() {
  if (!current) return;
  try {
  graduate = readGraduate();
  current = attachWorkspace(current);
  const study = makeStudy(current, cases, element('reflection').value);
  const url = URL.createObjectURL(new Blob([JSON.stringify(study, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'thermodynamics-lab02-2027-study.json';
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  text('status', 'Study downloaded with observations, fitting context, graduate sensitivity results, comparisons and all conclusions.');
  } catch (issue) { error(issue.message); issue.field?.focus(); }
}

async function openStudy(event) {
  const file = event.target.files[0];
  if (!file) return;
  const request = ++importRequest;
  const started = revision;
  clearError();
  try {
    const opened = parseStudy(await file.text(), data);
    if (request !== importRequest) return;
    if (revision !== started) throw new Error('This study changed while the file was opening. Choose the file again to restore it.');
    data = opened.data;
    retainedFit = opened.fit;
    current = opened;
    cases = opened.cases;
    const fitOption = element('case-model').querySelector('option[value="fit"]');
    fitOption.disabled = !retainedFit;
    writeInputs(opened.inputs);
    element('case-name').value = opened.name || 'Opened study';
    manualCaseName = true;
    element('reflection').value = opened.reflection || '';
    applyPrediction(opened.prediction);
    writeAnswers(opened.answers);
    element('observation-solution').open = !!opened.solutionOpen;
    restoreGraduate(opened.graduate, opened.graduateAnalysis, opened.inputs);
    revision += 1;
    renderPropertyRecords();
    renderObservation();
    renderComparisons();
    renderResult();
    renderChart();
    text('status', 'Study reopened and recalculated. ' + cases.length + ' saved comparisons restored.');
  } catch (issue) {
    if (request === importRequest) {
      error('Could not open this study. ' + issue.message);
      text('status', 'The current study has been retained.');
    }
  } finally {
    if (request === importRequest) event.target.value = '';
  }
}

function fitButtonLabel() {
  const train = element('training-pressure').value;
  text('fit-button', train === 'both' ? 'Fit both pressure datasets' : 'Fit ' + train + ' kPa data');
}

async function start() {
  const loadingControls = ['dataset', 'observation', 'alpha', 'training-pressure', 'evaluation-pressure',
    'fit-button', 'case-model', 'case-chart', 'show-observation', 'check-observation', 'inspect-reference',
    'import-study', 'g2-bound-T', 'g2-bound-P', 'g2-bound-x', 'g2-bound-y', 'g2-run-sensitivity', 'g2-run-alpha'];
  for (const id of loadingControls) element(id).disabled = true;
  const response = await fetch(new URL('../../labs/assets/ipa-water.json', import.meta.url));
  if (!response.ok) throw new Error('The experimental observations could not be loaded. Reload this page.');
  data = validateData(await response.json());
  writeInputs(DEFAULT_INPUTS);
  renderPropertyRecords();
  renderObservation();
  restoreGraduate(undefined, { sensitivity: null, alpha: null });
  element('dataset').addEventListener('change', () => {
    const prior = Number(element('observation').value);
    setObservationOptions(Number(element('dataset').value), prior);
    writeAnswers();
    element('observation-solution').open = false;
    renderObservation();
    clearGraduate(true, false);
    renderGraduate();
    revision += 1;
    if (current) recalculate();
  });
  element('observation').addEventListener('change', () => {
    writeAnswers();
    element('observation-solution').open = false;
    renderObservation();
    clearGraduate(true, false);
    renderGraduate();
    revision += 1;
    if (current) recalculate();
  });
  element('show-observation').addEventListener('click', () => {
    renderObservation();
    element('observation-solution').open = true;
    revision += 1;
  });
  element('check-observation').addEventListener('click', checkObservation);
  element('fit-button').addEventListener('click', fitNow);
  element('alpha').addEventListener('input', () => {
    invalidate('α changed. Fit again to calculate the teaching model with this value.');
  });
  element('training-pressure').addEventListener('change', () => {
    fitButtonLabel();
    invalidate('Training observations changed. Fit again; saved comparison cases remain available.');
  });
  for (const id of ['evaluation-pressure', 'case-model', 'case-chart']) {
    element(id).addEventListener('change', () => {
      revision += 1;
      recalculate(id === 'case-model');
    });
  }
  element('inspect-reference').addEventListener('click', () => {
    element('case-model').value = 'article';
    revision += 1;
    recalculate(true);
  });
  for (const id of ['prediction', 'case-name', 'reflection', 'answer-psat1', 'answer-psat2', 'answer-gamma1', 'answer-gamma2']) {
    element(id)?.addEventListener('input', () => { revision += 1; });
  }
  element('prediction').addEventListener('change', () => { importedPrediction = ''; show('recorded-prediction', false); });
  element('case-name').addEventListener('input', () => { manualCaseName = true; });
  element('case-form').addEventListener('submit', (event) => { event.preventDefault(); fitNow(); });
  element('case-form').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && event.target.matches('input[type="number"]')) {
      event.preventDefault();
      if (event.target.id.startsWith('answer-')) checkObservation();
      else if (event.target.id.startsWith('g2-bound-')) runGraduateSensitivity();
      else fitNow();
    }
  });
  element('save-case').addEventListener('click', saveCase);
  element('export-study').addEventListener('click', downloadStudy);
  element('import-study').addEventListener('change', openStudy);
  element('g2-run-sensitivity').addEventListener('click', runGraduateSensitivity);
  element('g2-run-alpha').addEventListener('click', runGraduateAlpha);
  for (const key of ['T', 'P', 'x', 'y']) {
    element('g2-bound-' + key).addEventListener('input', () => {
      clearGraduate(true, false, 'Assumed bounds changed. Run the scenarios again.');
      revision += 1;
    });
  }
  for (const key of ['assumptions', 'uncertainty', 'evidence', 'decision']) {
    element('g2-note-' + key).addEventListener('input', () => {
      graduate.notes = graduateNotes();
      revision += 1;
    });
  }
  renderComparisons();
  show('results', false);
  show('result-placeholder', true);
  show('plot-panel', false);
  element('save-case').disabled = true;
  element('export-study').disabled = true;
  fitButtonLabel();
  for (const id of loadingControls) element(id).disabled = false;
  element('case-model').querySelector('option[value="fit"]').disabled = true;
  text('status', 'Experimental observations loaded. Inspect one row, then fit the 60 kPa training data and evaluate the retained fit at 80 kPa.');
}

start().catch((issue) => {
  error('Unable to start Lab 02. ' + issue.message);
  text('status', 'Reload after the required source files become available.');
});
