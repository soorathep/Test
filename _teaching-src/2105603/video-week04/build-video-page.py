"""Build the Week 4 narrated lesson page from verified narration and video timing.

The recording's manifest and timing are verified unchanged. A separate current
study route replaces the recorded 20-minute H review with a questions-first
opening. Slide 36 offers an explicit optional-review choice, not required work.
Only this page is written; MP4, captions, narration and poster are unchanged.
Run with the absolute research interpreter path.
"""
from pathlib import Path
import argparse
import html
import json
import math

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUT=Path(__file__).resolve().parent/'week04-video.html'
LESSON_SLIDES=40
WORK_STOPS=(4,8,13,15,18,25,29,32,36,39)
ACTIVITY_MINUTES={4:8,8:6,13:10,15:5,18:22,20:10,25:10,29:5,32:24,36:20,39:10}
BREAK_SLIDE=20
OPENING_MINUTES=20
OPTIONAL_REVIEW_SLIDE=36
OPTIONAL_REVIEW_MINUTES=20


def apply_current_route(rows):
    """Keep recorded content, but distinguish this edition's required actions."""
    current=[]
    for source in rows:
        row=dict(source)
        row['recorded_cue']=row['cue']
        row['recorded_activity_minutes']=row['activity_minutes']
        row['optional_chapter']=35 <= row['slide'] <= 38
        row['optional_activity']=row['slide']==OPTIONAL_REVIEW_SLIDE
        if row['slide'] in (1,2,3):
            row['cue']='Current route: first complete the 20-minute questions page, then follow worksheet A–G with this video. H1–H4 is optional. Finish I and the Session 4 form.'
        elif row['optional_activity']:
            row['activity_minutes']=0
            row['cue']='H1–H4 is optional in the current route. The recording asks for a 20-minute attempt, but the required route now uses that time for the opening questions. Go to slide 39 for the exit ticket, or spend an extra 20 minutes on H1–H4 before its check.'
        elif row['optional_chapter']:
            row['cue']='Optional H review. Continue here only if you choose the extra H1–H4 practice. Otherwise select Go to exit ticket (slide 39). The recorded lesson is unchanged.'
        current.append(row)
    return current


def clock(seconds):
    seconds=int(seconds)
    return f'{seconds//60}:{seconds%60:02d}'


def study_label(row):
    if row.get('optional_chapter'):
        return 'Optional H review; outside the required work budget'
    if row['lesson_start'] is not None:
        return f'Study time {row["lesson_start"]}-{row["lesson_end"]} min'
    return 'Lesson introduction' if row['slide'] <= 3 else 'Follow the study route and activity cues'


def normalize_timeline(raw):
    if isinstance(raw,list):return raw
    for key in ('slides','chapters','timeline'):
        if isinstance(raw.get(key),list):return raw[key]
    raise ValueError('Timeline must contain a slides, chapters, or timeline array.')


def get_number(row,keys):
    for key in keys:
        if key in row:return float(row[key])
    raise ValueError(f'Missing timeline field: {keys}; available: {list(row)}')


