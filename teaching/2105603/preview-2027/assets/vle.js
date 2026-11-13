import {
  CASES, copy, defaults, calculateVLE, caseValues, pressureCurves, temperatureBoundaries,
  parseStudy, makeStudy, validatePropertyRecord,
} from './vle-state.js?v=review-1';
import { psat, R } from '../../labs/assets/thermo.js';
import { palette } from '../../labs/assets/palette.js';
import { FACTORS, NOTE_KEYS, graduateControls, restoreGraduate, sensitivityStudy, modelStudy } from './vle-graduate.js';

const element = (id) => document.getElementById(id);
const numericFields = ['T', 'P', 'z', 'A', 'A12', 'A21', 'tau12', 'tau21', 'alpha', 'referenceT'];
const labels = {
  T: 'Temperature', P: 'Pressure', z: 'Feed mole fraction',
  A: 'Margules A', A12: 'Margules A12', A21: 'Margules A21',
  tau12: 'NRTL tau12', tau21: 'NRTL tau21', alpha: 'NRTL alpha',
  referenceT: 'NRTL reference temperature',
};
const phaseLabels = {
  liquid: 'Liquid only', vapor: 'Vapor only', 'two-phase': 'Liquid + vapor',
  boundary: 'At a phase boundary',
  'bubble-boundary': 'Bubble boundary', 'dew-boundary': 'Dew boundary',
  indeterminate: 'Saturation · amounts undetermined',
};
let catalog;
let currentProperty;
let current = null;
let cases = [];
let revision = 0;
let importRequest = 0;
let graphRevision = 0;
let importedPrediction = '';
let transferredContext = {};
const importedRecords = new Map();
let graduate = { ...graduateControls(), sensitivity: null, comparison: null };
const mathNotation = {
  'P₁sat': ['P', '1', 'sat'], 'P₂sat': ['P', '2', 'sat'], 'Pᵢsat': ['P', 'i', 'sat'],
  'γ₁': ['γ', '1'], 'γ₂': ['γ', '2'], 'γᵢ': ['γ', 'i'],
  'x₁': ['x', '1'], 'y₁': ['y', '1'], 'z₁': ['z', '1'], 'xᵢ': ['x', 'i'],
  'τ₁₂': ['τ', '12'], 'τ₂₁': ['τ', '21'], 'A₁₂': ['A', '12'], 'A₂₁': ['A', '21'],
};
const mathPattern = new RegExp(Object.keys(mathNotation).sort((a, b) => b.length - a.length).join('|'), 'gu');

function mathText(node, value) {
  const source = String(value);
  const fragment = document.createDocumentFragment();
  let position = 0;
  mathPattern.lastIndex = 0;
  const make = (tag, text) => {
    const result = document.createElementNS('http://www.w3.org/1998/Math/MathML', tag);
    if (text !== undefined) result.textContent = text;
    return result;
  };
  for (const match of source.matchAll(mathPattern)) {
    fragment.append(document.createTextNode(source.slice(position, match.index)));
    const [base, subscript, superscript] = mathNotation[match[0]];
    const math = make('math');
    math.classList.add('inline-math');
    const body = make(superscript ? 'msubsup' : 'msub');
    const sub = make(/^\d+$/.test(subscript) ? 'mn' : 'mi', subscript);
    body.append(make('mi', base), sub);
    if (superscript) { const sup = make('mi', superscript); sup.setAttribute('mathvariant', 'normal'); body.append(sup); }
    math.append(body);
    fragment.append(math);
    position = match.index + match[0].length;
  }
  fragment.append(document.createTextNode(source.slice(position)));
  node.replaceChildren(fragment);
}

function setText(id, text) {
  if (element(id)) mathText(element(id), text);
}

function format(value, digits = 6) {
  if (value === null || !Number.isFinite(value)) return 'Not determined';
  if (value === 0) return '0';
  return Number(value.toPrecision(digits)).toString();
}

function show(id, visible) {
  if (element(id)) element(id).hidden = !visible;
}

function graduateForm() {
  const bounds = {};
  for (const factor of FACTORS) {
    const input = element('graduate-bound-' + factor.key);
    const value = Number(input.value);
    input.removeAttribute('aria-invalid');
    if (!input.value.trim() || !Number.isFinite(value) || value < 0 || value > factor.max) {
      input.setAttribute('aria-invalid', 'true');
      input.focus();
      throw new Error(factor.name + ' half-width must be from 0 to ' + factor.max + ' ' + factor.unit + '.');
    }
    bounds[factor.key] = value;
  }
  return graduateControls({ ...graduate, bounds,
    notes: Object.fromEntries(NOTE_KEYS.map((key) => [key, element('graduate-' + key).value])) });
}

function writeGraduateForm() {
  for (const factor of FACTORS) {
    element('graduate-bound-' + factor.key).value = graduate.bounds[factor.key];
    element('graduate-bound-' + factor.key).removeAttribute('aria-invalid');
  }
  for (const key of NOTE_KEYS) element('graduate-' + key).value = graduate.notes[key];
}

function invalidateGraduate(message = 'The baseline changed. Recalculate the state, then rerun the graduate investigations.') {
  graduate = { ...graduate, sensitivityRequested: false, comparisonRequested: false, sensitivity: null, comparison: null };
  setText('graduate-model-status', message);
  setText('graduate-sensitivity-status', message);
  setText('graduate-evidence-status', '');
  renderGraduate();
}

