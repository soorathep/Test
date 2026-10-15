#!/usr/bin/env python3
"""Build the dependency-free Session 2 video page from its audited audio and timeline.

Run using the research environment's absolute interpreter path. This builder writes
only week02-video.html; the video, poster, and timeline are prepared separately.
"""
from pathlib import Path
import argparse
import html
import json
import math

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'output/video/week02/week02-video.html'
ACTIVITY_SLIDES = {3, 5, 7, 9, 11, 13, 15, 16, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28}

def clock(seconds):
    seconds = int(seconds)
    return f'{seconds // 60}:{seconds % 60:02d}'

def normalize_timeline(raw):
    if isinstance(raw, list):
        return raw
    for key in ('slides', 'chapters', 'timeline'):
        if isinstance(raw.get(key), list):
            return raw[key]
    raise ValueError('Timeline must contain a slides, chapters, or timeline array.')

def get_number(row, keys):
    for key in keys:
        if key in row:
            return float(row[key])
    raise ValueError(f'Missing timeline field: {keys}; available: {list(row)}')

def build(manifest_path, timeline_path, output_path):
    manifest = json.loads(manifest_path.read_text())
    timeline = normalize_timeline(json.loads(timeline_path.read_text()))
    if len(manifest) != 28 or len(timeline) != 28:
        raise ValueError('Expected exactly 28 narration and timeline entries.')
    rows = []
    for m, t in zip(manifest, timeline):
        slide = int(m['slide'])
        if int(t.get('slide', slide)) != slide:
            raise ValueError('Timeline and narration slide order disagree.')
        start = get_number(t, ('start_seconds', 'start', 'video_start_seconds'))
        end = get_number(t, ('end_seconds', 'end', 'video_end_seconds'))
        if not math.isfinite(start + end) or end <= start:
            raise ValueError('Invalid timeline boundaries.')
        if rows and abs(rows[-1]['end'] - start) > .1:
            raise ValueError('Timeline has a gap or overlapping slides.')
        rows.append(dict(slide=slide, title=m['title'], narration=m['narration'],
                         cue=m['pause_instruction'], start=start, end=end,
                         lesson_start=m.get('stage_start_minute'),
                         lesson_end=m.get('stage_end_minute'),
                         activity=slide in ACTIVITY_SLIDES))
    total = rows[-1]['end']
    chapter_html = []
    for row in rows:
        title = row['title'].split(' · ')[0]
        badge = '<span class="activity-dot" aria-label="Activity pause">Pause</span>' if row['activity'] else ''
        chapter_html.append(f'''<li><a class="chapter" href="#slide-{row['slide']}" data-slide="{row['slide']}" aria-label="Slide {row['slide']}: {html.escape(title)}, video {clock(row['start'])}"><span class="chapter-number">{row['slide']:02d}</span><span class="chapter-copy"><span>{html.escape(title)}</span><span class="chapter-meta"><time>{clock(row['start'])}</time>{badge}</span></span></a></li>''')
    data = json.dumps(rows, ensure_ascii=False).replace('<', '\\u003c').replace('&', '\\u0026')
    first = rows[0]
    rendered = TEMPLATE.replace('@@CHAPTERS@@', '\n'.join(chapter_html)).replace('@@DATA@@', data)
    rendered = rendered.replace('@@DURATION@@', clock(total)).replace('@@FIRST_TITLE@@', html.escape(first['title']))
    rendered = rendered.replace('@@FIRST_NARRATION@@', html.escape(first['narration'])).replace('@@FIRST_CUE@@', html.escape(first['cue']))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered)
    print(f'Built {output_path}: {len(rows)} chapters, recording {clock(total)}, {len(ACTIVITY_SLIDES)} activity pauses.')

TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Session 2 independent thermodynamics lesson: narrated slides, guided calculations, Lab 08, and review activities. Allow about 180 minutes including independent work.">
<title>Session 2 video lesson | Advanced Thermodynamics</title>
<style>
:root{--teal:#0f6e6b;--teal-dark:#09524f;--amber:#e29a2d;--sand:#dfc98f;--graphite:#333f4a;--muted:#586572;--paper:#f5f7f7;--line:#d8e1e3;--white:#fff;--tint:#eaf4f3}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--graphite);background:var(--paper);font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--teal);text-underline-offset:.18em}a:hover{color:var(--teal-dark)}button,input{font:inherit}button,a,input{touch-action:manipulation}button{cursor:pointer}button:disabled{cursor:default;opacity:.5}button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--amber);outline-offset:4px}.skip-link{position:absolute;left:1rem;top:-5rem;background:var(--white);padding:.8rem;z-index:10}.skip-link:focus{top:1rem}.site-header{border-top:6px solid var(--teal);background:var(--white);border-bottom:1px solid var(--line)}.wrap{max-width:1440px;margin:0 auto;padding:0 32px}.topbar{display:flex;gap:20px;align-items:center;justify-content:space-between;padding-top:17px;padding-bottom:17px;font-size:.88rem}.brand{font-weight:750;letter-spacing:.02em}.topbar a{text-decoration:none}.hero{padding:35px 0 26px;max-width:950px}.eyebrow{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;font-weight:750;color:var(--teal);margin:0 0 10px}h1{font-size:clamp(1.8rem,3.5vw,2.85rem);line-height:1.15;letter-spacing:-.025em;margin:0 0 12px}h2{font-size:1.2rem;line-height:1.3;margin:0 0 12px}h3{font-size:1rem;margin:0 0 7px}p{margin:0 0 12px}.hero p{font-size:1.03rem;max-width:850px}.facts{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.fact{border:1px solid var(--line);background:var(--white);border-radius:24px;padding:6px 12px;font-size:.82rem}.fact strong{color:var(--teal)}.start{display:grid;grid-template-columns:1.3fr 1fr;gap:24px;margin-bottom:28px;background:var(--white);padding:22px 24px;border:1px solid var(--line);border-radius:12px}.start ol{padding-left:22px;margin:0}.start li+li{margin-top:5px}.start .time-note{background:var(--tint);padding:15px 18px;border-left:4px solid var(--teal);border-radius:6px}.start .time-note p{margin:0;font-size:.92rem}.resource-links{display:flex;gap:8px 18px;flex-wrap:wrap;margin-top:12px;font-size:.9rem}.lesson-layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:24px;align-items:start;margin-bottom:34px}.main-column{min-width:0}.player-shell{background:var(--white);border:1px solid var(--line);border-radius:12px;overflow:hidden}.video-stage{background:#1c242b}.video-stage video{display:block;width:100%;height:auto;aspect-ratio:16/9;background:#1c242b}.video-stage:fullscreen{display:flex;flex-direction:column;justify-content:center;overflow:auto;padding:0 2vw}.video-stage:fullscreen video{width:100%;max-height:80vh;object-fit:contain}.video-stage:fullscreen .pause-panel{flex-shrink:0;max-width:1000px;width:100%;align-self:center}.player-meta{padding:16px 20px 18px}.player-topline{display:flex;justify-content:space-between;gap:12px;font-size:.8rem;color:var(--muted);margin-bottom:8px}.current-title{margin:0 0 14px;font-size:1.2rem;font-weight:750;line-height:1.35}.player-controls{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.pause-toggle{display:flex;gap:9px;align-items:center;font-size:.9rem;font-weight:650;cursor:pointer}.pause-toggle input{width:19px;height:19px;accent-color:var(--teal)}.control-buttons{display:flex;gap:7px}.button{border:1px solid var(--line);background:var(--white);color:var(--graphite);border-radius:6px;padding:7px 11px;font-size:.84rem;min-height:38px}.button:hover{background:var(--tint);border-color:var(--teal)}.button.primary{background:var(--teal);border-color:var(--teal);color:var(--white);font-weight:700;padding:9px 14px}.button.primary:hover{background:var(--teal-dark)}.control-note{font-size:.79rem;color:var(--muted);margin:12px 0 0}.pause-panel{padding:18px 21px;background:#fff5df;color:var(--graphite);border-top:4px solid var(--amber)}.pause-panel[hidden]{display:none}.pause-panel h2{font-size:1.1rem;margin-bottom:7px}.pause-panel p{font-size:.94rem}.pause-panel .pause-actions{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.pause-panel small{font-size:.8rem;color:var(--muted)}.player-downloads{display:flex;gap:10px 20px;flex-wrap:wrap;border-top:1px solid var(--line);padding:12px 20px;font-size:.83rem}.content-card{margin-top:18px;padding:20px;border:1px solid var(--line);border-radius:10px;background:var(--white)}.action-card{border-left:4px solid var(--teal)}.action-card .label{color:var(--teal);font-size:.75rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase}.action-card p:last-child{margin-bottom:0}.transcript summary{font-weight:700;cursor:pointer}.transcript p{line-height:1.7;margin-top:12px;max-width:80ch}.chapter-card{background:var(--white);border:1px solid var(--line);border-radius:12px;overflow:hidden}.chapter-header{padding:17px 18px 13px;border-bottom:1px solid var(--line)}.chapter-header h2{margin-bottom:4px}.chapter-header p{font-size:.8rem;color:var(--muted);margin:0}.chapters{list-style:none;padding:0;margin:0;max-height:790px;overflow:auto;scrollbar-gutter:stable}.chapters li+li{border-top:1px solid #e8eded}.chapter{display:flex;align-items:flex-start;gap:12px;padding:12px 14px;text-decoration:none;color:var(--graphite);border-left:4px solid transparent;font-size:.87rem;line-height:1.35}.chapter:hover{background:#f1f8f7}.chapter[aria-current="true"]{background:var(--tint);border-left-color:var(--teal)}.chapter-number{font-variant-numeric:tabular-nums;font-weight:800;font-size:.8rem;color:var(--teal);min-width:21px;padding-top:2px}.chapter-copy{min-width:0;display:block}.chapter-meta{display:flex;align-items:center;gap:10px;margin-top:5px;font-size:.73rem;color:var(--muted)}.chapter-meta time{font-variant-numeric:tabular-nums}.activity-dot{font-size:.67rem;border:1px solid #d7bd80;background:#fff7e6;border-radius:12px;padding:1px 7px;color:#65501e}.end-note{padding:21px 24px;background:var(--white);border:1px solid var(--line);border-radius:12px;margin-bottom:30px}.end-note p{font-size:.92rem;max-width:105ch}.end-note p:last-child{margin-bottom:0}.error{padding:14px 20px;border-top:1px solid var(--line);color:#744815;background:#fff5df}.error[hidden]{display:none}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}footer{border-top:1px solid var(--line);padding:20px 0 30px;font-size:.8rem;color:var(--muted)}@media(max-width:1050px){.lesson-layout{grid-template-columns:minmax(0,1fr) 285px;gap:18px}.wrap{padding:0 22px}.start{gap:18px}.player-controls{align-items:flex-start}}@media(max-width:800px){.lesson-layout{grid-template-columns:1fr}.start{grid-template-columns:1fr}.chapter-card{order:2}.chapters{max-height:430px}.hero{padding-top:26px}.start{padding:19px}.wrap{padding:0 16px}.player-topline{flex-wrap:wrap}.player-meta{padding:14px 16px}.current-title{font-size:1.1rem}.topbar{font-size:.78rem}.chapter{padding:14px}.end-note{padding:19px}.hero p{font-size:.96rem}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{.site-header,.video-stage,.player-controls,.player-downloads,.chapter-card{display:none}.lesson-layout{display:block}.wrap{padding:0}.content-card,.start,.end-note{break-inside:avoid}body{background:#fff}}
</style>
</head>
<body>
<a class="skip-link" href="#lesson-player">Skip to video lesson</a>
<header class="site-header"><div class="wrap topbar"><a class="brand" href="./index.html">2105603 · Advanced Thermodynamics</a><a href="./labs/learning-path.html">Learning path</a></div></header>
<main class="wrap">
<section class="hero" aria-labelledby="page-title"><p class="eyebrow">Session 2 · Independent study</p><h1 id="page-title">Experimental VLE,<br>consistency and fitting</h1><p>Follow the narrated slides, stop to calculate, and investigate the same data in Lab 08. Start with the ideal-mixture ideas from Session 1; the activity coefficient is introduced here.</p><div class="facts"><span class="fact"><strong>180 min</strong> total study time</span><span class="fact"><strong>@@DURATION@@</strong> recording</span><span class="fact"><strong>28</strong> slides</span><span class="fact">English narration + transcript</span></div></section>
<section class="start" aria-labelledby="start-title"><div><h2 id="start-title">Start here</h2><ol><li>Open the <a href="./files/week02-practice.pdf" target="_blank" rel="noopener">four-page worksheet</a>. Keep it beside the video, or print it.</li><li>Prepare a calculator and paper. Start the video from Slide 1.</li><li>Leave <strong>Pause for activities</strong> on. Do the work, then select <strong>Continue to next slide</strong>.</li></ol><div class="resource-links"><a href="./postmidterm-02.html" target="_blank" rel="noopener">Open slide deck</a><a href="./files/postmidterm-02-slides.pdf" target="_blank" rel="noopener">Slides PDF</a><a href="./files/preclass-week-02.pdf" target="_blank" rel="noopener">Optional reading</a></div></div><div class="time-note"><h3>Video time is not lesson time</h3><p>The recording is about 25 minutes. Allow about <strong>3 hours</strong> including calculations, the Lab, a break, and review. Timing labels on the slides refer to <strong>elapsed study time</strong>. Pause as long as you need before continuing. Open <a href="./labs/vle-input.html#vi-experiment" target="_blank" rel="noopener">Lab 08</a> when you reach the Lab activity at study minute 100.</p></div></section>
<div class="lesson-layout">
<div class="main-column">
<section class="player-shell" id="lesson-player" aria-label="Narrated lesson video" tabindex="-1">
<div class="video-stage" id="video-stage"><video id="lesson-video" controls playsinline preload="metadata" poster="./media/week02/week02-poster.png" aria-label="Session 2 narrated slides" aria-describedby="player-help"><source src="./media/week02/week02-lecture.mp4" type="video/mp4">Your browser cannot play this video. <a href="./media/week02/week02-lecture.mp4">Download the recording</a> and use the slide deck and worksheet.</video>
<div class="pause-panel" id="pause-panel" hidden><h2 id="pause-heading">Pause and work</h2><p id="pause-cue"></p><div class="pause-actions"><button class="button primary" id="continue-button" type="button">Continue to next slide</button><small>Your work is not submitted by this player.</small></div></div></div>
<div class="player-meta"><div class="player-topline"><span id="slide-counter">Slide 1 of 28</span><span id="lesson-time">Lesson introduction</span></div><p class="current-title" id="current-title">@@FIRST_TITLE@@</p><div class="player-controls"><label class="pause-toggle"><input id="auto-pause" type="checkbox" checked> Pause for activities</label><div class="control-buttons"><button class="button" type="button" id="previous-button" disabled aria-label="Go to previous slide">Previous</button><button class="button" type="button" id="next-button" aria-label="Go to next slide">Next</button><button class="button" type="button" id="fullscreen-button">Full screen</button></div></div><p class="control-note" id="player-help">Use the video controls to play, pause, or change volume. Chapter links jump directly to a slide. Activity pauses keep the current slide visible until you continue.</p></div>
<div class="player-downloads"><a href="./media/week02/week02-lecture.mp4" download="week02-lecture.mp4">Download MP4</a><a href="./files/week02-practice.pdf" target="_blank" rel="noopener">Worksheet</a><a href="./labs/vle-input.html#vi-experiment" target="_blank" rel="noopener">Lab 08</a></div>
<p class="error" id="video-error" hidden>The video could not be loaded. Try the download link, or use the slide deck and transcript below.</p>
<noscript><p class="error">JavaScript is off. You can play the recording and open the documents, but automatic activity pauses and chapter navigation are unavailable. Pause manually when the narration asks you to work.</p></noscript>
</section>
<section class="content-card action-card" aria-labelledby="action-title"><p class="label" id="action-title">Your action on this slide</p><p id="current-cue">@@FIRST_CUE@@</p></section>
<details class="content-card transcript" open><summary id="transcript-title">Transcript · Slide 1</summary><p id="transcript-text">@@FIRST_NARRATION@@</p></details>
<div class="sr-only" id="announcer" role="status" aria-live="polite" aria-atomic="true"></div>
</div>
<nav class="chapter-card" aria-labelledby="chapters-title"><div class="chapter-header"><h2 id="chapters-title">Chapters</h2><p>Recording timestamps. Select a slide to review it.</p></div><ol class="chapters" id="chapters">@@CHAPTERS@@</ol></nav>
</div>
<section class="end-note" aria-labelledby="finish-title"><h2 id="finish-title">Finish the activities, then submit feedback</h2><p>Complete the worksheet, keep your original answers and corrections, and save the Lab exports. Attendance credit is for completing the activity, not a minimum test score. The instructor will provide the attendance submission route separately.</p><p>At the final slide, open the <a href="https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/?session=2" target="_blank" rel="noopener">Session 2 exit ticket and feedback form</a>. It is anonymous and <strong>does not identify attendance</strong>. Wait for “Response received.”</p></section>
</main>
<footer><div class="wrap">2105603 · Session 2 independent lesson · English synthetic narration. The recording does not replace the time spent calculating and working in the Lab.</div></footer>
<script id="chapter-data" type="application/json">@@DATA@@</script>
<script>
'use strict';
(() => {
  const chapters = JSON.parse(document.getElementById('chapter-data').textContent);
  const video = document.getElementById('lesson-video');
  const autoPause = document.getElementById('auto-pause');
  const panel = document.getElementById('pause-panel');
  const continueButton = document.getElementById('continue-button');
  const announcer = document.getElementById('announcer');
  const links = [...document.querySelectorAll('.chapter')];
  // Guard in the silent tail, before the next slide's first video frame.
  const guards = chapters.filter(c => c.activity).map(c => ({...c, at: c.end - 0.24}));
  const completed = new Set();
  let activeGuard = null;
  let currentIndex = -1;
  let lastVerifiedTime = 0;
  let timer = null;
  let raf = null;
  let internalSeek = null;
  let userSeeking = false;
  let intendedResume = false;
  const EPS = 0.012;

  function indexAt(time) {
    for (let i = chapters.length - 1; i >= 0; i--) if (time + .001 >= chapters[i].start) return i;
    return 0;
  }
  function render(time) {
    const i = activeGuard ? activeGuard.slide - 1 : indexAt(time);
    if (i === currentIndex) return;
    currentIndex = i;
    const c = chapters[i];
    document.getElementById('slide-counter').textContent = `Slide ${c.slide} of ${chapters.length}`;
    document.getElementById('current-title').textContent = c.title;
    document.getElementById('lesson-time').textContent = c.lesson_start === null ? 'Lesson introduction' : `Study time ${c.lesson_start}–${c.lesson_end} min`;
    document.getElementById('current-cue').textContent = c.cue;
    document.getElementById('transcript-title').textContent = `Transcript · Slide ${c.slide}`;
    document.getElementById('transcript-text').textContent = c.narration;
    document.getElementById('previous-button').disabled = i === 0;
    document.getElementById('next-button').disabled = i === chapters.length - 1;
    links.forEach((link, n) => n === i ? link.setAttribute('aria-current', 'true') : link.removeAttribute('aria-current'));
  }
  function clearSchedules() {
    if (timer !== null) clearTimeout(timer);
    if (raf !== null) cancelAnimationFrame(raf);
    timer = null; raf = null;
  }
  function clearPanel() { activeGuard = null; panel.hidden = true; }
  function resetFuture(time) {
    for (const c of chapters) if (c.end > time) completed.delete(c.slide);
  }
  function setInternalTime(time, kind, resume = false) {
    internalSeek = {target: time, kind};
    intendedResume = resume;
    lastVerifiedTime = time;
    video.currentTime = time;
    render(time);
  }
  async function exitNativeFullscreen() {
    try {
      if (document.fullscreenElement === video) await document.exitFullscreen();
      if (video.webkitDisplayingFullscreen && video.webkitExitFullscreen) video.webkitExitFullscreen();
    } catch (_) { /* The pause cue is also visible after leaving native full screen. */ }
  }
  function pauseFor(guard) {
    clearSchedules();
    activeGuard = guard;
    video.pause();
    document.getElementById('pause-heading').textContent = guard.slide === 28 ? 'Complete your exit ticket and feedback' : `Pause for Slide ${guard.slide}`;
    document.getElementById('pause-cue').textContent = guard.cue;
    continueButton.textContent = guard.slide === 28 ? 'Finish recording' : 'Continue to next slide';
    panel.hidden = false;
    // A delayed timeupdate can arrive beyond a boundary. Rewind to the activity,
    // never accept the solution slide as though the pause had been completed.
    if (Math.abs(video.currentTime - guard.at) > .015) setInternalTime(guard.at, 'guard');
    lastVerifiedTime = guard.at;
    render(guard.at);
    announcer.textContent = `Video paused. ${guard.cue} Select ${continueButton.textContent} when ready.`;
    exitNativeFullscreen();
  }
  function checkPlayback() {
    if (video.seeking || userSeeking || internalSeek || activeGuard) return;
    const now = video.currentTime;
    if (now + EPS < lastVerifiedTime) { resetFuture(now); lastVerifiedTime = now; }
    if (autoPause.checked && !video.paused) {
      const crossed = guards.find(g => !completed.has(g.slide) && g.at + EPS >= lastVerifiedTime && g.at <= now + EPS);
      if (crossed) { pauseFor(crossed); return; }
    }
    lastVerifiedTime = now;
    render(now);
  }
  function armTimer() {
    if (timer !== null) clearTimeout(timer);
    timer = null;
    if (video.paused || video.seeking || userSeeking || internalSeek || activeGuard || !autoPause.checked) return;
    const now = video.currentTime;
    const next = guards.find(g => !completed.has(g.slide) && g.at + EPS >= now);
    if (!next) return;
    const delay = Math.max(20, (next.at - now) / Math.max(.1, video.playbackRate) * 1000);
    timer = setTimeout(() => { timer = null; checkPlayback(); armTimer(); }, delay);
  }
  function frameLoop() {
    raf = null;
    if (video.paused) return;
    checkPlayback();
    if (!video.paused && !activeGuard) raf = requestAnimationFrame(frameLoop);
  }
  function schedule() {
    armTimer();
    if (raf === null && !video.paused && !activeGuard) raf = requestAnimationFrame(frameLoop);
  }
  function jumpTo(index) {
    const c = chapters[Math.max(0, Math.min(index, chapters.length - 1))];
    const wasPlaying = !video.paused && !activeGuard;
    const target = c.start + .025;
    clearSchedules();
    if (target < video.currentTime - .1) resetFuture(target);
    clearPanel();
    // Chapter selection is an intentional seek, not playback through all skipped activities.
    setInternalTime(target, 'chapter', wasPlaying);
    if (!wasPlaying) video.pause();
    history.replaceState(null, '', `#slide-${c.slide}`);
    announcer.textContent = `Selected Slide ${c.slide}: ${c.title}. ${wasPlaying ? 'Playback continues.' : 'Press play when ready.'}`;
  }
  links.forEach((link, i) => link.addEventListener('click', event => { event.preventDefault(); jumpTo(i); }));
  document.getElementById('previous-button').addEventListener('click', () => jumpTo(currentIndex - 1));
  document.getElementById('next-button').addEventListener('click', () => jumpTo(currentIndex + 1));
  continueButton.addEventListener('click', () => {
    if (!activeGuard) return;
    const guard = activeGuard;
    completed.add(guard.slide);
    clearPanel();
    if (guard.slide === chapters.length) {
      setInternalTime(Math.max(guard.at, chapters.at(-1).end - .05), 'finish');
      video.pause();
      announcer.textContent = 'End of the recording. Complete the exit ticket and keep your attendance work separately.';
      document.getElementById('finish-title').scrollIntoView({block:'nearest'});
      return;
    }
    setInternalTime(chapters[guard.slide].start + .025, 'continue', true);
    video.play().catch(() => { announcer.textContent = 'Press play to continue to the next slide.'; });
  });
  autoPause.addEventListener('change', () => {
    if (!autoPause.checked) { clearSchedules(); clearPanel(); }
    lastVerifiedTime = video.currentTime;
    render(video.currentTime);
    schedule();
    announcer.textContent = autoPause.checked ? 'Activity pauses enabled.' : 'Activity pauses disabled. Pause manually to complete the work.';
  });
  video.addEventListener('play', () => {
    if (activeGuard && autoPause.checked) { video.pause(); announcer.textContent = 'Complete the activity, then select the Continue button.'; return; }
    lastVerifiedTime = video.currentTime;
    schedule();
  });
  video.addEventListener('pause', clearSchedules);
  video.addEventListener('timeupdate', () => { checkPlayback(); armTimer(); });
  video.addEventListener('ratechange', schedule);
  video.addEventListener('seeking', () => {
    if (internalSeek && Math.abs(video.currentTime - internalSeek.target) < .35) return;
    internalSeek = null;
    intendedResume = false;
    userSeeking = true;
    clearSchedules();
    if (video.currentTime < lastVerifiedTime - .1) resetFuture(video.currentTime);
    clearPanel();
    lastVerifiedTime = video.currentTime;
    render(video.currentTime);
  });
  video.addEventListener('seeked', () => {
    const resume = intendedResume;
    const wasInternal = internalSeek !== null;
    internalSeek = null;
    userSeeking = false;
    intendedResume = false;
    lastVerifiedTime = video.currentTime;
    render(video.currentTime);
    if (wasInternal && resume && !activeGuard) video.play().catch(() => {});
    schedule();
  });
  video.addEventListener('ended', () => {
    clearSchedules();
    if (autoPause.checked && !completed.has(28) && !activeGuard) pauseFor(guards.at(-1));
  });
  video.addEventListener('error', () => { document.getElementById('video-error').hidden = false; });
  document.getElementById('fullscreen-button').addEventListener('click', async () => {
    const stage = document.getElementById('video-stage');
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (stage.requestFullscreen) await stage.requestFullscreen();
      else if (video.webkitEnterFullscreen) video.webkitEnterFullscreen();
      else announcer.textContent = 'Full screen is unavailable in this browser. Use the video controls or rotate your device.';
    } catch (_) { announcer.textContent = 'Full screen is unavailable. You can continue watching in this page.'; }
  });
  document.addEventListener('visibilitychange', () => { if (!document.hidden) { checkPlayback(); schedule(); } });
  video.addEventListener('loadedmetadata', () => {
    const match = location.hash.match(/^#slide-(\d+)$/);
    if (match && +match[1] >= 1 && +match[1] <= chapters.length) jumpTo(+match[1] - 1);
    else render(video.currentTime);
  });
  render(0);
})();
</script>
</body>
</html>
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, default=ROOT / 'output/audio/week02/manifest.json')
    parser.add_argument('--timeline', type=Path, default=ROOT / 'output/video/week02/timeline.json')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    build(args.manifest, args.timeline, args.output)
