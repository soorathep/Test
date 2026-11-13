/** Lab 04 · 2027 preview page module. Calculations use the shared course engine. */
import * as engine from '../../labs/assets/stability.js';
import { palette as c } from '../../labs/assets/palette.js';
import {
  STABILITY_GRADUATE_VERSION, MODELS, PARAMETER_KEYS, PARAMETER_LABELS, DEFAULT_BOUNDS,
  solve, localGlobalAudit, sensitivityStudy, modelMatchStudy, evidenceCheck,
} from './stability-graduate.js';

const SCHEMA = 'skh-thermo-stability-study/1';
const $ = id => document.getElementById(id);
const num = (v, d = 6) => v == null || !Number.isFinite(v) ? '—' : Number(v).toLocaleString('en-US', { maximumSignificantDigits: d });
const exp = v => v == null || !Number.isFinite(v) ? '—' : Math.abs(v) < 1e-4 && v !== 0 ? v.toExponential(2) : num(v);
const CASES = {
  baseline: { name: 'Starting case · z₁ = 0.50', inputs: { model: 'symmetric', A: 3, z: 0.5 } },
  dilute: { name: 'Dilute feed · z₁ = 0.12', inputs: { model: 'symmetric', A: 3, z: 0.12 } },
  'very-dilute': { name: 'Very dilute feed · z₁ = 0.02', inputs: { model: 'symmetric', A: 3, z: 0.02 } },
  'near-critical': { name: 'Near-critical · A = 2.05, z₁ = 0.50', inputs: { model: 'symmetric', A: 2.05, z: 0.5 } },
};
const RANGES = { A: [0, 6], A12: [0, 6], A21: [0, 6], tau12: [-2, 6], tau21: [-2, 6], alpha: [0.1, 0.6], z: [0, 1] };
const NOTE_IDS = { local: 'note-local', sensitivity: 'note-sensitivity', model: 'note-model', decision: 'note-decision' };

const study = { result: null, inputs: null, cases: [], audit: null, sensitivity: null, match: null, source: null };

function modelText(inputs) {
  if (inputs.model === 'symmetric') return 'Margules · A = ' + num(inputs.A);
  if (inputs.model === 'asymmetric') return 'Margules · A₁₂ = ' + num(inputs.A12) + ', A₂₁ = ' + num(inputs.A21);
  return 'NRTL · τ₁₂ = ' + num(inputs.tau12) + ', τ₂₁ = ' + num(inputs.tau21) + ', α = ' + num(inputs.alpha);
}

function showModelControls() {
  const model = $('model').value;
  $('symmetric-control').hidden = model !== 'symmetric';
  $('asymmetric-control').hidden = model !== 'asymmetric';
  $('nrtl-control').hidden = model !== 'nrtl';
  $('model-note').innerHTML = model === 'symmetric' ? 'g<sup>E</sup>/RT = A x₁x₂. The starting problem uses A = 3.'
    : model === 'asymmetric' ? 'g<sup>E</sup>/RT = x₁x₂(A₁₂x₂ + A₂₁x₁). A₁₂ = ln γ₁∞ and A₂₁ = ln γ₂∞.'
      : 'NRTL with constant τ at one fixed temperature. Some parameter sets give two separate miscibility gaps.';
  const option = $('view').querySelector('option[value="map"]');
  option.disabled = model === 'nrtl';
  if (model === 'nrtl' && $('view').value === 'map') $('view').value = 'gibbs';
}

function setField(key, value) { const input = $(key); if (input && value !== undefined) input.value = String(value); }

function applyInputs(inputs) {
  $('model').value = inputs.model;
  for (const key of ['A', 'A12', 'A21', 'tau12', 'tau21', 'alpha', 'z']) setField(key, inputs[key]);
  showModelControls(); buildBounds();
}

function readInputs() {
  const model = $('model').value, keys = [...PARAMETER_KEYS[model], 'z'], errors = [];
  const inputs = { model };
  for (const id of ['A', 'A12', 'A21', 'tau12', 'tau21', 'alpha', 'z']) { const e = $('error-' + id); if (e) { e.hidden = true; e.textContent = ''; } $(id)?.removeAttribute('aria-invalid'); }
  for (const key of keys) {
    const raw = $(key).value.trim(), value = Number(raw), [lo, hi] = RANGES[key];
    let message = '';
    if (raw === '') message = 'Enter ' + PARAMETER_LABELS[key] + '.';
    else if (!Number.isFinite(value)) message = PARAMETER_LABELS[key] + ' must be a number.';
    else if (value < lo || value > hi) message = PARAMETER_LABELS[key] + ' must lie between ' + lo + ' and ' + hi + '.';
    if (message) { errors.push({ key, message }); const e = $('error-' + key); e.textContent = message; e.hidden = false; $(key).setAttribute('aria-invalid', 'true'); }
    inputs[key] = value;
  }
  return { inputs, errors };
}

