"""Build the supplemental Lab 01 video player from final audio/video metadata.

This is an English Week 1 supplement, not a new three-hour replacement lesson.
The source metadata supplies chapter boundaries and optional practice pauses.
"""
from pathlib import Path
import argparse
import html
import json
import math

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CHAPTERS = 14
PRACTICE_MINUTES = {3: 2, 13: 5}
DEFAULT_MANIFEST = ROOT / 'outputs/lab01-video/audio/manifest.json'
DEFAULT_TIMELINE = ROOT / 'outputs/lab01-video/timeline.json'
DEFAULT_OUTPUT = ROOT / 'outputs/lab01-video/lab01-video.html'


def clock(seconds):
    whole = int(seconds)
    return f'{whole // 60}:{whole % 60:02d}'


def normalize_records(raw):
    if isinstance(raw, list):
        return raw
    for key in ('chapters', 'slides', 'timeline'):
        if isinstance(raw.get(key), list):
            return raw[key]
    raise ValueError('Expected a list or a chapters, slides, or timeline array.')


def number(row):
    for key in ('chapter', 'slide', 'id'):
        if key in row:
            return int(row[key])
    raise ValueError('A chapter needs a sequential chapter, slide, or id number.')


def numeric(row, *keys):
    for key in keys:
        if key in row:
            value = float(row[key])
            if math.isfinite(value):
                return value
            raise ValueError(f'Nonfinite {key}.')
    raise ValueError(f'Missing numeric field: {keys}.')


def load_rows(manifest_path, timeline_path):
    manifest = normalize_records(json.loads(manifest_path.read_text(encoding='utf-8')))
    raw_timeline = json.loads(timeline_path.read_text(encoding='utf-8'))
    timeline = normalize_records(raw_timeline)
    if len(manifest) != EXPECTED_CHAPTERS or len(timeline) != len(manifest):
        raise ValueError(f'Expected {EXPECTED_CHAPTERS} final narration chapters and matching timeline.')
    rows = []
    for expected, (m, t) in enumerate(zip(manifest, timeline), 1):
        if number(m) != expected or number(t) != expected:
            raise ValueError('Narration and video chapter order disagree.')
        start = numeric(t, 'start_seconds', 'start', 'video_start_seconds')
        end = numeric(t, 'end_seconds', 'end', 'video_end_seconds')
        if start < 0 or end - start <= .3:
            raise ValueError(f'Chapter {expected}: invalid boundary.')
        previous = rows[-1]['end'] if rows else 0
        if abs(previous - start) > .01:
            raise ValueError(f'Chapter {expected}: gap or overlap in the timeline.')
        for key in ('title', 'narration'):
            if not isinstance(m.get(key), str) or not m[key].strip():
                raise ValueError(f'Chapter {expected}: nonempty {key} required.')
        if not isinstance(m.get('activity'), bool):
            raise ValueError(f'Chapter {expected}: explicit activity boolean required.')
        if 'activity' in t and t['activity'] != m['activity']:
            raise ValueError(f'Chapter {expected}: activity flags disagree.')
        if not isinstance(m.get('pause_instruction'), str):
            raise ValueError(f'Chapter {expected}: pause_instruction string required.')
        if m['activity'] and not m['pause_instruction'].strip():
            raise ValueError(f'Chapter {expected}: optional practice needs an instruction.')
        minutes = float(m.get('activity_minutes', 0))
        if not math.isfinite(minutes) or minutes < 0 or (not m['activity'] and minutes != 0):
            raise ValueError(f'Chapter {expected}: invalid optional practice minutes.')
        if m['activity']:
            narration_end = numeric(t, 'narration_end_seconds')
            if narration_end < start or narration_end > end - .24:
                raise ValueError(f'Chapter {expected}: practice pause could cut off narration.')
        if m.get('title') != t.get('title', m['title']):
            raise ValueError(f'Chapter {expected}: timeline title disagrees with narration.')
        for key in ('script_sha256', 'narration_sha256'):
            if key in m and key in t and m[key] != t[key]:
                raise ValueError(f'Chapter {expected}: stale narration hash.')
        rows.append(dict(chapter=expected, title=m['title'], narration=m['narration'],
            cue=m['pause_instruction'] or m.get('on_screen') or 'Follow the demonstration, then repeat the calculation in Lab 01.',
            start=start, end=end, activity=m['activity'], activity_minutes=minutes))
    if {r['chapter']: r['activity_minutes'] for r in rows if r['activity']} != PRACTICE_MINUTES:
        raise ValueError('Optional practice must be chapter 3 (2 min) and chapter 13 (5 min).')
    if isinstance(raw_timeline, dict) and 'duration_seconds' in raw_timeline:
        if abs(numeric(raw_timeline, 'duration_seconds') - rows[-1]['end']) > .05:
            raise ValueError('The final chapter does not match the video duration.')
    return rows


