/** Deterministic graduate investigations. These scenarios are not statistical intervals. */
import * as engine from '../../labs/assets/case-study.js';

/** Liquid-curvature check across the measured temperatures of the selected pressures. */
export function measuredRangeCheck(data, parameters, pressures) {
  const temps = data.datasets.filter((set) => pressures.includes(set.pressureKPa))
    .flatMap((set) => set.rows).map((row) => engine.infer(row, data)).filter((row) => row.ln).map((row) => row.T);
  if (!temps.length) return engine.modelCheck(parameters, 350);
  const lo = Math.min(...temps), hi = Math.max(...temps);
  const checks = Array.from({ length: 5 }, (_, i) => engine.modelCheck(parameters, lo + (hi - lo) * i / 4));
  const worst = checks.reduce((a, b) => (b.minSampledScaledCurvature < a.minSampledScaledCurvature ? b : a));
  return { fixedTK: worst.fixedTK, rangeK: [lo, hi], temperatures: checks.length,
    maxGibbsDuhemResidual: Math.max(...checks.map((c) => c.maxGibbsDuhemResidual)),
    minSampledScaledCurvature: worst.minSampledScaledCurvature, samples: worst.samples };
}


export const GRADUATE_CASE_VERSION = 1;
export const GRADUATE_CASE_DEFAULTS = Object.freeze({
  version: GRADUATE_CASE_VERSION,
  bounds: { T: 0.1, P: 0.5, x: 0.005, y: 0.005 },
  run: { sensitivity: false, alpha: false },
  notes: { assumptions: '', uncertainty: '', evidence: '', decision: '', concept1: '', concept2: '', concept3: '' },
});
const clone = (value) => JSON.parse(JSON.stringify(value));
const factors = ['T', 'P', 'x', 'y'];
const alphaValues = [0.30, 0.47, 0.60];
const fitCache = new Map();

export function normalizeGraduateCase(value) {
  if (value === undefined) return clone(GRADUATE_CASE_DEFAULTS);
  if (!value || typeof value !== 'object' || Array.isArray(value)
    || value.version !== GRADUATE_CASE_VERSION || !value.bounds || !value.run || !value.notes) {
    throw new Error('The saved graduate investigation has an unsupported or incomplete format.');
  }
  const checked = clone(GRADUATE_CASE_DEFAULTS);
  const maxima = { T: 5, P: 10, x: 0.1, y: 0.1 };
  for (const key of factors) {
    const number = value.bounds[key];
    if (!Number.isFinite(number) || number < 0 || number > maxima[key]) {
      throw new Error('Graduate bound ' + key + ' must be finite and between 0 and ' + maxima[key] + '.');
    }
    checked.bounds[key] = number;
  }
  for (const key of ['sensitivity', 'alpha']) {
    if (typeof value.run[key] !== 'boolean') throw new Error('The saved graduate run selection is invalid.');
    checked.run[key] = value.run[key];
  }
  for (const key of Object.keys(checked.notes)) {
    if (value.notes[key] === undefined) continue;
    if (typeof value.notes[key] !== 'string' || value.notes[key].length > 10000) {
      throw new Error('Each graduate conclusion must be text of at most 10,000 characters.');
    }
    checked.notes[key] = value.notes[key];
  }
  return checked;
}

function selectedRow(data, inputs) {
  const set = data.datasets.find((item) => item.pressureKPa === Number(inputs.inspect));
  if (!set || !Number.isInteger(inputs.selectedRow) || !set.rows[inputs.selectedRow]) {
    throw new Error('Choose a measured observation before running graduate sensitivity.');
  }
  return clone(set.rows[inputs.selectedRow]);
}

function scenario(row, data, name, changes = {}) {
  const candidate = { ...row, ...changes };
  try {
    if (![candidate.T, candidate.PkPa, candidate.x, candidate.y].every(Number.isFinite)
      || candidate.T <= 0 || candidate.PkPa <= 0
      || candidate.x < 0 || candidate.x > 1 || candidate.y < 0 || candidate.y > 1) {
      throw new Error('Scenario leaves positive T/P or the mole-fraction interval [0, 1].');
    }
    const inferred = engine.infer(candidate, data);
    if (!inferred.ln || !inferred.ln.every(Number.isFinite)) {
      return { name, row: candidate, ln: null, gamma: null, status: 'unavailable',
        reason: candidate.x === 0 || candidate.x === 1
          ? 'Pure endpoint: the absent component’s activity coefficient cannot be inferred.'
          : candidate.y === 0 || candidate.y === 1
            ? 'Vapor composition is at an endpoint: a finite logarithmic activity pair cannot be inferred.'
          : inferred.reason || 'This scenario supplies no finite activity pair.' };
    }
    const gamma = inferred.ln.map(Math.exp);
    if (!gamma.every(Number.isFinite)) throw new Error('A scenario activity coefficient is nonfinite.');
    return { name, row: candidate, ln: [...inferred.ln], gamma, status: 'valid', reason: '' };
  } catch (issue) {
    return { name, row: candidate, ln: null, gamma: null, status: 'failed', reason: issue.message };
  }
}

function extent(rows, key, index) {
  const values = rows.filter((row) => row.status === 'valid').map((row) => row[key][index]);
  return values.length ? { min: Math.min(...values), max: Math.max(...values) } : null;
}

