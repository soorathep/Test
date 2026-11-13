/** Deterministic investigations. No probability model or statistical coverage is assigned. */
import * as engine from '../../labs/assets/consistency.js';
import { infer } from '../../labs/assets/case-study.js';

export const DEFAULT_SETTINGS = Object.freeze({
  dataset: 'syntheticT', scenario: 'clean', amplitude: 0.25,
  count: 81, extension: 'none', heat: true,
});
export const DEFAULT_BOUNDS = Object.freeze({ T: 0.1, P: 0.5, x: 0.002, y: 0.002 });
export const DEFAULT_REQUESTS = Object.freeze({ controls: false, grids: false, endpoints: false, sensitivity: false });
const finite = (raw, label) => {
  if ((typeof raw !== 'number' && typeof raw !== 'string') || (typeof raw === 'string' && !raw.trim())) {
    throw new Error('Enter ' + label + '.');
  }
  const value = Number(raw);
  if (!Number.isFinite(value)) throw new Error(label + ' must be finite.');
  return value;
};
const object = (value, label) => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(label + ' is invalid.');
  return value;
};

export function normalizeSettings(raw = {}) {
  object(raw, 'Scientific settings');
  const settings = { ...DEFAULT_SETTINGS, ...raw };
  if (!['syntheticT', 'syntheticP', 'article60', 'article80'].includes(settings.dataset)) throw new Error('Choose a supported data set.');
  if (!['clean', 'offset', 'cancel', 'local'].includes(settings.scenario)) throw new Error('Choose a controlled perturbation.');
  settings.amplitude = finite(settings.amplitude, 'log-activity perturbation amplitude');
  if (Math.abs(settings.amplitude) > 0.5) throw new Error('The log-activity perturbation amplitude must lie between −0.5 and 0.5.');
  settings.count = finite(settings.count, 'sampling resolution');
  if (![41, 81, 161].includes(settings.count)) throw new Error('Choose 41, 81 or 161 composition points.');
  if (!['none', 'linear', 'quadratic'].includes(settings.extension)) throw new Error('Choose a supported endpoint assumption.');
  if (typeof settings.heat !== 'boolean') throw new Error('The heat-correction setting must be true or false.');
  return Object.fromEntries(Object.keys(DEFAULT_SETTINGS).map(key => [key, settings[key]]));
}

export function normalizeBounds(raw = {}) {
  object(raw, 'Sensitivity half-widths');
  const bounds = { ...DEFAULT_BOUNDS, ...raw };
  const upper = { T: 2, P: 5, x: 0.02, y: 0.02 };
  for (const key of Object.keys(DEFAULT_BOUNDS)) {
    bounds[key] = finite(bounds[key], 'the ' + key + ' half-width');
    if (bounds[key] < 0 || bounds[key] > upper[key]) throw new Error(key + ' half-width must lie between 0 and ' + upper[key] + '.');
  }
  return Object.fromEntries(Object.keys(DEFAULT_BOUNDS).map(key => [key, bounds[key]]));
}

export function normalizeRequests(raw = {}) {
  object(raw, 'Graduate investigation choices');
  const requests = { ...DEFAULT_REQUESTS, ...raw };
  for (const key of Object.keys(DEFAULT_REQUESTS)) if (typeof requests[key] !== 'boolean') throw new Error('Graduate investigation choices must be true or false.');
  return Object.fromEntries(Object.keys(DEFAULT_REQUESTS).map(key => [key, requests[key]]));
}

export function analyze(rawSettings, data) {
  const settings = normalizeSettings(rawSettings);
  const set = settings.dataset.startsWith('article')
    ? engine.articleSet(data, Number(settings.dataset.slice(7)))
    : engine.syntheticSet(data, { path: settings.dataset === 'syntheticT' ? 'isothermal' : 'isobaric',
      kind: settings.scenario, amplitude: settings.amplitude, n: settings.count });
  if (set.valid.length < 3) throw new Error('At least three valid activity pairs are needed for the guided diagnostics.');
  const area = engine.areaAnalysis(set, set.synthetic ? 'none' : settings.extension);
  const local = engine.differential(set, settings.heat);
  return { settings, set, area, local };
}

export function summarize(analysis, label = '') {
  const { settings, set, area, local } = analysis;
  return { label, settings, I: area.area.signed, D: area.area.D, J: area.J, DminusJ: area.DminusJ,
    score: local.score, maxResidual: Math.max(...local.points.map(row => Math.abs(row.residual))),
    peakScore: 100 * Math.max(...local.points.map(row => Math.abs(row.residual))),
    areaStatus: set.path === 'isothermal' ? area.redlichKister.status : area.herington.status,
    localStatus: local.status, conditional: area.conditional, count: set.valid.length,
    excluded: set.excluded.length, xmin: area.area.xmin, xmax: area.area.xmax, analysis };
}

export function compareControls(data, rawSettings) {
  const settings = normalizeSettings(rawSettings);
  if (settings.dataset.startsWith('article')) throw new Error('Choose synthetic isothermal or isobaric data for the controlled-error comparison.');
  const labels = { clean: 'Consistent reference', offset: 'Uniform log-ratio shift', cancel: 'Canceling error', local: 'Localized defect' };
  return { rows: ['clean', 'offset', 'cancel', 'local'].map(scenario =>
    summarize(analyze({ ...settings, scenario }, data), labels[scenario])),
    note: 'The same path, resolution and amplitude are retained. The clean reference has no imposed error. Synthetic endpoint limits are known.' };
}

