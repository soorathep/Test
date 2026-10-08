"""Six reproducible synthetic Chemical Engineering figures.

Keep this module beside skh_palette.py and matplotlib_gallery.ipynb.
Open the notebook and run its cells. The make_* functions return a figure and
metadata and accept output_dir. The notebook writes to gallery_output/.
All observations and model equations are illustrative teaching examples.
"""

from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
PROJECT = BASE.parent if (BASE.parent / "slides").is_dir() else BASE
DEFAULT_OUTPUT = BASE / "matplotlib_gallery"
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".build" / "gallery-mpl"))
os.environ.setdefault("XDG_CACHE_HOME", str(PROJECT / ".build" / "gallery-cache"))
# Use the supplied palette beside this module, or the existing course copy.
for palette_dir in [BASE, PROJECT / "slides"]:
    if (palette_dir / "skh_palette.py").is_file():
        sys.path.insert(0, str(palette_dir))
        break

import skh_palette as skh

skh.use()

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize


SEED = 20261008
mpl.rcParams.update(
    {
        "font.family": "Arial",
        "font.size": 18,
        "axes.titlesize": 22,
        "axes.titleweight": "bold",
        "axes.titlepad": 18,
        "axes.labelsize": 18,
        "xtick.labelsize": 16,
        "ytick.labelsize": 16,
        "legend.fontsize": 15,
        "text.color": skh.C["graphite"],
        "axes.labelcolor": skh.C["graphite"],
        "axes.edgecolor": skh.C["graphite"],
        "xtick.color": skh.C["graphite"],
        "ytick.color": skh.C["graphite"],
        "axes.linewidth": 1.5,
        "lines.linewidth": 2.5,
        "lines.markersize": 6,
        "xtick.major.width": 1.5,
        "ytick.major.width": 1.5,
        "grid.color": skh.C["mist"],
        "grid.linewidth": 1.5,
        "grid.alpha": 0.32,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "rescom-matplotlib-gallery",
        "savefig.dpi": 600,
    }
)


def new_plot(title, *, grid=True):
    fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
    fig.set_constrained_layout_pads(w_pad=0.15, h_pad=0.14)
    ax.set_title(title, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=5, pad=7)
    ax.xaxis.labelpad = 10
    ax.yaxis.labelpad = 10
    ax.set_axisbelow(True)
    ax.grid(grid, axis="y")
    ax.grid(False, axis="x")
    return fig, ax


def save(fig, name, rows, *, output_dir, title, caption, when_use, model, alt):
    OUTPUT = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT
    OUTPUT.mkdir(parents=True, exist_ok=True)
    assert not rows.isna().any().any(), name
    rows.to_csv(OUTPUT / f"{name}.csv", index=False, float_format="%.9g")
    fig.savefig(OUTPUT / f"{name}.svg", metadata={"Date": None})
    fig.savefig(
        OUTPUT / f"{name}.pdf",
        metadata={"CreationDate": None, "ModDate": None},
    )
    entry = {
            "name": name,
            "title": title,
            "caption": caption,
            "when_use": when_use,
            "underlying_model": model,
            "alt": alt,
            "synthetic": True,
            "seed": SEED,
            "data": f"{name}.csv",
            "svg": f"{name}.svg",
            "pdf": f"{name}.pdf",
            "size_inches": [10, 5],
        }
    print(f"Saved {name}: {len(rows)} synthetic rows")
    return fig, entry


def response(temperature_C, residence_min):
    """Illustrative first-order conversion surface, X in percentage points."""
    rate_min_inv = 0.20 * np.exp(0.015 * (temperature_C - 350))
    return 100 * (1 - np.exp(-rate_min_inv * residence_min))


def readable_text(background):
    """Choose the higher-contrast palette neutral for an RGB background."""
    def luminance(color):
        rgb = np.asarray(mpl.colors.to_rgb(color))
        linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
        return np.dot(linear, [0.2126, 0.7152, 0.0722])
    back = luminance(background)
    def contrast(color):
        front = luminance(color)
        return (max(front, back) + 0.05) / (min(front, back) + 0.05)
    return max([skh.C["graphite"], skh.C["paper"]], key=contrast)


