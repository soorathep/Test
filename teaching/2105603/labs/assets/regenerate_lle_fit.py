"""Regenerate a Lab 05 study figure from exported JSON.
~/.venvs/research/bin/python figures/regenerate_lle_fit.py study.json output-prefix
"""
import json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
study=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
dataset=study['dataset'];r=study['result'];d=r['diagnostics'];rows=dataset['rows'];n=list(range(1,len(rows)+1))
fig,axes=plt.subplots(1,2,figsize=(10,4.6),layout='constrained')
for key,uncertainty,marker,label in [('xAlpha','expandedUncertaintyAlpha','o','Observed α'),('xBeta','expandedUncertaintyBeta','D','Observed β')]:
 errors=[v[uncertainty] for v in rows] if uncertainty in rows[0] else None
 axes[0].errorbar(n,[v[key] for v in rows],yerr=errors,fmt=marker,ms=5,lw=1.5,capsize=3,color=skh.C['teal'],label=label)
 b=d['binodal']
 if b:axes[0].axhline(b[key],color=skh.C['amber'],lw=1.5,ls='-' if key=='xAlpha' else '--',label='Predicted '+('α' if key=='xAlpha' else 'β'))
axes[0].set(xlabel='Observation pair',ylabel='Component 1 mole fraction',ylim=(0,1),xlim=(.5,len(rows)+.5),xticks=n)
curve=d['curve']
for key,label,color,style in [('g','Fitted liquid','amber','-'),('hull','Convex envelope','graphite','--')]:
 axes[1].plot([v['x'] for v in curve],[v[key] for v in curve],color=skh.C[color],lw=1.5,ls=style,label=label)
for i,b in enumerate(d['gaps']):
 axes[1].plot([b['xAlpha'],b['xBeta']],[b['gAlpha'],b['gBeta']],'o-',ms=5,lw=1.5,color=skh.C['graphite'],label='Common tangent' if i==0 else None)
if not curve:axes[1].text(.5,.5,'Stability unresolved',ha='center',transform=axes[1].transAxes)
axes[1].set(xlabel='Component 1 mole fraction',ylabel='Mixing Gibbs energy / RT',xlim=(0,1))
for ax in axes:ax.legend(frameon=False,fontsize=8)
p=r['parameters'];fig.suptitle(f"{dataset['name']} · {r['T']:g} K\nτ₁₂={p['tau12']:.4f}, τ₂₁={p['tau21']:.4f}, α={p['alpha']:g}",fontsize=11)
fig.savefig(out.with_suffix('.pdf'));fig.savefig(out.with_suffix('.png'),dpi=600)
