/**
 * Focused control-flow tests for the actual Week 3 PLAYER_SCRIPT.
 * No browser automation, rendered-video claims, or synthetic media QA.
 * Uses actual timing metadata when available; otherwise a clearly labeled
 * 44-slide synthetic timing fixture exercises only the controller branches.
 *
 * Run with an absolute Node executable. Options:
 *   --require-media-timeline  Refuse the synthetic timing fallback.
 *   --fixture                 Explicitly exercise synthetic timing.
 *   --output /path/report.json Save the clearly scoped result.
 */
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
const extraction=spawnSync(python,['-c',
  'import json,runpy,sys; m=runpy.run_path(sys.argv[1]); print(json.dumps({"script":m["PLAYER_SCRIPT"],"template":m["TEMPLATE"]}))',builder],
  {encoding:'utf8',maxBuffer:2**20});
assert.equal(extraction.status,0,extraction.stderr);
const {script,template}=JSON.parse(extraction.stdout);
const manifestPath=path.join(root,'outputs/week03-video/audio/manifest.json');
const timelinePath=path.join(root,'outputs/week03-video/timeline.json');
const expectedSlides=44;
const workStops=[4,11,13,17,26,32,36,40,43];
const breakSlide=28;
let mode,chapters;
if(!args.has('--fixture')&&fs.existsSync(manifestPath)&&fs.existsSync(timelinePath)){
  const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
  const raw=JSON.parse(fs.readFileSync(timelinePath,'utf8'));
  const timeline=Array.isArray(raw)?raw:raw.slides??raw.chapters??raw.timeline;
  assert.equal(manifest.length,expectedSlides,'Stale narration manifest; rebuild revised media or explicitly use --fixture.');assert.equal(timeline.length,manifest.length);
  chapters=manifest.map((m,i)=>{
    const t=timeline[i];assert.equal(m.slide,i+1);assert.equal(t.slide,i+1);
    assert.equal(t.activity,m.activity);
    return {slide:m.slide,title:m.title,narration:m.narration,cue:m.pause_instruction||'Listen, then continue through the lesson.',
      start:t.start_seconds,end:t.end_seconds,lesson_start:m.stage_start_minute,lesson_end:m.stage_end_minute,
      activity:m.activity,activity_minutes:m.activity_minutes};
  });
  mode='actual timing metadata; mocked media events, no decoded-video or browser QA';
}else{
  assert.ok(!args.has('--require-media-timeline'),'Actual final manifest/timeline required but unavailable.');
  let narration=JSON.parse(fs.readFileSync(path.join(here,'narration.json'),'utf8'));
  if(narration.length!==expectedSlides){
    narration=['narration-theory-draft.json','narration-demo-draft.json','narration-lle-draft.json']
      .flatMap(name=>JSON.parse(fs.readFileSync(path.join(here,name),'utf8')))
      .sort((a,b)=>a.number-b.number)
      .map(m=>({...m,slide:m.number,activity:m.activity_minutes>0}));
  }
  assert.equal(narration.length,expectedSlides,'The explicit fixture requires the revised 44-slide source/drafts.');
  assert.deepEqual(narration.map(m=>m.slide),Array.from({length:expectedSlides},(_,i)=>i+1));
  chapters=narration.map((m,i)=>({slide:i+1,title:m.title,narration:m.narration,
    cue:m.pause_instruction||'Listen, then continue through the lesson.',start:i*20,end:(i+1)*20,
    lesson_start:m.stage_start_minute,lesson_end:m.stage_end_minute,activity:m.activity,activity_minutes:m.activity_minutes}));
  mode='SYNTHETIC TIMING FIXTURE: 44 revised source slides, 20 seconds per slide; control flow only, not actual media QA';
}
assert.deepEqual(chapters.map(c=>c.slide),Array.from({length:expectedSlides},(_,i)=>i+1));
assert.ok(chapters.every(c=>Number.isFinite(c.start)&&c.end>c.start+.24));
assert.deepEqual(chapters.filter(c=>c.activity).map(c=>c.slide),[...workStops,breakSlide].sort((a,b)=>a-b));
assert.equal(chapters.at(-1).activity,false,'Slide 44 checks receipt and saved work; it does not ask for another submission.');

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
function harness({narrow=false,delayedTrack=false}={}){
  const queue=[];const timers=new Map();const frames=new Map();let serial=0;
  const ids=[...template.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
  const elements=new Map(ids.map(id=>[id,new Element(id)]));
  const el=id=>{assert.ok(elements.has(id),`Unknown DOM id: ${id}`);return elements.get(id);};
  const links=chapters.map(c=>new Element(`chapter-${c.slide}`));
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
    Blob,URL:{createObjectURL(){return 'blob:test-controller';},revokeObjectURL(){}},console};
  vm.runInNewContext(script,context,{filename:'Week3_PLAYER_SCRIPT.js',timeout:1000});
  async function settle(){for(let i=0;i<30;i++){while(queue.length)queue.shift()();await Promise.resolve();if(!queue.length)return;}throw new Error('Event queue failed to settle.');}
  async function jump(slide){links[slide-1].click();await settle();}
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
  return {el,video,links,jump,play,advance,settle,manualSeek,continueActivity,toggle,timers,frames,track,document,resizeCaptionLayout,loadTrack,setCues};
}
const tests=[];
async function test(name,fn){await fn();tests.push({name,status:'passed'});console.log(`PASS ${name}`);}
function near(actual,expected){assert.ok(Math.abs(actual-expected)<1e-7,`${actual} != ${expected}`);}
function checkPause(h,slide){
  const c=chapters[slide-1];assert.equal(h.video.paused,true);assert.equal(h.el('pause-panel').hidden,false);
  assert.equal(h.el('slide-counter').textContent,`Slide ${slide} of ${chapters.length}`);
  assert.equal(h.el('pause-cue').textContent,c.cue);
  assert.ok(h.video.currentTime<c.end,`Activity ${slide} crossed into its successor`);
  assert.equal(h.links[slide-1].getAttribute('aria-current'),'true');
  if(slide<chapters.length)assert.equal(h.links[slide].getAttribute('aria-current'),null);
}

