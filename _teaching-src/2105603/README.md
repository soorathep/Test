# 2105603 — slide decks (Quarto + Reveal.js)

Source for the decks published at
<https://www.skhgroup.net/teaching/2105603/>.

This folder starts with an underscore, so Jekyll ignores it: nothing here is
served. Only the rendered output in `teaching/2105603/` reaches the website.

One file per module, not per week.

| File | Module | Slides | Lectured by |
|------|--------|-------:|-------------|
| `eos.qmd` | 1 · Evolution of Equations of State | 56 | Chanon |
| `fugacity.qmd` | 2 · Fugacity, Chemical Potential and the Equilibrium Criterion | 22 | Chanon |
| `solution.qmd` | 3 · Solution Thermodynamics | 25 | Chanon |
| `vle.qmd` | 4 · Vapour-Liquid Equilibrium of Mixtures | 81 + 5 appendix | Soorathep |
| `stability.qmd` | 5 · Phase Stability and Complex Equilibria | 25 | Soorathep |
| `reaction.qmd` | 6 · Chemical Equilibrium | 30 | Soorathep |

The five appendix slides in `vle.qmd` carry `visibility="uncounted"`: they are
reachable but do not advance the slide counter, so the deck reads as 81 slides
and the extra material is there if a question needs it.

---

## Build

Install Quarto once from <https://quarto.org/docs/get-started/>. Then, from
inside this folder:

```bash
# while writing — live reload in the browser, speaker notes intact
quarto preview vle.qmd

# publish to the website
quarto render --profile public --output-dir _site   # all six decks
~/.venvs/research/bin/python tools/vendor-katex.py _site
~/.venvs/research/bin/python tools/publish.py                 # copies _site into ../../teaching/2105603/
```

To rebuild one module only, name it in both commands:

```bash
quarto render vle.qmd --profile public --output-dir _site
~/.venvs/research/bin/python tools/vendor-katex.py _site
~/.venvs/research/bin/python tools/publish.py vle.html
```

Three steps, and all three matter.

`--profile public` applies `tools/strip-notes.lua`, which removes every
`::: {.notes}` block. **Always use it for the website.** Reveal.js ships speaker
notes inside the HTML, so without the profile any student can press `S` and read
the teaching notes, the common-misconception list and the questions you were
going to ask them.

`tools/vendor-katex.py` copies a pinned KaTeX build into `site_libs/katex/` and
repoints the HTML at it. Quarto links katex@latest from a CDN; every equation in
these decks is live LaTeX, so a lecture theatre with no Wi-Fi would otherwise
lose all of them.

`tools/publish.py` copies only the six deck files, `site_libs/` and `figures/`.
It does **not** copy Quarto's generated `index.html`, which would overwrite the
Jekyll course page. Never point `--output-dir` straight at `teaching/2105603/`.

It also **merges** `site_libs/` and `figures/` rather than replacing them. Quarto
content-hashes the compiled theme, and Module 1 was rendered against an earlier
version of `theme/teal-amber.scss` than Modules 2-6, so the two hashes coexist
in `site_libs/revealjs/dist/theme/`. Replacing the folder after a single-module
render used to delete the file the other decks point at, and those decks then
loaded unstyled with no error at all. Same argument for `figures/`.

Verify before committing — from the repository root:

```bash
~/.venvs/research/bin/python _teaching-src/2105603/tools/verify.py
```

That checks all six decks for leftover speaker notes and CDN links, confirms the
Jekyll course page is intact, and confirms every file named in
`_data/act2026.yml` actually exists.

---

## Presenting

| Key | Does |
|-----|------|
| *click* | Next slide — anywhere on the slide, as in Keynote |
| `←` | Back. Or the arrow at the left edge of the screen |
| `S` | Speaker view — spoken script, next slide, elapsed timer |
| `F` | Full screen |
| `E` | Print layout, then Print → Save as PDF |
| `O` | Slide overview |
| `?` | All shortcuts |

The published deck has no speaker notes. Present from a local `quarto preview`,
or from a `bundle-deck.py` build without `--public`.

---

## Writing a slide

Each `##` starts a new slide. The house blocks are documented in the 2105620
README; these decks add nothing except the rules below, each of which exists
because breaking it broke something.

**Card headings use `[Head]{.card-h}`, never `### Head`.** A markdown heading
inside a fenced div makes pandoc emit a nested `<section>`, and Reveal.js then
treats every card as a slide of its own: 56 slides printed as 630 pages, and the
slide counter stopped matching the deck. `.card-h` is styled in
`theme/teal-amber.scss` to look exactly like `.card h3` did.

**Nest fenced divs by colon count, widest outside.** A `:::` block closes at the
first `:::`, so `::: {.cards}` containing `::: {.card}` silently collapses and
every later `##` ends up nested inside the wreckage. Use

