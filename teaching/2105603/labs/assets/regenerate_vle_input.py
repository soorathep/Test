"""Regenerate an imported VLE study figure: study.json output-prefix."""
import json,sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import skh_palette as skh
skh.use()
plt.rcParams.update({'pdf.fonttype':42,'ps.fonttype':42,'font.family':'DejaVu Sans'})
s=json.loads(Path(sys.argv[1]).read_text());rows=s['set']['valid'];fit=s.get('fit');out=Path(sys.argv[2]);out.parent.mkdir(parents=True,exist_ok=True)
fig,axes=plt.subplots(1,2,figsize=(10,4.5),layout='constrained')
for ax,key,pred,label in [(axes[0],'PkPa','Pcalc','Pressure / kPa'),(axes[1],'y','ycalc','Vapor mole fraction y₁')]:
 ax.plot([r['x'] for r in rows],[r[key] for r in rows],'o',ms=5,color=skh.C['teal'],label='Observed')
 if fit:ax.plot([r['x'] for r in fit['points']],[r[pred] for r in fit['points']],color=skh.C['amber'],lw=1.5,label='Fitted at measured T')
 ax.set(xlabel='Liquid mole fraction x₁',ylabel=label,xlim=(0,1));ax.legend(frameon=False)
fig.suptitle(s['set']['name'],fontsize=12);fig.savefig(out.with_suffix('.pdf'));fig.savefig(out.with_suffix('.png'),dpi=600)
