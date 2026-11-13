/** Lab 06 · VLLE graduate investigations: the missing amount specification,
 * a pressure sweep across the three-phase pressure, and relative volatility
 * versus the liquid gap (heterogeneous azeotrope). Pure functions. */
import * as vlle from '../../labs/assets/vlle.js';
import { modelParameters } from './stability-graduate.js';

export const VLLE_GRADUATE_VERSION = '1.0.0';

export function psatOf(inputs) {
  const psat = [Number(inputs.psat1), Number(inputs.psat2)];
  if (!psat.every(p => Number.isFinite(p) && p >= 10 && p <= 200)) throw new RangeError('Both saturation pressures must lie between 10 and 200 kPa.');
  return psat;
}

/** First three-phase state of the model, or null when the liquid has no gap. */
export function triple(inputs) {
  const t = vlle.triplePoints(modelParameters(inputs), psatOf(inputs));
  return t.length ? { P: t[0].P, xAlpha: t[0].xAlpha, xBeta: t[0].xBeta, y: t[0].y, count: t.length } : null;
}

export function pressureOf(inputs) {
  if (inputs.pressureMode === 'triple') {
    const t = triple(inputs);
    if (!t) throw new RangeError('This liquid model has no miscibility gap, so there is no three-phase pressure. Choose a pressure.');
    return t.P;
  }
  const P = Number(inputs.P);
  if (!Number.isFinite(P) || P < 1 || P > 500) throw new RangeError('Pressure must lie between 1 and 500 kPa.');
  return P;
}

export function solve(inputs) {
  const A = modelParameters(inputs), psat = psatOf(inputs), P = pressureOf(inputs);
  const r = vlle.equilibrium(A, psat, P, Number(inputs.z), Number.isFinite(inputs.choice) ? inputs.choice : 0.5);
  return { ...r, triple: triple(inputs) };
}

const label = type => ({ VLLE: 'Two liquids + vapor', LLE: 'Two liquids', VLE: 'Liquid + vapor', Liquid: 'One liquid', Vapor: 'Vapor only' }[type] || type);
export { label as phaseLabel };

/** A. Fix the amounts at the three-phase state by specifying the vapor fraction. */
export function amountsForVaporFraction(result, fV) {
  if (result.type !== 'VLLE') throw new RangeError('A vapor-fraction specification applies at the three-phase pressure.');
  const [a, b, v] = result.phases, z = result.z;
  const lo = result.family.vaporMin, hi = result.family.vaporMax;
  if (!Number.isFinite(fV) || fV < lo - 1e-12 || fV > hi + 1e-12) throw new RangeError('Choose a vapor fraction between ' + lo.toFixed(4) + ' and ' + hi.toFixed(4) + '.');
  const fBeta = (z - fV * v.x - (1 - fV) * a.x) / (b.x - a.x), fAlpha = 1 - fV - fBeta;
  return { fAlpha, fBeta, fV, balance: Math.abs(fAlpha * a.x + fBeta * b.x + fV * v.x - z), range: [lo, hi] };
}

/** B. Phase identity and amounts across a pressure range at fixed feed. */
export function pressureSweep(inputs, pressures) {
  const t = triple(inputs);
  const list = [...new Set([...pressures, ...(t ? [t.P] : [])])].sort((p, q) => p - q);
  return {
    triple: t,
    rows: list.map(P => {
      try {
        const r = vlle.equilibrium(modelParameters(inputs), psatOf(inputs), P, Number(inputs.z), 0.5);
        const vapor = r.phases.find(p => p.kind === 'vapor');
        return { P, isTriple: t && Math.abs(P - t.P) < 1e-9, type: r.type, phases: r.phases.map(p => ({ label: p.label, x: p.x, fraction: p.fraction })),
          vaporRange: r.type === 'VLLE' ? [r.family.vaporMin, r.family.vaporMax] : null, vaporFraction: vapor ? vapor.fraction : 0 };
      } catch (error) { return { P, type: 'failed', reason: error.message, phases: [] }; }
    }),
  };
}

/** C. Where does the three-phase vapor lie relative to the liquid gap? */
export const VOLATILITY_P2 = 10;
export function volatilityStudy(inputs, ratios = [1, 2, 5, 10, 15, 20]) {
  const p2 = VOLATILITY_P2;
  return ratios.map(ratio => {
    const p1 = ratio * p2;
    if (p1 < 10 || p1 > 200) return { ratio, status: 'failed', reason: 'P₁ˢᵃᵗ = ' + p1.toFixed(1) + ' kPa lies outside 10–200 kPa.' };
    try {
      const t = triple({ ...inputs, psat1: p1, psat2: p2 });
      if (!t) return { ratio, status: 'failed', reason: 'No liquid gap.' };
      const inside = t.y > t.xAlpha && t.y < t.xBeta;
      return { ratio, psat1: p1, psat2: p2, status: 'ok', P: t.P, xAlpha: t.xAlpha, xBeta: t.xBeta, y: t.y, inside,
        reading: inside ? 'Vapor lies inside the liquid gap: it condenses to two liquid layers (heterogeneous azeotrope).' : 'Vapor lies outside the liquid gap: it is richer in component 1 than both liquids.' };
    } catch (error) { return { ratio, status: 'failed', reason: error.message }; }
  });
}

export function evidenceCheck(record) {
  const issues = [];
  if (!record.amounts) issues.push('Fix the amounts in investigation A.');
  if (!record.sweep) issues.push('Run the pressure sweep in investigation B.');
  if (!record.volatility) issues.push('Run the volatility comparison in investigation C.');
  for (const [key, label] of [['amounts', 'Claim 1'], ['sweep', 'Claim 2'], ['volatility', 'Claim 3'], ['decision', 'Decision and next evidence']]) {
    const text = (record.notes?.[key] || '').trim();
    if (text.length < 40) issues.push(label + ' needs a fuller statement.');
    else if ((text.match(/\d/g) || []).length < 2) issues.push(label + ' should quote at least one calculated number.');
  }
  return { complete: issues.length === 0, issues };
}
