// Lab 02 Graduate step G3: weight each ln-gamma residual by its propagated measurement uncertainty.
// sigma(ln g1)^2 = (u_x/x)^2 + (u_y/y)^2 + (u_P/P)^2 + (dlnPsat1/dT * u_T)^2, and the same for
// component 2 with 1-x and 1-y. Standard uncertainties u = U/k from the article's average expanded
// uncertainties (k = 2). Two NRTL parameters (alpha fixed) are fitted by Levenberg-Marquardt, unweighted
// and weighted, from the same starts. Parameter standard deviations and their correlation come from the
// linearized covariance at the minimum. Saved in the study file under "weighted".
import * as engine from '../../labs/assets/case-study.js';

const $ = (id) => document.getElementById(id);
const fmt = (v, d = 3) => (Number.isFinite(v) ? v.toFixed(d) : '—');
const C = { teal: '#0F6E6B', amber: '#E29A2D', sand: '#DFC98F', ink: '#1C242B', graphite: '#333F4A', slate: '#66727C', mist: '#B9C1C6' };
let data = null, last = null;

export function points(dataset, d, xmin = 0) {
  const k = dataset.coverageFactor || 2, U = dataset.averageExpandedUncertainty;
  const u = { x: U.x / k, y: U.y / k, P: U.PkPa / k, T: U.T / k };
  const out = [];
  for (const row of dataset.rows) {
    const r = engine.infer(row, d);
    if (!r.ln || row.x < xmin) continue;
    const P = row.PkPa, { x, y, T } = row;
    const dlnps = d.properties.map((c) => Math.LN10 * c.B / (T + c.C) ** 2);
    const s1 = Math.hypot(u.x / x, u.y / y, u.P / P, dlnps[0] * u.T);
    const s2 = Math.hypot(u.x / (1 - x), u.y / (1 - y), u.P / P, dlnps[1] * u.T);
    out.push({ x, y, T, P, ln: r.ln, s: [s1, s2] });
  }
  return { rows: out, u };
}

function residuals(p, pts, alpha, weighted) {
  const r = [];
  for (const q of pts) {
    const m = engine.nrtl(q.x, q.T, { alpha, a12: p[0], a21: p[1], b12: 0, b21: 0 }).ln;
    r.push((m[0] - q.ln[0]) / (weighted ? q.s[0] : 1), (m[1] - q.ln[1]) / (weighted ? q.s[1] : 1));
  }
  return r;
}
const ss = (r) => r.reduce((a, v) => a + v * v, 0);

function jacobian(p, pts, alpha, weighted) {
  const r0 = residuals(p, pts, alpha, weighted), h = 1e-6;
  const cols = [0, 1].map((j) => { const q = [...p]; q[j] += h; return residuals(q, pts, alpha, weighted).map((v, i) => (v - r0[i]) / h); });
  return { r0, J: r0.map((_, i) => [cols[0][i], cols[1][i]]) };
}

function lm(pts, alpha, weighted, start) {
  let p = [...start], lambda = 1e-3, f = ss(residuals(p, pts, alpha, weighted)), converged = false;
  for (let it = 0; it < 300; it++) {
    const { r0, J } = jacobian(p, pts, alpha, weighted);
    let a = 0, b = 0, c = 0, g0 = 0, g1 = 0;
    J.forEach((row, i) => { a += row[0] * row[0]; b += row[0] * row[1]; c += row[1] * row[1]; g0 += row[0] * r0[i]; g1 += row[1] * r0[i]; });
    let improved = false;
    for (let k = 0; k < 30; k++) {
      const A = a * (1 + lambda), Cc = c * (1 + lambda), det = A * Cc - b * b;
      const step = [-(Cc * g0 - b * g1) / det, -(A * g1 - b * g0) / det];
      const q = [p[0] + step[0], p[1] + step[1]].map((v) => Math.max(-3, Math.min(8, v)));
      const fq = ss(residuals(q, pts, alpha, weighted));
      if (fq < f) {
        const done = Math.hypot(q[0] - p[0], q[1] - p[1]) < 1e-10 || (f - fq) < 1e-14 * (1 + f);
        p = q; f = fq; lambda = Math.max(lambda / 10, 1e-12); improved = true;
        if (done) converged = true;
        break;
      }
      lambda *= 10;
    }
    if (!improved || converged) { converged = true; break; }
  }
  return { p, f, converged };
}

