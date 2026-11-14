/** Lab 07 · PH flash with a per-system caloric record. Same model as ../../labs/assets/adiabatic.js
 * (Q = W = 0, ideal vapor, equal liquid and vapor Cp, constant latent heats, zero excess enthalpy),
 * extended so that a real-property record can carry its own Cp and latent heats. */
import { flash, bounded, psat } from '../../labs/assets/thermo.js';

export const ADIABATIC_VERSION = '1.1.0-preview';
export const SYNTHETIC_CALORIC = Object.freeze({ referenceT: 350, Cp: [100, 120], Hvap: [30000, 35000] });

export function caloricOf(system) {
  if (system?.caloric) return system.caloric;
  if (system?.kind === 'synthetic' && system.components?.every((c, i) => c.equation === 'clausius' && c.HvapJmol === SYNTHETIC_CALORIC.Hvap[i])) return SYNTHETIC_CALORIC;
  throw new RangeError('This property record has no caloric data (Cp and latent heats) for the energy balance.');
}

function validate(system, A) {
  const c = caloricOf(system);
  if (system.components.length !== 2 || ![c.referenceT, ...c.Cp, ...c.Hvap].every(Number.isFinite)) throw new RangeError('Incomplete caloric record.');
  if (A?.model === 'nrtl' && A.temperatureMode !== 'constant') throw new RangeError('Adiabatic flash requires the explicit constant-tau teaching assumption.');
  return c;
}

export function enthalpy(system, T, x, kind = 'liquid') {
  const c = caloricOf(system), h = c.Cp.map((cp, i) => cp * (T - c.referenceT) + (kind === 'vapor' ? c.Hvap[i] : 0));
  return x * h[0] + (1 - x) * h[1];
}

export function enthalpyState(system, T, P, z, A = 0) {
  const f = flash(system, T, P, z, A);
  if (f.beta === null) return { flash: f, min: enthalpy(system, T, z), max: enthalpy(system, T, z, 'vapor') };
  const hL = f.x === null ? 0 : enthalpy(system, T, f.x), hV = f.y === null ? 0 : enthalpy(system, T, f.y, 'vapor'), H = (1 - f.beta) * hL + f.beta * hV;
  return { flash: f, min: H, max: H };
}

export function phFlash(system, P, z, H, A = 0) {
  validate(system, A); bounded(P, 1000, 200000, 'Pressure (Pa)'); bounded(z, 0, 1, 'Feed fraction');
  if (!Number.isFinite(H)) throw new RangeError('Feed enthalpy must be finite.');
  let [lo, hi] = system.rangeK;
  const left = enthalpyState(system, lo, P, z, A), right = enthalpyState(system, hi, P, z, A);
  if (H < left.min - 1e-5 || H > right.max + 1e-5) throw new RangeError('No energy-balanced equilibrium within the ' + lo + '–' + hi + ' K property range.');
  for (let i = 0; i < 100; i++) {
    const T = i === 0 && Math.abs(H - left.min) < 1e-5 ? lo : i === 0 && Math.abs(H - right.max) < 1e-5 ? hi : (lo + hi) / 2, q = enthalpyState(system, T, P, z, A);
    const residual = H < q.min ? q.min - H : H > q.max ? q.max - H : 0;
    if (Math.abs(residual) < 1e-5) {
      const f = q.flash, beta = f.beta === null ? Math.max(0, Math.min(1, (H - q.min) / (q.max - q.min))) : f.beta;
      const x = f.x, y = f.y, hL = x === null ? 0 : enthalpy(system, T, x), hV = y === null ? 0 : enthalpy(system, T, y, 'vapor'), Hout = (1 - beta) * hL + beta * hV;
      const mass = Math.abs((1 - beta) * (x ?? z) + beta * (y ?? z) - z);
      if (Math.abs(Hout - H) > 1e-4 || mass > 1e-8) throw new Error('Independent energy or component balance failed.');
      return { version: ADIABATIC_VERSION, T, P, z, H, A, beta, x, y, Hout, energyResidual: Hout - H, balanceResidual: mass, phase: f.phase, innerFlash: f, caloric: caloricOf(system) };
    }
    if (residual > 0) hi = T; else lo = T;
  }
  throw new Error('Energy balance did not converge.');
}

export function adiabaticFlash(system, P, z, feedT, A = 0) {
  bounded(feedT, ...system.rangeK, 'Liquid feed temperature');
  const r = phFlash(system, P, z, enthalpy(system, feedT, z), A);
  return { ...r, feedT, feedSaturationPressures: system.components.map(c => psat(c, feedT)) };
}

export function energyCurve(system, P, z, A, n = 100) {
  validate(system, A);
  return Array.from({ length: n + 1 }, (_, i) => {
    const T = system.rangeK[0] + (system.rangeK[1] - system.rangeK[0]) * i / n, q = enthalpyState(system, T, P, z, A);
    return { T, min: q.min, max: q.max, beta: q.flash.beta };
  });
}
