/** Lab 10 · 2027 preview page module. Calculations use the shared SLE engine. */
import * as so from '../../labs/assets/solids.js';
import { palette as c } from '../../labs/assets/palette.js';
import { SOLIDS_GRADUATE_VERSION, MODELS, MODEL_KEYS, engineInput, solve, saturationT, coolingPath, modelStudy, propertyStudy, evidenceCheck } from './solids-graduate.js';

const SCHEMA = 'skh-thermo-solids-study/1';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d }).replace(/^-/, '−');
const BASE = { T: 340, z: 0.5, model: 'ideal', Tm1: 350, Tm2: 400, h1: 12, h2: 15 };
const CASES = {
  baseline: { name: 'Starting case · 340 K', inputs: { ...BASE } },
  near: { name: 'Cooler · 320 K', inputs: { ...BASE, T: 320 } },
  below: { name: 'Below the eutectic · 300 K', inputs: { ...BASE, T: 300 } },
  'a-rich': { name: 'A-rich feed · x₁ = 0.90', inputs: { ...BASE, z: 0.9 } },
  real: { name: 'Real data · naphthalene + biphenyl, 316 K', inputs: { ...BASE, T: 316, Tm1: 353.4, h1: 19.0, Tm2: 342.1, h2: 18.58 },
    source: 'Real data: A = naphthalene (Tm 353.4 K, Δhfus 19.0 kJ/mol; Chirico et al. 2002) and B = biphenyl (Tm 342.1 K, Δhfus 18.58 kJ/mol; Chirico et al. 1989), both via the NIST Chemistry WebBook, with an ideal liquid. The ideal model gives a eutectic at 313.9 K, x₂ = 0.556. Gallus et al. (J. Chem. Educ. 2001, 78, 961) report measured eutectics near 313–315 K at x₂ ≈ 0.54–0.56, and cite 312.6 K (39.4 °C) at 0.555 from earlier work.' },
};
const RANGES = { T: [250, 450], z: [0, 1], Tm1: [260, 440], Tm2: [260, 440], h1: [1, 100], h2: [1, 100], A: [-1, 1.8], A12: [-1, 3], A21: [-1, 3], tau12: [-2, 6], tau21: [-2, 6], alpha: [0.1, 0.6] };
const LABELS = { T: 'Temperature', z: 'z₁', Tm1: 'Tm of A', Tm2: 'Tm of B', h1: 'Δhfus of A', h2: 'Δhfus of B', A: 'A', A12: 'A₁₂', A21: 'A₂₁', tau12: 'τ₁₂', tau21: 'τ₂₁', alpha: 'α' };
const NOTE_IDS = { concept1: 'note-concept1', concept2: 'note-concept2', concept3: 'note-concept3', cooling: 'note-cooling', models: 'note-models', properties: 'note-properties', decision: 'note-decision' };
const study = { inputs: null, result: null, cases: [], cooling: null, models: null, properties: null };

function cell(t) { const td = document.createElement('td'); td.textContent = t; return td; }
function li(h) { const e = document.createElement('li'); e.innerHTML = h; return e; }
/** Engine works in J/mol; the page shows kJ/mol. */
const toEngine = i => ({ ...i, h1: i.h1 * 1000, h2: i.h2 * 1000 });
function modelText(i) { return i.model === 'margules' ? 'Margules A = ' + num(i.A) : i.model === 'margules2' ? 'Margules A₁₂ = ' + num(i.A12) + ', A₂₁ = ' + num(i.A21) : i.model === 'nrtl' ? 'NRTL τ₁₂ = ' + num(i.tau12) + ', τ₂₁ = ' + num(i.tau21) + ', α = ' + num(i.alpha) : 'Ideal liquid'; }
const phaseName = t => t.replace('solid 1', 'solid A').replace('solid 2', 'solid B').replace('Solid 1', 'Solid A');
const solidAmount = r => (r.solid1 ?? 0) + (r.solid2 ?? 0);

function showControls() { const m = $('model').value; $('margules-control').hidden = m !== 'margules'; $('margules2-control').hidden = m !== 'margules2'; $('nrtl-control').hidden = m !== 'nrtl'; }
function applyInputs(i) { $('model').value = i.model; for (const k of Object.keys(RANGES)) if (i[k] !== undefined) $(k).value = String(i[k]); showControls(); }

