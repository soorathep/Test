"""Build the optional Gibbs review page from measured video chapter boundaries.

Self-contained player with native captions, captions below narrow-screen video,
chapter seeking and optional pauses in the silent tail after each work prompt.
No fabricated timeline is accepted as a default. Media are built separately.
"""
from pathlib import Path
import argparse
import html
import json
import math

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'outputs/gibbs-review-video/week03-gibbs-review-video.html'
LESSON_SLIDES = 26
ACTIVITY_MINUTES = {7: 2, 12: 5, 15: 2, 18: 4, 19: 5, 22: 8, 25: 3}
DEMONSTRATIONS = {
    17: 'Open Lab 04 and set the metastable example',
    18: 'Read the Gibbs, curvature and TPD checks',
    20: 'Compare stable and unstable homogeneous feeds',
    23: 'Check the independent z = 0.35 calculation',
    24: 'Export JSON, reopen the study and recompute',
}


def clock(seconds):
    seconds = int(seconds)
    return f'{seconds // 60}:{seconds % 60:02d}'


def study_label(row):
    return (f'Suggested independent work: {row["activity_minutes"]:g} min'
            if row['activity'] else 'Optional Gibbs and stability review')


def normalize_manifest(raw):
    if isinstance(raw, list):
        return raw
    for key in ('slides', 'chapters', 'manifest'):
        if isinstance(raw.get(key), list):
            return raw[key]
    raise ValueError('Manifest must contain a slides, chapters, or manifest array.')


def build(manifest_path, timeline_path, output_path):
    manifest = normalize_manifest(json.loads(manifest_path.read_text()))
    measured = json.loads(timeline_path.read_text())
    if not isinstance(measured, dict) or not isinstance(measured.get('slides'), list):
        raise ValueError('Use the measured timeline object from the video pipeline.')
    timeline = measured['slides']
    if len(manifest) != LESSON_SLIDES or len(timeline) != LESSON_SLIDES:
        raise ValueError('The review requires exactly 26 narration entries and measured chapters.')
    duration = float(measured['duration_seconds'])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('A positive measured video duration is required.')
    rows = []
    for expected, (m, t) in enumerate(zip(manifest, timeline), 1):
        slide = int(m['slide'])
        if slide != expected or int(t['slide']) != slide:
            raise ValueError('Narration and timeline slide order disagree.')
        for key in ('title', 'narration'):
            if not isinstance(m.get(key), str) or not m[key].strip():
                raise ValueError(f'Slide {slide}: missing {key}.')
        if m['title'] != t['title']:
            raise ValueError(f'Slide {slide}: narration and timeline titles disagree.')
        start, end = float(t['start_seconds']), float(t['end_seconds'])
        narration_end = float(t['narration_end_seconds'])
        if not all(math.isfinite(n) for n in (start, end, narration_end)):
            raise ValueError('Nonfinite chapter timing.')
        if start < 0 or not start < narration_end <= end or end - start <= .3:
            raise ValueError('Invalid chapter or narration boundaries.')
        previous_end = rows[-1]['end'] if rows else 0
        if abs(previous_end - start) > .01:
            raise ValueError('Chapter timeline has a gap or overlap.')
        if not isinstance(m.get('activity'), bool) or t.get('activity') != m['activity']:
            raise ValueError('Activity flags must be explicit and agree.')
        if m['activity'] != (slide in ACTIVITY_MINUTES):
            raise ValueError('Activity flags differ from the review work stops.')
        minutes = float(m.get('activity_minutes', 0))
        if minutes != ACTIVITY_MINUTES.get(slide, 0) or float(t.get('activity_minutes', 0)) != minutes:
            raise ValueError('Review activity minutes disagree with the 29-minute plan.')
        cue = m.get('pause_instruction', '')
        if not isinstance(cue, str) or (m['activity'] and not cue.strip()):
            raise ValueError('Each activity needs a clear work instruction.')
        if m['activity'] and narration_end > end - .24:
            raise ValueError('Activity pause would interrupt the narration.')
        scenes = t.get('visual_scenes', [])
        actual_demo = any(scene.get('kind') == 'actual_lab_capture' for scene in scenes)
        if slide in DEMONSTRATIONS and not actual_demo:
            raise ValueError(f'Slide {slide}: real Lab capture is missing from the measured timeline.')
        rows.append(dict(slide=slide, title=m['title'], narration=m['narration'],
                         cue=cue or 'Listen and follow the calculation or demonstration.',
                         start=start, end=end, activity=m['activity'], activity_minutes=minutes,
                         demonstration=actual_demo))
    if abs(rows[-1]['end'] - duration) > .06:
        raise ValueError('Last chapter does not match the measured recording duration.')
    chapter_html, transcript_html = [], []
    for row in rows:
        badges = '<span class="activity-dot">Pause</span>' if row['activity'] else ''
        if row['demonstration']:
            badges += '<span class="activity-dot">Lab 04 demo</span>'
        title = html.escape(row['title'])
        chapter_html.append(f'<li><a class="chapter" href="#slide-{row["slide"]}" data-slide="{row["slide"]}" aria-label="Slide {row["slide"]}: {title}, recording {clock(row["start"])}"><span class="chapter-number">{row["slide"]:02d}</span><span class="chapter-copy"><span>{title}</span><span class="chapter-meta"><time>{clock(row["start"])}</time>{badges}</span></span></a></li>')
        transcript_html.append(f'<section aria-labelledby="transcript-slide-{row["slide"]}"><h3 id="transcript-slide-{row["slide"]}">Slide {row["slide"]}: {title}</h3><p class="control-note">Recording {clock(row["start"])} | {study_label(row)}</p><p class="transcript-copy">{html.escape(row["narration"])}</p><p class="cue"><strong>Your action:</strong> {html.escape(row["cue"])}</p></section>')
    demo_html = '\n'.join(f'<li><a href="#slide-{n}" data-demo-slide="{n}"><strong>{clock(rows[n-1]["start"])} · Slide {n}</strong>: {html.escape(title)}</a></li>' for n, title in DEMONSTRATIONS.items())
    data = json.dumps(rows, ensure_ascii=False).replace('<', '\\u003c').replace('&', '\\u0026')
    values = {'@@STYLE@@': STYLE, '@@SCRIPT@@': PLAYER_SCRIPT, '@@DATA@@': data,
              '@@CHAPTERS@@': '\n'.join(chapter_html), '@@FULL_TRANSCRIPT@@': '\n'.join(transcript_html),
              '@@DEMOS@@': demo_html, '@@DURATION@@': clock(duration), '@@COUNT@@': str(LESSON_SLIDES),
              '@@TOTAL_MINUTES@@': f'{duration / 60 + sum(ACTIVITY_MINUTES.values()):.1f}',
              '@@FIRST_TITLE@@': html.escape(rows[0]['title']),
              '@@FIRST_NARRATION@@': html.escape(rows[0]['narration']),
              '@@FIRST_CUE@@': html.escape(rows[0]['cue'])}
    rendered = TEMPLATE
    for key, value in values.items():
        rendered = rendered.replace(key, value)
    if '@@' in rendered:
        raise ValueError('Unresolved page placeholder.')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered)
    print(f'Built {output_path}: 26 chapters, recording {clock(duration)}, 7 optional work pauses, {sum(ACTIVITY_MINUTES.values())} independent-work minutes.')

