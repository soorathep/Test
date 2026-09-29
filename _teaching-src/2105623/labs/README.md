# Optimization Lab prototype

A static Quarto companion to Volumes 1 and 2, integrated into the existing SKH course website.

The browser selects one of 72 exact, precomputed Pyomo/HiGHS solutions. It does not solve or interpolate. Every combination available in the controls has a checked result. Prediction and reflection are session-local and are not sent to a server. The chart definitions are generated in Python using Plotly and the lab palette.

## Regenerate

Use the explicit lab interpreter:

```sh
uv pip install --python ~/.venvs/optim/bin/python -r requirements.txt
~/.venvs/optim/bin/python scripts/build_cases.py
```

Model sources are snapshots of the worked books: `food_manufacture.py` from Volume 1, `common.py`, `blending.py`, and `hydrogen.py` from Volume 2. Their SHA-256 hashes are embedded in the case data. Re-sync snapshots deliberately when the books change and rerun every case. Changing controls requires rebuilding the case library, not interpolating solver results.

The full website source additionally includes `index.qmd`, browser UI assets, and Quarto configuration. Run `build.sh` from that source directory to render to `teaching/2105623/labs/`. This is separate from the existing slide project. The course public slide profile and speaker notes are not involved.

The lab bundle includes model and figure code with answers. It is not an answer-free assignment package. No credentials or private lecture notes are included.
