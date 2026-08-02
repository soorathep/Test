"""
cv.py — cyclic-voltammetry calculations: D, b-value, capacitive/diffusive split, C.
====================================================================================
Helpers for the standard CV analyses, plus a runnable synthetic demo and figure.

  Randles–Ševčík (reversible, 25 °C):
        i_p = 2.69e5 · n^(3/2) · A · D^(1/2) · C · v^(1/2)
     → plot i_p vs √v (should be a straight line through ~0); D from the slope.

  b-value (what controls the current):
        i_p = a · v^b   → plot log(i_p) vs log(v); b ≈ 0.5 diffusion, b ≈ 1.0 surface/capacitive.

  Dunn separation at a fixed potential:
        i(V) = k1·v + k2·√v   (k1·v = capacitive, k2·√v = diffusion)
     → i/√v = k1·√v + k2 ; fit across scan rates to split the current.

  Capacitance from a CV loop:
        C = (∮ i dV) / (2 · v · ΔV)      C_specific = C / m

Units: A in cm², D in cm²/s, C in mol/cm³ (1 mM = 1e-6 mol/cm³), v in V/s, i in A.
See cv-guide.md for parameters, multi-cycle / multi-sample reporting, and caveats.

Quick start
-----------
    python cv.py                          # synthetic demo + cv_example.png

    import numpy as np, cv
    v  = np.array([0.01,0.02,0.05,0.1])          # V/s
    ip = np.array([...])                          # A, anodic peak per scan rate
    print(cv.randles_sevcik_D(v, ip, n=1, A=1.0, C=1e-6))
    print(cv.b_value(v, ip))
"""
import numpy as np

RS = 2.69e5   # Randles–Ševčík constant at 25 °C


def randles_sevcik_D(v, ip, n, A, C):
    """Diffusion coefficient (cm^2/s) from the slope of i_p vs √v (reversible)."""
    v, ip = np.asarray(v, float), np.abs(np.asarray(ip, float))
    slope = np.polyfit(np.sqrt(v), ip, 1)[0]           # A / (V/s)^0.5
    D = (slope / (RS * n**1.5 * A * C))**2
    return dict(D=D, slope=slope)


def b_value(v, ip):
    """Power-law exponent b in i_p = a·v^b (0.5 diffusion, 1.0 surface)."""
    v, ip = np.asarray(v, float), np.abs(np.asarray(ip, float))
    b, loga = np.polyfit(np.log10(v), np.log10(ip), 1)
    return dict(b=b, a=10**loga)


def dunn_separation(v, i_at_potential):
    """Split current at one potential into capacitive (k1·v) and diffusive (k2·√v).

    v : scan rates (V/s); i_at_potential : current at the SAME potential for each rate.
    Returns k1, k2 and the capacitive fraction at the highest rate.
    """
    v, i = np.asarray(v, float), np.asarray(i_at_potential, float)
    # i/√v = k1·√v + k2   → linear in √v
    k1, k2 = np.polyfit(np.sqrt(v), i / np.sqrt(v), 1)
    vmax = v.max()
    cap = k1 * vmax
    frac = cap / (cap + k2 * np.sqrt(vmax))
    return dict(k1=k1, k2=k2, capacitive_fraction_at_vmax=frac)


def capacitance_from_cv(E, i, v, m=None):
    """Capacitance (F, and F/g if m given) from one closed CV loop.

    C = (∮ i dE) / (2 · v · ΔV).  E in V, i in A, v in V/s, m in g.
    """
    E, i = np.asarray(E, float), np.asarray(i, float)
    area = np.abs(np.trapezoid(i, E)) if hasattr(np, "trapezoid") else np.abs(np.trapz(i, E))
    dV = E.max() - E.min()
    C = area / (2.0 * v * dV)
    return dict(C=C, C_specific=(C / m if m else None))


# ─────────────────────────── synthetic demo ───────────────────────────
def _synthetic_cv(v, D_true=1e-6, n=1, A=1.0, C=1e-6, Epa=0.25, Epc=0.15, npts=400):
    """A reversible-looking CV whose peak current obeys Randles–Ševčík for D_true."""
    ip = RS * n**1.5 * A * np.sqrt(D_true) * C * np.sqrt(v)      # target peak height
    E = np.linspace(-0.1, 0.5, npts)
    w = 0.045
    ip_cap = 2e-5 * v                                            # small capacitive box
    ia = ip * np.exp(-0.5 * ((E - Epa) / w)**2) + ip_cap         # anodic (forward)
    ic = -ip * np.exp(-0.5 * ((E - Epc) / w)**2) - ip_cap        # cathodic (reverse)
    return E, ia, ic, ip


def plot_cv(save="cv_example.png"):
    import matplotlib.pyplot as plt
    try:
        import labpalette as lp; lp.apply(); cyc = lp.cat(5); amber = lp.C["amber"]; teal = lp.C["teal"]
    except Exception:
        cyc = ["#0F6E6B", "#E29A2D", "#BE654C", "#5A91BE", "#83A462"]; amber = "#E29A2D"; teal = "#0F6E6B"
    rates = np.array([0.01, 0.02, 0.05, 0.1, 0.2])              # V/s
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ip_list = []
    for k, vr in enumerate(rates):
        E, ia, ic, ip = _synthetic_cv(vr)
        col = cyc[k % len(cyc)]
        ax[0].plot(E, ia * 1e6, color=col, lw=1.1)
        ax[0].plot(E, ic * 1e6, color=col, lw=1.1, label=f"{vr*1000:.0f} mV/s")
        ip_list.append(ip)
    ax[0].set_xlabel("E (V vs ref)"); ax[0].set_ylabel("i (µA)")
    ax[0].set_title("CV at several scan rates"); ax[0].legend(fontsize=6, ncol=2)
    ipa = np.array(ip_list)
    res = randles_sevcik_D(rates, ipa, n=1, A=1.0, C=1e-6)
    ax[1].plot(np.sqrt(rates), ipa * 1e6, "o", color=amber, ms=6)
    xf = np.linspace(0, np.sqrt(rates.max()) * 1.05, 50)
    ax[1].plot(xf, res["slope"] * xf * 1e6, color=teal, lw=1.2)
    ax[1].set_xlabel("√v  (V/s)^0.5"); ax[1].set_ylabel("i_p (µA)")
    ax[1].set_title(f"Randles–Ševčík → D ≈ {res['D']:.1e} cm²/s")
    fig.tight_layout(); fig.savefig(save, dpi=150)
    return save, res


def main():
    out, res = plot_cv()
    rates = np.array([0.01, 0.02, 0.05, 0.1, 0.2])
    ipa = np.array([_synthetic_cv(vr)[3] for vr in rates])
    print("Randles–Sevcik:", {k: (f"{x:.2e}" if k == 'D' else f"{x:.3e}") for k, x in res.items()})
    print("b-value:", {k: round(v, 3) for k, v in b_value(rates, ipa).items()})
    print("wrote", out)


if __name__ == "__main__":
    main()
