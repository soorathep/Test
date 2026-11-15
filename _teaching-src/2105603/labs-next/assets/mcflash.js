// Lab 01 Graduate step D: isothermal flash for up to five components with constant K-values.
// Rachford-Rice: f(beta) = sum z_i (K_i - 1) / (1 + beta (K_i - 1)) = 0, solved inside its
// asymptotes (1/(1-Kmax), 1/(1-Kmin)) so that negative flash results are reported, not hidden.
// Values are saved in the study file under "multicomponent" and restored when it is reopened.

const PRESETS = {
  bt30: { label: 'Benzene + toluene + p-xylene · 350 K · 30 kPa', P: 30, rows: [['Benzene', 0.3, 91.567], ['Toluene', 0.3, 34.786], ['p-Xylene', 0.4, 13.821]] },
  bt45: { label: 'Same feed · 350 K · 45 kPa', P: 45, rows: [['Benzene', 0.3, 91.567], ['Toluene', 0.3, 34.786], ['p-Xylene', 0.4, 13.821]] },
};
const MAX = 5;
const COLORS = { teal: '#0F6E6B', amber: '#E29A2D', sand: '#DFC98F', ink: '#1C242B', graphite: '#333F4A', slate: '#66727C', mist: '#B9C1C6' };
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 4) => (Number.isFinite(v) ? v.toFixed(d) : '—');

export function solve(z, K) {
  const n = z.length;
  const sz = z.reduce((a, b) => a + b, 0);
  if (n < 2 || z.some((v) => !(v > 0)) || K.some((v) => !(v > 0))) throw new Error('Every z and K must be positive, with at least two components.');
  if (Math.abs(sz - 1) > 1e-6) throw new Error(`The feed fractions add up to ${sz.toFixed(4)}, not 1.`);
  if (K.every((k) => k > 1) || K.every((k) => k < 1)) throw new Error('All K-values are on one side of 1: no tie line exists for any β.');
  const f = (b) => z.reduce((s, zi, i) => s + (zi * (K[i] - 1)) / (1 + b * (K[i] - 1)), 0);
  const lo = 1 / (1 - Math.max(...K)), hi = 1 / (1 - Math.min(...K));
  let a = lo + 1e-12 * (hi - lo), c = hi - 1e-12 * (hi - lo);
  for (let i = 0; i < 200; i++) {                       // bisection: f decreases monotonically in (lo, hi)
    const m = (a + c) / 2;
    if (f(m) > 0) a = m; else c = m;
  }
  const beta = (a + c) / 2;
  const x = z.map((zi, i) => zi / (1 + beta * (K[i] - 1)));
  const y = x.map((xi, i) => K[i] * xi);
  const sumZK = z.reduce((s, zi, i) => s + zi * K[i], 0), sumZoverK = z.reduce((s, zi, i) => s + zi / K[i], 0);
  const phase = sumZK <= 1 ? 'liquid' : sumZoverK <= 1 ? 'vapor' : 'two-phase';
  return { beta, x, y, lo, hi, f, sumZK, sumZoverK, phase };
}

function rows() {
  return [...document.querySelectorAll('#mc-body tr')].map((tr) => {
    const [name, z, ps] = tr.querySelectorAll('input');
    return { name: name.value.trim(), z: parseFloat(z.value), psat: parseFloat(ps.value) };
  }).filter((r) => r.name || Number.isFinite(r.z) || Number.isFinite(r.psat));
}

function setRows(list, P) {
  $('mc-P').value = P;
  document.querySelectorAll('#mc-body tr').forEach((tr, i) => {
    const r = list[i] || ['', '', ''];
    const inp = tr.querySelectorAll('input');
    inp[0].value = r[0]; inp[1].value = r[1]; inp[2].value = r[2];
  });
}

function plot(res) {
  const svg = $('mc-plot');
  const W = 640, H = 300, L = 62, R = 16, T = 16, B = 44;
  const span = res.hi - res.lo;
  const b0 = res.lo + 0.02 * span, b1 = res.hi - 0.02 * span;
  const pts = []; let ymin = Infinity, ymax = -Infinity;
  for (let i = 0; i <= 240; i++) {
    const b = b0 + (b1 - b0) * i / 240, v = res.f(b);
    pts.push([b, v]); ymin = Math.min(ymin, v); ymax = Math.max(ymax, v);
  }
  const edge = Math.max(Math.abs(res.f(Math.max(0, b0))), Math.abs(res.f(Math.min(1, b1))), 0.05);
  const clip = Math.min(Math.max(Math.abs(ymin), Math.abs(ymax)), 2.5 * edge);
  const X = (b) => L + (b - b0) / (b1 - b0) * (W - L - R);
  const Y = (v) => T + (1 - (Math.max(-clip, Math.min(clip, v)) + clip) / (2 * clip)) * (H - T - B);
  const path = pts.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join('');
  const band = `<rect x="${X(Math.max(0, b0))}" y="${T}" width="${Math.max(0, X(Math.min(1, b1)) - X(Math.max(0, b0)))}" height="${H - T - B}" fill="${COLORS.sand}" opacity=".35"/>`;
  const ticks = [];
  const step = span > 4 ? 1 : 0.5;
  for (let t = Math.ceil(b0 / step) * step; t <= b1; t += step) ticks.push(`<line x1="${X(t)}" x2="${X(t)}" y1="${H - B}" y2="${H - B + 5}" stroke="${COLORS.graphite}"/><text x="${X(t)}" y="${H - B + 20}" text-anchor="middle">${+t.toFixed(2)}</text>`);
  svg.innerHTML = `${band}
    <line x1="${L}" x2="${W - R}" y1="${Y(0)}" y2="${Y(0)}" stroke="${COLORS.graphite}" stroke-width="1"/>
    <line x1="${L}" x2="${L}" y1="${T}" y2="${H - B}" stroke="${COLORS.graphite}"/>
    <line x1="${L}" x2="${W - R}" y1="${H - B}" y2="${H - B}" stroke="${COLORS.graphite}"/>
    ${ticks.join('')}
    <path d="${path}" fill="none" stroke="${COLORS.teal}" stroke-width="2.4"/>
    <circle cx="${X(res.beta)}" cy="${Y(0)}" r="6" fill="${COLORS.amber}" stroke="#fff" stroke-width="1.5"/>
    <text x="${X(res.beta) + 9}" y="${Y(0) - 10}" fill="${COLORS.ink}">β = ${res.beta.toFixed(4)}</text>
    <text x="${X(Math.max(0, b0)) + 6}" y="${T + 16}" fill="${COLORS.slate}">physical range 0 ≤ β ≤ 1</text>
    <text x="${(L + W - R) / 2}" y="${H - 6}" text-anchor="middle" fill="${COLORS.ink}">vapor fraction β (between the asymptotes ${fmt(res.lo, 3)} and ${fmt(res.hi, 3)})</text>
    <text transform="translate(16 ${(T + H - B) / 2}) rotate(-90)" text-anchor="middle" fill="${COLORS.ink}">f(β)</text>`;
}

