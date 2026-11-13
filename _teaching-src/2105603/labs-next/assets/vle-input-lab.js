/** Lab 08 · 2027 preview page module. Data stay in the browser. */
import * as vi from '../../labs/assets/vle-input.js';
import { predict } from '../../labs/assets/vle-input.js';
import { palette as c } from '../../labs/assets/palette.js';
import { VLE_INPUT_GRADUATE_VERSION, MODELS, firstRow, pureLimits, errorSignatures, modelComparison, endpointStudy, evidenceCheck } from './vle-input-graduate.js';

const SCHEMA = 'skh-thermo-vle-input-study/1';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d });
const NOTE_IDS = { concept1: 'note-concept1', concept2: 'note-concept2', concept3: 'note-concept3', signatures: 'note-signatures', models: 'note-models', endpoints: 'note-endpoints', decision: 'note-decision' };
const LIMIT_TOL = 0.1;
const study = { set: null, options: null, text: '', fit: null, cases: [], signatures: null, models: null, endpoints: null };

function cell(t) { const td = document.createElement('td'); td.textContent = t; return td; }
function li(h) { const e = document.createElement('li'); e.innerHTML = h; return e; }

function buildAntoine() {
  const forms = Object.entries(vi.ANTOINE_FORMS).map(([k, f]) => '<option value="' + k + '">' + f.label + '</option>').join('');
  $('antoine-grid').innerHTML = [1, 2].map(i => '<div><h3>Component ' + i + '</h3>'
    + '<label for="a' + i + '-form">Equation form</label><select id="a' + i + '-form">' + forms + '</select>'
    + '<div class="abc">' + ['A', 'B', 'C'].map(k => '<div><label for="a' + i + '-' + k + '">' + k + '</label><input id="a' + i + '-' + k + '" type="number" step="any"></div>').join('') + '</div>'
    + '<div class="range"><div><label for="a' + i + '-tmin">Min T / K</label><input id="a' + i + '-tmin" type="number" step="any"></div><div><label for="a' + i + '-tmax">Max T / K</label><input id="a' + i + '-tmax" type="number" step="any"></div></div>'
    + '<div class="range"><div><label for="a' + i + '-tu">T unit in equation</label><select id="a' + i + '-tu"><option value="K">K</option><option value="C">°C</option></select></div><div><label for="a' + i + '-pu">Psat unit</label><select id="a' + i + '-pu"><option value="kPa">kPa</option><option value="bar">bar</option><option value="Pa">Pa</option><option value="mmHg">mmHg</option></select></div></div></div>').join('');
}

function writeAntoine(list) {
  list.forEach((a, k) => { const i = k + 1; $('a' + i + '-form').value = a.form; $('a' + i + '-A').value = String(a.A); $('a' + i + '-B').value = String(a.B); $('a' + i + '-C').value = String(a.C); $('a' + i + '-tmin').value = String(a.TminK); $('a' + i + '-tmax').value = String(a.TmaxK); $('a' + i + '-tu').value = a.temperatureUnit; $('a' + i + '-pu').value = a.pressureUnit; });
}
function readAntoine() {
  return [1, 2].map(i => ({ form: $('a' + i + '-form').value, A: Number($('a' + i + '-A').value), B: Number($('a' + i + '-B').value), C: Number($('a' + i + '-C').value), TminK: Number($('a' + i + '-tmin').value), TmaxK: Number($('a' + i + '-tmax').value), temperatureUnit: $('a' + i + '-tu').value, pressureUnit: $('a' + i + '-pu').value }));
}

function readOptions() {
  return { temperatureUnit: $('Tunit').value, pressureUnit: $('Punit').value, path: $('path').value, names: [$('name1').value.trim() || 'Component 1', $('name2').value.trim() || 'Component 2'], source: $('source').value.trim() || 'User-supplied measurements', antoine: readAntoine() };
}

function updateFirstRow() {
  const box = $('first-row'), text = $('data').value;
  const item = (t, v) => '<div><dt>' + t + '</dt><dd>' + v + '</dd></div>';
  if (!text.trim()) { box.innerHTML = item('Waiting for a table', '—'); return; }
  try {
    const f = firstRow(text, readOptions()), r = f.raw;
    box.innerHTML = item('Table values', 'T = ' + r.t + ', P = ' + r.p + ', x₁ = ' + r.x1 + ', y₁ = ' + r.y1)
      + item('Read as', num(f.T, 6) + ' K and ' + num(f.P, 6) + ' kPa')
      + item('P₁<sup>sat</sup>, P₂<sup>sat</sup> at this T', num(f.s[0], 5) + ' and ' + num(f.s[1], 5) + ' kPa')
      + item('γ₁, γ₂', f.gamma ? num(f.gamma[0], 4) + ' and ' + num(f.gamma[1], 4) : 'pure endpoint');
  } catch (error) { box.innerHTML = item('Cannot read the first row yet', error.message); }
}

