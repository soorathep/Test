# Lab 08 narrated screen walkthrough

The public film uses 49 edited views of the actual Excel and live Lab 08 interfaces, grouped into 14 chapters. Narration is English synthetic male speech generated locally with Kokoro v1.0, am_michael, speed 0.94. Duration: 608.3322917 seconds. Screenshots contain only the synthetic teaching workflow.

The observations were exported from the active VLE_data worksheet in desktop Excel and imported into the live Lab. Margules and NRTL were fitted. The saved Margules JSON was reopened, restored, validated, and refitted, reproducing both reported errors.

## Rebuild

Run from this directory with the absolute research interpreter. Install PyAV, NumPy, Pillow, SoundFile, SciPy, kokoro-onnx and the shared skh_palette package in that environment. The local Kokoro model files are excluded from Git: place kokoro-v1.0.onnx and voices-v1.0.bin in tmp/audio/kokoro-models, or pass --model-dir to the narration builder. Their original hashes are recorded in verification/timeline.json.

```sh
"$HOME/.venvs/research/bin/python" asynchronous-lab08/build-narration.py
"$HOME/.venvs/research/bin/python" asynchronous-lab08/build-video.py
"$HOME/.venvs/research/bin/python" asynchronous-lab08/build-video-page.py --timeline outputs/lab08-video/audio/timeline.json
```

Review outputs/lab08-video/contact-sheet.jpg and individual frames before publication. The video builder verifies exact sample coverage, all scene transitions, embedded chapters, H.264/AAC, faststart, source hashes, image fidelity, and audio synchronization. Visual review corrected the selector crops and ensured both residual charts include full axes and legends. Numerical audio checks passed; no claim of a complete subjective listening review is made.

Publish lab08-video.html to teaching/2105603/ and lab08-demo.mp4, poster.jpg, and audio/captions.vtt to teaching/2105603/media/lab08/. The existing Excel demonstration resources remain in teaching/2105603/files/. The offline ZIP links to this online video rather than embedding it.

Keep the scientific distinctions: all 19 observations are synthetic; the inferred activity coefficients assume ideal vapor and negligible Poynting correction; model recovery does not establish experimental consistency or prediction. The demonstration adds no new attendance task.
