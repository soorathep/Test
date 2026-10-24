"""Regenerate Gibbs review figures and numerical reference.

Run: ~/.venvs/research/bin/python _teaching-src/2105603/figures/gibbs_review.py
Uses Teal-Amber Lab Palette v1.0, SciPy and Matplotlib. All numbers are
independently computed here, rather than copied from the browser Lab.
The 2,001-point plotting grid is only for drawing; minima are checked at
all stationary points and endpoints for this symmetric A=3 model.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/gibbs-review-mpl")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq
import skh_palette as skh

skh.use()
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 14,
    "axes.titlesize": 16, "axes.labelsize": 14,
    "legend.fontsize": 14, "xtick.labelsize": 14,
    "ytick.labelsize": 14, "pdf.fonttype": 42, "ps.fonttype": 42,
    "svg.fonttype": "path", "axes.spines.top": False,
    "axes.spines.right": False,
})
C = skh.C
OUT = Path(__file__).resolve().parent
A = 3.0
Z = .12


def g(x):
    x = np.asarray(x, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where((x == 0) | (x == 1), 0.0,
                        x * np.log(x) + (1-x)*np.log1p(-x) + A*x*(1-x))


def slope(x):
    x = np.asarray(x, dtype=float)
    with np.errstate(divide="ignore"):
        return np.log(x/(1-x)) + A*(1-2*x)


def curvature(x):
    x = np.asarray(x, dtype=float)
    return 1/(x*(1-x))-2*A


def mu(x):
    return np.array([np.log(x)+A*(1-x)**2, np.log1p(-x)+A*x*x])


sa = (1-np.sqrt(1-2/A))/2
sb = 1-sa
xa = brentq(slope, 1e-14, sa, xtol=1e-15)
xb = 1-xa
geq = float(g(xa))


def stationary_points(m):
    """All roots of g'(w)=m, using analytical spinodals as branch limits."""
    cuts = [1e-14, sa, sb, 1-1e-14]
    result = []
    for lo, hi in zip(cuts[:-1], cuts[1:]):
        if (slope(lo)-m)*(slope(hi)-m) <= 0:
            result.append(float(brentq(lambda w: slope(w)-m, lo, hi, xtol=1e-15)))
    return result


def tpd_result(z):
    m = float(slope(z))
    candidates = [0.0, z, 1.0] + stationary_points(m)
    values = [float(g(w)-g(z)-m*(w-z)) for w in candidates]
    i = int(np.argmin(values))
    return {"minimum": values[i], "w": candidates[i],
            "stationaryCandidates": stationary_points(m)}


rows = []
for z in [.02, .12, .35, .5, .88]:
    split = xa < z < xb
    fb = (z-xa)/(xb-xa) if split else None
    fa = 1-fb if split else None
    equilibrium_g = geq if split else float(g(z))
    rows.append({
        "z": z, "homogeneousG": float(g(z)),
        "curvature": float(curvature(z)), "slope": float(slope(z)),
        "equilibriumG": equilibrium_g, "gain": float(g(z))-equilibrium_g,
        "state": "stable" if not split else ("unstable" if curvature(z) < 0 else "metastable"),
        "phase": "two liquids" if split else "one liquid",
        "fractionAlpha": fa, "fractionBeta": fb,
        "nAlphaFor100Mol": None if fa is None else 100*fa,
        "nBetaFor100Mol": None if fb is None else 100*fb,
        "componentBalance": None if fa is None else fa*xa+fb*xb,
        "tpd": tpd_result(z),
    })

