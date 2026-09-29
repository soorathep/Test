"""Reproducible chapter figures; use the lab palette for every visual."""

from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "styles"))
import skh_palette as skh
import pyomo.environ as pyo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "generated"


def create(number, module, m):
    skh.use()
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "lines.linewidth": 1.8,
            "lines.markersize": 5,
            "axes.linewidth": 1.5,
            "pdf.fonttype": 42,
        }
    )
    fig, ax = plt.subplots(figsize=(7.6, 4.3), layout="constrained")
    if number == 11:
        ax.scatter(
            module.X, module.Y, s=30, color=skh.C["teal"], label="Observed response"
        )
        ax.plot(
            module.X,
            [pyo.value(m.fit[j]) for j in m.J],
            color=skh.C["amber"],
            label="L1 straight-line fit",
        )
        ax.set(xlabel="Input (normalized units)", ylabel="Response (normalized units)")
        ax.legend()
    elif number == 17:
        plt.close(fig)
        fig, axes = plt.subplots(1, 3, figsize=(8.5, 3.2), layout="constrained")
        for z, ax in enumerate(axes):
            for x in range(3):
                for y in range(3):
                    white = pyo.value(m.x[x, y, z]) > 0.5
                    ax.scatter(
                        x,
                        y,
                        s=400,
                        facecolor=skh.C["sand"] if white else skh.C["graphite"],
                        edgecolor=skh.C["graphite"],
                        linewidth=1.5,
                    )
                    ax.text(
                        x,
                        y,
                        "W" if white else "D",
                        ha="center",
                        va="center",
                        color=skh.C["graphite"] if white else "white",
                        fontsize=10,
                    )
            ax.set(
                xlim=(-0.6, 2.6),
                ylim=(-0.6, 2.6),
                xticks=[0, 1, 2],
                yticks=[0, 1, 2],
                title=f"Layer z = {z}",
                xlabel="x",
                ylabel="y",
            )
            ax.set_aspect("equal")
    elif number in [23, 27]:
        coords = module.COORD
        if number == 23:
            paths = [module.route(m, t) for t in m.T]
        else:
            paths = [
                [0, *path]
                for r, (path, d) in enumerate(module.ROUTES)
                if pyo.value(m.y[r]) > 0.5
            ]
        for j, path in enumerate(paths):
            ax.plot(
                [coords[i][0] for i in path],
                [coords[i][1] for i in path],
                marker="o",
                color=skh.CATEGORICAL[j],
                label=f"Day {j + 1}" if number == 23 else f"Van {j + 1}",
            )
        for i, (x, y) in enumerate(coords):
            ax.annotate(str(i), (x, y), xytext=(5, 6), textcoords="offset points")
        ax.set(
            xlabel="East coordinate (km)" if number == 23 else "East coordinate",
            ylabel="North coordinate (km)" if number == 23 else "North coordinate",
            xlim=(-0.5, 7),
            ylim=(-0.5, 7),
        )
        ax.set_aspect("equal")
        ax.legend()
    elif number == 28:
        path = module.chosen(m)
        ax.plot([p[0] for p in path], [p[1] for p in path], color=skh.C["graphite"])
        for i, (x, y) in enumerate(path):
            ax.scatter(
                x,
                y,
                s=240,
                color=skh.C["amber"] if module.SEQUENCE[i] == "H" else skh.C["teal"],
                zorder=3,
            )
            ax.annotate(
                f"{i + 1} {module.SEQUENCE[i]}",
                (x, y),
                xytext=(7, 9),
                textcoords="offset points",
            )
        for i, j in module.contacts(path):
            ax.plot(
                [path[i][0], path[j][0]],
                [path[i][1], path[j][1]],
                "--",
                color=skh.C["amber"],
            )
        ax.set(xlabel="Lattice x", ylabel="Lattice y")
        ax.margins(0.25)
        ax.set_aspect("equal")
    elif number == 29:
        from matplotlib.patches import Arc

        for edges, y, count in [(module.EA, 1, 5), (module.EB, 0, 6)]:
            ax.scatter(range(count), [y] * count, s=50, color=skh.C["teal"], zorder=3)
            for i in range(count):
                ax.text(i, y - 0.1, str(i + 1), ha="center", va="top")
            for i, j in edges:
                ax.add_patch(
                    Arc(
                        ((i + j) / 2, y),
                        j - i,
                        0.6,
                        theta1=0,
                        theta2=180,
                        color=skh.C["graphite"],
                        lw=1.5,
                    )
                )
        for i, j in module.alignment(m).items():
            ax.plot([i, j], [0.9, 0.1], "--", color=skh.C["amber"])
        ax.text(-0.7, 1, "A", fontsize=14)
        ax.text(-0.7, 0, "B", fontsize=14)
        ax.set(xlim=(-1, 5.5), ylim=(-0.3, 1.5))
        ax.axis("off")
    else:
        labels, values, ylabel = module.plot(m)
        if any(v < 0 for v in values):
            norm = skh.diverging_norm(values)
            colors = skh.cmap("div")(norm(values))
            ax.axhline(0, color=skh.C["graphite"], lw=1.5)
        elif number in [4, 26]:
            colors = [skh.C["teal"], skh.C["amber"]]
        else:
            colors = skh.C["amber"]
        bars = ax.bar(labels, values, color=colors)
        ax.bar_label(bars, labels=[f"{v:,.2f}" for v in values], padding=4, fontsize=9)
        ax.set_ylabel(ylabel)
        ax.margins(y=0.2)
        ax.grid(axis="x", visible=False)
        if number == 13:
            ax.axhline(40, color=skh.C["graphite"], linestyle="--", lw=1.5)
        if number == 22:
            ax.axhline(1, color=skh.C["graphite"], linestyle="--", lw=1.5)
    OUT.mkdir(exist_ok=True)
    skh.save(
        fig,
        f"problem{number:02d}",
        directory=OUT,
        formats=("svg", "pdf", "png"),
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(fig)


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(ROOT))
    from models.common import run

    number = int(sys.argv[1])
    module, m, _, _ = run(number)
    create(number, module, m)
