WEEK 4 ROUTE UPDATE - 29 OCTOBER 2026

Begin with week04-questions.html: 20 minutes for consistency diagnostics,
modeling capability, Gibbs-graph interpretation and the lever rule.
Write R1-R3 in the existing notebook. No new form or export is required.

The opening replaces the formerly required 20-minute H1-H4 transfer activity.
Required worksheet work is now A-G and I. H1-H4 is an optional extension.

Timing: opening 20 + core video work 100 + break 10 + unchanged recording
57:29 = about 187.5 minutes conservatively, including the whole recording.
Skipping optional recorded H material reduces this. Completing H adds about
20 minutes. These are planning budgets, not measured student completion time.

The 40-slide recording, captions and original slide references are retained.
The revised study page and player identify which original H instructions
are now optional. Slide 36 pauses for an explicit choice, not a mandatory
20-minute exercise. The primary route goes to slide 39; the optional route
continues to the H check. No automatic silent jump is introduced.

Student materials: revised six-page worksheet, four-page guide and four-page
solutions, plus one HTML opening lesson. The opening derives D and the local
residual, shows a localized-defect example, defines Van Ness-type modeling
capability, and distinguishes excess Gibbs from total mixing Gibbs.
All student-facing wording is English.

Reproduction:
- build_week04.py --output <website>/teaching/2105603/files
- Copy week04-study.html and week04-questions.html to the public course folder.
- Use video-week04/build-video-page.py with the existing narration, audio
  manifest and video timeline, passed explicitly as arguments.
- Run video-week04/test-player.mjs with actual timing metadata.
- Run feedback-opening/update-course-links.py --site <website>.
- Refresh only the navigation-file hashes in labs/release-manifest.json.
  Engine versions, source commit and upstream source hashes are preserved.
- Build the offline package using feedback-opening/build-offline.py.
  The opening page is included; the unchanged MP4 remains an online download.

Private feedback reports, raw responses and student identifiers are excluded.
The changes respond to questions in the reviewed 28 October private snapshot.
They do not establish whether respondents viewed the previous Gibbs supplement.

ORIGINAL RECORDING CONTRACT (retained for media reproduction)

# Week 4 independent lesson: solid equilibria and adsorption

This lesson replaces live class while the instructor attends the ECS meeting.
It is an independent lesson, not a holiday announcement. Student materials are
US English. The video and the 40-slide deck present the same lesson; students
use one route with the six-page worksheet and four-page Lab guide. The separate
four-page worked solutions follow an independent attempt. The existing
three-page preclass PDF is optional background.

## Teaching contract

`lesson-contract.txt` defines the 40 slide IDs, worksheet mapping and case values.
Ten work pauses total 120 minutes, with a separate 10-minute break. These are
planning budgets, not measured completion times. The player computes actual
recording duration from the encoded timeline and adds the fixed activity
budgets. Do not force the recording plus work to equal 180 minutes or add silence
to make the video three hours long. The nominal study route is approximately
three hours; report the measured edition honestly.

| Stop slide | Work or break | Minutes |
| --- | --- | --- |
| 4 | A1-A3: processes and constraints | 8 |
| 8 | B1-B2: pure-solid solubility | 6 |
| 13 | C1-C3: finite-inventory GSE | 10 |
| 15 | D1: predictions before Lab 10 | 5 |
| 18 | D2-D4: independent Lab 10 rerun | 22 |
| 20 | Break | 10 |
| 25 | E1-E3: isotherm calculation | 10 |
| 29 | F1-F3: predictions before Lab 11 | 5 |
| 32 | G1-G4: independent Lab 11 rerun | 24 |
| 36 | H1-H4: unseen-case attempt | 20 |
| 39 | I: exit ticket and feedback | 10 |

Actual interface screenshots form the demonstrations in slide 16 (Lab 10) and
slide 30 (Lab 11). They document working UI controls and synthetic results,
including exports, reopening a comparison and recalculating after restore.
They are captured screens, not animated mockups. `demo-scenes.json` maps each
screen to an exact spoken sentence and the video builder verifies its timing.
Prediction stops precede the demonstrations. Direct chapter links deliberately
skip earlier stops; students should complete predictions first.

