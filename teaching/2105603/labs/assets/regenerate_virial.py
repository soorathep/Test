"""Reproduce Lab 09 exported fugacity and compressibility curves from study JSON."""
import json, sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
s=json.loads(Path(sys.argv[1]).read_text()); q=s['curve']; out=Path(sys.argv[2])
out.parent.mkdir(parents=True,exist_ok=True)
x=[v['x'] for v in q]
fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax in axes:
 ax.axhline(1,color=skh.C['teal'],lw=1.5,label='Ideal vapor')
 ax.set(xlabel='Trial vapor mole fraction y₁',xlim=(0,1))
for i,ls in [(0,'-'),(1,'--')]:
 axes[0].plot(x,[v['phi'][i] for v in q],color=skh.C['amber'],ls=ls,lw=1.5,label=f'Virial φ{i+1}')
axes[1].plot(x,[v['Z'] for v in q],color=skh.C['amber'],lw=1.5,label='Virial vapor')
axes[0].set_ylabel('Fugacity coefficient');axes[1].set_ylabel('Compressibility factor Z')
for ax in axes: ax.legend(frameon=False)
fig.suptitle(f"T={s['input']['T']:g} K, P={s['input']['P']/1000:g} kPa; trial vapor compositions")
fig.savefig(out.with_suffix('.pdf'));fig.savefig(out.with_suffix('.png'),dpi=600)