export function fitPair(pts, alpha, weighted) {
  let best = null;
  for (const s of [[0, 0], [0.5, 2], [2, 0.5], [4, -0.5], [-0.5, 4]]) {
    const r = lm(pts, alpha, weighted, s);
    if (r.converged && (!best || r.f < best.f)) best = r;
  }
  if (!best) throw new Error('The fit did not converge from any start.');
  const { J } = jacobian(best.p, pts, alpha, weighted);
  let a = 0, b = 0, c = 0;
  J.forEach((row) => { a += row[0] * row[0]; b += row[0] * row[1]; c += row[1] * row[1]; });
  const det = a * c - b * b, n = 2 * pts.length;
  const scale = weighted ? 1 : best.f / (n - 2);           // unweighted: residual variance estimated from the fit
  const cov = [[c / det * scale, -b / det * scale], [-b / det * scale, a / det * scale]];
  const sd = [Math.sqrt(cov[0][0]), Math.sqrt(cov[1][1])];
  const atBound = best.p.some((v) => v <= -3 + 1e-6 || v >= 8 - 1e-6);
  const curvature = engine.modelCheck({ alpha, a12: best.p[0], a21: best.p[1], b12: 0, b21: 0 }).minSampledScaledCurvature;
  return { tau: best.p, sd, corr: cov[0][1] / (sd[0] * sd[1]), atBound, curvature };
}

export function score(tau, pts, alpha) {
  const r = residuals(tau, pts, alpha, false), w = residuals(tau, pts, alpha, true);
  return { rmse: Math.sqrt(ss(r) / r.length), rmsz: Math.sqrt(ss(w) / w.length), n: pts.length };
}

export function analyze(d, train, xmin, alpha = 0.47) {
  const sets = Object.fromEntries(d.datasets.map((ds) => [ds.pressureKPa, points(ds, d, xmin)]));
  const all = Object.fromEntries(d.datasets.map((ds) => [ds.pressureKPa, points(ds, d, 0)]));
  const tr = train === 'both' ? [...sets[60].rows, ...sets[80].rows] : sets[Number(train)].rows;
  if (tr.length < 3) throw new Error('Fewer than three observations remain in the training set.');
  const fits = { unweighted: fitPair(tr, alpha, false), weighted: fitPair(tr, alpha, true) };
  const scores = {};
  for (const key of Object.keys(fits)) scores[key] = { 60: score(fits[key].tau, all[60].rows, alpha), 80: score(fits[key].tau, all[80].rows, alpha) };
  return { train, xmin, alpha, nTrain: tr.length, fits, scores, all, u: { 60: sets[60].u, 80: sets[80].u } };
}

function plot(res, P) {
  const svg = $('wf-plot');
  const W = 680, H = 300, L = 62, R = 16, T = 18, B = 46, lim = 1.2;
  const pts = res.all[P].rows;
  const X = (x) => L + (Math.log10(x) + 2.4) / 2.4 * (W - L - R);
  const Y = (v) => T + (lim - Math.max(-lim, Math.min(lim, v))) / (2 * lim) * (H - T - B);
  const mk = (key) => pts.map((q) => engine.nrtl(q.x, q.T, { alpha: res.alpha, a12: res.fits[key].tau[0], a21: res.fits[key].tau[1] }).ln[0] - q.ln[0]);
  const ru = mk('unweighted'), rw = mk('weighted');
  const bars = pts.map((q) => `<rect x="${X(q.x) - 4}" y="${Y(2 * q.s[0])}" width="8" height="${Y(-2 * q.s[0]) - Y(2 * q.s[0])}" fill="${C.sand}" opacity=".7"/>`).join('');
  const dots = pts.map((q, i) => `<circle cx="${X(q.x)}" cy="${Y(ru[i])}" r="5" fill="${C.teal}"/>${Math.abs(ru[i]) > lim ? `<text x="${X(q.x) + 7}" y="${Y(ru[i]) + 4}" fill="${C.teal}" font-size="11">${ru[i].toFixed(2)}</text>` : ''}`).join('');
  const dia = pts.map((q, i) => { const cx = X(q.x), cy = Y(rw[i]); return `<path d="M${cx},${cy - 6}L${cx + 6},${cy}L${cx},${cy + 6}L${cx - 6},${cy}Z" fill="${C.amber}" stroke="#fff" stroke-width="1"/>`; }).join('');
  const xt = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1].map((t) => `<line x1="${X(t)}" x2="${X(t)}" y1="${H - B}" y2="${H - B + 5}" stroke="${C.graphite}"/><text x="${X(t)}" y="${H - B + 19}" text-anchor="middle">${t}</text>`).join('');
  const yt = [-1, -0.5, 0, 0.5, 1].map((t) => `<text x="${L - 8}" y="${Y(t) + 4}" text-anchor="end">${t}</text><line x1="${L}" x2="${W - R}" y1="${Y(t)}" y2="${Y(t)}" stroke="${C.mist}" stroke-width="${t === 0 ? 1.4 : 0.6}"/>`).join('');
  svg.innerHTML = `${yt}${bars}
    <line x1="${L}" x2="${L}" y1="${T}" y2="${H - B}" stroke="${C.graphite}"/><line x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}" stroke="${C.graphite}"/>
    ${xt}${dots}${dia}
    <text x="${(L + W - R) / 2}" y="${H - 6}" text-anchor="middle" fill="${C.ink}">x₁ (log scale) · ${P} kPa data</text>
    <text transform="translate(16 ${(T + H - B) / 2}) rotate(-90)" text-anchor="middle" fill="${C.ink}">model − measured ln γ₁</text>
    <rect x="${W - R - 260}" y="${T + 2}" width="256" height="58" fill="#fff" opacity=".9"/>
    <circle cx="${W - R - 246}" cy="${T + 14}" r="5" fill="${C.teal}"/><text x="${W - R - 234}" y="${T + 18}">unweighted fit</text>
    <path d="M${W - R - 246},${T + 26}l6,6l-6,6l-6,-6z" fill="${C.amber}"/><text x="${W - R - 234}" y="${T + 36}">weighted fit</text>
    <rect x="${W - R - 250}" y="${T + 44}" width="8" height="12" fill="${C.sand}"/><text x="${W - R - 234}" y="${T + 54}">± 2σ of measured ln γ₁</text>`;
}