function graduateTable(id, rows, values) {
  element(id).replaceChildren(...rows.map((row) => {
    const tr = document.createElement('tr');
    for (const value of values(row)) {
      const cell = document.createElement('td');
      mathText(cell, value);
      tr.append(cell);
    }
    return tr;
  }));
}

function graduatePhase(row) {
  return row.status === 'failed' ? 'Outside assumptions/domain: ' + row.reason
    : phaseLabels[row.phase] || row.phase;
}

function renderGraduate() {
  for (const id of ['graduate-compare-models', 'graduate-run-sensitivity']) element(id).disabled = !current;
  setText('graduate-baseline', current
    ? 'Calculated baseline: T = ' + format(current.values.T) + ' K, P = ' + format(current.values.P)
      + ' kPa, z₁ = ' + format(current.values.z) + ', ' + current.result.model.name + ', '
      + phaseLabels[current.result.phase] + ', β = ' + format(current.result.beta) + '.'
    : 'Calculate a state in Step 1 before running either investigation.');
  show('graduate-model-wrap', !!graduate.comparison);
  if (graduate.comparison) {
    graduateTable('graduate-model-body', graduate.comparison.rows, (row) => [
      { ideal: 'Ideal liquid', margules: 'Margules · one parameter', margules2: 'Margules · two parameters', nrtl: 'NRTL' }[row.model],
      row.parameters, graduatePhase(row), format(row.beta), row.x === null ? 'Not reported' : format(row.x),
      row.y === null ? 'Not reported' : format(row.y),
    ]);
  }
  show('graduate-sensitivity-results', !!graduate.sensitivity);
  if (graduate.sensitivity) {
    const result = graduate.sensitivity;
    const counts = result.cornerSummary;
    setText('graduate-beta-range', counts.finite ? format(counts.minBeta) + ' to ' + format(counts.maxBeta) : 'No finite β values');
    setText('graduate-corner-counts', counts.finite + ' / ' + counts.indeterminate + ' / ' + counts.failed + ' of ' + counts.total);
    setText('graduate-phase-counts', 'Joint-corner phase counts: ' + (Object.entries(counts.phases)
      .map(([phase, count]) => (phaseLabels[phase] || phase) + ' = ' + count).join('; ') || 'No admitted phase result')
      + '. Counts describe the chosen scenarios, not phase probabilities.');
    const ranked = result.ranking.filter((row) => row.maxAbsoluteDeltaBeta !== null);
    setText('graduate-ranking', ranked.length
      ? 'Largest one-at-a-time |Δβ|: ' + ranked[0].name + ', ' + format(ranked[0].maxAbsoluteDeltaBeta)
        + '. OAT statuses: ' + result.oatSummary.finite + ' finite, ' + result.oatSummary.indeterminate
        + ' indeterminate, ' + result.oatSummary.failed + ' failed.'
      : 'No finite one-at-a-time change in β could be computed. Read the failure and indeterminate-state reasons.');
    graduateTable('graduate-oat-body', result.oat, (row) => [row.label, graduatePhase(row), format(row.beta), format(row.deltaBeta)]);
    graduateTable('graduate-corner-body', result.corners, (row) => [row.label, format(row.inputs.T), format(row.inputs.P),
      format(row.inputs.z), format(row.scales[0]), format(row.scales[1]), graduatePhase(row), format(row.beta)]);
  }
}

function storeGraduate() {
  graduate = restoreGraduate(graduateForm(), current);
  current.graduate = copy(graduate);
}

function runGraduate(kind) {
  if (!current) return;
  try {
    const controls = graduateForm();
    graduate = { ...graduate, ...controls };
    if (kind === 'comparison') {
      graduate.comparison = modelStudy(current);
      graduate.comparisonRequested = true;
      setText('graduate-model-status', 'Four candidates calculated at the same baseline conditions. Failures remain in the table; no candidate is validated by this comparison.');
    } else {
      graduate.sensitivity = sensitivityStudy(current, graduate.bounds);
      graduate.sensitivityRequested = true;
      const count = graduate.sensitivity.cornerSummary;
      setText('graduate-sensitivity-status', 'Ten one-at-a-time scenarios and 32 signed corner combinations evaluated. '
        + count.failed + ' corners failed their domain/assumption checks. No input or reference temperature was clipped or changed silently.');
    }
    current.graduate = copy(graduate);
    revision += 1;
    renderGraduate();
  } catch (error) {
    setText(kind === 'comparison' ? 'graduate-model-status' : 'graduate-sensitivity-status', error.message);
  }
}

function checkGraduateEvidence() {
  const notes = Object.fromEntries(NOTE_KEYS.map((key) => [key, element('graduate-' + key).value.trim()]));
  const missing = [];
  if (!graduate.comparison) missing.push('run the model comparison');
  if (!graduate.sensitivity) missing.push('run sensitivity scenarios for the current baseline');
  if (!notes.assumptions) missing.push('write the assumptions/model-evidence claim');
  if (!notes.sensitivity) missing.push('write the sensitivity/phase-robustness claim');
  if (!notes.comparison) missing.push('link model spread to input/property sensitivity');
  if (!notes.limits) missing.push('write the limited conclusion and next evidence needed');
  setText('graduate-evidence-status', missing.length ? 'Evidence record incomplete: ' + missing.join('; ') + '.'
    : 'The calculations and four explanation fields are present. Check that you cited at least two numerical outputs and justified the assumed bounds. This is a completeness check, not a grade or scientific validation.');
}

