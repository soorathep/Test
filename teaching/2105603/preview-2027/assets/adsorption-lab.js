/** Lab 11 · 2027 preview page module. Calculations use the shared adsorption engine. */
import * as ad from '../../labs/assets/adsorption.js';
import { palette as c } from '../../labs/assets/palette.js';
import { ADSORPTION_GRADUATE_VERSION, MODELS, R, solve, tFactor, isothermParameters, fitRangeStudy, heatStudy, swingStudy, evidenceCheck } from './adsorption-graduate.js';

const SCHEMA = 'skh-thermo-adsorption-study/1';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d }).replace(/^-/, '−');
const pct = v => num(100 * v, 3) + '%';
const BASE = { T: 300, V: 1, m: 20, n: 0.03, model: 'langmuir', qs: 2, b: 0.1, K: 0.2, Q: 25 };
const CASES = {
  baseline: { name: 'Starting case · 300 K, 20 g', inputs: { ...BASE } },
  empty: { name: 'No adsorbent', inputs: { ...BASE, m: 0 } },
  heated: { name: 'Heated to 340 K', inputs: { ...BASE, T: 340 } },
  henry: { name: 'Linear isotherm, same initial slope', inputs: { ...BASE, model: 'henry' } },
  co2: { name: 'Real data · CO₂ on zeolite 13X, 300 K', inputs: { ...BASE, n: 0.08, qs: 4.96, b: 0.46212, Q: 37.86 },
    source: 'Real data: CO₂ on zeolite 13X pellets (Grace MS 544HP), 1.0 L, 20 g, 0.080 mol CO₂. Langmuir model with constant saturation capacity from Son et al., J. Chem. Eng. Data 2018, 63, 1663 (Table S1): qs = 4.960 mol/kg, b = 1.1847×10⁻⁷ exp(4553/T) kPa⁻¹, so b(300 K) = 0.462 kPa⁻¹ and Q = 37.86 kJ/mol. Over 0–200 °C this simple model fits with RMSE 0.37 mol/kg. The authors’ 3-site Langmuir fit (RMSE 0.034 mol/kg) gives 13.3 kPa for this vessel at 300 K instead of 7.5 kPa, and 41.8 instead of 30.0 kPa at 340 K: the isotherm model matters more than the arithmetic.' },
};
const RANGES = { T: [250, 450], V: [0.01, 100], m: [0, 10000], n: [0.0001, 100], qs: [0.01, 50], b: [0.0001, 100], K: [0.0001, 100], Q: [0, 100] };
const LABELS = { T: 'Temperature', V: 'Free gas volume', m: 'Adsorbent mass', n: 'Gas inventory', qs: 'qs', b: 'b', K: 'K', Q: 'Q' };
const KEYS = { langmuir: ['qs', 'b'], henry: ['K'] };
const NOTE_IDS = { concept1: 'note-concept1', concept2: 'note-concept2', concept3: 'note-concept3', fits: 'note-fits', heat: 'note-heat', swing: 'note-swing', decision: 'note-decision' };
const MODEL_NAMES = { henry: 'Henry (linear)', langmuir: 'Langmuir', freundlich: 'Freundlich' };
const study = { inputs: null, result: null, cases: [], fits: null, heat: null, swing: null };

function cell(t) { const td = document.createElement('td'); td.textContent = t; return td; }
function li(h) { const e = document.createElement('li'); e.innerHTML = h; return e; }
const isoText = i => i.model === 'henry' ? 'Linear, K = ' + num(i.K) : 'Langmuir, qs = ' + num(i.qs) + ', b = ' + num(i.b);

function showControls() { const m = $('model').value; $('langmuir-control').hidden = m !== 'langmuir'; $('henry-control').hidden = m !== 'henry'; }
function applyInputs(i) { $('model').value = i.model; for (const k of Object.keys(RANGES)) if (i[k] !== undefined) $(k).value = String(i[k]); showControls(); }

