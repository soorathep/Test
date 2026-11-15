"""Session 2 discussion figure: residuals in ln gamma1 at 60 kPa for the fits trained at 60 and at 80 kPa,
with two-sigma bars propagated from the article's average uncertainties (k = 2)."""
import json, math
import numpy as np
from scipy.optimize import least_squares
import matplotlib.pyplot as plt
from style import setup, tidy, HERE, TEAL, AMBER, SAND, INK, GRAPHITE, SLATE

setup()
d = json.loads((HERE.parents[3] / 'teaching/2105603/labs/assets/ipa-water.json').read_text())
pr = d['properties']
ps = lambda c, T: 100 * 10 ** (c['A'] - c['B'] / (T + c['C']))
def pts(P):
    ds = [s for s in d['datasets'] if s['pressureKPa'] == P][0]; U = ds['averageExpandedUncertainty']; k = ds['coverageFactor']
    out = []
    for r in ds['rows']:
        x, y, T = r['x'], r['y'], r['T']
        if x in (0, 1) or not (334 <= T <= 362.41): continue
        l1 = math.log(y * P / (x * ps(pr[0], T))); l2 = math.log((1 - y) * P / ((1 - x) * ps(pr[1], T)))
        s1 = math.hypot(U['x'] / k / x, U['y'] / k / y, U['PkPa'] / k / P, math.log(10) * pr[0]['B'] / (T + pr[0]['C']) ** 2 * U['T'] / k)
        out.append((x, T, l1, l2, s1))
    return np.array(out)
def nrtl(x, a12, a21, al=.47):
    G12, G21, z = np.exp(-al * a12), np.exp(-al * a21), 1 - x
    return z * z * (a21 * (G21 / (x + z * G21)) ** 2 + a12 * G12 / (z + x * G12) ** 2), x * x * (a12 * (G12 / (z + x * G12)) ** 2 + a21 * G21 / (x + z * G21) ** 2)
res = lambda p, A: np.concatenate([nrtl(A[:, 0], *p)[0] - A[:, 2], nrtl(A[:, 0], *p)[1] - A[:, 3]])
A60, A80 = pts(60), pts(80)
f60 = least_squares(res, [.5, 1.5], args=(A60,)).x; f80 = least_squares(res, [.5, 1.5], args=(A80,)).x
r60 = nrtl(A60[:, 0], *f60)[0] - A60[:, 2]; r80 = nrtl(A60[:, 0], *f80)[0] - A60[:, 2]
fig, ax = plt.subplots(figsize=(8.2, 5.0))
x = A60[:, 0]
ax.bar(x, 4 * A60[:, 4], bottom=-2 * A60[:, 4], width=x * 0.16, color=SAND, alpha=.75, label=r'$\pm 2\sigma$ of measured ln $\gamma_1$')
ax.axhline(0, color=GRAPHITE, lw=1)
ax.plot(x, r60, 'o', color=TEAL, ms=8, mec='white', mew=1, label=f'fit at 60 kPa ($\\tau_{{21}}$ = {f60[1]:.2f})')
ax.plot(x, np.clip(r80, -1.25, 1.25), 'D', color=AMBER, ms=8, mec='white', mew=1, label=f'fit at 80 kPa ($\\tau_{{21}}$ = {f80[1]:.2f})')
for xi, ri in zip(x, r80):
    if ri > 1.25: ax.annotate(f'{ri:.2f}', (xi, 1.25), xytext=(6, -4), textcoords='offset points', color='#9a5f10', fontsize=14)
ax.axvspan(0.004, 0.02, color=SLATE, alpha=.07)
ax.text(0.0045, -1.12, 'four rows with $x_1$ < 0.02', color=SLATE, fontsize=14)
ax.set_xscale('log'); ax.set_xlim(0.004, 1.1); ax.set_ylim(-1.25, 1.35)
ax.set_xticks([0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1]); ax.set_xticklabels(['0.005', '0.01', '0.02', '0.05', '0.1', '0.2', '0.5', '1'])
ax.set_xlabel('$x_1$ (2-propanol), log scale · 60 kPa data'); ax.set_ylabel('model − measured ln $\\gamma_1$')
tidy(ax); ax.legend(frameon=False, fontsize=14, loc='upper right')
fig.tight_layout(); fig.savefig(HERE / 's02-resid.svg'); print(f60, f80)
