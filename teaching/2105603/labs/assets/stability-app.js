import * as e from './stability.js';
import {palette as c} from './palette.js';
const $=id=>document.getElementById(id),fmt=(v,n=4)=>v==null?'N/A':v!==0&&Math.abs(v)<1e-4?v.toExponential(2):Number(v).toFixed(n);
let result,curve,map=e.phaseMap();
const trace=(x,y,name,color,dash='solid',mode='lines')=>({x,y,name,mode,line:{color,width:2,dash},marker:{color,size:8},connectgaps:false});
async function chart(){
 if(!result)return;const {A,z,binodal:b}=result,kind=$('lle-chart').value;let traces=[],yTitle,note,xTitle='Mole fraction of component 1 · x₁',shapes=[];
 if(kind==='gibbs'){
  traces=[trace(curve.map(r=>r.x),curve.map(r=>r.ideal),'Ideal reference',c.teal),trace(curve.map(r=>r.x),curve.map(r=>r.g),'Homogeneous Margules liquid',c.amber),trace(curve.map(r=>r.x),curve.map(r=>r.hull),'Equilibrium convex envelope',c.graphite,'dash')];
  if(b){traces.push(trace([b.xAlpha,b.xBeta],[b.g,b.g],'Common tangent / binodal',c.graphite,'solid','lines+markers'));shapes=[b.spinodalAlpha,b.spinodalBeta].map(x=>({type:'line',xref:'x',yref:'paper',x0:x,x1:x,y0:0,y1:1,line:{color:c.graphite,width:1.5,dash:'dot'}}));}
  traces.push(trace([z],[result.homogeneousG],'Homogeneous feed',c.amber,'solid','markers'));traces.at(-1).marker.symbol='diamond';
  if(result.phase==='two liquids')traces.push(trace([z],[result.equilibriumG],'Equilibrated feed',c.graphite,'solid','markers'));
  yTitle='Mixing Gibbs energy / RT';note='The common tangent is a physical two-liquid mixture only between its contact points. Dotted vertical lines mark spinodals. The equilibrium envelope follows the original curve outside the miscibility gap.';
 }else if(kind==='map'){
  traces=[trace(map.map(r=>r.xAlpha),map.map(r=>r.A),'Binodal',c.amber),trace(map.map(r=>r.xBeta),map.map(r=>r.A),'Binodal (rich branch)',c.amber),trace(map.map(r=>r.spinodalAlpha),map.map(r=>r.A),'Spinodal',c.graphite,'dash'),trace(map.map(r=>r.spinodalBeta),map.map(r=>r.A),'Spinodal (rich branch)',c.graphite,'dash'),trace([.5],[2],'Critical point',c.graphite,'solid','markers'),trace([z],[A],'Current feed',c.teal,'solid','markers')];
  shapes=[{type:'line',x0:0,x1:1,y0:A,y1:A,line:{color:c.teal,width:1.5,dash:'dot'}}];yTitle='Interaction parameter A';note='Inside the binodal: two liquids at equilibrium. Between binodal and spinodal: metastable homogeneous feed. Inside the spinodal: unstable homogeneous feed. Vertical axis is A, not temperature.';
 }else{
  traces=[trace(curve.filter(r=>r.curvature!==null).map(r=>r.x),curve.filter(r=>r.curvature!==null).map(r=>r.curvature),'Homogeneous curvature',c.amber)];if(result.curvature!==null)traces.push(trace([z],[result.curvature],'Current feed',c.teal,'solid','markers'));
  yTitle='g″(x₁)';note='Negative curvature indicates local instability. Positive curvature alone cannot rule out metastability. Curvature diverges at pure endpoints; those endpoints are omitted. The vertical display is clipped to show the central region.';
 }
 await Plotly.react('lle-plot',traces,{margin:{l:65,r:16,t:18,b:55},font:{family:'Archivo, sans-serif',size:12,color:c.graphite},paper_bgcolor:'transparent',plot_bgcolor:'transparent',showlegend:false,xaxis:{title:{text:xTitle},range:[0,1],zeroline:false},yaxis:{title:{text:yTitle},zerolinecolor:c.graphite,...(kind==='curvature'?{range:[-9,20]}:kind==='map'?{range:[0,6.1]}:{})},shapes,hovermode:'closest'},{responsive:true,displayModeBar:false});
 $('lle-legend').replaceChildren(...traces.filter(t=>!t.name.includes('branch')).map(t=>{const span=document.createElement('span'),i=document.createElement('i');i.style.borderColor=t.line.color;i.style.borderTopStyle=t.line.dash==='solid'?'solid':'dashed';if(t.mode==='markers')i.className='legend-marker';span.append(i,document.createTextNode(t.name));return span;}));$('lle-chart-note').textContent=note;
}
function run(){
 try{
  for(const id of ['lle-A','lle-z'])if($(id).value.trim()==='')throw new Error('Enter both A and the feed composition.');
  const A=Number($('lle-A').value),z=Number($('lle-z').value);result=e.equilibrium(A,z);curve=e.gibbsCurve(A);
  $('lle-A-range').value=A;$('lle-z-range').value=z;$('lle-error').hidden=true;$('lle-results').hidden=false;$('lle-export').disabled=false;
  const r=result,b=r.binodal;$('lle-phase').textContent=r.phase;$('lle-state').textContent=r.state;$('lle-curvature').textContent=r.curvature===null?'Pure endpoint: curvature diverges':`g″(z₁) = ${fmt(r.curvature)}`;$('lle-beta').textContent=fmt(r.fractionBeta);$('lle-gain').textContent=fmt(r.gain,6);
  const explanation={stable:'The homogeneous feed is on the convex envelope. Its equilibrium state is one liquid at the feed composition.',metastable:'The homogeneous feed has positive curvature, but a finite split reaches a lower Gibbs energy on the common tangent. The equilibrium state is two liquids.',unstable:'The homogeneous feed has negative curvature. Small composition fluctuations lower Gibbs energy; the final bulk equilibrium is two liquids on the common tangent.',critical:'The two coexistence compositions merge at x₁ = 0.5. This is one critical liquid, not two distinct phases; a lever-rule fraction is not defined.','spinodal boundary':'The homogeneous feed has zero local curvature at the spinodal. The common tangent still gives a lower-energy two-liquid equilibrium.','binodal boundary':'The feed lies at a coexistence boundary. An infinitesimal amount of the conjugate liquid can appear; the present liquid remains at the feed composition.'};
  $('lle-interpretation').textContent=explanation[r.state];$('lle-alpha-x').textContent=fmt(b?.xAlpha,b&&b.xBeta-b.xAlpha<.001?8:4);$('lle-beta-x').textContent=fmt(b?.xBeta,b&&b.xBeta-b.xAlpha<.001?8:4);
  $('lle-composition-note').textContent=b?(r.phase==='two liquids'?'Both binodal compositions are present. Changing z₁ at fixed A changes the fractions, not these compositions.':'These are binodal boundary compositions at this A. Both are not present for the current feed.'):'No distinct coexistence compositions at A ≤ 2.';
  $('lle-lever').replaceChildren();if(r.phase==='two liquids'){for(const [name,fraction,color] of [['α',r.fractionAlpha,c.teal],['β',r.fractionBeta,c.amber]]){const span=document.createElement('span');span.style.width=`${100*fraction}%`;span.style.background=color;span.title=`${name}: ${fmt(fraction)}`;$('lle-lever').append(span);}}
  $('lle-fractions').textContent=r.phase==='two liquids'?`Lever rule: fᵅ = ${fmt(r.fractionAlpha)}, fᵝ = ${fmt(r.fractionBeta)}. α: component-1-poor; β: component-1-rich.`:`One liquid: x₁ = z₁ = ${fmt(z)}. No two-phase fraction is assigned.`;
  const check=(name,value)=>`<div class="check-row"><span>${name}</span><strong>${value}</strong></div>`;
  $('lle-checks').innerHTML=check('Component balance residual',r.balanceResidual.toExponential(2))+check('Chemical-potential equality between present phases',r.chemicalPotentialResidual===null?'N/A':r.chemicalPotentialResidual.toExponential(2))+check('Common-tangent residual (binodal construction)',b?b.tangentResidual.toExponential(2):'N/A')+check('Homogeneous g(z₁)',fmt(r.homogeneousG,6))+check('Equilibrium g(z₁)',fmt(r.equilibriumG,6))+'<p>Dimensionless chemical potentials relative to pure-liquid standards are ln x₁ + A(1−x₁)² and ln(1−x₁) + Ax₁². Their equality and the material balance independently check the two-liquid split. Stable single-liquid feeds do not have a second-phase equality to test.</p>';
  $('lle-table').innerHTML='<table><thead><tr><th>x₁</th><th>Homogeneous g</th><th>Convex envelope g</th><th>g″</th></tr></thead><tbody>'+curve.filter((_,i)=>i%10===0).map(v=>`<tr><td>${fmt(v.x)}</td><td>${fmt(v.g,6)}</td><td>${fmt(v.hull,6)}</td><td>${fmt(v.curvature)}</td></tr>`).join('')+'</tbody></table>';
  chart();
 }catch(err){result=null;curve=null;$('lle-error').textContent=err.message;$('lle-error').hidden=false;$('lle-results').hidden=true;$('lle-export').disabled=true;$('lle-checks').textContent='No valid calculation.';$('lle-table').replaceChildren();}
}
for(const key of ['A','z']){$(`lle-${key}-range`).addEventListener('input',()=>{$(`lle-${key}`).value=$(`lle-${key}-range`).value;run();});}
$('lle-run').addEventListener('click',run);$('lle-chart').addEventListener('change',chart);
$('lle-reset').addEventListener('click',()=>{$('lle-A').value=3;$('lle-z').value=.35;$('lle-preset').value='';run();});
$('lle-preset').addEventListener('change',()=>{const v={stable:[3,.02],meta:[3,.12],unstable:[3,.5],critical:[2,.5],ideal:[0,.5]}[$('lle-preset').value];if(v){$('lle-A').value=v[0];$('lle-z').value=v[1];run();}});
$('lle-export').addEventListener('click',()=>{if(!result)return;const data={version:e.STABILITY_VERSION,result,curve,phaseMap:map,prediction:$('lle-prediction').value,reflection:$('lle-reflection').value},url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='liquid-stability-study.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
run();