The Session 4 form is anonymous. Submit once at slide 39, wait for the receipt,
then verify it and retain work at slide 40. No attendance identity, deadline or
new response-storage service is introduced.

## Portable reproduction

Use the existing project workspace and website checkout. Paths below are
relative to the workspace except the absolute interpreters. Set the website
path to the intended checkout, such as `~/Documents/GitHub/Test`, or a managed
worktree. Never commit model weights, cached sentence audio or student records.

```sh
# Website documents and slides are built from the website source tree.
~/.venvs/research/bin/python <website>/_teaching-src/2105603/prereading/week04/build_week04.py --output <website>/teaching/2105603/files

# Normalize narration against the rendered 40-slide HTML.
~/.venvs/research/bin/python asynchronous-week04/prepare-narration.py --site <website>

# Generate the final male English tracks with the existing local model cache.
~/.venvs/research/bin/python asynchronous-week04/build-narration.py
~/.venvs/research/bin/python asynchronous-week04/calibrate-activities.py
~/.venvs/research/bin/python asynchronous-week04/build-video.py

# Build the player only after the final manifest and timeline exist.
~/.venvs/research/bin/python asynchronous-week04/build-video-page.py
~/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node asynchronous-week04/test-player.mjs --require-media-timeline --output outputs/week04-video/player-controller-qa.json
```

Confirm script arguments with `--help` if the pipeline changes. The voice is
Kokoro `am_michael`, speed 0.94, using the existing local ONNX and voice cache.
This is synthetic male narration prepared for the course, not an impersonation.
The narration generator records exact sentence/WAV hashes. Keep final
`narration.json`, audio manifest, video timeline and rendered PDF mutually
consistent; update the encoder PDF hash only after visual review of a frozen
deck. Do not claim a duration until the final encoded video has been measured.

`build-video-page.py` derives chapter timestamps and pause guards from verified
metadata. It rejects stale slide counts, inconsistent activity flags, wrong
budgets and timeline gaps. English captions remain native on wide screens and
native full-screen video; on narrow screens, timed captions render below the
slide to keep equations visible. A downloaded MP4 needs manual pauses.

## Verification and publication

`test-player.mjs --fixture` tests controller branches with synthetic timing only;
it does not establish actual video, audio or browser correctness. Final testing
uses `--require-media-timeline`, then actual browser playback, both demonstration
jumps, prediction/continue transitions, caption layout and the form links.

Inspect all document pages and all changed slides as images. Check embedded
fonts with no Type 3 fonts, page bounds, links, numerical values, units and the
independent balances. Scientific checks preserve distinctions among partial
and total pressure, phase composition and amount, and uptake per kg and adsorbed
moles. The known-pressure adsorption example at 10 kPa requires 0.01400908 mol;
the Lab 11 investigation instead uses 0.010 mol. Both are deliberate.

Stage only the finished student artifacts and reproducible sources. Rebuild the
offline ZIP after slides, PDFs, hub and player are frozen. The ZIP includes the
same slides, Labs and documents but excludes MP4 files and video players; video
links point online and preserve `#slide-16` and `#slide-30`. The response form
requires internet. Build from the labs repository, then validate from this workspace:

```sh
SKH_WEBSITE_DIR=<website> ~/.venvs/research/bin/python tools/build-offline.py
# Return to the course workspace before the following command.
SKH_WEBSITE_DIR=<website> ~/.venvs/research/bin/python asynchronous-week04/validate-offline.py
```

The offline report verifies every manifest hash, byte-identical Week 4 PDFs,
HTML changed only by the documented offline link rewrites, both demo anchors,
the current Lab release and exclusion of media. It is saved as
`outputs/week04-video/offline-qa.json` with portable relative file references.
After deployment, run the source-backed publication check:

```sh
~/.venvs/research/bin/python asynchronous-week04/verify-publication.py --site <website>
```

Confirm canonical file hashes, first and last MP4 byte ranges, and actual browser
playback before reporting that the lesson is live. The local QA reports distinguish
ASR spot checks and numerical media checks from full subjective listening.
