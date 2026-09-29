"""Prepare one independently checked experiment for every workbook problem."""
from pathlib import Path
import sys, json, importlib, copy, hashlib, zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import pyomo.environ as p
from models.common import solve, audit, value
from figures.charts import chart
META=json.loads((ROOT/'scripts/chapter_metadata.json').read_text())
REF=json.loads((ROOT/'scripts/baseline_references.json').read_text())
# label, values, original value, parameterized equation, learning question
SPECS={
2:('Maximum oils per month',[2,3,4],3,'sum(selected oils) <= maximum oils','Does allowing another oil always improve profit? Identify whether the count or a processing constraint is binding.'),
3:('Reactor capacity multiplier',[.8,1,1.2],1,'reactor hours used <= multiplier × original monthly capacity','Does a 20% increase in reactor hours give a 20% increase in contribution? Explain any remaining bottleneck.'),
4:('Reactor maintenance loss (h)',[20,40,60],40,'reactor hours <= 120 − maintenance loss × maintenance indicator','Which maintenance month is selected as downtime grows, and what role does inventory play?'),
5:('Annual retraining capacity (FTE)',[4,6,8],6,'retrained staff <= annual retraining capacity','When does more training capacity substitute for specialist hiring? Explain why the objective can stay unchanged.'),
6:('Gasoline sales ceiling (t/day)',[60,90,110],90,'gasoline output <= sales ceiling','Can the refinery profit from a higher sales ceiling, or do quality and processing limits prevent it?'),
7:('Mine royalty multiplier',[.5,1,2],1,'discounted profit = sum(discount × (margin × extraction − multiplier × royalty × open))','How do royalties affect closure timing? Explain why a closed mine cannot return later.'),
8:('Purchased feed price (thousand USD/t)',[.1,.2,.4],.2,'profit includes − feed price × purchased feed','Does expensive purchased feed change herd size, land allocation, or both? Use the feed balance to explain.'),
9:('Annual labor capacity',[100,110,130],110,'sum(output labor + expansion labor) <= labor capacity','Why does capacity expansion consume resources before it becomes productive? Identify the limiting year.'),
10:('Interunit transport cost multiplier',[0,.5,1,2],1,'total cost = operating cost + multiplier × original transport cost','When does co-location outweigh a low operating cost? Check whether multiple assignments have the same cost.'),
11:('Observed response at input 4',[4,7.5,10],7.5,'minimize sum(abs(observation − fitted response))','Move the outlier and inspect the L1 residuals. Why need the fitted line not pass through every observation?'),
12:('Logic target: 0=XOR, 1=OR, 2=AND',[0,1,2],0,'NOR network output(A,B) = selected truth table target','Which truth table requires the most NOR gates? Verify all four input combinations.'),
13:('Target division share',[.3,.4,.5],.4,'minimize max(abs(division share − target)); 0.25 <= share <= 0.55','Why can the maximum share deviation remain positive even when the target lies within the allowed range?'),
14:('Bottom block value (thousand USD)',[5,18,30],18,'maximize sum(block value × extraction indicator)','Find when deeper extraction becomes attractive. Which negative-value surface blocks must be included?'),
15:('Reserve margin (fraction)',[0,.15,.3],.15,'online capacity >= (1 + reserve margin) × demand','Why can reserve increase commitment cost without increasing delivered energy?'),
16:('Storage energy ceiling (MWh)',[120,180,240],240,'5 <= stored energy <= storage ceiling; final energy = 120 MWh','How much is additional energy capacity worth when charging power and thermal commitment also constrain operation?'),
17:('Number of white markers',[9,13,17],13,'sum(white indicators) = selected count','Relate the marker balance to unavoidable monochromatic lines. Would exchanging both colors preserve the optimum?'),
18:('Absolute coefficient bound',[20,30,40],40,'1 <= abs(integer coefficient) <= bound; preserve all 256 classifications','Does loosening coefficient bounds improve the smallest absolute RHS? Verify equivalence on every binary point.'),
19:('Customer demand multiplier',[.8,1,1.2],1,'customer receipts = multiplier × original demand','How does increasing demand reroute material through depots? Identify the first capacity bottleneck.'),
20:('Depot 2 expansion charge (USD/day)',[0,30,100],30,'cost = transport + depot charges + expansion charge × expansion indicator','Does cheap expansion alter the selected depots? Explain the relationship between opening and expansion decisions.'),
21:('Fat availability (t/day)',[20,22,24],22,'sum(menu fat use × selected menu) <= fat availability','Does more fat allow more revenue, or does the basket-price restriction become limiting?'),
22:('Target plant: 0=A through 5=F',[0,1,2,3,4,5],2,'peer inputs <= efficiency × target inputs; peer output >= target output','Which plants lie on the observed frontier? Explain why a score of one is relative efficiency, not absolute performance.'),
23:('Daily truck capacity (1000 L)',[16,18,20],16,'sum(collection quantity × visit indicator) <= daily capacity','How does a larger truck change the two-day tours while preserving the required visit frequencies?'),
24:('Probability of low demand',[.2,.4,.8],.4,'expected contribution = early contribution + p × low recourse + (1−p) × high recourse − campaign cost','Which decisions are made before demand is known? Explain how changing probability alters the early commitment.'),
25:('Repair capacity multiplier',[.5,1,1.5],1,'repairs at each depot <= multiplier × original capacity','Does additional repair capacity reduce damaged stock or increase rentals? Use the cyclic conservation check.'),
26:('Investment charge multiplier',[.5,1,2],1,'net profit = operating profit − multiplier × selected investment charges','Does a second investment remain attractive when charges double? Check the precedence requirement.'),
27:('Maximum route duration (min)',[45,50,60],60,'select routes with duration <= limit; minimize 61 × vans + longest duration','Can a tighter route limit force another van? Explain why the coefficient 61 preserves priority over route duration.'),
28:('Sequence: 0=HPHHPPHH, 1=HHHHPPPP, 2=HPHPHPHP',[0,1,2],0,'maximize nonbonded nearest-neighbor H−H contacts','Why does composition alone not determine the maximum contacts? Compare sequence order and the selected lattice conformation.'),
29:('B contact map: 0=original, 1=remove (4,6), 2=add (2,5)',[0,1,2],0,'maximize conserved contacts under an order-preserving one-to-one alignment','Does adding a contact to B guarantee another conserved contact? Explain the order constraint using the alignment table.')}

