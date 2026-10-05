import {questions, VERSION} from './questions.mjs';
export {questions, VERSION};
const bank = new Map(questions.map(q=>[q.id,q]));
export function randomInt(max) {
 const range=2**32, limit=range-range%max;
 const v=new Uint32Array(1);
 do { crypto.getRandomValues(v); } while(v[0]>=limit);
 return v[0]%max;
}
export function shuffle(values, draw=randomInt) {
 const a=[...values];
 for(let i=a.length-1;i>0;i--){const j=draw(i+1);[a[i],a[j]]=[a[j],a[i]];}
 return a;
}
export function createAttempt() {
 return {version:VERSION,id:crypto.randomUUID(),started:new Date().toISOString(),submitted:null,
  order:shuffle(questions.map(q=>q.id)),options:Object.fromEntries(questions.map(q=>[q.id,shuffle(q.choices.map(c=>c.id))])),answers:{},flagged:[],position:0};
}
function permutation(a,b){return Array.isArray(a)&&a.length===b.length&&new Set(a).size===a.length&&a.every(x=>b.includes(x));}
export function validAttempt(a){
 return a&&a.version===VERSION&&typeof a.id==='string'&&Number.isFinite(Date.parse(a.started))&&
 (a.submitted===null||Number.isFinite(Date.parse(a.submitted)))&&permutation(a.order,[...bank.keys()])&&
 a.options&&questions.every(q=>permutation(a.options[q.id],q.choices.map(c=>c.id)))&&
 a.answers&&typeof a.answers==='object'&&!Array.isArray(a.answers)&&Object.entries(a.answers).every(([id,c])=>bank.has(id)&&bank.get(id).choices.some(x=>x.id===c))&&
 Array.isArray(a.flagged)&&a.flagged.every(id=>bank.has(id))&&Number.isInteger(a.position)&&a.position>=0&&a.position<questions.length;
}
export function grade(a){
 if(!validAttempt(a))throw new Error('Invalid attempt');
 const rows=a.order.map(id=>{const q=bank.get(id);return {id,topic:q.topic,selected:a.answers[id]??null,correct:q.answer,earned:a.answers[id]===q.answer?1:0};});
 return {score:rows.reduce((s,r)=>s+r.earned,0),total:questions.length,answered:rows.filter(r=>r.selected!==null).length,rows};
}
