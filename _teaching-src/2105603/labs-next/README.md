# Thermodynamics labs for 2027

This source folder contains working Lab 01–05 and Lab 13 prototypes and the design plan for
the next version of the 13 course labs. The public preview is generated at
`teaching/2105603/preview-2027/`.

The preparation scope is a shared interaction design, four functional prototypes,
and a staged implementation plan. Independent student usability sessions and
the remaining seven lab interfaces are future work. Implementation proceeds in
lab-number order, with Lab 06 next. Lab 13 is the earlier reference prototype.

Labs 01–05 now use a graduate teaching route. The foundation calculation is
a reproducible control; the core work audits assumptions, compares sensitivity
outputs and defends conclusions with evidence. Numbered instructions and explicit
quantity units remain available throughout.

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

The saturation-property block explicitly labels P1sat(T) and P2sat(T), shows
each component name and pressure in kPa, and explains pure-component equilibrium
with a closed-vessel illustration. The entered mixture operating pressure is
identified separately. An adjacent disclosure provides the correlation, its
constants, units, temperature range and source. Fixed-temperature imports are
identified as supplied values. Invalid temperatures clear the displayed numbers.

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

## Lab 02 prototype

The guided case uses the existing isopropanol/water measurements and NRTL engine
from `ipa-water.json` and `case-study.js`. Measured data remain read only. The
starting problem fits two constant tau values to 60 kPa and evaluates that frozen
fit against the 80 kPa observations. The sequence is inspect a measurement,
calculate activities, fit, inspect plots, then save and explain a comparison.

The starting measurement is Table 4, row 7: T = 341.25 K, P = 60 kPa,
x1 = 0.4943 and y1 = 0.5690. Antoine constants, their equation and units are
visible beside optional numerical practice fields. Students can enter saturation
pressures in kPa and dimensionless activity coefficients, check their answers
with a stated rounding tolerance, and open the worked calculation.

There are 18 usable activity pairs at 60 kPa and 17 at 80 kPa. Pure endpoints
cannot supply the absent-component activity. A further 80 kPa observation falls
outside the joint Antoine range of 334 to 362.41 K. All measured rows remain
visible with exclusion reasons, and curve gaps are preserved without extrapolation.

Core equations and dynamic mathematical tokens use native MathML for fractions,
subscripts and superscripts. Plot labels use script markup, and ordinary form
labels use HTML scripts. The formulas remain readable at 200% text on a narrow
screen, with keyboard-accessible scrolling for long expressions.

Fit alpha is held fixed, initially 0.47, while two dimensionless tau parameters
are estimated. The optional alpha control is restricted to 0.10 to 0.60 for this
teaching exercise. Fit errors use dimensionless ln-gamma RMSE over 2N residuals.
Changing the checking pressure retains the parameters. A joint fit to both
pressures has no held-out pressure. The article's temperature-dependent reference
was fitted against broader data and is not treated as a held-out validation model.

Native studies reopen in this prototype with recomputed results, saved
comparisons and explanations. Supported original Lab 02 exports can be imported.
The original Lab 02 interface does not restore the new prototype's fitted-model
state, so that reverse compatibility is not claimed. Model consistency checks
and regression errors do not certify experimental thermodynamic consistency.

## Graduate investigations in Labs 01 and 02

Shared presentation is in `assets/graduate.css`. The scientific scenario methods
are pure modules, `vle-graduate.js` and `case-graduate.js`, using the unchanged
course engines. The measurements, source correlations and current-semester labs
remain unchanged. Each prototype uses its existing single study-file workflow.
Graduate control settings, run selections and structured notes are validated
before restoring a study, and derived results are recalculated rather than trusted.
Studies without the optional graduate block remain supported.

Lab 01 compares four liquid-model candidates at a common baseline and retains
invalid or nonconvex candidates as explicit outcomes. Its sensitivity exercise
evaluates ten signed one-factor scenarios and 32 signed joint corners in T, P,
z1 and independent multiplicative scales of the two saturation-pressure
correlations. Antoine scaling shifts A by log10(scale); Clausius scaling changes
the reference pressure; fixed records scale their supplied pressure. The original
property record is not edited. Fixed-temperature NRTL references are not moved
to admit an otherwise invalid temperature scenario.

