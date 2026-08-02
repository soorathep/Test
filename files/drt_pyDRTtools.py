"""
drt_pyDRTtools.py — a real DRT from EIS data with pyDRTtools (L-curve λ).
========================================================================
A worked pipeline: load an EIS spectrum → compute the distribution of relaxation
times with pyDRTtools, choosing the regularisation λ by the L-curve → find the
peaks (τ and the process resistance) → plot γ(τ). This is the *real* DRT, not the
illustrative one in eis.py.

Install
-------
    pip install pyDRTtools cvxopt scikit-learn
    # pyDRTtools ships a GUI (launchGUI). We only use the compute core here, so the
    # few lines below stub the GUI modules — that lets the script run headless
    # (servers, notebooks, CI) without PyQt5. Delete them if you have PyQt5 and
    # prefer the GUI.

Choosing λ
----------
The inversion is ill-posed, so λ trades resolution vs noise. pyDRTtools picks it
objectively — here with the **L-curve** (cv_type="LC"); "GCV" and "mGCV" are also
available. ALWAYS report λ and the method. Feed it Kramers–Kronig-valid data.

Quick start
-----------
    python drt_pyDRTtools.py                 # synthetic demo -> drt-real-example.png
    python drt_pyDRTtools.py myspectrum.csv  # columns: freq[Hz], Z_re[Ω], Z_im[Ω]
"""
import sys, types, io, contextlib
import numpy as np

# --- make pyDRTtools importable headless (skip its PyQt5 GUI) ---
for _m in ("pyDRTtools.GUI", "pyDRTtools.cli", "pyDRTtools.layout"):
    sys.modules.setdefault(_m, types.ModuleType(_m))


def compute_drt(freq, Z_re, Z_im, cv_type="LC"):
    """Run pyDRTtools and return (tau, gamma, lambda_value)."""
    from pyDRTtools import runs
    entry = runs.EIS_object(np.asarray(freq, float),
                            np.asarray(Z_re, float), np.asarray(Z_im, float))
    with contextlib.redirect_stdout(io.StringIO()):        # hush the solver's chatter
        entry = runs.simple_run(entry, rbf_type="Gaussian",
                                data_used="Combined Re-Im Data", induct_used=1,
                                der_used="1st order", cv_type=cv_type)
    return entry.out_tau_vec, entry.gamma, float(np.ravel(entry.lambda_value)[0])


def find_drt_peaks(tau, gamma):
    """Peaks of γ(τ): returns list of (tau_peak, f_peak, R_area). R = ∫γ dln τ over the peak."""
    try:
        from scipy.signal import find_peaks, peak_prominences
    except Exception:
        return []
    lnt = np.log(tau)
    idx, _ = find_peaks(gamma, prominence=0.02 * gamma.max())
    if len(idx) == 0:
        return []
    # split at the minima between consecutive peaks to integrate each peak's area (=R)
    edges = [0]
    for a, b in zip(idx[:-1], idx[1:]):
        edges.append(a + int(np.argmin(gamma[a:b])))
    edges.append(len(tau) - 1)
    out = []
    for k, p in enumerate(idx):
        lo, hi = edges[k], edges[k + 1]
        R = np.trapezoid(gamma[lo:hi + 1], lnt[lo:hi + 1]) if hasattr(np, "trapezoid") \
            else np.trapz(gamma[lo:hi + 1], lnt[lo:hi + 1])
        out.append((tau[p], 1.0 / (2 * np.pi * tau[p]), abs(R)))
    return out


def plot_drt(tau, gamma, lam, peaks, save="drt-real-example.png"):
    import matplotlib.pyplot as plt
    try:
        import labpalette as lp; lp.apply(); teal, amber = lp.C["teal"], lp.C["amber"]
    except Exception:
        teal, amber = "#0F6E6B", "#E29A2D"
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    ax.plot(tau, gamma, color=teal, lw=1.5)
    ax.fill_between(tau, gamma, color=teal, alpha=0.12)
    ax.set_xscale("log"); ax.set_xlabel("τ (s)"); ax.set_ylabel("γ(τ)  (Ω)")
    ax.set_ylim(0, gamma.max() * 1.5)
    ax.set_title(f"DRT (pyDRTtools, L-curve λ = {lam:.1e})", pad=10)
    for (tp, fp, R) in peaks:
        gp = gamma[np.argmin(np.abs(tau - tp))]
        ax.annotate(f"τ ≈ {tp:.1e} s\nf ≈ {fp:.0f} Hz\nR ≈ {R:.0f} Ω",
                    (tp, gp), textcoords="offset points", xytext=(0, 6),
                    ha="center", va="bottom", fontsize=7, color=amber)
    fig.tight_layout(); fig.savefig(save, dpi=150)
    return save


def main():
    if len(sys.argv) > 1:                       # load a real spectrum
        data = np.loadtxt(sys.argv[1], delimiter="," if sys.argv[1].endswith(".csv") else None)
        f, Zr, Zi = data[:, 0], data[:, 1], data[:, 2]
    else:                                       # synthetic demo (two clean RC arcs)
        import eis
        f, Z, _ = eis.synthetic_eis(Aw=0.0, noise=0.03); Zr, Zi = Z.real, Z.imag

    tau, gamma, lam = compute_drt(f, Zr, Zi, cv_type="LC")
    peaks = find_drt_peaks(tau, gamma)
    print(f"L-curve λ = {lam:.2e}")
    for (tp, fp, R) in peaks:
        print(f"  peak: τ = {tp:.2e} s  (f = {fp:.0f} Hz)   R ≈ {R:.1f} Ω")
    print("wrote", plot_drt(tau, gamma, lam, peaks))


if __name__ == "__main__":
    main()