function readInputs() {
  const model = $('model').value, keys = ['T', 'V', 'm', 'n', 'Q', ...KEYS[model]], inputs = { ...BASE, model }, errors = [];
  for (const k of Object.keys(RANGES)) { const e = $('error-' + k); if (e) e.hidden = true; $(k)?.removeAttribute('aria-invalid'); }
  for (const k of Object.keys(RANGES)) {
    const raw = $(k).value.trim(), v = Number(raw), [lo, hi] = RANGES[k];
    if (!keys.includes(k)) { if (Number.isFinite(v)) inputs[k] = v; continue; }
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

function friendly(message) {
  if (/outside the declared pressure/.test(message) || /200 kPa/.test(message)) return 'The equilibrium pressure would exceed 200 kPa, the ideal-gas scope of this lab. Reduce the gas inventory or the temperature, or enlarge the vessel.';
  return message;
}

function invalidateGraduate(msg) {
  study.fits = null; study.heat = null; study.swing = null;
  for (const id of ['fits-wrap', 'heat-wrap', 'swing-wrap']) $(id).hidden = true;
  for (const id of ['fits-status', 'heat-status', 'swing-status']) $(id).textContent = msg || '';
}

function calculate({ quiet = false } = {}) {
  const { inputs, errors } = readInputs(); showErrors(errors);
  if (errors.length) return false;
  let s;
  try { s = solve(inputs); } catch (error) { showErrors([{ id: 'n', msg: friendly(error.message) }]); return false; }
  if (JSON.stringify(inputs) !== JSON.stringify(study.inputs)) invalidateGraduate('Settings changed. Run this investigation again for the current vessel.');
  study.inputs = inputs; study.result = s;
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderChart();
  for (const id of ['save-case', 'run-fits', 'run-heat', 'run-swing', 'export-study']) $(id).disabled = false;
  $('graduate-baseline').textContent = 'Current vessel: ' + num(inputs.V) + ' L, ' + num(inputs.m) + ' g, ' + num(inputs.n) + ' mol at ' + num(inputs.T, 5) + ' K, ' + isoText(inputs) + ', Q = ' + num(inputs.Q) + ' kJ mol⁻¹ · P = ' + num(s.r.P, 4) + ' kPa.';
  if (!quiet) $('status').textContent = 'Calculated. Add the result to the comparison before changing a setting.';
  return true;
}

function renderResult() {
  const s = study.result, r = s.r, i = study.inputs, adsShare = 1 - r.gasFraction;
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-phase').textContent = 'P = ' + num(r.P, 4) + ' kPa';
  $('phase-interpretation').textContent = i.m === 0 ? 'Without adsorbent all the gas is in the free volume, so P = nRT/V.' : num(100 * adsShare, 3) + '% of the gas is held by the solid. The pressure is ' + num(r.P / s.Pempty * 100, 3) + '% of the value without adsorbent.';
  const p = $('prediction').value, band = adsShare < 0.5 ? 'low' : adsShare <= 0.9 ? 'mid' : 'high';
  $('prediction-feedback').textContent = p ? (p === band ? 'Your prediction matches the calculation.' : 'The solid holds ' + pct(adsShare) + ' of the gas here. Question A in Step 4 shows the balance.') : '';
  const rows = [['Free gas, PV/RT', r.gas, r.gasFraction], ['Adsorbed, m q', r.adsorbed, adsShare], ['Total', r.gas + r.adsorbed, 1]];
  $('share-body').replaceChildren(...rows.map(([a, b, f]) => { const tr = document.createElement('tr'), th = document.createElement('th'); th.scope = 'row'; th.textContent = a; tr.append(th, cell(num(b, 4)), cell(pct(f))); return tr; }));
  $('result-q').textContent = i.m === 0 ? 'No adsorbent' : num(r.q, 4) + ' mol kg⁻¹';
  $('result-theta').textContent = i.m === 0 ? '—' : s.coverage == null ? 'Not defined for a linear isotherm' : num(s.coverage, 3);
  $('result-empty').textContent = num(s.Pempty, 4) + ' kPa';
  $('result-param').textContent = i.model === 'henry' ? 'K = ' + num(s.params.K, 4) + ' mol kg⁻¹ kPa⁻¹' : 'b = ' + num(s.params.b, 4) + ' kPa⁻¹';
  $('result-res').textContent = Math.abs(r.balance).toExponential(2);
}

function renderPaper() {
  const s = study.result, r = s.r, i = study.inputs, list = $('calc-steps');
  list.replaceChildren();
  if (i.T !== 300) list.append(li('Temperature factor: exp[(Q/R)(1/T − 1/300)] = exp[(' + num(i.Q * 1000) + '/' + num(R, 5) + ')(1/' + num(i.T, 5) + ' − 1/300)] = ' + num(tFactor(i.T, i.Q * 1000), 4) + ', so ' + (i.model === 'henry' ? 'K = ' + num(s.params.K, 4) : 'b = ' + num(s.params.b, 4) + ' kPa⁻¹') + '.'));
  list.append(li('Free gas at P = ' + num(r.P, 5) + ' kPa: PV/RT = (' + num(r.P * 1000, 5) + ' Pa)(' + num(i.V / 1000) + ' m³)/(' + num(R, 5) + ' × ' + num(i.T, 5) + ') = ' + num(r.gas, 4) + ' mol.'));
  if (i.m > 0) list.append(li(i.model === 'henry' ? 'Uptake: q = KP = ' + num(s.params.K, 4) + ' × ' + num(r.P, 5) + ' = ' + num(r.q, 4) + ' mol kg⁻¹; adsorbed m q = ' + num(i.m / 1000) + ' × ' + num(r.q, 4) + ' = ' + num(r.adsorbed, 4) + ' mol.' : 'Uptake: bP = ' + num(s.params.b * r.P, 4) + ', q = q<sub>s</sub>bP/(1 + bP) = ' + num(r.q, 4) + ' mol kg⁻¹; adsorbed m q = ' + num(i.m / 1000) + ' × ' + num(r.q, 4) + ' = ' + num(r.adsorbed, 4) + ' mol.'));
  list.append(li('Balance: ' + num(r.gas, 4) + ' + ' + num(r.adsorbed, 4) + ' = ' + num(r.gas + r.adsorbed, 4) + ' mol = n. Without adsorbent, P = nRT/V = ' + num(s.Pempty, 4) + ' kPa.'));
}

async function renderChart() {
  if (!study.result) return;
  if (!window.Plotly) { setTimeout(renderChart, 200); return; }
  const s = study.result, r = s.r, i = study.inputs, Pmax = Math.min(200, Math.max(40, r.P * 2.2)), Ps = Array.from({ length: 121 }, (_, k) => Pmax * k / 120);
  const iso = T => Ps.map(P => ad.uptake(i.model, P, isothermParameters(i, T)));
  const traces = [{ x: Ps, y: iso(i.T), name: 'Isotherm at ' + num(i.T, 4) + ' K', mode: 'lines', line: { color: c.teal, width: 2.5 } }];
  if (i.T !== 300) traces.push({ x: Ps, y: iso(300), name: 'Isotherm at 300 K', mode: 'lines', line: { color: c.graphite, width: 1.5, dash: 'dot' } });
  if (i.m > 0) {
    const g = 1000 * (i.V / 1000) / (R * i.T), line = Ps.map(P => (i.n - P * g) / (i.m / 1000)).map(q => (q >= 0 ? q : null));
    traces.push({ x: Ps, y: line, name: 'Material balance', mode: 'lines', line: { color: c.amber, width: 2.5 } });
  }
  if (i.m > 0) traces.push({ x: [r.P], y: [r.q], name: 'Equilibrium', mode: 'markers', marker: { color: c.ink, size: 10 }, line: { color: c.ink } });
  const qtop = i.model === 'langmuir' ? Math.max(i.qs * 1.05, r.q * 1.3) : Math.max(r.q * 1.8, 0.5);
  const layout = { margin: { l: 70, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false, hovermode: 'closest',
    xaxis: { title: { text: 'Pressure P / kPa' }, range: [0, Pmax], zeroline: false, linecolor: c.graphite, gridcolor: c.mist }, yaxis: { title: { text: 'Uptake q / mol kg⁻¹' }, range: [0, qtop], zeroline: false, linecolor: c.graphite, gridcolor: c.mist } };
  try { await window.Plotly.react('ad-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* numbers are in Step 2 */ }
  $('chart-legend').replaceChildren(...traces.map(t => { const s2 = document.createElement('span'), e = document.createElement('i'); e.style.borderColor = t.line.color; if (t.mode === 'markers') e.className = 'legend-dot'; else e.style.borderTopStyle = t.line.dash === 'dot' ? 'dotted' : 'solid'; s2.append(e, document.createTextNode(t.name)); return s2; }));
  $('chart-note').textContent = i.m > 0 ? 'The material-balance line q = (n − PV/RT)/m falls with pressure because more gas stays in the free volume. Its crossing with the isotherm is the only state that satisfies both.' : 'Without adsorbent there is no balance line: all the gas is in the free volume.';
}

function runFits() {
  if (!study.result) return;
  const s = fitRangeStudy(study.inputs); study.fits = true;
  const par = (m, p) => m === 'henry' ? 'K = ' + num(p.K, 3) : m === 'langmuir' ? 'qs = ' + num(p.qs, 3) + ', b = ' + num(p.b, 3) : 'K = ' + num(p.K, 3) + ', m = ' + num(p.m, 3);
  $('fits-body').replaceChildren(...s.rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(r.range), cell(MODEL_NAMES[r.model]), cell(r.status === 'ok' ? par(r.model, r.parameters) : 'Failed: ' + r.reason), cell(num(r.RMSE, 3)), cell(r.vesselP == null ? (r.reason ? friendly(r.reason) : '—') : num(r.vesselP, 4)), cell(num(r.q60, 3))); return tr; }));
  $('fits-wrap').hidden = false;
  $('fits-status').textContent = 'The low-loading points reach ' + num(s.rows[0].Pmax, 3) + ' kPa and all points reach ' + num(s.rows[3].Pmax, 3) + ' kPa. The vessel uses the current volume, mass and inventory at 300 K; 60 kPa lies outside both data ranges.';
}

function runHeat() {
  if (!study.result) return;
  const rows = heatStudy(); study.heat = true;
  $('heat-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(r.label), cell(r.status === 'ok' ? num(r.min, 4) + '–' + num(r.max, 4) : 'Failed: ' + r.reason), cell(num(r.mean, 4)), cell(r.lnPRMSE == null ? '—' : r.lnPRMSE.toExponential(1)), cell(r.warning || '')); return tr; }));
  $('heat-wrap').hidden = false;
  $('heat-status').textContent = 'Synthetic isotherms generated with Q = 25 kJ mol⁻¹. Qst is evaluated at nine loadings inside the shared loading range; the misfit column is the RMSE of ln P about the line in 1/T.';
}

function runSwing() {
  if (!study.result) return;
  const sets = swingStudy(study.inputs); study.swing = true;
  const temps = sets[0].rows.map(r => r.T);
  $('swing-body').replaceChildren(...temps.map((T, k) => { const tr = document.createElement('tr'); tr.append(cell(num(T)), ...sets.map(s => cell(s.rows[k].status === 'ok' ? num(s.rows[k].P, 4) : 'Refused')), ...sets.map(s => cell(s.rows[k].status === 'ok' ? num(1000 * s.rows[k].released, 3) : '—'))); return tr; }));
  $('swing-wrap').hidden = false;
  const r25 = sets[1].rows.find(r => r.T === 380);
  $('swing-status').textContent = 'Start: the current vessel at 300 K. Released = adsorbed amount at 300 K minus adsorbed amount at T.' + (r25?.status === 'ok' ? ' At 380 K with Q = 25 kJ mol⁻¹, ' + pct(r25.gasFraction) + ' of the gas is in the free volume.' : '');
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([k, id]) => [k, $(id).value])); }
function summary(s) { return { P: s.r.P, q: s.r.adsorbed > 0 ? s.r.q : null, adsorbedShare: 1 - s.r.gasFraction }; }

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
    tr.append(cell(s.name), cell(num(s.inputs.T, 5)), cell(num(s.inputs.m)), cell(isoText(s.inputs)), cell(num(m.P, 4)), cell(num(m.q, 4)), cell(pct(m.adsorbedShare)));
    const td = document.createElement('td'), b = document.createElement('button');
    b.type = 'button'; b.className = 'secondary-button'; b.textContent = 'Reopen'; b.setAttribute('aria-label', 'Reopen ' + s.name);
    b.addEventListener('click', () => { applyInputs(s.inputs); $('case-name').value = s.name; calculate({ quiet: true }); $('status').textContent = 'Reopened and recalculated “' + s.name + '”.'; $('results').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    td.append(b); tr.append(td); return tr;
  }));
}

