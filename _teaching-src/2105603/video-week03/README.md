# Week 3 narrated lesson source

Reproducible source for **Thermodynamic consistency and liquid stability**, course 2105603. The 44-slide English lesson introduces consistency tests before liquid stability and LLE. Narration is synthetic US English male speech generated locally with **Kokoro v1.0, `am_michael`, speed `0.94`**. It is not a recording or imitation of the instructor.

## Restore the build layout

The website archive lives at `_teaching-src/2105603/video-week03/`. To rebuild, copy this directory to `asynchronous-week03/` immediately inside a working project directory. Scripts resolve their project root from that location, not from the current shell directory.

Required local inputs:

```text
project/
  asynchronous-week03/                 # this source package, including demo-scenes.json and demo-frames/
  output/pdf/postmidterm-03-slides.pdf  # audited 44-page slide PDF
  tmp/audio/kokoro-models/
    kokoro-v1.0.onnx
    voices-v1.0.bin
```

Also retain the matching website checkout, including `teaching/2105603/postmidterm-03.html`. Its slide IDs and order must match the PDF and narration. The published PDF is `teaching/2105603/files/postmidterm-03-slides.pdf`; copy it to the input location above. Rendering the slide deck itself is outside this video package.

Use the research Python environment at `$HOME/.venvs/research/bin/python`, Python 3.12, and a Node.js executable for controller tests. Install the pinned Python dependencies with:

```sh
uv pip install --python "$HOME/.venvs/research/bin/python" -r asynchronous-week03/requirements.txt
```

The local `skh_palette` module must be importable; it supplies the Teal-Amber Lab Palette. It is not a PyPI dependency in this requirements file. The model and voice files must already be installed locally. This package does not download them or grant redistribution rights to them.

## Run order

Run from the working project directory. Replace the website checkout path below with the actual checkout.

```sh
"$HOME/.venvs/research/bin/python" asynchronous-week03/prepare-narration.py --site "$HOME/Documents/GitHub/WEBSITE_REPOSITORY"
"$HOME/.venvs/research/bin/python" asynchronous-week03/build-narration.py
"$HOME/.venvs/research/bin/python" asynchronous-week03/calibrate-activities.py
"$HOME/.venvs/research/bin/python" asynchronous-week03/build-video.py
"$HOME/.venvs/research/bin/python" asynchronous-week03/build-video-page.py
"$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" asynchronous-week03/test-player.mjs --require-media-timeline --output outputs/week03-video/player-controller-qa.json
```

Use another absolute Node executable path if that bundled runtime is unavailable.

1. `prepare-narration.py` validates all slide IDs against the website HTML and derives `narration.json` from `narration-draft.json`. Review any source changes before synthesis; this step overwrites the normalized narration.
2. `build-narration.py` produces 44 mono 24 kHz PCM WAV segments, a concatenated master, sentence captions, manifest, timing and audio QA under `outputs/week03-video/audio/`. It caches sentences under `tmp/audio/week03-male/`, keyed by spoken text, settings and model/voice hashes. Pronunciation aliases affect speech while captions preserve the original wording.
3. `calibrate-activities.py` checks the revised fixed budgets: **115 minutes of independent work/reflection plus a ten-minute break**. The intended recording budget is approximately 55 minutes, but the page reports the actual recording duration and its sum with those 125 minutes. Do not inflate work budgets to hide a short recording. Run this step after narration and before video/page builds; it does not change the speech.
4. `build-video.py` adds a two-second silent tail after each segment, renders complete slides inside the top 920 pixels of a 1920 × 1080 frame, and reserves a 160-pixel graphite caption band. It writes H.264/AAC MP4, poster, adjusted WebVTT captions, timing and video QA under `outputs/week03-video/`. The actual Lab 03 interface demonstration occupies chapters 19-25; `demo-scenes.json` maps captured frames in `demo-frames/` to narration sentence prefixes. Keep those reviewed synthetic-data captures with the source. The optional reopen demonstration uses the Lab's shared Study workspace to load its own synthetic-case JSON, restore inputs and rerun the modeling test. Imported comparison results remain recorded evidence, not a fresh calculation. No student data is used. No activity-length filler silence is encoded. The MP4 must be below 100 MB; the script stops otherwise.
5. `build-video-page.py` combines the calibrated manifest with video timing into `week03-video.html`. It does not render media. Caption, poster and MP4 paths are relative to the published course directory.
6. `test-player.mjs` tests the actual controller with minimal fake DOM/media events. `--require-media-timeline` uses the final timing metadata. Without this flag, missing metadata triggers an explicitly labeled synthetic timing fixture. Use `--fixture` explicitly while only the old media exists; it uses revised narration sources with artificial 20-second intervals and does not generate media. These tests are not browser, audiovisual or rendering QA.

