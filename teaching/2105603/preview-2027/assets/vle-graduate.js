import { flash } from '../../labs/assets/thermo.js';

export const GRADUATE_VERSION = 1;
export const GRADUATE_DEFAULTS = Object.freeze({ T: 0.2, P: 0.5, z: 0.005, psat1: 1, psat2: 1 });
export const FACTORS = [
  { key: 'T', name: 'Temperature T', unit: 'K', max: 10 },
  { key: 'P', name: 'Operating pressure P', unit: 'kPa', max: 20 },
  { key: 'z', name: 'Feed composition z₁', unit: 'mol/mol', max: 0.2 },
  { key: 'psat1', name: 'Component 1 correlation scale', unit: '%', max: 20 },
  { key: 'psat2', name: 'Component 2 correlation scale', unit: '%', max: 20 },
];
export const NOTE_KEYS = ['assumptions', 'comparison', 'sensitivity', 'limits', 'concept1', 'concept2', 'concept3'];
const clone = (value) => JSON.parse(JSON.stringify(value));

export function graduateControls(raw = undefined) {
  if (raw === undefined) raw = {};
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw new Error('The graduate investigation record is invalid.');
  if (raw.version !== undefined && raw.version !== GRADUATE_VERSION) throw new Error('This graduate investigation uses an unsupported version.');
  const sourceBounds = raw.bounds === undefined ? GRADUATE_DEFAULTS : raw.bounds;
  if (!sourceBounds || typeof sourceBounds !== 'object' || Array.isArray(sourceBounds)) throw new Error('The sensitivity bounds are invalid.');
  const bounds = {};
  for (const factor of FACTORS) {
    const value = sourceBounds[factor.key];
    if (!Number.isFinite(value) || value < 0 || value > factor.max) {
      throw new Error(factor.name + ' half-width must be from 0 to ' + factor.max + ' ' + factor.unit + '.');
    }
    bounds[factor.key] = value;
  }
  const sourceNotes = raw.notes === undefined ? {} : raw.notes;
  if (!sourceNotes || typeof sourceNotes !== 'object' || Array.isArray(sourceNotes)) throw new Error('The graduate explanations are invalid.');
  const notes = {};
  for (const key of NOTE_KEYS) {
    const value = sourceNotes[key] ?? '';
    if (typeof value !== 'string' || value.length > 10000) throw new Error('Each graduate explanation must be text of at most 10000 characters.');
    notes[key] = value;
  }
  const flags = {};
  for (const key of ['sensitivityRequested', 'comparisonRequested']) {
    const value = raw[key] ?? false;
    if (typeof value !== 'boolean') throw new Error('The graduate calculation flag is invalid.');
    flags[key] = value;
  }
  return { version: GRADUATE_VERSION, bounds, notes, ...flags };
}

function parameters(values) {
  if (values.model === 'ideal') return 0;
  if (values.model === 'margules') return values.A;
  if (values.model === 'margules2') return { A12: values.A12, A21: values.A21 };
  return { model: 'nrtl', tau12: values.tau12, tau21: values.tau21,
    alpha: values.alpha, referenceT: values.referenceT, temperatureMode: values.temperatureMode };
}

export function scaledProperty(record, scales) {
  const changed = clone(record);
  changed.components.forEach((component, index) => {
    const scale = scales[index];
    if (!Number.isFinite(scale) || scale <= 0) throw new Error('Each saturation-pressure scale must be positive.');
    if (component.equation === 'clausius') component.PrefPa *= scale;
    else if (component.equation === 'antoine') component.A += Math.log10(scale);
    else if (component.equation === 'fixed') component.pressurePa *= scale;
    else throw new Error('Unsupported saturation-pressure correlation.');
  });
  return changed;
}

function run(baseline, shifts, label, kind, factor = null) {
  const values = clone(baseline.values);
  for (const key of ['T', 'P', 'z']) values[key] += shifts[key] || 0;
  const scales = [1 + (shifts.psat1 || 0) / 100, 1 + (shifts.psat2 || 0) / 100];
  try {
    const property = scaledProperty(baseline.propertyRecord, scales);
    const result = flash(property, values.T, values.P * 1000, values.z, parameters(values));
    return { label, kind, factor, shifts: clone(shifts), inputs: { T: values.T, P: values.P, z: values.z },
      scales, status: result.beta === null ? 'indeterminate' : 'finite', phase: result.phase,
      beta: result.beta, x: result.x, y: result.y, balanceResidual: result.balanceResidual,
      deltaBeta: result.beta === null || baseline.result.beta === null ? null : result.beta - baseline.result.beta };
  } catch (error) {
    return { label, kind, factor, shifts: clone(shifts), inputs: { T: values.T, P: values.P, z: values.z },
      scales, status: 'failed', phase: null, beta: null, x: null, y: null, deltaBeta: null,
      reason: error.message, code: error.code || 'DOMAIN' };
  }
}

