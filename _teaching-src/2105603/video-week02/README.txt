SESSION 2 NARRATED VIDEO: REPRODUCTION

The three build scripts belong in asynchronous-week02/ under this directory.
Use the research interpreter by its absolute path. The build uses local Kokoro
models and the macOS audio encoder; no API credentials are used.

1. Install requirements into the research environment if needed:
   uv pip install --python ~/.venvs/research/bin/python -r requirements.txt
2. Put the published 28-page PDF at output/pdf/postmidterm-02-independent-study.pdf.
   Source in this repository: teaching/2105603/files/postmidterm-02-slides.pdf.
3. Put kokoro-v1.0.onnx and voices-v1.0.bin in tmp/audio/kokoro-models/.
   Official models: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1
   Voice/model information: https://huggingface.co/hexgrad/Kokoro-82M
4. Generate narration, video and player in order:
   ~/.venvs/research/bin/python asynchronous-week02/build-narration.py
   ~/.venvs/research/bin/python asynchronous-week02/build-video.py
   ~/.venvs/research/bin/python asynchronous-week02/build-video-page.py
5. Inspect the audio/video and browser activity pauses before publication.
   The video builder verifies all 28 slide transitions and samples audio sync.

Copy output/video/week02/week02-video.html to teaching/2105603/.
Copy week02-lecture.mp4, week02-poster.png, timeline.json and timeline.csv to
teaching/2105603/media/week02/.
Keep output/ and tmp/ untracked. They include large model weights and raw audio.
video-qa.json records the published build's checks and hashes.
The student player discloses synthetic narration and distinguishes video time
from the total 180-minute lesson. The offline ZIP links to the online video.
