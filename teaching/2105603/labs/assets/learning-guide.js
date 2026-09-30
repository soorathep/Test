// Worksheet notes are independent of solver state and never certify correctness.
const file=location.pathname.split('/').pop()||'index.html',lab=file.replace('.html','');
const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
const download=(value,name)=>{const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'})),a=el('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
async function init(){const response=await fetch(new URL('./learning-path.json',import.meta.url));if(!response.ok)throw new Error('Learning guide unavailable');const data=await response.json(),guide=data.labs[lab];if(!guide)return;
const panel=el('section');panel.className='learning-guide';panel.setAttribute('aria-label','Independent lab activity');
const link=el('a',`Session ${guide.session} · learning path and slides`);link.href='learning-path.html#session-'+guide.session;panel.append(link);
const details=el('details');details.open=true;details.append(el('summary','Guided activity · predict, calculate, explain'),el('p',guide.predict));const list=el('ol');guide.steps.forEach(v=>list.append(el('li',v)));details.append(list,el('p','Evidence to retain: '+guide.check),el('p','Scope: '+guide.limit));panel.append(details);
const notes=el('details');notes.append(el('summary','My worksheet · save and continue later'));
notes.append(el('p','These notes are separate from calculator inputs and results. Save the lab’s study export as well. “Save on this browser” stores only the five notes below on this device; no upload or grading is performed.'));
const fields={prediction:'Prediction before running',baseline:'Baseline inputs, units and source',change:'Changed input and numerical observations',checks:'Balance/residual checks and assumptions',explanation:'Explanation and limits of the conclusion'},inputs={};
for(const [key,label] of Object.entries(fields)){const l=el('label',label),t=el('textarea');t.id='worksheet-'+key;t.rows=3;t.maxLength=12000;l.htmlFor=t.id;inputs[key]=t;notes.append(l,t);}
const status=el('p');status.setAttribute('role','status');const key='thermo-worksheet-v1:'+lab;
function read(){return{kind:'thermo-worksheet',version:1,lab,notes:Object.fromEntries(Object.entries(inputs).map(([k,v])=>[k,v.value]))};}
function validate(v){if(v?.kind!=='thermo-worksheet'||v.version!==1||v.lab!==lab||!v.notes||Object.keys(fields).some(k=>typeof v.notes[k]!=='string'||v.notes[k].length>12000))throw new Error('Choose a valid worksheet for this lab, not a calculator study export.');return v;}
function fill(v){validate(v);for(const k of Object.keys(fields))inputs[k].value=v.notes[k];}
const button=(label,fn)=>{const b=el('button',label);b.type='button';b.className='secondary-button';b.addEventListener('click',()=>{try{fn();}catch(e){status.textContent=e.message;}});notes.append(b);};
button('Save on this browser',()=>{localStorage.setItem(key,JSON.stringify(read()));status.textContent='Notes saved on this browser. Calculator state is not included.';});
button('Download worksheet',()=>{download(read(),`lab-${lab}-worksheet.json`);status.textContent='Worksheet downloaded. Export calculator results separately.';});
button('Clear saved notes',()=>{localStorage.removeItem(key);for(const t of Object.values(inputs))t.value='';status.textContent='Worksheet notes cleared on this browser.';});
const label=el('label','Restore worksheet JSON'),fileInput=el('input');fileInput.type='file';fileInput.accept='.json,application/json';fileInput.id='worksheet-import';label.htmlFor=fileInput.id;notes.append(label,fileInput);
fileInput.addEventListener('change',async()=>{try{const f=fileInput.files[0];if(!f)return;if(f.size>100000)throw new Error('Worksheet file exceeds 100 kB.');fill(JSON.parse(await f.text()));status.textContent='Worksheet restored in memory. Save on this browser to retain it here.';}catch(e){status.textContent=e.message;}finally{fileInput.value='';}});
notes.append(status);panel.append(notes);document.querySelector('.hero')?.after(panel);
try{const saved=localStorage.getItem(key);if(saved){fill(JSON.parse(saved));status.textContent='Saved notes restored. Reopen your calculator study separately.';}}catch{status.textContent='Browser storage is unavailable or the saved notes are invalid. JSON download is still available.';}
}
init().catch(()=>{/* Calculator remains usable if optional guidance cannot load. */});
