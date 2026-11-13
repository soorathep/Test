import * as engine from '../../labs/assets/case-study.js';
import { normalizeGraduateCase, analyzeGraduateCase } from './case-graduate.js';

export const GUIDED_CASE_VERSION = 1;
export const STUDY_SCHEMA = 'skh-thermo-case-study/1';
export const DEFAULT_INPUTS = Object.freeze({
  inspect: 60, selectedRow: 6, train: '60', evaluate: 80, alpha: 0.47,
  model: 'article', chart: 'txy',
});

export const copy = (value) => JSON.parse(JSON.stringify(value));
const fitCache = new Map();
const finite = (value, label) => {
  if (!Number.isFinite(value)) throw new Error(label + ' must be a finite number.');
  return value;
};
const finiteInput = (value, label) => {
  if (typeof value === 'string' && !value.trim()) throw new Error('Enter ' + label.toLowerCase() + '.');
  return finite(typeof value === 'string' ? Number(value) : value, label);
};
const text = (value, fallback = '', limit = 10000) => {
  if (value === undefined) return fallback;
  if (typeof value !== 'string' || value.length > limit) throw new Error('The saved text field is invalid.');
  return value;
};
const range = (value, label) => {
  if (!Array.isArray(value) || value.length !== 2 || !value.every(Number.isFinite)
    || value[0] <= 0 || value[1] < value[0]) throw new Error(label + ' needs a valid range in K.');
  return value;
};

export function validateData(input) {
  if (!input || typeof input !== 'object' || Array.isArray(input)
    || input.id !== 'barbieri-2024-ipa-water' || typeof input.version !== 'string'
    || !Array.isArray(input.components) || input.components.length !== 2
    || !input.components.every((name) => typeof name === 'string' && name.trim())
    || !Array.isArray(input.properties) || input.properties.length !== 2
    || !Array.isArray(input.datasets) || input.datasets.length !== 2) {
    throw new Error('Choose the supported isopropanol–water study. Open other data in the original Lab 02.');
  }
  const data = copy(input);
  data.properties.forEach((property, index) => {
    if (!property || typeof property.name !== 'string') throw new Error('Each property record needs a component name.');
    range(property.rangeK, 'Component ' + (index + 1));
    for (const key of ['A', 'B', 'C']) finite(property[key], 'Antoine ' + key);
    const denominators = property.rangeK.map((T) => T + property.C);
    if (denominators[0] * denominators[1] <= 0) throw new Error('The Antoine equation is singular in its stated range.');
  });
  const joint = engine.domain(data);
  if (joint[0] > joint[1]) throw new Error('The pure-component property ranges do not overlap.');
  const pressures = data.datasets.map((dataset) => dataset.pressureKPa).sort((a, b) => a - b);
  if (pressures[0] !== 60 || pressures[1] !== 80) throw new Error('This guided study requires the 60 and 80 kPa data sets.');
  for (const dataset of data.datasets) {
    if (!Array.isArray(dataset.rows) || !dataset.rows.length) throw new Error('Each pressure needs measured observations.');
    dataset.rows.forEach((row) => {
      if (!row || !['PkPa', 'T', 'x', 'y'].every((key) => Number.isFinite(row[key]))
        || row.PkPa !== dataset.pressureKPa || row.T <= 0 || row.x < 0 || row.x > 1 || row.y < 0 || row.y > 1) {
        throw new Error('A saved VLE observation has invalid pressure, temperature or mole fractions.');
      }
    });
  }
  if (!data.nrtl || !['alpha', 'a12', 'a21', 'b12', 'b21'].every((key) => Number.isFinite(data.nrtl[key]))
    || data.nrtl.alpha < 0 || data.nrtl.alpha > 1) throw new Error('The article NRTL record is invalid.');
  return data;
}

function scientificContext(data) {
  return JSON.stringify({
    id: data.id, version: data.version, components: data.components,
    properties: data.properties.map((property) => ({ name: property.name, A: property.A, B: property.B,
      C: property.C, rangeK: property.rangeK })),
    nrtl: Object.fromEntries(['alpha', 'a12', 'a21', 'b12', 'b21'].map((key) => [key, data.nrtl[key]])),
    datasets: [...data.datasets].sort((a, b) => a.pressureKPa - b.pressureKPa).map((dataset) => ({
      pressureKPa: dataset.pressureKPa,
      rows: dataset.rows.map(({ PkPa, T, x, y }) => ({ PkPa, T, x, y })),
    })),
  });
}

