/** Lab 04 graduate investigations: local versus global evidence, bounded
 * parameter sensitivity and model-form comparison at matched dilute limits.
 * Pure functions; the page module renders the results. */
import * as engine from '../../labs/assets/stability.js';

export const STABILITY_GRADUATE_VERSION = '1.0.0';
export const MODELS = Object.freeze(['symmetric', 'asymmetric', 'nrtl']);
export const PARAMETER_KEYS = Object.freeze({ symmetric: ['A'], asymmetric: ['A12', 'A21'], nrtl: ['tau12', 'tau21', 'alpha'] });
export const PARAMETER_LABELS = Object.freeze({ A: 'A', A12: 'A₁₂', A21: 'A₂₁', tau12: 'τ₁₂', tau21: 'τ₂₁', alpha: 'α', z: 'z₁' });
export const DEFAULT_BOUNDS = Object.freeze({ A: 0.1, A12: 0.1, A21: 0.1, tau12: 0.1, tau21: 0.1, alpha: 0.02, z: 0.005 });
export const MATCH_ALPHAS = Object.freeze([0.2, 0.3, 0.47]);

const finite = (value, label) => {
  if (!Number.isFinite(value)) throw new RangeError(label + ' must be a finite number.');
  return value;
};

/** Engine parameter object for the selected liquid model. */
export function modelParameters(inputs) {
  const model = inputs.model;
  if (!MODELS.includes(model)) throw new RangeError('Choose a supported liquid model.');
  if (model === 'symmetric') return finite(inputs.A, 'A');
  if (model === 'asymmetric') return { A12: finite(inputs.A12, 'A₁₂'), A21: finite(inputs.A21, 'A₂₁') };
  return { model: 'nrtl', tau12: finite(inputs.tau12, 'τ₁₂'), tau21: finite(inputs.tau21, 'τ₂₁'), alpha: finite(inputs.alpha, 'α') };
}

/** Infinite-dilution log activity coefficients of the selected model. */
export function dilutionLimits(inputs) {
  if (inputs.model === 'symmetric') return [inputs.A, inputs.A];
  if (inputs.model === 'asymmetric') return [inputs.A12, inputs.A21];
  const g12 = Math.exp(-inputs.alpha * inputs.tau12), g21 = Math.exp(-inputs.alpha * inputs.tau21);
  return [inputs.tau21 + inputs.tau12 * g12, inputs.tau12 + inputs.tau21 * g21];
}

/** One equilibrium calculation, reduced to the quantities the lab reports. */
export function solve(inputs) {
  const parameters = modelParameters(inputs), z = finite(inputs.z, 'z₁');
  const r = engine.equilibrium(parameters, z), spin = engine.spinodals(parameters);
  return {
    parameters, z, phase: r.phase, state: r.state, xAlpha: r.xAlpha, xBeta: r.xBeta,
    fractionAlpha: r.fractionAlpha, fractionBeta: r.fractionBeta,
    gapAlpha: r.binodal?.xAlpha ?? null, gapBeta: r.binodal?.xBeta ?? null, gapCount: r.gaps.length,
    homogeneousG: r.homogeneousG, equilibriumG: r.equilibriumG, gain: r.gain, curvature: r.curvature,
    tpdMinimum: r.tpd.minimum, tpdTrial: r.tpd.w, tpdStatus: r.tpd.status,
    balanceResidual: r.balanceResidual, chemicalPotentialResidual: r.chemicalPotentialResidual,
    tangentResidual: r.binodal?.tangentResidual ?? null, tangentSlope: r.binodal?.slope ?? null,
    spinodals: spin.roots, minScaledCurvature: spin.minScaledCurvature, raw: r,
  };
}

/** A. Local curvature versus global tangent-plane evidence for one feed. */
export function localGlobalAudit(inputs) {
  const s = solve(inputs);
  const local = s.curvature === null ? 'undefined at a pure endpoint' : s.curvature > 0 ? 'positive' : s.curvature < 0 ? 'negative' : 'zero';
  const global = s.tpdMinimum === null ? 'not applicable' : s.tpdMinimum < -1e-10 ? 'negative' : 'nonnegative';
  const disagreement = local === 'positive' && global === 'negative';
  return {
    z: s.z, state: s.state, phase: s.phase, curvature: s.curvature, local, tpdMinimum: s.tpdMinimum,
    tpdTrial: s.tpdTrial, global, gain: s.gain, disagreement,
    reading: disagreement
      ? 'Positive curvature with a negative tangent-plane distance: the feed resists small fluctuations but a finite split lowers the Gibbs energy. Local evidence alone would misclassify the equilibrium.'
      : local === 'negative'
        ? 'Negative curvature already shows local instability. The tangent-plane distance confirms that a split lowers the Gibbs energy.'
        : global === 'nonnegative'
          ? 'Positive curvature and no negative tangent-plane distance on the searched stationary points. Within this binary model the homogeneous liquid is the equilibrium state.'
          : 'Read the curvature and tangent-plane distance together before classifying the feed.',
  };
}