function invalidateGraduate(msg) {
  study.signatures = null; study.models = null; study.endpoints = null;
  for (const id of ['sig-wrap', 'models-wrap', 'end-wrap']) $(id).hidden = true;
  for (const id of ['sig-status', 'models-status', 'end-status']) $(id).textContent = msg || '';
}

function showError(message) {
  const box = $('form-error');
  if (!message) { box.hidden = true; box.textContent = ''; return; }
  box.textContent = message; box.hidden = false; box.focus();
}

function validate({ quiet = false } = {}) {
  const options = readOptions(), text = $('data').value;
  let set;
  try { set = vi.importVLE(text, options); } catch (error) { showError(error.message); return false; }
  showError('');
  const changed = text !== study.text || JSON.stringify(options) !== JSON.stringify(study.options);
  study.set = set; study.options = options; study.text = text;
  if (changed) { invalidateGraduate('The data or settings changed. Run this investigation again.'); study.fit = null; $('fit-metrics').hidden = true; $('fit-status').textContent = ''; }
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderChart();
  for (const id of ['save-case', 'run-sig', 'run-models', 'run-end', 'export-study']) $(id).disabled = false;
  $('graduate-baseline').textContent = 'Current table: ' + set.name + ', ' + set.valid.length + ' interior rows, T in ' + (options.temperatureUnit === 'C' ? '°C' : 'K') + ', P in ' + options.pressureUnit + '.';
  if (!quiet) $('status').textContent = 'Validated. Add the result to the comparison before changing a setting.';
  return true;
}

function renderResult() {
  const set = study.set, lim = pureLimits(set), bad = Math.abs(lim.lnGamma1AtHighX.value) > LIMIT_TOL || Math.abs(lim.lnGamma2AtLowX.value) > LIMIT_TOL;
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-phase').textContent = bad ? 'Check the units and vapor pressures' : 'Pure-liquid limits look reasonable';
  $('result-phase').classList.toggle('verdict-fail', bad);
  $('phase-interpretation').textContent = bad
    ? 'At least one ln γ is far from 0 where its component is nearly pure. With a pure-liquid standard state, γᵢ → 1 as xᵢ → 1. A constant offset in both ln γ usually means a pressure-unit or vapor-pressure error.'
    : 'Each ln γ is close to 0 where its component is nearly pure, as the pure-liquid standard state requires. This is a necessary check, not proof that the data are accurate.';
  const p = $('prediction').value;
  $('prediction-feedback').textContent = p === 'zero' ? 'Correct: with a pure-liquid standard state, γ₁ → 1 and ln γ₁ → 0 as x₁ → 1.' : p === 'inf' ? 'The infinite-dilution limit applies as x₁ → 0. As x₁ → 1, γ₁ → 1 and ln γ₁ → 0.' : '';
  const f = v => '<span class="' + (Math.abs(v.value) > LIMIT_TOL ? 'limit-bad' : '') + '">' + num(v.value, 4) + '</span> at x₁ = ' + num(v.x, 4);
  $('limit2').innerHTML = f(lim.lnGamma2AtLowX); $('limit1').innerHTML = f(lim.lnGamma1AtHighX);
  $('counts').textContent = set.valid.length + ' / ' + set.excluded.length;
  $('rows-body').replaceChildren(...set.rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(r.x, 5)), cell(num(r.y, 5)), cell(num(r.T, 6)), cell(num(r.PkPa, 6)), cell(num(r.s[0], 5)), cell(num(r.s[1], 5)), cell(r.ln ? num(Math.exp(r.ln[0]), 5) : 'endpoint'), cell(r.ln ? num(Math.exp(r.ln[1]), 5) : 'endpoint')); return tr; }));
}