function datasetAt(data, pressure) {
  const dataset = data.datasets.find((entry) => entry.pressureKPa === pressure);
  if (!dataset) throw new Error('Choose 60 or 80 kPa.');
  return dataset;
}

function inferObservation(row, data) {
  const inferred = engine.infer(row, data);
  return row.x === 0 || row.x === 1
    ? { ...inferred, reason: 'Pure endpoint: the absent component’s activity coefficient cannot be inferred from this measurement.' }
    : inferred;
}

export function normalizeInputs(input = {}, suppliedData) {
  const data = validateData(suppliedData);
  if (!input || typeof input !== 'object' || Array.isArray(input)) throw new Error('The study inputs are invalid.');
  const values = { ...DEFAULT_INPUTS, ...input };
  for (const key of ['inspect', 'evaluate']) {
    values[key] = finiteInput(values[key], 'Data pressure');
    datasetAt(data, values[key]);
  }
  values.selectedRow = finiteInput(values.selectedRow, 'Observation number');
  if (!Number.isInteger(values.selectedRow) || values.selectedRow < 0
    || values.selectedRow >= datasetAt(data, values.inspect).rows.length) throw new Error('Choose an observation in the selected data set.');
  values.train = String(values.train);
  if (!['60', '80', 'both'].includes(values.train)) throw new Error('Choose a training data set: 60 kPa, 80 kPa, or both.');
  values.alpha = finiteInput(values.alpha, 'NRTL alpha');
  if (values.alpha < 0.1 || values.alpha > 0.6) throw new Error('NRTL alpha must be between 0.1 and 0.6.');
  if (!['article', 'fit'].includes(values.model)) throw new Error('Choose the article model or a teaching fit.');
  if (!['txy', 'gamma', 'residual'].includes(values.chart)) throw new Error('Choose the T–x–y, activity or residual view.');
  return Object.fromEntries(Object.keys(DEFAULT_INPUTS).map((key) => [key, values[key]]));
}

export function observation(suppliedData, pressure, rowIndex) {
  const data = validateData(suppliedData);
  pressure = finiteInput(pressure, 'Observation pressure');
  rowIndex = finiteInput(rowIndex, 'Observation number');
  const dataset = datasetAt(data, pressure);
  if (!Number.isInteger(rowIndex) || rowIndex < 0 || rowIndex >= dataset.rows.length) throw new Error('Choose a measured observation.');
  const row = copy(dataset.rows[rowIndex]);
  const inferred = inferObservation(row, data);
  let psat = null;
  try { psat = data.properties.map((component) => engine.pressure(component, row.T)); }
  catch (error) { if (!(error instanceof RangeError)) throw error; }
  return { row, rowIndex, pressureKPa: pressure, psat, ln: inferred.ln,
    gamma: inferred.ln ? inferred.ln.map(Math.exp) : null, reason: inferred.reason };
}

function trainingPressures(selection) { return selection === 'both' ? [60, 80] : [Number(selection)]; }
const pressureLabel = (pressures) => pressures.map((pressure) => pressure + ' kPa').join(' + ');

function rowsFor(data, pressures, parameters) {
  return pressures.flatMap((pressureKPa) => datasetAt(data, pressureKPa).rows.map((row, rowIndex) => {
    const inferred = inferObservation(row, data);
    return { ...inferred, pressureKPa, rowIndex,
      gamma: inferred.ln ? inferred.ln.map(Math.exp) : null,
      modelLn: inferred.ln && parameters ? engine.nrtl(row.x, row.T, parameters).ln : null };
  }));
}

function summary(data, pressures, parameters) {
  const rows = rowsFor(data, pressures, parameters);
  const valid = rows.filter((row) => row.ln);
  if (!valid.length) throw new Error('No usable activity-coefficient pairs remain in this data set.');
  return { pressures: [...pressures], label: pressureLabel(pressures), total: rows.length, count: valid.length,
    excluded: rows.length - valid.length, rows, rmse: Math.sqrt(engine.objective(valid, parameters)),
    exclusions: rows.filter((row) => !row.ln).map(({ rowIndex, pressureKPa, reason }) => ({ rowIndex, pressureKPa, reason })) };
}