function loadCase(id) {
  const p = CASES[id]; if (!p) return;
  const note = $('case-source'); if (note) { note.textContent = p.source || ''; note.hidden = !p.source; }
  applyInputs(p.inputs); $('case-name').value = p.name;
  for (const b of document.querySelectorAll('[data-case]')) b.setAttribute('aria-pressed', String(b.dataset.case === id));
  $('status').textContent = p.name + ' loaded. Make a prediction, then press Calculate the equilibrium.';
}

function validInputs(i) {
  if (!i || !MODELS.includes(i.model)) return false;
  return ['T', 'V', 'm', 'n', 'Q', ...KEYS[i.model]].every(k => Number.isFinite(i[k]) && i[k] >= RANGES[k][0] && i[k] <= RANGES[k][1]);
}

function exportStudy() {
  const record = { schema: SCHEMA, engineVersion: ad.ADSORPTION_VERSION, graduateVersion: ADSORPTION_GRADUATE_VERSION, savedAt: new Date().toISOString(),
    inputs: study.inputs || readInputs().inputs, prediction: $('prediction').value, caseName: $('case-name').value, cases: study.cases,
    notes: notes(), reflection: $('reflection').value, investigations: { fits: Boolean(study.fits), heat: Boolean(study.heat), swing: Boolean(study.swing) } };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab11-adsorption-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded. Open it later to restore the cases, settings and notes.';
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2e6) throw new Error('The file is larger than a Lab 11 study.');
    const rec = JSON.parse(await file.text());
    if (rec.schema !== SCHEMA) throw new Error('This file is not a Lab 11 (2027) study.');
    if (!validInputs(rec.inputs)) throw new Error('The saved inputs are invalid.');
    applyInputs(rec.inputs); $('prediction').value = rec.prediction || ''; $('case-name').value = typeof rec.caseName === 'string' ? rec.caseName.slice(0, 80) : '';
    for (const [k, id] of Object.entries(NOTE_IDS)) $(id).value = typeof rec.notes?.[k] === 'string' ? rec.notes[k] : '';
    $('reflection').value = typeof rec.reflection === 'string' ? rec.reflection : '';
    const cases = [];
    for (const s of (Array.isArray(rec.cases) ? rec.cases : []).slice(0, 50)) {
      if (!validInputs(s?.inputs) || typeof s.name !== 'string') continue;
      try { cases.push({ name: s.name.slice(0, 80), inputs: { ...BASE, ...s.inputs }, summary: summary(solve({ ...BASE, ...s.inputs })) }); } catch { /* skip cases the engine now refuses */ }
    }
    study.cases = cases; study.inputs = null; renderCases(); calculate({ quiet: true });
    if (rec.investigations?.fits) runFits();
    if (rec.investigations?.heat) runHeat();
    if (rec.investigations?.swing) runSwing();
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases and the investigations were recalculated from the saved inputs.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

function init() {
  showControls();
  for (const b of document.querySelectorAll('[data-case]')) b.addEventListener('click', () => loadCase(b.dataset.case));
  $('model').addEventListener('change', showControls);
  $('calculate').addEventListener('click', () => calculate());
  $('ad-form').addEventListener('submit', e => { e.preventDefault(); calculate(); });
  $('save-case').addEventListener('click', saveCase);
  $('run-fits').addEventListener('click', runFits); $('run-heat').addEventListener('click', runHeat); $('run-swing').addEventListener('click', runSwing);
  $('check-evidence').addEventListener('click', () => { const r = evidenceCheck({ fits: study.fits, heat: study.heat, swing: study.swing, notes: notes() }); $('evidence-status').textContent = r.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : r.issues.join(' '); });
  $('export-study').addEventListener('click', exportStudy); $('import-study').addEventListener('change', openStudy);
  loadCase('baseline');
}

init();