function showErrors(errors) {
  const box = $('form-error');
  if (!errors.length) { box.hidden = true; box.replaceChildren(); return; }
  box.replaceChildren(Object.assign(document.createElement('p'), { textContent: 'Correct these entries, then calculate again:' }),
    Object.assign(document.createElement('ul'), { innerHTML: '' }));
  for (const error of errors) { const li = document.createElement('li'), a = document.createElement('a'); a.href = '#' + error.key; a.textContent = error.message; li.append(a); box.lastChild.append(li); }
  box.hidden = false; box.focus();
}

const STATE_TEXT = {
  stable: 'The homogeneous feed lies on the convex envelope of g. Its equilibrium is one liquid at the feed composition.',
  metastable: 'The homogeneous feed has positive curvature, so it resists small fluctuations. A finite split onto the common tangent still lowers the Gibbs energy, so the equilibrium is two liquids.',
  unstable: 'The homogeneous feed has negative curvature: small composition fluctuations already lower g. The equilibrium is two liquids on the common tangent.',
  critical: 'The two coexistence compositions merge at the critical composition. This is one critical liquid; a lever-rule fraction is not defined.',
  'spinodal boundary': 'The feed sits on the spinodal, where the local curvature is zero. The common tangent still gives a lower-energy two-liquid equilibrium.',
  'binodal boundary': 'The feed lies at a coexistence boundary. An infinitesimal amount of the conjugate liquid can appear; the present liquid keeps the feed composition.',
};

function invalidateGraduate(message) {
  study.audit = null; study.sensitivity = null; study.match = null;
  for (const id of ['audit-wrap', 'sensitivity-results', 'match-wrap']) $(id).hidden = true;
  for (const id of ['audit-status', 'sensitivity-status', 'match-status']) $(id).textContent = message || '';
}

function calculate({ quiet = false } = {}) {
  const { inputs, errors } = readInputs();
  showErrors(errors);
  if (errors.length) return false;
  let result;
  try { result = solve(inputs); }
  catch (error) {
    showErrors([{ key: inputs.model === 'symmetric' ? 'A' : PARAMETER_KEYS[inputs.model][0], message: error.message }]);
    return false;
  }
  const changed = JSON.stringify(inputs) !== JSON.stringify(study.inputs);
  study.result = result; study.inputs = inputs;
  if (changed) invalidateGraduate('Settings changed. Run this investigation again for the current feed.');
  $('diagram-panel').hidden = false;
  renderResult(); renderPaper(); renderChart(); renderCurveTable();
  for (const id of ['save-case', 'run-audit', 'run-sensitivity', 'run-match', 'export-study']) $(id).disabled = false;
  $('graduate-baseline').textContent = 'Current baseline: ' + modelText(inputs) + ', z₁ = ' + num(inputs.z) + ' · ' + result.phase + ' (' + result.state + ' homogeneous feed).';
  if (!quiet) $('status').textContent = 'Calculated. Add the result to the comparison before changing a setting.';
  return true;
}

