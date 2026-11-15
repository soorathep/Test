"""Session 1 (graduate version): vapor fraction against pressure for benzene + toluene + p-xylene at 350 K."""
import numpy as np
from scipy.optimize import brentq
import matplotlib.pyplot as plt
from style import setup, tidy, HERE, TEAL, AMBER, SAND, INK, GRAPHITE, SLATE

setup()
z = np.array([.3, .3, .4]); psat = np.array([91.567, 34.786, 13.821])   # kPa at 350 K, NIST Antoine (Willingham 1945)
Pb, Pd = (z * psat).sum(), 1 / (z / psat).sum()
def beta(P):
    K = psat / P; f = lambda b: (z * (K - 1) / (1 + b * (K - 1))).sum()
    return brentq(f, 1 / (1 - K.max()) + 1e-9, 1 / (1 - K.min()) - 1e-9)
P = np.linspace(20, 50, 300); B = np.array([beta(p) for p in P])
fig, ax = plt.subplots(figsize=(7.4, 5.0))
ax.axhspan(0, 1, color=SAND, alpha=.35, lw=0)
inside = (B >= 0) & (B <= 1)
ax.plot(P[inside], B[inside], color=AMBER, lw=2.8)
ax.plot(P[~inside & (P > Pb)], B[~inside & (P > Pb)], color=AMBER, lw=1.8, ls=(0, (4, 3)))
ax.plot(P[~inside & (P < Pd)], B[~inside & (P < Pd)], color=AMBER, lw=1.8, ls=(0, (4, 3)))
ax.axhline(0, color=GRAPHITE, lw=1); ax.axhline(1, color=GRAPHITE, lw=1)
for p_, lab in [(30, 'β = 0.601'), (45, 'β = −0.064')]:
    b = beta(p_); ax.plot([p_], [b], 'o', color=AMBER, ms=8, mec='white', mew=1.5)
    ax.text(p_ + .6, b + .06, lab.replace('β', r'$\beta$'), color=INK, fontsize=15)
ax.axvline(Pd, color=TEAL, lw=1.2, ls=':'); ax.axvline(Pb, color=TEAL, lw=1.2, ls=':')
ax.text(Pd + .3, 1.32, f'dew {Pd:.2f}', color=TEAL, fontsize=14); ax.text(Pb + .3, 1.32, f'bubble {Pb:.2f}', color=TEAL, fontsize=14)
ax.text(47.6, .5, 'one liquid\n(negative flash)', ha='center', va='center', color=SLATE, fontsize=13)
ax.text(21.8, .5, 'one\nvapor', ha='center', va='center', color=SLATE, fontsize=13)
ax.set_xlim(20, 50); ax.set_ylim(-.45, 1.45)
ax.set_xlabel(r'pressure  $P$ / kPa  (350 K, $z$ = 0.3 / 0.3 / 0.4)'); ax.set_ylabel(r'Rachford–Rice root  $\beta$')
tidy(ax); fig.tight_layout(); fig.savefig(HERE / 's01-beta3.svg', transparent=True); plt.close(fig)
print(round(Pd, 3), round(Pb, 3))
