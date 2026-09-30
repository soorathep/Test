/** Synthetic PH flash: Q=W=0; equal phase Cp, constant latent heats, constant tau/A. */
import {flash,bounded,psat} from './thermo.js';
export const ADIABATIC_VERSION='1.0.0';
export const caloric={referenceT:350,Cp:[100,120],Hvap:[30000,35000],units:'Cp: J mol^-1 K^-1; Hvap: J mol^-1'};
export function enthalpy(T,x,kind='liquid'){
 const h=caloric.Cp.map((cp,i)=>cp*(T-caloric.referenceT)+(kind==='vapor'?caloric.Hvap[i]:0));return x*h[0]+(1-x)*h[1];
}
function validate(system,A){
 if(system.kind!=='synthetic'||system.components.length!==2||!system.components.every((c,i)=>c.equation==='clausius'&&c.HvapJmol===caloric.Hvap[i]))throw new RangeError('The caloric model is only defined for the original synthetic binary system.');
 if(A?.model==='nrtl'&&A.temperatureMode!=='constant')throw new RangeError('Adiabatic flash requires the explicit constant-tau teaching assumption. A fixed-T fit has no caloric temperature model.');
}
export function enthalpyState(system,T,P,z,A=0){
 const f=flash(system,T,P,z,A);
 if(f.beta===null){const hL=enthalpy(T,z),hV=enthalpy(T,z,'vapor');return {flash:f,min:hL,max:hV};}
 const hL=f.x===null?0:enthalpy(T,f.x),hV=f.y===null?0:enthalpy(T,f.y,'vapor'),H=(1-f.beta)*hL+f.beta*hV;return{flash:f,min:H,max:H};
}
export function phFlash(system,P,z,H,A=0){
 validate(system,A);bounded(P,1000,200000,'Pressure (Pa)');bounded(z,0,1,'Feed fraction');if(!Number.isFinite(H))throw new RangeError('Feed enthalpy must be finite.');
 let [lo,hi]=system.rangeK;const left=enthalpyState(system,lo,P,z,A),right=enthalpyState(system,hi,P,z,A),history=[];
 if(H<left.min-1e-5||H>right.max+1e-5)throw new RangeError('No energy-balanced equilibrium within the 300–390 K property range.');
 for(let i=0;i<100;i++){
  const T=i===0&&Math.abs(H-left.min)<1e-5?lo:i===0&&Math.abs(H-right.max)<1e-5?hi:(lo+hi)/2,q=enthalpyState(system,T,P,z,A);
  const residual=H<q.min?q.min-H:H>q.max?q.max-H:0;history.push({iteration:i+1,T,enthalpyMin:q.min,enthalpyMax:q.max,residual});
  if(Math.abs(residual)<1e-5){
   const f=q.flash,beta=f.beta===null?Math.max(0,Math.min(1,(H-q.min)/(q.max-q.min))):f.beta;
   const x=f.x,y=f.y,hL=x===null?0:enthalpy(T,x),hV=y===null?0:enthalpy(T,y,'vapor'),Hout=(1-beta)*hL+beta*hV;
   const mass=Math.abs((1-beta)*(x??z)+beta*(y??z)-z);
   if(Math.abs(Hout-H)>1e-4||mass>1e-8)throw new Error('Independent energy or component balance failed.');
   return{version:ADIABATIC_VERSION,T,P,z,H,A,beta,x,y,hL:x===null?null:hL,hV:y===null?null:hV,Hout,energyResidual:Hout-H,balanceResidual:mass,phase:f.phase==='indeterminate'?'Saturation · amount fixed by energy':f.phase,innerFlash:f,history,caloric,scope:'Synthetic binary only; ideal vapor; convex liquid; constant dimensionless activity parameters; equal liquid/vapor Cp; zero excess enthalpy; no pressure enthalpy correction, heat loss, shaft work or kinetic/potential energy.'};
  }
  if(residual>0)hi=T;else lo=T;
 }
 throw new Error('Energy balance did not converge.');
}
export function adiabaticFlash(system,P,z,feedT,A=0){
 bounded(feedT,...system.rangeK,'Liquid feed temperature');const r=phFlash(system,P,z,enthalpy(feedT,z),A);
 const s=system.components.map(c=>psat(c,feedT));
 // Upstream liquid is stipulated compressed, with its pressure above its bubble pressure.
 return {...r,feedT,feedCondition:'Compressed liquid feed at sufficient upstream pressure; pressure contribution to enthalpy neglected.',feedSaturationPressures:s};
}
export function energyCurve(system,P,z,A,n=100){validate(system,A);return Array.from({length:n+1},(_,i)=>{const T=system.rangeK[0]+(system.rangeK[1]-system.rangeK[0])*i/n,q=enthalpyState(system,T,P,z,A);return{T,min:q.min,max:q.max,beta:q.flash.beta};});}
