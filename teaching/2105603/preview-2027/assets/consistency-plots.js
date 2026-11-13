/** Method-specific visual evidence. Criteria are aggregate claims, not pointwise bands. */
import { palette } from '../../labs/assets/palette.js';
import { analyze } from './consistency-graduate.js';

const methods = ['area', 'herington', 'differential', 'model'];
const $ = id => document.getElementById(id);
const num = (value, digits = 6) => value == null || !Number.isFinite(value) ? 'undefined' : Number(value).toLocaleString('en-US', { maximumSignificantDigits: digits });
let renderEpoch = 0;
const sizeWatchers = new Map();
const plotId = method => 'c3-' + method + '-plot';
const plotConfig = { responsive: true, displayModeBar: false };

function scheduleResize(record, force = false) {
  record.force = record.force || force;
  if (record.frame !== null || !window.Plotly?.Plots?.resize) return;
  const schedule = typeof window.requestAnimationFrame === 'function'
    ? callback => window.requestAnimationFrame(callback) : callback => setTimeout(callback, 0);
  record.frame = schedule(() => {
    record.frame = null;
    const width = record.target.clientWidth, forced = record.force;
    record.force = false;
    if (width <= 0) { record.lastWidth = 0; return; }
    if (record.target.dataset.methodPlotState !== 'ready') return;
    if (!forced && Math.abs(width - record.lastWidth) < 1) return;
    // Record width before resizing, so height-only observer callbacks do not loop.
    record.lastWidth = width;
    try { Promise.resolve(window.Plotly.Plots.resize(record.target)).catch(() => {}); }
    catch { /* The numerical tables remain available if a hidden plot cannot resize. */ }
  });
}
function watchSize(target) {
  let record = sizeWatchers.get(target);
  if (!record) {
    record = { target, lastWidth: 0, frame: null, force: false, observer: null };
    if (typeof ResizeObserver === 'function') {
      record.observer = new ResizeObserver(entries => {
        const entry = entries.find(item => item.target === target);
        if (!entry) return;
        const width = Math.round(entry.contentRect.width);
        if (width <= 0) { record.lastWidth = 0; return; }
        if (Math.abs(width - record.lastWidth) >= 1) scheduleResize(record);
      });
      record.observer.observe(target);
    }
    sizeWatchers.set(target, record);
  }
  // Plotly.react may retain a previous fullLayout width. Reconcile once per draw.
  scheduleResize(record, true);
}

function line(x, y, name, color = palette.teal, dash = 'solid', mode = 'lines') {
  return { x, y, name, mode, line: { color, width: 2, dash },
    marker: { color, size: 6 }, connectgaps: false };
}
function commonLayout(container, yTitle, height = 360) {
  const narrow = container.clientWidth > 0 && container.clientWidth < 400;
  return { autosize: true, height, margin: { l: narrow ? 63 : 75, r: 14, t: 14, b: 68 },
    font: { family: 'Source Sans 3, sans-serif', color: palette.graphite, size: 13 },
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent', showlegend: false,
    xaxis: { title: { text: 'x<sub>1</sub> / mol mol<sup>−1</sup>', standoff: 14 },
      zeroline: false, automargin: true, nticks: narrow ? 4 : 6,
      gridcolor: palette.mist, linecolor: palette.graphite, linewidth: 2 },
    yaxis: { title: { text: yTitle, standoff: 10 }, zeroline: true,
      zerolinecolor: palette.graphite, zerolinewidth: 2, automargin: true, nticks: 5,
      gridcolor: palette.mist, linecolor: palette.graphite, linewidth: 2 },
    hovermode: 'closest' };
}
function legend(method, entries) {
  const target = $(plotId(method) + '-legend');
  if (!target) return;
  target.replaceChildren(...entries.map(entry => {
    const item = document.createElement('span'), swatch = document.createElement('i');
    swatch.style.borderColor = entry.color || palette.teal;
    swatch.style.borderTopStyle = entry.dash === 'dash' ? 'dashed' : 'solid';
    if (entry.fill) {
      swatch.style.borderTopWidth = '8px'; swatch.style.borderColor = palette.sand;
    }
    item.append(swatch, document.createTextNode(entry.label)); return item;
  }));
}
function message(method, text) {
  const target = $(plotId(method));
  if (!target) return;
  if (window.Plotly) window.Plotly.purge(target);
  const p = document.createElement('p'); p.className = 'method-plot-empty'; p.textContent = text;
  target.replaceChildren(p); target.dataset.methodPlotState = 'message';
  const watcher = sizeWatchers.get(target); if (watcher) watcher.lastWidth = 0;
  legend(method, []);
}
async function draw(method, traces, layout, entries, caption, epoch) {
  const target = $(plotId(method)), note = $(plotId(method) + '-note');
  if (!target || epoch !== renderEpoch) return;
  if (note) note.textContent = caption;
  if (!window.Plotly) {
    message(method, 'The optional plotting library is unavailable. Use the numerical observations, method scores and residual tables to inspect this evidence.');
    return;
  }
  try {
    // Purged/message containers can retain their explanatory paragraph when
    // Plotly appends a new graph. Remove only that direct placeholder child.
    for (const child of Array.from(target.children)) {
      if (child.className === 'method-plot-empty') child.remove();
    }
    await window.Plotly.react(target, traces, layout, plotConfig);
    if (epoch !== renderEpoch) return;
    target.dataset.methodPlotState = 'ready'; legend(method, entries); watchSize(target);
  } catch {
    if (epoch !== renderEpoch) return;
    message(method, 'This plot could not be drawn. The numerical observations, scores and residuals remain available in the tables.');
  }
}

