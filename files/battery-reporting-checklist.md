# Battery Reporting Checklist

**What every battery figure and Methods section must disclose — and what to do to make the
numbers trustworthy.** Distilled from the reporting guidelines of *Joule*, *ACS Energy Letters*,
*Advanced Energy Materials*, and the *Nature* journals. Most journals — including *Materials Today
Energy* — expect these same items even when they do not provide a form.

> Rule of thumb: a reader should be able to **rebuild your cell and reproduce your plot** from the
> Methods and SI alone, and **compare your numbers** to anyone else's on equal terms. If they can't,
> something on this list is missing.

---

## A · Report these (in Methods / SI)

### 1. Cell and electrodes
- [ ] **Cell type and configuration** — coin / pouch / Swagelok; **half-cell vs full-cell**; 2- vs 3-electrode.
- [ ] **Counter / reference electrode** identity (e.g. Li metal). *Half-cell CE against Li is not full-cell CE — say which you report.*
- [ ] **Active-material mass** and **mass loading** (mg cm⁻²).
- [ ] **Electrode area** (cm²) and **areal capacity** (mAh cm⁻²).
- [ ] **Electrode formulation** (active : conductive : binder), thickness, and density after calendering.
- [ ] **N/P ratio** (negative-to-positive capacity) for full cells.
- [ ] **Li-metal anodes:** lithium thickness / excess (the lithium inventory).

### 2. Electrolyte and separator
- [ ] **Electrolyte composition** and — crucially — **amount**, as **E/C ratio** (µL mAh⁻¹) or µL cm⁻². *A flooded coin cell hides poor efficiency.*
- [ ] **Separator** type and thickness.

### 3. Test protocol
- [ ] **Voltage window** (cut-offs).
- [ ] **Current:** the **C-rate** *and* the **current density**, with a clear definition of what **1C** means (which capacity it is based on).
- [ ] **Basis** of every specific current / specific capacity: per **active material**, per **total electrode**, or per **cell**.
- [ ] **Temperature** (and whether it was controlled).
- [ ] **Formation protocol**, CC vs CC–CV (and the CV cut-off current), and any rest steps.
- [ ] **Number of cycles** actually run.

### 4. Metrics
- [ ] **Specific capacity** with an explicit basis (per active mass vs per electrode / cell).
- [ ] **Initial (first-cycle) Coulombic efficiency** and **steady-state CE**, to enough significant figures (e.g. 99.92 %, not "~100 %").
- [ ] **Capacity retention:** % over N cycles **and** the absolute capacities.
- [ ] **Energy / power density:** state the level — material, electrode, or **cell**.
- [ ] **Rate capability** across defined C-rates.

---

## B · Do these (rigour)

- [ ] Test at a **practical mass loading** (aim for areal capacity in the mAh cm⁻² range, not µAh); ultra-thin electrodes inflate rate and cycling.
- [ ] Run a **fair baseline / control** under identical conditions in the same study.
- [ ] Report **more than one cell**: give **n**, show **error bars or the spread**, and report the **average** — never just the best cell.
- [ ] Show **raw voltage profiles** (V vs capacity), not only capacity-vs-cycle.
- [ ] Use an appropriate number of **significant figures**; put **error bars** on plots.
- [ ] Build a **full cell** — or state plainly that you did not — before claiming device-level performance.
- [ ] Disclose enough that **someone else could rebuild the cell**.

---

## C · Red flags reviewers catch

- A large **areal capacity implied by a tiny loading**, or huge specific capacity from ~0.5 mg cm⁻².
- **Half-cell** data presented as if it were a full cell.
- **CE** quoted as "~100 %" or to two significant figures.
- **No electrolyte amount** / E/C ratio.
- "**High rate**" from an electrode far thinner than any real device.
- Only **% retention** with no absolute numbers; only the **single best cell** shown.

---

## Journal notes

- **Joule** requires a **Battery Checklist** to be submitted with the manuscript (*Standardized Battery Reporting Guidelines*).
- **ACS Energy Letters** publishes *An Experimental Checklist for Reporting Battery Performances* — the items above track it.
- **Advanced Energy Materials** gives community guidelines for interpreting and reporting energy-storage performance.
- **Nature Energy / Nature** journals scrutinise loading, cell count, and reproducibility (*The path to accurate reporting*).
- **Materials Today Energy** and most other journals expect the same core items even without a bespoke form.

## Sources

- Standardized Battery Reporting Guidelines — *Joule* (2021). https://www.cell.com/joule/fulltext/S2542-4351(20)30625-5
- An Experimental Checklist for Reporting Battery Performances — *ACS Energy Letters* 6, 2187 (2021). https://pubs.acs.org/doi/10.1021/acsenergylett.1c00870
- Energy Storage Data Reporting in Perspective — Guidelines for Interpreting the Performance of Electrochemical Energy Storage Systems — *Advanced Energy Materials* (2019). https://advanced.onlinelibrary.wiley.com/doi/abs/10.1002/aenm.201902007
- Best Practices for Reporting on Energy Storage — *ACS Applied Materials & Interfaces* (2015). https://pubs.acs.org/doi/10.1021/acsami.5b06029
- Aligning academia and industry for unified battery performance metrics — *Nature Communications* (2018). https://www.nature.com/articles/s41467-018-07599-8
- The path to accurate reporting — *Nature Energy* (2024). https://www.nature.com/articles/s41560-024-01663-y
