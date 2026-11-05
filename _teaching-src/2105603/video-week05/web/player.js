'use strict';
(() => {
  const chapters=JSON.parse(document.getElementById('chapter-data').textContent);
  const video=document.getElementById('lesson-video');
  const autoPause=document.getElementById('auto-pause');
  const panel=document.getElementById('pause-panel');
  const continueButton=document.getElementById('continue-button');
  const announcer=document.getElementById('announcer');
  const links=[...document.querySelectorAll('.chapter')];
  const guards=chapters.filter(c=>c.activity).map(c=>({...c,at:c.end-.24}));
  const workGuards=guards.filter(c=>!c.is_break);
  const completed=new Set();
  const acknowledged=new Set();
  const storageKey='thermo-week05-'+document.getElementById('chapter-data').dataset.version;
  const resumePanel=document.getElementById('resume-panel');
  let stored=null,storageOK=true,activeGuard=null,currentIndex=-1,lastVerifiedTime=0,timer=null,raf=null,internalSeek=null,userSeeking=false,intendedResume=false,lastSaved=0,hasInteracted=false;
  const EPS=.012;
  try {
    const item=JSON.parse(localStorage.getItem(storageKey)||'null');
    if(item&&Number.isFinite(item.time)&&item.time>=0&&item.time<=chapters.at(-1).end&&Array.isArray(item.acknowledged)&&Array.isArray(item.completed))stored=item;
  } catch(_){storageOK=false;document.getElementById('storage-note').textContent='This browser cannot save your place. Keep a note of the chapter; you can still use every lesson control.';}
  function clock(t){const s=Math.floor(t);return `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;}
  function paintProgress(){
    const done=workGuards.filter(g=>acknowledged.has(g.slide)).length;
    document.getElementById('lesson-progress').value=done;
    document.getElementById('progress-text').textContent=`${done} of ${workGuards.length} activity stops acknowledged on this device. This is a personal checklist, not submitted work or attendance.`;
  }
  function saveProgress(force=false){
    if(!storageOK||!hasInteracted||(!force&&Date.now()-lastSaved<4000))return;
    lastSaved=Date.now();
    try{localStorage.setItem(storageKey,JSON.stringify({time:video.currentTime,completed:[...completed],acknowledged:[...acknowledged],pending:activeGuard?.slide||null,autoPause:autoPause.checked,captions:document.getElementById('captions-enabled').checked}));}
    catch(_){storageOK=false;document.getElementById('storage-note').textContent='This browser cannot save your place. Keep a note of the chapter; you can still use every lesson control.';}
  }
  function indexAt(time){for(let i=chapters.length-1;i>=0;i--)if(time+.001>=chapters[i].start)return i;return 0;}
  function studyLabel(c){return c.is_break?'Ten-minute break':`Worksheet ${c.worksheet}${c.activity?` · ${c.activity_minutes} minutes to work`:''}`;}
  function render(time){
    const i=activeGuard?activeGuard.slide-1:indexAt(time);if(i===currentIndex)return;currentIndex=i;const c=chapters[i];
    document.getElementById('slide-counter').textContent=`Slide ${c.slide} of ${chapters.length}`;
    document.getElementById('current-title').textContent=c.title;
    document.getElementById('lesson-time').textContent=studyLabel(c);
    document.getElementById('current-cue').textContent=c.cue;
    document.getElementById('transcript-title').textContent=`Transcript · slide ${c.slide}`;
    document.getElementById('transcript-text').textContent=c.narration;
    document.getElementById('previous-button').disabled=i===0;
    document.getElementById('next-button').disabled=i===chapters.length-1;
    links.forEach((a,n)=>n===i?a.setAttribute('aria-current','true'):a.removeAttribute('aria-current'));
  }
  function clearSchedules(){if(timer!==null)clearTimeout(timer);if(raf!==null)cancelAnimationFrame(raf);timer=null;raf=null;}
  function clearPanel(){activeGuard=null;panel.hidden=true;}
  function resetFuture(time){for(const c of chapters)if(c.end>time)completed.delete(c.slide);}
  function setInternalTime(time,kind,resume=false){internalSeek={target:time,kind};intendedResume=resume;lastVerifiedTime=time;video.currentTime=time;render(time);}
  async function exitNativeFullscreen(){try{if(document.fullscreenElement===video)await document.exitFullscreen();if(video.webkitDisplayingFullscreen&&video.webkitExitFullscreen)video.webkitExitFullscreen();}catch(_){}}
  function pauseFor(guard){
    clearSchedules();activeGuard=guard;video.pause();
    document.getElementById('pause-heading').textContent=guard.is_break?'Take the ten-minute break':guard.slide===chapters.length?'Finish your exit ticket and feedback':`Pause and work: slide ${guard.slide}`;
    document.getElementById('pause-cue').textContent=guard.cue;
    document.getElementById('pause-budget').textContent=guard.is_break?'Take about 10 minutes. The recording waits until you choose Continue.':`Use about ${guard.activity_minutes} minutes. If you reach the time limit, write down the sticking point and continue to the explanation. You do not need to solve every part before moving on. The player will not resume automatically.`;
    continueButton.textContent=guard.slide===chapters.length?'Finish lesson':'Continue to next slide';
    panel.hidden=false;
    if(Math.abs(video.currentTime-guard.at)>.015)setInternalTime(guard.at,'guard');
    lastVerifiedTime=guard.at;render(guard.at);saveProgress(true);
    announcer.textContent=`Video paused. ${guard.cue} Select ${continueButton.textContent} when ready.`;exitNativeFullscreen();
  }
  function checkPlayback(){
    if(video.seeking||userSeeking||internalSeek||activeGuard)return;
    const now=video.currentTime;
    if(now+EPS<lastVerifiedTime){resetFuture(now);lastVerifiedTime=now;}
    if(autoPause.checked&&!video.paused){const g=guards.find(g=>!completed.has(g.slide)&&g.at+EPS>=lastVerifiedTime&&g.at<=now+EPS);if(g){pauseFor(g);return;}}
    lastVerifiedTime=now;render(now);saveProgress();
  }
  function armTimer(){
    if(timer!==null)clearTimeout(timer);timer=null;
    if(video.paused||video.seeking||userSeeking||internalSeek||activeGuard||!autoPause.checked)return;
    const now=video.currentTime;const next=guards.find(g=>!completed.has(g.slide)&&g.at+EPS>=now);if(!next)return;
    timer=setTimeout(()=>{timer=null;checkPlayback();armTimer();},Math.max(20,(next.at-now)/Math.max(.1,video.playbackRate)*1000));
  }
  function frameLoop(){raf=null;if(video.paused)return;checkPlayback();if(!video.paused&&!activeGuard)raf=requestAnimationFrame(frameLoop);}
  function schedule(){armTimer();if(raf===null&&!video.paused&&!activeGuard)raf=requestAnimationFrame(frameLoop);}
  function jumpTo(index){
    hasInteracted=true;
    const c=chapters[Math.max(0,Math.min(index,chapters.length-1))];const wasPlaying=!video.paused&&!activeGuard;const target=c.start+.025;
    clearSchedules();if(target<video.currentTime-.1)resetFuture(target);clearPanel();
    setInternalTime(target,'chapter',wasPlaying);if(!wasPlaying)video.pause();
    history.replaceState(null,'',`#${c.anchor}`);
    document.getElementById('lesson-player').scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
    announcer.textContent=`Selected slide ${c.slide}: ${c.title}. ${wasPlaying?'Playback continues.':'Press play when ready.'}`;saveProgress(true);
  }
  links.forEach((a,i)=>a.addEventListener('click',e=>{e.preventDefault();jumpTo(i);}));
  document.querySelectorAll('[data-jump]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();jumpTo(Number(a.dataset.jump)-1);}));
  document.getElementById('previous-button').addEventListener('click',()=>jumpTo(currentIndex-1));
  document.getElementById('next-button').addEventListener('click',()=>jumpTo(currentIndex+1));
  continueButton.addEventListener('click',()=>{
    if(!activeGuard)return;const guard=activeGuard;completed.add(guard.slide);acknowledged.add(guard.slide);clearPanel();paintProgress();
    if(guard.slide===chapters.length){
      setInternalTime(Math.max(guard.at,chapters.at(-1).end-.05),'finish');video.pause();saveProgress(true);
      announcer.textContent='Recording finished. Verify Response received in the Session 5 form and retain your worksheet and Lab files. This player does not submit attendance.';
      document.getElementById('finish-title').scrollIntoView({block:'nearest'});return;
    }
    setInternalTime(chapters[guard.slide].start+.025,'continue',true);saveProgress(true);
    video.play().catch(()=>{announcer.textContent='Press play to continue.';});
  });
  autoPause.addEventListener('change',()=>{
    if(!autoPause.checked){clearSchedules();clearPanel();}lastVerifiedTime=video.currentTime;render(video.currentTime);schedule();saveProgress(true);
    announcer.textContent=autoPause.checked?'Activity pauses enabled.':'Activity pauses disabled. Pause manually at the worksheet instructions.';
  });
  video.addEventListener('play',()=>{
    hasInteracted=true;
    if(activeGuard&&autoPause.checked){video.pause();announcer.textContent='Attempt the activity or record your sticking point, then select Continue.';return;}lastVerifiedTime=video.currentTime;schedule();
  });
  video.addEventListener('pause',()=>{clearSchedules();saveProgress(true);});
  video.addEventListener('timeupdate',()=>{checkPlayback();armTimer();});
  video.addEventListener('ratechange',schedule);
  video.addEventListener('seeking',()=>{
    if(internalSeek&&Math.abs(video.currentTime-internalSeek.target)<.35)return;
    internalSeek=null;intendedResume=false;userSeeking=true;clearSchedules();
    if(video.currentTime<lastVerifiedTime-.1)resetFuture(video.currentTime);clearPanel();lastVerifiedTime=video.currentTime;render(video.currentTime);
  });
  video.addEventListener('seeked',()=>{
    const resume=intendedResume;const wasInternal=internalSeek!==null;internalSeek=null;userSeeking=false;intendedResume=false;lastVerifiedTime=video.currentTime;render(video.currentTime);
    if(wasInternal&&resume&&!activeGuard)video.play().catch(()=>{});schedule();saveProgress(true);
  });
  video.addEventListener('ended',()=>{
    clearSchedules();if(autoPause.checked&&!activeGuard){const g=guards.find(g=>!completed.has(g.slide)&&g.at+EPS>=lastVerifiedTime&&g.at<=video.currentTime+EPS);if(g)pauseFor(g);}saveProgress(true);
  });
  video.addEventListener('error',()=>{document.getElementById('video-error').hidden=false;});
  document.getElementById('fullscreen-button').addEventListener('click',async()=>{
    const stage=document.getElementById('video-stage');try{if(document.fullscreenElement)await document.exitFullscreen();else if(stage.requestFullscreen)await stage.requestFullscreen();else if(video.webkitEnterFullscreen)video.webkitEnterFullscreen();else announcer.textContent='Use the native video controls or rotate your device.';}catch(_){announcer.textContent='Full screen is unavailable. Continue watching in this page.';}
  });
  document.addEventListener('visibilitychange',()=>{if(document.hidden)saveProgress(true);else{checkPlayback();schedule();}});
  window.addEventListener('pagehide',()=>saveProgress(true));
  function selectHashChapter(){const anchor=location.hash.slice(1);const index=chapters.findIndex(c=>c.anchor===anchor||c.slide_id===anchor);if(index>=0)jumpTo(index);else render(video.currentTime);}
  video.addEventListener('loadedmetadata',selectHashChapter);window.addEventListener('hashchange',selectHashChapter);
  if(stored&&stored.time>2){
    document.getElementById('resume-description').textContent=`Your saved place is ${clock(stored.time)}, near slide ${indexAt(stored.time)+1}. Resume keeps the activity checklist stored in this browser. Explicit chapter links still open the selected slide.`;resumePanel.hidden=false;
  }
  function restorePlace(){
    if(!stored)return;hasInteracted=true;
    completed.clear();acknowledged.clear();for(const n of stored.completed)if(guards.some(g=>g.slide===n))completed.add(n);for(const n of stored.acknowledged)if(guards.some(g=>g.slide===n))acknowledged.add(n);
    autoPause.checked=stored.autoPause!==false;document.getElementById('captions-enabled').checked=stored.captions!==false;syncCaptions();
    video.pause();clearSchedules();clearPanel();paintProgress();
    const g=guards.find(x=>x.slide===stored.pending&&!completed.has(x.slide));
    if(g&&autoPause.checked){setInternalTime(g.at,'resume');pauseFor(g);}else setInternalTime(Math.min(stored.time,chapters.at(-1).end-.05),'resume');
    resumePanel.hidden=true;announcer.textContent='Saved place restored. Press play or complete the displayed activity.';
  }
  document.getElementById('resume-button').addEventListener('click',()=>{if(video.readyState===0)video.addEventListener('loadedmetadata',restorePlace,{once:true});else restorePlace();});
  document.getElementById('restart-button').addEventListener('click',()=>{stored=null;completed.clear();acknowledged.clear();paintProgress();clearPanel();video.pause();jumpTo(0);resumePanel.hidden=true;saveProgress(true);announcer.textContent='Started a new pass from slide 1.';});
  document.getElementById('download-transcript').addEventListener('click',()=>{
    const minutes=chapters.at(-1).end/60;
    const lines=['Week 5: Chemical equilibrium and routes to K','Independent lesson for 6 November 2026. Next in-person class: 13 November 2026.',`Recording: ${minutes.toFixed(1)} minutes. Add 128 minutes of work and a 10-minute break: ${(minutes+138).toFixed(1)} minutes total.`,'Use one worksheet and Lab 12. At each time limit, record the sticking point and continue. No extra required preparation or follow-up.',''];
    for(const c of chapters)lines.push(`SLIDE ${c.slide}: ${c.title}`,studyLabel(c),'',c.narration,'',`YOUR ACTION: ${c.cue}`,'');
    const url=URL.createObjectURL(new Blob([lines.join('\n')],{type:'text/plain;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='week05-narration-transcript.txt';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  const captionToggle=document.getElementById('captions-enabled');
  const captionRegion=document.getElementById('responsive-captions');
  const captionText=document.getElementById('responsive-caption-text');
  const captionElement=document.getElementById('english-caption-track');
  const narrowCaptions=window.matchMedia('(max-width: 900px)');
  let attachedCaptionTrack=null,nativeFullscreen=false,captionLoadFailed=false;
  function captionTrack(){return captionElement.track||video.textTracks?.[0]||null;}
  function captionsBelow(){return narrowCaptions.matches&&!nativeFullscreen&&document.fullscreenElement!==video&&!video.webkitDisplayingFullscreen;}
  function paintCaption(){
    if(captionRegion.hidden)return;const track=captionTrack();
    const text=[...(track?.activeCues||[])].map(c=>c.getCueAsHTML?c.getCueAsHTML().textContent:c.text).join(' ').replace(/\s+/g,' ').trim();
    const display=captionLoadFailed?'English captions could not be loaded. Read the transcript below.':text;if(captionText.textContent!==display)captionText.textContent=display;
  }
  function syncCaptions(){
    const track=captionTrack();const below=captionsBelow()&&captionToggle.checked;captionRegion.hidden=!below;document.getElementById('video-stage').setAttribute('data-captions-below',String(below));
    if(track){if(attachedCaptionTrack!==track){if(attachedCaptionTrack)attachedCaptionTrack.removeEventListener('cuechange',paintCaption);track.addEventListener('cuechange',paintCaption);attachedCaptionTrack=track;}const mode=captionToggle.checked?(below?'hidden':'showing'):'disabled';if(track.mode!==mode)track.mode=mode;}
    if(!below)captionText.textContent='';else paintCaption();
  }
  captionToggle.addEventListener('change',()=>{syncCaptions();saveProgress(true);});captionElement.addEventListener('load',()=>{captionLoadFailed=false;syncCaptions();});captionElement.addEventListener('error',()=>{captionLoadFailed=true;syncCaptions();});
  video.addEventListener('loadedmetadata',syncCaptions);video.addEventListener('seeked',paintCaption);window.addEventListener('resize',syncCaptions);if(narrowCaptions.addEventListener)narrowCaptions.addEventListener('change',syncCaptions);document.addEventListener('fullscreenchange',syncCaptions);
  video.addEventListener('webkitbeginfullscreen',()=>{nativeFullscreen=true;syncCaptions();});video.addEventListener('webkitendfullscreen',()=>{nativeFullscreen=false;syncCaptions();});
  if(video.textTracks?.addEventListener){video.textTracks.addEventListener('addtrack',syncCaptions);video.textTracks.addEventListener('change',()=>{const track=captionTrack();if(!captionsBelow()&&track&&(track.mode==='showing'||track.mode==='disabled'))captionToggle.checked=track.mode==='showing';syncCaptions();});}
  syncCaptions();paintProgress();render(0);
})();
