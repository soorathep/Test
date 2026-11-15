# 2027 session decks (sample: Session 1)

Seven sessions of 180 minutes, one Quarto + Reveal.js deck each, published at
`teaching/2105603/slides-2027/sNN.html`.

Each deck has, at the top right:

- **Narration** on/off: English voice per slide (Kokoro v1.0, voice am_michael,
  the same voice as the Lab 01 video).
- **Captions** off / English / Thai. With narration on, captions follow the audio
  sentence by sentence. With narration off, the slide's full text is shown to read.
- **Auto-advance** on/off: go to the next slide when the narration ends
  (for students studying on their own in a week without class).

Settings are remembered in the browser.

## Session pattern

Concepts (30 min), Activity 1 (10 min), lab demonstration (20 min), break,
Activity 2 as a pair investigation in the lab (70 min), discussion and exit
ticket (40 min). Activity slides use the `.activity` class (amber rule) and end
with a note for students studying on their own.

## Files

| File | Role |
|---|---|
| `s01.qmd` | slides |
| `s01-narration.json` | narration script per slide id: `en` caption, `th` caption, optional `say` (what the voice reads, for numbers and units) |
| `build_narration.py` | writes `narration/s01/<slide>.mp3` and `narration/s01.json` (cue times) |
| `figures/s01_pxy.py` | Pxy figure, text drawn in Source Sans 3 from the theme fonts |
| `narration-player.html` | the controls and caption box (included after the body) |
| `slides-2027.css` | layouts for the 2027 decks |
| `publish.py` | copies `_site/` to `teaching/2105603/slides-2027/` and points KaTeX at the vendored copy |

## Build

```bash
python3 figures/s01_pxy.py
python3 build_narration.py s01 --models <folder with kokoro-v1.0.onnx and voices-v1.0.bin>
quarto render s01.qmd
python3 publish.py
```

Slide ids in `s01.qmd` (`{#route}` etc.) must match the keys in the narration
JSON; the title slide is `title-slide`.
