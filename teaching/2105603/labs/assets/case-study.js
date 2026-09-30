/** IPA/water teaching study. Independent of the Margules-only flash API. */
export const CASE_VERSION='1.0.0';
function finite(v,label){if(!Number.isFinite(v))throw new RangeError(`${label} must be finite.`);return v;}
export function nrtl(x,T,p){
  if(!(x>=0&&x<=1&&T>0))throw new RangeError('Invalid NRTL state.');
  const t12=finite(p.a12,'a12')+finite(p.b12??0,'b12')/T;
  const t21=finite(p.a21,'a21')+finite(p.b21??0,'b21')/T;
  const alpha=finite(p.alpha,'alpha');if(alpha<0||alpha>1)throw new RangeError('alpha outside 0–1.');
  const G12=Math.exp(-alpha*t12),G21=Math.exp(-alpha*t21),z=1-x;
  const d21=x+z*G21,d12=z+x*G12;
  const ln=[z*z*(t21*(G21/d21)**2+t12*G12/d12**2),x*x*(t12*(G12/d12)**2+t21*G21/d21**2)];
  return {ln,gamma:ln.map(Math.exp),gE:x*z*(t21*G21/d21+t12*G12/d12),t12,t21};
}
export function pressure(c,T){
  if(!Number.isFinite(T)||T<c.rangeK[0]||T>c.rangeK[1])throw new RangeError(`${c.name}: T outside ${c.rangeK.join('–')} K.`);
  return 100*10**(c.A-c.B/(T+c.C)); // kPa
}
export function domain(data){return [Math.max(...data.properties.map(c=>c.rangeK[0])),Math.min(...data.properties.map(c=>c.rangeK[1]))];}
export function infer(row,data){
  const {x,y,T}=row,P=row.PkPa;
  if(!(P>0&&x>=0&&x<=1&&y>=0&&y<=1))throw new RangeError('Invalid VLE observation.');
  if(x===0||x===1)return {...row,ln:null,reason:'Pure endpoint: absent-component activity is undefined.'};
  if(y===0||y===1)return {...row,ln:null,reason:'Zero vapor fraction prevents logarithm.'};
  try {const s=data.properties.map(c=>pressure(c,T));return {...row,ln:[Math.log(y*P/(x*s[0])),Math.log((1-y)*P/((1-x)*s[1]))],reason:null};}
  catch(e){if(e instanceof RangeError)return {...row,ln:null,reason:e.message};throw e;}
}
/** Piecewise-linear signed and absolute areas; split segments at zero exactly. */
export function areas(points){
  const rows=[...points].sort((a,b)=>a.x-b.x);let positive=0,negative=0;
  for(let i=1;i<rows.length;i++){
    const a=rows[i-1],b=rows[i],dx=b.x-a.x;
    if(!(dx>0)||![a.f,b.f].every(Number.isFinite))throw new RangeError('Area points must be finite with distinct compositions.');
    if(a.f*b.f<0){const fraction=Math.abs(a.f)/(Math.abs(a.f)+Math.abs(b.f));const A=.5*dx*fraction*Math.abs(a.f),B=.5*dx*(1-fraction)*Math.abs(b.f);if(a.f>0){positive+=A;negative+=B;}else{negative+=A;positive+=B;}}
    else {const A=.5*dx*(a.f+b.f);if(A>=0)positive+=A;else negative-=A;}
  }
  const total=positive+negative;
  return {positive,negative,signed:positive-negative,D:total>1e-12?100*Math.abs(positive-negative)/total:null,xmin:rows[0]?.x??null,xmax:rows.at(-1)?.x??null};
}
export function experimentalDiagnostic(dataset,data){
  const rows=dataset.rows.map(r=>infer(r,data)),valid=rows.filter(r=>r.ln);
  return {rows,area:areas(valid.map(r=>({x:r.x,f:r.ln[0]-r.ln[1]}))),validCount:valid.length,
    verdict:'Not assessed: partial composition interval and isobaric temperature correction unresolved.',paper:dataset.paperConsistency};
}
export function modelCheck(p,T=350){
  let residual=0,minScaledCurvature=Infinity;const h=1e-5;
  for(let i=1;i<200;i++){
    const x=i/200,lo=nrtl(x-h,T,p).ln,hi=nrtl(x+h,T,p).ln;
    const d=hi.map((v,j)=>(v-lo[j])/(2*h));
    residual=Math.max(residual,Math.abs(x*d[0]+(1-x)*d[1]));
    minScaledCurvature=Math.min(minScaledCurvature,1+x*(1-x)*(d[0]-d[1]));
  }
  return {fixedTK:T,maxGibbsDuhemResidual:residual,minSampledScaledCurvature:minScaledCurvature,samples:199};
}
export function synthetic(p,bias=0,T=350){
  finite(bias,'bias');if(Math.abs(bias)>.3)throw new RangeError('Bias is restricted to ±0.3.');
  // Controlled log-activity perturbation, not an experimental VLE measurement.
  const points=Array.from({length:401},(_,i)=>{const x=i/400,ln=nrtl(x,T,p).ln;return {x,f:ln[0]-ln[1]+bias*(1-x)**2};});
  return {points,area:areas(points),bias,T,description:'Synthetic fixed-T activity data; ln gamma1 receives bias*(1-x)^2; gamma2 unchanged.'};
}
export function bubble(data,P,x,p){
  if(!(P>0&&x>=0&&x<=1))throw new RangeError('Invalid bubble input.');
  const at=T=>{const g=nrtl(x,T,p).gamma,s=data.properties.map(c=>pressure(c,T)),Pcalc=x*g[0]*s[0]+(1-x)*g[1]*s[1];return {T,x,y:x*g[0]*s[0]/Pcalc,Pcalc};};
  let [lo,hi]=domain(data),flo=at(lo).Pcalc-P,fhi=at(hi).Pcalc-P;
  if(flo*fhi>0)return null;
  for(let i=0;i<70;i++){const mid=(lo+hi)/2,v=at(mid),f=v.Pcalc-P;if(Math.abs(f/P)<1e-11)return v;if(f*flo<=0){hi=mid;}else{lo=mid;flo=f;}}
  throw new Error('Bubble solver failed to converge.');
}
export function curve(data,P,p){return Array.from({length:101},(_,i)=>bubble(data,P,i/100,p)??{x:i/100,y:null,T:null});}
export function objective(points,p){
  if(!points.length)throw new RangeError('No valid points to fit.');
  return points.reduce((sum,r)=>{const ln=nrtl(r.x,r.T,p).ln;return sum+(ln[0]-r.ln[0])**2+(ln[1]-r.ln[1])**2;},0)/(2*points.length);
}
/** Two constant tau parameters, fixed alpha; bounded multistart Nelder–Mead. */
export function fit(points,alpha=.47){
  const clamp=v=>v.map(x=>Math.max(-3,Math.min(8,x)));
  const make=v=>{v=clamp(v);const p={alpha,a12:v[0],a21:v[1],b12:0,b21:0};return {v,f:objective(points,p)};};
  let best=null;
  for(const start of [[0,0],[.5,2],[2,.5],[4,-.5],[-.5,4]]){
    let s=[make(start),make([start[0]+.3,start[1]]),make([start[0],start[1]+.3])],converged=false,iteration=0;
    for(;iteration<350;iteration++){
      s.sort((a,b)=>a.f-b.f);
      if(Math.max(...s.slice(1).map(a=>Math.hypot(a.v[0]-s[0].v[0],a.v[1]-s[0].v[1])))<1e-7){converged=true;break;}
      const c=s[0].v.map((v,j)=>(v+s[1].v[j])/2),r=make(c.map((v,j)=>2*v-s[2].v[j]));
      if(r.f<s[0].f){const e=make(c.map((v,j)=>v+2*(r.v[j]-v)));s[2]=e.f<r.f?e:r;}
      else if(r.f<s[1].f)s[2]=r;
      else {const outside=r.f<s[2].f,ref=outside?r:s[2],q=make(c.map((v,j)=>v+.5*(ref.v[j]-v)));
        if(q.f<(outside?r.f:s[2].f))s[2]=q;else s=[s[0],...s.slice(1).map(a=>make(a.v.map((v,j)=>(v+s[0].v[j])/2)))];}
    }
    s.sort((a,b)=>a.f-b.f);const a=s[0];if(converged&&(!best||a.f<best.f))best={...a,converged,iterations:iteration};
  }
  if(!best)throw new Error('Fit did not converge.');
  return {parameters:{alpha,a12:best.v[0],a21:best.v[1],b12:0,b21:0},rmse:Math.sqrt(best.f),objective:best.f,points:points.length,converged:best.converged,iterations:best.iterations,atBound:best.v.some(v=>Math.abs(v+3)<1e-5||Math.abs(v-8)<1e-5),method:'Five-start bounded Nelder–Mead, tau in [-3,8], unweighted mean squared ln-gamma residual, fixed alpha. Constant tau across the selected temperature range.'};
}
