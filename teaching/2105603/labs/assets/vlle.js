/** Binary, isothermal Margules / NRTL liquids + ideal vapor on a shared Gibbs reference. */
import * as liquid from './stability.js';
import {nrtl} from './case-study.js';
export const VLLE_VERSION='1.1.0';
const ENERGY_TOL=1e-9,COMPOSITION_TOL=1e-10;
export function validate(A,psat,P=100,z=.5){
 liquid.parameters(A);
 if(!Array.isArray(psat)||psat.length!==2||!psat.every(p=>Number.isFinite(p)&&p>=10&&p<=200))throw new RangeError('Both synthetic saturation pressures must be between 10 and 200 kPa.');
 if(!Number.isFinite(P)||P<1||P>500)throw new RangeError('Pressure must be between 1 and 500 kPa.');
 if(!Number.isFinite(z)||z<0||z>1)throw new RangeError('Feed composition must be between 0 and 1.');
}
function root(fn,lo,hi){let a=fn(lo),b=fn(hi);if(a===0)return lo;if(b===0)return hi;if(a*b>0)throw new Error('Unbracketed phase-equilibrium root.');for(let i=0;i<100;i++){const m=(lo+hi)/2,f=fn(m);if(f===0||hi-lo<1e-14)return m;if(a*f<=0)hi=m;else{lo=m;a=f;}}throw new Error('Phase-equilibrium root did not converge.');}
const unique=xs=>xs.sort((a,b)=>a-b).filter((x,i,a)=>i===0||x-a[i-1]>1e-12);
export function vaporG(y,P,psat){return liquid.gibbs(y,0)+y*Math.log(P/psat[0])+(1-y)*Math.log(P/psat[1]);}
export function vaporMu(y,P,psat){return[Math.log(y*P/psat[0]),Math.log((1-y)*P/psat[1])];}
export function bubble(x,A,psat){const mu=liquid.chemicalPotentials(x,A),partial=mu.map((v,i)=>Math.exp(v)*psat[i]),P=partial[0]+partial[1];return{x,y:partial[0]/P,P,mu,partial};}
/** Minimize each phase's distance from the line mu2+(mu1-mu2)*x. */
export function support(A,psat,P,mu){
 const slope=mu[0]-mu[1],intercept=mu[1],cuts=[0,...liquid.spinodals(A).roots,1],candidates=[0,1];
 for(let i=1;i<cuts.length;i++)if((liquid.slope(cuts[i-1],A)-slope)*(liquid.slope(cuts[i],A)-slope)<=0)candidates.push(root(x=>liquid.slope(x,A)-slope,cuts[i-1],cuts[i]));
 const distance=x=>liquid.gibbs(x,A)-intercept-slope*x,x=candidates.reduce((a,b)=>distance(a)<distance(b)?a:b);
 const partial=mu.map((v,i)=>Math.exp(v)*psat[i]),Q=partial[0]+partial[1];
 return{liquidMinimum:distance(x),liquidAt:x,vaporMinimum:Math.log(P/Q),vaporAt:partial[0]/Q,slope,intercept,tolerance:ENERGY_TOL,verified:distance(x)>=-ENERGY_TOL&&Math.log(P/Q)>=-ENERGY_TOL};
}
export function triplePoints(A,psat){
 validate(A,psat);return liquid.coexistenceGaps(A).map(b=>{const a=bubble(b.xAlpha,A,psat),beta=bubble(b.xBeta,A,psat),mu=a.mu,check=support(A,psat,a.P,mu);return{...b,P:a.P,y:a.y,mu,liquidPressureResidual:Math.abs(a.P-beta.P)/a.P,support:check};});
}
function quadratic(a,b,c){if(Math.abs(a)<1e-14)return Math.abs(b)<1e-14?[]:[-c/b];const d=b*b-4*a*c;if(d<0)return[];const q=-.5*(b+(b>=0?1:-1)*Math.sqrt(d));return q===0?[-b/(2*a)]:[q/a,c/q];}
export function azeotropes(A,psat){
 if(A?.model==='nrtl'){
  liquid.parameters(A);
  // d(ln gamma1 - ln gamma2)/dx = gE''. Positive denominators let
  // a/Du^3 + b/Dv^3 = 0 reduce exactly to a linear cube-root equation.
  const u=Math.exp(-A.alpha*A.tau21),v=Math.exp(-A.alpha*A.tau12),a=Math.cbrt(A.tau21*u*u),b=Math.cbrt(A.tau12*v*v);
  const denominator=a*(v-1)+b*(1-u),stationary=denominator===0?NaN:-(a+b*u)/denominator;
  const cuts=[0,...(stationary>0&&stationary<1?[stationary]:[]),1];
  const f=x=>{const q=nrtl(x,350,{a12:A.tau12,a21:A.tau21,b12:0,b21:0,alpha:A.alpha});return q.ln[0]-q.ln[1]+Math.log(psat[0]/psat[1]);};
  const roots=cuts.filter(x=>x>0&&x<1&&Math.abs(f(x))<1e-12);
  for(let i=1;i<cuts.length;i++)if(f(cuts[i-1])*f(cuts[i])<0)roots.push(root(f,cuts[i-1],cuts[i]));
  return unique(roots);
 }
 const {A12:a,A21:b}=liquid.parameters(A);return unique(quadratic(3*(a-b),2*(b-2*a),a+Math.log(psat[0]/psat[1])).filter(x=>x>0&&x<1));}
