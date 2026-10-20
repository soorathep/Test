# Lab 01 supplemental video

This English screen demonstration supplements the Week 1 classroom lesson. It covers ideal VLE and uses the same live Lab 01 workflow as the students. It is not a replacement three-hour lesson and does not request another exit ticket or feedback submission.

## Chapter contract

1. Open Lab 01 and explain where the demonstration fits.
2. Set the ideal model and identify the property inputs and units.
3. Predict the phase behavior. Optional 2-minute practice pause.
4. Calculate bubble and dew pressures. Distinguish `x = z` at the bubble boundary from `y = z` at the dew boundary.
5. Run the TP flash at 95 kPa and distinguish phase amounts from compositions.
6. Check total and component balances independently.
7. Read the Rachford-Rice chart and equations.
8. Save the baseline case.
9. Calculate and save the 110 kPa liquid case.
10. Calculate and save the 80 kPa vapor case.
11. Compare the three cases and export the curve CSV.
12. Download the comparison JSON, reopen it, restore a case, and calculate again.
13. Independently attempt the 90 kPa case. Optional 5-minute practice pause.
14. Check the 90 kPa case and keep the saved work.

The final screen capture and narration must agree with these steps. Neither optional pause adds exercise-length silence to the MP4. The webpage pauses in the silent tail of chapters 3 and 13 until the learner selects Continue. Downloads require manual pausing.

## Player input contract

`build-video-page.py` reads these final products by default:

- `outputs/lab01-video/audio/manifest.json`: a list of 14 narration records.
- `outputs/lab01-video/timeline.json`: an object containing a `slides` array of 14 final encoded chapter ranges.

Manifest records contain sequential `slide` integers (with `id` values `01` through `14` also supported), nonempty `title` and `narration`, explicit `activity` booleans, `activity_minutes`, and `pause_instruction` strings. Chapters 3 and 13 have activity budgets 2 and 5, respectively. Other chapters have `activity: false` and zero minutes. Nonempty pause instructions are required at both checkpoints.

Timeline records contain the same sequential `slide` number plus `start_seconds`, `narration_end_seconds`, and `end_seconds`. Ranges must be contiguous and begin at zero. Activity flags and titles, when present, must match the manifest. The guard at `end_seconds - 0.24` must follow the narration, so the encoder must preserve its silent tail. Shared script hashes are checked when present. A top-level `duration_seconds`, when present, must match the final chapter end. The loader also accepts `chapter`/`id` numbering and `chapters`/`timeline` arrays for compatible pipelines.

The player never invents timestamps or a recording duration. Its URLs use `#chapter-1` through `#chapter-14`. At narrow widths, the same timed VTT track is displayed below the screen image; native video fullscreen uses native captions.

## Narration generation

After cross-review freezes `narration.json`, generate its 14 chapters with the same Michael male US English voice used for the later lessons:

```sh
"$HOME/.venvs/research/bin/python" asynchronous-lab01/build-narration.py
```

The generator uses Kokoro `am_michael` at speed `0.94`, the existing local model files in `tmp/audio/kokoro-models/`, and a separate sentence cache in `tmp/audio/lab01-male/`. It writes mono 24 kHz PCM audio, source-preserving captions and sentence cues, narration hashes, the manifest, and `audio-qa.json` under `outputs/lab01-video/audio/`. Source script hashes are checked before and after generation. Model weights, caches and WAV masters are working files rather than website assets.

After generation, `check-audio.py` verifies all narration and WAV hashes, then transcribes six selected technical chapters with the existing local faster-whisper `tiny.en` cache using one CPU thread. Model download is disabled. Compare the resulting ASR text with the original narration and resolve meaningful omissions or numerical changes before publication. ASR is not a complete subjective listening review.

```sh
"$HOME/.venvs/research/bin/python" asynchronous-lab01/check-audio.py
```

## Encoder input and verification

`build-video.py` uses the final narration and audio manifest, `audio/timeline.json`, and `demo-scenes.json`. Each scene specifies `slide`, `file`, `sentence_prefix`, and `label`; captures are in `demo-frames/`. An optional `sha256` field freezes an individually reviewed capture.

Every chapter must have a real capture. Its first scene must match the first narration cue and appears at the chapter start, including the short leading silence. All later scene prefixes must uniquely identify a cue and follow narration order. The encoder adds two seconds of silence per chapter, then maps audio and images to integer 24 kHz sample offsets. It preserves screenshot aspect ratios inside a 1920 × 920 region and reserves the remaining 160 pixels for the graphite caption band using the imported lab palette.

The encoder verifies narration text against the source script and its hash, checks every WAV against the audio manifest, and records hashes for all input sources and captures. The final validation verifies those hashes again, checks the sample-exact PCM master and silent tails, decodes every video frame to test contiguous boundaries, checks transition PSNR against the source images, confirms MP4 chapter offsets and faststart, and compares decoded AAC with source PCM near the beginning, middle, and end. These checks supplement visual and listening review.

Do not run the encoder until the narration, captures and scene map have been reviewed and frozen:

```sh
"$HOME/.venvs/research/bin/python" asynchronous-lab01/build-video.py
```

The encoder writes the MP4, poster, captions, final timeline and `video-qa.json` under `outputs/lab01-video/`. Temporary canvases and the PCM master stay under `tmp/video/lab01/`. It never regenerates narration or alters the interface shown in the captured screens.

## Build and verify

Run from the project workspace with the absolute interpreters:

```sh
"$HOME/.venvs/research/bin/python" asynchronous-lab01/build-video-page.py
"$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" asynchronous-lab01/test-player.mjs --require-media-timeline --output outputs/lab01-video/player-controller-qa.json
```

The output page is `outputs/lab01-video/lab01-video.html`. The controller tests use a fake DOM and media events. They do not establish that the encoded media plays, that narration is synchronized, or that the layout is visually correct. Complete those checks separately against the staged and published webpage.

During development only, `--fixture` runs clearly labeled synthetic timings:

```sh
"$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" asynchronous-lab01/test-player.mjs --fixture --output outputs/lab01-video/player-fixture-qa.json
```

Fixture files stay in `outputs/lab01-video/controller-fixtures/`. Do not publish them or substitute them for the final metadata.

## Publication layout

Stage the generated page at `teaching/2105603/lab01-video.html`, alongside:

- `media/lab01/lab01-demo.mp4`
- `media/lab01/lab01-poster.png`
- `media/lab01/lab01-captions.vtt`

The page links to the Week 1 Lab guide, original Week 1 slides, Lab 01, Session 1 in the learning path, and the optional three-case reference at `files/lab01-demo-comparison.json`. Learners are instructed to save their own comparison JSON. Existing shared `labs/assets/palette.css` supplies the course palette. The template contains no student-response endpoint and does not submit work.
