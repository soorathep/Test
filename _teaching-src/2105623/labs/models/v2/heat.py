"""Heat recovery between fixed-temperature utility-like streams."""

import pyomo.environ as pyo
from models.v2.common import value

HOT = {"H1": 120, "H2": 80}  # kW available
ARCS = [("H1", "C1"), ("H1", "C2"), ("H2", "C2")]
CAP = {("H1", "C1"): 100, ("H1", "C2"): 90, ("H2", "C2"): 70}
FIXED = {("H1", "C1"): 25, ("H1", "C2"): 20, ("H2", "C2"): 18}  # USD/d


def build(level):
    states = (
        {"normal": (100, 100, 1.0, 1.0)}
        if level < 3
        else {"low": (100, 80, 1.0, 0.5), "high": (100, 130, 2.0, 0.5)}
    )
    m = pyo.ConcreteModel(name="Fixed-temperature heat recovery")
    m.A = pyo.Set(initialize=ARCS, dimen=2)
    m.H = pyo.Set(initialize=list(HOT))
    m.C = pyo.Set(initialize=["C1", "C2"])
    m.S = pyo.Set(initialize=list(states))
    m.z = pyo.Var(m.A, domain=pyo.Binary)
    if level == 1:
        for a in m.A:
            m.z[a].fix(1)
    m.q = pyo.Var(m.S, m.A, domain=pyo.NonNegativeReals)
    m.hu = pyo.Var(m.S, m.C, domain=pyo.NonNegativeReals)
    m.cu = pyo.Var(m.S, m.H, domain=pyo.NonNegativeReals)
    m.hot = pyo.Constraint(
        m.S,
        m.H,
        rule=lambda m, s, h: (
            sum(m.q[s, i, j] for i, j in m.A if i == h) + m.cu[s, h] == HOT[h]
        ),
    )
    m.cold = pyo.Constraint(
        m.S,
        m.C,
        rule=lambda m, s, c: (
            sum(m.q[s, i, j] for i, j in m.A if j == c) + m.hu[s, c]
            == states[s][0 if c == "C1" else 1]
        ),
    )
    m.cap = pyo.Constraint(
        m.S, m.A, rule=lambda m, s, h, c: m.q[s, h, c] <= CAP[h, c] * m.z[h, c]
    )
    if level == 3:
        m.budget = pyo.Constraint(expr=sum(FIXED[a] * m.z[a] for a in m.A) <= 45)
    fixed = 0 if level == 1 else sum(FIXED[a] * m.z[a] for a in m.A)
    m.obj = pyo.Objective(
        expr=fixed
        + sum(
            states[s][3]
            * (
                states[s][2] * sum(m.hu[s, c] for c in m.C)
                + 0.15 * sum(m.cu[s, h] for h in m.H)
            )
            for s in m.S
        )
    )
    m._states = states
    return m


def check(m, level):
    for s in m.S:
        recovery = sum(value(m.q[s, h, c]) for h, c in m.A)
        assert abs(recovery + sum(value(m.cu[s, h]) for h in m.H) - 200) < 1e-6
        assert (
            abs(recovery + sum(value(m.hu[s, c]) for c in m.C) - sum(m._states[s][:2]))
            < 1e-6
        )


def report(m, level):
    rows = []
    for s in m.S:
        for h, c in m.A:
            rows.append(
                {
                    "State": s,
                    "Match": h + " to " + c,
                    "Installed": round(value(m.z[h, c])),
                    "Heat (kW)": value(m.q[s, h, c]),
                }
            )
    metrics = {
        f"{s}: hot utility (kW)": sum(value(m.hu[s, c]) for c in m.C) for s in m.S
    }
    metrics.update(
        {f"{s}: cold utility (kW)": sum(value(m.cu[s, h]) for h in m.H) for s in m.S}
    )
    return {
        "objective": value(m.obj),
        "units": "USD/d",
        "rows": rows,
        "metrics": metrics,
    }


if __name__ == "__main__":
    import sys
    from models.v2.common import cli

    cli(sys.modules[__name__])
