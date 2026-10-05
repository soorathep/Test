import {writtenQuestions,WRITTEN_VERSION} from './written-questions.mjs';
const storageKey='skh-2105623-written-v1',status=document.getElementById('written-status');
let answers={},storageAvailable=true;
try{const saved=JSON.parse(localStorage.getItem(storageKey)||'null');if(saved?.version===WRITTEN_VERSION&&saved.answers&&typeof saved.answers==='object'){for(const q of writtenQuestions)if(typeof saved.answers[q.id]==='string')answers[q.id]=saved.answers[q.id];}}catch{storageAvailable=false;}
function el(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function updateStatus(){const n=writtenQuestions.filter(q=>(answers[q.id]||'').trim()).length;status.textContent=`${n} of 5 answers started. ${storageAvailable?'Saved in this browser only.':'Browser saving is unavailable. Keep this tab open and download your answers.'}`;}
function save(){try{localStorage.setItem(storageKey,JSON.stringify({version:WRITTEN_VERSION,answers}));storageAvailable=true;}catch{storageAvailable=false;}updateStatus();}
const host=document.getElementById('written-questions');
for(const [i,q]of writtenQuestions.entries()){
 const a=el('article',undefined,'panel written-question');a.id=q.id;
 const label=el('div',undefined,'question-label');label.append(el('p',`Problem ${i+1} · ${q.id}`,'eyebrow'),el('p','4 marks','eyebrow'));
 a.append(label,el('h2',q.title),el('p',q.context),el('p',q.variables,'variables'),el('p',q.task,'task'));
 const l=el('label','Your formulation','answer-label');l.htmlFor=`answer-${q.id}`;
 const input=el('textarea');input.id=l.htmlFor;input.value=answers[q.id]||'';input.spellcheck=false;input.setAttribute('aria-label',`Your formulation for problem ${i+1}`);
 const printed=el('pre',input.value,'print-answer');input.addEventListener('input',()=>{answers[q.id]=input.value;printed.textContent=input.value;save();});
 a.append(l,input,printed);
 const details=el('details');details.append(el('summary','Model answer and marking guide'),el('pre',q.solution.join('\n'),'model-equations'),el('p',q.explanation));
 const table=el('table',undefined,'rubric'),head=el('thead'),hr=el('tr');hr.append(el('th','Marks'),el('th','Credit for'));head.append(hr);const body=el('tbody');for(const row of q.rubric){const tr=el('tr');tr.append(el('td',row[0]),el('td',row[1]));body.append(tr);}table.append(head,body);details.append(table,el('p',q.check,'check'));a.append(details);host.append(a);
}
updateStatus();
let printOpen=[];
window.addEventListener('beforeprint',()=>{printOpen=[...document.querySelectorAll('details')].map(d=>d.open);const include=document.getElementById('include-solutions').checked;document.body.classList.toggle('print-solutions',include);if(include)for(const d of document.querySelectorAll('details'))d.open=true;});
window.addEventListener('afterprint',()=>{[...document.querySelectorAll('details')].forEach((d,i)=>d.open=printOpen[i]||false);document.body.classList.remove('print-solutions');});
document.getElementById('print-written').onclick=()=>window.print();
document.getElementById('download-written').onclick=()=>{const text=['2105623: Written Formulation Practice','Responses only. This file is not a graded or verified examination record.','',...writtenQuestions.flatMap((q,i)=>[`Problem ${i+1}: ${q.title} (${q.id})`,q.context,q.variables,'Task: '+q.task,'','My answer:',answers[q.id]||'(No answer entered)','',''])].join('\n');const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'})),a=el('a');a.href=url;a.download='optimization-written-answers.txt';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);};
