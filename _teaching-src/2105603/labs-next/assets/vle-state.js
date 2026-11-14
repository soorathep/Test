import {
  VERSION, flash, bubbleP, dewP, bubbleT, dewT, diagram, parameters, psat,
} from '../../labs/assets/thermo.js';
import { restoreGraduate } from './vle-graduate.js';

export const GUIDED_VLE_VERSION = 1;
export const MODELS = ['ideal', 'margules', 'margules2', 'nrtl'];
export const CASES = {
  baseline: { name: 'Starting case', P: 90, task: 'At 350 K and 90 kPa, which phases form and how much feed becomes vapor?' },
  compressed: { name: 'Higher pressure', P: 100, task: 'Raise the pressure to 100 kPa. Predict which phase or phases remain.' },
  'low-pressure': { name: 'Lower pressure', P: 75, task: 'Lower the pressure to 75 kPa. Predict which phase or phases remain.' },
  bubble: { name: 'Bubble boundary', boundary: 'bubble', task: 'At the feed bubble pressure, identify the incipient phase and its composition.' },
  dew: { name: 'Dew boundary', boundary: 'dew', task: 'At the feed dew pressure, identify the incipient phase and its composition.' },
  real: { name: 'Real data · benzene + toluene', system: 'benzene-toluene', T: 350, P: 50, task: 'At 350 K and 50 kPa, which phases form and how much feed becomes vapor?',
    source: 'Real properties: benzene (1) + toluene (2) with NIST Antoine vapor pressures (Willingham et al., J. Res. NBS 1945) and an ideal liquid. At 350 K, P₁ˢᵃᵗ = 91.6 kPa and P₂ˢᵃᵗ = 34.8 kPa. Raoult’s law is an approximation for this pair; no measured mixture data are used here.' },
};

export function copy(value) {
  return JSON.parse(JSON.stringify(value));
}

function number(value, label) {
  if (!Number.isFinite(value)) throw new Error(label + ' must be a finite number.');
  return value;
}

function recordRange(value, label) {
  if (!Array.isArray(value) || value.length !== 2 || !value.every(Number.isFinite)
    || value[0] <= 0 || value[1] < value[0]) {
    throw new Error(label + ' needs a valid temperature range in kelvin.');
  }
  return [...value];
}

export function validatePropertyRecord(record) {
  if (!record || typeof record !== 'object' || Array.isArray(record)
    || !Array.isArray(record.components) || record.components.length !== 2) {
    throw new Error('This study needs a binary property record with two components.');
  }
  const checked = copy(record);
  checked.rangeK = recordRange(checked.rangeK, 'The mixture');
  checked.components.forEach((component, index) => {
    if (!component || typeof component !== 'object' || typeof component.name !== 'string'
      || !component.name.trim()) throw new Error('Each component needs a name.');
    component.rangeK = recordRange(component.rangeK, 'Component ' + (index + 1));
    if (checked.rangeK[0] < component.rangeK[0] || checked.rangeK[1] > component.rangeK[1]) {
      throw new Error('The mixture temperature range must be inside both component ranges.');
    }
    const required = {
      fixed: ['pressurePa'],
      clausius: ['PrefPa', 'HvapJmol', 'Tref'],
      antoine: ['A', 'B', 'C'],
    }[component.equation];
    if (!required) throw new Error('The property record uses an unsupported vapor-pressure equation.');
    required.forEach((key) => number(component[key], 'Component ' + (index + 1) + ' ' + key));
    if (component.equation === 'antoine'
      && ((component.temperatureUnit && component.temperatureUnit !== 'K')
        || (component.pressureUnit && component.pressureUnit !== 'bar'))) {
      throw new Error('This Antoine property record must use kelvin and bar.');
    }
  });
  if (checked.label !== undefined && typeof checked.label !== 'string') {
    throw new Error('The property-record label must be text.');
  }
  if (checked.description !== undefined && typeof checked.description !== 'string') {
    throw new Error('The property-record description must be text.');
  }
  if (checked.sources !== undefined && !Array.isArray(checked.sources)) {
    throw new Error('Property sources must be a list.');
  }
  return checked;
}