STYLE = r''':root{--teal:var(--palette-teal);--teal-dark:var(--palette-graphite);--amber:var(--palette-amber);--sand:var(--palette-sand);--graphite:var(--palette-graphite);--muted:var(--palette-slate);--paper:var(--palette-paper);--line:var(--palette-mist);--white:white;--tint:color-mix(in srgb,var(--palette-teal) 8%,white)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--graphite);background:var(--paper);font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--teal);text-underline-offset:.18em}a:hover{color:var(--teal-dark)}button,input{font:inherit}button,a,input{touch-action:manipulation}button{cursor:pointer}button:disabled{cursor:default;opacity:.5}button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--amber);outline-offset:4px}.skip-link{position:absolute;left:1rem;top:-5rem;background:var(--white);padding:.8rem;z-index:10}.skip-link:focus{top:1rem}.site-header{border-top:6px solid var(--teal);background:var(--white);border-bottom:1px solid var(--line)}.wrap{max-width:1440px;margin:0 auto;padding:0 32px}.topbar{display:flex;gap:20px;align-items:center;justify-content:space-between;padding-top:17px;padding-bottom:17px;font-size:.88rem}.brand{font-weight:750;letter-spacing:.02em}.topbar a{text-decoration:none}.hero{padding:35px 0 26px;max-width:950px}.eyebrow{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;font-weight:750;color:var(--teal);margin:0 0 10px}h1{font-size:clamp(1.8rem,3.5vw,2.85rem);line-height:1.15;letter-spacing:-.025em;margin:0 0 12px}h2{font-size:1.2rem;line-height:1.3;margin:0 0 12px}h3{font-size:1rem;margin:0 0 7px}p{margin:0 0 12px}.hero p{font-size:1.03rem;max-width:850px}.facts{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.fact{border:1px solid var(--line);background:var(--white);border-radius:24px;padding:6px 12px;font-size:.82rem}.fact strong{color:var(--teal)}.start{display:grid;grid-template-columns:1.3fr 1fr;gap:24px;margin-bottom:28px;background:var(--white);padding:22px 24px;border:1px solid var(--line);border-radius:12px}.start ol{padding-left:22px;margin:0}.start li+li{margin-top:5px}.start .time-note{background:var(--tint);padding:15px 18px;border-left:4px solid var(--teal);border-radius:6px}.start .time-note p{margin:0;font-size:.92rem}.resource-links{display:flex;gap:8px 18px;flex-wrap:wrap;margin-top:12px;font-size:.9rem}.lesson-layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:24px;align-items:start;margin-bottom:34px}.main-column{min-width:0}.player-shell{background:var(--white);border:1px solid var(--line);border-radius:12px;overflow:hidden}.video-stage{background:var(--palette-ink)}.video-stage video{display:block;width:100%;height:auto;aspect-ratio:16/9;background:var(--palette-ink)}.video-stage:fullscreen{display:flex;flex-direction:column;justify-content:center;overflow:auto;padding:0 2vw}.video-stage:fullscreen video{width:100%;max-height:80vh;object-fit:contain}.video-stage:fullscreen .pause-panel{flex-shrink:0;max-width:1000px;width:100%;align-self:center}.player-meta{padding:16px 20px 18px}.player-topline{display:flex;justify-content:space-between;gap:12px;font-size:.8rem;color:var(--muted);margin-bottom:8px}.current-title{margin:0 0 14px;font-size:1.2rem;font-weight:750;line-height:1.35}.player-controls{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.pause-toggle{display:flex;gap:9px;align-items:center;font-size:.9rem;font-weight:650;cursor:pointer}.pause-toggle input{width:19px;height:19px;accent-color:var(--teal)}.control-buttons{display:flex;gap:7px}.button{border:1px solid var(--line);background:var(--white);color:var(--graphite);border-radius:6px;padding:7px 11px;font-size:.84rem;min-height:38px}.button:hover{background:var(--tint);border-color:var(--teal)}.button.primary{background:var(--teal);border-color:var(--teal);color:var(--white);font-weight:700;padding:9px 14px}.button.primary:hover{background:var(--teal-dark)}.control-note{font-size:.79rem;color:var(--muted);margin:12px 0 0}.pause-panel{padding:18px 21px;background:color-mix(in srgb,var(--sand) 35%,white);color:var(--graphite);border-top:4px solid var(--amber)}.pause-panel[hidden]{display:none}.pause-panel h2{font-size:1.1rem;margin-bottom:7px}.pause-panel p{font-size:.94rem}.pause-panel .pause-actions{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.pause-panel small{font-size:.8rem;color:var(--muted)}.player-downloads{display:flex;gap:10px 20px;flex-wrap:wrap;border-top:1px solid var(--line);padding:12px 20px;font-size:.83rem}.content-card{margin-top:18px;padding:20px;border:1px solid var(--line);border-radius:10px;background:var(--white)}.action-card{border-left:4px solid var(--teal)}.action-card .label{color:var(--teal);font-size:.75rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase}.action-card p:last-child{margin-bottom:0}.transcript summary{font-weight:700;cursor:pointer}.transcript p{line-height:1.7;margin-top:12px;max-width:80ch}.chapter-card{background:var(--white);border:1px solid var(--line);border-radius:12px;overflow:hidden}.chapter-header{padding:17px 18px 13px;border-bottom:1px solid var(--line)}.chapter-header h2{margin-bottom:4px}.chapter-header p{font-size:.8rem;color:var(--muted);margin:0}.chapters{list-style:none;padding:0;margin:0;max-height:790px;overflow:auto;scrollbar-gutter:stable}.chapters li+li{border-top:1px solid var(--line)}.chapter{display:flex;align-items:flex-start;gap:12px;padding:12px 14px;text-decoration:none;color:var(--graphite);border-left:4px solid transparent;font-size:.87rem;line-height:1.35}.chapter:hover{background:var(--tint)}.chapter[aria-current="true"]{background:var(--tint);border-left-color:var(--teal)}.chapter-number{font-variant-numeric:tabular-nums;font-weight:800;font-size:.8rem;color:var(--teal);min-width:21px;padding-top:2px}.chapter-copy{min-width:0;display:block}.chapter-meta{display:flex;align-items:center;gap:10px;margin-top:5px;font-size:.73rem;color:var(--muted)}.chapter-meta time{font-variant-numeric:tabular-nums}.activity-dot{font-size:.67rem;border:1px solid var(--sand);background:color-mix(in srgb,var(--sand) 20%,white);border-radius:12px;padding:1px 7px;color:var(--graphite)}.end-note{padding:21px 24px;background:var(--white);border:1px solid var(--line);border-radius:12px;margin-bottom:30px}.end-note p{font-size:.92rem;max-width:105ch}.end-note p:last-child{margin-bottom:0}.error{padding:14px 20px;border-top:1px solid var(--line);color:var(--graphite);background:color-mix(in srgb,var(--sand) 35%,white)}.error[hidden]{display:none}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}footer{border-top:1px solid var(--line);padding:20px 0 30px;font-size:.8rem;color:var(--muted)}@media(max-width:1050px){.lesson-layout{grid-template-columns:minmax(0,1fr) 285px;gap:18px}.wrap{padding:0 22px}.start{gap:18px}.player-controls{align-items:flex-start}}@media(max-width:800px){.lesson-layout{grid-template-columns:1fr}.start{grid-template-columns:1fr}.chapter-card{order:2}.chapters{max-height:430px}.hero{padding-top:26px}.start{padding:19px}.wrap{padding:0 16px}.player-topline{flex-wrap:wrap}.player-meta{padding:14px 16px}.current-title{font-size:1.1rem}.topbar{font-size:.78rem}.chapter{padding:14px}.end-note{padding:19px}.hero p{font-size:.96rem}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{.site-header,.video-stage,.player-controls,.player-downloads,.chapter-card{display:none}.lesson-layout{display:block}.wrap{padding:0}.content-card,.start,.end-note{break-inside:avoid}body{background:var(--white)}}
.lesson-layout{display:block}.chapter-card{margin-top:22px}.chapters{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));max-height:440px}.chapters li{min-width:0;border-top:1px solid var(--line)}.chapter{height:100%;overflow-wrap:anywhere}.transcript-full{margin-bottom:30px}.transcript-full section{padding:12px 0;border-top:1px solid var(--line);break-inside:avoid}.transcript-full .transcript-copy{white-space:pre-line}.transcript-full .cue{border-left:3px solid var(--amber);padding-left:12px}.resources-section{margin-bottom:24px}.resources-section ul{padding-left:20px}.pause-budget{font-size:.85rem;color:var(--muted);margin-top:8px}.chapter-card .chapter-header p{max-width:75ch}.pause-panel a{font-weight:700}video::cue{font-family:system-ui,sans-serif;font-size:clamp(12px,1.5vw,22px);line-height:1.25}@media(max-width:900px){.chapters{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.chapters{grid-template-columns:1fr}.control-buttons{flex-wrap:wrap}.resource-links{gap:9px 16px}.topbar{flex-wrap:wrap}}@media print{.transcript-full{display:block}.transcript-full>summary,.transcript-full button{display:none}.pause-panel,.content-card.action-card,.current-transcript{display:none}}.responsive-captions{background:var(--white);color:var(--graphite);padding:12px 18px;border-top:1px solid var(--line);font-size:1rem;line-height:1.55;flex-shrink:0;width:100%;margin:0 auto}.responsive-captions[hidden]{display:none}.responsive-captions .caption-label{display:block;font-size:.7rem;font-weight:750;letter-spacing:.06em;text-transform:uppercase;color:var(--teal);margin-bottom:4px}.responsive-captions p{margin:0;min-height:3.1em;white-space:pre-line;overflow-wrap:anywhere}.video-stage[data-captions-below="true"]:fullscreen video{max-height:62vh}.video-stage:fullscreen .responsive-captions{max-width:1000px}.caption-toggle{font-size:.86rem}@media print{.caption-toggle{display:none}}'''

