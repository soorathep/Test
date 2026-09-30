import * as engine from './case-study.js';
import {palette as c} from './palette.js';
const $=id=>document.getElementById(id),fmt=(v,n=4)=>v==null?'—':Number(v).toFixed(n);
let data,diagnostic,parameters,fitResult=null,fitContext=null,lastExport=null;
const trace=(x,y,name,color,dash='solid',mode='lines')=>({x,y,name,mode,line:{color,width:2,dash},marker:{color,size:6},connectgaps:false});
function plot(id,traces,xTitle,yTitle){
  return Plotly.react(id,traces,{margin:{l:58,r:18,t:16,b:53},font:{family:'Archivo, sans-serif',size:12,color:c.graphite},paper_bgcolor:'transparent',plot_bgcolor:'transparent',showlegend:false,xaxis:{title:{text:xTitle},zeroline:false},yaxis:{title:{text:yTitle},zerolinecolor:c.graphite},hovermode:'closest'},{responsive:true,displayModeBar:false});
}
function selected(){return data.datasets.find(d=>d.pressureKPa===Number($('dataset').value));}
function synthetic(){
  const bias=Number($('bias').value),s=engine.synthetic(data.nrtl,bias),ref=engine.synthetic(data.nrtl,0);
  $('bias-value').textContent=fmt(bias,2);
  plot('synthetic-plot',[trace(ref.points.map(p=>p.x),ref.points.map(p=>p.f),'Consistent reference',c.teal),trace(s.points.map(p=>p.x),s.points.map(p=>p.f),'Perturbed activity data',c.amber)],'x₁','ln(γ₁/γ₂)');
  $('synthetic-summary').textContent=`Teal: consistent reference; amber: controlled perturbation. Signed area = ${fmt(s.area.signed,6)}; exact δ/3 = ${fmt(bias/3,6)}; D = ${fmt(s.area.D,3)}%. ${bias===0?'The small area residual is numerical quadrature error.':'Nonzero signed area reveals the imposed inconsistency.'}`;
  if(lastExport)lastExport.synthetic=s;
}
async function render(){
 try{
  $('case-error').hidden=true;$('case-results').hidden=false;$('download-case').disabled=false;
  const ds=selected();diagnostic=engine.experimentalDiagnostic(ds,data);
  parameters=$('case-model').value==='fit'&&fitResult?fitResult.parameters:data.nrtl;
  if($('case-model').value==='fit'&&!fitResult){$('case-model').value='paper';}
  const valid=diagnostic.rows.filter(r=>r.ln),check=engine.modelCheck(parameters),predicted=valid.map(r=>({...r,modelLn:engine.nrtl(r.x,r.T,parameters).ln}));
  const curve=engine.curve(data,ds.pressureKPa,parameters),rmse=Math.sqrt(engine.objective(valid,parameters));
  $('usable').textContent=valid.length;$('excluded').textContent=`${20-valid.length} excluded pairs; see table`;$('rmse').textContent=fmt(rmse,3);
  $('case-heading').textContent=`Isopropanol + water · ${ds.pressureKPa} kPa`;
  const kind=$('case-chart').value;let traces,xTitle='Liquid mole fraction · x₁',yTitle,note;
  if(kind==='txy'){
    traces=[trace(ds.rows.map(r=>r.x),ds.rows.map(r=>r.T),'Measured liquid',c.teal,'solid','markers'),trace(ds.rows.map(r=>r.y),ds.rows.map(r=>r.T),'Measured vapor',c.teal,'dot','markers'),trace(curve.map(r=>r.x),curve.map(r=>r.T),'NRTL bubble',c.amber),trace(curve.map(r=>r.y),curve.map(r=>r.T),'NRTL dew',c.amber,'dash')];traces[1].marker.symbol='diamond-open';
    xTitle='Mole fraction of 2-propanol · x₁ or y₁';yTitle='Temperature / K';note='All 20 original observations are shown. Model curves stop at the joint property domain (334–362.41 K); gaps are not extrapolated.';
  }else if(kind==='gamma'){
    traces=[trace(valid.map(r=>r.x),valid.map(r=>Math.exp(r.ln[0])),'Inferred γ₁',c.teal,'solid','markers'),trace(valid.map(r=>r.x),valid.map(r=>Math.exp(r.ln[1])),'Inferred γ₂',c.teal,'dot','markers'),trace(predicted.map(r=>r.x),predicted.map(r=>Math.exp(r.modelLn[0])),'NRTL γ₁',c.amber),trace(predicted.map(r=>r.x),predicted.map(r=>Math.exp(r.modelLn[1])),'NRTL γ₂',c.amber,'dash')];traces[1].marker.symbol='diamond-open';yTitle='Activity coefficient · γ';note='Each model value uses the measured T and x of that point. This is an isobaric data path, not a fixed-temperature γ(x) curve.';
  }else if(kind==='area'){
    traces=[trace(valid.map(r=>r.x),valid.map(r=>r.ln[0]-r.ln[1]),'Inferred log ratio',c.teal,'solid','lines+markers')];yTitle='ln(γ₁/γ₂)';note='Partial measured interval only. No endpoint extrapolation, no excess-enthalpy correction, and no independent experimental pass/fail verdict.';
  }else{
    traces=[trace(predicted.map(r=>r.x),predicted.map(r=>r.modelLn[0]-r.ln[0]),'ln γ₁ residual',c.amber,'solid','markers'),trace(predicted.map(r=>r.x),predicted.map(r=>r.modelLn[1]-r.ln[1]),'ln γ₂ residual',c.amber,'dash','markers')];traces[1].marker.symbol='diamond-open';yTitle='Model − inferred ln γ';note='Unweighted log-activity residuals at measured T and x. A small residual does not prove thermodynamic consistency.';
  }
  await plot('case-plot',traces,xTitle,yTitle);
  $('case-legend').replaceChildren(...traces.map(t=>{const span=document.createElement('span'),i=document.createElement('i');i.style.borderColor=t.line.color;i.style.borderTopStyle=t.line.dash==='solid'?'solid':'dashed';if(t.mode==='markers'){i.className='legend-marker';if(t.marker.symbol!=='diamond-open'){i.style.transform='none';i.style.borderRadius='50%';}}span.append(i,document.createTextNode(t.name));return span;}));
  $('plot-note').textContent=note;
  $('diagnostic-summary').textContent=diagnostic.verdict;
  $('parameters').textContent=`α = ${parameters.alpha}; a₁₂ = ${fmt(parameters.a12,6)}, a₂₁ = ${fmt(parameters.a21,6)}; b₁₂ = ${fmt(parameters.b12,6)} K, b₂₁ = ${fmt(parameters.b21,6)} K.`;
  $('fit-status').textContent=fitResult?`Teaching fit trained on ${fitContext}: ${fitResult.points} pairs, RMSE = ${fmt(fitResult.rmse,5)}; converged.${fitResult.atBound?' A parameter reached its bound; interpret cautiously.':''} Changing pressure retains this fit for comparison.`:'Article parameters selected. Fit two parameters to compare a simpler temperature assumption.';
  $('reported').textContent=`Table 6: ${ds.pressureKPa} kPa, reported value ${ds.paperConsistency.value}, tolerance 10%, result “Passed”. This is the authors’ result, not a reproduction by this lab.`;
  const a=diagnostic.area;
  $('partial').textContent=`Usable interval x₁ = ${fmt(a.xmin)} to ${fmt(a.xmax)}. Signed partial area = ${fmt(a.signed,5)}; A₊ = ${fmt(a.positive,5)}, A₋ = ${fmt(a.negative,5)}. These omit the endpoint intervals and must not be compared directly with the article’s 10% criterion.`;
  $('model-check').textContent=`At fixed 350 K, max |x₁ d ln γ₁/dx₁ + x₂ d ln γ₂/dx₁| = ${check.maxGibbsDuhemResidual.toExponential(2)} (central differences at 199 interior points). Minimum sampled scaled liquid curvature = ${fmt(check.minSampledScaledCurvature,4)}. ${check.minSampledScaledCurvature>0?'Positive on this sampled grid; not a global stability proof.':'Nonpositive curvature detected: homogeneous bubble curves may be unstable; no LLE calculation is provided.'}`;
  const u=ds.averageExpandedUncertainty;$('uncertainty').textContent=`Average expanded uncertainties (coverage factor 2): U(P) = ${u.PkPa} kPa; U(T) = ${u.T} K; U(x) = ${u.x}; U(y) = ${u.y}. Composition averages exclude pure endpoints. These are not point-specific error bars.`;
  $('case-table').innerHTML='<table><thead><tr><th>T / K</th><th>x₁</th><th>y₁</th><th>ln γ₁</th><th>ln γ₂</th><th>Pair status</th></tr></thead><tbody>'+diagnostic.rows.map(r=>`<tr><td>${fmt(r.T,2)}</td><td>${fmt(r.x)}</td><td>${fmt(r.y)}</td><td>${fmt(r.ln?.[0])}</td><td>${fmt(r.ln?.[1])}</td><td>${r.reason??'Included'}</td></tr>`).join('')+'</tbody></table>';
  lastExport={version:engine.CASE_VERSION,source:data,selectedPressureKPa:ds.pressureKPa,parameters,fit:fitResult,fitContext,diagnostic,modelCheck:check,curve,predicted,rmse};synthetic();
 }catch(e){lastExport=null;$('case-error').hidden=false;$('case-error').textContent=e.message;$('case-results').hidden=true;$('download-case').disabled=true;}
}
async function fitNow(){
 $('fit-button').disabled=true;$('fit-status').textContent='Fitting…';
 try{
  const sets=$('fit-scope').value==='both'?data.datasets:[selected()],points=sets.flatMap(ds=>ds.rows.map(r=>engine.infer(r,data))).filter(r=>r.ln);
  fitResult=engine.fit(points);$('fit-option').disabled=false;fitContext=sets.map(s=>`${s.pressureKPa} kPa`).join(' + ');$('case-model').value='fit';await render();
 }catch(e){$('case-error').hidden=false;$('case-error').textContent=e.message;}
 finally{$('fit-button').disabled=false;}
}
function download(){if(!lastExport)return;const blob=new Blob([JSON.stringify({...lastExport,reflection:$('case-reflection').value},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`ipa-water-${selected().pressureKPa}kPa-study.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
try{
 const response=await fetch('assets/ipa-water.json');if(!response.ok)throw new Error('Could not load the study data.');data=await response.json();
 $('case-app').hidden=false;$('case-loading').hidden=true;
 for(const id of ['dataset','case-chart','case-model'])$(id).addEventListener('change',render);
 $('fit-button').addEventListener('click',fitNow);$('bias').addEventListener('input',synthetic);$('download-case').addEventListener('click',download);
 await render();
}catch(e){$('case-loading').textContent=e.message;}
