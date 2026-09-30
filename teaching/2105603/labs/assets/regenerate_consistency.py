"""Recreate diagnostic plots from a Lab 03 JSON export.
Usage: ~/.venvs/research/bin/python figures/regenerate_consistency.py study.json prefix
"""
from pathlib import Path
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
r=json.loads(Path(sys.argv[1]).read_text());prefix=Path(sys.argv[2]);prefix.parent.mkdir(parents=True,exist_ok=True)
fig,axes=plt.subplots(1,2,figsize=(10,4.5),layout='constrained')
valid=r['set']['valid'];area=r['area'];local=r['differential']['points']
perturbed=r['set']['synthetic'] and r['set']['kind']!='clean'
curve_color=skh.C['amber'] if perturbed else skh.C['teal']
axes[0].plot([v['x'] for v in valid],[v['f'] for v in valid],color=curve_color,lw=1.5,marker='o',ms=4,label='Supplied activity ratio')
if area['conditional']:
 axes[0].plot([v['x'] for v in area['points']],[v['f'] for v in area['points']],color=skh.C['amber'],lw=1.5,ls='--',label='Endpoint assumption')
axes[1].plot([v['x'] for v in local],[v['raw'] for v in local],color=curve_color,lw=1.5,label='Raw differential residual')
if r['set']['path']=='isobaric' and r['set']['synthetic'] and r['settings']['heatCorrection']:
 axes[1].plot([v['x'] for v in local],[v['residual'] for v in local],color=skh.C['amber'],lw=1.5,label='With supplied heat correction')
for ax in axes:
 ax.axhline(0,color=skh.C['graphite'],lw=1.5,ls=':');ax.set_xlabel('Liquid mole fraction, x₁');ax.legend(frameon=False,fontsize=8)
axes[0].set_ylabel('ln(γ₁/γ₂)');axes[1].set_ylabel('Differential residual (dimensionless)')
fig.suptitle(r['set']['name']+' | '+('Synthetic teaching data' if r['set']['synthetic'] else 'Barbieri et al. (2024), DOI: 10.1016/j.jct.2024.107342'),fontsize=10)
fig.savefig(prefix.with_suffix('.pdf'));fig.savefig(prefix.with_suffix('.png'),dpi=600)
