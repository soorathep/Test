"""
skh_palette
===========

Teal-Amber Lab Palette v1.0 for matplotlib.

The palette is CVD-safe and grayscale-separable. Semantics are fixed
across all figures produced by the lab:

    teal   control / baseline / reference
    amber  the effect of interest (the treatment or result the figure
           is about)
    sand   confidence bands and shaded fills

Rules enforced or supported here:
  * categorical colours are used in the listed order;
  * ordered or continuous data use a ramp, never the categorical cycle;
  * the diverging ramp is centred on zero (vmin = -vmax);
  * lines are at least 1.5 pt and markers at least 4 pt;
  * axes are graphite, text is ink, gridlines are mist;
  * export is vector, or raster at 600 dpi or more.

Quick start
-----------
    import skh_palette as skh
    skh.use()                       # publication profile
    fig, ax = plt.subplots()
    ax.plot(x, y0, label="Baseline")          # teal, automatically
    ax.plot(x, y1, label="0.5 M additive")    # amber, automatically
    skh.ci_band(ax, x, lo, hi)
    skh.save(fig, "fig2_rate_capability")     # writes .pdf and .png

Author: prepared for the SKH Research Group, Chulalongkorn University.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

__all__ = [
    "CATEGORICAL",
    "NEUTRALS",
    "C",
    "use",
    "cmap",
    "diverging_norm",
    "ci_band",
    "panel_labels",
    "save",
    "figsize",
    "swatch",
]

# ---------------------------------------------------------------------
# Colour definitions
# ---------------------------------------------------------------------

#: Categorical colours in their fixed order. Do not reorder.
CATEGORICAL = [
    "#0F6E6B",  # 0 teal     control / baseline / reference
    "#E29A2D",  # 1 amber    the effect of interest
    "#BE654C",  # 2 rust
    "#5A91BE",  # 3 skyblue
    "#83A462",  # 4 sage
    "#995A90",  # 5 plum
    "#333F4A",  # 6 graphite
    "#DFC98F",  # 7 sand     confidence bands and fills
]

#: Neutrals. Graphite is the darkest tone used for rules and axes;
#: pure black is never used.
NEUTRALS = {
    "ink": "#1C242B",       # body text
    "graphite": "#333F4A",  # axes, reference lines
    "slate": "#66727C",     # secondary text, annotations
    "mist": "#B9C1C6",      # gridlines
    "paper": "#F3F0EB",     # tinted background for slides and reports
}

#: Named access to every colour, e.g. C["teal"], C["mist"].
C = {
    "teal": CATEGORICAL[0],
    "amber": CATEGORICAL[1],
    "rust": CATEGORICAL[2],
    "skyblue": CATEGORICAL[3],
    "sage": CATEGORICAL[4],
    "plum": CATEGORICAL[5],
    "graphite": CATEGORICAL[6],
    "sand": CATEGORICAL[7],
    **NEUTRALS,
}

# ---------------------------------------------------------------------
# Colour ramps
# ---------------------------------------------------------------------

_SEQ_TEAL = ["#F4F9F8", "#C3E0DD", "#7FBEB9", "#3B948F", "#0F6E6B", "#0A4A47"]
_SEQ_AMBER = ["#FDF7EC", "#F7E3BF", "#EFC57F", "#E29A2D", "#B87516", "#80500B"]
_DIV_TEAL_AMBER = [
    "#0A4A47", "#0F6E6B", "#4FA39E", "#A8CFCB",
    "#F2F1EE",
    "#F4DFB6", "#EFC57F", "#E29A2D", "#A86E15",
]

_RAMPS = {
    "skh_teal": _SEQ_TEAL,
    "skh_amber": _SEQ_AMBER,
    "skh_div": _DIV_TEAL_AMBER,
}

_REGISTERED = False


def _register_cmaps() -> None:
    """Register the three ramps with matplotlib, forward and reversed."""
    global _REGISTERED
    if _REGISTERED:
        return
    for name, colors in _RAMPS.items():
        for suffix, seq in (("", colors), ("_r", list(reversed(colors)))):
            full = name + suffix
            cm = LinearSegmentedColormap.from_list(full, seq, N=256)
            try:
                mpl.colormaps.register(cm, name=full, force=True)
            except (AttributeError, ValueError):
                # Older matplotlib, or already present.
                try:
                    mpl.cm.register_cmap(name=full, cmap=cm)
                except Exception:
                    pass
    _REGISTERED = True


def cmap(kind: str = "teal"):
    """
    Return one of the palette ramps.

    Parameters
    ----------
    kind : {"teal", "amber", "div", "teal_r", "amber_r", "div_r"}
        ``teal`` and ``amber`` are sequential, for ordered or continuous
        data. ``div`` is diverging and must be paired with
        :func:`diverging_norm` so that the neutral midpoint sits at zero.
    """
    _register_cmaps()
    key = kind if kind.startswith("skh_") else f"skh_{kind}"
    return mpl.colormaps[key]


def diverging_norm(data, center: float = 0.0) -> TwoSlopeNorm:
    """
    Build a symmetric norm for the diverging ramp.

    The palette rule is that a diverging map is centred on zero with
    ``vmin = -vmax``, so that equal deviations in either direction read
    as equally strong.
    """
    arr = np.asarray(data, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        raise ValueError("no finite values in data")
    half = float(np.max(np.abs(finite - center)))
    if half == 0.0:
        half = 1.0
    return TwoSlopeNorm(vmin=center - half, vcenter=center, vmax=center + half)


# ---------------------------------------------------------------------
# Style activation
# ---------------------------------------------------------------------

_STYLE_DIR = Path(__file__).resolve().parent


def use(profile: str = "publication", thai: bool = False, **overrides) -> None:
    """
    Activate the lab style.

    Parameters
    ----------
    thai : bool
        Set True for a figure containing Thai text. Inter has no Thai glyphs and
        matplotlib does not fall back per glyph, so Thai would render as empty boxes.
        This switches the whole figure to IBM Plex Sans Thai, which carries both
        scripts, keeping Latin text consistent within the figure.
    profile : {"publication", "slides"}
        ``publication`` is a white canvas at journal font sizes.
        ``slides`` uses the paper tint, larger type and heavier lines,
        for talks and internal reports.
    **overrides
        Any additional rcParams, applied after the profile.
    """
    style_file = _STYLE_DIR / "skh_lab.mplstyle"
    if style_file.exists():
        plt.style.use(str(style_file))
    else:  # fall back to an inline equivalent of the essentials
        plt.rcParams.update(
            {
                "axes.prop_cycle": mpl.cycler(color=CATEGORICAL),
                "axes.edgecolor": C["graphite"],
                "text.color": C["ink"],
                "grid.color": C["mist"],
                "axes.grid": True,
                "lines.linewidth": 1.6,
                "lines.markersize": 4.5,
                "pdf.fonttype": 42,
                "ps.fonttype": 42,
                "savefig.dpi": 600,
            }
        )

    if profile == "slides":
        plt.rcParams.update(
            {
                "figure.figsize": (6.5, 4.2),
                "figure.facecolor": C["paper"],
                "axes.facecolor": C["paper"],
                "savefig.facecolor": C["paper"],
                "font.size": 13.0,
                "axes.titlesize": 15.0,
                "axes.labelsize": 13.0,
                "xtick.labelsize": 11.0,
                "ytick.labelsize": 11.0,
                "legend.fontsize": 11.0,
                "lines.linewidth": 2.4,
                "lines.markersize": 6.5,
                "axes.linewidth": 1.1,
            }
        )
    elif profile != "publication":
        raise ValueError("profile must be 'publication' or 'slides'")

    if thai:
        plt.rcParams["font.family"] = "IBM Plex Sans Thai"

    _register_cmaps()
    plt.rcParams["image.cmap"] = "skh_teal"

    if overrides:
        plt.rcParams.update(overrides)


def figsize(width: str = "single", ratio: float = 0.75) -> tuple[float, float]:
    """
    Journal figure widths in inches.

    ``single`` 3.35 in (85 mm), ``onehalf`` 4.72 in (120 mm),
    ``double`` 6.93 in (176 mm). These cover the Elsevier, RSC and ACS
    column specifications without rescaling at the proof stage, which is
    what keeps the font size in the figure equal to the size you set.
    """
    widths = {"single": 3.35, "onehalf": 4.72, "double": 6.93}
    if width not in widths:
        raise ValueError(f"width must be one of {sorted(widths)}")
    w = widths[width]
    return (w, w * ratio)


# ---------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------

def ci_band(ax, x, lower, upper, color: str | None = None,
            alpha: float = 0.45, **kwargs):
    """
    Shade a confidence or uncertainty band.

    Sand is the palette's designated fill colour, so a band never
    competes with the categorical series drawn over it.
    """
    return ax.fill_between(
        x, lower, upper,
        color=color or C["sand"],
        alpha=alpha,
        linewidth=0,
        zorder=kwargs.pop("zorder", 1),
        **kwargs,
    )


def panel_labels(axes, labels=None, weight: str = "bold",
                 size: float | None = None, x: float = -0.02,
                 y: float = 1.06, **kwargs):
    """
    Add (a), (b), (c) labels to a multi-panel figure.

    Placed in axes coordinates just outside the top-left corner of each
    panel, which is the position most publishers expect.
    """
    axes = np.atleast_1d(np.asarray(axes, dtype=object)).ravel()
    if labels is None:
        labels = [f"({chr(97 + i)})" for i in range(len(axes))]
    size = size or plt.rcParams["axes.titlesize"]
    out = []
    for ax, lab in zip(axes, labels):
        out.append(
            ax.text(x, y, lab, transform=ax.transAxes,
                    fontsize=size, fontweight=weight,
                    color=C["ink"], ha="right", va="bottom", **kwargs)
        )
    return out


def reference_line(ax, value, axis: str = "y", **kwargs):
    """Draw a graphite reference line, the palette's role for that colour."""
    opts = dict(color=C["graphite"], linewidth=1.0, linestyle=(0, (4, 3)),
                zorder=0.5)
    opts.update(kwargs)
    if axis == "y":
        return ax.axhline(value, **opts)
    return ax.axvline(value, **opts)


