"""
eis.py — plot and read electrochemical impedance spectra (EIS), the right way.
=============================================================================
Helpers to load an EIS spectrum (frequency, Z', Z''), draw a correct Nyquist
(EQUAL axes) and Bode plot, and read off R_s and an R_ct estimate. It also
builds a synthetic spectrum so the script is runnable out of the box, and
shows an illustrative DRT.

For the DRT itself use the validated community tools — do NOT hand-roll the
regularised inversion:
    pip install pyDRTtools          # https://github.com/ciuccislab/pyDRTtools
    # in Python:
    #   from pyDRTtools.runs import simple_run
    #   simple_run(freq, Z_real, Z_imag, rbf_type="Gaussian", lambda_value=1e-3)
Choose the regularisation λ with the L-curve / GCV and REPORT it. Validate the
data with a Lin-KK test first. See eis-drt-guide.md.

Quick start
-----------
    python eis.py                       # synthetic demo -> eis_drt_example.png

    import numpy as np, eis
    f, Zr, Zi = np.loadtxt("eis.csv", delimiter=",", unpack=True)   # Hz, ohm, ohm
    Z = Zr + 1j*Zi
    print(eis.read_Rs_Rct(f, Z))
    eis.plot_nyquist_bode(f, Z, save="eis.png")
"""
import numpy as np

PI = np.pi


def zarc(f, R, tau, phi=0.85):
    """A depressed RC arc (ZARC / R–CPE):  Z = R / (1 + (jωτ)^phi)."""
    w = 2 * PI * f
    return R / (1 + (1j * w * tau) ** phi)


def warburg(f, Aw):
    """Semi-infinite Warburg (the low-frequency 45° tail):  Z = Aw (1−j)/√ω."""
    w = 2 * PI * f
    return Aw * (1 - 1j) / np.sqrt(w)


def synthetic_eis(f=None, Rs=8.0, arcs=((25.0, 2e-3, 0.88), (60.0, 5e-2, 0.80)),
                  Aw=12.0, noise=0.0):
    """Fabricate a spectrum: series R + two ZARC arcs + a Warburg tail.

    arcs = list of (R, tau, phi). Returns (f, Z). Also the ground-truth (R, tau)
    of each arc, so the illustrative DRT below matches the data exactly.
    """
    if f is None:
        f = np.logspace(5, -2, 70)              # 100 kHz -> 10 mHz
    Z = np.full(f.shape, Rs, dtype=complex)
    for (R, tau, phi) in arcs:
        Z = Z + zarc(f, R, tau, phi)
    Z = Z + warburg(f, Aw)
    if noise:
        rng = np.random.default_rng(0)
        Z = Z + noise * (rng.normal(size=f.size) + 1j * rng.normal(size=f.size))
    return f, Z, arcs


def read_Rs_Rct(f, Z):
    """Rough reads: R_s = real part at the highest frequency where −Z''≈0;
    R_ct ≈ (real-axis span of the capacitive arcs) before the diffusion tail."""
    order = np.argsort(f)[::-1]
    Zr, Zi = Z.real[order], Z.imag[order]
    Rs = Zr[np.argmin(np.abs(Zi[:max(3, len(f)//10)]))]   # near high-f intercept
    # crude R_ct: max real part in the mid band minus Rs (excludes the low-f tail)
    mid = (f > np.percentile(f, 10)) & (f < np.percentile(f, 95))
    Rct = float(np.max(Z.real[mid]) - Rs)
    return dict(Rs=float(Rs), Rct_estimate=Rct)


def illustrative_drt(ax, arcs, Rs=0.0):
    """Draw a DRT-style γ(τ) with one peak per arc (area ∝ R). Illustrative:
    the real thing comes from pyDRTtools on measured data."""
    tau = np.logspace(-4, 0.5, 800)
    gamma = np.zeros_like(tau)
    for (R, t0, phi) in arcs:
        width = 0.20 / phi                       # broader for lower phi
        gamma += R * np.exp(-0.5 * (np.log10(tau) - np.log10(t0))**2 / width**2)
    try:
        import labpalette as lp; teal = lp.C["teal"]
    except Exception:
        teal = "#0F6E6B"
    ax.plot(tau, gamma, color=teal, lw=1.4)
    ax.fill_between(tau, gamma, color=teal, alpha=0.12)
    ax.set_xscale("log"); ax.set_xlabel("τ (s)"); ax.set_ylabel("γ(τ)  (Ω)")
    ax.set_title("DRT — one peak per process")
    for (R, t0, phi) in arcs:
        ax.annotate(f"τ≈{t0:g}s\nR≈{R:g}Ω", (t0, R), ha="center", va="bottom",
                    fontsize=7)


def plot_nyquist_bode(f, Z, arcs=None, save="eis_drt_example.png"):
    import matplotlib.pyplot as plt
    try:
        import labpalette as lp; lp.apply(); teal, amber = lp.C["teal"], lp.C["amber"]
    except Exception:
        teal, amber = "#0F6E6B", "#E29A2D"
    ncol = 3 if arcs is not None else 2
    fig, ax = plt.subplots(1, ncol, figsize=(3.2 * ncol, 3.2))

    # Nyquist — EQUAL axes (this is the whole point)
    ax[0].plot(Z.real, -Z.imag, "o-", color=teal, ms=3, lw=1)
    ax[0].set_aspect("equal", adjustable="datalim")
    ax[0].set_xlabel("Z′ (Ω)"); ax[0].set_ylabel("−Z″ (Ω)")
    ax[0].set_title("Nyquist (equal axes)")

    # Bode — |Z| and phase
    b = ax[1]; b.loglog(f, np.abs(Z), color=teal, lw=1.2); b.set_xlabel("f (Hz)")
    b.set_ylabel("|Z| (Ω)", color=teal); b.tick_params(axis="y", colors=teal)
    b2 = b.twinx(); b2.semilogx(f, -np.degrees(np.angle(Z)), color=amber, lw=1.2)
    b2.set_ylabel("−phase (°)", color=amber); b2.tick_params(axis="y", colors=amber)
    b.set_title("Bode")

    if arcs is not None:
        illustrative_drt(ax[2], arcs)
    fig.tight_layout(); fig.savefig(save, dpi=150)
    return save


def main():
    f, Z, arcs = synthetic_eis()
    print("reads:", read_Rs_Rct(f, Z))
    out = plot_nyquist_bode(f, Z, arcs=arcs)
    print("wrote", out)


if __name__ == "__main__":
    main()
