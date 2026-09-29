TITLE = "Refinery Process and Blend Optimization"
SOURCE = "Refinery optimisation"
ADAPTATION = "New mass-based two-crude teaching instance, with simplified distillation, reforming, cracking, and two final products."
UNITS = "thousand USD/day"
PROBLEM = """A refinery buys crude A and B at 0.32 and 0.28 thousand USD/t, with daily availability 100 and 80 t. Distillation capacity is 150 t/day. Mass yields (naphtha, gas oil, residue) are (0.5,0.3,0.2) for A and (0.3,0.5,0.2) for B. Naphtha can be blended directly into gasoline with octane index 80 or reformed with mass yield 0.8 to octane-100 reformate. Gas oil can become fuel oil directly or be cracked with yields 0.4 gasoline (octane 95), 0.5 fuel oil, and 0.1 loss. Reforming and cracking feed capacities are 40 and 35 t/day; costs are 0.03 and 0.02 thousand USD/t feed. Residue joins fuel oil. Gasoline must have mass-weighted octane index at least 90. Gasoline and fuel-oil sales limits are 90 and 100 t/day, with prices 0.65 and 0.30 thousand USD/t. All material must be routed or sold; only stated conversion losses leave the system. Maximize daily margin. Linear mass blending of octane is a deliberate teaching approximation."""
FORMULATION = r"""Crude feeds $c_A,c_B$, reformer feed $r$, cracker feed $k$, direct naphtha $n$, and direct gas oil $d$ are nonnegative t/day. Product sales are $G,F$.

$$n+r=.5c_A+.3c_B,\quad d+k=.3c_A+.5c_B,$$
$$G=n+.8r+.4k,\quad F=d+.5k+.2(c_A+c_B),$$
$$80n+100(.8r)+95(.4k)\ge90G.$$

Bound crude feeds by availability, total crude by 150, $r\le40$, $k\le35$, $G\le90$, and $F\le100$. Maximize $0.65G+0.30F-0.32c_A-0.28c_B-0.03r-0.02k$. All terms are thousand USD/day. This LP separates unit feed from unit output so conversion losses are not counted twice."""
DISCUSSION = """The reformer improves quality but loses mass and incurs cost. More gasoline is therefore not automatically more profitable. The total crude input must equal product sales plus reforming and cracking losses. Experiment: increase gasoline octane to 92 and compare feed selection and conversion intensity."""
# MODEL CODE
import pyomo.environ as pyo
from models.v1.common import frame


def build():
    m = pyo.ConcreteModel()
    m.x = pyo.Var(["A", "B", "r", "k", "n", "d", "G", "F"], domain=pyo.NonNegativeReals)
    x = m.x
    m.c = pyo.ConstraintList()
    for key, limit in {"A": 100, "B": 80, "r": 40, "k": 35, "G": GASOLINE_CAP, "F": 100}.items():
        x[key].setub(limit)
    m.c.add(x["A"] + x["B"] <= 150)
    m.c.add(x["n"] + x["r"] == 0.5 * x["A"] + 0.3 * x["B"])
    m.c.add(x["d"] + x["k"] == 0.3 * x["A"] + 0.5 * x["B"])
    m.c.add(x["G"] == x["n"] + 0.8 * x["r"] + 0.4 * x["k"])
    m.c.add(x["F"] == x["d"] + 0.5 * x["k"] + 0.2 * (x["A"] + x["B"]))
    m.c.add(80 * x["n"] + 80 * x["r"] + 38 * x["k"] >= 90 * x["G"])
    m.obj = pyo.Objective(
        expr=0.65 * x["G"]
        + 0.30 * x["F"]
        - 0.32 * x["A"]
        - 0.28 * x["B"]
        - 0.03 * x["r"]
        - 0.02 * x["k"],
        sense=pyo.maximize,
    )
    return m


def check(m):
    x = {k: pyo.value(v) for k, v in m.x.items()}
    assert abs(x["A"] + x["B"] - x["G"] - x["F"] - 0.2 * x["r"] - 0.1 * x["k"]) < 1e-6


def tables(m):
    labels = {
        "A": "Crude A",
        "B": "Crude B",
        "r": "Reformer feed",
        "k": "Cracker feed",
        "n": "Direct naphtha",
        "d": "Direct gas oil",
        "G": "Gasoline",
        "F": "Fuel oil",
    }
    return {
        "flows": frame(
            [[labels[k], pyo.value(v)] for k, v in m.x.items()],
            ["Stream", "Flow (t/day)"],
        )
    }


def plot(m):
    return (
        ["Crude A", "Crude B", "Gasoline", "Fuel oil"],
        [pyo.value(m.x[k]) for k in ["A", "B", "G", "F"]],
        "Flow (t/day)",
    )

GASOLINE_CAP=90
