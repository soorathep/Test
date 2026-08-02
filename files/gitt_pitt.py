"""
gitt_pitt.py — compute the diffusion coefficient from GITT (and PITT) data.
============================================================================
Reads a galvanostatic-intermittent-titration run (time, current, voltage),
finds each pulse+rest step, and returns the chemical (apparent) diffusion
coefficient D vs state of charge using the Weppner–Huggins equation:

        4      ( m_B · V_M )²   ( ΔE_s )²
  D  =  ───  · (───────────)  · (──────)        valid for   τ ≪ L²/D
        π·τ    (  M_B · S  )     ( ΔE_τ )

    τ     pulse duration (s)
    m_B   active-material mass (g)         M_B  molar mass (g/mol)
    V_M   molar volume (cm³/mol)           S    electrode–electrolyte area (cm²)
    ΔE_s  equilibrium (OCV) change of the step  = E4 − E1
    ΔE_τ  transient change during the pulse (IR removed) = E3 − E2

Read the guide (gitt-pitt-guide.md) for the assumptions and caveats. The
absolute D is only a RELATIVE measure — S and L are the big uncertainties.

Quick start
-----------
    python gitt_pitt.py                 # runs a built-in synthetic demo + plot

    # with your own data:
    import numpy as np, gitt_pitt as gp
    t, I, V = np.loadtxt("mydata.csv", delimiter=",", unpack=True)   # s, A, V
    P = gp.PARAMS(m_B=1.5e-3, M_B=96.0, V_M=20.0, S=1.13)            # EDIT THESE
    soc, D, steps = gp.analyse_gitt(t, I, V, P)
    gp.plot_gitt(t, I, V, soc, D, save="gitt.png")
"""
from dataclasses import dataclass
import numpy as np

PI = np.pi
_trapz = getattr(np, "trapezoid", np.trapz)   # numpy 2.x renamed trapz -> trapezoid


@dataclass
class PARAMS:
    """Everything the Weppner–Huggins equation needs. EDIT for your electrode."""
    m_B: float   # active-material mass, g
    M_B: float   # molar mass, g/mol
    V_M: float   # molar volume, cm^3/mol  (= M_B / density)
    S:   float   # electrode–electrolyte contact area, cm^2 (geometric or BET — say which)


def D_weppner_huggins(tau, dEs, dEt, P):
    """Chemical diffusion coefficient (cm^2/s) for one GITT step.

    tau : pulse duration [s];  dEs, dEt : ΔE_s, ΔE_τ [V] (use magnitudes).
    """
    pref = 4.0 / (PI * tau)
    geom = (P.m_B * P.V_M) / (P.M_B * P.S)          # cm  (units: g·cm^3/mol / (g/mol·cm^2) = cm)
    return pref * geom**2 * (abs(dEs) / abs(dEt))**2   # cm^2/s


def _segments(I, thresh=None):
    """Split a run into alternating (pulse, rest) index ranges by |current|."""
    I = np.asarray(I, float)
    if thresh is None:
        thresh = 0.05 * np.max(np.abs(I))            # 5% of peak current
    on = np.abs(I) > thresh
    edges = np.flatnonzero(np.diff(on.astype(int)) != 0) + 1
    bounds = np.concatenate(([0], edges, [len(I)]))
    segs = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        segs.append(("pulse" if on[a] else "rest", a, b))
    return segs


def analyse_gitt(t, I, V, P):
    """Return (soc_fraction, D_array, steps). One D per current pulse.

    Per step: E1 = end of the previous rest, E2 = first pulse point (with IR),
    E3 = last pulse point, E4 = end of the following rest.
    """
    t, I, V = map(lambda x: np.asarray(x, float), (t, I, V))
    segs = _segments(I)
    steps, Ds, cap = [], [], 0.0
    total_cap = _trapz(np.abs(I), t) / 3600.0      # A·h, for SOC scaling
    for k, (kind, a, b) in enumerate(segs):
        if kind != "pulse":
            continue
        tau = t[b - 1] - t[a]
        E2, E3 = V[a], V[b - 1]
        E1 = V[a - 1] if a > 0 else V[a]             # end of previous rest
        # E4 = end of the following rest (next segment if it is a rest)
        if k + 1 < len(segs) and segs[k + 1][0] == "rest":
            E4 = V[segs[k + 1][2] - 1]
        else:
            E4 = E3
        dEs, dEt = E4 - E1, E3 - E2
        step_cap = _trapz(np.abs(I[a:b]), t[a:b]) / 3600.0
        cap += step_cap
        if abs(dEt) > 1e-6 and tau > 0:
            Ds.append(D_weppner_huggins(tau, dEs, dEt, P))
            steps.append(dict(tau=tau, E1=E1, E2=E2, E3=E3, E4=E4,
                              dEs=dEs, dEt=dEt, soc=cap / total_cap))
    soc = np.array([s["soc"] for s in steps])
    return soc, np.array(Ds), steps


