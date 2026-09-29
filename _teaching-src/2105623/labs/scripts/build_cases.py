"""Re-solve every selectable case; never interpolate optimization outcomes."""
from pathlib import Path
import sys,json,importlib.metadata,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from models import food_manufacture as fm,blending as blend,hydrogen as h2
from models.common import solve,audit,value
from figures.charts import chart
from plotly.offline import get_plotlyjs

OUT=ROOT/'assets';OUT.mkdir(exist_ok=True)

def control(id,label,values,default):return dict(id=id,label=label,values=values,default=default)
def key(*values):return '|'.join(f'{v:g}' for v in values)
def checks(*pairs):return [{'name':a,'value':b} for a,b in pairs]

def food_case(holding,cap):
    m=solve(fm.build_model(storage_cost=holding,vegetable_capacity=cap));fm.validate(m)
    stock=[2500]+[sum(value(m.stock[i,t]) for i in m.I) for t in m.T]
    prod=[value(m.product[t]) for t in m.T];buy=[sum(value(m.buy[i,t]) for i in m.I) for t in m.T]
    tight=sum(abs(cap-sum(value(m.use[i,t]) for i in m.V))<1e-6 for t in m.T)
    return {'objective':value(m.profit),'secondary':sum(prod),'tertiary':sum(stock[1:])/6,'parameters':{'holding':holding,'cap':cap},
            'raw':{'inventory':stock,'production':prod,'purchases':buy},
            'checks':checks(('Monthly inventory balances','Passed'),('Initial and final stock','500 t per oil'),('Blend hardness bounds','3 to 6, all months'),('Vegetable capacity binding',f'{tight} of 6 months')),
            'table':{'columns':['Month','Product (t)','Purchases (t)','Closing stock (t)'],'rows':[[s,prod[j],buy[j],stock[j+1]] for j,s in enumerate(fm.MONTHS)]},
            'audit':audit(m)}

food={'title':'Food manufacture','eyebrow':'Volume 1 · Problem 1','question':'What is inventory flexibility worth?',
      'intro':'Change the monthly holding charge and vegetable refining capacity. Compare the six-month production and inventory plan with the original case.',
      'objectiveLabel':'Six-month profit','unit':'GBP','sense':'maximize','secondaryLabel':'Total product (t)','tertiaryLabel':'Mean closing stock (t)',
      'baseline':'5|200','controls':[control('holding','Holding charge (GBP/t/month)',[0,2,5,8,10],5),control('cap','Vegetable capacity (t/month)',[150,200,250],200)],
      'charts':{'inventory':'Inventory','production':'Production','purchases':'Purchases'},
      'book':'../books/volume-1/chapters/01-food-manufacture.html',
      'assumptions':'Five oils, six months, 150 GBP/t selling price. Nonvegetable capacity is 250 t/month. Each oil starts and ends at 500 t. Holding is charged on all six closing stocks, including June.',
      'equations':[{'label':'Inventory balance','math':'previous stock + purchases = processing + closing stock','why':'Purchases can be shifted between months, but mass cannot disappear. Each oil has its own balance.'},
                   {'label':'Profit','math':'sales revenue − purchases − holding charges','why':'A lower holding charge changes the objective coefficients. It does not create new refining capacity.'}],
      'challenge':'Find a case with lower holding charges but unchanged total production. Explain where the profit improvement comes from.', 'cases':{}}
for a in [0,2,5,8,10]:
 for b in [150,200,250]:food['cases'][key(a,b)]=food_case(a,b)
base=food['cases'][food['baseline']]
for c in food['cases'].values():
 c['figures']={n:chart(['Start']+fm.MONTHS if n=='inventory' else fm.MONTHS,base['raw'][n],c['raw'][n], 'Stock (t)' if n=='inventory' else 'Flow (t/month)', 'line' if n=='inventory' else 'bar') for n in food['charts']}
 c['interpretation']=f"Profit changes by {c['objective']-base['objective']:,.2f} GBP relative to the fixed baseline. The plant produces {c['secondary']:,.1f} t over six months. Holding charges apply to every month-end stock, including the restored June reserve. Compare inventory and purchases to explain the result."