function fitFor(data, inputs) {
  const pressures = trainingPressures(inputs.train);
  const key = scientificContext(data) + '|' + inputs.train + '|' + inputs.alpha;
  if (!fitCache.has(key)) {
    const valid = rowsFor(data, pressures).filter((row) => row.ln);
    const fitted = engine.fit(valid, inputs.alpha);
    if (!fitted.converged || !Number.isFinite(fitted.rmse)) throw new Error('The teaching fit did not converge.');
    fitCache.set(key, { ...fitted, train: inputs.train, pressures, label: pressureLabel(pressures),
      alpha: inputs.alpha, sourceId: data.id, dataVersion: data.version,
      context: scientificContext(data) });
    if (fitCache.size > 32) fitCache.delete(fitCache.keys().next().value);
  }
  return copy(fitCache.get(key));
}

function checkedFit(fitted, data, inputs) {
  if (fitted === null || fitted === undefined) return null;
  if (typeof fitted !== 'object' || Array.isArray(fitted) || !fitted.parameters
    || fitted.train !== inputs.train || fitted.alpha !== inputs.alpha
    || fitted.sourceId !== data.id || fitted.dataVersion !== data.version
    || fitted.context !== scientificContext(data)) throw new Error('The training data or alpha changed. Fit the two parameters again.');
  const p = fitted.parameters;
  if (![p.alpha, p.a12, p.a21, p.b12, p.b21].every(Number.isFinite)
    || p.alpha !== inputs.alpha || p.b12 !== 0 || p.b21 !== 0
    || p.a12 < -3 || p.a12 > 8 || p.a21 < -3 || p.a21 > 8) throw new Error('The saved teaching-fit parameters are invalid.');
  return fitted;
}

export function analyze(suppliedData, input = {}, suppliedFit = null) {
  const data = validateData(suppliedData);
  const inputs = normalizeInputs(input, data);
  const fitted = checkedFit(suppliedFit, data, inputs);
  if (inputs.model === 'fit' && !fitted) throw new Error('Fit the training data before selecting the teaching model.');
  const parameters = copy(inputs.model === 'fit' ? fitted.parameters : data.nrtl);
  const pressures = trainingPressures(inputs.train);
  const train = { ...summary(data, pressures, parameters), selection: inputs.train };
  const heldOut = inputs.model === 'fit' && !pressures.includes(inputs.evaluate);
  const evaluation = { ...summary(data, [inputs.evaluate], parameters), pressure: inputs.evaluate,
    heldOut, role: inputs.model === 'article' ? 'reference' : heldOut ? 'held-out' : 'training' };
  const reference = { trainRmse: summary(data, pressures, data.nrtl).rmse,
    evaluationRmse: summary(data, [inputs.evaluate], data.nrtl).rmse };
  return { selected: observation(data, inputs.inspect, inputs.selectedRow),
    observations: datasetAt(data, inputs.inspect).rows.map((_, index) => observation(data, inputs.inspect, index)),
    train, evaluation, parameters, reference,
    curve: engine.curve(data, inputs.evaluate, parameters), referenceCurve: engine.curve(data, inputs.evaluate, data.nrtl),
    modelCheck: engine.modelCheck(parameters, 350), domainK: engine.domain(data),
    limits: [
      'Activity coefficients are inferred using ideal vapor, negligible Poynting correction and pure-liquid standard states.',
      'RMSE is dimensionless and uses both ln-gamma residuals at measured temperature and liquid composition; each usable pair has equal weight.',
      'The teaching fit holds alpha fixed and fits two constant tau values across the selected temperature range.',
      'A fit evaluated on either training pressure is an in-sample comparison. Fitting both pressures leaves no held-out pressure set.',
      'The article model uses temperature-dependent parameters fitted to a wider literature collection; its errors here are reference comparisons.',
      'Pure endpoints and observations outside the joint Antoine domain remain visible but are excluded from activity regression.',
      'This isobaric, partially covered activity data set does not provide an independent thermodynamic-consistency pass or fail verdict.',
      'A sampled model curvature or Gibbs–Duhem check does not certify all data or establish global phase stability.',
    ], sourceData: data };
}

export function fitStudy(suppliedData, input = {}) {
  const data = validateData(suppliedData);
  const inputs = { ...normalizeInputs(input, data), model: 'fit' };
  const fitted = fitFor(data, inputs);
  return { data, inputs, fit: fitted, analysis: analyze(data, inputs, fitted) };
}

