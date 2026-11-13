/** Lab 06 · 2027 preview page module. Calculations use the shared VLLE engine. */
import * as engine from '../../labs/assets/vlle.js';
import * as liquid from '../../labs/assets/stability.js';
import { palette as c } from '../../labs/assets/palette.js';
import { PARAMETER_KEYS, PARAMETER_LABELS, MODELS, modelParameters } from './stability-graduate.js';
import { VLLE_GRADUATE_VERSION, VOLATILITY_P2, solve, phaseLabel, amountsForVaporFraction, pressureSweep, volatilityStudy, evidenceCheck } from './vlle-graduate.js';

const SCHEMA = 'skh-thermo-vlle-study/1';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d });
const exp = v => v == null || !Number.isFinite(v) ? '—' : Math.abs(v) < 1e-4 && v !== 0 ? v.toExponential(2) : num(v);
const BASE = { model: 'symmetric', A: 3, psat1: 80, psat2: 40 };
const CASES = {
  baseline: { name: 'Starting case · P₃, z₁ = 0.50', inputs: { ...BASE, pressureMode: 'triple', P: 100, z: 0.5 } },
  'feed-02': { name: 'Same pressure · P₃, z₁ = 0.20', inputs: { ...BASE, pressureMode: 'triple', P: 100, z: 0.2 } },
  'high-p': { name: 'Higher pressure · 140 kPa, z₁ = 0.50', inputs: { ...BASE, pressureMode: 'manual', P: 140, z: 0.5 } },
  'low-p': { name: 'Lower pressure · 100 kPa, z₁ = 0.50', inputs: { ...BASE, pressureMode: 'manual', P: 100, z: 0.5 } },
};
const RANGES = { A: [0, 6], A12: [0, 6], A21: [0, 6], tau12: [-2, 6], tau21: [-2, 6], alpha: [0.1, 0.6], psat1: [10, 200], psat2: [10, 200], P: [1, 500], z: [0, 1] };
const LABELS = { ...PARAMETER_LABELS, psat1: 'P₁ˢᵃᵗ', psat2: 'P₂ˢᵃᵗ', P: 'Pressure' };
const NOTE_IDS = { concept1: 'note-concept1', concept2: 'note-concept2', concept3: 'note-concept3', amounts: 'note-amounts', sweep: 'note-sweep', volatility: 'note-volatility', decision: 'note-decision' };
const study = { inputs: null, result: null, cases: [], amounts: null, sweep: null, volatility: null };

function cell(t) { const td = document.createElement('td'); td.textContent = t; return td; }
function li(h) { const e = document.createElement('li'); e.innerHTML = h; return e; }

function showControls() {
  const m = $('model').value;
  $('symmetric-control').hidden = m !== 'symmetric'; $('asymmetric-control').hidden = m !== 'asymmetric'; $('nrtl-control').hidden = m !== 'nrtl';
  $('pressure-control').hidden = $('pressure-mode').value !== 'manual';
}

function applyInputs(i) {
  $('model').value = i.model;
  for (const k of ['A', 'A12', 'A21', 'tau12', 'tau21', 'alpha', 'psat1', 'psat2', 'P', 'z']) if (i[k] !== undefined) $(k).value = String(i[k]);
  $('pressure-mode').value = i.pressureMode; showControls();
}

function readInputs() {
  const model = $('model').value, mode = $('pressure-mode').value, keys = [...PARAMETER_KEYS[model], 'psat1', 'psat2', ...(mode === 'manual' ? ['P'] : []), 'z'];
  const inputs = { model, pressureMode: mode }, errors = [];
  for (const id of Object.keys(RANGES)) { const e = $('error-' + id); if (e) { e.hidden = true; } $(id)?.removeAttribute('aria-invalid'); }
  for (const k of keys) {
    const raw = $(k).value.trim(), v = Number(raw), [lo, hi] = RANGES[k];
    let msg = '';
    if (raw === '' || !Number.isFinite(v)) msg = 'Enter a number for ' + LABELS[k] + '.';
    else if (v < lo || v > hi) msg = LABELS[k] + ' must lie between ' + lo + ' and ' + hi + '.';
    if (msg) { errors.push({ id: k, msg }); const e = $('error-' + k); e.textContent = msg; e.hidden = false; $(k).setAttribute('aria-invalid', 'true'); }
    inputs[k] = v;
  }
  if (mode !== 'manual') inputs.P = Number($('P').value) || 100;
  inputs.choice = Number($('choice').value);
  return { inputs, errors };
}

