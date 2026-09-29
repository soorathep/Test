"""Blend design: nominal, box-robust, and budget-robust quality."""

import itertools
import pyomo.environ as pyo
from models.v2.common import value, solve

COST = {"A": 100, "B": 80, "C": 55}  # USD/t
NOMINAL = {"A": 0.02, "B": 0.08, "C": 0.14}  # mass fraction
DELTA = {"A": 0.01, "B": 0.02, "C": 0.03}
CAP = {"A": 60, "B": 60, "C": 60}  # t/d
TOTAL = 100  # t/d
LIMIT = 0.07  # maximum impurity mass fraction


def build(level, gamma=1.5):
    m = pyo.ConcreteModel(name="Blend quality")
    m.I = pyo.Set(initialize=list(COST))
    m.x = pyo.Var(m.I, domain=pyo.NonNegativeReals, bounds=lambda m, i: (0, CAP[i]))
    m.mass = pyo.Constraint(expr=sum(m.x[i] for i in m.I) == TOTAL)
    nominal = sum(NOMINAL[i] * m.x[i] for i in m.I)
    if level == 1:
        m.quality = pyo.Constraint(expr=nominal <= LIMIT * TOTAL)
    elif level == 2:
        m.quality = pyo.Constraint(
            expr=nominal + sum(DELTA[i] * m.x[i] for i in m.I) <= LIMIT * TOTAL
        )
    else:
        m.p = pyo.Var(domain=pyo.NonNegativeReals)
        m.q = pyo.Var(m.I, domain=pyo.NonNegativeReals)
        m.support = pyo.Constraint(
            m.I, rule=lambda m, i: m.p + m.q[i] >= DELTA[i] * m.x[i]
        )
        m.quality = pyo.Constraint(
            expr=nominal + gamma * m.p + sum(m.q[i] for i in m.I) <= LIMIT * TOTAL
        )
    m.cost = pyo.Objective(expr=sum(COST[i] * m.x[i] for i in m.I))
    m._gamma = gamma
    return m


def worst_load(m, gamma):
    terms = sorted((DELTA[i] * value(m.x[i]) for i in m.I), reverse=True)
    whole = int(gamma)
    return sum(terms[:whole]) + (gamma - whole) * (
        terms[whole] if whole < len(terms) else 0
    )


def check(m, level):
    assert abs(sum(value(m.x[i]) for i in m.I) - TOTAL) < 1e-6
    g = 0 if level == 1 else 3 if level == 2 else m._gamma
    load = sum(NOMINAL[i] * value(m.x[i]) for i in m.I) + worst_load(m, g)
    assert load <= TOTAL * LIMIT + 1e-6
    if level == 2:
        for u in itertools.product([0, 1], repeat=3):
            assert (
                sum(
                    (NOMINAL[i] + u[k] * DELTA[i]) * value(m.x[i])
                    for k, i in enumerate(m.I)
                )
                <= TOTAL * LIMIT + 1e-6
            )


def report(m, level):
    nominal = sum(NOMINAL[i] * value(m.x[i]) for i in m.I) / TOTAL
    full = nominal + worst_load(m, 3) / TOTAL
    g = 0 if level == 1 else 3 if level == 2 else m._gamma
    return {
        "objective": value(m.cost),
        "units": "USD/d",
        "rows": [{"Feed": i, "Flow (t/d)": value(m.x[i])} for i in m.I],
        "metrics": {
            "Nominal impurity (%)": 100 * nominal,
            "Full-box impurity (%)": 100 * full,
            "Protected impurity (%)": 100 * (nominal + worst_load(m, g) / TOTAL),
            "Gamma": g,
        },
    }


if __name__ == "__main__":
    import sys
    from models.v2.common import cli

    cli(sys.modules[__name__])
