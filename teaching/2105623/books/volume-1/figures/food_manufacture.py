"""Regenerate all Chapter 1 figures from solver output."""

from pathlib import Path
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "styles"))
import skh_palette as skh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "generated"
OUT.mkdir(exist_ok=True)
skh.use()
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "legend.fontsize": 10,
        "lines.linewidth": 1.8,
        "lines.markersize": 5,
        "pdf.fonttype": 42,
        "axes.linewidth": 1.5,
    }
)


def save(fig, name):
    skh.save(
        fig,
        name,
        directory=OUT,
        formats=("svg", "pdf", "png"),
        dpi=600,
        bbox_inches="tight",
    )
    plt.close(fig)


fig, ax = plt.subplots(figsize=(11, 4))
ax.set(xlim=(0, 11), ylim=(0, 4))
ax.axis("off")


def box(x, y, w, h, label):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.08",
            linewidth=1.5,
            edgecolor=skh.C["graphite"],
            facecolor=skh.C["sand"],
            alpha=0.8,
        )
    )
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=11)


def arrow(a, b):
    ax.annotate(
        "",
        xy=b,
        xytext=a,
        arrowprops=dict(arrowstyle="->", color=skh.C["graphite"], lw=1.8),
    )


box(0.15, 1.4, 1.55, 1.1, "Monthly\npurchases")
box(2.25, 1.4, 2, 1.1, "Raw-oil storage\n5 separate stocks")
box(5, 2.65, 2.4, 0.8, "Vegetable refining\n200 t/month")
box(5, 0.45, 2.4, 0.8, "Nonvegetable refining\n250 t/month")
box(8.1, 1.4, 2.65, 1.1, "Blending and sales\n3 ≤ hardness ≤ 6")
arrow((1.8, 1.95), (2.15, 1.95))
arrow((4.35, 2.2), (4.9, 3.0))
arrow((4.35, 1.7), (4.9, 0.85))
arrow((7.5, 3.0), (8.05, 2.2))
arrow((7.5, 0.85), (8.05, 1.7))
ax.text(
    3.25,
    0.8,
    "500 t/oil initially and finally\n0–1,000 t/oil at month-end",
    ha="center",
    va="center",
    fontsize=10,
)
ax.text(9.4, 0.9, "No refined-oil or product storage", ha="center", fontsize=10)
save(fig, "process_flow")

stock = pd.read_csv(ROOT / "results/stock.csv", index_col=0)
fig, ax = plt.subplots(figsize=(8, 4.3), layout="constrained")
for i in stock.columns:
    ax.plot(
        ["Initial", *stock.index], [500, *stock[i].clip(lower=0)], marker="o", label=i
    )
ax.set(xlabel="Inventory observation", ylabel="Raw-oil inventory (t)", ylim=(-30, 1050))
ax.axhline(1000, color=skh.C["graphite"], linestyle="--", linewidth=1.5)
ax.text(0.05, 1018, "Storage limit per oil", fontsize=9)
ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False)
save(fig, "inventory")

scenarios = pd.read_csv(ROOT / "results/scenarios.csv").set_index("Scenario")
fig, ax = plt.subplots(figsize=(7, 3.7), layout="constrained")
values = [
    scenarios.loc["Fixed monthly reserves", "Profit (GBP)"],
    scenarios.loc["Reference", "Profit (GBP)"],
]
bars = ax.barh(
    ["Fixed monthly reserves", "Flexible inventory"],
    values,
    color=[skh.C["teal"], skh.C["amber"]],
    height=0.55,
)
ax.bar_label(bars, labels=[f"£{v:,.0f}" for v in values], padding=6)
ax.set(xlabel="Six-month operating profit (£)", xlim=(0, 130000))
ax.ticklabel_format(axis="x", style="plain")
ax.grid(axis="y", visible=False)
save(fig, "inventory_value")