function showErrors(errors) {
  const box = $('form-error');
  if (!errors.length) { box.hidden = true; box.replaceChildren(); return; }
  const list = document.createElement('ul');
  for (const e of errors) { const item = document.createElement('li'), a = document.createElement('a'); a.href = '#' + e.id; a.textContent = e.msg; item.append(a); list.append(item); }
  box.replaceChildren(Object.assign(document.createElement('p'), { textContent: 'Correct these entries, then calculate again:' }), list); box.hidden = false; box.focus();
}

function invalidateGraduate(message) {
  study.amounts = null; study.sweep = null; study.volatility = null;
  for (const id of ['sweep-wrap', 'volatility-wrap']) $(id).hidden = true;
  for (const id of ['amounts-status', 'sweep-status', 'volatility-status']) $(id).textContent = message || '';
}

const sameState = (a, b) => b && JSON.stringify({ ...a, choice: 0 }) === JSON.stringify({ ...b, choice: 0 });

function calculate({ quiet = false } = {}) {
  const { inputs, errors } = readInputs(); showErrors(errors);
  if (errors.length) return false;
  let r;
  try { r = solve(inputs); } catch (error) { showErrors([{ id: inputs.pressureMode === 'manual' ? 'P' : 'model', msg: error.message }]); return false; }
  if (!sameState(inputs, study.inputs)) invalidateGraduate('Settings changed. Run this investigation again for the current state.');
  study.inputs = inputs; study.result = r;
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderChart();
  for (const id of ['save-case', 'run-amounts', 'run-sweep', 'run-volatility', 'export-study']) $(id).disabled = false;
  $('graduate-baseline').textContent = 'Current state: P = ' + num(r.P, 5) + ' kPa, z₁ = ' + num(r.z) + ' · ' + phaseLabel(r.type) + '.';
  if (!quiet) $('status').textContent = 'Calculated. Add the result to the comparison before changing a setting.';
  return true;
}

const INTERPRET = {
  VLLE: 'Two liquids and a vapor coexist. The pressure and all three compositions are fixed by the temperature; the feed only decides the amounts, and even those are not unique.',
  LLE: 'The pressure is above the three-phase pressure. The vapor Gibbs curve lies above the liquid common tangent, so two liquids coexist and no vapor forms.',
  VLE: 'One liquid coexists with vapor. Their compositions are fixed by T and P; the lever rule sets the amounts.',
  Vapor: 'The pressure is low enough that the vapor alone has the lowest Gibbs energy.',
  Liquid: 'The feed is a single stable liquid at this pressure.',
};

function renderResult() {
  const r = study.result, tri = r.type === 'VLLE';
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-phase').textContent = phaseLabel(r.type);
  $('phase-interpretation').textContent = INTERPRET[r.type] || '';
  const p = $('prediction').value;
  $('prediction-feedback').textContent = p ? (p === r.type ? 'Your prediction matches the calculation.' : 'You predicted ' + phaseLabel(p).toLowerCase() + '; the calculation gives ' + phaseLabel(r.type).toLowerCase() + '. Use Step 3 to see why.') : '';
  $('result-p').textContent = num(r.P, 6) + ' kPa';
  $('result-p-note').textContent = r.triple ? (tri ? 'the three-phase pressure P₃ at this T' : 'P₃ = ' + num(r.triple.P, 5) + ' kPa for this system') : 'this system has no three-phase pressure';
  $('phase-body').replaceChildren(...r.phases.map(ph => { const tr = document.createElement('tr'); tr.append(cell(ph.label === 'V' ? 'Vapor V' : ph.label === 'Lα' ? 'Liquid α' : ph.label === 'Lβ' ? 'Liquid β' : ph.kind === 'vapor' ? 'Vapor' : 'Liquid'), cell(num(ph.x, 6)), cell(num(ph.fraction, 4))); return tr; }));
  $('family-control').hidden = !tri;
  $('family-note').textContent = tri ? 'For this feed the vapor amount can be anything from ' + num(r.family.vaporMin, 4) + ' to ' + num(r.family.vaporMax, 4) + ' mol. The table shows one choice; the slider shows the others.' : 'The amounts are unique: ' + r.phases.length + (r.phases.length === 1 ? ' phase.' : ' phases and two balances.');
  $('result-balance').textContent = r.balanceResidual.toExponential(2);
  $('result-fug').textContent = r.equalityResidual === null ? 'Not applicable · one phase' : r.equalityResidual.toExponential(2);
}

