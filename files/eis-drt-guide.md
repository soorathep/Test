# EIS &amp; DRT — a simple guide: measure, analyse, plot, and report

**EIS** (electrochemical impedance spectroscopy) applies a tiny AC perturbation across a range of
frequencies and measures the impedance `Z(ω) = Z′ − jZ″`. Because different processes respond on
different timescales, EIS **separates them by frequency**: series resistance, film/SEI, charge
transfer, and diffusion each live in a different part of the spectrum.

**DRT** (distribution of relaxation times) is a **model-free** transform of the same EIS data into a
distribution `γ(τ)` of relaxation times. Overlapping arcs that blur into one semicircle on a Nyquist
plot become **separate peaks** on a `log τ` axis — so you can count and time-resolve the processes
without guessing an equivalent circuit first.

> One-line warning: EIS and DRT are only as good as the data. Use a **small amplitude**, a **stable
> (non-drifting) cell**, and **validate with Kramers–Kronig** before you interpret anything. DRT
> amplifies noise and its peaks depend on a regularisation parameter — always report it.

---

## EIS

### What it tells you (by frequency, high → low)
- **R_s / R_ohmic** — high-frequency real-axis intercept: electrolyte + contacts + wiring.
- **Film / SEI semicircle** — high-to-mid frequency (if present).
- **Charge transfer, R_ct** — mid-frequency semicircle; its **diameter = R_ct**, with a
  double-layer capacitance C_dl (use a **CPE** for a depressed arc).
- **Diffusion / Warburg** — low-frequency ~45° line (finite-length diffusion bends to a capacitive tail).

### How to run it (design)
- **Small amplitude** so the response is linear: ~**5–10 mV** (potentiostatic) around a defined DC
  point, or a current amplitude that keeps the voltage response ≲ 10 mV.
- At a **defined, equilibrated OCV / SOC** — let the cell relax first.
- **Wide frequency range** (e.g. ~100 kHz–10 mHz), enough points per decade (≥ 6–10).
- State **temperature**, and whether it is **2-electrode** (whole cell) or **3-electrode / symmetric
  cell** (to isolate one electrode).

### Validate the data first — Kramers–Kronig (KK)
KK holds only if the system is **linear, causal, and stable (time-invariant)**. Run a **Lin-KK** test;
if the residuals are small and unstructured, the spectrum is trustworthy. Large or systematic
residuals at low frequency usually mean the **SOC drifted** during the sweep — shorten the sweep,
increase amplitude only within the linear limit, or measure faster.

### How to analyse / calculate
- **Read directly:** R_s = high-f intercept; R_ct = semicircle diameter; the apex frequency gives the
  time constant `τ = 1/(2πf_apex)` and `C_dl = 1/(2π f_apex R_ct)`.
- **Equivalent-circuit model (ECM) fit:** report the **circuit you used**, the fitted values **with
  uncertainties**, and the **goodness of fit (χ²)**. Use CPEs for depressed arcs.
- **Non-uniqueness:** many circuits fit the same data. Keep the circuit as simple as the data justify,
  and support each element with physical reasoning (or with DRT — next section).

### How to plot
- **Nyquist** (−Z″ vs Z′) with **equal (1:1) axes** — this is essential; unequal axes turn circles
  into ellipses and mislead the reader. Mark the **frequency direction** and a few decade points.
- **Bode** (|Z| and phase vs log f) alongside it — Nyquist hides the frequency axis; Bode shows every
  frequency and reveals features a Nyquist plot buries.
- Overlay the **fit on the data** and show the **residuals**.
- **Normalise by electrode area (Ω·cm²)** whenever you compare samples.

### Cautions
- Amplitude too large → non-linear, KK fails. · Cell drifting → low-frequency distortion. ·
  High-frequency **inductive tail** from cables (below the real axis) — keep leads short, don't
  mistake it for a process. · Never publish a squashed (unequal-axis) Nyquist. · One semicircle is
  not automatically one process.

---

## DRT

### What it adds
`Z(ω) = R_∞ + R_pol · ∫ γ(τ) / (1 + jωτ) dτ`, with `∫ γ dτ = 1`. Each **peak in γ(τ)** is a process;
its **position** is the time constant `τ` (`f = 1/(2πτ)`) and the **area under the peak** is that
process's resistance. DRT resolves overlapping arcs far better than a Nyquist plot and needs **no
assumed circuit**.

