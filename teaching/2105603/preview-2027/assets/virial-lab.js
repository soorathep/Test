/** Lab 09 · 2027 preview page module. Calculations use the shared second-virial engine. */
import * as vr from '../../labs/assets/virial.js';
import { palette as c } from '../../labs/assets/palette.js';
import { VIRIAL_GRADUATE_VERSION, MODELS, MODEL_KEYS, SYSTEMS, solve, decomposition, crossStudy, scaleStudy, evidenceCheck } from './virial-graduate.js';

const SCHEMA = 'skh-thermo-virial-study/1';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d }).replace(/^-/, '−');
const signed = (v, d = 2) => v == null || !Number.isFinite(v) ? '—' : (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(d);
const BASE = { T: 350, P: 95, z: 0.5, model: 'ideal', b11: -120, b12: -90, b22: -180, poynting: false, v1: 90, v2: 110 };
const CASES = {
  baseline: { name: 'Starting case · 95 kPa', inputs: { ...BASE } },
  strong: { name: 'Ten times larger |B|', inputs: { ...BASE, b11: -1200, b12: -900, b22: -1800 } },
  zero: { name: 'All B = 0', inputs: { ...BASE, b11: 0, b12: 0, b22: 0 } },
  poynting: { name: 'Starting case with Poynting factor', inputs: { ...BASE, poynting: true } },
  'benzene-toluene': { name: 'Real data · benzene + toluene, 360 K', inputs: { ...BASE, T: 360, P: 80, b11: -933.0, b12: -1194.5, b22: -1529.2, system: 'benzene-toluene' },
    source: 'Real data: benzene (1) + toluene (2) at 360 K, 80 kPa, ideal liquid. Antoine constants from the NIST Chemistry WebBook. B₁₁ and B₂₂ from the Ambrose correlation B = a − b exp(c/T) fitted to measured data (benzene 290–600 K, toluene 341–583 K). B₁₂ is the geometric mean, an assumption: no measured cross coefficient is used.' },
};
let currentSystem = null;
const RANGES = { T: [300, 390], P: [1, 200], z: [0, 1], b11: [-5000, 500], b12: [-5000, 500], b22: [-5000, 500], v1: [1, 1000], v2: [1, 1000], A: [-1, 1.8], A12: [-1, 3], A21: [-1, 3], tau12: [-2, 6], tau21: [-2, 6], alpha: [0.1, 0.6] };
const LABELS = { T: 'Temperature', P: 'Pressure', z: 'z₁', b11: 'B₁₁', b12: 'B₁₂', b22: 'B₂₂', v1: 'v₁ᴸ', v2: 'v₂ᴸ', A: 'A', A12: 'A₁₂', A21: 'A₂₁', tau12: 'τ₁₂', tau21: 'τ₂₁', alpha: 'α' };
const NOTE_IDS = { concept1: 'note-concept1', concept2: 'note-concept2', concept3: 'note-concept3', decomposition: 'note-decomposition', cross: 'note-cross', scale: 'note-scale', decision: 'note-decision' };
const study = { inputs: null, result: null, cases: [], decomposition: null, cross: null, scale: null };

function cell(t) { const td = document.createElement('td'); td.textContent = t; return td; }
function li(h) { const e = document.createElement('li'); e.innerHTML = h; return e; }
function bText(i) { return num(i.b11, 5) + ', ' + num(i.b12, 5) + ', ' + num(i.b22, 5); }
function modelText(i) { return i.model === 'margules' ? 'Margules A = ' + num(i.A) : i.model === 'margules2' ? 'Margules A₁₂ = ' + num(i.A12) + ', A₂₁ = ' + num(i.A21) : i.model === 'nrtl' ? 'NRTL τ₁₂ = ' + num(i.tau12) + ', τ₂₁ = ' + num(i.tau21) + ', α = ' + num(i.alpha) : 'ideal liquid'; }
const pct = (a, b) => a == null || b == null || !Number.isFinite(a) || !Number.isFinite(b) || b === 0 ? null : 100 * (a - b) / b;

function showControls() { const m = $('model').value; $('margules-control').hidden = m !== 'margules'; $('margules2-control').hidden = m !== 'margules2'; $('nrtl-control').hidden = m !== 'nrtl'; }
function applyInputs(i) { setSystem(i.system); $('model').value = i.model; $('poynting').checked = Boolean(i.poynting); for (const k of Object.keys(RANGES)) if (i[k] !== undefined) $(k).value = String(i[k]); showControls(); }

function readInputs() {
  const model = $('model').value, keys = ['T', 'P', 'z', 'b11', 'b12', 'b22', 'v1', 'v2', ...MODEL_KEYS[model]], inputs = { model, poynting: $('poynting').checked, ...(currentSystem ? { system: currentSystem } : {}) }, errors = [];
  for (const k of Object.keys(RANGES)) { const e = $('error-' + k); if (e) e.hidden = true; $(k)?.removeAttribute('aria-invalid'); }
  for (const k of keys) {
    const raw = $(k).value.trim(), v = Number(raw), [lo, hi] = RANGES[k];
    let msg = '';
    if (raw === '' || !Number.isFinite(v)) msg = 'Enter a number for ' + LABELS[k] + '.';
    else if (v < lo || v > hi) msg = LABELS[k] + ' must lie between ' + lo + ' and ' + hi + '.';
    if (msg) { errors.push({ id: k, msg }); const e = $('error-' + k); e.textContent = msg; e.hidden = false; $(k).setAttribute('aria-invalid', 'true'); }
    inputs[k] = v;
  }
  return { inputs, errors };
}

function showErrors(errors) {
  const box = $('form-error');
  if (!errors.length) { box.hidden = true; box.replaceChildren(); return; }
  const list = document.createElement('ul');
  for (const e of errors) { const item = document.createElement('li'), a = document.createElement('a'); a.href = '#' + e.id; a.textContent = e.msg; item.append(a); list.append(item); }
  box.replaceChildren(Object.assign(document.createElement('p'), { textContent: 'Correct these entries, then calculate again:' }), list); box.hidden = false; box.focus();
}

function invalidateGraduate(msg) {
  study.decomposition = null; study.cross = null; study.scale = null;
  for (const id of ['dec-wrap', 'cross-wrap', 'scale-wrap']) $(id).hidden = true;
  for (const id of ['dec-status', 'cross-status', 'scale-status']) $(id).textContent = msg || '';
}

function friendly(message) {
  if (/truncation guard/.test(message)) return 'The second-virial truncation guard is exceeded: max|Bᵢⱼ| × max(P, Pˢᵃᵗ)/RT must not exceed 0.1. Reduce |B| or the pressure; at this size an equation of state is needed.';
  if (/Antoine|outside.*range|Temperature outside/i.test(message) && currentSystem) return 'The real-data correlations for this system apply only within their temperature ranges (benzene Antoine 333.4–373.5 K). Choose T inside that range.';
  if (/Nonconvex liquid/.test(message)) return 'This liquid model splits into two liquids at this temperature. Use Lab 06 for VLLE, or reduce the nonideality.';
  return message;
}

function calculate({ quiet = false } = {}) {
  const { inputs, errors } = readInputs(); showErrors(errors);
  if (errors.length) return false;
  let r;
  try { r = solve(inputs); } catch (error) { showErrors([{ id: 'b22', msg: friendly(error.message) }]); return false; }
  if (JSON.stringify(inputs) !== JSON.stringify(study.inputs)) invalidateGraduate('Settings changed. Run this investigation again for the current state.');
  study.inputs = inputs; study.result = r;
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderChart();
  for (const id of ['save-case', 'run-dec', 'run-cross', 'run-scale', 'export-study']) $(id).disabled = false;
  $('graduate-baseline').textContent = 'Current state: ' + num(inputs.T, 5) + ' K, ' + num(inputs.P) + ' kPa, z₁ = ' + num(inputs.z) + ', B = ' + bText(inputs) + ' cm³ mol⁻¹, ' + modelText(inputs) + (inputs.poynting ? ', with Poynting' : '') + ' · β = ' + num(r.real.beta, 4) + ' (ideal vapor ' + num(r.ideal.beta, 4) + ').';
  if (!quiet) $('status').textContent = 'Calculated. Add the result to the comparison before changing a setting.';
  return true;
}

function kValues(q) { return q.x != null && q.y != null && q.beta > 1e-9 && q.beta < 1 - 1e-9 ? [q.y / q.x, (1 - q.y) / (1 - q.x)] : [null, null]; }

function renderResult() {
  const { real: q, ideal: o } = study.result, two = q.type === 'Liquid + vapor';
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-phase').textContent = q.type + (o.type !== q.type ? ' · ideal vapor gives ' + o.type.toLowerCase() : '');
  const db = pct(q.beta, o.beta);
  $('phase-interpretation').textContent = two
    ? 'Both vapors use the same liquid and saturation pressures. The vapor amount changes by ' + (db == null ? '—' : signed(db, 1) + '%') + ' when the vapor is treated as nonideal.'
    : 'The feed is single-phase at this T and P, so the vapor correction shows only in the bubble and dew pressures.';
  const p = $('prediction').value, size = db == null ? null : Math.abs(db) < 2 ? 'small' : Math.abs(db) <= 10 ? 'medium' : 'large';
  $('prediction-feedback').textContent = p && size ? (p === size ? 'Your prediction matches the calculation.' : 'The vapor amount changes by ' + num(Math.abs(db), 2) + '% here. Questions B and C in Step 4 explain why.') : '';
  const kq = kValues(q), ko = kValues(o);
  const rows = [
    ['Vapor fraction β', o.beta, q.beta, 4],
    ['Liquid x₁', o.x, q.x, 4],
    ['Vapor y₁', o.y, q.y, 4],
    ['K₁ = y₁/x₁', ko[0], kq[0], 4],
    ['K₂ = y₂/x₂', ko[1], kq[1], 4],
    ['Bubble pressure / kPa', study.result.bubble.ideal, study.result.bubble.virial, 6],
    ['Dew pressure / kPa', study.result.dew.ideal, study.result.dew.virial, 6],
  ];
  $('compare-body').replaceChildren(...rows.map(([label, a, b, d]) => { const tr = document.createElement('tr'), th = document.createElement('th'); th.scope = 'row'; th.textContent = label; const ch = pct(b, a); tr.append(th, cell(num(a, d)), cell(num(b, d)), cell(ch == null ? '—' : signed(ch, 2) + '%')); return tr; }));
  $('result-Z').textContent = q.vapor ? num(q.vapor.Z, 5) : 'No vapor';
  $('result-phi').textContent = q.vapor ? num(q.vapor.phi[0], 5) + ', ' + num(q.vapor.phi[1], 5) : '—';
  $('result-ind').textContent = num(q.input.indicator, 3);
  $('result-fug').textContent = q.fugacityResidual == null ? '—' : q.fugacityResidual.toExponential(2);
}

function renderPaper() {
  const { real: q } = study.result, s = q.input, i = study.inputs, RT = vr.R * i.T, list = $('calc-steps');
  const B = s.B.map(b => b * 1e6);
  list.replaceChildren(li('Saturation pressures at ' + num(i.T, 5) + ' K: P₁ˢᵃᵗ = ' + num(s.sat[0] / 1000, 5) + ' kPa, P₂ˢᵃᵗ = ' + num(s.sat[1] / 1000, 5) + ' kPa. RT = ' + num(RT, 6) + ' J mol⁻¹.'));
  if (q.vapor && q.y != null) {
    const y = q.y, Bm = q.vapor.Bmix * 1e6;
    list.append(
      li('Mixture coefficient at y₁ = ' + num(y, 4) + ': B<sub>mix</sub> = y₁²B₁₁ + 2y₁y₂B₁₂ + y₂²B₂₂ = ' + num(Bm, 5) + ' cm³ mol⁻¹, so Z = 1 + B<sub>mix</sub>P/RT = 1 + (' + num(Bm, 5) + ' × 10⁻⁶)(' + num(i.P * 1000) + ')/' + num(RT, 6) + ' = ' + num(q.vapor.Z, 5) + '.'),
      li('Vapor mixture: ln φ₁ = (2(y₁B₁₁ + y₂B₁₂) − B<sub>mix</sub>)P/RT = ' + num(q.vapor.lnPhi[0], 4) + ', ln φ₂ = ' + num(q.vapor.lnPhi[1], 4) + '.'),
      li('Pure saturated vapor: ln φ₁ˢᵃᵗ = B₁₁P₁ˢᵃᵗ/RT = ' + num(s.lnSat[0], 4) + ', ln φ₂ˢᵃᵗ = B₂₂P₂ˢᵃᵗ/RT = ' + num(s.lnSat[1], 4) + (i.poynting ? '. Poynting: ln Πᵢ = vᵢᴸ(P − Pᵢˢᵃᵗ)/RT = ' + num(s.lnPoynting[0], 4) + ', ' + num(s.lnPoynting[1], 4) : '') + '.'),
      li('Check component 1: y₁φ₁P = ' + num(q.fV[0] / 1000, 6) + ' kPa and x₁γ₁φ₁ˢᵃᵗP₁ˢᵃᵗΠ₁ = ' + num(q.fL[0] / 1000, 6) + ' kPa.'),
    );
  } else list.append(li('No vapor is present at this T and P, so only the bubble and dew pressures in Step 2 show the vapor correction.'));
  if (B.every(b => b === 0)) list.append(li('With all B = 0, every φ equals 1 and the two columns in Step 2 are identical.'));
}

async function renderChart() {
  if (!study.result) return;
  if (!window.Plotly) { setTimeout(renderChart, 200); return; }
  const view = $('view').value, rows = vr.curves(study.result.r, 100), q = study.result.real;
  let traces, yTitle;
  if (view === 'Z') {
    traces = [{ x: rows.map(r => r.x), y: rows.map(() => 1), name: 'Ideal gas · Z = 1', mode: 'lines', line: { color: c.graphite, width: 1.5, dash: 'dash' } },
      { x: rows.map(r => r.x), y: rows.map(r => r.Z), name: 'Virial vapor Z', mode: 'lines', line: { color: c.amber, width: 2.5 } }];
    if (q.vapor) traces.push({ x: [q.y], y: [q.vapor.Z], name: 'Equilibrium vapor', mode: 'markers', marker: { color: c.ink, size: 10 }, line: { color: c.ink } });
    yTitle = 'Compressibility Z';
  } else {
    traces = [{ x: rows.map(r => r.x), y: rows.map(() => 1), name: 'Ideal vapor · φ = 1', mode: 'lines', line: { color: c.graphite, width: 1.5, dash: 'dash' } },
      { x: rows.map(r => r.x), y: rows.map(r => r.phi[0]), name: 'φ₁', mode: 'lines', line: { color: c.teal, width: 2.5 } },
      { x: rows.map(r => r.x), y: rows.map(r => r.phi[1]), name: 'φ₂', mode: 'lines', line: { color: c.amber, width: 2.5 } }];
    if (q.vapor) traces.push({ x: [q.y, q.y], y: q.vapor.phi, name: 'Equilibrium vapor', mode: 'markers', marker: { color: c.ink, size: 9 }, line: { color: c.ink } });
    yTitle = 'Fugacity coefficient φᵢ';
  }
  const layout = { margin: { l: 80, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false, hovermode: 'closest',
    xaxis: { title: { text: 'Vapor mole fraction y₁' }, range: [0, 1], zeroline: false, linecolor: c.graphite, gridcolor: c.mist }, yaxis: { title: { text: yTitle }, zeroline: false, linecolor: c.graphite, gridcolor: c.mist, tickformat: '.4f' } };
  try { await window.Plotly.react('vr-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* numbers are in Step 2 */ }
  $('chart-legend').replaceChildren(...traces.map(t => { const s = document.createElement('span'), e = document.createElement('i'); e.style.borderColor = t.line.color; if (t.mode === 'markers') e.className = 'legend-dot'; else e.style.borderTopStyle = t.line.dash === 'dash' ? 'dashed' : 'solid'; s.append(e, document.createTextNode(t.name)); return s; }));
  $('chart-note').textContent = view === 'Z'
    ? 'Z is below 1 because the coefficients are negative (net attraction). The departure grows in proportion to P and to |B|.'
    : 'φᵢ is the factor by which the vapor fugacity of i differs from yᵢP. The component with the more negative self and cross coefficients has the smaller φ.';
}

function runDecomposition() {
  if (!study.result) return;
  const rows = decomposition(study.result);
  if (!rows) { $('dec-status').textContent = 'There is no vapor at this state. Choose conditions inside the two-phase region.'; $('dec-wrap').hidden = true; return; }
  study.decomposition = true;
  $('dec-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(String(r.component)), cell(signed(r.lnPhi, 5)), cell(signed(r.lnPhiSat, 5)), cell(study.inputs.poynting ? signed(r.lnPoynting, 5) : '0 · off'), cell(signed(r.net, 5) + ' (' + signed(100 * (Math.exp(r.net) - 1), 2) + '% in K)')); return tr; }));
  $('dec-wrap').hidden = false;
  $('dec-status').textContent = 'Net change in ln Kᵢ = ln φᵢˢᵃᵗ + ln Πᵢ − ln φᵢ at fixed liquid composition and γᵢ. The flash then adjusts x and y, so the K-values in Step 2 also include that shift.';
}

function runCross() {
  if (!study.result) return;
  const rows = crossStudy(study.inputs); study.cross = true;
  $('cross-body').replaceChildren(...rows.map((r, k) => { const tr = document.createElement('tr'); tr.append(cell(num(r.b12, 5)), cell(k === 0 ? 'Supplied' : r.geometric ? 'Geometric mean' : num(r.b12 / study.inputs.b12, 2) + ' × supplied'), cell(r.status === 'ok' ? num(r.beta, 4) : 'Failed: ' + friendly(r.reason)), cell(num(r.y, 4)), cell(num(r.bubble, 6))); return tr; }));
  $('cross-wrap').hidden = false;
  const ok = rows.filter(r => r.status === 'ok' && Number.isFinite(r.bubble));
  $('cross-status').textContent = ok.length > 1 ? 'Across these B₁₂ values the bubble pressure spans ' + num(Math.min(...ok.map(r => r.bubble)), 6) + '–' + num(Math.max(...ok.map(r => r.bubble)), 6) + ' kPa. B₁₁ and B₂₂ are unchanged.' : 'Compare the rows that calculated.';
}

function runScale() {
  if (!study.result) return;
  const rows = scaleStudy(study.inputs); study.scale = true;
  $('scale-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(r.factor) + '×'), cell(r.status === 'ok' ? 'Calculated' : 'Refused: ' + friendly(r.reason)), cell(num(r.Z, 5)), cell(r.status === 'ok' ? num(r.beta, 4) + ' / ' + num(r.betaIdeal, 4) : '—'), cell(r.bubbleError == null ? '—' : signed(r.bubbleError, 2)), cell(num(r.indicator, 3))); return tr; }));
  $('scale-wrap').hidden = false;
  const fail = rows.find(r => r.status !== 'ok');
  $('scale-status').textContent = 'The error column is (ideal − virial)/virial bubble pressure.' + (fail ? ' The ' + fail.factor + '× case is refused by the truncation guard.' : '');
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([k, id]) => [k, $(id).value])); }
function summary(r) { return { Z: r.real.vapor ? r.real.vapor.Z : null, beta: r.real.beta, betaIdeal: r.ideal.beta, bubble: r.bubble.virial, bubbleIdeal: r.bubble.ideal }; }

function saveCase() {
  if (!study.result) return;
  const name = $('case-name').value.trim() || 'Case ' + (study.cases.length + 1);
  study.cases.push({ name, inputs: { ...study.inputs }, summary: summary(study.result) }); renderCases();
  $('status').textContent = 'Saved “' + name + '”. Change one setting, calculate, then save the next case.';
}

function renderCases() {
  $('comparison-empty').hidden = study.cases.length > 0; $('comparison-table-wrap').hidden = !study.cases.length;
  $('comparison-body').replaceChildren(...study.cases.map(s => {
    const tr = document.createElement('tr'), m = s.summary;
    tr.append(cell(s.name), cell(num(s.inputs.P)), cell(bText(s.inputs)), cell(num(m.Z, 5)), cell(num(m.beta, 4) + ' / ' + num(m.betaIdeal, 4)), cell(num(m.bubble, 6) + ' / ' + num(m.bubbleIdeal, 6)));
    const td = document.createElement('td'), b = document.createElement('button');
    b.type = 'button'; b.className = 'secondary-button'; b.textContent = 'Reopen'; b.setAttribute('aria-label', 'Reopen ' + s.name);
    b.addEventListener('click', () => { applyInputs(s.inputs); $('case-name').value = s.name; calculate({ quiet: true }); $('status').textContent = 'Reopened and recalculated “' + s.name + '”.'; $('results').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    td.append(b); tr.append(td); return tr;
  }));
}

function setSystem(system) {
  currentSystem = SYSTEMS[system] ? system : null;
  const note = $('case-source');
  if (note) { const c = Object.values(CASES).find(x => x.inputs.system === currentSystem && x.source); note.textContent = currentSystem && c ? c.source : ''; note.hidden = !currentSystem; }
}
function loadCase(id) {
  const p = CASES[id]; if (!p) return;
  applyInputs(p.inputs); $('case-name').value = p.name;
  for (const b of document.querySelectorAll('[data-case]')) b.setAttribute('aria-pressed', String(b.dataset.case === id));
  $('status').textContent = p.name + ' loaded. Make a prediction, then press Compare the two vapors.';
}

function validInputs(i) {
  if (!i || !MODELS.includes(i.model)) return false;
  return ['T', 'P', 'z', 'b11', 'b12', 'b22', 'v1', 'v2', ...MODEL_KEYS[i.model]].every(k => Number.isFinite(i[k]) && i[k] >= RANGES[k][0] && i[k] <= RANGES[k][1]);
}

function exportStudy() {
  const record = { schema: SCHEMA, engineVersion: vr.VIRIAL_VERSION, graduateVersion: VIRIAL_GRADUATE_VERSION, savedAt: new Date().toISOString(),
    inputs: study.inputs || readInputs().inputs, prediction: $('prediction').value, caseName: $('case-name').value, cases: study.cases, view: $('view').value,
    notes: notes(), reflection: $('reflection').value, investigations: { decomposition: Boolean(study.decomposition), cross: Boolean(study.cross), scale: Boolean(study.scale) } };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab09-virial-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded. Open it later to restore the cases, settings and notes.';
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2e6) throw new Error('The file is larger than a Lab 09 study.');
    const rec = JSON.parse(await file.text());
    if (rec.schema !== SCHEMA) throw new Error('This file is not a Lab 09 (2027) study.');
    if (!validInputs(rec.inputs)) throw new Error('The saved inputs are invalid.');
    applyInputs(rec.inputs); $('prediction').value = rec.prediction || ''; $('case-name').value = typeof rec.caseName === 'string' ? rec.caseName.slice(0, 80) : '';
    $('view').value = rec.view === 'Z' ? 'Z' : 'phi';
    for (const [k, id] of Object.entries(NOTE_IDS)) $(id).value = typeof rec.notes?.[k] === 'string' ? rec.notes[k] : '';
    $('reflection').value = typeof rec.reflection === 'string' ? rec.reflection : '';
    const cases = [];
    for (const s of (Array.isArray(rec.cases) ? rec.cases : []).slice(0, 50)) {
      if (!validInputs(s?.inputs) || typeof s.name !== 'string') continue;
      try { cases.push({ name: s.name.slice(0, 80), inputs: { ...s.inputs, poynting: Boolean(s.inputs.poynting) }, summary: summary(solve(s.inputs)) }); } catch { /* skip cases the engine now refuses */ }
    }
    study.cases = cases; study.inputs = null; renderCases(); calculate({ quiet: true });
    if (rec.investigations?.decomposition) runDecomposition();
    if (rec.investigations?.cross) runCross();
    if (rec.investigations?.scale) runScale();
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases and the investigations were recalculated from the saved inputs.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

function init() {
  showControls();
  for (const b of document.querySelectorAll('[data-case]')) b.addEventListener('click', () => loadCase(b.dataset.case));
  $('model').addEventListener('change', showControls);
  $('calculate').addEventListener('click', () => calculate());
  $('vr-form').addEventListener('submit', e => { e.preventDefault(); calculate(); });
  $('view').addEventListener('change', renderChart);
  $('save-case').addEventListener('click', saveCase);
  $('run-dec').addEventListener('click', runDecomposition); $('run-cross').addEventListener('click', runCross); $('run-scale').addEventListener('click', runScale);
  $('check-evidence').addEventListener('click', () => { const r = evidenceCheck({ decomposition: study.decomposition, cross: study.cross, scale: study.scale, notes: notes() }); $('evidence-status').textContent = r.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : r.issues.join(' '); });
  $('export-study').addEventListener('click', exportStudy); $('import-study').addEventListener('change', openStudy);
  loadCase('baseline');
}

init();