function renderPaper() {
  const r = study.set.valid[0], u = study.options;
  $('calc-steps').replaceChildren(
    li('Read the row in SI-consistent units: T = ' + num(r.T, 6) + ' K, P = ' + num(r.PkPa, 6) + ' kPa (declared P unit: ' + u.pressureUnit + ').'),
    li('Vapor pressures from your Antoine constants at this T: P₁<sup>sat</sup> = ' + num(r.s[0], 5) + ' kPa, P₂<sup>sat</sup> = ' + num(r.s[1], 5) + ' kPa.'),
    li('γ₁ = y₁P/(x₁P₁<sup>sat</sup>) = ' + num(r.y, 5) + ' × ' + num(r.PkPa, 5) + '/(' + num(r.x, 5) + ' × ' + num(r.s[0], 5) + ') = ' + num(Math.exp(r.ln[0]), 5) + '.'),
    li('γ₂ = y₂P/(x₂P₂<sup>sat</sup>) = ' + num(1 - r.y, 5) + ' × ' + num(r.PkPa, 5) + '/(' + num(1 - r.x, 5) + ' × ' + num(r.s[1], 5) + ') = ' + num(Math.exp(r.ln[1]), 5) + '.'),
  );
}

function fit() {
  if (!study.set) return;
  try {
    const f = vi.fitVLE(study.set, { model: $('fit-model').value, alpha: 0.3 }); study.fit = f;
    $('fit-metrics').hidden = false; $('fit-dp').textContent = num(f.deltaP, 4) + ' %'; $('fit-dy').textContent = num(f.deltaY, 4);
    $('fit-status').textContent = MODELS[f.model] + ': ' + f.parameterNames.map((n, k) => n + ' = ' + num(f.parameters[k], 5)).join(', ') + (f.atBound ? ' · a parameter is at its search bound.' : '.') + ' A good fit shows the model can represent this table; it does not test the data.';
    renderChart();
  } catch (error) { $('fit-status').textContent = 'No fit reported: ' + error.message; }
}

const trace = (x, y, name, color, dash = 'solid', mode = 'lines', symbol = 'circle') => ({ x, y, name, mode, line: { color, width: 2, dash }, marker: { color, size: 8, symbol }, hovertemplate: name + '<br>%{x:.4f}, %{y:.4f}<extra></extra>' });