function run() {
  const status = $('mc-status');
  try {
    const P = parseFloat($('mc-P').value);
    if (!(P > 0)) throw new Error('Enter a positive pressure.');
    const r = rows();
    if (r.some((v) => !v.name || !Number.isFinite(v.z) || !Number.isFinite(v.psat))) throw new Error('Complete or clear every row you use: name, z and Psat.');
    const z = r.map((v) => v.z), K = r.map((v) => v.psat / P);
    const res = solve(z, K);
    $('mc-sumzk').textContent = fmt(res.sumZK); $('mc-sumzok').textContent = fmt(res.sumZoverK);
    $('mc-bounds').textContent = `${fmt(res.lo, 3)} to ${fmt(res.hi, 3)}`;
    $('mc-beta').textContent = fmt(res.beta);
    const verdict = res.phase === 'two-phase' ? 'Two phases: 0 < β < 1.'
      : res.phase === 'liquid' ? `Σ zᵢKᵢ ≤ 1, so the feed is at or below its bubble point: one liquid phase. The root β = ${fmt(res.beta)} is a negative flash.`
      : `Σ zᵢ/Kᵢ ≤ 1, so the feed is at or above its dew point: one vapor phase. The root β = ${fmt(res.beta)} is a negative flash.`;
    $('mc-verdict').textContent = verdict;
    $('mc-out').innerHTML = r.map((v, i) => `<tr><td>${v.name.replace(/[<>&]/g, '')}</td><td>${fmt(z[i])}</td><td>${fmt(K[i])}</td><td>${fmt(res.x[i])}</td><td>${fmt(res.y[i])}</td></tr>`).join('')
      + `<tr class="sum"><td>Sum</td><td>${fmt(z.reduce((a, b) => a + b, 0))}</td><td></td><td>${fmt(res.x.reduce((a, b) => a + b, 0))}</td><td>${fmt(res.y.reduce((a, b) => a + b, 0))}</td></tr>`;
    plot(res);
    $('mc-results').hidden = false;
    status.textContent = 'Calculated with constant K = Psat/P (ideal liquid and vapor). A real mixture needs K updated from x and y and the flash repeated.';
    state.last = { P, rows: r, beta: res.beta, phase: res.phase };
  } catch (e) {
    $('mc-results').hidden = true;
    status.textContent = e.message;
  }
}

const state = { last: null };
window.mcFlash = { state: () => ({ inputs: { P: $('mc-P')?.value, rows: rows() }, result: state.last, note: $('mc-claim')?.value || '' }) };

function restore(rec) {
  const m = rec?.multicomponent;
  if (!m?.inputs) return;
  setRows((m.inputs.rows || []).slice(0, MAX).map((r) => [r.name, r.z, r.psat]), m.inputs.P ?? '');
  if ($('mc-claim')) $('mc-claim').value = typeof m.note === 'string' ? m.note : '';
  if (m.result) run();
}

function init() {
  if (!$('mc-body')) return;
  $('mc-body').innerHTML = Array.from({ length: MAX }, (_, i) => `<tr><td><input aria-label="Component ${i + 1} name" type="text" maxlength="30"></td><td><input aria-label="Component ${i + 1} feed mole fraction" type="number" step="any" min="0" max="1"></td><td><input aria-label="Component ${i + 1} saturation pressure in kPa" type="number" step="any" min="0"></td></tr>`).join('');
  $('mc-preset').innerHTML = Object.entries(PRESETS).map(([k, p]) => `<option value="${k}">${p.label}</option>`).join('');
  const load = () => { const p = PRESETS[$('mc-preset').value]; setRows(p.rows, p.P); $('mc-results').hidden = true; $('mc-status').textContent = 'Preset loaded. Press Solve the flash.'; };
  $('mc-load').addEventListener('click', load);
  $('mc-run').addEventListener('click', run);
  load();
  const file = document.getElementById('import-study');
  file?.addEventListener('change', async () => {
    const f = file.files?.[0]; if (!f || f.size > 5e6) return;
    try { restore(JSON.parse(await f.text())); } catch { /* the lab reports invalid files */ }
  });
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
