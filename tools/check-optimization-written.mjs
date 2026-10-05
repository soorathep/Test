import assert from 'node:assert/strict';
import {writtenQuestions} from '../teaching/2105623/practice/written-questions.mjs';
assert.equal(writtenQuestions.length,5);assert.equal(new Set(writtenQuestions.map(q=>q.id)).size,5);
for(const q of writtenQuestions){assert.equal(q.rubric.reduce((s,r)=>s+Number(r[0]),0),4);for(const field of ['context','variables','task','explanation','check'])assert.ok(q[field]?.length>20);}
assert.equal(120*50+75*20+900,8400);
assert.equal(.04*120,4.8);assert.ok(Math.abs(.01*60+.07*60-4.8)<1e-10);
assert.ok(.01*50+.07*70>4.8);assert.ok(60<=90&&60<=100);
for(const y of [0,1])for(const x of [-1,0,1,14,15,20,70,71])assert.equal(15*y<=x&&x<=70*y,y===0?x===0:x>=15&&x<=70);
const x1=40,s1=5,x2=65,s2=5;assert.equal(10+x1,45+s1);assert.equal(s1+x2,65+s2);assert.equal(x1+x2,45+65+5-10);
let states=0;
for(const y1 of [0,1])for(const y2 of [0,1])for(const yS of [0,1]){const feasible=y1+y2===1&&y2<=yS;const intended=(y1!==y2)&&(y2===0||yS===1);assert.equal(feasible,intended);if(feasible)states++;}
assert.equal(states,3);
console.log('PASS: five complete problems, 20 rubric marks, numerical checks, supplier logic and every reactor/support binary combination.');
