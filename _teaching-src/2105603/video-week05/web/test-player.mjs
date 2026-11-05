/** Week5 controller verification with mocked DOM/media events; not browser/decoded-video QA. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(here,'../..');
const args=process.argv.slice(2);
function opt(flag,fallback){const i=args.indexOf(flag);return i<0?fallback:path.resolve(args[i+1]);}
const manifestPath=opt('--manifest',path.join(root,'outputs/week05-video/audio/manifest.json'));
const timelinePath=opt('--timeline',path.join(root,'outputs/week05-video/timeline.json'));
const fixture=args.includes('--fixture');
const contract=JSON.parse(fs.readFileSync(path.join(here,'../documents/lesson-contract.json'),'utf8'));
let manifest,timeline,mode;
if(fixture){
  manifest=contract.slides.map(c=>({slide:c.number,slide_id:c.id,title:c.title,narration:'Synthetic controller fixture; not teaching narration.',activity:c.pause_minutes>0,activity_minutes:c.pause_minutes,pause_instruction:c.pause_minutes?'Complete the fixture worksheet activity.':''}));
  timeline=manifest.map((m,i)=>({...m,start_seconds:i*20,end_seconds:(i+1)*20,narration_end_seconds:(i+1)*20-2}));
  mode='SYNTHETIC 20-second timing fixtures; mocked DOM/media. No browser or decoded-media QA.';
}else{
  manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));const raw=JSON.parse(fs.readFileSync(timelinePath,'utf8'));timeline=raw.slides??raw.chapters??raw.timeline;
  assert.match(raw.video_sha256,/^[0-9a-f]{64}$/);mode='Actual final media timing metadata; mocked DOM/media. No browser or decoded-media QA.';
}
const result=spawnSync(path.join(os.homedir(),'.venvs/research/bin/python'),['-c','import json,runpy,sys; d=json.load(sys.stdin); b=runpy.run_path(sys.argv[1]); print(json.dumps(b["prepare_rows"](d["contract"],d["manifest"],d["timeline"])))',path.join(here,'build-video-page.py')],{input:JSON.stringify({contract,manifest,timeline}),encoding:'utf8',maxBuffer:1024*1024});
assert.equal(result.status,0,result.stderr);
const chapters=JSON.parse(result.stdout),script=fs.readFileSync(path.join(here,'player.js'),'utf8'),template=fs.readFileSync(path.join(here,'video-template.html'),'utf8');
const guards=chapters.filter(c=>c.activity),tests=[];
class Element{
  constructor(id){this.id=id;this.textContent='';this.hidden=false;this.disabled=false;this.checked=false;this.dataset={};this.listeners=new Map();this.attributes=new Map();this.scrolls=[];}
  addEventListener(t,f,o){const a=this.listeners.get(t)||[];a.push({f,once:o?.once});this.listeners.set(t,a);}
  removeEventListener(t,f){this.listeners.set(t,(this.listeners.get(t)||[]).filter(x=>x.f!==f));}
  emit(t,extra={}){for(const x of [...(this.listeners.get(t)||[])]){x.f({type:t,target:this,preventDefault(){},...extra});if(x.once)this.removeEventListener(t,x.f);}}
  click(){if(!this.disabled)this.emit('click');}
  setAttribute(n,v){this.attributes.set(n,String(v));}removeAttribute(n){this.attributes.delete(n);}getAttribute(n){return this.attributes.get(n)??null;}scrollIntoView(o){this.scrolls.push(o);}
}
function harness({narrow=false,delayedTrack=false,hash='',saved=null,blockStorage=false}={}){
  const queue=[],timers=new Map(),frames=new Map(),downloads=[],storage=new Map();let serial=0;
  const key='thermo-week05-test-version';if(saved)storage.set(key,JSON.stringify(saved));
  const elements=new Map([...template.matchAll(/\bid="([^"]+)"/g)].map(m=>[m[1],new Element(m[1])]));
  const el=id=>{assert.ok(elements.has(id),`Unknown element ${id}`);return elements.get(id);};
  const links=chapters.map(c=>new Element('chapter-'+c.slide));
  const jumps=[1,20,22,30].map(n=>{const a=new Element('jump-'+n);a.dataset.jump=String(n);return a;});
  class Media extends Element{
    constructor(){super('lesson-video');this._time=0;this.paused=true;this.seeking=false;this.playbackRate=1;this.readyState=4;this.duration=chapters.at(-1).end;}
    get currentTime(){return this._time;}set currentTime(x){assert.ok(Number.isFinite(x));this._time=x;this.seeking=true;queue.push(()=>this.emit('seeking'));queue.push(()=>{this.seeking=false;this.emit('seeked');});}
    play(){if(this.paused){this.paused=false;this.emit('play');}return Promise.resolve();}pause(){if(!this.paused){this.paused=true;this.emit('pause');}}
  }
  const video=new Media();elements.set('lesson-video',video);
  const trackEvents=new Element('tracks'),tracks=[];tracks.addEventListener=trackEvents.addEventListener.bind(trackEvents);video.textTracks=tracks;
  class Track extends Element{constructor(){super('track');this._mode='disabled';this.activeCues=[];}get mode(){return this._mode;}set mode(x){if(this._mode!==x){this._mode=x;queue.push(()=>trackEvents.emit('change'));}}}
  const track=new Track();if(!delayedTrack){tracks.push(track);el('english-caption-track').track=track;}
  el('chapter-data').textContent=JSON.stringify(chapters);el('chapter-data').dataset.version='test-version';el('auto-pause').checked=true;el('captions-enabled').checked=true;el('pause-panel').hidden=true;el('resume-panel').hidden=true;el('video-error').hidden=true;
  const document=new Element('document');document.hidden=false;document.fullscreenElement=null;document.getElementById=el;document.querySelectorAll=q=>q==='.chapter'?links:q==='[data-jump]'?jumps:assert.fail('Unexpected selector');document.createElement=t=>new Element(t);document.exitFullscreen=async()=>{};
  const location={hash},history={replaceState(a,b,h){location.hash=h;}};
  const mq=new Element('mq');mq.matches=narrow;const window=new Element('window');window.matchMedia=q=>q==='(max-width: 900px)'?mq:{matches:true};
  const localStorage={getItem(k){if(blockStorage)throw Error('blocked');return storage.get(k)||null;},setItem(k,v){if(blockStorage)throw Error('blocked');storage.set(k,v);}};
  const context={document,window,history,location,localStorage,Blob,URL:{createObjectURL(b){downloads.push(b);return'blob:test';},revokeObjectURL(){}},setTimeout(f,d){const i=++serial;timers.set(i,{f,d});return i;},clearTimeout(i){timers.delete(i);},requestAnimationFrame(f){const i=++serial;frames.set(i,f);return i;},cancelAnimationFrame(i){frames.delete(i);},console};
  vm.runInNewContext(script,context,{timeout:1000,filename:'Week5-player.js'});
  async function settle(){for(let i=0;i<30;i++){while(queue.length)queue.shift()();await Promise.resolve();if(!queue.length)return;}throw Error('Unsettled queue');}
  async function jump(n){links[n-1].click();await settle();}
  async function play(){await video.play();await settle();}
  async function advance(t,kind='timeupdate'){assert.equal(video.paused,false);video._time=t;if(kind==='frame'){const a=frames.entries().next().value;assert.ok(a);frames.delete(a[0]);a[1]();}else if(kind==='timer'){const a=timers.entries().next().value;assert.ok(a);timers.delete(a[0]);a[1].f();}else video.emit(kind);await settle();}
  async function click(id){el(id).click();await settle();}
  return {el,video,links,jumps,document,window,location,track,storage,key,downloads,settle,jump,play,advance,click,queue,frames,timers,async manualSeek(t){video.currentTime=t;await settle();},toggle(v){el('auto-pause').checked=v;el('auto-pause').emit('change');},resize(v){mq.matches=v;window.emit('resize');mq.emit('change');},loadTrack(){tracks.push(track);el('english-caption-track').track=track;trackEvents.emit('addtrack');el('english-caption-track').emit('load');}};
}
async function check(name,fn){await fn();tests.push({name,pass:true});}
await check('32 chapters and contract budgets',()=>{assert.equal(chapters.length,32);assert.equal(chapters.reduce((a,c)=>a+c.activity_minutes,0),138);assert.deepEqual(chapters.filter(c=>c.is_demo).map(c=>c.slide),[20,22,30]);});
await check('every required stop guards before next slide and continues manually',async()=>{for(const g of guards){const h=harness();await h.jump(g.slide);await h.play();await h.advance(g.end+.15);assert.equal(h.video.paused,true);assert.equal(h.el('pause-panel').hidden,false);assert.equal(h.el('slide-counter').textContent,`Slide ${g.slide} of 32`);assert.ok(Math.abs(h.video.currentTime-(g.end-.24))<.01);await h.click('continue-button');assert.equal(h.el('pause-panel').hidden,true);if(g.slide<32){assert.equal(h.video.paused,false);assert.ok(Math.abs(h.video.currentTime-chapters[g.slide].start-.025)<.01);}else assert.equal(h.video.paused,true);}});
await check('solution does not play while a work stop is active',async()=>{const h=harness(),g=guards[0];await h.jump(g.slide);await h.play();await h.advance(g.end);await h.play();assert.equal(h.video.paused,true);});
await check('intentional chapter seek skips preceding activities without acknowledging them',async()=>{const h=harness();await h.jump(20);assert.equal(h.el('pause-panel').hidden,true);assert.equal(h.el('lesson-progress').value,0);assert.equal(h.location.hash,'#slide-20');});
await check('demo shortcuts select20,22,30',async()=>{const h=harness();for(const n of [20,22,30]){h.jumps.find(x=>x.dataset.jump===String(n)).click();await h.settle();assert.equal(h.el('slide-counter').textContent,`Slide ${n} of 32`);}});
await check('manual seek remains usable during activity pause',async()=>{const h=harness(),g=guards[0];await h.jump(g.slide);await h.play();await h.advance(g.end);await h.manualSeek(chapters[19].start+.1);assert.equal(h.el('pause-panel').hidden,true);assert.equal(h.el('slide-counter').textContent,'Slide 20 of 32');});
await check('guard works with requestAnimationFrame',async()=>{const h=harness(),g=guards[0];await h.jump(g.slide);await h.play();await h.advance(g.end-.23,'frame');assert.equal(h.video.paused,true);});
await check('guard works after playback-rate change',async()=>{const h=harness(),g=guards[0];await h.jump(g.slide);h.video.playbackRate=2;h.video.emit('ratechange');await h.play();await h.advance(g.end-.23,'timer');assert.equal(h.video.paused,true);});
await check('disabled auto-pause allows uninterrupted playback',async()=>{const h=harness(),g=guards[0];h.toggle(false);await h.jump(g.slide);await h.play();await h.advance(g.end+.1);assert.equal(h.video.paused,false);assert.equal(h.el('pause-panel').hidden,true);});
await check('backward review can pause again without erasing checklist',async()=>{const h=harness(),g=guards[0];await h.jump(g.slide);await h.play();await h.advance(g.end);await h.click('continue-button');assert.equal(h.el('lesson-progress').value,1);await h.jump(g.slide);await h.play();await h.advance(g.end);assert.equal(h.video.paused,true);assert.equal(h.el('lesson-progress').value,1);});
await check('metadata deep link uses slide anchor',async()=>{const h=harness({hash:'#slide-30'});h.video.emit('loadedmetadata');await h.settle();assert.equal(h.el('slide-counter').textContent,'Slide 30 of 32');});
await check('metadata accepts descriptive slide ID',async()=>{const h=harness({hash:'#'+chapters[19].slide_id});h.video.emit('loadedmetadata');await h.settle();assert.equal(h.el('slide-counter').textContent,'Slide 20 of 32');});
await check('resume preserves active attempt before answer',async()=>{const g=guards[0],saved={time:g.end-.24,completed:[],acknowledged:[],pending:g.slide,autoPause:true,captions:true};const h=harness({saved});assert.equal(h.el('resume-panel').hidden,false);await h.click('resume-button');assert.equal(h.el('pause-panel').hidden,false);assert.equal(h.video.paused,true);assert.equal(h.el('slide-counter').textContent,`Slide ${g.slide} of 32`);});
await check('resume restores acknowledged checklist',async()=>{const g=guards[0],saved={time:chapters[19].start+2,completed:[g.slide],acknowledged:[g.slide],pending:null,autoPause:true,captions:false};const h=harness({saved});await h.click('resume-button');assert.equal(h.el('lesson-progress').value,1);assert.equal(h.el('captions-enabled').checked,false);assert.equal(h.video.paused,true);});
await check('loading and leaving page does not erase unused saved place',async()=>{const saved={time:chapters[19].start+2,completed:[],acknowledged:[],pending:null};const h=harness({saved});h.window.emit('pagehide');assert.deepEqual(JSON.parse(h.storage.get(h.key)),saved);});
await check('restart clears saved completion and returns to first slide',async()=>{const g=guards[0];const h=harness({saved:{time:chapters[19].start+2,completed:[g.slide],acknowledged:[g.slide],pending:null}});await h.click('resume-button');await h.click('restart-button');assert.equal(h.el('lesson-progress').value,0);assert.equal(h.el('slide-counter').textContent,'Slide 1 of 32');assert.equal(h.video.paused,true);});
await check('blocked local storage does not break playback',async()=>{const h=harness({blockStorage:true});await h.jump(20);await h.play();assert.equal(h.video.paused,false);});
await check('wide screen uses native English captions',async()=>{const h=harness();await h.settle();assert.equal(h.track.mode,'showing');assert.equal(h.el('responsive-captions').hidden,true);});
await check('narrow screen places timed captions below image',async()=>{const h=harness({narrow:true});await h.settle();h.track.activeCues=[{text:'Independent equations and balance.'}];h.track.emit('cuechange');assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-captions').hidden,false);assert.equal(h.el('responsive-caption-text').textContent,'Independent equations and balance.');});
await check('caption toggle disables and reenables track',async()=>{const h=harness({narrow:true});h.el('captions-enabled').checked=false;h.el('captions-enabled').emit('change');await h.settle();assert.equal(h.track.mode,'disabled');assert.equal(h.el('responsive-captions').hidden,true);h.el('captions-enabled').checked=true;h.el('captions-enabled').emit('change');await h.settle();assert.equal(h.track.mode,'hidden');});
await check('delayed caption load attaches track',async()=>{const h=harness({narrow:true,delayedTrack:true});h.loadTrack();await h.settle();assert.equal(h.track.mode,'hidden');});
await check('caption load failure provides transcript fallback',async()=>{const h=harness({narrow:true});h.el('english-caption-track').emit('error');assert.match(h.el('responsive-caption-text').textContent,/transcript/);});
await check('video load failure shows useful fallback',async()=>{const h=harness();h.video.emit('error');assert.equal(h.el('video-error').hidden,false);});
await check('transcript download includes all32chapters and correct week',async()=>{const h=harness();await h.click('download-transcript');assert.equal(h.downloads.length,1);const txt=await h.downloads[0].text();assert.match(txt,/Week 5/);assert.match(txt,/128 minutes/);assert.equal((txt.match(/SLIDE \d+:/g)||[]).length,32);assert.doesNotMatch(txt,/Week 4: Questions|H1/);});
const output=opt('--output',path.join(here,fixture?'fixture-controller-qa.json':'controller-qa.json'));
fs.writeFileSync(output,JSON.stringify({mode,passed:tests.length,failed:0,checks:tests},null,2)+'\n');console.log(JSON.stringify({output,mode,passed:tests.length,failed:0},null,2));