def build(manifest_path,timeline_path,output_path):
    manifest=json.loads(manifest_path.read_text())
    timeline=normalize_timeline(json.loads(timeline_path.read_text()))
    if len(manifest)!=LESSON_SLIDES or len(timeline)!=len(manifest):
        raise ValueError(f'Expected {LESSON_SLIDES} revised narration entries and matching timeline; stale media must be rebuilt.')
    rows=[]
    for expected,(m,t) in enumerate(zip(manifest,timeline),1):
        slide=int(m['slide'])
        if slide!=expected or int(t.get('slide',slide))!=slide:
            raise ValueError('Timeline and narration slide order disagree.')
        start=get_number(t,('start_seconds','start','video_start_seconds'))
        end=get_number(t,('end_seconds','end','video_end_seconds'))
        if not math.isfinite(start+end) or start<0 or end-start<=.3:
            raise ValueError('Invalid timeline boundaries.')
        if (not rows and abs(start)>.001) or (rows and abs(rows[-1]['end']-start)>.01):
            raise ValueError('Timeline has a gap or overlapping slides.')
        if not isinstance(m.get('activity'),bool):
            raise ValueError(f'Slide {slide}: activity must be an explicit boolean.')
        if 'activity' in t and t['activity']!=m['activity']:
            raise ValueError('Timeline and narration activity flags disagree.')
        for key in ('title','narration'):
            if not isinstance(m.get(key),str) or not m[key].strip():
                raise ValueError(f'Slide {slide}: {key} must be nonempty.')
        if not isinstance(m.get('pause_instruction'),str):
            raise ValueError(f'Slide {slide}: pause_instruction must be a string.')
        if m['activity'] and not m['pause_instruction'].strip():
            raise ValueError(f'Slide {slide}: an activity needs its pause instruction.')
        cue=m['pause_instruction'] or 'Listen, then continue through the lesson.'
        if m['activity'] and 'narration_end_seconds' in t and float(t['narration_end_seconds'])>end-.24:
            raise ValueError(f'Slide {slide}: pause guard would interrupt narration.')
        minutes=float(m.get('activity_minutes',0))
        if not math.isfinite(minutes) or minutes<0:raise ValueError('Invalid activity budget.')
        lo=m.get('stage_start_minute');hi=m.get('stage_end_minute')
        if (lo is None)!=(hi is None):raise ValueError('Incomplete lesson-time range.')
        if lo is not None and not (0<=float(lo)<=float(hi)<=180):raise ValueError('Invalid study-time range.')
        rows.append(dict(slide=slide,title=m['title'],narration=m['narration'],cue=cue,start=start,end=end,lesson_start=lo,lesson_end=hi,activity=m['activity'],activity_minutes=minutes))
    # Validation only: the actual guard list below is derived from activity flags.
    for required in (*WORK_STOPS,BREAK_SLIDE):
        if not rows[required-1]['activity']:
            raise ValueError(f'Critical attempt, break or finish pause is missing at slide {required}.')
    if {r['slide'] for r in rows if r['activity']} != set(WORK_STOPS)|{BREAK_SLIDE}:
        raise ValueError('Activity flags do not match the revised work-stop contract.')
    if any(row['activity_minutes'] != ACTIVITY_MINUTES.get(row['slide'],0) for row in rows):
        raise ValueError('Activity budgets must match the Week 4 contract, including prediction stops at 15/29 before demonstrations at 16/30.')
    work_minutes=sum(rows[n-1]['activity_minutes'] for n in WORK_STOPS)
    break_minutes=rows[BREAK_SLIDE-1]['activity_minutes']
    if abs(work_minutes-120)>.01 or abs(break_minutes-10)>.01:
        raise ValueError('Revised plan requires 120 independent-work minutes and a 10-minute break.')
    rows=apply_current_route(rows)
    core_work_minutes=sum(r['activity_minutes'] for r in rows if r['slide']!=BREAK_SLIDE)
    if core_work_minutes!=100:
        raise ValueError('The current route must retain 100 core-work minutes.')
    planned_total=rows[-1]['end']/60+OPENING_MINUTES+core_work_minutes+break_minutes
    chapter_html=[];transcript_html=[]
    for row in rows:
        title=row['title'].split(' · ')[0]
        badge=('<span class="activity-dot">Optional choice</span>' if row['optional_activity'] else '<span class="activity-dot">Optional H review</span>' if row['optional_chapter'] else '<span class="activity-dot" aria-label="Activity pause">Pause</span>' if row['activity'] else '')
        if row['slide']==16:badge+='<span class="activity-dot">Lab 10 demo</span>'
        if row['slide']==30:badge+='<span class="activity-dot">Lab 11 demo</span>'
        chapter_html.append(f'<li><a class="chapter" href="#slide-{row["slide"]}" data-slide="{row["slide"]}" aria-label="Slide {row["slide"]}: {html.escape(title)}, recording {clock(row["start"])}"><span class="chapter-number">{row["slide"]:02d}</span><span class="chapter-copy"><span>{html.escape(title)}</span><span class="chapter-meta"><time>{clock(row["start"])}</time>{badge}</span></span></a></li>')
        study=study_label(row)
        transcript_html.append(f'<section aria-labelledby="transcript-slide-{row["slide"]}"><h3 id="transcript-slide-{row["slide"]}">Slide {row["slide"]}: {html.escape(row["title"])}</h3><p class="control-note">Recording {clock(row["start"])} | {study}</p><p class="transcript-copy">{html.escape(row["narration"])}</p><p class="cue"><strong>Current route action:</strong> {html.escape(row["cue"])}</p></section>')
    data=json.dumps(rows,ensure_ascii=False).replace('<','\\u003c').replace('&','\\u0026')
    replacements={'@@STYLE@@':STYLE,'@@SCRIPT@@':PLAYER_SCRIPT,'@@DATA@@':data,'@@CHAPTERS@@':'\n'.join(chapter_html),'@@FULL_TRANSCRIPT@@':'\n'.join(transcript_html),'@@DURATION@@':clock(rows[-1]['end']),'@@COUNT@@':str(len(rows)),'@@TOTAL_MINUTES@@':f'{planned_total:.1f}','@@FIRST_TITLE@@':html.escape(rows[0]['title']),'@@FIRST_NARRATION@@':html.escape(rows[0]['narration']),'@@FIRST_CUE@@':html.escape(rows[0]['cue'])}
    rendered=TEMPLATE
    for key,value in replacements.items():rendered=rendered.replace(key,value)
    if '@@' in rendered:raise ValueError('Unresolved page placeholder.')
    # Lab 03/04 references are intentional in the new questions-first opening.
    if any(value in TEMPLATE for value in ('week02','week03','session=2','session=3','attendance?','Q1–Q6','Q1-Q6','holiday')):raise ValueError('Stale course-specific template content.')
    output_path.parent.mkdir(parents=True,exist_ok=True);output_path.write_text(rendered)
    print(f'Built {output_path}: {len(rows)} unchanged chapters, recording {clock(rows[-1]["end"])}, opening {OPENING_MINUTES} min + core work {core_work_minutes:g} min + break {break_minutes:g} min; {planned_total:.1f} planned minutes, optional H adds 20 min.')

