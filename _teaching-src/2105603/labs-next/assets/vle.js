import {
  CASES, copy, defaults, calculateVLE, caseValues, pressureCurves, temperatureBoundaries,
  parseStudy, makeStudy, validatePropertyRecord,
} from './vle-state.js';
import { psat } from '../../labs/assets/thermo.js';
import { palette } from '../../labs/assets/palette.js';

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

function setText(id, text) {
  if (element(id)) element(id).textContent = text;
}

function format(value, digits = 6) {
  if (value === null || !Number.isFinite(value)) return 'Not determined';
  if (value === 0) return '0';
  return Number(value.toPrecision(digits)).toString();
}

function show(id, visible) {
  if (element(id)) element(id).hidden = !visible;
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
  setText('system-note', record.description || record.label || 'Saved binary property record.');
  setText('component1-name', record.components[0].name);
  setText('component2-name', record.components[1].name);
  setText('temperature-range', 'Both vapor-pressure records apply from ' + record.rangeK.join(' to ') + ' K.');
  element('T').min = record.rangeK[0];
  element('T').max = record.rangeK[1];
  element('T').readOnly = record.rangeK[0] === record.rangeK[1];
  if (!element('T').value.trim() || !Number.isFinite(T) || T < record.rangeK[0] || T > record.rangeK[1]) {
    setText('property-values', 'Enter a temperature within the stated range to read both saturation pressures.');
  } else {
    try {
      const sat = record.components.map((component) => psat(component, T) / 1000);
      setText('property-values', 'At ' + format(T) + ' K: component 1 saturation pressure = '
        + format(sat[0]) + ' kPa; component 2 = ' + format(sat[1]) + ' kPa.');
    } catch (error) {
      setText('property-values', 'Vapor-pressure data unavailable at this temperature. ' + error.message);
    }
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

function invalidate(message = 'Inputs changed. Predict the phases, then calculate again.') {
  revision += 1;
  current = null;
  show('results', false);
  show('result-placeholder', true);
  setText('result-placeholder', message);
  element('save-case').disabled = true;
  element('export-study').disabled = true;
  hideError();
  clearPlot();
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
  invalidate('Starting values loaded. Predict the phases and calculate this case.');
  setCaseSelection(key);
  setText('case-description', 'A 1.00 mol binary feed at 350 K and ' + format(chosen.values.P, 10)
    + ' kPa has a component 1 feed mole fraction z₁ = 0.40. Assume ideal vapor and ideal liquid.');
  setText('case-task', 'Predict the phases, calculate x₁, y₁ and both phase amounts, then check the component balance.');
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
    row.textContent = text;
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
    renderResult();
    setText('status', phaseLabels[current.result.phase] + '. Vapor fraction '
      + format(current.result.beta) + '. Check the calculation and save a case to compare.');
    requestAnimationFrame(() => {
      if (current) renderChart();
    });
    const result = element('results');
    if (result.getBoundingClientRect().top > innerHeight - 100) {
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
  current.name = element('case-name').value.trim() || 'Custom case';
  cases.push(copy(current));
  revision += 1;
  renderComparisons();
  setText('status', current.name + ' saved. ' + cases.length + ' comparison cases in this study.');
}

function downloadStudy() {
  if (!current) return;
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
  setText('status', 'Study downloaded with inputs, property records, comparisons and your explanation.');
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
    revision += 1;
    setCaseSelection();
    renderComparisons();
    renderResult();
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
  loadCase('baseline');
  renderComparisons();
  element('calculate').disabled = false;
}

start().catch((error) => {
  showError('Unable to start this activity. ' + error.message);
  setText('status', 'Reload the page after the property files become available.');
});
