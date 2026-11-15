"""Pxy diagram for Session 1: Lab 01 synthetic ideal binary at 350 K (P1sat 150, P2sat 60 kPa).

Text is drawn as paths in Source Sans 3, decoded from theme/_fonts-embedded.scss,
so the SVG looks the same inside <img> as the slide text (needs fonttools + brotli).
"""
from pathlib import Path
import base64, io, logging, re, tempfile

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from fontTools.ttLib import TTFont

logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
HERE = Path(__file__).resolve().parent
TEAL, AMBER, SAND, GRAPHITE, INK, SLATE, MIST = '#0F6E6B', '#E29A2D', '#DFC98F', '#333F4A', '#1C242B', '#66727C', '#B9C1C6'


def register_fonts():
    scss = (HERE.parents[1] / 'theme/_fonts-embedded.scss').read_text()
    tmp = Path(tempfile.mkdtemp())
    pat = r'font-family:"Source Sans 3";\s*font-style:(\w+);\s*font-weight:(\d+);\s*src:url\(data:font/woff2;base64,([A-Za-z0-9+/=]+)\)'
    for style, weight, data in re.findall(pat, scss):
        font = TTFont(io.BytesIO(base64.b64decode(data))); font.flavor = None
        path = tmp / f'SourceSans3-{weight}-{style}.ttf'; font.save(path)
        font_manager.fontManager.addfont(str(path))


register_fonts()
# The embedded subset is named after its variable-font default instance.
FAMILY = 'Source Sans 3 ExtraLight'
plt.rcParams.update({'svg.fonttype': 'path', 'font.family': FAMILY, 'font.size': 17,
                     'mathtext.fontset': 'custom', 'mathtext.rm': FAMILY, 'mathtext.it': FAMILY + ':italic',
                     'axes.edgecolor': GRAPHITE, 'axes.labelcolor': INK, 'xtick.color': GRAPHITE, 'ytick.color': GRAPHITE})

P1, P2, P, Z = 150.0, 60.0, 95.0, 0.5
x = np.linspace(0, 1, 201)
bubble = x * P1 + (1 - x) * P2
dew = 1 / (x / P1 + (1 - x) / P2)
xl = (P - P2) / (P1 - P2); yv = xl * P1 / P; beta = (Z - xl) / (yv - xl)



def base_axes():
    fig, ax = plt.subplots(figsize=(7.4, 5.6))
    ax.set_xlim(0, 1); ax.set_ylim(55, 155)
    ax.set_xlabel(r'mole fraction of component 1,  $x_1$ or $y_1$')
    ax.set_ylabel(r'pressure  $P$ / kPa')
    for s_ in ('top', 'right'): ax.spines[s_].set_visible(False)
    ax.grid(axis='y', color=MIST, lw=.6, alpha=.6)
    return fig, ax


# bubble line only
fig, ax = base_axes()
ax.plot(x, bubble, color=TEAL, lw=2.4)
ax.plot([0.5], [105], 'o', color=AMBER, ms=9, mec='white', mew=1.5)
ax.plot([0.5, 0.5], [55, 105], color=GRAPHITE, lw=1, ls=':')
ax.text(0.53, 104, r'$x_1$ = 0.5,  $P_\mathrm{bubble}$ = 105 kPa', va='top', color=INK, fontsize=16)
ax.text(0.06, 136, 'Liquid above this line', color=INK, fontsize=17, fontweight=600)
ax.text(0.64, 128.5, 'bubble line', color=TEAL, fontsize=15, rotation=24)
fig.tight_layout(); fig.savefig(HERE / 's01-bubble.svg', transparent=True); plt.close(fig)

# dew line only
fig, ax = base_axes()
ax.plot(x, dew, color=TEAL, lw=2.4, ls=(0, (5, 3)))
pdew = 1 / (0.5 / P1 + 0.5 / P2)
ax.plot([0.5], [pdew], 'o', color=AMBER, ms=9, mec='white', mew=1.5)
ax.plot([0.5, 0.5], [55, pdew], color=GRAPHITE, lw=1, ls=':')
ax.text(0.53, pdew - 1.5, r'$y_1$ = 0.5,  $P_\mathrm{dew}$ = 85.71 kPa', va='top', color=INK, fontsize=16)
ax.text(0.62, 64, 'Vapor below this line', color=INK, fontsize=17, fontweight=600)
ax.text(0.83, 108.5, 'dew line', color=TEAL, fontsize=15, rotation=36)
fig.tight_layout(); fig.savefig(HERE / 's01-dew.svg', transparent=True); plt.close(fig)