Finite-beta, indeterminate and failed scenarios are counted separately. Reported
minima and maxima cover only the evaluated corners. They are not probabilities,
confidence intervals, or proven global bounds. Zero half-widths can repeat a
physical state. At the default 90 kPa baseline all 32 corners remain two phase,
but beta spans approximately 0.1761565 to 0.4259372. At the 96 kPa boundary,
the same bounds produce 16 liquid and 16 two-phase outcomes. This separates
robustness of phase identity from sensitivity of phase amount.

Lab 02 evaluates eight one-factor scenarios and sixteen joint corners for one
valid interior measurement in T, P, x1 and y1. The demonstration half-widths are
assumed analysis settings. The article's reported average expanded uncertainties
with coverage factor 2 are not treated as independent pointwise standard
deviations or automatic regression weights. Shared inputs also correlate inferred
log-activity values. The uncertainty discussion identifies which input error
distributions and covariances would be required for statistical propagation.

The conditional-fit exercise holds alpha at 0.30, 0.47 and 0.60 in separate
two-parameter fits to the same training observations. It retains the checking
pressure and reports parameter, score, convergence, bound and sampled-curvature
changes without changing the student's retained model. This is not a joint
three-parameter fit or an identifiability proof. If checking scores inform alpha
selection, that set has served model selection and cannot also be described as an
untouched final test of the selected model. Fresh independent data or an
appropriate validation design would be required.

Both routes conclude with structured claims about assumptions, sensitivity,
model discrepancy and the next evidence needed. The record check indicates
completion of calculations and written sections; it does not grade scientific
reasoning. The original general reflection remains an optional additional note.

## Lab 03 graduate consistency investigation

The guiding question is whether satisfying one diagnostic criterion is enough
to justify using a VLE data set. Students first calculate the synthetic
isothermal reference at 350 K, then impose a canceling log-activity-ratio defect.
The visible opening data guide identifies model-generated cases A–C, the article
measurements in case D and the 80 kPa option, component order, measured versus
derived quantities and the purpose of each control. A source note beside the
data selector updates with the selected family and sampling resolution. No
experimental file is required; the JSON opener restores this lab's saved work.
Students can open a preview of every supplied T/P/x/y row, with a column key and
units, before calculating. Four method-specific plots remain visible together:
area cancellation, the Herington boiling range, local residuals, and fitted
pressure/composition residuals in separate panels. The graph captions retain
method applicability and distinguish aggregate criteria from pointwise values.
The numbered route separates applicability, a control calculation, a deliberate
challenge and a defended conclusion. A conceptual vector diagram distinguishes
global area cancellation from local agreement. Mathematical quantities use
native MathML or HTML scripts, with units beside editable quantities.

The adapter reuses `consistency.js` and the existing measured-data/property
records. Original course engines and measurements remain unchanged. The four
methods are the piecewise-linear isothermal area criterion, the empirical
Herington D−J variant, a three-point differential Gibbs–Duhem diagnostic and a
Van Ness-type NRTL modeling-capability test. They are teaching implementations,
not reproductions of the complete NIST TDE algorithms. A status refers only to
the stated criterion. A converged model fit is not independent certification
of experimental thermodynamic consistency.

For isothermal area analysis, pressure/excess-volume effects are neglected.
For isobaric differential analysis, the synthetic generator supplies an excess
enthalpy correction. No equivalent verdict is assigned to real isobaric data
without independent excess-enthalpy information. The Herington boiling-range
allowance is empirical, not a measured excess-enthalpy correction. Missing
endpoint intervals remain missing unless a clearly labeled extrapolation or
smoothing assumption is selected. Pure experimental endpoints cannot provide
the absent component's activity coefficient; synthetic endpoint limits are
known from their generator.

The graduate investigations compare sampling resolutions, endpoint assumptions
and deterministic perturbations of measurements. Scenario ranges and counts
are sensitivity evidence, not uncertainty distributions, confidence intervals
or probabilities that a data set is consistent. Eight one-factor common-bias
scenarios shift all temperatures or pressures together, or shift interior x or
y measurements while retaining pure-component identities. The nominal included
activity set is retained. An invalid included observation rejects the whole
scenario instead of silently removing it. A statistical assessment would need
experimentally justified uncertainties and covariance. A common pressure bias
is a useful blind spot: both log activities shift together, leaving the area
log-ratio and composition derivative unchanged under the adopted approximations.

At the 81-point isothermal reference, D is approximately 0.0196883% and the
differential mean score is 0.0301719. With a canceling amplitude of 0.25,
D remains approximately 0.0183991%, while the differential mean score rises to
15.7781. This shows why an area criterion alone can miss imposed errors.
A localized defect with the same amplitude gives D approximately 1.95606% and
a differential mean score of 1.59077, both below their aggregate thresholds.
Students therefore inspect the residual trace and its maximum as well as the
mean. A local defect is not guaranteed to exceed an aggregate threshold.

