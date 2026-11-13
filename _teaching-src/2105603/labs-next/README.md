# Thermodynamics labs for 2027

This source folder contains working Lab 01 and Lab 13 prototypes and the design plan for
the next version of the 13 course labs. The public preview is generated at
`teaching/2105603/preview-2027/`.

The preparation scope is a shared interaction design, two functional prototypes,
and a staged implementation plan. Independent student usability sessions and
the remaining 11 lab interfaces are future work. Implementation now proceeds in
lab-number order from Lab 01. Lab 13 is the earlier reference prototype.

## Evidence and design decisions

During the 13 November 2026 instructor walkthrough, the starting example was
difficult to find, the left/right species tables needed explanation, the editable
concentration was unclear, and the next investigative action needed verbal
instructions. These are observations from the walkthrough. Source inspection of
the other labs identifies candidate design problems for further testing.

The original Lab 13 puts its preset after the property, half-reaction and CSV
controls. The common learning guide and study workspace add separate instructions
and save/restore concepts before the calculation. The prototype brings the
assigned starting case, direct quantity inputs and calculation together.

The student path is to choose a case, enter quantities with units, make an
optional prediction, calculate, check the physical meaning and worked calculation,
then compare cases and save the study. Detailed model assumptions remain available
next to the inputs. Structured data editors are planned for measured data and
general reactions.

All student-facing copy uses English. Colors import the existing generated
Teal-Amber palette. Fonts follow the course's Source Sans/Source Serif typography.
Native fields, buttons, tables and details elements support keyboard use.

## Lab 01 prototype

The starting problem uses 1 mol of the synthetic ideal mixture at 350 K and
90 kPa with feed mole fraction z1 = 0.40. Students predict the phases, calculate,
distinguish phase composition from vapor fraction, read the P–x–y diagram, and
check that the two phases reconstruct the feed.

A simple vector illustration introduces the feed, flash vessel and two outlet
phases. Plain-language labels distinguish z1, x1 and y1 from the phase amounts
L and V. The caption explicitly limits the two-outlet picture to coexistence.

The visible inputs are temperature in K, pressure in kPa and feed mole fraction.
Pure-component vapor pressures at the current temperature are visible for the
paper calculation. Named cases compare 90, 100 and 75 kPa. Bubble and dew cases
use full-precision boundary conditions. One mol of feed is the fixed amount basis.

The prototype reuses `thermo.js` and `systems.json` from the current course lab.
Ideal, one- and two-parameter Margules and NRTL models are available in the model
disclosure, with the existing parameter and liquid-convexity checks. The two
property systems retain their temperature domains and source records. Synthetic
vapor pressures use their Clausius correlations, so 150/60 kPa apply at 350 K.

Absent phase compositions remain absent. At bubble/dew boundaries, limiting
compositions are labelled as incipient phases. Pure/azeotropic saturated states
retain an undetermined vapor amount when T, P and overall composition cannot
specify it. The phase diagram has a numerical curve-data alternative.

Students save named cases, compare pressure changes, download the study and
reopen it with their notes. Supported original studies are validated and
recalculated from their property and model context. Unsupported contexts have
an explicit route to the original Lab 01. Editing scientific inputs invalidates
the current result and diagram while retaining saved comparisons.

## Lab 13 prototype

The prototype uses the same `calculate()` engine as the current lab via
`../../labs/assets/electrochemistry.js`. The adapter maps concentration and
activity-coefficient fields to its validated half-reaction representation.
It implements the synthetic identical M2+/M concentration cell at 298.15 K,
with two electrons, a common standard-potential reference, equal standard
potentials of zero, a 1 mol/L concentration standard and zero junction potential.

The visible starting cases are the baseline, exchanged concentrations and equal
concentrations. Further cases investigate a smaller ratio and common scaling.
The activity coefficients are editable in the model disclosure.

Changing a scientific input invalidates the current displayed result and its
save/export actions. A saved comparison is a snapshot. Exports retain the existing
`kind: "electrochemistry"` and engine input representation, adding guided-version,
comparison and reflection fields. Supported original concentration-cell files
can be reopened. File contents are validated and recalculated before replacing
the current study. Other cell models have an explicit route to the general builder.

## Implementation sequence

The shared course configuration should identify the teaching year, session,
assigned starting case, worksheet version and response endpoint. Exit-ticket
and feedback reporting should distinguish teaching years in its metadata.
Each lab adapter should validate and recalculate supported older study files.
Pilot observations inform the readiness review for the 2027 cohort.

