TITLE = "Cyclic Rental Fleet and Repair Planning"
SOURCE = "Car rental 1"
ADAPTATION = "New three-depot, three-day cyclic instance with one-day rentals, deterministic return fractions, and a repair-state balance."
UNITS = "USD per three-day cycle"
PROBLEM = """Three depots A,B,C rent one-day vehicles in a repeating three-day cycle. Rental demand caps by day (A,B,C) are (15,12,10), (10,18,12), (12,10,18). Each rental contributes 25 USD before repair, transfer, and fleet costs. Return fractions from A are (0.7,0.2,0.1), from B (0.2,0.6,0.2), and from C (0.1,0.2,0.7). Ten percent of returns are damaged; 90% are immediately usable next morning. Damaged cars enter a separate queue and can only start repair after arrival. Repairs take one day and cost 2 USD/car, with daily depot capacities (2,1,1). Undamaged transfers take one day and cost 4 USD between A/B or B/C and 6 USD between A/C. At each morning, choose rentals, transfers, and repairs from the stocks then available. Fleet ownership costs 4 USD/car/day. Choose steady-state stocks and operations to maximize cycle profit. Fractional expected vehicle counts are allowed; no rounding is claimed to preserve feasibility."""
FORMULATION = r"""Morning usable and damaged stocks are $s_{it},d_{it}\ge0$. Rentals $r_{it}$, repairs $v_{it}$, and transfers $f_{ijt}$ are nonnegative. For cyclic successor $t^+$,

$$r_{it}+\sum_{j\ne i}f_{ijt}\le s_{it},\quad v_{it}\le d_{it},\quad v_{it}\le C_i,$$
$$s_{i,t^+}=s_{it}-r_{it}-\sum_jf_{ijt}+\sum_jf_{jit}+0.9\sum_jP_{ji}r_{jt}+v_{it},$$
$$d_{i,t^+}=d_{it}-v_{it}+0.1\sum_jP_{ji}r_{jt}.$$

Demand bounds apply to rentals. Fleet size $N=\sum_i(s_{i0}+d_{i0})$ is constant under the balances. Maximize $25\sum r-2\sum v-\sum c_{ij}f_{ijt}-12N$. Repair output and transfer arrivals become usable the next morning. The model is an LP for expected fleet flows."""
DISCUSSION = """Repair queues consume fleet capital as well as repair capacity. Ignoring the damaged stock would make cars reappear without a delay. Cyclic boundary conditions remove a privileged start day but assume the demand pattern repeats. Experiment: double one depot’s repair capacity and measure the value before adding a fixed investment charge."""
# MODEL CODE
import pyomo.environ as pyo
from models.common import frame

DEMAND = [[15, 12, 10], [10, 18, 12], [12, 10, 18]]
P = [[0.7, 0.2, 0.1], [0.2, 0.6, 0.2], [0.1, 0.2, 0.7]]
CAP = [2, 1, 1]


def build():
    m = pyo.ConcreteModel()
    m.I = pyo.RangeSet(0, 2)
    m.T = pyo.RangeSet(0, 2)
    arcs = [(i, j, t) for i in m.I for j in m.I if i != j for t in m.T]
    m.s = pyo.Var(m.I, m.T, domain=pyo.NonNegativeReals)
    m.d = pyo.Var(m.I, m.T, domain=pyo.NonNegativeReals)
    m.r = pyo.Var(m.I, m.T, domain=pyo.NonNegativeReals)
    m.v = pyo.Var(m.I, m.T, domain=pyo.NonNegativeReals)
    m.f = pyo.Var(arcs, domain=pyo.NonNegativeReals)
    m.c = pyo.ConstraintList()
    for i in m.I:
        for t in m.T:
            incoming = sum(P[j][i] * m.r[j, t] for j in m.I)
            outgoing = sum(m.f[i, j, t] for j in m.I if j != i)
            inbound = sum(m.f[j, i, t] for j in m.I if j != i)
            m.c.add(m.r[i, t] + outgoing <= m.s[i, t])
            m.c.add(m.r[i, t] <= DEMAND[t][i])
            m.c.add(m.v[i, t] <= m.d[i, t])
            m.c.add(
                m.s[i, (t + 1) % 3]
                == m.s[i, t]
                - m.r[i, t]
                - outgoing
                + inbound
                + 0.9 * incoming
                + m.v[i, t]
            )
            m.c.add(m.d[i, (t + 1) % 3] == m.d[i, t] - m.v[i, t] + 0.1 * incoming)
    m.repaircap = pyo.Constraint(m.I, m.T, rule=lambda m, i, t: m.v[i, t] <= CAP[i])
    m.fleet = pyo.Expression(expr=sum(m.s[i, 0] + m.d[i, 0] for i in m.I))
    m.obj = pyo.Objective(
        expr=25 * sum(m.r[i, t] for i in m.I for t in m.T)
        - 2 * sum(m.v[i, t] for i in m.I for t in m.T)
        - sum((4 if abs(i - j) == 1 else 6) * m.f[i, j, t] for i, j, t in arcs)
        - 12 * m.fleet,
        sense=pyo.maximize,
    )
    return m


def check(m):
    for t in m.T:
        assert (
            abs(sum(pyo.value(m.s[i, t] + m.d[i, t]) for i in m.I) - pyo.value(m.fleet))
            < 1e-6
        )
    assert (
        abs(sum(pyo.value(m.v[i, t] - 0.1 * m.r[i, t]) for i in m.I for t in m.T))
        < 1e-6
    )


def tables(m):
    return {
        "fleet_plan": frame(
            [
                [
                    t + 1,
                    "ABC"[i],
                    *[pyo.value(getattr(m, k)[i, t]) for k in ["s", "d", "r", "v"]],
                ]
                for t in m.T
                for i in m.I
            ],
            ["Day", "Depot", "Usable stock", "Damaged stock", "Rentals", "Repairs"],
        ),
        "transfers": frame(
            [
                [t + 1, "ABC"[i], "ABC"[j], pyo.value(m.f[i, j, t])]
                for i, j, t in m.f
                if pyo.value(m.f[i, j, t]) > 1e-6
            ],
            ["Day", "From", "To", "Vehicles"],
        ),
    }


def plot(m):
    return (
        ["Day 1", "Day 2", "Day 3"],
        [sum(pyo.value(m.r[i, t]) for i in m.I) for t in m.T],
        "Vehicles rented (expected count)",
    )
