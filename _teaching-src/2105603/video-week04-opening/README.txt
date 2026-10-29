WEEK 4 INTEGRATED QUESTIONS-FIRST RECORDING

Publication edition: 29 October 2026

The complete MP4 now starts with 14 narrated opening chapters, followed by
40 core slides. Opening 13 has a four-minute R1-R3 notebook pause. The page
also supplies a text companion; students do not repeat both as compulsory work.
Core A-G and I retain 100 working minutes and a separate ten-minute break.
H1-H4 is optional (+20 working minutes). The actual total is the measured full
recording + 104 work + 10 break. Skipping optional recorded H material shortens
this conservative budget. Study estimates are not enforced waiting timers.

Stable links use #opening-01 ... #opening-14 for the new opening and retain
#slide-1 ... #slide-40 for every core slide. Internal combined chapter numbers
are 1-54. Core Lab10/11 demonstrations still use the same genuine UI captures
and their verified spoken sentence transitions. No new form is created and
no student responses are included in these files.

Voice: Kokoro ONNX am_michael, US English, speed 0.94, same local model and
sentence cache as the prior Week4 edition. It is synthetic male narration.
All new opening narration and core1/3/35/36 are generated for this edition.
Other core sentences are reused from the existing hash-verified cache.
No API credentials, voice-model weights, raw student data or audio cache are
published. Core2/3/35/36 PDF frames and the corresponding core HTML/QMD sections
are updated. The 54-page video PDF contains the opening plus the corrected core.

Portable source layout
Use the existing course workspace and its asynchronous-week04 source folder.
This package lives at week04-feedback-opening/video/. The earlier source
folder contains the actual Lab demonstration JSON and demo-frames. Website
figures are read from ~/Documents/GitHub/Test; change SITE in the frame source
only if using another checkout. base-core-slides.pdf is the frozen old core
PDF used as the input, so rebuilding never reads the already revised output.
The established research interpreter is ~/.venvs/research/bin/python.

Reproduce in this order (always call an absolute interpreter):
1. prepare_combined.py creates narration.json from the opening, original core
   narration and reviewed core patches. Final narration.json is also saved.
2. build-narration.py generates PCM tracks, sentence cues, captions and hashes.
3. figures/build_frames.py regenerates the matching video PDF and review PNGs.
   Inspect changed frames and embedded fonts, then record reviewed-pdf.sha256.
4. build-video.py --expected-pdf-sha256 <reviewed hash> builds and decodes the
   combined video, verifying all visual boundaries and audio synchronization.
5. player/build-video-page.py --manifest <audio/manifest.json> --timeline
   <timeline.json> --output <week04-video.html> creates the final browser player.
   Media URLs are versioned using the final encoded video hash.
6. player/test-player.mjs --require-media-timeline --manifest <manifest.json>
   --timeline <timeline.json> --output <controller-qa.json> checks controller
   behavior against actual metadata with mocked media. Also test a real browser.
7. route/apply-timing.py --timeline <timeline.json> updates measured hub timing.
   Build route/build_week04.py --output <public course files>, then stage the
   hub, written companion, corrected core HTML/QMD and PDFs.
8. route/update-course-links.py --site <website> changes only Session4. Refresh
   the three navigation hashes in labs/release-manifest.json without replacing
   engine versions or source-commit metadata.
9. route/build-offline.py rebuilds the student-only package. Videos remain an
   online/separate download; opening and original core anchors are preserved.

QA limitations
The media validator decodes every frame boundary and checks source hashes,
PCM placement and audio correlations. ASR checks cover all 14 new opening
tracks and four revised core tracks, with hash-bound manual source comparison.
ASR is not a complete subjective listening review. Subjective listening was
unavailable in this runtime and is not claimed. Browser QA checks playback,
chapter mapping, activity guards and narrow caption layout without submitting
student forms. Preserve these distinctions when describing verification.
