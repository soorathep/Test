"""
gcd.py — galvanostatic charge–discharge: capacity, CE, energy, retention (+ supercap C, ESR).
=============================================================================================
Constant-current cycling is the workhorse test. From it you get, per cycle:

  Specific capacity     q = I·Δt / (3.6·m)              [mAh/g]   (I in A, Δt in s, m in g)
  Coulombic efficiency  CE = Δt_dis / Δt_ch = Q_dis/Q_ch          (at constant current)
  Specific energy       E = I·∫V dt / (3.6·m)           [mWh/g] ; average V = E/q
  Capacity retention    Q_N / Q_1 × 100 %

For supercapacitors (triangular profile):
  Capacitance (from discharge slope)   C = I / |dV/dt|            → C_spec = C/m [F/g]
  ESR (from the IR drop at reversal)   ESR = ΔV_IR / (2·I)        [Ω]
  Energy  E = ½ C ΔV²        Power  P = E / Δt_dis

Report at a PRACTICAL mass loading, give n cells, and never quote a formation cycle as steady
state. See gcd-guide.md.

Quick start
-----------
    python gcd.py                        # synthetic demo + gcd_example.png

    import numpy as np, gcd
    q = gcd.specific_capacity(I=1e-3, dt=3600, m=1.5e-3)      # mAh/g
    print(gcd.supercap_from_discharge(t, V, I=1e-3, m=1.5e-3))
"""
import numpy as np

_trapz = getattr(np, "trapezoid", np.trapz)


def specific_capacity(I, dt, m):
    """mAh/g from current I [A], duration dt [s], active mass m [g]."""
    return I * dt / (3.6 * m)


def coulombic_efficiency(dt_charge, dt_discharge):
    """CE (%) at constant current = discharge time / charge time."""
    return 100.0 * dt_discharge / dt_charge


def specific_energy(t, V, I, m):
    """mWh/g for one half-cycle:  E = I·∫V dt /(3.6 m).  t [s], V [V]."""
    return abs(I) * abs(_trapz(V, t)) / (3.6 * m)


def supercap_from_discharge(t, V, I, m, ir_jump=None):
    """Supercapacitor capacitance (F, F/g) from the discharge slope, and ESR.

    Fits dV/dt on the linear part of the discharge (10–90 %), excluding the IR drop.
    ir_jump : the voltage step at current reversal (V); if given, ESR = ir_jump/(2I).
    """
    t, V = np.asarray(t, float), np.asarray(V, float)
    a, b = int(0.1 * len(t)), int(0.9 * len(t))
    slope = np.polyfit(t[a:b], V[a:b], 1)[0]            # V/s (negative)
    C = abs(I) / abs(slope)
    out = dict(C=C, C_specific=C / m, dVdt=slope)
    if ir_jump is not None:
        out["ESR"] = abs(ir_jump) / (2 * abs(I))
    return out


# ─────────────────────────── synthetic demo ───────────────────────────
def _profile(Q=150.0, Vmin=2.8, Vmax=4.2, ir=0.03, N=300):
    """A battery-like discharge profile V vs q (sloping plateau + IR drop)."""
    q = np.linspace(0, Q, N)
    frac = q / Q
    Vdis = Vmin + (Vmax - Vmin) * (1 - frac) + 0.15 * np.tanh((0.5 - frac) * 6) - ir
    Vcha = Vmin + (Vmax - Vmin) * frac + 0.15 * np.tanh((frac - 0.5) * 6) + ir
    return q, Vcha, Vdis


def _cycling(n=60, Q0=150.0):
    rng = np.random.default_rng(0)
    cyc = np.arange(1, n + 1)
    Qd = Q0 * (1 - 0.0025 * cyc) + rng.normal(0, 0.4, n)      # gentle fade
    CE = 99.2 + 0.6 * (1 - np.exp(-cyc / 5)) + rng.normal(0, 0.05, n)
    return cyc, Qd, np.clip(CE, 0, 100)


def plot_gcd(save="gcd_example.png"):
    import matplotlib.pyplot as plt
    try:
        import labpalette as lp; lp.apply(); teal, amber = lp.C["teal"], lp.C["amber"]
    except Exception:
        teal, amber = "#0F6E6B", "#E29A2D"
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    q, Vc, Vd = _profile()
    ax[0].plot(q, Vc, color=teal, lw=1.3, label="charge")
    ax[0].plot(q, Vd, color=amber, lw=1.3, label="discharge")
    ax[0].set_xlabel("specific capacity (mAh g⁻¹)"); ax[0].set_ylabel("voltage (V)")
    ax[0].set_title("GCD voltage profile"); ax[0].legend(fontsize=7)
    cyc, Qd, CE = _cycling()
    ax[1].plot(cyc, Qd, "o", color=amber, ms=3.5)
    ax[1].set_xlabel("cycle number"); ax[1].set_ylabel("discharge capacity (mAh g⁻¹)", color=amber)
    ax[1].tick_params(axis="y", colors=amber)
    a2 = ax[1].twinx(); a2.plot(cyc, CE, "-", color=teal, lw=1.2)
    a2.set_ylabel("Coulombic efficiency (%)", color=teal); a2.tick_params(axis="y", colors=teal)
    a2.set_ylim(95, 100.5)
    ax[1].set_title("Capacity & CE vs cycle")
    fig.tight_layout(); fig.savefig(save, dpi=150)
    return save


def main():
    # worked numbers: 1.5 mA discharge for 1 h on 15 mg of active material
    I, dt, m = 1.5e-3, 3600.0, 1.5e-2
    q = specific_capacity(I, dt, m)
    print(f"q = I·Δt/(3.6·m) = ({I}·{dt})/(3.6·{m}) = {q:.0f} mAh/g")
    print(f"CE (Δt_dis=3560 s, Δt_ch=3600 s) = {coulombic_efficiency(3600, 3560):.2f} %")
    out = plot_gcd()
    print("wrote", out)


if __name__ == "__main__":
    main()
