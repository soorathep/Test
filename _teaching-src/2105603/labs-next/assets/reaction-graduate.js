/** Lab 12 · ideal-gas reaction equilibrium A2 ⇌ 2 A. Graduate investigations:
 * how K is carried to another temperature, the driving force of a sample, and
 * pressure, inert gas and the standard state. */
import * as rx from '../../labs/assets/reaction.js';

export const REACTION_GRADUATE_VERSION = '1.0.0';
export const R = rx.R;
export const TREF = 350;

/** i: T (K), P (kPa), nI (mol inert), nA2 (mol), dG (kJ/mol at 350 K), dH (kJ/mol), dCp (J/mol/K), Pstd (kPa). */
export function species(i) {
  return [{ name: 'A2', nu: -1, phase: 'gas', atoms: { X: 2 }, charge: 0, n0: i.nA2 }, { name: 'A', nu: 2, phase: 'gas', atoms: { X: 1 }, charge: 0, n0: 0 }];
}

/** ln K at T from the 350 K data with constant ΔCp (ΔCp = 0 gives the constant-ΔH van 't Hoff form). */
export function lnK(i, T = i.T, over = {}) {
  const v = { ...i, ...over }, lnKr = -v.dG * 1000 / (R * TREF);
  return rx.vanthoff(T, TREF, lnKr, v.dH * 1000, v.dCp).lnK;
}

export function equilibrium(i, over = {}) {
  const v = { ...i, ...over }, L = lnK(v, v.T);
  const e = rx.extent(species(v), { lnK: L, T: v.T, P: v.P, Pstandard: v.Pstd ?? 100, inert: v.nI });
  return { lnK: L, K: Math.exp(L), dGT: -R * v.T * L, xi: e.xi, conversion: e.xi / v.nA2, e };
}

export function solve(i) {
  const q = equilibrium(i);
  return { ...q, closed: i.nI === 0 ? Math.sqrt(q.K / (4 * i.P / (i.Pstd ?? 100) + q.K)) * i.nA2 : null };
}

/** A. Carry K from 350 K to other temperatures with different thermal data. */
export function temperatureStudy(i, temps = [300, 350, 400, 450, 500, 550]) {
  const variants = [
    ['constant ΔH', { dCp: 0 }],
    ['ΔCp = +30', { dCp: 30 }],
    ['ΔH − 10%', { dH: i.dH * 0.9, dCp: 0 }],
    ['ΔH + 10%', { dH: i.dH * 1.1, dCp: 0 }],
  ];
  return { temps, variants: variants.map(([label, over]) => ({ label, rows: temps.map(T => {
    try { const q = equilibrium(i, { ...over, T }); return { T, status: 'ok', lnK: q.lnK, conversion: q.conversion }; }
    catch (error) { return { T, status: 'failed', reason: error.message }; }
  }) })) };
}

/** B. Driving force of gas samples taken from a reactor at the current T. */
export function drivingForce(i, samples = [[0.2, 100], [0.5, 100], [0.1, 100], [0.2, 1000]]) {
  const L = lnK(i, i.T), Pstd = i.Pstd ?? 100;
  return { lnK: L, rows: samples.map(([yA2, P]) => {
    const yA = 1 - yA2, lnQ = 2 * Math.log(yA * P / Pstd) - Math.log(yA2 * P / Pstd), d = lnQ - L;
    return { yA2, yA, P, Q: Math.exp(lnQ), lnQ, dG: R * i.T * d / 1000, direction: Math.abs(d) < 1e-8 ? 'At equilibrium' : d < 0 ? 'Forward: more A forms' : 'Reverse: A recombines' };
  }) };
}

/** C. Pressure, inert gas and the standard-state convention for K. */
export function pressureStudy(i) {
  const L = lnK(i, i.T), atm = 101.325;
  const run = (label, over, lnKover) => {
    try {
      const v = { ...i, ...over };
      const e = rx.extent(species(v), { lnK: lnKover ?? L, T: v.T, P: v.P, Pstandard: v.Pstd ?? 100, inert: v.nI });
      return { label, status: 'ok', P: v.P, nI: v.nI, Pstd: v.Pstd ?? 100, lnK: lnKover ?? L, conversion: e.xi / v.nA2, yA: e.composition[1].y };
    } catch (error) { return { label, status: 'failed', reason: error.message }; }
  };
  // Δν = +1, so K(1 atm) = K(1 bar) · (1 bar / 1 atm).
  const lnKatm = L + Math.log(100 / atm);
  return [
    run('Current state', {}),
    run('Pressure × 10', { P: i.P * 10 }),
    run('Pressure ÷ 10', { P: i.P / 10 }),
    run('Add 4 mol inert', { nI: i.nI + 4 }),
    run('K converted to P° = 1 atm, used with P° = 1 atm', { Pstd: atm }, lnKatm),
    run('K for P° = 1 bar, used with P° = 1 atm by mistake', { Pstd: atm }, L),
  ];
}

export function evidenceCheck(record) {
  const issues = [];
  if (!record.temperature) issues.push('Run the temperature study in investigation A.');
  if (!record.driving) issues.push('Run the driving-force table in investigation B.');
  if (!record.pressure) issues.push('Run the pressure and standard-state study in investigation C.');
  for (const [key, label] of [['temperature', 'Claim 1'], ['driving', 'Claim 2'], ['pressure', 'Claim 3'], ['decision', 'Decision and next evidence']]) {
    const text = (record.notes?.[key] || '').trim();
    if (text.length < 40) issues.push(label + ' needs a fuller statement.');
    else if ((text.match(/\d/g) || []).length < 2) issues.push(label + ' should quote at least one calculated number.');
  }
  return { complete: issues.length === 0, issues };
}
