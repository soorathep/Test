"""Recreate Lab 06 Gibbs and P-x-y figures from a study JSON.
~/.venvs/research/bin/python figures/regenerate_vlle.py study.json output-prefix
"""
import json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
s=json.loads(Path(sys.argv[1]).read_text());r=s['result'];curve=s['curve'];diagram=s['pressureDiagram'];out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
fig,axes=plt.subplots(1,2,figsize=(10,4.8),layout='constrained')
for key,label,color,style in [('gL','Liquid','teal','-'),('gV','Vapor','amber','-'),('hull','Global envelope','graphite','--')]:
 axes[0].plot([v['x'] for v in curve],[v[key] for v in curve],label=label,color=skh.C[color],ls=style,lw=1.5)
p=sorted(r['phases'],key=lambda p:p['x'])
if len(p)>1:axes[0].plot([v['x'] for v in p],[v['g'] for v in p],'o-',ms=5,lw=1.5,color=skh.C['graphite'],label='Coexistence')
axes[0].plot(r['z'],r['equilibriumG'],'D',ms=5,color=skh.C['graphite'],label='Equilibrium feed')
for key,label,color in [('x','Bubble branches','teal'),('y','Dew branches','amber')]:
 axes[1].plot([v[key] for v in diagram['points']],[v['P'] for v in diagram['points']],color=skh.C[color],lw=1.5,label=label)
for i,t in enumerate(diagram['triples']):
 xs=sorted([t['xAlpha'],t['xBeta'],t['y']]);axes[1].plot([xs[0],xs[-1]],[t['P'],t['P']],color=skh.C['graphite'],lw=1.5,ls='--',label='VLLE pressure' if i==0 else None)
 axes[1].plot([t['xAlpha'],t['xBeta']],[t['P'],t['P']],'o',ms=5,color=skh.C['teal'])
 axes[1].plot(t['y'],t['P'],'D',ms=5,color=skh.C['amber'])
axes[1].plot(r['z'],r['P'],'D',ms=5,color=skh.C['graphite'],label='Current feed')
for ax in axes:ax.set(xlim=(0,1),xlabel='Component 1 mole fraction');ax.legend(frameon=False,fontsize=8)
if s.get('view',{}).get('zoom',True):
 gL=[v['gL'] for v in curve];vmin=min(v['gV'] for v in curve);lo=min(*gL,vmin);hi=max(*gL,vmin);pad=max(.02,.15*(hi-lo));axes[0].set_ylim(lo-pad,hi+pad);axes[0].set_title('Near phase minima; higher-energy segments clipped',fontsize=8)
axes[0].set_ylabel('Molar Gibbs energy / RT · common reference');axes[1].set_ylabel('Pressure / kPa')
A=r['A'];label=f"A={A:g}" if isinstance(A,(int,float)) else (f"NRTL: τ₁₂={A['tau12']:g}, τ₂₁={A['tau21']:g}, α={A['alpha']:g}" if A.get('model')=='nrtl' else f"A₁₂={A['A12']:g}, A₂₁={A['A21']:g}")
fig.suptitle(f"Synthetic activity model + ideal vapor · {label}\nP={r['P']:.4f} kPa, z₁={r['z']:g} · {r['type']}",fontsize=11)
fig.savefig(out.with_suffix('.pdf'));fig.savefig(out.with_suffix('.png'),dpi=600)