function scenario(base, changes, label) {
  const inputs = { ...base, ...changes };
  try {
    const s = solve(inputs);
    return { label, inputs, status: 'finite', phase: s.phase, state: s.state, xAlpha: s.gapAlpha, xBeta: s.gapBeta,
      fractionBeta: s.fractionBeta, gain: s.gain, reason: '' };
  } catch (error) {
    if (!(error instanceof RangeError) && !(error instanceof Error)) throw error;
    return { label, inputs, status: 'failed', phase: null, state: null, xAlpha: null, xBeta: null, fractionBeta: null, gain: null, reason: error.message };
  }
}

const span = (rows, key) => {
  const values = rows.map(row => row[key]).filter(Number.isFinite);
  return values.length ? [Math.min(...values), Math.max(...values)] : null;
};

/** Normalize half-widths; zero is allowed, negative and non-finite are not. */
export function normalizeBounds(inputs, raw = {}) {
  const keys = [...PARAMETER_KEYS[inputs.model], 'z'];
  return Object.fromEntries(keys.map(key => {
    const value = raw[key] === undefined || raw[key] === '' ? DEFAULT_BOUNDS[key] : Number(raw[key]);
    if (!Number.isFinite(value) || value < 0) throw new RangeError('Half-width for ' + PARAMETER_LABELS[key] + ' must be zero or positive.');
    return [key, value];
  }));
}

/** Local derivative of the symmetric-Margules binodal composition with respect to A. */
export function binodalDerivative(A) {
  const gap = engine.coexistence(A);
  if (!gap) return null;
  const x = gap.xAlpha, denominator = 1 / (x * (1 - x)) - 2 * A;
  return { xAlpha: x, dxdA: -(1 - 2 * x) / denominator, denominator };
}

/** B. Deterministic one-at-a-time and signed-corner scenarios. */
export function sensitivityStudy(inputs, rawBounds) {
  const bounds = normalizeBounds(inputs, rawBounds), keys = Object.keys(bounds);
  const baseline = scenario(inputs, {}, 'Baseline');
  if (baseline.status !== 'finite') throw new Error('The baseline calculation failed: ' + baseline.reason);
  const oneAtATime = keys.flatMap(key => [-1, 1].map(sign => scenario(inputs, { [key]: inputs[key] + sign * bounds[key] },
    PARAMETER_LABELS[key] + (sign > 0 ? ' + ' : ' − ') + bounds[key])));
  const corners = Array.from({ length: 2 ** keys.length }, (_, index) => {
    const changes = {}, signs = [];
    keys.forEach((key, bit) => { const sign = (index >> bit) & 1 ? 1 : -1; changes[key] = inputs[key] + sign * bounds[key]; signs.push(sign > 0 ? '+' : '−'); });
    return scenario(inputs, changes, signs.join(''));
  });
  const finiteCorners = corners.filter(row => row.status === 'finite');
  const phaseCounts = finiteCorners.reduce((counts, row) => ({ ...counts, [row.phase]: (counts[row.phase] || 0) + 1 }), {});
  const stateCounts = finiteCorners.reduce((counts, row) => ({ ...counts, [row.state]: (counts[row.state] || 0) + 1 }), {});
  const effect = key => {
    const rows = oneAtATime.filter(row => row.inputs[key] !== inputs[key] && row.status === 'finite');
    const delta = field => Math.max(0, ...rows.map(row => Number.isFinite(row[field]) && Number.isFinite(baseline[field]) ? Math.abs(row[field] - baseline[field]) : 0));
    return { key, label: PARAMETER_LABELS[key], accepted: rows.length, attempted: 2, xAlpha: delta('xAlpha'), fractionBeta: delta('fractionBeta'),
      phaseChange: rows.some(row => row.phase !== baseline.phase) };
  };
  const derivative = inputs.model === 'symmetric' ? binodalDerivative(inputs.A) : null;
  return {
    bounds, keys, baseline, oneAtATime, corners,
    counts: { finite: finiteCorners.length, failed: corners.length - finiteCorners.length, total: corners.length },
    phaseCounts, stateCounts,
    ranges: { xAlpha: span(finiteCorners, 'xAlpha'), xBeta: span(finiteCorners, 'xBeta'), fractionBeta: span(finiteCorners, 'fractionBeta'), gain: span(finiteCorners, 'gain') },
    effects: keys.map(effect).sort((a, b) => b.xAlpha + b.fractionBeta - a.xAlpha - a.fractionBeta),
    derivative: derivative && bounds.A ? { ...derivative, linearChange: Math.abs(derivative.dxdA) * bounds.A } : derivative,
  };
}

