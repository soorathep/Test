/** Lab 07 · 2027 preview page module. Calculations use the shared adiabatic engine. */
import * as ad from '../../labs/assets/adiabatic.js';
import { palette as c } from '../../labs/assets/palette.js';
import { ADIABATIC_GRADUATE_VERSION, MODELS, MODEL_KEYS, modelParameters, solve, feedSweep, modelComparison, dutyForVapor, evidenceCheck } from './adiabatic-graduate.js';

const SCHEMA = 'skh-thermo-adiabatic-study/1';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d });
const BASE = { model: 'ideal', z: 0.4 };
const CASES = {
  baseline: { name: 'Starting case · 370 K feed to 90 kPa', inputs: { ...BASE, feedT: 370, P: 90 } },
  hotter: { name: 'Hotter feed · 390 K to 90 kPa', inputs: { ...BASE, feedT: 390, P: 90 } },
  cooler: { name: 'Cooler feed · 340 K to 90 kPa', inputs: { ...BASE, feedT: 340, P: 90 } },
  'lower-p': { name: 'Lower outlet pressure · 370 K to 60 kPa', inputs: { ...BASE, feedT: 370, P: 60 } },
};
const RANGES = { feedT: [300, 390], P: [1, 200], z: [0, 1], A: [-1, 1.8], A12: [-1, 3], A21: [-1, 3], tau12: [-2, 6], tau21: [-2, 6], alpha: [0.1, 0.6] };
const LABELS = { feedT: 'Feed temperature', P: 'Outlet pressure', z: 'z₁', A: 'A', A12: 'A₁₂', A21: 'A₂₁', tau12: 'τ₁₂', tau21: 'τ₂₁', alpha: 'α' };
const MODEL_NAMES = { ideal: 'Ideal liquid', margules: 'Margules', margules2: 'Margules · 2 parameters', nrtl: 'NRTL' };
const NOTE_IDS = { concept1: 'note-concept1', concept2: 'note-concept2', concept3: 'note-concept3', sweep: 'note-sweep', models: 'note-models', duty: 'note-duty', decision: 'note-decision' };
const study = { system: null, inputs: null, result: null, cases: [], sweep: null, models: null, duty: null };

function cell(t) { const td = document.createElement('td'); td.textContent = t; return td; }
function li(h) { const e = document.createElement('li'); e.innerHTML = h; return e; }
function modelText(i) { return i.model === 'margules' ? 'Margules A = ' + num(i.A) : i.model === 'margules2' ? 'Margules A₁₂ = ' + num(i.A12) + ', A₂₁ = ' + num(i.A21) : i.model === 'nrtl' ? 'NRTL τ₁₂ = ' + num(i.tau12) + ', τ₂₁ = ' + num(i.tau21) + ', α = ' + num(i.alpha) : 'Ideal liquid'; }

function showControls() { const m = $('model').value; $('margules-control').hidden = m !== 'margules'; $('margules2-control').hidden = m !== 'margules2'; $('nrtl-control').hidden = m !== 'nrtl'; }
function applyInputs(i) { $('model').value = i.model; for (const k of Object.keys(RANGES)) if (i[k] !== undefined) $(k).value = String(i[k]); showControls(); }

function readInputs() {
  const model = $('model').value, keys = ['feedT', 'P', 'z', ...MODEL_KEYS[model]], inputs = { model }, errors = [];
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
  study.sweep = null; study.models = null; study.duty = null;
  for (const id of ['sweep-wrap', 'models-wrap']) $(id).hidden = true;
  for (const id of ['sweep-status', 'models-status', 'duty-status']) $(id).textContent = msg || '';
}

function calculate({ quiet = false } = {}) {
  const { inputs, errors } = readInputs(); showErrors(errors);
  if (errors.length || !study.system) return false;
  let r;
  try { r = solve(study.system, inputs); } catch (error) { showErrors([{ id: 'feedT', msg: error.message }]); return false; }
  if (JSON.stringify(inputs) !== JSON.stringify(study.inputs)) invalidateGraduate('Settings changed. Run this investigation again for the current feed.');
  study.inputs = inputs; study.result = r;
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderChart();
  for (const id of ['save-case', 'run-sweep', 'run-models', 'run-duty', 'export-study']) $(id).disabled = false;
  $('graduate-baseline').textContent = 'Current feed: ' + num(inputs.feedT, 5) + ' K liquid to ' + num(inputs.P) + ' kPa, z₁ = ' + num(inputs.z) + ', ' + modelText(inputs) + ' · outlet ' + num(r.T, 5) + ' K, β = ' + num(r.beta, 4) + '.';
  if (!quiet) $('status').textContent = 'Calculated. Add the result to the comparison before changing a setting.';
  return true;
}

