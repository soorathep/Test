/** Lab 01 controller tests. Fake DOM/media events are not browser or encoded-media QA.
 * Use --fixture for synthetic timings or --require-media-timeline for actual metadata.
 * Invoke through an absolute Node interpreter. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';

const here=path.dirname(fileURLToPath(import.meta.url));
const root=path.dirname(here);
const args=new Set(process.argv.slice(2));
const python=path.join(os.homedir(),'.venvs/research/bin/python');
const builder=path.join(here,'build-video-page.py');
const artifactRoot=path.join(root,'outputs/lab01-video');
const fixtureDir=path.join(artifactRoot,'controller-fixtures');
fs.mkdirSync(fixtureDir,{recursive:true});
const actualManifest=path.join(artifactRoot,'audio/manifest.json');
const actualTimeline=path.join(artifactRoot,'timeline.json');
const pauses={3:2,13:5};
let manifestPath,timelinePath,mode;
if(!args.has('--fixture')&&fs.existsSync(actualManifest)&&fs.existsSync(actualTimeline)){
  manifestPath=actualManifest;timelinePath=actualTimeline;
  mode='actual timing metadata; mocked media events, no encoded-media or browser QA';
}else{
  assert.ok(!args.has('--require-media-timeline'),'Final manifest/timeline required but unavailable.');
  manifestPath=path.join(fixtureDir,'manifest.json');timelinePath=path.join(fixtureDir,'timeline.json');
  const manifest=Array.from({length:14},(_,i)=>({id:String(i+1).padStart(2,'0'),slide:i+1,
    title:`Fixture chapter ${i+1}`,narration:'Synthetic controller fixture, not a final narration script.',
    activity:(i+1) in pauses,activity_minutes:pauses[i+1]??0,
    pause_instruction:(i+1) in pauses?'Try the fixture calculation before viewing the check.':'Follow the fixture screen.'}));
  fs.writeFileSync(manifestPath,JSON.stringify(manifest));
  fs.writeFileSync(timelinePath,JSON.stringify({duration_seconds:280,slides:manifest.map((m,i)=>({
    slide:m.slide,title:m.title,start_seconds:i*20,narration_end_seconds:(i+1)*20-2,end_seconds:(i+1)*20,activity:m.activity}))}));
  mode='SYNTHETIC TIMING FIXTURE: 14 chapters of 20 seconds, control flow only; no actual media claims';
}
const extractCode='import json,runpy,sys; m=runpy.run_path(sys.argv[1]); from pathlib import Path; rows=m["load_rows"](Path(sys.argv[2]),Path(sys.argv[3])); print(json.dumps({"script":m["PLAYER_SCRIPT"],"template":m["TEMPLATE"],"chapters":rows}))';
const extraction=spawnSync(python,['-c',extractCode,builder,manifestPath,timelinePath],{encoding:'utf8',maxBuffer:2**20});
assert.equal(extraction.status,0,extraction.stderr);
const {script,template,chapters}=JSON.parse(extraction.stdout);
assert.equal(chapters.length,14);
assert.deepEqual(chapters.filter(c=>c.activity).map(c=>[c.chapter,c.activity_minutes]),[[3,2],[13,5]]);
const build=spawnSync(python,[builder,'--manifest',manifestPath,'--timeline',timelinePath,'--output',path.join(fixtureDir,'page.html')],{encoding:'utf8'});
assert.equal(build.status,0,build.stderr);
const rendered=fs.readFileSync(path.join(fixtureDir,'page.html'),'utf8');
class Element {
  constructor(id){this.id=id;this.textContent='';this.hidden=false;this.disabled=false;this.checked=false;this.listeners=new Map();this.attributes=new Map();this.scrolls=[];}
  addEventListener(type,fn){const list=this.listeners.get(type)||[];list.push(fn);this.listeners.set(type,list);}
  removeEventListener(type,fn){this.listeners.set(type,(this.listeners.get(type)||[]).filter(item=>item!==fn));}
  emit(type,extra={}){for(const fn of this.listeners.get(type)||[])fn({type,target:this,preventDefault(){},...extra});}
  click(){if(!this.disabled)this.emit('click');}
  setAttribute(name,value){this.attributes.set(name,String(value));}
  removeAttribute(name){this.attributes.delete(name);}
  getAttribute(name){return this.attributes.get(name)??null;}
  scrollIntoView(options){this.scrolls.push(options);}
}
function harness({narrow=false,delayedTrack=false,records=chapters}={}){
  const chapters=records;
  const downloads=[];
  const queue=[];const timers=new Map();const frames=new Map();let serial=0;
  const ids=[...template.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
  const elements=new Map(ids.map(id=>[id,new Element(id)]));
  const el=id=>{assert.ok(elements.has(id),`Unknown DOM id: ${id}`);return elements.get(id);};
  const links=chapters.map(c=>new Element(`chapter-${c.chapter}`));
  class Media extends Element {
    constructor(){super('lesson-video');this._time=0;this.paused=true;this.seeking=false;this.playbackRate=1;this.duration=chapters.at(-1).end;}
    get currentTime(){return this._time;}
    set currentTime(value){
      assert.ok(Number.isFinite(value));this._time=value;this.seeking=true;
      queue.push(()=>this.emit('seeking'));
      queue.push(()=>{this.seeking=false;this.emit('seeked');});
    }
    play(){if(this.paused){this.paused=false;this.emit('play');}return Promise.resolve();}
    pause(){if(!this.paused){this.paused=true;this.emit('pause');}}
  }
  const video=new Media();elements.set('lesson-video',video);
  const trackEvents=new Element('textTracks');
  const textTracks=[];
  textTracks.addEventListener=trackEvents.addEventListener.bind(trackEvents);
  class CaptionTrack extends Element {
    constructor(){super('english-text-track');this._mode='disabled';this.activeCues=[];}
    get mode(){return this._mode;}
    set mode(value){if(this._mode!==value){this._mode=value;queue.push(()=>trackEvents.emit('change'));}}
  }
  const track=new CaptionTrack();
  video.textTracks=textTracks;
  if(!delayedTrack){textTracks.push(track);el('english-caption-track').track=track;}
  el('chapter-data').textContent=JSON.stringify(chapters);
  el('auto-pause').checked=/<input\b[^>]*id="auto-pause"[^>]*\bchecked\b/.test(template);
  el('captions-enabled').checked=/<input\b[^>]*id="captions-enabled"[^>]*\bchecked\b/.test(template);
  el('pause-panel').hidden=true;el('video-error').hidden=true;
  const document=new Element('document');document.hidden=false;document.fullscreenElement=null;
  document.getElementById=el;document.querySelectorAll=selector=>{assert.equal(selector,'.chapter');return links;};
  document.createElement=tag=>new Element(tag);document.exitFullscreen=async()=>{};
  const location={hash:''};const history={replaceState(_a,_b,hash){location.hash=hash;}};
  const captionMedia=new Element('narrow-caption-query');captionMedia.matches=narrow;
  const window=new Element('window');window.matchMedia=query=>query==='(max-width: 900px)'?captionMedia:{matches:true};
  const context={document,window,history,location,
    setTimeout(fn,delay){const id=++serial;timers.set(id,{fn,delay});return id;},clearTimeout(id){timers.delete(id);},
    requestAnimationFrame(fn){const id=++serial;frames.set(id,fn);return id;},cancelAnimationFrame(id){frames.delete(id);},
    Blob,URL:{createObjectURL(blob){downloads.push(blob);return 'blob:test-controller';},revokeObjectURL(){}},console};
  vm.runInNewContext(script,context,{filename:'Lab01_PLAYER_SCRIPT.js',timeout:1000});
  async function settle(){for(let i=0;i<30;i++){while(queue.length)queue.shift()();await Promise.resolve();if(!queue.length)return;}throw new Error('Event queue failed to settle.');}
  async function jump(chapter){links[chapter-1].click();await settle();}
  async function play(){await video.play();await settle();}
  async function advance(time,event='timeupdate'){
    assert.equal(video.paused,false,'Natural playback advance requires playing media');video._time=time;
    if(event==='frame'){
      const entry=frames.entries().next().value;assert.ok(entry,'No scheduled animation frame');frames.delete(entry[0]);entry[1]();
    }else if(event==='timer'){
      const entry=timers.entries().next().value;assert.ok(entry,'No scheduled guard timer');timers.delete(entry[0]);entry[1].fn();
    }else video.emit(event);
    await settle();
  }
  async function manualSeek(time){video.currentTime=time;await settle();}
  async function continueActivity(){el('continue-button').click();await settle();}
  function toggle(value){el('auto-pause').checked=value;el('auto-pause').emit('change');}
  function resizeCaptionLayout(isNarrow){captionMedia.matches=isNarrow;window.emit('resize');captionMedia.emit('change');}
  function loadTrack(){textTracks.push(track);el('english-caption-track').track=track;trackEvents.emit('addtrack');el('english-caption-track').emit('load');}
  function setCues(texts){track.activeCues=texts.map(text=>({text}));track.emit('cuechange');}
  return {el,video,links,jump,play,advance,settle,manualSeek,continueActivity,toggle,timers,frames,track,document,location,resizeCaptionLayout,loadTrack,setCues,downloads};
}
const tests=[];
async function test(name,fn){await fn();tests.push({name,status:'passed'});console.log(`PASS ${name}`);}
function near(actual,expected){assert.ok(Math.abs(actual-expected)<1e-7,`${actual} != ${expected}`);}
function checkPause(h,chapter){
  const c=chapters[chapter-1];assert.equal(h.video.paused,true);assert.equal(h.el('pause-panel').hidden,false);
  assert.equal(h.el('chapter-counter').textContent,`Chapter ${chapter} of ${chapters.length}`);
  assert.equal(h.el('pause-cue').textContent,c.cue);
  assert.ok(h.video.currentTime<c.end,`Activity ${chapter} crossed into its successor`);
  assert.equal(h.links[chapter-1].getAttribute('aria-current'),'true');
  if(chapter<chapters.length)assert.equal(h.links[chapter].getAttribute('aria-current'),null);
}

await test('The page is a Week 1 supplement with actual duration and no repeat submission',async()=>{
  assert.match(rendered,/Week 1 · Supplemental Lab demonstration/);
  assert.match(rendered,/No repeat exit-ticket or feedback submission is needed/);
  for(const stale of ['Week 4','Session 4','Lab 10','Lab 11','180 min','three-hour','ECS','#slide-']) assert.ok(!rendered.includes(stale),`Stale content: ${stale}`);
  for(const href of ['files/week01-lab-guide.pdf','files/lab01-demo-comparison.json','labs/#experiment','postmidterm-01.html','labs/learning-path.html#session-1','media/lab01/lab01-demo.mp4','media/lab01/lab01-captions.vtt','media/lab01/lab01-poster.png']) assert.ok(rendered.includes(href),href);
  assert.match(rendered,/about <strong>7 minutes/);
  assert.match(rendered,/predict the two new pressure cases/);assert.ok(!rendered.includes('before the first results'));
  assert.match(rendered,/Save your own comparison JSON/);
  assert.equal((rendered.match(/<a class="chapter"/g)||[]).length,14);
  assert.equal((rendered.match(/<span class="activity-dot">Optional pause/g)||[]).length,2);
});
await test('Default optional pauses preserve chapters 3 and 13 until Continue',async()=>{
  for(const chapter of [3,13]){
    const h=harness();assert.equal(h.el('auto-pause').checked,true);await h.jump(chapter);await h.play();
    await h.advance(chapters[chapter-1].end-.24);checkPause(h,chapter);await h.play();checkPause(h,chapter);
    assert.equal(h.el('continue-button').textContent,'Continue to next chapter');
    assert.match(h.el('pause-budget').textContent,/Optional practice:/);
  }
});
await test('Continue moves from the prediction to chapter 4 and from the attempt to check 14',async()=>{
  for(const chapter of [3,13]){
    const h=harness();await h.jump(chapter);await h.play();await h.advance(chapters[chapter-1].end-.24);
    await h.continueActivity();assert.equal(h.el('pause-panel').hidden,true);assert.equal(h.video.paused,false);
    near(h.video.currentTime,chapters[chapter].start+.025);
    assert.equal(h.el('chapter-counter').textContent,`Chapter ${chapter+1} of 14`);
  }
});
await test('A delayed playback event rewinds to the attempt before showing its check',async()=>{
  const h=harness();await h.jump(13);await h.play();await h.advance(chapters[13].start+.12);
  checkPause(h,13);near(h.video.currentTime,chapters[12].end-.24);
});
await test('Timer and animation-frame guards hold practice without a timeupdate event',async()=>{
  for(const event of ['timer','frame']){
    const h=harness();await h.jump(13);await h.play();await h.advance(chapters[12].end-.24,event);checkPause(h,13);
  }
});
await test('Intentional chapter and native seeks do not trigger skipped optional pauses',async()=>{
  const h=harness();await h.play();await h.jump(8);await h.advance(chapters[7].start+.5);
  assert.equal(h.video.paused,false);assert.equal(h.el('pause-panel').hidden,true);
  await h.manualSeek(chapters[11].start+.5);await h.advance(chapters[11].start+1);
  assert.equal(h.el('pause-panel').hidden,true);assert.equal(h.el('chapter-counter').textContent,'Chapter 12 of 14');
});
await test('Replaying a completed practice checkpoint reinstates its pause',async()=>{
  const h=harness();await h.jump(3);await h.play();await h.advance(chapters[2].end-.24);await h.continueActivity();
  await h.jump(3);await h.advance(chapters[2].end-.24);checkPause(h,3);
});
await test('Turning optional pauses off clears a held pause and permits continuous playback',async()=>{
  const h=harness();await h.jump(3);await h.play();await h.advance(chapters[2].end-.24);checkPause(h,3);
  h.toggle(false);assert.equal(h.el('pause-panel').hidden,true);await h.play();await h.advance(chapters[3].start+.3);
  assert.equal(h.video.paused,false);assert.equal(h.el('chapter-counter').textContent,'Chapter 4 of 14');
  h.video.pause();h.toggle(true);await h.jump(13);await h.play();await h.advance(chapters[12].end-.24);checkPause(h,13);
});
await test('A late natural end still catches an unfinished attempt; a final-check seek does not',async()=>{
  const h=harness();await h.jump(13);await h.play();h.video._time=chapters.at(-1).end;h.video.paused=true;
  h.video.emit('ended');await h.settle();checkPause(h,13);
  const j=harness();await j.jump(14);await j.play();j.video._time=chapters.at(-1).end;j.video.paused=true;
  j.video.emit('ended');await j.settle();assert.equal(j.el('pause-panel').hidden,true);
});
await test('All labels and downloadable transcripts describe demonstration chapters',async()=>{
  const h=harness();for(const chapter of [1,3,8,13,14]){
    await h.jump(chapter);
    assert.equal(h.el('chapter-counter').textContent,`Chapter ${chapter} of 14`);
    assert.equal(h.el('lesson-time').textContent,chapters[chapter-1].activity?'Optional practice checkpoint':'Week 1 supplemental demonstration');
    assert.equal(h.el('transcript-title').textContent,`Transcript · Chapter ${chapter}`);
  }
  h.el('download-transcript').click();const text=await h.downloads.at(-1).text();
  assert.match(text,/Lab 01: Ideal VLE/);assert.match(text,/CHAPTER 14:/);assert.match(text,/No repeat submission is needed/);
  assert.ok(!text.includes('Week 4'));assert.ok(!text.includes('SLIDE'));
});
await test('Deep links and Previous/Next use exact chapter starts',async()=>{
  const h=harness();h.location.hash='#chapter-8';h.video.emit('loadedmetadata');await h.settle();
  near(h.video.currentTime,chapters[7].start+.025);assert.equal(h.el('chapter-counter').textContent,'Chapter 8 of 14');
  h.el('next-button').click();await h.settle();near(h.video.currentTime,chapters[8].start+.025);
  h.el('previous-button').click();await h.settle();near(h.video.currentTime,chapters[7].start+.025);
  await h.jump(1);assert.equal(h.el('previous-button').disabled,true);await h.jump(14);assert.equal(h.el('next-button').disabled,true);
  assert.match(script,/#chapter-\$\{c.chapter\}/);assert.match(script,/\^#chapter-/);
});
await test('Wide captions stay native; narrow captions use timed text below the image',async()=>{
  const h=harness();await h.settle();assert.equal(h.track.mode,'showing');assert.equal(h.el('responsive-captions').hidden,true);
  h.resizeCaptionLayout(true);await h.settle();assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-captions').hidden,false);
  h.setCues(['First line\ncontinues.','Second sentence.']);assert.equal(h.el('responsive-caption-text').textContent,'First line continues. Second sentence.');
  assert.equal(h.el('video-stage').getAttribute('data-captions-below'),'true');
  h.setCues([]);assert.equal(h.el('responsive-caption-text').textContent,'');
  h.resizeCaptionLayout(false);await h.settle();assert.equal(h.track.mode,'showing');assert.equal(h.el('responsive-captions').hidden,true);
});
await test('Caption toggle disables both formats without duplicate mobile captions',async()=>{
  const h=harness({narrow:true});await h.settle();h.setCues(['An active sentence.']);
  h.el('captions-enabled').checked=false;h.el('captions-enabled').emit('change');await h.settle();
  assert.equal(h.track.mode,'disabled');assert.equal(h.el('responsive-captions').hidden,true);assert.equal(h.el('responsive-caption-text').textContent,'');
  h.el('captions-enabled').checked=true;h.el('captions-enabled').emit('change');await h.settle();
  assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-caption-text').textContent,'An active sentence.');
  h.track.mode='showing';await h.settle();assert.equal(h.track.mode,'hidden');
});
await test('Native video full screen uses native captions; wrapper full screen keeps captions below',async()=>{
  const h=harness({narrow:true});await h.settle();h.setCues(['Current sentence.']);
  h.document.fullscreenElement=h.el('video-stage');h.document.emit('fullscreenchange');await h.settle();
  assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-captions').hidden,false);
  h.document.fullscreenElement=h.video;h.document.emit('fullscreenchange');await h.settle();
  assert.equal(h.track.mode,'showing');assert.equal(h.el('responsive-captions').hidden,true);
  h.document.fullscreenElement=null;h.document.emit('fullscreenchange');await h.settle();assert.equal(h.track.mode,'hidden');
  h.video.emit('webkitbeginfullscreen');await h.settle();assert.equal(h.track.mode,'showing');
  h.video.emit('webkitendfullscreen');await h.settle();assert.equal(h.track.mode,'hidden');
});
await test('Late caption loading attaches cue updates and desktop CC updates the toggle',async()=>{
  const h=harness({narrow:true,delayedTrack:true});await h.settle();h.loadTrack();await h.settle();h.setCues(['Late loaded cue.']);
  assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-caption-text').textContent,'Late loaded cue.');
  h.resizeCaptionLayout(false);await h.settle();h.track.mode='disabled';await h.settle();assert.equal(h.el('captions-enabled').checked,false);
  h.track.mode='showing';await h.settle();assert.equal(h.el('captions-enabled').checked,true);
});
await test('Caption and video load failures provide readable fallbacks',async()=>{
  const h=harness({narrow:true});await h.settle();h.el('english-caption-track').emit('error');await h.settle();
  assert.match(h.el('responsive-caption-text').textContent,/could not be loaded.*transcript/);
  h.video.emit('error');assert.equal(h.el('video-error').hidden,false);
});
await test('Builder rejects unsafe pause tails, changed budgets and inconsistent timeline boundaries',async()=>{
  const baseM=JSON.parse(fs.readFileSync(manifestPath,'utf8'));const baseT=JSON.parse(fs.readFileSync(timelinePath,'utf8'));
  function reject(mutator,expected){
    const m=structuredClone(baseM),t=structuredClone(baseT);mutator(m,t);
    const mp=path.join(fixtureDir,'invalid-manifest.json'),tp=path.join(fixtureDir,'invalid-timeline.json');
    fs.writeFileSync(mp,JSON.stringify(m));fs.writeFileSync(tp,JSON.stringify(t));
    const p=spawnSync(python,['-c',extractCode,builder,mp,tp],{encoding:'utf8'});
    assert.notEqual(p.status,0);assert.match(p.stderr,expected);
  }
  const rows=t=>Array.isArray(t)?t:t.slides??t.chapters??t.timeline;
  reject((_m,t)=>{const r=rows(t)[2];r.narration_end_seconds=r.end_seconds;},/cut off narration/);
  reject((m,_t)=>{m[2].activity_minutes=3;},/Optional practice must be/);
  reject((_m,t)=>{rows(t)[1].start_seconds+=1;},/gap or overlap/);
  reject((m,_t)=>{m[12].pause_instruction='';},/needs an instruction/);
  reject((_m,t)=>{rows(t)[0].end_seconds=Number.NaN;},/TypeError|Nonfinite/);
});
const result={scope:'Controller and metadata validation tests with a fake DOM/media; not rendering, narration synchronization, or real playback QA',
  mode,script_sha256:createHash('sha256').update(script).digest('hex'),chapters:chapters.length,tests};
if(mode.startsWith('actual'))result.timing_source=path.relative(root,timelinePath);
const oi=process.argv.indexOf('--output');if(oi>=0){const dest=path.resolve(process.argv[oi+1]);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');}
console.log(`\n${tests.length} tests passed. ${mode}`);
