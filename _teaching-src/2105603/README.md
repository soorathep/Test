# 2105603 — slide decks (Quarto + Reveal.js)

Source for the decks published at
<https://www.skhgroup.net/teaching/2105603/>.

This folder starts with an underscore, so Jekyll ignores it: nothing here is
served. Only the rendered output in `teaching/2105603/` reaches the website.

One file per module, not per week. `eos.qmd` is Module EOS, 56 slides.

---

## Build

Install Quarto once from <https://quarto.org/docs/get-started/>. Then, from
inside this folder:

```bash
# while writing — live reload in the browser, speaker notes intact
quarto preview eos.qmd

# publish to the website
quarto render eos.qmd --profile public --output-dir _site
python3 tools/vendor-katex.py _site
python3 tools/publish.py                 # copies _site into ../../teaching/2105603/
```

Three steps, and all three matter.

`--profile public` applies `tools/strip-notes.lua`, which removes every
`::: {.notes}` block. **Always use it for the website.** Reveal.js ships speaker
notes inside the HTML, so without the profile any student can press `S` and read
the teaching notes, the common-misconception list and the questions you were
going to ask them.

`tools/vendor-katex.py` copies a pinned KaTeX build into `site_libs/katex/` and
repoints the HTML at it. Quarto links katex@latest from a CDN; every equation in
this module is live LaTeX, so a lecture theatre with no Wi-Fi would otherwise
lose all forty-four of them.

`tools/publish.py` copies only `eos.html`, `site_libs/` and `figures/`. It does
**not** copy Quarto's generated `index.html`, which would overwrite the Jekyll
course page. Never point `--output-dir` straight at `teaching/2105603/`.

Verify before committing:

```bash
grep -c 'class="notes"'  ../../teaching/2105603/eos.html   # must print 0
grep -c 'cdn.jsdelivr'   ../../teaching/2105603/eos.html   # must print 0
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

The published deck has no speaker notes. Present from a local `quarto preview`,
or from a `bundle-deck.py` build without `--public`.

---

## Writing a slide

Each `##` starts a new slide. The house blocks are documented in the 2105620
README; this deck adds nothing except the rules below, each of which exists
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

---

## Regenerating the deck

`eos.qmd` was generated from the original PowerPoint build script rather than
retyped, so the slide content and the speaker notes are the same text that was
lectured from. The generator lives outside this repo; if the PowerPoint source
changes, regenerate rather than hand-editing both.

Figures come from `figures/`, which is a copy of the module's Python toolkit
output. To change a figure, edit the script in the toolkit, re-run it, copy the
PNG here, and re-render.

---

## A new module

```bash
cp eos.qmd <module>.qmd
```

Edit the front matter and body, then add the module to `_data/act2026.yml` with
`slides: <module>.html`, and it appears on the course page by itself — in the
module list and as a link in the weekly schedule, through the `module:` key on
the relevant weeks.

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
