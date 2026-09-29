"""Single-vessel sequencing with release times and directed cleaning."""

import itertools
import pyomo.environ as pyo
from models.v2.common import value

JOBS = ["A1", "A2", "B1", "C1"]
DURATION = {"A1": 2, "A2": 3, "B1": 2, "C1": 4}  # h
RELEASE = {"A1": 0, "A2": 2, "B1": 1, "C1": 0}
DUE = {"A1": 6, "A2": 12, "B1": 7, "C1": 14}
WEIGHT = {"A1": 4, "A2": 2, "B1": 5, "C1": 1}  # USD/(h of tardiness)
CLEAN = {
    ("A", "B"): 1,
    ("A", "C"): 2,
    ("B", "A"): 3,
    ("B", "C"): 1,
    ("C", "A"): 1,
    ("C", "B"): 2,
}


def cleaning(i, j, level):
    return 0 if level == 1 or i == "start" or j == "end" else CLEAN.get((i[0], j[0]), 0)


def build(level):
    arcs = [
        (i, j)
        for i in ["start"] + JOBS
        for j in JOBS + ["end"]
        if i != j and (i, j) != ("start", "end")
    ]
    m = pyo.ConcreteModel(name="Batch vessel schedule")
    m.J = pyo.Set(initialize=JOBS)
    m.A = pyo.Set(initialize=arcs, dimen=2)
    m.x = pyo.Var(m.A, domain=pyo.Binary)
    m.s = pyo.Var(m.J, bounds=(0, 30))
    m.finish = pyo.Var(bounds=(0, 40))
    m.out = pyo.Constraint(
        ["start"] + JOBS,
        rule=lambda m, i: sum(m.x[i, j] for a, j in m.A if a == i) == 1,
    )
    m.inc = pyo.Constraint(
        JOBS + ["end"], rule=lambda m, j: sum(m.x[i, j] for i, b in m.A if b == j) == 1
    )
    m.release = pyo.Constraint(m.J, rule=lambda m, j: m.s[j] >= RELEASE[j])
    m.time = pyo.ConstraintList()
    for i, j in arcs:
        if i == "start":
            continue
        target = m.finish if j == "end" else m.s[j]
        m.time.add(
            target
            >= m.s[i] + DURATION[i] + cleaning(i, j, level) - 50 * (1 - m.x[i, j])
        )
    m.tardy = pyo.Var(m.J, domain=pyo.NonNegativeReals)
    m.late = pyo.Constraint(
        m.J, rule=lambda m, j: m.tardy[j] >= m.s[j] + DURATION[j] - DUE[j]
    )
    m.overtime = pyo.Var(domain=pyo.NonNegativeReals)
    m.over = pyo.Constraint(expr=m.overtime >= m.finish - 12)
    objective = (
        m.finish
        if level < 3
        else sum(WEIGHT[j] * m.tardy[j] for j in m.J) + 0.5 * m.overtime
    )
    m.obj = pyo.Objective(expr=objective)
    return m


def enumerate_best(level):
    best = float("inf")
    for order in itertools.permutations(JOBS):
        finish = 0
        prev = "start"
        cost = 0
        for j in order:
            start = max(RELEASE[j], finish + cleaning(prev, j, level))
            finish = start + DURATION[j]
            cost += WEIGHT[j] * max(0, finish - DUE[j])
            prev = j
        obj = finish if level < 3 else cost + 0.5 * max(0, finish - 12)
        best = min(best, obj)
    return best


def check(m, level):
    assert abs(enumerate_best(level) - value(m.obj)) < 1e-6
    order = sorted(JOBS, key=lambda j: value(m.s[j]))
    for i, j in zip(order, order[1:]):
        assert value(m.s[j]) + 1e-6 >= value(m.s[i]) + DURATION[i] + cleaning(
            i, j, level
        )


def report(m, level):
    order = sorted(JOBS, key=lambda j: value(m.s[j]))
    rows = [
        {
            "Job": j,
            "Start (h)": value(m.s[j]),
            "Finish (h)": value(m.s[j]) + DURATION[j],
            "Tardiness (h)": max(0, value(m.s[j]) + DURATION[j] - DUE[j]),
        }
        for j in order
    ]
    return {
        "objective": value(m.obj),
        "units": "h" if level < 3 else "USD",
        "rows": rows,
        "metrics": {
            "Sequence": " > ".join(order),
            "Makespan (h)": max(r["Finish (h)"] for r in rows),
            "Cleaning (h)": sum(
                cleaning(i, j, level) for i, j in zip(order, order[1:])
            ),
        },
    }


if __name__ == "__main__":
    import sys
    from models.v2.common import cli

    cli(sys.modules[__name__])