await test('Default pause holds all nine revised work stops before advancing',async()=>{
  for(const slide of workStops){
    const h=harness();assert.equal(h.el('auto-pause').checked,true);await h.jump(slide);await h.play();
    await h.advance(chapters[slide-1].end-.24);checkPause(h,slide);
    await h.play();checkPause(h,slide);
  }
});
await test('Delayed timeupdate beyond a boundary rewinds to the previous task',async()=>{
  const h=harness();await h.jump(13);await h.play();await h.advance(chapters[13].start+.12);
  checkPause(h,13);near(h.video.currentTime,chapters[12].end-.24);
});
await test('Continue advances from the lever-rule attempt to its check and resumes',async()=>{
  const h=harness();await h.jump(32);await h.play();await h.advance(chapters[31].end-.24);await h.continueActivity();
  assert.equal(h.el('pause-panel').hidden,true);assert.equal(h.video.paused,false);
  near(h.video.currentTime,chapters[32].start+.025);assert.equal(h.el('slide-counter').textContent,`Slide 33 of ${chapters.length}`);
});
await test('Intentional chapter and native seeks do not trigger skipped work stops',async()=>{
  const h=harness();await h.play();await h.jump(19);assert.equal(h.video.paused,false);
  await h.advance(chapters[18].start+.5);assert.equal(h.el('pause-panel').hidden,true);
  await h.manualSeek(chapters[28].start+.5);await h.advance(chapters[28].start+1);
  assert.equal(h.el('pause-panel').hidden,true);assert.equal(h.el('slide-counter').textContent,`Slide 29 of ${chapters.length}`);
  await h.advance(chapters[31].end-.24);checkPause(h,32);
});
await test('The demo link intentionally selects Lab 03 chapter 19',async()=>{
  const h=harness();h.el('demo-start').click();await h.settle();
  near(h.video.currentTime,chapters[18].start+.025);assert.equal(h.el('slide-counter').textContent,`Slide 19 of ${chapters.length}`);
  assert.equal(h.el('pause-panel').hidden,true);
});
await test('Replaying a completed activity reinstates its future pause',async()=>{
  const h=harness();await h.jump(4);await h.play();await h.advance(chapters[3].end-.24);await h.continueActivity();
  await h.jump(4);await h.advance(chapters[3].end-.24);checkPause(h,4);
});
await test('Turning work pauses off permits manual playback and clears a shown pause',async()=>{
  const h=harness();await h.jump(4);await h.play();await h.advance(chapters[3].end-.24);checkPause(h,4);
  h.toggle(false);assert.equal(h.el('pause-panel').hidden,true);await h.play();await h.advance(chapters[4].start+.3);
  assert.equal(h.video.paused,false);assert.equal(h.el('slide-counter').textContent,`Slide 5 of ${chapters.length}`);
  h.video.pause();h.toggle(true);await h.jump(11);await h.play();await h.advance(chapters[10].end-.24);checkPause(h,11);
});
await test('Timer and frame guards protect the unseen-review boundary without timeupdate',async()=>{
  for(const event of ['timer','frame']){
    const h=harness();await h.jump(40);await h.play();await h.advance(chapters[39].end-.24,event);checkPause(h,40);
  }
});
await test('The ten-minute break holds slide 28 and Continue resumes slide 29',async()=>{
  const h=harness();await h.jump(breakSlide);await h.play();await h.advance(chapters[breakSlide-1].end-.24);checkPause(h,breakSlide);
  assert.equal(chapters[breakSlide-1].activity_minutes,10);await h.continueActivity();assert.equal(h.el('slide-counter').textContent,`Slide 29 of ${chapters.length}`);
});
await test('Final form pause 43 leads to receipt check 44 without inventing another work stop',async()=>{
  const h=harness();await h.jump(43);await h.play();await h.advance(chapters[42].end-.24);checkPause(h,43);
  assert.equal(h.el('continue-button').textContent,'Continue to next slide');await h.continueActivity();
  assert.equal(h.video.paused,false);assert.equal(h.el('pause-panel').hidden,true);near(h.video.currentTime,chapters[43].start+.025);
  h.video._time=chapters.at(-1).end;h.video.paused=true;h.video.emit('ended');await h.settle();
  assert.equal(h.el('pause-panel').hidden,true);assert.equal(h.el('slide-counter').textContent,`Slide 44 of ${chapters.length}`);
});
await test('Delayed natural ended event catches unfinished form pause 43',async()=>{
  const h=harness();await h.jump(43);await h.play();h.video._time=chapters.at(-1).end;h.video.paused=true;
  h.video.emit('ended');await h.settle();checkPause(h,43);
});
await test('An intentional jump to final receipt check does not trigger skipped form work',async()=>{
  const h=harness();await h.jump(44);await h.play();h.video._time=chapters.at(-1).end;h.video.paused=true;
  h.video.emit('ended');await h.settle();assert.equal(h.el('pause-panel').hidden,true);
});
await test('Wide captions remain native; narrow captions use active timed cues below the image',async()=>{
  const h=harness();await h.settle();assert.equal(h.track.mode,'showing');assert.equal(h.el('responsive-captions').hidden,true);
  h.resizeCaptionLayout(true);await h.settle();assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-captions').hidden,false);
  h.setCues(['First line\ncontinues.','Second sentence.']);assert.equal(h.el('responsive-caption-text').textContent,'First line continues. Second sentence.');
  assert.equal(h.el('video-stage').getAttribute('data-captions-below'),'true');
  h.setCues([]);assert.equal(h.el('responsive-caption-text').textContent,'');
  h.resizeCaptionLayout(false);await h.settle();assert.equal(h.track.mode,'showing');assert.equal(h.el('responsive-captions').hidden,true);assert.equal(h.el('responsive-caption-text').textContent,'');
});
await test('Caption toggle disables both presentations and restores the appropriate narrow mode',async()=>{
  const h=harness({narrow:true});await h.settle();h.setCues(['An active sentence.']);
  h.el('captions-enabled').checked=false;h.el('captions-enabled').emit('change');await h.settle();
  assert.equal(h.track.mode,'disabled');assert.equal(h.el('responsive-captions').hidden,true);assert.equal(h.el('responsive-caption-text').textContent,'');
  h.el('captions-enabled').checked=true;h.el('captions-enabled').emit('change');await h.settle();
  assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-caption-text').textContent,'An active sentence.');
  h.track.mode='showing';await h.settle();assert.equal(h.track.mode,'hidden','Native CC must not duplicate narrow custom captions');
});
await test('Native full screen uses native captions; narrow wrapper full screen retains separate captions',async()=>{
  const h=harness({narrow:true});await h.settle();h.setCues(['Current sentence.']);
  h.document.fullscreenElement=h.el('video-stage');h.document.emit('fullscreenchange');await h.settle();
  assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-captions').hidden,false);
  h.document.fullscreenElement=h.video;h.document.emit('fullscreenchange');await h.settle();
  assert.equal(h.track.mode,'showing');assert.equal(h.el('responsive-captions').hidden,true);
  h.document.fullscreenElement=null;h.document.emit('fullscreenchange');await h.settle();assert.equal(h.track.mode,'hidden');
  h.video.emit('webkitbeginfullscreen');await h.settle();assert.equal(h.track.mode,'showing');assert.equal(h.el('responsive-captions').hidden,true);
  h.video.emit('webkitendfullscreen');await h.settle();assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-captions').hidden,false);
});
await test('Late caption loading attaches cue updates and desktop native CC changes update the toggle',async()=>{
  const h=harness({narrow:true,delayedTrack:true});await h.settle();h.loadTrack();await h.settle();h.setCues(['Late loaded cue.']);
  assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-caption-text').textContent,'Late loaded cue.');
  h.resizeCaptionLayout(false);await h.settle();h.track.mode='disabled';await h.settle();assert.equal(h.el('captions-enabled').checked,false);
  h.track.mode='showing';await h.settle();assert.equal(h.el('captions-enabled').checked,true);
});
const result={scope:'Controller unit tests using minimal fake DOM/media; not actual rendering, audio synchronization or browser playback QA',
  mode,script_sha256:createHash('sha256').update(script).digest('hex'),chapters:chapters.length,tests};
if(mode.startsWith('actual'))result.timing_source=path.relative(root,timelinePath);
const outputIndex=process.argv.indexOf('--output');
if(outputIndex>=0){assert.ok(process.argv[outputIndex+1]);const dest=path.resolve(process.argv[outputIndex+1]);fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,JSON.stringify(result,null,2)+'\n');}
console.log(`\n${tests.length} tests passed. ${mode}`);