function hideError() {
  element('form-error').replaceChildren();
  element('form-error').hidden = true;
  show('stability-route', false);
}

function showError(message, code = '') {
  const box = element('form-error');
  box.replaceChildren(document.createTextNode(message));
  if (code === 'LIQUID_STABILITY') {
    show('stability-route', true);
    element('stability-route')?.closest('details')?.setAttribute('open', '');
  }
  if (message.includes('original Lab 01')) {
    const link = document.createElement('a');
    link.href = '../labs/index.html#experiment';
    link.textContent = 'Open the original Lab 01';
    box.append(document.createTextNode(' '), link);
  }
  box.hidden = false;
  box.focus();
}

function clearFieldErrors() {
  for (const id of numericFields) {
    element(id)?.removeAttribute('aria-invalid');
    show('error-' + id, false);
  }
}

function selectedProperty() {
  const key = element('system').value;
  if (currentProperty && currentProperty.key === key) return currentProperty.record;
  return importedRecords.get(key) || catalog.systems[key];
}

function modelControls() {
  const selected = element('model').value;
  show('margules-control', selected === 'margules');
  show('margules2-control', selected === 'margules2');
  show('nrtl-control', selected === 'nrtl');
  setText('model-note', selected === 'ideal'
    ? 'Ideal liquid and ideal vapor. The worked calculation uses Raoult’s law.'
    : 'The selected liquid activity model is paired with an ideal vapor. Parameters are teaching inputs unless a property source supplies a fit.');
  updateProblemContext();
}

function updateProblemContext() {
  const fields = ['T', 'P', 'z'].map((id) => element(id));
  const valid = fields.every((field) => field.value.trim() && Number.isFinite(Number(field.value)));
  if (!valid) {
    setText('case-description', 'Set the conditions for a 1.00 mol binary feed. Enter the temperature, pressure and component 1 feed mole fraction below.');
    return;
  }
  const model = element('model').value;
  const names = { margules: 'one-parameter Margules', margules2: 'two-parameter Margules', nrtl: 'NRTL' };
  setText('case-description', 'A 1.00 mol binary feed at ' + format(Number(element('T').value), 10)
    + ' K and ' + format(Number(element('P').value), 10) + ' kPa has a component 1 feed mole fraction z₁ = '
    + format(Number(element('z').value), 8) + '. Assume ideal vapor and '
    + (model === 'ideal' ? 'ideal liquid.' : 'the ' + names[model] + ' liquid activity model.'));
}

function updateProperties() {
  const record = selectedProperty();
  if (!record) return;
  const T = Number(element('T').value);
  const fixed = record.components.every((component) => component.equation === 'fixed');
  const types = [...new Set(record.components.map((component) => component.equation))];
  setText('system-note', record.description || record.label || 'Saved binary property record.');
  setText('component1-name', record.components[0].name);
  setText('component2-name', record.components[1].name);
  setText('temperature-range', fixed
    ? 'Supplied property values are available only at ' + format(record.rangeK[0]) + ' K.'
    : 'Both vapor-pressure records apply from ' + record.rangeK.join(' to ') + ' K.');
  element('T').min = record.rangeK[0];
  element('T').max = record.rangeK[1];
  element('T').readOnly = record.rangeK[0] === record.rangeK[1];
  setText('property-method', fixed
    ? 'Supplied saturation pressures at ' + format(record.rangeK[0]) + ' K · fixed-temperature record.'
    : types.length === 1 && types[0] === 'clausius'
      ? (record.kind === 'synthetic' ? 'Synthetic teaching data · ' : '') + 'Clausius–Clapeyron correlation.'
      : types.length === 1 && types[0] === 'antoine'
        ? 'Antoine correlations · source equations use bar and kelvin.'
        : 'Each component uses its own vapor-pressure record, shown below.');
  const enteredPressure = element('P').value.trim();
  const P = Number(enteredPressure);
  setText('property-operating-pressure', (enteredPressure && Number.isFinite(P) && P >= 1 && P <= 200
    ? 'Mixture operating pressure P = ' + format(P) + ' kPa. This is the pressure entered above.'
    : 'Enter a mixture operating pressure from 1 to 200 kPa in the Pressure field above.')
    + ' The mixture bubble and dew pressures are calculated in Step 2.');
  setText('psat1-value', '—');
  setText('psat2-value', '—');
  setText('property-temperature', '—');
  if (!element('T').value.trim() || !Number.isFinite(T) || T < record.rangeK[0] || T > record.rangeK[1]) {
    setText('property-status', fixed
      ? 'This property record supplies values only at ' + format(record.rangeK[0]) + ' K. No saturation pressures are shown for another temperature.'
      : 'Enter a temperature from ' + record.rangeK.join(' to ') + ' K to read both saturation pressures.');
  } else {
    try {
      const sat = record.components.map((component) => psat(component, T) / 1000);
      if (!sat.every((value) => Number.isFinite(value) && value > 0)) {
        throw new Error('The property record does not give positive finite saturation pressures.');
      }
      setText('psat1-value', format(sat[0]));
      setText('psat2-value', format(sat[1]));
      setText('property-temperature', 'At T = ' + format(T) + ' K');
      setText('property-status', fixed
        ? 'Supplied values at this temperature. This record does not predict values at other temperatures.' : '');
    } catch (error) {
      setText('property-status', 'Saturation pressures are unavailable at this temperature. ' + error.message);
    }
  }
  const correlation = element('property-correlation');
  if (correlation) {
    const cards = record.components.map((component, index) => {
      const card = document.createElement('section');
      card.className = 'property-equation-card';
      const heading = document.createElement('h4');
      heading.textContent = 'Component ' + (index + 1) + ' · ' + component.name;
      const equation = document.createElement('p');
      equation.className = 'property-equation';
      const constants = document.createElement('p');
      constants.className = 'property-constants';
      const units = document.createElement('p');
      if (component.equation === 'antoine') {
        equation.textContent = 'log₁₀(Psat / bar) = A − B/(T + C)';
        constants.textContent = 'A = ' + format(component.A, 15) + '; B = ' + format(component.B, 15)
          + '; C = ' + format(component.C, 15) + '.';
        units.textContent = 'Use T in K. The equation returns Psat in bar. Multiply by 100 for kPa.';
      } else if (component.equation === 'clausius') {
        equation.textContent = 'ln(Psat / Pref) = −(ΔHvap / R)(1/T − 1/Tref)';
        constants.textContent = 'Pref = ' + format(component.PrefPa / 1000, 12)
          + ' kPa; Tref = ' + format(component.Tref, 12) + ' K; ΔHvap = '
          + format(component.HvapJmol, 12) + ' J/mol.';
        units.textContent = 'Use T and Tref in K. Use ΔHvap in J/mol with R = '
          + format(R, 8) + ' J/(mol K). Psat has the same pressure unit as Pref.';
      } else {
        equation.textContent = 'Supplied saturation pressure at ' + format(component.rangeK[0]) + ' K';
        constants.textContent = 'Psat = ' + format(component.pressurePa / 1000, 12) + ' kPa.';
        units.textContent = 'This fixed-temperature record has no equation for extrapolating to other temperatures.';
      }
      const range = document.createElement('p');
      range.textContent = component.rangeK[0] === component.rangeK[1]
        ? 'Valid only at ' + format(component.rangeK[0]) + ' K.'
        : 'Component correlation range: ' + component.rangeK.join(' to ') + ' K.';
      card.append(heading, equation, constants, units, range);
      return card;
    });
    correlation.replaceChildren(...cards);
  }
  const sources = element('property-sources');
  if (sources) {
    const items = (record.sources || []).map((source) => {
      const row = document.createElement('p');
      if (typeof source?.url === 'string' && /^https?:\/\//i.test(source.url)) {
        const link = document.createElement('a');
        link.href = source.url;
        link.textContent = typeof source.title === 'string' ? source.title : 'Property source';
        row.append(link);
      } else row.textContent = typeof source?.title === 'string' ? source.title : 'Saved property record';
      return row;
    });
    sources.replaceChildren(...items);
  }
  updateProblemContext();
}