function answersFrom(value) {
  if (value === undefined) return { psat1: '', psat2: '', gamma1: '', gamma2: '' };
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('The saved calculation answers are invalid.');
  return Object.fromEntries(['psat1', 'psat2', 'gamma1', 'gamma2'].map((key) => {
    const answer = value[key] === undefined ? '' : text(value[key], '', 100);
    if (answer.trim() && (!Number.isFinite(Number(answer)) || Number(answer) <= 0)) throw new Error('A saved calculation answer must be blank or a positive finite number.');
    return [key, answer];
  }));
}

function snapshot(current) {
  const data = validateData(current.data || current.analysis?.sourceData);
  const inputs = normalizeInputs(current.inputs, data);
  const fitted = checkedFit(current.fit, data, inputs);
  if (inputs.model === 'fit' && !fitted) throw new Error('Calculate a teaching fit before saving this result.');
  const name = text(current.name, 'Case study', 120).trim() || 'Case study';
  const solutionOpen = current.solutionOpen ?? false;
  if (typeof solutionOpen !== 'boolean') throw new Error('The saved solution-view state is invalid.');
  const graduate = normalizeGraduateCase(current.graduate);
  return { schema: STUDY_SCHEMA, guidedVersion: GUIDED_CASE_VERSION, engineVersion: engine.CASE_VERSION,
    sourceId: data.id, dataVersion: data.version, source: data, inputs, fit: fitted ? copy(fitted) : null,
    name, prediction: text(current.prediction), reflection: text(current.reflection),
    answers: answersFrom(current.answers), solutionOpen, graduate,
    graduateResults: analyzeGraduateCase(data, inputs, graduate),
    ...(current.originalContext ? { originalContext: copy(current.originalContext) } : {}) };
}

export function makeStudy(current, cases = [], reflection = '') {
  if (!Array.isArray(cases)) throw new Error('The saved comparisons must be a list.');
  const base = snapshot(current);
  const analysis = analyze(base.source, base.inputs, base.fit);
  return { ...base, interface: '2105603-2027-guided-case-study', exportedAt: new Date().toISOString(),
    reflection: text(reflection), comparisonCases: cases.map(snapshot),
    parameters: analysis.parameters, fitContext: base.fit?.label || null,
    selectedPressureKPa: base.inputs.evaluate,
    summary: { trainingRMSE: analysis.train.rmse, evaluationRMSE: analysis.evaluation.rmse,
      evaluationRole: analysis.evaluation.role, usableTrainingPairs: analysis.train.count,
      usableEvaluationPairs: analysis.evaluation.count } };
}

function importedData(study, catalog) {
  const base = validateData(catalog);
  const source = Object.hasOwn(study, 'source') ? study.source
    : Object.hasOwn(study, 'data') ? study.data : base;
  const data = validateData(source);
  if (scientificContext(data) !== scientificContext(base)) {
    throw new Error('This file has a different source data or property context. Open it in the original Lab 02.');
  }
  if (study.sourceId !== undefined && study.sourceId !== data.id) throw new Error('The saved source identity is inconsistent.');
  if (study.dataVersion !== undefined && study.dataVersion !== data.version) throw new Error('The saved source version is inconsistent.');
  return data;
}