STYLE = r''':root{--teal:var(--palette-teal);--teal-dark:var(--palette-graphite);--amber:var(--palette-amber);--sand:var(--palette-sand);--graphite:var(--palette-graphite);--muted:var(--palette-slate);--paper:var(--palette-paper);--line:var(--palette-mist);--white:white;--tint:color-mix(in srgb,var(--palette-teal) 8%,white)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--graphite);background:var(--paper);font:16px/1.55 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--teal);text-underline-offset:.18em}a:hover{color:var(--teal-dark)}button,input{font:inherit}button,a,input{touch-action:manipulation}button{cursor:pointer}button:disabled{cursor:default;opacity:.5}button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--amber);outline-offset:4px}.skip-link{position:absolute;left:1rem;top:-5rem;background:var(--white);padding:.8rem;z-index:10}.skip-link:focus{top:1rem}.site-header{border-top:6px solid var(--teal);background:var(--white);border-bottom:1px solid var(--line)}.wrap{max-width:1440px;margin:0 auto;padding:0 32px}.topbar{display:flex;gap:20px;align-items:center;justify-content:space-between;padding-top:17px;padding-bottom:17px;font-size:.88rem}.brand{font-weight:750;letter-spacing:.02em}.topbar a{text-decoration:none}.hero{padding:35px 0 26px;max-width:950px}.eyebrow{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;font-weight:750;color:var(--teal);margin:0 0 10px}h1{font-size:clamp(1.8rem,3.5vw,2.85rem);line-height:1.15;letter-spacing:-.025em;margin:0 0 12px}h2{font-size:1.2rem;line-height:1.3;margin:0 0 12px}h3{font-size:1rem;margin:0 0 7px}p{margin:0 0 12px}.hero p{font-size:1.03rem;max-width:850px}.facts{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.fact{border:1px solid var(--line);background:var(--white);border-radius:24px;padding:6px 12px;font-size:.82rem}.fact strong{color:var(--teal)}.start{display:grid;grid-template-columns:1.3fr 1fr;gap:24px;margin-bottom:28px;background:var(--white);padding:22px 24px;border:1px solid var(--line);border-radius:12px}.start ol{padding-left:22px;margin:0}.start li+li{margin-top:5px}.start .time-note{background:var(--tint);padding:15px 18px;border-left:4px solid var(--teal);border-radius:6px}.start .time-note p{margin:0;font-size:.92rem}.resource-links{display:flex;gap:8px 18px;flex-wrap:wrap;margin-top:12px;font-size:.9rem}.lesson-layout{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:24px;align-items:start;margin-bottom:34px}.main-column{min-width:0}.player-shell{background:var(--white);border:1px solid var(--line);border-radius:12px;overflow:hidden}.video-stage{background:var(--palette-ink)}.video-stage video{display:block;width:100%;height:auto;aspect-ratio:16/9;background:var(--palette-ink)}.video-stage:fullscreen{display:flex;flex-direction:column;justify-content:center;overflow:auto;padding:0 2vw}.video-stage:fullscreen video{width:100%;max-height:80vh;object-fit:contain}.video-stage:fullscreen .pause-panel{flex-shrink:0;max-width:1000px;width:100%;align-self:center}.player-meta{padding:16px 20px 18px}.player-topline{display:flex;justify-content:space-between;gap:12px;font-size:.8rem;color:var(--muted);margin-bottom:8px}.current-title{margin:0 0 14px;font-size:1.2rem;font-weight:750;line-height:1.35}.player-controls{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.pause-toggle{display:flex;gap:9px;align-items:center;font-size:.9rem;font-weight:650;cursor:pointer}.pause-toggle input{width:19px;height:19px;accent-color:var(--teal)}.control-buttons{display:flex;gap:7px}.button{border:1px solid var(--line);background:var(--white);color:var(--graphite);border-radius:6px;padding:7px 11px;font-size:.84rem;min-height:38px}.button:hover{background:var(--tint);border-color:var(--teal)}.button.primary{background:var(--teal);border-color:var(--teal);color:var(--white);font-weight:700;padding:9px 14px}.button.primary:hover{background:var(--teal-dark)}.control-note{font-size:.79rem;color:var(--muted);margin:12px 0 0}.pause-panel{padding:18px 21px;background:color-mix(in srgb,var(--sand) 35%,white);color:var(--graphite);border-top:4px solid var(--amber)}.pause-panel[hidden]{display:none}.pause-panel h2{font-size:1.1rem;margin-bottom:7px}.pause-panel p{font-size:.94rem}.pause-panel .pause-actions{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.pause-panel small{font-size:.8rem;color:var(--muted)}.player-downloads{display:flex;gap:10px 20px;flex-wrap:wrap;border-top:1px solid var(--line);padding:12px 20px;font-size:.83rem}.content-card{margin-top:18px;padding:20px;border:1px solid var(--line);border-radius:10px;background:var(--white)}.action-card{border-left:4px solid var(--teal)}.action-card .label{color:var(--teal);font-size:.75rem;font-weight:800;letter-spacing:.07em;text-transform:uppercase}.action-card p:last-child{margin-bottom:0}.transcript summary{font-weight:700;cursor:pointer}.transcript p{line-height:1.7;margin-top:12px;max-width:80ch}.chapter-card{background:var(--white);border:1px solid var(--line);border-radius:12px;overflow:hidden}.chapter-header{padding:17px 18px 13px;border-bottom:1px solid var(--line)}.chapter-header h2{margin-bottom:4px}.chapter-header p{font-size:.8rem;color:var(--muted);margin:0}.chapters{list-style:none;padding:0;margin:0;max-height:790px;overflow:auto;scrollbar-gutter:stable}.chapters li+li{border-top:1px solid var(--line)}.chapter{display:flex;align-items:flex-start;gap:12px;padding:12px 14px;text-decoration:none;color:var(--graphite);border-left:4px solid transparent;font-size:.87rem;line-height:1.35}.chapter:hover{background:var(--tint)}.chapter[aria-current="true"]{background:var(--tint);border-left-color:var(--teal)}.chapter-number{font-variant-numeric:tabular-nums;font-weight:800;font-size:.8rem;color:var(--teal);min-width:21px;padding-top:2px}.chapter-copy{min-width:0;display:block}.chapter-meta{display:flex;align-items:center;gap:10px;margin-top:5px;font-size:.73rem;color:var(--muted)}.chapter-meta time{font-variant-numeric:tabular-nums}.activity-dot{font-size:.67rem;border:1px solid var(--sand);background:color-mix(in srgb,var(--sand) 20%,white);border-radius:12px;padding:1px 7px;color:var(--graphite)}.end-note{padding:21px 24px;background:var(--white);border:1px solid var(--line);border-radius:12px;margin-bottom:30px}.end-note p{font-size:.92rem;max-width:105ch}.end-note p:last-child{margin-bottom:0}.error{padding:14px 20px;border-top:1px solid var(--line);color:var(--graphite);background:color-mix(in srgb,var(--sand) 35%,white)}.error[hidden]{display:none}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}footer{border-top:1px solid var(--line);padding:20px 0 30px;font-size:.8rem;color:var(--muted)}@media(max-width:1050px){.lesson-layout{grid-template-columns:minmax(0,1fr) 285px;gap:18px}.wrap{padding:0 22px}.start{gap:18px}.player-controls{align-items:flex-start}}@media(max-width:800px){.lesson-layout{grid-template-columns:1fr}.start{grid-template-columns:1fr}.chapter-card{order:2}.chapters{max-height:430px}.hero{padding-top:26px}.start{padding:19px}.wrap{padding:0 16px}.player-topline{flex-wrap:wrap}.player-meta{padding:14px 16px}.current-title{font-size:1.1rem}.topbar{font-size:.78rem}.chapter{padding:14px}.end-note{padding:19px}.hero p{font-size:.96rem}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{.site-header,.video-stage,.player-controls,.player-downloads,.chapter-card{display:none}.lesson-layout{display:block}.wrap{padding:0}.content-card,.start,.end-note{break-inside:avoid}body{background:var(--white)}}
.lesson-layout{display:block}.chapter-card{margin-top:22px}.chapters{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));max-height:440px}.chapters li{min-width:0;border-top:1px solid var(--line)}.chapter{height:100%;overflow-wrap:anywhere}.transcript-full{margin-bottom:30px}.transcript-full section{padding:12px 0;border-top:1px solid var(--line);break-inside:avoid}.transcript-full .transcript-copy{white-space:pre-line}.transcript-full .cue{border-left:3px solid var(--amber);padding-left:12px}.resources-section{margin-bottom:24px}.resources-section ul{padding-left:20px}.pause-budget{font-size:.85rem;color:var(--muted);margin-top:8px}.chapter-card .chapter-header p{max-width:75ch}.pause-panel a{font-weight:700}video::cue{font-family:system-ui,sans-serif;font-size:clamp(12px,1.5vw,22px);line-height:1.25}@media(max-width:900px){.chapters{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.chapters{grid-template-columns:1fr}.control-buttons{flex-wrap:wrap}.resource-links{gap:9px 16px}.topbar{flex-wrap:wrap}}@media print{.transcript-full{display:block}.transcript-full>summary,.transcript-full button{display:none}.pause-panel,.content-card.action-card,.current-transcript{display:none}}'''

