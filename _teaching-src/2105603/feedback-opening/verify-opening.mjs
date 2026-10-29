/** Reproduce the printed Week 4 opening examples from the existing Lab engines.
 * Run with the absolute bundled Node executable.
 * Optional arguments: --repo PATH --site PATH --page PATH --output PATH
 * Synthetic examples only. Does not read or modify student responses.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const here=path.dirname(fileURLToPath(import.meta.url));
const args=process.argv.slice(2);
function option(name,fallback){const i=args.indexOf(name);if(i<0)return fallback;assert.ok(args[i+1],`${name} needs a path`);return path.resolve(args[i+1]);}
const repo=option('--repo',path.join(os.homedir(),'Documents/GitHub/2026-course-advanced-thermodynamics'));
const site=option('--site',path.join(os.homedir(),'Documents/GitHub/Test'));
const pagePath=option('--page',path.join(here,'week04-questions.html'));
const output=option('--output',path.join(here,'numerical-qa.json'));
const consistencyPath=path.join(repo,'src/engine/consistency.js');
const stabilityPath=path.join(repo,'src/engine/stability.js');
const dataPath=path.join(repo,'data/case-studies/ipa-water.json');
const e=await import(pathToFileURL(consistencyPath));
const liquid=await import(pathToFileURL(stabilityPath));
const data=JSON.parse(fs.readFileSync(dataPath,'utf8'));
const html=fs.readFileSync(pagePath,'utf8');
const sha=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const checks=[];
function near(name,actual,expected,tolerance){
  assert.ok(Number.isFinite(actual),`${name}: nonfinite value`);
  assert.ok(Math.abs(actual-expected)<=tolerance,`${name}: ${actual} differs from ${expected} by more than ${tolerance}`);
  checks.push({name,actual,expected,tolerance,status:'passed'});
}
function printed(name,value){assert.ok(html.includes(value),`${name}: expected printed value ${value} not found`);}

const printedConsistency=[
  {n:41,D:2.013463,score:1.671839},
  {n:81,D:1.956058,score:1.590767},
  {n:161,D:1.941724,score:1.565607},
];
const consistency=printedConsistency.map(expected=>{
  const set=e.syntheticSet(data,{path:'isothermal',kind:'local',amplitude:.25,n:expected.n});
  const area=e.areaAnalysis(set),local=e.differential(set);
  near(`D at ${expected.n} points`,area.area.D,expected.D,5e-7);
  near(`Score at ${expected.n} points`,local.score,expected.score,5e-7);
  printed('D table',expected.D.toFixed(6));printed('Score table',expected.score.toFixed(6));
  assert.equal(area.redlichKister.status,'meets-criterion');
  assert.equal(local.status,'meets-criterion');
  const peak=local.points.find(r=>Math.abs(r.x-.35)<1e-12);
  assert.ok(peak);assert.ok(Math.abs(peak.residual)>.24,'The localized residual must remain despite the mean threshold.');
  return {points:expected.n,D_percent:area.area.D,scaled_mean_absolute_residual:local.score,
    residual_at_x035:peak.residual,area_status:area.redlichKister.status,score_status:local.status};
});
near('Rounded local residual at x=.35, 81 points',consistency[1].residual_at_x035,-.250,5e-4);

// Direct formulas independently reproduce the symmetric Margules example.
const A=3;
const g=x=>x===0||x===1?0:x*Math.log(x)+(1-x)*Math.log1p(-x)+A*x*(1-x);
const slope=x=>Math.log(x/(1-x))+A*(1-2*x);
const curvature=x=>1/x+1/(1-x)-2*A;
function bisect(fn,lo,hi){
  let fl=fn(lo);assert.ok(fl*fn(hi)<=0,'Root must be bracketed');
  for(let i=0;i<150;i++){
    const mid=(lo+hi)/2,f=fn(mid);
    if(f===0||hi-lo<2e-15)return mid;
    if(fl*f<=0)hi=mid;else{lo=mid;fl=f;}
  }
  throw new Error('Bisection did not converge');
}
const sa=(1-Math.sqrt(1-2/A))/2,sb=1-sa;
const xa=bisect(slope,1e-14,sa),xb=1-xa;
const cuts=[1e-14,sa,sb,1-1e-14];
const stationary=[];
for(let i=1;i<cuts.length;i++)stationary.push(bisect(slope,cuts[i-1],cuts[i]));
const supportCandidates=[0,1,...stationary];
const supportDistances=supportCandidates.map(x=>g(x)-g(xa));
const supportMin=Math.min(...supportDistances);
assert.ok(supportMin>=-1e-12,'Common tangent must support the curve at every possible extremum and both endpoints');
near('Printed alpha contact',xa,.07072018,5e-9);
near('Printed beta contact',xb,.92927982,5e-9);
printed('Alpha contact','0.07072018');printed('Beta contact','0.92927982');
const expectedStates=[
  {z:.12,beta:.057398,alpha:.942602,curvature:3.469697,state:'metastable'},
  {z:.35,beta:.325289,alpha:.674711,curvature:-1.604396,state:'unstable'},
];
const gibbs=expectedStates.map(expected=>{
  const z=expected.z,fb=(z-xa)/(xb-xa),fa=1-fb;
  const split=fa*g(xa)+fb*g(xb),homogeneous=g(z),gain=homogeneous-split;
  const model=liquid.equilibrium(A,z);
  near(`Printed beta fraction at z=${z}`,fb,expected.beta,5e-7);
  near(`Printed alpha fraction at z=${z}`,fa,expected.alpha,5e-7);
  near(`Printed curvature at z=${z}`,curvature(z),expected.curvature,5e-7);
  near(`Independent component balance at z=${z}`,fa*xa+fb*xb,z,1e-14);
  near(`Engine alpha at z=${z}`,model.xAlpha,xa,1e-12);
  near(`Engine beta at z=${z}`,model.xBeta,xb,1e-12);
  near(`Engine phase fraction at z=${z}`,model.fractionBeta,fb,1e-12);
  near(`Engine energy reduction at z=${z}`,model.gain,gain,1e-12);
  assert.equal(model.state,expected.state);assert.equal(model.phase,'two liquids');
  assert.ok(model.tpd.minimum<0,'Both homogeneous feeds are not globally stable.');
  for(const [name,val] of [['beta fraction',expected.beta],['alpha fraction',expected.alpha]])printed(name,val.toFixed(6));
  if(z===.12){
    near('Printed homogeneous Gibbs',homogeneous,-.05012499,5e-9);
    near('Printed split Gibbs',split,-.05834135,5e-9);
    near('Printed energy reduction',gain,.00821636,5e-9);
    for(const v of ['−0.05012499','−0.05834135','0.00821636'])printed('Gibbs worked example',v);
  }
  return {A,z,xAlpha:xa,xBeta:xb,fractionAlpha:fa,fractionBeta:fb,curvature:curvature(z),
    homogeneousG:homogeneous,splitG:split,reductionPerRT:gain,state:model.state,
    feedTPDMinimum:model.tpd.minimum,balanceResidual:fa*xa+fb*xb-z};
});

const lab03=fs.readFileSync(path.join(site,'teaching/2105603/labs/consistency.html'),'utf8');
const lab04=fs.readFileSync(path.join(site,'teaching/2105603/labs/stability.html'),'utf8');
for(const text of ['Synthetic · isothermal, 350 K','Localized defect near x₁ = 0.35','Sampling resolution','Local Gibbs–Duhem residual'])assert.ok(lab03.includes(text)&&html.includes(text),`Lab03 control mismatch: ${text}`);
for(const text of ['Liquid model','Margules · 1 parameter','Interaction parameter A','Feed mole fraction z₁','Find equilibrium'])assert.ok(lab04.includes(text)&&html.includes(text),`Lab04 control mismatch: ${text}`);
const figureSource=fs.readFileSync(path.join(site,'teaching/2105603/figures/gibbs_review.py'),'utf8');
assert.match(figureSource,/color=C\["amber"\].*label="Homogeneous liquid"/);
assert.match(figureSource,/color=C\["teal"\].*ls="--".*label="Equilibrium envelope"/);
assert.match(figureSource,/color=C\["graphite"\].*label="Supporting common tangent"/);
assert.match(figureSource,/ax\.plot\(Z, g\(Z\), "D", color=C\["amber"\]/);
assert.match(figureSource,/ax\.plot\(Z, geq, "o", color=C\["teal"\]/);
const result={status:'passed',scope:'Synthetic numerical and source-label verification; not new experimental data, grading, or browser QA',
  sources:{consistency_engine:'src/engine/consistency.js',consistency_sha256:sha(consistencyPath),stability_engine:'src/engine/stability.js',stability_sha256:sha(stabilityPath),
    property_data:'data/case-studies/ipa-water.json',property_sha256:sha(dataPath),review_page:path.basename(pagePath),review_page_sha256:sha(pagePath)},
  checks,consistency,gibbs,
  support:{method:'Check both endpoints and all roots of g-prime=0, bracketed by the analytical spinodals. No coarse plotting grid is used for the criterion.',
    spinodals:[sa,sb],candidateCompositions:supportCandidates,distances:supportDistances,minimum:supportMin,tolerance:1e-12},
  ui_labels:'All control names quoted in the review match the inspected Lab03 and Lab04 HTML.',
  figure:'Existing Gibbs review: amber homogeneous curve and feed diamond; dashed teal envelope and equilibrium-feed circle; graphite supporting tangent and contact circles. No vertical feed line is drawn.'};
fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');
console.log(`${checks.length} numerical comparisons passed; Lab labels and existing figure palette verified. Saved ${path.basename(output)}.`);
