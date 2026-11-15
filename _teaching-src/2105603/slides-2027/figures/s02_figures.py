"""Session 2 figures from Barbieri, De Guido and Moioli (2024), 2-propanol + water (Lab 02 data)."""
import json, math
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
import matplotlib.pyplot as plt
from style import setup, tidy, HERE, TEAL, AMBER, SAND, INK, GRAPHITE, SLATE

setup()
data = json.loads((HERE.parents[3] / 'teaching/2105603/labs/assets/ipa-water.json').read_text())
A = [(p['A'], p['B'], p['C']) for p in data['properties']]
psat = lambda i, T: 100 * 10 ** (A[i][0] - A[i][1] / (T + A[i][2]))      # kPa
rows60 = data['datasets'][0]['rows']

# 1. Measured T-x-y at 60 kPa against Raoult's law
P = 60.0
xs = np.linspace(0, 1, 101)
Tb = [brentq(lambda T: x * psat(0, T) + (1 - x) * psat(1, T) - P, 334, 362.4) for x in xs]
Td = [brentq(lambda T: 1 / (y / psat(0, T) + (1 - y) / psat(1, T)) - P, 334, 362.4) for y in xs]
fig, ax = plt.subplots(figsize=(7.4, 5.4))
ax.plot(xs, Tb, color=TEAL, lw=2.2); ax.plot(xs, Td, color=TEAL, lw=2.2, ls=(0, (5, 3)))
ax.plot([r['x'] for r in rows60], [r['T'] for r in rows60], 'o', color=AMBER, ms=7, mec='white', mew=1)
ax.plot([r['y'] for r in rows60], [r['T'] for r in rows60], 'o', color='white', ms=7, mec=AMBER, mew=2)
az = rows60[4]
ax.annotate(f"azeotrope\n{az['T']:.2f} K, $x_1$ = {az['x']:.4f}", (az['x'], az['T']), xytext=(0.62, 337.2),
            color=INK, fontsize=15, arrowprops=dict(arrowstyle='-', color=GRAPHITE, lw=1))
ax.text(0.03, 338.4, "Raoult's law", color=TEAL, fontsize=16, fontweight=600)
ax.text(0.03, 336.6, 'solid: bubble   dashed: dew', color=SLATE, fontsize=14)
ax.text(0.6, 357.6, 'measured, 60 kPa', color='#9a5f10', fontsize=16, fontweight=600)
ax.text(0.6, 355.9, 'filled: liquid   open: vapor', color=SLATE, fontsize=14)
ax.set_xlim(0, 1); ax.set_ylim(335, 360)
ax.set_xlabel(r'2-propanol mole fraction,  $x_1$ or $y_1$'); ax.set_ylabel(r'temperature  $T$ / K')
tidy(ax); fig.tight_layout(); fig.savefig(HERE / 's02-txy.svg', transparent=True); plt.close(fig)

# 2. ln gamma from every interior 60 kPa row, with the NRTL teaching fit (fit 60 kPa)
pts = []
for r in rows60:
    if 0 < r['x'] < 1 and 334 <= r['T'] <= 362.41:
        g1 = r['y'] * P / (r['x'] * psat(0, r['T'])); g2 = (1 - r['y']) * P / ((1 - r['x']) * psat(1, r['T']))
        pts.append((r['x'], math.log(g1), math.log(g2)))
t12, t21, al = 0.3618156, 1.752437, 0.47
G12, G21 = math.exp(-al * t12), math.exp(-al * t21)
x1 = np.linspace(0.001, 0.999, 300); x2 = 1 - x1
lg1 = x2**2 * (t21 * (G21 / (x1 + x2 * G21))**2 + t12 * G12 / (x2 + x1 * G12)**2)
lg2 = x1**2 * (t12 * (G12 / (x2 + x1 * G12))**2 + t21 * G21 / (x1 + x2 * G21)**2)
fig, ax = plt.subplots(figsize=(7.4, 5.2))
ax.axhline(0, color=GRAPHITE, lw=1)
ax.plot(x1, lg1, color=TEAL, lw=2.2); ax.plot(x1, lg2, color=AMBER, lw=2.2)
ax.plot([p[0] for p in pts], [p[1] for p in pts], 'o', color=TEAL, ms=7, mec='white', mew=1)
ax.plot([p[0] for p in pts], [p[2] for p in pts], 'o', color=AMBER, ms=7, mec='white', mew=1)
ax.text(0.2, 2.15, r'ln $\gamma_1$  (2-propanol)', color=TEAL, fontsize=16, fontweight=600)
ax.text(0.52, 1.45, r'ln $\gamma_2$  (water)', color='#9a5f10', fontsize=16, fontweight=600)
ax.text(0.98, -0.12, r'$\gamma = 1$: ideal liquid', ha='right', color=SLATE, fontsize=14)
ax.text(0.02, -0.33, f'points: 60 kPa data ({len(pts)} pairs)   lines: NRTL fit, $\\alpha$ = 0.47', color=SLATE, fontsize=13)
ax.set_xlim(0, 1); ax.set_ylim(-0.4, 2.6)
ax.set_xlabel(r'2-propanol mole fraction in the liquid,  $x_1$'); ax.set_ylabel(r'ln $\gamma_i$')
tidy(ax); fig.tight_layout(); fig.savefig(HERE / 's02-lngamma.svg', transparent=True); plt.close(fig)
print('pairs', len(pts))

# 3. Fitting against checking error (Lab 02 results)
fits = ['fit 60\ncheck 80', 'fit 80\ncheck 60', 'fit both\ncheck 80']
train = [0.16828, 0.042925, 0.15483]; check = [0.16438, 0.2908, 0.11876]
fig, ax = plt.subplots(figsize=(7.4, 4.8))
i = np.arange(3); w = .36
ax.bar(i - w / 2, train, w, color=TEAL, label='fitting error')
bars = ax.bar(i + w / 2, check, w, color=AMBER, label='checking error')
bars[2].set_hatch('//'); bars[2].set_edgecolor('white')
for k in range(3):
    ax.text(k - w / 2, train[k] + .006, f'{train[k]:.3f}', ha='center', fontsize=14, color=INK)
    ax.text(k + w / 2, check[k] + .006, f'{check[k]:.3f}', ha='center', fontsize=14, color=INK)
ax.text(2 + w / 2, .2, 'not held\nout', ha='center', fontsize=13, color=SLATE)
ax.set_xticks(i, fits); ax.set_ylabel(r'RMSE in ln $\gamma$'); ax.set_ylim(0, .34)
ax.legend(frameon=False, loc='upper left', fontsize=14)
tidy(ax); fig.tight_layout(); fig.savefig(HERE / 's02-rmse.svg', transparent=True); plt.close(fig)
