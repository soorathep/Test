TITLE = "Open-Pit Block Selection"
SOURCE = "Opencast mining"
ADAPTATION = "New 14-block, three-level mine with explicit support dependencies; replaces the source geometry and financial data."
UNITS = "thousand USD"
PROBLEM = """Consider a three-level pit. The surface is a 3×3 grid labeled S00 through S22; the middle level is a 2×2 grid M00 through M11; the bottom block is B. Extracting middle block Mij requires surface blocks Sij, S(i+1)j, Si(j+1), and S(i+1)(j+1). Extracting B requires all four middle blocks. Surface-block net values (revenue minus extraction cost), row by row, are [-3,-4,-2], [-5,-3,-4], [-2,-4,-3] thousand USD. Middle net values are [6,8], [5,7], and the bottom value is 18. Choose which blocks to extract to maximize total net value. There is no requirement to extract any block and no production-capacity limit."""
FORMULATION = r"""Binary $x_b$ indicates extraction of block $b$. For each precedence pair $(b,p)$, where upper block $p$ must be removed before lower block $b$,

$$x_b\le x_p,\qquad \max\sum_b v_bx_b.$$

The objective includes negative-value overburden. A profitable deep block cannot be selected independently of the material above it. This is a maximum-weight closure formulation; the MILP is small enough to verify by enumerating all subsets."""
DISCUSSION = """A negative-value block can be part of the optimal pit because it enables valuable deeper extraction. Selecting only positive-value blocks violates the slope dependencies. Experiment: lower the bottom-block value until it is no longer worth opening the deepest level."""
# MODEL CODE
import itertools
import pyomo.environ as pyo
from models.common import frame

VALUES = {
    f"S{i}{j}": v
    for i, row in enumerate([[-3, -4, -2], [-5, -3, -4], [-2, -4, -3]])
    for j, v in enumerate(row)
}
VALUES.update(
    {f"M{i}{j}": v for i, row in enumerate([[6, 8], [5, 7]]) for j, v in enumerate(row)}
)
VALUES["B"] = 18
PRECEDENCE = [
    (f"M{i}{j}", f"S{i + di}{j + dj}")
    for i in range(2)
    for j in range(2)
    for di, dj in itertools.product([0, 1], repeat=2)
] + [("B", f"M{i}{j}") for i, j in itertools.product(range(2), repeat=2)]


def build():
    m = pyo.ConcreteModel()
    m.x = pyo.Var(list(VALUES), domain=pyo.Binary)
    m.slope = pyo.Constraint(PRECEDENCE, rule=lambda m, b, p: m.x[b] <= m.x[p])
    m.obj = pyo.Objective(
        expr=sum(v * m.x[b] for b, v in VALUES.items()), sense=pyo.maximize
    )
    return m


def check(m):
    names = list(VALUES)
    best = 0
    for bits in itertools.product([0, 1], repeat=len(names)):
        chosen = dict(zip(names, bits))
        if all(chosen[b] <= chosen[p] for b, p in PRECEDENCE):
            best = max(best, sum(VALUES[b] * chosen[b] for b in names))
    assert abs(pyo.value(m.obj) - best) < 1e-6


def tables(m):
    return {
        "blocks": frame(
            [[b, v, round(pyo.value(m.x[b]))] for b, v in VALUES.items()],
            ["Block", "Net value (thousand USD)", "Extract"],
        )
    }


def plot(m):
    return (
        ["Surface", "Middle", "Bottom"],
        [
            sum(pyo.value(m.x[b]) for b in VALUES if b.startswith(prefix))
            for prefix in ["S", "M", "B"]
        ],
        "Selected blocks",
    )
