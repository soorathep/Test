"""Regenerate a thermodynamics diagram from the exported experiment JSON.

Run with your absolute research interpreter:
  ~/.venvs/research/bin/python figures/regenerate.py experiment.json --output figure
Requires numpy, matplotlib, and the lab's skh_palette module on PYTHONPATH.
Writes vector PDF and 600 dpi PNG. Check the PDF with pdffonts (no Type 3).
"""
import argparse
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
import skh_palette as skh
skh.use()
mpl.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,'ps.fonttype':42,'lines.linewidth':1.8,'lines.markersize':5})

def make_figure(data, output):
    kind=data['inputs']['chart']
    selected=data['curves']['selected']
    ideal=data['curves']['ideal']
    f=data['result']
    model=f.get('model',{'nonideal':bool(f['A']),'name':'Margules model' if f['A'] else 'Ideal model'})
    nonideal=model['nonideal']
    fig,ax=plt.subplots(figsize=(7,4.8))
    if kind=='rr':
        if not data['chartRows']: raise ValueError('No Rachford-Rice curve at this state.')
        points=data['chartRows']
        ax.plot([p['beta'] for p in points],[p['F'] for p in points],color=skh.C['amber'] if nonideal else skh.C['teal'],label='Converged K values')
        ax.axhline(0,color=skh.C['graphite'],lw=1.5,ls=':')
        ax.plot(f['beta'],0,'D',color=skh.C['graphite'],label='Flash root')
        ax.set(xlabel='Vapor fraction β',ylabel='Rachford–Rice F(β)')
    else:
        sets=[('Ideal reference',ideal,skh.C['teal'])] if data['inputs']['compare'] and nonideal else []
        sets.append((model['name'],selected,skh.C['amber'] if nonideal else skh.C['teal']))
        for name,points,color in sets:
            xs=[p['x'] for p in points];ys=[float('nan') if p['y'] is None else p['y'] for p in points]
            if kind=='gamma':
                ax.plot(xs,[p['gamma'][0] for p in points],color=color,label=f'{name}: γ₁')
                ax.plot(xs,[p['gamma'][1] for p in points],color=color,ls='--',label=f'{name}: γ₂')
            elif kind=='xy': ax.plot(xs,ys,color=color,label=name)
            else:
                k='P' if kind=='pxy' else 'T';scale=1000 if kind=='pxy' else 1
                values=[float('nan') if p[k] is None else p[k]/scale for p in points]
                ax.plot(xs,values,color=color,label=f'{name}: bubble')
                ax.plot(ys,values,color=color,ls='--',label=f'{name}: dew')
        if kind=='gamma':
            ax.set(xlabel='Liquid mole fraction x₁',ylabel='Activity coefficient γᵢ')
        elif kind=='xy':
            ax.plot([0,1],[0,1],':',color=skh.C['graphite'],label='y₁ = x₁')
            ax.set(xlabel='Liquid mole fraction x₁',ylabel='Vapor mole fraction y₁',ylim=(0,1))
        else:
            level=f['P']/1000 if kind=='pxy' else f['T']
            if f['x'] is not None and f['y'] is not None: ax.plot([f['x'],f['y']],[level,level],'o:',color=skh.C['graphite'],label='Current tie line')
            ax.plot(f['z'],level,'D',mfc='none',color=skh.C['graphite'],label='Feed')
            ax.set(xlabel='Mole fraction of component 1',ylabel='Pressure (kPa)' if kind=='pxy' else 'Temperature (K)')
    ax.set_xlim(0,1)
    title=data['propertyRecord']['label']
    ax.set_title(title,fontsize=11)
    ax.legend(fontsize=8,loc='best',frameon=False)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(output.with_suffix('.pdf'))
    fig.savefig(output.with_suffix('.png'),dpi=600)
    plt.close(fig)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('experiment');p.add_argument('--output',default='thermodynamics-figure')
    args=p.parse_args();make_figure(json.loads(Path(args.experiment).read_text()),args.output)
