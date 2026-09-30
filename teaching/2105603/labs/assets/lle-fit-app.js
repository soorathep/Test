import * as e from './lle-fit.js';
import * as s from './stability.js';
import {palette as c} from './palette.js';
const $=id=>document.getElementById(id),fmt=(v,n=5)=>v==null?'N/A':v!==0&&Math.abs(v)<1e-4?v.toExponential(2):Number(v).toFixed(n);
let data,set,result=null,worker=null;
const line=(x,y,name,color,dash='solid',mode='lines')=>({x,y,name,mode,line:{color,width:2,dash},marker:{color,size:7},connectgaps:false});
function stop(){if(worker)worker.terminate();worker=null;}
function clear(){stop();result=null;$('lf-results').hidden=true;$('lf-placeholder').hidden=false;$('lf-export').disabled=true;$('lf-runs').textContent='Run a fit to compare starts.';$('lf-fit').disabled=!data;$('lf-status').textContent='Inputs changed. Fit again to update the result.';}
function num(id){if($(id).value.trim()==='')throw new Error('Enter all active numerical inputs.');const n=Number($(id).value);if(!Number.isFinite(n))throw new Error('Numerical inputs must be finite.');return n;}
function settings(){const alpha=num('lf-alpha'),start=[num('lf-tau12'),num('lf-tau21')];s.parameters({model:'nrtl',alpha,tau12:start[0],tau21:start[1]});return{alpha,start,multistart:$('lf-multistart').checked};}
function readSet(){return $('lf-data').value==='synthetic'?e.synthetic(num('lf-noise'),num('lf-seed')):e.experimental(data,num('lf-temperature'));}
function fail(err){clear();$('lf-error').textContent=err.message;$('lf-error').hidden=false;$('lf-status').textContent='Calculation unavailable. Correct the inputs and run again.';}
function table(headers,rows){const t=document.createElement('table'),head=t.createTHead().insertRow();for(const v of headers){const cell=document.createElement('th');cell.textContent=v;head.append(cell);}const body=t.createTBody();for(const row of rows){const tr=body.insertRow();for(const v of row)tr.insertCell().textContent=String(v);}return t;}
function renderData(){
 const synthetic=$('lf-data').value==='synthetic';$('lf-synthetic').hidden=!synthetic;$('lf-experimental').hidden=synthetic;
 set=readSet();$('lf-title').textContent=set.name;$('lf-data-note').textContent=`${set.rows.length} coexistence pair${set.rows.length>1?'s':''} at ${set.rows[0].T} K. ${synthetic?'Hypothetical component 1; known τ₁₂=3, τ₂₁=2, α=0.3.':'Component 1: cyclohexane. Each temperature is fitted independently.'}`;
 $('lf-table-note').textContent=synthetic?set.noiseDescription+' Clean repeats share exactly the same phase compositions.':set.uncertainty;
 $('lf-data-table').replaceChildren(table(['Pair','T / K','x₁ᵅ','x₁ᵝ','U95(x₁ᵅ)','U95(x₁ᵝ)'],set.rows.map((r,i)=>[i+1,r.T,fmt(r.xAlpha,6),fmt(r.xBeta,6),fmt(r.expandedUncertaintyAlpha),fmt(r.expandedUncertaintyBeta)])));
}
function inputsChanged(){clear();try{renderData();settings();$('lf-error').hidden=true;}catch(err){set=null;$('lf-data-table').replaceChildren();fail(err);}}
async function chart(){
 if(!result)return;const kind=$('lf-chart').value,d=result.diagnostics,p=result.parameters,rows=set.rows;let traces=[],xTitle,yTitle,note,extra={};
 $('lf-phase').hidden=kind!=='tpd';$('lf-phase-label').hidden=kind!=='tpd';
 if(kind==='composition'){
  const n=rows.map((_,i)=>i+1);traces=[line(n,rows.map(r=>r.xAlpha),'Observed α',c.teal,'solid','markers'),line(n,rows.map(r=>r.xBeta),'Observed β',c.teal,'solid','markers')];traces[1].marker.symbol='diamond';
  if(set.kind==='experimental')for(const [i,key] of ['expandedUncertaintyAlpha','expandedUncertaintyBeta'].entries())traces[i].error_y={type:'data',array:rows.map(r=>r[key]),visible:true,color:c.teal};
  if(d.binodal){traces.push(line([.6,rows.length+.4],[d.binodal.xAlpha,d.binodal.xAlpha],'Predicted α',c.amber));traces.push(line([.6,rows.length+.4],[d.binodal.xBeta,d.binodal.xBeta],'Predicted β',c.amber,'dash'));}
  xTitle='Observation pair';yTitle='Component 1 mole fraction';extra={xaxis:{dtick:1,range:[.5,rows.length+.5]},yaxis:{range:[0,1]}};note='Predicted compositions come from global common-tangent equilibrium after fitting. Error bars, when present, are source expanded uncertainties at 95% confidence; they are not regression confidence intervals.';
 }else if(kind==='gibbs'){
  const initial=Array.from({length:401},(_,i)=>({x:i/400,g:s.gibbs(i/400,result.initial.parameters)}));traces=[line(initial.map(v=>v.x),initial.map(v=>v.g),'Initial-guess liquid',c.teal),line(d.curve.map(v=>v.x),d.curve.map(v=>v.g),'Fitted liquid',c.amber),line(d.curve.map(v=>v.x),d.curve.map(v=>v.hull),'Global convex envelope',c.graphite,'dash')];
  for(const [i,b] of d.gaps.entries())traces.push(line([b.xAlpha,b.xBeta],[b.gAlpha,b.gBeta],`Common tangent ${i+1}`,c.graphite,'solid','lines+markers'));
  const observed=[d.observedMean.xAlpha,d.observedMean.xBeta];traces.push(line(observed,observed.map(x=>s.gibbs(x,p)),'Observed mean compositions',c.teal,'solid','markers'));
  xTitle='Mole fraction of component 1 · x₁';yTitle='Mixing Gibbs energy / RT';note=d.message+' All verified gaps are shown. The composition RMSE uses the branch nearest the observations.';
 }else if(kind==='tpd'){
  const i=Number($('lf-phase').value),a=d.observedTPD[i],b=d.predictedTPD[i];traces=[line(a.points.map(v=>v.x),a.points.map(v=>v.tpd),'Observed mean composition',c.teal)];if(b)traces.push(line(b.points.map(v=>v.x),b.points.map(v=>v.tpd),'Predicted coexisting liquid',c.amber,'dash'));
  xTitle='Trial composition · w₁';yTitle='TPD / RT';note=`Observed-mean minimum: ${fmt(a.minimum,8)}. Predicted-liquid minimum: ${fmt(b?.minimum,8)}. Observed means can be unstable under a fitted model when there is measurement noise or model error. The global search uses stationary points, not plot samples.`;
 }else if(kind==='objective'){
  const grid=Array.from({length:45},(_,i)=>-2+8*i/44),z=grid.map(tau21=>grid.map(tau12=>Math.log10(Math.max(1e-16,e.objective(rows,{...p,tau12,tau21})))));
  traces=[{x:grid,y:grid,z,type:'heatmap',name:'log₁₀ J',colorscale:[[0,c.paper],[1,c.teal]],colorbar:{title:{text:'log₁₀ J'},thickness:12},hovertemplate:'τ₁₂=%{x:.3f}<br>τ₂₁=%{y:.3f}<br>log₁₀ J=%{z:.3f}<extra></extra>'},line([p.tau12],[p.tau21],'Selected fit',c.amber,'solid','markers'),line([result.initial.parameters.tau12],[result.initial.parameters.tau21],'Your starting point',c.graphite,'solid','markers')];
  xTitle='τ₁₂';yTitle='τ₂₁';note='A sampled objective landscape at fixed α. The 45 × 45 grid illustrates parameter sensitivity; it neither drives the optimizer nor proves a global parameter optimum.';
 }else{
  traces=result.runs.map((r,i)=>line(r.history.map(v=>v.iteration),r.history.map(v=>Math.max(v.objective,1e-20)),`Start ${i+1}`,i===0?c.teal:c.amber,i===0?'solid':'dash'));
  xTitle='Iteration';yTitle='Objective J (log scale)';extra={yaxis:{type:'log'}};note='Teal is your start; amber lines are the additional starts. Values below 10⁻²⁰ are clipped for display only. Full objectives and parameter histories are exported.';
 }
 await Plotly.react('lf-plot',traces,{margin:{l:65,r:kind==='objective'?65:18,t:20,b:58},font:{family:'Archivo, sans-serif',color:c.graphite,size:12},paper_bgcolor:'transparent',plot_bgcolor:'transparent',showlegend:false,xaxis:{title:{text:xTitle},zeroline:false,...extra.xaxis},yaxis:{title:{text:yTitle},zerolinecolor:c.graphite,...extra.yaxis},hovermode:'closest'},{responsive:true,displayModeBar:false});
 $('lf-legend').replaceChildren(...traces.filter(t=>t.line).map(t=>{const el=document.createElement('span'),swatch=document.createElement('i');swatch.style.borderColor=t.line.color;swatch.style.borderTopStyle=t.line.dash==='solid'?'solid':'dashed';el.append(swatch,document.createTextNode(t.name));return el;}));$('lf-chart-note').textContent=note;
}
function render(){
 const r=result,d=r.diagnostics;$('lf-fit12').textContent=fmt(r.parameters.tau12);$('lf-fit21').textContent=fmt(r.parameters.tau21);$('lf-rmse').textContent=fmt(d.compositionRMSE);$('lf-results').hidden=false;$('lf-placeholder').hidden=true;$('lf-export').disabled=false;
 $('lf-interpretation').textContent=`${r.converged?'The selected optimizer converged.':'The iteration limit was reached; the selected result is not converged.'} ${r.atBound?'At least one parameter is at a search bound. ':''}${d.message} Nearest-branch composition RMSE: ${fmt(d.compositionRMSE)}. ${set.kind==='experimental'?'One experimental pair and two fitted parameters can give a nearly exact calibration; this is not independent predictive validation.':'Compare with the known synthetic parameters. Changing fixed α can preserve the compositions while changing both τ values.'}`;
 const checks=[['Chemical-potential RMSE',fmt(r.chemicalPotentialRMSE,8)],['Initial objective J',fmt(r.initial.objective,8)],['Fitted objective J',fmt(r.objective,8)],['Common-tangent residual',fmt(d.binodal?.tangentResidual,8)],['Predicted α minimum TPD',fmt(d.predictedTPD[0]?.minimum,8)],['Predicted β minimum TPD',fmt(d.predictedTPD[1]?.minimum,8)],['Residual-Jacobian singular-value ratio',r.sensitivity.singularValueRatio===null?'Singular / unresolved':fmt(r.sensitivity.singularValueRatio,2)]];
 $('lf-checks').replaceChildren(...checks.map(([name,value])=>{const el=document.createElement('div');el.className='check-row';const a=document.createElement('span'),b=document.createElement('strong');a.textContent=name;b.textContent=value;el.append(a,b);return el;}));
 $('lf-runs').replaceChildren(table(['Start','Initial τ₁₂, τ₂₁','Fitted τ₁₂, τ₂₁','J','Converged','At bound','x RMSE','Verified gaps'],r.runs.map((v,i)=>[i+1,v.start.join(', '),`${fmt(v.parameters.tau12)}, ${fmt(v.parameters.tau21)}`,fmt(v.objective,8),v.converged?'Yes':'No',v.atBound?'Yes':'No',fmt(v.diagnostic.compositionRMSE),v.diagnostic.resolved?v.diagnostic.gaps:'Unresolved'])));
 const q=new URLSearchParams({model:'nrtl',tau12:r.parameters.tau12,tau21:r.parameters.tau21,alpha:r.parameters.alpha,z:d.binodal?(d.binodal.xAlpha+d.binodal.xBeta)/2:.5});$('lf-stability-link').href=`stability.html?${q}#lle-experiment`;
 const v=new URLSearchParams({source:'lab05',model:'nrtl',tau12:r.parameters.tau12,tau21:r.parameters.tau21,alpha:r.parameters.alpha,referenceT:set.rows[0].T,T:set.rows[0].T,temperatureMode:'fixed',fitKind:set.kind});$('lf-vle-link').href=`./?${v}#experiment`;
 chart().catch(fail);
}
function run(){clear();try{renderData();const options=settings();$('lf-error').hidden=true;$('lf-fit').disabled=true;$('lf-status').textContent='Fitting parameters and checking global stability…';worker=new Worker(new URL('./lle-fit-worker.js',import.meta.url),{type:'module'});worker.onmessage=({data:response})=>{stop();$('lf-fit').disabled=false;if(response.error){fail(new Error(response.error));return;}result=response.result;$('lf-status').textContent='Fit complete. Inspect reproduction and stability separately.';render();};worker.onerror=()=>fail(new Error('Regression worker failed to load or run. Reload this page and try again.'));worker.postMessage({rows:set.rows,options});}catch(err){fail(err);}}
for(const id of ['lf-data','lf-temperature','lf-noise','lf-seed','lf-alpha','lf-tau12','lf-tau21','lf-multistart'])$(id).addEventListener('input',inputsChanged);
$('lf-noise-range').addEventListener('input',()=>{$('lf-noise').value=$('lf-noise-range').value;inputsChanged();});$('lf-noise').addEventListener('input',()=>{$('lf-noise-range').value=$('lf-noise').value;});
$('lf-fit').addEventListener('click',run);for(const id of ['lf-chart','lf-phase'])$(id).addEventListener('change',()=>chart().catch(fail));
$('lf-reset').addEventListener('click',()=>{$('lf-data').value='synthetic';$('lf-noise').value=0;$('lf-noise-range').value=0;$('lf-seed').value=42;$('lf-alpha').value=.3;$('lf-tau12').value=1;$('lf-tau21').value=1;$('lf-multistart').checked=true;inputsChanged();});
$('lf-export').addEventListener('click',()=>{if(!result)return;const blob=new Blob([JSON.stringify({version:e.LLE_FIT_VERSION,dataset:set,result,reflection:$('lf-reflection').value},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='lle-regression-study.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
try{const response=await fetch('./assets/cyclohexane-methanol-lle.json');if(!response.ok)throw new Error('Experimental source data could not be loaded.');data=await response.json();$('lf-temperature').replaceChildren(...data.rows.map(r=>new Option(String(r.T),String(r.T))));$('lf-temperature').value='298.15';inputsChanged();$('lf-status').textContent='Ready. Select Fit & verify to begin.';}catch(err){fail(err);}