def configure1(n,mod,x):
    kw={}
    names={2:'MAX_OILS',4:'REACTOR_LOSS',5:'TRAINING_CAP',6:'GASOLINE_CAP',8:'FEED_PRICE',9:'LABOR_CAP',13:'TARGET',16:'STORAGE_CAP',17:'WHITE_COUNT',18:'COEFFICIENT_BOUND',20:'EXPANSION_COST',21:'FAT_LIMIT',22:'TARGET_PLANT',23:'TRUCK_CAP',26:'INVESTMENT_SCALE'}
    if n in names:setattr(mod,names[n],x)
    if n==3:mod.CAPACITY['reactor']=[v*x for v in [120,80,120]]
    if n==7:mod.ROYALTY=[v*x for v in [1,.6,.8]]
    if n==10:mod.V={k:v*x for k,v in mod.V.items()}
    if n==11:mod.Y[4]=x
    if n==12:mod.ROWS=[(a,b, (a^b) if x==0 else (a|b) if x==1 else (a&b)) for a,b in [(0,0),(0,1),(1,0),(1,1)]]
    if n==14:mod.VALUES['B']=x
    if n==15:kw={'reserve':x}
    if n==19:mod.DEMAND=[v*x for v in [20,25,30,20]]
    if n==22:kw={'target':x}
    if n==24:mod.PROB=[x,1-x]
    if n==25:mod.CAP=[v*x for v in [2,1,1]]
    if n==27:mod.ROUTES=[r for r in mod.ROUTES if r[1]<=x]
    if n==28:mod.SEQUENCE=['HPHHPPHH','HHHHPPPP','HPHPHPHP'][x]
    if n==29:
        if x==1:mod.EB.remove((3,5))
        if x==2:mod.EB.append((1,4))
    return mod.build(**kw)

