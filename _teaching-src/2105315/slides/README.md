# 2105315 session decks

Fourteen sessions of 90 minutes before the midterm, one Quarto + Reveal.js deck each, published at
`teaching/2105315/slides/sNN.html`. Session 1 is built; the others follow one at a time.

Controls at the bottom left of every deck:

- **Narration**: off / English / ไทย. English: Kokoro v1.0, voice am_michael (as in the 2105603 decks).
  Thai: Meta MMS-TTS Thai (`facebook/mms-tts-tha`, CC BY-NC 4.0), an AI placeholder until a recorded voice replaces it.
- **Pause / Resume** and **Replay slide** while narration is on.
- **Captions**: off / English / ไทย, in either language whatever the voice. With narration off, the slide's full text is shown.
- **Auto-advance**: next slide when the narration ends, for self-study.

Settings are remembered in the browser (keys `nr315-*`, separate from the 2105603 decks).

## Session pattern (90 min)

Concepts, Activity 1 (pairs, no computer), concepts, Activity 2 (the week's web lab), debrief, exit ticket.
Activity slides use `.activity` (amber rule) and end with a note for students studying alone.

## Files

| File | Role |
|---|---|
| `s01.qmd` | slides; slide ids (`{#route}`) must match the narration keys; the title slide is `title-slide` |
| `s01-narration.json` | per slide, sentences with `en`, `th` (captions) and `th_say` (what the Thai voice reads: Thai script only, English terms as they sound, numbers in words) |
| `build_narration.py` | writes `narration/s01/<slide>.en.mp3`, `.th.mp3` and `narration/s01.json` (texts and cue times) |
| `narration-player.html` | controls and caption box |
| `slides.css` | layouts; theme and click-to-advance come from `../../2105603/theme/` |
| `publish.py` | copies `_site/` to `teaching/2105315/slides/` and the Thai font to `teaching/shared/fonts/` |

## Build

```bash
pip install quarto-cli kokoro-onnx soundfile transformers torch
python3 build_narration.py s01 --models <folder with kokoro-v1.0.onnx and voices-v1.0.bin>
quarto render s01.qmd
python3 publish.py
```

## Replacing the Thai voice with a recording

Record one MP3 per slide, name it `<slide-id>.th.mp3`, put it in `narration/s01/`, then run
`python3 build_narration.py s01 --only en --keep-th`. Thai caption timing is then spread over each
recording by sentence length; read the sentences in the order of the narration file.
