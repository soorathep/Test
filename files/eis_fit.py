"""
eis_fit.py — fit an equivalent-circuit model (ECM) to an EIS spectrum.
======================================================================
Self-contained (numpy + scipy + matplotlib) complex non-linear least-squares
fit with the circuits people actually use, returning best-fit values WITH
uncertainties and a goodness-of-fit, plus a data-vs-fit + residual plot.

Circuits (elements: R, CPE, Warburg):
    "R_CPE"          Rs + (R1 ∥ CPE1)                         — one arc, no diffusion
    "randles"        Rs + (R1 ∥ CPE1) + W                     — one arc + Warburg tail
    "two_RC"         Rs + (R1 ∥ CPE1) + (R2 ∥ CPE2)           — film/SEI + charge transfer
    "two_RC_W"       Rs + (R1 ∥ CPE1) + (R2 ∥ CPE2) + W       — the above + diffusion

CPE:  Z = 1 / (Q·(jω)^a)   (a=1 → ideal capacitor C=Q; a<1 → depressed arc).
Warburg (semi-infinite):  Z = Aw·(1−j)/√ω.

Choosing the model — read this before fitting
----------------------------------------------
1. Validate the data first (Lin-KK). A bad spectrum cannot be rescued by a circuit.
2. Let the physics set the number of elements: run a DRT (pyDRTtools) — the number of
   peaks is the number of R∥CPE arcs you need. Don't add elements the data can't resolve.
3. Use a CPE (not an ideal C) for any depressed/flattened arc.
4. Add a Warburg only if there is a low-frequency ~45° tail.
5. Keep it as simple as the data justify (Occam). More elements always lower χ², but
   watch for: huge parameter uncertainties, parameters that wander with the initial guess,
   or physically silly values — all signs of over-fitting / a non-unique circuit.
6. Judge the fit by the RESIDUALS (should be small and unstructured vs frequency), not by χ² alone.
7. Report the circuit drawn out, every value ± its uncertainty, and χ². A good fit to the wrong
   circuit is still the wrong circuit — tie each element to a physical process.

For the fuller toolbox (built-in circuits, string syntax) see impedance.py:
    pip install impedance   #   from impedance.models.circuits import CustomCircuit

Quick start
-----------
    python eis_fit.py                     # synthetic demo: fit + eis-fit-example.png

    import numpy as np, eis_fit
    f, Zr, Zi = np.loadtxt("eis.csv", delimiter=",", unpack=True)
    r = eis_fit.fit_eis(f, Zr + 1j*Zi, model="two_RC_W")
    print(r["params"], r["perr"], r["chi2"])
"""
import numpy as np
from scipy.optimize import least_squares

# ── elements ──
def _cpe(f, Q, a):
    return 1.0 / (Q * (1j * 2 * np.pi * f) ** a)

def _par(Z1, Z2):
    return 1.0 / (1.0 / Z1 + 1.0 / Z2)

def _warburg(f, Aw):
    w = 2 * np.pi * f
    return Aw * (1 - 1j) / np.sqrt(w)


# ── models: name -> (parameter names, Z(params, f)) ──
def _randles(p, f):
    Rs, R1, Q1, a1, Aw = p
    return Rs + _par(R1, _cpe(f, Q1, a1)) + _warburg(f, Aw)

def _r_cpe(p, f):
    Rs, R1, Q1, a1 = p
    return Rs + _par(R1, _cpe(f, Q1, a1))

def _two_rc(p, f):
    Rs, R1, Q1, a1, R2, Q2, a2 = p
    return Rs + _par(R1, _cpe(f, Q1, a1)) + _par(R2, _cpe(f, Q2, a2))

def _two_rc_w(p, f):
    Rs, R1, Q1, a1, R2, Q2, a2, Aw = p
    return Rs + _par(R1, _cpe(f, Q1, a1)) + _par(R2, _cpe(f, Q2, a2)) + _warburg(f, Aw)

MODELS = {
    "R_CPE":    (["Rs", "R1", "Q1", "a1"], _r_cpe),
    "randles":  (["Rs", "R1", "Q1", "a1", "Aw"], _randles),
    "two_RC":   (["Rs", "R1", "Q1", "a1", "R2", "Q2", "a2"], _two_rc),
    "two_RC_W": (["Rs", "R1", "Q1", "a1", "R2", "Q2", "a2", "Aw"], _two_rc_w),
}