function clearPlot() {
  graphRevision += 1;
  if (element('vle-chart')) {
    if (globalThis.Plotly) globalThis.Plotly.purge(element('vle-chart'));
    element('vle-chart').replaceChildren();
  }
  if (element('curve-body')) element('curve-body').replaceChildren();
  show('curve-wrap', false);
  show('diagram-panel', false);
  setText('chart-note', 'Calculate a state to show its phase diagram.');
}

function invalidate(message = 'Inputs changed. Check the inputs, then calculate again.') {
  revision += 1;
  current = null;
  show('results', false);
  show('result-placeholder', true);
  setText('result-placeholder', message);
  element('save-case').disabled = true;
  element('export-study').disabled = true;
  hideError();
  clearPlot();
  invalidateGraduate();
}

function writeValues(values, property) {
  const system = element('system');
  if (![...system.options].some((option) => option.value === values.system)) {
    system.append(new Option(property.label || 'Opened property record', values.system));
  }
  currentProperty = { key: values.system, record: copy(property) };
  transferredContext = values.system === 'fit-transfer'
    ? { fitP1: values.fitP1, fitP2: values.fitP2, fitKind: values.fitKind } : {};
  if (!Object.hasOwn(catalog.systems, values.system)) importedRecords.set(values.system, copy(property));
  system.value = values.system;
  element('model').value = values.model;
  for (const id of numericFields) element(id).value = values[id];
  element('temperatureMode').value = values.temperatureMode;
  if (element('compare')) element('compare').checked = values.compare;
  clearFieldErrors();
  modelControls();
  updateProperties();
}

function setCaseSelection(key = '') {
  for (const button of document.querySelectorAll('[data-case]')) {
    button.setAttribute('aria-pressed', String(button.dataset.case === key));
  }
}

function loadCase(key) {
  const chosen = caseValues(key, catalog);
  writeValues(chosen.values, chosen.propertyRecord);
  element('case-name').value = chosen.name;
  element('prediction').value = '';
  importedPrediction = '';
  show('recorded-prediction', false);
  invalidate('Starting values loaded. You can make a prediction before calculating this case.');
  setCaseSelection(key);
  setText('case-description', 'A 1.00 mol binary feed at 350 K and ' + format(chosen.values.P, 10)
    + ' kPa has a component 1 feed mole fraction z₁ = 0.40. Assume ideal vapor and ideal liquid.');
  setText('case-task', 'Verify the phase calculation, then complete the graduate model audit and sensitivity investigation in Step 4.');
  setText('status', chosen.name + ' loaded. Saved comparison rows remain available.');
}