```
:::::: {.columns}
::::: {.column width="54%"}
:::: {.cards}
::: {.card}
```

**Do not use `.cards.stack` for long headings.** It is a three-column grid meant
for short labels; a long heading overflows into the body text. Stack cards by
emitting one `:::: {.cards}` block per card instead.

**`auto-stretch` is off.** It collapsed any figure that shared a slide with
cards. Figures instead carry an explicit width and are capped at `60vh` by the
theme. Two figures on one slide go side by side in columns; stacked, they run
off the bottom.

**A long display equation does not wrap.** KaTeX renders it at full width and it
runs off the right edge, where nothing warns you. Split it into two `$$…$$`
blocks at a natural `=` or `+`. Four slides in Modules 2 and 3 needed this.

**Check overflow mechanically, not by looking.** `tools/check-overflow.py` drives
the rendered deck headless and measures every element against the slide box:

```bash
~/.venvs/research/bin/python tools/check-overflow.py _site/vle.html
```

Three things in that script are not obvious and are commented in place: hidden
KaTeX MathML reports a 12,958 px width and must be skipped, SVG stretchy
delimiters legitimately exceed their box, and `Reveal.getTotalSlides()` excludes
`visibility="uncounted"` slides so the script walks the DOM instead. All six
decks currently measure zero overflow.

---

## Figures

Figures come from `figures/`, which is a copy of each module's Python toolkit
output. To change a figure, edit the script in the toolkit, re-run it, copy the
PNG here, and re-render. Prefixes keep the modules apart: `f01`-`f34` are Module
1, then `f2_*`, `f3_*`, `f4_*`, `f5_*`, `f6_*`. Every figure is committed as both
PNG (used by the deck) and PDF (for reuse in a paper or a handout).

Each toolkit script is standalone and prints the numbers it computed, so a figure
can be checked against its own output rather than trusted.

---

## A new module

```bash
cp vle.qmd <module>.qmd
```

Edit the front matter and body, add the module to `_data/act2026.yml` with
`slides: <module>.html`, and add the rendered filename to `DECKS` in
`tools/publish.py`. It then appears on the course page by itself.

---

## Notes

- Fonts are bundled as base64 in `theme/_fonts-embedded.scss` — Source Serif 4
  and Source Sans 3 for Latin, Sarabun and Noto Serif Thai for Thai. Nothing is
  fetched from Google. Re-run `~/.venvs/research/bin/python build_fonts.py` from inside `theme/` only
  if you change a font file.
- Equations are live LaTeX rendered by KaTeX, not images. They stay sharp at any
  zoom, they can be copied, and a screen reader can read them.
- The site build does not run Quarto, so the published deck is exactly what was
  rendered here.
- `_data/act2026.yml` deliberately carries no weekly schedule and no assessment
  table. Both stay off the public page until they come from the registered
  syllabus rather than from a draft.


## After-midterm teaching sequence (18 hours)

The editable `postmidterm-01.qmd` through `postmidterm-06.qmd` cover Modules 4–6,
including solid/surface and electrochemical topics. Standard classroom sessions
use 12 slides and an optional appendix: 30 minutes of concepts, 20 minutes of
hand calculation, 20 minutes of demonstration, a 10-minute break, 70 minutes of
pair work, and 30 minutes of discussion and exit reflection. Their required
independent work is 15–20 minutes of preparation and 30–40 minutes of follow-up.

Session 2 replaces the class on 16 October 2026 with a 28-slide English independent
lesson. Its 180 minutes include preparation (10), phase/material-balance checks
(25), activity coefficients (30), Antoine conventions (25), break (10), Lab 08
(45), and review/corrections/exit/feedback (35). Its reading is optional; the
worksheet and Lab work are within those 180 minutes. Students begin without
prior knowledge of gamma. The narrated video is about 25 minutes, with deliberate
student pauses. `week02-video.html` is the entry point, and `labs/learning-path.html`
links the resources. Module decks remain extended references.

Render the six classroom decks and six session appendices using the
existing public-profile, vendored-KaTeX and publish workflow. Use the research
interpreter by absolute path, `~/.venvs/research/bin/python`, for every tool.
Public PDF copies are `files/postmidterm-01-slides.pdf` through
`files/postmidterm-06-slides.pdf`. Original module teaching notes remain in the QMD sources and are stripped
from published HTML and PDFs. Classroom activity prompts are student-facing.


Session validation/export helpers use Node.js and Playwright (the bundled runtime
path is documented in each script):

```sh
node tools/check-postmidterm.mjs
node tools/export-postmidterm-pdf.mjs
```

The PDF exporter rewrites local preview links to the public website. The session
CSS embeds a DejaVu symbol fallback so scientific Unicode remains portable;
regenerate it with `~/.venvs/research/bin/python tools/build-postmidterm-fonts.py`.
The font license travels with the CSS in `assets/`.