function renderResult() {
  const r = study.result, two = r.phase === 'two liquids';
  $('result-placeholder').hidden = true; $('results').hidden = false;
  $('result-phase').textContent = two ? 'Two liquids' : r.state === 'critical' ? 'One critical liquid' : 'One liquid';
  $('phase-interpretation').textContent = STATE_TEXT[r.state] || '';
  const predicted = $('prediction').value, predictedLocal = $('prediction-local').value, feedback = [];
  if (predicted) feedback.push(predicted === r.phase ? 'Your equilibrium prediction matches the calculation.' : 'You predicted ' + predicted + '; the calculation gives ' + r.phase + '. Use Step 3 to see why.');
  if (predictedLocal && r.curvature !== null) {
    const actual = r.curvature > 0 ? 'resists' : 'grows';
    feedback.push(predictedLocal === actual ? 'Your local prediction matches the sign of g″(z₁).' : 'The sign of g″(z₁) differs from your local prediction.');
  }
  $('prediction-feedback').textContent = feedback.join(' ');
  $('result-xa').textContent = num(r.gapAlpha, 8); $('result-xb').textContent = num(r.gapBeta, 8);
  $('result-xa-note').textContent = r.gapAlpha === null ? 'No miscibility gap for these parameters.' : two ? 'Component-1-poor liquid present at equilibrium.' : 'Boundary of the gap. This liquid is not present for the current feed.';
  $('result-xb-note').textContent = r.gapBeta === null ? 'No miscibility gap for these parameters.' : two ? 'Component-1-rich liquid present at equilibrium.' : 'Boundary of the gap. This liquid is not present for the current feed.';
  if (r.gapCount > 1) $('result-xb-note').textContent += ' The model has ' + r.gapCount + ' separate gaps; the plot shows all of them.';
  $('result-fb').textContent = two ? num(r.fractionBeta) : 'Not defined';
  $('result-fb-note').innerHTML = two ? 'Lever rule: f<sub>β</sub> = (z₁ − x₁<sup>α</sup>)/(x₁<sup>β</sup> − x₁<sup>α</sup>).' : 'One liquid: no lever-rule fraction is assigned.';
  $('result-na').textContent = two ? num(r.fractionAlpha) : num(1); $('result-nb').textContent = two ? num(r.fractionBeta) : '0';
  $('result-state').innerHTML = '<span class="state-label">' + r.state + '</span>';
  $('result-curvature').textContent = r.curvature === null ? 'Diverges at a pure feed' : num(r.curvature);
  $('result-tpd').textContent = r.tpdMinimum === null ? 'Not applicable' : exp(r.tpdMinimum) + (r.tpdMinimum < -1e-10 ? ' (negative)' : '');
  $('result-gain').textContent = exp(r.gain);
  $('result-balance').textContent = r.balanceResidual.toExponential(2);
  $('result-mu').textContent = r.chemicalPotentialResidual === null ? 'Not applicable · one liquid' : r.chemicalPotentialResidual.toExponential(2);
}

function li(html) { const item = document.createElement('li'); item.innerHTML = html; return item; }

function renderPaper() {
  const r = study.result, i = study.inputs, z = i.z, list = $('calc-steps');
  list.replaceChildren();
  if (i.model === 'symmetric') {
    const A = i.A;
    list.append(li('Local test: g″(z₁) = 1/[z₁(1 − z₁)] − 2A = 1/[' + num(z) + '(' + num(1 - z) + ')] − ' + num(2 * A) + ' = ' + num(r.curvature) + '.'));
    if (A > 2) {
      const s = (1 - Math.sqrt(1 - 2 / A)) / 2;
      list.append(li('Spinodals: x₁(1 − x₁) = 1/(2A) gives x₁ = ' + num(s) + ' and ' + num(1 - s) + '. Between them the homogeneous liquid is locally unstable.'));
      list.append(li('Coexistence (symmetric model): ln[x₁/(1 − x₁)] + A(1 − 2x₁) = 0 with x₁<sup>β</sup> = 1 − x₁<sup>α</sup>. Check: ln[' + num(r.gapAlpha) + '/' + num(1 - r.gapAlpha) + '] + ' + num(A) + '(' + num(1 - 2 * r.gapAlpha) + ') = ' + exp(Math.log(r.gapAlpha / (1 - r.gapAlpha)) + A * (1 - 2 * r.gapAlpha)) + '.'));
    } else list.append(li('A ≤ 2, so g″ &gt; 0 everywhere and no common tangent exists. The feed is one liquid.'));
  } else {
    list.append(li('The coexistence compositions satisfy equal chemical potentials of both components in both liquids: ln(x<sub>i</sub>γ<sub>i</sub>)<sup>α</sup> = ln(x<sub>i</sub>γ<sub>i</sub>)<sup>β</sup>. The residual above checks this equality.'));
    list.append(li('Local test: the sign of g″(z₁) = ' + num(r.curvature) + ' decides only the response to small fluctuations.'));
  }
  if (r.phase === 'two liquids') {
    list.append(li('Lever rule: f<sub>β</sub> = (' + num(z) + ' − ' + num(r.gapAlpha) + ')/(' + num(r.gapBeta) + ' − ' + num(r.gapAlpha) + ') = ' + num(r.fractionBeta) + ', so f<sub>α</sub> = ' + num(r.fractionAlpha) + '.'));
    list.append(li('Balance: f<sub>α</sub>x₁<sup>α</sup> + f<sub>β</sub>x₁<sup>β</sup> = ' + num(r.fractionAlpha * r.gapAlpha + r.fractionBeta * r.gapBeta) + ', matching z₁ = ' + num(z) + '.'));
    list.append(li('Energy: the split lowers g from ' + num(r.homogeneousG) + ' to ' + num(r.equilibriumG) + ', a decrease of ' + exp(r.gain) + ' per mol of feed.'));
  } else {
    list.append(li('One liquid at x₁ = z₁ = ' + num(z) + '. Do not apply the lever rule outside the coexistence interval; it would give a negative fraction.'));
  }
}

