WEEK 4 INTEGRATED OPENING: ROUTE AND DOCUMENT SOURCES

This directory contains edited copies only. The canonical website checkout
has not been changed by this subtask. Do not rerun revise-route.py: it records
the one-time transformation of the prior text-only route.

Teaching contract
- Watch Opening 01-14 at the start of the combined Week 4 video.
- Opening 13 pauses for four minutes for the same R1-R3 notebook questions.
- Opening 14 checks the answers, then the video continues to core slide 1.
- The questions page is an alternative written opening or a reference. It is
  not another required 20-minute task after watching the video opening.
- A-G and I remain required, with 100 minutes of core work and a 10-minute
  break. H1-H4 remain optional, requiring 20 additional working minutes.
- Total budget = measured combined recording + 104 working minutes + 10 break.
- The opening replaces the former required H block. No new form is introduced.
- The nominal 0-180 minute table remains a planning guide. The measured
  conservative total is shown separately; neither is a measured student time.

Files
week04-study.html: updated hub, with timing tokens awaiting the final timeline.
week04-questions.html: written alternative, preserving scientific content.
build_week04.py: complete revised handout generator; still 6/4/4 pages.
apply-timing.py: fill or refresh hub timing using a verified combined timeline.
update-course-links.py: changes only Session 4 HTML/JSON; reads timing from hub.
build-offline.py: retains the established student-only allowlist and all fragments.
verify-route-fixture.py / route-fixture-qa.json: synthetic-timing fixture only.

Final build order (use the absolute research interpreter):
1. Run apply-timing.py --timeline <final combined timeline> --hub <this hub>.
   Expected schema: 54 rows in slides or chapters, 14 with section=opening,
   then 40 with section=core and core_slide=1..40. Contiguous start/end_seconds.
2. Copy hub and questions page to the website source and public course folders.
3. Run build_week04.py --output <website>/teaching/2105603/files.
   Render changed PDF pages and inspect layout; check fonts and page counts.
4. Run update-course-links.py --site <website> after staging the measured hub.
   Refresh only the three affected navigation-file hashes in release-manifest.
5. Run build-offline.py with SKH_WEBSITE_DIR=<website> after final media/page
   and navigation staging. The package excludes MP4s and players as before;
   its video links preserve #opening-01 and the existing #slide-16/#slide-30.

Validation performed in this subtask
- Syntax checks pass for the four Python builders/updaters.
- Synthetic-timing fixture verifies timing totals without inventing live duration.
- Navigation is idempotent, preserves content outside Session 4, and leaves all
  other JSON sessions unchanged.
- Offline link rewriting preserves both opening and legacy core fragments.
- No raw feedback records, student identifiers, canonical writes or publication.

No PDFs were generated in this subtask; the parent should build the final set
once and inspect it together with the final video/route.

CORE SLIDE REFERENCE REPAIR
- postmidterm-04.html and postmidterm-04.qmd are revised copies for the
  existing canonical destinations. update-core-slides.py reproduces them.
- Only setup slide 2, route slide 3 and optional H slides 35-36 are changed.
  All 40 IDs/order remain; all other HTML sections are byte-identical.
- core-slide-sync-qa.json records this bounded comparison.
- The hub and Session 4 navigation now link files/week04-video-slides.pdf as
  "Complete video slides (opening + core)". The 40-slide HTML/PDF is labelled
  as a core reference.
- The offline builder's established PDF glob includes the new combined PDF;
  a guard now requires it to be staged before archive creation.
- Generate the final 40-page core PDF by extracting combined PDF pages 15-54.
  Check setup slide 2 against the revised reference directions as well.