blending={'title':'Robust blending','eyebrow':'Volume 2 · Problems 1–3','question':'How much protection will you buy?',
          'intro':'Increase the uncertainty budget or tighten the quality specification. Watch the least-cost recipe change and distinguish protected quality from a full-box stress test.',
          'objectiveLabel':'Daily blend cost','unit':'USD/d','sense':'minimize','secondaryLabel':'Protected impurity (%)','tertiaryLabel':'Full-box impurity (%)',
          'baseline':'0|7','controls':[control('gamma','Uncertainty budget Γ',[0,.5,1,1.5,2,2.5,3],0),control('limit','Impurity limit (%)',[6,7,8],7)],
          'charts':{'recipe':'Blend recipe'},'book':'../books/volume-2/chapters/03-blending.html',
          'assumptions':'100 t/day of product; each feed is limited to 60 t/day. Costs are 100, 80, and 55 USD/t. Nominal impurity is 2%, 8%, and 14%; upward deviations are 1, 2, and 3 percentage points. Γ is an uncertainty-set budget, not a probability.',
          'equations':[{'label':'Mass balance','math':'xA + xB + xC = 100 t/day','why':'A cheap feed can only replace another feed; it cannot change the production target.'},
                       {'label':'Robust quality','math':'nominal impurity load + worst permitted deviation ≤ limit × 100','why':'The worst permitted deviation is calculated over the selected uncertainty budget. Full-box protection requires Γ = 3.'}],
          'challenge':'At a 7% limit, compare Γ = 0, 1.5, and 3. Explain why the intermediate recipe can pass its protected check but fail the full-box stress test.','cases':{}}
for gamma in [0,.5,1,1.5,2,2.5,3]:
 for limit in [6,7,8]:
  blend.LIMIT=limit/100;m=solve(blend.build(3,gamma));blend.check(m,3);r=blend.report(m,3)
  vals=[value(m.x[i]) for i in m.I]
  c={'objective':r['objective'],'secondary':r['metrics']['Protected impurity (%)'],'tertiary':r['metrics']['Full-box impurity (%)'],
     'parameters':{'gamma':gamma,'limit':limit},'raw':{'recipe':vals},'audit':audit(m),
     'checks':checks(('Total blend','100 t/day'),('Protected quality',f"{r['metrics']['Protected impurity (%)']:.3f}% ≤ {limit}%"),('Feed availability','All feeds ≤ 60 t/day'),('Full-box stress test','Pass' if r['metrics']['Full-box impurity (%)']<=limit+1e-6 else 'Fails outside selected protection')),
     'table':{'columns':['Feed','Flow (t/day)','Cost (USD/t)','Nominal impurity (%)'],'rows':[[i,vals[j],blend.COST[i],100*blend.NOMINAL[i]] for j,i in enumerate(m.I)]}}
  blending['cases'][key(gamma,limit)]=c
blend.LIMIT=.07
base=blending['cases']['0|7']
for c in blending['cases'].values():
 c['figures']={'recipe':chart(['A','B','C'],base['raw']['recipe'],c['raw']['recipe'],'Feed (t/day)','bar')}
 c['interpretation']=f"The selected design costs {c['objective']:,.2f} USD/day, compared with {base['objective']:,.2f} for the nominal 7% baseline. Its full-box impurity is {c['tertiary']:.3f}%. A smaller uncertainty budget does not guarantee the full-box specification. If both controls change, the cost difference combines both effects."

hydrogen={'title':'Hydrogen storage','eyebrow':'Volume 2 · Problems 13–14','question':'Store hydrogen or buy expensive power?',
          'intro':'Choose a tank size and change electricity prices during periods 3 and 4. Compare total daily cost, including the same capacity charge for every tank.',
          'objectiveLabel':'Total daily cost','unit':'USD/d','sense':'minimize','secondaryLabel':'Electricity cost (USD/d)','tertiaryLabel':'Capacity charge (USD/d)',
          'baseline':'150|1','controls':[control('tank','Tank capacity (kg)',[50,100,150,200,300,400,420,450,500],150),control('peak','Period 3–4 price multiplier',[.75,1,1.25,1.5],1)],
          'charts':{'inventory':'Inventory','power':'Electrolyzer power'},'book':'../books/volume-2/chapters/14-hydrogen.html',
          'assumptions':'Six four-hour periods; power ≤ 4 MW; 0.05 MWh/kg; initial and final stock 50 kg. Capacity costs 0.15 USD/(kg day). Production and withdrawal are uniform within each period. No startup charges or minimum load in this experiment.',
          'equations':[{'label':'Hydrogen balance','math':'end stock = previous stock + 4 × power / 0.05 − demand','why':'Power is in MW. Multiply by four hours before converting electricity to kilograms.'},
                       {'label':'Daily cost','math':'Σ(price × 4 × power) + 0.15 × tank capacity','why':'Every comparison includes ownership cost. A larger tank can move production in time without reducing daily energy use.'}],
          'challenge':'At the original prices, find the best tank in the selectable menu. Explain why increasing capacity beyond that point can raise total cost.','cases':{}}
