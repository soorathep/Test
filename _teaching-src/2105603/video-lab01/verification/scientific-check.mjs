/** Independent algebraic audit of the Week 1 ideal-binary screen demonstration. */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {pathToFileURL,fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';

const labs = process.env.LAB01_LABS_ROOT || path.join(os.homedir(),'Documents/GitHub/2026-course-advanced-thermodynamics');
const site = process.env.LAB01_SITE_ROOT || path.join(os.homedir(),'Documents/GitHub/Test');
const output = new URL('./scientific-qa.json', import.meta.url);
const e = await import(pathToFileURL(path.join(labs, 'src/engine/thermo.js')));
const catalog = JSON.parse(fs.readFileSync(path.join(labs, 'data/systems.json'), 'utf8'));
const system = catalog.systems.synthetic;
const tolerance = 1e-10;
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected}`);
const sat = [150, 60], z = .5, T = 350;
const bubble = z * sat[0] + (1-z) * sat[1];
const dew = 1/(z/sat[0]+(1-z)/sat[1]);
const independent = P => {
  if (P > bubble) return {P_kPa:P, phase:'liquid', beta:0, x1:z, y1:null};
  if (P < dew) return {P_kPa:P, phase:'vapor', beta:1, x1:null, y1:z};
  const x1 = (P-sat[1])/(sat[0]-sat[1]);
  const y1 = sat[0]*x1/P;
  const beta = (z-x1)/(y1-x1);
  return {P_kPa:P, phase:P===bubble?'bubble-boundary':P===dew?'dew-boundary':'two-phase', beta, x1, y1};
};
const cases = [110,95,80,90,100,bubble,dew].map(P=>{
  const expected=independent(P), actual=e.flash(system,T,P*1000,z,0);
  assert.equal(actual.phase, expected.phase);
  for(const [key,field] of [['beta','beta'],['x','x1'],['y','y1']]){
    if(expected[field]===null) assert.equal(actual[key],null);
    else close(actual[key],expected[field]);
  }
  const nL=1-expected.beta,nV=expected.beta;
  const liquid=expected.x1===null?[0,0]:[nL*expected.x1,nL*(1-expected.x1)];
  const vapor=expected.y1===null?[0,0]:[nV*expected.y1,nV*(1-expected.y1)];
  const balance=[liquid[0]+vapor[0]-.5,liquid[1]+vapor[1]-.5];
  balance.forEach(r=>close(r,0));
  const K=sat.map(s=>s/P);
  const equilibrium=expected.x1===null||expected.y1===null?null:[expected.x1*K[0]-expected.y1,(1-expected.x1)*K[1]-(1-expected.y1)];
  if(equilibrium) equilibrium.forEach(r=>close(r,0));
  const rr=expected.phase==='two-phase'?z*(K[0]-1)/(1+expected.beta*(K[0]-1))+(1-z)*(K[1]-1)/(1+expected.beta*(K[1]-1)):null;
  if(rr!==null) close(rr,0);
  const rrEndpoints={atZero:z*(K[0]-1)+(1-z)*(K[1]-1),atOne:z*(K[0]-1)/K[0]+(1-z)*(K[1]-1)/K[1]};
  if(P===95){close(rrEndpoints.atZero,2/19);close(rrEndpoints.atOne,-13/120);}
  assert.equal(actual.stability.verified,true);
  return {...expected,liquidFraction:nL,vaporFraction:nV,K,oneMolFeed:{liquidMoles:nL,vaporMoles:nV,liquidComponentMoles:liquid,vaporComponentMoles:vapor,componentBalanceResiduals:balance},equilibriumResiduals:equilibrium,rrResidual:rr,rrEndpoints,engine:{phase:actual.phase,beta:actual.beta,x1:actual.x,y1:actual.y,balanceResidual:actual.balanceResidual,equilibriumResidual:actual.equilibriumResidual,stabilityVerified:actual.stability.verified}};
});
close(e.bubbleP(system,T,z,0).P/1000,bubble);
close(e.dewP(system,T,z,0).P/1000,dew);
system.components.map(c=>e.psat(c,T)/1000).forEach((v,i)=>close(v,sat[i]));
const testArgs=['--test','tests/engine.test.mjs','tests/teaching-examples.test.mjs'];
const testOutput=execFileSync(process.execPath,testArgs,{cwd:labs,encoding:'utf8',env:{...process.env,FORCE_COLOR:'0'}});
assert.match(testOutput,/# pass 18|pass 18/);
assert.match(testOutput,/# fail 0|fail 0/);
const files=['data/systems.json','src/engine/thermo.js','src/ui/app.js','src/ui/study-state.js','src/ui/study-workspace.js','tests/engine.test.mjs','tests/teaching-examples.test.mjs','tools/render-assessments.mjs'];
const sha=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const report={
  schema:'lab01-video-scientific-qa/1',status:'pass',checkedAt:new Date().toISOString(),
  scope:'Supplemental Week 1 core Lab 01 demonstration: ideal binary at fixed 350 K, no introduction of nonideal models or extensions.',
  basis:{system:'Teaching binary · synthetic',componentNames:['Component A','Component B'],T_K:T,z1:z,saturationPressure_kPa:sat,Pbubble_at_x1_equals_z1_kPa:bubble,Pdew_at_y1_equals_z1_kPa:dew,model:'Ideal solution',feedBasis_mol:1},
  independentMethod:{bubble:'P = x1*Psat1 + (1-x1)*Psat2',dew:'1/P = y1/Psat1 + (1-y1)/Psat2',twoPhase:'x1 = (P-Psat2)/(Psat1-Psat2); y1 = x1*Psat1/P; beta = (z1-x1)/(y1-x1)',singlePhase:'Compare P with the bubble and dew boundaries evaluated at the specified overall composition. Absent-phase composition is null.',tolerance},
  cases,
  recommendation:{baseline_kPa:95,comparisonPressures_kPa:[110,80],independentAttempt_kPa:90,optionalAlternateAttempt_kPa:100,reason:'90 kPa matches the existing Session 1 independent assessment. Its exact x1=1/3, y1=5/9 and beta=3/4 provide a clean independent check.'},
  ui:{systemLabel:'Teaching binary · synthetic',modelLabel:'Ideal solution · γᵢ = 1',calculateLabel:'Calculate equilibrium',diagramLabel:'P–x–y · fixed temperature',betaLabel:'Vapor fraction · β',liquidLabel:'Liquid · x₁',vaporLabel:'Vapor · y₁',bubbleLabel:'Bubble pressure · x₁ = z₁',dewLabel:'Dew pressure · y₁ = z₁',studyExport:'Export experiment ↓',curveExport:'Curve CSV ↓',workspace:'Study workspace · reopen and compare cases',loadLabel:'Load studies or a comparison JSON',downloadLabel:'Download comparison',restore:'Restore <case label>, then Calculate equilibrium',rawUnits:{'inputs.P':'kPa','result.P':'Pa','curves.selected[].P':'Pa','chartRows[].P_Pa':'Pa','T':'K','x1,y1,z1,beta':'dimensionless molar fractions'}},
  teachingCautions:[
    'The synthetic property record defines Psat=150 and 60 kPa at 350 K. These are not experimental fluid data and should not be entered as arbitrary pressure controls.',
    'x1 and y1 are compositions of the individual phases; beta is the molar fraction of the feed in the vapor phase. Beta is not y1, a mass fraction, or a volume fraction.',
    'The two boundary pressures use different specified phase compositions: x1=z1 for bubble and y1=z1 for dew. They are not the current tie-line endpoints at 95 kPa.',
    'At fixed T and z, lowering P increases beta through the two-phase interval; beta stays zero or one in the corresponding single-phase region.',
    'At 110 kPa there is no bulk vapor and y1 is N/A, not zero. At 80 kPa there is no bulk liquid and x1 is N/A, not zero.',
    'At the exact bubble/dew boundary the engine may display an incipient phase composition with zero phase amount. That is different from a bulk phase being present.',
    'P–x–y uses composition horizontally and pressure vertically. Solid line is bubble versus liquid x1; dashed line is dew versus vapor y1. The diamond is overall composition z1 at the selected flash pressure.',
    'Lowering P at fixed T does not lower the saturation pressure. The two Psat values stay fixed in this pressure comparison.',
    'Round only the displayed final values. Small residuals with full precision do not require a hand balance using four-decimal values to equal zero exactly.',
    'The lab also offers other model and diagram controls and a nonideal exercise list. This supplemental first-week demonstration stays with Ideal solution and the required ideal pressure comparison.',
    'Inputs update or invalidate displayed results on editing. Explicitly press Calculate equilibrium after restoring a study before claiming it is freshly reproduced.',
    'Export experiment contains computed evidence and automatically captures a comparison case. Download current inputs only contains no computed result.',
    'The comparison is held in browser memory until Download comparison is used. Restoring imported inputs does not make recorded results a fresh calculation.',
    'Small numerical residuals establish consistency with the chosen equations, not physical validation against measurements or general validity of the ideal assumption.',
    'Single-phase cases have no two-phase equilibrium residual or Rachford–Rice root. Do not interpret Not applicable as a failed solve.',
    'The ideal teaching system is admitted only in 300–390 K and pressure input 1–200 kPa; remaining in that range is a software scope check, not an accuracy guarantee.'
  ],
  tests:{command:'<node> --test tests/engine.test.mjs tests/teaching-examples.test.mjs',passed:18,failed:0,output:testOutput},
  sources:{labsCommit:execFileSync('git',['rev-parse','HEAD'],{cwd:labs,encoding:'utf8'}).trim(),files:files.map(file=>({repository:'labs',file,sha256:sha(path.join(labs,file))})),week1Deck:{repository:'website',file:'_teaching-src/2105603/postmidterm-01.qmd',sha256:sha(path.join(site,'_teaching-src/2105603/postmidterm-01.qmd'))}},
  pendingReview:'Final narration and captured screen sequence are reviewed separately after production. This report does not assert browser capture or media QA.'
};
fs.mkdirSync(path.dirname(fileURLToPath(output)),{recursive:true});
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,cases:cases.length,testsPassed:18,bubble_kPa:bubble,dew_kPa:dew,report:path.basename(fileURLToPath(output))},null,2));