Native study files retain settings, written claims and comparison contexts.
Reopening validates inputs and recomputes derived results. Changed scientific
controls invalidate current results while retaining written notes and saved
comparisons. Unsupported or malformed files retain the current valid study.
Numerical references, state checks and browser checks are recorded privately;
they do not establish independent student usability.

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
| Current graduate prototypes | 01–03 | Guided calculations, model evidence, sensitivity and consistency-test interpretation |
| Next | 04 | Gibbs geometry, liquid stability, supporting tangents and coexistence |
| Then | 05–07 | Fitting, phase amounts, material/energy checks and structured observations |
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
Responsive checks include 320 px with 200% text and the desktop layout. Mobile
phase-composition cards stack to keep labels and complete values readable. Numerical results and
curve tables remain available when the optional plot library is unavailable.
These are functional checks, not evidence of independent student usability.

Lab 02 reference checks reproduce P1sat = 55.85317436 kPa,
P2sat = 28.70289322 kPa, gamma1 = 1.23658805 and gamma2 = 1.78159872 for the
starting observation. At alpha = 0.47, fitting 60 kPa gives tau12 = 0.3618155960
and tau21 = 1.7524367107. Training ln-gamma RMSE is 0.1682833041, and the retained
fit has a held-out 80 kPa RMSE of 0.1643767093. A joint fit uses 35 pairs with
RMSE = 0.1548271965 and has no held-out pressure.

Lab 02 adapter and browser checks cover numerical inference, fixed-alpha fitting,
retained evaluation, all three views, exclusions, source-bearing original imports,
native studies and saved comparisons, invalid-file atomicity, delayed imports,
plot-library fallback and keyboard error recovery. Layout checks include 320 px
with 200% text and 1280 px desktop. These checks do not establish student usability.

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
- NIST uncertainty propagation https://physics.nist.gov/cuu/Uncertainty/combination.html
- NIST expanded uncertainty and coverage https://physics.nist.gov/cuu/Uncertainty/coverage.html

## Lab 04 prototype

The starting problem uses 1 mol of a symmetric Margules liquid with A = 3 at fixed
T and P. The named feeds z1 = 0.50, 0.12 and 0.02 match the post-midterm lesson and
worksheet (unstable, metastable and stable homogeneous feeds; the labels are not
shown before calculation). Students calculate the coexistence compositions, the
lever-rule amounts, the Gibbs energy decrease, the local curvature and the global
tangent-plane distance, then check the material balance and chemical-potential
equality.

The graduate route has three investigations. A compares local curvature with the
global tangent-plane distance for several feeds. B runs deterministic one-at-a-time
and signed-corner scenarios for the model parameters and feed, reports the closed-form
binodal derivative for symmetric Margules, and repeats near the critical point
(A = 2.05), where the phase count itself changes. C builds two-parameter Margules and
NRTL candidates (alpha = 0.2, 0.3, 0.47) that reproduce the same infinite-dilution
activity coefficients and compares their predicted splits. At A = 3, NRTL with
alpha = 0.47 predicts no miscibility gap, so dilute activity data cannot decide the
LLE. Lab 02 fits link into Lab 04 with their constant tau values.

## Lab 05 prototype

The starting problem is a synthetic control: one tie line at 298.15 K generated by
NRTL with tau12 = 3, tau21 = 2 and alpha = 0.3. Fitting the two tau values at fixed
alpha recovers the known values. The measured cases use the cyclohexane (1) + methanol
(2) tie lines of Atik and Kerboub (2008) from NIST ThermoML, at 298.15 and 313.15 K.
Each fit reports the chemical-potential residual, the tie line predicted by the global
common tangent of the fitted model, the composition error, the TPD at the predicted
liquids, the number of converged starts and a residual-Jacobian singular-value ratio.

The graduate route has three investigations. A predicts the eight other measured tie
lines with constant tau, tau proportional to 1/T, and tau = a + b/T from two
calibration temperatures. At alpha = 0.3 and 298.15 K the held-out RMS composition
error falls from 0.077 (constant) and 0.056 (1/T) to 0.0097 (a + b/T with 313.15 K).
B refits the same tie line at alpha = 0.2, 0.3 and 0.47; alpha = 0.47 converges but
misses the tie line. C refits within the source expanded uncertainties.
