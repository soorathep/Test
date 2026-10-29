/**
 * Integrated Week 4 controller checks with minimal fake media/DOM.
 * Actual metadata mode is not decoded-video, browser, or listening QA.
 * Options: --fixture | --require-media-timeline, --manifest PATH,
 * --timeline PATH, --output PATH. Run with the absolute bundled Node.
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
const root=path.resolve(here,'../../..');
const argv=process.argv.slice(2);
const args=new Set(argv);
function option(name,fallback){const i=argv.indexOf(name);if(i<0)return fallback;assert.ok(argv[i+1]);return path.resolve(argv[i+1]);}
const python=path.join(os.homedir(),'.venvs/research/bin/python');
const builder=path.join(here,'build-video-page.py');
const manifestPath=option('--manifest',path.join(root,'outputs/week04-opening-video/audio/manifest.json'));
const timelinePath=option('--timeline',path.join(root,'outputs/week04-opening-video/timeline.json'));
const OPENING=14,CORE=40;
const activityMinutes={4:8,8:6,13:10,15:5,18:22,20:10,25:10,29:5,32:24,39:10};
let mode,manifest,timeline;
if(!args.has('--fixture')&&fs.existsSync(manifestPath)&&fs.existsSync(timelinePath)){
  manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
  const raw=JSON.parse(fs.readFileSync(timelinePath,'utf8'));
  timeline=Array.isArray(raw)?raw:raw.slides??raw.chapters??raw.timeline;
  mode='actual timing metadata; mocked media events, no decoded-video or browser QA';
}else{
  assert.ok(!args.has('--require-media-timeline'),'Actual final manifest/timeline required but unavailable.');
  manifest=Array.from({length:OPENING+CORE},(_,i)=>{
    const slide=i+1,opening=slide<=OPENING,core_slide=opening?null:slide-OPENING;
    const activity_minutes=opening?(slide===13?4:0):(activityMinutes[core_slide]??0);
    return {slide,section:opening?'opening':'core',core_slide,anchor:opening?'opening-'+String(slide).padStart(2,'0'):'slide-'+core_slide,
      title:'Synthetic fixture '+slide,narration:'Synthetic controller fixture; not spoken teaching content.',
      activity:activity_minutes>0||core_slide===36,activity_minutes,
      pause_instruction:activity_minutes>0||core_slide===36?'Complete the fixture task or choose the optional route.':'',
      stage_start_minute:null,stage_end_minute:null};
  });
  timeline=manifest.map((m,i)=>({...m,start_seconds:i*20,end_seconds:(i+1)*20,narration_end_seconds:(i+1)*20-2}));
  mode='SYNTHETIC TIMING FIXTURE: 14 opening + 40 core controller records, 20 seconds each; control flow only';
}
function prepare(m,t){
  return spawnSync(python,['-c','import json,runpy,sys; d=json.load(sys.stdin); b=runpy.run_path(sys.argv[1]); print(json.dumps({"rows":b["prepare_rows"](d["manifest"],d["timeline"]),"script":b["PLAYER_SCRIPT"],"template":b["TEMPLATE"]}))',builder],
    {input:JSON.stringify({manifest:m,timeline:t}),encoding:'utf8',maxBuffer:4*1024*1024});
}
const prepared=prepare(manifest,timeline);
assert.equal(prepared.status,0,prepared.stderr);
const {rows:chapters,script,template}=JSON.parse(prepared.stdout);
const core=n=>chapters.find(c=>c.core_slide===n);
const opening=n=>chapters[n-1];
const label=n=>'Slide '+n+' of 40';
assert.equal(chapters.length,OPENING+CORE);
assert.equal(chapters.filter(c=>c.section==='opening').length,OPENING);
assert.equal(chapters.filter(c=>c.section==='core').length,CORE);
assert.equal(chapters.reduce((v,c)=>v+c.activity_minutes,0),114);
assert.equal(core(36).activity_minutes,0);
assert.equal(core(36).optional_activity_minutes,20);
assert.equal(opening(13).activity_minutes,4);

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
function harness({narrow=false,delayedTrack=false,records=chapters,hash=''}={}){
  const chapters=records;
  const downloads=[];
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
  const location={hash};const history={replaceState(_a,_b,hash){location.hash=hash;}};
  const captionMedia=new Element('narrow-caption-query');captionMedia.matches=narrow;
  const window=new Element('window');window.matchMedia=query=>query==='(max-width: 900px)'?captionMedia:{matches:true};
  const context={document,window,history,location,
    setTimeout(fn,delay){const id=++serial;timers.set(id,{fn,delay});return id;},clearTimeout(id){timers.delete(id);},
    requestAnimationFrame(fn){const id=++serial;frames.set(id,fn);return id;},cancelAnimationFrame(id){frames.delete(id);},
    Blob,URL:{createObjectURL(blob){downloads.push(blob);return 'blob:test-controller';},revokeObjectURL(){}},console};
  vm.runInNewContext(script,context,{filename:'Week4_PLAYER_SCRIPT.js',timeout:1000});
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
  return {el,video,links,jump,play,advance,settle,location,window,manualSeek,continueActivity,toggle,timers,frames,track,document,resizeCaptionLayout,loadTrack,setCues,downloads};
}

const tests=[];
async function test(name,fn){await fn();tests.push({name,status:'passed'});console.log('PASS '+name);}
function near(actual,expected){assert.ok(Math.abs(actual-expected)<1e-7,actual+' != '+expected);}
function checkPause(h,c){
  assert.equal(h.video.paused,true);assert.equal(h.el('pause-panel').hidden,false);
  assert.equal(h.el('slide-counter').textContent,c.counter);
  assert.equal(h.el('pause-cue').textContent,c.cue);
  assert.ok(h.video.currentTime<c.end,'Task crossed into its successor.');
  assert.equal(h.links[c.slide-1].getAttribute('aria-current'),'true');
}
async function pauseAt(h,c,event='timeupdate'){
  await h.jump(c.slide);await h.play();await h.advance(c.end-.24,event);checkPause(h,c);
}
await test('Builder rejects old forty-slide media, wrong anchors, missing pauses and double-counted opening work',async()=>{
  assert.notEqual(prepare(manifest.slice(14),timeline.slice(14)).status,0);
  for(const mutate of [
    x=>x[14].anchor='slide-15',
    x=>x[12].activity_minutes=20,
    x=>x[12].activity=false,
    x=>x[17].activity_minutes=7,
  ]){
    const broken=structuredClone(manifest);mutate(broken);assert.notEqual(prepare(broken,timeline).status,0);
  }
});
await test('Default playback starts with Opening 01 and no repeated reading assignment',async()=>{
  const h=harness();assert.equal(h.el('slide-counter').textContent,'Opening 1 of 14');
  near(h.video.currentTime,0);
  assert.match(template,/questions page.*text companion/);
  assert.match(template,/No separate 20-minute reading task is added/);
  assert.ok(!template.includes('unchanged recording'));
});
await test('All forty historical core anchors retain their original semantic target',async()=>{
  for(let n=1;n<=40;n++){
    const h=harness({hash:'#slide-'+n});h.video.emit('loadedmetadata');await h.settle();
    near(h.video.currentTime,core(n).start+.025);
    assert.equal(h.el('slide-counter').textContent,label(n));
    assert.equal(h.location.hash,'#slide-'+n);
  }
});
await test('Every opening anchor selects its own chapter without colliding with core slide numbers',async()=>{
  for(let n=1;n<=14;n++){
    const h=harness({hash:'#opening-'+String(n).padStart(2,'0')});h.video.emit('loadedmetadata');await h.settle();
    near(h.video.currentTime,opening(n).start+.025);
    assert.equal(h.el('slide-counter').textContent,'Opening '+n+' of 14');
  }
});
await test('Hash changes and the opening/core start links select explicitly without autoplay',async()=>{
  const h=harness();h.location.hash='#slide-30';h.window.emit('hashchange');await h.settle();
  near(h.video.currentTime,core(30).start+.025);assert.equal(h.video.paused,true);
  h.el('opening-start').click();await h.settle();near(h.video.currentTime,.025);
  h.el('core-start').click();await h.settle();near(h.video.currentTime,core(1).start+.025);
  h.location.hash='#slide-999';h.window.emit('hashchange');await h.settle();
  near(h.video.currentTime,core(1).start+.025);
});
await test('The R1–R3 pause stops before answers and Continue advances to Opening 14',async()=>{
  const h=harness();await pauseAt(h,opening(13));
  assert.match(h.el('pause-budget').textContent,/about 4 minutes/);
  await h.play();checkPause(h,opening(13));await h.continueActivity();
  near(h.video.currentTime,opening(14).start+.025);assert.equal(h.video.paused,false);
  assert.equal(h.el('slide-counter').textContent,'Opening 14 of 14');
});
await test('A delayed update cannot expose opening answers before the R1–R3 pause',async()=>{
  const h=harness();await h.jump(opening(13).slide);await h.play();
  await h.advance(opening(14).start+.12);checkPause(h,opening(13));
  near(h.video.currentTime,opening(13).end-.24);
});
await test('Opening 14 transitions continuously to the original core slide 1',async()=>{
  const h=harness();await h.jump(opening(14).slide);await h.play();
  await h.advance(core(1).start+.1);
  assert.equal(h.el('pause-panel').hidden,true);
  assert.equal(h.el('slide-counter').textContent,label(1));
});
await test('All nine required core work stops remain intact',async()=>{
  for(const n of [4,8,13,15,18,25,29,32,39]){
    const h=harness();await pauseAt(h,core(n));await h.play();checkPause(h,core(n));
  }
});
await test('Study labels distinguish opening and core introduction and preserve explicit ranges',async()=>{
  const h=harness();assert.equal(h.el('lesson-time').textContent,'Opening questions: R1–R3 in your notebook');
  for(const n of [1,2,3]){await h.jump(core(n).slide);assert.equal(h.el('lesson-time').textContent,'Core lesson introduction');}
  const records=chapters.map(c=>({...c,lesson_start:null,lesson_end:null}));
  records[core(30).slide-1].lesson_start=120;records[core(30).slide-1].lesson_end=150;
  const r=harness({records});await r.jump(core(30).slide);
  assert.equal(r.el('lesson-time').textContent,'Study time 120-150 min');
});
await test('Delayed core task updates rewind without revealing checks',async()=>{
  const h=harness();await h.jump(core(13).slide);await h.play();
  await h.advance(core(14).start+.12);checkPause(h,core(13));
});
await test('Required investigation Continue resumes at the correct core check',async()=>{
  const h=harness();await pauseAt(h,core(32));await h.continueActivity();
  assert.equal(h.el('pause-panel').hidden,true);assert.equal(h.video.paused,false);
  near(h.video.currentTime,core(33).start+.025);
});
await test('Intentional chapter and native seeks do not trigger earlier opening or core tasks',async()=>{
  const h=harness();await h.play();await h.jump(core(16).slide);
  await h.advance(core(16).start+.5);assert.equal(h.el('pause-panel').hidden,true);
  await h.manualSeek(core(30).start+.5);await h.advance(core(30).start+1);
  assert.equal(h.el('pause-panel').hidden,true);
  await h.advance(core(32).end-.24);checkPause(h,core(32));
});
await test('Both Lab demo links resolve after the opening offset and retain prediction instructions',async()=>{
  for(const [id,n] of [['demo-start',16],['demo-adsorption-start',30]]){
    const h=harness();h.el(id).click();await h.settle();
    near(h.video.currentTime,core(n).start+.025);
    assert.equal(h.el('slide-counter').textContent,label(n));
    assert.equal(h.location.hash,'#slide-'+n);
  }
  assert.match(template,/Before opening the Lab 10 demonstration, complete D1 predictions at slide 15/);
  assert.match(template,/Before opening the Lab 11 demonstration, complete F1-F3 predictions at slide 29/);
});
await test('Both prediction stops precede Lab demos and resume into them',async()=>{
  for(const [predict,demo] of [[15,16],[29,30]]){
    const h=harness();await pauseAt(h,core(predict));
    assert.equal(core(predict).activity_minutes,5);await h.continueActivity();
    near(h.video.currentTime,core(demo).start+.025);assert.equal(h.video.paused,false);
  }
});
await test('Replay reinstates opening and core pauses',async()=>{
  for(const c of [opening(13),core(4)]){
    const h=harness();await pauseAt(h,c);await h.continueActivity();
    await h.jump(c.slide);await h.advance(c.end-.24);checkPause(h,c);
  }
});
await test('Turning pauses off permits manual playback and clears the current task',async()=>{
  const h=harness();await pauseAt(h,opening(13));h.toggle(false);
  assert.equal(h.el('pause-panel').hidden,true);await h.play();await h.advance(opening(14).start+.3);
  assert.equal(h.video.paused,false);h.video.pause();h.toggle(true);await pauseAt(h,core(8));
});
await test('Timer and frame guards handle opening attempts and optional choices without timeupdate',async()=>{
  for(const c of [opening(13),core(36)])for(const event of ['timer','frame']){
    const h=harness();await pauseAt(h,c,event);
  }
});
await test('Optional H choice skips to the correctly offset form chapter and stays paused',async()=>{
  const h=harness();await pauseAt(h,core(36));
  assert.equal(h.el('pause-heading').textContent,'Optional practice: choose your route');
  assert.equal(h.el('optional-skip-button').hidden,false);
  assert.match(h.el('pause-budget').textContent,/No additional work is required here/);
  h.el('optional-skip-button').click();await h.settle();
  near(h.video.currentTime,core(39).start+.025);
  assert.equal(h.video.paused,true);assert.equal(h.location.hash,'#slide-39');
  await h.play();await h.advance(core(39).end-.24);checkPause(h,core(39));
});
await test('Optional H Continue resumes the optional check only after an explicit choice',async()=>{
  const h=harness();await pauseAt(h,core(36));await h.continueActivity();
  near(h.video.currentTime,core(37).start+.025);assert.equal(h.video.paused,false);
});
await test('Optional H navigation appears only on core slides 35–38',async()=>{
  const h=harness();
  for(const c of chapters){
    await h.jump(c.slide);
    assert.equal(h.el('optional-review-navigation').hidden,!c.optional_chapter);
  }
  await h.jump(core(35).slide);h.el('optional-review-exit').click();await h.settle();
  near(h.video.currentTime,core(39).start+.025);
});
await test('Ten-minute break resumes core slide 21 after the opening offset',async()=>{
  const h=harness();await pauseAt(h,core(20));assert.equal(core(20).activity_minutes,10);
  await h.continueActivity();near(h.video.currentTime,core(21).start+.025);
});
await test('Final form pause leads once to receipt check without another submission stop',async()=>{
  const h=harness();await pauseAt(h,core(39));await h.continueActivity();
  near(h.video.currentTime,core(40).start+.025);assert.equal(h.video.paused,false);
  h.video._time=chapters.at(-1).end;h.video.paused=true;h.video.emit('ended');await h.settle();
  assert.equal(h.el('pause-panel').hidden,true);
});
await test('Delayed natural ended event catches unfinished form but intentional final jump does not',async()=>{
  const h=harness();await h.jump(core(39).slide);await h.play();
  h.video._time=chapters.at(-1).end;h.video.paused=true;h.video.emit('ended');await h.settle();checkPause(h,core(39));
  const k=harness();await k.jump(core(40).slide);await k.play();
  k.video._time=chapters.at(-1).end;k.video.paused=true;k.video.emit('ended');await k.settle();
  assert.equal(k.el('pause-panel').hidden,true);
});
await test('Transcript counts integrated narration once and labels opening versus historical core slides',async()=>{
  const h=harness();h.el('download-transcript').click();
  const text=await h.downloads.at(-1).text();
  assert.match(text,/integrated at the start/);
  assert.match(text,/Do not add a separate 20-minute reading task/);
  assert.match(text,/Add 4 minutes.*100 minutes.*10-minute break/);
  assert.match(text,/H1–H4 is optional/);
  assert.match(text,/OPENING 01:/);assert.match(text,/OPENING 14:/);assert.match(text,/SLIDE 1:/);assert.match(text,/SLIDE 40:/);
  assert.ok(!text.includes('unchanged from the original recording'));
  assert.match(template,/week04-video-slides\.pdf/);
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

await test('Production media requires an encoded hash and versions every media URL consistently',async()=>{
  const code=[
    'import contextlib,io,json,pathlib,runpy,sys,tempfile',
    'd=json.load(sys.stdin); b=runpy.run_path(sys.argv[1]); digest="a123456789bc"+"0"*52',
    'assert b["media_version"]([])=="dev"',
    'for raw in ({}, {"video_sha256":"short"}):',
    '    try: b["media_version"](raw)',
    '    except ValueError: pass',
    '    else: raise AssertionError("Missing encoded hash was accepted")',
    'with tempfile.TemporaryDirectory() as tmp:',
    '    p=pathlib.Path(tmp); (p/"m.json").write_text(json.dumps(d["manifest"])); (p/"t.json").write_text(json.dumps({"slides":d["timeline"],"video_sha256":digest}))',
    '    with contextlib.redirect_stdout(io.StringIO()): b["build"](p/"m.json",p/"t.json",p/"page.html")',
    '    text=(p/"page.html").read_text()',
    '    for asset in ("week04-lecture.mp4","week04-captions.vtt","week04-poster.png"):',
    '        assert "./media/week04/"+asset+"?v="+digest[:12] in text',
    '        assert "./media/week04/"+asset+chr(34) not in text',
    '    assert "download="+chr(34)+"week04-lecture.mp4"+chr(34) in text',
    'print("passed")',
  ].join('\n');
  const check=spawnSync(python,['-c',code,builder],{input:JSON.stringify({manifest,timeline}),encoding:'utf8',maxBuffer:1024*1024});
  assert.equal(check.status,0,check.stderr);
  assert.equal(check.stdout.trim(),'passed');
});
const result={scope:'Controller tests using minimal fake DOM/media; not rendered-video, audio synchronization, listening or browser QA',mode,script_sha256:createHash('sha256').update(script).digest('hex'),chapters:chapters.length,route:{opening_chapters:14,opening_work_minutes:4,core_work_minutes:100,break_minutes:10,optional_H_minutes:20,integrated_recording:true},tests};
if(mode.startsWith('actual'))result.timing_source=path.relative(root,timelinePath);
const outputPath=option('--output',null);
if(outputPath){fs.mkdirSync(path.dirname(outputPath),{recursive:true});fs.writeFileSync(outputPath,JSON.stringify(result,null,2)+'\n');}
console.log(tests.length+' tests passed. '+mode);