function readValues() {
  clearFieldErrors();
  const values = { ...defaults(element('system').value, selectedProperty()), ...transferredContext };
  values.model = element('model').value;
  values.temperatureMode = element('temperatureMode').value;
  values.compare = element('compare') ? element('compare').checked : true;
  const active = ['T', 'P', 'z', ...({
    ideal: [], margules: ['A'], margules2: ['A12', 'A21'],
    nrtl: ['tau12', 'tau21', 'alpha', 'referenceT'],
  }[values.model] || [])];
  const ranges = {
    T: selectedProperty().rangeK, P: [1, 200], z: [0, 1], A: [-1, 1.8],
    A12: [-1, 3], A21: [-1, 3], tau12: [-2, 6], tau21: [-2, 6],
    alpha: [0.1, 0.6], referenceT: [1, 2000],
  };
  const invalid = [];
  for (const id of numericFields) {
    const input = element(id);
    const value = Number(input.value);
    if (active.includes(id) && (!input.value.trim() || !Number.isFinite(value)
      || value < ranges[id][0] || value > ranges[id][1])) {
      const message = labels[id] + ' must be between ' + ranges[id].join(' and ') + '.';
      input.setAttribute('aria-invalid', 'true');
      setText('error-' + id, message);
      show('error-' + id, true);
      invalid.push({ id, message });
    }
    if (input.value.trim() && Number.isFinite(value)) values[id] = value;
  }
  if (invalid.length) {
    showError('Check the highlighted inputs, then calculate again.');
    const list = document.createElement('ul');
    for (const item of invalid) {
      const row = document.createElement('li');
      const link = document.createElement('a');
      link.href = '#' + item.id;
      link.textContent = item.message;
      link.addEventListener('click', (event) => {
        event.preventDefault();
        element(item.id).closest('details')?.setAttribute('open', '');
        element(item.id).focus();
      });
      row.append(link);
      list.append(row);
    }
    element('form-error').append(list);
    element(invalid[0].id).closest('details')?.setAttribute('open', '');
    element(invalid[0].id).focus();
    return null;
  }
  return values;
}

function phaseMeaning(result) {
  if (result.phase === 'liquid') return 'All 1 mol of feed is liquid. Its composition equals the overall feed composition.';
  if (result.phase === 'vapor') return 'All 1 mol of feed is vapor. Its composition equals the overall feed composition.';
  if (result.phase === 'bubble-boundary') return 'This is the bubble boundary. Vapor is incipient: its composition is defined while its limiting amount is zero.';
  if (result.phase === 'dew-boundary') return 'This is the dew boundary. Liquid is incipient: its composition is defined while its limiting amount is zero.';
  if (result.beta === null) return 'Liquid and vapor have the same composition at this saturation state. T, P and the overall composition leave the phase amounts undetermined.';
  return 'Liquid and vapor coexist. Their compositions differ from the overall feed composition.';
}

function workedSteps(values, result) {
  const sat = result.bubble.psat.map((value) => value / 1000);
  const steps = [
    'Read saturation pressures at this temperature: P₁sat = ' + format(sat[0])
      + ' kPa and P₂sat = ' + format(sat[1]) + ' kPa.',
  ];
  if (values.model === 'ideal') {
    steps.push('At x₁ = z₁, the bubble pressure is z₁P₁sat + (1 − z₁)P₂sat = '
      + format(result.bubble.P / 1000) + ' kPa.');
    steps.push('At y₁ = z₁, the dew pressure is 1/[z₁/P₁sat + (1 − z₁)/P₂sat] = '
      + format(result.dew.P / 1000) + ' kPa.');
  } else {
    steps.push('The liquid model supplies γ₁ and γ₂. At the feed bubble boundary, P = ΣxᵢγᵢPᵢsat = '
      + format(result.bubble.P / 1000) + ' kPa. The dew boundary at y₁ = z₁ is '
      + format(result.dew.P / 1000) + ' kPa.');
  }
  if (result.beta === null) {
    steps.push('At saturation with x₁ = y₁ = z₁, a lever-rule denominator is zero. An additional specification, such as enthalpy, is needed to determine the phase amounts.');
  } else if (result.x === null || result.y === null) {
    steps.push('The stable state is ' + phaseLabels[result.phase].toLowerCase()
      + '. Its present-phase composition is z₁ = ' + format(values.z)
      + '; the absent phase has no reported composition.');
    steps.push('For the 1 mol basis, liquid = ' + format(1 - result.beta)
      + ' mol and vapor = ' + format(result.beta) + ' mol.');
  } else {
    if (values.model === 'ideal' && Math.abs(sat[0] - sat[1]) > 1e-10) {
      steps.push('Solve P = x₁P₁sat + (1 − x₁)P₂sat: x₁ = (P − P₂sat)/(P₁sat − P₂sat) = '
        + format(result.x) + '. Then y₁ = x₁P₁sat/P = ' + format(result.y) + '.');
    } else {
      steps.push('Solve the equilibrium relations with the selected liquid model: x₁ = '
        + format(result.x) + ' and y₁ = ' + format(result.y) + '.');
    }
    steps.push('Use β = (z₁ − x₁)/(y₁ − x₁) = ' + format(result.beta)
      + '. The liquid and vapor amounts are ' + format(1 - result.beta)
      + ' and ' + format(result.beta) + ' mol per 1 mol feed.');
    steps.push('Check component 1: (1 − β)x₁ + βy₁ = '
      + format((1 - result.beta) * result.x + result.beta * result.y)
      + ', matching z₁ = ' + format(values.z) + '.');
  }
  return steps;
}

