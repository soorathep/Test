# 2105315 session decks

Fourteen sessions of 90 minutes before the midterm, one Quarto + Reveal.js deck each, published at
`teaching/2105315/slides/sNN.html`. Session 1 is built; the others follow one at a time.

Controls at the bottom left of every deck:

- **Narration**: off / English (Kokoro v1.0, voice am_michael, as in the 2105603 decks). A Thai voice appears
  in the same button once Thai recordings are added (see below); until then there is no Thai voice.
  The AI Thai voices tried (MMS-TTS Thai, F5-TTS-THAI) were not good enough, so none is published.
- **Pause / Resume** and **Replay slide** while narration is on.
- **Captions**: off / English / ไทย, in either language whatever the voice. With narration off, the slide's full text is shown.
- **Auto-advance**: next slide when the narration ends, for self-study.

Settings are remembered in the browser (keys `nr315-*`, separate from the 2105603 decks).

## Session pattern (90 min)

Concepts, Activity 1 (pairs, no computer), concepts, Activity 2 (the week's web lab), debrief, exit ticket.
Activity slides use `.activity` (amber rule) and end with a note for students studying alone.

## Exit ticket and feedback

The exit-ticket slide shows a QR code for `exit.html?s=N` (one PNG per session, `make_exit_qr.py N`).
The form is anonymous and posts to the same Cloudflare relay as 2105603; answers are saved in the private
repository `soorathep/course-feedback` under `responses/2105315/sNN/`. Setup, the relay code,
`collect.py` and the guide are in that repository. Add each session's question to
`PROMPTS` in `exit.html`.

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
python3 build_narration.py s01 --only en --models <folder with kokoro-v1.0.onnx and voices-v1.0.bin>
quarto render s01.qmd
python3 publish.py
```

## Replacing the Thai voice with a recording

Record one MP3 per slide, name it `<slide-id>.th.mp3`, put it in `narration/s01/`, then run
`python3 build_narration.py s01 --only en --keep-th`. Thai caption timing is then spread over each
recording by sentence length; read the sentences in the order of the narration file.