PLAYER_SCRIPT = r''''use strict';
(() => {
  const chapters = JSON.parse(document.getElementById('chapter-data').textContent);
  const video = document.getElementById('lesson-video');
  const autoPause = document.getElementById('auto-pause');
  const panel = document.getElementById('pause-panel');
  const continueButton = document.getElementById('continue-button');
  const announcer = document.getElementById('announcer');
  const links = [...document.querySelectorAll('.chapter')];
  // On narrow screens, render the same timed VTT cues below the video instead
  // of covering the slide. A hidden TextTrack remains active and fires cues.
  const captionToggle = document.getElementById('captions-enabled');
  const captionRegion = document.getElementById('responsive-captions');
  const captionText = document.getElementById('responsive-caption-text');
  const captionElement = document.getElementById('english-caption-track');
  const narrowCaptions = window.matchMedia('(max-width: 900px)');
  let attachedCaptionTrack = null;
  let nativeFullscreen = false;
  let captionLoadFailed = false;
  function captionTrack() { return captionElement.track || video.textTracks?.[0] || null; }
  function captionsBelow() {
    return narrowCaptions.matches && !nativeFullscreen && document.fullscreenElement !== video && !video.webkitDisplayingFullscreen;
  }
  function paintCaption() {
    if (captionRegion.hidden) return;
    const track = captionTrack();
    const text = [...(track?.activeCues || [])].map(cue => cue.getCueAsHTML ? cue.getCueAsHTML().textContent : cue.text).join(' ').replace(/\s+/g, ' ').trim();
    const display = captionLoadFailed ? 'English captions could not be loaded. Read the transcript below.' : text;
    if (captionText.textContent !== display) captionText.textContent = display;
  }
  function syncCaptions() {
    const track = captionTrack();
    const below = captionsBelow() && captionToggle.checked;
    captionRegion.hidden = !below;
    document.getElementById('video-stage').setAttribute('data-captions-below', String(below));
    if (track) {
      if (attachedCaptionTrack !== track) {
        if (attachedCaptionTrack) attachedCaptionTrack.removeEventListener('cuechange', paintCaption);
        track.addEventListener('cuechange', paintCaption);
        attachedCaptionTrack = track;
      }
      const mode = captionToggle.checked ? (below ? 'hidden' : 'showing') : 'disabled';
      if (track.mode !== mode) track.mode = mode;
    }
    if (!below) captionText.textContent = '';
    else paintCaption();
  }
  captionToggle.addEventListener('change', syncCaptions);
  captionElement.addEventListener('load', () => { captionLoadFailed = false; syncCaptions(); });
  captionElement.addEventListener('error', () => { captionLoadFailed = true; syncCaptions(); });
  video.addEventListener('loadedmetadata', syncCaptions);
  video.addEventListener('seeked', paintCaption);
  window.addEventListener('resize', syncCaptions);
  if (narrowCaptions.addEventListener) narrowCaptions.addEventListener('change', syncCaptions);
  document.addEventListener('fullscreenchange', syncCaptions);
  video.addEventListener('webkitbeginfullscreen', () => { nativeFullscreen = true; syncCaptions(); });
  video.addEventListener('webkitendfullscreen', () => { nativeFullscreen = false; syncCaptions(); });
  if (video.textTracks?.addEventListener) {
    video.textTracks.addEventListener('addtrack', syncCaptions);
    video.textTracks.addEventListener('change', () => {
      const track = captionTrack();
      // Honor the browser's CC control on wide/native-fullscreen video. The
      // explicit page toggle controls narrow custom captions to avoid duplicates.
      if (!captionsBelow() && track && (track.mode === 'showing' || track.mode === 'disabled')) captionToggle.checked = track.mode === 'showing';
      syncCaptions();
    });
  }
  syncCaptions();
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
  function studyLabel(c) {
    return c.activity ? `Suggested independent work: ${c.activity_minutes} min` : 'Optional Gibbs and stability review';
  }
  function render(time) {
    const i = activeGuard ? activeGuard.slide - 1 : indexAt(time);
    if (i === currentIndex) return;
    currentIndex = i;
    const c = chapters[i];
    document.getElementById('slide-counter').textContent = `Slide ${c.slide} of ${chapters.length}`;
    document.getElementById('current-title').textContent = c.title;
    document.getElementById('lesson-time').textContent = studyLabel(c);
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
    document.getElementById('pause-heading').textContent = guard.slide === chapters.length ? 'Save your review work' : `Pause and work: Slide ${guard.slide}`;
    document.getElementById('pause-cue').textContent = guard.cue;
    document.getElementById('pause-budget').textContent = guard.activity_minutes > 0 ? `Suggested work: about ${guard.activity_minutes} minutes. Take longer if needed. The player does not resume automatically.` : 'Complete the instruction before continuing.';
    continueButton.textContent = guard.slide === chapters.length ? 'Finish lesson' : 'Continue to next slide';
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
    document.getElementById('lesson-player').scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    announcer.textContent = `Selected Slide ${c.slide}: ${c.title}. ${wasPlaying ? 'Playback continues.' : 'Press play when ready.'}`;
  }
  links.forEach((link, i) => link.addEventListener('click', event => { event.preventDefault(); jumpTo(i); }));
  document.querySelectorAll('[data-demo-slide]').forEach(link => link.addEventListener('click', event => { event.preventDefault(); jumpTo(Number(link.dataset.demoSlide) - 1); }));
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
      announcer.textContent = 'End of the review. Save your calculations and Lab export. No additional attendance or repeat exit-ticket submission is required.';
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
    if (autoPause.checked && !activeGuard) {
      const missed = guards.find(g => !completed.has(g.slide) && g.at + EPS >= lastVerifiedTime && g.at <= video.currentTime + EPS);
      if (missed) pauseFor(missed);
    }
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
  document.getElementById('download-transcript').addEventListener('click', () => {
    const lines = ['Reading Gibbs curves and checking stability', 'English synthetic male narration. Optional review with 29 minutes of suggested independent work in addition to the recording.', 'Attempt each calculation or prediction before consulting its check. No additional attendance or repeat exit-ticket submission is required.', ''];
    for (const c of chapters) {
      lines.push(`SLIDE ${c.slide}: ${c.title}`, studyLabel(c), '', c.narration, '', `YOUR ACTION: ${c.cue}`, '');
    }
    const url = URL.createObjectURL(new Blob([lines.join('\n')], {type:'text/plain;charset=utf-8'}));
    const a = document.createElement('a'); a.href=url; a.download='gibbs-review-transcript.txt'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  render(0);
})();'''

