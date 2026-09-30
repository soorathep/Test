import {VERSION, flash, bubbleT, dewT, diagram, rrValue, azeotropes, gamma, psat} from './thermo.js';
import {palette} from './palette.js';
const el = id => document.getElementById(id);
let catalog, state, result, curves, chartRows, fitTransfer=null, renderVersion=0;
const format = (v,n=4) => v===null || !Number.isFinite(v) ? 'Not present' : v.toFixed(n);
const labels={'liquid':'Liquid only','vapor':'Vapor only','two-phase':'Liquid + vapor','bubble-boundary':'Bubble boundary','dew-boundary':'Dew boundary','indeterminate':'Saturated · β undetermined'};
const defaults = system => ({system,model:'ideal',T:catalog.systems[system].defaultT,P:catalog.systems[system].defaultP/1000,z:.5,A:1,A12:1.5,A21:0.5,chart:'pxy',compare:true,tau12:.5,tau21:.5,alpha:.3,temperatureMode:'fixed',referenceT:catalog.systems[system].defaultT});
function writeControls(s) {
  el('system').value=s.system; el('model').value=s.model; el('chart-kind').value=s.chart; el('compare').checked=s.compare;
  const sys=catalog.systems[s.system];
  for(const id of ['T','P','z','A','A12','A21','tau12','tau21','alpha']) { el(id).value=s[id]; el(`${id}-range`).value=s[id]; }
  for (const id of ['T','T-range']) {el(id).min=sys.rangeK[0];el(id).max=sys.rangeK[1];el(id).value=s.T;}
  el('a-control').hidden=s.model!=='margules';el('two-a-control').hidden=s.model!=='margules2';
  el('nrtl-control').hidden=s.model!=='nrtl';el('temperatureMode').value=s.temperatureMode;el('referenceT').value=s.referenceT;
  el('system-note').textContent=sys.description;
  el('t-domain').textContent=`Valid for both components: ${sys.rangeK[0]}–${sys.rangeK[1]} K.`;
}
function readControls() {
  const s={system:el('system').value,model:el('model').value,chart:el('chart-kind').value,compare:el('compare').checked};
  s.temperatureMode=el('temperatureMode').value;s.referenceT=Number(el('referenceT').value);
  const active=new Set(['T','P','z',...(s.model==='margules'?['A']:s.model==='margules2'?['A12','A21']:s.model==='nrtl'?['tau12','tau21','alpha']:[])]);
  for(const id of ['T','P','z','A','A12','A21','tau12','tau21','alpha']) {
    if(el(id).value.trim()==='') {
      if(active.has(id)) throw new Error(`${id} is required.`);
      s[id]=defaults(s.system)[id];
    } else s[id]=Number(el(id).value);
  }
  return s;
}
function table(headers, rows) {
  const t=document.createElement('table'), head=document.createElement('thead'), body=document.createElement('tbody');
  const r=document.createElement('tr');
  for(const h of headers){const c=document.createElement('th');c.scope='col';c.textContent=h;r.append(c);} head.append(r);
  for(const row of rows){const tr=document.createElement('tr');for(const value of row){const td=document.createElement('td');td.textContent=value;tr.append(td);}body.append(tr);}
  t.append(head,body);return t;
}
function check(label,value) {const row=document.createElement('div');row.className='check-row';const a=document.createElement('span'),b=document.createElement('strong');a.textContent=label;b.textContent=value;row.append(a,b);return row;}
function showSources(sys) {
  const title=document.createElement('p');title.textContent=sys.description;
  const list=document.createElement('ul');
  for(const source of sys.sources){const li=document.createElement('li');if(source.url){const a=document.createElement('a');a.href=source.url;a.textContent=source.title;li.append(a);}else{li.textContent=source.title;}list.append(li);}
  el('sources').replaceChildren(title,list);
  el('version').textContent=`Engine ${VERSION} · Data ${catalog.version}. Local calculations; no input data is sent to a server.`;
}
function updateText(sys) {
  const f=result, c=sys.components[0].name;
  el('phase').textContent=labels[f.phase];el('beta').textContent=f.beta===null?'N/A':f.beta.toFixed(4);
  el('beta-note').textContent=f.beta===null?'Not fixed by T and P':`${(100*f.beta).toFixed(1)}% of the feed`;
  el('x').textContent=f.x===null?'N/A':f.x.toFixed(4);el('y').textContent=f.y===null?'N/A':f.y.toFixed(4);
  el('x-note').textContent=f.x===null?'No liquid phase':`${c} in liquid`;
  el('y-note').textContent=f.y===null?'No vapor phase':`${c} in vapor`;
  el('bubble').textContent=`${(f.bubble.P/1000).toFixed(3)} kPa`;el('dew').textContent=`${(f.dew.P/1000).toFixed(3)} kPa`;
  let sentence;
  if(f.phase==='liquid')sentence='The feed is entirely liquid. There is no bulk vapor composition to report. Lower the pressure toward the bubble boundary to form the first vapor.';
  else if(f.phase==='vapor')sentence='The feed is entirely vapor. There is no bulk liquid composition to report. Raise the pressure toward the dew boundary to form the first liquid.';
  else if(f.beta===null)sentence='Liquid and vapor have the same composition at this saturation state. Temperature, pressure, and overall composition cannot determine the phase amounts; an additional specification such as enthalpy is needed.';
  else sentence=`On a 1 mol feed basis, ${(1-f.beta).toFixed(4)} mol is liquid and ${f.beta.toFixed(4)} mol is vapor. ${c} is ${f.y>f.x?'enriched in the vapor':'enriched in the liquid'}. The feed lies ${f.phase==='two-phase'?'between':'at an end of'} the tie line: z₁ = (1 − β)x₁ + βy₁.`;
  el('interpretation').textContent=sentence;
  const azs=azeotropes(sys,state.T,f.A);
  el('azeotrope').textContent=azs.length?`Model azeotrope${azs.length>1?'s':''} at this T: ${azs.map(az=>`x₁ = y₁ = ${az.x.toFixed(4)}, P = ${(az.P/1000).toFixed(3)} kPa`).join('; ')}. These are model predictions, not experimental observations.`:'No isolated azeotrope in this model at the selected temperature.';
  el('checks').replaceChildren(
    check('Component balance |(1 − β)x₁ + βy₁ − z₁|',f.beta===null?'Undetermined β':f.balanceResidual.toExponential(2)),
    check('Equilibrium max |xᵢKᵢ − yᵢ|',f.equilibriumResidual===null?'Not applicable':f.equilibriumResidual.toExponential(2)),
    check('Phase compositions',f.beta===null?'Saturation state':'Normalized & bounded'),
    check('Correlation domain','Within stated T range'),
    check('Liquid model',f.model.name),
    check('Minimum scaled liquid curvature',f.convexity.minScaledCurvature.toFixed(5)+' > 0'),
    check('Activity coefficients at liquid x₁',f.x===null?'No liquid phase':gamma(f.x,f.A).map((g,i)=>`γ${i===0?'₁':'₂'} = ${g.toFixed(4)}`).join(', ')),
    check('Global binary tangent support',f.stability.verified?'Verified':'Unresolved'),check('Liquid / vapor tangent minima',f.stability.pure?'Pure-component saturation check':`${f.stability.liquidMinimum.toExponential(2)} / ${f.stability.vaporMinimum.toExponential(2)}`)
  );
  const hist=f.history.map(h=>['Liquid x₁',h.iteration,h.value.toFixed(10),h.residual.toExponential(3),h.gamma.map(v=>v.toFixed(5)).join(', '),h.K.map(v=>v.toFixed(5)).join(', ')]).concat(f.rrHistory.map(h=>['Vapor β',h.iteration,h.value.toFixed(10),h.residual.toExponential(3),'Fixed at converged x','Fixed at converged x']));
  el('iteration-summary').textContent=hist.length?`${f.history.length} composition iterations and ${f.rrHistory.length} Rachford–Rice iterations. Values are dimensionless; composition residual is Pbubble/P − 1.`:'No two-phase iteration is needed at this state. Absent-phase equilibrium residuals are not reported.';
  el('iterations').replaceChildren(table(['Solve','Iteration','Trial value','Residual','γ₁, γ₂','K₁, K₂'],hist));
  const temps=[],boundaryTrace=f.dew.history.map(h=>['Dew P: liquid x',h.iteration,h.value.toFixed(8),h.residual.toExponential(3)]);f.boundaryCalculations={bubbleP:f.bubble,dewP:f.dew};
  for(const [label,fn] of [['Bubble',bubbleT],['Dew',dewT]]){
    try {const q=fn(sys,f.P,state.z,f.A);f.boundaryCalculations[label+'T']=q;temps.push(`${label}: ${q.T.toFixed(3)} K`);boundaryTrace.push(...q.history.map(h=>[label+' T',h.iteration,h.value.toFixed(8),h.residual.toExponential(3)]));}
    catch(e){if(e.code==='FIXED_T')temps.push(`${label}: disabled in fixed-temperature mode`);else if(e instanceof RangeError && e.message.startsWith('No root'))temps.push(`${label}: outside the joint correlation range`);else throw e;}
  }
  el('boundary-temperatures').textContent=temps.join(' · ');el('boundary-summary').textContent=`Bubble P is a direct sum of xᵢγᵢPᵢsat = ${f.bubble.P.toFixed(3)} Pa. Dew P solves ycalc − yspecified = 0 on x∈[0,1]. Temperature roots use Pbubble/P − 1 or Pdew/P − 1. All traces are exported.`;el('boundary-trace').replaceChildren(table(['Solve','Iteration','Trial x or T / K','Residual'],boundaryTrace));
}
function line(x,y,name,color,dash='solid') {return {x,y,name,type:'scatter',mode:'lines',line:{color,width:2.2,dash},connectgaps:false,hovertemplate:'%{x:.4f}, %{y:.4f}<extra>%{fullData.name}</extra>'};}
async function plot(sys,version) {
  const kind=state.chart, A=result.A, nonideal=result.model.nonideal, selected=diagram(sys,state.T,result.P,A,kind), ideal=!nonideal?selected:diagram(sys,state.T,result.P,0,kind);
  curves={selected,ideal};chartRows=[];const traces=[], teal=palette.teal, amber=palette.amber, graphite=palette.graphite;
  let xlabel='Mole fraction of component 1',ylabel,caption;
  const axis = key => ({title:{text:key,font:{size:12}},zeroline:false,gridcolor:palette.mist,gridwidth:.5,linecolor:graphite,tickfont:{size:11},showline:true,ticks:'outside',automargin:true});
  if(kind==='rr') {
    el('chart-title').textContent='A root fixes the phase amount.';
    xlabel='Vapor fraction β';ylabel='Rachford–Rice F(β)';
    if(result.K){
      chartRows=Array.from({length:101},(_,i)=>({beta:i/100,F:rrValue(i/100,state.z,result.K)}));
      traces.push(line(chartRows.map(p=>p.beta),chartRows.map(p=>p.F),'Converged K values',!nonideal?teal:amber));
      traces.push({x:[result.beta],y:[0],name:'Flash root',mode:'markers',type:'scatter',marker:{color:graphite,size:9,symbol:'diamond'}});
      caption='K values are evaluated at the converged liquid composition. This curve verifies the final split; it does not replace the composition-dependent equilibrium calculation.';
    }else caption='Rachford–Rice is shown only when distinct liquid and vapor equilibrium compositions have been determined. No two-phase root is fabricated for this state.';
  } else {
    const sets=state.compare&&nonideal?[['Ideal reference',ideal,teal],[result.model.name,selected,amber]]:[[result.model.name,selected,!nonideal?teal:amber]];
    if(kind==='pxy'||kind==='txy'){
      const ordinate=kind==='pxy'?'P':'T',scale=kind==='pxy'?1000:1;
      ylabel=kind==='pxy'?'Pressure (kPa)':'Temperature (K)';
      el('chart-title').textContent=kind==='pxy'?'Pressure reveals the split.':'Temperature moves the boundary.';
      for(const [name,data,color] of sets){traces.push(line(data.map(p=>p.x),data.map(p=>p[ordinate]===null?null:p[ordinate]/scale),`${name} · bubble`,color));traces.push(line(data.map(p=>p.y),data.map(p=>p[ordinate]===null?null:p[ordinate]/scale),`${name} · dew`,color,'dash'));}
      const level=kind==='pxy'?state.P:state.T;
      if(result.x!==null&&result.y!==null)traces.push({x:[result.x,result.y],y:[level,level],name:'Current tie line',type:'scatter',mode:'lines+markers',line:{color:graphite,width:2,dash:'dot'},marker:{color:graphite,size:7,symbol:'circle'}});
      traces.push({x:[state.z],y:[level],name:'Feed (z₁)',type:'scatter',mode:'markers',marker:{color:graphite,size:10,symbol:'diamond-open',line:{width:2}}});
      caption=kind==='pxy'?`At ${state.T.toFixed(2)} K. Solid = bubble line (x₁); dashed = dew line (y₁). Diamond = feed at the flash pressure.`:`At ${state.P.toFixed(2)} kPa. Solid = bubble line; dashed = dew line. Only temperatures inside ${sys.rangeK.join('–')} K are calculated.`;
      if(kind==='txy'&&selected.some(p=>p.T===null))caption+=' Gaps are outside the correlation range, not missing phases.';
    }else if(kind==='gamma'){
      el('chart-title').textContent='See the asymmetry in activity.';xlabel='Liquid mole fraction x₁';ylabel='Activity coefficient γᵢ';
      if(state.compare&&nonideal)traces.push(line([0,1],[1,1],'Ideal γ₁ = γ₂ = 1',teal));
      const color=nonideal?amber:teal;
      traces.push(line(selected.map(p=>p.x),selected.map(p=>p.gamma[0]),'γ₁ · component 1',color));
      traces.push(line(selected.map(p=>p.x),selected.map(p=>p.gamma[1]),'γ₂ · component 2',color,'dash'));
      caption=`${result.model.name}: A₁₂ = ${result.model.parameters.A12}, A₂₁ = ${result.model.parameters.A21}. ln γ₁ at infinite dilution = A₁₂; ln γ₂ at infinite dilution = A₂₁. Pure-component activity coefficients are one.`;
    }else{
      el('chart-title').textContent='Compare the two compositions.';xlabel='Liquid mole fraction x₁';ylabel='Vapor mole fraction y₁';
      for(const [name,data,color] of sets)traces.push(line(data.map(p=>p.x),data.map(p=>p.y),name,color));
      traces.push(line([0,1],[0,1],'y₁ = x₁',graphite,'dot'));
      if(result.x!==null&&result.y!==null)traces.push({x:[result.x],y:[result.y],name:'Current equilibrium',mode:'markers',type:'scatter',marker:{color:graphite,size:9}});
      caption=`Isothermal equilibrium at ${state.T.toFixed(2)} K; pressure varies along the curve. A crossing of y₁ = x₁ inside (0,1) is an azeotrope of this model.`;
    }
    chartRows=selected.map(p=>({x1:p.x,y1:p.y,T_K:p.T,P_Pa:p.P,gamma1:p.gamma?.[0]??null,gamma2:p.gamma?.[1]??null}));
  }
  el('compare').disabled=kind==='rr'||!nonideal;
  const layout={autosize:true,height:window.innerWidth<760?330:360,margin:{l:55,r:12,t:10,b:55},paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{family:'Archivo, sans-serif',color:graphite,size:11},xaxis:{...axis(xlabel),range:[0,1]},yaxis:axis(ylabel),legend:{orientation:'h',y:-.24,x:0,font:{size:10},itemwidth:30},hovermode:'closest',showlegend:false};
  if(kind==='xy')layout.yaxis.range=[0,1];
  if(kind==='rr')layout.shapes=[{type:'line',x0:0,x1:1,y0:0,y1:0,line:{color:graphite,width:1.5,dash:'dot'}}];
  if(kind==='rr'&&!result.K)layout.annotations=[{xref:'paper',yref:'paper',x:.5,y:.5,showarrow:false,text:'No distinct two-phase split<br>at these conditions.',font:{color:graphite,size:14}}];
  el('chart-legend').replaceChildren(...traces.map(trace=>{const item=document.createElement('span'),mark=document.createElement('i');mark.style.borderColor=trace.line?.color||trace.marker?.color||graphite;mark.style.borderTopStyle=trace.line?.dash==='dash'?'dashed':trace.line?.dash==='dot'?'dotted':'solid';if(trace.mode==='markers')mark.className='legend-marker';item.append(mark,document.createTextNode(trace.name));return item;}));
  await Plotly.react(el('chart'),traces,layout,{responsive:true,displayModeBar:false,scrollZoom:false});
  if(version!==renderVersion)return;
  el('chart-note').textContent=caption;
  const headers=chartRows.length?Object.keys(chartRows[0]):['No curve at this state'];
  el('curve-table').replaceChildren(table(headers,chartRows.filter((_,i)=>i%5===0).map(p=>Object.values(p).map(v=>v===null?'Outside range':format(v,5)))));
}
function enableExports(enabled){for(const id of ['export-json','export-csv','share'])el(id).disabled=!enabled;}
async function calculate(){
  const version=++renderVersion;enableExports(false);
  try {
    state=readControls();if(fitTransfer){const sys=catalog.systems['fit-transfer'];for(const [i,id] of ['fit-p1','fit-p2'].entries()){if(el(id).value.trim()===''||!(Number(el(id).value)>0))throw new Error('Enter both pure-component saturation pressures at the fit temperature before calculating.');sys.components[i].pressurePa=1000*Number(el(id).value);}state.fitP1=Number(el('fit-p1').value);state.fitP2=Number(el('fit-p2').value);state.fitKind=fitTransfer.kind;}el('stability-route').hidden=true;el('export-status').textContent='';const sys=catalog.systems[state.system];
    result=flash(sys,state.T,state.P*1000,state.z,state.model==='nrtl'?{model:'nrtl',tau12:state.tau12,tau21:state.tau21,alpha:state.alpha,temperatureMode:state.temperatureMode,referenceT:state.referenceT}:state.model==='ideal'?0:state.model==='margules2'?{A12:state.A12,A21:state.A21}:state.A);
    if(state.chart==='txy'&&(fitTransfer||(state.model==='nrtl'&&state.temperatureMode==='fixed'))){state.chart='pxy';el('chart-kind').value='pxy';el('export-status').textContent='T–x–y is unavailable with fixed-temperature parameters. Showing P–x–y.';}el('error').hidden=true;el('result-content').hidden=false;
    updateText(sys);showSources(sys);await plot(sys,version);
    if(version===renderVersion)enableExports(true);
  }catch(error){
    if(version!==renderVersion)return;
    if(error.code==='LIQUID_STABILITY'&&state.model!=='nrtl'){el('stability-route').hidden=false;el('route-lle').href='stability.html';el('route-vlle').href='vlle.html';el('route-vlle').hidden=false;el('route-note').textContent='Choose the same Margules parameters in the stability lab. Parameters are not transferred by these links.';}
    if(error.code==='LIQUID_STABILITY'&&state.model==='nrtl'){el('stability-route').hidden=false;const q=new URLSearchParams({model:'nrtl',tau12:state.tau12,tau21:state.tau21,alpha:state.alpha,z:state.z});el('route-lle').href=`stability.html?${q}#lle-experiment`;const sat=catalog.systems[state.system].components.map(c=>psat(c,state.T)/1000);const supported=sat.every(v=>v>=10&&v<=200);el('route-vlle').hidden=!supported;if(supported){q.set('p1',sat[0]);q.set('p2',sat[1]);q.set('P',state.P);q.set('T',state.T);q.set('source','lab01');el('route-vlle').href=`vlle.html?${q}#vl-experiment`;}el('route-note').textContent=supported?'Lab 06 receives these parameters and saturation pressures at the current T. It treats them as a fixed-temperature model study.':'Lab 06 accepts saturation pressures from 10 to 200 kPa. This state is outside that teaching range; use Lab 04 to inspect liquid stability.';}
    result=null;curves=null;chartRows=[];el('error').textContent=error.message;el('error').hidden=false;el('result-content').hidden=true;
    for(const id of ['checks','iteration-summary','iterations','boundary-temperatures','curve-table','boundary-trace','boundary-summary'])el(id).replaceChildren();
    el('export-status').textContent='Correct the inputs and calculate again before exporting.';
  }
}
function save(name,content,type){const u=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}
function snapshot(){return {schema:'skh-thermo-experiment/1',engineVersion:VERSION,dataVersion:catalog.version,inputs:state,result,curves,chartRows,propertyRecord:catalog.systems[state.system],prediction:el('prediction').value,reflection:el('reflection').value};}
async function start(){
  const response=await fetch('assets/systems.json');if(!response.ok)throw new Error('Property records could not be loaded. Reload the page.');catalog=await response.json();
  for(const [id,sys] of Object.entries(catalog.systems)){const o=document.createElement('option');o.value=id;o.textContent=sys.label;el('system').append(o);}
  const params=new URLSearchParams(location.search);let system=params.get('system')||'synthetic';
  if(params.get('source')==='lab05'||system==='fit-transfer'){
   const T=Number(params.get('referenceT')),kind=params.get('fitKind')==='experimental'?'experimental':'synthetic';if(!(T>0&&T<2000))throw new Error('Invalid fit temperature.');fitTransfer={T,kind};
   const names=kind==='experimental'?['Cyclohexane','Methanol']:['Hypothetical component 1','Hypothetical component 2'];
   catalog.systems['fit-transfer']={label:'Transferred LLE fit · fixed T',description:`${names.join(' / ')}; LLE fit at ${T} K. Vapor pressures must be supplied at this temperature.`,rangeK:[T,T],defaultT:T,defaultP:95000,components:names.map(name=>({name,equation:'fixed',rangeK:[T,T],pressurePa:null})),sources:[{title:'Parameters transferred from Lab 05; user-supplied saturation pressures',url:null}]};
   const o=new Option('Transferred LLE fit · fixed T','fit-transfer');el('system').append(o);system='fit-transfer';el('fit-controls').hidden=false;el('fit-note').textContent=catalog.systems[system].description;el('system').disabled=true;el('temperatureMode').disabled=true;el('referenceT').readOnly=true;for(const id of ['T','T-range'])el(id).disabled=true;
   for(const [id,key] of [['fit-p1','fitP1'],['fit-p2','fitP2']])if(params.has(key))el(id).value=params.get(key);
  }
  if(!catalog.systems[system])throw new Error('The link names an unknown system. Remove the query string to reset.');
  const initial=defaults(system);
  for(const id of ['T','P','z','A','A12','A21','tau12','tau21','alpha'])if(params.has(id))initial[id]=Number(params.get(id));
  for(const id of ['referenceT'])if(params.has(id))initial[id]=Number(params.get(id));if(params.has('temperatureMode'))initial.temperatureMode=params.get('temperatureMode');if(fitTransfer){initial.temperatureMode='fixed';initial.referenceT=fitTransfer.T;}
  if(params.has('model')){if(!['ideal','margules','margules2','nrtl'].includes(params.get('model')))throw new Error('Unknown model in link.');initial.model=params.get('model');}
  if(params.has('chart')){if(!['pxy','txy','xy','rr','gamma'].includes(params.get('chart')))throw new Error('Unknown diagram in link.');initial.chart=params.get('chart');}
  if(params.has('compare'))initial.compare=params.get('compare')!=='0';
  writeControls(initial);el('loading').hidden=true;el('app').hidden=false;
  el('run').addEventListener('click',calculate);
  for(const id of ['T','P','z','A','A12','A21','tau12','tau21','alpha']){
    el(`${id}-range`).addEventListener('input',()=>{el(id).value=el(`${id}-range`).value;calculate();});
    el(id).addEventListener('input',()=>{++renderVersion;enableExports(false);el('stability-route').hidden=true;el('phase').textContent='Inputs changed';el('result-content').hidden=true;el('export-status').textContent='Inputs changed. Calculate to update results.';for(const target of ['checks','iterations','iteration-summary','boundary-temperatures','curve-table'])el(target).replaceChildren();});
    el(id).addEventListener('change',()=>{el(`${id}-range`).value=el(id).value;calculate();});
    el(id).addEventListener('keydown',e=>{if(e.key==='Enter')calculate();});
  }
  el('model').addEventListener('change',()=>{el('a-control').hidden=el('model').value!=='margules';el('two-a-control').hidden=el('model').value!=='margules2';el('nrtl-control').hidden=el('model').value!=='nrtl';calculate();});
  for(const id of ['referenceT','temperatureMode','fit-p1','fit-p2'])el(id).addEventListener('input',()=>{enableExports(false);el('result-content').hidden=true;el('stability-route').hidden=true;for(const target of ['checks','iterations','boundary-trace','boundary-summary','boundary-temperatures'])el(target).replaceChildren();});
  for(const id of ['chart-kind','compare'])el(id).addEventListener('change',calculate);
  el('system').addEventListener('change',()=>{writeControls(defaults(el('system').value));calculate();});
  el('reset').addEventListener('click',()=>{writeControls(defaults(el('system').value));el('prediction').value='';calculate();});
  el('export-json').addEventListener('click',()=>{save('thermodynamics-experiment.json',JSON.stringify(snapshot(),null,2),'application/json');el('export-status').textContent='Exported inputs, results, curves, sources, prediction, and reflection.';});
  el('export-csv').addEventListener('click',()=>{if(!chartRows.length){el('export-status').textContent='No curve to export for this state.';return;}const keys=Object.keys(chartRows[0]);save(`thermodynamics-${state.chart}.csv`,[keys.join(','),...chartRows.map(p=>keys.map(k=>p[k]??'').join(','))].join('\n'),'text/csv');el('export-status').textContent='Exported selected-model curve. JSON includes the reference curve and full context.';});
  el('share').addEventListener('click',async()=>{const url=new URL(location.href);url.search='';url.searchParams.set('module','vle');for(const [k,v] of Object.entries(state))url.searchParams.set(k,k==='compare'?(v?'1':'0'):String(v));try{await navigator.clipboard.writeText(url.href);el('export-status').textContent='Link copied. Your prediction and reflection are not included.';}catch{el('export-status').textContent=url.href;}});
  await calculate();
}
start().catch(error=>{el('loading').textContent=`Unable to start: ${error.message}`;el('loading').className='error';});