function renderPaper() {
  const r = study.result, list = $('calc-steps'), i = study.inputs;
  list.replaceChildren();
  if (r.triple) {
    const t = r.triple, a1 = liquid.chemicalPotentials(t.xAlpha, modelParameters(i)).map(Math.exp);
    list.append(li('Liquid–liquid equilibrium fixes x₁ᵅ = ' + num(t.xAlpha) + ' and x₁ᵝ = ' + num(t.xBeta) + ' (as in Lab 04). Both liquids have the same activities: a₁ = x₁γ₁ = ' + num(a1[0]) + ', a₂ = x₂γ₂ = ' + num(a1[1]) + '.'));
    list.append(li('A vapor in equilibrium with both liquids has partial pressures p<sub>i</sub> = a<sub>i</sub>P<sub>i</sub><sup>sat</sup>: p₁ = ' + num(a1[0] * i.psat1) + ' kPa and p₂ = ' + num(a1[1] * i.psat2) + ' kPa.'));
    list.append(li('So P₃ = p₁ + p₂ = ' + num(t.P) + ' kPa and y₁ = p₁/P₃ = ' + num(t.y) + '.'));
  }
  if (r.type === 'VLLE') {
    const [a, b, v] = r.phases;
    list.append(li('Balances: f<sup>α</sup> + f<sup>β</sup> + f<sup>V</sup> = 1 and ' + num(a.x, 4) + 'f<sup>α</sup> + ' + num(b.x, 4) + 'f<sup>β</sup> + ' + num(v.x, 4) + 'f<sup>V</sup> = ' + num(r.z) + '. Two equations, three unknowns.'));
    list.append(li('With f<sup>V</sup> = ' + num(v.fraction, 4) + ': f<sup>β</sup> = (z₁ − f<sup>V</sup>y₁ − (1 − f<sup>V</sup>)x₁ᵅ)/(x₁ᵝ − x₁ᵅ) = ' + num(b.fraction, 4) + ', f<sup>α</sup> = ' + num(a.fraction, 4) + '.'));
  } else if (r.phases.length === 2) {
    const [a, b] = r.phases;
    list.append(li('Lever rule: f(' + b.label + ') = (z₁ − ' + num(a.x, 4) + ')/(' + num(b.x, 4) + ' − ' + num(a.x, 4) + ') = ' + num(b.fraction, 4) + '.'));
  } else list.append(li('One phase: its composition equals the feed, z₁ = ' + num(r.z) + '.'));
}

const trace = (x, y, name, color, dash = 'solid', mode = 'lines', symbol = 'circle') => ({ x, y, name, mode, line: { color, width: 2, dash }, marker: { color, size: 9, symbol }, connectgaps: false, hovertemplate: name + '<br>%{x:.4f}, %{y:.4f}<extra></extra>' });

