/** Lab 12 · 2027 preview page module. Calculations use the shared reaction engine. */
import * as rx from '../../labs/assets/reaction.js';
import { palette as c } from '../../labs/assets/palette.js';
import { REACTION_GRADUATE_VERSION, R, TREF, lnK, equilibrium, solve, temperatureStudy, drivingForce, pressureStudy, evidenceCheck } from './reaction-graduate.js';

const SCHEMA = 'skh-thermo-reaction-study/1';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d }).replace(/^-/, '−');
const pct = v => num(100 * v, 3) + '%';
const BASE = { T: 350, P: 100, nA2: 1, nI: 0, dG: -4, dH: 50, dCp: 0, Pstd: 100 };
const CASES = {
  baseline: { name: 'Starting case · 350 K, 100 kPa', inputs: { ...BASE } },
  'high-p': { name: 'Ten times the pressure · 1000 kPa', inputs: { ...BASE, P: 1000 } },
  inert: { name: 'Add 4 mol inert gas', inputs: { ...BASE, nI: 4 } },
  hot: { name: 'Heated to 400 K', inputs: { ...BASE, T: 400 } },
};
const RANGES = { T: [250, 650], P: [1, 5000], nA2: [0.001, 100], nI: [0, 100], dG: [-200, 200], dH: [-500, 500], dCp: [-500, 500] };
const LABELS = { T: 'Temperature', P: 'Pressure', nA2: 'A₂ fed', nI: 'Inert gas fed', dG: 'ΔG°', dH: 'ΔH°', dCp: 'ΔCp°' };
const NOTE_IDS = { concept1: 'note-concept1', concept2: 'note-concept2', concept3: 'note-concept3', temperature: 'note-temperature', driving: 'note-driving', pressure: 'note-pressure', decision: 'note-decision' };
const study = { inputs: null, result: null, cases: [], temperature: null, driving: null, pressure: null };

function cell(t) { const td = document.createElement('td'); td.textContent = t; return td; }
function li(h) { const e = document.createElement('li'); e.innerHTML = h; return e; }

function applyInputs(i) { for (const k of Object.keys(RANGES)) if (i[k] !== undefined) $(k).value = String(i[k]); }

