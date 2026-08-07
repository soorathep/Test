# 2105620 — slide decks (Quarto + Reveal.js)

Source for the slide decks published at
<https://www.skhgroup.net/teaching/2105620/>.

This folder starts with an underscore, so Jekyll ignores it: nothing here is
served. Only the rendered output in `teaching/2105620/` reaches the website.

---

## Build

Install Quarto once from <https://quarto.org/docs/get-started/>. Then, from
inside this folder:

```bash
# while writing — live reload in the browser, speaker notes intact
quarto preview w01.qmd

# publish to the website (run from this folder, at the repo root level)
quarto render --profile public --output-dir ../../teaching/2105620
```

`--profile public` applies `tools/strip-notes.lua`, which removes every
`::: {.notes}` block. **Always use it for the website.** The notes contain the
Activity 2 answer key and private teaching observations, and Reveal.js ships
notes inside the HTML — without the profile, any student can press `S` and read
them.

Verify before committing:

```bash
grep -c '<div class="notes"' ../../teaching/2105620/w01.html    # must print 0
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
| `S` | Speaker view — spoken script, next slide, elapsed timer |
| `F` | Full screen |
| `E` | Print layout, then Print → Save as PDF |
| `O` | Slide overview |
| `?` | All shortcuts |

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

All colours and type live in `theme/teal-amber.scss` — the same Teal–Amber
palette as the group's Matplotlib figures. Note this is deliberately *not* the
website palette; a deck read from ten metres away needs different contrast from
a page read at arm's length.

---

## A new week

```bash
cp w01.qmd w03.qmd
```

Edit the front matter and body, and keep the last line —
`{{< include _feedback.qmd >}}` — so the closing QR slide is added
automatically. One QR serves all fourteen weeks; the feedback form separates
sessions by submission time.

Then add the week to `_data/rcs2026.yml` with `slides: w03.html`, and the link
appears on the course page by itself.

---

## Notes

- Fonts are bundled as base64 in `theme/_fonts-embedded.scss` — Source Serif 4
  and Source Sans 3 for Latin, Sarabun and Noto Serif Thai for Thai. Nothing is
  fetched from Google. Re-run `python3 build_fonts.py` from inside `theme/` only
  if you change a font file.
- Rendering writes into `teaching/2105620/`, which is committed. The site build
  does not run Quarto, so the published decks are exactly what was rendered here.
