/** Lab 13 · concentration cell M | M²⁺(L) || M²⁺(R) | M. Graduate investigations:
 * activity coefficients, temperature and the entropy of the cell reaction, and discharge. */
import * as engine from '../../labs/assets/electrochemistry.js';

export const CELL_GRADUATE_VERSION = '1.0.0';
export const R = engine.R;
export const F = engine.F;
export const N = 2;
/** Debye–Hückel constant for water near 298 K, log10 basis, (mol/L)^(-1/2). */
export const DH_A = 0.509;

/** i: T (K), cL, cR (mol/L), gL, gR (activity coefficients). */
export function engineInput(i) {
  const input = engine.example(true), header = 'species,nu,phase,atoms,charge,value,gamma\n';
  input.T = i.T; input.potentialT = i.T; input.Eleft = 0; input.Eright = 0; input.nLeft = 2; input.nRight = 2; input.cStandard = 1; input.mode = 'concentration';
  input.left = header + 'M2+,-1,solute,M:1,2,' + i.cL + ',' + i.gL + '\nM,1,solid,M:1,0,1,1';
  input.right = header + 'M2+,-1,solute,M:1,2,' + i.cR + ',' + i.gR + '\nM,1,solid,M:1,0,1,1';
  input.source = 'Synthetic identical M2+/M electrodes; concentrations in mol/L with supplied activity coefficients; c° = 1 mol/L; liquid-junction potential neglected.';
  return input;
}

export function solve(i) {
  const r = engine.calculate(engineInput(i)), aL = i.gL * i.cL, aR = i.gR * i.cR;
  const closed = R * i.T / (N * F) * Math.log(aR / aL);
  return { r, E: r.E, aL, aR, closed, dG: r.deltaG, slope: R * i.T * Math.LN10 / (N * F) };
}

/** Single-ion Debye–Hückel estimates for M²⁺ in an MX₂ solution, I = 3c. */
export function gammaDH(c, form) {
  const sI = Math.sqrt(3 * c), z2 = 4;
  return 10 ** (-DH_A * z2 * (form === 'extended' ? sI / (1 + sI) : sI));
}

/** A. How the activity-coefficient assumption changes E. */
export function activityStudy(i) {
  const forms = [['Ideal solution · γ = 1', () => 1], ['Debye–Hückel limiting law', c => gammaDH(c, 'limiting')], ['Extended Debye–Hückel', c => gammaDH(c, 'extended')]];
  return forms.map(([label, g]) => {
    const gL = g(i.cL), gR = g(i.cR);
    try { const s = solve({ ...i, gL, gR }); return { label, status: 'ok', gL, gR, IL: 3 * i.cL, IR: 3 * i.cR, E: s.E }; }
    catch (error) { return { label, status: 'failed', reason: error.message }; }
  });
}

/** B. Temperature: E, ΔG, ΔS and the reversible heat at fixed activities. */
export function temperatureStudy(i, temps = [278.15, 298.15, 318.15, 338.15]) {
  return temps.map(T => {
    const s = solve({ ...i, T }), dS = N * F * s.E / T;
    return { T, E: s.E, dG: s.dG, dS, qrev: T * dS, dH: s.dG + T * dS };
  });
}

/** C. Discharge with equal compartment volumes V (L) and constant activity coefficients. */
export function dischargeStudy(i, V = 0.1, fractions = [0, 0.25, 0.5, 0.75, 0.9, 0.99]) {
  const xm = (i.gR * i.cR - i.gL * i.cL) / (i.gR + i.gL); // mol/L moved toward equal activity; negative if the left is the cathode
  const E = x => R * i.T / (N * F) * Math.log(i.gR * (i.cR - x) / (i.gL * (i.cL + x)));
  const steps = 4000; let W = 0;
  for (let k = 0; k < steps; k++) { const a = xm * k / steps, b = xm * (k + 1) / steps, m = (a + b) / 2; W += (E(a) + 4 * E(m) + E(b)) / 6 * (b - a); }
  W *= N * F * V;
  const qmax = N * F * V * Math.abs(xm);
  return { V, xm, qmax, W, meanE: qmax > 0 ? W / qmax : 0, rows: fractions.map(f => { const x = f * xm; return { f, cL: i.cL + x, cR: i.cR - x, q: N * F * V * Math.abs(x), E: E(x) }; }) };
}

export function evidenceCheck(record) {
  const issues = [];
  if (!record.activity) issues.push('Run the activity study in investigation A.');
  if (!record.temperature) issues.push('Run the temperature study in investigation B.');
  if (!record.discharge) issues.push('Run the discharge study in investigation C.');
  for (const [key, label] of [['activity', 'Claim 1'], ['temperature', 'Claim 2'], ['discharge', 'Claim 3'], ['decision', 'Decision and next evidence']]) {
    const text = (record.notes?.[key] || '').trim();
    if (text.length < 40) issues.push(label + ' needs a fuller statement.');
    else if ((text.match(/\d/g) || []).length < 2) issues.push(label + ' should quote at least one calculated number.');
  }
  return { complete: issues.length === 0, issues };
}