function solve2(fn, start) {
  // Damped Newton for two equations with a finite-difference Jacobian.
  let v = [...start];
  for (let iteration = 0; iteration < 80; iteration++) {
    const f = fn(v), norm = Math.hypot(...f);
    if (norm < 1e-12) return { v, iterations: iteration, converged: true };
    const h = 1e-7, J = [0, 1].map(j => { const w = [...v]; w[j] += h; const g = fn(w); return [(g[0] - f[0]) / h, (g[1] - f[1]) / h]; });
    const det = J[0][0] * J[1][1] - J[1][0] * J[0][1];
    if (!Number.isFinite(det) || Math.abs(det) < 1e-14) break;
    const step = [(f[0] * J[1][1] - f[1] * J[1][0]) / det, (J[0][0] * f[1] - J[0][1] * f[0]) / det];
    let lambda = 1;
    while (lambda > 1e-4) {
      const trial = [v[0] - lambda * step[0], v[1] - lambda * step[1]];
      if (Math.hypot(...fn(trial)) < norm) { v = trial; break; }
      lambda /= 2;
    }
    if (lambda <= 1e-4) break;
  }
  return { v, converged: Math.hypot(...fn(v)) < 1e-10 };
}

/** NRTL τ values that reproduce two infinite-dilution log activities at fixed α. */
export function matchNrtl(lnInf, alpha) {
  const residual = ([t12, t21]) => [t21 + t12 * Math.exp(-alpha * t12) - lnInf[0], t12 + t21 * Math.exp(-alpha * t21) - lnInf[1]];
  const guess = (lnInf[0] + lnInf[1]) / 4;
  for (const start of [[guess, guess], [lnInf[1] / 2, lnInf[0] / 2], [1, 1], [3, 3]]) {
    const result = solve2(residual, start);
    if (result.converged) return { tau12: result.v[0], tau21: result.v[1] };
  }
  return null;
}

/** C. Models that share the selected infinite-dilution limits. */
export function modelMatchStudy(inputs) {
  const lnInf = dilutionLimits(inputs), z = inputs.z;
  const rows = [];
  const add = (label, candidate, note) => {
    try {
      const s = solve({ ...candidate, z });
      rows.push({ label, candidate, status: 'finite', phase: s.phase, state: s.state, xAlpha: s.gapAlpha, xBeta: s.gapBeta,
        fractionBeta: s.fractionBeta, gain: s.gain, note });
    } catch (error) {
      rows.push({ label, candidate, status: 'failed', reason: error.message, note });
    }
  };
  if (lnInf.every(v => v >= 0 && v <= 6)) add('Margules · two parameters', { model: 'asymmetric', A12: lnInf[0], A21: lnInf[1] }, 'A₁₂ = ln γ₁∞, A₂₁ = ln γ₂∞');
  else rows.push({ label: 'Margules · two parameters', status: 'failed', reason: 'Matched Margules parameters fall outside 0–6.' });
  for (const alpha of MATCH_ALPHAS) {
    const tau = matchNrtl(lnInf, alpha);
    if (!tau) rows.push({ label: 'NRTL · α = ' + alpha, status: 'failed', reason: 'No τ pair reproduces both limits at this α.' });
    else if (![tau.tau12, tau.tau21].every(v => v >= -2 && v <= 6)) rows.push({ label: 'NRTL · α = ' + alpha, status: 'failed', reason: 'Matched τ lies outside −2 to 6.' });
    else add('NRTL · α = ' + alpha, { model: 'nrtl', ...tau, alpha }, 'τ₁₂ = ' + tau.tau12.toFixed(4) + ', τ₂₁ = ' + tau.tau21.toFixed(4));
  }
  const finiteRows = rows.filter(row => row.status === 'finite');
  return { lnInf, z, rows, phases: [...new Set(finiteRows.map(row => row.phase))], xAlphaRange: span(finiteRows, 'xAlpha') };
}

/** Completeness check for the evidence record; it does not grade reasoning. */
export function evidenceCheck(record) {
  const issues = [];
  if (!record.audit) issues.push('Run investigation A.');
  if (!record.sensitivity) issues.push('Run the sensitivity scenarios in investigation B.');
  if (!record.match) issues.push('Run the model comparison in investigation C.');
  const notes = record.notes || {};
  for (const [key, label] of [['local', 'Claim 1'], ['sensitivity', 'Claim 2'], ['model', 'Claim 3'], ['decision', 'Decision and next evidence']]) {
    const text = (notes[key] || '').trim();
    if (text.length < 40) issues.push(label + ' needs a fuller statement.');
    else if ((text.match(/\d/g) || []).length < 2) issues.push(label + ' should quote at least one calculated number.');
  }
  return { complete: issues.length === 0, issues };
}
