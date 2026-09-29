"""Segregated wastewater reuse with fixed-quality source streams."""

import pyomo.environ as pyo
from models.v2.common import value

SUPPLY = {"S1": 60, "S2": 50}  # m3/h
NOMINAL = {"S1": 40, "S2": 120}  # mg/L
HIGH = {"S1": 60, "S2": 160}
DEMAND = {"U1": 50, "U2": 40}  # m3/h
LIMIT = {"U1": 30, "U2": 60}  # mg/L
TECH = {"moderate": (0.75, 40, 0.25, 3), "advanced": (0.95, 80, 0.45, 12)}
# removal fraction, hydraulic capacity m3/h, variable USD/m3, fixed USD/h


def build(level):
    conc = HIGH if level == 3 else NOMINAL
    techs = [] if level == 1 else ["moderate"] if level == 2 else list(TECH)
    m = pyo.ConcreteModel(name="Segregated water reuse")
    m.I = pyo.Set(initialize=list(SUPPLY))
    m.J = pyo.Set(initialize=list(DEMAND))
    m.K = pyo.Set(initialize=techs)
    m.x = pyo.Var(m.I, m.J, domain=pyo.NonNegativeReals)
    m.y = pyo.Var(m.I, m.J, m.K, domain=pyo.NonNegativeReals)
    m.f = pyo.Var(m.J, domain=pyo.NonNegativeReals)
    m.d = pyo.Var(m.I, domain=pyo.NonNegativeReals)
    m.z = pyo.Var(m.K, domain=pyo.Binary)
    if level == 2:
        m.z["moderate"].fix(1)
    if level == 3:
        m.choose = pyo.Constraint(expr=sum(m.z[k] for k in m.K) <= 1)
    m.source = pyo.Constraint(
        m.I,
        rule=lambda m, i: (
            sum(m.x[i, j] + sum(m.y[i, j, k] for k in m.K) for j in m.J) + m.d[i]
            == SUPPLY[i]
        ),
    )
    m.sink = pyo.Constraint(
        m.J,
        rule=lambda m, j: (
            sum(m.x[i, j] + sum(m.y[i, j, k] for k in m.K) for i in m.I) + m.f[j]
            == DEMAND[j]
        ),
    )
    m.quality = pyo.Constraint(
        m.J,
        rule=lambda m, j: (
            sum(
                conc[i]
                * (m.x[i, j] + sum((1 - TECH[k][0]) * m.y[i, j, k] for k in m.K))
                for i in m.I
            )
            <= LIMIT[j] * DEMAND[j]
        ),
    )
    m.cap = pyo.Constraint(
        m.K,
        rule=lambda m, k: (
            sum(m.y[i, j, k] for i in m.I for j in m.J) <= TECH[k][1] * m.z[k]
        ),
    )
    m.obj = pyo.Objective(
        expr=sum(m.f[j] for j in m.J)
        + 0.1 * sum(m.d[i] for i in m.I)
        + sum(TECH[k][2] * m.y[i, j, k] for i in m.I for j in m.J for k in m.K)
        + (sum(TECH[k][3] * m.z[k] for k in m.K) if level == 3 else 0)
    )
    m._conc = conc
    return m


def check(m, level):
    fresh = sum(value(m.f[j]) for j in m.J)
    disposal = sum(value(m.d[i]) for i in m.I)
    assert abs(110 + fresh - 90 - disposal) < 1e-6
    incoming = sum(m._conc[i] * SUPPLY[i] for i in m.I)
    sinkload = sum(
        m._conc[i]
        * (value(m.x[i, j]) + sum((1 - TECH[k][0]) * value(m.y[i, j, k]) for k in m.K))
        for i in m.I
        for j in m.J
    )
    waste = sum(m._conc[i] * value(m.d[i]) for i in m.I)
    captured = sum(
        m._conc[i] * TECH[k][0] * value(m.y[i, j, k])
        for i in m.I
        for j in m.J
        for k in m.K
    )
    assert abs(incoming - sinkload - waste - captured) < 1e-5


def report(m, level):
    rows = []
    for j in m.J:
        load = sum(
            m._conc[i]
            * (
                value(m.x[i, j])
                + sum((1 - TECH[k][0]) * value(m.y[i, j, k]) for k in m.K)
            )
            for i in m.I
        )
        rows.append(
            {
                "User": j,
                "Fresh (m3/h)": value(m.f[j]),
                "Direct reuse (m3/h)": sum(value(m.x[i, j]) for i in m.I),
                "Treated reuse (m3/h)": sum(
                    value(m.y[i, j, k]) for i in m.I for k in m.K
                ),
                "Concentration (mg/L)": load / DEMAND[j],
            }
        )
    selected = ", ".join(k for k in m.K if value(m.z[k]) > 0.5) or "none"
    return {
        "objective": value(m.obj),
        "units": "USD/h",
        "rows": rows,
        "metrics": {
            "Freshwater (m3/h)": sum(value(m.f[j]) for j in m.J),
            "Disposal (m3/h)": sum(value(m.d[i]) for i in m.I),
            "Technology": selected,
        },
    }


if __name__ == "__main__":
    import sys
    from models.v2.common import cli

    cli(sys.modules[__name__])
