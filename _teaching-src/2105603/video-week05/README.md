# Week 5 independent lesson

The 6 November 2026 lesson replaces an in-person class. Onsite teaching resumes
on 13 November. Student content is US English. The required route uses one
six-page worksheet and Lab 12, with 128 minutes of activity budgets and a
10-minute break. The video page reports measured playback time rather than
equating recording length with study time. Additional reading is optional.

The first four slides respond to Week 4 questions without publishing student
responses. The synthetic A2 ⇌ 2A example uses the same three cases throughout:
350 K/100 kPa, 350 K/400 kPa and 400 K/100 kPa. The third case uses constant
reaction enthalpy with ΔCp° = 0. The standard pressure is 100 kPa.

## Source and review

- The canonical slide source is `../postmidterm-05.qmd` in the course source
  folder. Its reviewed 32-page PDF is included as `reviewed-slides.pdf`.
- `documents/lesson-contract.json` defines chapter IDs, worksheet references
  and activity budgets. `documents/build_week05.py` regenerates the handouts.
- `media/narration.json` contains the English narration. The published synthetic
  voice is Kokoro ONNX `am_michael`, speed 0.94, using locally held model files.
- `media/demo-frames/` contains genuine Lab 12 interface captures. Chapters 20,
  22 and 30 show baseline, pressure and temperature calculations and baseline
  JSON restore. These are narrated stepwise screen captures, not a continuous
  mouse recording. Exported synthetic cases are in `media/downloads/`.
- `qa/` contains the slide, audio, media and player verification receipts.
  Integer 24 kHz sample positions govern slide and screenshot transitions.
  Two-second chapter tails permit a pause before the next slide. Work-length
  silence is not encoded. Caption cues refer to the delivered audio.
- The player stores only device-local progress. It does not record attendance
  or submit responses. Session 5 uses the existing anonymous response form.

## Regeneration

Use the absolute research interpreter `~/.venvs/research/bin/python` and the
configured Node runtime. Run within the course source folder. Read the project
instructions before editing. Work in a separate content checkout and never
write generated media into an archive or a different actor's workspace.

1. Render `postmidterm-05.qmd` with the existing public Quarto profile. Vendor
   KaTeX and publish only the named deck and its dependencies. Do not replace
   the Jekyll course index. The course theme and SI-unit heading CSS must remain.
2. Serve the website checkout with `serve_preview.py --site <checkout>` and
   export slides with `export-slides.mjs <checkout>`. `COURSE_ORIGIN` sets the
   preview origin. Review all pages, verify embedded fonts and freeze its hash.
3. Run `media/build-narration.py` with explicit `--model-dir`, `--script`,
   `--output` and `--cache` paths. Keep models, caches and WAVs local. A new
   narration revision requires new verification and matching captions.
4. Run `media/build-video.py --pdf video-week05/reviewed-slides.pdf
   --expected-pdf-sha256 <reviewed SHA-256>`. Its defaults use
   `outputs/week05-video/` beneath the course source folder. A portable working
   copy can use the same directory arrangement with the package named
   `asynchronous-week05`; pass explicit paths when it differs.
5. Build the web pages using `web/build-video-page.py --manifest <manifest>
   --timeline <timeline>`, then run `web/test-player.mjs` against those inputs.
   Verify real playback, chapter changes, activity pauses, captions and mobile
   layout in a browser. The programmatic controller tests are not browser QA.
6. Stage only the allowlisted public assets. Update Week 5 navigation and the
   13 November notice. The offline builder excludes MP4s/players and rewrites
   video links to the live site. Refresh only the changed public Lab manifest
   entries, preserving calculation-engine metadata.
7. Verify local and live links, PDFs, media hashes, range delivery and deployment
   before announcing the lesson. Do not publish private course feedback reports.

`stage_release.py` documents the local authoring workspace layout used for this
edition. Its input paths should be explicitly adapted for a new workspace.
No API keys, tokens, voice models, raw response data or private reports belong
in the public repository.
