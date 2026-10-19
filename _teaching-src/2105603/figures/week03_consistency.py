"""Regenerate Week 3 teaching figures with the published Lab 03 engine.

Run with ~/.venvs/research/bin/python. Supply --labs for another checkout.
"""
import argparse
import json
from pathlib import Path
import subprocess

import matplotlib.pyplot as plt
import numpy as np
import skh_palette as skh

skh.use()
parser = argparse.ArgumentParser()
parser.add_argument('--labs', type=Path, default=Path.home() / 'Documents/GitHub/2026-course-advanced-thermodynamics')
parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent)
args = parser.parse_args()
node = Path.home() / '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
js = '''
import fs from 'node:fs';
import {syntheticSet,areaAnalysis,differential} from './src/engine/consistency.js';
const data=JSON.parse(fs.readFileSync('data/case-studies/ipa-water.json'));
console.log(JSON.stringify(['clean','cancel'].map(kind=>{
const set=syntheticSet(data,{path:'isothermal',kind,amplitude:.25,n:41});
return {kind,rows:set.rows.map(r=>({x:r.x,f:r.f})),area:areaAnalysis(set).area,differential:differential(set)};
})));
'''
cases = json.loads(subprocess.check_output([str(node), '--input-type=module', '-e', js], cwd=args.labs, text=True))
fig, axes = plt.subplots(1, 2, figsize=(11.8, 3.7), layout='constrained')
for item, name, color in zip(cases, ['Consistent reference', 'Canceling errors'], [skh.C['teal'], skh.C['amber']]):
    axes[0].plot([r['x'] for r in item['rows']], [r['f'] for r in item['rows']], color=color, lw=2, label=name)
    p = item['differential']['points']
    axes[1].plot([r['x'] for r in p], [r['residual'] for r in p], color=color, lw=2, label=name)
for ax in axes:
    ax.axhline(0, color=skh.C['graphite'], lw=1.5, ls=':')
    ax.set_xlabel('Liquid mole fraction, $x_1$')
    ax.set_xlim(0, 1)
axes[0].set_ylabel(r'$\ln(\gamma_1/\gamma_2)$')
axes[1].set_ylabel('Local residual, $r$ (dimensionless)')
axes[1].set_ylim(-.28, .34)
axes[0].set_title('Both satisfy the area criterion')
axes[1].set_title('The local diagnostic distinguishes them')
axes[0].legend(frameon=False, fontsize=10)
axes[1].text(.5, .97, '41 points; amplitude = 0.25', ha='center', va='top', transform=axes[1].transAxes, fontsize=10, color=skh.C['graphite'])
args.output.mkdir(parents=True, exist_ok=True)
for suffix in ['pdf', 'png']:
    fig.savefig(args.output / f'week03-area-local.{suffix}', dpi=600, bbox_inches='tight')
plt.close(fig)
(args.output / 'week03-area-local.json').write_text(json.dumps(cases, indent=2) + '\n')
print(args.output / 'week03-area-local.pdf')
