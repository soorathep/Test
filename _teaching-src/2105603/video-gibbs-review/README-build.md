# Gibbs review recording build

This pipeline combines the audited 26-slide PDF with English narration and genuine Lab 04 browser captures. It is an optional Week 3 review. It adds no attendance or exit-ticket requirement.

## Reproduce

Use the absolute research interpreter. Replace the site path with the website checkout containing the audited review deck and PDF.

```sh
cd "$HOME/Documents/Projects/Adv thermo"
"$HOME/.venvs/research/bin/python" asynchronous-gibbs-review/prepare-narration.py --site "$HOME/Documents/GitHub/Test"
"$HOME/.venvs/research/bin/python" asynchronous-gibbs-review/build-narration.py
"$HOME/.venvs/research/bin/python" asynchronous-gibbs-review/build-video.py --site "$HOME/Documents/GitHub/Test"
```

Review and approve the narration before running synthesis. The voice is the locally installed Kokoro `am_michael` US English male voice, at speed `0.94`. Models remain in `tmp/audio/kokoro-models`. The sentence cache remains in `tmp/audio/gibbs-review-male`. Neither models nor caches belong in the website repository.

The PDF is frozen at SHA-256 `ce1931747b20493413893c43f674f4cfd300952afea32230afc123f1eeb15ef6`. A changed PDF requires another content and visual review before updating the frozen hash in both preparation scripts.

## Inputs and scene timing

`narration-draft.json` contains 26 objects under `slides`, with `number`, `slide_id`, `title`, `narration`, `pause_instruction`, and `activity_minutes`. The preparation script checks the published HTML order and PDF identity, then writes `narration.json`. Spoken activity instructions belong in `narration` once. The `pause_instruction` field is display metadata and is not synthesized separately.

`demo-scenes.json` uses this format:

```json
{
  "scenes": [
    {
      "slide": 17,
      "cue": "An exact complete sentence from that slide's narration.",
      "image": "asynchronous-gibbs-review/demo-frames/17-01-inputs.png",
      "label": "Choose the metastable example",
      "source_url": "https://www.skhgroup.net/teaching/2105603/labs/stability.html#lle-experiment"
    }
  ]
}
```

Image paths are relative to the workspace. Captures must be genuine interface screenshots, with no invented controls or calculated results. For a return to the PDF during narration, supply `"kind": "slide"` and omit `image`. Each cue must match exactly one full sentence in its chapter. The pipeline requires genuine Lab captures in chapters 17, 18, 20, 23, and 24.

## Deliverables

`outputs/gibbs-review-video/` contains:

- `gibbs-review.mp4`, H.264, 1920 by 1080, AAC mono, fast start, below the 100 MB GitHub per-file limit.
- `gibbs-review-poster.png`, `gibbs-review-captions.vtt`, and `gibbs-review-transcript.txt`.
- `timeline.json`, `timeline.csv`, `manifest.json`, and `caption-timeline.json`, with measured timings.
- `video-qa.json`, recording container, image, source hash, exact PCM, transition, and decoded audio checks.
- `audio/`, containing individual PCM WAV files, master WAV, sentence cues, and `audio-qa.json`.

Final captions include the two-second silent tail after each chapter. They must be published with the video; the audio-only captions under `audio/` have different timestamps and must not be used for the final MP4. Long activity pauses are not encoded as filler silence. The player pauses after narrated instructions, and students resume when ready.

The final manifest merges the original spoken text with final video chapter times and adjusted sentence cues. The page generator can derive the actual viewing time and the 29-minute suggested activity budget from these files.

## Verification

```sh
"$HOME/.venvs/research/bin/python" asynchronous-gibbs-review/build-video.py --site "$HOME/Documents/GitHub/Test" --validate-only
```

The checks verify all slide and capture transitions, source hashes, contiguous frame intervals, audible source placement, silence tails, chapter marks, fast-start ordering, no clipping, and decoded AAC delay at the start, middle, and end. A transition contact sheet is written to `tmp/video/gibbs-review/transition-contact-sheet.jpg` for visual review. Automated checks do not replace listening to representative narration, inspecting equations and captures, and checking the published player, captions, chapter selection, and activity pause controls.

Only stage public media and teaching source assets. Do not publish private feedback reports, student responses, local audio models, caches, or temporary files.

## Verified build, October 24, 2026

The recording is 1,258.666833 seconds (20 minutes 58.7 seconds), including 52 seconds of chapter tails. Narration accounts for 1,206.666833 seconds. Together with the suggested 29 minutes of independent work, the review takes about 50 minutes.

The MP4 is 25,585,711 bytes. The build contains 26 chapters, 210 English caption cues, and 49 visual states, including 24 genuine Lab capture appearances. All source hashes, PCM placement, frame boundaries, chapter marks, and fast-start checks passed. The minimum transition PSNR was 42.86 dB. Decoded audio comparisons at the start, middle, and end found zero-sample delay and correlation above 0.99988. No PCM samples clipped.

All 49 decoded visual states were inspected. The separate narration review checked ten complete tracks with local ASR, verified all 26 audio hashes, and found no confirmed content error. A repeated-digit ambiguity in slide 11 was checked separately and resolved. This is an ASR spot check, not a claim of full subjective listening. The detailed report is `outputs/gibbs-review-video/audio/spot-check-transcripts.json`.
