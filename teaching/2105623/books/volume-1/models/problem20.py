TITLE = "Depot Location and Capacity Expansion"
SOURCE = "Depot location (distribution 2)"
ADAPTATION = "Extends Chapter 19 with facility fixed costs, an optional D2 expansion, and a two-depot limit."
UNITS = "USD/day"
PROBLEM = """Use the complete shipping data from Chapter 19. Choose which depots to operate, paying daily fixed costs D1=100, D2=80, D3=60 USD. At most two depots may operate. D2 can be expanded by 20 t/day at an additional 30 USD/day, only if it is open. Other capacities are unchanged. Minimize fixed, expansion, and shipping costs while meeting all customer demands. Fixed costs are daily equivalents of capital and operating commitments; no separate investment horizon is modeled."""
FORMULATION = r"""Add opening binaries $y_d$ and expansion binary $e$. Replace depot capacities by

$$\sum_cg_{dc}\le V_d y_d+20e\,\mathbf1_{d=2},\quad e\le y_2,\quad\sum_dy_d\le2.$$

Minimize the transportation objective from Chapter 19 plus $100y_1+80y_2+60y_3+30e$. A closed depot has zero flow. The expansion term is added capacity, not a multiplication of decision variables, so the formulation remains linear."""
DISCUSSION = """A fixed charge creates a tradeoff between a more extensive network and cheaper delivery routes. Total capacity alone is necessary but does not explain the best geography. Experiment: remove the two-depot limit and compare the cost-saving value of the third location."""
# MODEL CODE
import pyomo.environ as pyo
from models import problem19 as base
from models.common import frame


def build():
    m = base.build()
    m.cap.deactivate()
    m.obj.deactivate()
    m.y = pyo.Var(m.D, domain=pyo.Binary)
    m.e = pyo.Var(domain=pyo.Binary)
    m.newcap = pyo.Constraint(
        m.D,
        rule=lambda m, d: (
            sum(m.g[d, c] for c in m.C)
            <= base.VD[d] * m.y[d] + (20 * m.e if d == 1 else 0)
        ),
    )
    m.requires = pyo.Constraint(expr=m.e <= m.y[1])
    m.count = pyo.Constraint(expr=sum(m.y[d] for d in m.D) <= 2)
    m.cost = pyo.Objective(
        expr=m.obj.expr + sum([100, 80, 60][d] * m.y[d] for d in m.D) + 30 * m.e
    )
    return m


def check(m):
    base.check(m)
    for d in m.D:
        if pyo.value(m.y[d]) < 0.5:
            assert sum(pyo.value(m.g[d, c]) for c in m.C) < 1e-6


def tables(m):
    answer = base.tables(m)
    answer["facilities"] = frame(
        [
            [
                f"D{d + 1}",
                pyo.value(m.y[d]),
                pyo.value(m.e) if d == 1 else 0,
                sum(pyo.value(m.g[d, c]) for c in m.C),
            ]
            for d in m.D
        ],
        ["Depot", "Open", "Expanded", "Throughput (t/day)"],
    )
    return answer


def plot(m):
    return base.plot(m)
