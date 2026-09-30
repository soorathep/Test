"""Regenerate Lab 04 Gibbs and phase-map plots from exported JSON.
Usage: ~/.venvs/research/bin/python figures/regenerate_stability.py study.json prefix
"""
import json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
s=json.loads(Path(sys.argv[1]).read_text());p=Path(sys.argv[2]);p.parent.mkdir(parents=True,exist_ok=True)
r=s['result'];rows=s['curve'];m=s['phaseMap']
fig,axes=plt.subplots(1,2,figsize=(10,4.5),layout='constrained')
for key,label,color,style in [('ideal','Ideal reference','teal','-'),('g','Homogeneous liquid','amber','-'),('hull','Equilibrium envelope','graphite','--')]:
 axes[0].plot([v['x'] for v in rows],[v[key] for v in rows],color=skh.C[color],lw=1.5,ls=style,label=label)
axes[0].plot(r['z'],r['homogeneousG'],'D',ms=5,color=skh.C['amber'],label='Homogeneous feed')
if r['binodal']:
 b=r['binodal'];axes[0].plot([b['xAlpha'],b['xBeta']],[b['g'],b['g']],'o-',ms=5,lw=1.5,color=skh.C['graphite'],label='Common tangent')
for key,label,color,style in [('xAlpha','Binodal','amber','-'),('xBeta',None,'amber','-'),('spinodalAlpha','Spinodal','graphite','--'),('spinodalBeta',None,'graphite','--')]:
 axes[1].plot([v[key] for v in m],[v['A'] for v in m],color=skh.C[color],lw=1.5,ls=style,label=label)
axes[1].plot(r['z'],r['A'],'o',ms=5,color=skh.C['teal'],label='Current feed')
for ax in axes:ax.set_xlim(0,1);ax.set_xlabel('Mole fraction of component 1');ax.legend(frameon=False,fontsize=8)
axes[0].set_ylabel('Mixing Gibbs energy / RT');axes[1].set(ylabel='Interaction parameter A',ylim=(0,6.1))
fig.suptitle(f"Symmetric Margules: A = {r['A']:g}, z₁ = {r['z']:g} | {r['state']} homogeneous feed",fontsize=11)
fig.savefig(p.with_suffix('.pdf'));fig.savefig(p.with_suffix('.png'),dpi=600)
