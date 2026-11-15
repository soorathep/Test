#!/usr/bin/env python3
"""Check that every Antoine triple (A, B, C) in the 2027 labs and slides is a set in data/antoine-nist.json.
Run from _teaching-src/2105603:  python3 tools/check-antoine.py"""
import json, os, re, sys
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
reg = json.load(open(os.path.join(root, 'data', 'antoine-nist.json')))
known = {(s['A'], s['B'], s['C']): name for name, c in reg['compounds'].items() for s in c['sets']}
pat = re.compile(r'(\d\.\d{3,6})[^0-9\n]{1,40}?(\d{3,4}\.\d{1,4})[^0-9\n]{1,40}?([-−]\s?\d{1,3}\.\d{1,4})')
dirs = ['labs-next', 'slides-2027', os.path.join('..', '..', 'teaching', '2105603', 'labs', 'assets')]
bad = 0; seen = 0
for d in dirs:
    for dp, _, fn in os.walk(os.path.join(root, d)):
        if any(x in dp for x in ('_site', 'node_modules', '.quarto')): continue
        for f in fn:
            if not f.endswith(('.js', '.json', '.qmd', '.html', '.py')) or 'plotly' in f or 'katex' in f: continue
            p = os.path.join(dp, f); s = open(p, encoding='utf-8', errors='ignore').read()
            for m in pat.finditer(s):
                a, b, c = float(m[1]), float(m[2]), float(m[3].replace('−', '-').replace(' ', ''))
                if not (2 < a < 8 and 500 < b < 3500 and -300 < c < 10): continue
                seen += 1
                if (a, b, c) not in known:
                    bad += 1; print('NOT IN REGISTRY', os.path.relpath(p, root), (a, b, c))
print(f'{seen} Antoine sets found, {bad} not in the registry')
sys.exit(1 if bad else 0)
