TITLE = "Choosing Maintenance Months"
SOURCE = "Factory planning 2"
ADAPTATION = "Extends the adapted specialty-chemical plant in Chapter 3. Each of two units has one maintenance month."
UNITS = "thousand USD"
PROBLEM = """Use the margins, processing times, sales limits, storage costs, and boundary stocks in Chapter 3. Each month has a base capacity of 120 reactor hours and 100 finishing hours. Reactor maintenance removes 40 h in exactly one month; finishing maintenance removes 20 h in exactly one month. Choose the two maintenance months and the production plan jointly. Maintenance of both units in the same month is permitted. The original Chapter 3 schedule is reactor maintenance in month 2 and finishing maintenance in month 3."""
FORMULATION = r"""Retain the Chapter 3 LP and introduce binary $y_{rt}$ to indicate maintenance of unit $r$ in month $t$. Replace fixed capacity by

$$\sum_i a_{ri}x_{it}\le C_r^0-L_r y_{rt},\qquad \sum_t y_{rt}=1.$$

$L_r$ is the loss in available operating hours, not the whole monthly capacity. The stock, sales, and profit equations are unchanged. This MILP contains the original maintenance schedule as a feasible choice, so its optimal profit cannot be lower."""
DISCUSSION = """Maintenance flexibility has a value only through the production and inventory decisions it enables. It does not create extra total operating hours over the horizon. Experiment: prohibit simultaneous maintenance with a monthly sum of maintenance binaries at most one, then measure the lost flexibility."""
# MODEL CODE
import pyomo.environ as pyo
from models import problem03 as base
from models.common import frame, solve


def build():
    m = base.build()
    m.capacity.deactivate()
    m.maintenance = pyo.Var(["reactor", "finishing"], m.T, domain=pyo.Binary)
    m.once = pyo.Constraint(
        ["reactor", "finishing"],
        rule=lambda m, r: sum(m.maintenance[r, t] for t in m.T) == 1,
    )
    m.adjusted = pyo.Constraint(
        ["reactor", "finishing"],
        m.T,
        rule=lambda m, r, t: (
            sum(base.HOURS[r][j] * m.make[i, t] for j, i in enumerate(base.PRODUCTS))
            <= ({"reactor": 120, "finishing": 100}[r])
            - ({"reactor": 40, "finishing": 20}[r]) * m.maintenance[r, t]
        ),
    )
    return m


def check(m):
    base.check(m)
    fixed = solve(base.build())
    assert pyo.value(m.obj) >= pyo.value(fixed.obj) - 1e-6


def tables(m):
    answer = base.tables(m)
    answer["maintenance"] = frame(
        [
            [r, t + 1]
            for r in ["reactor", "finishing"]
            for t in m.T
            if pyo.value(m.maintenance[r, t]) > 0.5
        ],
        ["Unit", "Maintenance month"],
    )
    fixed = solve(base.build())
    answer["comparison"] = frame(
        [
            ["Fixed schedule", pyo.value(fixed.obj)],
            ["Optimized schedule", pyo.value(m.obj)],
        ],
        ["Policy", "Contribution (thousand USD)"],
    )
    return answer


def plot(m):
    f = solve(base.build())
    return (
        ["Fixed schedule", "Optimized schedule"],
        [pyo.value(f.obj), pyo.value(m.obj)],
        "Contribution (thousand USD)",
    )