STYLE += r'''.responsive-captions{background:var(--white);color:var(--graphite);padding:12px 18px;border-top:1px solid var(--line);font-size:1rem;line-height:1.55;flex-shrink:0;width:100%;margin:0 auto}.responsive-captions[hidden]{display:none}.responsive-captions .caption-label{display:block;font-size:.7rem;font-weight:750;letter-spacing:.06em;text-transform:uppercase;color:var(--teal);margin-bottom:4px}.responsive-captions p{margin:0;min-height:3.1em;white-space:pre-line;overflow-wrap:anywhere}.video-stage[data-captions-below="true"]:fullscreen video{max-height:62vh}.video-stage:fullscreen .responsive-captions{max-width:1000px}.caption-toggle{font-size:.86rem}@media print{.caption-toggle{display:none}}'''

PLAYER_SCRIPT = r''''use strict';
(() => {
  const chapters = JSON.parse(document.getElementById('chapter-data').textContent);
  const video = document.getElementById('lesson-video');
  const autoPause = document.getElementById('auto-pause');
  const panel = document.getElementById('pause-panel');
  const continueButton = document.getElementById('continue-button');
  const optionalSkipButton = document.getElementById('optional-skip-button');
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
    if (c.optional_chapter) return 'Optional H review; outside the required work budget';
    if (c.lesson_start != null) return `Study time ${c.lesson_start}-${c.lesson_end} min`;
    return c.slide <= 3 ? 'Lesson introduction' : 'Follow the study route and activity cues';
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
    document.getElementById('optional-review-navigation').hidden = !c.optional_chapter;
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
  function clearPanel() { activeGuard = null; panel.hidden = true; optionalSkipButton.hidden = true; }
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
    document.getElementById('pause-heading').textContent = guard.optional_activity ? 'Optional practice: choose your route' : guard.slide === chapters.length ? 'Finish your feedback and save your work' : `Pause and work: Slide ${guard.slide}`;
    document.getElementById('pause-cue').textContent = guard.cue;
    document.getElementById('pause-budget').textContent = guard.optional_activity ? 'No additional work is required here. Optional H1–H4 adds about 20 minutes beyond the current required route. Choose explicitly; the player will not skip or resume by itself.' : guard.activity_minutes > 0 ? `Suggested work or break: about ${guard.activity_minutes} minutes, included in the planned lesson. The player does not resume automatically.` : 'This pause is included in the planned lesson. Complete the instruction before continuing.';
    continueButton.textContent = guard.optional_activity ? 'I completed optional H1–H4; show check' : guard.slide === chapters.length ? 'Finish lesson' : 'Continue to next slide';
    optionalSkipButton.hidden = !guard.optional_activity;
    panel.hidden = false;
    // A delayed timeupdate can arrive beyond a boundary. Rewind to the activity,
    // never accept the solution slide as though the pause had been completed.
    if (Math.abs(video.currentTime - guard.at) > .015) setInternalTime(guard.at, 'guard');
    lastVerifiedTime = guard.at;
    render(guard.at);
    announcer.textContent = guard.optional_activity ? 'Video paused at an optional activity. Choose Go to exit ticket, or complete optional H1–H4 before continuing.' : `Video paused. ${guard.cue} Select ${continueButton.textContent} when ready.`;
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
  document.getElementById('demo-start').addEventListener('click', event => { event.preventDefault(); jumpTo(15); });
  document.getElementById('demo-adsorption-start').addEventListener('click', event => { event.preventDefault(); jumpTo(29); });
  function skipOptionalReview() {
    if (activeGuard?.optional_activity) completed.add(activeGuard.slide);
    video.pause();
    jumpTo(38);
    announcer.textContent = 'Selected slide 39. H1–H4 was optional and has been skipped. Press play for the exit-ticket instructions.';
  }
  optionalSkipButton.addEventListener('click', skipOptionalReview);
  document.getElementById('optional-review-exit').addEventListener('click', skipOptionalReview);
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
      announcer.textContent = 'End of the recording. Finish the Session 4 anonymous exit ticket and feedback, wait for Response received, and save your worksheet and Lab exports.';
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
    if (activeGuard && autoPause.checked) { video.pause(); announcer.textContent = activeGuard.optional_activity ? 'Choose Go to exit ticket, or attempt optional H1–H4 and then show its check.' : 'Complete the activity, then select the Continue button.'; return; }
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
    const recordingMinutes = chapters.at(-1).end / 60;
    const lines = ['Week 4: Solid equilibria and adsorption', 'English synthetic male narration, unchanged from the original recording.', `Current route: complete the 20-minute questions page first. Core work A–G and I totals 100 minutes, plus a 10-minute break. The full recording is about ${recordingMinutes.toFixed(1)} minutes; the conservative total is about ${(recordingMinutes+130).toFixed(1)} minutes.`, 'H1–H4 is optional and adds about 20 minutes. Original narration still describes H as required. Follow CURRENT ROUTE ACTION below.', 'Attempt required questions, or any optional questions you choose, before consulting their answers.', ''];
    for (const c of chapters) {
      lines.push(`SLIDE ${c.slide}: ${c.title}`, studyLabel(c), '', c.narration, '', `CURRENT ROUTE ACTION: ${c.cue}`, '');
    }
    const url = URL.createObjectURL(new Blob([lines.join('\n')], {type:'text/plain;charset=utf-8'}));
    const a = document.createElement('a'); a.href=url; a.download='week04-narration-transcript.txt'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  render(0);
})();'''

