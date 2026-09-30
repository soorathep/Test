"""Recreate Lab 12 log K and reaction Gibbs-energy plots from exported JSON."""
import json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
s=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
fig,axes=plt.subplots(1,2,figsize=(11,4.7),layout='constrained');ax=axes[0];q=s['curve'];inputs=s['input'];R=8.31446261815324
for key,label,color,style in [('vh','Kref, constant H',skh.C['teal'],'-'),('hs','H/S, constant values',skh.C['teal'],'--'),('vhCp','Kref, Cp corrected',skh.C['amber'],'-'),('hsCp','H/S, Cp corrected',skh.C['amber'],'--')]:
 ax.plot([v['T'] for v in q],[v[key] for v in q],label=label,color=color,lw=1.5,ls=style)
for T,G,label,marker in [(inputs['Tdirect'],inputs['Gdirect'],'Direct Gibbs energy','o'),(inputs['Tformation'],s['formationG'],'Formation energies','D')]:
 if inputs['Tmin']<=T<=inputs['Tmax']:ax.plot(T,-G/(R*T),marker,ms=5,color=skh.C['graphite'],label=label)
ax.set(xlabel='Temperature / K',ylabel='ln K');ax.legend(frameon=False,fontsize=8)
ax=axes[1];x=s['equilibrium']
if 'unavailable' in x:ax.text(.5,.5,'Extent unavailable for these inputs',transform=ax.transAxes,ha='center',color=skh.C['graphite'])
else:
 ax.plot([v['xi'] for v in x['curve']],[v['relativeG'] for v in x['curve']],color=skh.C['teal'],lw=1.5,label='Ideal-gas reaction path')
 ax.plot(x['xi'],x['relativeG'],'o',ms=5,color=skh.C['amber'],label='Equilibrium');ax.legend(frameon=False)
ax.set(xlabel='Reaction extent / mol',ylabel='[G(ξ) − G(0)] / RT · mol')
fig.savefig(out.with_suffix('.pdf'));fig.savefig(out.with_suffix('.png'),dpi=600)
