/** Lab 10 · solid–liquid equilibrium graduate investigations: the cooling path,
 * the liquid activity model, and sensitivity to the pure-solid fusion data. */
import * as so from '../../labs/assets/solids.js';
import { gamma } from '../../labs/assets/thermo.js';

export const SOLIDS_GRADUATE_VERSION = '1.0.0';
export const R = so.R;
export const MODELS = Object.freeze(['ideal', 'margules', 'margules2', 'nrtl']);
export const MODEL_KEYS = Object.freeze({ ideal: [], margules: ['A'], margules2: ['A12', 'A21'], nrtl: ['tau12', 'tau21', 'alpha'] });
export const T_RANGE = Object.freeze([250, 450]);

export function liquidParameters(i) {
  if (i.model === 'ideal') return 0;
  if (i.model === 'margules') return Number(i.A);
  if (i.model === 'margules2') return { A12: Number(i.A12), A21: Number(i.A21) };
  return { model: 'nrtl', tau12: Number(i.tau12), tau21: Number(i.tau21), alpha: Number(i.alpha), temperatureMode: 'constant' };
}

export function engineInput(i, over = {}) {
  const v = { ...i, ...over };
  return { T: v.T, Tmin: T_RANGE[0], Tmax: T_RANGE[1], z: v.z, Tm: [v.Tm1, v.Tm2], fusion: [v.h1, v.h2], A: liquidParameters(v) };
}

/** Temperature at which a liquid of composition x is saturated with pure solid i (null if outside range). */
export function saturationT(i, x, k) {
  if (!(x > 0 && x < 1)) return k === 0 ? (x === 1 ? i.Tm1 : null) : (x === 0 ? i.Tm2 : null);
  const g = gamma(x, liquidParameters(i)), a = k === 0 ? x * g[0] : (1 - x) * g[1], Tm = k === 0 ? i.Tm1 : i.Tm2, h = k === 0 ? i.h1 : i.h2;
  const T = 1 / (1 / Tm - R / h * Math.log(a));
  return Number.isFinite(T) && T > 0 ? T : null;
}

/** First crystals on cooling: the higher of the two saturation temperatures at x = z. */
export function liquidus(i) {
  const T1 = saturationT(i, i.z, 0), T2 = saturationT(i, i.z, 1);
  if (T1 == null && T2 == null) return null;
  return (T2 ?? -Infinity) > (T1 ?? -Infinity) ? { T: T2, solid: 2 } : { T: T1, solid: 1 };
}

export function solve(i) {
  const s = engineInput(i), r = so.sle(s), e = so.eutectic(s);
  return { r, input: s, eutectic: e.unavailable ? null : e, liquidus: liquidus(i), gs: r.gs };
}

/** A. Cool the feed and record the phase amounts. */
export function coolingPath(i, temps) {
  const sol = solve(i), Te = sol.eutectic?.T, TL = sol.liquidus?.T;
  const list = temps ?? [...new Set([400, 380, 360, TL && Math.round(TL * 100) / 100, 340, 330, Te && Math.round((Te + 0.5) * 100) / 100, Te && Math.round((Te - 0.5) * 100) / 100, 300].filter(Number.isFinite))].sort((a, b) => b - a);
  return { liquidus: sol.liquidus, eutectic: sol.eutectic, rows: list.map(T => {
    try { const r = so.sle(engineInput(i, { T })); return { T, status: 'ok', type: r.type, x: r.x, liquid: r.liquid, solid1: r.solid1, solid2: r.solid2 }; }
    catch (error) { return { T, status: 'failed', reason: error.message }; }
  }) };
}

/** B. Same pure solids, different liquid nonideality (one-parameter Margules). */
export function modelStudy(i, values = [-1, 0, 1, 1.5]) {
  return values.map(A => {
    const v = { ...i, model: A === 0 ? 'ideal' : 'margules', A };
    try {
      const sol = solve(v), r = sol.r;
      return { A, status: 'ok', eutecticT: sol.eutectic?.T ?? null, eutecticX: sol.eutectic?.x ?? null, liquidusT: sol.liquidus?.T ?? null, type: r.type, x: r.x, liquid: r.liquid, solid: (r.solid1 ?? 0) + (r.solid2 ?? 0) };
    } catch (error) { return { A, status: 'failed', reason: error.message }; }
  });
}

/** C. Change one fusion property at a time within an assumed uncertainty. */
export function propertyStudy(i) {
  const cases = [
    ['Reference', {}],
    ['Δh₂ − 10%', { h2: i.h2 * 0.9 }], ['Δh₂ + 10%', { h2: i.h2 * 1.1 }],
    ['Tₘ₂ − 5 K', { Tm2: i.Tm2 - 5 }], ['Tₘ₂ + 5 K', { Tm2: i.Tm2 + 5 }],
    ['Δh₁ − 10%', { h1: i.h1 * 0.9 }], ['Δh₁ + 10%', { h1: i.h1 * 1.1 }],
  ];
  return cases.map(([label, over]) => {
    const v = { ...i, ...over };
    try {
      const sol = solve(v), r = sol.r;
      return { label, status: 'ok', eutecticT: sol.eutectic?.T ?? null, eutecticX: sol.eutectic?.x ?? null, liquidusT: sol.liquidus?.T ?? null, x: r.x, solid: (r.solid1 ?? 0) + (r.solid2 ?? 0) };
    } catch (error) { return { label, status: 'failed', reason: error.message }; }
  });
}

export function evidenceCheck(record) {
  const issues = [];
  if (!record.cooling) issues.push('Run the cooling path in investigation A.');
  if (!record.models) issues.push('Run the liquid-model comparison in investigation B.');
  if (!record.properties) issues.push('Run the property sensitivity in investigation C.');
  for (const [key, label] of [['cooling', 'Claim 1'], ['models', 'Claim 2'], ['properties', 'Claim 3'], ['decision', 'Decision and next evidence']]) {
    const text = (record.notes?.[key] || '').trim();
    if (text.length < 40) issues.push(label + ' needs a fuller statement.');
    else if ((text.match(/\d/g) || []).length < 2) issues.push(label + ' should quote at least one calculated number.');
  }
  return { complete: issues.length === 0, issues };
}