export function defaults(system = 'synthetic', record = null) {
  const T = record?.defaultT ?? record?.rangeK?.[0] ?? 350;
  return {
    system, model: 'ideal', T, P: system === 'synthetic' ? 90 : (record?.defaultP ?? 90000) / 1000,
    z: 0.4, A: 1, A12: 1.5, A21: 0.5, tau12: 0.5, tau21: 0.5, alpha: 0.3,
    temperatureMode: 'fixed', referenceT: T, chart: 'pxy', compare: true,
  };
}

export function normalizeValues(input, propertyRecord) {
  if (!input || typeof input !== 'object' || Array.isArray(input)) {
    throw new Error('This study needs an input object.');
  }
  if (typeof input.system !== 'string' || !input.system.trim()) {
    throw new Error('Choose a component system.');
  }
  const record = validatePropertyRecord(propertyRecord);
  const values = { ...defaults(input.system, record), ...input, chart: 'pxy' };
  if (!MODELS.includes(values.model)) throw new Error('Choose a supported liquid model.');
  for (const [key, label] of [['T', 'Temperature'], ['P', 'Pressure'], ['z', 'Feed mole fraction']]) {
    number(values[key], label);
  }
  if (values.P < 1 || values.P > 200) throw new Error('Pressure must be between 1 and 200 kPa.');
  if (values.z < 0 || values.z > 1) throw new Error('Feed mole fraction must be between 0 and 1.');
  if (values.T < record.rangeK[0] || values.T > record.rangeK[1]) {
    throw new Error('Temperature must be between ' + record.rangeK.join(' and ') + ' K for this system.');
  }
  const active = {
    ideal: [], margules: ['A'], margules2: ['A12', 'A21'],
    nrtl: ['tau12', 'tau21', 'alpha', 'referenceT'],
  }[values.model];
  const fallback = defaults(values.system, record);
  for (const key of ['A', 'A12', 'A21', 'tau12', 'tau21', 'alpha', 'referenceT']) {
    if (!Number.isFinite(values[key])) {
      if (active.includes(key)) throw new Error(key + ' must be a finite number.');
      values[key] = fallback[key];
    }
  }
  if (typeof values.compare !== 'boolean') throw new Error('The ideal-reference selection must be true or false.');
  const sat = record.components.map((component) => psat(component, values.T));
  if (!sat.every((value) => Number.isFinite(value) && value > 0)) {
    throw new Error('The supplied vapor-pressure correlation does not give positive finite pressures.');
  }
  if (values.system === 'fit-transfer') {
    if (record.rangeK[0] !== record.rangeK[1]
      || record.components.some((component) => component.equation !== 'fixed')) {
      throw new Error('A transferred fit needs fixed-temperature property data. Open it in the original Lab 01.');
    }
    for (const [index, key] of ['fitP1', 'fitP2'].entries()) {
      const expected = record.components[index].pressurePa / 1000;
      if (values[key] !== undefined && (!Number.isFinite(values[key])
        || Math.abs(values[key] - expected) > 1e-8 * Math.max(1, expected))) {
        throw new Error('The transferred vapor pressures disagree with the saved property record.');
      }
      values[key] = expected;
    }
    if (values.temperatureMode !== 'fixed' || Math.abs(values.referenceT - values.T) > 1e-8) {
      throw new Error('The transferred fit needs its saved fixed-temperature context. Open it in the original Lab 01.');
    }
  }
  parameters(modelParameters(values));
  return values;
}

export function modelParameters(values) {
  if (values.model === 'ideal') return 0;
  if (values.model === 'margules') return values.A;
  if (values.model === 'margules2') return { A12: values.A12, A21: values.A21 };
  return {
    model: 'nrtl', tau12: values.tau12, tau21: values.tau21, alpha: values.alpha,
    temperatureMode: values.temperatureMode, referenceT: values.referenceT,
  };
}