def make_time_response(output_dir=None):
    """Save this figure and its CSV, returning (figure, metadata)."""
    # 1. A process response with a correctly defined between-run SD band.
    rng = np.random.default_rng(SEED + 1)
    time = np.linspace(0, 60, 31)
    records = []
    for condition, plateau, time_constant in [
        ("Baseline", 78, 13),
        ("Modified", 92, 9),
    ]:
        for replicate in range(1, 9):
            plateau_run = plateau * (1 + rng.normal(0, 0.025))
            tau_run = time_constant * (1 + rng.normal(0, 0.06))
            observation = plateau_run * (1 - np.exp(-time / tau_run))
            observation += rng.normal(0, 0.55, size=time.size) * (1 - np.exp(-time / 5))
            observation = np.clip(observation, 0, 100)
            for t, x in zip(time, observation):
                records.append([condition, replicate, t, x])
    rows = pd.DataFrame(records, columns=["condition", "replicate", "time_min", "conversion_pct"])
    fig, ax = new_plot("Follow a process response")
    for condition, color in [("Baseline", skh.C["teal"]), ("Modified", skh.C["amber"])]:
        grouped = rows[rows.condition.eq(condition)].groupby("time_min").conversion_pct
        mean, sd = grouped.mean(), grouped.std(ddof=1)
        ax.fill_between(mean.index, mean - sd, mean + sd, color=skh.C["sand"], alpha=0.60, linewidth=0)
        ax.plot(mean.index, mean, color=color, label=condition, linewidth=2.8)
    ax.set(xlabel="Time (min)", ylabel="Conversion (%)", xlim=(0, 60), ylim=(0, 100))
    ax.legend(loc="lower right", frameon=False, title="8 synthetic runs each", title_fontsize=15)
    ax.text(0.03, 0.93, "Band: mean ± 1 SD", transform=ax.transAxes, fontsize=16, va="top")
    return save(
        fig, "01_time_response", rows, output_dir=output_dir,
        title="Time-series response with uncertainty",
        caption="Synthetic step responses. Lines show the mean of eight independent simulated runs per condition; sand bands show ±1 sample SD at each time. They are not confidence intervals.",
        when_use="Compare how a response evolves and show between-run spread without hiding the time course.",
        model="X(t) = X_inf [1 - exp(-t/tau)]. Baseline X_inf=78%, tau=13 min; modified X_inf=92%, tau=9 min. Each run perturbs X_inf (2.5% SD), tau (6% SD), and adds 0.55-percentage-point observation noise scaled to zero at t=0.",
        alt="Two synthetic conversion curves rise from zero. The modified condition rises faster and approaches a higher plateau than the baseline. Sand bands show one standard deviation across eight runs.",
    )


def make_raw_points_sd(output_dir=None):
    """Save this figure and its CSV, returning (figure, metadata)."""
    # 2. Preserve the observations behind a summary statistic.
    rng = np.random.default_rng(SEED + 2)
    records = []
    for temperature, mean, sd in [(300, 40, 2), (325, 55, 2.5), (350, 70, 3), (375, 80, 3.5)]:
        for replicate, x in enumerate(rng.normal(mean, sd, 8), 1):
            records.append([temperature, replicate, x])
    rows = pd.DataFrame(records, columns=["temperature_C", "replicate", "conversion_pct"])
    fig, ax = new_plot("Keep the individual runs visible")
    for temperature, group in rows.groupby("temperature_C"):
        jitter = rng.uniform(-3.4, 3.4, len(group))
        ax.scatter(temperature + jitter, group.conversion_pct, s=62, color=skh.C["amber"],
                   alpha=0.38, edgecolors=skh.C["graphite"], linewidths=1.5, zorder=3)
        ax.errorbar(temperature, group.conversion_pct.mean(), yerr=group.conversion_pct.std(ddof=1),
                    fmt="D", color=skh.C["amber"], markeredgecolor=skh.C["graphite"],
                    markeredgewidth=1.5, markersize=8, linewidth=2.2, capsize=7, capthick=2.2, zorder=4)
    ax.set(xlabel="Temperature (°C)", ylabel="Conversion (%)", xlim=(290, 385),
           ylim=(0, 100), xticks=[300, 325, 350, 375])
    ax.text(0.03, 0.95, "Dots: 8 runs each\nDiamond + whiskers: mean ± 1 SD",
            transform=ax.transAxes, va="top", fontsize=16, linespacing=1.45)
    return save(
        fig, "02_raw_points_sd", rows, output_dir=output_dir,
        title="Raw observations with mean and SD",
        caption="Synthetic conversion at four temperature settings, eight runs per setting. Horizontal dot jitter only prevents overlap; diamonds show means and whiskers show ±1 sample SD.",
        when_use="Show replicate counts, spread, possible unusual observations, and the summary on one chart.",
        model="Eight normal draws at each setting: mean conversion=[40,55,70,80]% and generating SD=[2,2.5,3,3.5] percentage points at T=[300,325,350,375] °C. Displayed statistics are computed from the draws.",
        alt="Eight dots at each of four temperatures with overlaid mean diamonds and standard-deviation whiskers. Synthetic conversion increases from approximately 40% to 80%.",
    )


