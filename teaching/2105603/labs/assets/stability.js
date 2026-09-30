/** Binary Margules / NRTL liquid equilibrium and global TPD. */
import {nrtl} from './case-study.js';
export const STABILITY_VERSION='1.2.0';
export function parameters(A){
 if(A?.model==='nrtl'){if(![A.tau12,A.tau21].every(v=>Number.isFinite(v)&&v>=-2&&v<=6)||!Number.isFinite(A.alpha)||A.alpha<.1||A.alpha>.6)throw new RangeError('NRTL requires tau12, tau21 in [-2,6] and alpha in [0.1,0.6].');return A;}
 const p=typeof A==='number'?{A12:A,A21:A}:A;
 if(!p||![p.A12,p.A21].every(v=>Number.isFinite(v)&&v>=0&&v<=6))throw new RangeError('Margules parameters must lie between 0 and 6.');
 return p;
}
function check(A,x){parameters(A);if(!Number.isFinite(x)||x<0||x>1)throw new RangeError('Mole fraction must lie between 0 and 1.');}
function nr(x,A){return nrtl(x,350,{a12:A.tau12,a21:A.tau21,b12:0,b21:0,alpha:A.alpha});}
export function gibbs(x,A){check(A,x);if(A?.model==='nrtl')return (x===0||x===1?0:x*Math.log(x)+(1-x)*Math.log1p(-x))+nr(x,A).gE;const {A12:a,A21:b}=parameters(A);return (x===0||x===1?0:x*Math.log(x)+(1-x)*Math.log1p(-x))+x*(1-x)*(a*(1-x)+b*x);}
export function slope(x,A){check(A,x);if(A?.model==='nrtl'){const l=nr(x,A).ln;return Math.log(x/(1-x))+l[0]-l[1];}const {A12:a,A21:b}=parameters(A);return Math.log(x/(1-x))+a+2*(b-2*a)*x+3*(a-b)*x*x;}
export function curvature(x,A){check(A,x);if(A?.model==='nrtl'){const u=Math.exp(-A.alpha*A.tau21),v=Math.exp(-A.alpha*A.tau12);return 1/(x*(1-x))-2*A.tau21*u*u/(x+(1-x)*u)**3-2*A.tau12*v*v/(1-x+x*v)**3;}const {A12:a,A21:b}=parameters(A);return 1/(x*(1-x))+2*b-4*a+6*(a-b)*x;}
export function chemicalPotentials(x,A){check(A,x);if(A?.model==='nrtl'){const l=nr(x,A).ln;return[Math.log(x)+l[0],Math.log1p(-x)+l[1]];}const {A12:a,A21:b}=parameters(A);return [Math.log(x)+(1-x)**2*(a+2*(b-a)*x),Math.log1p(-x)+x*x*(b+2*(a-b)*(1-x))];}
function root(fn,lo,hi){let fl=fn(lo),fh=fn(hi);if(fl===0)return lo;if(fh===0)return hi;if(fl*fh>0)throw new Error('Root not bracketed.');for(let i=0;i<100;i++){const mid=(lo+hi)/2,f=fn(mid);if(f===0||hi-lo<2e-14)return mid;if(fl*f<=0){hi=mid;}else{lo=mid;fl=f;}}throw new Error('Root did not converge.');}
const mul=(a,b)=>{const c=Array(a.length+b.length-1).fill(0);a.forEach((v,i)=>b.forEach((w,j)=>c[i+j]+=v*w));return c;};
const add=(a,b)=>Array.from({length:Math.max(a.length,b.length)},(_,i)=>(a[i]??0)+(b[i]??0));
const poly=(a,x)=>a.reduceRight((v,c)=>v*x+c,0);
function polynomialRoots(a){
 while(a.length>1&&Math.abs(a.at(-1))<1e-14*Math.max(...a.map(Math.abs)))a=a.slice(0,-1);
 if(a.length<=1)return[];if(a.length===2){const x=-a[0]/a[1];return x>0&&x<1?[x]:[];}
 const cuts=[0,...polynomialRoots(a.slice(1).map((v,i)=>v*(i+1))),1],roots=[];
 for(const x of cuts.slice(1,-1))if(Math.abs(poly(a,x))<1e-12*Math.max(...a.map(Math.abs)))roots.push(x);
 for(let i=1;i<cuts.length;i++)if(poly(a,cuts[i-1])*poly(a,cuts[i])<0)roots.push(root(x=>poly(a,x),cuts[i-1],cuts[i]));
 return [...new Set(roots)].sort((a,b)=>a-b);
}
function nrtlSpinodals(A){
 const u=Math.exp(-A.alpha*A.tau21),v=Math.exp(-A.alpha*A.tau12),d1=[u,1-u],d2=[1,v-1],cube=d=>mul(mul(d,d),d),c1=cube(d1),c2=cube(d2);
 const numerator=add(mul(c1,c2),mul([0,-2,2],add(c2.map(t=>t*A.tau21*u*u),c1.map(t=>t*A.tau12*v*v))));
 const cuts=[0,...polynomialRoots(numerator.slice(1).map((v,i)=>v*(i+1))),1],h=x=>x===0||x===1?1:x*(1-x)*curvature(x,A),roots=[];
 for(let i=1;i<cuts.length;i++)if(h(cuts[i-1])*h(cuts[i])<0)roots.push(root(h,cuts[i-1],cuts[i]));
 return {roots,minScaledCurvature:Math.min(...cuts.map(h)),criticalX:cuts.reduce((a,b)=>h(a)<h(b)?a:b)};
}
export function spinodals(A){
 if(A?.model==='nrtl'){parameters(A);return nrtlSpinodals(A);}
 const {A12:a,A21:b}=parameters(A),c=2*b-4*a,d=6*(a-b),h=x=>1+x*(1-x)*(c+d*x);
 const cuts=[0,1];const qa=-3*d,qb=2*(d-c),qc=c;
 if(Math.abs(qa)<1e-14){if(qb!==0){const x=-qc/qb;if(x>0&&x<1)cuts.push(x);}}
 else {const disc=qb*qb-4*qa*qc;if(disc>=0)for(const sign of [-1,1]){const x=(-qb+sign*Math.sqrt(disc))/(2*qa);if(x>0&&x<1)cuts.push(x);}}
 cuts.sort((a,b)=>a-b);const roots=[];
 for(let i=1;i<cuts.length;i++)if(h(cuts[i-1])*h(cuts[i])<0)roots.push(root(h,cuts[i-1],cuts[i]));
 return {roots,minScaledCurvature:Math.min(...cuts.map(h)),criticalX:cuts.reduce((best,x)=>h(x)<h(best)?x:best,cuts[0])};
}
function generalGaps(A){
 const sp=spinodals(A).roots;if(!sp.length)return [];
 if(sp.length%2)throw new Error('Unresolved spinodal topology.');
 for(let i=1;i<sp.length;i++)if(sp[i]-sp[i-1]<1e-5)throw new RangeError('State too close to criticality to resolve reliably. Move the parameters slightly.');
 const cuts=[0,...sp,1],branches=[];for(let i=0;i<cuts.length-1;i+=2)branches.push([cuts[i],cuts[i+1]]);
 const gaps=[];
 for(let i=0;i<branches.length;i++)for(let j=i+1;j<branches.length;j++){
  const L=branches[i],B=branches[j],lo=Math.max(slope(L[0],A),slope(B[0],A)),hi=Math.min(slope(L[1],A),slope(B[1],A));if(!(hi>lo))continue;
  const pair=m=>{const a=root(x=>slope(x,A)-m,...L),b=root(x=>slope(x,A)-m,...B);return{a,b,d:gibbs(b,A)-m*b-gibbs(a,A)+m*a};};
  if(pair(lo).d*pair(hi).d>0)continue;
  const m=root(m=>pair(m).d,lo,hi),{a,b}=pair(m),ga=gibbs(a,A),gb=gibbs(b,A),ma=chemicalPotentials(a,A),mb=chemicalPotentials(b,A),intercept=ga-m*a;
  const candidates=[0,1];for(let k=1;k<cuts.length;k++)if((slope(cuts[k-1],A)-m)*(slope(cuts[k],A)-m)<=0)candidates.push(root(x=>slope(x,A)-m,cuts[k-1],cuts[k]));
  if(Math.min(...candidates.map(x=>gibbs(x,A)-m*x-intercept))< -1e-9)continue;
  const result={xAlpha:a,xBeta:b,spinodalAlpha:sp[2*i],spinodalBeta:sp[2*j-1],g:ga,gAlpha:ga,gBeta:gb,slope:m,intercept,chemicalPotentialResidual:Math.max(...ma.map((v,k)=>Math.abs(v-mb[k]))),tangentResidual:Math.max(Math.abs(slope(a,A)-m),Math.abs(slope(b,A)-m),Math.abs((gb-ga)/(b-a)-m))};
  if(result.chemicalPotentialResidual>1e-7||result.tangentResidual>1e-7)throw new Error('Common-tangent verification failed.');gaps.push(result);
 }
 gaps.sort((a,b)=>a.xAlpha-b.xAlpha);
 if(!gaps.length)throw new Error('No verified common tangent found for a nonconvex liquid.');
 for(let i=1;i<gaps.length;i++)if(gaps[i].xAlpha<gaps[i-1].xBeta-1e-8)throw new RangeError('Degenerate multiphase coexistence is unresolved. Move the parameters slightly.');
 return gaps;
}
export function coexistenceGaps(A){const p=parameters(A);return p.model==='nrtl'||p.A12!==p.A21?generalGaps(A):[coexistence(A)].filter(Boolean);}
export function tpd(A,z,n=400){
 check(A,z);if(z===0||z===1)return {minimum:null,w:null,points:[],status:'Not applicable to pure feeds: absent-component chemical potential diverges.'};
 const g=gibbs(z,A),m=slope(z,A),f=w=>gibbs(w,A)-g-m*(w-z),cuts=[0,...spinodals(A).roots,1],candidates=[0,z,1];
 for(let i=1;i<cuts.length;i++){const lo=cuts[i-1],hi=cuts[i];if((slope(lo,A)-m)*(slope(hi,A)-m)<=0)candidates.push(root(w=>slope(w,A)-m,lo,hi));}
 const w=candidates.reduce((best,x)=>f(x)<f(best)?x:best,z),minimum=f(w);
 return {minimum,w,tolerance:1e-10,status:minimum < -1e-10?'Negative TPD: homogeneous feed is not globally stable.':'No negative TPD resolved within 1e-10.',points:Array.from({length:n+1},(_,i)=>({x:i/n,tpd:f(i/n)})),stationaryCandidates:candidates};
}
export function coexistence(A){
 check(A,.5);const p=parameters(A);if(p.model==='nrtl'||p.A12!==p.A21)return generalGaps(A)[0]??null;A=p.A12;if(A<=2)return null;
 // u=1-2*x_alpha removes the spurious x=.5 root. Series avoids cancellation near criticality.
 const ratio=u=>Math.abs(u)<.001?2*(1+u*u/3+u**4/5+u**6/7):2*Math.atanh(u)/u;
 let lo=0,hi=1-1e-12,iterations=0;
 for(;iterations<100;iterations++){const u=(lo+hi)/2;if(ratio(u)>A)hi=u;else lo=u;if(hi-lo<2e-14)break;}
 const u=(lo+hi)/2,xAlpha=(1-u)/2,xBeta=1-xAlpha;
 const spinodalAlpha=(1-Math.sqrt(1-2/A))/2,spinodalBeta=1-spinodalAlpha;
 const muA=chemicalPotentials(xAlpha,A),muB=chemicalPotentials(xBeta,A);
 return {xAlpha,xBeta,spinodalAlpha,spinodalBeta,g:gibbs(xAlpha,A),gAlpha:gibbs(xAlpha,A),gBeta:gibbs(xBeta,A),slope:0,intercept:gibbs(xAlpha,A),iterations,
 chemicalPotentialResidual:Math.max(...muA.map((v,i)=>Math.abs(v-muB[i]))),tangentResidual:Math.max(Math.abs(slope(xAlpha,A)),Math.abs(slope(xBeta,A)))};
}
export function equilibrium(A,z){
 check(A,z);const gaps=coexistenceGaps(A),binodal=gaps.find(b=>z>=b.xAlpha&&z<=b.xBeta)??gaps[0]??null,homogeneousG=gibbs(z,A),k=curvature(z,A);
 let state='stable',phase='one liquid',fractionBeta=null,fractionAlpha=null,xAlpha=null,xBeta=null,equilibriumG=homogeneousG;
 const p=parameters(A),info=spinodals(A);if(!binodal&&Math.abs(info.minScaledCurvature)<1e-12&&Math.abs(z-info.criticalX)<1e-10)state='critical';
 if(binodal){
  const a=binodal.xAlpha,b=binodal.xBeta;
  if(z>a&&z<b){
   phase='two liquids';fractionBeta=(z-a)/(b-a);fractionAlpha=1-fractionBeta;xAlpha=a;xBeta=b;equilibriumG=fractionAlpha*gibbs(a,A)+fractionBeta*gibbs(b,A);
   state=info.roots.some(x=>Math.abs(z-x)<1e-12)?'spinodal boundary':k<0?'unstable':'metastable';
  }else if(Math.min(Math.abs(z-a),Math.abs(z-b))<1e-12)state='binodal boundary';
 }
 const balanceResidual=phase==='two liquids'?Math.abs(fractionAlpha*xAlpha+fractionBeta*xBeta-z):0;
 return {A,z,state,phase,homogeneousG,equilibriumG,gain:Math.max(0,homogeneousG-equilibriumG),curvature:Number.isFinite(k)?k:null,
  binodal,gaps,xAlpha,xBeta,fractionAlpha,fractionBeta,balanceResidual,chemicalPotentialResidual:phase==='two liquids'?binodal.chemicalPotentialResidual:null,
  parameters:p,tpd:tpd(A,z),critical:state==='critical',scope:'Binary Margules / NRTL liquids and global binary TPD; no vapor, kinetics, interfacial energy or multicomponent TPD.'};
}
export function gibbsCurve(A,n=400){const gaps=coexistenceGaps(A);return Array.from({length:n+1},(_,i)=>{const x=i/n,g=gibbs(x,A),b=gaps.find(v=>x>=v.xAlpha&&x<=v.xBeta);return{x,g,ideal:gibbs(x,0),hull:b?b.intercept+b.slope*x:g,curvature:x===0||x===1?null:curvature(x,A)};});}
export function phaseMap(fixedA21=null){return Array.from({length:161},(_,i)=>{const A=fixedA21===null?2+4*i/160:6*i/160,b=coexistence(fixedA21===null?A:{A12:A,A21:fixedA21});return{A,xAlpha:b?.xAlpha??(fixedA21===null?.5:null),xBeta:b?.xBeta??(fixedA21===null?.5:null),spinodalAlpha:b?.spinodalAlpha??(fixedA21===null?.5:null),spinodalBeta:b?.spinodalBeta??(fixedA21===null?.5:null)};});}