function renderCurveTable() {
  const curve = engine.gibbsCurve(study.result.parameters, 100);
  $('curve-body').replaceChildren(...curve.filter((_, k) => k % 5 === 0).map(p => {
    const tr = document.createElement('tr');
    for (const v of [num(p.x, 3), num(p.g), num(p.hull), p.curvature === null ? '—' : num(p.curvature)]) { const td = document.createElement('td'); td.textContent = v; tr.append(td); }
    return tr;
  }));
}

const trace = (x, y, name, color, dash = 'solid', mode = 'lines') => ({ x, y, name, mode, line: { color, width: 2, dash }, marker: { color, size: 9 }, connectgaps: false, hovertemplate: name + '<br>%{x:.4f}, %{y:.5f}<extra></extra>' });

async function renderChart() {
  if (!study.result || !window.Plotly) { if (study.result) setTimeout(renderChart, 200); return; }
  const r = study.result, p = r.parameters, z = r.z, view = $('view').value;
  let traces = [], shapes = [], yTitle = '', xTitle = 'Mole fraction of component 1 · x₁', note = '', yRange;
  const vline = x => ({ type: 'line', xref: 'x', yref: 'paper', x0: x, x1: x, y0: 0, y1: 1, line: { color: c.graphite, width: 1.5, dash: 'dot' } });
  if (view === 'gibbs') {
    const curve = engine.gibbsCurve(p);
    traces = [trace(curve.map(q => q.x), curve.map(q => q.ideal), 'Ideal mixture', c.teal),
      trace(curve.map(q => q.x), curve.map(q => q.g), 'Homogeneous liquid', c.amber),
      trace(curve.map(q => q.x), curve.map(q => q.hull), 'Equilibrium envelope', c.graphite, 'dash')];
    r.raw.gaps.forEach((gap, k) => traces.push(trace([gap.xAlpha, gap.xBeta], [gap.gAlpha, gap.gBeta], 'Common tangent' + (r.raw.gaps.length > 1 ? ' ' + (k + 1) : ''), c.graphite, 'solid', 'lines+markers')));
    traces.push(trace([z], [r.homogeneousG], 'Homogeneous feed', c.amber, 'solid', 'markers'));
    if (r.phase === 'two liquids') traces.push(trace([z], [r.equilibriumG], 'Split feed', c.graphite, 'solid', 'markers'));
    shapes = r.spinodals.map(vline);
    yTitle = 'Mixing Gibbs energy · g = ΔmixG/(nRT)';
    note = 'The common tangent touches g at the two coexistence compositions. Between them the equilibrium follows the tangent, not the curve. Dotted lines mark the spinodals.';
  } else if (view === 'tpd') {
    const t = r.raw.tpd;
    traces = [trace(t.points.map(q => q.x), t.points.map(q => q.tpd), 'TPD relative to the feed', c.amber)];
    if (t.minimum !== null) traces.push(trace([t.w], [t.minimum], 'Global minimum', c.graphite, 'solid', 'markers'));
    shapes = [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 0, y1: 0, line: { color: c.graphite, width: 1.5 } }];
    yTitle = 'Tangent-plane distance / RT'; xTitle = 'Trial liquid composition · w₁';
    note = 'TPD(w) = g(w) − g(z) − g′(z)(w − z). Any negative value shows that a trial liquid lies below the tangent at the feed, so the homogeneous feed is not the equilibrium. The minimum is found from stationary points, not only from the plotted samples.';
  } else if (view === 'curvature') {
    const curve = engine.gibbsCurve(p).filter(q => q.curvature !== null);
    traces = [trace(curve.map(q => q.x), curve.map(q => q.curvature), 'g″(x₁)', c.amber)];
    if (r.curvature !== null) traces.push(trace([z], [r.curvature], 'Current feed', c.teal, 'solid', 'markers'));
    shapes = [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 0, y1: 0, line: { color: c.graphite, width: 1.5 } }];
    yTitle = 'g″(x₁)'; yRange = [-9, 20];
    note = 'Negative curvature marks local instability. Positive curvature alone cannot exclude a lower-energy split. Curvature diverges at the pure endpoints; the vertical axis is clipped.';
  } else {
    const fixed = study.inputs.model === 'asymmetric' ? study.inputs.A21 : null, level = study.inputs.model === 'asymmetric' ? study.inputs.A12 : study.inputs.A;
    const map = engine.phaseMap(fixed);
    traces = [trace(map.map(q => q.xAlpha), map.map(q => q.A), 'Binodal', c.amber), trace(map.map(q => q.xBeta), map.map(q => q.A), 'Binodal (rich branch)', c.amber),
      trace(map.map(q => q.spinodalAlpha), map.map(q => q.A), 'Spinodal', c.graphite, 'dash'), trace(map.map(q => q.spinodalBeta), map.map(q => q.A), 'Spinodal (rich branch)', c.graphite, 'dash'),
      trace([z], [level], 'Current feed', c.teal, 'solid', 'markers')];
    shapes = [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: level, y1: level, line: { color: c.teal, width: 1.5, dash: 'dot' } }];
    yTitle = fixed === null ? 'Margules A' : 'A₁₂ (A₂₁ = ' + num(fixed) + ' fixed)'; yRange = [0, 6.1];
    note = 'Inside the binodal the equilibrium is two liquids. Between binodal and spinodal a homogeneous feed is metastable; inside the spinodal it is unstable. The vertical axis is a model parameter, not temperature.';
  }
  const layout = { margin: { l: 70, r: 16, t: 16, b: 56 }, font: { family: 'Source Sans 3, sans-serif', size: 13, color: c.ink }, paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false,
    xaxis: { title: { text: xTitle }, range: [0, 1], zeroline: false, linecolor: c.graphite, gridcolor: c.mist },
    yaxis: { title: { text: yTitle }, zeroline: false, linecolor: c.graphite, gridcolor: c.mist, ...(yRange ? { range: yRange } : {}) }, shapes, hovermode: 'closest' };
  try { await window.Plotly.react('lle-chart', traces, layout, { responsive: true, displayModeBar: false }); } catch { /* the table below still holds the values */ }
  $('chart-legend').replaceChildren(...traces.filter(t => !t.name.includes('branch')).map(t => {
    const s = document.createElement('span'), i = document.createElement('i');
    i.style.borderColor = t.line.color; if (t.mode === 'markers') i.className = 'legend-dot'; else i.style.borderTopStyle = t.line.dash === 'solid' ? 'solid' : 'dashed';
    s.append(i, document.createTextNode(t.name)); return s;
  }));
  $('chart-note').textContent = note;
}