function renderResult() {
  const { values, result } = current;
  setText('result-phase', phaseLabels[result.phase] || result.phase);
  setText('result-beta', format(result.beta));
  setText('result-beta-note', result.beta === null ? 'An additional specification is needed.'
    : 'V/F · mole fraction of feed that is vapor');
  setText('result-x', result.x === null ? 'No liquid' : format(result.x));
  setText('result-y', result.y === null ? 'No vapor' : format(result.y));
  setText('result-x-note', result.phase === 'dew-boundary' ? 'Incipient liquid · limiting amount zero'
    : result.x === null ? 'Liquid is absent at this state.' : 'Component 1 in the liquid');
  setText('result-y-note', result.phase === 'bubble-boundary' ? 'Incipient vapor · limiting amount zero'
    : result.y === null ? 'Vapor is absent at this state.' : 'Component 1 in the vapor');
  setText('result-liquid-moles', format(result.phaseAmounts.liquid));
  setText('result-vapor-moles', format(result.phaseAmounts.vapor));
  setText('result-bubble', format(result.bubble.P / 1000));
  setText('result-dew', format(result.dew.P / 1000));
  setText('result-balance', result.beta === null ? 'Amounts undetermined'
    : format(result.balanceResidual, 3));
  setText('phase-interpretation', phaseMeaning(result));
  const feedback = element('prediction-feedback');
  const chosen = element('prediction').value;
  const boundary = ['bubble-boundary', 'dew-boundary', 'indeterminate'].includes(result.phase);
  const matches = chosen === result.phase || (chosen === 'boundary' && boundary);
  feedback.textContent = !chosen ? '' : boundary
    ? 'Compare your prediction with the boundary interpretation. A limiting phase can have zero amount and a defined incipient composition.'
    : matches ? 'Your phase prediction matches this state.'
      : 'You predicted ' + phaseLabels[chosen] + '. Compare the pressure with the feed bubble/dew boundaries and explain the calculated phase.';
  feedback.hidden = !chosen;
  element('calc-steps').replaceChildren(...workedSteps(values, result).map((text) => {
    const row = document.createElement('li');
    mathText(row, text);
    return row;
  }));
  const temperatures = temperatureBoundaries(values, current.propertyRecord);
  setText('boundary-temperatures', temperatures.map((boundaryResult) => boundaryResult.T === null
    ? boundaryResult.name + ' T: ' + boundaryResult.message
    : boundaryResult.name + ' T at the specified P and feed boundary composition: '
      + format(boundaryResult.T) + ' K.').join(' '));
  show('results', true);
  show('result-placeholder', false);
  element('save-case').disabled = false;
  element('export-study').disabled = false;
}

function renderCurveTable(data) {
  if (!element('curve-body')) return;
  const rows = data.map((point) => {
    const row = document.createElement('tr');
    for (const value of [point.x, point.y, point.P / 1000]) {
      const cell = document.createElement('td');
      cell.textContent = format(value);
      row.append(cell);
    }
    return row;
  });
  element('curve-body').replaceChildren(...rows);
  show('curve-wrap', true);
}

async function renderChart() {
  const epoch = ++graphRevision;
  const saved = current;
  if (!saved) return;
  show('diagram-panel', true);
  try {
    const curves = pressureCurves(saved.values, saved.propertyRecord);
    saved.curves = curves;
    renderCurveTable(curves.selected);
    if (!globalThis.Plotly) {
      setText('chart-note', 'The chart library is unavailable. The numerical results, worked calculation and curve data remain available.');
      return;
    }
    const nonideal = saved.result.model.nonideal;
    const selectedColor = nonideal ? palette.amber : palette.teal;
    const traces = [];
    const addCurves = (data, label, color) => {
      traces.push({ x: data.map((p) => p.x), y: data.map((p) => p.P / 1000),
        type: 'scatter', mode: 'lines', name: label + 'Bubble · x₁',
        line: { color, width: 2 } });
      traces.push({ x: data.map((p) => p.y), y: data.map((p) => p.P / 1000),
        type: 'scatter', mode: 'lines', name: label + 'Dew · y₁',
        line: { color, width: 2, dash: 'dash' } });
    };
    if (curves.ideal && nonideal) addCurves(curves.ideal, 'Ideal ', palette.teal);
    addCurves(curves.selected, '', selectedColor);
    const result = saved.result;
    if (result.x !== null && result.y !== null) {
      traces.push({ x: [result.x, result.y], y: [saved.values.P, saved.values.P],
        type: 'scatter', mode: 'lines+markers', name: 'Equilibrium x₁, y₁',
        line: { color: palette.graphite, width: 2, dash: 'dot' },
        marker: { color: palette.graphite, size: 7 } });
    }
    traces.push({ x: [saved.values.z], y: [saved.values.P], type: 'scatter', mode: 'markers',
      name: 'Feed · z₁', marker: { color: palette.graphite, size: 11, symbol: 'diamond-open' } });
    await globalThis.Plotly.react(element('vle-chart'), traces, {
      margin: { t: 24, r: 20, b: 105, l: 65 },
      paper_bgcolor: 'white', plot_bgcolor: 'white',
      font: { family: 'Source Sans 3, sans-serif', color: palette.graphite, size: 14 },
      xaxis: { title: { text: 'Component 1 mole fraction · x₁, y₁' }, range: [0, 1], gridcolor: palette.mist },
      yaxis: { title: { text: 'Pressure / kPa' }, rangemode: 'tozero', gridcolor: palette.mist },
      legend: { orientation: 'h', x: 0, y: -0.28, entrywidth: 145, entrywidthmode: 'pixels' },
      shapes: [{ type: 'line', x0: 0, x1: 1, y0: saved.values.P, y1: saved.values.P,
        line: { color: palette.graphite, width: 1.5, dash: 'dot' } }],
    }, { responsive: true, displaylogo: false, modeBarButtonsToRemove: ['lasso2d', 'select2d'] });
    if (epoch !== graphRevision || current !== saved) {
      if (!current) clearPlot();
      return;
    }
    setText('chart-note', saved.result.model.name + ' at ' + format(saved.values.T)
      + ' K. Solid line uses liquid x₁; dashed line uses vapor y₁. The diamond is the overall feed at the specified pressure.');
  } catch (error) {
    if (epoch === graphRevision) setText('chart-note', 'The diagram could not be drawn. Use the numerical phase results and balance check. ' + error.message);
  }
}

