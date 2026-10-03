"""Regenerate the synthetic teaching figures, using Teal-Amber Lab Palette v1.0."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans','font.size':11,'axes.labelsize':11,'lines.linewidth':1.8})
C=skh.C
OUT=Path(__file__).resolve().parent/'generated'
OUT.mkdir(exist_ok=True)
R=8.314462618

def canvas():
    fig,ax=plt.subplots(figsize=(7.2,3.5),layout='constrained')
    ax.spines[['top','right']].set_visible(False)
    ax.grid(alpha=.17)
    return fig,ax

def save(fig,name):
    fig.savefig(OUT/f'preclass-{name}.pdf')
    fig.savefig(OUT/f'preclass-{name}.png',dpi=600)
    plt.close(fig)

f,a=canvas(); x=np.linspace(0,1,501)
a.plot(x,60+90*x,color=C['teal'],label='Bubble boundary (liquid x₁)')
a.plot(x,1/(x/150+(1-x)/60),color=C['amber'],label='Dew boundary (vapor y₁)')
xl=(95-60)/90; yv=xl*150/95
a.plot([xl,yv],[95,95],color=C['graphite'],marker='o',markersize=5)
a.axvline(.5,color=C['graphite'],ls=':',lw=1.5)
a.scatter([.5],[95],color=C['amber'],s=38,zorder=5)
a.text(.13,125,'LIQUID',color=C['graphite']); a.text(.69,76,'VAPOR',color=C['graphite'])
a.annotate('95 kPa tie line',(.5,95),(.05,88),arrowprops={'arrowstyle':'->','color':C['graphite']},color=C['graphite'])
a.set(xlim=(0,1),ylim=(55,155),xlabel='Component-1 mole fraction: x₁, y₁ or z₁',ylabel='Pressure / kPa')
a.legend(fontsize=9,loc='upper left');save(f,'vle')

f,a=canvas(); x=np.linspace(.00001,.99999,2001)
g=lambda x:x*np.log(x)+(1-x)*np.log(1-x)+3*x*(1-x)
lo,hi=.00001,.2
for _ in range(80):
    mid=(lo+hi)/2
    if np.log(mid/(1-mid))+3*(1-2*mid)>0:hi=mid
    else:lo=mid
alpha=(lo+hi)/2; beta=1-alpha
assert abs(np.log(alpha/(1-alpha))+3*(1-2*alpha))<1e-10
assert np.min(g(x)-g(alpha))>-1e-8
a.plot(x,g(x),color=C['teal'],label='Homogeneous liquid: Margules A = 3')
a.plot([0,1],[g(alpha)]*2,color=C['graphite'],ls='--',label='Supporting common tangent')
a.fill_between(x,g(alpha),g(x),where=(x>=alpha)&(x<=beta),color=C['sand'],alpha=.65)
a.plot([alpha,beta],[g(alpha)]*2,'o',color=C['amber'],ms=6,label=f'Coexistence: {alpha:.4f}, {beta:.4f}')
a.set(xlim=(0,1),ylim=(-.07,.105),xlabel='Liquid mole fraction x₁',ylabel='Mixing Gibbs energy / RT');a.legend(fontsize=9,loc='upper center');save(f,'lle')

f,a=canvas(); n=np.linspace(0,.012,401); cap=10/(R*300)
a.plot(n,np.minimum(n*R*300,10),color=C['teal'],label='Equilibrium gas pressure')
a.axvline(cap,color=C['graphite'],ls='--',lw=1.5,label='Solid-depletion boundary')
a.plot([.002,.01],[.002*R*300,10],'o',color=C['amber'],ms=6,label='Hand examples')
a.set(xlabel='Total amount / mol',ylabel='Pressure / kPa',ylim=(0,12))
a.legend(fontsize=9,loc='lower right');save(f,'gse')

f,a=canvas(); u=np.linspace(.000001,.999999,1001); lk=4000/(R*350); k=np.exp(lk); ue=np.sqrt(k/(k+4))
G=lambda u:(1-u)*np.log((1-u)/(1+u))+2*u*np.log(2*u/(1+u))-lk*u
a.plot(u,G(u),color=C['teal'],label='Gibbs energy along feasible extent')
a.plot([ue],[G(ue)],'o',color=C['amber'],ms=6,label=f'Minimum: ξ/n₀ = {ue:.5f}')
a.axvline(ue,color=C['graphite'],ls=':',lw=1.5)
a.set(xlabel='Normalized extent ξ/n₀ (n₀ = 1 mol A₂)',ylabel='G / (n₀RT), chosen reference',xlim=(0,1))
a.legend(fontsize=9);save(f,'reaction')

f,a=canvas(); r=np.linspace(-3,3,401); slope=R*298.15*np.log(10)/(2*96485.33212)
a.plot(r,slope*r,color=C['teal'],label='Same M²⁺/M couple at 298.15 K')
a.axhline(0,color=C['graphite'],lw=1.5);a.axvline(0,color=C['graphite'],lw=1.5)
a.plot([2],[2*slope],'o',color=C['amber'],ms=6,label='aRight/aLeft = 100')
a.set(xlabel='log₁₀(aRight/aLeft)',ylabel='Eright − Eleft / V');a.legend(fontsize=9);save(f,'cell')
print(f'Generated five vector and 600 dpi figures in {OUT}')
