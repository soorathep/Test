/** Symmetric one-parameter Margules liquid stability. Dimensionless mixing G/RT. */
export const STABILITY_VERSION='1.0.0';
function check(A,x){if(!Number.isFinite(A)||A<0||A>6)throw new RangeError('A must lie between 0 and 6.');if(!Number.isFinite(x)||x<0||x>1)throw new RangeError('Mole fraction must lie between 0 and 1.');}
export function gibbs(x,A){check(A,x);return (x===0||x===1?0:x*Math.log(x)+(1-x)*Math.log1p(-x))+A*x*(1-x);}
export function slope(x,A){check(A,x);return Math.log(x/(1-x))+A*(1-2*x);}
export function curvature(x,A){check(A,x);return 1/(x*(1-x))-2*A;}
export function chemicalPotentials(x,A){check(A,x);return [Math.log(x)+A*(1-x)**2,Math.log1p(-x)+A*x*x];}
export function coexistence(A){
 check(A,.5);if(A<=2)return null;
 // u=1-2*x_alpha removes the spurious x=.5 root. Series avoids cancellation near criticality.
 const ratio=u=>Math.abs(u)<.001?2*(1+u*u/3+u**4/5+u**6/7):2*Math.atanh(u)/u;
 let lo=0,hi=1-1e-12,iterations=0;
 for(;iterations<100;iterations++){const u=(lo+hi)/2;if(ratio(u)>A)hi=u;else lo=u;if(hi-lo<2e-14)break;}
 const u=(lo+hi)/2,xAlpha=(1-u)/2,xBeta=1-xAlpha;
 const spinodalAlpha=(1-Math.sqrt(1-2/A))/2,spinodalBeta=1-spinodalAlpha;
 const muA=chemicalPotentials(xAlpha,A),muB=chemicalPotentials(xBeta,A);
 return {xAlpha,xBeta,spinodalAlpha,spinodalBeta,g:gibbs(xAlpha,A),slope:0,iterations,
 chemicalPotentialResidual:Math.max(...muA.map((v,i)=>Math.abs(v-muB[i]))),tangentResidual:Math.max(Math.abs(slope(xAlpha,A)),Math.abs(slope(xBeta,A)))};
}
export function equilibrium(A,z){
 check(A,z);const binodal=coexistence(A),homogeneousG=gibbs(z,A),k=curvature(z,A);
 let state='stable',phase='one liquid',fractionBeta=null,fractionAlpha=null,xAlpha=null,xBeta=null,equilibriumG=homogeneousG;
 if(A===2&&z===.5)state='critical';
 if(binodal){
  const a=binodal.xAlpha,b=binodal.xBeta;
  if(z>a&&z<b){
   phase='two liquids';fractionBeta=(z-a)/(b-a);fractionAlpha=1-fractionBeta;xAlpha=a;xBeta=b;equilibriumG=fractionAlpha*gibbs(a,A)+fractionBeta*gibbs(b,A);
   state=Math.min(Math.abs(z-binodal.spinodalAlpha),Math.abs(z-binodal.spinodalBeta))<1e-12?'spinodal boundary':k<0?'unstable':'metastable';
  }else if(Math.min(Math.abs(z-a),Math.abs(z-b))<1e-12)state='binodal boundary';
 }
 const balanceResidual=phase==='two liquids'?Math.abs(fractionAlpha*xAlpha+fractionBeta*xBeta-z):0;
 return {A,z,state,phase,homogeneousG,equilibriumG,gain:Math.max(0,homogeneousG-equilibriumG),curvature:Number.isFinite(k)?k:null,
  binodal,xAlpha,xBeta,fractionAlpha,fractionBeta,balanceResidual,chemicalPotentialResidual:phase==='two liquids'?binodal.chemicalPotentialResidual:null,
  critical:A===2&&z===.5,scope:'Symmetric binary liquid only; no vapor, kinetics, interfacial energy or general multicomponent TPD calculation.'};
}
export function gibbsCurve(A,n=400){const b=coexistence(A);return Array.from({length:n+1},(_,i)=>{const x=i/n,g=gibbs(x,A);return{x,g,ideal:gibbs(x,0),hull:b&&x>=b.xAlpha&&x<=b.xBeta?b.g:g,curvature:x===0||x===1?null:curvature(x,A)};});}
export function phaseMap(){return Array.from({length:161},(_,i)=>{const A=2+4*i/160,b=coexistence(A);return{A,xAlpha:b?.xAlpha??.5,xBeta:b?.xBeta??.5,spinodalAlpha:b?.spinodalAlpha??.5,spinodalBeta:b?.spinodalBeta??.5};});}
