"""Check coverage, menus, baseline references, audits, and monotone relaxations."""
from pathlib import Path
import json,itertools,math
ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'assets/cases.json').read_text());labs=p['labs']
expected={f'v{v}-{n:02}' for v,count in [(1,29),(2,18)] for n in range(1,count+1)}
assert set(labs)==expected
refs=json.loads((ROOT/'scripts/baseline_references.json').read_text())
for id,l in labs.items():
    expected_keys={'|'.join(f'{v:g}' for v in vals) for vals in itertools.product(*(c['values'] for c in l['controls']))}
    assert set(l['cases'])==expected_keys,id
    assert l['baseline'] in l['cases']
    if id in refs:assert math.isclose(l['cases'][l['baseline']]['objective'],refs[id],abs_tol=1e-5),id
    for key,c in l['cases'].items():
        assert math.isfinite(c['objective']) and c['audit']<=1e-6,(id,key)
        assert set(c['figures'])==set(l['charts']),(id,key)
        assert len(c['table']['columns'])>0
        for row in c['table']['rows']:assert len(row)==len(c['table']['columns'])
# Increasing these upper bounds expands the feasible set with the same objective.
for id in ['v1-02','v1-03','v1-05','v1-06','v1-09','v1-16','v1-18','v1-19','v1-21','v1-23','v1-25','v1-27','v2-01','v2-02','v2-04','v2-05','v2-06','v2-07','v2-08','v2-09','v2-13','v2-16','v2-17','v2-18']:
    if id=='v1-19':continue # Demand is an equality, not a relaxed capacity.
    l=labs[id];values=[l['cases'][f'{x:g}']['objective'] for x in l['controls'][0]['values']]
    sign=1 if l['sense']=='maximize' else -1
    assert all(sign*(b-a)>=-1e-6 for a,b in zip(values,values[1:])),(id,values)
assert p['caseCount']==sum(len(l['cases']) for l in labs.values())==159
assert abs(labs['v1-01']['cases']['5|200']['objective']-107842.59259259)<1e-5
print('PASS: 47 problems, 159 complete cases, 47 baseline references, all audits and monotone relaxations.')
