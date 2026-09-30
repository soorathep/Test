/** User-supplied binary VLE; all pressures normalized to kPa. */
import {nrtl} from './case-study.js';
import {areaAnalysis,differential,nelder} from './consistency.js';
export const INPUT_VERSION='1.0.0';
export function parseTable(text,withAntoine=false){
 if(typeof text!=='string'||text.length>1000000)throw new Error('Use a text table smaller than 1 MB.');
 text=text.replace(/^\uFEFF/,'');const first=text.split(/\r?\n/)[0],delimiter=first.includes('\t')?'\t':first.includes(';')?';':',';
 const rows=[];let row=[],field='',quoted=false;
 for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){field+='"';i++;}else if(quoted||field.trim()==='')quoted=!quoted;else throw new Error('Malformed quoted field.');}else if(!quoted&&(c===delimiter||c==='\n'||c==='\r')){row.push(field.trim());field='';if(c!==delimiter){if(row.some(v=>v!==''))rows.push(row);row=[];if(c==='\r'&&text[i+1]==='\n')i++;}}else field+=c;}
 if(quoted)throw new Error('Unclosed quote in table.');row.push(field.trim());if(row.some(v=>v!==''))rows.push(row);
 if(rows.length<2||rows.length>501)throw new Error('Supply a header and 1–500 data rows.');
 const headers=rows.shift().map(v=>v.toLowerCase()),required=withAntoine?['t','p','x1','y1']:['t','p','x1','y1','psat1','psat2'];
 if(new Set(headers).size!==headers.length||required.some(h=>!headers.includes(h)))throw new Error('Headers must include the required VLE columns without duplicates. With Antoine use T,P,x1,y1; otherwise also Psat1,Psat2. Optional: HE.');
 if(headers.some(h=>![...required,'he'].includes(h)))throw new Error('Unknown column. With Antoine use T,P,x1,y1 and optionally HE; remove any Psat columns because pressures are calculated from the correlations.');
 return rows.map((r,i)=>{if(r.length!==headers.length)throw new Error(`Row ${i+2}: column count differs from the header.`);return Object.fromEntries(headers.map((h,j)=>{const value=r[j];if(h==='he'&&value==='')return[h,null];if(!/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(value)||!Number.isFinite(Number(value)))throw new Error(`Row ${i+2}: ${h} must be a finite decimal number. Use a dot decimal separator.`);return[h,Number(value)];}));});
}
export function importVLE(text,{temperatureUnit='K',pressureUnit='kPa',path='isothermal',names=['Component 1','Component 2'],source='User-supplied measurements',antoine=null}={}){
 if(!['K','C'].includes(temperatureUnit)||!['kPa','Pa','bar'].includes(pressureUnit)||!['isothermal','isobaric'].includes(path))throw new Error('Unknown units or experimental path.');
 if(antoine!==null&&(!Array.isArray(antoine)||antoine.length!==2))throw new Error('Supply Antoine constants for both components.');
 if(names.length!==2||names.some(n=>typeof n!=='string'||!n.trim()))throw new Error('Name both components in their measured order.');
 const scale={kPa:1,Pa:.001,bar:100}[pressureUnit],raw=parseTable(text,antoine!==null),rows=raw.map((r,i)=>{
  const T=r.t+(temperatureUnit==='C'?273.15:0),PkPa=r.p*scale,s=antoine?antoine.map(c=>antoinePressure(c,T)):[r.psat1*scale,r.psat2*scale],x=r.x1,y=r.y1,HE=r.he??null;
  if(!(T>0&&T<2000&&Number.isFinite(PkPa)&&PkPa>0&&s.every(p=>Number.isFinite(p)&&p>0)&&x>=0&&x<=1&&y>=0&&y<=1))throw new Error(`Row ${i+2}: invalid temperature, pressure or mole fraction.`);
  if((x===0||x===1)&&y!==x)throw new Error(`Row ${i+2}: a pure liquid endpoint must have the same pure vapor composition.`);
  if(x>0&&x<1&&(y===0||y===1))throw new Error(`Row ${i+2}: interior liquid with zero vapor component cannot give finite log activity.`);
  const ln=x===0||x===1?null:[Math.log(y)+Math.log(PkPa)-Math.log(x)-Math.log(s[0]),Math.log1p(-y)+Math.log(PkPa)-Math.log1p(-x)-Math.log(s[1])];
  return{row:i+2,T,PkPa,x,y,s,HE,ln,f:ln?ln[0]-ln[1]:null,reason:ln?null:'Pure endpoint: absent-component activity is undefined; excluded from log-activity tests and fitting.'};
 }).sort((a,b)=>a.x-b.x);
 for(let i=1;i<rows.length;i++)if(rows[i].x-rows[i-1].x<1e-8)throw new Error(`Repeated or indistinguishable x1 near row ${rows[i].row}. Review replicates before importing; no averaging is performed.`);
 const ts=rows.map(r=>r.T),ps=rows.map(r=>r.PkPa);
 if(path==='isothermal'&&Math.max(...ts)-Math.min(...ts)>.05)throw new Error('Isothermal data must span no more than 0.05 K. Separate different experimental runs.');
 if(path==='isobaric'&&(Math.max(...ps)-Math.min(...ps))/(ps.reduce((a,b)=>a+b,0)/ps.length)>.001)throw new Error('Isobaric data must span no more than 0.1% of mean pressure. Separate different runs.');
 const valid=rows.filter(r=>r.ln);if(valid.length<5)throw new Error('At least five distinct interior observations are required.');
 return {version:INPUT_VERSION,name:names.join(' / '),names,source,path,synthetic:false,rows,valid,excluded:rows.filter(r=>!r.ln),endpointsKnown:false,heatKnown:valid.every(r=>r.HE!==null),antoine,pressureSource:antoine?'Antoine correlations evaluated at every measured T':'Supplied per-row saturation pressures',inputUnits:{temperatureUnit,pressureUnit,HE:'J/mol'},assumptions:'Binary mole fractions; ideal vapor; negligible Poynting and excess-volume pressure contributions. Supplied saturation pressures must apply at each measured T. Property sources and validity are the user’s responsibility.'};
}
export function diagnose(set,extension='none'){return{area:areaAnalysis(set,extension),differential:differential(set,true)};}
export function predict(row,model,v,alpha=.3,temperatureDependent=false){
 let gamma;if(model==='nrtl')gamma=nrtl(row.x,row.T,{alpha,a12:v[0]-(v[2]??0),a21:v[1]-(v[3]??0),b12:350*(v[2]??0),b21:350*(v[3]??0)}).gamma;
 else{const a=v[0],b=model==='margules1'?a:v[1],x=row.x;gamma=[Math.exp((1-x)**2*(a+2*(b-a)*x)),Math.exp(x*x*(b+2*(a-b)*(1-x)))];}
 const a=row.x*gamma[0]*row.s[0],b=(1-row.x)*gamma[1]*row.s[1];return{P:a+b,y:a/(a+b),gamma};
}
export function fitVLE(set,{model='nrtl',alpha=.3,temperatureDependent=false}={}){
 if(!['nrtl','margules1','margules2'].includes(model)||!Number.isFinite(alpha)||alpha<.1||alpha>.6)throw new Error('Invalid model or alpha.');
 if(temperatureDependent&&(model!=='nrtl'||set.path!=='isobaric'))throw new Error('Temperature-dependent fitting requires NRTL and an isobaric temperature series.');
 if(temperatureDependent&&Math.max(...set.valid.map(r=>r.T))-Math.min(...set.valid.map(r=>r.T))<1)throw new Error('At least 1 K of temperature span is required for four-parameter fitting; this does not guarantee identifiability.');
 const n=temperatureDependent?4:model==='margules1'?1:2;if(set.valid.length<n+3)throw new Error('Too few observations for the selected parameter count.');
 const bounds=Array.from({length:n},(_,i)=>i>1?[-40,40]:[-3,8]),fn=v=>set.valid.reduce((sum,r)=>{const q=predict(r,model,v,alpha);return sum+(100*(q.P-r.PkPa)/r.PkPa)**2+(100*(q.y-r.y))**2;},0)/set.valid.length;
 const starts=(n===1?[[0],[1],[3]]:[[0,0],[.5,2],[2,.5],[4,-.5],[-.5,4]]).map(v=>n===4?[...v,0,0]:v),runs=starts.map(v=>nelder(fn,v,bounds)),eligible=runs.filter(r=>r.converged&&Number.isFinite(r.f)).sort((a,b)=>a.f-b.f);
 if(!eligible.length)throw new Error('No fit converged. No fitted result is reported.');
 const best=eligible[0],points=set.valid.map(r=>{const q=predict(r,model,best.v,alpha);return {...r,Pcalc:q.P,ycalc:q.y,pressureResidual:100*(q.P-r.PkPa)/r.PkPa,yResidual:q.y-r.y};});
 const mean=key=>points.reduce((sum,r)=>sum+Math.abs(r[key]),0)/points.length,deltaP=mean('pressureResidual'),deltaY=100*mean('yResidual');
 return{model,alpha:model==='nrtl'?alpha:null,temperatureDependent,parameters:best.v,parameterNames:model==='nrtl'?(n===4?['c12','c21','d12','d21']:['tau12','tau21']):model==='margules1'?['A']:['A12','A21'],temperatureLaw:n===4?'tauij = cij + dij (350/T - 1)':'Dimensionless parameters held constant across the measured temperature range',objective:best.f,iterations:best.iterations,converged:true,atBound:best.v.some((v,i)=>Math.min(v-bounds[i][0],bounds[i][1]-v)<1e-4),runs,points,deltaP,deltaY,status:deltaP<1&&deltaY<1?'meets-reproduction-threshold':'outside-reproduction-threshold',method:'Joint unweighted mean [(100 ΔP/P)^2 + (100 Δy)^2], bounded multistart Nelder–Mead. These reproduction thresholds are teaching diagnostics, not certification of experimental consistency. No measurement weighting, parameter confidence intervals or global parameter-optimum claim.'};
}
export function exampleCSV(){const rows=['T,P,x1,y1,Psat1,Psat2'];for(let i=1;i<20;i++){const r={T:350,x:i/20,s:[150,60]},p=predict(r,'nrtl',[.8,1.2],.3);rows.push([r.T,p.P.toPrecision(12),r.x,p.y.toPrecision(12),150,60].join(','));}return rows.join('\n');}

