/* No solver or interpolation in the browser. All chart objects come from Python. */
(async () => {
  'use strict';
  const el = id => document.getElementById(id);
  const fmt = x => typeof x === 'number' ? x.toLocaleString('en-US', {maximumFractionDigits: 4}) : x;
  let data, labId='v1-01', shownKey, submittedPrediction='', submittedNotes='';
  const lab = () => data.labs[labId];
  const current = () => lab().cases[shownKey];
  const controlKey = () => lab().controls.map(c => Number(el('control-'+c.id).value).toString()).join('|');
  function table(container, rows, headers) {
    const t=document.createElement('table'), head=t.createTHead().insertRow();
    headers.forEach(h => {const th=document.createElement('th');th.scope='col';th.textContent=h;head.append(th);});
    const body=t.createTBody();
    rows.forEach(row => {const tr=body.insertRow();row.forEach(v => {tr.insertCell().textContent=fmt(v);});});
    container.replaceChildren(t);
  }
  function chart() {
    const name=el('chart-choice').value, fig=current().figures[name];
    Plotly.react('chart',structuredClone(fig.data),structuredClone(fig.layout),{responsive:true,displayModeBar:false,scrollZoom:false});
    el('chart').setAttribute('aria-label',name==='sensitivity'?`${lab().title}: all prepared objective values compared with the original objective.`:`${lab().title}: ${lab().charts[name]}, baseline compared with the displayed case. Exact numbers are in Data and assumptions.`);
  }
  function renderCase() {
    const l=lab(), c=current(), baseline=l.cases[l.baseline], delta=c.objective-baseline.objective;
    el('objective-label').textContent=l.objectiveLabel+' ('+l.unit+')';
    el('objective-value').textContent=fmt(c.objective);
    el('objective-delta').textContent=`${delta>=0?'+':''}${fmt(delta)} ${l.unit} vs baseline`;
    ['secondary','tertiary'].forEach(k => {el(k+'-label').textContent=l[k+'Label'];el(k+'-value').textContent=fmt(c[k]);});
    const description=l.controls.map(control => `${control.label}: ${fmt(c.parameters[control.id])}`).join(' · ');
    el('case-status').textContent=shownKey===l.baseline?'Baseline shown':'Selected case shown';
    el('baseline-description').textContent='Displayed: '+description+'. Baseline: '+l.controls.map(control=>`${control.label}: ${fmt(baseline.parameters[control.id])}`).join('; ')+'.';
    el('interpretation').textContent=c.interpretation;
    const checks=el('checks');checks.replaceChildren();
    c.checks.forEach(check=>{const row=document.createElement('div');row.className='check-row';const a=document.createElement('span'),b=document.createElement('span');a.textContent=check.name;b.textContent=check.value;if(check.value.startsWith('Fails'))b.className='stress-fail';row.append(a,b);checks.append(row);});
    el('result-table').replaceChildren();
    (c.tables||[c.table]).forEach(t=>{const section=document.createElement('section');if(t.title){const h=document.createElement('h4');h.textContent=t.title;section.append(h);}const box=document.createElement('div');table(box,t.rows,t.columns);section.append(box);el('result-table').append(section);});
    const feedback=el('prediction-feedback');feedback.hidden=!submittedPrediction;
    if(submittedPrediction){const actual=Math.abs(delta)<1e-6?'same':delta>0?'up':'down';feedback.textContent=(submittedPrediction===actual?'Your prediction matches this case. ':'This case differs from your prediction. ')+(actual==='same'?'The objective is unchanged.':`The objective is ${actual==='up'?'higher':'lower'} than baseline by ${fmt(Math.abs(delta))} ${l.unit}. `)+'Which changed assumption explains it?';}
    chart();
  }
  function populateProblems(volume){
    const select=el('problem-choice');select.replaceChildren();
    Object.entries(data.labs).filter(([id,l])=>l.volume===Number(volume)).forEach(([id,l])=>{const option=document.createElement('option');option.value=id;option.textContent=String(l.problem).padStart(2,'0')+' · '+l.title;select.append(option);});
  }
  function selectLab(id) {
    labId=id;const l=lab();shownKey=l.baseline;submittedPrediction='';submittedNotes='';
    el('volume-choice').value=String(l.volume);
    populateProblems(l.volume);el('problem-choice').value=id;
    const ids=Object.keys(data.labs);el('previous-problem').disabled=ids.indexOf(id)===0;el('next-problem').disabled=ids.indexOf(id)===ids.length-1;
    el('experiment-tag').textContent=l.eyebrow;el('experiment-title').textContent=l.question;el('experiment-description').textContent=l.intro;
    el('chapter-link').href=l.book;el('assumptions').textContent=l.assumptions;el('challenge').textContent=l.challenge;
    el('prediction-label').textContent=`Compared with baseline, will ${l.objectiveLabel.toLowerCase()} be…?`;
    el('prediction').value='';el('reflection').value='';
    const controls=el('parameter-controls');controls.replaceChildren();
    l.controls.forEach(c=>{const label=document.createElement('label'),select=document.createElement('select');label.htmlFor='control-'+c.id;label.textContent=c.label;select.id=label.htmlFor;c.values.forEach(v=>{const o=document.createElement('option');o.value=v;o.textContent=fmt(v);select.append(o);});select.value=c.default;select.addEventListener('change',()=>{el('case-status').textContent=controlKey()===shownKey?'Displayed case is current':'Inputs changed. Reveal to update results.';});controls.append(label,select);});
    const choices=el('chart-choice');choices.replaceChildren();Object.entries(l.charts).forEach(([k,v])=>{const o=document.createElement('option');o.value=k;o.textContent=v;choices.append(o);});
    const equations=el('equations');equations.replaceChildren();l.equations.forEach(e=>{const box=document.createElement('div');box.className='equation';const title=document.createElement('strong'),math=document.createElement('code'),why=document.createElement('p');title.textContent=e.label;math.textContent=e.math;why.textContent=e.why;box.append(title,math,why);equations.append(box);});
    renderCase();
  }
  try {
    const response=await fetch('assets/cases.json');if(!response.ok)throw new Error('Case library unavailable');
    data=await response.json();el('loading').hidden=true;el('experiment').hidden=false;
    el('library-count').textContent=`${data.problemCount} problems · ${data.caseCount} verified Pyomo cases`;
    const aliases={food:'v1-01',blend:'v2-03',hydrogen:'v2-14'};
    const requested=new URL(location.href).searchParams.get('lab');
    const initial=aliases[requested]||requested;selectLab(data.labs[initial]?initial:'v1-01');
    function navigate(id){selectLab(id);const url=new URL(location.href);url.searchParams.set('lab',id);history.replaceState(null,'',url);}
    el('volume-choice').addEventListener('change',()=>navigate(Object.keys(data.labs).find(id=>data.labs[id].volume===Number(el('volume-choice').value))));
    el('problem-choice').addEventListener('change',()=>navigate(el('problem-choice').value));
    ['previous','next'].forEach(direction=>el(direction+'-problem').addEventListener('click',()=>{const ids=Object.keys(data.labs);navigate(ids[ids.indexOf(labId)+(direction==='next'?1:-1)]);}));
    el('reveal').addEventListener('click',()=>{shownKey=controlKey();submittedPrediction=el('prediction').value;submittedNotes=el('reflection').value;renderCase();});
    el('reset').addEventListener('click',()=>selectLab(labId));
    el('chart-choice').addEventListener('change',chart);
    el('export').addEventListener('click',()=>{
      const record={experiment:lab().title,mode:data.mode,parameters:current().parameters,objective:current().objective,units:lab().unit,baseline:lab().cases[lab().baseline].parameters,baselineObjective:lab().cases[lab().baseline].objective,
        variables:current().variables||null,tables:current().tables||[current().table],prediction:submittedPrediction||null,reflection:el('reflection').value,checks:current().checks,table:current().table,versions:data.versions};
      const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`optimization-${labId}-${shownKey.replaceAll('|','-')}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
  } catch(error) {el('loading').hidden=false;el('loading').textContent='The case library could not load. Serve this page over HTTP and reload. '+error.message;el('experiment').hidden=true;}
})();
