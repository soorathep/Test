/** Lab 07 · adiabatic flash graduate investigations: where the flash begins,
 * how the liquid model moves the outlet, and the heater duty that replaces Q = 0.
 * Pure functions on top of the shared course engines. */
import * as ad from '../../labs/assets/adiabatic.js';
import { flash } from '../../labs/assets/thermo.js';

export const ADIABATIC_GRADUATE_VERSION = '1.0.0';
export const MODELS = Object.freeze(['ideal', 'margules', 'margules2', 'nrtl']);
export const MODEL_KEYS = Object.freeze({ ideal: [], margules: ['A'], margules2: ['A12', 'A21'], nrtl: ['tau12', 'tau21', 'alpha'] });
export const CALORIC = ad.caloric;

export function modelParameters(i) {
  if (i.model === 'ideal') return 0;
  if (i.model === 'margules') return Number(i.A);
  if (i.model === 'margules2') return { A12: Number(i.A12), A21: Number(i.A21) };
  if (i.model === 'nrtl') return { model: 'nrtl', tau12: Number(i.tau12), tau21: Number(i.tau21), alpha: Number(i.alpha), temperatureMode: 'constant' };
  throw new RangeError('Choose a supported liquid model.');
}

export const cpOf = z => z * CALORIC.Cp[0] + (1 - z) * CALORIC.Cp[1];
export const hvapOf = y => y * CALORIC.Hvap[0] + (1 - y) * CALORIC.Hvap[1];

export function solve(system, i) {
  const r = ad.adiabaticFlash(system, i.P * 1000, i.z, i.feedT, modelParameters(i));
  const cp = cpOf(i.z), latent = r.y === null ? null : hvapOf(r.y);
  return { ...r, cp, latent, betaClosed: latent ? cp * (i.feedT - r.T) / latent : null, bubbleT: bubbleT(system, i) };
}

/** Temperature at which the feed first forms vapor at the outlet pressure. */
export function bubbleT(system, i) {
  const A = modelParameters(i), P = i.P * 1000, [lo0, hi0] = system.rangeK;
  const vapor = T => { const f = flash(system, T, P, i.z, A); return f.beta !== null && f.beta > 1e-12; };
  if (vapor(lo0)) return null;
  if (!vapor(hi0)) return null;
  let lo = lo0, hi = hi0;
  for (let k = 0; k < 60; k++) { const m = (lo + hi) / 2; if (vapor(m)) hi = m; else lo = m; }
  return (lo + hi) / 2;
}

/** A. Outlet temperature and vapor amount across feed temperatures. */
export function feedSweep(system, i, temps = [330, 340, 350, 360, 370, 380, 390]) {
  const Tb = bubbleT(system, i);
  return {
    bubbleT: Tb,
    rows: temps.map(T => {
      try { const r = ad.adiabaticFlash(system, i.P * 1000, i.z, T, modelParameters(i)); return { feedT: T, T: r.T, beta: r.beta, phase: r.phase, status: 'ok' }; }
      catch (error) { return { feedT: T, status: 'failed', reason: error.message }; }
    }),
  };
}

/** B. Same feed and pressure, different liquid models. */
export function modelComparison(system, i) {
  const candidates = [
    { label: 'Ideal liquid', inputs: { ...i, model: 'ideal' } },
    { label: 'Margules A = −1 (negative deviation)', inputs: { ...i, model: 'margules', A: -1 } },
    { label: 'Margules A = +1 (positive deviation)', inputs: { ...i, model: 'margules', A: 1 } },
  ];
  return candidates.map(c => {
    try { const r = solve(system, c.inputs); return { label: c.label, status: 'ok', T: r.T, beta: r.beta, x: r.x, y: r.y, bubbleT: r.bubbleT }; }
    catch (error) { return { label: c.label, status: 'failed', reason: error.message }; }
  });
}

/** C. Heater duty needed to reach a target vapor amount at the outlet pressure. */
export function dutyForVapor(system, i, targetBeta) {
  if (!Number.isFinite(targetBeta) || targetBeta <= 0 || targetBeta >= 1) throw new RangeError('Choose a target vapor amount between 0 and 1 mol.');
  const A = modelParameters(i), P = i.P * 1000, [lo0, hi0] = system.rangeK;
  const betaAt = T => { const f = flash(system, T, P, i.z, A); return f.beta === null ? 0.5 : f.beta; };
  if (betaAt(lo0) > targetBeta || betaAt(hi0) < targetBeta) throw new RangeError('That vapor amount is not reached within 300–390 K at this pressure.');
  let lo = lo0, hi = hi0;
  for (let k = 0; k < 70; k++) { const m = (lo + hi) / 2; if (betaAt(m) < targetBeta) lo = m; else hi = m; }
  const T = (lo + hi) / 2, f = flash(system, T, P, i.z, A);
  const Hout = (1 - f.beta) * ad.enthalpy(T, f.x) + f.beta * ad.enthalpy(T, f.y, 'vapor'), Hfeed = ad.enthalpy(i.feedT, i.z);
  return { targetBeta, T, x: f.x, y: f.y, beta: f.beta, Hout, Hfeed, Q: Hout - Hfeed };
}

export function evidenceCheck(record) {
  const issues = [];
  if (!record.sweep) issues.push('Run the feed-temperature sweep in investigation A.');
  if (!record.models) issues.push('Run the model comparison in investigation B.');
  if (!record.duty) issues.push('Calculate a heater duty in investigation C.');
  for (const [key, label] of [['sweep', 'Claim 1'], ['models', 'Claim 2'], ['duty', 'Claim 3'], ['decision', 'Decision and next evidence']]) {
    const text = (record.notes?.[key] || '').trim();
    if (text.length < 40) issues.push(label + ' needs a fuller statement.');
    else if ((text.match(/\d/g) || []).length < 2) issues.push(label + ' should quote at least one calculated number.');
  }
  return { complete: issues.length === 0, issues };
}
