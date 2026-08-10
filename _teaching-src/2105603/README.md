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
| `vle.qmd` | 4 · Vapour-Liquid Equilibrium of Mixtures | 41 + 5 appendix | Soorathep |
| `stability.qmd` | 5 · Phase Stability and Complex Equilibria | 24 | Soorathep |
| `reaction.qmd` | 6 · Chemical Equilibrium | 29 | Soorathep |

The five appendix slides in `vle.qmd` carry `visibility="uncounted"`: they are
reachable but do not advance the slide counter, so the deck reads as 41 slides
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
python3 tools/vendor-katex.py _site
python3 tools/publish.py                 # copies _site into ../../teaching/2105603/
```

To rebuild one module only, name it in both commands:

```bash
quarto render vle.qmd --profile public --output-dir _site
python3 tools/vendor-katex.py _site
python3 tools/publish.py vle.html
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
python3 _teaching-src/2105603/tools/verify.py
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
python3 tools/check-overflow.py _site/vle.html
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
  fetched from Google. Re-run `python3 build_fonts.py` from inside `theme/` only
  if you change a font file.
- Equations are live LaTeX rendered by KaTeX, not images. They stay sharp at any
  zoom, they can be copied, and a screen reader can read them.
- The site build does not run Quarto, so the published deck is exactly what was
  rendered here.
- `_data/act2026.yml` deliberately carries no weekly schedule and no assessment
  table. Both stay off the public page until they come from the registered
  syllabus rather than from a draft.
