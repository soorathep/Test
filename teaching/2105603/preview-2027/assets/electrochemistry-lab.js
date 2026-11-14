/** Lab 13 · 2027 preview page module. Calculations use the shared electrochemistry engine. */
import * as engine from '../../labs/assets/electrochemistry.js';
import { palette as c } from '../../labs/assets/palette.js';
import { CELL_GRADUATE_VERSION, R, F, N, solve, activityStudy, temperatureStudy, dischargeStudy, evidenceCheck } from './electrochemistry-graduate.js';

const SCHEMA = 'skh-thermo-cell-study/1';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d }).replace(/^-/, '−');
const mV = v => num(1000 * v, 4) + ' mV';
const BASE = { T: 298.15, cL: 0.01, cR: 1, gL: 1, gR: 1 };
const CASES = {
  baseline: { name: 'Starting case · 0.01 and 1.0', inputs: { ...BASE } },
  swap: { name: 'Concentrations exchanged', inputs: { ...BASE, cL: 1, cR: 0.01 } },
  equal: { name: 'Equal concentrations', inputs: { ...BASE, cL: 1, cR: 1 } },
  'same-ratio': { name: 'Same ratio · 0.001 and 0.1', inputs: { ...BASE, cL: 0.001, cR: 0.1 } },
};
const RANGES = { cL: [0.000001, 10], cR: [0.000001, 10], T: [273.15, 373.15], gL: [0.0001, 10], gR: [0.0001, 10] };
const LABELS = { cL: 'Left concentration', cR: 'Right concentration', T: 'Temperature', gL: 'Left γ', gR: 'Right γ' };
const NOTE_IDS = { concept1: 'note-concept1', concept2: 'note-concept2', concept3: 'note-concept3', activity: 'note-activity', temperature: 'note-temperature', discharge: 'note-discharge', decision: 'note-decision' };
const study = { inputs: null, result: null, cases: [], activity: null, temperature: null, discharge: null };

function cell(t) { const td = document.createElement('td'); td.textContent = t; return td; }
function li(h) { const e = document.createElement('li'); e.innerHTML = h; return e; }
const ZERO = 1e-9;
const cathode = E => (E > ZERO ? 'Right' : E < -ZERO ? 'Left' : 'Neither');

function applyInputs(i) { for (const k of Object.keys(RANGES)) if (i[k] !== undefined) $(k).value = String(i[k]); }

