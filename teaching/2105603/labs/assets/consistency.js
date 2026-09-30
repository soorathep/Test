/** Teaching variants of area, Herington, differential and Van Ness tests. */
import {nrtl,pressure,domain,infer,areas} from './case-study.js';
export const CONSISTENCY_VERSION='1.0.0';
const R=8.31446261815324;
const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
export function perturbation(x,amplitude,kind){
 if(kind==='clean')return 0;
 if(kind==='offset')return amplitude;
 if(kind==='cancel')return amplitude*Math.cos(2*Math.PI*x);
 if(kind==='local')return amplitude*Math.exp(-(((x-.35)/.035)**2));
 throw new Error('Unknown synthetic perturbation.');
}
export function syntheticSet(data,{path='isothermal',kind='clean',amplitude=.25,n=81}={}){
 if(!['isothermal','isobaric'].includes(path)||!Number.isInteger(n)||n<21||n>321||!Number.isFinite(amplitude)||Math.abs(amplitude)>.5)throw new RangeError('Invalid synthetic setting.');
 const rows=Array.from({length:n},(_,i)=>{
  const x=i/(n-1),f=perturbation(x,amplitude,kind);
  const state=T=>{const base=nrtl(x,T,data.nrtl),ln=[base.ln[0]+(1-x)*f,base.ln[1]-x*f],s=data.properties.map(c=>pressure(c,T)),a=x*Math.exp(ln[0])*s[0],b=(1-x)*Math.exp(ln[1])*s[1];return {x,T,PkPa:a+b,y:a/(a+b),ln};};
  let T=350;
  if(path==='isobaric'){
   let [lo,hi]=domain(data);if((state(lo).PkPa-60)*(state(hi).PkPa-60)>0)throw new RangeError('Synthetic bubble state outside property domain.');
   for(let j=0;j<60;j++){T=(lo+hi)/2;if(state(T).PkPa>60)hi=T;else lo=T;}
  }
  const row=state(T),h=.001;
  row.HE=-R*T*T*(nrtl(x,T+h,data.nrtl).gE-nrtl(x,T-h,data.nrtl).gE)/(2*h);
  row.f= row.ln[0]-row.ln[1];return row;
 });
 return {name:`Synthetic ${path}`,path,synthetic:true,rows,valid:rows,excluded:[],endpointsKnown:true,kind,amplitude,n,
   heatSource:'Synthetic H^E from the temperature derivative of the generating NRTL gE. The perturbations cancel in sum(x_i ln gamma_i), so this synthetic H^E is unchanged.'};
}
export function articleSet(data,P){
 const ds=data.datasets.find(s=>s.pressureKPa===P);if(!ds)throw new RangeError('Unknown article pressure.');
 const rows=ds.rows.map(r=>infer(r,data)),valid=rows.filter(r=>r.ln).sort((a,b)=>a.x-b.x).map(r=>({...r,f:r.ln[0]-r.ln[1]}));
 return {name:`Article · ${P} kPa`,path:'isobaric',synthetic:false,rows,valid,excluded:rows.filter(r=>!r.ln),endpointsKnown:false,paper:ds.paperConsistency};
}
function solve(A,b){
 const n=b.length,m=A.map((r,i)=>[...r,b[i]]);
 for(let j=0;j<n;j++){
  let k=j;for(let i=j+1;i<n;i++)if(Math.abs(m[i][j])>Math.abs(m[k][j]))k=i;
  if(Math.abs(m[k][j])<1e-12)throw new Error('Ill-conditioned polynomial fit.');
  [m[j],m[k]]=[m[k],m[j]];const v=m[j][j];for(let t=j;t<=n;t++)m[j][t]/=v;
  for(let i=0;i<n;i++)if(i!==j){const f=m[i][j];for(let t=j;t<=n;t++)m[i][t]-=f*m[j][t];}
 }
 return m.map(r=>r[n]);
}
export function areaAnalysis(set,extension='none'){
 if(!['none','linear','quadratic'].includes(extension))throw new RangeError('Unknown endpoint assumption.');
 let points=set.valid.map(r=>({x:r.x,f:r.f}));const partial=areas(points);
 if(!set.endpointsKnown&&extension==='linear'){
  const a=points[0],b=points[1],d=points.at(-2),e=points.at(-1);
  points=[{x:0,f:a.f-a.x*(b.f-a.f)/(b.x-a.x)},...points,{x:1,f:e.f+(1-e.x)*(e.f-d.f)/(e.x-d.x)}];
 }
 if(!set.endpointsKnown&&extension==='quadratic'){
  const design=points.map(r=>[1,2*r.x-1,(2*r.x-1)**2]);
  const coeff=solve([0,1,2].map(i=>[0,1,2].map(j=>design.reduce((s,r)=>s+r[i]*r[j],0))),[0,1,2].map(i=>design.reduce((s,r,k)=>s+r[i]*points[k].f,0)));
  points=Array.from({length:401},(_,i)=>{const x=i/400,u=2*x-1;return{x,f:coeff[0]+coeff[1]*u+coeff[2]*u*u};});
 }
 const area=areas(points),full=set.endpointsKnown||extension!=='none',temps=set.rows.map(r=>r.T),J=150*(Math.max(...temps)-Math.min(...temps))/Math.min(...temps);
 const conditional=!set.endpointsKnown&&full,eligible=full&&area.D!==null;
 return {area,partial,points,full,conditional,extension,J,DminusJ:area.D===null?null:area.D-J,
  redlichKister:set.path!=='isothermal'?{status:'not-applicable',reason:'Zero-area criterion requires an isothermal path (pressure/excess-volume effects neglected).'}:!eligible?{status:'not-assessed',reason:full?'Area normalization is undefined near ideality.':'Full composition range is missing.'}:{status:area.D<5?'meets-criterion':'outside-criterion',conditional,criterion:'D < 5%',value:area.D},
  herington:set.path!=='isobaric'?{status:'not-applicable',reason:'Use the isothermal area criterion for this path.'}:!eligible?{status:'not-assessed',reason:full?'Area normalization is undefined near ideality.':'Supply endpoint estimates to evaluate a full-range empirical area criterion.'}:{status:area.D-J<10?'meets-criterion':'outside-criterion',conditional,criterion:'D − J < 10; J = 150(Tmax−Tmin)/Tmin',value:area.D-J}};
}
/** Three-point Lagrange derivative at interior, nonuniform x coordinates. */
export function derivative(a,b,c,key){
 const x=a.x,y=b.x,z=c.x;
 if(!(x<y&&y<z))throw new RangeError('Strictly increasing compositions required.');
 return a[key]*(y-z)/((x-y)*(x-z))+b[key]*(2*y-x-z)/((y-x)*(y-z))+c[key]*(y-x)/((z-x)*(z-y));
}
export function differential(set,correctHeat=true){
 const rows=set.valid.map(r=>({...r,g:r.x*r.ln[0]+(1-r.x)*r.ln[1]}));
 const assessed=set.path==='isothermal'||((set.synthetic||set.heatKnown)&&correctHeat);
 const points=rows.slice(1,-1).map((r,i)=>{
  const a=rows[i],c=rows[i+2],slope=derivative(a,r,c,'g'),dTdx=derivative(a,r,c,'T');
  const heat=(set.path==='isobaric'&&(set.synthetic||set.heatKnown)&&correctHeat)?r.HE/(R*r.T*r.T)*dTdx:0;
  return {x:r.x,raw:slope-r.f,residual:slope-r.f+heat,heat,dTdx};
 });
 const score=100*mean(points.map(r=>Math.abs(r.residual)));
 return {points,score,assessed,status:assessed?(score<5?'meets-criterion':'outside-criterion'):'not-assessed',
  criterion:'100 × mean |d(gE/RT)/dx − ln(γ1/γ2) + H^E/(RT²) dT/dx| < 5 (teaching threshold)',
  reason:assessed?'Local finite differences, not the NIST Padé-based Kojima point-test implementation. Derivatives amplify noise and depend on spacing.':'Isobaric heat correction unavailable or disabled; the raw residual is not a consistency verdict.'};
}
export function nelder(fn,start,bounds){
 const clamp=v=>v.map((x,i)=>Math.max(bounds[i][0],Math.min(bounds[i][1],x))),make=v=>{v=clamp(v);return{v,f:fn(v)};},n=start.length;
 let s=[make(start),...start.map((_,i)=>make(start.map((v,j)=>v+(i===j?.3:0))))];
 for(let iter=0;iter<1600;iter++){
  s.sort((a,b)=>a.f-b.f);
  if(Math.max(...s.slice(1).map(a=>Math.hypot(...a.v.map((v,j)=>v-s[0].v[j]))))<1e-6)return {...s[0],iterations:iter,converged:true};
  const c=start.map((_,j)=>mean(s.slice(0,n).map(a=>a.v[j]))),r=make(c.map((v,j)=>2*v-s[n].v[j]));
  if(r.f<s[0].f){const e=make(c.map((v,j)=>v+2*(r.v[j]-v)));s[n]=e.f<r.f?e:r;}
  else if(r.f<s[n-1].f)s[n]=r;
  else{const outside=r.f<s[n].f,ref=outside?r:s[n],q=make(c.map((v,j)=>v+.5*(ref.v[j]-v)));if(q.f<(outside?r.f:s[n].f))s[n]=q;else s=[s[0],...s.slice(1).map(a=>make(a.v.map((v,j)=>(v+s[0].v[j])/2)))];}
 }
 s.sort((a,b)=>a.f-b.f);return {...s[0],iterations:1600,converged:false};
}
export function modelingTest(set,data){
 const rows=set.valid.filter(r=>r.x>0&&r.x<1),isobaric=set.path==='isobaric';
 const input=rows.map(r=>({...r,s:data.properties.map(c=>pressure(c,r.T))}));
 const bounds=isobaric?[[-3,8],[-3,8],[-40,40],[-40,40]]:[[-3,8],[-3,8]];
 const convert=v=>({alpha:.47,a12:v[0]-(v[2]??0),a21:v[1]-(v[3]??0),b12:350*(v[2]??0),b21:350*(v[3]??0)});
 const predict=(r,p)=>{const g=nrtl(r.x,r.T,p).gamma,a=r.x*g[0]*r.s[0],b=(1-r.x)*g[1]*r.s[1];return{P:a+b,y:a/(a+b)};};
 const fn=v=>{const p=convert(v);return mean(input.map(r=>{const q=predict(r,p);return (100*(q.P-r.PkPa)/r.PkPa)**2+(100*(q.y-r.y))**2;}));};
 const starts=[[0,0],[.5,2],[2,.5],[4,-.5],[-.5,4]].map(v=>isobaric?[...v,0,0]:v);
 const fits=starts.map(s=>nelder(fn,s,bounds)),eligible=fits.filter(f=>f.converged).sort((a,b)=>a.f-b.f);
 if(!eligible.length)throw new Error('Modeling fit did not converge; no verdict.');
 const best=eligible[0],p=convert(best.v),points=input.map(r=>{const q=predict(r,p);return{x:r.x,T:r.T,P:r.PkPa,y:r.y,Pcalc:q.P,ycalc:q.y,pressureResidual:100*(q.P-r.PkPa)/r.PkPa,yResidual:100*(q.y-r.y)};});
 const deltaP=mean(points.map(r=>Math.abs(r.pressureResidual))),deltaY=mean(points.map(r=>Math.abs(r.yResidual)));
 return {points,parameters:p,centeredParameters:best.v,objective:best.f,deltaP,deltaY,converged:true,starts:5,iterations:best.iterations,count:points.length,
  status:deltaP<1&&deltaY<1?'meets-criterion':'outside-criterion',criterion:'Mean absolute relative P error < 1% AND mean absolute y error < 0.01',
  atBound:best.v.some((v,i)=>Math.min(Math.abs(v-bounds[i][0]),Math.abs(v-bounds[i][1]))<1e-4),
  method:`Van Ness-type modeling capability: ${isobaric?'4 temperature-dependent':'2 constant'} NRTL parameters, alpha=.47 fixed; joint least squares of 100 ΔP/P and 100 Δy. Pure endpoints excluded. This is not the five-parameter NIST TDE implementation; failure can reflect the selected model or vapor-property approximation.`};
}
