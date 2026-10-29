INTEGRATED WEEK 4 PLAYER

Deliverable source files:
  build-video-page.py
  test-player.mjs

The other files in this directory are development fixtures and transform
scratch files. Do not publish fixture-preview.html or synthetic manifests.

Input contract:
- 14 opening chapters followed by 40 core slides, sequential slide 1–54.
- section: opening or core
- core_slide: null for opening; 1–40 for core
- anchor: opening-01 … opening-14; slide-1 … slide-40 for core
- opening 13: activity true, activity_minutes 4
- core 36: activity true, activity_minutes 0,
  optional_activity_minutes 20 (legacy 20 required minutes is normalized)
- original core work stops retain 100 required minutes, plus a 10-minute break.
- Full combined recording + 4 + 100 + 10 is the conservative study budget.
  Do not add a separate 20-minute reading activity.

The combined recording uses the existing media/week04/ URLs. Stable core
anchors remain valid and point to the new time of their original core content.
The matching video-frame PDF is linked at files/week04-video-slides.pdf.

Build with the absolute research interpreter and explicit paths:
  build-video-page.py --manifest <combined-manifest.json>
    --timeline <combined-timeline.json> --output <week04-video.html>

Test with the absolute bundled Node executable:
  test-player.mjs --require-media-timeline
    --manifest <combined-manifest.json> --timeline <combined-timeline.json>
    --output <controller-qa.json>

Current QA:
  30 fixture controller tests passed. These cover all stable anchors,
  explicit opening/core navigation, the R1–R3 pause before its answers,
  continuous opening-to-core transition, every core task, optional H choice,
  prediction-before-demo guards, replay and seek behavior, final form/receipt
  behavior, transcript accounting and responsive caption controls.
  Fixture HTML renders 54 unique chapter links and 54 transcript sections.

Limits: These are mocked DOM/media tests and structural HTML checks.
They do not establish decoded audio/video synchronization or browser playback.
The parent task must run actual-metadata tests and real-browser checks.

Media cache versioning: production timeline objects must contain the final
encoded video_sha256. All MP4, caption and poster source/download URLs use
?v=<first 12 hash characters>. Download filenames remain unchanged. Bare
timeline arrays are development fixtures and use ?v=dev. Defaults resolve
from workspace root to outputs/week04-opening-video.
