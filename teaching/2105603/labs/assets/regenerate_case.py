"""Regenerate the exported case study T-x-y comparison with the lab palette.
Usage: ~/.venvs/research/bin/python figures/regenerate_case.py study.json output_prefix
"""
from pathlib import Path
import sys
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype': 42, 'ps.fonttype': 42, 'font.family': 'DejaVu Sans'})
record=json.loads(Path(sys.argv[1]).read_text())
prefix=Path(sys.argv[2]); prefix.parent.mkdir(parents=True,exist_ok=True)
# Palette is imported through skh.use(), including its prescribed cycle.
teal,amber=skh.C['teal'],skh.C['amber']
rows=next(s['rows'] for s in record['source']['datasets'] if s['pressureKPa']==record['selectedPressureKPa'])
curve=record['curve']
fig,ax=plt.subplots(figsize=(6.8,4.8))
for key,marker,label in [('x','o','Measured liquid'),('y','D','Measured vapor')]:
 ax.plot([r[key] for r in rows],[r['T'] for r in rows],ls='none',marker=marker,ms=4,color=teal,label=label,markerfacecolor='none' if key=='y' else teal,markeredgecolor=teal,markeredgewidth=1)
for key,style,label in [('x','-','NRTL bubble'),('y','--','NRTL dew')]:
 ax.plot([r[key] if r['T'] is not None else float('nan') for r in curve],[r['T'] if r['T'] is not None else float('nan') for r in curve],style,lw=1.5,color=amber,label=label)
ax.set(xlabel='Mole fraction of 2-propanol, x₁ or y₁',ylabel='Temperature / K',title=f"Isopropanol + water, {record['selectedPressureKPa']} kPa")
ax.legend(frameon=False,fontsize=9)
fig.text(.1,.015,'Data: Barbieri et al., J. Chem. Thermodynamics 198 (2024) 107342.\nModel: ideal vapor; curves restricted to property domain.',fontsize=8)
fig.tight_layout(rect=(0,.08,1,1))
fig.savefig(prefix.with_suffix('.pdf'));fig.savefig(prefix.with_suffix('.png'),dpi=600)
