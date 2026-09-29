TITLE = "Chemical Distribution Through Depots"
SOURCE = "Distribution 1"
ADAPTATION = "New two-plant, three-depot, four-customer transportation instance. All shipments pass through a depot."
UNITS = "USD/day"
PROBLEM = """Plants P1 and P2 can supply at most 60 and 70 t/day. Depots D1,D2,D3 have throughput limits 45,40,50 t/day. Customer demands C1–C4 are 20,25,30,20 t/day and must all be met. Plant-to-depot shipping costs (D1,D2,D3) are P1:(2,4,5), P2:(5,2,3) USD/t. Depot-to-customer costs (C1,C2,C3,C4) are D1:(2,3,6,7), D2:(5,2,3,4), D3:(6,5,2,2) USD/t. No losses or inventory are allowed. Minimize total shipping cost."""
FORMULATION = r"""Let $f_{pd}\ge0$ be plant-to-depot flow and $g_{dc}\ge0$ be depot-to-customer flow in t/day. Minimize $\sum_{pd}c_{pd}f_{pd}+\sum_{dc}k_{dc}g_{dc}$ subject to

$$\sum_df_{pd}\le U_p,\quad \sum_pf_{pd}=\sum_cg_{dc},\quad\sum_cg_{dc}\le V_d,\quad\sum_dg_{dc}=D_c.$$

The depot balance forbids material creation or disappearance. Plant capacity is an upper bound, while customer demand is an equality. This is a transshipment LP with two transport legs."""
DISCUSSION = """A cheap last-mile route can be unattractive after including inbound depot cost. Depot capacity can redirect flows across the whole network. Experiment: add 10 t/day capacity at each depot separately and report which expansion reduces cost the most."""
# MODEL CODE
import pyomo.environ as pyo
from models.v1.common import frame

UP = [60, 70]
VD = [45, 40, 50]
DEMAND = [20, 25, 30, 20]
C = [[2, 4, 5], [5, 2, 3]]
K = [[2, 3, 6, 7], [5, 2, 3, 4], [6, 5, 2, 2]]


def build():
    m = pyo.ConcreteModel()
    m.P = pyo.RangeSet(0, 1)
    m.D = pyo.RangeSet(0, 2)
    m.C = pyo.RangeSet(0, 3)
    m.f = pyo.Var(m.P, m.D, domain=pyo.NonNegativeReals)
    m.g = pyo.Var(m.D, m.C, domain=pyo.NonNegativeReals)
    m.plant = pyo.Constraint(
        m.P, rule=lambda m, p: sum(m.f[p, d] for d in m.D) <= UP[p]
    )
    m.balance = pyo.Constraint(
        m.D,
        rule=lambda m, d: sum(m.f[p, d] for p in m.P) == sum(m.g[d, c] for c in m.C),
    )
    m.cap = pyo.Constraint(m.D, rule=lambda m, d: sum(m.g[d, c] for c in m.C) <= VD[d])
    m.demand = pyo.Constraint(
        m.C, rule=lambda m, c: sum(m.g[d, c] for d in m.D) == DEMAND[c]
    )
    m.obj = pyo.Objective(
        expr=sum(C[p][d] * m.f[p, d] for p in m.P for d in m.D)
        + sum(K[d][c] * m.g[d, c] for d in m.D for c in m.C)
    )
    return m


def check(m):
    assert abs(sum(pyo.value(m.f[p, d]) for p in m.P for d in m.D) - sum(DEMAND)) < 1e-6
    for d in m.D:
        assert (
            abs(
                sum(pyo.value(m.f[p, d]) for p in m.P)
                - sum(pyo.value(m.g[d, c]) for c in m.C)
            )
            < 1e-6
        )


def tables(m):
    return {
        "shipments": frame(
            [
                [f"P{p + 1}", f"D{d + 1}", pyo.value(m.f[p, d])]
                for p in m.P
                for d in m.D
                if pyo.value(m.f[p, d]) > 1e-6
            ]
            + [
                [f"D{d + 1}", f"C{c + 1}", pyo.value(m.g[d, c])]
                for d in m.D
                for c in m.C
                if pyo.value(m.g[d, c]) > 1e-6
            ],
            ["From", "To", "Flow (t/day)"],
        )
    }


def plot(m):
    return (
        ["D1", "D2", "D3"],
        [sum(pyo.value(m.g[d, c]) for c in m.C) for d in m.D],
        "Depot throughput (t/day)",
    )