function readInputs() {
  const model = $('model').value, keys = ['T', 'z', 'Tm1', 'Tm2', 'h1', 'h2', ...MODEL_KEYS[model]], inputs = { model }, errors = [];
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

function friendly(message) {
  if (/strictly convex liquid/.test(message)) return 'This liquid model splits into two liquids. This lab treats a single liquid with pure solids; use Lab 04 for liquid–liquid splitting.';
  return message;
}

function invalidateGraduate(msg) {
  study.cooling = null; study.models = null; study.properties = null;
  for (const id of ['cool-wrap', 'models-wrap', 'props-wrap']) $(id).hidden = true;
  for (const id of ['cool-status', 'models-status', 'props-status']) $(id).textContent = msg || '';
}

function calculate({ quiet = false } = {}) {
  const { inputs, errors } = readInputs(); showErrors(errors);
  if (errors.length) return false;
  let r;
  try { r = solve(toEngine(inputs)); } catch (error) { showErrors([{ id: inputs.model === 'ideal' ? 'T' : 'model', msg: friendly(error.message) }]); return false; }
  if (JSON.stringify(inputs) !== JSON.stringify(study.inputs)) invalidateGraduate('Settings changed. Run this investigation again for the current feed.');
  study.inputs = inputs; study.result = r;
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderChart();
  for (const id of ['save-case', 'run-cool', 'run-models', 'run-props', 'export-study']) $(id).disabled = false;
  $('graduate-baseline').textContent = 'Current state: z₁ = ' + num(inputs.z) + ' at ' + num(inputs.T, 5) + ' K, ' + modelText(inputs) + ' · ' + phaseName(r.r.type) + (r.eutectic ? ', eutectic ' + num(r.eutectic.T, 5) + ' K.' : '.');
  if (!quiet) $('status').textContent = 'Calculated. Add the result to the comparison before changing a setting.';
  return true;
}

function interpretation(q, sol) {
  if (/undetermined/.test(q.type)) return 'The temperature lies exactly on a three-phase or pure-melting state. The compositions are fixed, but the amounts are not: they depend on how much heat has been removed.';
  if (q.type === 'Liquid') return 'The feed is above its first-crystal temperature' + (sol.liquidus ? ' (' + num(sol.liquidus.T, 5) + ' K)' : '') + ', so it stays entirely liquid.';
  if (/Solid 1 \+ solid 2/.test(q.type)) return 'The temperature is below the eutectic. No liquid can exist, so the feed is a mixture of the two pure solids in feed proportion.';
  const i = q.type.endsWith('2') ? 'B' : 'A', o = i === 'B' ? 'A' : 'B';
  return 'Pure solid ' + i + ' crystallizes. The remaining liquid is saturated with ' + i + ' and enriched in ' + o + '. Its composition is fixed by the temperature alone.';
}

function renderResult() {
  const sol = study.result, q = sol.r, i = study.inputs;
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-phase').textContent = phaseName(q.type);
  $('phase-interpretation').textContent = interpretation(q, sol);
  const p = $('prediction').value, first = sol.liquidus ? String(sol.liquidus.solid) : null;
  $('prediction-feedback').textContent = p && first ? (p === first ? 'Your prediction matches the calculation.' : 'Solid ' + (first === '2' ? 'B' : 'A') + ' appears first for this feed, at ' + num(sol.liquidus.T, 5) + ' K. Question B in Step 4 explains why.') : '';
  const undetermined = q.liquid === null;
  const rows = [['Liquid', undetermined ? 'Undetermined' : num(q.liquid, 4), q.x == null ? '—' : num(q.x, 4)], ['Solid A', undetermined ? 'Undetermined' : num(q.solid1, 4), '1'], ['Solid B', undetermined ? 'Undetermined' : num(q.solid2, 4), '0']];
  $('phase-body').replaceChildren(...rows.map(([a, b, x]) => { const tr = document.createElement('tr'), th = document.createElement('th'); th.scope = 'row'; th.textContent = a; tr.append(th, cell(b), cell(x)); return tr; }));
  $('result-liquidus').textContent = sol.liquidus ? num(sol.liquidus.T, 5) + ' K · solid ' + (sol.liquidus.solid === 2 ? 'B' : 'A') : '—';
  $('result-eutectic').textContent = sol.eutectic ? num(sol.eutectic.T, 5) + ' K at x₁ = ' + num(sol.eutectic.x, 4) : 'Outside 250–450 K';
  $('result-gs').textContent = num(q.gs[0], 4) + ', ' + num(q.gs[1], 4);
  $('result-res').textContent = q.balanceResidual == null ? '—' : q.balanceResidual.toExponential(2);
}

function renderPaper() {
  const sol = study.result, q = sol.r, i = study.inputs, R = so.R, list = $('calc-steps');
  list.replaceChildren(li('Pure-solid terms at ' + num(i.T, 5) + ' K: ln a₁ˢ = −(' + num(i.h1 * 1000) + '/' + num(R, 5) + ')(1/' + num(i.T, 5) + ' − 1/' + num(i.Tm1, 5) + ') = ' + num(q.gs[0], 4) + ' and ln a₂ˢ = ' + num(q.gs[1], 4) + '.'));
  if (/Liquid \+ solid/.test(q.type)) {
    const B = q.type.endsWith('2');
    list.append(
      li('Solid ' + (B ? 'B' : 'A') + ' saturates the liquid: ln(x<sub>' + (B ? '2' : '1') + '</sub>γ<sub>' + (B ? '2' : '1') + '</sub>) = ' + num(B ? q.gs[1] : q.gs[0], 4) + (i.model === 'ideal' ? ', so with γ = 1, ' + (B ? 'x₂ = ' + num(Math.exp(q.gs[1]), 4) + ' and x₁ = ' + num(q.x, 4) : 'x₁ = ' + num(q.x, 4)) + '.' : '; solving with the liquid model gives x₁ = ' + num(q.x, 4) + '.')),
      li(B ? 'All of A stays in the liquid: L = z₁/x₁ = ' + num(i.z) + '/' + num(q.x, 4) + ' = ' + num(q.liquid, 4) + ' mol, so solid B = ' + num(q.solid2, 4) + ' mol.' : 'All of B stays in the liquid: L = (1 − z₁)/(1 − x₁) = ' + num(1 - i.z) + '/' + num(1 - q.x, 4) + ' = ' + num(q.liquid, 4) + ' mol, so solid A = ' + num(q.solid1, 4) + ' mol.'),
    );
  } else if (q.type === 'Liquid') list.append(li('For this feed, x₁γ₁ and x₂γ₂ both exceed the solid limits above, so neither solid can form.'));
  else if (/Solid 1 \+ solid 2/.test(q.type)) list.append(li('Below the eutectic no liquid satisfies both solubility limits, so the feed is ' + num(i.z) + ' mol solid A and ' + num(1 - i.z) + ' mol solid B.'));
  if (sol.liquidus) list.append(li('First crystals: solve ln(x<sub>i</sub>γ<sub>i</sub>) at x₁ = z₁ for T. Solid B gives ' + num(saturationT(toEngine(i), i.z, 1), 5) + ' K and solid A gives ' + num(saturationT(toEngine(i), i.z, 0), 5) + ' K; the higher one forms first.'));
}

async function renderChart() {
  if (!study.result) return;
  if (!window.Plotly) { setTimeout(renderChart, 200); return; }
  const sol = study.result, q = sol.r, i = study.inputs, curves = so.sleCurves(engineInput(toEngine(i)));
  const traces = [
    { x: curves.branches[1].map(p => p.x), y: curves.branches[1].map(p => p.T), name: 'Saturated with solid B', mode: 'lines', connectgaps: false, line: { color: c.teal, width: 2.5 } },
    { x: curves.branches[0].map(p => p.x), y: curves.branches[0].map(p => p.T), name: 'Saturated with solid A', mode: 'lines', connectgaps: false, line: { color: c.skyblue, width: 2.5 } },
  ];
  if (sol.eutectic) traces.push({ x: [0, 1], y: [sol.eutectic.T, sol.eutectic.T], name: 'Eutectic', mode: 'lines', line: { color: c.amber, width: 2, dash: 'dash' } });
  traces.push({ x: [i.z, i.z], y: [250, 450], name: 'Feed', mode: 'lines', line: { color: c.graphite, width: 1.5, dash: 'dot' } });
  if (/Liquid \+ solid/.test(q.type)) traces.push({ x: [q.type.endsWith('2') ? 0 : 1, q.x], y: [i.T, i.T], name: 'Tie line', mode: 'lines+markers', marker: { color: c.amber, size: 8 }, line: { color: c.amber, width: 2 } });
  traces.push({ x: [i.z], y: [i.T], name: 'Current state', mode: 'markers', marker: { color: c.ink, size: 10 }, line: { color: c.ink } });
  const Ts = [i.Tm1, i.Tm2, i.T, sol.eutectic?.T].filter(Number.isFinite), lo = Math.max(250, Math.min(...Ts) - 25), hi = Math.min(450, Math.max(...Ts) + 15);
  const layout = { margin: { l: 70, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false, hovermode: 'closest',
    xaxis: { title: { text: 'Mole fraction of A, x₁' }, range: [0, 1], zeroline: false, linecolor: c.graphite, gridcolor: c.mist }, yaxis: { title: { text: 'Temperature / K' }, range: [lo, hi], zeroline: false, linecolor: c.graphite, gridcolor: c.mist } };
  try { await window.Plotly.react('so-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* numbers are in Step 2 */ }
  $('chart-legend').replaceChildren(...traces.map(t => { const s = document.createElement('span'), e = document.createElement('i'); e.style.borderColor = t.line.color; if (t.mode === 'markers') e.className = 'legend-dot'; else e.style.borderTopStyle = t.line.dash === 'dash' ? 'dashed' : t.line.dash === 'dot' ? 'dotted' : 'solid'; s.append(e, document.createTextNode(t.name)); return s; }));
  $('chart-note').textContent = 'Above both curves the mixture is liquid. Between a curve and the eutectic line, liquid coexists with one pure solid; the tie line joins the pure solid to the saturated liquid. Below the eutectic, both solids coexist.';
}

function runCooling() {
  if (!study.result) return;
  const s = coolingPath(toEngine(study.inputs)); study.cooling = true;
  $('cool-body').replaceChildren(...s.rows.map(r => { const tr = document.createElement('tr'), u = r.status === 'ok' && r.liquid === null; tr.append(cell(num(r.T, 5)), cell(r.status === 'ok' ? phaseName(r.type) : 'Failed: ' + friendly(r.reason)), cell(num(r.x, 4)), cell(u ? '—' : num(r.liquid, 4)), cell(u ? '—' : num(r.solid1, 4)), cell(u ? '—' : num(r.solid2, 4))); return tr; }));
  $('cool-wrap').hidden = false;
  $('cool-status').textContent = 'First crystals at ' + (s.liquidus ? num(s.liquidus.T, 5) + ' K (solid ' + (s.liquidus.solid === 2 ? 'B' : 'A') + ')' : '—') + '. Eutectic at ' + (s.eutectic ? num(s.eutectic.T, 5) + ' K, x₁ = ' + num(s.eutectic.x, 4) : '—') + '. Rows 0.5 K above and below the eutectic bracket the disappearance of the liquid.';
}

function runModels() {
  if (!study.result) return;
  const rows = modelStudy(toEngine(study.inputs)); study.models = true;
  $('models-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(r.A)), cell(r.status === 'ok' ? num(r.eutecticT, 5) : 'Failed: ' + friendly(r.reason)), cell(num(r.eutecticX, 4)), cell(num(r.liquidusT, 5)), cell(r.type ? phaseName(r.type) : '—'), cell(num(r.solid, 4))); return tr; }));
  $('models-wrap').hidden = false;
  $('models-status').textContent = 'Same pure-solid data, feed z₁ = ' + num(study.inputs.z) + ' at ' + num(study.inputs.T, 5) + ' K. Only the one-parameter Margules liquid changes.';
}

function runProperties() {
  if (!study.result) return;
  const rows = propertyStudy(toEngine(study.inputs)); study.properties = true;
  $('props-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(r.label), cell(r.status === 'ok' ? num(r.eutecticT, 5) : 'Failed: ' + friendly(r.reason)), cell(num(r.eutecticX, 4)), cell(num(r.liquidusT, 5)), cell(num(r.x, 4)), cell(num(r.solid, 4))); return tr; }));
  $('props-wrap').hidden = false;
  $('props-status').textContent = 'One property changed at a time, with the current liquid model. These are deterministic sensitivities, not confidence intervals.';
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([k, id]) => [k, $(id).value])); }
function summary(sol) { const r = sol.r; return { type: r.type, x: r.x, solid: r.liquid === null ? null : solidAmount(r) }; }

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
    tr.append(cell(s.name), cell(num(s.inputs.T, 5)), cell(num(s.inputs.z)), cell(modelText(s.inputs)), cell(phaseName(m.type)), cell(num(m.x, 4)), cell(m.solid === null ? 'Undetermined' : num(m.solid, 4)));
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
  return ['T', 'z', 'Tm1', 'Tm2', 'h1', 'h2', ...MODEL_KEYS[i.model]].every(k => Number.isFinite(i[k]) && i[k] >= RANGES[k][0] && i[k] <= RANGES[k][1]);
}

function exportStudy() {
  const record = { schema: SCHEMA, engineVersion: so.SOLIDS_VERSION, graduateVersion: SOLIDS_GRADUATE_VERSION, savedAt: new Date().toISOString(),
    inputs: study.inputs || readInputs().inputs, prediction: $('prediction').value, caseName: $('case-name').value, cases: study.cases,
    notes: notes(), reflection: $('reflection').value, investigations: { cooling: Boolean(study.cooling), models: Boolean(study.models), properties: Boolean(study.properties) } };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab10-sle-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded. Open it later to restore the cases, settings and notes.';
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2e6) throw new Error('The file is larger than a Lab 10 study.');
    const rec = JSON.parse(await file.text());
    if (rec.schema !== SCHEMA) throw new Error('This file is not a Lab 10 (2027) study.');
    if (!validInputs(rec.inputs)) throw new Error('The saved inputs are invalid.');
    applyInputs(rec.inputs); $('prediction').value = rec.prediction || ''; $('case-name').value = typeof rec.caseName === 'string' ? rec.caseName.slice(0, 80) : '';
    for (const [k, id] of Object.entries(NOTE_IDS)) $(id).value = typeof rec.notes?.[k] === 'string' ? rec.notes[k] : '';
    $('reflection').value = typeof rec.reflection === 'string' ? rec.reflection : '';
    const cases = [];
    for (const s of (Array.isArray(rec.cases) ? rec.cases : []).slice(0, 50)) {
      if (!validInputs(s?.inputs) || typeof s.name !== 'string') continue;
      try { cases.push({ name: s.name.slice(0, 80), inputs: s.inputs, summary: summary(solve(toEngine(s.inputs))) }); } catch { /* skip cases the engine now refuses */ }
    }
    study.cases = cases; study.inputs = null; renderCases(); calculate({ quiet: true });
    if (rec.investigations?.cooling) runCooling();
    if (rec.investigations?.models) runModels();
    if (rec.investigations?.properties) runProperties();
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases and the investigations were recalculated from the saved inputs.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

function init() {
  showControls();
  for (const b of document.querySelectorAll('[data-case]')) b.addEventListener('click', () => loadCase(b.dataset.case));
  $('model').addEventListener('change', showControls);
  $('calculate').addEventListener('click', () => calculate());
  $('so-form').addEventListener('submit', e => { e.preventDefault(); calculate(); });
  $('save-case').addEventListener('click', saveCase);
  $('run-cool').addEventListener('click', runCooling); $('run-models').addEventListener('click', runModels); $('run-props').addEventListener('click', runProperties);
  $('check-evidence').addEventListener('click', () => { const r = evidenceCheck({ cooling: study.cooling, models: study.models, properties: study.properties, notes: notes() }); $('evidence-status').textContent = r.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : r.issues.join(' '); });
  $('export-study').addEventListener('click', exportStudy); $('import-study').addEventListener('change', openStudy);
  loadCase('baseline');
}

init();