def make_parity_temperature(output_dir=None):
    """Save this figure and its CSV, returning (figure, metadata)."""
    # 3. A parity plot shows agreement against an identity reference.
    rng = np.random.default_rng(SEED + 3)
    temperature = rng.uniform(300, 400, 52)
    residence = rng.uniform(1, 8, 52)
    truth = response(temperature, residence)
    observed = np.clip(truth + rng.normal(0, 2.2, 52), 0, 100)
    predicted = np.clip(0.97 * truth + 1.5 + rng.normal(0, 1.4, 52), 0, 100)
    rows = pd.DataFrame({"temperature_C": temperature, "residence_min": residence,
                         "observed_conversion_pct": observed, "predicted_conversion_pct": predicted})
    fig, ax = new_plot("Predicted vs observed", grid=False)
    ax.plot([0, 100], [0, 100], color=skh.C["graphite"], linestyle=(0, (5, 4)), linewidth=1.8, zorder=1)
    points = ax.scatter(observed, predicted, c=temperature, cmap=skh.cmap("teal"),
                        norm=Normalize(300, 400), s=76, edgecolors=skh.C["graphite"], linewidths=1.5, zorder=2)
    ax.set(xlabel="Observed conversion (%)", ylabel="Predicted conversion (%)",
           xlim=(0, 100), ylim=(0, 100), xticks=[0, 25, 50, 75, 100], yticks=[0, 25, 50, 75, 100])
    ax.set_aspect("equal", adjustable="box")
    ax.text(0.05, 0.93, "Dashed line: identity", transform=ax.transAxes, fontsize=15, va="top")
    cbar = fig.colorbar(points, ax=ax, pad=0.045, fraction=0.05, ticks=[300, 325, 350, 375, 400])
    cbar.set_label("Temperature (°C)", labelpad=12)
    cbar.outline.set_linewidth(1.5)
    cbar.outline.set_edgecolor(skh.C["graphite"])
    rmse = float(np.sqrt(np.mean((predicted - observed) ** 2)))
    fig.text(0.04, 0.63, "52 synthetic\noperating points", fontsize=20, fontweight="bold", linespacing=1.5)
    fig.text(0.04, 0.39, f"RMSE = {rmse:.1f} pp\n\nSame scale on both axes", fontsize=16)
    return save(
        fig, "03_parity_temperature", rows, output_dir=output_dir,
        title="Parity plot with a continuous color variable",
        caption="Synthetic observed and predicted conversion for 52 operating points. Equal axis scales and the graphite identity line reveal agreement. Point color encodes temperature on a continuous ramp; this is an illustration, not model validation.",
        when_use="Inspect prediction errors and whether they vary with an operating condition. A high correlation alone does not establish agreement.",
        model="Latent X=100[1-exp(-k(T)*tau)], k(T)=0.20 exp(0.015(T-350)) min^-1. Observed X adds N(0,2.2) percentage points. Predicted X=0.97X+1.5+N(0,1.4), clipped to physical bounds. T~U(300,400) °C and tau~U(1,8) min.",
        alt="Predicted versus observed synthetic conversion with equal zero-to-100 axes, a dashed identity line, and points colored continuously by temperature from 300 to 400 degrees Celsius.",
    )


