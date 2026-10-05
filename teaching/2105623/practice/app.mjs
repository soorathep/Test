import {questions,VERSION,createAttempt,validAttempt,grade} from './engine.mjs';
const $=id=>document.getElementById(id), key='skh-2105623-practice-v1';
const bank=new Map(questions.map(q=>[q.id,q]));
let attempt=null, pending=null;
function readSaved(){try{const raw=localStorage.getItem(key);if(!raw)return null;const a=JSON.parse(raw);if(validAttempt(a))return a;$('storage-status').textContent='The previous saved attempt is incompatible with this test. Start a new attempt.';}catch{$('storage-status').textContent='Browser storage is unavailable or unreadable. Keep this tab open to retain your progress.';}return null;}
function save(){try{localStorage.setItem(key,JSON.stringify(attempt));$('storage-status').textContent='Progress saved in this browser. No score is sent to your instructor.';}catch{$('storage-status').textContent='Progress could not be saved. Keep this tab open. You can download your result after submitting.';}}
function el(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function show(id){for(const n of ['welcome','test','results'])$(n).hidden=n!==id;}
function confirmAction(title,text,label,fn){$('confirm-title').textContent=title;$('confirm-text').textContent=text;$('confirm-action').textContent=label;pending=fn;$('confirm').showModal();}
$('confirm-action').onclick=()=>{const f=pending;pending=null;$('confirm').close();f?.();};
$('cancel').onclick=()=>{$('confirm').close();pending=null;};
$('confirm').addEventListener('cancel',()=>{pending=null;});
function start(){attempt=createAttempt();save();renderQuestion(true);}
function requestNew(){if(attempt)confirmAction('Start a new attempt?','This replaces the saved attempt in this browser. Download your result first if you want to keep it. The new attempt will shuffle questions and choices again.','Start new attempt',start);else start();}
$('start').onclick=requestNew;$('retake').onclick=requestNew;
$('resume').onclick=()=>attempt.submitted?renderResults():renderQuestion(true);
function renderNavigator(){const nav=$('navigator');nav.replaceChildren();attempt.order.forEach((id,i)=>{const n=el('button',String(i+1));n.type='button';const answered=attempt.answers[id]!==undefined, flagged=attempt.flagged.includes(id);n.classList.toggle('answered',answered);n.classList.toggle('flagged',flagged);n.classList.toggle('current',i===attempt.position);n.setAttribute('aria-label',`Question ${i+1}, ${answered?'answered':'unanswered'}${flagged?', flagged':''}`);if(i===attempt.position)n.setAttribute('aria-current','step');n.onclick=()=>{attempt.position=i;save();renderQuestion(true);};nav.append(n);});const count=Object.keys(attempt.answers).length;$('progress').textContent=`${count} of ${questions.length} answered`;$('progressbar').value=count;}
function renderQuestion(focus=false){
 if(attempt.submitted){renderResults();return;}
 show('test');const id=attempt.order[attempt.position],q=bank.get(id);
 $('attempt-id').textContent=`Practice attempt ${attempt.id.slice(0,8)}`;
 $('question-number').textContent=`Question ${attempt.position+1} of ${questions.length}`;
 $('stem').textContent=q.stem;
 const field=$('choices');field.replaceChildren(el('legend','Select one answer','sr-only'));
 attempt.options[id].forEach((cid,i)=>{const c=q.choices.find(c=>c.id===cid),label=el('label'),input=el('input');input.type='radio';input.name='answer';input.value=cid;input.checked=attempt.answers[id]===cid;input.addEventListener('change',()=>{if(attempt.submitted)return;attempt.answers[id]=cid;save();renderNavigator();});label.append(input,el('span',String.fromCharCode(65+i)+'.','letter'),el('span',c.text));field.append(label);});
 $('flag').checked=attempt.flagged.includes(id);$('previous').disabled=attempt.position===0;$('next').textContent=attempt.position===questions.length-1?'Review and submit':'Next question';renderNavigator();if(focus){$('stem').focus();window.scrollTo({top:0,behavior:'instant'});}
}
$('flag').onchange=()=>{if(!attempt||attempt.submitted)return;const id=attempt.order[attempt.position];attempt.flagged=attempt.flagged.filter(x=>x!==id);if($('flag').checked)attempt.flagged.push(id);save();renderNavigator();};
$('clear').onclick=()=>{if(!attempt||attempt.submitted)return;delete attempt.answers[attempt.order[attempt.position]];save();renderQuestion();};
$('previous').onclick=()=>{if(attempt.position>0){attempt.position--;save();renderQuestion(true);}};
$('next').onclick=()=>{if(attempt.position<questions.length-1){attempt.position++;save();renderQuestion(true);}else submit();};
function submit(){if(attempt.submitted)return;const remaining=questions.length-Object.keys(attempt.answers).length;confirmAction('Submit this attempt?',`${remaining?`${remaining} unanswered question${remaining===1?'':'s'} will receive zero points. `:'All 25 questions have an answer. '}${attempt.flagged.length} question(s) flagged for review. After submitting, answers are locked and the explanations become available.`,'Submit and see result',()=>{attempt.submitted=new Date().toISOString();save();renderResults();});}
$('submit').onclick=submit;
function renderResults(){show('results');const r=grade(attempt);$('score').textContent=`${r.score} / ${r.total} · ${Math.round(100*r.score/r.total)}%`;$('result-meta').textContent=`Attempt ${attempt.id.slice(0,8)} · ${r.answered} answered · Completed ${new Date(attempt.submitted).toLocaleString()}`;
 const totals=new Map();r.rows.forEach(row=>{const t=totals.get(row.topic)||[0,0];t[0]+=row.earned;t[1]++;totals.set(row.topic,t);});$('topics').replaceChildren();for(const [name,t]of totals){const n=el('div',undefined,'topic-row');n.append(el('span',name),el('strong',`${t[0]} / ${t[1]}`));$('topics').append(n);}
 $('review').replaceChildren();r.rows.forEach((row,i)=>{const q=bank.get(row.id),article=el('article',undefined,`panel review-item${row.earned?' correct':''}`);article.append(el('p',`Question ${i+1} · ${row.earned?'Correct':row.selected===null?'Unanswered':'Incorrect'}`,'eyebrow'),el('h3',q.stem));attempt.options[q.id].forEach((cid,j)=>{const c=q.choices.find(c=>c.id===cid);let text=`${String.fromCharCode(65+j)}. ${c.text}`;if(cid===row.selected)text+=' [Your answer]';if(cid===row.correct)text+=' [Correct answer]';article.append(el('p',text,`review-choice${cid===row.correct?' right':''}`));});article.append(el('p',q.explanation,'explanation'));$('review').append(article);});window.scrollTo({top:0,behavior:'instant'});
}
$('download').onclick=()=>{const r=grade(attempt);const data={course:'2105623',type:'Self-reported practice result; not a verified examination record',version:VERSION,attemptId:attempt.id,started:attempt.started,submitted:attempt.submitted,...r,questionOrder:attempt.order,choiceOrder:attempt.options};const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob),a=el('a');a.href=url;a.download=`optimization-practice-${attempt.id.slice(0,8)}.json`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);};
$('print').onclick=()=>window.print();
window.addEventListener('storage',event=>{if(event.key!==key)return;const updated=readSaved();if(!updated){show('welcome');attempt=null;$('resume').hidden=true;return;}attempt=updated;if(!$('welcome').hidden)welcome();else if(attempt.submitted)renderResults();else renderQuestion();});
function welcome(){show('welcome');if(attempt){$('resume').hidden=false;$('resume').textContent=attempt.submitted?'View saved result':'Continue saved attempt';$('start').textContent='Start a new shuffled attempt';$('resume-info').hidden=false;$('resume-info').textContent=`Saved attempt ${attempt.id.slice(0,8)}: ${attempt.submitted?'completed':`${Object.keys(attempt.answers).length} of 25 answered`}.`;}}
attempt=readSaved();welcome();