function readInputs() {
  const inputs = { Pstd: 100 }, errors = [];
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

function friendly(message) {
  if (/depletion boundary/.test(message)) return 'The equilibrium lies so close to complete reaction (or no reaction) that the composition cannot be resolved. ln K is still meaningful; change T or P to see the composition.';
  return message;
}

function invalidateGraduate(msg) {
  study.temperature = null; study.driving = null; study.pressure = null;
  for (const id of ['temp-wrap', 'drive-wrap', 'press-wrap']) $(id).hidden = true;
  for (const id of ['temp-status', 'drive-status', 'press-status']) $(id).textContent = msg || '';
}

function calculate({ quiet = false } = {}) {
  const { inputs, errors } = readInputs(); showErrors(errors);
  if (errors.length) return false;
  let s;
  try { s = solve(inputs); } catch (error) { showErrors([{ id: 'T', msg: friendly(error.message) }]); return false; }
  if (JSON.stringify(inputs) !== JSON.stringify(study.inputs)) invalidateGraduate('Settings changed. Run this investigation again for the current reactor.');
  study.inputs = inputs; study.result = s;
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderChart();
  for (const id of ['save-case', 'run-temp', 'run-drive', 'run-press', 'export-study']) $(id).disabled = false;
  $('graduate-baseline').textContent = 'Current reactor: ' + num(inputs.T, 5) + ' K, ' + num(inputs.P) + ' kPa, ' + num(inputs.nA2) + ' mol A₂, ' + num(inputs.nI) + ' mol inert · K = ' + num(s.K, 4) + ', ' + pct(s.conversion) + ' dissociated.';
  if (!quiet) $('status').textContent = 'Calculated. Add the result to the comparison before changing a setting.';
  return true;
}

function renderResult() {
  const s = study.result, i = study.inputs, comp = s.e.composition;
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-phase').textContent = 'ξ = ' + num(s.xi, 4) + ' mol';
  $('phase-interpretation').textContent = pct(s.conversion) + ' of the A₂ fed has dissociated. ' + (s.K > 1 ? 'K > 1 favors products, but the reaction stops where Q = K.' : 'K < 1 favors the reactant, yet some A still forms because pure A₂ has Q = 0 < K.');
  const p = $('prediction').value, band = s.conversion < 0.3 ? 'low' : s.conversion <= 0.9 ? 'mid' : 'high';
  $('prediction-feedback').textContent = p ? (p === band ? 'Your prediction matches the calculation.' : pct(s.conversion) + ' of the A₂ dissociates here. Question A in Step 4 shows the calculation.') : '';
  const rows = [['A₂', i.nA2, comp[0].n, comp[0].y], ['A', 0, comp[1].n, comp[1].y]];
  if (i.nI > 0) rows.push(['Inert', i.nI, i.nI, s.e.inertY]);
  rows.push(['Total', i.nA2 + i.nI, s.e.total, 1]);
  $('comp-body').replaceChildren(...rows.map(([a, f, n, y]) => { const tr = document.createElement('tr'), th = document.createElement('th'); th.scope = 'row'; th.textContent = a; tr.append(th, cell(num(f, 4)), cell(num(n, 4)), cell(num(y, 4))); return tr; }));
  $('result-K').textContent = num(s.K, 4) + ' (ln K = ' + num(s.lnK, 4) + ')';
  $('result-dG').textContent = num(s.dGT / 1000, 4) + ' kJ mol⁻¹';
  $('result-conv').textContent = pct(s.conversion);
  $('result-res').textContent = Math.abs(s.e.residual).toExponential(2);
}

function renderPaper() {
  const s = study.result, i = study.inputs, list = $('calc-steps'), r = i.P / 100;
  list.replaceChildren();
  if (i.T !== TREF) list.append(li('Van ’t Hoff: ln K(' + num(i.T, 5) + ') = ln K(350) + (ΔH°/R)(1/350 − 1/' + num(i.T, 5) + ')' + (i.dCp ? ' + ΔC<sub>p</sub>° term' : '') + ' = ' + num(-i.dG * 1000 / (R * TREF), 4) + ' + ' + num(s.lnK + i.dG * 1000 / (R * TREF), 4) + ' = ' + num(s.lnK, 4) + '.'));
  else list.append(li('K = exp(−ΔG°/RT) = exp(' + num(-i.dG * 1000) + '/(' + num(R, 5) + ' × 350)) = ' + num(s.K, 4) + '.'));
  list.append(li('Amounts: n<sub>A₂</sub> = ' + num(i.nA2) + ' − ξ, n<sub>A</sub> = 2ξ, n<sub>total</sub> = ' + num(i.nA2 + i.nI) + ' + ξ. Condition: K = (2ξ)²/[(' + num(i.nA2) + ' − ξ)(' + num(i.nA2 + i.nI) + ' + ξ)] × P/P° with P/P° = ' + num(r) + '.'));
  if (s.closed != null) list.append(li('Without inert gas this solves directly: ξ = n<sub>A₂,0</sub>[K/(K + 4P/P°)]<sup>1/2</sup> = ' + num(i.nA2) + ' × (' + num(s.K, 4) + '/' + num(s.K + 4 * r, 4) + ')<sup>1/2</sup> = ' + num(s.closed, 4) + ' mol.'));
  else list.append(li('With inert gas the equation is solved numerically: ξ = ' + num(s.xi, 4) + ' mol. Check: (2ξ)²/[(n₀ − ξ)(n<sub>total</sub>)] × P/P° = ' + num(4 * s.xi ** 2 / ((i.nA2 - s.xi) * s.e.total) * r, 4) + ' = K.'));
  list.append(li('Mole fractions: y<sub>A</sub> = 2ξ/n<sub>total</sub> = ' + num(s.e.composition[1].y, 4) + ', y<sub>A₂</sub> = ' + num(s.e.composition[0].y, 4) + '.'));
}

async function renderChart() {
  if (!study.result) return;
  if (!window.Plotly) { setTimeout(renderChart, 200); return; }
  const s = study.result, i = study.inputs, view = $('view').value;
  let traces, layout;
  const base = { margin: { l: 70, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false, hovermode: 'closest' };
  if (view === 'T') {
    const Ts = Array.from({ length: 81 }, (_, k) => 250 + 5 * k), conv = over => Ts.map(T => { try { return equilibrium(i, { ...over, T }).conversion; } catch { return null; } });
    traces = [
      { x: Ts, y: conv({}), name: 'At ' + num(i.P) + ' kPa', mode: 'lines', line: { color: c.teal, width: 2.5 } },
      { x: Ts, y: conv({ P: i.P * 10 }), name: 'At ' + num(i.P * 10) + ' kPa', mode: 'lines', line: { color: c.amber, width: 2.5 } },
      { x: [i.T], y: [s.conversion], name: 'Current state', mode: 'markers', marker: { color: c.ink, size: 10 }, line: { color: c.ink } },
    ];
    layout = { ...base, xaxis: { title: { text: 'Temperature / K' }, zeroline: false, linecolor: c.graphite, gridcolor: c.mist }, yaxis: { title: { text: 'Fraction of A₂ dissociated' }, range: [0, 1.02], zeroline: false, linecolor: c.graphite, gridcolor: c.mist } };
    $('chart-note').textContent = 'The dissociation is endothermic, so the curve rises with temperature. Higher pressure shifts the whole curve to higher temperatures.';
  } else {
    const curve = over => { try { return equilibrium(i, over).e.curve; } catch { return []; } }, a = curve({}), b = curve({ P: i.P * 10 });
    traces = [
      { x: a.map(p => p.xi), y: a.map(p => p.relativeG), name: 'At ' + num(i.P) + ' kPa', mode: 'lines', line: { color: c.teal, width: 2.5 } },
      { x: b.map(p => p.xi), y: b.map(p => p.relativeG), name: 'At ' + num(i.P * 10) + ' kPa', mode: 'lines', line: { color: c.amber, width: 2.5 } },
      { x: [s.xi], y: [s.e.relativeG], name: 'Equilibrium, current state', mode: 'markers', marker: { color: c.ink, size: 10 }, line: { color: c.ink } },
    ];
    layout = { ...base, xaxis: { title: { text: 'Extent of reaction ξ / mol' }, zeroline: false, linecolor: c.graphite, gridcolor: c.mist }, yaxis: { title: { text: '[G(ξ) − G(0)]/RT' }, zeroline: true, zerolinecolor: c.mist, linecolor: c.graphite, gridcolor: c.mist } };
    $('chart-note').textContent = 'The minimum of each curve is the equilibrium extent. The slope at any ξ is ln(Q/K): negative before the minimum, positive after it.';
  }
  try { await window.Plotly.react('rx-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* numbers are in Step 2 */ }
  $('chart-legend').replaceChildren(...traces.map(t => { const s2 = document.createElement('span'), e = document.createElement('i'); e.style.borderColor = t.line.color; if (t.mode === 'markers') e.className = 'legend-dot'; s2.append(e, document.createTextNode(t.name)); return s2; }));
}

function runTemperature() {
  if (!study.result) return;
  const s = temperatureStudy(study.inputs); study.temperature = true;
  const head = document.createElement('tr'); head.append(...['T / K', ...s.variants.map(v => 'ln K, ' + v.label), ...s.variants.map(v => 'Dissociated, ' + v.label)].map(t => { const th = document.createElement('th'); th.scope = 'col'; th.textContent = t; return th; }));
  $('temp-head').replaceChildren(head);
  $('temp-body').replaceChildren(...s.temps.map((T, k) => { const tr = document.createElement('tr'); tr.append(cell(num(T)), ...s.variants.map(v => cell(v.rows[k].status === 'ok' ? num(v.rows[k].lnK, 4) : '—')), ...s.variants.map(v => cell(v.rows[k].status === 'ok' ? pct(v.rows[k].conversion) : 'Failed'))); return tr; }));
  $('temp-wrap').hidden = false;
  $('temp-status').textContent = 'All variants share ΔG° at 350 K, so they agree there. Pressure ' + num(study.inputs.P) + ' kPa, ' + num(study.inputs.nI) + ' mol inert.';
}

function runDriving() {
  if (!study.result) return;
  const d = drivingForce(study.inputs); study.driving = true;
  $('drive-body').replaceChildren(...d.rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(r.yA2)), cell(num(r.yA)), cell(num(r.P)), cell(num(r.Q, 4)), cell(num(r.dG, 4)), cell(r.direction)); return tr; }));
  $('drive-wrap').hidden = false;
  $('drive-status').textContent = 'At ' + num(study.inputs.T, 5) + ' K, K = ' + num(Math.exp(d.lnK), 4) + '. ΔG < 0 means the forward reaction lowers the Gibbs energy.';
}