def table_frame(df):
    return {'columns':list(df.columns),'rows':json.loads(df.to_json(orient='values'))}

def frame_rows(rows):return {'columns':list(rows[0]) if rows else [],'rows':[list(r.values()) for r in rows]}

def extract(m):
    obj=next(m.component_data_objects(p.Objective,active=True))
    variables={v.name:value(v) for v in m.component_data_objects(p.Var) if v.value is not None}
    binding=sum(not c.equality and ((c.has_lb() and abs(value(c.body)-value(c.lower))<1e-6) or (c.has_ub() and abs(value(c.body)-value(c.upper))<1e-6)) for c in m.component_data_objects(p.Constraint,active=True))
    return obj,variables,binding

def lab_shell(id,label,values,default,equation,challenge):
    vol=int(id[1]);n=int(id[3:]);meta=META[id]
    return dict(title=meta['title'],volume=vol,problem=n,eyebrow=f'Volume {vol} · Problem {n:02}',question=meta['title'],
        intro=f'Explore {label[0].lower()+label[1:]}. Predict the objective change, then compare the selected solution with the original workbook case.',
        controls=[dict(id='value',label=label,values=values,default=default)],baseline=f'{default:g}',
        book=f'../books/volume-{vol}/chapters/'+meta['file'],
        assumptions='The baseline uses the original chapter data. Only the control named above changes; the remaining model assumptions are retained. Read the worked chapter for complete data and formulation. Alternative optimal plans may have the same objective.',
        equations=[dict(label='The relationship changed in this experiment',math=equation,why='The selected value is used to rebuild and solve the model. It is not an interpolation between answers.')],
        challenge=challenge,charts={'plan':'Decision comparison','sensitivity':'Objective across prepared cases'},cases={})

def finalize(lab):
    base=lab['cases'][lab['baseline']]
    if f"v{lab['volume']}-{lab['problem']:02}" in REF:
        reference=REF[f"v{lab['volume']}-{lab['problem']:02}"]
        assert abs(base['objective']-reference)<1e-5,(lab['title'],base['objective'],reference)
    for c in lab['cases'].values():
        x=list(dict.fromkeys(base['_x']+c['_x']))
        bv=dict(zip(base['_x'],base['_y']));cv=dict(zip(c['_x'],c['_y']))
        c['figures']={'plan':chart(x,[bv.get(i,0) for i in x],[cv.get(i,0) for i in x],c['_ylabel'],'bar')}
        changed=sum(abs(v-base['variables'].get(k,0))>1e-6 for k,v in c['variables'].items())
        if lab['volume']==1:c['tertiary']=changed
        delta=c['objective']-base['objective']
        c['interpretation']=f"The objective is {c['objective']:,.4g} {lab['unit']}, a change of {delta:+,.4g} relative to the original case. {lab['challenge']} A different optimal plan can have the same objective; changed variables alone do not prove an improvement."
    for c in lab['cases'].values():
        for k in ['_x','_y','_ylabel']:del c[k]
    # A discrete menu is not a continuous response curve. No connecting lines.
    values=lab['controls'][0]['values'];objectives=[lab['cases'][f'{x:g}']['objective'] for x in values]
    fig=chart([str(x) for x in values],[base['objective']]*len(values),objectives,lab['unit'],'bar')
    fig['data'][0]['name']='Original objective';fig['data'][1]['name']='Prepared optimum'
    for c in lab['cases'].values():c['figures']['sensitivity']=fig
    return lab