function cell(text) { const td = document.createElement('td'); td.textContent = text; return td; }

function runAudit() {
  if (!study.result) return;
  const feeds = [...new Set([study.inputs.z, 0.02, 0.12, 0.5])].sort((a, b) => a - b);
  try {
    const rows = feeds.map(z => localGlobalAudit({ ...study.inputs, z }));
    study.audit = { inputs: { ...study.inputs }, rows };
    $('audit-body').replaceChildren(...rows.map(row => {
      const tr = document.createElement('tr');
      tr.append(cell(num(row.z) + (row.z === study.inputs.z ? ' (current)' : '')), cell(row.reading), cell(row.curvature === null ? '—' : num(row.curvature)),
        cell(row.tpdMinimum === null ? '—' : exp(row.tpdMinimum)), cell(num(row.tpdTrial, 4)), cell(exp(row.gain)), cell(row.state));
      if (row.disagreement) tr.className = 'highlight-row';
      return tr;
    }));
    $('audit-wrap').hidden = false;
    const disagree = rows.filter(row => row.disagreement).map(row => num(row.z));
    $('audit-status').textContent = rows.length + ' feeds compared with ' + modelText(study.inputs) + '. ' + (disagree.length ? 'Local and global evidence disagree at z₁ = ' + disagree.join(', ') + '.' : 'No feed shows positive curvature with a negative TPD for these parameters.');
  } catch (error) { $('audit-status').textContent = 'The audit could not run: ' + error.message; }
}