TEMPLATE = r'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Optional Gibbs energy and liquid stability review: worked calculations, English male narration, captions, and real-screen Lab 04 demonstrations with pauses to follow along.">
<title>Gibbs and stability review video | 2105603</title>
<link rel="icon" href="/favicon.png"><link rel="canonical" href="https://www.skhgroup.net/teaching/2105603/week03-gibbs-review-video.html">
<link rel="stylesheet" href="labs/assets/palette.css"><style>@@STYLE@@</style>
</head><body>
<a class="skip-link" href="#lesson-player">Skip to review video</a>
<header class="site-header"><div class="wrap topbar"><a class="brand" href="./index.html">2105603 · Advanced Thermodynamics</a><a href="./week03-study.html">Week 3 study route</a><a href="./week03-gibbs-review.html">Review slides</a></div></header>
<main class="wrap">
<section class="hero" aria-labelledby="page-title"><p class="eyebrow">Week 3 · Optional targeted review</p><h1 id="page-title">Reading Gibbs curves<br>and checking stability</h1><p>Work through the metastable liquid example one calculation at a time. Then follow real-screen Lab 04 demonstrations to compare Gibbs energy, local curvature and tangent-plane distance, change the feed, and reopen a saved JSON study.</p><div class="facts"><span class="fact"><strong>@@DURATION@@</strong> measured recording</span><span class="fact"><strong>29 min</strong> suggested independent work</span><span class="fact"><strong>@@COUNT@@</strong> slides</span><span class="fact">English male narration + captions</span></div></section>
<section class="start" aria-labelledby="start-title"><div><h2 id="start-title">Open the guide and Lab, then press play</h2><ol><li>Open the <a href="./files/week03-gibbs-review-guide.pdf" target="_blank" rel="noopener">four-page calculation and Lab 04 guide</a> and <a href="./labs/stability.html#lle-experiment" target="_blank" rel="noopener">Lab 04</a>. Have a calculator and paper ready.</li><li>Leave <strong>Pause for activities</strong> on. The player keeps the current slide visible until you select <strong>Continue to next slide</strong>.</li><li>Attempt the calculations and predictions before advancing to their checks. Follow the on-screen instructions and guide pages in order.</li><li>Keep your calculations, corrections and Lab JSON together. <strong>No additional attendance or repeat exit-ticket submission is required.</strong></li></ol><div class="resource-links"><a href="./week03-gibbs-review.html" target="_blank" rel="noopener">Review slide deck</a><a href="./files/week03-gibbs-review-slides.pdf" target="_blank" rel="noopener">Slides PDF</a><a href="#lab-demonstrations">Lab demonstration chapters</a><a href="#full-transcript">Full transcript</a></div></div><div class="time-note"><h3>Recording time and practice time are different</h3><p>The <strong>@@DURATION@@ recording is measured from the final video</strong>. Seven optional work stops add <strong>29 minutes</strong> of suggested calculation and practice: about <strong>@@TOTAL_MINUTES@@ minutes</strong> in total if you complete every stop. Take longer when needed. The recording does not include exercise-length silence.</p><p style="margin-top:10px">Use this review instead of repeating Week 3 steps you already understand. It supports the existing Week 3 lesson and adds no new required assignment. The original Week 3 study route remains available. The guide’s 45-minute estimate describes its read-and-practice route; use the measured recording plus work time shown here for the narrated route.</p></div></section>
<details class="content-card resources-section"><summary><strong>Follow the four-page guide</strong></summary><ul><li><strong>Guide page 1, A1-A3:</strong> distinguish consistency and stability, read the axes, and separate the local and global questions. Continue to <strong>page 2, B1-B2</strong> for the model and tangent contacts. Pause on slide 7 for 2 minutes.</li><li><strong>Guide page 2, B3-B5:</strong> phase amounts, component balance, homogeneous versus split Gibbs energy and tangent support. Pause on slide 12 for 5 minutes and slide 15 for 2 minutes.</li><li><strong>Guide page 3, C1-C2:</strong> compare the feed tangent with the common tangent, then repeat the Lab example. Pause on slides 18 and 19 for 4 and 5 minutes.</li><li><strong>Guide page 4, D1-D2:</strong> independently calculate the z = 0.35 case, check it in Lab 04, then attempt the self-check. Use <strong>page 3, C3</strong> for exporting and reopening the JSON study. Pause on slides 22 and 25 for 8 and 3 minutes.</li></ul><p class="control-note">The minutes above are suggested independent-work budgets. Chapter timestamps below are positions in the recording.</p></details>
<div class="lesson-layout"><div class="main-column">
<section class="player-shell" id="lesson-player" aria-label="Narrated Gibbs and stability review" tabindex="-1">
<div class="video-stage" id="video-stage"><video id="lesson-video" controls playsinline preload="metadata" poster="./media/gibbs-review/gibbs-review-poster.png" aria-label="Reading Gibbs curves and checking stability: narrated slides and Lab 04 demonstrations" aria-describedby="player-help"><source src="./media/gibbs-review/gibbs-review.mp4" type="video/mp4"><track id="english-caption-track" kind="captions" src="./media/gibbs-review/gibbs-review-captions.vtt" srclang="en" label="English" default>Your browser cannot play this video. <a href="./media/gibbs-review/gibbs-review.mp4">Download the recording</a> and use the slides and transcript.</video>
<div class="responsive-captions" id="responsive-captions" role="region" aria-label="English captions" hidden><span class="caption-label">English captions</span><p id="responsive-caption-text" aria-live="polite" aria-atomic="true"></p></div>
<div class="pause-panel" id="pause-panel" hidden><h2 id="pause-heading">Pause and work</h2><p id="pause-cue"></p><p class="pause-budget" id="pause-budget"></p><div class="pause-actions"><button class="button primary" id="continue-button" type="button">Continue to next slide</button><small>Your work is not submitted by this player.</small></div></div></div>
<div class="player-meta"><div class="player-topline"><span id="slide-counter">Slide 1 of @@COUNT@@</span><span id="lesson-time">Optional Gibbs and stability review</span></div><p class="current-title" id="current-title">@@FIRST_TITLE@@</p><div class="player-controls"><label class="pause-toggle"><input id="auto-pause" type="checkbox" checked> Pause for activities</label><label class="pause-toggle caption-toggle"><input id="captions-enabled" type="checkbox" checked> Show English captions</label><div class="control-buttons"><button class="button" type="button" id="previous-button" disabled aria-label="Go to previous slide">Previous</button><button class="button" type="button" id="next-button" aria-label="Go to next slide">Next</button><button class="button" type="button" id="fullscreen-button">Full screen</button></div></div><p class="control-note" id="player-help">For small equations, use Full screen and turn a phone sideways. Use the video controls to play, pause, change speed or set volume. On narrow screens, captions appear below the image; in native video full screen, they appear inside the video. Chapter links intentionally jump directly to a slide. Automatic activity pauses retain that slide until you continue. In a downloaded MP4 or with pauses off, pause manually when prompted.</p></div>
<div class="player-downloads"><a href="./media/gibbs-review/gibbs-review.mp4" download="gibbs-review.mp4">Download MP4</a><a href="./media/gibbs-review/gibbs-review-captions.vtt" download="gibbs-review-captions.vtt">English captions</a><a href="./media/gibbs-review/gibbs-review-transcript.txt" download="gibbs-review-transcript.txt">Narration transcript</a><a href="./files/week03-gibbs-review-guide.pdf" target="_blank" rel="noopener">Four-page guide</a><a href="./labs/stability.html#lle-experiment" target="_blank" rel="noopener">Open Lab 04</a></div>
<p class="error" id="video-error" hidden>The video could not be loaded. Use the download link, or continue with the review slides, guide and transcript below.</p><noscript><p class="error">JavaScript is off. Video playback and English captions still work, but automatic activity pauses and chapter navigation are unavailable. Pause manually before working and before the answers. The complete transcript is available below.</p></noscript></section>
<section class="content-card action-card" aria-labelledby="action-title"><p class="label" id="action-title">Your action on this slide</p><p id="current-cue">@@FIRST_CUE@@</p></section>
<details class="content-card transcript current-transcript" open><summary id="transcript-title">Transcript · Slide 1</summary><p id="transcript-text">@@FIRST_NARRATION@@</p></details>
<div class="sr-only" id="announcer" role="status" aria-live="polite" aria-atomic="true"></div></div>
<nav class="chapter-card" aria-labelledby="chapters-title"><div class="chapter-header"><h2 id="chapters-title">Choose a slide</h2><p>These timestamps refer to the recording. Pause badges mark independent work; Lab 04 demo badges mark actual screen captures. Complete predictions before opening their checks.</p></div><ol class="chapters" id="chapters">@@CHAPTERS@@</ol></nav></div>
<section class="content-card resources-section" id="lab-demonstrations" aria-labelledby="demos-title"><h2 id="demos-title">Follow the actual Lab 04 demonstrations</h2><ul>@@DEMOS@@</ul><p class="control-note">These links deliberately seek to the selected chapter. Preserve your predictions from slide 19 before viewing slide 20, and your independent calculation from slide 22 before viewing slide 23. All examples use the same synthetic binary liquid model, Margules with A = 3 at fixed temperature and pressure.</p></section>
<section class="content-card resources-section" aria-labelledby="resources-title"><h2 id="resources-title">Resources for this review</h2><div class="resource-links"><a href="./week03-gibbs-review.html">Interactive review slides</a><a href="./files/week03-gibbs-review-slides.pdf">Review slides PDF</a><a href="./files/week03-gibbs-review-guide.pdf">Calculation and Lab 04 guide · 4 pages</a><a href="./labs/stability.html#lle-experiment">Lab 04: Liquid stability and LLE</a><a href="./files/gibbs-review-lab04-study.json" download="gibbs-review-lab04-study.json">Download the synthetic demonstration study JSON</a><a href="./week03-study.html">Original Week 3 study route</a><a href="./week03-video.html">Original Week 3 video</a></div><p class="control-note">Separate phase composition x, overall feed composition z, and phase amount. Positive curvature is a local test; compare the homogeneous state with the globally supporting common tangent before declaring global stability. The downloadable JSON is the synthetic demonstration result for A = 3 and z = 0.35, not a student submission. Import it into the Lab workspace, restore it and recompute; use your own export for your calculations.</p></section>
<section class="end-note" aria-labelledby="finish-title"><h2 id="finish-title">Save your work and return to the Week 3 route</h2><p>Keep the attempted calculations, any corrections, and your Lab study JSON. Restore the saved study and select <strong>Find equilibrium →</strong> to recompute the result. Check the inputs and material balance after reopening.</p><p>This is optional targeted review. It adds no new required assignment, attendance test or repeat exit-ticket submission. Use the original Week 3 study route for any unfinished course activities.</p></section>
<details class="content-card transcript-full" id="full-transcript"><summary>Full narration transcript · includes checks and solutions</summary><p class="control-note">Attempt each calculation before reading its check. The text below matches the spoken narration. You can download it or print this page after expanding the transcript.</p><button class="button" type="button" id="download-transcript">Download transcript (.txt)</button>@@FULL_TRANSCRIPT@@</details>
</main><footer><div class="wrap">2105603 · Optional Gibbs and stability review · Synthetic English male narration generated for these teaching materials. Pause to calculate and reproduce the Lab examples.</div></footer>
<script id="chapter-data" type="application/json">@@DATA@@</script><script>@@SCRIPT@@</script>
</body></html>
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=ROOT / 'outputs/gibbs-review-video/manifest.json')
    parser.add_argument('--timeline', type=Path, default=ROOT / 'outputs/gibbs-review-video/timeline.json')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    build(args.manifest, args.timeline, args.output)
