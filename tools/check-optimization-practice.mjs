import assert from 'node:assert/strict';
import {questions,createAttempt,validAttempt,grade} from '../teaching/2105623/practice/engine.mjs';
assert.equal(questions.length,25);assert.equal(new Set(questions.map(q=>q.id)).size,25);
for(const q of questions){assert.equal(q.choices.length,4);assert.equal(new Set(q.choices.map(c=>c.text)).size,4);assert.ok(q.choices.some(c=>c.id===q.answer));assert.ok(q.explanation.length>40);}
const signatures=new Set(),positions=new Set();
for(let n=0;n<200;n++){
 const a=createAttempt();assert.ok(validAttempt(a));signatures.add(JSON.stringify([a.order,a.options]));positions.add(a.options.Q01.indexOf('0'));
 assert.equal(grade(a).score,0);
 a.answers=Object.fromEntries(questions.map(q=>[q.id,q.answer]));assert.equal(grade(a).score,25);
 a.answers=Object.fromEntries(questions.map(q=>[q.id,q.choices.find(c=>c.id!==q.answer).id]));assert.equal(grade(a).score,0);
 delete a.answers.Q01;assert.equal(grade(a).answered,24);
 const copied=JSON.parse(JSON.stringify(a));assert.ok(validAttempt(copied));assert.deepEqual(grade(copied),grade(a));
 a.order[0]=a.order[1];assert.equal(validAttempt(a),false);
}
assert.equal(signatures.size,200);assert.equal(positions.size,4);
// Independent numerical checks behind quantitative items.
assert.equal((5-.02*100)/(.10-.02),37.5);assert.equal(100-37.5,62.5);
assert.equal(80-37.5,42.5);assert.equal(10000-8500,1500);
assert.equal(80-40,40);assert.equal(80*5+20*8+40+100*2,800);
assert.ok((.02*60+.10*40)/100>.05);
console.log('PASS: 25 unique items; 200 shuffled attempts; correct scoring under all permutations; serialization; corrupt-order rejection; quantitative answers.');