def make_operating_heatmap(output_dir=None):
    """Save this figure and its CSV, returning (figure, metadata)."""
    # 4. An explicitly discrete set of operating conditions.
    temperatures = np.arange(300, 401, 20)
    residences = np.arange(1, 9)
    R, T = np.meshgrid(residences, temperatures)
    Z = response(T, R)
    rows = pd.DataFrame({"temperature_C": T.ravel(), "residence_min": R.ravel(), "conversion_pct": Z.ravel()})
    fig, ax = new_plot("Read a grid of operating conditions", grid=False)
    cmap = skh.cmap("amber")
    norm = Normalize(0, 100)
    hm = ax.imshow(Z, origin="lower", cmap=cmap, norm=norm, aspect="auto",
                   extent=(0.5, 8.5, 290, 410), interpolation="nearest")
    for i, temperature in enumerate(temperatures):
        for j, residence in enumerate(residences):
            color = readable_text(cmap(norm(Z[i, j])))
            ax.text(residence, temperature, f"{Z[i, j]:.0f}", ha="center", va="center",
                    fontsize=15, color=color)
    ax.set(xlabel="Residence time (min)", ylabel="Temperature (°C)",
           xticks=residences, yticks=temperatures)
    cbar = fig.colorbar(hm, ax=ax, pad=0.025, fraction=0.05, ticks=[0, 20, 40, 60, 80, 100])
    cbar.set_label("Conversion (%)", labelpad=10)
    cbar.outline.set_linewidth(1.5)
    cbar.outline.set_edgecolor(skh.C["graphite"])
    return save(
        fig, "04_operating_heatmap", rows, output_dir=output_dir,
        title="Heatmap of a two-variable response",
        caption="Synthetic conversion at 48 operating settings. Cell labels round the model output to whole percentages; the color scale is fixed at 0–100%. The six temperature rows and eight residence-time columns are discrete settings.",
        when_use="Compare a measured or calculated grid and locate broad patterns across two factors without hiding exact values.",
        model="X(T,tau)=100[1-exp(-0.20 exp(0.015(T-350))*tau)]. Temperature: 300,320,...,400 °C; residence time: 1,2,...,8 min. Illustrative model with no experimental noise.",
        alt="An amber sequential heatmap of synthetic conversion across six temperature settings and eight residence times. Conversion increases toward the high-temperature, long-residence corner.",
    )


def make_response_contours(output_dir=None):
    """Save this figure and its CSV, returning (figure, metadata)."""
    # 5. Same model, now displayed continuously with iso-response lines.
    temperatures = np.linspace(300, 400, 101)
    residences = np.linspace(1, 8, 113)
    R, T = np.meshgrid(residences, temperatures)
    Z = response(T, R)
    rows = pd.DataFrame({"temperature_C": T.ravel(), "residence_min": R.ravel(), "conversion_pct": Z.ravel()})
    fig, ax = new_plot("Trace combinations with the same response", grid=False)
    filled = ax.contourf(R, T, Z, levels=np.arange(0, 101, 5), cmap=skh.cmap("amber"), norm=Normalize(0, 100))
    curves = ax.contour(R, T, Z, levels=[20, 40, 60, 80, 90], colors=[skh.C["graphite"]], linewidths=1.5)
    contour_labels = ax.clabel(curves, inline=True, inline_spacing=8, fmt=lambda value: f"{value:.0f}%", fontsize=15)
    for label in contour_labels:
        value = float(label.get_text().rstrip("%"))
        label.set_color(readable_text(skh.cmap("amber")(Normalize(0, 100)(value))))
    ax.set(xlabel="Residence time (min)", ylabel="Temperature (°C)",
           xlim=(1, 8), ylim=(300, 400), xticks=[1, 2, 3, 4, 5, 6, 7, 8], yticks=[300, 320, 340, 360, 380, 400])
    cbar = fig.colorbar(filled, ax=ax, pad=0.025, fraction=0.05, ticks=[0, 20, 40, 60, 80, 100])
    cbar.set_label("Conversion (%)", labelpad=10)
    cbar.outline.set_linewidth(1.5)
    cbar.outline.set_edgecolor(skh.C["graphite"])
    return save(
        fig, "05_response_contours", rows, output_dir=output_dir,
        title="Contour map of the same response surface",
        caption="The same synthetic model and 0–100% color scale as the heatmap, evaluated on a fine grid. Labeled contours connect equal conversion. Smooth regions reflect the assumed model, not additional measurements.",
        when_use="Explore tradeoffs between two continuous operating variables and follow equal-response combinations within a justified model domain.",
        model="Identical equation to 04_operating_heatmap, evaluated at 101 temperatures from 300 to 400 °C and 113 residence times from 1 to 8 min. No extrapolation beyond that displayed domain.",
        alt="A smooth amber contour map with labeled lines at 20%, 40%, 60%, 80%, and 90% synthetic conversion. Higher temperature can produce the same model conversion at shorter residence time.",
    )


