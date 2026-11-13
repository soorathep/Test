/** Lab 05 · 2027 preview page module. Fits use the shared course engines. */
import * as engine from '../../labs/assets/stability.js';
import { palette as c } from '../../labs/assets/palette.js';
import {
  LLE_GRADUATE_VERSION, SYNTHETIC_T, TRANSFER_LABELS, syntheticRows, measuredRows, fitSummary, fitVerdict,
  temperatureTransfer, alphaStudy, measurementSensitivity, evidenceCheck,
} from './lle-graduate.js';

const SCHEMA = 'skh-thermo-lle-fit-study/1';
const DATA_URL = '../labs/assets/cyclohexane-methanol-lle.json';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d });
const exp = v => v == null || !Number.isFinite(v) ? '—' : Math.abs(v) < 1e-4 && v !== 0 ? v.toExponential(2) : num(v);
const CASES = {
  synthetic: { name: 'Starting case · synthetic control', inputs: { source: 'synthetic', T: SYNTHETIC_T, alpha: 0.3, start12: 1, start21: 1 } },
  'measured-298': { name: 'Measured · 298.15 K', inputs: { source: 'measured', T: 298.15, alpha: 0.3, start12: 1, start21: 1 } },
  'measured-313': { name: 'Measured · 313.15 K', inputs: { source: 'measured', T: 313.15, alpha: 0.3, start12: 1, start21: 1 } },
};
const NOTE_IDS = { calibration: 'note-calibration', alpha: 'note-alpha', measurement: 'note-measurement', decision: 'note-decision' };
const study = { data: null, fit: null, inputs: null, rows: null, cases: [], transfer: null, alpha: null, sensitivity: null };

function cell(text) { const td = document.createElement('td'); td.textContent = text; return td; }
function li(html) { const item = document.createElement('li'); item.innerHTML = html; return item; }

function rowsFor(inputs) { return inputs.source === 'synthetic' ? syntheticRows() : measuredRows(study.data, inputs.T); }

function renderObservations() {
  const source = $('source').value; let rows;
  try { rows = rowsFor({ source, T: Number($('temperature').value) }); } catch { return; }
  $('temperature-control').hidden = source !== 'measured';
  $('observation-body').replaceChildren(...rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(r.T, 5)), cell(num(r.xAlpha, source === 'synthetic' ? 8 : 3)), cell(num(r.xBeta, source === 'synthetic' ? 8 : 3)), cell(r.uAlpha ? '±' + num(r.uAlpha) + ', ±' + num(r.uBeta) : 'None · generated')); return tr; }));
  $('source-note').textContent = source === 'synthetic'
    ? 'Generated from τ₁₂ = 3, τ₂₁ = 2, α = 0.3 by the global common tangent. Not a laboratory measurement.'
    : 'Measured tie line. x is the cyclohexane mole fraction; α is the cyclohexane-poor liquid.';
  const bounds = rows[0].uAlpha ? [rows[0].uAlpha, rows[0].uBeta] : [0.005, 0.005];
  $('bound-a').value = String(bounds[0]); $('bound-b').value = String(bounds[1]);
  $('run-transfer').disabled = source !== 'measured' || !study.fit;
}

function readInputs() {
  const errors = [], inputs = { source: $('source').value, T: $('source').value === 'synthetic' ? SYNTHETIC_T : Number($('temperature').value) };
  for (const [id, key, lo, hi, label] of [['alpha', 'alpha', 0.1, 0.6, 'α'], ['start12', 'start12', -2, 6, 'Starting τ₁₂'], ['start21', 'start21', -2, 6, 'Starting τ₂₁']]) {
    const raw = $(id).value.trim(), v = Number(raw), e = $('error-' + id);
    e.hidden = true; $(id).removeAttribute('aria-invalid');
    let message = '';
    if (raw === '' || !Number.isFinite(v)) message = 'Enter a number for ' + label + '.';
    else if (v < lo || v > hi) message = label + ' must lie between ' + lo + ' and ' + hi + '.';
    if (message) { errors.push({ id, message }); e.textContent = message; e.hidden = false; $(id).setAttribute('aria-invalid', 'true'); }
    inputs[key] = v;
  }
  return { inputs, errors };
}