function calculate() {
  hideError();
  const values = readValues();
  if (!values) return;
  try {
    current = {
      ...calculateVLE(values, selectedProperty()),
      name: element('case-name').value.trim() || 'Custom case',
      prediction: element('prediction').value || importedPrediction,
    };
    revision += 1;
    graduate = restoreGraduate(graduate, current);
    current.graduate = copy(graduate);
    setText('graduate-model-status', graduate.comparison ? 'Saved model candidates recomputed for the calculated baseline.' : 'Baseline calculated. Compare the liquid-model candidates in Step 4.');
    setText('graduate-sensitivity-status', graduate.sensitivity ? 'Saved sensitivity settings recomputed for the calculated baseline.' : 'Baseline calculated. Run the sensitivity scenarios in Step 4.');
    renderGraduate();
    renderResult();
    setText('status', phaseLabels[current.result.phase] + '. Vapor fraction '
      + format(current.result.beta) + '. Check the calculation and save a case to compare.');
    requestAnimationFrame(() => {
      if (current) renderChart();
    });
    const result = element('result-heading')?.closest('section') || element('results');
    const resultTop = result.getBoundingClientRect().top;
    if (resultTop < 0 || resultTop > innerHeight - 100) {
      const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
      result.scrollIntoView({ block: 'start', behavior: reducedMotion ? 'auto' : 'smooth' });
    }
  } catch (error) {
    invalidate('Correct the inputs or choose a model within its valid domain.');
    showError(error.message, error.code);
  }
}

function renderComparisons() {
  const rows = cases.map((saved, index) => {
    const row = document.createElement('tr');
    const cells = [saved.name, saved.values.T, saved.values.P, saved.values.z,
      saved.result.model.name, phaseLabels[saved.result.phase], saved.result.beta,
      saved.result.x, saved.result.y];
    cells.forEach((value, column) => {
      const cell = document.createElement('td');
      cell.textContent = column === 0 || column === 4 || column === 5 ? value
        : column === 7 && value === null ? 'No liquid'
          : column === 8 && value === null ? 'No vapor' : format(value);
      row.append(cell);
    });
    const cell = document.createElement('td');
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = 'Load case';
    button.setAttribute('aria-label', 'Load ' + saved.name + ', comparison ' + (index + 1));
    button.addEventListener('click', () => {
      writeValues(saved.values, saved.propertyRecord);
      element('case-name').value = saved.name;
      applyPrediction(saved.prediction);
      invalidate('Saved inputs loaded. Calculate to reproduce this comparison.');
      graduate = { ...graduateControls(saved.graduate), sensitivity: null, comparison: null };
      writeGraduateForm();
      renderGraduate();
      setCaseSelection();
      setText('case-description', 'Recalculate this saved case, then compare it with the stored row.');
      setText('case-task', 'The saved property record and model parameters are restored with the inputs.');
      setText('status', saved.name + ' loaded. Calculate to reproduce the stored result.');
      element('calculate').focus();
    });
    cell.append(button);
    row.append(cell);
    return row;
  });
  element('comparison-body').replaceChildren(...rows);
  show('comparison-empty', cases.length === 0);
  show('comparison-table-wrap', cases.length > 0);
}

function saveCase() {
  if (!current) return;
  try { storeGraduate(); }
  catch (error) { setText('graduate-sensitivity-status', 'The comparison was not saved. ' + error.message); return; }
  current.name = element('case-name').value.trim() || 'Custom case';
  cases.push(copy(current));
  revision += 1;
  renderComparisons();
  setText('status', current.name + ' saved. ' + cases.length + ' comparison cases in this study.');
}

