TITLE = "Dairy Product Pricing with Resource Limits"
SOURCE = "Agricultural pricing"
ADAPTATION = "New four-product instance with finite price menus. This is an exact menu-selection MILP, not a solution of the source continuous-price nonlinear model."
UNITS = "thousand USD/day"
PROBLEM = """Price milk, butter, cheese A, and cheese B. Baseline prices are (1,4,5,4) thousand USD/t and baseline demands are (100,10,15,10) t/day. Each price must be 0.8, 1.0, or 1.2 times its baseline. Own-price elasticities are (0.4,1.5,1.1,0.4). Demand for product i is its baseline times [1−elasticity_i×(relative price_i−1)]. Each cheese also gains 0.1 times its baseline demand times the other cheese’s relative price increase. Fat fractions are (0.04,0.80,0.35,0.25), and dry-matter fractions are (0.09,0.02,0.30,0.40). Daily available fat and dry matter are 22 and 22 t. All induced demand must be supplied. The price index cannot exceed the baseline: the cost of the baseline basket at new prices must not increase. Maximize daily revenue. Production cost and water availability are outside this exercise."""
FORMULATION = r"""Enumerate the 81 price combinations $k$. For each, calculate prices $p_{ik}$, induced demands $d_{ik}$, revenue $R_k=\sum_i p_{ik}d_{ik}$, fat $F_k$, dry matter $M_k$, and baseline-basket expense $B_k$. Binary $y_k$ selects exactly one combination:

$$\sum_ky_k=1,\quad\sum_kF_ky_k\le22,\quad\sum_kM_ky_k\le22,\quad\sum_kB_ky_k\le B_0,$$
$$\max\sum_kR_ky_k.$$

All menu-dependent quantities are constants, so no product of decision variables remains. This formulation is exact for the stated finite menu only. Increasing menu resolution does not by itself prove global optimality for a continuous pricing model."""
DISCUSSION = """Cross-price effects couple the cheese products, while the price index uses baseline quantities rather than the new demand quantities. Revenue is not profit. Experiment: remove the price-index limit and compare both revenue and resource use; then refine the price menu and assess how sensitive the result is to discretization."""
# MODEL CODE
import itertools
import pyomo.environ as pyo
from models.common import frame

P = [1, 4, 5, 4]
Q = [100, 10, 15, 10]
E = [0.4, 1.5, 1.1, 0.4]
FAT = [0.04, 0.8, 0.35, 0.25]
DRY = [0.09, 0.02, 0.3, 0.4]
MENUS = list(itertools.product([0.8, 1, 1.2], repeat=4))


def metrics(k):
    relative = MENUS[k]
    price = [P[i] * relative[i] for i in range(4)]
    demand = [
        Q[i]
        * (
            1
            - E[i] * (relative[i] - 1)
            + (0.1 * (relative[5 - i] - 1) if i in [2, 3] else 0)
        )
        for i in range(4)
    ]
    return (
        price,
        demand,
        sum(price[i] * demand[i] for i in range(4)),
        sum(FAT[i] * demand[i] for i in range(4)),
        sum(DRY[i] * demand[i] for i in range(4)),
        sum(price[i] * Q[i] for i in range(4)),
    )


def build():
    m = pyo.ConcreteModel()
    m.y = pyo.Var(range(81), domain=pyo.Binary)
    m.one = pyo.Constraint(expr=sum(m.y[k] for k in range(81)) == 1)
    m.c = pyo.ConstraintList()
    for field, limit in [(3, 22), (4, 22), (5, sum(P[i] * Q[i] for i in range(4)))]:
        m.c.add(sum(metrics(k)[field] * m.y[k] for k in range(81)) <= limit)
    m.obj = pyo.Objective(
        expr=sum(metrics(k)[2] * m.y[k] for k in range(81)), sense=pyo.maximize
    )
    return m


def check(m):
    possible = [
        metrics(k)[2]
        for k in range(81)
        if metrics(k)[3] <= 22 + 1e-9
        and metrics(k)[4] <= 22 + 1e-9
        and metrics(k)[5] <= 255 + 1e-9
    ]
    assert abs(max(possible) - pyo.value(m.obj)) < 1e-6


def tables(m):
    k = next(k for k in range(81) if pyo.value(m.y[k]) > 0.5)
    p, d, r, f, s, b = metrics(k)
    return {
        "pricing": frame(
            [
                [name, p[i], d[i], p[i] * d[i]]
                for i, name in enumerate(["Milk", "Butter", "Cheese A", "Cheese B"])
            ],
            [
                "Product",
                "Price (thousand USD/t)",
                "Demand (t/day)",
                "Revenue (thousand USD/day)",
            ],
        ),
        "resources": frame(
            [
                ["Fat (t/day)", f, 22],
                ["Dry matter (t/day)", s, 22],
                ["Basket cost (thousand USD)", b, 255],
            ],
            ["Measure", "Use", "Limit"],
        ),
    }


def plot(m):
    k = next(k for k in range(81) if pyo.value(m.y[k]) > 0.5)
    return ["Milk", "Butter", "Cheese A", "Cheese B"], metrics(k)[1], "Demand (t/day)"
