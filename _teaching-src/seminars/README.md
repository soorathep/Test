# Seminars — slide decks (Quarto + Reveal.js)

Source for the one-off graduate seminars and invited talks published at
<https://www.skhgroup.net/teaching/seminars/>.

This folder starts with an underscore, so Jekyll ignores it: nothing here is
served. Only the rendered output in `teaching/seminars/` reaches the website.

Courses live in their own folders (`_teaching-src/2105620/` and so on). This
one is for talks that are not part of a course.

| File | Talk |
|------|------|
| `conferences.qmd` | Making Conferences Work for You — 17 August 2026 |
| `review-articles.qmd` | Beyond the Summary: writing a high-impact review article — 9 September 2026 (MMS3 Talk) |

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

---

## Adding a seminar

```bash
cp conferences.qmd 2026-09-09-review-articles.qmd
```

Edit the front matter and body, render, publish, then add an entry to
`_data/seminars.yml` — the talk appears on `/teaching/seminars/` by itself.

### Shipping a handout with a talk

Drop the PDF into `teaching/seminars/` next to the rendered deck and add one
key to the entry in `_data/seminars.yml`:

```yaml
  handout: Beyond_the_Summary_Handout.pdf
```

`teaching/seminars/index.html` prints a "Participant handout (PDF)" link under
the note whenever that key is present. A deck can also link its own handout
with a plain relative href, since the PDF is a sibling of the rendered HTML —
`review-articles.qmd` does both.

---

## Notes

- Fonts are bundled as base64 in `theme/_fonts-embedded.scss` — Source Serif 4
  and Source Sans 3 for Latin, Sarabun and Noto Serif Thai for Thai. Nothing is
  fetched from Google.
- Rendering writes into `teaching/seminars/`, which is committed. The site
  build does not run Quarto, so the published deck is exactly what was
  rendered here.
