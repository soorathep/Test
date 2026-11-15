/** Small SVG charts for the 2105315 labs. Teal = reference, amber = the effect the step is about.
 * Every chart is a 760 x 300 viewBox; on phones the container scrolls sideways (.figure-scroll). */
const NS = 'http://www.w3.org/2000/svg';
const W = 760, H = 300, M = { l: 58, r: 18, t: 18, b: 44 };

function el(name, attrs = {}, text) {
  const node = document.createElementNS(NS, name);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}

function frame(svg, label) {
  svg.replaceChildren();
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', label);
}

function niceTicks(lo, hi, count = 5) {
  const span = hi - lo || 1, raw = span / count, mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw);
  const out = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9; v += step) out.push(+v.toFixed(10));
  return out;
}

function yAxis(svg, y, ticks, label, fmt = (v) => String(v)) {
  const g = el('g', { class: 'grid' }), a = el('g', { class: 'ax' });
  for (const v of ticks) {
    g.append(el('line', { x1: M.l, x2: W - M.r, y1: y(v), y2: y(v) }));
    a.append(el('text', { x: M.l - 8, y: y(v) + 4, 'text-anchor': 'end' }, fmt(v)));
  }
  a.append(el('line', { x1: M.l, x2: M.l, y1: M.t, y2: H - M.b }));
  a.append(el('text', { class: 'ax-label', x: 14, y: M.t + (H - M.t - M.b) / 2, transform: `rotate(-90 14 ${M.t + (H - M.t - M.b) / 2})`, 'text-anchor': 'middle' }, label));
  svg.append(g, a);
}

/** CO(GT) over the window. mode 'recorded' plots -200 as a number; 'missing' leaves a gap and marks a rug. */
export function coChart(svg, points, mode) {
  const n = points.length;
  const valid = points.filter((p) => !p.missing).map((p) => p.value);
  const top = Math.max(1, ...valid) * 1.08;
  const lo = mode === 'recorded' ? -210 : 0;
  const x = (k) => M.l + (k / Math.max(1, n - 1)) * (W - M.l - M.r);
  const y = (v) => M.t + (1 - (v - lo) / (top - lo)) * (H - M.t - M.b);
  frame(svg, mode === 'recorded'
    ? 'CO(GT) over 14 days with the -200 code plotted as if it were a concentration. The line drops to -200 at every missing hour.'
    : 'CO(GT) over 14 days with -200 treated as missing. The line breaks at missing hours, which are marked on the time axis.');
  const ticks = mode === 'recorded' ? [-200, -150, -100, -50, 0] : niceTicks(0, top, 5);
  yAxis(svg, y, ticks, 'CO(GT) / mg m⁻³');
  const ax = el('g', { class: 'ax' });
  ax.append(el('line', { x1: M.l, x2: W - M.r, y1: H - M.b, y2: H - M.b }));
  points.forEach((p, k) => {
    if (p.hour === 0) {
      ax.append(el('line', { x1: x(k), x2: x(k), y1: H - M.b, y2: H - M.b + 5 }));
      if (k + 24 <= n) ax.append(el('text', { x: x(k + 12), y: H - M.b + 18, 'text-anchor': 'middle' }, p.date.slice(0, 5)));
    }
  });
  svg.append(ax);
  if (mode === 'recorded') svg.append(el('line', { class: 'zero-line', x1: M.l, x2: W - M.r, y1: y(0), y2: y(0) }));
  let d = '', pen = false;
  points.forEach((p, k) => {
    if (mode === 'missing' && p.missing) { pen = false; return; }
    const v = p.missing ? -200 : p.value;
    d += `${pen ? 'L' : 'M'}${x(k).toFixed(1)},${y(v).toFixed(1)}`; pen = true;
  });
  svg.append(el('path', { class: 'series-ref', d }));
  const marks = el('g');
  points.forEach((p, k) => {
    if (!p.missing) return;
    if (mode === 'recorded') marks.append(el('circle', { class: 'pt-missing', cx: x(k), cy: y(-200), r: 3.2 }));
    else marks.append(el('line', { class: 'rug-missing', x1: x(k), x2: x(k), y1: H - M.b - 1, y2: H - M.b - 9 }));
  });
  svg.append(marks);
}

