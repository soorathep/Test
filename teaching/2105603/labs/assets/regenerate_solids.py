"""Recreate a Lab 10 study figure: study.json output-prefix."""
import json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
s=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
fig,ax=plt.subplots(figsize=(7,5),layout='constrained')
if s['mode']=='sle':
 for group,label,color in [(s['ideal'],'Ideal liquid',skh.C['teal']),(s['curves'],'Selected liquid',skh.C['amber'])]:
  for j,b in enumerate(group['branches']):ax.plot([v['x'] for v in b],[float('nan') if v['T'] is None else v['T'] for v in b],lw=1.5,ls='--' if j else '-',color=color,label=f'{label}, solid {j+1}')
 te=s['curves']['eutectic'].get('T')
 if te:ax.axhline(te,lw=1.5,ls=':',color=skh.C['graphite'],label='Eutectic')
 ax.plot(s['input']['z'],s['input']['T'],'o',ms=5,color=skh.C['graphite'],label='Feed')
 ax.set(xlabel='Component 1 mole fraction',ylabel='Temperature / K',xlim=(0,1))
else:
 q=s['curves']
 for key,label,color,ls in [('ps','Sublimation pressure',skh.C['teal'],'-'),('partial','Actual partial pressure',skh.C['amber'],'-'),('total','Total pressure',skh.C['graphite'],'--')]:
  ax.plot([v['T'] for v in q],[v.get(key,float('nan'))/1000 for v in q],color=color,ls=ls,lw=1.5,label=label)
 ax.set(xlabel='Temperature / K',ylabel='Pressure / kPa')
ax.legend(frameon=False);fig.savefig(out.with_suffix('.pdf'));fig.savefig(out.with_suffix('.png'),dpi=600)