function render(res) {
  const t = $('wf-out');
  const row = (name, key) => {
    const f = res.fits[key], s = res.scores[key];
    return `<tr><th scope="row">${name}</th><td>${fmt(f.tau[0], 4)} ± ${fmt(f.sd[0])}</td><td>${fmt(f.tau[1], 4)} ± ${fmt(f.sd[1])}</td><td>${fmt(f.corr, 2)}</td>
      <td>${fmt(s[60].rmse)}</td><td>${fmt(s[80].rmse)}</td><td>${fmt(s[60].rmsz, 2)}</td><td>${fmt(s[80].rmsz, 2)}</td><td${f.curvature <= 0 ? ' class="warn"' : ''}>${fmt(f.curvature)}${f.curvature <= 0 ? ' · predicts a liquid split' : ''}</td><td>${f.atBound ? 'yes' : 'no'}</td></tr>`;
  };
  t.innerHTML = row('Unweighted', 'unweighted') + row('Weighted by σ', 'weighted');
  const trainTxt = res.train === 'both' ? '60 and 80 kPa' : res.train + ' kPa';
  $('wf-context').textContent = `Training set: ${trainTxt}, ${res.nTrain} observations${res.xmin > 0 ? ` with x₁ ≥ ${res.xmin}` : ''}; α = ${res.alpha}. Scores use every usable observation at each pressure. Standard uncertainties used for σ: u(x) = ${fmt(res.u[60].x, 4)}, u(y) = ${fmt(res.u[60].y, 4)} at 60 kPa; u(x) = ${fmt(res.u[80].x, 4)}, u(y) = ${fmt(res.u[80].y, 4)} at 80 kPa (article averages, k = 2).`;
  $('wf-results').hidden = false;
  plot(res, Number($('wf-plotP').value));
}

function run() {
  try {
    const train = $('wf-train').value, xmin = parseFloat($('wf-xmin').value);
    if (!(xmin >= 0 && xmin < 0.5)) throw new Error('Choose a minimum x₁ between 0 and 0.5.');
    last = analyze(data, train, xmin);
    render(last);
    $('wf-status').textContent = 'Both fits converged. Compare the parameters, then the errors at each pressure.';
  } catch (e) { last = null; $('wf-results').hidden = true; $('wf-status').textContent = e.message; }
}

function state() {
  return { train: $('wf-train').value, xmin: parseFloat($('wf-xmin').value), plotP: $('wf-plotP').value, claim: $('wf-claim').value,
    result: last && { nTrain: last.nTrain, fits: last.fits, scores: Object.fromEntries(Object.entries(last.scores).map(([k, v]) => [k, { 60: v[60], 80: v[80] }])) } };
}
function restore(s) {
  if (!s) return;
  if (s.train) $('wf-train').value = s.train;
  if (Number.isFinite(s.xmin)) $('wf-xmin').value = s.xmin;
  if (s.plotP) $('wf-plotP').value = s.plotP;
  $('wf-claim').value = s.claim || '';
  if (s.result) run();
}

async function init() {
  if (!$('wf-run')) return;
  try {
    const response = await fetch(new URL('../../labs/assets/ipa-water.json', import.meta.url));
    data = await response.json();
    $('wf-run').disabled = false;
  } catch { $('wf-status').textContent = 'The measured data could not be loaded.'; }
  $('wf-run').addEventListener('click', run);
  $('wf-plotP').addEventListener('change', () => last && plot(last, Number($('wf-plotP').value)));
  $('import-study')?.addEventListener('change', async (e) => {
    const file = e.target.files?.[0]; if (!file) return;
    try { const rec = JSON.parse(await file.text()); restore(rec.weighted); } catch { /* the lab reports invalid files */ }
  });
  window.wFit = { state, run };
}
init();