function readInputs() {
  const inputs = {}, errors = [];
  for (const k of Object.keys(RANGES)) {
    const e = $('error-' + k); e.hidden = true; $(k).removeAttribute('aria-invalid');
    const raw = $(k).value.trim(), v = Number(raw), [lo, hi] = RANGES[k];
    let msg = '';
    if (raw === '' || !Number.isFinite(v)) msg = 'Enter a number for ' + LABELS[k] + '.';
    else if (v < lo || v > hi) msg = LABELS[k] + ' must lie between ' + lo + ' and ' + hi + '.';
    if (msg) { errors.push({ id: k, msg }); e.textContent = msg; e.hidden = false; $(k).setAttribute('aria-invalid', 'true'); }
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
  study.activity = null; study.temperature = null; study.discharge = null;
  for (const id of ['act-wrap', 'temp-wrap', 'dis-wrap']) $(id).hidden = true;
  for (const id of ['act-status', 'temp-status', 'dis-status']) $(id).textContent = msg || '';
}

function calculate({ quiet = false } = {}) {
  const { inputs, errors } = readInputs(); showErrors(errors);
  if (errors.length) return false;
  let s;
  try { s = solve(inputs); } catch (error) { showErrors([{ id: 'cL', msg: error.message }]); return false; }
  if (JSON.stringify(inputs) !== JSON.stringify(study.inputs)) invalidateGraduate('Settings changed. Run this investigation again for the current cell.');
  study.inputs = inputs; study.result = s;
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderChart();
  for (const id of ['save-case', 'run-act', 'run-temp', 'run-dis', 'export-study']) $(id).disabled = false;
  $('graduate-baseline').textContent = 'Current cell: ' + num(inputs.cL) + ' and ' + num(inputs.cR) + ' mol L⁻¹, γ = ' + num(inputs.gL) + ', ' + num(inputs.gR) + ' at ' + num(inputs.T, 5) + ' K · E = ' + mV(s.E) + '.';
  if (!quiet) $('status').textContent = 'Calculated. Add the result to the comparison before changing a setting.';
  return true;
}

function renderResult() {
  const s = study.result, i = study.inputs, E = s.E, side = cathode(E);
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-phase').textContent = 'E = ' + mV(E);
  $('phase-interpretation').textContent = side === 'Neither' ? 'The two activities are equal, so Q = K = 1 and there is no driving force.' : side === 'Right' ? 'E > 0: the cell runs as written. Metal dissolves on the dilute left side and deposits on the concentrated right side.' : 'E < 0: the reverse reaction is favored. The left solution is now the more concentrated one, so the left electrode is the cathode.';
  const p = $('prediction').value, sign = E > ZERO ? 'positive' : E < -ZERO ? 'negative' : 'zero';
  $('prediction-feedback').textContent = p ? (p === sign ? 'Your prediction matches the calculation.' : 'E is ' + sign + ' here. Question B in Step 4 explains what sets the sign.') : '';
  const role = (k) => (side === 'Neither' ? '—' : (side === k ? 'Cathode' : 'Anode'));
  const rx = (k) => (side === 'Neither' ? 'No net reaction' : side === k ? 'M²⁺ + 2e⁻ → M' : 'M → M²⁺ + 2e⁻');
  $('electrode-body').replaceChildren(...[['Left', s.aL, 'Left'], ['Right', s.aR, 'Right']].map(([n, a, k]) => { const tr = document.createElement('tr'), th = document.createElement('th'); th.scope = 'row'; th.textContent = n; tr.append(th, cell(num(a, 4)), cell(role(k)), cell(rx(k))); return tr; }));
  $('result-Q').textContent = num(s.r.Q, 4);
  $('result-dG').textContent = num(s.dG / 1000, 4) + ' kJ mol⁻¹';
  $('result-slope').textContent = num(1000 * s.slope, 4) + ' mV per decade';
  $('result-res').textContent = Math.abs(s.E - s.closed).toExponential(2);
}

function renderPaper() {
  const s = study.result, i = study.inputs, list = $('calc-steps'), k = R * i.T / (N * F);
  list.replaceChildren(
    li('Activities: a<sub>L</sub> = γ<sub>L</sub>c<sub>L</sub>/c° = ' + num(s.aL, 4) + ', a<sub>R</sub> = ' + num(s.aR, 4) + '.'),
    li('Cell reaction as written: M²⁺(R) → M²⁺(L), n = 2, E° = 0. Q = a<sub>L</sub>/a<sub>R</sub> = ' + num(s.r.Q, 4) + '.'),
    li('RT/nF = ' + num(R, 5) + ' × ' + num(i.T, 5) + '/(2 × ' + num(F, 6) + ') = ' + num(k, 4) + ' V, so E = −(RT/nF) ln Q = −' + num(k, 4) + ' × (' + num(Math.log(s.r.Q), 4) + ') = ' + mV(s.E) + '.'),
    li('ΔG = −nFE = −2 × ' + num(F, 6) + ' × ' + num(s.E, 4) + ' = ' + num(s.dG / 1000, 4) + ' kJ per mol of M²⁺ transferred.'),
  );
}

async function renderChart() {
  if (!study.result) return;
  if (!window.Plotly) { setTimeout(renderChart, 200); return; }
  const s = study.result, i = study.inputs, xs = Array.from({ length: 61 }, (_, k) => -3 + k / 10), slope = 1000 * s.slope;
  const ref = 1000 * R * 298.15 * Math.LN10 / (N * F), x0 = Math.log10(s.aR / s.aL);
  const traces = [{ x: xs, y: xs.map(x => slope * x), name: 'At ' + num(i.T, 5) + ' K', mode: 'lines', line: { color: c.teal, width: 2.5 } }];
  if (Math.abs(i.T - 298.15) > 1e-6) traces.push({ x: xs, y: xs.map(x => ref * x), name: 'At 298.15 K', mode: 'lines', line: { color: c.graphite, width: 1.5, dash: 'dot' } });
  traces.push({ x: [x0], y: [1000 * s.E], name: 'Current cell', mode: 'markers', marker: { color: c.amber, size: 11, line: { color: c.ink, width: 1.5 } }, line: { color: c.amber } });
  const layout = { margin: { l: 70, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false, hovermode: 'closest',
    xaxis: { title: { text: 'log₁₀(a_R/a_L)' }, range: [Math.min(-3, x0 - 0.3), Math.max(3, x0 + 0.3)], zeroline: true, zerolinecolor: c.mist, linecolor: c.graphite, gridcolor: c.mist }, yaxis: { title: { text: 'E / mV' }, zeroline: true, zerolinecolor: c.mist, linecolor: c.graphite, gridcolor: c.mist } };
  try { await window.Plotly.react('ec-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* numbers are in Step 2 */ }
  $('chart-legend').replaceChildren(...traces.map(t => { const s2 = document.createElement('span'), e = document.createElement('i'); e.style.borderColor = t.line.color; if (t.mode === 'markers') e.className = 'legend-dot'; else e.style.borderTopStyle = t.line.dash === 'dot' ? 'dotted' : 'solid'; s2.append(e, document.createTextNode(t.name)); return s2; }));
  $('chart-note').textContent = 'Every tenfold change in the activity ratio changes E by ' + num(slope, 3) + ' mV at this temperature. The line passes through zero because E° = 0 for identical electrodes.';
}

function runActivity() {
  if (!study.result) return;
  const rows = activityStudy(study.inputs); study.activity = true;
  $('act-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(r.label), cell(num(r.IL, 3)), cell(num(r.gL, 3)), cell(num(r.IR, 3)), cell(num(r.gR, 3)), cell(r.status === 'ok' ? num(1000 * r.E, 4) : 'Failed: ' + r.reason)); return tr; }));
  $('act-wrap').hidden = false;
  $('act-status').textContent = 'Single-ion log₁₀γ = −0.509 z²√I (limiting) or −0.509 z²√I/(1 + √I) (extended), z = 2, I = 3c for MX₂ at 298 K. The current γ inputs are replaced in this table only.';
}

function runTemperature() {
  if (!study.result) return;
  const rows = temperatureStudy(study.inputs); study.temperature = true;
  $('temp-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(r.T, 5)), cell(num(1000 * r.E, 4)), cell(num(r.dG / 1000, 4)), cell(num(r.dS, 4)), cell(num(r.qrev / 1000, 4)), cell(num(Math.abs(r.dH) < 1e-6 ? 0 : r.dH / 1000, 3))); return tr; }));
  $('temp-wrap').hidden = false;
  const dEdT = (rows.at(-1).E - rows[0].E) / (rows.at(-1).T - rows[0].T);
  $('temp-status').textContent = 'dE/dT = ' + num(1e6 * dEdT, 4) + ' µV K⁻¹ at fixed activities. γ is held constant; real activity coefficients also change with temperature.';
}

function runDischarge() {
  if (!study.result) return;
  const d = dischargeStudy(study.inputs); study.discharge = true;
  $('dis-body').replaceChildren(...d.rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(100 * r.f, 3) + '%'), cell(num(r.cL, 4)), cell(num(r.cR, 4)), cell(num(r.q, 4)), cell(num(1000 * r.E, 4))); return tr; }));
  $('dis-wrap').hidden = false;
  $('dis-status').textContent = d.qmax === 0 ? 'The activities are already equal, so no work is available.' : 'Total charge ' + num(d.qmax, 4) + ' C. Reversible work W = ∫E dq = ' + num(d.W, 4) + ' J, a mean voltage of ' + mV(d.meanE) + ', compared with ' + mV(Math.abs(d.rows[0].E)) + ' at the start.';
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([k, id]) => [k, $(id).value])); }
function summary(s) { return { E: s.E }; }

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
    tr.append(cell(s.name), cell(num(s.inputs.cL)), cell(num(s.inputs.cR)), cell(num(s.inputs.gL) + ', ' + num(s.inputs.gR)), cell(num(s.inputs.T, 5)), cell(num(1000 * m.E, 4)), cell(cathode(m.E)));
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
  $('status').textContent = p.name + ' loaded. Make a prediction, then press Calculate the cell.';
}