function buildBounds(saved = {}) {
  const model = $('model').value, keys = [...PARAMETER_KEYS[model], 'z'], grid = $('bounds-grid');
  grid.replaceChildren(...keys.map(key => {
    const wrap = document.createElement('div'), label = document.createElement('label'), box = document.createElement('div'), input = document.createElement('input'), unit = document.createElement('span');
    label.htmlFor = 'bound-' + key; label.textContent = 'Half-width ±Δ' + PARAMETER_LABELS[key];
    box.className = 'quantity-input'; input.id = 'bound-' + key; input.type = 'number'; input.min = '0'; input.step = 'any';
    input.value = String(saved[key] ?? DEFAULT_BOUNDS[key]); unit.id = 'bound-unit-' + key; unit.textContent = key === 'z' ? 'mol/mol' : 'dimensionless';
    input.setAttribute('aria-describedby', unit.id); box.append(input, unit); wrap.append(label, box); return wrap;
  }));
}

function readBounds() { return Object.fromEntries([...$('bounds-grid').querySelectorAll('input')].map(input => [input.id.slice(6), input.value.trim()])); }

function runSensitivity() {
  if (!study.result) return;
  try {
    const result = sensitivityStudy(study.inputs, readBounds());
    study.sensitivity = { inputs: { ...study.inputs }, bounds: result.bounds, result };
    const range = r => r ? num(r[0]) + ' to ' + num(r[1]) : 'No sampled corner has a gap';
    $('range-xa').textContent = range(result.ranges.xAlpha); $('range-fb').textContent = range(result.ranges.fractionBeta);
    const phases = Object.entries(result.phaseCounts).map(([k, v]) => k + ' = ' + v).join(', ');
    $('sensitivity-counts').textContent = result.counts.total + ' signed corners: ' + result.counts.finite + ' finite, ' + result.counts.failed + ' failed. Phase counts: ' + (phases || 'none') + '. Counts describe the chosen scenarios, not phase probabilities.';
    const d = result.derivative;
    $('sensitivity-derivative').textContent = d ? 'Local derivative at A = ' + num(study.inputs.A) + ': dx₁ᵅ/dA = −(1 − 2x₁ᵅ)/[1/(x₁ᵅ(1 − x₁ᵅ)) − 2A] = ' + num(d.dxdA) + '. For ±ΔA = ' + num(result.bounds.A) + ' the linear estimate is |Δx₁ᵅ| ≈ ' + num(d.linearChange) + '. Compare it with the finite one-factor change in the table. The denominator ' + num(d.denominator) + ' approaches zero at the critical point, A = 2.'
      : study.inputs.model === 'symmetric' ? 'No miscibility gap at the baseline, so the binodal derivative is not defined. Compare the scenarios that gain a gap with those that do not.' : 'The closed-form derivative applies to symmetric Margules only. Use the finite one-factor changes.';
    $('effects-body').replaceChildren(...result.effects.map(e => { const tr = document.createElement('tr'); tr.append(cell(e.label), cell(e.accepted + ' / ' + e.attempted), cell(num(e.xAlpha)), cell(num(e.fractionBeta)), cell(e.phaseChange ? 'Yes' : 'No')); return tr; }));
    $('scenario-body').replaceChildren(...[...result.oneAtATime, ...result.corners].map(row => {
      const tr = document.createElement('tr'), inputs = result.keys.map(k => PARAMETER_LABELS[k] + ' = ' + num(row.inputs[k])).join(', ');
      tr.append(cell(row.label), cell(inputs), cell(row.status === 'finite' ? row.phase : 'Failed: ' + row.reason), cell(row.state || '—'), cell(num(row.xAlpha)), cell(num(row.xBeta)), cell(num(row.fractionBeta)));
      return tr;
    }));
    $('sensitivity-results').hidden = false;
    $('sensitivity-status').textContent = 'Ran ' + result.oneAtATime.length + ' one-at-a-time scenarios and ' + result.counts.total + ' signed corners around ' + modelText(study.inputs) + ', z₁ = ' + num(study.inputs.z) + '.';
  } catch (error) { $('sensitivity-status').textContent = 'The scenarios could not run: ' + error.message; $('sensitivity-results').hidden = true; }
}

function runMatch() {
  if (!study.result) return;
  try {
    const result = modelMatchStudy(study.inputs);
    study.match = { inputs: { ...study.inputs }, result };
    $('match-body').replaceChildren(...result.rows.map(row => {
      const tr = document.createElement('tr');
      tr.append(cell(row.label), cell(row.note || '—'), cell(row.status === 'finite' ? row.phase : 'Failed: ' + row.reason), cell(num(row.xAlpha)), cell(num(row.xBeta)), cell(num(row.fractionBeta)));
      return tr;
    }));
    $('match-wrap').hidden = false;
    $('match-status').textContent = 'Every candidate reproduces ln γ₁∞ = ' + num(result.lnInf[0], 5) + ' and ln γ₂∞ = ' + num(result.lnInf[1], 5) + '. Predicted phases at z₁ = ' + num(result.z) + ': ' + result.phases.join(' and ') + '.';
  } catch (error) { $('match-status').textContent = 'The comparison could not run: ' + error.message; }
}