def _guess(model, f, Z):
    Rs = float(np.min(Z.real))
    span = float(np.max(Z.real) - Rs)
    g = {"Rs": max(Rs, 1e-3), "R1": span * 0.4, "R2": span * 0.6,
         "Q1": 1e-4, "Q2": 1e-2, "a1": 0.85, "a2": 0.85, "Aw": 10.0}
    return [g[n] for n in MODELS[model][0]]


def fit_eis(f, Z, model="two_RC_W", p0=None):
    """Fit `model` to (f, Z). Proportional weighting (residual/|Z|).

    Returns dict: names, params, perr (1σ), chi2 (reduced), Zfit, model.
    """
    f = np.asarray(f, float); Z = np.asarray(Z, complex)
    names, func = MODELS[model]
    if p0 is None:
        p0 = _guess(model, f, Z)
    w = np.abs(Z)

    def resid(p):
        Zm = func(p, f)
        return np.concatenate([(Zm.real - Z.real) / w, (Zm.imag - Z.imag) / w])

    lb = [1e-6] * len(p0)
    ub = [np.inf] * len(p0)
    for i, n in enumerate(names):          # CPE exponents bounded 0..1
        if n.startswith("a"):
            ub[i] = 1.0
    sol = least_squares(resid, p0, bounds=(lb, ub), method="trf", max_nfev=20000)

    # uncertainties from the Jacobian: cov = (JᵀJ)⁻¹ · s²
    dof = max(len(sol.fun) - len(p0), 1)
    s2 = 2 * sol.cost / dof
    try:
        cov = np.linalg.inv(sol.jac.T @ sol.jac) * s2
        perr = np.sqrt(np.abs(np.diag(cov)))
    except np.linalg.LinAlgError:
        perr = np.full(len(p0), np.nan)
    chi2 = 2 * sol.cost / dof
    return dict(names=names, params=sol.x, perr=perr, chi2=chi2,
                Zfit=func(sol.x, f), model=model)


def plot_fit(f, Z, res, save="eis-fit-example.png"):
    import matplotlib.pyplot as plt
    try:
        import labpalette as lp; lp.apply(); teal, amber, rust = lp.cat(3)
    except Exception:
        teal, amber, rust = "#0F6E6B", "#E29A2D", "#BE654C"
    Zf = res["Zfit"]
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ax[0].plot(Z.real, -Z.imag, "o", color=teal, ms=3, label="data")
    ax[0].plot(Zf.real, -Zf.imag, "-", color=amber, lw=1.4, label="fit")
    ax[0].set_aspect("equal", adjustable="datalim")
    ax[0].set_xlabel("Z′ (Ω)"); ax[0].set_ylabel("−Z″ (Ω)")
    ax[0].set_title(f"{res['model']} fit  ·  χ²={res['chi2']:.1e}"); ax[0].legend(fontsize=7)
    rr = (Zf.real - Z.real) / np.abs(Z) * 100
    ri = (Zf.imag - Z.imag) / np.abs(Z) * 100
    ax[1].semilogx(f, rr, "o-", color=teal, ms=3, lw=1, label="Re")
    ax[1].semilogx(f, ri, "o-", color=rust, ms=3, lw=1, label="Im")
    ax[1].axhline(0, color="#999", lw=0.6)
    ax[1].set_xlabel("f (Hz)"); ax[1].set_ylabel("relative residual (%)")
    ax[1].set_title("Residuals (want small & unstructured)"); ax[1].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(save, dpi=150)
    return save


def main():
    try:
        import eis
        f, Z, _ = eis.synthetic_eis(noise=0.15)
    except Exception:                      # standalone fallback
        f = np.logspace(5, -2, 70)
        Z = _two_rc_w([8, 25, 1e-4, 0.88, 60, 5e-2, 0.80, 12], f)
    res = fit_eis(f, Z, model="two_RC_W")
    print(f"model: {res['model']}   χ² = {res['chi2']:.2e}")
    for n, v, e in zip(res["names"], res["params"], res["perr"]):
        print(f"  {n:>3} = {v:.4g} ± {e:.2g}")
    print("wrote", plot_fit(f, Z, res))


if __name__ == "__main__":
    main()