/** Split the piecewise-linear curve at every sign change before shading it. */
function zeroSplit(points) {
  const result = [];
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    if (i) {
      const previous = points[i - 1];
      if (previous.f * p.f < 0) {
        const fraction = Math.abs(previous.f) / (Math.abs(previous.f) + Math.abs(p.f));
        result.push({ x: previous.x + fraction * (p.x - previous.x), f: 0 });
      }
    }
    result.push({ x: p.x, f: p.f });
  }
  return result;
}
async function areaPlot({ analysis, settings, data }, epoch) {
  const { set, area } = analysis, id = plotId('area'), target = $(id); if (!target) return;
  const split = zeroSplit(area.points), x = split.map(p => p.x);
  const traces = [
    { ...line(x, split.map(p => Math.max(p.f, 0)), 'Positive area magnitude A+', palette.sand),
      line: { width: 0, color: palette.sand }, fill: 'tozeroy', fillcolor: palette.sand,
      opacity: 0.55, hoverinfo: 'skip' },
    { ...line(x, split.map(p => Math.min(p.f, 0)), 'Negative area magnitude A−', palette.sand),
      line: { width: 0, color: palette.sand }, fill: 'tozeroy', fillcolor: palette.sand,
      opacity: 0.55, hoverinfo: 'skip' },
  ];
  const entries = [{ label: 'Positive and negative areas', color: palette.sand, fill: true }];
  if (set.synthetic && settings.scenario !== 'clean' && data) {
    const control = analyze({ ...settings, scenario: 'clean' }, data).set;
    traces.push(line(control.valid.map(r => r.x), control.valid.map(r => r.f), 'Consistent control', palette.teal));
    entries.push({ label: 'Consistent control', color: palette.teal });
  }
  if (area.conditional) {
    traces.push(line(area.points.map(r => r.x), area.points.map(r => r.f), 'Assumed full-range curve', palette.amber, 'dash'));
    traces.push(line(set.valid.map(r => r.x), set.valid.map(r => r.f), 'Original inferred points', palette.teal, 'solid', 'markers'));
    entries.push({ label: 'Assumed full-range curve', color: palette.amber, dash: 'dash' }, { label: 'Original inferred points', color: palette.teal });
  } else {
    const color = set.synthetic && settings.scenario !== 'clean' ? palette.amber : palette.teal;
    const name = set.synthetic ? 'Generated log ratio' : 'Inferred log ratio on measured interval';
    traces.push(line(set.valid.map(r => r.x), set.valid.map(r => r.f), name, color, 'solid', 'lines+markers'));
    entries.push({ label: name, color });
  }
  const caption = 'A+ = ' + num(area.area.positive) + '; A− (magnitude) = ' + num(area.area.negative)
    + '; I = ' + num(area.area.signed) + '; D = ' + num(area.area.D) + '%. '
    + (area.conditional ? 'Shading integrates the assumed full-range curve, not new measurements. The quadratic option also smooths the measured interval. '
      : area.full ? 'The full-range synthetic curve uses supplied endpoint limits. ' : 'Shading covers the included measured interval only; missing endpoint areas are not supplied. ')
    + (set.path === 'isothermal' ? 'A small signed area can conceal positive and negative errors that cancel.' : 'This is an isobaric path. Use the Herington assumption and applicability discussion below, not an isothermal zero-area verdict.');
  await draw('area', traces, commonLayout(target, 'ln(γ<sub>1</sub>/γ<sub>2</sub>)'), entries, caption, epoch);
}

