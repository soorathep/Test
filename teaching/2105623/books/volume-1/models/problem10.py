TITLE = "Locating Interdependent Process Support Units"
SOURCE = "Decentralisation"
ADAPTATION = "New four-unit, three-site instance; pairwise coordination costs retain the quadratic-assignment structure."
UNITS = "thousand USD/year"
PROBLEM = """Locate support units A, B, C, D among sites North, Central, South. Each site hosts at most two units. Annual operating costs by unit (North,Central,South) are A:(8,12,10), B:(9,11,8), C:(12,9,7), D:(10,8,11), in thousand USD. Pairwise coordination volumes are AB=4, AC=1, AD=2, BC=3, BD=1, CD=4. Coordination cost per volume unit is 0 for co-location, 2 between North and Central or Central and South, and 4 between North and South. Count each unordered unit pair once. Minimize operating plus coordination cost."""
FORMULATION = r"""Binary $x_{is}$ assigns unit $i$ to site $s$, with $\sum_s x_{is}=1$ and $\sum_i x_{is}\le2$. For each unordered unit pair $i<j$ and site pair $(s,t)$, introduce continuous $z_{ijst}\in[0,1]$ and impose

$$z_{ijst}\le x_{is},\quad z_{ijst}\le x_{jt},\quad z_{ijst}\ge x_{is}+x_{jt}-1.$$
$$\min\sum_{is}c_{is}x_{is}+\sum_{i<j}\sum_{st}v_{ij}d_{st}z_{ijst}.$$

Because the assignment variables are binary, these constraints enforce the product exactly at integer solutions. The MILP replaces a quadratic objective without changing the integer feasible assignments."""
DISCUSSION = """Low local operating cost can be outweighed by communication with tightly coupled units. Counting both ordered unit pairs would double the coordination cost. Experiment: set all coordination volumes to zero, then compare the placement and evaluate its cost under the original volumes."""
# MODEL CODE
import itertools
import pyomo.environ as pyo
from models.common import frame

COST = [[8, 12, 10], [9, 11, 8], [12, 9, 7], [10, 8, 11]]
V = {(0, 1): 4, (0, 2): 1, (0, 3): 2, (1, 2): 3, (1, 3): 1, (2, 3): 4}


def score(a):
    return sum(COST[i][a[i]] for i in range(4)) + sum(
        v * 2 * abs(a[i] - a[j]) for (i, j), v in V.items()
    )


def build():
    m = pyo.ConcreteModel()
    m.I = pyo.RangeSet(0, 3)
    m.S = pyo.RangeSet(0, 2)
    keys = [(i, j, s, t) for i, j in V for s in m.S for t in m.S]
    m.x = pyo.Var(m.I, m.S, domain=pyo.Binary)
    m.z = pyo.Var(keys, bounds=(0, 1))
    m.assign = pyo.Constraint(m.I, rule=lambda m, i: sum(m.x[i, s] for s in m.S) == 1)
    m.cap = pyo.Constraint(m.S, rule=lambda m, s: sum(m.x[i, s] for i in m.I) <= 2)
    m.link = pyo.ConstraintList()
    for i, j, s, t in keys:
        m.link.add(m.z[i, j, s, t] <= m.x[i, s])
        m.link.add(m.z[i, j, s, t] <= m.x[j, t])
        m.link.add(m.z[i, j, s, t] >= m.x[i, s] + m.x[j, t] - 1)
    m.obj = pyo.Objective(
        expr=sum(COST[i][s] * m.x[i, s] for i in m.I for s in m.S)
        + sum(V[i, j] * 2 * abs(s - t) * m.z[i, j, s, t] for i, j, s, t in keys)
    )
    return m


def check(m):
    best = min(
        score(a)
        for a in itertools.product(range(3), repeat=4)
        if all(a.count(s) <= 2 for s in range(3))
    )
    assert abs(pyo.value(m.obj) - best) < 1e-6


def tables(m):
    return {
        "locations": frame(
            [
                ["ABCD"[i], ["North", "Central", "South"][s], COST[i][s]]
                for i in m.I
                for s in m.S
                if pyo.value(m.x[i, s]) > 0.5
            ],
            ["Unit", "Site", "Operating cost (thousand USD/year)"],
        )
    }


def plot(m):
    return (
        ["ABCD"[i] for i in m.I],
        [sum(COST[i][s] * pyo.value(m.x[i, s]) for s in m.S) for i in m.I],
        "Assigned operating cost (thousand USD/year)",
    )
