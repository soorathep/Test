# Optimization Lab

Static Quarto companion to all 47 problems in Volumes 1 and 2, integrated into the existing SKH course website. The catalog has 159 exact, precomputed Pyomo/HiGHS solutions. It does not solve or interpolate in the browser. Every selectable combination is checked. Prediction and reflection remain in the page and are not sent to a server.

## Reproduce the cases

```sh
uv pip install --python ~/.venvs/optim/bin/python -r requirements.txt
~/.venvs/optim/bin/python scripts/build_cases.py
~/.venvs/optim/bin/python scripts/build_all.py
~/.venvs/optim/bin/python scripts/verify_catalog.py
```

The first script creates the original detailed food-manufacture experiment. The second creates the complete 47-problem catalog. Models in `models/v1` and `models/v2` are snapshots from the workbooks with explicit experiment parameters added. Their SHA-256 hashes accompany the results. Do not overwrite workbook models with these teaching variants.

Every case requires optimal termination, a constraint/bound/integrality audit, and the model's independent domain checks. The original objectives are checked against 46 stored workbook results; Problem 1 is checked against its numerical reference directly. The original case stays the baseline even when the selected parameter changes. Alternative optimal plans may differ without changing their objective. No uniqueness is claimed. All menu options are feasible; these menus do not establish feasibility outside the listed range.

Charts are generated in `figures/charts.py` with Plotly and the imported lab palette. The sensitivity chart shows discrete cases as bars, not a continuous interpolated response. Source bundles contain complete worked answers.

## Website integration

The full website source additionally includes `index.qmd`, UI assets, and Quarto configuration. Run `build.sh` to regenerate and render the lab, then `scripts/link_chapters.py` to add a lab link to every rendered chapter. Reapply that script after replacing either rendered book. Book source and lecture slides remain separate projects. No speaker notes are involved.

The browser supports deep links such as `?lab=v1-17` and `?lab=v2-15`; the original `food`, `blend`, and `hydrogen` links remain aliases. `hydrogen` now opens the workbook's tank-design experiment rather than the initial fixed-tank demonstration.
