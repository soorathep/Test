"""Usage: ~/.venvs/research/bin/python regenerate_electrochemistry.py study.json output_stem"""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42, 'font.family': 'DejaVu Sans'})
s = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2]); out.parent.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(7, 4.5), layout='constrained')
ax.plot([v['log10Q'] for v in s['curve']], [v['E'] for v in s['curve']], color=skh.C['teal'], lw=1.5, label='Nernst relation')
import math
ax.plot(s['lnQ']/math.log(10), s['E'], 'o', ms=6, color=skh.C['amber'], label='Supplied state')
ax.plot(s['log10K'], 0, 'D', ms=5, color=skh.C['graphite'], label='Q = K')
ax.axhline(0, color=skh.C['graphite'], lw=1.5, ls=':')
ax.set(xlabel='log₁₀ Q', ylabel='Cell potential / V', title=f"T = {s['input']['T']:g} K; n = {s['n']}")
ax.legend(frameon=False)
fig.savefig(out.with_suffix('.pdf')); fig.savefig(out.with_suffix('.png'), dpi=600)
