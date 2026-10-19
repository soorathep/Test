# Week 3 handouts

The independent holiday lesson places thermodynamic consistency before liquid
stability and LLE. All student-facing text is English. Required work is limited
to 180 minutes, including the break, self-review, existing Session 3 exit ticket
and feedback. No new Week 3 video or attendance-identification form is promised.

## Build

From the website repository root:

```sh
MPLCONFIGDIR=/private/tmp/week03-matplotlib "$HOME/.venvs/research/bin/python" \
  _teaching-src/2105603/prereading/week03/build_week03.py \
  --output teaching/2105603/files
```

Dependencies: ReportLab, matplotlib, qrcode and the local `skh_palette` module.
The palette is imported; DejaVu Sans fonts are embedded. QR modules and text
are vector objects. No Type 3 fonts are used.

Outputs:

- `week03-practice.pdf`: four pages, sections A-I.
- `week03-solutions.pdf`: three pages of worked solutions and reference values.
- `week03-lab-guide.pdf`: three pages, exact Lab 03 and Lab 04 controls.
- `preclass-week-03.pdf`: three pages of optional background, consistency first.

The existing `tools/build_prereading.py --week 3` entry point calls this module's
`background` function so subsequent six-week builds cannot restore LLE-only
background or compulsory preparation. The other five week dictionaries and
their rendering are unchanged.

## Teaching sequence and reference values

Lab 03 uses an independent synthetic dataset, not Lab 08's demonstration
parameters. D1 records clean-reference area and local evidence; D2 introduces
canceling errors; D3 introduces a localized defect. D4 returns to the clean
reference and performs the only required model fit, at minutes 74-80.

Reference calculations were run directly against the shipped lab engines,
`src/engine/consistency.js` and `src/engine/stability.js`, using the lab's
`data/case-studies/ipa-water.json` unchanged. At 350 K, 41 points, amplitude
0.25, the area D/local-score pairs are:

- Clean: 0.0786915466 / 0.117763009.
- Canceling: 0.0735519252 / 15.5986977574.
- Localized: 2.0134632247 / 1.6718389636.

The localized case meets both aggregate criteria despite its visible residual
peak. The clean modeling errors are about 1.1248317e-6 percent for pressure and
6.4768432e-7 percentage points for vapor composition.

Lab 04 symmetric Margules A=3 gives endpoints 0.07072018168 and 0.92927981832.
At z=0.35, the beta fraction is 0.3252887818. These values differ intentionally
from the supplied hand-example endpoints 0.20 and 0.80, which give beta=0.25.

Primary method descriptions:

- https://trc.nist.gov/TDE/Help/TDE103b_v4_0/VLE-DataSets-ConsistencyTests/Herington.htm
- https://trc.nist.gov/TDE/Help/TDE103b_v4_0/VLE-DataSets-ConsistencyTests/Point.htm
- https://trc.nist.gov/TDE/Help/TDE103b_v4_0/VLE-DataSets-ConsistencyTests/VanNess.htm

Lab 03's finite-difference local diagnostic and parameterized modeling test
are teaching variants, not exact NIST TDE implementations. The documents
state the path assumptions, missing-endpoint limits and interpretation limits.

## Validation

Render with Poppler and inspect every page after content or layout changes.
`pdffonts` must show embedded fonts and no Type 3. The current 13 pages were
rendered and visually reviewed with no clipping or overlap. PDF text bounds,
page counts and links were checked. The legacy Week 3 prereading entry point
produces exactly the same extracted text as this renderer. `qa.json` records
the delivered file checks.