function renderResult() {
  const r = study.result, i = study.inputs, flashed = r.beta > 1e-9;
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-phase').textContent = flashed ? (r.beta < 1 - 1e-9 ? 'Liquid + vapor' : 'Vapor only') : 'Liquid only · no flash';
  $('phase-interpretation').textContent = flashed
    ? 'Part of the liquid vaporizes. The energy for vaporization comes from cooling the whole stream, so the outlet is colder than the feed.'
    : 'The feed enthalpy is below that of the saturated liquid at the outlet pressure, so nothing vaporizes and the outlet stays at the feed temperature.';
  const p = $('prediction').value, dir = r.T < i.feedT - 1e-6 ? 'lower' : r.T > i.feedT + 1e-6 ? 'higher' : 'same';
  $('prediction-feedback').textContent = p ? (p === dir ? 'Your prediction matches the calculation.' : 'The outlet temperature is ' + dir + ' than the feed temperature here. Step 3 shows why.') : '';
  $('result-T').textContent = num(r.T, 6); $('result-T-note').textContent = 'K · ' + num(r.T - i.feedT, 4) + ' K relative to the feed';
  $('result-beta').textContent = num(r.beta, 4);
  $('result-xy').textContent = (r.x === null ? '—' : num(r.x, 4)) + ', ' + (r.y === null ? '—' : num(r.y, 4));
  $('result-hf').textContent = num(r.H, 6) + ' J mol⁻¹'; $('result-hout').textContent = num(r.Hout, 6) + ' J mol⁻¹';
  $('result-tb').textContent = r.bubbleT === null ? 'Outside 300–390 K' : num(r.bubbleT, 6) + ' K';
  $('result-res').textContent = r.energyResidual.toExponential(2);
}

function renderPaper() {
  const r = study.result, i = study.inputs, list = $('calc-steps');
  list.replaceChildren(
    li('Feed enthalpy: h<sub>F</sub> = C<sub>p</sub>(z)(T<sub>F</sub> − 350) with C<sub>p</sub>(z) = ' + num(i.z) + '(100) + ' + num(1 - i.z) + '(120) = ' + num(r.cp) + ' J mol⁻¹ K⁻¹, so h<sub>F</sub> = ' + num(r.H) + ' J mol⁻¹.'),
  );
  if (r.beta > 1e-9 && r.y !== null) {
    list.append(
      li('At the outlet, T = ' + num(r.T, 6) + ' K and P = ' + num(i.P) + ' kPa; TP equilibrium gives x₁ = ' + num(r.x, 4) + ' and y₁ = ' + num(r.y, 4) + ' (as in Lab 01).'),
      li('Latent heat of the vapor: Δh<sub>vap</sub>(y) = ' + num(r.y, 4) + '(30 000) + ' + num(1 - r.y, 4) + '(35 000) = ' + num(r.latent) + ' J mol⁻¹.'),
      li('Energy balance with equal liquid and vapor C<sub>p</sub>: C<sub>p</sub>(T<sub>F</sub> − T) = β Δh<sub>vap</sub>(y), so β = ' + num(r.cp) + ' × ' + num(i.feedT - r.T, 5) + '/' + num(r.latent) + ' = ' + num(r.betaClosed, 5) + '.'),
    );
  } else list.append(li('h<sub>F</sub> is below the saturated-liquid enthalpy at the outlet pressure, so β = 0 and T = T<sub>F</sub>.'));
}