export function calculateVLE(input, propertyRecord) {
  const property = validatePropertyRecord(propertyRecord);
  const values = normalizeValues(input, property);
  const result = flash(property, values.T, values.P * 1000, values.z, modelParameters(values));
  result.phaseAmounts = result.beta === null
    ? { liquid: null, vapor: null }
    : { liquid: 1 - result.beta, vapor: result.beta };
  return { values, propertyRecord: property, result };
}

export function caseValues(key, catalog) {
  const choice = CASES[key];
  if (!choice) throw new Error('Choose a named starting case.');
  const systemKey = choice.system ?? 'synthetic', property = catalog.systems[systemKey];
  const values = defaults(systemKey, property);
  if (Number.isFinite(choice.T)) { values.T = choice.T; values.referenceT = choice.T; }
  if (choice.boundary === 'bubble') values.P = bubbleP(property, 350, 0.4, 0).P / 1000;
  else if (choice.boundary === 'dew') values.P = dewP(property, 350, 0.4, 0).P / 1000;
  else values.P = choice.P;
  return { values, propertyRecord: copy(property), name: choice.name, task: choice.task, source: choice.source ?? '' };
}

export function pressureCurves(values, property) {
  const selected = diagram(property, values.T, values.P * 1000, modelParameters(values), 'pxy');
  return {
    selected,
    ideal: values.compare && values.model !== 'ideal'
      ? diagram(property, values.T, values.P * 1000, 0, 'pxy') : null,
  };
}

export function temperatureBoundaries(values, property) {
  return [['Bubble', bubbleT], ['Dew', dewT]].map(([name, solve]) => {
    try {
      return { name, T: solve(property, values.P * 1000, values.z, modelParameters(values)).T };
    } catch (error) {
      return { name, T: null, message: error.code === 'FIXED_T'
        ? 'Requires temperature-dependent vapor pressures and an explicit temperature assumption.'
        : error.message };
    }
  });
}

function shortName(value, fallback) {
  if (value === undefined || value === '') return fallback;
  if (typeof value !== 'string' || value.length > 120) throw new Error('Use a short text case name.');
  return value.trim() || fallback;
}

function prediction(value) {
  if (value === undefined || value === '') return '';
  if (typeof value !== 'string') throw new Error('The recorded prediction must be text.');
  if (!['liquid', 'two-phase', 'vapor', 'boundary'].includes(value)) {
    // Original Lab 01 used an unrestricted prediction textarea.
    return value;
  }
  return value;
}

function inputsFromWorkspace(study) {
  const workspace = study.workspace;
  if (workspace?.schema !== 'thermo-controls-v1' || workspace.lab !== 'index'
    || !workspace.controls || typeof workspace.controls !== 'object') return null;
  const c = workspace.controls;
  const values = { system: c.system, model: c.model };
  for (const key of ['T', 'P', 'z', 'A', 'A12', 'A21', 'tau12', 'tau21', 'alpha', 'referenceT']) {
    if (c[key] !== undefined && c[key] !== '') values[key] = Number(c[key]);
  }
  if (c.temperatureMode !== undefined) values.temperatureMode = c.temperatureMode;
  if (c.compare !== undefined) values.compare = c.compare;
  if (c['fit-p1'] !== undefined) values.fitP1 = Number(c['fit-p1']);
  if (c['fit-p2'] !== undefined) values.fitP2 = Number(c['fit-p2']);
  values.fitKind = workspace.context?.fitKind;
  return values;
}