| Order | Labs | Main interface work |
| --- | --- | --- |
| Current prototype | 01 | Guided feed problem, units, phase interpretation, pressure comparison and balance check |
| Next | 02 | Fit and validation roles, investigative questions beside evidence |
| Then | 03–07 | Diagnostic applicability, Gibbs geometry, phase amounts, material/energy checks and structured observations |
| Then | 08–12 | Data mapping, equation/unit validation, property editors and structured reactions |
| Earlier reference, review in sequence | 13 | Two solutions, visible cases, physical interpretation, comparison and reopening |

### Per-lab design inventory

| Lab | Student workflow | Design focus |
| --- | --- | --- |
| 01 VLE/flash | Specify a mixture and compare states/models | Named starting problem, relevant model inputs, saved baseline |
| 02 Experimental case study | Inspect, fit, evaluate elsewhere | Distinct fitting/validation data, next question beside evidence |
| 03 Consistency | Compare diagnostic methods | Applicability before verdicts, perturbation linked to diagnostic |
| 04 Stability/LLE | Read Gibbs geometry and coexistence | Selected feed linked to curvature, tangent, endpoints and fractions |
| 05 LLE fitting | Enter observations and compare fits | Editable observation grid and fit/check/compare sequence |
| 06 VLLE | Identify coexisting phases and amounts | Clear conditions and quantities determined by the specification |
| 07 Adiabatic flash | Specify feed and solve balances | Feed route, temperature/phases, material and energy checks |
| 08 Experimental VLE input | Import measurements and properties | Column mapping, equation preview and unit/range validation |
| 09 Virial | Compare vapor models | Explained reference case, one-coefficient experiment, property editor |
| 10 SLE/GSE | Select a solid-equilibrium question | Separate task routes and relevant fields |
| 11 Adsorption | Compare, solve vessel or fit | Task-specific entry with matching inputs and outputs |
| 12 Reaction equilibrium | Calculate K then Q/extent | Named routes, structured species/properties and explicit comparison |
| 13 Electrochemistry | Predict polarity and change activities | Two solution fields, visible cases and sign interpretation |

## Verification and pilot

Lab 01 reference checks at 350 K, z1 = 0.40 and ideal liquid give the following
results for the synthetic binary. At 90 kPa, x1 = 1/3, y1 = 5/9, beta = 0.30,
L = 0.70 mol and V = 0.30 mol. The reconstructed component-1 amount is
0.70(1/3) + 0.30(5/9) = 0.40 mol. At 100 kPa the state is liquid only, and at
75 kPa it is vapor only. Bubble pressure is 96 kPa and dew pressure is
78.94736842105263 kPa. Pure-component saturation retains indeterminate amounts.

Adapter and browser checks cover the five named cases, pure saturation, all
four liquid models, model restrictions, invalid inputs and stale-result
invalidation. The saved-study checks include new studies with comparison rows,
supported original snapshots/workspaces and fixed-temperature fit transfers,
atomic rejection of invalid files, and asynchronous file-selection races.
Responsive checks include 320 px and enlarged text. Numerical results and
curve tables remain available when the optional plot library is unavailable.
These are functional checks, not evidence of independent student usability.

Numerical reference cases use the course engine. At 298.15 K, gamma = 1,
and E°cell = 0, the starting case 0.01/1 mol/L gives Q = 0.01 and E =
+0.05915935 V. Exchanging the concentrations gives Q = 100 and the negative
voltage. Equal activities give Q = K = 1 and E = 0. The 0.1/1 case gives
+0.02957967 V. Common scaling to 0.001/0.1 preserves the baseline ratio.
With both concentrations 1 mol/L and gamma left/right = 0.5/1, Q = 0.5 and
E = +0.00890437 V.

Check zero, negative, blank and nonfinite input messages, editing after a
calculation, immutable comparison snapshots, keyboard access, responsive reflow,
and a save/reopen round trip, including large valid studies. Malformed,
unsupported and partly invalid files should retain the current valid study.

For the student pilot, observe a first-time student start the assigned case,
predict/calculate, change the intended input, explain a comparison, and save/reopen
the study without instructor hints. Record completion, assistance, time and errors.
Test on the devices students use. These are proposed pilot tasks, with results
to be recorded after real sessions.

## Build

Run the scoped publisher from any working directory with the absolute research
interpreter.

```sh
"$HOME/.venvs/research/bin/python" _teaching-src/2105603/labs-next/build.py
```

Serve the repository with the existing course preview server. The calculator
loads the course engine as an ES module, so use a local HTTP server.

## Primary design references

- W3C form instructions https://www.w3.org/WAI/tutorials/forms/instructions/
- W3C user notifications https://www.w3.org/WAI/tutorials/forms/notifications/
- W3C form validation https://www.w3.org/WAI/tutorials/forms/validation/
- WCAG 2.2 target size https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- GOV.UK error summary https://design-system.service.gov.uk/components/error-summary/
