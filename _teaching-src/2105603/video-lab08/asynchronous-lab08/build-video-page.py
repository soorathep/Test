#!/usr/bin/env python3
"""Build the public Lab 08 narrated walkthrough page from its exact audio timeline.

Run with the absolute research interpreter, for example:
  ~/.venvs/research/bin/python asynchronous-lab08/build-video-page.py

Only Python's standard library is required. The output embeds its styling,
chapter data, transcript and player behavior; MP4/poster/captions are separate
public media files under teaching/2105603/media/lab08/.
"""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
CANONICAL_URL = "https://www.skhgroup.net/teaching/2105603/lab08-video.html"


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def clock(seconds: float) -> str:
    """Round a display label only; seeking uses the exact timeline value."""
    whole = int(math.floor(seconds + 0.5))
    minutes, seconds = divmod(whole, 60)
    return f"{minutes}:{seconds:02d}"


def load_timeline(path: Path) -> tuple[float, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    duration = float(data["duration_seconds"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Timeline duration_seconds must be finite and positive")
    chapters = data["chapters"]
    if len(chapters) != 14:
        raise ValueError(f"Expected 14 chapters, found {len(chapters)}")
    previous_end = 0.0
    for number, chapter in enumerate(chapters, 1):
        if str(chapter["id"]) != f"{number:02d}":
            raise ValueError(f"Unexpected chapter id at position {number}")
        for key in ("title", "narration", "on_screen"):
            if not isinstance(chapter.get(key), str) or not chapter[key].strip():
                raise ValueError(f"Chapter {number} needs nonempty {key}")
        start, end = float(chapter["start_seconds"]), float(chapter["end_seconds"])
        if not (math.isfinite(start) and math.isfinite(end)):
            raise ValueError(f"Nonfinite time in chapter {number}")
        if start < 0 or end <= start or end > duration + 0.05:
            raise ValueError(f"Invalid start/end range in chapter {number}")
        if abs(start - previous_end) > 0.05:
            raise ValueError(f"Timeline is not contiguous at chapter {number}")
        previous_end = end
    if abs(previous_end - duration) > 0.05:
        raise ValueError("Final chapter does not match the total duration")
    return duration, chapters


STYLE = r"""
:root{--ink:#333f4a;--accent:#0f6e6b;--amber:#e29a2d;--sand:#dfc98f;--paper:#fff;--soft:#f3f6f5;--rule:#cbd5d2;--muted:#53616c}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:1280px;margin:auto;padding:28px 26px 52px}a{color:var(--accent);text-underline-offset:3px}a:focus-visible,button:focus-visible,summary:focus-visible,video:focus-visible{outline:3px solid var(--amber);outline-offset:4px}
h1,h2,h3{line-height:1.22}h1{font-size:clamp(2rem,5vw,3rem);margin:14px 0}h2{font-size:1.45rem;margin:0 0 12px}h3{font-size:1.08rem;margin:18px 0 7px}p{margin:9px 0}nav{font-size:.9rem}header{padding-bottom:22px;border-bottom:2px solid var(--accent)}.eyebrow{font-weight:700;color:var(--accent);font-size:.88rem;letter-spacing:.035em}.lede{font-size:1.1rem;max-width:850px}
.resources{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}.resources a,.action{padding:9px 14px;border:1px solid var(--accent);border-radius:5px;background:var(--paper);font:inherit;color:var(--accent);text-decoration:none;cursor:pointer}.resources a:first-child,.action.primary{background:var(--accent);color:var(--paper)}
.small{font-size:.9rem;color:var(--muted)}section{padding:25px 0;border-bottom:1px solid var(--rule)}ol,ul{padding-left:24px;margin:8px 0}li{margin:6px 0}.note{padding:12px 15px;background:var(--soft);border-left:3px solid var(--accent);margin:14px 0}.practice-note{border-left-color:var(--amber)}
.player-layout{display:grid;grid-template-columns:minmax(0,1fr);gap:22px;align-items:start}.player-column{min-width:0}video{display:block;width:100%;height:auto;aspect-ratio:16/9;background:var(--ink);border-radius:6px}video::cue{font-family:system-ui,sans-serif}.player-tools{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin:12px 0}.player-tools .action{font-size:.9rem}.progress-label{display:flex;justify-content:space-between;gap:10px;font-size:.9rem;margin-top:10px}progress{display:block;width:100%;height:10px;accent-color:var(--accent)}.now-playing{font-weight:600;margin-top:13px}.player-message:empty{display:none}.player-message{padding:10px 12px;border-left:3px solid var(--amber);background:var(--soft)}
.chapters h3{margin:0 0 10px}.chapter-list{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1px;max-height:none;overflow:hidden;border:1px solid var(--rule);border-radius:5px;background:var(--rule)}.chapter-list li{margin:0;min-width:0;background:var(--paper)}.chapter{display:grid;grid-template-columns:42px minmax(0,1fr);gap:10px;align-items:start;width:100%;height:100%;padding:11px 12px;border:0;background:var(--paper);color:var(--ink);text-align:left;font:inherit;font-size:.88rem;line-height:1.4;cursor:pointer}.chapter-list li:last-child .chapter{border-bottom:0}.chapter:hover{background:var(--soft)}.chapter[aria-current="true"]{background:var(--soft);box-shadow:inset 4px 0 var(--amber);font-weight:700}.chapter-time{color:var(--accent);font-variant-numeric:tabular-nums}.chapter-title{overflow-wrap:anywhere}
details{margin:12px 0;border:1px solid var(--rule);border-radius:5px}summary{padding:12px 15px;cursor:pointer;font-weight:600;color:var(--accent)}details[open]>summary{border-bottom:1px solid var(--rule)}.transcript-body{padding:4px 17px 17px}.transcript-body p{white-space:pre-line}.transcript-time{font-size:.9rem;font-weight:400;color:var(--muted)}.watch-for{font-size:.92rem;color:var(--muted)}.transcript-all>.transcript-body{padding:4px 15px 15px}.practice-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.practice-grid h3{margin-top:4px}footer{padding-top:22px;font-size:.9rem;color:var(--muted)}.skip{position:absolute;left:-9999px}.skip:focus{left:12px;top:12px;background:var(--paper);padding:10px;z-index:2}.visually-hidden{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
@media(max-width:900px){.chapter-list{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){main{padding:20px 18px 35px}body{font-size:16px}.resources{display:grid;grid-template-columns:1fr}.chapter-list{grid-template-columns:minmax(0,1fr)}.practice-grid{grid-template-columns:1fr;gap:12px}.player-tools{align-items:flex-start}.progress-label{font-size:.8rem}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@media print{main{padding:0;max-width:none}body{font-size:10pt}header,section{padding:12px 0}.player-layout,.skip,.resources,.player-message{display:none}details{break-inside:avoid}.practice-grid{display:block}a{color:var(--ink)}}
"""


PLAYER_SCRIPT = r"""
(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('chapter-data').textContent);
  const video = document.getElementById('lesson-video');
  const buttons = [...document.querySelectorAll('button.chapter')];
  const progress = document.getElementById('video-progress');
  const currentTime = document.getElementById('elapsed-time');
  const durationLabel = document.getElementById('total-time');
  const chapterLabel = document.getElementById('active-chapter');
  const message = document.getElementById('player-message');
  let chapterLimit = null;
  let active = -1;
  let request = 0;

  const clock = seconds => {
    const whole = Math.max(0, Math.floor(seconds));
    return `${Math.floor(whole / 60)}:${String(whole % 60).padStart(2, '0')}`;
  };
  const duration = () => Number.isFinite(video.duration) && video.duration > 0
    ? video.duration : data.duration_seconds;
  const bounded = time => Math.max(0, Math.min(time, Math.max(0, duration() - 0.01)));

  function update() {
    const time = Math.max(0, Math.min(video.currentTime || 0, duration()));
    progress.max = duration();
    progress.value = time;
    progress.setAttribute('aria-valuetext', `${clock(time)} of ${clock(duration())}`);
    currentTime.textContent = clock(time);
    durationLabel.textContent = clock(duration());
    let index = data.chapters.findIndex(c => time >= c.start_seconds && time < c.end_seconds);
    if (index < 0) index = time >= data.chapters.at(-1).end_seconds ? data.chapters.length - 1 : 0;
    if (index !== active) {
      active = index;
      buttons.forEach((button, i) => {
        if (i === index) button.setAttribute('aria-current', 'true');
        else button.removeAttribute('aria-current');
      });
      chapterLabel.textContent = `Chapter ${data.chapters[index].id}: ${data.chapters[index].title}`;
    }
  }

  function metadata() {
    if (video.readyState >= 1) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const cleanup = () => {
        video.removeEventListener('loadedmetadata', ready);
        video.removeEventListener('error', failed);
        window.clearTimeout(timer);
      };
      const ready = () => { cleanup(); resolve(); };
      const failed = () => { cleanup(); reject(new Error('Video metadata unavailable')); };
      const timer = window.setTimeout(failed, 20000);
      video.addEventListener('loadedmetadata', ready);
      video.addEventListener('error', failed);
      video.load();
    });
  }

  async function playFrom(index) {
    const thisRequest = ++request;
    message.textContent = '';
    try {
      await metadata();
      if (thisRequest !== request) return;
      const chapter = index === null ? null : data.chapters[index];
      chapterLimit = chapter;
      video.currentTime = bounded(chapter ? chapter.start_seconds : 0);
      update();
      await video.play();
    } catch (error) {
      if (thisRequest !== request) return;
      message.textContent = 'Playback could not start. Try the video play control, or use the download link below.';
    }
  }

  buttons.forEach(button => button.addEventListener('click', () => playFrom(Number(button.dataset.chapter))));
  document.getElementById('play-all').addEventListener('click', () => playFrom(null));
  video.addEventListener('loadedmetadata', update);
  video.addEventListener('durationchange', update);
  video.addEventListener('seeking', () => {
    if (chapterLimit && (video.currentTime < chapterLimit.start_seconds - 0.05
      || video.currentTime > chapterLimit.end_seconds + 0.05)) chapterLimit = null;
  });
  video.addEventListener('timeupdate', () => {
    if (chapterLimit && video.currentTime >= chapterLimit.end_seconds - 0.05) {
      const finished = chapterLimit;
      chapterLimit = null;
      video.pause();
      video.currentTime = bounded(Math.max(finished.start_seconds, finished.end_seconds - 0.02));
      message.textContent = `Chapter ${finished.id} finished. Pause to check your work, choose another chapter, or press play to continue.`;
    }
    update();
  });
  video.addEventListener('play', () => { message.textContent = ''; });
  video.addEventListener('ended', () => { chapterLimit = null; update(); });
  video.addEventListener('error', () => {
    message.textContent = 'The video is unavailable here. Open the online lesson or use the downloadable MP4. The transcript and resource links remain available.';
  });
  update();
})();
"""


def build_page(duration: float, chapters: list[dict]) -> str:
    chapter_buttons = []
    transcript_sections = []
    for index, chapter in enumerate(chapters):
        identifier = escape(chapter["id"])
        title = escape(chapter["title"])
        timing = f"{clock(float(chapter['start_seconds']))}–{clock(float(chapter['end_seconds']))}"
        chapter_buttons.append(
            f'<li><button class="chapter" type="button" data-chapter="{index}" '
            f'aria-label="Play chapter {identifier}: {title}, starting at {clock(float(chapter["start_seconds"]))}">'
            f'<span class="chapter-time">{clock(float(chapter["start_seconds"]))}</span>'
            f'<span class="chapter-title">{identifier}. {title}</span></button></li>'
        )
        pause = chapter.get("pause_instruction", "")
        pause_html = f'<p class="note practice-note"><strong>Your action:</strong> {escape(pause)}</p>' if pause else ""
        transcript_sections.append(
            f'<details id="transcript-{identifier}"><summary>{identifier}. {title} '
            f'<span class="transcript-time">{timing}</span></summary><div class="transcript-body">'
            f'<p>{escape(chapter["narration"])}</p>'
            f'<p class="watch-for"><strong>On screen:</strong> {escape(chapter["on_screen"])}</p>'
            f'{pause_html}</div></details>'
        )
    client_data = {
        "duration_seconds": duration,
        "chapters": [{key: chapter[key] for key in ("id", "title", "start_seconds", "end_seconds")} for chapter in chapters],
    }
    safe_json = json.dumps(client_data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lab 08 video: Excel to VLE model comparison | 2105603</title>
<meta name="description" content="A narrated screen walkthrough of Excel CSV export, Lab 08 import, an independent activity check, two model fits, and saved-study recovery. English captions and transcript included.">
<link rel="canonical" href="{CANONICAL_URL}">
<style>{STYLE}</style>
</head>
<body>
<a class="skip" href="#watch">Skip to the video</a>
<main>
<nav aria-label="Breadcrumb"><a href="./">2105603 course</a> / <a href="lab08-demo.html">Lab 08 walkthrough</a> / Video</nav>
<header>
<p class="eyebrow">LAB 08 · NARRATED SCREEN WALKTHROUGH</p>
<h1>From Excel to a VLE model comparison</h1>
<p class="lede">Watch the actual workbook and Lab controls, then repeat the workflow: export a CSV, import and check one observation, fit two models, and restore a saved study.</p>
<p><strong>Video: {clock(duration)} · 14 chapters.</strong> Allow about 20 minutes to work through the demonstration with pauses. The video runtime is shorter than the practice time.</p>
<p class="small">Synthetic teaching data throughout. Narrated with a synthetic male English voice. English captions and the full transcript are available below.</p>
<div class="resources" aria-label="Lesson resources">
<a href="files/lab08-demo.xlsx" download>Download Excel workbook</a>
<a href="files/lab08-demo-excel-export.csv" download>Download CSV exported from Excel</a>
<a href="labs/vle-input.html#vi-experiment">Open Lab 08</a>
<a href="lab08-demo.html">Open the step-by-step guide</a>
</div>
<div class="note"><strong>Prepare your workspace.</strong> Keep the workbook, Lab 08 and guide open. The workbook's <strong>VLE_data</strong> tab is the observation table to export; <strong>Demo</strong> contains the independent calculation. Using the supplied CSV lets you practice importing, but it does not practice the Excel export step.</div>
</header>

<section id="watch" aria-labelledby="watch-title">
<h2 id="watch-title">Watch, pause, and follow along</h2>
<p class="small" id="player-help">Select a chapter to play that section and pause at its end. Use “Play full video” for continuous playback, or the native video controls to pause, seek, change speed and enable captions. <strong>Use full screen to read worksheet formulas and numerical results.</strong></p>
<div class="player-layout">
<div class="player-column">
<video id="lesson-video" controls playsinline preload="metadata" poster="media/lab08/poster.jpg" aria-label="Lab 08 narrated screen demonstration" aria-describedby="player-help">
<source src="media/lab08/lab08-demo.mp4" type="video/mp4">
<track kind="captions" src="media/lab08/captions.vtt" srclang="en" label="English" default>
Your browser does not support this video. <a href="media/lab08/lab08-demo.mp4">Download the MP4</a> and use the transcript below.
</video>
<div class="progress-label"><label for="video-progress">Video progress</label><span><span id="elapsed-time">0:00</span> / <span id="total-time">{clock(duration)}</span></span></div>
<progress id="video-progress" max="{duration:.6f}" value="0" aria-label="Video progress">0%</progress>
<p id="active-chapter" class="now-playing" role="status" aria-live="polite">Chapter 01: {escape(chapters[0]['title'])}</p>
<p id="player-message" class="small player-message" role="status" aria-live="polite"></p>
<div class="player-tools"><button id="play-all" type="button" class="action primary">Play full video</button><span><a href="media/lab08/lab08-demo.mp4" download>Download MP4</a> · <a href="media/lab08/captions.vtt" download>Download captions</a></span></div>
<p class="small">The MP4 is a separate download from the course offline package. If playback is unavailable in a local copy, <a href="{CANONICAL_URL}">open the online lesson</a>.</p>
<noscript><p class="note">Chapter buttons require JavaScript. You can still play the video with its controls and use the chapter timestamps and transcript below.</p></noscript>
</div>
<aside class="chapters" aria-labelledby="chapters-title"><h3 id="chapters-title">Choose a chapter</h3><ol class="chapter-list">{''.join(chapter_buttons)}</ol></aside>
</div>
</section>

<section id="practice" aria-labelledby="practice-title">
<h2 id="practice-title">Pause and repeat the workflow</h2>
<p>Set aside about 20 minutes for your own attempt. Pause or replay any step you need. Keep your files and corrections with the original worksheet.</p>
<div class="practice-grid"><div><h3>Complete the steps</h3><ol>
<li>Export the active <strong>VLE_data</strong> worksheet as CSV, preserving all 19 observations.</li>
<li>Initialize the matching synthetic property setup, select your CSV, check units, and validate.</li>
<li>Check input row 11 using the <strong>Demo</strong> formulas. Compare gamma with <strong>EXP(table ln gamma)</strong>.</li>
<li>Fit Margules and NRTL using the same inputs. Save a study JSON and residual CSV for each model.</li>
<li>Load a saved JSON, restore its inputs, then validate and fit again.</li>
</ol></div><div><h3>Keep the conclusion within the evidence</h3><p>State one finding, give the numerical comparison with units, and explain one limitation. These observations were generated with NRTL, so close recovery of that model is expected. A small training error alone does not establish thermodynamic consistency or prediction on new observations.</p><div class="note practice-note"><strong>No new attendance task.</strong> This walkthrough is practice supporting the existing worksheet. Keep your own exported files and corrections; follow the instructor's existing submission arrangements.</div></div></div>
</section>

<section id="transcript" aria-labelledby="transcript-title">
<h2 id="transcript-title">Full English transcript</h2>
<p class="small">Open the transcript, then expand any chapter. The times are video timestamps, not the suggested working-time schedule.</p>
<details class="transcript-all"><summary>Read the complete transcript · 14 chapters</summary><div class="transcript-body">{''.join(transcript_sections)}</div></details>
</section>
<footer>2105603 · Advanced Chemical Engineering Thermodynamics · Synthetic teaching example. The observation CSV supplies data; complete study JSON preserves the setup and recorded results. Restore and recalculate before relying on saved outputs.</footer>
</main>
<script id="chapter-data" type="application/json">{safe_json}</script>
<script>{PLAYER_SCRIPT}</script>
</body>
</html>
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeline", type=Path, default=WORKSPACE / "outputs" / "lab08-video" / "audio" / "timeline.json")
    parser.add_argument("--output", type=Path, default=WORKSPACE / "outputs" / "lab08-video" / "lab08-video.html")
    args = parser.parse_args()
    duration, chapters = load_timeline(args.timeline)
    page = build_page(duration, chapters)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(page, encoding="utf-8")
    print(f"Wrote {args.output}: 14 chapters, video duration {clock(duration)}")


if __name__ == "__main__":
    main()