/** Share of hours at -200 for each hour of the day: amber bars for the student's window, teal outline for the year. */
export function hoursChart(svg, mine, year) {
  frame(svg, 'Share of hours with CO(GT) missing, by hour of the day. Bars: your 14 days. Outlined bars: the whole year.');
  const top = Math.max(0.1, ...mine, ...year) * 1.1;
  const bw = (W - M.l - M.r) / 24;
  const y = (v) => M.t + (1 - v / top) * (H - M.t - M.b);
  yAxis(svg, y, niceTicks(0, top, 4), 'share missing', (v) => `${Math.round(v * 100)}%`);
  const ax = el('g', { class: 'ax' });
  ax.append(el('line', { x1: M.l, x2: W - M.r, y1: H - M.b, y2: H - M.b }));
  for (let h = 0; h < 24; h += 2) ax.append(el('text', { x: M.l + bw * (h + 0.5), y: H - M.b + 18, 'text-anchor': 'middle' }, String(h).padStart(2, '0')));
  ax.append(el('text', { class: 'ax-label', x: M.l + (W - M.l - M.r) / 2, y: H - 6, 'text-anchor': 'middle' }, 'hour of day (local time)'));
  svg.append(ax);
  mine.forEach((v, h) => svg.append(el('rect', { class: 'bar-effect', x: M.l + bw * h + bw * 0.22, y: y(v), width: bw * 0.56, height: Math.max(0, H - M.b - y(v)) })));
  year.forEach((v, h) => svg.append(el('rect', { class: 'bar-ref', x: M.l + bw * h + bw * 0.12, y: y(v), width: bw * 0.76, height: Math.max(0, H - M.b - y(v)) })));
}

/** Daily mean CO(GT): filled teal = reported, open = below the minimum number of valid hours. */
export function dailyChart(svg, days) {
  frame(svg, 'Daily mean CO(GT). Filled points are days with enough valid hours to report; open points are days below the minimum; dashed squares are days with no valid hour.');
  const vals = days.filter((d) => Number.isFinite(d.mean)).map((d) => d.mean);
  const top = Math.max(1, ...vals) * 1.15;
  const step = (W - M.l - M.r) / days.length;
  const y = (v) => M.t + (1 - v / top) * (H - M.t - M.b);
  yAxis(svg, y, niceTicks(0, top, 4), 'daily mean CO / mg m⁻³');
  const ax = el('g', { class: 'ax' });
  ax.append(el('line', { x1: M.l, x2: W - M.r, y1: H - M.b, y2: H - M.b }));
  days.forEach((d, k) => {
    const cx = M.l + step * (k + 0.5);
    if (k % 2 === 0) ax.append(el('text', { x: cx, y: H - M.b + 18, 'text-anchor': 'middle' }, `${d.day.slice(8, 10)}/${d.day.slice(5, 7)}`));
    if (!Number.isFinite(d.mean)) {
      svg.append(el('rect', { class: 'day-empty', x: cx - 5, y: H - M.b - 12, width: 10, height: 10 }));
      svg.append(el('text', { class: 'ax-label', x: cx, y: H - M.b - 18, 'text-anchor': 'middle' }, '0h'));
      return;
    }
    svg.append(el('circle', { class: d.reported ? 'day-reported' : 'day-dropped', cx, cy: y(d.mean), r: 5.5 }));
    svg.append(el('text', { class: 'ax-label', x: cx, y: y(d.mean) - 10, 'text-anchor': 'middle' }, `${d.valid}h`));
  });
  svg.append(ax);
}
