# Galvanostatic Charge–Discharge (GCD) — run, calculate, report

GCD cycles the cell at **constant current** between two voltage cut-offs and records the voltage.
It is the workhorse test: it gives **capacity**, **Coulombic efficiency**, the **voltage profile**
(and thus energy and average voltage), **cycle life / retention**, and **rate capability** — and, for
capacitors, **capacitance** and **ESR**.

> This pairs with the **Battery reporting checklist** (same section): GCD is where most of those
> numbers come from, so report loading, area, current basis, and cell count alongside them.

---

## What GCD gives you

| Quantity | From |
|---|---|
| Specific / areal capacity | `q = I·Δt / (3.6·m)` or `I·Δt/A` |
| Coulombic efficiency (CE) | discharge/charge charge ratio |
| Voltage profile, plateaus | V vs capacity |
| Specific energy, average voltage | `∫V dQ` |
| Capacity retention, cycle life | capacity vs cycle |
| Rate capability | capacity vs C-rate |
| (Supercapacitors) capacitance, ESR | discharge slope, IR drop |

---

## How to run it — choosing parameters

- **Current** — state it as a **C-rate** *and* a current density (mA cm⁻² or mA g⁻¹), and **define 1C**
  (which capacity it is based on).
- **Voltage window** — the cut-offs; inside the safe range for the chemistry.
- **CC vs CC–CV** — say whether you hold at the top (constant-voltage step) and give the **CV cut-off
  current**; a CC–CV charge adds capacity that a CC-only discharge will not return (affects CE).
- **Formation cycles** — run a few and **report a steady cycle**, not the first.
- **Rest / relaxation** between charge and discharge, if any.
- **Temperature** (and whether controlled); **number of cycles**; cell format and **mass loading**.

---

## Calculations

### Capacity, efficiency, energy
```
Specific capacity   q   = I·Δt / (3.6·m)              [mAh/g]   (I in A, Δt in s, m in g)
Areal capacity      q_A = I·Δt / (3600·A)             [mAh/cm²]
Coulombic eff.      CE  = Q_dis / Q_ch  = Δt_dis/Δt_ch  (constant I)   [%]
Specific energy     E   = I·∫V dt / (3.6·m)           [mWh/g]
Average voltage     V̄   = E / q
Capacity retention  = Q_N / Q_1 × 100 %
```

### Supercapacitors (triangular profile)
```
Capacitance (discharge slope)   C = I / |dV/dt|        → C_specific = C/m   [F/g]
   (fit dV/dt on the linear 10–90 % of the discharge, EXCLUDING the IR drop)
ESR (from the IR drop at reversal)  ESR = ΔV_IR / (2·I)   [Ω]
Energy  E = ½ C ΔV²        Power  P = E / Δt_dis
```
Use the **discharge** branch and a **two-electrode** cell for device-relevant capacitor numbers.

---

## Running several cycles

- **Report which cycle** the capacity/CE come from — a steady cycle, not formation.
- Plot **capacity vs cycle** and **CE vs cycle**; show **voltage profiles at selected cycles**
  (e.g. 1st, 10th, Nth) to reveal how the shape changes.
- **Do not point-by-point average voltage profiles** across cycles or cells — it smears plateaus.
  Show a **representative** profile.

## Running several samples

- Fix the current basis, window, protocol, temperature, and mass basis.
- **Normalise** (per g or per cm²) before comparing.
- Report capacity, CE, retention as **mean ± SD with n** (≥ 3 cells where feasible); overlay
  capacity-vs-cycle for all cells (thin) with the mean bold.
- Account for every cell (measured vs included, and why any were excluded).

---

## Presentation

- **Voltage vs specific capacity** for the profile; capacitors usually **voltage vs time** (triangles).
- **Capacity & CE vs cycle number** (twin axes) — with the multi-cell treatment above.
- **Rate capability:** capacity vs C-rate (and note recovery when the rate returns to low).
- Caption: current / C-rate, window, cycle number, temperature, mass loading, cell type.

---

## Caveats

- **CE needs enough significant figures** (99.92 %, not "~100 %"); tiny CE losses compound over
  hundreds of cycles.
- **Specific capacity basis** must be explicit (per active material vs per electrode/cell).
- **Ultra-low loading inflates** apparent rate and cycling — report a practical areal capacity.
- **CC–CV** on charge but CC-only discharge lowers CE for reasons that are protocol, not material.
- **Capacitance from GCD ≠ from CV** in general; state the method. Exclude the IR drop when fitting.

---

## References to read (start with 1–2)

1. **M. D. Stoller &amp; R. S. Ruoff, "Best practical methods for making the most reliable measurements
   on supercapacitors," *Energy Environ. Sci.* 3, 1294 (2010).** The standard for capacitor GCD.
2. The lab's **Battery reporting checklist** (same Resources section) — what to disclose with any GCD
   result.
3. **A. J. Bard &amp; L. R. Faulkner, *Electrochemical Methods*, Wiley** — fundamentals behind constant-
   current techniques.
4. **BioLogic Application Note 51** — DC (galvanostatic) characterisation of supercapacitors: capacity,
   energy, ESR, CE.
5. For batteries specifically: the reporting guidelines of **Joule**, **ACS Energy Letters**, and
   **Nature Energy** cited in the battery checklist.

**Script:** `gcd.py` (in the Resources downloads) computes specific capacity, CE, energy, retention,
and the supercapacitor C/ESR, and plots the voltage profile + capacity/CE-vs-cycle. Run `python gcd.py`.