To repeat media validation without encoding, use `build-video.py --validate-only`. It requires the original inputs, rendered slide images, PCM master and unchanged final manifest. Changing the manifest after building invalidates its recorded hash; rebuild video and page after such changes.

## Timing, pauses and verification

Slide headings describe elapsed **study time**, while chapter timestamps describe the shorter recording. The route is 0-15 review A; 15-40 Gibbs-Duhem/path B; 40-65 hand calculations C; 65-95 Lab 03 D/E; 95-105 break; 105-155 LLE F/G; 155-170 unseen review H; 170-180 reflection/feedback I. The worksheet has six pages, the guide four and the solutions four. Default-on activity pauses derive from each manifest row's `activity` flag and stop in the silent tail, before the following slide. The task slide remains visible until Continue. The nine work stops are slides **4, 11, 13, 17, 26, 32, 36, 40 and 43**; the ten-minute break is slide **28**. Slide 43 completes reflection and feedback, records actual study minutes/pace in the existing feedback text, and submits once. Slide 44 checks the receipt and saved work; it does not ask for another submission. Chapter links and deliberate seeks allow navigation; they are not assessment access controls. A downloaded MP4 or playback with activity pauses disabled requires manual pausing.

English captions are on by default. At viewport widths up to 900 pixels, timed captions appear in a separate accessible region below the video; the native text track uses `hidden` mode to avoid duplicate captions over the slide. Wider screens and native video full screen use native captions. Narrow wrapper full screen keeps the separate region. The **Show English captions** checkbox controls both presentations, with cue/load/resize/fullscreen handling. Real browser inspection is still required.

Audio QA checks sample placement, cue text, clipping and contiguous timing. Video QA checks source hashes, chapter/frame boundaries, slide fidelity and sampled decoded-audio alignment. These checks do not replace listening or visual inspection. Review playback, long captions, mobile/fullscreen layouts, resources and pause-before-answer behavior in a real browser before publication. The existing Session 3 form is anonymous, not an individual attendance mechanism.

## Publication and provenance

Publish only the final student assets into the matching website checkout:

| Generated file | Website destination |
| --- | --- |
| `outputs/week03-video/week03-video.html` | `teaching/2105603/week03-video.html` |
| `outputs/week03-video/week03-lecture.mp4` | `teaching/2105603/media/week03/week03-lecture.mp4` |
| `outputs/week03-video/week03-poster.png` | `teaching/2105603/media/week03/week03-poster.png` |
| `outputs/week03-video/week03-captions.vtt` | `teaching/2105603/media/week03/week03-captions.vtt` |

The page provides the transcript and a text download, and depends on the existing `labs/assets/palette.css`, Week 3 documents, Labs 03/04 and Session 3 form. Copying files does not deploy the site; use the website repository's normal publication process.

After completing the checks and regenerating the offline package, `stage-publication.py --site /absolute/path/to/website` copies the verified media, page, sources and reports to those destinations. It checks matching revised source/media/page counts, the current manifest/MP4/published-PDF hashes, and actual-timing controller results before copying. A synthetic-fixture test result is not accepted for staging. Run it with the absolute research Python interpreter. It does not run Git or deploy the site.

Archive this directory's source scripts, `test-player.mjs`, narration JSON files, lesson contract, README, requirements, `demo-scenes.json` and reviewed `demo-frames/*.png`. The staging allowlist also includes optional theory/demo/LLE draft files and `revised-deck-text.json` when present. These help explain and reconstruct the revised narration; the merged `narration-draft.json` is the input to preparation. Preserve the final calibrated manifest, timeline and QA reports alongside the source if desired; review them for local identifiers before publication. Model/voice SHA-256 values, exact audio sample positions and input/output hashes provide provenance, not a guarantee of bit-identical encoding on another platform. The pinned requirements record the build environment's relevant packages, not a complete transitive lockfile.

Exclude model weights, voice binaries, sentence caches, intermediate WAV/master files, rendered temporary slides (the reviewed demo source captures are included), `__pycache__`, private feedback/student data, credentials and local configuration from the public source archive. Keep reusable local assets outside Git. No student response data is needed to rebuild this lesson.