async function renderChart() {
  const r = study.result; if (!r) return;
  if (!window.Plotly) { setTimeout(renderChart, 200); return; }
  const i = study.inputs, curve = ad.energyCurve(study.system, i.P * 1000, i.z, modelParameters(i));
  const traces = [
    { x: curve.flatMap(v => [v.T, v.T]), y: curve.flatMap(v => [v.min, v.max]), name: 'Outlet enthalpy at equilibrium', mode: 'lines', line: { color: c.teal, width: 2 } },
    { x: study.system.rangeK, y: [r.H, r.H], name: 'Feed enthalpy', mode: 'lines', line: { color: c.amber, width: 2, dash: 'dash' } },
    { x: [r.T], y: [r.Hout], name: 'Adiabatic outlet', mode: 'markers', marker: { color: c.ink, size: 10 }, line: { color: c.ink } },
  ];
  const layout = { margin: { l: 80, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false, hovermode: 'closest',
    xaxis: { title: { text: 'Outlet temperature / K' }, zeroline: false, linecolor: c.graphite, gridcolor: c.mist }, yaxis: { title: { text: 'Enthalpy / J mol⁻¹' }, zeroline: false, linecolor: c.graphite, gridcolor: c.mist } };
  try { await window.Plotly.react('ad-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* numbers are in Step 2 */ }
  $('chart-legend').replaceChildren(...traces.map(t => { const s = document.createElement('span'), e = document.createElement('i'); e.style.borderColor = t.line.color; if (t.mode === 'markers') e.className = 'legend-dot'; else e.style.borderTopStyle = t.line.dash === 'dash' ? 'dashed' : 'solid'; s.append(e, document.createTextNode(t.name)); return s; }));
}

function runSweep() {
  if (!study.result) return;
  const s = feedSweep(study.system, study.inputs); study.sweep = true;
  $('sweep-body').replaceChildren(...s.rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(r.feedT)), cell(r.status === 'ok' ? (r.beta > 1e-9 ? 'Liquid + vapor' : 'Liquid only') : 'Failed: ' + r.reason), cell(num(r.T, 6)), cell(num(r.beta, 4))); return tr; }));
  $('sweep-wrap').hidden = false;
  $('sweep-status').textContent = s.bubbleT === null ? 'The bubble temperature lies outside 300–390 K at this pressure.' : 'Bubble temperature of the feed at ' + num(study.inputs.P) + ' kPa: ' + num(s.bubbleT, 6) + ' K. Feeds below it do not flash.';
}

function runModels() {
  if (!study.result) return;
  const rows = modelComparison(study.system, study.inputs); study.models = true;
  $('models-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(r.label), cell(num(r.bubbleT, 6)), cell(r.status === 'ok' ? num(r.T, 6) : 'Failed: ' + r.reason), cell(num(r.beta, 4)), cell(num(r.x, 4)), cell(num(r.y, 4))); return tr; }));
  $('models-wrap').hidden = false;
  $('models-status').textContent = 'Same feed (' + num(study.inputs.feedT) + ' K, z₁ = ' + num(study.inputs.z) + ') and outlet pressure (' + num(study.inputs.P) + ' kPa). Only the liquid activity model changes.';
}

function runDuty() {
  if (!study.result) return;
  try {
    const d = dutyForVapor(study.system, study.inputs, Number($('target-beta').value)); study.duty = { target: d.targetBeta };
    $('duty-status').textContent = 'β = ' + num(d.beta, 4) + ' at ' + num(study.inputs.P) + ' kPa needs T = ' + num(d.T, 6) + ' K (x₁ = ' + num(d.x, 4) + ', y₁ = ' + num(d.y, 4) + '). Outlet h = ' + num(d.Hout) + ' J mol⁻¹, feed h = ' + num(d.Hfeed) + ' J mol⁻¹, so Q = ' + num(d.Q) + ' J per mol of feed.';
  } catch (error) { $('duty-status').textContent = error.message; }
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([k, id]) => [k, $(id).value])); }
function summary(r) { return { T: r.T, beta: r.beta, x: r.x, y: r.y }; }

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
    tr.append(cell(s.name), cell(num(s.inputs.feedT)), cell(num(s.inputs.P)), cell(modelText(s.inputs)), cell(num(m.T, 6)), cell(num(m.beta, 4)), cell((m.x === null ? '—' : num(m.x, 4)) + ', ' + (m.y === null ? '—' : num(m.y, 4))));
    const td = document.createElement('td'), b = document.createElement('button');
    b.type = 'button'; b.className = 'secondary-button'; b.textContent = 'Reopen'; b.setAttribute('aria-label', 'Reopen ' + s.name);
    b.addEventListener('click', () => { applyInputs(s.inputs); $('case-name').value = s.name; calculate({ quiet: true }); $('status').textContent = 'Reopened and recalculated “' + s.name + '”.'; $('results').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    td.append(b); tr.append(td); return tr;
  }));
}