TEMPLATE = r'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Week 4 narrated thermodynamics lesson: solid equilibria and adsorption, replacing class during the instructor’s ECS meeting, with guided pauses, English captions and actual Lab 10 and Lab 11 demonstrations. Begin with the current questions-first opening. Allow approximately three hours including core activities; H1-H4 is optional.">
<title>Week 4 video: Solid equilibria and adsorption | 2105603</title>
<link rel="icon" href="/favicon.png"><link rel="canonical" href="https://www.skhgroup.net/teaching/2105603/week04-video.html">
<link rel="stylesheet" href="labs/assets/palette.css"><style>@@STYLE@@</style>
</head><body>
<a class="skip-link" href="#lesson-player">Skip to video lesson</a>
<header class="site-header"><div class="wrap topbar"><a class="brand" href="./index.html">2105603 · Advanced Thermodynamics</a><a href="./week04-study.html">Week 4 study guide</a><a href="./labs/learning-path.html#session-4">Learning path</a></div></header>
<main class="wrap">
<section class="hero" aria-labelledby="page-title"><p class="eyebrow">Week 4 · Independent ECS replacement lesson</p><h1 id="page-title">Solid equilibria<br>and adsorption</h1><p>This independent lesson replaces class while the instructor attends the ECS meeting. Identify the phases and vessel constraints, calculate inventory balances, then follow the actual Lab 10 and Lab 11 demonstrations and repeat the investigations yourself.</p><div class="facts"><span class="fact"><strong>About 3 hours</strong> planned study route</span><span class="fact"><strong>@@DURATION@@</strong> recording</span><span class="fact"><strong>@@COUNT@@</strong> slides</span><span class="fact">English male narration + captions</span></div></section>
<section class="content-card resources-section" aria-labelledby="route-update-title"><h2 id="route-update-title">Start here: answers to your questions · 20 minutes</h2><p>Begin with the <a href="./week04-questions.html"><strong>Week 4 opening questions</strong></a>. Read the explanations, try the short calculations, and compare the stated results in Lab 03 and Lab 04 before starting this recording.</p><p><strong>This opening replaces the 20-minute H1–H4 review.</strong> Follow worksheet A–G, then I. H1–H4 and its recorded check on slides 35–38 are optional. At the optional stop, choose <strong>Go to exit ticket (slide 39)</strong> for the required route. This page updates the study instructions; it does not contain a new recording. The original audio, slide images, captions and timestamps are unchanged.</p></section>
<section class="start" aria-labelledby="start-title"><div><h2 id="start-title">After the opening questions, prepare your worksheet</h2><ol><li>Complete the <a href="./week04-questions.html">20-minute opening questions</a> first. Then open the <a href="./files/week04-practice.pdf" target="_blank" rel="noopener">six-page worksheet</a> and <a href="./files/week04-lab-guide.pdf" target="_blank" rel="noopener">four-page Lab guide</a>. Have a calculator and paper ready.</li><li>Leave <strong>Pause for activities</strong> on. The player keeps the current slide visible until you continue. Slide 36 offers a choice to skip optional H1–H4 and go to the exit ticket.</li><li>Complete A–G and I. Attempt each required question before its check. Only attempt H1–H4 if you choose the extra practice. Chapter links intentionally jump to the selected slide.</li><li>Finish with the existing Session 4 anonymous exit ticket and feedback.</li></ol><div class="resource-links"><a href="./postmidterm-04.html" target="_blank" rel="noopener">Slide deck</a><a href="./files/postmidterm-04-slides.pdf" target="_blank" rel="noopener">Slides PDF</a><a href="./week04-study.html" target="_blank" rel="noopener">Full study route</a><a href="#full-transcript">Full transcript</a><a id="demo-start" href="#slide-16">Jump to the Lab 10 demonstration</a><a id="demo-adsorption-start" href="#slide-30">Jump to the Lab 11 demonstration</a></div><p class="control-note">The demonstration links deliberately jump to chapters 16 and 30. Before opening the Lab 10 demonstration, complete D1 predictions at slide 15. Before opening the Lab 11 demonstration, complete F1-F3 predictions at slide 29. Independently rerun the investigations at slides 18 and 32.</p></div><div class="time-note"><h3>Recording time and study time are different</h3><p>The unchanged <strong>@@DURATION@@ recording</strong>, <strong>20-minute questions-first opening</strong>, <strong>100 minutes of core work and reflection</strong>, and a <strong>10-minute break</strong> total about <strong>@@TOTAL_MINUTES@@ minutes</strong>. This conservative estimate includes the full recording, even if you skip the optional H review. Completing H1–H4 adds about 20 minutes. Learner pace will vary. These are planning budgets, not measured completion times; MP4 chapter times remain unchanged.</p><p style="margin-top:10px">Complete the 5-minute prediction stops before Lab 10 on slide 16 and Lab 11 on slide 30. Use the 22-minute independent Lab 10 rerun at slide 18 and the 24-minute Lab 11 rerun at slide 32. Nine required video work stops total 100 minutes. Together with the 20-minute opening, this preserves 120 active minutes. Follow worksheet A–G, then I; H1–H4 is optional. Preserve predictions before checks.</p></div></section>
<details class="content-card resources-section"><summary><strong>Current route and required outputs</strong></summary><p class="control-note">Follow this order. Work budgets below exclude the associated recorded explanations; the measured recording is counted once in the total above.</p><ol><li><strong>Opening questions · 20 minutes:</strong> read <a href="./week04-questions.html">the answers to questions from Week 3</a>, calculate the short examples and compare with Lab 03/04. Then return here.</li><li><strong>A1–A3, B1–B2 and C1–C3 · 24 work minutes:</strong> worksheet pages 1–2. Classify processes, identify constraints, calculate saturated-liquid composition, then the finite GSE inventory and phase-presence condition.</li><li><strong>D1–D4 · 27 work minutes:</strong> page 3 and guide pages 1–2. Predict at slide 15, watch Lab 10 at 16, then rerun the three cases at 18, check balances and reopen a study.</li><li><strong>Break · 10 minutes:</strong> pause at slide 20.</li><li><strong>E1–E3, F1–F3 and G1–G4 · 39 work minutes:</strong> pages 4–5 and guide pages 3–4. Calculate uptake, predict at slide 29, watch Lab 11 at 30, then compare cases, check the balance and reopen a study at 32.</li><li><strong>I · 10 work minutes:</strong> page 6. Go to slide 39 for the Session 4 exit ticket and feedback. Continue to slide 40 to verify the receipt and save your work.</li></ol><p><strong>Optional:</strong> the H1–H4 case and check in slides 35–38 remain available. An independent attempt adds about 20 minutes; it is no longer required in this route. The original spoken instructions have not been re-recorded.</p></details>
<div class="lesson-layout"><div class="main-column">
<section class="player-shell" id="lesson-player" aria-label="Narrated Week 4 video lesson" tabindex="-1">
<div class="video-stage" id="video-stage"><video id="lesson-video" controls playsinline preload="metadata" poster="./media/week04/week04-poster.png" aria-label="Solid equilibria and adsorption: narrated slides" aria-describedby="player-help"><source src="./media/week04/week04-lecture.mp4" type="video/mp4"><track id="english-caption-track" kind="captions" src="./media/week04/week04-captions.vtt" srclang="en" label="English" default>Your browser cannot play this video. <a href="./media/week04/week04-lecture.mp4">Download the recording</a> and use the slides and transcript.</video>
<div class="responsive-captions" id="responsive-captions" role="region" aria-label="English captions" hidden><span class="caption-label">English captions</span><p id="responsive-caption-text" aria-live="polite" aria-atomic="true"></p></div>
<div class="pause-panel" id="pause-panel" hidden><h2 id="pause-heading">Pause and work</h2><p id="pause-cue"></p><p class="pause-budget" id="pause-budget"></p><div class="pause-actions"><button class="button primary" id="optional-skip-button" type="button" hidden>Go to exit ticket (slide 39)</button><button class="button primary" id="continue-button" type="button">Continue to next slide</button><small>Your work is not submitted by this player.</small></div></div></div>
<div class="player-meta"><div class="player-topline"><span id="slide-counter">Slide 1 of @@COUNT@@</span><span id="lesson-time">Lesson introduction</span></div><p class="current-title" id="current-title">@@FIRST_TITLE@@</p><div class="player-controls"><label class="pause-toggle"><input id="auto-pause" type="checkbox" checked> Pause for activities</label><label class="pause-toggle caption-toggle"><input id="captions-enabled" type="checkbox" checked> Show English captions</label><div class="control-buttons"><button class="button" type="button" id="previous-button" disabled aria-label="Go to previous slide">Previous</button><button class="button" type="button" id="next-button" aria-label="Go to next slide">Next</button><button class="button" type="button" id="fullscreen-button">Full screen</button></div></div><p class="control-note" id="player-help">For small equations, use Full screen and turn a phone sideways. Use the video controls to play, pause, change speed or set volume. Use Show English captions to toggle captions. On narrow screens, captions appear below the image; in native video full screen, they appear inside the video. Chapter links jump directly to a slide. Automatic activity pauses retain that slide until you continue. In a downloaded MP4 or with this option off, pause manually for the core tasks. Follow the current route above: the recorded H1–H4 task is optional.</p></div>
<div class="player-downloads"><a href="./media/week04/week04-lecture.mp4" download="week04-lecture.mp4">Download MP4</a><a href="./media/week04/week04-captions.vtt" download="week04-captions.vtt">English captions</a><a href="./files/week04-practice.pdf" target="_blank" rel="noopener">Worksheet</a><a href="./labs/solids.html#so-experiment" target="_blank" rel="noopener">Lab 10</a><a href="./labs/adsorption.html#ad-experiment" target="_blank" rel="noopener">Lab 11</a></div>
<p class="error" id="video-error" hidden>The video could not be loaded. Use the download link, or continue with the slides, worksheet and transcript below.</p><noscript><p class="error">JavaScript is off. Video playback and English captions still work, but automatic activity pauses and chapter navigation are unavailable. Pause manually before working and before the answers. The complete transcript is available below.</p></noscript></section>
<section class="content-card action-card" aria-labelledby="action-title"><p class="label" id="action-title">Your action on this slide</p><p id="current-cue">@@FIRST_CUE@@</p><div id="optional-review-navigation" hidden><p>This H review is optional. The current required route continues at slide 39.</p><button class="button" id="optional-review-exit" type="button">Go to exit ticket (slide 39)</button></div></section>
<details class="content-card transcript current-transcript" open><summary id="transcript-title">Transcript · Slide 1</summary><p id="transcript-text">@@FIRST_NARRATION@@</p></details>
<div class="sr-only" id="announcer" role="status" aria-live="polite" aria-atomic="true"></div></div>
<nav class="chapter-card" aria-labelledby="chapters-title"><div class="chapter-header"><h2 id="chapters-title">Choose a slide</h2><p>These timestamps refer to the recording. The Pause badge marks required work or a break. Optional H labels identify the extra review; the choice at slide 36 lets you go directly to slide 39. Start with the questions page and follow the current route.</p></div><ol class="chapters" id="chapters">@@CHAPTERS@@</ol></nav></div>
<section class="content-card resources-section" aria-labelledby="resources-title"><h2 id="resources-title">Resources for this lesson</h2><div class="resource-links"><a href="./week04-questions.html">Opening questions · start here</a><a href="./week04-study.html">Week 4 study guide</a><a href="./postmidterm-04.html">Interactive slides</a><a href="./files/week04-practice.pdf">Worksheet · 6 pages</a><a href="./files/week04-lab-guide.pdf">Lab guide · 4 pages</a><a href="./files/week04-solutions.pdf">Worked solutions · 4 pages, after your attempt</a><a href="./files/preclass-week-04.pdf">Optional background reading</a><a href="./labs/solids.html#so-experiment">Lab 10: Solid equilibria</a><a href="./labs/adsorption.html#ad-experiment">Lab 11: Adsorption equilibrium</a></div><p class="control-note">Keep the known-pressure example on slide 28 (total inventory 0.01400908 mol) separate from the Lab 11 investigation (0.0100 mol). Record partial versus total pressure, uptake per kg versus adsorbed amount, inputs, units and an independent balance.</p></section>
<section class="end-note" aria-labelledby="finish-title"><h2 id="finish-title">Finish the Session 4 reflection and feedback</h2><p>After the opening questions and worksheet A–G, complete I on page 6. H1–H4 is optional. At slide 39, open the <a href="https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/?session=4" target="_blank" rel="noopener"><strong>Session 4 exit ticket and feedback form</strong></a>.</p><p>Use the <strong>concept answer</strong> to explain the finite-inventory GSE condition and volatile partial pressure. In the <strong>evidence answer</strong>, include one Lab 10 comparison and one Lab 11 balance with settings, units and a limitation. Complete the reflection and feedback during the pause on slide 39. In the existing feedback text, include your actual study minutes and any pacing difficulty. Submit once and wait for <strong>Response received</strong>. Continue to slide 40 to verify the receipt and save your files; do not submit again.</p><p>The form is anonymous and <strong>does not identify individual attendance</strong>. The video player and Lab exports do not submit assignments. Keep your worksheet, original attempts, corrections and Lab exports or screenshots together. The planned work budgets already include this reflection and feedback. Keep actual recording time separate from the study-time guide.</p></section>
<details class="content-card transcript-full" id="full-transcript"><summary>Full narration transcript · includes checks and solutions</summary><p class="control-note">Attempt the worksheet questions before reading their checks. The narration text below matches the unchanged recording. Its original H1–H4 instructions are superseded by the separately labeled Current route action: that practice is optional. You can download the transcript with these route notes or print this page.</p><button class="button" type="button" id="download-transcript">Download transcript (.txt)</button>@@FULL_TRANSCRIPT@@</details>
</main><footer><div class="wrap">2105603 · Week 4 independent lesson · Synthetic English male narration. The voice is generated for these teaching materials. Begin with the questions page, then pause for the core calculations and Lab investigations. H1–H4 is optional; there is no additional compulsory homework.</div></footer>
<script id="chapter-data" type="application/json">@@DATA@@</script><script>@@SCRIPT@@</script>
</body></html>'''

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=ROOT/'outputs/week04-video/audio/manifest.json')
    parser.add_argument('--timeline',type=Path,default=ROOT/'outputs/week04-video/timeline.json')
    parser.add_argument('--output',type=Path,default=DEFAULT_OUT)
    args=parser.parse_args()
    build(args.manifest,args.timeline,args.output)