prices=list(h2.PRICE)
for tank in [50,100,150,200,300,400,420,450,500]:
 for peak in [.75,1,1.25,1.5]:
  h2.PRICE=[v*(peak if j in [2,3] else 1) for j,v in enumerate(prices)]
  m=h2.build(2);m.k.fix(tank);solve(m);h2.check(m,2)
  stock=[50]+[value(m.stock['nominal',t]) for t in m.T];power=[value(m.power['nominal',t]) for t in m.T]
  c={'objective':value(m.obj),'secondary':value(m.obj)-.15*tank,'tertiary':.15*tank,'parameters':{'tank':tank,'peak':peak},
     'raw':{'inventory':stock,'power':power},'audit':audit(m),
     'checks':checks(('Daily production','990 kg'),('Daily electricity','49.5 MWh'),('Final stock','50 kg'),('Capacity and power bounds','Passed')),
     'table':{'columns':['Period','Price (USD/MWh)','Power (MW)','End stock (kg)'],'rows':[[j+1,h2.PRICE[j],power[j],stock[j+1]] for j in range(6)]}}
  hydrogen['cases'][key(tank,peak)]=c
h2.PRICE=prices
base=hydrogen['cases']['150|1']
for c in hydrogen['cases'].values():
 c['figures']={'inventory':chart(list(range(7)),base['raw']['inventory'],c['raw']['inventory'],'Inventory (kg)',capacity=c['parameters']['tank']),
               'power':chart(list(range(1,7)),base['raw']['power'],c['raw']['power'],'Power (MW)','bar')}
 best=min((q for q in hydrogen['cases'].values() if q['parameters']['peak']==c['parameters']['peak']),key=lambda q:q['objective'])
 c['interpretation']=f"The {c['parameters']['tank']} kg tank incurs {c['secondary']:,.2f} USD/day for electricity and {c['tertiary']:,.2f} USD/day for capacity. All cases consume 49.5 MWh/day. Storage changes when electricity is bought, not conversion efficiency. The baseline always uses the original prices and a 150 kg tank."

payload={'mode':'precomputed-exact','solver':'Pyomo + HiGHS','labs':{'food':food,'blend':blending,'hydrogen':hydrogen},
         'versions':{n:importlib.metadata.version(n) for n in ['pyomo','highspy','plotly']},
         'models':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'models').glob('*.py')}}
allcases=[c for lab in payload['labs'].values() for c in lab['cases'].values()]
assert len(allcases)==72 and max(c['audit'] for c in allcases)<=1e-6
assert abs(food['cases']['5|200']['objective']-107842.59259259)<1e-5
assert abs(blending['cases']['3|7']['objective']-8771.42857143)<1e-5
assert abs(hydrogen['cases']['420|1']['objective']-1635.5)<1e-6
(OUT/'cases.json').write_text(json.dumps(payload,separators=(',',':')))
(OUT/'plotly.min.js').write_text(get_plotlyjs())
with zipfile.ZipFile(OUT/'lab-models.zip','w',zipfile.ZIP_DEFLATED) as z:
 for folder in ['models','figures','styles','scripts']:
  for p in (ROOT/folder).rglob('*.py'):
   if '__pycache__' not in p.parts:z.write(p,p.relative_to(ROOT))
 z.write(ROOT/'styles/skh_lab.mplstyle','styles/skh_lab.mplstyle')
 for p in [ROOT/'README.md',ROOT/'requirements.txt']:z.write(p,p.name)
print(f'Prepared and audited {len(allcases)} exact cases; largest residual {max(c["audit"] for c in allcases):.2e}.')