function phase(kind,x,A,P,psat,label){return{kind,label,x,g:kind==='vapor'?vaporG(x,P,psat):liquid.gibbs(x,A)};}
function vleCandidates(A,psat,P){
 const cuts=unique([0,...liquid.spinodals(A).roots,...azeotropes(A,psat),1]),f=x=>bubble(x,A,psat).P-P,roots=[];
 for(const x of cuts)if(Math.abs(f(x))<=1e-11*Math.max(P,1))roots.push(x);
 for(let i=1;i<cuts.length;i++)if(f(cuts[i-1])*f(cuts[i])<0)roots.push(root(f,cuts[i-1],cuts[i]));
 return unique(roots).filter(x=>x>0&&x<1).map(x=>{
  const b=bubble(x,A,psat),check=support(A,psat,P,b.mu);
  return{type:'VLE',phases:[phase('liquid',x,A,P,psat,'L'),phase('vapor',b.y,A,P,psat,'V')],support:check};
 }).filter(r=>r.support.verified);
}
/** All vertices of the nonnegative mole-fraction solutions to sum(f)=1, sum(f*x)=z. */
export function fractionFamily(phases,z){
 const vertices=[],push=f=>{if(!vertices.some(v=>v.every((a,i)=>Math.abs(a-f[i])<1e-9)))vertices.push(f);};
 phases.forEach((p,i)=>{if(Math.abs(p.x-z)<COMPOSITION_TOL){const f=phases.map(()=>0);f[i]=1;push(f);}});
 for(let i=0;i<phases.length;i++)for(let j=i+1;j<phases.length;j++){
  const dx=phases[j].x-phases[i].x;if(Math.abs(dx)<1e-12)continue;const b=(z-phases[i].x)/dx;
  if(b>=-COMPOSITION_TOL&&b<=1+COMPOSITION_TOL){const f=phases.map(()=>0);f[i]=1-Math.max(0,Math.min(1,b));f[j]=1-f[i];push(f);}
 }
 const vi=phases.findIndex(p=>p.kind==='vapor');vertices.sort((a,b)=>(vi<0?0:a[vi]-b[vi]));
 return {vertices,indeterminate:vertices.length>1,vaporMin:vertices.length?Math.min(...vertices.map(v=>vi<0?0:v[vi])):null,vaporMax:vertices.length?Math.max(...vertices.map(v=>vi<0?0:v[vi])):null};
}
function candidates(A,psat,P,z){
 const triples=triplePoints(A,psat),list=[];
 for(const t of triples){
  const phases=[phase('liquid',t.xAlpha,A,P,psat,'Lα'),phase('liquid',t.xBeta,A,P,psat,'Lβ')],check=support(A,psat,P,t.mu);
  if(Math.abs(Math.log(P/t.P))<1e-10)list.push({type:'VLLE',phases:[...phases,phase('vapor',t.y,A,P,psat,'V')],support:check});
  else if(check.verified)list.push({type:'LLE',phases,support:check});
 }
 const p=liquid.parameters(A);
 if((p.model==='nrtl'?p.tau12===0&&p.tau21===0:p.A12===0&&p.A21===0)&&Math.abs(Math.log(psat[0]/psat[1]))<1e-12&&Math.abs(Math.log(P/psat[0]))<1e-10){
  list.push({type:'Equal-volatility saturation',phases:[phase('liquid',z,A,P,psat,'L'),phase('vapor',z,A,P,psat,'V')],support:z>0&&z<1?support(A,psat,P,vaporMu(z,P,psat)):null});
 }else list.push(...vleCandidates(A,psat,P));
 for(const kind of ['liquid','vapor']){const mu=kind==='liquid'?liquid.chemicalPotentials(z,A):vaporMu(z,P,psat);list.push({type:kind==='liquid'?'Liquid':'Vapor',phases:[phase(kind,z,A,P,psat,kind==='liquid'?'L':'V')],support:z>0&&z<1?support(A,psat,P,mu):null});}
 if((z===0||z===1)&&Math.abs(Math.log(P/psat[z===1?0:1]))<1e-10)list.push({type:'Pure-component saturation',phases:[phase('liquid',z,A,P,psat,'L'),phase('vapor',z,A,P,psat,'V')],support:null});
 return{list,triples};
}
export function equilibrium(A,psat,P,z,choice=.5){
 validate(A,psat,P,z);if(!Number.isFinite(choice)||choice<0||choice>1)throw new RangeError('Fraction-family choice must be between 0 and 1.');
 const {list,triples}=candidates(A,psat,P,z),possible=[];
 for(const item of list){const family=fractionFamily(item.phases,z);if(!family.vertices.length)continue;const g=family.vertices[0].reduce((sum,f,i)=>sum+f*item.phases[i].g,0);possible.push({...item,family,g});}
 possible.sort((a,b)=>Math.abs(a.g-b.g)<1e-10?b.phases.length-a.phases.length:a.g-b.g);const best=possible[0],v=best.family.vertices;
 const fractions=v[0].map((f,i)=>(1-choice)*f+choice*v.at(-1)[i]);
 const sums={total:fractions.reduce((a,b)=>a+b,0),component:fractions.reduce((sum,f,i)=>sum+f*best.phases[i].x,0),g:fractions.reduce((sum,f,i)=>sum+f*best.phases[i].g,0)};
 const fugacities=best.phases.map(p=>({phase:p.label,values:p.kind==='vapor'?[p.x*P,(1-p.x)*P]:bubble(p.x,A,psat).partial}));
 const equalityResidual=best.phases.length>1?Math.max(...fugacities.flatMap(f=>f.values.map((value,i)=>Math.abs(value-fugacities[0].values[i])/Math.max(P,1)))):null;
 if(best.support&&!best.support.verified)throw new Error('Global phase stability could not be verified.');
 if(equalityResidual!==null&&equalityResidual>1e-7)throw new Error('Fugacity equality could not be verified.');
 return{version:VLLE_VERSION,A,psat,P,z,choice,type:best.type,phases:best.phases.map((p,i)=>({...p,fraction:fractions[i]})),family:best.family,activePhaseCount:fractions.filter(f=>f>1e-9).length,equilibriumG:sums.g,balanceResidual:Math.abs(sums.component-z),totalResidual:Math.abs(sums.total-1),equalityResidual,fugacities,support:best.support,triples,
 homogeneousLiquidG:liquid.gibbs(z,A),homogeneousVaporG:vaporG(z,P,psat),tieLines:list.filter(i=>i.phases.length>1),scope:'Hypothetical isothermal binary Margules / NRTL liquids + ideal vapor, synthetic saturation pressures, no Poynting correction or temperature dependence.'};
}
export function curves(r,n=400){
 return Array.from({length:n+1},(_,i)=>{const x=i/n,gL=liquid.gibbs(x,r.A),gV=vaporG(x,r.P,r.psat),values=[gL,gV];
  for(const t of r.tieLines){const xs=t.phases.map(p=>p.x);if(t.support&&x>=Math.min(...xs)&&x<=Math.max(...xs))values.push(t.support.intercept+t.support.slope*x);}
  const ref=r.support? r.support.intercept+r.support.slope*x:null;
  return{x,gL,gV,hull:Math.min(...values),liquidTPD:ref===null?null:gL-ref,vaporTPD:ref===null?null:gV-ref};
 });
}
export function pressureDiagram(A,psat,n=400){
 validate(A,psat);const triples=triplePoints(A,psat),xs=unique([...Array.from({length:n+1},(_,i)=>i/n),...triples.flatMap(t=>[t.xAlpha,t.xBeta]),...azeotropes(A,psat)]);
 return {triples,points:xs.map(x=>{const b=bubble(x,A,psat),inGap=triples.some(t=>x>t.xAlpha+1e-12&&x<t.xBeta-1e-12);return{x,y:inGap?null:b.y,P:inGap?null:b.P,homogeneousP:b.P};}),note:'Only globally stable liquid–vapor branches are drawn. Nonconvex/metastable liquid portions are omitted; the three-phase pressure is drawn separately.'};
}
