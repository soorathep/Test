/** Lab 11 · adsorption in a closed vessel. Graduate investigations: the fitted
 * pressure range, the isosteric heat, and temperature-swing release. */
import * as ad from '../../labs/assets/adsorption.js';

export const ADSORPTION_GRADUATE_VERSION = '1.0.0';
export const R = ad.R;
export const TREF = 300;
export const MODELS = Object.freeze(['langmuir', 'henry']);

/** Temperature factor for b (Langmuir) or K (Henry) with a constant isosteric heat Q (J/mol). */
export const tFactor = (T, Q) => Math.exp(Q / R * (1 / T - 1 / TREF));

export function isothermParameters(i, T = i.T) {
  const f = tFactor(T, i.Q * 1000);
  return i.model === 'henry' ? { K: i.K * f } : { qs: i.qs, b: i.b * f };
}

/** i: T (K), V (L), m (g), n (mol), model, qs (mol/kg), b (1/kPa at 300 K), K (mol/kg/kPa at 300 K), Q (kJ/mol). */
export function vessel(i, T = i.T, over = {}) {
  const v = { ...i, ...over };
  return ad.vessel({ model: v.model, parameters: isothermParameters(v, T), T, volume: v.V / 1000, mass: v.m / 1000, amount: v.n, inert: 0, Pmin: 0, Pmax: 200 });
}

export function noAdsorbentPressure(i, T = i.T) { return i.n * R * T / (i.V / 1000) / 1000; }

export function solve(i) {
  const r = vessel(i);
  return { r, Pempty: noAdsorbentPressure(i), coverage: i.model === 'langmuir' ? r.q / i.qs : null, params: isothermParameters(i) };
}

/** Synthetic measured isotherms: Langmuir qs = 2 mol/kg, b(300 K) = 0.1 kPa⁻¹, Q = 25 kJ/mol,
 * with a fixed ±2% pressure scatter so that no model reproduces the data exactly. */
const SCATTER = [1.02, 0.98, 1.01, 0.99, 1.02, 0.98, 1.01];
export function syntheticData() {
  const rows = []; let row = 2;
  [300, 320, 340].forEach((T, t) => {
    const b = 0.1 * tFactor(T, 25000);
    [0.1, 0.25, 0.5, 0.8, 1, 1.3, 1.5].forEach((q, k) => rows.push({ T, P: q / (b * (2 - q)) * SCATTER[(k + t) % SCATTER.length], q, row: row++ }));
  });
  return rows;
}

/** A. Fit three models to the 300 K isotherm over a low-loading range and the full range, then use each fit in the vessel. */
export function fitRangeStudy(i) {
  const all = syntheticData().filter(r => r.T === 300), low = all.filter(r => r.q <= 0.8);
  const out = [];
  for (const [range, rows] of [['q ≤ 0.8 mol/kg', low], ['all, q ≤ 1.5 mol/kg', all]]) for (const model of ['henry', 'langmuir', 'freundlich']) {
    try {
      const f = ad.fit(rows, model);
      let P = null, reason = null;
      try { P = ad.vessel({ model, parameters: f.parameters, T: 300, volume: i.V / 1000, mass: i.m / 1000, amount: i.n, inert: 0, Pmin: 0, Pmax: 200 }).P; } catch (error) { reason = error.message; }
      out.push({ range, model, status: 'ok', parameters: f.parameters, RMSE: f.RMSE, Pmax: f.range[1], vesselP: P, reason, q60: ad.uptake(model, 60, f.parameters) });
    } catch (error) { out.push({ range, model, status: 'failed', reason: error.message }); }
  }
  return { rows: out, data: all };
}

/** B. Isosteric heat from the synthetic isotherms, with fewer temperatures and with a 2 K temperature error. */
export function heatStudy() {
  const rows = syntheticData();
  const cases = [
    ['Three temperatures · 300, 320, 340 K', rows, [300, 320, 340]],
    ['Two temperatures · 300, 340 K', rows.filter(r => r.T !== 320), [300, 340]],
    ['340 K isotherm recorded as 342 K', rows.map(r => (r.T === 340 ? { ...r, T: 342 } : r)), [300, 320, 342]],
  ];
  return cases.map(([label, data, temperatures]) => {
    const h = ad.isosteric({ rows: data, temperatures });
    if (h.unavailable) return { label, status: 'failed', reason: h.unavailable };
    const Q = h.points.map(p => p.Qst / 1000);
    return { label, status: 'ok', min: Math.min(...Q), max: Math.max(...Q), mean: Q.reduce((a, b) => a + b, 0) / Q.length, range: h.range, lnPRMSE: Math.max(...h.points.map(p => p.lnPRMSE)), warning: h.warning };
  });
}

/** C. Heat the closed vessel and track the pressure and the gas released from the solid. */
export function swingStudy(i, temps = [300, 320, 340, 360, 380, 400], heats = [20, 25, 30]) {
  const base = vessel(i, TREF);
  return heats.map(Q => ({ Q, rows: temps.map(T => {
    try {
      const r = vessel({ ...i, Q }, T);
      return { T, status: 'ok', P: r.P, q: r.q, gasFraction: r.gasFraction, released: (base.adsorbed - r.adsorbed) };
    } catch (error) { return { T, status: 'failed', reason: error.message }; }
  }) }));
}

export function evidenceCheck(record) {
  const issues = [];
  if (!record.fits) issues.push('Run the fit-range study in investigation A.');
  if (!record.heat) issues.push('Run the isosteric-heat study in investigation B.');
  if (!record.swing) issues.push('Run the temperature swing in investigation C.');
  for (const [key, label] of [['fits', 'Claim 1'], ['heat', 'Claim 2'], ['swing', 'Claim 3'], ['decision', 'Decision and next evidence']]) {
    const text = (record.notes?.[key] || '').trim();
    if (text.length < 40) issues.push(label + ' needs a fuller statement.');
    else if ((text.match(/\d/g) || []).length < 2) issues.push(label + ' should quote at least one calculated number.');
  }
  return { complete: issues.length === 0, issues };
}