function parseCase(study, catalog, fallbackName) {
  if (!study || typeof study !== 'object' || Array.isArray(study)) {
    throw new Error('A comparison case is not a calculator study.');
  }
  if (study.guidedVersion !== undefined && study.guidedVersion !== GUIDED_VLE_VERSION) {
    throw new Error('Open this guided study with the version that created it.');
  }
  const native = study.schema === 'skh-thermo-experiment/1' ? study.inputs : null;
  const values = native || inputsFromWorkspace(study);
  if (!values) throw new Error('Choose a Lab 01 calculator study, input file or comparison collection.');
  const property = study.propertyRecord || catalog.systems[values.system];
  if (!property) {
    throw new Error('The study needs its original property record. Open the file in the original Lab 01.');
  }
  const calculated = calculateVLE(values, property);
  const reflection = study.reflection ?? study.workspace?.controls?.reflection ?? '';
  const recordedPrediction = study.prediction ?? study.workspace?.controls?.prediction;
  if (typeof reflection !== 'string') {
    throw new Error('The explanation in the study must be text.');
  }
  return {
    ...calculated,
    name: shortName(study.caseName, fallbackName),
    prediction: prediction(recordedPrediction),
    reflection,
    graduate: restoreGraduate(study.graduate, calculated),
    originalContext: study.originalContext || {
      schema: study.schema || study.kind,
      chart: native?.chart || study.workspace?.controls?.['chart-kind'] || null,
    },
  };
}

export function parseStudy(text, catalog) {
  let study;
  try { study = JSON.parse(text); }
  catch { throw new Error('This file is not valid JSON. Choose a downloaded Lab 01 study.'); }
  if (study?.kind === 'thermo-comparison') {
    if (study.lab !== 'index' || !Array.isArray(study.cases) || study.cases.length === 0) {
      throw new Error('Choose a Lab 01 comparison containing at least one case.');
    }
    const cases = study.cases.map((entry, index) => ({
      ...parseCase(entry.study, catalog, 'Case ' + (index + 1)),
      name: shortName(entry.label, 'Case ' + (index + 1)),
    }));
    return { ...copy(cases[0]), cases };
  }
  const current = parseCase(study, catalog, 'Opened study');
  if (study.comparisonCases !== undefined && !Array.isArray(study.comparisonCases)) {
    throw new Error('The saved comparison list is invalid.');
  }
  const cases = (study.comparisonCases || []).map((entry, index) => (
    parseCase(entry, catalog, 'Case ' + (index + 1))
  ));
  return { ...current, cases };
}

function workspace(values, predictionText, reflection) {
  const controls = { ...values, prediction: predictionText, reflection };
  controls['chart-kind'] = 'pxy';
  for (const [key, value] of Object.entries(controls)) {
    controls[key] = typeof value === 'boolean' ? value : String(value);
  }
  if (values.system === 'fit-transfer') {
    controls['fit-p1'] = String(values.fitP1);
    controls['fit-p2'] = String(values.fitP2);
  }
  return {
    schema: 'thermo-controls-v1', lab: 'index', savedAt: new Date().toISOString(),
    context: { fitKind: values.fitKind === 'experimental' ? 'experimental' : 'synthetic' }, controls,
  };
}

function snapshot(saved, dataVersion) {
  return {
    schema: 'skh-thermo-experiment/1', engineVersion: VERSION, dataVersion,
    inputs: copy(saved.values), propertyRecord: copy(saved.propertyRecord), result: copy(saved.result),
    caseName: saved.name, prediction: saved.prediction || '', reflection: saved.reflection || '',
    graduate: restoreGraduate(saved.graduate, saved),
    ...(saved.originalContext ? { originalContext: copy(saved.originalContext) } : {}),
    ...(saved.curves ? { curves: copy(saved.curves) } : {}),
  };
}

export function makeStudy(current, cases, reflection, dataVersion) {
  return {
    ...snapshot(current, dataVersion),
    guidedVersion: GUIDED_VLE_VERSION, interface: '2105603-2027-guided-vle',
    exportedAt: new Date().toISOString(), reflection,
    workspace: workspace(current.values, current.prediction || '', reflection),
    comparisonCases: cases.map((saved) => snapshot(saved, dataVersion)),
  };
}
