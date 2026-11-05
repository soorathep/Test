Week 5 video player and study route

Scope: independent local content proposal. No published website, NFS version,
repository state, database or response form is changed by these source files.

Source of lesson identity, activity stops and budgets:
  ../documents/lesson-contract.json

Before encoded media exists:
  ~/.venvs/research/bin/python build-video-page.py --study-only
This marks 42 minutes explicitly as a production target. Do not publish that
provisional timing in place of the final measured duration.

After the final narration manifest and video timeline are ready:
  ~/.venvs/research/bin/python build-video-page.py \
    --manifest ../../outputs/week05-video/audio/manifest.json \
    --timeline ../../outputs/week05-video/timeline.json

Use absolute paths for the command and arguments if running from another
working directory. Defaults resolve those media paths from this source file.
Outputs: week05-video.html, week05-study.html, week05-page-build-qa.json.

The media timeline must contain the actual encoded video_sha256. Cache-busting
URLs bind MP4, captions and poster to that revision. This builder does not
claim to verify their file contents; encoding/publication QA must do that.

Controller checks:
  /opt/homebrew/bin/node test-player.mjs --fixture
  /opt/homebrew/bin/node test-player.mjs

The second command requires final manifest/timing files and applies all tests
to those timing records. These tests use a mocked DOM and media event model.
They are not browser, visual, decoded-video or listening QA. Parent task owns
actual browser checks, capture alignment, file hashes and publication.

The controller supports chapter anchors, descriptive slide-ID anchors,
manual continuation after required stops, device-local resume/checklist,
auto-pause toggle, English caption toggle, responsive captions below narrow
video, transcript download and native/full-stage fullscreen.

Checklist acknowledgments are not proof of completed work or attendance.
The response form remains anonymous. No form is submitted by this player.

Public artifact paths:
  teaching/2105603/week05-video.html
  teaching/2105603/week05-study.html
  teaching/2105603/files/week05-practice.pdf
  teaching/2105603/files/week05-lab-guide.pdf
  teaching/2105603/files/week05-solutions.pdf
  teaching/2105603/files/postmidterm-05-slides.pdf
  teaching/2105603/media/week05/week05-lecture.mp4
  teaching/2105603/media/week05/week05-captions.vtt
  teaching/2105603/media/week05/week05-poster.png

Only generated final HTML goes to the public teaching folder. Fixture files,
QA files and builders belong in teaching source or private working storage.