async function heringtonPlot({ analysis }, epoch) {
  const { set, area } = analysis, target = $(plotId('herington')); if (!target) return;
  const all = set.rows.filter(r => Number.isFinite(r.T)), low = Math.min(...all.map(r => r.T)), high = Math.max(...all.map(r => r.T));
  const usable = all.filter(r => r.ln), excluded = all.filter(r => !r.ln);
  const traces = [line(usable.map(r => r.x), usable.map(r => r.T), 'States usable for activity inference', palette.teal, 'solid', 'lines+markers')];
  const entries = [{ label: 'States usable for activity inference', color: palette.teal }];
  if (excluded.length) {
    const t = line(excluded.map(r => r.x), excluded.map(r => r.T), 'Excluded activity pairs; T retained for range', palette.graphite, 'solid', 'markers');
    t.marker.symbol = 'circle-open'; traces.push(t); entries.push({ label: 'Excluded activity pairs; T retained for range', color: palette.graphite });
  }
  const layout = commonLayout(target, 'Temperature T / K');
  layout.shapes = [low, high].filter((v, i, a) => !i || Math.abs(v - a[0]) > 1e-9).map(T => ({ type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: T, y1: T,
    line: { color: palette.graphite, width: 2, dash: 'dash' } }));
  entries.push({ label: Math.abs(high - low) > 1e-9 ? 'Minimum and maximum T' : 'Constant T', color: palette.graphite, dash: 'dash' });
  let caption = 'Tmin = ' + num(low) + ' K; Tmax = ' + num(high) + ' K; J = 150(Tmax − Tmin)/Tmin = ' + num(area.J) + '. ';
  if (set.path === 'isothermal') caption += 'Herington is not applicable to this fixed-temperature path; a flat T curve is not a passed isobaric test.';
  else {
    caption += 'The temperature range includes every original or generated state, including rows excluded from activity inference. D = ' + num(area.area.D) + '%; D − J = ' + num(area.DminusJ) + '. ';
    caption += !area.full ? 'The area is partial, so no full-range Herington verdict is assigned. ' : area.conditional ? 'The Herington result is conditional on the assumed endpoint curve. ' : '';
    caption += 'J is an empirical boiling-range allowance, not a measured Hᴱ correction.';
  }
  await draw('herington', traces, layout, entries, caption, epoch);
}

async function differentialPlot({ analysis, settings }, epoch) {
  const { set, local } = analysis, target = $(plotId('differential')); if (!target) return;
  const x = local.points.map(r => r.x), corrected = set.path === 'isobaric' && set.synthetic && settings.heat;
  const traces = [line(x, local.points.map(r => r.raw), set.path === 'isothermal' ? 'Residual r at fixed T' : 'Raw residual without heat term', palette.teal, 'solid', 'lines+markers')];
  const entries = [{ label: traces[0].name, color: palette.teal }];
  if (corrected) {
    traces.push(line(x, local.points.map(r => r.residual), 'Residual with supplied synthetic Hᴱ term', palette.amber, 'solid', 'lines+markers'));
    entries.push({ label: traces[1].name, color: palette.amber });
  }
  const peak = Math.max(...local.points.map(r => Math.abs(r.residual)));
  const caption = '100 mean |r| = ' + num(local.score) + '; maximum |r| = ' + num(peak) + '. '
    + (local.assessed ? 'The teaching criterion compares the mean score with 5; it does not impose a pointwise residual band. ' : 'The required isobaric heat correction is unavailable or disabled: the raw curve is descriptive and no differential consistency verdict is assigned. ')
    + 'The zero line is a reference. A narrow defect can be visible even when an average meets its threshold; numerical derivatives also depend on sampling resolution.';
  await draw('differential', traces, commonLayout(target, 'Dimensionless local residual r'), entries, caption, epoch);
}

