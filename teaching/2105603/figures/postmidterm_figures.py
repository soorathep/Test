"""Regenerate the new post-midterm synthetic scientific figures."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
out=Path(__file__).resolve().parent
P=np.linspace(0,50,301); qs=2.; b=.1
fig,ax=plt.subplots(figsize=(9,4.6),layout='constrained')
ax.plot(P,qs*b*P,color=skh.C['teal'],lw=1.8,label='Henry: K = 0.2 mol kg⁻¹ kPa⁻¹')
ax.plot(P,qs*b*P/(1+b*P),color=skh.C['amber'],lw=1.8,label='Langmuir: qₛ = 2 mol/kg, b = 0.1 kPa⁻¹')
ax.axhline(qs,color=skh.C['graphite'],lw=1.5,ls=':',label='Langmuir saturation loading')
ax.set(xlabel='Pressure / kPa',ylabel='Absolute uptake / mol kg⁻¹',title='Synthetic comparison at one fixed temperature')
ax.legend(frameon=False,fontsize=10)
fig.savefig(out/'postmidterm-adsorption.pdf');fig.savefig(out/'postmidterm-adsorption.png',dpi=600);plt.close(fig)
R=8.31446261815324; F=96485.33212331002; T=298.15; n=2
logratio=np.linspace(-3,3,301); E=-R*T*np.log(10)*logratio/(n*F)
fig,ax=plt.subplots(figsize=(9,4.6),layout='constrained')
ax.plot(logratio,E*1000,color=skh.C['teal'],lw=1.8,label='Identical-electrode Nernst relation')
ax.plot(-2, -R*T*np.log(.01)/(n*F)*1000,'o',ms=6,color=skh.C['amber'],label='aL/aR = 0.01')
ax.axhline(0,color=skh.C['graphite'],lw=1.5,ls=':')
ax.set(xlabel='log₁₀(aL/aR)',ylabel='Cell potential / mV',title='Synthetic concentration cell: 298.15 K, n = 2')
ax.legend(frameon=False,fontsize=10)
fig.savefig(out/'postmidterm-cell.pdf');fig.savefig(out/'postmidterm-cell.png',dpi=600);plt.close(fig)
print('Generated two vector PDFs and 600 dpi PNGs')