async function renderChart() {
  const r = study.result; if (!r) return;
  if (!window.Plotly) { setTimeout(renderChart, 200); return; }
  const view = $('view').value, A = modelParameters(study.inputs), psat = [study.inputs.psat1, study.inputs.psat2];
  let traces, x, y, note, shapes = [];
  if (view === 'gibbs') {
    const cv = engine.curves(r);
    traces = [trace(cv.map(q => q.x), cv.map(q => q.gL), 'Liquid', c.teal), trace(cv.map(q => q.x), cv.map(q => q.gV), 'Vapor', c.amber), trace(cv.map(q => q.x), cv.map(q => q.hull), 'Lowest envelope', c.graphite, 'dash')];
    if (r.support) traces.push(trace([0, 1], [r.support.intercept, r.support.intercept + r.support.slope], 'Common tangent', c.graphite, 'dot'));
    traces.push(trace(r.phases.map(p => p.x), r.phases.map(p => p.g), 'Equilibrium phases', c.ink, 'solid', 'markers'));
    x = 'Mole fraction of component 1 · x₁ or y₁'; y = 'Gibbs energy of mixing / RT';
    note = 'Both curves share one reference. The stable phases sit where one straight line touches the lowest curves. Raising P lifts the vapor curve by ln P.';
  } else {
    const d = engine.pressureDiagram(A, psat), pts = d.points.filter(p => p.P !== null);
    traces = [trace(pts.map(p => p.x), pts.map(p => p.P), 'Bubble · x₁', c.teal), trace(pts.map(p => p.y), pts.map(p => p.P), 'Dew · y₁', c.teal, 'dash')];
    for (const t of d.triples) {
      traces.push(trace([t.xAlpha, t.xBeta], [t.P, t.P], 'Three-phase line', c.amber));
      traces.push(trace([t.xAlpha, t.xAlpha], [t.P, Math.max(t.P * 1.35, r.P * 1.05)], 'Liquid–liquid boundary', c.graphite, 'dot'), trace([t.xBeta, t.xBeta], [t.P, Math.max(t.P * 1.35, r.P * 1.05)], 'Liquid–liquid boundary (β)', c.graphite, 'dot'));
      traces.push(trace([t.y], [t.P], 'Three-phase vapor', c.amber, 'solid', 'markers', 'diamond'));
    }
    traces.push(trace([r.z], [r.P], 'Current feed and pressure', c.ink, 'solid', 'markers', 'cross'));
    x = 'Mole fraction of component 1 · x₁ or y₁'; y = 'Pressure / kPa';
    note = 'Solid teal: bubble curve (liquid). Dashed teal: dew curve (vapor). The amber line is the three-phase pressure. Dotted lines bound the two-liquid region above it.';
  }
  const layout = { margin: { l: 70, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false, hovermode: 'closest', shapes,
    xaxis: { title: { text: x }, range: [0, 1], zeroline: false, linecolor: c.graphite, gridcolor: c.mist }, yaxis: { title: { text: y }, zeroline: false, linecolor: c.graphite, gridcolor: c.mist } };
  try { await window.Plotly.react('vlle-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* tables hold values */ }
  $('chart-legend').replaceChildren(...traces.filter(t => !t.name.includes('(β)')).map(t => { const s = document.createElement('span'), i = document.createElement('i'); i.style.borderColor = t.line.color; if (t.mode === 'markers') i.className = 'legend-dot'; else i.style.borderTopStyle = t.line.dash === 'solid' ? 'solid' : 'dashed'; s.append(i, document.createTextNode(t.name)); return s; }));
  $('chart-note').textContent = note;
}

function runAmounts() {
  const r = study.result; if (!r) return;
  try {
    const a = amountsForVaporFraction(r, Number($('spec-fv').value));
    study.amounts = { fV: a.fV };
    $('amounts-status').textContent = 'Allowed vapor amount: ' + num(a.range[0], 4) + ' to ' + num(a.range[1], 4) + ' mol. With a vapor amount of ' + num(a.fV, 4) + ' mol: liquid α = ' + num(a.fAlpha, 4) + ' mol, liquid β = ' + num(a.fBeta, 4) + ' mol. Component balance residual ' + a.balance.toExponential(2) + '.';
  } catch (error) { $('amounts-status').textContent = error.message; }
}

function runSweep() {
  if (!study.result) return;
  const s = pressureSweep(study.inputs, [90, 95, 100, 105, 110, 112, 114, 120, 130, 140]);
  study.sweep = true;
  $('sweep-body').replaceChildren(...s.rows.map(row => {
    const tr = document.createElement('tr');
    tr.append(cell(num(row.P, 5) + (row.isTriple ? ' (P₃)' : '')), cell(row.type === 'failed' ? 'Failed: ' + row.reason : phaseLabel(row.type)), cell(row.phases.map(p => p.label + ' ' + num(p.x, 4)).join(', ')), cell(row.vaporRange ? num(row.vaporRange[0], 3) + ' to ' + num(row.vaporRange[1], 3) : num(row.vaporFraction, 4)));
    if (row.isTriple) tr.className = 'highlight-row';
    return tr;
  }));
  $('sweep-wrap').hidden = false;
  $('sweep-status').textContent = s.triple ? 'P₃ = ' + num(s.triple.P, 5) + ' kPa is included. The vapor amount jumps from a single value below P₃, to a range at P₃, to zero above it.' : 'This system has no three-phase pressure; the phases change continuously.';
}

function runVolatility() {
  if (!study.result) return;
  const rows = volatilityStudy(study.inputs);
  study.volatility = true;
  $('volatility-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(r.ratio)), cell(r.status === 'ok' ? r.reading : 'Failed: ' + r.reason), cell(num(r.P, 5)), cell(num(r.xAlpha, 4)), cell(num(r.y, 4)), cell(num(r.xBeta, 4))); if (r.status === 'ok' && !r.inside) tr.className = 'highlight-row'; return tr; }));
  $('volatility-wrap').hidden = false;
  const outside = rows.filter(r => r.status === 'ok' && !r.inside).map(r => num(r.ratio));
  $('volatility-status').textContent = 'P₂ˢᵃᵗ = ' + VOLATILITY_P2 + ' kPa for every row; the liquid model is unchanged. ' + (outside.length ? 'The vapor leaves the liquid gap at ratio ' + outside.join(', ') + '.' : 'The vapor stays inside the liquid gap at every ratio tested.');
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([k, id]) => [k, $(id).value])); }

function summary(r) { return { type: r.type, P: r.P, phases: r.phases.map(p => ({ label: p.label, x: p.x, fraction: p.fraction })) }; }

function saveCase() {
  if (!study.result) return;
  const name = $('case-name').value.trim() || 'Case ' + (study.cases.length + 1);
  study.cases.push({ name, inputs: { ...study.inputs }, summary: summary(study.result) });
  renderCases(); $('status').textContent = 'Saved “' + name + '”. Change one setting, calculate, then save the next case.';
}

function renderCases() {
  $('comparison-empty').hidden = study.cases.length > 0; $('comparison-table-wrap').hidden = !study.cases.length;
  $('comparison-body').replaceChildren(...study.cases.map(s => {
    const tr = document.createElement('tr'), m = s.summary;
    tr.append(cell(s.name), cell(num(m.P, 5)), cell(num(s.inputs.z)), cell(phaseLabel(m.type)), cell(m.phases.map(p => p.label + ' ' + num(p.x, 4)).join(', ')), cell(m.phases.map(p => p.label + ' ' + num(p.fraction, 3)).join(', ')));
    const td = document.createElement('td'), b = document.createElement('button');
    b.type = 'button'; b.className = 'secondary-button'; b.textContent = 'Reopen'; b.setAttribute('aria-label', 'Reopen ' + s.name);
    b.addEventListener('click', () => { applyInputs(s.inputs); $('choice').value = String(s.inputs.choice ?? 0.5); $('case-name').value = s.name; calculate({ quiet: true }); $('status').textContent = 'Reopened and recalculated “' + s.name + '”.'; $('results').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    td.append(b); tr.append(td); return tr;
  }));
}

function loadCase(id) {
  const p = CASES[id]; if (!p) return;
  applyInputs(p.inputs); $('choice').value = '0.5'; $('case-name').value = p.name;
  for (const b of document.querySelectorAll('[data-case]')) b.setAttribute('aria-pressed', String(b.dataset.case === id));
  $('status').textContent = p.name + ' loaded. Make a prediction, then press Calculate equilibrium.';
}

function validInputs(i) {
  if (!i || !MODELS.includes(i.model) || !['triple', 'manual'].includes(i.pressureMode)) return false;
  return [...PARAMETER_KEYS[i.model], 'psat1', 'psat2', 'P', 'z'].every(k => Number.isFinite(i[k]) && i[k] >= RANGES[k][0] && i[k] <= RANGES[k][1]);
}

function exportStudy() {
  const record = { schema: SCHEMA, engineVersion: engine.VLLE_VERSION, graduateVersion: VLLE_GRADUATE_VERSION, savedAt: new Date().toISOString(),
    inputs: study.inputs || readInputs().inputs, prediction: $('prediction').value, caseName: $('case-name').value, cases: study.cases,
    specFV: $('spec-fv').value, notes: notes(), reflection: $('reflection').value,
    investigations: { amounts: Boolean(study.amounts), sweep: Boolean(study.sweep), volatility: Boolean(study.volatility) } };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab06-vlle-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded. Open it later to restore the cases, settings and notes.';
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2e6) throw new Error('The file is larger than a Lab 06 study.');
    const rec = JSON.parse(await file.text());
    if (rec.schema !== SCHEMA) throw new Error('This file is not a Lab 06 (2027) study.');
    if (!validInputs(rec.inputs)) throw new Error('The saved inputs are invalid.');
    applyInputs(rec.inputs); $('choice').value = String(Number.isFinite(rec.inputs.choice) ? rec.inputs.choice : 0.5);
    $('prediction').value = rec.prediction || ''; $('case-name').value = typeof rec.caseName === 'string' ? rec.caseName.slice(0, 80) : '';
    $('spec-fv').value = rec.specFV ?? '0.3';
    for (const [k, id] of Object.entries(NOTE_IDS)) $(id).value = typeof rec.notes?.[k] === 'string' ? rec.notes[k] : '';
    $('reflection').value = typeof rec.reflection === 'string' ? rec.reflection : '';
    study.cases = (Array.isArray(rec.cases) ? rec.cases : []).filter(s => validInputs(s?.inputs) && typeof s.name === 'string').slice(0, 50)
      .map(s => ({ name: s.name.slice(0, 80), inputs: s.inputs, summary: summary(solve(s.inputs)) }));
    study.inputs = null; renderCases(); calculate({ quiet: true });
    if (rec.investigations?.amounts) runAmounts();
    if (rec.investigations?.sweep) runSweep();
    if (rec.investigations?.volatility) runVolatility();
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases and the investigations were recalculated from the saved inputs.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

function init() {
  showControls();
  for (const b of document.querySelectorAll('[data-case]')) b.addEventListener('click', () => loadCase(b.dataset.case));
  $('model').addEventListener('change', showControls); $('pressure-mode').addEventListener('change', showControls);
  $('calculate').addEventListener('click', () => calculate());
  $('vlle-form').addEventListener('submit', e => { e.preventDefault(); calculate(); });
  $('choice').addEventListener('input', () => { if (study.result?.type === 'VLLE') calculate({ quiet: true }); });
  $('view').addEventListener('change', renderChart);
  $('save-case').addEventListener('click', saveCase);
  $('run-amounts').addEventListener('click', runAmounts); $('run-sweep').addEventListener('click', runSweep); $('run-volatility').addEventListener('click', runVolatility);
  $('check-evidence').addEventListener('click', () => { const r = evidenceCheck({ amounts: study.amounts, sweep: study.sweep, volatility: study.volatility, notes: notes() }); $('evidence-status').textContent = r.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : r.issues.join(' '); });
  $('export-study').addEventListener('click', exportStudy); $('import-study').addEventListener('change', openStudy);
  loadCase('baseline');
}

init();