### How to compute (and the one knob that matters)
- Use a tool: **DRTtools** (MATLAB) or **pyDRTtools** (Python).
- The inversion is **ill-posed**, so it uses **Tikhonov regularisation** with a parameter **λ**:
  - **λ too small** → high resolution but **noise-amplified, spurious peaks**.
  - **λ too large** → **oversmoothed**, peaks merge and disappear.
  - Choose λ objectively with the **L-curve**, **generalised cross-validation (GCV)**, or the
    **discrepancy principle** — and **report the value and the method**.
- Feed it **KK-valid, low-noise** data; handle the **high-frequency inductance** (crop or fit it);
  keep the **same frequency range** for every spectrum you compare.

### How to interpret &amp; plot
- Plot **γ(τ) vs log τ** (or vs log f). **Label each peak** with its assigned process and give λ + the
  tool in the caption.
- **Assign peaks with evidence, not by eye:** watch how a peak moves with **temperature** (activation
  energy), **SOC**, or in a **symmetric cell**. A peak is a time constant, not automatically a single
  physical step.
- Report each process's **R** (peak area) and **τ** (peak position); these feed a physically grounded ECM.

### Cautions
- Results **depend on λ** — show a brief sensitivity (2–3 λ values) or state how λ was chosen. ·
  Noise → fake peaks. · Don't over-interpret tiny peaks. · Same λ **and** same frequency range across
  all samples, or the comparison is meaningless.

### Worked example
From a spectrum with `R_s ≈ 8 Ω` (high-frequency intercept) whose DRT resolves two peaks —
`τ ≈ 2 ms, R ≈ 25 Ω` and `τ ≈ 50 ms, R ≈ 60 Ω` — you get `R_ct,total ≈ 85 Ω`, and each process's
capacitance from `C = τ/R` (≈ 80 µF and ≈ 830 µF). The low-frequency 45° tail is diffusion.
The script `eis.py` (in the Resources downloads) draws the correct Nyquist (equal axes) + Bode,
reads R_s / R_ct, and shows an illustrative DRT; use **pyDRTtools** for the real DRT on measured data
and report λ.

---

## Running replicates or several samples — how to report

- **Fix everything** across cells/samples: SOC, temperature, amplitude, frequency range, equilibration
  time, and (for DRT) λ and range. Otherwise the spectra are not comparable.
- **Normalise to area (Ω·cm²)** so different electrodes can be compared.
- **Do not just average raw spectra.** Instead: **fit each replicate**, then report the **parameters
  (R_s, R_ct, C_dl, …) as mean ± SD with n**. Overlay all spectra as **thin lines** with a
  **representative (median) one bold**.
- **DRT across replicates/samples:** compute each with the **same λ and range**, overlay the γ(τ)
  curves, and report **peak τ and peak area (R) as mean ± SD**.
- **Account for every cell** — how many measured vs included, and why any were excluded.
- State **n**, the frequency range, amplitude, temperature, and SOC **in every caption**.

---

## References to read (start with 1–2)

1. **A. Lasia, *Electrochemical Impedance Spectroscopy and its Applications*, Springer.** The standard
   teaching text — start here for EIS.
2. **M. E. Orazem &amp; B. Tribollet, *Electrochemical Impedance Spectroscopy*, 2nd ed., Wiley.** Rigorous
   treatment, including Kramers–Kronig.
3. **N. Meddings et al., "Application of EIS to commercial Li-ion cells: A review," *J. Power Sources*
   480, 228742 (2020).** Battery-specific practice and pitfalls.
4. **M. Schönleber, D. Klotz, E. Ivers-Tiffée, "A method for improving the robustness of linear
   Kramers–Kronig validity tests," *Electrochim. Acta* 131, 20 (2014).** The Lin-KK data-quality test.
5. **T. H. Wan, M. Saccoccio, C. Chen, F. Ciucci, "Influence of the discretization methods on the
   distribution of relaxation times deconvolution," *Electrochim. Acta* 184, 483 (2015)** — the theory
   behind **DRTtools / pyDRTtools**.
6. **M. Hahn et al., "Computation of DRT by Tikhonov regularization for Li-ion batteries: usage of the
   L-curve method," *Sci. Rep.* 11, 13285 (2021).** Choosing λ. https://doi.org/10.1038/s41598-021-91871-3
7. A recent review: **"Distribution of relaxation times: foundations, methods, diagnostics, and
   prognosis for electrochemical systems," *J. Power Sources / Electrochim. Acta* (2025).**

**Software:** DRTtools (MATLAB) and pyDRTtools (Python) — both open source, from the Ciucci group.