export function observationSensitivity(data, inputs, settings) {
  const graduate = normalizeGraduateCase(settings);
  const row = selectedRow(data, inputs);
  const baseline = scenario(row, data, 'Measured baseline');
  if (baseline.status !== 'valid') {
    throw new Error('Choose a valid interior observation for the graduate sensitivity exercise. ' + baseline.reason);
  }
  const oneAtATime = [];
  for (const key of factors) {
    const property = key === 'P' ? 'PkPa' : key;
    for (const direction of [-1, 1]) {
      oneAtATime.push({ factor: key, direction,
        ...scenario(row, data, key + (direction < 0 ? ' minus bound' : ' plus bound'),
          { [property]: row[property] + direction * graduate.bounds[key] }) });
    }
  }
  const corners = Array.from({ length: 16 }, (_, mask) => {
    const changes = {};
    const signs = {};
    factors.forEach((key, index) => {
      const direction = mask & (1 << index) ? 1 : -1;
      const property = key === 'P' ? 'PkPa' : key;
      changes[property] = row[property] + direction * graduate.bounds[key];
      signs[key] = direction;
    });
    return { ...scenario(row, data, 'Corner ' + (mask + 1), changes), signs };
  });
  const ranking = factors.map((factor) => {
    const rows = oneAtATime.filter((candidate) => candidate.factor === factor);
    const valid = rows.filter((candidate) => candidate.status === 'valid');
    return { factor, valid: valid.length, attempted: rows.length,
      maxAbsDeltaLn: baseline.ln && valid.length
        ? [0, 1].map((index) => Math.max(...valid.map((candidate) => Math.abs(candidate.ln[index] - baseline.ln[index])))) : null };
  }).sort((a, b) => Math.max(...(b.maxAbsDeltaLn || [-Infinity])) - Math.max(...(a.maxAbsDeltaLn || [-Infinity])));
  return { context: { inspect: inputs.inspect, selectedRow: inputs.selectedRow, row },
    bounds: clone(graduate.bounds), baseline, oneAtATime, corners, ranking,
    counts: { attempted: corners.length, valid: corners.filter((item) => item.status === 'valid').length,
      unavailable: corners.filter((item) => item.status === 'unavailable').length,
      failed: corners.filter((item) => item.status === 'failed').length },
    ranges: { ln: [0, 1].map((index) => extent(corners, 'ln', index)),
      gamma: [0, 1].map((index) => extent(corners, 'gamma', index)) },
    limits: 'Eight one-factor scenarios and sixteen joint corners are deterministic samples. Repeated scenarios occur for zero bounds. Their range is not a confidence interval, probability statement or guaranteed full range. No values are clipped or extrapolated.' };
}

function fittedFor(data, pressures, alpha) {
  const key = JSON.stringify({ data, pressures, alpha });
  if (!fitCache.has(key)) {
    const valid = pressures.flatMap((pressure) => data.datasets.find((set) => set.pressureKPa === pressure).rows
      .map((row) => engine.infer(row, data))).filter((row) => row.ln);
    if (!valid.length) throw new Error('No valid pairs are available for this alpha comparison.');
    const fit = engine.fit(valid, alpha);
    fitCache.set(key, { ...fit, trainingPairs: valid.length });
    if (fitCache.size > 32) fitCache.delete(fitCache.keys().next().value);
  }
  return clone(fitCache.get(key));
}

export function alphaSensitivity(data, inputs) {
  const pressures = inputs.train === 'both' ? [60, 80] : [Number(inputs.train)];
  if (!pressures.every((pressure) => data.datasets.some((set) => set.pressureKPa === pressure))) {
    throw new Error('Choose supplied training observations for the alpha comparison.');
  }
  const evaluating = data.datasets.find((set) => set.pressureKPa === Number(inputs.evaluate));
  if (!evaluating) throw new Error('Choose a supplied checking pressure.');
  const valid = evaluating.rows.map((row) => engine.infer(row, data)).filter((row) => row.ln);
  const rows = alphaValues.map((alpha) => {
    try {
      const fit = fittedFor(data, pressures, alpha);
      const check = measuredRangeCheck(data, fit.parameters, [...new Set([...pressures, Number(inputs.evaluate)])]);
      return { alpha, status: 'valid', tau12: fit.parameters.a12, tau21: fit.parameters.a21,
        trainingPairs: fit.trainingPairs, checkingPairs: valid.length,
        trainingRMSE: fit.rmse, checkingRMSE: Math.sqrt(engine.objective(valid, fit.parameters)),
        converged: fit.converged, atBound: fit.atBound,
        minSampledScaledCurvature: check.minSampledScaledCurvature,
        fixedTK: check.fixedTK, rangeK: check.rangeK, reason: '' };
    } catch (issue) { return { alpha, status: 'failed', reason: issue.message }; }
  });
  return { context: { train: inputs.train, pressures, evaluate: Number(inputs.evaluate) }, rows,
    heldOut: !pressures.includes(Number(inputs.evaluate)),
    limits: 'Each row refits only the same training observations while holding a different alpha fixed. The original data and current retained model are unchanged. This is conditional sensitivity, not a confidence interval, bootstrap, joint three-parameter fit or proof of non-identifiability.' };
}

export function analyzeGraduateCase(data, inputs, settings) {
  const graduate = normalizeGraduateCase(settings);
  return { settings: graduate,
    sensitivity: graduate.run.sensitivity ? observationSensitivity(data, inputs, graduate) : null,
    alpha: graduate.run.alpha ? alphaSensitivity(data, inputs) : null };
}