support_candidates = [0, 1] + stationary_points(0)
support_min = min(float(g(w))-geq for w in support_candidates)
reference = {
    "model": "Symmetric Margules", "A": A,
    "scope": "Fixed T and P; binary liquid phases; no vapor, solid, kinetics or interface energy.",
    "gDefinition": "Delta_mix G / (n R T)",
    "coexistence": {"xAlpha": xa, "xBeta": xb, "gAlpha": geq, "gBeta": float(g(xb)),
                    "commonTangentSlope": 0, "spinodalAlpha": sa, "spinodalBeta": sb,
                    "chemicalPotentialAlpha": mu(xa).tolist(), "chemicalPotentialBeta": mu(xb).tolist()},
    "calculationAtZ012": {
        "idealTerm1": float(Z*np.log(Z)), "idealTerm2": float((1-Z)*np.log1p(-Z)),
        "excessTerm": A*Z*(1-Z),
        "inverseCompositionProduct": 1/(Z*(1-Z)),
        "tpdAtW09": float(g(.9)-g(Z)-slope(Z)*(.9-Z)),
        "gAtW09": float(g(.9)),
        "feedTangentAtW09": float(g(Z)+slope(Z)*(.9-Z)),
    },
    "cases": rows,
    "verification": {
        "maxChemicalPotentialResidual": float(np.max(np.abs(mu(xa)-mu(xb)))),
        "maxTangentSlopeResidual": float(max(abs(slope(xa)), abs(slope(xb)))),
        "globalSupportCandidates": support_candidates,
        "minimumCommonTangentDistance": support_min,
        "method": "Check endpoints and all stationary points, whose brackets are set by analytical spinodals; plotting grid is not the stability criterion.",
    },
    "source": "https://ocw.mit.edu/courses/3-020-thermodynamics-of-materials-spring-2021/mit3_020s21_l21.pdf",
    "notes": [
        "The label stable, metastable or unstable describes the hypothetical homogeneous feed. Inside the miscibility gap the equilibrium is two liquids.",
        "A horizontal common tangent is special to this symmetric mixing-energy curve. Adding or subtracting an affine pure-state reference preserves coexistence and stability.",
        "A negative TPD at any admissible trial composition rules out global stability. TPD minimizer is not generally a coexistence endpoint.",
        "Equality of chemical potentials is necessary but a candidate tangent must also support the entire admissible Gibbs curve.",
        "No kinetics, nucleation barrier or time to separate is predicted.",
    ],
}
assert reference["verification"]["maxChemicalPotentialResidual"] < 1e-12
assert reference["verification"]["maxTangentSlopeResidual"] < 1e-12
assert support_min > -1e-12
assert all(abs(row["componentBalance"]-row["z"]) < 1e-12 for row in rows if row["phase"] == "two liquids")
(OUT/"gibbs-review-reference.json").write_text(json.dumps(reference, indent=2)+"\n")


def axes(title, ylabel, ylim=None):
    fig, ax = plt.subplots(figsize=(10, 5.2), layout="constrained")
    ax.set(xlim=(0, 1), xlabel="Mole fraction of component 1, x", ylabel=ylabel)
    ax.set_title(title, loc="left", pad=16)
    if ylim:
        ax.set_ylim(*ylim)
    ax.tick_params(width=1.5)
    ax.grid(axis="y", alpha=.35, color=C["mist"], linewidth=1.0)
    return fig, ax


def save(fig, name):
    for ext in ("svg", "pdf"):
        fig.savefig(OUT/f"{name}.{ext}", facecolor="white")
    # 600 dpi delivery raster also allows reliable PDF/browser figure QA.
    fig.savefig(OUT/f"{name}.png", dpi=600, facecolor="white")
    plt.close(fig)


x = np.linspace(0, 1, 2001)
hull = np.where((x >= xa) & (x <= xb), geq, g(x))

# 1. Full Gibbs curve: compare alternatives at the same overall composition.
fig, ax = axes("Read vertically at the same overall composition", r"$g=\Delta_{\mathrm{mix}}G/(nRT)$", (-.080, .080))
ax.plot(x, g(x), color=C["amber"], lw=2.4, label="Homogeneous liquid")
ax.plot(x, hull, color=C["teal"], lw=2.2, ls="--", label="Equilibrium envelope")
ax.plot([xa, xb], [geq, geq], color=C["graphite"], lw=1.6, label="Supporting common tangent")
ax.plot([xa, xb], [geq, geq], "o", color=C["graphite"], ms=7)
ax.plot(Z, g(Z), "D", color=C["amber"], ms=8)
ax.plot(Z, geq, "o", color=C["teal"], ms=7)
ax.annotate("Homogeneous feed\nz = 0.12", (Z, float(g(Z))), xytext=(.30, -.010),
            arrowprops={"arrowstyle": "->", "color": C["graphite"], "lw": 1.5}, color=C["graphite"])
ax.text(xa, -.067, r"$x^\alpha=0.07072$", ha="left", va="top", fontsize=14)
ax.text(xb, -.067, r"$x^\beta=0.92928$", ha="right", va="top", fontsize=14)
ax.legend(loc="upper left", bbox_to_anchor=(.00, 1.01), frameon=False, fontsize=14)
save(fig, "gibbs-review-curve")

# 2. The small positive-curvature energy gap is visible on its own scale.
fig, ax = axes("Positive curvature can still sit above equilibrium", r"$g=\Delta_{\mathrm{mix}}G/(nRT)$")
u = np.linspace(.04, .16, 801)
ax.plot(u, g(u), color=C["amber"], lw=2.5, label="Homogeneous liquid")
ax.axhline(geq, color=C["teal"], lw=2.2, ls="--", label="Equilibrium two-liquid mixture")
ax.set(xlim=(.04, .16), ylim=(-.0605, -.034))
ax.plot(Z, g(Z), "D", color=C["amber"], ms=8)
ax.plot(Z, geq, "o", color=C["teal"], ms=7)
ax.annotate("", (Z, geq), xytext=(Z, float(g(Z))),
            arrowprops={"arrowstyle": "<->", "color": C["graphite"], "lw": 1.8})