def build(manifest_path=DEFAULT_MANIFEST, timeline_path=DEFAULT_TIMELINE, output_path=DEFAULT_OUTPUT):
    rows = load_rows(manifest_path, timeline_path)
    chapters, transcripts = [], []
    for row in rows:
        n = row['chapter']; title = html.escape(row['title'])
        badge = '<span class="activity-dot">Optional pause</span>' if row['activity'] else ''
        chapters.append(f'<li><a class="chapter" href="#chapter-{n}" data-chapter="{n}" aria-label="Chapter {n}: {title}, recording {clock(row["start"])}"><span class="chapter-number">{n:02d}</span><span class="chapter-copy"><span>{title}</span><span class="chapter-meta"><time>{clock(row["start"])}</time>{badge}</span></span></a></li>')
        transcripts.append(f'<section aria-labelledby="transcript-chapter-{n}"><h3 id="transcript-chapter-{n}">Chapter {n}: {title}</h3><p class="control-note">Recording {clock(row["start"])}</p><p class="transcript-copy">{html.escape(row["narration"])}</p><p class="cue"><strong>Your action:</strong> {html.escape(row["cue"])}</p></section>')
    data = json.dumps(rows, ensure_ascii=False).replace('<', '\\u003c').replace('&', '\\u0026')
    practice = sum(r['activity_minutes'] for r in rows)
    replacements = {'@@STYLE@@': STYLE, '@@SCRIPT@@': PLAYER_SCRIPT, '@@DATA@@': data,
        '@@CHAPTERS@@': '\n'.join(chapters), '@@FULL_TRANSCRIPT@@': '\n'.join(transcripts),
        '@@DURATION@@': clock(rows[-1]['end']), '@@COUNT@@': str(len(rows)),
        '@@PAUSES@@': str(sum(r['activity'] for r in rows)), '@@PRACTICE_MINUTES@@': f'{practice:g}',
        '@@FIRST_TITLE@@': html.escape(rows[0]['title']), '@@FIRST_NARRATION@@': html.escape(rows[0]['narration']),
        '@@FIRST_CUE@@': html.escape(rows[0]['cue'])}
    rendered = TEMPLATE
    for key, value in replacements.items():
        rendered = rendered.replace(key, value)
    if '@@' in rendered:
        raise ValueError('Unresolved page placeholder.')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding='utf-8')
    print(f'Built {output_path}: {len(rows)} chapters; {clock(rows[-1]["end"])} recording; {practice:g} optional practice minutes.')

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
  // of covering the chapter. A hidden TextTrack remains active and fires cues.
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
  // Guard in the silent tail, before the next chapter's first video frame.
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
    return c.activity ? 'Optional practice checkpoint' : 'Week 1 supplemental demonstration';
  }
  function render(time) {
    const i = activeGuard ? activeGuard.chapter - 1 : indexAt(time);
    if (i === currentIndex) return;
    currentIndex = i;
    const c = chapters[i];
    document.getElementById('chapter-counter').textContent = `Chapter ${c.chapter} of ${chapters.length}`;
    document.getElementById('current-title').textContent = c.title;
    document.getElementById('lesson-time').textContent = studyLabel(c);
    document.getElementById('current-cue').textContent = c.cue;
    document.getElementById('transcript-title').textContent = `Transcript · Chapter ${c.chapter}`;
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
    for (const c of chapters) if (c.end > time) completed.delete(c.chapter);
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
    document.getElementById('pause-heading').textContent = `Try it yourself: Chapter ${guard.chapter}`;
    document.getElementById('pause-cue').textContent = guard.cue;
    document.getElementById('pause-budget').textContent = guard.activity_minutes > 0 ? `Optional practice: about ${guard.activity_minutes} minutes. The player does not resume automatically.` : 'Optional practice. Select Continue when you are ready; the player does not resume automatically.';
    continueButton.textContent = guard.chapter === chapters.length ? 'Finish demonstration' : 'Continue to next chapter';
    panel.hidden = false;
    // A delayed timeupdate can arrive beyond a boundary. Rewind to the activity,
    // never accept the solution chapter as though the pause had been completed.
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
      const crossed = guards.find(g => !completed.has(g.chapter) && g.at + EPS >= lastVerifiedTime && g.at <= now + EPS);
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
    const next = guards.find(g => !completed.has(g.chapter) && g.at + EPS >= now);
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
    history.replaceState(null, '', `#chapter-${c.chapter}`);
    document.getElementById('lesson-player').scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    announcer.textContent = `Selected Chapter ${c.chapter}: ${c.title}. ${wasPlaying ? 'Playback continues.' : 'Press play when ready.'}`;
  }
  links.forEach((link, i) => link.addEventListener('click', event => { event.preventDefault(); jumpTo(i); }));
  document.getElementById('previous-button').addEventListener('click', () => jumpTo(currentIndex - 1));
  document.getElementById('next-button').addEventListener('click', () => jumpTo(currentIndex + 1));
  continueButton.addEventListener('click', () => {
    if (!activeGuard) return;
    const guard = activeGuard;
    completed.add(guard.chapter);
    clearPanel();
    if (guard.chapter === chapters.length) {
      setInternalTime(Math.max(guard.at, chapters.at(-1).end - .05), 'finish');
      video.pause();
      announcer.textContent = 'End of the demonstration. Keep your calculations and saved Lab study for review. No repeat submission is needed.';
      document.getElementById('finish-title').scrollIntoView({block:'nearest'});
      return;
    }
    setInternalTime(chapters[guard.chapter].start + .025, 'continue', true);
    video.play().catch(() => { announcer.textContent = 'Press play to continue to the next chapter.'; });
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
      const missed = guards.find(g => !completed.has(g.chapter) && g.at + EPS >= lastVerifiedTime && g.at <= video.currentTime + EPS);
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
    const match = location.hash.match(/^#chapter-(\d+)$/);
    if (match && +match[1] >= 1 && +match[1] <= chapters.length) jumpTo(+match[1] - 1);
    else render(video.currentTime);
  });
  document.getElementById('download-transcript').addEventListener('click', () => {
    const lines = ['Lab 01: Ideal VLE, from inputs to a saved study', 'Week 1 supplemental demonstration. English synthetic male narration.', 'Optional pauses let you repeat the calculation in the Lab. No repeat submission is needed.', ''];
    for (const c of chapters) {
      lines.push(`CHAPTER ${c.chapter}: ${c.title}`, studyLabel(c), '', c.narration, '', `YOUR ACTION: ${c.cue}`, '');
    }
    const url = URL.createObjectURL(new Blob([lines.join('\n')], {type:'text/plain;charset=utf-8'}));
    const a = document.createElement('a'); a.href=url; a.download='lab01-narration-transcript.txt'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  render(0);
})();'''

TEMPLATE = r'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="A supplemental Week 1 walkthrough of Lab 01: ideal bubble and dew pressures, TP flash, component balances, pressure changes, and saving and reopening a JSON study. English narration and captions.">
<title>Lab 01 video: Ideal VLE walkthrough | 2105603</title>
<link rel="icon" href="/favicon.png"><link rel="canonical" href="https://www.skhgroup.net/teaching/2105603/lab01-video.html">
<link rel="stylesheet" href="labs/assets/palette.css"><style>@@STYLE@@</style>
</head><body>
<a class="skip-link" href="#lesson-player">Skip to demonstration</a>
<header class="site-header"><div class="wrap topbar"><a class="brand" href="./index.html">2105603 · Advanced Thermodynamics</a><a href="./postmidterm-01.html">Week 1 slides</a><a href="./labs/learning-path.html#session-1">Learning path</a></div></header>
<main class="wrap">
<section class="hero" aria-labelledby="page-title"><p class="eyebrow">Week 1 · Supplemental Lab demonstration</p><h1 id="page-title">Lab 01: Ideal VLE,<br>from inputs to a saved study</h1><p>Follow the actual Lab 01 screen from the initial setup through bubble and dew pressures, a TP flash, independent balance checks, and three pressure cases. Save the study as JSON, reopen it, restore a case, and calculate again.</p><div class="facts"><span class="fact"><strong>@@DURATION@@</strong> recording</span><span class="fact"><strong>@@COUNT@@</strong> chapters</span><span class="fact"><strong>@@PAUSES@@</strong> optional practice pauses</span><span class="fact">English male narration + captions</span></div></section>
<section class="start" aria-labelledby="start-title"><div><h2 id="start-title">Open the guide and Lab, then follow along</h2><ol><li>Open the <a href="./files/week01-lab-guide.pdf" target="_blank" rel="noopener">Week 1 Lab guide</a> and <a href="./labs/#experiment" target="_blank" rel="noopener">Lab 01</a> in separate tabs. Have a calculator and paper ready.</li><li>Follow the ideal-model setup shown in the video. Check the temperature, pressure, overall composition and units before each calculation.</li><li>Leave <strong>Optional practice pauses</strong> on to predict the two new pressure cases and attempt the final pressure case. Select <strong>Continue to next chapter</strong> when ready.</li><li>Keep your calculations and saved JSON together so you can reproduce the results later.</li></ol><div class="resource-links"><a href="./postmidterm-01.html" target="_blank" rel="noopener">Original Week 1 slides</a><a href="./labs/learning-path.html#session-1" target="_blank" rel="noopener">Week 1 learning path</a><a href="#full-transcript">Full transcript</a></div></div><div class="time-note"><h3>A supplement to our classroom lesson</h3><p>This walkthrough demonstrates the Lab that you explored independently after Week 1. It adds a guided screen demonstration to that lesson.</p><p style="margin-top:10px">The recording is <strong>@@DURATION@@</strong>. Two optional practice checkpoints add about <strong>@@PRACTICE_MINUTES@@ minutes</strong>; take longer whenever needed. You can turn the pauses off to watch first and repeat the steps afterward. No repeat exit-ticket or feedback submission is needed for this supplement.</p></div></section>
<div class="lesson-layout"><div class="main-column">
<section class="player-shell" id="lesson-player" aria-label="Lab 01 narrated screen demonstration" tabindex="-1">
<div class="video-stage" id="video-stage"><video id="lesson-video" controls playsinline preload="metadata" poster="./media/lab01/lab01-poster.png" aria-label="Ideal VLE: Lab 01 screen demonstration" aria-describedby="player-help"><source src="./media/lab01/lab01-demo.mp4" type="video/mp4"><track id="english-caption-track" kind="captions" src="./media/lab01/lab01-captions.vtt" srclang="en" label="English" default>Your browser cannot play this video. <a href="./media/lab01/lab01-demo.mp4">Download the demonstration</a> and use the guide and transcript.</video>
<div class="responsive-captions" id="responsive-captions" role="region" aria-label="English captions" hidden><span class="caption-label">English captions</span><p id="responsive-caption-text" aria-live="polite" aria-atomic="true"></p></div>
<div class="pause-panel" id="pause-panel" hidden><h2 id="pause-heading">Try it yourself</h2><p id="pause-cue"></p><p class="pause-budget" id="pause-budget"></p><div class="pause-actions"><button class="button primary" id="continue-button" type="button">Continue to next chapter</button><small>Your work is not submitted by this player.</small></div></div></div>
<div class="player-meta"><div class="player-topline"><span id="chapter-counter">Chapter 1 of @@COUNT@@</span><span id="lesson-time">Week 1 supplemental demonstration</span></div><p class="current-title" id="current-title">@@FIRST_TITLE@@</p><div class="player-controls"><label class="pause-toggle"><input id="auto-pause" type="checkbox" checked> Optional practice pauses</label><label class="pause-toggle caption-toggle"><input id="captions-enabled" type="checkbox" checked> Show English captions</label><div class="control-buttons"><button class="button" type="button" id="previous-button" disabled aria-label="Go to previous chapter">Previous</button><button class="button" type="button" id="next-button" aria-label="Go to next chapter">Next</button><button class="button" type="button" id="fullscreen-button">Full screen</button></div></div><p class="control-note" id="player-help">For small equations or controls, use Full screen and turn a phone sideways. Use the video controls to play, pause, change speed or set volume. On narrow screens, English captions appear below the image; in native video full screen, they appear inside the video. Chapter links deliberately jump to a new point. Optional practice pauses retain the current screen until you continue. In a downloaded MP4, pause manually when prompted.</p></div>
<div class="player-downloads"><a href="./media/lab01/lab01-demo.mp4" download="lab01-demo.mp4">Download MP4</a><a href="./media/lab01/lab01-captions.vtt" download="lab01-captions.vtt">English captions</a><a href="./files/week01-lab-guide.pdf" target="_blank" rel="noopener">Lab guide</a><a href="./labs/#experiment" target="_blank" rel="noopener">Open Lab 01</a></div>
<p class="error" id="video-error" hidden>The video could not be loaded. Use the download link, or follow the guide and transcript below.</p><noscript><p class="error">JavaScript is off. Video playback and captions still work, but automatic pauses and chapter navigation are unavailable. Pause manually when prompted. The complete transcript is available below.</p></noscript></section>
<section class="content-card action-card" aria-labelledby="action-title"><p class="label" id="action-title">Your action in this chapter</p><p id="current-cue">@@FIRST_CUE@@</p></section>
<details class="content-card transcript current-transcript" open><summary id="transcript-title">Transcript · Chapter 1</summary><p id="transcript-text">@@FIRST_NARRATION@@</p></details>
<div class="sr-only" id="announcer" role="status" aria-live="polite" aria-atomic="true"></div></div>
<nav class="chapter-card" aria-labelledby="chapters-title"><div class="chapter-header"><h2 id="chapters-title">Choose a chapter</h2><p>Timestamps refer to the recording. The optional pauses let you predict the two new pressure cases and attempt the final case before its self-check. On your first pass, follow the chapters in order.</p></div><ol class="chapters" id="chapters">@@CHAPTERS@@</ol></nav></div>
<section class="end-note" aria-labelledby="finish-title"><h2 id="finish-title">Keep a calculation you can reproduce</h2><p>Retain the ideal-model inputs, your total and component balance checks, and the comparison JSON. Reopening a JSON study restores the saved records. Restore a selected case and select Calculate to recompute the current results.</p><p>The <a href="./files/lab01-demo-comparison.json" download="lab01-demo-comparison.json">Three-case example JSON</a> is an optional reference containing the demonstrated cases. Save your own comparison JSON as you follow the steps; use the example if you want to inspect or reopen the demonstrated records.</p><p>In the final two chapters, attempt the 90 kPa case before opening the self-check. Record your prediction, calculation and any correction. This supplemental demonstration does not require another exit ticket or feedback submission.</p><div class="resource-links"><a href="./files/week01-lab-guide.pdf">Week 1 Lab guide</a><a href="./labs/#experiment">Lab 01: VLE and flash</a><a href="./postmidterm-01.html">Original Week 1 slides</a><a href="./labs/learning-path.html#session-1">Week 1 learning path</a></div></section>
<details class="content-card transcript-full" id="full-transcript"><summary>Full narration transcript · includes the checks</summary><p class="control-note">Attempt each practice checkpoint before reading its check. The text matches the narration. You can download it or print this page after expanding the transcript.</p><button class="button" type="button" id="download-transcript">Download transcript (.txt)</button>@@FULL_TRANSCRIPT@@</details>
</main><footer><div class="wrap">2105603 · Lab 01 supplemental walkthrough · Synthetic English male narration, generated for these teaching materials. Repeat the demonstrated steps at your own pace.</div></footer>
<script id="chapter-data" type="application/json">@@DATA@@</script><script>@@SCRIPT@@</script>
</body></html>'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--timeline', type=Path, default=DEFAULT_TIMELINE)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(args.manifest, args.timeline, args.output)
