# Thermodynamics labs for 2027

This source folder contains a working Lab 13 prototype and the design plan for
the next version of the 13 course labs. The public preview is generated at
`teaching/2105603/preview-2027/`.

The preparation scope is a shared interaction design, one functional prototype,
and a staged implementation plan. Independent student usability sessions and
the remaining 12 lab interfaces are future work.

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

| Stage | Labs | Main interface work |
| --- | --- | --- |
| Prototype and pilot | 13 | Two solutions, visible cases, prediction, physical interpretation, comparison and reopening |
| Next | 01, 08 | Task entry, simple phase inputs, data template/preview/mapping, Antoine form and unit checks |
| Data and evidence | 02, 03 | Fit and validation roles, diagnostic applicability, linked observations and residuals |
| Phase investigations | 04, 05, 06, 07 | Feed, Gibbs geometry, phase amounts, structured observations, material/energy checks |
| Property and reaction models | 09, 10, 11, 12 | Experiment-specific routes, property editors, structured reactions and independent checks |

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
