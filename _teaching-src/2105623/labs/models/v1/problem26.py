TITLE = "Repair-Capacity Investment with Precedence"
SOURCE = "Car rental 2"
ADAPTATION = "Extends the adapted cyclic rental model in Chapter 25 with three indivisible repair-capacity options."
UNITS = "USD per three-day cycle"
PROBLEM = """Use all fleet, demand, return, cost, and timing data from Chapter 25. Option 1 adds one repair/car per day at depot A for 12 USD per cycle. Option 2 adds a further one repair/car per day at A for 8 USD per cycle, but requires option 1. Option 3 adds one repair/car per day at B for 10 USD per cycle. At most two options can be selected. Costs are cycle-equivalent investment charges. Re-optimize the rental and repair plan with investment choices to maximize net cycle profit."""
FORMULATION = r"""Add binary investments $z_1,z_2,z_3$, with $z_2\le z_1$ and $z_1+z_2+z_3\le2$. Replace repair-capacity bounds by

$$v_{At}\le2+z_1+z_2,\quad v_{Bt}\le1+z_3,\quad v_{Ct}\le1.$$

Subtract $12z_1+8z_2+10z_3$ from the Chapter 25 objective. All fleet balances stay active. The second-stage expansion is available only after the first expansion at A is selected; there is no fractional purchase of an option."""
DISCUSSION = """The value of a repair expansion depends on the return network, queues, and demand, not simply its added capacity. A low-price option can be unattractive when it expands the wrong depot. Experiment: compare investment values before and after increasing depot C’s demand."""
# MODEL CODE
import pyomo.environ as pyo
from models.v1 import problem25 as base
from models.v1.common import frame, solve


def build():
    m = base.build()
    m.repaircap.deactivate()
    m.obj.deactivate()
    m.z = pyo.Var(range(3), domain=pyo.Binary)
    m.precedence = pyo.Constraint(expr=m.z[1] <= m.z[0])
    m.limit = pyo.Constraint(expr=sum(m.z[k] for k in range(3)) <= 2)
    m.newcap = pyo.Constraint(
        m.I,
        m.T,
        rule=lambda m, i, t: (
            m.v[i, t]
            <= base.CAP[i] + (m.z[0] + m.z[1] if i == 0 else m.z[2] if i == 1 else 0)
        ),
    )
    m.profit = pyo.Objective(
        expr=m.obj.expr - INVESTMENT_SCALE * (12 * m.z[0] + 8 * m.z[1] + 10 * m.z[2]), sense=pyo.maximize
    )
    return m


def check(m):
    base.check(m)
    reference = solve(base.build())
    assert pyo.value(m.profit) >= pyo.value(reference.obj) - 1e-6


def tables(m):
    answer = base.tables(m)
    reference = solve(base.build())
    answer["investment"] = frame(
        [[k + 1, pyo.value(m.z[k]), INVESTMENT_SCALE * [12, 8, 10][k]] for k in range(3)],
        ["Option", "Selected", "Cycle charge (USD)"],
    )
    answer["comparison"] = frame(
        [
            ["No expansion", pyo.value(reference.obj)],
            ["Optimal expansion", pyo.value(m.profit)],
        ],
        ["Policy", "Net profit (USD/cycle)"],
    )
    return answer


def plot(m):
    a = solve(base.build())
    return (
        ["No expansion", "Optimal expansion"],
        [pyo.value(a.obj), pyo.value(m.profit)],
        "Net profit (USD/cycle)",
    )

INVESTMENT_SCALE=1