function runPressure() {
  if (!study.result) return;
  const rows = pressureStudy(study.inputs); study.pressure = true;
  $('press-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(r.label), cell(num(r.P, 5)), cell(num(r.nI)), cell(num(r.Pstd, 6)), cell(num(r.lnK, 5)), cell(r.status === 'ok' ? pct(r.conversion) : 'Failed: ' + friendly(r.reason)), cell(num(r.yA, 4))); return tr; }));
  $('press-wrap').hidden = false;
  $('press-status').textContent = 'For Δν = +1, K(1 atm) = K(1 bar) × (100/101.325). Rows 5 and 6 differ only in whether that conversion was made.';
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([k, id]) => [k, $(id).value])); }
function summary(s) { return { K: s.K, xi: s.xi, yA: s.e.composition[1].y }; }

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
    tr.append(cell(s.name), cell(num(s.inputs.T, 5)), cell(num(s.inputs.P)), cell(num(s.inputs.nI)), cell(num(m.K, 4)), cell(num(m.xi, 4)), cell(num(m.yA, 4)));
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
  $('status').textContent = p.name + ' loaded. Make a prediction, then press Calculate the equilibrium.';
}

function validInputs(i) { return i && Object.keys(RANGES).every(k => Number.isFinite(i[k]) && i[k] >= RANGES[k][0] && i[k] <= RANGES[k][1]); }