function showErrors(errors) {
  const box = $('form-error');
  if (!errors.length) { box.hidden = true; box.replaceChildren(); return; }
  const list = document.createElement('ul');
  for (const error of errors) { const item = document.createElement('li'), a = document.createElement('a'); a.href = '#' + error.id; a.textContent = error.message; item.append(a); list.append(item); }
  box.replaceChildren(Object.assign(document.createElement('p'), { textContent: 'Correct these entries, then fit again:' }), list);
  box.hidden = false; box.focus();
}

function invalidateGraduate(message) {
  study.transfer = null; study.alpha = null; study.sensitivity = null;
  for (const id of ['transfer-results', 'alpha-wrap', 'measurement-results']) $(id).hidden = true;
  for (const id of ['transfer-status', 'alpha-status', 'measurement-status']) $(id).textContent = message || '';
  const option = $('view').querySelector('option[value="temperature"]'); option.disabled = true;
  if ($('view').value === 'temperature') $('view').value = 'gibbs';
}

function fit({ quiet = false } = {}) {
  const { inputs, errors } = readInputs(); showErrors(errors);
  if (errors.length || !study.data) return false;
  let rows, summary;
  try { rows = rowsFor(inputs); summary = fitSummary(rows, inputs.alpha, [inputs.start12, inputs.start21]); }
  catch (error) { showErrors([{ id: 'alpha', message: error.message }]); return false; }
  const changed = JSON.stringify(inputs) !== JSON.stringify(study.inputs);
  study.fit = summary; study.inputs = inputs; study.rows = rows;
  if (changed) invalidateGraduate('Settings changed. Run this investigation again for the current fit.');
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderRuns(); renderChart();
  for (const id of ['save-case', 'run-alpha', 'run-measurement', 'export-study']) $(id).disabled = false;
  $('run-transfer').disabled = inputs.source !== 'measured';
  $('transfer-status').textContent = inputs.source !== 'measured' ? 'The synthetic control has one temperature. Load a measured case to test temperature transfer.' : $('transfer-status').textContent;
  $('graduate-baseline').textContent = 'Current baseline: ' + (inputs.source === 'synthetic' ? 'synthetic control' : 'measured tie line') + ' at ' + num(inputs.T, 5) + ' K, α = ' + num(inputs.alpha) + ' · τ₁₂ = ' + num(summary.tau12, 5) + ', τ₂₁ = ' + num(summary.tau21, 5) + '.';
  if (!quiet) $('status').textContent = 'Fitted. Add the result to the comparison before changing a setting.';
  return true;
}

function renderResult() {
  const s = study.fit, v = fitVerdict(s), synthetic = study.inputs.source === 'synthetic';
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-verdict').textContent = v.level === 'pass' ? 'Tie line reproduced' : 'Fit converged, tie line missed';
  $('result-verdict').classList.toggle('verdict-fail', v.level !== 'pass');
  $('verdict-text').textContent = v.text;
  const p = $('prediction').value;
  $('prediction-feedback').textContent = !p ? '' : p === 'calibrates' ? 'Your prediction matches the design of this fit: two equations, two unknowns. Investigation A tests it on held-out tie lines.' : 'A near-zero residual here is guaranteed by two equations and two unknowns. Investigation A shows what it does not establish.';
  $('result-t12').textContent = num(s.tau12, 7); $('result-t21').textContent = num(s.tau21, 7);
  $('result-t12-note').textContent = synthetic ? 'Known value: τ₁₂ = 3.' : 'Dimensionless, at ' + num(s.T, 5) + ' K.';
  $('result-t21-note').textContent = synthetic ? 'Known value: τ₂₁ = 2.' : 'Dimensionless, at ' + num(s.T, 5) + ' K.';
  $('result-crmse').textContent = s.compositionRMSE === null ? 'No predicted split' : exp(s.compositionRMSE);
  $('result-pa').textContent = num(s.predictedAlpha); $('result-pb').textContent = num(s.predictedBeta);
  $('result-mu').textContent = exp(s.muRMSE);
  const tpd = s.predictedTPD.filter(Number.isFinite);
  $('result-tpd').textContent = tpd.length ? exp(Math.min(...tpd)) : 'Not available';
  $('result-starts').textContent = s.convergedStarts + ' / ' + s.starts;
  $('result-bound').textContent = s.atBound ? 'Yes' : 'No';
  $('result-svr').textContent = s.singularValueRatio === null ? 'Not defined' : num(s.singularValueRatio, 4);
  const link = $('lab04-link-row');
  if (v.level === 'pass') {
    const z = (s.predictedAlpha + s.predictedBeta) / 2;
    link.innerHTML = '';
    const a = document.createElement('a');
    a.href = 'stability.html?model=nrtl&from=lab05&tau12=' + s.tau12.toFixed(6) + '&tau21=' + s.tau21.toFixed(6) + '&alpha=' + s.alpha + '&z=' + z.toFixed(4);
    a.textContent = 'Inspect this fitted model in Lab 04';
    link.append(a, document.createTextNode(' (feed at the middle of the predicted tie line).'));
  } else link.textContent = '';
}

