# Publish the Gibbs review recording

The player uses the measured final timeline and seven optional work pauses totaling 29 minutes. Its recording replaces the read-through portion of the review. It adds no attendance or repeat exit-ticket requirement.

## Prepare and verify

Run these commands from the teaching workspace after the recording pipeline has completed and the actual video, narration and Lab captures have been reviewed. Use the absolute interpreters.

```sh
cd "$HOME/Documents/Projects/Adv thermo"
"$HOME/.venvs/research/bin/python" asynchronous-gibbs-review/build-video-page.py
"$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" asynchronous-gibbs-review/test-player.mjs --output outputs/gibbs-review-video/player-controller-qa.json
```

The controller checks use measured media metadata by default. The optional `--fixture` flag only tests event logic using private synthetic timings. Fixture results cannot pass the publication preflight and are not copied to the website.

Review the player on desktop and a narrow screen. Check chapter jumps, captions, activity pauses, Continue, resource links and the JSON download. Actual media and browser review are separate from the controller's mocked-event checks.

## Stage the public files

Set the website path to the actual website checkout. The script only copies files; it never commits, pushes or deploys.

```sh
"$HOME/.venvs/research/bin/python" asynchronous-gibbs-review/stage-publication.py --site "$HOME/Documents/GitHub/Test" --check-only
"$HOME/.venvs/research/bin/python" asynchronous-gibbs-review/stage-publication.py --site "$HOME/Documents/GitHub/Test"
```

The `--workspace` option selects a different workspace. Its default is `~/Documents/Projects/Adv thermo`. The website receives:

- `teaching/2105603/week03-gibbs-review-video.html`.
- Four media files in `teaching/2105603/media/gibbs-review/`: MP4, poster, final captions and transcript.
- `teaching/2105603/files/gibbs-review-lab04-study.json`, the synthetic A = 3, z = 0.35 demonstration result. It is not a student submission.
- Reproducible scripts, narration, referenced Lab captures and verification metadata in `_teaching-src/2105603/video-gibbs-review/`.

Staging uses explicit allowlists. No model weights, sentence caches, PCM audio, private feedback reports or student responses are copied. Final caption timings are taken from the video output, not the audio-only output. The reviewed ASR report is archived as `verification/asr-spot-check-transcripts.json`; its scope and limitations are preserved.

Course index and Week 3 study/video navigation edits live in their existing canonical sources. The Gibbs review remains optional; the original lesson and its player are preserved.

## Refresh the offline package

`build-offline.py` is a reviewed copy of the existing Labs builder, extended only for the new review resources. It does not change the original Labs repository. Its changes are:

1. Exclude `week03-gibbs-review-video.html` because its large media are not included.
2. Rewrite every link to that omitted player to the public URL, preserving query strings and chapter fragments.
3. Include only the explicitly named synthetic demonstration JSON, plus the existing review slides and PDFs.
4. Explain the online review video and optional status in the offline homepage and README.

After staging the public review files, run:

```sh
SKH_WEBSITE_DIR="$HOME/Documents/GitHub/Test" "$HOME/.venvs/research/bin/python" asynchronous-gibbs-review/build-offline.py
SKH_WEBSITE_DIR="$HOME/Documents/GitHub/Test" "$HOME/.venvs/research/bin/python" asynchronous-gibbs-review/validate-offline.py
```

The ZIP contains no video player with missing local media. The review slide/document route and synthetic saved-study example remain usable locally. Re-run staging after offline validation if the new offline verification report should also be archived with the teaching sources.