ax.text(.124, -.0551, "Molar decrease\n= 0.008216 RT", ha="left", va="center", fontsize=14)
ax.text(.043, -.0467, "At z = 0.12:\ng″ = +3.4697\nHomogeneous feed is metastable.", va="center", fontsize=14)
ax.legend(loc="upper left", frameon=False, fontsize=14)
save(fig, "gibbs-review-gap")

# 3. Curvature is a local test. Stable/metastable labels also use global envelope.
fig, ax = axes("Local curvature and global stability answer different questions", r"$g''(x)$", (-3, 8))
u = np.linspace(.001, .999, 2001)
for left, right, label in [(0, xa, "stable"), (xa, sa, "metastable"),
                            (sa, sb, "unstable"), (sb, xb, "metastable"), (xb, 1, "stable")]:
    if label == "unstable":
        ax.axvspan(left, right, facecolor=C["sand"], alpha=.36)
    if label == "metastable":
        ax.axvspan(left, right, facecolor=C["sand"], alpha=.20, hatch="///", edgecolor=C["sand"], linewidth=0)
    ax.text((left+right)/2, 7.35, label, ha="center", va="top", rotation=90 if label=="stable" else 0,
            fontsize=14, color=C["graphite"])
ax.plot(u, curvature(u), color=C["amber"], lw=2.5)
ax.axhline(0, color=C["graphite"], lw=1.5)
for v in [sa, sb]:
    ax.axvline(v, color=C["graphite"], lw=1.5, ls=":")
for v in [xa, xb]:
    ax.axvline(v, color=C["graphite"], lw=1.5, ls="--")
ax.plot([.12, .5], curvature(np.array([.12, .5])), "o", color=C["teal"], ms=7)
ax.annotate("z = 0.12", (.12, float(curvature(.12))), xytext=(.25, 3.7),
            arrowprops={"arrowstyle": "->", "color": C["graphite"], "lw": 1.5}, fontsize=14)
ax.annotate("z = 0.50", (.5, -2), xytext=(.58, -.9),
            arrowprops={"arrowstyle": "->", "color": C["graphite"], "lw": 1.5}, fontsize=14)
ax.text(.5, .5, "g″ < 0", ha="center", fontsize=15)
fig.text(.5, .005, "Dashed: binodals 0.07072, 0.92928  |  Dotted: spinodals 0.21132, 0.78868", ha="center", fontsize=12, color=C["slate"])
fig.set_constrained_layout_pads(h_pad=.12, w_pad=.08)
save(fig, "gibbs-review-regions")

# 4. Feed tangent and TPD: separate plots avoid confusing common/feed tangents.
fig, ax = axes("Test the homogeneous feed tangent over all trial compositions", r"$\mathrm{TPD}(w;z)$", (-.29, .10))
tpd = g(x)-g(Z)-slope(Z)*(x-Z)
ax.set_xlabel("Trial liquid composition, w")
ax.axhline(0, color=C["teal"], lw=1.8, label="Feed tangent reference: TPD = 0")
ax.plot(x, tpd, color=C["amber"], lw=2.5, label="TPD relative to feed z = 0.12")
ax.fill_between(x, tpd, 0, where=tpd < 0, color=C["sand"], alpha=.38)
ax.plot(Z, 0, "o", color=C["teal"], ms=7)
ax.annotate("w = z: zero by construction", (Z, 0), xytext=(.04, -.045), arrowprops={"arrowstyle": "->", "color": C["graphite"], "lw": 1.5}, fontsize=14)
t = tpd_result(Z)
ax.plot(t["w"], t["minimum"], "D", color=C["amber"], ms=8)
ax.annotate(f"Minimum = {t['minimum']:.5f}\nat w = {t['w']:.5f}", (t["w"], t["minimum"]), xytext=(.37, -.24),
            arrowprops={"arrowstyle": "->", "color": C["graphite"], "lw": 1.5}, fontsize=14)
ax.text(.05, -.14, "A negative trial value rules out\nglobal stability of this feed.", fontsize=13)
ax.legend(loc="upper left", frameon=False, fontsize=14)
save(fig, "gibbs-review-tpd")

print(json.dumps({"figures": [f"gibbs-review-{n}" for n in ["curve", "gap", "regions", "tpd"]],
                  "reference": "gibbs-review-reference.json", "verification": reference["verification"]}, indent=2))