async function renderChart() {
  if (!study.set) return;
  if (!window.Plotly) { setTimeout(renderChart, 200); return; }
  const v = study.set.valid, f = study.fit, view = $('view').value;
  let traces, x = 'Liquid mole fraction · x₁', y, note;
  if (view === 'pxy') {
    traces = [trace(v.map(r => r.x), v.map(r => r.PkPa), 'Measured P against x₁', c.teal, 'solid', 'markers'), trace(v.map(r => r.y), v.map(r => r.PkPa), 'Measured P against y₁', c.teal, 'solid', 'markers', 'diamond')];
    if (f) {
      const T = v[0].T, s = v[0].s, xs = Array.from({ length: 101 }, (_, k) => k / 100), m = xs.map(xx => predict({ x: xx, T, s }, f.model, f.parameters, f.alpha ?? 0.3));
      if (study.set.path === 'isothermal') traces.push(trace(xs, m.map(q => q.P), 'Fitted bubble curve', c.amber), trace(m.map(q => q.y), m.map(q => q.P), 'Fitted dew curve', c.amber, 'dash'));
      else traces.push(trace(f.points.map(p => p.x), f.points.map(p => p.Pcalc), 'Fitted P at each row', c.amber, 'solid', 'markers', 'x'));
    }
    x = 'Mole fraction of component 1 · x₁ or y₁'; y = 'Pressure / kPa';
    note = 'Circles: measured liquid compositions. Diamonds: measured vapor compositions. Amber: the fitted model.';
  } else {
    traces = [trace(v.map(r => r.x), v.map(r => r.ln[0]), 'ln γ₁ from data', c.teal, 'solid', 'markers'), trace(v.map(r => r.x), v.map(r => r.ln[1]), 'ln γ₂ from data', c.skyblue, 'solid', 'markers', 'diamond')];
    if (f && study.set.path === 'isothermal') {
      const T = v[0].T, s = v[0].s, xs = Array.from({ length: 99 }, (_, k) => (k + 1) / 100), m = xs.map(xx => predict({ x: xx, T, s }, f.model, f.parameters, f.alpha ?? 0.3).gamma.map(Math.log));
      traces.push(trace(xs, m.map(q => q[0]), 'ln γ₁ fitted', c.amber), trace(xs, m.map(q => q[1]), 'ln γ₂ fitted', c.amber, 'dash'));
    }
    y = 'ln γ';
    note = 'With a pure-liquid standard state, ln γ₁ must reach 0 at x₁ = 1 and ln γ₂ must reach 0 at x₁ = 0. Curves that end far from zero point to a unit or vapor-pressure error.';
  }
  const layout = { margin: { l: 70, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false, hovermode: 'closest',
    xaxis: { title: { text: x }, range: [0, 1], zeroline: false, linecolor: c.graphite, gridcolor: c.mist }, yaxis: { title: { text: y }, zeroline: view !== 'pxy', zerolinecolor: c.graphite, linecolor: c.graphite, gridcolor: c.mist } };
  try { await window.Plotly.react('vi-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* table holds values */ }
  $('chart-legend').replaceChildren(...traces.map(t => { const s = document.createElement('span'), i = document.createElement('i'); i.style.borderColor = t.line.color; if (t.mode === 'markers') i.className = 'legend-dot'; else i.style.borderTopStyle = t.line.dash === 'dash' ? 'dashed' : 'solid'; s.append(i, document.createTextNode(t.name)); return s; }));
  $('chart-note').textContent = note;
}

function runSig() {
  if (!study.set) return;
  const rows = errorSignatures(study.text, study.options); study.signatures = true;
  $('sig-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(r.label), cell(r.status === 'imported' ? 'Imported' : 'Rejected: ' + r.reason), cell(r.lnG2Low ? num(r.lnG2Low.value, 4) : '—'), cell(r.lnG1High ? num(r.lnG1High.value, 4) : '—'), cell(num(r.D, 4)), cell(r.fit ? (r.fit.error ? 'No fit: ' + r.fit.error : num(r.fit.deltaP, 4) + ' %') : '—')); if (r.label !== 'As declared') tr.className = 'highlight-row'; return tr; }));
  $('sig-wrap').hidden = false;
  $('sig-status').textContent = 'The same table was re-imported five times. Only the declared units changed.';
}

function runModels() {
  if (!study.set) return;
  const rows = modelComparison(study.set); study.models = true;
  $('models-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(r.label), cell(r.status === 'ok' ? r.names.map((n, k) => n + ' = ' + num(r.parameters[k], 5)).join(', ') : 'Failed: ' + r.reason), cell(num(r.deltaP, 4)), cell(num(r.deltaY, 4)), cell(r.atBound ? 'Yes' : 'No')); return tr; }));
  $('models-wrap').hidden = false;
  $('models-status').textContent = 'All three models use the same ' + study.set.valid.length + ' observations and the same vapor pressures.';
}

function runEnd() {
  if (!study.set) return;
  const rows = endpointStudy(study.set); study.endpoints = true;
  const label = { none: 'No extension · measured interval only', linear: 'Linear extension to x₁ = 0 and 1', quadratic: 'Quadratic fit of ln(γ₁/γ₂)' };
  $('end-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(label[r.ext]), cell(r.status === 'ok' ? num(r.xmin, 3) + ' to ' + num(r.xmax, 3) : 'Failed: ' + r.reason), cell(num(r.I, 4)), cell(num(r.D, 4))); return tr; }));
  $('end-wrap').hidden = false;
  $('end-status').textContent = 'The extended results are conditional on the extrapolation; no observation was added.';
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([k, id]) => [k, $(id).value])); }

function saveCase() {
  if (!study.set) return;
  const name = $('case-name').value.trim() || 'Case ' + (study.cases.length + 1), lim = pureLimits(study.set);
  study.cases.push({ name, text: study.text, options: study.options, summary: { names: study.set.name, valid: study.set.valid.length, lim } });
  renderCases(); $('status').textContent = 'Saved “' + name + '”. Change one setting, validate, then save the next case.';
}

function renderCases() {
  $('comparison-empty').hidden = study.cases.length > 0; $('comparison-table-wrap').hidden = !study.cases.length;
  $('comparison-body').replaceChildren(...study.cases.map(s => {
    const tr = document.createElement('tr'), m = s.summary;
    tr.append(cell(s.name), cell(m.names), cell((s.options.temperatureUnit === 'C' ? '°C' : 'K') + ', ' + s.options.pressureUnit), cell(String(m.valid)), cell(num(m.lim.lnGamma2AtLowX.value, 4)), cell(num(m.lim.lnGamma1AtHighX.value, 4)));
    const td = document.createElement('td'), b = document.createElement('button');
    b.type = 'button'; b.className = 'secondary-button'; b.textContent = 'Reopen'; b.setAttribute('aria-label', 'Reopen ' + s.name);
    b.addEventListener('click', () => { applyOptions(s.options, s.text); $('case-name').value = s.name; validate({ quiet: true }); $('status').textContent = 'Reopened and revalidated “' + s.name + '”.'; $('results').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    td.append(b); tr.append(td); return tr;
  }));
}

function applyOptions(o, text) {
  $('Tunit').value = o.temperatureUnit; $('Punit').value = o.pressureUnit; $('path').value = o.path; $('name1').value = o.names[0]; $('name2').value = o.names[1]; $('source').value = o.source;
  writeAntoine(o.antoine); $('data').value = text; updateFirstRow();
}

function loadExample() {
  applyOptions({ temperatureUnit: 'K', pressureUnit: 'kPa', path: 'isothermal', names: ['Component A', 'Component B'], source: 'Synthetic teaching example · not a measurement', antoine: vi.exampleAntoine() }, vi.exampleAntoineCSV());
  $('case-name').value = 'Synthetic example · 350 K';
  $('status').textContent = 'Synthetic example loaded. Read the first-row preview, then press Validate.';
}

function exportStudy() {
  const record = { schema: SCHEMA, engineVersion: vi.INPUT_VERSION, graduateVersion: VLE_INPUT_GRADUATE_VERSION, savedAt: new Date().toISOString(), options: readOptions(), text: $('data').value,
    fitModel: $('fit-model').value, fitted: Boolean(study.fit), prediction: $('prediction').value, caseName: $('case-name').value, cases: study.cases, notes: notes(), reflection: $('reflection').value,
    investigations: { signatures: Boolean(study.signatures), models: Boolean(study.models), endpoints: Boolean(study.endpoints) } };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab08-vle-data-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded, including your data table.';
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 5e6) throw new Error('The file is larger than a Lab 08 study.');
    const rec = JSON.parse(await file.text());
    if (rec.schema !== SCHEMA || typeof rec.text !== 'string' || !rec.options) throw new Error('This file is not a Lab 08 (2027) study.');
    applyOptions(rec.options, rec.text);
    $('fit-model').value = rec.fitModel || 'nrtl'; $('prediction').value = rec.prediction || ''; $('case-name').value = typeof rec.caseName === 'string' ? rec.caseName.slice(0, 80) : '';
    for (const [k, id] of Object.entries(NOTE_IDS)) $(id).value = typeof rec.notes?.[k] === 'string' ? rec.notes[k] : '';
    $('reflection').value = typeof rec.reflection === 'string' ? rec.reflection : '';
    study.cases = (Array.isArray(rec.cases) ? rec.cases : []).slice(0, 30).flatMap(s => { try { const set = vi.importVLE(s.text, s.options); return [{ name: String(s.name).slice(0, 80), text: s.text, options: s.options, summary: { names: set.name, valid: set.valid.length, lim: pureLimits(set) } }]; } catch { return []; } });
    study.text = null; renderCases();
    if (validate({ quiet: true })) {
      if (rec.fitted) fit();
      if (rec.investigations?.signatures) runSig();
      if (rec.investigations?.models) runModels();
      if (rec.investigations?.endpoints) runEnd();
    }
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases were revalidated from the saved tables.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

function init() {
  buildAntoine();
  $('load-example').addEventListener('click', loadExample);
  $('validate').addEventListener('click', () => validate());
  $('vi-form').addEventListener('submit', e => { e.preventDefault(); validate(); });
  $('vi-form').addEventListener('input', e => { if (e.target.id !== 'prediction') updateFirstRow(); });
  $('vi-form').addEventListener('change', updateFirstRow);
  $('data-file').addEventListener('change', async e => { const f = e.target.files?.[0]; if (!f) return; if (f.size > 1e6) { showError('Use a table smaller than 1 MB.'); return; } $('data').value = await f.text(); updateFirstRow(); e.target.value = ''; $('status').textContent = 'Table loaded from ' + f.name + '. Check the units and Antoine constants, then validate.'; });
  $('fit').addEventListener('click', fit); $('view').addEventListener('change', renderChart);
  $('save-case').addEventListener('click', saveCase);
  $('run-sig').addEventListener('click', runSig); $('run-models').addEventListener('click', runModels); $('run-end').addEventListener('click', runEnd);
  $('check-evidence').addEventListener('click', () => { const r = evidenceCheck({ signatures: study.signatures, models: study.models, endpoints: study.endpoints, notes: notes() }); $('evidence-status').textContent = r.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : r.issues.join(' '); });
  $('export-study').addEventListener('click', exportStudy); $('import-study').addEventListener('change', openStudy);
  loadExample();
}

init();
