"""
labpalette.py — Teal–Amber Lab Palette for matplotlib / seaborn
================================================================
Publication figure colour system v1.0 · CVD-safe, greyscale-separable.

The whole point of this module is consistency: every figure the laboratory
produces should be drawn from the same colours, with the same meanings, so that
our output is recognisable and remains readable for colour-blind readers and in
greyscale. See lab_palette_guide.pdf for the full specification.

Quick start
-----------
    import labpalette as lp
    lp.apply()                                  # house style (colours, fonts, 600 dpi)

    ax.plot(x, y1, label="control")             # cycles teal, amber, rust, ...
    ax.plot(x, y2, label="treated")

    lp.cat(4)                                    # ['#0F6E6B', '#E29A2D', '#BE654C', '#5A91BE']
    lp.C["amber"]                                # '#E29A2D'

    ax.imshow(Z, cmap=lp.cmap("teal"))           # sequential magnitude
    ax.imshow(D, cmap=lp.cmap("diverging"),      # signed, centred on zero
              vmin=-3, vmax=3)

    import seaborn as sns
    sns.set_palette(lp.cat(5))

Semantic roles (fix these across every figure)
----------------------------------------------
    teal    control / baseline / untreated / reference
    amber   the effect of interest (treatment, mutant, the result the figure is about)
    rust    third condition        skyblue  fourth condition
    sage    fifth condition        plum     sixth condition
    graphite  axes, ticks, text, reference lines — never pure black
    sand    confidence bands, shaded fills, non-data backgrounds
"""

from matplotlib.colors import LinearSegmentedColormap

__version__ = "1.0"

# ── Categorical colours — USE IN THIS ORDER (the order encodes the CVD optimisation) ──
CAT_NAMES = ["teal", "amber", "rust", "skyblue", "sage", "plum", "graphite", "sand"]
CATEGORICAL = ["#0F6E6B", "#E29A2D", "#BE654C", "#5A91BE",
               "#83A462", "#995A90", "#333F4A", "#DFC98F"]

# ── Neutrals — carry all non-data ink ──
NEUTRALS = {
    "ink":      "#1C242B",   # body text, titles, labels
    "graphite": "#333F4A",   # axes, ticks, tick labels, reference lines
    "slate":    "#66727C",   # secondary text, captions, annotations
    "mist":     "#B9C1C6",   # gridlines, minor rules
    "paper":    "#F3F0EB",   # panel backgrounds, table banding
}

# ── Named lookup: every categorical + neutral colour by name ──
C = dict(zip(CAT_NAMES, CATEGORICAL))
C.update(NEUTRALS)

# ── Continuous ramps ──
SEQ_TEAL = ["#EDF9FA", "#B8E4E7", "#85CED2", "#51B7BC", "#009FA3",
            "#00888A", "#006F70", "#005756", "#003F3D"]           # linear L* 97→23
SEQ_AMBER = ["#FDF9EE", "#F3DEA8", "#E4C27C", "#D5A656", "#C58A33",
             "#B46F0C", "#A35200", "#923400", "#810800"]          # linear L* 98→26
DIVERGING = ["#007372", "#008C8B", "#53A6A5", "#86C0BF", "#B6D9D9", "#F3F0EB",
             "#ECCF9F", "#DDAD68", "#CC8C36", "#BA6A00", "#A84500"]  # symmetric, stop 6 = zero

# Recommended subset sizes → the colours to use (from the guide, §4.3)
_SUBSETS = {2: CATEGORICAL[:2], 3: CATEGORICAL[:3], 4: CATEGORICAL[:4],
            5: CATEGORICAL[:5], 6: CATEGORICAL[:6], 7: CATEGORICAL[:7], 8: CATEGORICAL}


def cat(n=8):
    """First `n` categorical colours, in the accessibility-optimised order.

    Taking a subset from the *middle* of the list voids the CVD guarantee — always
    start from the front. Raises if you ask for more than eight.
    """
    if not 1 <= n <= 8:
        raise ValueError("categorical palette has 8 colours; ask for 1–8")
    return CATEGORICAL[:n]


_RAMPS = {"teal": SEQ_TEAL, "amber": SEQ_AMBER, "diverging": DIVERGING,
          "div": DIVERGING, "seq_teal": SEQ_TEAL, "seq_amber": SEQ_AMBER}


def cmap(name="teal", n=256):
    """A matplotlib colormap from one of the ramps.

    name : "teal" | "amber" | "diverging"  (append "_r" to reverse)
    Use sequential ramps for unsigned magnitude, the diverging ramp for signed
    quantities centred on a meaningful zero (set vmin = -vmax).
    """
    reverse = name.endswith("_r")
    key = name[:-2] if reverse else name
    if key not in _RAMPS:
        raise ValueError(f"unknown ramp {name!r}; use teal, amber or diverging")
    stops = list(_RAMPS[key])
    if reverse:
        stops = stops[::-1]
    return LinearSegmentedColormap.from_list(f"lab_{key}{'_r' if reverse else ''}", stops, N=n)