/** Explicit selectable Antoine conventions; output is always kPa. */
export const ANTOINE_FORMS={
 'log10-plus':{label:'log₁₀(Psat) = A − B/(T + C)',base:10,cSign:1,bSign:-1},
 'ln-plus':{label:'ln(Psat) = A − B/(T + C)',base:Math.E,cSign:1,bSign:-1},
 'log10-minus':{label:'log₁₀(Psat) = A − B/(T − C)',base:10,cSign:-1,bSign:-1},
 'ln-minus':{label:'ln(Psat) = A − B/(T − C)',base:Math.E,cSign:-1,bSign:-1},
 'log10-signed':{label:'log₁₀(Psat) = A + B/(T + C)',base:10,cSign:1,bSign:1},
 'ln-signed':{label:'ln(Psat) = A + B/(T + C)',base:Math.E,cSign:1,bSign:1}
};
export function antoinePressure(c,T){
 const scale={kPa:1,Pa:.001,bar:100,mmHg:.13332236842105263},form=ANTOINE_FORMS[c?.form??'log10-plus'];
 if(!c||!form||![c.A,c.B,c.C,c.TminK,c.TmaxK,T].every(Number.isFinite)||!(c.TminK>0&&c.TmaxK>c.TminK)||!['K','C'].includes(c.temperatureUnit)||!Object.hasOwn(scale,c.pressureUnit))throw new Error('Invalid Antoine constants, equation form, units or temperature range.');
 if(form.bSign*c.B>=0)throw new Error(form.bSign===1?'For A + B/(T + C), B must be negative for increasing vapor pressure. Check the source convention.':'For A − B/(T ± C), B must be positive for increasing vapor pressure. Check the source convention.');
 if(T<c.TminK||T>c.TmaxK)throw new Error(`Antoine temperature ${T.toFixed(3)} K is outside the declared ${c.TminK}–${c.TmaxK} K range. No extrapolation is performed.`);
 const t=c.temperatureUnit==='C'?T-273.15:T,lo=c.temperatureUnit==='C'?c.TminK-273.15:c.TminK;
 if(lo+form.cSign*c.C<=0)throw new Error('Antoine denominator must be positive throughout the declared range. Check the selected equation and temperature convention.');
 const exponent=c.A+form.bSign*c.B/(t+form.cSign*c.C),P=scale[c.pressureUnit]*(form.base===10?10**exponent:Math.exp(exponent));
 if(!Number.isFinite(P)||P<=0)throw new Error('Antoine pressure is non-finite or nonpositive. Check constants and units.');
 return P;
}
export function exampleAntoine(){return [150,60].map((P,i)=>{const B=[30000,35000][i]/(8.31446261815324*Math.LN10);return{form:'log10-plus',A:Math.log10(P)+B/350,B,C:0,TminK:300,TmaxK:390,temperatureUnit:'K',pressureUnit:'kPa'};});}
export function exampleAntoineCSV(){return exampleCSV().split('\n').map(r=>r.split(',').slice(0,4).join(',')).join('\n');}