## Pre-class readings

Six original three-page handouts are published as `files/preclass-week-01.pdf`
through `files/preclass-week-06.pdf`. Each contains essential concepts, one
synthetic worked example and three short preparation questions. The textbook
section locators refer only to the supplied contents photographs; no book title
or unseen chapter content is inferred. Preparation is part of the weekly time
budget, not another assignment. The optional partial-molar, Henry-solubility
and osmosis paper exercises do not add lab solvers.

Editable prose and the PDF builder live in `prereading/`. Regenerate from this
course-source directory (research environment with reportlab, matplotlib and
skh_palette):

```sh
MPLCONFIGDIR=/tmp/thermo-mpl ~/.venvs/research/bin/python prereading/figures/preclass_figures.py
MPLCONFIGDIR=/tmp/thermo-mpl ~/.venvs/research/bin/python prereading/tools/build_prereading.py --output ../../teaching/2105603/files
```

Copy the generated figure PNG/PDF pairs from `prereading/figures/generated/`
into `figures/` before rendering slides. Inspect rendered PDF pages and run
`pdffonts`; embedded fonts must not be Type 3. Rebuild the offline ZIP after
publishing the readings and refreshed classroom PDFs.


## End-of-class responses

In standard classroom sessions, the final 30 minutes are discussion (20), exit
ticket (5), feedback (3), and closing (2). In Session 2, the exit ticket and
feedback occupy study minutes 172–180, after the review and corrections. The classroom decks have 12 slides; Session 2 now has 28 slides for independent study. Their final slides contain
a QR and clickable link to `https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/?session=N`.

Responses persist in the Sites D1 table `course_responses`; the student page
has no response-list endpoint. The instructor can ask ChatGPT to read the Sites
database for reporting. No name, ID or email is requested. Do not add response
exports to this public repository.

Regenerate QR images with the research interpreter and
`figures/generate_exit_qr.py`. Verify that each QR decodes to its own session.
The offline package includes QR slides, but submitting the form needs internet.

### Session 2 independent study and narrated video

All student-facing Session 2 content is English. The 28-slide deck introduces
gamma from an ideal-mixture comparison, then guides every worksheet item and Lab
step. `files/week02-practice.pdf` contains four pages: phase/activity checks,
Antoine and baseline records, fit comparison and reasoning, and review answers.
Its editable source is `prereading/week02-practice.html`. With a local preview:

```
node tools/export-week02-practice.mjs
```

Set `COURSE_ORIGIN` if the preview is not on port 8766. Regenerate the three-page
Week 2 reading with `~/.venvs/research/bin/python prereading/tools/build_prereading.py
--week 2 --output ../../teaching/2105603/files`.

The video uses the same 28-slide PDF and validated male English narration.
Every slide starts with its own audio and remains visible for the exact PCM
length plus two seconds. `week02-video.html` offers chapters, transcripts and
optional activity pauses, enabled by default. The downloadable MP4 requires
students to pause manually. The 25-minute recording is part of the 180-minute
working schedule. Before viewing review solutions on Slide 26, students submit
their own Q1–Q6 attempt with
student ID and name at `https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site/attendance?session=2`.
The attendance form records completion, not a minimum accuracy score. Its link
is on the video page, course index, learning path, assessment page and worksheet.
After a successful save, the form reveals worked solutions. Students may submit
corrections afterward and retain their original worksheet, Lab exports and receipt.
The player pauses on Slide 25 with a direct submission link. This is instructional
guidance, not an access restriction on the existing public recording or slides.
The anonymous exit form remains separate and does not identify attendance.

Video sources and reproduction instructions are in `video-week02/`. Public
media are under `teaching/2105603/media/week02/`. The offline ZIP contains the
updated documents and labs; the video is available online or as a separate MP4
download. Rebuild the offline ZIP whenever course documents change.

The Sarabun fonts retain their OFL license. Keep private response reports and
student records outside this public repository.


### Week 2 feedback follow-up

`week02-clarifications.qmd` provides 12 content slides plus a title and three optional reference slides. Use the core review for the first 15 minutes of Session 3's existing opening block; the complete class remains 180 minutes. The recorded Week 2 deck and narration retain their synchronized slide order. The video landing page, course index, Lab 08 and learning path link this follow-up.

`prereading/week02-lab-guide.html` is a three-page English guide with the exact synthetic baseline, measured versus equation units, CSV and JSON workflows, model comparison, evidence limits and self-check answers. Render the slides with the public profile, vendor KaTeX, publish, then run `tools/export-week02-clarifications.mjs` against the preview specified by `COURSE_ORIGIN`. It exports the clarification PDF, guide PDF and revised Session 3 PDF. Rebuild the offline package after those exports. No student responses or identifying details belong in this public source.