function loadCase(id) {
  const p = CASES[id]; if (!p) return;
  applyInputs(p.inputs); $('case-name').value = p.name;
  for (const b of document.querySelectorAll('[data-case]')) b.setAttribute('aria-pressed', String(b.dataset.case === id));
  $('status').textContent = p.name + ' loaded. Make a prediction, then press Calculate.';
}

function validInputs(i) {
  if (!i || !MODELS.includes(i.model)) return false;
  return ['feedT', 'P', 'z', ...MODEL_KEYS[i.model]].every(k => Number.isFinite(i[k]) && i[k] >= RANGES[k][0] && i[k] <= RANGES[k][1]);
}

function exportStudy() {
  const record = { schema: SCHEMA, engineVersion: ad.ADIABATIC_VERSION, graduateVersion: ADIABATIC_GRADUATE_VERSION, savedAt: new Date().toISOString(),
    inputs: study.inputs || readInputs().inputs, prediction: $('prediction').value, caseName: $('case-name').value, cases: study.cases, targetBeta: $('target-beta').value,
    notes: notes(), reflection: $('reflection').value, investigations: { sweep: Boolean(study.sweep), models: Boolean(study.models), duty: Boolean(study.duty) } };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab07-adiabatic-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded. Open it later to restore the cases, settings and notes.';
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2e6) throw new Error('The file is larger than a Lab 07 study.');
    const rec = JSON.parse(await file.text());
    if (rec.schema !== SCHEMA) throw new Error('This file is not a Lab 07 (2027) study.');
    if (!validInputs(rec.inputs)) throw new Error('The saved inputs are invalid.');
    applyInputs(rec.inputs); $('prediction').value = rec.prediction || ''; $('case-name').value = typeof rec.caseName === 'string' ? rec.caseName.slice(0, 80) : '';
    $('target-beta').value = rec.targetBeta ?? '0.3';
    for (const [k, id] of Object.entries(NOTE_IDS)) $(id).value = typeof rec.notes?.[k] === 'string' ? rec.notes[k] : '';
    $('reflection').value = typeof rec.reflection === 'string' ? rec.reflection : '';
    study.cases = (Array.isArray(rec.cases) ? rec.cases : []).filter(s => validInputs(s?.inputs) && typeof s.name === 'string').slice(0, 50)
      .map(s => ({ name: s.name.slice(0, 80), inputs: s.inputs, summary: summary(solve(study.system, s.inputs)) }));
    study.inputs = null; renderCases(); calculate({ quiet: true });
    if (rec.investigations?.sweep) runSweep();
    if (rec.investigations?.models) runModels();
    if (rec.investigations?.duty) runDuty();
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases and the investigations were recalculated from the saved inputs.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

async function init() {
  showControls();
  for (const b of document.querySelectorAll('[data-case]')) b.addEventListener('click', () => loadCase(b.dataset.case));
  $('model').addEventListener('change', showControls);
  $('calculate').addEventListener('click', () => calculate());
  $('ad-form').addEventListener('submit', e => { e.preventDefault(); calculate(); });
  $('save-case').addEventListener('click', saveCase);
  $('run-sweep').addEventListener('click', runSweep); $('run-models').addEventListener('click', runModels); $('run-duty').addEventListener('click', runDuty);
  $('check-evidence').addEventListener('click', () => { const r = evidenceCheck({ sweep: study.sweep, models: study.models, duty: study.duty, notes: notes() }); $('evidence-status').textContent = r.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : r.issues.join(' '); });
  $('export-study').addEventListener('click', exportStudy); $('import-study').addEventListener('change', openStudy);
  try {
    const response = await fetch('../labs/assets/systems.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error('HTTP ' + response.status);
    study.system = (await response.json()).systems.synthetic;
    $('calculate').disabled = false; loadCase('baseline');
  } catch (error) { $('status').textContent = 'The property record could not be loaded (' + error.message + '). Reload the page to try again.'; }
}

init();
