CURRENT PUBLICATION: The combined opening + core recording is now reproduced from ../video-week04-opening/. This file documents the prior edition and its retained source inputs.

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