function notes() { return Object.fromEntries(Object.entries(NOTE_IDS).map(([key, id]) => [key, $(id).value])); }

function checkEvidence() {
  const result = evidenceCheck({ audit: study.audit, sensitivity: study.sensitivity, match: study.match, notes: notes() });
  $('evidence-status').textContent = result.complete ? 'All sections and calculations are present. Scientific reasoning still needs instructor review.' : result.issues.join(' ');
}

function saveCase() {
  if (!study.result) return;
  const r = study.result, name = $('case-name').value.trim() || 'Case ' + (study.cases.length + 1);
  study.cases.push({ name, inputs: { ...study.inputs }, summary: { phase: r.phase, state: r.state, xAlpha: r.gapAlpha, xBeta: r.gapBeta, fractionBeta: r.fractionBeta, gain: r.gain } });
  renderCases(); $('status').textContent = 'Saved “' + name + '”. Change one setting, calculate, then save the next case.';
}

function renderCases() {
  $('comparison-empty').hidden = study.cases.length > 0; $('comparison-table-wrap').hidden = !study.cases.length;
  $('comparison-body').replaceChildren(...study.cases.map((saved, index) => {
    const tr = document.createElement('tr'), s = saved.summary, two = s.phase === 'two liquids';
    tr.append(cell(saved.name), cell(modelText(saved.inputs)), cell(num(saved.inputs.z)), cell(s.state), cell(s.phase), cell(num(s.xAlpha)), cell(num(s.xBeta)), cell(two ? num(s.fractionBeta) : '—'), cell(exp(s.gain)));
    const td = document.createElement('td'), button = document.createElement('button');
    button.type = 'button'; button.className = 'secondary-button'; button.textContent = 'Reopen'; button.setAttribute('aria-label', 'Reopen ' + saved.name);
    button.addEventListener('click', () => { applyInputs(saved.inputs); $('case-name').value = saved.name; calculate({ quiet: true }); $('status').textContent = 'Reopened and recalculated “' + saved.name + '”.'; $('results').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    td.append(button); tr.append(td); return tr;
  }));
}

function loadCase(id) {
  const preset = CASES[id]; if (!preset) return;
  applyInputs(preset.inputs); $('case-name').value = preset.name;
  for (const button of document.querySelectorAll('[data-case]')) button.setAttribute('aria-pressed', String(button.dataset.case === id));
  $('case-description').textContent = 'A 1.00 mol binary liquid feed at fixed temperature and pressure follows the symmetric Margules model with A = ' + num(preset.inputs.A) + '. The feed contains ' + num(preset.inputs.z) + ' mol of component 1.';
  $('status').textContent = preset.name + ' loaded. Make a prediction, then press Calculate equilibrium.';
}

function exportStudy() {
  const record = {
    schema: SCHEMA, engineVersion: engine.STABILITY_VERSION, graduateVersion: STABILITY_GRADUATE_VERSION, savedAt: new Date().toISOString(),
    inputs: study.inputs || readInputs().inputs, predictions: { equilibrium: $('prediction').value, local: $('prediction-local').value },
    caseName: $('case-name').value, cases: study.cases, bounds: readBounds(), notes: notes(), reflection: $('reflection').value,
    investigations: { audit: Boolean(study.audit), sensitivity: Boolean(study.sensitivity), match: Boolean(study.match) }, source: study.source,
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], { type: 'application/json' })), a = document.createElement('a');
  a.href = url; a.download = 'lab04-liquid-stability-study.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('status').textContent = 'Study downloaded. Open it later to restore the cases, settings and notes.';
}

function validInputs(inputs) {
  if (!inputs || !MODELS.includes(inputs.model)) return false;
  return [...PARAMETER_KEYS[inputs.model], 'z'].every(key => Number.isFinite(inputs[key]) && inputs[key] >= RANGES[key][0] && inputs[key] <= RANGES[key][1]);
}