def _register_cmaps():
    """Register lab_teal / lab_amber / lab_diverging so they work as string names too.

    Idempotent and silent: skips ramps already in the registry, so importing the
    module (or calling apply()) twice does not emit 'overwriting cmap' warnings.
    """
    try:
        import matplotlib
        for key in ("teal", "amber", "diverging"):
            for suffix in ("", "_r"):
                name = f"lab_{key}{suffix}"
                try:
                    registered = name in matplotlib.colormaps           # mpl >= 3.6
                except TypeError:
                    registered = name in matplotlib.colormaps()
                if registered:
                    continue
                cm = cmap(key + suffix)
                try:
                    matplotlib.colormaps.register(cm, name=cm.name)      # mpl >= 3.6
                except AttributeError:
                    import matplotlib.cm as mcm
                    mcm.register_cmap(name=cm.name, cmap=cm)             # older mpl
    except Exception:
        pass


def apply(base_font=9.0, grid=False):
    """Set the laboratory house style on the global matplotlib rcParams.

    Colour cycle → the 8 categorical colours in order.
    Default colormap → sequential teal.
    Axes furniture → graphite; text → ink; gridlines → mist; no top/right spines.
    Lines ≥ 1.5 pt, markers ≥ 5 pt, and figures export at 600 dpi (vector-friendly).
    """
    import matplotlib as mpl
    from cycler import cycler

    _register_cmaps()

    rc = {
        # colour
        "axes.prop_cycle": cycler(color=CATEGORICAL),
        "image.cmap": "lab_teal",
        # text / fonts
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": base_font,
        "text.color": C["ink"],
        "axes.titlesize": base_font + 1,
        "axes.labelsize": base_font,
        "xtick.labelsize": base_font - 1,
        "ytick.labelsize": base_font - 1,
        "legend.fontsize": base_font - 1,
        # axis furniture in graphite, never pure black
        "axes.edgecolor": C["graphite"],
        "axes.labelcolor": C["ink"],
        "xtick.color": C["graphite"],
        "ytick.color": C["graphite"],
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        # data ink
        "lines.linewidth": 1.5,
        "lines.markersize": 5.0,
        "patch.linewidth": 0.8,
        # grid
        "axes.grid": grid,
        "grid.color": C["mist"],
        "grid.linewidth": 0.6,
        "grid.alpha": 1.0,
        # background
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        # export — 600 dpi raster fallback; prefer vector (savefig to .pdf/.eps)
        "figure.dpi": 110,
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,   # embed real fonts, editable text in Illustrator
        "ps.fonttype": 42,
    }
    mpl.rcParams.update(rc)
    return mpl.rcParams


# Register colormaps on import so `cmap="lab_teal"` works even without apply()
_register_cmaps()


if __name__ == "__main__":
    # Self-check + a one-page contact sheet of the whole palette.
    import matplotlib.pyplot as plt
    import numpy as np

    apply()
    fig, axs = plt.subplots(2, 2, figsize=(9, 6))

    # categorical
    for i, (name, hexv) in enumerate(zip(CAT_NAMES, CATEGORICAL)):
        axs[0, 0].bar(i, 1, color=hexv)
        axs[0, 0].text(i, -0.08, name, ha="center", va="top", fontsize=7, color=C["slate"])
    axs[0, 0].set_title("Categorical (use in order)")
    axs[0, 0].set_ylim(0, 1.1); axs[0, 0].axis("off")

    # sequential
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    axs[0, 1].imshow(grad, aspect="auto", cmap=cmap("teal"))
    axs[0, 1].set_title("Sequential — teal"); axs[0, 1].axis("off")

    # diverging
    axs[1, 0].imshow(grad, aspect="auto", cmap=cmap("diverging"))
    axs[1, 0].set_title("Diverging — teal↔amber"); axs[1, 0].axis("off")

    # lines
    x = np.linspace(0, 10, 100)
    for i in range(5):
        axs[1, 1].plot(x, np.sin(x + i * 0.6) + i, label=CAT_NAMES[i])
    axs[1, 1].set_title("Colour cycle"); axs[1, 1].legend(loc="upper left", ncol=2)

    fig.suptitle(f"Teal–Amber Lab Palette v{__version__}", color=C["ink"])
    fig.tight_layout()
    fig.savefig("labpalette_preview.png")
    print("wrote labpalette_preview.png  ·  cat(4) =", cat(4))