payload=json.loads((ROOT/'assets/cases.json').read_text());food=payload['labs'].get('food',payload['labs'].get('v1-01'));food.update(volume=1,problem=1,eyebrow='Volume 1 · Problem 01')
labs={'v1-01':food}
for n,spec in SPECS.items():
    id=f'v1-{n:02}';lab=lab_shell(id,*spec)
    for x in spec[1]:
        # Reload dependencies as well, so each scenario starts with the chapter data.
        for dep in ['problem03','problem15','problem19','problem25']:
            importlib.reload(importlib.import_module('models.v1.'+dep))
        mod=importlib.reload(importlib.import_module(f'models.v1.problem{n:02}'))
        m=solve(configure1(n,mod,x));mod.check(m);obj,variables,binding=extract(m)
        tables=mod.tables(m)
        if n==15:tables.pop('reserve_cost')
        if n==4:tables.pop('comparison')
        if n==22:
            tables={'peers':mod.frame([["ABCDEF"[j],value(m.lam[j])] for j in m.J],['Reference plant','Peer weight'])}
            axis=list('ABCDEF');ys=[value(m.lam[j]) for j in m.J];ylabel='Reference peer weight'
        elif n==4:
            axis=['Month 1','Month 2','Month 3'];ys=[sum(value(m.make[i,t]) for i in m.I) for t in m.T];ylabel='Production (t)'
        else:axis,ys,ylabel=mod.plot(m)
        all_tables=[dict(title=name.replace('_',' ').title(),**table_frame(df)) for name,df in tables.items()]
        if n==11:all_tables.reverse()
        lab.update(unit=mod.UNITS if n!=22 else 'radial input efficiency (fraction)',sense='minimize' if obj.sense==p.minimize else 'maximize',objectiveLabel='Optimal objective',secondaryLabel='Binding inequalities',tertiaryLabel='Changed variables vs baseline')
        lab['cases'][f'{x:g}']=dict(objective=value(obj),secondary=binding,tertiary=0,parameters={'value':x},variables=variables,
            audit=audit(m),checks=[dict(name='Solver termination',value='Optimal'),dict(name='Constraint, bound, and integrality audit',value='Passed'),dict(name='Independent chapter domain checks',value='Passed')],
            table=all_tables[0],tables=all_tables,_x=list(axis),_y=list(ys),_ylabel=ylabel)
        print(id,x,value(obj),flush=True)
    labs[id]=finalize(lab)