function exportStudy() {
  const record = { schema: SCHEMA, engineVersion: rx.REACTION_VERSION, graduateVersion: REACTION_GRADUATE_VERSION, savedAt: new Date().toISOString(),
    inputs: study.inputs || readInputs().inputs, prediction: $('prediction').value, caseName: $('case-name').value, cases: study.cases, view: $('view').value,
    notes: notes(), reflection: $('reflection').value, investigations: { temperature: Boolean(study.temperature), driving: Boolean(study.driving), pressure: Boolean(study.pressure) } };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab12-reaction-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded. Open it later to restore the cases, settings and notes.';
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2e6) throw new Error('The file is larger than a Lab 12 study.');
    const rec = JSON.parse(await file.text());
    if (rec.schema !== SCHEMA) throw new Error('This file is not a Lab 12 (2027) study.');
    if (!validInputs(rec.inputs)) throw new Error('The saved inputs are invalid.');
    applyInputs(rec.inputs); $('prediction').value = rec.prediction || ''; $('case-name').value = typeof rec.caseName === 'string' ? rec.caseName.slice(0, 80) : '';
    $('view').value = rec.view === 'T' ? 'T' : 'G';
    for (const [k, id] of Object.entries(NOTE_IDS)) $(id).value = typeof rec.notes?.[k] === 'string' ? rec.notes[k] : '';
    $('reflection').value = typeof rec.reflection === 'string' ? rec.reflection : '';
    const cases = [];
    for (const s of (Array.isArray(rec.cases) ? rec.cases : []).slice(0, 50)) {
      if (!validInputs(s?.inputs) || typeof s.name !== 'string') continue;
      try { const inputs = { ...s.inputs, Pstd: 100 }; cases.push({ name: s.name.slice(0, 80), inputs, summary: summary(solve(inputs)) }); } catch { /* skip cases the engine now refuses */ }
    }
    study.cases = cases; study.inputs = null; renderCases(); calculate({ quiet: true });
    if (rec.investigations?.temperature) runTemperature();
    if (rec.investigations?.driving) runDriving();
    if (rec.investigations?.pressure) runPressure();
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases and the investigations were recalculated from the saved inputs.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

function init() {
  for (const b of document.querySelectorAll('[data-case]')) b.addEventListener('click', () => loadCase(b.dataset.case));
  $('calculate').addEventListener('click', () => calculate());
  $('rx-form').addEventListener('submit', e => { e.preventDefault(); calculate(); });
  $('view').addEventListener('change', renderChart);
  $('save-case').addEventListener('click', saveCase);
  $('run-temp').addEventListener('click', runTemperature); $('run-drive').addEventListener('click', runDriving); $('run-press').addEventListener('click', runPressure);
  $('check-evidence').addEventListener('click', () => { const r = evidenceCheck({ temperature: study.temperature, driving: study.driving, pressure: study.pressure, notes: notes() }); $('evidence-status').textContent = r.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : r.issues.join(' '); });
  $('export-study').addEventListener('click', exportStudy); $('import-study').addEventListener('change', openStudy);
  loadCase('baseline');
}

init();
