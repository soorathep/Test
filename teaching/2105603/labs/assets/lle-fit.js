/** Isothermal binary LLE regression: fit chemical-potential equality, then verify stability. */
import * as s from './stability.js';
export const LLE_FIT_VERSION='1.1.0';
export const TRUTH=Object.freeze({model:'nrtl',tau12:3,tau21:2,alpha:.3});
const mean=a=>a.reduce((v,x)=>v+x,0)/a.length;
export function validateRows(rows){
 if(!Array.isArray(rows)||!rows.length)throw new RangeError('At least one coexistence pair is required.');
 for(const r of rows)if(![r.T,r.xAlpha,r.xBeta].every(Number.isFinite)||!(r.T>0&&r.xAlpha>0&&r.xBeta<1&&r.xAlpha<r.xBeta))throw new RangeError('Require T > 0 and 0 < xAlpha < xBeta < 1.');
 if(rows.some(r=>Math.abs(r.T-rows[0].T)>1e-8))throw new RangeError('Fit one temperature at a time; constant tau across temperatures is not assumed.');
}
export function synthetic(noise=0,seed=42){
 if(!Number.isFinite(noise)||noise<0||noise>.02||!Number.isInteger(seed)||seed<0||seed>4294967295)throw new RangeError('Noise must be 0–0.02 and seed an integer in 0–4294967295.');
 let state=seed>>>0;const rand=()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296;},b=s.coexistence(TRUTH);
 const rows=Array.from({length:8},()=>({T:298.15,xAlpha:b.xAlpha+noise*(2*rand()-1),xBeta:b.xBeta+noise*(2*rand()-1)}));validateRows(rows);
 return {name:'Synthetic isothermal NRTL replicates',kind:'synthetic',rows,truth:TRUTH,truthGap:b,noise,seed,pressureKPa:null,noiseDescription:'Independent uniform composition offsets in [-amplitude,+amplitude], 8 replicates, seeded LCG. No clipping or resampling.'};
}
export function experimental(data,T){const row=data.rows.find(r=>Math.abs(r.T-T)<1e-8);if(!row)throw new RangeError('Select a reported experimental temperature.');return {...data,rows:[{...row}],allRows:data.rows};}
export function residuals(rows,p){return rows.flatMap(r=>{const a=s.chemicalPotentials(r.xAlpha,p),b=s.chemicalPotentials(r.xBeta,p);return a.map((v,i)=>v-b[i]);});}
export function objective(rows,p){return mean(residuals(rows,p).map(v=>v*v));}
function optimize(rows,alpha,start,maxIterations){
 const clamp=v=>v.map(x=>Math.max(-2,Math.min(6,x))),make=v=>{v=clamp(v);return{v,f:objective(rows,{model:'nrtl',alpha,tau12:v[0],tau21:v[1]})};};
 const step=x=>x>5.7?-.3:.3;
 let simplex=[make(start),make([start[0]+step(start[0]),start[1]]),make([start[0],start[1]+step(start[1])])],converged=false,iteration=0,history=[];
 for(;iteration<maxIterations;iteration++){
  simplex.sort((a,b)=>a.f-b.f);history.push({iteration,objective:simplex[0].f,tau12:simplex[0].v[0],tau21:simplex[0].v[1]});
  if(Math.max(...simplex.slice(1).map(a=>Math.hypot(a.v[0]-simplex[0].v[0],a.v[1]-simplex[0].v[1])))<1e-8){converged=true;break;}
  const c=simplex[0].v.map((v,j)=>(v+simplex[1].v[j])/2),r=make(c.map((v,j)=>2*v-simplex[2].v[j]));
  if(r.f<simplex[0].f){const ex=make(c.map((v,j)=>v+2*(r.v[j]-v)));simplex[2]=ex.f<r.f?ex:r;}
  else if(r.f<simplex[1].f)simplex[2]=r;
  else{const outside=r.f<simplex[2].f,ref=outside?r:simplex[2],q=make(c.map((v,j)=>v+.5*(ref.v[j]-v)));if(q.f<(outside?r.f:simplex[2].f))simplex[2]=q;else simplex=[simplex[0],...simplex.slice(1).map(a=>make(a.v.map((v,j)=>(v+simplex[0].v[j])/2)))];}
 }
 simplex.sort((a,b)=>a.f-b.f);const best=simplex[0];
 return {start,parameters:{model:'nrtl',alpha,tau12:best.v[0],tau21:best.v[1]},objective:best.f,converged,iterations:iteration,atBound:best.v.some(v=>Math.min(Math.abs(v+2),Math.abs(v-6))<1e-5),history};
}
export function diagnose(rows,p){
 const xAlpha=mean(rows.map(r=>r.xAlpha)),xBeta=mean(rows.map(r=>r.xBeta)),observedTPD=[s.tpd(p,xAlpha),s.tpd(p,xBeta)];
 try{
  const gaps=s.coexistenceGaps(p),rank=gaps.map(b=>({b,mse:mean(rows.flatMap(r=>[(b.xAlpha-r.xAlpha)**2,(b.xBeta-r.xBeta)**2]))})).sort((a,b)=>a.mse-b.mse),b=rank[0]?.b??null;
  return {resolved:true,gaps,binodal:b,compositionRMSE:b?Math.sqrt(rank[0].mse):null,observedMean:{xAlpha,xBeta},observedTPD,predictedTPD:b?[s.tpd(p,b.xAlpha),s.tpd(p,b.xBeta)]:[],curve:s.gibbsCurve(p),message:b?'A globally supporting coexistence branch was found. Compare its compositions with the observations.':'This fit predicts no liquid split; equality residuals alone do not establish LLE.'};
 }catch(err){return{resolved:false,gaps:[],binodal:null,compositionRMSE:null,observedMean:{xAlpha,xBeta},observedTPD,predictedTPD:[],curve:[],message:`Stability calculation unresolved: ${err.message}`};}
}
export function sensitivity(rows,p){
 const h=1e-4,columns=['tau12','tau21'].map(key=>{const lo=Math.max(-2,p[key]-h),hi=Math.min(6,p[key]+h),a=residuals(rows,{...p,[key]:lo}),b=residuals(rows,{...p,[key]:hi});return b.map((v,i)=>(v-a[i])/(hi-lo));});
 const a=mean(columns[0].map(v=>v*v)),b=mean(columns[0].map((v,i)=>v*columns[1][i])),d=mean(columns[1].map(v=>v*v)),disc=Math.hypot(a-d,2*b),hi=(a+d+disc)/2,lo=Math.max(0,(a+d-disc)/2);
 return {singularValueRatio:lo>1e-16?Math.sqrt(hi/lo):null,method:'Finite-difference residual Jacobian, fixed alpha. Ratio of largest to smallest singular value; not a parameter confidence interval.'};
}
export function fit(rows,{alpha=.3,start=[1,1],multistart=true,maxIterations=500}={}){
 validateRows(rows);if(!Array.isArray(start)||start.length!==2)throw new RangeError('Two starting tau values are required.');s.parameters({model:'nrtl',alpha,tau12:start[0],tau21:start[1]});
 if(!Number.isInteger(maxIterations)||maxIterations<1||maxIterations>2000)throw new RangeError('Invalid iteration limit.');
 const starts=multistart?[start,[0,0],[2.5,1.5],[1.5,2.5],[5,5],[-1,5],[5,-1]]:[start];
 const runs=starts.map(v=>optimize(rows,alpha,v,maxIterations));
 const eligible=runs.filter(r=>r.converged),best=[...(eligible.length?eligible:runs)].sort((a,b)=>a.objective-b.objective)[0];
 for(const r of runs){const d=diagnose(rows,r.parameters);r.diagnostic={resolved:d.resolved,compositionRMSE:d.compositionRMSE,gaps:d.gaps.length,message:d.message};}
 const diagnostics=diagnose(rows,best.parameters);
 return {version:LLE_FIT_VERSION,T:rows[0].T,parameters:best.parameters,objective:best.objective,chemicalPotentialRMSE:Math.sqrt(best.objective),converged:best.converged,atBound:best.atBound,iterations:best.iterations,runs,diagnostics,sensitivity:sensitivity(rows,best.parameters),initial:{parameters:{model:'nrtl',alpha,tau12:start[0],tau21:start[1]},objective:objective(rows,{model:'nrtl',alpha,tau12:start[0],tau21:start[1]})},method:'Bounded Nelder–Mead; tau in [-2,6], fixed alpha. Unweighted mean squared dimensionless chemical-potential differences across the observed liquids. Lowest objective among converged starts is selected, before stability verification. A small simplex is numerical convergence, not a global parameter optimum or a physical-equilibrium guarantee.'};
}