function renderPaper() {
  const s = study.fit, r = study.rows[0], list = $('calc-steps'), p = s.parameters;
  const muA = engine.chemicalPotentials(r.xAlpha, p), muB = engine.chemicalPotentials(r.xBeta, p);
  list.replaceChildren(
    li('Unknowns: τ₁₂ and τ₂₁ (α = ' + num(s.alpha) + ' fixed). Equations: one chemical-potential equality per component. Two equations, two unknowns.'),
    li('At x₁<sup>α</sup> = ' + num(r.xAlpha) + ': ln(x₁γ₁) = ' + num(muA[0]) + ', ln(x₂γ₂) = ' + num(muA[1]) + '.'),
    li('At x₁<sup>β</sup> = ' + num(r.xBeta) + ': ln(x₁γ₁) = ' + num(muB[0]) + ', ln(x₂γ₂) = ' + num(muB[1]) + '.'),
    li('Residuals: r₁ = ' + exp(muA[0] - muB[0]) + ', r₂ = ' + exp(muA[1] - muB[1]) + '. Their RMS is the chemical-potential residual above.'),
    li('Equal chemical potentials are necessary but not sufficient. The lab also solves the global common tangent of the fitted model: predicted x₁<sup>α</sup> = ' + num(s.predictedAlpha) + ', x₁<sup>β</sup> = ' + num(s.predictedBeta) + '.'),
  );
}

function renderRuns() {
  $('runs-body').replaceChildren(...study.fit.runs.map(run => { const tr = document.createElement('tr'); tr.append(cell('(' + num(run.start[0], 3) + ', ' + num(run.start[1], 3) + ')'), cell(num(run.tau12)), cell(num(run.tau21)), cell(exp(run.objective)), cell(run.converged ? 'Yes' : 'No'), cell(run.compositionRMSE === null ? 'No split' : exp(run.compositionRMSE))); return tr; }));
}

const trace = (x, y, name, color, dash = 'solid', mode = 'lines', symbol = 'circle') => ({ x, y, name, mode, line: { color, width: 2, dash }, marker: { color, size: 9, symbol }, connectgaps: false, hovertemplate: name + '<br>%{x:.4f}, %{y:.4f}<extra></extra>' });