function counts(rows) {
  const finite = rows.filter((row) => row.status === 'finite');
  const phases = {};
  for (const row of rows.filter((row) => row.status !== 'failed')) phases[row.phase] = (phases[row.phase] || 0) + 1;
  return { total: rows.length, finite: finite.length,
    indeterminate: rows.filter((row) => row.status === 'indeterminate').length,
    failed: rows.filter((row) => row.status === 'failed').length,
    minBeta: finite.length ? Math.min(...finite.map((row) => row.beta)) : null,
    maxBeta: finite.length ? Math.max(...finite.map((row) => row.beta)) : null,
    phases };
}

export function sensitivityStudy(baseline, suppliedBounds = GRADUATE_DEFAULTS) {
  const controls = graduateControls({ bounds: suppliedBounds });
  const bounds = controls.bounds;
  const oat = FACTORS.flatMap((factor) => [-1, 1].map((sign) => run(baseline,
    { [factor.key]: sign * bounds[factor.key] }, factor.name + (sign < 0 ? ' −' : ' +'), 'one-at-a-time', factor.key)));
  const corners = Array.from({ length: 32 }, (_, index) => {
    const shifts = Object.fromEntries(FACTORS.map((factor, bit) => [factor.key, (index & (1 << bit) ? 1 : -1) * bounds[factor.key]]));
    return run(baseline, shifts, 'Corner ' + (index + 1), 'joint-corner');
  });
  const ranking = FACTORS.map((factor) => {
    const rows = oat.filter((row) => row.factor === factor.key);
    const deltas = rows.filter((row) => row.deltaBeta !== null).map((row) => Math.abs(row.deltaBeta));
    return { factor: factor.key, name: factor.name, maxAbsoluteDeltaBeta: deltas.length ? Math.max(...deltas) : null,
      phaseChanged: rows.some((row) => row.status !== 'failed' && row.phase !== baseline.result.phase),
      failed: rows.filter((row) => row.status === 'failed').length };
  }).sort((a, b) => (b.maxAbsoluteDeltaBeta ?? -1) - (a.maxAbsoluteDeltaBeta ?? -1));
  return { version: GRADUATE_VERSION, bounds, baseline: { values: clone(baseline.values),
    beta: baseline.result.beta, phase: baseline.result.phase }, oat, corners,
    oatSummary: counts(oat), cornerSummary: counts(corners), ranking,
    method: 'Ten signed one-at-a-time scenarios and 32 signed corner combinations. Zero half-widths can repeat a state. Correlation-scale factors multiply the entire pure-component vapor-pressure correlation over its valid domain.',
    interpretation: 'A deterministic sampled scenario range, not a confidence interval, probability, or proven global bound. Inputs are assumed independently variable within the entered half-widths; correlations between their errors have not been specified.' };
}

export function modelStudy(baseline) {
  const rows = ['ideal', 'margules', 'margules2', 'nrtl'].map((model) => {
    const values = { ...baseline.values, model };
    const descriptions = {
      ideal: 'γ₁ = γ₂ = 1', margules: 'A = ' + values.A,
      margules2: 'A₁₂ = ' + values.A12 + ', A₂₁ = ' + values.A21,
      nrtl: 'τ₁₂ = ' + values.tau12 + ', τ₂₁ = ' + values.tau21 + ', α = ' + values.alpha
        + ', ' + values.temperatureMode + ', reference T = ' + values.referenceT + ' K',
    };
    try {
      const result = flash(baseline.propertyRecord, values.T, values.P * 1000, values.z, parameters(values));
      return { model, parameters: descriptions[model], status: result.beta === null ? 'indeterminate' : 'finite',
        phase: result.phase, beta: result.beta, x: result.x, y: result.y };
    } catch (error) {
      return { model, parameters: descriptions[model], status: 'failed', phase: null, beta: null, x: null, y: null,
        reason: error.message, code: error.code || 'DOMAIN' };
    }
  });
  return { baseline: { T: baseline.values.T, P: baseline.values.P, z: baseline.values.z }, rows,
    interpretation: 'All four candidates retain ideal vapor and neglected pressure corrections. Parameter values come from the model controls and are hypothetical teaching inputs unless independently calibrated. A difference between candidates is model spread, not an uncertainty distribution or model validation.' };
}

export function restoreGraduate(raw, baseline) {
  const controls = graduateControls(raw);
  return { ...controls,
    sensitivity: controls.sensitivityRequested ? sensitivityStudy(baseline, controls.bounds) : null,
    comparison: controls.comparisonRequested ? modelStudy(baseline) : null };
}
