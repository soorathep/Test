/** Pressure-form second virial, Z=1+Bmix P/RT, with matching fugacity reference. */
import {gamma,liquidG,convexity,parameters} from './thermo.js';
import {antoinePressure} from './vle-input.js';
export const VIRIAL_VERSION='1.0.0',R=8.31446261815324;
const mix=x=>x===0||x===1?0:x*Math.log(x)+(1-x)*Math.log1p(-x);
const unique=a=>a.sort((x,y)=>x-y).filter((x,i,b)=>i===0||x-b[i-1]>1e-9);
function root(f,a,b){let fa=f(a),fb=f(b);if(Math.abs(fa)<1e-12)return a;if(Math.abs(fb)<1e-12)return b;if(fa*fb>0)throw new Error('Root is not bracketed.');for(let i=0;i<80;i++){const m=(a+b)/2,fm=f(m);if(Math.abs(fm)<1e-12||b-a<1e-13)return m;if(fa*fm<=0)b=m;else{a=m;fa=fm;}}throw new Error('Root did not converge.');}
const mul=(a,b)=>{const c=Array(a.length+b.length-1).fill(0);a.forEach((v,i)=>b.forEach((w,j)=>c[i+j]+=v*w));return c;};
const add=(a,b)=>Array.from({length:Math.max(a.length,b.length)},(_,i)=>(a[i]??0)+(b[i]??0));
const poly=(a,x)=>a.reduceRight((v,c)=>v*x+c,0);
function roots(a){const scale=Math.max(...a.map(Math.abs));if(scale===0)return[];a=a.map(v=>v/scale);while(a.length>1&&Math.abs(a.at(-1))<1e-13)a=a.slice(0,-1);if(a.length<2)return[];if(a.length===2){const x=-a[0]/a[1];return x>0&&x<1?[x]:[];}const cuts=[0,...roots(a.slice(1).map((v,i)=>v*(i+1))),1],out=[];for(const x of cuts.slice(1,-1))if(Math.abs(poly(a,x))<1e-10)out.push(x);for(let i=1;i<cuts.length;i++)if(poly(a,cuts[i-1])*poly(a,cuts[i])<0)out.push(root(x=>poly(a,x),cuts[i-1],cuts[i]));return unique(out);}
export function coefficients(v,T){
 if(!v||!Array.isArray(v.B)||!Array.isArray(v.slope)||!['cm3/mol','m3/mol'].includes(v.unit)||!['constant','linear'].includes(v.law)||![v.Tref,v.Tmin,v.Tmax,T,...v.B,...v.slope].every(Number.isFinite)||v.B.length!==3||v.slope.length!==3||v.Tmin<=0||v.Tmax<=v.Tmin||v.Tref<v.Tmin||v.Tref>v.Tmax)throw new Error('Invalid virial coefficients, units or temperature range.');
 if(T<v.Tmin||T>v.Tmax)throw new Error('Temperature outside the declared virial-coefficient range.');const factor=v.unit==='cm3/mol'?1e-6:1;
 return v.B.map((b,i)=>factor*(b+(v.law==='linear'?v.slope[i]*(T-v.Tref):0)));
}
export function vapor(y,T,P,B){
 if(!(y>=0&&y<=1&&T>0&&P>0)||B.length!==3||!B.every(Number.isFinite))throw new Error('Invalid vapor state.');
 const [a,b,c]=B,z=1-y,Bmix=y*y*a+2*y*z*b+z*z*c,lnPhi=[(2*(y*a+z*b)-Bmix)*P/(R*T),(2*(y*b+z*c)-Bmix)*P/(R*T)];return{Bmix,Z:1+Bmix*P/(R*T),lnPhi,phi:lnPhi.map(Math.exp)};
}
export function state(input,P=input.P){
 const {T,A,antoine,virial,poynting=false,volumes=[0,0]}=input;parameters(A);if(!convexity(A).convex)throw new Error('Nonconvex liquid: this VLE comparison excludes LLE/VLLE. Use Lab 06.');
 if(A?.model==='nrtl'&&A.temperatureMode==='fixed'&&Math.abs(T-A.referenceT)>1e-8)throw new Error('NRTL parameters are fixed at a different temperature.');
 if(!Array.isArray(antoine)||antoine.length!==2||!Number.isFinite(P)||P<1000||P>200000)throw new Error('Supply two Antoine correlations and pressure within 1–200 kPa.');
 const sat=antoine.map(c=>antoinePressure(c,T)*1000),B=coefficients(virial,T),indicator=Math.max(P,...sat)*Math.max(...B.map(Math.abs))/(R*T);
 if(indicator>.1+1e-12)throw new Error('Virial truncation guard exceeded: max |Bij| × max(P, Psat)/(RT) must be ≤ 0.1. This teaching guard is not an accuracy guarantee.');
 if(volumes.length!==2||!volumes.every(v=>Number.isFinite(v)&&v>=0&&v<=1000)||(poynting&&volumes.some(v=>v<=0)))throw new Error('Liquid molar volumes must be positive and ≤1000 cm³/mol when Poynting is enabled.');
 const lnSat=[B[0]*sat[0]/(R*T),B[2]*sat[1]/(R*T)],lnPoynting=volumes.map((v,i)=>poynting?v*1e-6*(P-sat[i])/(R*T):0),offset=sat.map((p,i)=>Math.log(P/p)-lnSat[i]-lnPoynting[i]);
 const delta=B[0]-2*B[1]+B[2];if(1+Math.min(0,delta*P/(2*R*T))<=1e-8)throw new Error('Vapor composition curvature is not positive.');
 return{...input,P,sat,B,lnSat,lnPoynting,offset,indicator,delta};
}
export function vaporG(y,s){return mix(y)+y*s.offset[0]+(1-y)*s.offset[1]+vapor(y,s.T,s.P,s.B).Bmix*s.P/(R*s.T);}
const liquidMu=(x,A)=>{const g=gamma(x,A);return[Math.log(x)+Math.log(g[0]),Math.log1p(-x)+Math.log(g[1])];};
export function vaporMu(y,s){const v=vapor(y,s.T,s.P,s.B);return[Math.log(y)+s.offset[0]+v.lnPhi[0],Math.log1p(-y)+s.offset[1]+v.lnPhi[1]];}
const difference=a=>a[0]-a[1];
function yForSlope(slope,s){return root(y=>difference(vaporMu(y,s))-slope,0,1);}
function fromLiquid(x,s){if(x===0||x===1)return{x,y:x,residual:vaporG(x,s)};const mu=liquidMu(x,s.A),slope=difference(mu),y=yForSlope(slope,s);return{x,y,mu,residual:vaporG(y,s)-mu[1]-slope*y};}
function fromVapor(y,s){if(y===0||y===1)return{x:y,y,residual:-vaporG(y,s)};const mu=vaporMu(y,s),slope=difference(mu),x=root(x=>difference(liquidMu(x,s.A))-slope,0,1);return{x,y,mu,residual:liquidG(x,s.A)-mu[1]-slope*x};}
/** All extrema of vapor distance from a liquid tangent occur at x=y. */
function equalCompositionRoots(s){
 const C=-s.offset[0]+s.offset[1]-2*s.P*(s.B[1]-s.B[2])/(R*s.T),L=-2*s.P*s.delta/(R*s.T),p=parameters(s.A);
 if(p.model!=='nrtl')return roots([p.A12+C,2*(p.A21-2*p.A12)+L,3*(p.A12-p.A21)]);
 const u=Math.exp(-p.alpha*p.tau21),v=Math.exp(-p.alpha*p.tau12),du=mul([u,1-u],[u,1-u]),dv=mul([1,v-1],[1,v-1]);
 const a=[u,-2*u,-(1-u)].map(t=>t*p.tau21*u),b=[1,-2,-(v-1)].map(t=>t*p.tau12*v);
 return roots(add(add(mul(a,dv),mul(b,du)),mul([C,L],mul(du,dv))));
}
export function flash(input){
 const s=state(input),z=input.z;if(!Number.isFinite(z)||z<0||z>1)throw new Error('Feed mole fraction must lie in [0,1].');const candidates=[];
 if(z===0||z===1){const g=vaporG(z,s),beta=Math.abs(g)<1e-9?null:g>0?0:1;return finish(s,{type:beta===null?'Saturation · β undetermined':beta===0?'Liquid':'Vapor',x:beta===1?null:z,y:beta===0?null:z,beta,g:Math.min(0,g),support:{liquidMinimum:null,vaporMinimum:null,verified:true}},[]);}
 const cuts=unique([0,...equalCompositionRoots(s),1]),h=x=>fromLiquid(x,s).residual,xs=[];
 for(const x of cuts)if(Math.abs(h(x))<1e-9)xs.push(x);
 for(let i=1;i<cuts.length;i++)if(h(cuts[i-1])*h(cuts[i])<0)xs.push(root(h,cuts[i-1],cuts[i]));
 const atFeed=fromLiquid(z,s);if(Math.abs(atFeed.residual)<1e-10&&Math.abs(atFeed.x-atFeed.y)<1e-9)xs.push(z);
 const ties=unique(xs).map(x=>fromLiquid(x,s));
 for(const q of ties){if(Math.abs(q.x-q.y)<1e-8){if(Math.abs(z-q.x)<1e-8)candidates.push({type:'Azeotropic saturation · β undetermined',...q,beta:null,g:liquidG(z,s.A),support:{liquidMinimum:0,vaporMinimum:q.residual,verified:Math.abs(q.residual)<1e-8}});continue;}let beta=(z-q.x)/(q.y-q.x);if(beta< -1e-9||beta>1+1e-9)continue;beta=Math.max(0,Math.min(1,beta));candidates.push({type:'Liquid + vapor',...q,beta,g:(1-beta)*liquidG(q.x,s.A)+beta*vaporG(q.y,s),support:{liquidMinimum:0,vaporMinimum:q.residual,verified:Math.abs(q.residual)<1e-8}});}
 const l=fromLiquid(z,s),v=fromVapor(z,s);if(l.residual>=-1e-9)candidates.push({type:'Liquid',x:z,y:null,beta:0,g:liquidG(z,s.A),support:{liquidMinimum:0,vaporMinimum:l.residual,verified:true}});if(v.residual>=-1e-9)candidates.push({type:'Vapor',x:null,y:z,beta:1,g:vaporG(z,s),support:{liquidMinimum:v.residual,vaporMinimum:0,verified:true}});
 if(!candidates.length)throw new Error('No globally supporting VLE state could be resolved.');candidates.sort((a,b)=>Math.abs(a.g-b.g)<1e-9?(a.beta===null?-1:b.beta===null?1:(a.type==='Liquid + vapor'?-1:1)):a.g-b.g);return finish(s,candidates[0],ties);
}
function finish(s,q,ties){
 const beta=q.beta,balance=beta===null?null:Math.abs((1-beta)*(q.x??0)+beta*(q.y??0)-s.z),vl=q.y===null?null:vapor(q.y,s.T,s.P,s.B),g=q.x===null?null:gamma(q.x,s.A),fL=g?g.map((v,i)=>(i===0?q.x:1-q.x)*v*s.sat[i]*Math.exp(s.lnSat[i]+s.lnPoynting[i])):null,fV=vl?vl.phi.map((v,i)=>(i===0?q.y:1-q.y)*v*s.P):null;
 const residual=fL&&fV?Math.max(...fL.map((v,i)=>Math.abs(v-fV[i])/s.P)):null;if((balance!==null&&balance>1e-8)||(residual!==null&&residual>1e-7)||!q.support.verified)throw new Error('Independent balance, fugacity or stability verification failed.');
 return{version:VIRIAL_VERSION,input:s,...q,ties,vapor:vl,gamma:g,fL,fV,fugacityResidual:residual,balanceResidual:balance};
}
export function boundary(input,composition,kind='bubble'){
 if(!Number.isFinite(composition)||composition<0||composition>1||!['bubble','dew'].includes(kind))throw new Error('Invalid boundary specification.');const initial=state(input),limit=Math.min(200000,Math.max(...initial.B.map(Math.abs))===0?200000:.1*R*input.T/Math.max(...initial.B.map(Math.abs))),history=[];
 const f=P=>{const s=state(input,P),q=kind==='bubble'?fromLiquid(composition,s):fromVapor(composition,s);return q.residual;};
 const lo=1000,hi=limit;if(hi<lo)throw new Error('No pressure interval inside the virial guard.');if(f(lo)*f(hi)>0)throw new RangeError('Boundary outside 1–200 kPa or the virial truncation guard.');
 const P=root(p=>{const residual=f(p);history.push({P:p,residual});return residual;},lo,hi),s=state(input,P),q=kind==='bubble'?fromLiquid(composition,s):fromVapor(composition,s);return{...q,P,kind,history};
}
export function compare(input){const real=flash(input),idealInput={...input,virial:{...input.virial,B:[0,0,0],slope:[0,0,0]}},ideal=flash(idealInput);const boundaries={};for(const [name,v] of [['virial',input],['ideal',idealInput]]){boundaries[name]={};for(const kind of ['bubble','dew']){try{boundaries[name][kind]=boundary(v,input.z,kind);}catch(error){boundaries[name][kind]={unavailable:error.message};}}}return{version:VIRIAL_VERSION,input,real,ideal,boundaries};}
export function curves(result,n=100){const s=result.real.input,t=result.ideal.input;return Array.from({length:n+1},(_,i)=>{const x=i/n;return{x,liquidG:liquidG(x,s.A),virialG:vaporG(x,s),idealG:vaporG(x,t),Z:vapor(x,s.T,s.P,s.B).Z,phi:vapor(x,s.T,s.P,s.B).phi};});}