async function modelPlot({ model }, epoch) {
  const method = 'model', target = $(plotId(method)); if (!target) return;
  if (!model) {
    message(method, 'Run the NRTL modeling test for this calculated case to see pressure and vapor-composition residuals.');
    const note = $(plotId(method) + '-note'); if (note) note.textContent = 'No fitted-model residuals are available yet. Area and differential calculations do not supply this fit.';
    return;
  }
  const x = model.points.map(r => r.x), traces = [
    { ...line(x, model.points.map(r => r.pressureResidual), 'Pressure residual 100 ΔP/P', palette.amber, 'solid', 'lines+markers'), xaxis: 'x', yaxis: 'y', hovertemplate: 'x₁ = %{x:.5f}<br>100 ΔP/P = %{y:.5f}%<extra></extra>' },
    { ...line(x, model.points.map(r => r.yResidual / 100), 'Vapor-composition residual Δy', palette.amber, 'dash', 'lines+markers'), xaxis: 'x2', yaxis: 'y2', hovertemplate: 'x₁ = %{x:.5f}<br>Δy = %{y:.6f} mol/mol<extra></extra>' },
  ];
  const layout = commonLayout(target, '100 ΔP/P / %', 480);
  layout.margin = { ...layout.margin, b: 68, t: 16 };
  layout.xaxis = { ...layout.xaxis, domain: [0, 1], anchor: 'y', title: undefined, showticklabels: true };
  layout.yaxis = { ...layout.yaxis, domain: [0.59, 1], anchor: 'x' };
  layout.xaxis2 = { ...layout.xaxis, domain: [0, 1], anchor: 'y2', title: { text: 'x<sub>1</sub> / mol mol<sup>−1</sup>', standoff: 14 } };
  layout.yaxis2 = { ...layout.yaxis, domain: [0, 0.41], anchor: 'x2', title: { text: 'Δy / mol mol<sup>−1</sup>', standoff: 10 } };
  const caption = 'Residuals are model minus observation. The separate vertical axes retain pressure percent and vapor-composition mol/mol. Mean |100 ΔP/P| = '
    + num(model.deltaP) + '%; mean |Δy| = ' + num(model.deltaY / 100) + ' mol/mol. The criteria apply to these means (< 1% and < 0.01 mol/mol), not to every individual point. '
    + (model.atBound ? 'At least one parameter is at a bound. ' : '')
    + 'Reproduction by this chosen NRTL fit does not certify the experimental data or identify the cause of a discrepancy.';
  await draw(method, traces, layout, [
    { label: 'Pressure residual (%)', color: palette.amber },
    { label: 'Vapor-composition residual (mol/mol)', color: palette.amber, dash: 'dash' },
  ], caption, epoch);
}

export async function renderMethodPlots(input) {
  const epoch = ++renderEpoch;
  if (!input?.analysis) { clearMethodPlots(); return; }
  const context = { ...input, settings: input.settings || input.analysis.settings };
  await Promise.all([
    areaPlot(context, epoch), heringtonPlot(context, epoch),
    differentialPlot(context, epoch), modelPlot(context, epoch),
  ]);
}

export function clearMethodPlots() {
  ++renderEpoch;
  for (const method of methods) {
    message(method, 'Calculate a current case in Step 1 to inspect this method.');
    const note = $(plotId(method) + '-note'); if (note) note.textContent = '';
  }
}
