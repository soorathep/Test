import {stringifyStudy} from './study-state.js';
import * as e from './consistency.js';
import {palette as c} from './palette.js';
const $=id=>document.getElementById(id),f=(x,n=3)=>x==null?'undefined':Number(x).toFixed(n);
let data,set,area,local,model=null,worker=null;
const line=(x,y,name,color=c.teal,dash='solid',mode='lines')=>({x,y,name,mode,line:{color,width:2,dash},marker:{color,size:6},connectgaps:false});
function makeSet(){const key=$('ct-dataset').value;return key.startsWith('article')?e.articleSet(data,Number(key.slice(7))):e.syntheticSet(data,{path:key==='syntheticT'?'isothermal':'isobaric',kind:$('ct-scenario').value,amplitude:Number($('ct-amplitude').value),n:Number($('ct-count').value)});}
function stopFit(){if(worker){worker.terminate();worker=null;}$('ct-fit').disabled=false;}
function card(title,result,value){
 const el=document.createElement('div');el.className='ct-card';
 const label=result?.status??'not-run',text={'meets-criterion':'Meets this criterion','outside-criterion':'Outside this criterion','not-assessed':'Not assessed','not-applicable':'Not applicable','not-run':'Not run'}[label];
 const h=document.createElement('h3');h.textContent=title;const status=document.createElement('strong');status.className='ct-status '+label;status.textContent=text+(result?.conditional?' · conditional':'');
 const p=document.createElement('p');p.textContent=value;const small=document.createElement('small');small.textContent=result?.reason??result?.criterion??'Run the modeling test to evaluate this criterion.';
 el.append(h,status,p,small);return el;
}
function renderCards(){
 $('ct-scorecards').replaceChildren(card('1 · Isothermal area',area.redlichKister,`I = ${f(area.area.signed,5)}; D = ${f(area.area.D)}%${area.full?'':' (partial interval)'}`),card('2 · Herington',area.herington,`J = ${f(area.J)}; D − J = ${f(area.DminusJ)}${area.full?'':' (partial only)'}`),card('3 · Differential',local,`100 mean |r| = ${f(local.score)}`),card('4 · Van Ness-type',model,model?`Δp = ${f(model.deltaP)}%; Δy = ${f(model.deltaY)} percentage points`:'Model reproduction of P and y'));
}
async function chart(){
 const kind=$('ct-chart').value;let traces=[],xTitle='Liquid mole fraction · x₁',yTitle,note;
 if(kind==='area'){
  traces=[line(set.valid.map(r=>r.x),set.valid.map(r=>r.f),set.synthetic?'Generated log ratio':'Inferred log ratio',set.synthetic&&set.kind!=='clean'?c.amber:c.teal,'solid','lines+markers')];
  if(set.synthetic&&set.kind!=='clean'){const ref=e.syntheticSet(data,{path:set.path,kind:'clean',n:set.n});traces.unshift(line(ref.valid.map(r=>r.x),ref.valid.map(r=>r.f),'Consistent reference',c.teal));}
  if(area.conditional)traces.push(line(area.points.map(r=>r.x),area.points.map(r=>r.f),'Assumed full-range curve',c.amber,'dash'));
  yTitle='ln(γ₁/γ₂)';note=`A₊ = ${f(area.area.positive,5)}, A₋ = ${f(area.area.negative,5)}. ${area.full?'Full-range integral':'Partial-range diagnostic'}. ${area.conditional?'Endpoint estimates are assumptions.':''}`;
 }else if(kind==='differential'){
  traces=[line(local.points.map(r=>r.x),local.points.map(r=>r.raw),'Raw derivative residual',c.teal,'solid','lines+markers')];
  if(set.path==='isobaric'&&set.synthetic&&$('ct-heat').checked)traces.push(line(local.points.map(r=>r.x),local.points.map(r=>r.residual),'With supplied Hᴱ correction',c.amber));
  yTitle='Local residual r (dimensionless)';note=local.reason;
 }else if(kind==='model'){
  if(model)traces=[line(model.points.map(r=>r.x),model.points.map(r=>r.pressureResidual),'100 ΔP/P',c.amber,'solid','lines+markers'),line(model.points.map(r=>r.x),model.points.map(r=>r.yResidual),'100 Δy',c.amber,'dash','lines+markers')];
  yTitle='P error / % · y error / percentage points';note=model?model.method:'Run the modeling test first. No residuals or verdict are available yet.';
 }else{
  const isT=set.path==='isothermal',key=isT?'PkPa':'T';
  traces=[line(set.rows.map(r=>r.x),set.rows.map(r=>r[key]),'Liquid compositions',c.teal,'solid','markers'),line(set.rows.map(r=>r.y),set.rows.map(r=>r[key]),'Vapor compositions',c.teal,'solid','markers')];traces[1].marker.symbol='diamond-open';
  xTitle='Mole fraction of 2-propanol · x₁ or y₁';yTitle=isT?'Pressure / kPa':'Temperature / K';note='All observations are shown here, including any excluded from activity inference. Numerical values are available below.';
 }
 await Plotly.react('ct-plot',traces,{margin:{l:65,r:16,t:18,b:60},font:{family:'Archivo, sans-serif',color:c.graphite,size:12},paper_bgcolor:'transparent',plot_bgcolor:'transparent',showlegend:false,xaxis:{title:{text:xTitle},zeroline:false},yaxis:{title:{text:yTitle},zerolinecolor:c.graphite},hovermode:'closest'},{responsive:true,displayModeBar:false});
 $('ct-legend').replaceChildren(...traces.map(t=>{const span=document.createElement('span'),i=document.createElement('i');i.style.borderColor=t.line.color;i.style.borderTopStyle=t.line.dash==='solid'?'solid':'dashed';span.append(i,document.createTextNode(t.name));return span;}));$('ct-chart-note').textContent=note;
}
function render(){
 area=e.areaAnalysis(set,set.synthetic?'none':$('ct-extension').value);local=e.differential(set,$('ct-heat').checked);
 $('ct-title').textContent=set.name;$('ct-scope').textContent=`${set.rows.length} observations; ${set.valid.length} activity pairs; ${set.excluded.length} excluded. ${set.synthetic?'Synthetic endpoint limits are supplied.':'The article’s reported result remains separate from this calculation.'}`;
 renderCards();chart();
 $('ct-interpretation').textContent=set.synthetic&&set.kind==='cancel'&&set.path==='isothermal'?'The imposed cosine error has exactly zero net area. Compare its global area with the local residual and the modeling result. A criterion met here is not a blanket validation.':area.conditional?'This area result depends on extrapolation and, for the quadratic option, smoothing. Compare another endpoint assumption. Agreement between two extrapolations does not establish the missing measurements.':'Each result addresses a different claim. “Not assessed” means missing information or an unmet assumption; it is not a failed consistency test.';
 $('ct-table-note').textContent=set.synthetic?set.heatSource:`Original article observations; ${set.excluded.length} excluded pairs. No independent Hᴱ is provided. Table 6 reports ${set.paper.value}, tolerance 10%, “${set.paper.result}”; that number is not reproduced by these teaching variants.`;
 $('ct-table').innerHTML='<table><thead><tr><th>x₁</th><th>y₁</th><th>T / K</th><th>P / kPa</th><th>ln γ₁</th><th>ln γ₂</th><th>Status</th></tr></thead><tbody>'+set.rows.map(r=>`<tr><td>${f(r.x,4)}</td><td>${f(r.y,4)}</td><td>${f(r.T,2)}</td><td>${f(r.PkPa,3)}</td><td>${r.ln?f(r.ln[0],4):'—'}</td><td>${r.ln?f(r.ln[1],4):'—'}</td><td>${r.reason??'Included'}</td></tr>`).join('')+'</tbody></table>';
 $('ct-fit-detail').textContent=model?JSON.stringify({parameters:model.parameters,centeredParameters:model.centeredParameters,objective:model.objective,atBound:model.atBound,method:model.method},null,2):'Modeling test not run.';
}
function update(){
 try{stopFit();model=null;$('ct-error').hidden=true;$('ct-results').hidden=false;$('ct-export').disabled=false;
  set=makeSet();$('ct-synthetic-controls').hidden=!set.synthetic;$('ct-endpoint-controls').hidden=set.synthetic;
  $('ct-amplitude-value').textContent=f(Number($('ct-amplitude').value),2);$('ct-amplitude').disabled=$('ct-scenario').value==='clean';
  $('ct-heat').disabled=!(set.synthetic&&set.path==='isobaric');$('ct-heat-note').textContent=set.path==='isothermal'?'No temperature correction on an isothermal path.':set.synthetic?'Toggle the known synthetic Hᴱ term to see its effect.':'Article Hᴱ unavailable: the differential test cannot assign a verdict.';
  $('ct-fit-status').textContent='Modeling test has not been run for this data set.';render();
 }catch(error){$('ct-error').hidden=false;$('ct-error').textContent=error.message;$('ct-results').hidden=true;$('ct-export').disabled=true;$('ct-fit').disabled=true;}
}
function fit(){
 stopFit();model=null;render();$('ct-fit').disabled=true;$('ct-fit-status').textContent='Fitting P and y from five starts…';$('ct-error').hidden=true;
 const current=new Worker(new URL('./consistency-worker.js',import.meta.url),{type:'module'});worker=current;
 current.onmessage=({data:reply})=>{if(worker!==current)return;stopFit();if(reply.error){$('ct-fit-status').textContent='No modeling verdict.';$('ct-error').hidden=false;$('ct-error').textContent=reply.error;return;}model=reply.result;$('ct-fit-status').textContent=`Converged: ${model.count} points. ${model.atBound?'A parameter reached its bound; model limitations may dominate.':'No fitted parameter at a bound.'}`;render();};
 current.onerror=()=>{if(worker!==current)return;stopFit();$('ct-fit-status').textContent='Modeling worker failed; no verdict.';};
 current.postMessage({set,properties:data});
}
function exportResults(){
 const payload={version:e.CONSISTENCY_VERSION,articleSource:data,settings:{dataset:$('ct-dataset').value,extension:$('ct-extension').value,heatCorrection:$('ct-heat').checked},set,area,differential:local,modeling:model,reflection:$('ct-reflection').value};
 const url=URL.createObjectURL(new Blob([stringifyStudy(payload,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='thermodynamic-consistency-study.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
try{const response=await fetch('assets/ipa-water.json');if(!response.ok)throw new Error('Data could not be loaded.');data=await response.json();$('ct-app').hidden=false;$('ct-loading').hidden=true;
 for(const id of ['ct-dataset','ct-scenario','ct-count'])$(id).addEventListener('change',update);
 $('ct-amplitude').addEventListener('input',update);$('ct-extension').addEventListener('change',render);$('ct-heat').addEventListener('change',render);$('ct-chart').addEventListener('change',chart);$('ct-fit').addEventListener('click',fit);$('ct-export').addEventListener('click',exportResults);update();
}catch(error){$('ct-loading').textContent=error.message;}
