TITLE = "Thermal Generation and Reserve Capacity"
SOURCE = "Tariff rates (power generation)"
ADAPTATION = "New three-generator, three-period daily dispatch instance. Initial units are off and end-of-day shutdown is not imposed."
UNITS = "USD/day"
PROBLEM = """An industrial park requires 50, 140, and 100 MW in three consecutive 8-hour periods. Thermal units A,B,C have minimum outputs (20,20,30) MW, maximum outputs (60,60,100) MW, fixed online costs (30,30,60) USD/h, marginal energy costs (2,2.5,3) USD/MWh, and startup costs (200,200,150) USD/start. All units are off before period 1. Each period must have online maximum capacity at least 115% of demand, although dispatched power equals demand. No minimum up/down times or ramp restrictions are imposed. Choose online states, startups, and dispatch to minimize total daily cost. There is no terminal online-state requirement."""
FORMULATION = r"""Power $p_{gt}\ge0$ is continuous MW, online state $y_{gt}$ and startup $u_{gt}$ are binary. Initial state is $y_{g0}=0$.

$$P_g^{\min}y_{gt}\le p_{gt}\le P_g^{\max}y_{gt},\quad\sum_gp_{gt}=D_t,\quad\sum_gP_g^{\max}y_{gt}\ge1.15D_t.$$
$$u_{gt}\ge y_{gt}-y_{g,t-1},\quad u_{gt}\le y_{gt},\quad u_{gt}\le1-y_{g,t-1}.$$
$$\min\sum_{gt}\left[8(F_gy_{gt}+c_gp_{gt})+S_gu_{gt}\right].$$

The factor 8 converts power and hourly fixed costs into period energy costs. Reserve is unused online capability; it is not extra scheduled generation. This MILP models commitment and dispatch jointly."""
DISCUSSION = """A unit may be online to provide reserve while another supplies cheaper energy. Startup charges couple consecutive periods. A reserve-policy cost is a re-solved scenario difference, not a universal electricity tariff. Experiment: reduce reserve to zero and compare daily cost and the commitment schedule."""
# MODEL CODE
import pyomo.environ as pyo
from models.common import frame, solve

MIN = [20, 20, 30]
MAX = [60, 60, 100]
FIX = [30, 30, 60]
COST = [2, 2.5, 3]
START = [200, 200, 150]
DEMAND = [50, 140, 100]


def build(reserve=0.15):
    m = pyo.ConcreteModel()
    m.G = pyo.RangeSet(0, 2)
    m.T = pyo.RangeSet(0, 2)
    m.p = pyo.Var(m.G, m.T, domain=pyo.NonNegativeReals)
    m.y = pyo.Var(m.G, m.T, domain=pyo.Binary)
    m.u = pyo.Var(m.G, m.T, domain=pyo.Binary)
    m.c = pyo.ConstraintList()
    for g in m.G:
        for t in m.T:
            previous = m.y[g, t - 1] if t else 0
            m.c.add(m.p[g, t] >= MIN[g] * m.y[g, t])
            m.c.add(m.p[g, t] <= MAX[g] * m.y[g, t])
            m.c.add(m.u[g, t] >= m.y[g, t] - previous)
            m.c.add(m.u[g, t] <= m.y[g, t])
            m.c.add(m.u[g, t] <= 1 - previous)
    m.balance = pyo.Constraint(
        m.T, rule=lambda m, t: sum(m.p[g, t] for g in m.G) == DEMAND[t]
    )
    m.reserve = pyo.Constraint(
        m.T,
        rule=lambda m, t: (
            sum(MAX[g] * m.y[g, t] for g in m.G) >= (1 + reserve) * DEMAND[t]
        ),
    )
    m.obj = pyo.Objective(
        expr=sum(
            8 * (FIX[g] * m.y[g, t] + COST[g] * m.p[g, t]) + START[g] * m.u[g, t]
            for g in m.G
            for t in m.T
        )
    )
    return m


def check(m):
    for t in m.T:
        assert abs(sum(pyo.value(m.p[g, t]) for g in m.G) - DEMAND[t]) < 1e-6


def tables(m):
    no_reserve = solve(build(0))
    return {
        "dispatch": frame(
            [
                [
                    t + 1,
                    "ABC"[g],
                    pyo.value(m.y[g, t]),
                    pyo.value(m.u[g, t]),
                    pyo.value(m.p[g, t]),
                ]
                for t in m.T
                for g in m.G
            ],
            ["Period", "Unit", "Online", "Startup", "Power (MW)"],
        ),
        "reserve_cost": frame(
            [
                ["15% reserve", pyo.value(m.obj)],
                ["No reserve", pyo.value(no_reserve.obj)],
            ],
            ["Policy", "Daily cost (USD)"],
        ),
    }


def plot(m):
    return (
        ["A", "B", "C"],
        [8 * sum(pyo.value(m.p[g, t]) for t in m.T) for g in m.G],
        "Daily energy (MWh)",
    )
