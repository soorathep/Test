# Cyclic Voltammetry (CV) — run it, calculate it, report it

CV sweeps the potential up and back at a constant **scan rate** `v` and records the current. From the
peak positions, peak currents, and how they change with `v` you get: **redox potentials**,
**reversibility**, the **mechanism** (diffusion- vs surface-controlled), a **diffusion coefficient**,
**capacitance**, and how all of these **evolve over cycles**.

> Do the **b-value check first**. Randles–Ševčík (and a "diffusion coefficient") only make sense if
> the current is actually diffusion-controlled. If b ≈ 1 the process is surface/capacitive and you
> should report capacitance, not D.

---

## What CV tells you

| Read | From |
|---|---|
| Redox potentials E°′ ≈ (E_pa + E_pc)/2 | peak positions |
| Reversibility | ΔE_p, i_pa/i_pc, E_p vs scan rate |
| Diffusion- vs surface-controlled | **b-value** (log i_p vs log v) |
| Diffusion coefficient D | **Randles–Ševčík** (i_p vs √v) |
| Capacitive vs diffusive split at a potential | **Dunn** method |
| Capacitance | area of the CV loop |
| Stability / activation | change over cycles |

---

## How to run it — choosing parameters

- **Reference electrode** — state it (Ag/AgCl, SCE, Li/Li⁺, Hg/HgO…) and quote all potentials against it.
- **Potential window** — inside the electrolyte's stability; extend only far enough to capture the
  peaks. Going too far adds side reactions and irreversible damage.
- **Scan-rate range** — cover **at least a decade**, e.g. 5, 10, 20, 50, 100 (mV/s), so slopes
  (i_p vs √v, log–log) are well defined. Low rates → near-equilibrium; high rates → kinetics + more iR.
- **Start potential & equilibration** — start at OCV (or a defined potential) and let the cell settle.
- **Number of cycles** — run several and **report a stabilised cycle** (often the 3rd–5th), not the
  first (formation/activation). Show cycle 1 vs stabilised if they differ.
- **iR compensation** — correct or report the uncompensated resistance; iR drop distorts peaks at high v.
- **Cell** — usually **3-electrode** (working / counter / reference); state area and (for gravimetric
  metrics) active mass. Temperature too.

---

## Calculations

### Diffusion coefficient — Randles–Ševčík (reversible, 25 °C)
```
i_p = 2.69e5 · n^(3/2) · A · D^(1/2) · C · v^(1/2)
```
Plot **i_p vs √v** (a straight line through ~0 confirms diffusion control) and take the **slope**:
```
D = ( slope / (2.69e5 · n^(3/2) · A · C) )²
```
`n` electrons, `A` electrode area (cm²), `C` bulk concentration (mol cm⁻³; 1 mM = 1e-6), `v` (V s⁻¹).
For quasi-reversible/irreversible systems this constant changes (use the α-dependent form).

### Reversibility diagnostics
- `ΔE_p = |E_pa − E_pc| ≈ 59/n mV` at 25 °C (reversible; grows with v if sluggish).
- `i_pa / i_pc ≈ 1`.
- `E_p` independent of scan rate (reversible) vs shifting (irreversible).

### What controls the current — the b-value
```
i_p = a · v^b     → plot log(i_p) vs log(v);  b = slope
```
`b ≈ 0.5` diffusion-controlled · `b ≈ 1.0` surface / capacitive · in between = mixed.

### Capacitive vs diffusive split — Dunn method
At a **fixed potential**, across scan rates:
```
i(V) = k1·v + k2·√v      (k1·v = capacitive,  k2·√v = diffusion)
i(V)/√v = k1·√v + k2      → fit vs √v to get k1, k2 ; integrate the capacitive part over the sweep
```

### Capacitance from the CV loop
```
C = (∮ i dV) / (2 · v · ΔV)          C_specific = C / m
```
∮ i dV = area enclosed by one full loop; `ΔV` = window; `m` = active mass. (Factor 2 = charge+discharge.)

---

## Running several cycles

- **Report which cycle** you show, and why. Use a **stabilised** cycle for quantitative reads; show
  cycle 1 separately if activation/formation matters.
- Overlay cycle 1 → N to show stabilisation; don't average across non-equivalent cycles.

## Running several samples

- **Fix everything:** window, scan-rate set, reference, cycle number, equilibration, temperature.
- **Normalise the current** — per area (mA cm⁻²) or per active mass (A g⁻¹) — before comparing.
- **Fit each sample**, then report the numbers (E_p, ΔE_p, i_p, D, C, b) as **mean ± SD with n**.
- Overlay the CVs as **thin lines** with a **representative** one bold; state n in the caption.
- Account for every cell (how many measured vs included, and why any were excluded).

---

## Presentation

- Overlay scan rates on **one set of axes**; mark the **scan direction**.
- **Normalise** current (mA cm⁻² or A g⁻¹) so samples are comparable.
- Show the **pair**: the CV overlay **and** the analysis plot (i_p vs √v, or the log–log b-value plot).
- Caption must give **scan rate(s), window, reference electrode, cycle number, temperature**, and iR status.

---

## Caveats

- **b-value first.** Randles–Ševčík is for **diffusion-controlled, reversible** couples with known A
  and C. On porous/insertion electrodes it gives only an **apparent** D, and a capacitive contribution
  inflates i_p.
- **Don't** apply Randles–Ševčík to a surface/capacitive system (b ≈ 1).
- **iR drop** distorts peaks and inflates ΔE_p at high v — compensate or report R_u.
- **Area matters:** geometric vs real (BET) area shifts D; state which.
- **First cycle differs** from later ones — never quote formation-cycle numbers as steady state.

---

## References to read (start with 1–2)

1. **N. Elgrishi et al., "A Practical Beginner's Guide to Cyclic Voltammetry," *J. Chem. Educ.* 95,
   197–206 (2018).** The clearest student introduction. https://doi.org/10.1021/acs.jchemed.7b00361
2. **A. J. Bard &amp; L. R. Faulkner, *Electrochemical Methods: Fundamentals and Applications*, Wiley.**
   The reference text — CV theory, Randles–Ševčík, reversibility.
3. **J. Wang, B. Dunn et al., "Pseudocapacitive contributions to electrochemical energy storage in
   TiO₂ (anatase) nanoparticles," *J. Phys. Chem. C* 111, 14925 (2007).** The k1·v + k2·√v separation.
4. **The Randles–Ševčík equation** — overview and the exact constant/derivation:
   https://en.wikipedia.org/wiki/Randles%E2%80%93Sevcik_equation
5. For pseudocapacitance vs battery behaviour: **T. Brousse, D. Bélanger, J. W. Long, "To Be or Not
   To Be Pseudocapacitive?" *J. Electrochem. Soc.* 162, A5185 (2015).**

**Script:** `cv.py` (in the Resources downloads) computes D (Randles–Ševčík), the b-value, the Dunn
split, and capacitance, and plots the CV overlay + i_p-vs-√v fit. Run `python cv.py` for a demo.