function legacyInputs(study) {
  const workspace = study.workspace;
  const controls = workspace?.schema === 'thermo-controls-v1' && workspace.lab === 'case-study'
    ? workspace.controls : null;
  const hasOriginal = study.version === engine.CASE_VERSION && study.source?.id === 'barbieri-2024-ipa-water';
  if (!hasOriginal && !controls) return null;
  if (controls && (typeof controls !== 'object' || Array.isArray(controls))) throw new Error('The original Lab 02 controls are invalid.');
  const c = controls || {};
  const inspect = Number(c.dataset ?? study.selectedPressureKPa ?? 60);
  const originalModel = c['case-model'] ?? (study.fit ? 'fit' : 'paper');
  const wantsFit = originalModel === 'fit';
  let train;
  if (wantsFit) {
    if (typeof study.fitContext !== 'string') {
      throw new Error('This original study does not retain its fit training context. Open it in the original Lab 02.');
    }
    const found = study.fitContext.match(/\b(?:60|80)\b/g) || [];
    const pressures = [...new Set(found.map(Number))].sort((a, b) => a - b);
    train = pressures.length === 2 ? 'both' : pressures.length === 1 ? String(pressures[0]) : null;
    if (!train || !study.fit?.parameters) throw new Error('The original teaching fit has no complete training context.');
  } else train = c['fit-scope'] === 'both' ? 'both' : String(inspect);
  const originalChart = c['case-chart'] || 'txy';
  const chart = ['txy', 'gamma', 'residual'].includes(originalChart) ? originalChart : 'txy';
  return { inputs: { ...DEFAULT_INPUTS, inspect, evaluate: inspect, train, chart,
    alpha: wantsFit ? study.fit.parameters.alpha : 0.47, model: wantsFit ? 'fit' : 'article' },
    wantsFit, reflection: study.reflection ?? c['case-reflection'] ?? '',
    originalContext: { chart: originalChart, bias: c.bias ?? null, fitScope: c['fit-scope'] ?? null },
    notices: chart !== originalChart ? ['The original chart selection is retained as metadata. This guided view opens T–x–y; use the original Lab 02 for area diagnostics.'] : [] };
}

function parseCase(study, catalog) {
  if (!study || typeof study !== 'object' || Array.isArray(study)) throw new Error('The saved case is invalid.');
  const data = importedData(study, catalog);
  let inputs, wantsFit, reflection, originalContext, notices = [];
  if (study.schema === STUDY_SCHEMA) {
    if (study.guidedVersion !== GUIDED_CASE_VERSION) throw new Error('Open this guided study with the version that created it.');
    inputs = normalizeInputs(study.inputs, data);
    wantsFit = study.fit !== null && study.fit !== undefined;
    if (inputs.model === 'fit' && !wantsFit) throw new Error('The saved teaching-model selection has no training fit.');
    if (wantsFit) checkedFit(study.fit, data, inputs);
    reflection = study.reflection ?? '';
    originalContext = study.originalContext;
  } else {
    const legacy = legacyInputs(study);
    if (!legacy) throw new Error('Choose a guided Lab 02 study or a supported original Lab 02 export.');
    inputs = normalizeInputs(legacy.inputs, data);
    ({ wantsFit, reflection, originalContext, notices } = legacy);
  }
  // Fit training data again. Saved parameter values and summary metrics are not evidence of a valid fit.
  const fitted = wantsFit ? fitFor(data, inputs) : null;
  const solutionOpen = study.solutionOpen ?? false;
  if (typeof solutionOpen !== 'boolean') throw new Error('The saved solution-view state is invalid.');
  const graduate = normalizeGraduateCase(study.graduate);
  const graduateAnalysis = analyzeGraduateCase(data, inputs, graduate);
  return { data, inputs, fit: fitted, analysis: analyze(data, inputs, fitted),
    name: text(study.name ?? study.caseName, 'Opened case', 120).trim() || 'Opened case',
    prediction: text(study.prediction), reflection: text(reflection),
    answers: answersFrom(study.answers), solutionOpen, graduate, graduateAnalysis,
    ...(originalContext ? { originalContext: copy(originalContext) } : {}), notices };
}

export function parseStudy(json, catalog) {
  let study;
  try { study = typeof json === 'string' ? JSON.parse(json) : copy(json); }
  catch { throw new Error('This file is not valid JSON. Choose a downloaded Lab 02 study.'); }
  if (study?.kind === 'thermo-comparison') {
    if (study.lab !== 'case-study' || !Array.isArray(study.cases) || !study.cases.length) throw new Error('Choose a Lab 02 comparison containing saved cases.');
    const cases = study.cases.map((entry, index) => {
      if (!entry || typeof entry !== 'object' || Array.isArray(entry)) throw new Error('A saved comparison entry is invalid.');
      return { ...parseCase(entry.study, catalog),
        name: text(entry.label, 'Case ' + (index + 1), 120).trim() || 'Case ' + (index + 1) };
    });
    return { ...copy(cases[0]), cases };
  }
  const current = parseCase(study, catalog);
  if (study.comparisonCases !== undefined && !Array.isArray(study.comparisonCases)) throw new Error('The saved comparison list is invalid.');
  const cases = (study.comparisonCases || []).map((entry) => parseCase(entry, catalog));
  return { ...current, cases };
}
