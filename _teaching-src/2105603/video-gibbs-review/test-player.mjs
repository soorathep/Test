/** Test review-player event logic with measured chapter data, without browser automation.
 * --fixture uses clearly labelled, private synthetic timings for development only.
 * Default mode requires final media metadata. This does not assess video or audio quality.
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
const fixture=process.argv.includes('--fixture');
const result=spawnSync(path.join(os.homedir(),'.venvs/research/bin/python'),['-c','import json,runpy,sys;m=runpy.run_path(sys.argv[1]);print(json.dumps({"script":m["PLAYER_SCRIPT"],"template":m["TEMPLATE"]}))',path.join(here,'build-video-page.py')],{encoding:'utf8',maxBuffer:2**20});
assert.equal(result.status,0,result.stderr);
const {script,template}=JSON.parse(result.stdout);
const minutes={7:2,12:5,15:2,18:4,19:5,22:8,25:3};
let chapters;
if(fixture){
  chapters=Array.from({length:26},(_,i)=>({slide:i+1,title:`Fixture slide ${i+1}`,narration:'Private synthetic test data.',cue:minutes[i+1]?'Do the fixture work.':'Follow the fixture.',start:i*20,end:(i+1)*20,activity:!!minutes[i+1],activity_minutes:minutes[i+1]||0}));
}else{
  const manifest=JSON.parse(fs.readFileSync(path.join(root,'outputs/gibbs-review-video/manifest.json'),'utf8'));
  const timing=JSON.parse(fs.readFileSync(path.join(root,'outputs/gibbs-review-video/timeline.json'),'utf8')).slides;
  chapters=manifest.map((m,i)=>({...m,cue:m.pause_instruction||'Listen and follow the calculation or demonstration.',start:timing[i].start_seconds,end:timing[i].end_seconds}));
}
assert.equal(chapters.length,26);
assert.deepEqual(chapters.filter(c=>c.activity).map(c=>c.slide),[7,12,15,18,19,22,25]);
assert.equal(chapters.reduce((sum,c)=>sum+c.activity_minutes,0),29);
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
  document.getElementById=el;document.querySelectorAll=selector=>{if(selector==='.chapter')return links;if(selector==='[data-demo-slide]')return [17,18,20,23,24].map(n=>{const link=new Element('demo-'+n);link.dataset={demoSlide:String(n)};return link;});throw new Error('Unknown selector '+selector);};
  document.createElement=tag=>new Element(tag);document.exitFullscreen=async()=>{};
  const location={hash:''};const history={replaceState(_a,_b,hash){location.hash=hash;}};
  const captionMedia=new Element('narrow-caption-query');captionMedia.matches=narrow;
  const window=new Element('window');window.matchMedia=query=>query==='(max-width: 900px)'?captionMedia:{matches:true};
  const context={document,window,history,location,
    setTimeout(fn,delay){const id=++serial;timers.set(id,{fn,delay});return id;},clearTimeout(id){timers.delete(id);},
    requestAnimationFrame(fn){const id=++serial;frames.set(id,fn);return id;},cancelAnimationFrame(id){frames.delete(id);},
    Blob,URL:{createObjectURL(blob){downloads.push(blob);return 'blob:test-controller';},revokeObjectURL(){}},console};
  vm.runInNewContext(script,context,{filename:'GibbsReview_PLAYER_SCRIPT.js',timeout:1000});
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
  return {el,video,links,jump,play,advance,settle,manualSeek,continueActivity,toggle,timers,frames,track,document,resizeCaptionLayout,loadTrack,setCues,downloads};
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


await test('Every work stop pauses before the next slide and Continue reaches the next chapter', async()=>{
  for(const slide of [7,12,15,18,19,22,25]){
    const h=harness();await h.jump(slide);await h.play();
    await h.advance(chapters[slide-1].end+.15);checkPause(h,slide);
    await h.continueActivity();assert.equal(h.el('pause-panel').hidden,true);assert.equal(h.video.paused,false);
    near(h.video.currentTime,chapters[slide].start+.025);
  }
});
await test('Delayed playback cannot skip two activity boundaries',async()=>{
  const h=harness();await h.jump(18);await h.play();await h.advance(chapters[18].end+.5);checkPause(h,18);
});
await test('Frame and timer event paths preserve the pause guard',async()=>{
  for(const event of ['frame','timer']){const h=harness();await h.jump(12);await h.play();await h.advance(chapters[11].end-.2,event);checkPause(h,12);}
});
await test('Intentional chapter selection bypasses skipped work but keeps playback paused',async()=>{
  const h=harness();await h.jump(23);near(h.video.currentTime,chapters[22].start+.025);assert.equal(h.video.paused,true);assert.equal(h.el('pause-panel').hidden,true);
});
await test('Manual seeking and replaying an earlier exercise rearm its pause',async()=>{
  const h=harness();await h.jump(7);await h.play();await h.advance(chapters[6].end);checkPause(h,7);await h.continueActivity();
  await h.manualSeek(chapters[6].start+1);await h.play();await h.advance(chapters[6].end);checkPause(h,7);
});
await test('Disabling pauses allows ordinary playback and reenabling restores later stops',async()=>{
  const h=harness();await h.jump(7);h.toggle(false);await h.play();await h.advance(chapters[6].end+.1);assert.equal(h.video.paused,false);assert.equal(h.el('pause-panel').hidden,true);
  h.toggle(true);await h.jump(12);await h.advance(chapters[11].end);checkPause(h,12);
});
await test('Wide captions are native; narrow captions remain timed below the image',async()=>{
  const h=harness();await h.settle();assert.equal(h.track.mode,'showing');assert.equal(h.el('responsive-captions').hidden,true);
  h.resizeCaptionLayout(true);await h.settle();assert.equal(h.track.mode,'hidden');assert.equal(h.el('responsive-captions').hidden,false);
  h.setCues(['Curvature is local.','Test global support.']);assert.equal(h.el('responsive-caption-text').textContent,'Curvature is local. Test global support.');
  h.el('captions-enabled').checked=false;h.el('captions-enabled').emit('change');await h.settle();assert.equal(h.el('responsive-captions').hidden,true);assert.equal(h.track.mode,'disabled');
});
await test('Delayed caption loading and failures retain readable fallback instructions',async()=>{
  const h=harness({narrow:true,delayedTrack:true});await h.settle();h.loadTrack();await h.settle();h.setCues(['A measured caption.']);assert.equal(h.el('responsive-caption-text').textContent,'A measured caption.');
  h.el('english-caption-track').emit('error');await h.settle();assert.match(h.el('responsive-caption-text').textContent,/transcript below/);
});
await test('Optional review labels and transcript contain no new attendance request',async()=>{
  const h=harness();await h.jump(12);assert.equal(h.el('lesson-time').textContent,'Suggested independent work: 5 min');
  await h.jump(13);assert.equal(h.el('lesson-time').textContent,'Optional Gibbs and stability review');
  h.el('download-transcript').click();const text=await h.downloads.at(-1).text();assert.match(text,/29 minutes/);assert.match(text,/No additional attendance/);assert.doesNotMatch(text,/Week 4|180 minutes|Session 4/);
});
const hash=value=>createHash('sha256').update(value).digest('hex');
const report={chapters:chapters.length,script_sha256:hash(script),manifest_sha256:fixture?null:hash(fs.readFileSync(path.join(root,'outputs/gibbs-review-video/manifest.json'))),timeline_sha256:fixture?null:hash(fs.readFileSync(path.join(root,'outputs/gibbs-review-video/timeline.json'))),mode:fixture?'Synthetic timing fixture; controller logic only':'Final measured timeline; mocked media events only',tests,scope:'No browser, decoded-video, audio or visual QA is claimed.'};
const out=process.argv.indexOf('--output');if(out>=0){const target=process.argv[out+1];fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,JSON.stringify(report,null,2));}
console.log(`${tests.length} tests passed; ${report.mode}`);
