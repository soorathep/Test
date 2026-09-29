/** Binary, low-pressure gamma/Raoult VLE. No DOM or plotting dependencies. */
export const VERSION = '0.2.0';
export const R = 8.31446261815324;
const EPS = 1e-13;
export function bounded(v, lo, hi, label) {
  if (!Number.isFinite(v) || v < lo || v > hi) throw new RangeError(`${label} must be between ${lo} and ${hi}.`);
  return v;
}
export function psat(c, T) {
  bounded(T, ...c.rangeK, 'Temperature (K)');
  if (c.equation === 'antoine') return 1e5 * 10 ** (c.A - c.B / (T + c.C));
  if (c.equation === 'clausius') return c.PrefPa * Math.exp(-c.HvapJmol / R * (1 / T - 1 / c.Tref));
  throw new Error('Unsupported vapor-pressure correlation.');
}
/** A scalar preserves the 1-parameter API; {A12,A21} selects 3-suffix Margules. */
export function parameters(A = 0) {
  if (typeof A === 'number') { bounded(A, -1, 1.8, 'Margules A'); return {A12:A, A21:A}; }
  if (!A || typeof A !== 'object') throw new RangeError('Margules parameters must be a number or {A12, A21}.');
  return {A12:bounded(A.A12,-1,3,'Margules A12'), A21:bounded(A.A21,-1,3,'Margules A21')};
}
export function modelInfo(A = 0) {
  const p=parameters(A), nonideal=p.A12!==0||p.A21!==0;
  return {name:typeof A==='number'?(nonideal?'Margules (1 parameter)':'Ideal solution'):'Margules (2 parameters)',parameters:p,nonideal};
}
function quadraticRoots(a,b,c) {
  if (Math.abs(a)<1e-14) return Math.abs(b)<1e-14?[]:[-c/b];
  const d=b*b-4*a*c;
  if (d<0) return [];
  const q=-0.5*(b+(b>=0?1:-1)*Math.sqrt(d));
  if (q===0) return [-b/(2*a)];
  return [...new Set([q/a,c/q])].sort((x,y)=>x-y);
}
export function convexity(A = 0) {
  const {A12:a,A21:b}=parameters(A), c0=2*b-4*a, c1=6*(a-b);
  // h = x(1-x) gL''/RT is cubic. Inspect endpoints and ALL stationary points.
  const h=x=>1+x*(1-x)*(c0+c1*x);
  const points=[0,1,...quadraticRoots(-3*c1,2*(c1-c0),c0).filter(x=>x>0&&x<1)];
  const minScaledCurvature=Math.min(...points.map(h));
  return {convex:minScaledCurvature>1e-8,minScaledCurvature};
}
function requireConvex(A) {
  const check=convexity(A);
  if(!check.convex) throw new RangeError('These Margules parameters produce non-convex or near-critical liquid Gibbs energy. Reduce A12 or A21: this VLE-only lab does not solve liquid-liquid equilibrium (LLE).');
  return check;
}
export function gamma(x, A = 0) {
  bounded(x, 0, 1, 'Liquid mole fraction'); const {A12:a,A21:b}=parameters(A);
  return [Math.exp((1-x)**2*(a+2*(b-a)*x)), Math.exp(x**2*(b+2*(a-b)*(1-x)))];
}
export function bisect(fn, lo, hi, tolerance = EPS, maxIterations = 100) {
  let flo = fn(lo), fhi = fn(hi); const history = [];
  if (!Number.isFinite(flo) || !Number.isFinite(fhi)) throw new Error('Non-finite bracket residual.');
  if (Math.abs(flo) <= tolerance) return {root: lo, residual: flo, history};
  if (Math.abs(fhi) <= tolerance) return {root: hi, residual: fhi, history};
  if (flo * fhi > 0) throw new RangeError('No root in the valid correlation range.');
  for (let i = 0; i < maxIterations; i++) {
    const mid = (lo + hi) / 2, f = fn(mid);
    if (!Number.isFinite(f)) throw new Error('Non-finite solver residual.');
    history.push({iteration: i + 1, value: mid, residual: f});
    if (Math.abs(f) <= tolerance) return {root: mid, residual: f, history};
    if (flo * f <= 0) { hi = mid; fhi = f; } else { lo = mid; flo = f; }
  }
  throw new Error(`Solver did not converge in ${maxIterations} iterations.`);
}
export function bubbleP(system, T, x, A = 0) {
  bounded(T, ...system.rangeK, 'Temperature (K)'); requireConvex(A);
  const g = gamma(x, A), s = system.components.map(c => psat(c, T));
  const P = x * g[0] * s[0] + (1 - x) * g[1] * s[1];
  return {T, P, x, y: x * g[0] * s[0] / P, gamma: g, psat: s};
}
export function dewP(system, T, y, A = 0) {
  bounded(y, 0, 1, 'Vapor mole fraction');
  // The validated positive liquid curvature guarantees a strictly monotone y(x).
  const solve = bisect(x => bubbleP(system, T, x, A).y - y, 0, 1);
  return {...bubbleP(system, T, solve.root, A), history: solve.history};
}
export function bubbleT(system, P, x, A = 0) {
  bounded(P, 1000, 200000, 'Pressure (Pa)');
  const solve = bisect(T => bubbleP(system, T, x, A).P / P - 1, ...system.rangeK);
  return {...bubbleP(system, solve.root, x, A), history: solve.history};
}
export function dewT(system, P, y, A = 0) {
  bounded(P, 1000, 200000, 'Pressure (Pa)');
  const solve = bisect(T => dewP(system, T, y, A).P / P - 1, ...system.rangeK);
  return {...dewP(system, solve.root, y, A), history: solve.history};
}
export function rrValue(beta, z, K) {
  return z * (K[0] - 1) / (1 + beta * (K[0] - 1)) + (1 - z) * (K[1] - 1) / (1 + beta * (K[1] - 1));
}
export function rachfordRice(z, K) {
  bounded(z, 0, 1, 'Feed mole fraction');
  K.forEach(k => {if (!Number.isFinite(k) || k <= 0) throw new RangeError('K values must be finite and positive.');});
  const f0 = rrValue(0, z, K), f1 = rrValue(1, z, K);
  if (Math.max(...K.map(k => Math.abs(k - 1))) < 1e-9) return {beta: null, phase: 'indeterminate', history: []};
  if (f0 <= EPS) return {beta: 0, phase: 'liquid', history: []};
  if (f1 >= -EPS) return {beta: 1, phase: 'vapor', history: []};
  const solve = bisect(b => rrValue(b, z, K), 0, 1, 1e-14);
  return {beta: solve.root, phase: 'two-phase', history: solve.history};
}
export function azeotropes(system, T, A = 0) {
  requireConvex(A); const {A12:a,A21:b}=parameters(A);
  const [s1,s2]=system.components.map(c=>psat(c,T));
  // ln(gamma1/gamma2) is the derivative of excess Gibbs energy, a quadratic.
  return quadraticRoots(3*(a-b),2*(b-2*a),a+Math.log(s1/s2))
    .filter(x=>x>0&&x<1).map(x=>bubbleP(system,T,x,A));
}
// Retain the original single-azeotrope convenience API for existing callers.
export function azeotrope(system, T, A = 0) {return azeotropes(system,T,A)[0]??null;}
const mixEntropy = x => (x === 0 || x === 1) ? 0 : x * Math.log(x) + (1 - x) * Math.log(1 - x);
export function liquidG(x, A) { const {A12:a,A21:b}=parameters(A); return mixEntropy(x) + x*(1-x)*(a*(1-x)+b*x); }
export function vaporG(y, P, s) { return mixEntropy(y) + y * Math.log(P / s[0]) + (1 - y) * Math.log(P / s[1]); }
export function flash(system, T, P, z, A = 0) {
  bounded(z, 0, 1, 'Feed mole fraction'); bounded(P, 1000, 200000, 'Pressure (Pa)');
  const base = bubbleP(system, T, z, A), dew = dewP(system, T, z, A);
  const meta = {T, P, z, A, model:modelInfo(A), convexity:requireConvex(A), converged: true, within_model_domain: true,
    stability_status: 'Restricted to convex binary liquid and ideal vapor; no general TPD test.',
    bubble: base, dew, history: [], rrHistory: [], equilibriumResidual: null,
    balanceResidual: 0, K: null};
  const pure = z === 0 || z === 1;
  if (pure) {
    const ratio = P / base.P;
    if (Math.abs(ratio - 1) <= 1e-9) return {...meta, phase: 'indeterminate', beta: null, x: z, y: z};
    return {...meta, phase: ratio > 1 ? 'liquid' : 'vapor', beta: ratio > 1 ? 0 : 1,
      x: ratio > 1 ? z : null, y: ratio > 1 ? null : z};
  }
  const azs = azeotropes(system, T, A);
  const saturated=base.gamma.every((g,i)=>Math.abs(g*base.psat[i]/P-1)<1e-9);
  if (saturated) return {...meta, phase:'indeterminate', beta:null, x:z, y:z};
  // Positive liquid curvature makes pressure stationary only where gamma1*Psat1
  // equals gamma2*Psat2. Include every quadratic root, not only the first azeotrope.
  const cuts = [0, ...azs.map(az=>az.x), 1], candidates = [];
  for (let i = 0; i < cuts.length - 1; i++) {
    const fn = x => bubbleP(system, T, x, A).P / P - 1;
    if (fn(cuts[i]) * fn(cuts[i + 1]) > 0 && Math.min(Math.abs(fn(cuts[i])), Math.abs(fn(cuts[i + 1]))) > EPS) continue;
    const solve = bisect(fn, cuts[i], cuts[i + 1]);
    const eq = bubbleP(system, T, solve.root, A), width = eq.y - eq.x;
    if (Math.abs(width) < 1e-9) continue;
    const lever = (z - eq.x) / width;
    if (lever < -1e-8 || lever > 1 + 1e-8) continue;
    const K = eq.gamma.map((g, j) => g * eq.psat[j] / P);
    const rr = rachfordRice(z, K);
    if (rr.beta === null) continue;
    const beta = rr.beta;
    const balanceResidual = Math.abs((1 - beta) * eq.x + beta * eq.y - z);
    const equilibriumResidual = Math.max(Math.abs(eq.x * K[0] - eq.y), Math.abs((1 - eq.x) * K[1] - (1 - eq.y)));
    candidates.push({...meta, phase: beta <= EPS ? 'bubble-boundary' : beta >= 1 - EPS ? 'dew-boundary' : 'two-phase',
      beta, x: eq.x, y: eq.y, K, history: solve.history, rrHistory: rr.history, balanceResidual, equilibriumResidual,
      g: (1 - beta) * liquidG(eq.x, A) + beta * vaporG(eq.y, P, eq.psat)});
  }
  if (candidates.length) {
    candidates.sort((a, b) => a.g - b.g);
    const result = candidates[0];
    if (result.balanceResidual > 1e-8 || result.equilibriumResidual > 1e-8) throw new Error('Flash failed the independent balance or equilibrium residual check.');
    return result;
  }
  const liquid = liquidG(z, A) <= vaporG(z, P, base.psat);
  return {...meta, phase: liquid ? 'liquid' : 'vapor', beta: liquid ? 0 : 1, x: liquid ? z : null, y: liquid ? null : z};
}
export function diagram(system, T, P, A, kind = 'pxy', n = 100) {
  return Array.from({length: n + 1}, (_, i) => {
    const x = i / n;
    if (kind !== 'txy') return bubbleP(system, T, x, A);
    try { return bubbleT(system, P, x, A); }
    catch (error) { if (error instanceof RangeError && error.message.startsWith('No root')) return {x, y: null, T: null, P}; throw error; }
  });
}
