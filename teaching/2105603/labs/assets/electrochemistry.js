// Equilibrium cell thermodynamics. Both half-reactions are entered as reductions.
import {R,fromLog} from './reaction.js';
export {R};
export const ELECTROCHEMISTRY_VERSION='1.0.0', F=96485.33212331002;
const sum=a=>a.reduce((s,v)=>s+v,0);
function finite(v,label){if(!Number.isFinite(v))throw new Error(label+' must be finite.');return v;}
function positive(v,label){finite(v,label);if(v<=0)throw new Error(label+' must be positive.');return v;}
export function half(text,n,mode='activities',cStandard=1){
 if(!Number.isInteger(n)||n<1||n>100)throw new Error('Electron count must be an integer from 1 to 100.');
 if(!['activities','concentration'].includes(mode))throw new Error('Unknown activity convention.');positive(cStandard,'Standard concentration');
 const lines=text.trim().split(/\r?\n/).filter(s=>s.trim()),sep=lines[0]?.includes('\t')?'\t':',';
 const rows=lines.map(s=>s.split(sep).map(v=>v.trim()));
 if(rows.shift()?.join(',')!=='species,nu,phase,atoms,charge,value,gamma')throw new Error('Use the exact species,nu,phase,atoms,charge,value,gamma header.');
 if(rows.length<1||rows.length>12)throw new Error('Enter 1 to 12 species per half-reaction, excluding electrons.');
 const species=rows.map(row=>{
  if(row.length!==7||row.some(v=>!v))throw new Error('Every row needs seven nonempty fields; quoted CSV is not supported.');
  const [name,nuText,phase,atomText,chargeText,valueText,gammaText]=row,nu=Number(nuText),charge=Number(chargeText),value=Number(valueText),gamma=Number(gammaText);
  if(!Number.isInteger(nu)||nu===0||Math.abs(nu)>100)throw new Error('Use nonzero integer stoichiometry with magnitude at most 100.');
  if(!Number.isInteger(charge)||Math.abs(charge)>100)throw new Error('Enter an integer species charge.');
  if(!['solute','gas','solid','pureLiquid'].includes(phase))throw new Error('Phase must be solute, gas, solid or pureLiquid.');
  const atoms={};for(const item of atomText.split(';')){const m=item.match(/^([A-Z][a-z]?):([1-9]\d*)$/);if(!m||atoms[m[1]])throw new Error('Use explicit unique atom counts, e.g. H:2;O:1.');const count=Number(m[2]);if(!Number.isSafeInteger(count)||count>1000)throw new Error('Atom counts must be integers no larger than 1000.');atoms[m[1]]=count;}
  positive(value,'Activity or concentration');positive(gamma,'Activity coefficient');let lnActivity;
  if(['solid','pureLiquid'].includes(phase)){if(value!==1||gamma!==1)throw new Error('Present pure phases require value=1 and gamma=1.');lnActivity=0;}
  else if(mode==='concentration'&&phase==='solute')lnActivity=Math.log(value)-Math.log(cStandard)+Math.log(gamma);
  else{if(gamma!==1)throw new Error('Direct activities (including gas f/p°) require gamma=1.');lnActivity=Math.log(value);}
  return{name,nu,phase,atoms,charge,value,gamma,lnActivity};
 });
 if(new Set(species.map(s=>s.name)).size!==species.length)throw new Error('Species names must be unique within each half-cell.');
 const balance={};for(const s of species)for(const [a,k] of Object.entries(s.atoms))balance[a]=(balance[a]??0)+s.nu*k;
 balance.charge=sum(species.map(s=>s.nu*s.charge))+n;
 if(Object.values(balance).some(v=>v!==0))throw new Error('Half-reaction is not balanced in atoms or charge after adding '+n+' electrons on the reactant side.');
 return{species,n,balance,lnQ:sum(species.map(s=>s.nu*s.lnActivity))};
}
export function calculate(s){
 positive(s.T,'Temperature');positive(s.potentialT,'Potential-data temperature');
 if(Math.abs(s.T-s.potentialT)>1e-8)throw new Error('E° data apply only at the declared potential-data temperature. Supply E° at the evaluation temperature; no extrapolation is made.');
 if(!s.source?.trim()||!s.reference?.trim())throw new Error('Document property sources, standard states and the common electrode reference.');
 finite(s.Eleft,'Left E°');finite(s.Eright,'Right E°');
 const left=half(s.left,s.nLeft,s.mode,s.cStandard),right=half(s.right,s.nRight,s.mode,s.cStandard);
 const gcd=(a,b)=>b?gcd(b,a%b):a,n=s.nLeft*s.nRight/gcd(s.nLeft,s.nRight),scaleLeft=n/s.nLeft,scaleRight=n/s.nRight;
 const net=[...left.species.map(v=>({...v,compartment:'L',nu:-v.nu*scaleLeft})),...right.species.map(v=>({...v,compartment:'R',nu:v.nu*scaleRight}))];
 const E0=s.Eright-s.Eleft,lnQ=sum(net.map(v=>v.nu*v.lnActivity)),lnK=n*F*E0/(R*s.T),E=E0-R*s.T/(n*F)*lnQ;
 const deltaG0=-n*F*E0,deltaG=-n*F*E;[E0,lnQ,lnK,E,deltaG0,deltaG].forEach(v=>finite(v,'Calculated result'));
 const standard=fromLog(lnK,s.T),observed=fromLog(lnQ,s.T);
 const potentialLeft=s.Eleft-R*s.T/(s.nLeft*F)*left.lnQ,potentialRight=s.Eright-R*s.T/(s.nRight*F)*right.lnQ;
 const direction=Math.abs(E)<1e-10?'Equilibrium within numerical tolerance':E>0?'Written direction favored: left oxidation, right reduction':'Reverse direction favored: right oxidation, left reduction';
 const logQ=lnQ/Math.LN10,logK=lnK/Math.LN10,lo=Math.min(-6,logQ-2,logK-2),hi=Math.max(6,logQ+2,logK+2);
 const curve=Array.from({length:161},(_,i)=>{const log10Q=lo+(hi-lo)*i/160;return{log10Q,E:E0-R*s.T*Math.LN10/(n*F)*log10Q};});
 return{version:ELECTROCHEMISTRY_VERSION,input:{...s},left,right,net,n,scaleLeft,scaleRight,E0,E,potentialLeft,potentialRight,lnQ,Q:observed.K,Qstatus:observed.Kstatus.replace('ln K','ln Q'),...standard,deltaG0,deltaG,direction,curve};
}
export function example(concentration=false){const header='species,nu,phase,atoms,charge,value,gamma\n';return{T:298.15,potentialT:298.15,Eleft:concentration?0:-0.4,Eright:concentration?0:0.3,nLeft:2,nRight:2,cStandard:1,mode:'concentration',reference:'Same hypothetical reference electrode for both reduction potentials',source:concentration?'Synthetic identical M2+/M electrodes in separate compartments; concentration in mol/L, gamma=1, c°=1 mol/L. Liquid junction potential assumed zero.':'Synthetic X2+/X and Y2+/Y electrodes. Potentials are teaching definitions, not real-material data. c°=1 mol/L, pure solids present; liquid junction potential zero.',left:header+(concentration?'M2+,-1,solute,M:1,2,0.01,1\nM,1,solid,M:1,0,1,1':'X2+,-1,solute,X:1,2,0.1,1\nX,1,solid,X:1,0,1,1'),right:header+(concentration?'M2+,-1,solute,M:1,2,1,1\nM,1,solid,M:1,0,1,1':'Y2+,-1,solute,Y:1,2,0.5,1\nY,1,solid,Y:1,0,1,1')};}
