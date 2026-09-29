TITLE = "Production Planning with Scheduled Maintenance"
SOURCE = "Factory planning 1"
ADAPTATION = "New three-product, three-month teaching instance for a specialty chemical plant; replaces the seven-product numerical instance."
UNITS = "thousand USD"
PROBLEM = """A specialty chemical plant produces grades A, B, and C over three months. Processing contribution margins (before holding cost) are 8, 10, and 12 thousand USD/t. Reactor hours per tonne are 2, 3, and 4; finishing hours are 3, 2, and 2. Monthly reactor availability is 120, 80, 120 h and finishing availability is 100, 100, 80 h, after scheduled maintenance. Sales limits (A,B,C) are (20,15,10), (15,20,15), (20,15,20) t. Initial stocks are zero, final stocks must be 5 t per grade, and month-end storage is limited to 15 t per grade. Holding cost is 0.5 thousand USD/t at every month-end, including month 3. Choose production, sales, and inventories to maximize total contribution. Final stock has no sale or salvage credit in this horizon. There is no requirement to satisfy all sales opportunities."""
FORMULATION = r"""Let $x_{it},z_{it},s_{it}\ge0$ be production, sales, and closing stock (t). Parameters are contribution $p_i$, holding charge $h$, processing hours $a_{ri}$, capacity $C_{rt}$, and sales limit $D_{it}$.

$$\max\sum_{it}(p_i z_{it}-h s_{it}),\qquad s_{i,t-1}+x_{it}=z_{it}+s_{it}.$$

$$\sum_i a_{ri}x_{it}\le C_{rt},\quad z_{it}\le D_{it},\quad0\le s_{it}\le15,\quad s_{i0}=0,\ s_{i3}=5.$$

Production consumes capacity; sales generate contribution. These are distinct variables because inventory can connect months. Capacity is supplied after maintenance, so maintenance decisions are not optimized in this LP."""
DISCUSSION = """A capacity reduction can make earlier production and temporary storage worthwhile even though storage has a positive cost. Sales caps are upper bounds, not demand equalities. Experiment: increase month 2 reactor availability by 10 h and calculate the extra contribution; compare it with the cost of overtime."""
# MODEL CODE
import pyomo.environ as pyo
from models.v1.common import frame

PRODUCTS = ["A", "B", "C"]
MARGIN = {"A": 8, "B": 10, "C": 12}
HOURS = {"reactor": [2, 3, 4], "finishing": [3, 2, 2]}
CAPACITY = {"reactor": [120, 80, 120], "finishing": [100, 100, 80]}
DEMAND = [[20, 15, 10], [15, 20, 15], [20, 15, 20]]


def build():
    m = pyo.ConcreteModel()
    m.I = pyo.Set(initialize=PRODUCTS)
    m.T = pyo.RangeSet(0, 2)
    m.make = pyo.Var(m.I, m.T, domain=pyo.NonNegativeReals)
    m.sell = pyo.Var(m.I, m.T, domain=pyo.NonNegativeReals)
    m.stock = pyo.Var(m.I, m.T, bounds=(0, 15))
    m.balance = pyo.Constraint(
        m.I,
        m.T,
        rule=lambda m, i, t: (
            (m.stock[i, t - 1] if t else 0) + m.make[i, t]
            == m.sell[i, t] + m.stock[i, t]
        ),
    )
    m.demand = pyo.Constraint(
        m.I, m.T, rule=lambda m, i, t: m.sell[i, t] <= DEMAND[t][PRODUCTS.index(i)]
    )
    m.final = pyo.Constraint(m.I, rule=lambda m, i: m.stock[i, 2] == 5)
    m.capacity = pyo.Constraint(
        list(HOURS),
        m.T,
        rule=lambda m, r, t: (
            sum(HOURS[r][j] * m.make[i, t] for j, i in enumerate(PRODUCTS))
            <= CAPACITY[r][t]
        ),
    )
    m.obj = pyo.Objective(
        expr=sum(
            MARGIN[i] * m.sell[i, t] - 0.5 * m.stock[i, t] for i in m.I for t in m.T
        ),
        sense=pyo.maximize,
    )
    return m


def check(m):
    for i in PRODUCTS:
        assert abs(sum(pyo.value(m.make[i, t] - m.sell[i, t]) for t in m.T) - 5) < 1e-6


def tables(m):
    return {
        "plan": frame(
            [
                [
                    t + 1,
                    i,
                    *[
                        pyo.value(getattr(m, k)[i, t])
                        for k in ["make", "sell", "stock"]
                    ],
                ]
                for t in m.T
                for i in m.I
            ],
            ["Month", "Grade", "Production (t)", "Sales (t)", "Stock (t)"],
        )
    }


def plot(m):
    return (
        ["Month 1", "Month 2", "Month 3"],
        [sum(pyo.value(m.make[i, t]) for i in m.I) for t in m.T],
        "Total production (t)",
    )