/** Explicit single-temperature student input; replicates are retained without averaging. */
export function importRows(text,{names,source,temperatureUnit='K',pressureKPa}={}){
 if(typeof text!=='string'||text.length>100000)throw new Error('Paste at most 100 kB of data.');
 if(!Array.isArray(names)||names.length!==2||names.some(v=>typeof v!=='string'||!v.trim())||typeof source!=='string'||!source.trim())throw new Error('Name both components and provide the data source.');
 if(!['K','C'].includes(temperatureUnit)||!Number.isFinite(pressureKPa)||pressureKPa<=0)throw new Error('Specify temperature units and positive pressure / kPa.');
 const lines=text.trim().split(/\r?\n/).filter(v=>v.trim()),sep=lines[0]?.includes('\t')?'\t':',';
 if(lines[0]?.split(sep).map(v=>v.trim()).join(',')!=='T,xAlpha,xBeta')throw new Error('Required header: T,xAlpha,xBeta (CSV or TSV; mole fractions of component 1).');
 if(lines.length<2||lines.length>501)throw new Error('Supply 1–500 coexistence pairs.');
 const rows=lines.slice(1).map((line,i)=>{const a=line.split(sep).map(v=>v.trim());if(a.length!==3||a.some(v=>v===''||!Number.isFinite(Number(v))))throw new Error(`Invalid row ${i+2}: three finite numbers required.`);const [t,xAlpha,xBeta]=a.map(Number);return{T:t+(temperatureUnit==='C'?273.15:0),xAlpha,xBeta};});
 validateRows(rows);return{name:names.join(' + '),names:names.map(v=>v.trim()),source:source.trim(),kind:'imported',rows,pressureKPa,originalText:text,temperatureUnit,uncertainty:'User-supplied compositions. No uncertainties assumed. All replicates retained; unweighted fit. One temperature and pressure per dataset.'};
}
