"""Regenerate bootstrap evidence figures from a downloaded evidence JSON.
Usage: ~/.venvs/research/bin/python regenerate_evidence.py study.json output.pdf
Requires matplotlib and the group's skh_palette module; input data are read only.
"""
import json, sys
from pathlib import Path
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({"pdf.fonttype":42,"ps.fonttype":42,"font.family":"DejaVu Sans"})
d=json.loads(Path(sys.argv[1]).read_text()); b=d['reports']['bootstrap']
if b.get('unavailable'): raise ValueError(b['unavailable'])
fig,ax=plt.subplots(figsize=(7,4.5))
# Palette is imported; semantic colors come from the installed palette module.
# Matplotlib's configured cycle starts with reference teal and effect amber.
colors=plt.rcParams['axes.prop_cycle'].by_key()['color']
if b['kind']=='vle-bootstrap':
    x=[r['x'] for r in b['band']]
    ax.fill_between(x,[r['P']['lower'] for r in b['band']],[r['P']['upper'] for r in b['band']],color=skh.C['sand'],label='95% pointwise fit spread')
    ax.plot(x,[r['Pcalc'] for r in b['base']['points']],color=colors[0],lw=1.8,label='Full-data fit')
    ax.set(xlabel='Liquid mole fraction $x_1$ (at each measured T)',ylabel='Predicted pressure / kPa')
else:
    ax.plot([r['tau12'] for r in b['samples']],[r['tau21'] for r in b['samples']],'o',color=colors[1],ms=4,label='Supported resampled fits')
    ax.plot(b['base']['parameters']['tau12'],b['base']['parameters']['tau21'],'o',color=colors[0],ms=7,label='Original-data fit')
    ax.set(xlabel=r'$\tau_{12}$',ylabel=r'$\tau_{21}$')
ax.legend();fig.tight_layout();fig.savefig(sys.argv[2],dpi=600)