FAMILIES=['blending','reactors','heat','scheduling','hydrogen','water']
for n in range(1,19):
    family=FAMILIES[(n-1)//3];level=(n-1)%3+1;id=f'v2-{n:02}'
    specs={
      'blending':('Impurity limit (%)',[6,7,8],7,'protected impurity load <= selected limit × total blend','How does tightening quality change the cheapest recipe and the cost of protection?'),
      'reactors':('Holdup ceiling (kmol)',[150,250,350],250,'sum(feed × residence time) <= holdup ceiling','Does extra holdup change the chosen residence time or reactor? Explain why this result is optimal only over the stated operating menu.'),
      'heat':('Exchanger capacity multiplier',[.5,1,1.5],1,'heat on each match <= multiplier × original capacity × installed indicator','Which utility demand remains after increasing exchanger capacities? Distinguish a capacity limit from a forbidden match.'),
      'scheduling':('Cleaning-time multiplier',[.5,1,1.5],1,'next start >= previous finish + selected cleaning time','Does more cleaning change the sequence, the makespan, or the lateness cost? Explain using start and finish times.'),
      'hydrogen':('Tank charge (USD/kg/day)',[.05,.15,.5],.15,'daily cost = electricity + selected capacity charge × tank size','How does the optimal tank respond to its ownership charge? Distinguish common design decisions from scenario operation.'),
      'water':('User 1 concentration ceiling (mg/L)',[20,30,40],30,'contaminant load delivered to U1 <= selected ceiling × U1 demand','Does a tighter water specification increase freshwater or favor treatment? Check the contaminant and water balances.')}
    spec=specs[family]
    if n==3:spec=('Uncertainty budget Γ',[0,.5,1.5,2,3],1.5,'nominal load + budgeted worst deviation <= 7% × total blend','Why can a budget-protected recipe fail the full-box test? Gamma is a set size, not a probability.')
    if n==10:spec=('Batch C1 duration (h)',[2,4,6],4,'finish(C1) = start(C1) + selected duration','Does a longer C1 batch create idle time or simply extend the schedule? Inspect the release constraints.')
    if n==12:spec=('Batch B1 due time (h)',[5,7,10],7,'tardiness(B1) >= finish(B1) − selected due time','Does giving B1 more time reduce total cost or shift lateness to another job?')
    if n==13:spec=('Fixed tank capacity (kg)',[100,150,300],150,'inventory <= fixed tank capacity','How does a larger installed tank shift electricity purchases? This chapter excludes capacity ownership cost.')
    lab=lab_shell(id,*spec)
    for x in spec[1]:
        mod=importlib.reload(importlib.import_module('models.v2.'+family));kw={}
        if family=='blending':
            if n==3:kw={'gamma':x}
            else:mod.LIMIT=x/100
        if family=='reactors':mod.VOLUME_MAX=x
        if family=='heat':mod.CAP={a:v*x for a,v in mod.CAP.items()}
        if family=='scheduling':
            if n==10:mod.DURATION['C1']=x
            elif n==12:mod.DUE['B1']=x
            else:mod.CLEAN={a:v*x for a,v in mod.CLEAN.items()}
        if family=='hydrogen' and n!=13:mod.TANK_CHARGE=x
        if family=='water':mod.LIMIT['U1']=x
        m=mod.build(level,**kw)
        if n==13:m.k.fix(x)
        solve(m);mod.check(m,level);r=mod.report(m,level);obj,variables,binding=extract(m)
        metrics=list(r['metrics'].items());lab.update(unit=r['units'],sense='minimize' if obj.sense==p.minimize else 'maximize',objectiveLabel='Optimal objective',secondaryLabel=metrics[0][0],tertiaryLabel=metrics[1][0])
        if family=='blending':axis=[i for i in m.I];ys=[value(m.x[i]) for i in m.I];ylabel='Feed (t/day)'
        if family=='reactors':axis=[row['State'] for row in r['rows']];ys=[row['Desired (kmol/h)'] for row in r['rows']];ylabel='Desired product (kmol/h)'
        if family=='heat':axis=[row['State']+': '+row['Match'] for row in r['rows']];ys=[row['Heat (kW)'] for row in r['rows']];ylabel='Recovered heat (kW)'
        if family=='scheduling':axis=mod.JOBS;ys=[value(m.s[j])+mod.DURATION[j] for j in axis];ylabel='Batch completion (h)'
        if family=='hydrogen':axis=[row['State']+': '+str(row['Period']) for row in r['rows']];ys=[row['End stock (kg)'] for row in r['rows']];ylabel='End stock (kg)'
        if family=='water':axis=list(m.J);ys=[value(m.f[j]) for j in axis];ylabel='Freshwater (m3/h)'
        tab=frame_rows(r['rows'])
        lab['cases'][f'{x:g}']=dict(objective=value(obj),secondary=metrics[0][1],tertiary=metrics[1][1],parameters={'value':x},variables=variables,audit=audit(m),
            checks=[dict(name='Solver termination',value='Optimal'),dict(name='Constraint, bound, and integrality audit',value='Passed'),dict(name='Independent chapter domain checks',value='Passed')],table=tab,tables=[dict(title='Selected solution',**tab),dict(title='Process metrics',columns=['Metric','Value'],rows=[list(a) for a in metrics])],_x=axis,_y=ys,_ylabel=ylabel)
        print(id,x,value(obj),flush=True)
    labs[id]=finalize(lab)
assert len(labs)==47
assert abs(labs['v1-01']['cases']['5|200']['objective']-107842.59259259)<1e-5
payload['labs']=labs;payload['problemCount']=47;payload['caseCount']=sum(len(l['cases']) for l in labs.values())
payload['models']={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT/'models').rglob('*.py')}
(ROOT/'assets/cases.json').write_text(json.dumps(payload,separators=(',',':'),allow_nan=False))
with zipfile.ZipFile(ROOT/'assets/lab-models.zip','w',zipfile.ZIP_DEFLATED) as z:
    for folder in ['models','figures','styles','scripts']:
        for f in (ROOT/folder).rglob('*'):
            if f.is_file() and f.suffix in ['.py','.json','.mplstyle'] and '__pycache__' not in f.parts:z.write(f,f.relative_to(ROOT))
    for name in ['README.md','requirements.txt']:z.write(ROOT/name,name)
print(f"VERIFIED: {len(labs)} problems; {payload['caseCount']} exact optimal cases; {len(REF)} available baseline references.")
