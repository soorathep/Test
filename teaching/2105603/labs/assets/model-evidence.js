/** Conditional resampling and explicit held-out validation. Never a consistency verdict. */
import {fitVLE,predict} from './vle-input.js';
import {fit as fitLLE,validateRows} from './lle-fit.js';
export function random(seed){if(!Number.isInteger(seed)||seed<0||seed>4294967295)throw new Error('Seed must be an integer in [0, 4294967295].');let state=seed>>>0;return()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296;};}
export function quantile(values,p){const a=[...values].sort((x,y)=>x-y),x=(a.length-1)*p,i=Math.floor(x);return a.length?a[i]+(a[Math.min(i+1,a.length-1)]-a[i])*(x-i):null;}
const interval=a=>({lower:quantile(a,.025),median:quantile(a,.5),upper:quantile(a,.975)});
const metrics=rows=>({count:rows.length,pressureRMSEpercent:Math.sqrt(rows.reduce((s,r)=>s+r.pressureResidual**2,0)/rows.length),yRMSEpoints:100*Math.sqrt(rows.reduce((s,r)=>s+r.yResidual**2,0)/rows.length)});
const evaluate=(rows,fit)=>rows.map(r=>{const q=predict(r,fit.model,fit.parameters,fit.alpha??.3);return{row:r.row,T:r.T,x:r.x,P:r.PkPa,y:r.y,Pcalc:q.P,ycalc:q.y,pressureResidual:100*(q.P-r.PkPa)/r.PkPa,yResidual:q.y-r.y};});
export function splitVLE(set,{method='interleaved',fraction=.2,seed=42}={}){
 if(!set?.valid||!['interleaved','upper-x','random'].includes(method)||!Number.isFinite(fraction)||fraction<.1||fraction>.4)throw new Error('Choose a 10–40% holdout and a supported split.');
 const rand=random(seed),rows=[...set.valid].sort((a,b)=>a.x-b.x),n=Math.max(2,Math.round(rows.length*fraction));
 if(rows.length-n<5)throw new Error('Need at least five training rows and two held-out rows.');
 let indices;if(method==='upper-x')indices=Array.from({length:n},(_,i)=>rows.length-n+i);
 else if(method==='interleaved')indices=Array.from({length:n},(_,i)=>Math.floor((i+.5)*rows.length/n));
 else{const all=rows.map((_,i)=>i);for(let i=all.length-1;i>0;i--){const j=Math.floor(rand()*(i+1));[all[i],all[j]]=[all[j],all[i]];}indices=all.slice(0,n);}
 const selected=new Set(indices),train=rows.filter((_,i)=>!selected.has(i)),test=rows.filter((_,i)=>selected.has(i));
 return{method,fraction,seed,train,test,trainingRowIds:train.map(r=>r.row),heldOutRowIds:test.map(r=>r.row),warning:'Holdout observations never enter fitting. Repeated tuning against this holdout makes it part of model selection; use independent data for a final assessment. Split is by observation, not by experiment or laboratory. Upper-x tests extrapolation in composition.'};
}
export function validateVLE(set,options={},progress=()=>{}){
 const split=splitVLE(set,options),results=[];
 for(const model of ['margules1','margules2','nrtl']){try{const fit=fitVLE({...set,valid:split.train},{model,alpha:options.alpha??.3,temperatureDependent:false}),training=evaluate(split.train,fit),heldOut=evaluate(split.test,fit);results.push({model,fit,training:metrics(training),validation:metrics(heldOut),trainingPredictions:training,heldOutPredictions:heldOut});}catch(e){results.push({model,unavailable:e.message});}progress(results.length,3);}
 return{kind:'vle-validation',split,results,assumptions:'Same split and constant dimensionless parameters for all three models; fixed NRTL alpha. Ideal vapor, original Antoine properties and unweighted fitting objective. No automatic claim of a winning model.'};
}
function options(o){const count=o.count??40,seed=o.seed??42;if(!Number.isInteger(count)||count<30||count>200)throw new Error('Use 30–200 bootstrap resamples. Small resample counts give rough percentile estimates.');return{count,seed,rand:random(seed)};}
export function bootstrapVLE(set,fitOptions={},o={},progress=()=>{}){
 const {count,seed,rand}=options(o),base=fitVLE(set,fitOptions),samples=[],failures=[];let bounds=0;
 for(let b=0;b<count;b++){try{const rows=set.valid.map(()=>set.valid[Math.floor(rand()*set.valid.length)]);if(new Set(rows.map(r=>r.x)).size<base.parameters.length+2)throw new Error('Insufficient distinct sampled compositions.');const fit=fitVLE({...set,valid:rows},fitOptions);if(fit.atBound)bounds++;samples.push({parameters:fit.parameters,atBound:fit.atBound,predictions:evaluate(set.valid,fit).map(r=>({Pcalc:r.Pcalc,ycalc:r.ycalc}))});}catch(e){failures.push({replicate:b+1,reason:e.message});}progress(b+1,count);}
 const enough=samples.length>=Math.max(20,Math.ceil(.8*count));
 return{kind:'vle-bootstrap',count,seed,base,successful:samples.length,failures,boundFits:bounds,samples,parameters:enough?base.parameterNames.map((name,i)=>({name,...interval(samples.map(s=>s.parameters[i]))})):null,band:enough?set.valid.map((r,i)=>({row:r.row,T:r.T,x:r.x,P:interval(samples.map(s=>s.predictions[i].Pcalc)),y:interval(samples.map(s=>s.predictions[i].ycalc))})):null,unavailable:enough?null:'Fewer than 80% or 20 successful resamples; no interval is reported.',method:'Seeded pairs bootstrap of the full imported interior observations, refitting each sample. 95% pointwise percentile fit-spread intervals, conditional on the model, fixed alpha and supplied pure-component properties. Not simultaneous bands or new-observation prediction intervals. Correlated/systematic measurement error and model discrepancy are excluded. Exact synthetic data can give degenerate intervals; that does not imply physical certainty.'};
}
export function bootstrapLLE(rows,fitOptions={},o={},progress=()=>{}){
 validateRows(rows);if(rows.length<4)throw new Error('At least four independent replicate tie-line pairs at one temperature are required. A single tie line cannot supply an empirical bootstrap distribution.');
 const {count,seed,rand}=options(o),base=fitLLE(rows,{...fitOptions,multistart:true}),samples=[],failures=[];let bounds=0;
 for(let b=0;b<count;b++){try{const sample=rows.map(()=>rows[Math.floor(rand()*rows.length)]),fit=fitLLE(sample,{...fitOptions,multistart:true});if(!fit.converged||!fit.diagnostics.resolved||!fit.diagnostics.binodal)throw new Error('No converged, globally supported coexistence branch.');if(fit.atBound)bounds++;samples.push({tau12:fit.parameters.tau12,tau21:fit.parameters.tau21,xAlpha:fit.diagnostics.binodal.xAlpha,xBeta:fit.diagnostics.binodal.xBeta,atBound:fit.atBound});}catch(e){failures.push({replicate:b+1,reason:e.message});}progress(b+1,count);}
 const enough=samples.length>=Math.max(20,Math.ceil(.8*count));
 return{kind:'lle-bootstrap',count,seed,base,successful:samples.length,failures,boundFits:bounds,samples,intervals:enough?['tau12','tau21','xAlpha','xBeta'].map(name=>({name,...interval(samples.map(s=>s[name]))})):null,unavailable:enough?null:'Fewer than 80% or 20 supported fits; no interval is reported.',method:'Seeded paired bootstrap of complete (xAlpha,xBeta) replicate pairs, preserving within-pair association. Fixed T and alpha; bounded multistart fitting and global coexistence verification per resample. 95% marginal percentile fit-spread intervals conditional on the model. Replicates do not add distinct equilibrium states; intervals exclude uncertainty in alpha, systematic error and model discrepancy. Identical replicates yield degenerate spread, not certainty.'};
}