function downloadStudy() {
  if (!current) return;
  try { storeGraduate(); }
  catch (error) { setText('graduate-sensitivity-status', 'The study was not downloaded. ' + error.message); return; }
  current.name = element('case-name').value.trim() || 'Custom case';
  const study = makeStudy(current, cases, element('reflection').value, catalog.version);
  const url = URL.createObjectURL(new Blob([JSON.stringify(study, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'thermodynamics-lab01-2027-study.json';
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  setText('status', 'Study downloaded with inputs, original property records, comparisons, graduate settings and explanations. Graduate calculations will be recomputed when reopened.');
}

function applyPrediction(value) {
  const known = [...element('prediction').options].some((option) => option.value === value);
  element('prediction').value = known ? value : '';
  importedPrediction = known ? '' : value || '';
  setText('recorded-prediction', importedPrediction ? 'Recorded prediction from the opened study: ' + importedPrediction : '');
  show('recorded-prediction', !!importedPrediction);
}

async function openStudy(event) {
  const file = event.target.files[0];
  if (!file) return;
  const request = ++importRequest;
  const startedAt = revision;
  hideError();
  try {
    const opened = parseStudy(await file.text(), catalog);
    if (request !== importRequest) return;
    if (revision !== startedAt) throw new Error('The study changed while the file was opening. Choose the file again to restore it.');
    writeValues(opened.values, opened.propertyRecord);
    element('case-name').value = opened.name;
    element('reflection').value = opened.reflection;
    applyPrediction(opened.prediction);
    cases = opened.cases;
    current = opened;
    graduate = opened.graduate;
    writeGraduateForm();
    revision += 1;
    setCaseSelection();
    renderComparisons();
    renderResult();
    renderGraduate();
    setText('case-description', 'Study inputs reopened and recalculated. Compare the restored state with your saved cases.');
    setText('case-task', 'The saved property data and model parameters are retained for recalculation.');
    renderChart();
    setText('status', 'Study reopened and recalculated. ' + cases.length + ' saved comparison cases restored.');
  } catch (error) {
    if (request === importRequest) {
      showError('Could not open this study. ' + error.message);
      setText('status', 'The current study has been retained.');
    }
  } finally {
    if (request === importRequest) event.target.value = '';
  }
}

async function start() {
  const response = await fetch(new URL('../../labs/assets/systems.json', import.meta.url));
  if (!response.ok) throw new Error('Property records could not be loaded. Reload this page.');
  catalog = await response.json();
  for (const record of Object.values(catalog.systems)) validatePropertyRecord(record);
  element('system').replaceChildren(...Object.entries(catalog.systems).map(([key, record]) => new Option(record.label, key)));
  for (const button of document.querySelectorAll('[data-case]')) {
    button.addEventListener('click', () => loadCase(button.dataset.case));
  }
  for (const id of numericFields) {
    element(id).addEventListener('input', () => {
      if (Object.values(CASES).some((choice) => choice.name === element('case-name').value)) {
        element('case-name').value = 'Custom case';
      }
      element('prediction').value = '';
      importedPrediction = '';
      show('recorded-prediction', false);
      element(id).removeAttribute('aria-invalid');
      show('error-' + id, false);
      invalidate();
      setCaseSelection();
      updateProperties();
    });
  }
  element('system').addEventListener('change', () => {
    const key = element('system').value;
    const record = importedRecords.get(key) || catalog.systems[key];
    writeValues(defaults(key, record), record);
    element('case-name').value = 'Custom system case';
    applyPrediction('');
    invalidate('System values loaded. Read the property data, then calculate.');
    setCaseSelection();
    setText('case-description', 'Choose T, P and feed composition for this system. Predict its phases before calculating.');
    setText('case-task', 'Use the property record and its stated temperature range.');
  });
  element('model').addEventListener('change', () => {
    modelControls();
    invalidate('Liquid model changed. Predict its effect and calculate again.');
    setCaseSelection();
  });
  for (const id of ['temperatureMode', 'compare']) {
    element(id)?.addEventListener('change', () => { invalidate(); setCaseSelection(); });
  }
  element('prediction').addEventListener('change', () => {
    importedPrediction = '';
    show('recorded-prediction', false);
    invalidate('Prediction recorded. Calculate to check the predicted phases.');
  });
  for (const id of ['case-name', 'reflection']) {
    element(id).addEventListener('input', () => { revision += 1; });
  }
  element('calculate').addEventListener('click', calculate);
  element('vle-form').addEventListener('submit', (event) => { event.preventDefault(); calculate(); });
  element('vle-form').addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && event.target.matches('input[type="number"]')) {
      event.preventDefault();
      calculate();
    }
  });
  element('save-case').addEventListener('click', saveCase);
  element('export-study').addEventListener('click', downloadStudy);
  element('import-study').addEventListener('change', openStudy);
  for (const factor of FACTORS) {
    element('graduate-bound-' + factor.key).addEventListener('input', () => {
      graduate.sensitivity = null;
      graduate.sensitivityRequested = false;
      revision += 1;
      setText('graduate-sensitivity-status', 'Sensitivity settings changed. Run the scenarios again; the base phase calculation is retained.');
      setText('graduate-evidence-status', '');
      renderGraduate();
    });
  }
  for (const key of NOTE_KEYS) element('graduate-' + key).addEventListener('input', () => {
    graduate.notes[key] = element('graduate-' + key).value;
    revision += 1;
    setText('graduate-evidence-status', '');
  });
  element('graduate-open-model').addEventListener('click', () => {
    element('model').closest('details').open = true;
    element('model').focus();
  });
  element('graduate-compare-models').addEventListener('click', () => runGraduate('comparison'));
  element('graduate-run-sensitivity').addEventListener('click', () => runGraduate('sensitivity'));
  element('graduate-check-evidence').addEventListener('click', checkGraduateEvidence);
  element('graduate-boundary-case').addEventListener('click', () => {
    loadCase('bubble');
    setText('graduate-sensitivity-status', 'The 96 kPa boundary case is loaded. Calculate it in Step 1, then rerun the same sensitivity settings and compare the phase counts with the 90 kPa study.');
    element('calculate').focus();
  });
  writeGraduateForm();
  loadCase('baseline');
  renderComparisons();
  element('calculate').disabled = false;
}

start().catch((error) => {
  showError('Unable to start this activity. ' + error.message);
  setText('status', 'Reload the page after the property files become available.');
});