def D_pitt_longtime(t, I, L):
    """PITT: D from the long-time slope of ln|I| vs t.  ln I = c − (π²D/4L²) t.

    Fit the linear tail (last ~40% of the transient). L = diffusion length [cm].
    """
    t, I = np.asarray(t, float), np.abs(np.asarray(I, float))
    m = t > (t[0] + 0.6 * (t[-1] - t[0]))
    slope = np.polyfit(t[m], np.log(I[m]), 1)[0]     # 1/s
    return -slope * 4.0 * L**2 / PI**2               # cm^2/s


# ─────────────────────────── synthetic demo ───────────────────────────
def _synthetic_gitt(P, D_true=1e-10, n_steps=12, tau=600.0, rest=3600.0,
                    I0=1e-4, dt=5.0):
    """Fabricate a plausible GITT run so the script is runnable out of the box."""
    L = (P.m_B * P.V_M) / (P.M_B * P.S)              # characteristic length (cm)
    R_ir = 15.0                                      # ohmic-ish IR (V/A)
    ocv0, ocv1 = 3.4, 4.1
    t_all, I_all, V_all, ocv = [], [], [], ocv0
    clock = 0.0
    rng = np.random.default_rng(0)
    for k in range(n_steps):
        # OCV rises a little each step (charging)
        d_ocv = (ocv1 - ocv0) / n_steps
        # pulse
        n = int(tau / dt)
        tp = np.arange(n) * dt
        # WH transient: E ~ ocv + IR + slope*sqrt(t)
        slope = d_ocv / np.sqrt(tau)                 # gives ΔE_τ≈d_ocv over the pulse
        Vp = ocv + I0 * R_ir + slope * np.sqrt(tp)
        for i in range(n):
            t_all.append(clock + tp[i]); I_all.append(I0); V_all.append(Vp[i])
        clock += tau
        ocv += d_ocv
        # rest: exponential relaxation to new OCV
        m = int(rest / dt)
        tr = np.arange(m) * dt
        Vr = ocv + (Vp[-1] - I0 * R_ir - ocv) * np.exp(-tr / (0.15 * rest))
        for i in range(m):
            t_all.append(clock + tr[i]); I_all.append(0.0); V_all.append(Vr[i])
        clock += rest
    t = np.array(t_all); I = np.array(I_all)
    V = np.array(V_all) + rng.normal(0, 3e-4, len(t_all))   # a little noise
    return t, I, V


def plot_gitt(t, I, V, soc, D, save="gitt_example.png"):
    import matplotlib.pyplot as plt
    try:
        import labpalette as lp; lp.apply(); teal, amber = lp.C["teal"], lp.C["amber"]
    except Exception:
        teal, amber = "#0F6E6B", "#E29A2D"
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    ax[0].plot(t / 3600.0, V, color=teal, lw=1.2)
    ax[0].set_xlabel("time (h)"); ax[0].set_ylabel("voltage (V)")
    ax[0].set_title("GITT — pulses & rests")
    ax[1].semilogy(soc * 100, D, "o-", color=amber, ms=5, lw=1.2)
    ax[1].set_xlabel("state of charge (%)"); ax[1].set_ylabel("D (cm² s⁻¹)")
    ax[1].set_title("Apparent diffusion coefficient")
    fig.tight_layout(); fig.savefig(save, dpi=150)
    return save


def main():
    # NOTE: demo values — replace PARAMS with your real electrode numbers.
    P = PARAMS(m_B=1.5e-3, M_B=96.0, V_M=20.0, S=1.13)
    t, I, V = _synthetic_gitt(P)
    soc, D, steps = analyse_gitt(t, I, V, P)
    s0 = steps[len(steps) // 2]
    print("Worked step (mid-SOC):")
    print(f"  tau={s0['tau']:.0f}s  E1={s0['E1']:.4f}  E2={s0['E2']:.4f}  "
          f"E3={s0['E3']:.4f}  E4={s0['E4']:.4f} V")
    print(f"  ΔE_s={s0['dEs']*1e3:.2f} mV   ΔE_τ={s0['dEt']*1e3:.2f} mV")
    print(f"  ->  D = {D[len(D)//2]:.2e} cm^2/s")
    print(f"\nD across {len(D)} steps: {D.min():.1e} … {D.max():.1e} cm^2/s")
    out = plot_gitt(t, I, V, soc, D)
    print("wrote", out)


if __name__ == "__main__":
    main()