async function renderChart() {
  if (!study.fit || !window.Plotly) { if (study.fit) setTimeout(renderChart, 200); return; }
  const view = $('view').value, s = study.fit, r = study.rows[0];
  let traces, layoutAxes, note;
  if (view === 'temperature' && study.transfer) {
    const t = study.transfer, rows = t.rows;
    traces = [trace(rows.map(q => q.xAlpha), rows.map(q => q.T), 'Measured', c.teal, 'solid', 'markers'), trace(rows.map(q => q.xBeta), rows.map(q => q.T), 'Measured (rich branch)', c.teal, 'solid', 'markers')];
    const colors = { constant: c.graphite, inverse: c.amber, 'two-point': c.rust };
    for (const mode of t.modes) {
      const ok = rows.filter(q => q.predictions[mode].status === 'split');
      traces.push(trace(ok.map(q => q.predictions[mode].xAlpha), ok.map(q => q.T), TRANSFER_LABELS[mode], colors[mode], mode === 'constant' ? 'dot' : 'solid', 'lines'));
      traces.push(trace(ok.map(q => q.predictions[mode].xBeta), ok.map(q => q.T), TRANSFER_LABELS[mode] + ' (rich branch)', colors[mode], mode === 'constant' ? 'dot' : 'solid', 'lines'));
    }
    layoutAxes = { xaxis: { title: { text: 'Cyclohexane mole fraction · x₁' }, range: [0, 1] }, yaxis: { title: { text: 'Temperature / K' } } };
    note = 'Points are measured tie lines. Lines are predictions from the calibration at ' + num(t.T0, 5) + ' K' + (t.T1 ? ' and ' + num(t.T1, 5) + ' K' : '') + ' under each τ(T) assumption.';
  } else {
    const curve = engine.gibbsCurve(s.parameters);
    traces = [trace(curve.map(q => q.x), curve.map(q => q.g), 'Fitted homogeneous liquid', c.amber), trace(curve.map(q => q.x), curve.map(q => q.hull), 'Equilibrium envelope', c.graphite, 'dash')];
    if (s.predictedAlpha !== null) traces.push(trace([s.predictedAlpha, s.predictedBeta], [engine.gibbs(s.predictedAlpha, s.parameters), engine.gibbs(s.predictedBeta, s.parameters)], 'Predicted tie line', c.graphite, 'solid', 'lines+markers'));
    traces.push(trace([r.xAlpha, r.xBeta], [engine.gibbs(r.xAlpha, s.parameters), engine.gibbs(r.xBeta, s.parameters)], 'Observed compositions', c.teal, 'solid', 'markers', 'diamond'));
    layoutAxes = { xaxis: { title: { text: 'Mole fraction of component 1 · x₁' }, range: [0, 1] }, yaxis: { title: { text: 'Mixing Gibbs energy · g = ΔmixG/(nRT)' } } };
    note = 'A successful fit puts the observed compositions (diamonds) at the contact points of the common tangent. If they sit elsewhere on the curve, equal chemical potentials were not reached on the observed branch.';
  }
  const layout = { margin: { l: 70, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false, hovermode: 'closest',
    xaxis: { zeroline: false, linecolor: c.graphite, gridcolor: c.mist, ...layoutAxes.xaxis }, yaxis: { zeroline: false, linecolor: c.graphite, gridcolor: c.mist, ...layoutAxes.yaxis } };
  try { await window.Plotly.react('fit-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* tables hold the values */ }
  $('chart-legend').replaceChildren(...traces.filter(t => !t.name.includes('rich branch')).map(t => {
    const sp = document.createElement('span'), i = document.createElement('i');
    i.style.borderColor = t.line.color; if (t.mode === 'markers') i.className = 'legend-dot'; else i.style.borderTopStyle = t.line.dash === 'solid' ? 'solid' : 'dashed';
    sp.append(i, document.createTextNode(t.name)); return sp;
  }));
  $('chart-note').textContent = note;
}

function predictionText(p) {
  if (!p) return '—';
  if (p.status === 'split') return num(p.xAlpha, 3) + ', ' + num(p.xBeta, 3) + (p.withinU ? ' ✓' : '');
  return p.status === 'none' ? 'No split' : 'Failed: ' + p.reason;
}

function runTransfer() {
  if (!study.fit || study.inputs.source !== 'measured') return;
  const T1raw = $('second-T').value, T1 = T1raw === '' ? null : Number(T1raw);
  try {
    const t = temperatureTransfer(study.data, study.inputs.alpha, study.inputs.T, T1);
    study.transfer = t; study.transferT1 = T1;
    $('transfer-summary').replaceChildren(...t.modes.map(mode => { const s = t.summary[mode], tr = document.createElement('tr'); tr.append(cell(TRANSFER_LABELS[mode]), cell(s.predicted + ' of ' + s.heldOut), cell(num(s.rmse, 4)), cell(num(s.maxError, 4)), cell(s.withinU + ' of ' + s.predicted)); return tr; }));
    $('transfer-body').replaceChildren(...t.rows.map(r => { const tr = document.createElement('tr'); tr.append(cell(num(r.T, 5)), cell(r.calibration ? 'Calibration' : 'Held out'), cell(num(r.xAlpha, 3) + ', ' + num(r.xBeta, 3)), cell(predictionText(r.predictions.constant)), cell(predictionText(r.predictions.inverse)), cell(predictionText(r.predictions['two-point']))); return tr; }));
    $('transfer-results').hidden = false;
    $('view').querySelector('option[value="temperature"]').disabled = false;
    $('view').querySelector('option[value="temperature"]').textContent = 'Tie lines across temperature';
    const best = t.modes.reduce((a, b) => (t.summary[b].rmse ?? Infinity) < (t.summary[a].rmse ?? Infinity) ? b : a);
    $('transfer-status').textContent = 'Calibrated at ' + num(t.T0, 5) + ' K' + (t.T1 ? ' and ' + num(t.T1, 5) + ' K' : '') + '. Lowest held-out error: ' + TRANSFER_LABELS[best] + ', ' + num(t.summary[best].rmse, 3) + ' mol/mol. ✓ marks predictions within the expanded uncertainty of both compositions.';
  } catch (error) { $('transfer-status').textContent = 'The prediction could not run: ' + error.message; }
}

function runAlpha() {
  if (!study.fit) return;
  const measured = study.inputs.source === 'measured';
  const rows = alphaStudy(study.rows, measured ? study.data : null, measured ? study.inputs.T : null);
  study.alpha = rows;
  $('alpha-body').replaceChildren(...rows.map(row => {
    const tr = document.createElement('tr'), s = row.summary;
    if (row.status !== 'fitted') { tr.append(cell(num(row.alpha)), cell('Failed: ' + row.reason), cell('—'), cell('—'), cell('—'), cell('—'), cell('—')); return tr; }
    tr.append(cell(num(row.alpha)), cell(row.verdict.level === 'pass' ? 'Reproduces the tie line' : 'Converged but misses the tie line' + (s.atBound ? ' (τ at a bound)' : '')), cell(num(s.tau12, 5)), cell(num(s.tau21, 5)), cell(s.compositionRMSE === null ? 'No split' : exp(s.compositionRMSE)), cell(s.convergedStarts + ' / ' + s.starts), cell(row.transfer ? num(row.transfer.rmse, 3) : measured ? '—' : 'One temperature only'));
    if (row.verdict.level !== 'pass') tr.className = 'highlight-row';
    return tr;
  }));
  $('alpha-wrap').hidden = false;
  const pass = rows.filter(r => r.verdict?.level === 'pass').map(r => num(r.alpha));
  $('alpha-status').textContent = pass.length + ' of 3 α values reproduce the same tie line (α = ' + (pass.join(', ') || 'none') + ') with different τ. The tie line alone cannot choose among them.';
}

function runMeasurement() {
  if (!study.fit) return;
  try {
    const m = measurementSensitivity(study.rows, study.inputs.alpha, { xAlpha: $('bound-a').value.trim(), xBeta: $('bound-b').value.trim() });
    study.sensitivity = m;
    const range = r => r ? num(r[0], 4) + ' to ' + num(r[1], 4) : 'No accepted refit';
    $('range-t12').textContent = range(m.ranges.tau12); $('range-t21').textContent = range(m.ranges.tau21);
    $('measurement-body').replaceChildren(...[...m.oneAtATime, ...m.corners].map(s => { const tr = document.createElement('tr'); tr.append(cell(s.label), cell(s.status === 'fitted' ? 'Tie line reproduced' : s.reason), cell(num(s.xAlpha, 4)), cell(num(s.xBeta, 4)), cell(num(s.tau12, 5)), cell(num(s.tau21, 5))); return tr; }));
    $('measurement-results').hidden = false;
    $('measurement-status').textContent = m.accepted + ' of ' + m.total + ' shifted tie lines refitted around α = ' + num(m.alpha) + ' with ±Δx₁ᵅ = ' + num(m.bounds.xAlpha) + ' and ±Δx₁ᵝ = ' + num(m.bounds.xBeta) + '.';
  } catch (error) { $('measurement-status').textContent = 'The refits could not run: ' + error.message; $('measurement-results').hidden = true; }
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([k, id]) => [k, $(id).value])); }

function saveCase() {
  if (!study.fit) return;
  const name = $('case-name').value.trim() || 'Case ' + (study.cases.length + 1), s = study.fit;
  study.cases.push({ name, inputs: { ...study.inputs }, summary: { tau12: s.tau12, tau21: s.tau21, compositionRMSE: s.compositionRMSE } });
  renderCases(); $('status').textContent = 'Saved “' + name + '”. Change one setting, fit, then save the next case.';
}

function renderCases() {
  $('comparison-empty').hidden = study.cases.length > 0; $('comparison-table-wrap').hidden = !study.cases.length;
  $('comparison-body').replaceChildren(...study.cases.map(saved => {
    const tr = document.createElement('tr'), s = saved.summary;
    tr.append(cell(saved.name), cell(saved.inputs.source === 'synthetic' ? 'Synthetic control' : 'Measured'), cell(num(saved.inputs.T, 5)), cell(num(saved.inputs.alpha)), cell(num(s.tau12, 5)), cell(num(s.tau21, 5)), cell(s.compositionRMSE === null ? 'No split' : exp(s.compositionRMSE)));
    const td = document.createElement('td'), b = document.createElement('button');
    b.type = 'button'; b.className = 'secondary-button'; b.textContent = 'Reopen'; b.setAttribute('aria-label', 'Reopen ' + saved.name);
    b.addEventListener('click', () => { applyInputs(saved.inputs); $('case-name').value = saved.name; fit({ quiet: true }); $('status').textContent = 'Reopened and refitted “' + saved.name + '”.'; $('results').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    td.append(b); tr.append(td); return tr;
  }));
}

function applyInputs(inputs) {
  $('source').value = inputs.source; $('temperature').value = String(inputs.T);
  $('alpha').value = String(inputs.alpha); $('start12').value = String(inputs.start12); $('start21').value = String(inputs.start21);
  renderObservations(); fillSecondT();
}

function fillSecondT(selected) {
  if (!study.data) return;
  const T0 = Number($('temperature').value), keep = selected ?? $('second-T').value;
  const options = [Object.assign(document.createElement('option'), { value: '', textContent: 'None · one-temperature assumptions only' }),
    ...study.data.rows.filter(r => r.T !== T0).map(r => Object.assign(document.createElement('option'), { value: String(r.T), textContent: num(r.T, 5) + ' K' }))];
  $('second-T').replaceChildren(...options);
  const preferred = keep && study.data.rows.some(r => String(r.T) === String(keep) && r.T !== T0) ? String(keep) : (T0 === 313.15 ? '298.15' : '313.15');
  $('second-T').value = preferred;
}

function loadCase(id) {
  const preset = CASES[id]; if (!preset) return;
  applyInputs(preset.inputs); $('case-name').value = preset.name;
  for (const b of document.querySelectorAll('[data-case]')) b.setAttribute('aria-pressed', String(b.dataset.case === id));
  $('case-description').textContent = preset.inputs.source === 'synthetic'
    ? 'One tie line at 298.15 K was generated by NRTL with τ₁₂ = 3, τ₂₁ = 2 and α = 0.3. Fit τ₁₂ and τ₂₁ with α fixed, and check whether the known values are recovered.'
    : 'Cyclohexane (1) + methanol (2) at ' + num(preset.inputs.T, 5) + ' K and about 100 kPa. Fit τ₁₂ and τ₂₁ to the measured tie line with α = 0.3, then test what the fit predicts at other temperatures.';
  $('status').textContent = preset.name + ' loaded. Make a prediction, then press Fit and verify.';
}

function exportStudy() {
  const record = { schema: SCHEMA, graduateVersion: LLE_GRADUATE_VERSION, savedAt: new Date().toISOString(), inputs: study.inputs || readInputs().inputs,
    prediction: $('prediction').value, caseName: $('case-name').value, cases: study.cases, secondT: $('second-T').value,
    bounds: { xAlpha: $('bound-a').value, xBeta: $('bound-b').value }, notes: notes(), reflection: $('reflection').value,
    investigations: { transfer: Boolean(study.transfer), alpha: Boolean(study.alpha), sensitivity: Boolean(study.sensitivity) } };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab05-lle-fit-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded. Open it later to restore the cases, settings and notes.';
}

function validInputs(i) {
  if (!i || !['synthetic', 'measured'].includes(i.source)) return false;
  if (i.source === 'measured' && !study.data.rows.some(r => r.T === i.T)) return false;
  return [['alpha', 0.1, 0.6], ['start12', -2, 6], ['start21', -2, 6]].every(([k, lo, hi]) => Number.isFinite(i[k]) && i[k] >= lo && i[k] <= hi);
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2e6) throw new Error('The file is larger than a Lab 05 study.');
    const record = JSON.parse(await file.text());
    if (record.schema !== SCHEMA) throw new Error('This file is not a Lab 05 (2027) study.');
    if (!validInputs(record.inputs)) throw new Error('The saved inputs are invalid.');
    applyInputs(record.inputs); fillSecondT(record.secondT);
    $('bound-a').value = record.bounds?.xAlpha ?? $('bound-a').value; $('bound-b').value = record.bounds?.xBeta ?? $('bound-b').value;
    $('prediction').value = record.prediction || ''; $('case-name').value = typeof record.caseName === 'string' ? record.caseName.slice(0, 80) : '';
    for (const [k, id] of Object.entries(NOTE_IDS)) $(id).value = typeof record.notes?.[k] === 'string' ? record.notes[k] : '';
    $('reflection').value = typeof record.reflection === 'string' ? record.reflection : '';
    const cases = Array.isArray(record.cases) ? record.cases.filter(s => validInputs(s?.inputs) && typeof s.name === 'string').slice(0, 30) : [];
    study.cases = cases.map(saved => { const s = fitSummary(rowsFor(saved.inputs), saved.inputs.alpha, [saved.inputs.start12, saved.inputs.start21]); return { name: saved.name.slice(0, 80), inputs: saved.inputs, summary: { tau12: s.tau12, tau21: s.tau21, compositionRMSE: s.compositionRMSE } }; });
    study.inputs = null; renderCases(); fit({ quiet: true });
    if (record.investigations?.transfer && study.inputs.source === 'measured') runTransfer();
    if (record.investigations?.alpha) runAlpha();
    if (record.investigations?.sensitivity) runMeasurement();
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases and the investigations were refitted from the saved inputs.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

async function init() {
  for (const b of document.querySelectorAll('[data-case]')) b.addEventListener('click', () => loadCase(b.dataset.case));
  $('source').addEventListener('change', () => { renderObservations(); fillSecondT(); });
  $('temperature').addEventListener('change', () => { renderObservations(); fillSecondT(); });
  $('fit').addEventListener('click', () => fit());
  $('fit-form').addEventListener('submit', e => { e.preventDefault(); fit(); });
  $('view').addEventListener('change', renderChart);
  $('save-case').addEventListener('click', saveCase);
  $('run-transfer').addEventListener('click', runTransfer);
  $('run-alpha').addEventListener('click', runAlpha);
  $('run-measurement').addEventListener('click', runMeasurement);
  $('check-evidence').addEventListener('click', () => {
    const r = evidenceCheck({ transfer: study.transfer, alpha: study.alpha, sensitivity: study.sensitivity, notes: notes() });
    $('evidence-status').textContent = r.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : r.issues.join(' ');
  });
  $('export-study').addEventListener('click', exportStudy);
  $('import-study').addEventListener('change', openStudy);
  try {
    const response = await fetch(DATA_URL, { cache: 'no-cache' });
    if (!response.ok) throw new Error('HTTP ' + response.status);
    study.data = await response.json();
    $('temperature').replaceChildren(...study.data.rows.map(r => Object.assign(document.createElement('option'), { value: String(r.T), textContent: num(r.T, 5) + ' K' })));
    $('fit').disabled = false;
    loadCase('synthetic');
  } catch (error) { $('status').textContent = 'The measured data record could not be loaded (' + error.message + '). Reload the page to try again.'; }
}

init();
