"""Regenerate Lab 07 exported energy plot: absolute Python script study.json output-prefix."""
import json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
s=json.loads(Path(sys.argv[1]).read_text());r=s['result'];q=s['curve'];out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
fig,ax=plt.subplots(figsize=(7,4.8),layout='constrained')
ax.plot([v['T'] for v in q for _ in range(2)],[h for v in q for h in [v['min'],v['max']]],color=skh.C['teal'],lw=1.5,label='Equilibrium outlet enthalpy')
ax.axhline(r['H'],color=skh.C['amber'],lw=1.5,ls='--',label='Feed enthalpy')
ax.plot(r['T'],r['Hout'],'D',ms=5,color=skh.C['graphite'],label='Energy-balanced outlet')
ax.set(xlabel='Outlet temperature / K',ylabel='Molar enthalpy / J mol⁻¹',title=f"Synthetic adiabatic flash: P={r['P']/1000:g} kPa, z₁={r['z']:g}")
ax.legend(frameon=False);fig.savefig(out.with_suffix('.pdf'));fig.savefig(out.with_suffix('.png'),dpi=600)
