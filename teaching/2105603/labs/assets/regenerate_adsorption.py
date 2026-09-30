"""Recreate a Lab 11 model or data study from exported JSON."""
import json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
s=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
models=['henry','langmuir','freundlich','bet'];styles=[':', '-', '--', '-.']
def uptake(m,P,p):
 if m=='henry':return p['K']*P
 if m=='langmuir':return p['qs']*p['b']*P/(1+p['b']*P)
 if m=='freundlich':return p['K']*P**p['m']
 r=P/p['P0'];return p['qm']*p['C']*r/((1-r)*(1+(p['C']-1)*r))
if s['kind']=='models':
 fig,ax=plt.subplots(figsize=(7,5),layout='constrained');q=s['curves']
 for m,ls,color in zip(models,styles,[skh.C['teal'],skh.C['amber'],skh.C['rust'],skh.C['skyblue']]):ax.plot([r['P'] for r in q],[float('nan') if r[m] is None else r[m] for r in q],label=m.title(),ls=ls,lw=1.5,color=color)
 ax.set(xlabel='Adsorbate pressure / kPa',ylabel='Absolute uptake / mol kg⁻¹',title=f"Parameters at {s['input']['T']:g} K");ax.legend(frameon=False)
else:
 fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained');ax=axes[0];group=s['groups'][0];obs=[r for r in s['dataset']['rows'] if r['T']==group['T']]
 ax.plot([r['P'] for r in obs],[r['q'] for r in obs],'o',ms=4,color=skh.C['teal'],label='Observed')
 for m,ls in zip(models,styles):
  f=group['fits'][m]
  if 'unavailable' in f:continue
  P=np.linspace(*f['range'],101);ax.plot(P,uptake(m,P,f['parameters']),lw=1.5,ls=ls,color=skh.C['amber'],label=m.title())
 ax.set(xlabel='Adsorbate pressure / kPa',ylabel='Absolute uptake / mol kg⁻¹',title=f"Independent fits at {group['T']:g} K");ax.legend(frameon=False)
 heat=s['heat'];ax=axes[1]
 if 'points' in heat:
  values=[r['Qst']/1000 for r in heat['points']];lo=min(values);hi=max(values);center=(lo+hi)/2;half=max((hi-lo)*.6,1,abs(center)*.05)
  ax.plot([r['q'] for r in heat['points']],values,'-o',ms=4,lw=1.5,color=skh.C['amber']);ax.set_ylim(center-half,center+half)
 else:ax.text(.5,.5,'Isosteric heat unavailable',transform=ax.transAxes,ha='center',color=skh.C['graphite'])
 ax.set(xlabel='Absolute loading / mol kg⁻¹',ylabel='Qst / kJ mol⁻¹')
fig.savefig(out.with_suffix('.pdf'));fig.savefig(out.with_suffix('.png'),dpi=600)