# ---------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------

def save(fig, stem, formats=("pdf", "png"), directory: str | os.PathLike = ".",
         dpi: int = 600, **kwargs):
    """
    Export a figure in vector and raster form in one call.

    The PDF is the submission file; the PNG at 600 dpi is for drafts,
    slides and e-mail. Both satisfy the palette's export rule.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for fmt in formats:
        path = directory / f"{stem}.{fmt}"
        fig.savefig(path, format=fmt, dpi=dpi, **kwargs)
        written.append(path)
    return written


# ---------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------

def swatch(save_to: str | None = None):
    """Render the palette itself, for checking against a printed proof."""
    use()
    fig, axes = plt.subplots(3, 1, figsize=(6.0, 4.4), height_ratios=[1.3, 1, 1.6])

    names = ["teal", "amber", "rust", "skyblue", "sage", "plum", "graphite", "sand"]
    for i, (name, col) in enumerate(zip(names, CATEGORICAL)):
        axes[0].add_patch(plt.Rectangle((i, 0), 0.92, 1, color=col))
        axes[0].text(i + 0.46, -0.18, name, ha="center", va="top", fontsize=7.5,
                     color=C["slate"])
        axes[0].text(i + 0.46, 1.12, col, ha="center", va="bottom", fontsize=6.5,
                     color=C["slate"])
    axes[0].set_xlim(0, len(CATEGORICAL))
    axes[0].set_ylim(-0.6, 1.5)
    axes[0].set_title("Categorical, in fixed order")

    for i, (key, col) in enumerate(NEUTRALS.items()):
        axes[1].add_patch(plt.Rectangle((i, 0), 0.92, 1, color=col,
                                        ec=C["mist"], lw=0.5))
        axes[1].text(i + 0.46, -0.18, key, ha="center", va="top", fontsize=7.5,
                     color=C["slate"])
    axes[1].set_xlim(0, len(NEUTRALS))
    axes[1].set_ylim(-0.6, 1.2)
    axes[1].set_title("Neutrals")

    grad = np.linspace(0, 1, 256).reshape(1, -1)
    for i, (key, label) in enumerate(
        [("teal", "sequential teal"), ("amber", "sequential amber"),
         ("div", "diverging teal-amber")]
    ):
        axes[2].imshow(grad, aspect="auto", cmap=cmap(key),
                       extent=(0, 10, 2 - i - 0.82, 2 - i - 0.08))
        axes[2].text(-0.15, 2 - i - 0.45, label, ha="right", va="center",
                     fontsize=7.5, color=C["slate"])
    axes[2].set_xlim(-3.2, 10)
    axes[2].set_ylim(-0.1, 2.05)
    axes[2].set_title("Ramps")

    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for s in ax.spines.values():
            s.set_visible(False)

    if save_to:
        save(fig, Path(save_to).stem, directory=Path(save_to).parent or ".")
    return fig


if __name__ == "__main__":
    swatch("palette_swatch")
    print("wrote palette_swatch.pdf and palette_swatch.png")