def make_catalyst_distributions(output_dir=None):
    """Save this figure and its CSV, returning (figure, metadata)."""
    # 6. A distribution can reveal more than its mean.
    rng = np.random.default_rng(SEED + 6)
    records = []
    for catalyst, mean, sd in [("A: Control", 72, 5), ("B: Modified", 81, 3), ("C: Alternative", 83, 7)]:
        for replicate, value in enumerate(np.clip(rng.normal(mean, sd, 30), 0, 100), 1):
            records.append([catalyst, replicate, value])
    rows = pd.DataFrame(records, columns=["catalyst", "replicate", "selectivity_pct"])
    groups = [group.selectivity_pct.to_numpy() for _, group in rows.groupby("catalyst", sort=False)]
    colors = skh.CATEGORICAL[:3]
    fig, ax = new_plot("Look beyond the average")
    parts = ax.violinplot(groups, positions=[1, 2, 3], widths=0.78, showmeans=False,
                          showmedians=False, showextrema=False, bw_method=0.55)
    for body, color in zip(parts["bodies"], colors):
        body.set_facecolor(color)
        body.set_edgecolor(color)
        body.set_alpha(0.24)
        body.set_linewidth(1.5)
    for x, values, color in zip([1, 2, 3], groups, colors):
        jitter = rng.uniform(-0.23, 0.23, len(values))
        ax.scatter(x+jitter, values, s=39, color=color, alpha=0.70,
                   edgecolors=skh.C["graphite"], linewidths=1.5, zorder=3)
    ax.boxplot(groups, positions=[1, 2, 3], widths=0.12, showfliers=False,
               patch_artist=True, zorder=4,
               boxprops={"facecolor": skh.C["paper"], "edgecolor": skh.C["graphite"], "linewidth": 1.5},
               medianprops={"color": skh.C["graphite"], "linewidth": 2.2},
               whiskerprops={"color": skh.C["graphite"], "linewidth": 1.5},
               capprops={"color": skh.C["graphite"], "linewidth": 1.5})
    ax.set(ylabel="Product selectivity (%)", ylim=(45, 100), xlim=(0.4, 3.6),
           xticks=[1, 2, 3], xticklabels=["A · Control", "B · Modified", "C · Alternative"])
    ax.text(0.03, 0.95, "30 synthetic runs per catalyst", transform=ax.transAxes, fontsize=16, va="top")
    return save(
        fig, "06_catalyst_distributions", rows, output_dir=output_dir,
        title="Violin, box, and raw observations",
        caption="Thirty synthetic selectivity values per catalyst. Dots are individual runs; violin width is a smoothed density. Boxes span the interquartile range with a median line; whiskers extend to the most extreme points within 1.5 IQR. The y-axis starts at 45%, as labeled.",
        when_use="Compare centers, spread, and distribution shape while keeping sample sizes and observations visible. A violin is descriptive, not a test of significance.",
        model="Thirty draws from normal distributions with mean=[72,81,83]% and SD=[5,3,7] percentage points for A/B/C, clipped to 0–100%. Gaussian KDE bandwidth factor 0.55; horizontal jitter has no scientific meaning.",
        alt="Three catalyst distributions, shown as teal, amber, and rust violins with raw points and small box plots. The modified group is relatively narrow; the alternative group has a broader synthetic spread.",
    )


def make_all(output_dir=None, *, verify_fonts=True):
    """Generate all six examples. Return their metadata and font checks.

    Each make_* function also works on its own and returns (fig, metadata).
    In a notebook, display(fig), then plt.close(fig). The palette module can
    sit beside this script; no ResCom-specific path is required.
    """
    OUTPUT = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT
    OUTPUT.mkdir(parents=True, exist_ok=True)
    metadata = []
    for make in [make_time_response, make_raw_points_sd, make_parity_temperature,
                 make_operating_heatmap, make_response_contours, make_catalyst_distributions]:
        fig, entry = make(OUTPUT)
        metadata.append(entry)
        plt.close(fig)
    pdffonts = shutil.which("pdffonts")
    if not pdffonts:
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin/pdffonts"
        if bundled.exists():
            pdffonts = str(bundled)
    font_checks = {}
    if verify_fonts and pdffonts:
        for pdf in sorted(OUTPUT.glob("*.pdf")):
            text = subprocess.check_output([pdffonts, str(pdf)], text=True)
            assert "Type 3" not in text, (pdf, text)
            assert "yes yes yes" in text, (pdf, text)
            font_checks[pdf.name] = text
    elif verify_fonts:
        raise RuntimeError("pdffonts is required for font verification; in a notebook you may set verify_fonts=False")
    else:
        font_checks = {"status": "Not checked in this run"}
    result = {"figures": metadata, "font_verification": font_checks}
    (OUTPUT / "gallery_metadata.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--no-font-check", action="store_true", help="Skip external pdffonts check, e.g. in Colab")
    args = parser.parse_args()
    make_all(args.output_dir, verify_fonts=not args.no_font_check)