# full diagram with the 95 kPa tie line
fig, ax = base_axes()
ax.fill_between(x, dew, bubble, color=SAND, alpha=.55, lw=0)
ax.plot(x, bubble, color=TEAL, lw=2.4)
ax.plot(x, dew, color=TEAL, lw=2.4, ls=(0, (5, 3)))
ax.plot([xl, yv], [P, P], color=AMBER, lw=2.6)
ax.plot([xl, yv], [P, P], 'o', color=AMBER, ms=8, mec='white', mew=1.5)
ax.plot([Z], [P], 'o', color=INK, ms=7)
ax.axhline(110, color=GRAPHITE, lw=1.2, ls=':')
ax.text(0.02, 111.8, '110 kPa ?', ha='left', va='bottom', color=GRAPHITE, fontsize=16)
ax.text(0.06, 136, 'Liquid', color=INK, fontsize=19, fontweight=600)
ax.text(0.80, 66, 'Vapor', color=INK, fontsize=19, fontweight=600)
ax.text(0.585, 103.2, 'two phases', color=SLATE, fontsize=15, style='italic', rotation=24)
ax.text(0.64, 128.5, 'bubble line', color=TEAL, fontsize=15, rotation=24)
ax.text(0.83, 108.5, 'dew line', color=TEAL, fontsize=15, rotation=36)
ax.text(xl - .025, P, rf'$x_1$ = {xl:.3f}', ha='right', va='center', color=INK, fontsize=16)
ax.text(yv + .025, P, rf'$y_1$ = {yv:.3f}', ha='left', va='center', color=INK, fontsize=16)
ax.text(Z, P - 2.2, r'$z_1$ = 0.5', ha='center', va='top', color=INK, fontsize=16)
fig.tight_layout()
fig.savefig(HERE / 's01-pxy.svg', transparent=True); plt.close(fig)

# vapor fraction against pressure at z1 = 0.5
pb, pd = Z * P1 + (1 - Z) * P2, 1 / (Z / P1 + (1 - Z) / P2)
pp = np.linspace(pd, pb, 200)
xx = (pp - P2) / (P1 - P2); yy = xx * P1 / pp; bb = (Z - xx) / (yy - xx)
fig, ax = plt.subplots(figsize=(7.4, 5.0))
ax.axvspan(78, pd, color=SAND, alpha=.35, lw=0); ax.axvspan(pb, 114, color='#0F6E6B', alpha=.08, lw=0)
ax.plot(pp, bb, color=AMBER, lw=2.8)
for P_, lab in [(90, '0.75'), (95, '0.494'), (100, '0.25')]:
    x_ = (P_ - P2) / (P1 - P2); y_ = x_ * P1 / P_; b_ = (Z - x_) / (y_ - x_)
    ax.plot([P_], [b_], 'o', color=AMBER, ms=8, mec='white', mew=1.5)
    ax.text(P_ + 1.0, b_ + .05, rf'$\beta$ = {lab}', color=INK, fontsize=15)
ax.axvline(110, color=GRAPHITE, lw=1.2, ls=':'); ax.text(109.6, .9, 'Activity 1', ha='right', color=GRAPHITE, fontsize=14)
ax.text((78 + pd) / 2, .5, 'all vapor', ha='center', color=INK, fontsize=16, rotation=90, va='center')
ax.text((pb + 114) / 2 - 1.2, .5, 'all liquid', ha='center', color=INK, fontsize=16, rotation=90, va='center')
ax.text(pd + .4, -.09, f'dew {pd:.2f}', color=SLATE, fontsize=13); ax.text(pb - .4, -.09, f'bubble {pb:.0f}', color=SLATE, fontsize=13, ha='right')
ax.set_xlim(78, 114); ax.set_ylim(-0.13, 1.08)
ax.set_xlabel(r'pressure  $P$ / kPa  (350 K, $z_1$ = 0.5)'); ax.set_ylabel(r'vapor fraction  $\beta$')
for s_ in ('top', 'right'): ax.spines[s_].set_visible(False)
ax.grid(axis='y', color=MIST, lw=.6, alpha=.6)
fig.tight_layout(); fig.savefig(HERE / 's01-beta.svg', transparent=True); plt.close(fig)
print('s01-pxy.svg', round(xl, 6), round(yv, 6), round(beta, 6))