async function openStudy(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2e6) throw new Error('The file is larger than a Lab 04 study.');
    const record = JSON.parse(await file.text());
    if (record.schema !== SCHEMA) throw new Error('This file is not a Lab 04 (2027) study.');
    if (!validInputs(record.inputs)) throw new Error('The saved inputs are invalid.');
    const cases = Array.isArray(record.cases) ? record.cases.filter(saved => validInputs(saved?.inputs) && typeof saved.name === 'string').slice(0, 50) : [];
    applyInputs(record.inputs); buildBounds(record.bounds || {});
    $('prediction').value = record.predictions?.equilibrium || ''; $('prediction-local').value = record.predictions?.local || '';
    $('case-name').value = typeof record.caseName === 'string' ? record.caseName.slice(0, 80) : '';
    for (const [key, id] of Object.entries(NOTE_IDS)) $(id).value = typeof record.notes?.[key] === 'string' ? record.notes[key] : '';
    $('reflection').value = typeof record.reflection === 'string' ? record.reflection : '';
    study.cases = cases.map(saved => { const s = solve(saved.inputs); return { name: saved.name.slice(0, 80), inputs: saved.inputs, summary: { phase: s.phase, state: s.state, xAlpha: s.gapAlpha, xBeta: s.gapBeta, fractionBeta: s.fractionBeta, gain: s.gain } }; });
    study.source = record.source || null; study.inputs = null;
    renderCases(); calculate({ quiet: true });
    if (record.investigations?.audit) runAudit();
    if (record.investigations?.sensitivity) runSensitivity();
    if (record.investigations?.match) runMatch();
    $('status').textContent = 'Study reopened. ' + study.cases.length + ' saved cases and the investigations were recalculated from the saved inputs.';
  } catch (error) { $('status').textContent = 'The study could not be opened: ' + error.message; }
  finally { event.target.value = ''; }
}

function importFromQuery() {
  const q = new URLSearchParams(location.search);
  if (q.get('model') !== 'nrtl') return false;
  const inputs = { model: 'nrtl', tau12: Number(q.get('tau12')), tau21: Number(q.get('tau21')), alpha: Number(q.get('alpha')), z: q.has('z') ? Number(q.get('z')) : 0.5 };
  if (!validInputs(inputs)) { $('import-note').textContent = 'The imported NRTL parameters are outside the supported range, so the starting case was kept.'; $('import-note').hidden = false; return false; }
  study.source = { from: q.get('from') || 'link', tau12: inputs.tau12, tau21: inputs.tau21, alpha: inputs.alpha };
  applyInputs(inputs); $('case-name').value = 'Imported NRTL fit · z₁ = ' + num(inputs.z);
  for (const button of document.querySelectorAll('[data-case]')) button.setAttribute('aria-pressed', 'false');
  $('case-description').textContent = 'A 1.00 mol binary liquid feed follows the imported NRTL parameters τ₁₂ = ' + num(inputs.tau12) + ', τ₂₁ = ' + num(inputs.tau21) + ' and α = ' + num(inputs.alpha) + '.';
  $('import-note').textContent = (q.get('from') === 'lab02' ? 'Parameters imported from your Lab 02 fit. ' : q.get('from') === 'lab05' ? 'Parameters imported from your Lab 05 tie-line fit. ' : 'Imported NRTL parameters. ') + 'They are constant τ values; this lab treats them at one fixed temperature. Check the liquid stability, then return to the named cases for the core investigation.';
  $('import-note').hidden = false;
  return true;
}

function init() {
  buildBounds(); showModelControls();
  for (const button of document.querySelectorAll('[data-case]')) button.addEventListener('click', () => loadCase(button.dataset.case));
  $('model').addEventListener('change', () => { showModelControls(); buildBounds(); });
  $('calculate').addEventListener('click', () => calculate());
  $('lle-form').addEventListener('submit', event => { event.preventDefault(); calculate(); });
  $('view').addEventListener('change', renderChart);
  $('save-case').addEventListener('click', saveCase);
  $('run-audit').addEventListener('click', runAudit);
  $('run-sensitivity').addEventListener('click', runSensitivity);
  $('run-match').addEventListener('click', runMatch);
  $('near-critical').addEventListener('click', () => { loadCase('near-critical'); calculate(); $('sensitivity-status').textContent = 'Near-critical case calculated. Run the same half-widths again.'; });
  $('check-evidence').addEventListener('click', checkEvidence);
  $('export-study').addEventListener('click', exportStudy);
  $('import-study').addEventListener('change', openStudy);
  if (!importFromQuery()) loadCase('baseline');
}

init();
