# Week 3 handouts

The 44-slide independent holiday lesson places thermodynamic consistency before
liquid stability and LLE. All student-facing material is English. Start at
`week03-study.html`; the recording, calculations, Lab investigations, review,
existing Session 3 exit ticket and feedback belong to the same approximately
180-minute lesson. The fixed activity budgets are 115 minutes of active
work/reflection and a 10-minute break. The expanded recording is expected to be
about 60 minutes, but the player reports its actual measured duration and the
sum with those activity budgets. These are planning estimates, not measured
student completion times or enforced waits. There are ten work checkpoints plus
the break. Background reading and the appendix remain optional; no additional
attendance-identification form is used.

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

- `week03-practice.pdf`: six pages, sections A-I.
- `week03-solutions.pdf`: four pages of worked solutions and reference values.
- `week03-lab-guide.pdf`: four pages, calculations and exact Lab 03/04 controls.
- `preclass-week-03.pdf`: three pages of optional background, consistency first.

The existing `tools/build_prereading.py --week 3` entry point calls this module's
`background` function so subsequent six-week builds cannot restore LLE-only
background or compulsory preparation. The other five week dictionaries and
their rendering are unchanged.

## Teaching sequence and reference values

Nominal elapsed study blocks, including recording and independent work:

| Minutes | Work | Worksheet |
| --- | --- | --- |
| 0-15 | Review composition, activity and fitting | p. 1, A1-A3 |
| 15-40 | Derive the slope relation and identify path corrections | p. 1, B1-B3 |
| 40-65 | Signed area, worked local calculation and independent local calculation | p. 2, C1-C6 |
| 65-95 | Real Lab 03 demonstration, predictions, sampling and model reproduction | p. 3, D1-D5 and E1-E2 |
| 95-105 | Break | |
| 105-155 | Stability, hand lever rule and three-feed LLE investigation | pp. 4-5, F1-F3 and G1-G4 |
| 155-170 | Unseen cases, attempted before solutions | p. 6, H1-H4 |
| 170-180 | Existing anonymous exit ticket, feedback and saved work | p. 6, I |

C4/C5 use the same numerical operator as Lab 03: form
`g = x ln(gamma1) + (1-x) ln(gamma2)`, estimate its slope, and subtract the
center log-activity ratio. C4 changes only the upper `ln(gamma1)` from 0.32
to 0.36, giving `g(0.60)=0.504` and residual `+0.120`. C5 changes only the
upper `ln(gamma2)` from 0.375 to 0.425, giving `g(0.50)=0.400` and residual
`+0.125`. Both clean residuals are zero apart from roundoff. The one-point
residual is not the dataset score `100 mean |r|`.

Lab 03 uses an independent synthetic dataset, not Lab 08's demonstration
parameters. D1 records the clean-reference area and local evidence. Students
predict D2/D3 before seeing the canceling and localized perturbations. D4 is
the required localized 41-versus-161-point comparison. D5 returns to clean
41-point data and performs the only required model fit. E1/E2 retain an
annotated residual plot and a claim supported by evidence with a limitation.

Reference calculations use the shipped lab engines,
`src/engine/consistency.js` and `src/engine/stability.js`, with the lab's
`data/case-studies/ipa-water.json` unchanged. At 350 K and defect amplitude
0.25, the area D/local-score pairs are:

- Clean, 41 points: 0.0786915466 / 0.117763009.
- Canceling, 41 points: 0.0735519252 / 15.5986977574.
- Localized, 41 points: 2.0134632247 / 1.6718389636.
- Localized, 161 points: 1.9417238226 / 1.5656069081.

Both localized cases meet the aggregate criteria despite a visible residual
peak. Denser synthetic sampling does not add experimental measurements or
remove the imposed defect. Clean modeling errors are about 1.1248317e-6
percent for pressure and 6.4768432e-7 percentage points for vapor composition.
Lab 03 exports JSON evidence with input controls. To reopen it, expand
**Study workspace · reopen and compare cases**, use **Load studies or a comparison
JSON**, and select **Restore** beside the loaded case. Restore loads inputs;
recalculate or rerun **Run modeling test** to produce fresh results. Imported
results remain recorded evidence rather than replacing a fresh calculation.

There are two real-screen demonstrations: Lab 03 starts at slide 19 and the
complete Lab 04 workflow is on slide 35. Before Lab 04, slide 34 pauses for
three minutes of G1 predictions. Slide 36 then pauses for 25 minutes of
independent G2-G4 reruns, replacing the previous combined 28-minute allocation.
Students save all three cases. After restoring a saved Lab 04 case, check its
inputs and select **Find equilibrium** for a fresh calculation; imported results
remain recorded evidence.

Lab 04 symmetric Margules A=3 gives endpoints 0.07072018168 and
0.92927981832. The homogeneous feeds at z=0.02, 0.12 and 0.50 are stable,
metastable and unstable, respectively; their equilibria are one, two and two
liquids. At z=0.12, beta fraction is 0.05739824727 and the Gibbs-energy
decrease divided by RT is 0.00821635817. At z=0.50, the fractions are equal
and the decrease is 0.11519416888. These model endpoints differ intentionally
from the illustrative hand endpoints 0.20 and 0.80. G3 requires two independent
balances; G4 requires the z=0.12 energy calculation and global tangent evidence.
An A sweep, NRTL comparison, LLE fit and VLLE are optional extensions.

Primary method descriptions:

- https://trc.nist.gov/TDE/Help/TDE103b_v4_0/VLE-DataSets-ConsistencyTests/Herington.htm
- https://trc.nist.gov/TDE/Help/TDE103b_v4_0/VLE-DataSets-ConsistencyTests/Point.htm
- https://trc.nist.gov/TDE/Help/TDE103b_v4_0/VLE-DataSets-ConsistencyTests/VanNess.htm

Lab 03's finite-difference local diagnostic and parameterized modeling test
are teaching variants, not exact NIST TDE implementations. The documents
state the path assumptions, missing-endpoint limits and interpretation limits.
Real isobaric data without independent excess enthalpy receive no corrected
local verdict. Herington's empirical allowance does not supply that property.

## Validation

Render with Poppler and inspect every page after content or layout changes.
`pdffonts` must show embedded fonts and no Type 3. The current 17 pages were
rendered and visually reviewed by the document author; PDF text bounds, page
counts, calculations and links were checked. `qa.json` records the delivered
file checks. Keep this validation record synchronized when rebuilding.
