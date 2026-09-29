TITLE = "Delivery Routing with Lexicographic Objectives"
SOURCE = "Lost baggage distribution"
ADAPTATION = "New six-customer delivery instance using complete feasible-route enumeration. Open delivery routes do not need to return within the delivery deadline."
UNITS = "lexicographic score = 61 × vans + longest route minutes"
PROBLEM = """A depot at (0,0) dispatches vans to six customers at (2,1), (1,4), (4,3), (6,1), (5,5), and (2,6). Travel time is five minutes per unit of Euclidean distance. Service time is zero and vehicle load is unrestricted. Each route starts at the depot and finishes at its last customer, without a required return trip in the deadline. All deliveries must finish within 60 minutes. First minimize the number of vans; among solutions using that number, minimize the longest route duration. Every customer must be visited exactly once."""
FORMULATION = r"""For each nonempty customer subset, enumerate all orders and retain a shortest open route. Discard subsets whose shortest route exceeds 60 min. Let $R$ be the resulting route set, $a_{ir}$ indicate route membership, and $d_r$ be its duration. Choose route binaries $y_r$ and $T\in[0,60]$.

$$\sum_r a_{ir}y_r=1\quad\forall i,\qquad T\ge d_ry_r\quad\forall r.$$
$$\min\ 61\sum_r y_r+T.$$

Since $T$ can vary by at most 60 min, one additional van always costs more than any improvement in $T$. The scalar objective therefore implements the stated lexicographic priorities exactly. Route enumeration is complete for this small instance; it does not scale to large delivery networks."""
DISCUSSION = """Minimizing total distance is different from minimizing the longest route. The fleet count takes strict priority here. Retaining only the shortest route for each subset is valid because every route with that subset serves the same customers and a longer duration is dominated. Experiment: impose return-to-depot travel and compare the required vans."""
# MODEL CODE
import itertools
import math
import pyomo.environ as pyo
from models.common import frame

COORD = [(0, 0), (2, 1), (1, 4), (4, 3), (6, 1), (5, 5), (2, 6)]
ROUTES = []
for size in range(1, 7):
    for subset in itertools.combinations(range(1, 7), size):
        duration, path = min(
            (sum(5 * math.dist(COORD[a], COORD[b]) for a, b in zip((0,) + p, p)), p)
            for p in itertools.permutations(subset)
        )
        if duration <= 60:
            ROUTES.append((path, duration))


def build():
    m = pyo.ConcreteModel()
    m.R = pyo.RangeSet(0, len(ROUTES) - 1)
    m.y = pyo.Var(m.R, domain=pyo.Binary)
    m.T = pyo.Var(bounds=(0, 60))
    m.cover = pyo.Constraint(
        range(1, 7),
        rule=lambda m, i: sum(m.y[r] for r in m.R if i in ROUTES[r][0]) == 1,
    )
    m.longest = pyo.Constraint(m.R, rule=lambda m, r: m.T >= ROUTES[r][1] * m.y[r])
    m.obj = pyo.Objective(expr=61 * sum(m.y[r] for r in m.R) + m.T)
    return m


def check(m):
    selected = [ROUTES[r] for r in m.R if pyo.value(m.y[r]) > 0.5]
    visits = [i for route, _ in selected for i in route]
    assert sorted(visits) == list(range(1, 7))
    assert abs(max(d for _, d in selected) - pyo.value(m.T)) < 1e-6
    # Independent subset dynamic programming for the lexicographic pair.
    best = {0: (0, 0.0)}
    for mask in range(1, 64):
        choices = []
        for path, d in ROUTES:
            bits = sum(1 << (i - 1) for i in path)
            if bits & mask == bits and mask ^ bits in best:
                k, t = best[mask ^ bits]
                choices.append((k + 1, max(t, d)))
        if choices:
            best[mask] = min(choices)
    assert best[63][0] == len(selected) and abs(best[63][1] - pyo.value(m.T)) < 1e-6


def tables(m):
    selected = [ROUTES[r] for r in m.R if pyo.value(m.y[r]) > 0.5]
    return {
        "routes": frame(
            [
                [j + 1, "0 → " + " → ".join(map(str, path)), duration]
                for j, (path, duration) in enumerate(selected)
            ],
            ["Van", "Open route", "Duration (min)"],
        ),
        "priorities": frame(
            [["Vans", len(selected)], ["Longest route (min)", pyo.value(m.T)]],
            ["Criterion", "Value"],
        ),
    }


def plot(m):
    selected = [d for r, (path, d) in enumerate(ROUTES) if pyo.value(m.y[r]) > 0.5]
    return (
        [f"Van {j + 1}" for j in range(len(selected))],
        selected,
        "Route duration (min)",
    )