export function compareGrids(data, rawSettings) {
  const settings = normalizeSettings(rawSettings);
  if (settings.dataset.startsWith('article')) throw new Error('Sampling-resolution experiments require a synthetic generator; no extra article measurements are invented.');
  return { rows: [41, 81, 161].map(count => summarize(analyze({ ...settings, count }, data), count + ' points')),
    note: 'These grids resample the same known synthetic function. Grid changes mix integration and differentiation error; they are not measurement uncertainty or additional experimental evidence.' };
}

export function compareEndpoints(data, rawSettings) {
  const settings = normalizeSettings(rawSettings);
  if (!settings.dataset.startsWith('article')) throw new Error('Choose article data to investigate missing endpoint intervals.');
  const labels = { none: 'No endpoint extension', linear: 'Linear endpoint extension', quadratic: 'Global quadratic smoothing and extension' };
  return { rows: ['none', 'linear', 'quadratic'].map(extension =>
    summarize(analyze({ ...settings, extension }, data), labels[extension])),
    note: 'The original measured rows remain unchanged. Linear extension estimates two missing limits. The quadratic option replaces the whole log-ratio curve by a fitted polynomial. Neither supplies missing excess enthalpy.' };
}

/** Eight one-factor common-bias scenarios on the fixed nominal included set. */
export function measurementSensitivity(data, rawSettings, rawBounds = {}) {
  const settings = normalizeSettings(rawSettings), bounds = normalizeBounds(rawBounds);
  if (!settings.dataset.startsWith('article')) throw new Error('Choose article data for the measurement-bias sensitivity exercise.');
  const baseline = analyze(settings, data), nominal = summarize(baseline, 'Nominal measurements');
  const eligibleIndices = baseline.set.rows.map((row, index) => row.ln ? index : -1).filter(index => index >= 0);
  const eligible = new Set(eligibleIndices);
  const rows = [];
  for (const factor of ['T', 'P', 'x', 'y']) for (const sign of [-1, 1]) {
    const label = factor + (sign < 0 ? ' − ' : ' + ') + bounds[factor];
    const scenario = { label, factor, sign, shift: sign * bounds[factor], status: 'rejected', reason: '' };
    try {
      const changed = baseline.set.rows.map((original, index) => {
        const row = { T: original.T, PkPa: original.PkPa, x: original.x, y: original.y };
        // Calibration offsets in T or P apply to every observation. Composition
        // offsets apply to measured interior rows, preserving pure-component identities.
        if (factor === 'T') row.T += sign * bounds.T;
        if (factor === 'P') row.PkPa += sign * bounds.P;
        if ((factor === 'x' || factor === 'y') && original.x > 0 && original.x < 1) row[factor] += sign * bounds[factor];
        if (!(row.T > 0 && row.PkPa > 0 && row.x >= 0 && row.x <= 1 && row.y >= 0 && row.y <= 1)) {
          if (eligible.has(index)) throw new Error('A nominally included observation leaves the physical composition or pressure domain. The entire scenario is rejected.');
          return { ...row, ln: null, reason: original.reason || 'Outside the physical domain after the assumed shift.' };
        }
        const inferred = infer(row, data);
        if (eligible.has(index) && !inferred.ln) throw new Error('A nominally included observation is unavailable: ' + inferred.reason + ' The entire scenario is rejected.');
        // Keep the nominal inclusion mask: an excluded source point does not enter
        // the comparison merely because a calibration scenario moves its value.
        return eligible.has(index) ? { ...inferred, f: inferred.ln[0] - inferred.ln[1] }
          : { ...row, ln: null, reason: 'Excluded in the nominal source set: ' + (original.reason || 'No nominal activity pair.') };
      });
      const valid = eligibleIndices.map(index => changed[index]).sort((a, b) => a.x - b.x);
      if (valid.some((row, index) => index && row.x <= valid[index - 1].x)) throw new Error('The perturbed included compositions are not distinct. The entire scenario is rejected.');
      const set = { ...baseline.set, rows: changed, valid, excluded: changed.filter(row => !row.ln),
        endpointsKnown: false, name: baseline.set.name + ' · ' + label };
      const area = engine.areaAnalysis(set, settings.extension), local = engine.differential(set, settings.heat);
      Object.assign(scenario, summarize({ settings, set, area, local }, label), { status: 'ok', reason: '' });
    } catch (error) { scenario.reason = error.message; }
    rows.push(scenario);
  }
  return { bounds, nominal, rows, accepted: rows.filter(row => row.status === 'ok').length,
    rejected: rows.filter(row => row.status !== 'ok').length,
    note: 'Eight deterministic one-factor common-bias scenarios, not independent random errors or a joint uncertainty region. T and P offsets apply to all observations; x and y offsets apply to measured interior rows while pure identities remain fixed. The nominal activity-inclusion mask is retained. Invalid included rows reject an entire scenario without clipping, extrapolation or silent deletion. No probability, coverage or confidence interval is assigned.' };
}

export function runGraduate(data, settings, bounds, rawRequests) {
  const requests = normalizeRequests(rawRequests), normalized = normalizeSettings(settings);
  const result = {};
  // A saved study may retain an inactive experiment flag after switching paths.
  // Only scientifically applicable experiments are evaluated for its current set.
  if (!normalized.dataset.startsWith('article')) {
    if (requests.controls) result.controls = compareControls(data, normalized);
    if (requests.grids) result.grids = compareGrids(data, normalized);
  } else {
    if (requests.endpoints) result.endpoints = compareEndpoints(data, normalized);
    if (requests.sensitivity) result.sensitivity = measurementSensitivity(data, normalized, bounds);
  }
  return result;
}