function validInputs(i) { return i && Object.keys(RANGES).every(k => Number.isFinite(i[k]) && i[k] >= RANGES[k][0] && i[k] <= RANGES[k][1]); }

function exportStudy() {
  const record = { schema: SCHEMA, engineVersion: engine.ELECTROCHEMISTRY_VERSION ?? null, graduateVersion: CELL_GRADUATE_VERSION, savedAt: new Date().toISOString(),
    inputs: study.inputs || readInputs().inputs, prediction: $('prediction').value, caseName: $('case-name').value, cases: study.cases,
    notes: notes(), reflection: $('reflection').value, investigations: { activity: Boolean(study.activity), temperature: Boolean(study.temperature), discharge: Boolean(study.discharge) } };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab13-cell-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded. Open it later to restore the cases, settings and notes.';
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2e6) throw new Error('The file is larger than a Lab 13 study.');
    const rec = JSON.parse(await file.text());
    if (rec.kind === 'electrochemistry') throw new Error('This file was saved by the earlier Lab 13 calculator. Open it in the current Lab 13.');
    if (rec.schema !== SCHEMA) throw new Error('This file is not a Lab 13 (2027) study.');
    if (!validInputs(rec.inputs)) throw new Error('The saved inputs are invalid.');
    applyInputs(rec.inputs); $('prediction').value = rec.prediction || ''; $('case-name').value = typeof rec.caseName === 'string' ? rec.caseName.slice(0, 80) : '';
    for (const [k, id] of Object.entries(NOTE_IDS)) $(id).value = typeof rec.notes?.[k] === 'string' ? rec.notes[k] : '';
    $('reflection').value = typeof rec.reflection === 'string' ? rec.reflection : '';
    const cases = [];
    for (const s of (Array.isArray(rec.cases) ? rec.cases : []).slice(0, 50)) {
      if (!validInputs(s?.inputs) || typeof s.name !== 'string') continue;
      try { cases.push({ name: s.name.slice(0, 80), inputs: s.inputs, summary: summary(solve(s.inputs)) }); } catch { /* skip cases the engine now refuses */ }
    }
    study.cases = cases; study.inputs = null; renderCases(); calculate({ quiet: true });
    if (rec.investigations?.activity) runActivity();
    if (rec.investigations?.temperature) runTemperature();
    if (rec.investigations?.discharge) runDischarge();
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases and the investigations were recalculated from the saved inputs.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

function init() {
  for (const b of document.querySelectorAll('[data-case]')) b.addEventListener('click', () => loadCase(b.dataset.case));
  $('calculate').addEventListener('click', () => calculate());
  $('ec-form').addEventListener('submit', e => { e.preventDefault(); calculate(); });
  $('save-case').addEventListener('click', saveCase);
  $('run-act').addEventListener('click', runActivity); $('run-temp').addEventListener('click', runTemperature); $('run-dis').addEventListener('click', runDischarge);
  $('check-evidence').addEventListener('click', () => { const r = evidenceCheck({ activity: study.activity, temperature: study.temperature, discharge: study.discharge, notes: notes() }); $('evidence-status').textContent = r.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : r.issues.join(' '); });
  $('export-study').addEventListener('click', exportStudy); $('import-study').addEventListener('change', openStudy);
  loadCase('baseline');
}

init();
