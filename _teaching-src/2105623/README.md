# 2105623 — slide decks (Quarto + Reveal.js)

Source for the slide decks published at
<https://www.skhgroup.net/teaching/2105623/>.

This folder starts with an underscore, so Jekyll ignores it: nothing here is
served. Only the rendered output in `teaching/2105623/` reaches the website.

---

## Build

Install Quarto once from <https://quarto.org/docs/get-started/>. Then, from
inside this folder:

```bash
# while writing — live reload in the browser, speaker notes intact
quarto preview w01.qmd

# publish to the website (run from this folder, at the repo root level)
quarto render --profile public --output-dir ../../teaching/2105623
```

`--profile public` applies `tools/strip-notes.lua`, which removes every
`::: {.notes}` block. **Always use it for the website.** The notes contain the
activity answer keys and private teaching observations, and Reveal.js ships
notes inside the HTML — without the profile, any student can press `S` and read
them. In Week 1 that is the three responses to be ready for in Activity 2; in
Week 2 it is the four ambiguities and the capacity duals.

Verify before committing:

```bash
grep -c 'class="notes"' ../../teaching/2105623/w01.html    # must print 0
```

### One-file copy for teaching

For a laptop with no network, or to email a deck to a co-teacher:

```bash
python3 tools/bundle-deck.py w01            # dist/w01.html, notes included
python3 tools/bundle-deck.py w01 --public   # notes stripped
```

That produces a single ~4 MB HTML file with nothing external. (Quarto's own
`embed-resources` drops custom SCSS themes, so the script renders twice and
injects the compiled CSS — see the comments in the file.)

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

Click-to-advance is added by `theme/click-advance.html`, wired in through
`_quarto.yml` so every deck gets it. It stays out of the way of links, controls,
double-clicks and text selection — see the comments in that file.

The published decks have no speaker notes. Present from a local
`quarto preview`, or from a `bundle-deck.py` build without `--public`.

---

## Writing a slide

Each `##` starts a new slide.

```markdown
## Four sentences. No more.

::: {.kicker .c-amber}
Activity 1
:::

::: {.numbered .n4}
1. **Who** I am ___, and I work on ___.
2. **The problem** The difficulty in this area is that ___.
:::

::: {.foot}
::: {.note}
Sentence 2 is the one most people cannot finish.
:::
:::

::: {.notes}
Speaker notes. Stripped from the published build.
:::
```

Backgrounds:

```markdown
## Title {.tint background-color="#F3F0EB"}                     warm paper
## Title {.dark background-color="#1C242B"}                     dark
## Title {.dark .divider .c-teal background-color="#1C242B"}    section break
## &nbsp; {.dark .mid background-color="#1C242B"}               centred statement
```

Blocks: `.kicker` `.lede` `.note` `.punch` `.flag` `.foot` `.vcenter`
`.cards` (`.feature` `.g3` `.stack`) `.card` `.chip` `.numbered` `.dots`
`.steps`/`.step` `.spec` `.evidence` `.statement`/`.statement-hi`
`.break-circle`

Accents: `.c-teal` `.c-amber` `.c-rust` `.c-sky` `.c-sage` `.c-plum`
`.c-mist` `.c-slate`

All colours and type live in `theme/teal-amber.scss` — the same file as
2105620, and the same Teal–Amber palette as the group's Matplotlib figures and
the printed course package. Note this is deliberately *not* the
website palette; a deck read from ten metres away needs different contrast from
a page read at arm's length.

---

## A new week

```bash
cp w01.qmd w03.qmd
```

Edit the front matter and body, and keep the last line —
`{{< include _feedback.qmd >}}` — so the closing QR slide is added
automatically. One QR serves all fifteen weeks; the feedback form separates
sessions by submission time.

Then add the week to `_data/opt2026.yml` with `slides: w03.html`, and the link
appears on the course page by itself.

---

## Notes

- Fonts are bundled as base64 in `theme/_fonts-embedded.scss` — Source Serif 4
  and Source Sans 3 for Latin, Sarabun and Noto Serif Thai for Thai. Nothing is
  fetched from Google. Re-run `python3 build_fonts.py` from inside `theme/` only
  if you change a font file.
- Rendering writes into `teaching/2105623/`, which is committed. The site build
  does not run Quarto, so the published decks are exactly what was rendered here.

---

## No LaTeX math in these decks

Quarto fetches MathJax from a CDN, so an equation renders as raw `\(z\)` on a
laptop with no network, and inside a `bundle-deck.py` single file that is
supposed to have nothing external. Every deck here therefore uses Unicode
(`≤ ≥ ∈ ∇ x₁ x₂ Σ`) with `<sub>` and `<sup>`, and sets algebra in a `.spec`
panel. Keep it that way when you add a week.

Two theme traps worth knowing before you write:

- `.dots` is a two-column grid. Any inline markup after the leading `**bold**`
  becomes its own grid cell and breaks the layout, so those items are bold plus
  plain prose only.
- A `.card` whose first child is a `###` gets absorbed into the heading's
  section by Pandoc. Start such a card with `[]{.dot}` or an `[eyebrow]{.eyebrow}`.

## Where the content comes from

These decks are the browser version of the printed course package kept in
`Lecture/Optimization/2026_optimization_v3/` on the instructor's machine. The
Beamer sources in `slides/` there are the reference for every number; the
session design and the speaker-note content come from `WEEK01_DESIGN.md`,
`WEEK02_DESIGN.md` and the matching `WeekNN_Session_Outline.docx`. If a figure
disagrees between the two, the Beamer source wins, because its numbers are the
ones verified against the notebooks.
