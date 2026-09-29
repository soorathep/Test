TITLE = "Balanced Assignment of Chemical Distributors"
SOURCE = "Market sharing"
ADAPTATION = "New eight-distributor instance with three balancing measures and a 15 percentage-point feasibility tolerance."
UNITS = "maximum absolute share deviation (fraction)"
PROBLEM = """Allocate each of eight distributors entirely to division D1 or D2. Distributor records (solvent volume, resin volume, delivery points) are (12,8,3), (8,15,4), (15,6,5), (10,12,3), (6,14,2), (14,9,4), (9,11,3), (16,5,6). Volumes are thousand t/year and points are counts. D1 should receive 40% of each total; D2 receives the remainder. Every D1 share must lie between 25% and 55%. Minimize the maximum absolute deviation from the 40% target across the three measures. A distributor cannot be split."""
FORMULATION = r"""Let $x_i\in\{0,1\}$ indicate assignment to D1. For measure $k$, known normalized weights are $w_{ik}=a_{ik}/\sum_j a_{jk}$. Let $E\ge0$.

$$0.25\le\sum_i w_{ik}x_i\le0.55,\qquad -E\le\sum_iw_{ik}x_i-0.4\le E.$$

Minimize $E$. Normalizing each criterion prevents physical units or large totals from dominating the comparison. The result is a minimax MILP; $E=0.01$ means one percentage point, not one percent relative to the target."""
DISCUSSION = """Indivisibility usually prevents every measure from attaining exactly 40%. A small deviation in one metric does not prove the allocation is balanced in the others. Experiment: minimize the sum of absolute deviations and compare which criterion becomes worst."""
# MODEL CODE
import itertools
import pyomo.environ as pyo
from models.v1.common import frame

DATA = [
    (12, 8, 3),
    (8, 15, 4),
    (15, 6, 5),
    (10, 12, 3),
    (6, 14, 2),
    (14, 9, 4),
    (9, 11, 3),
    (16, 5, 6),
]
TOTAL = [sum(row[k] for row in DATA) for k in range(3)]


def build():
    m = pyo.ConcreteModel()
    m.I = pyo.RangeSet(0, 7)
    m.x = pyo.Var(m.I, domain=pyo.Binary)
    m.E = pyo.Var(domain=pyo.NonNegativeReals)
    m.c = pyo.ConstraintList()
    for k in range(3):
        share = sum(DATA[i][k] / TOTAL[k] * m.x[i] for i in m.I)
        m.c.add(share >= 0.25)
        m.c.add(share <= 0.55)
        m.c.add(share - TARGET <= m.E)
        m.c.add(TARGET - share <= m.E)
    m.obj = pyo.Objective(expr=m.E)
    return m


def check(m):
    candidates = []
    for bits in itertools.product([0, 1], repeat=8):
        shares = [
            sum(DATA[i][k] * bits[i] for i in range(8)) / TOTAL[k] for k in range(3)
        ]
        if all(0.25 <= s <= 0.55 for s in shares):
            candidates.append(max(abs(s - TARGET) for s in shares))
    assert abs(pyo.value(m.obj) - min(candidates)) < 1e-6


def tables(m):
    return {
        "assignment": frame(
            [[i + 1, "D1" if pyo.value(m.x[i]) > 0.5 else "D2"] for i in m.I],
            ["Distributor", "Division"],
        ),
        "shares": frame(
            [
                [
                    name,
                    100 * sum(DATA[i][k] * pyo.value(m.x[i]) for i in m.I) / TOTAL[k],
                ]
                for k, name in enumerate(["Solvent", "Resin", "Delivery points"])
            ],
            ["Measure", "D1 share (%)"],
        ),
    }


def plot(m):
    return (
        ["Solvent", "Resin", "Delivery points"],
        [
            100 * sum(DATA[i][k] * pyo.value(m.x[i]) for i in m.I) / TOTAL[k]
            for k in range(3)
        ],
        "D1 share (%)",
    )

TARGET=.4
