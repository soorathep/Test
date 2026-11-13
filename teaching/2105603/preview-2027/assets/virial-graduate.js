/** Lab 09 · second-virial vapor graduate investigations: where the
 * correction enters K, the cross coefficient B12, and the size of B·P/RT. */
import * as vr from '../../labs/assets/virial.js';
import { exampleAntoine } from '../../labs/assets/vle-input.js';

export const VIRIAL_GRADUATE_VERSION = '1.0.0';
export const R = vr.R;
export const MODELS = Object.freeze(['ideal', 'margules', 'margules2', 'nrtl']);
export const MODEL_KEYS = Object.freeze({ ideal: [], margules: ['A'], margules2: ['A12', 'A21'], nrtl: ['tau12', 'tau21', 'alpha'] });

export function liquidParameters(i) {
  if (i.model === 'ideal') return 0;
  if (i.model === 'margules') return Number(i.A);
  if (i.model === 'margules2') return { A12: Number(i.A12), A21: Number(i.A21) };
  return { model: 'nrtl', tau12: Number(i.tau12), tau21: Number(i.tau21), alpha: Number(i.alpha), temperatureMode: 'constant' };
}

export function engineInput(i, B = [i.b11, i.b12, i.b22]) {
  return { T: i.T, P: i.P * 1000, z: i.z, A: liquidParameters(i), antoine: i.antoine ?? exampleAntoine(),
    virial: { B: B.map(Number), slope: [0, 0, 0], unit: 'cm3/mol', law: 'constant', Tref: 350, Tmin: 300, Tmax: 390 },
    poynting: Boolean(i.poynting), volumes: [Number(i.v1 ?? 90), Number(i.v2 ?? 110)] };
}

const boundaryP = (b) => (b && Number.isFinite(b.P) ? b.P / 1000 : null);

export function solve(i) {
  const r = vr.compare(engineInput(i));
  return { r, real: r.real, ideal: r.ideal, bubble: { virial: boundaryP(r.boundaries.virial.bubble), ideal: boundaryP(r.boundaries.ideal.bubble) },
    dew: { virial: boundaryP(r.boundaries.virial.dew), ideal: boundaryP(r.boundaries.ideal.dew) } };
}

/** A. Each correction term in ln K_i = ln(P_i^sat/P) + ln γ_i + ln φ_i^sat + ln Π_i − ln φ_i. */
export function decomposition(result) {
  const q = result.real, s = q.input;
  if (!q.vapor) return null;
  return [0, 1].map(k => ({ component: k + 1, lnPhi: q.vapor.lnPhi[k], lnPhiSat: s.lnSat[k], lnPoynting: s.lnPoynting[k],
    net: s.lnSat[k] + s.lnPoynting[k] - q.vapor.lnPhi[k] }));
}

/** B. Same pure coefficients, different cross coefficient B12. */
export function crossStudy(i) {
  const gm = -Math.sqrt(Math.abs(i.b11 * i.b22));
  const values = [...new Set([Number(i.b12), gm, 0.7 * Number(i.b12), 1.3 * Number(i.b12)].map(v => Math.round(v * 10) / 10))];
  return values.map(b12 => {
    try {
      const r = vr.compare(engineInput(i, [i.b11, b12, i.b22]));
      return { b12, status: 'ok', beta: r.real.beta, y: r.real.y, bubble: boundaryP(r.boundaries.virial.bubble), geometric: Math.abs(b12 - gm) < 0.06 };
    } catch (error) { return { b12, status: 'failed', reason: error.message }; }
  });
}

/** C. Scale every B by a factor and watch the ideal-vapor error grow toward the truncation guard. */
export function scaleStudy(i, factors = [1, 3, 5, 8, 10, 15]) {
  return factors.map(f => {
    try {
      const r = vr.compare(engineInput(i, [i.b11 * f, i.b12 * f, i.b22 * f]));
      const bv = boundaryP(r.boundaries.virial.bubble), bi = boundaryP(r.boundaries.ideal.bubble);
      return { factor: f, status: 'ok', Z: r.real.vapor ? r.real.vapor.Z : null, beta: r.real.beta, betaIdeal: r.ideal.beta, bubble: bv, bubbleIdeal: bi,
        bubbleError: bv && bi ? 100 * (bi - bv) / bv : null, indicator: r.real.input.indicator };
    } catch (error) { return { factor: f, status: 'failed', reason: error.message }; }
  });
}

export function evidenceCheck(record) {
  const issues = [];
  if (!record.decomposition) issues.push('Run the decomposition in investigation A.');
  if (!record.cross) issues.push('Run the B₁₂ comparison in investigation B.');
  if (!record.scale) issues.push('Run the scale study in investigation C.');
  for (const [key, label] of [['decomposition', 'Claim 1'], ['cross', 'Claim 2'], ['scale', 'Claim 3'], ['decision', 'Decision and next evidence']]) {
    const text = (record.notes?.[key] || '').trim();
    if (text.length < 40) issues.push(label + ' needs a fuller statement.');
    else if ((text.match(/\d/g) || []).length < 2) issues.push(label + ' should quote at least one calculated number.');
  }
  return { complete: issues.length === 0, issues };
}
