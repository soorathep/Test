/** Lab 08 · user VLE data: first-row interpretation, pure-limit checks,
 * deliberate unit-error signatures, model comparison and endpoint assumptions. */
import * as vi from '../../labs/assets/vle-input.js';

export const VLE_INPUT_GRADUATE_VERSION = '1.0.0';
export const MODELS = Object.freeze({ nrtl: 'NRTL · α = 0.3', margules1: 'Margules · 1 parameter', margules2: 'Margules · 2 parameters' });

/** How the first data row is read with the declared units, before validation. */
export function firstRow(text, options) {
  const rows = vi.parseTable(text, options.antoine !== null);
  const r = rows.find(q => q.x1 > 0 && q.x1 < 1) || rows[0];
  const T = r.t + (options.temperatureUnit === 'C' ? 273.15 : 0), P = r.p * ({ kPa: 1, Pa: 0.001, bar: 100 }[options.pressureUnit]);
  const s = options.antoine.map(c => vi.antoinePressure(c, T));
  const g = r.x1 > 0 && r.x1 < 1 ? [r.y1 * P / (r.x1 * s[0]), (1 - r.y1) * P / ((1 - r.x1) * s[1])] : null;
  return { raw: r, T, P, s, gamma: g };
}

/** Pure-liquid standard state: ln γ1 → 0 as x1 → 1 and ln γ2 → 0 as x1 → 0. */
export function pureLimits(set) {
  const first = set.valid[0], last = set.valid.at(-1);
  return { lnGamma2AtLowX: { x: first.x, value: first.ln[1] }, lnGamma1AtHighX: { x: last.x, value: last.ln[0] } };
}

export function summary(set) {
  const d = vi.diagnose(set, 'none'), lim = pureLimits(set);
  return { rows: set.rows.length, valid: set.valid.length, excluded: set.excluded.length, D: d.area.area.D, partial: !set.endpointsKnown, limits: lim };
}

/** A. Re-import the same text under deliberate misreadings and record what each check sees. */
export function errorSignatures(text, options) {
  const cases = [
    { label: 'As declared', opts: options },
    { label: 'Pressure column read as bar', opts: { ...options, pressureUnit: options.pressureUnit === 'bar' ? 'kPa' : 'bar' } },
    { label: 'Pressure column read as Pa', opts: { ...options, pressureUnit: options.pressureUnit === 'Pa' ? 'kPa' : 'Pa' } },
    { label: 'Temperature column read as °C', opts: { ...options, temperatureUnit: options.temperatureUnit === 'C' ? 'K' : 'C' } },
    { label: 'Antoine constants read with °C', opts: { ...options, antoine: options.antoine.map(c => ({ ...c, temperatureUnit: c.temperatureUnit === 'C' ? 'K' : 'C' })) } },
  ];
  return cases.map(c => {
    try {
      const set = vi.importVLE(text, c.opts), s = summary(set);
      let fit = null;
      try { const f = vi.fitVLE(set, { model: 'nrtl', alpha: 0.3 }); fit = { deltaP: f.deltaP, deltaY: f.deltaY }; } catch (error) { fit = { error: error.message }; }
      return { label: c.label, status: 'imported', D: s.D, lnG1High: s.limits.lnGamma1AtHighX, lnG2Low: s.limits.lnGamma2AtLowX, fit };
    } catch (error) { return { label: c.label, status: 'rejected', reason: error.message }; }
  });
}

/** B. Three activity models fitted to the same observations. */
export function modelComparison(set) {
  return Object.entries(MODELS).map(([model, label]) => {
    try { const f = vi.fitVLE(set, { model, alpha: 0.3 }); return { model, label, status: 'ok', parameters: f.parameters, names: f.parameterNames, deltaP: f.deltaP, deltaY: f.deltaY, atBound: f.atBound, points: f.points }; }
    catch (error) { return { model, label, status: 'failed', reason: error.message }; }
  });
}

/** C. Area test under three endpoint assumptions. */
export function endpointStudy(set) {
  return ['none', 'linear', 'quadratic'].map(ext => {
    try { const a = vi.diagnose(set, ext).area; return { ext, status: 'ok', D: a.area.D, I: a.area.signed, xmin: a.area.xmin, xmax: a.area.xmax }; }
    catch (error) { return { ext, status: 'failed', reason: error.message }; }
  });
}

export function evidenceCheck(record) {
  const issues = [];
  if (!record.signatures) issues.push('Run the unit-error signatures in investigation A.');
  if (!record.models) issues.push('Run the model comparison in investigation B.');
  if (!record.endpoints) issues.push('Run the endpoint comparison in investigation C.');
  for (const [key, label] of [['signatures', 'Claim 1'], ['models', 'Claim 2'], ['endpoints', 'Claim 3'], ['decision', 'Decision and next evidence']]) {
    const text = (record.notes?.[key] || '').trim();
    if (text.length < 40) issues.push(label + ' needs a fuller statement.');
    else if ((text.match(/\d/g) || []).length < 2) issues.push(label + ' should quote at least one calculated number.');
  }
  return { complete: issues.length === 0, issues };
}
