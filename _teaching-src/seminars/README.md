# Seminars — slide decks (Quarto + Reveal.js)

Source for the one-off graduate seminars and invited talks published at
<https://www.skhgroup.net/teaching/seminars/>.

This folder starts with an underscore, so Jekyll ignores it: nothing here is
served. Only the rendered output in `teaching/seminars/` reaches the website.

Courses live in their own folders (`_teaching-src/2105620/` and so on). This
one is for talks that are not part of a course.

| File | Talk |
|------|------|
| `acssi-2026-plenary.qmd` | Beyond Ionic Conductivity, ACSSI 2026 Plenary Lecture 2, 14 September 2026 |
| `conferences.qmd` | Making Conferences Work for You — 17 August 2026 |
| `review-articles.qmd` | Beyond the Summary — MMS3, 9 September 2026 |

---

## Build

Install Quarto once from <https://quarto.org/docs/get-started/>. Then, from
inside this folder:

```bash
# while writing — live reload in the browser, speaker notes intact
quarto preview conferences.qmd

# publish to the website
quarto render --profile public --output-dir _site
python3 tools/publish.py                    # every deck it finds
python3 tools/publish.py conferences.html   # or just one
```

`--profile public` applies `tools/strip-notes.lua`, which removes every
`::: {.notes}` block. **Always use it for the website.** The notes contain the
full spoken script and private observations about the audience, and Reveal.js
ships notes inside the HTML — without the profile, anyone can press `S` and
read them.

`tools/publish.py` copies only the decks and merges `site_libs/`. It never
touches `teaching/seminars/index.html`, which is the Jekyll listing page, and
it refuses to publish a deck that still contains speaker notes.

Verify before committing:

```bash
grep -c 'class="notes"' ../../teaching/seminars/conferences.html   # must print 0
```

### Check the slides actually fit

```bash
python3 tools/check-overflow.py _site/conferences.html
```

Reveal clips anything past 1280 × 720 silently, and the clipped part is
usually the last card — which is where the point of the slide lives.

### One-file copy for presenting

For a laptop with no network, or to email the deck to someone:

```bash
python3 tools/bundle-deck.py conferences            # dist/, notes included
python3 tools/bundle-deck.py conferences --public   # notes stripped
```

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

The published deck has no speaker notes. Present from a local
`quarto preview`, or from a `bundle-deck.py` build without `--public`.

The notes in `conferences.qmd` carry running clock times in the form
`[00:24 – 00:29]` against a 12:00 start, so speaker view and the plan agree.

---

## Writing a slide

Same conventions as the course decks — see
`_teaching-src/2105620/README.md` for the full list of blocks and accents.
The theme here is a copy of that one, so the two stay visually identical.

One trap worth recording: **white cards do not work on a dark slide.**
`section.dark` sets `h3 { color: white }`, so a `### heading` inside a
`.card` on a `.dark` slide renders white-on-white and disappears without any
error. Use `.numbered`, `.dots` or `.steps` on dark backgrounds — those style
their own `strong` in ink and survive the override. The closing slide of
`conferences.qmd` was built the wrong way first.

Two more, learned while building `review-articles.qmd`:

**`.numbered` costs about 90 px a row.** Each `<li>` is a padded white card
with a 38 px disc, and `strong` inside it is `display: block`, so every item is
two lines minimum. Seven or eight items will not fit in 720 px once a title and
a `.punch` are on the slide. Use `.dots` instead and fold the ordinal into the
label — `- **1. Collection** …`. A `.dots` row is a 34 % / 1fr grid at roughly
48 px, so eight of them fit with room to spare. Accents are defined for
`nth-child(1)` to `(8)`; a ninth item falls back to teal.

**Inline markup breaks the `.dots` grid.** Every in-flow child of a grid
container becomes a grid item, so `- **Label** text *emphasis*` produces three
items, and the emphasis wraps onto the next row in the label column. Wrap the
whole right-hand side in one span — `- **Label** [text *emphasis*]{.dd}` —
whenever it contains `*`, `**` or a link.

---

## Adding a seminar

```bash
cp conferences.qmd 2026-09-09-review-articles.qmd
```

Edit the front matter and body, render, publish, then add an entry to
`_data/seminars.yml` — the talk appears on `/teaching/seminars/` by itself.

---

## Notes

- Fonts are bundled as base64 in `theme/_fonts-embedded.scss` — Source Serif 4
  and Source Sans 3 for Latin, Sarabun and Noto Serif Thai for Thai. Nothing is
  fetched from Google.
- Rendering writes into `teaching/seminars/`, which is committed. The site
  build does not run Quarto, so the published deck is exactly what was
  rendered here.

## MMS3 materials — updated 8 September 2026

The MMS3 presenter has explicitly published the full Thai speaking script and
editable sources with the slides. The MMS3 HTML therefore retains speaker notes.
This is an exception to the public-note stripping convention above; other seminars
keep their existing publication settings.

The verified 50-slide HTML and PDF, 29-page Thai script, 14-page handout and complete
Quarto ZIP are in `teaching/seminars/`. The editable master is `review-articles.qmd`;
its updated theme is isolated in `theme/mms3/` so other decks retain their appearance.
The ZIP includes both original Quarto filenames, themes, assets and build instructions.

Worksheet A and B are on handout PDF page 9; the worked evidence matrix is on page 12;
Worksheet C is on page 13. Existing deck and handout URLs remain usable.

## ACSSI 2026 plenary lecture

`acssi-2026-plenary.qmd` is the 24-slide Revision 6 presentation. Its styles and
images are isolated in `theme/acssi2026/` and `assets/acssi2026/`. It preserves
the approved 1280 × 720 slide design and embeds its resources in one HTML file.

Render only this deck with `quarto render acssi-2026-plenary.qmd --profile public`,
then copy the checked output with `python3 tools/publish.py acssi-2026-plenary.html`.
This repository copy contains source references only in the notes. The spoken
script and delivery cues are omitted from both the source and the website at
the presenter's request. The public profile removes the reference-note blocks
from the rendered HTML. The complete presenter version remains in the local
ACSSI project, Chair_Plenary_Talk/Revision_6. This does not regenerate the
separately authored PowerPoint or PDF.

The news announcement is `_posts/2026-09-13-plenary-acssi-2026.md` at the repository
root. The schedule is September 14, 2026, 11:00–11:40 AM, Rajamontien 4,
Montien Hotel Surawong, Bangkok (UTC+7). The HTML and PDF in `teaching/seminars/`
are ready for GitHub Pages; the website build does not require Quarto.
