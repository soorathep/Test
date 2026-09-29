"""Daily hydrogen dispatch, tank design, and scenario-dependent operation."""

import pyomo.environ as pyo
from models.common import value

PRICE = [30, 25, 80, 100, 45, 35]  # USD/MWh
DEMAND = [120, 150, 180, 220, 180, 140]  # kg per four-hour period
DT = 4  # h
SPECIFIC_ENERGY = 0.05  # MWh/kg
TANK_CHARGE = 0.15  # USD/(kg capacity d)


def build(level):
    states = (
        {"nominal": (1, 1)} if level < 3 else {"low": (0.9, 0.5), "high": (1.15, 0.5)}
    )
    m = pyo.ConcreteModel(name="Hydrogen production and storage")
    m.S = pyo.Set(initialize=list(states))
    m.T = pyo.RangeSet(0, 5)
    m.k = pyo.Var(bounds=(50, 500))
    if level == 1:
        m.k.fix(150)
    m.power = pyo.Var(m.S, m.T, bounds=(0, 4))
    m.stock = pyo.Var(m.S, m.T, domain=pyo.NonNegativeReals)
    m.balance = pyo.Constraint(
        m.S,
        m.T,
        rule=lambda m, s, t: (
            m.stock[s, t]
            == (50 if t == 0 else m.stock[s, t - 1])
            + DT * m.power[s, t] / SPECIFIC_ENERGY
            - DEMAND[t] * states[s][0]
        ),
    )
    m.capacity = pyo.Constraint(m.S, m.T, rule=lambda m, s, t: m.stock[s, t] <= m.k)
    m.terminal = pyo.Constraint(m.S, rule=lambda m, s: m.stock[s, 5] == 50)
    if level == 3:
        m.on = pyo.Var(m.S, m.T, domain=pyo.Binary)
        m.start = pyo.Var(m.S, m.T, domain=pyo.Binary)
        m.upper = pyo.Constraint(
            m.S, m.T, rule=lambda m, s, t: m.power[s, t] <= 4 * m.on[s, t]
        )
        m.lower = pyo.Constraint(
            m.S, m.T, rule=lambda m, s, t: m.power[s, t] >= m.on[s, t]
        )
        m.startup = pyo.Constraint(
            m.S,
            m.T,
            rule=lambda m, s, t: (
                m.start[s, t] >= m.on[s, t] - (0 if t == 0 else m.on[s, t - 1])
            ),
        )
    fixed = 0 if level == 1 else TANK_CHARGE * m.k
    m.obj = pyo.Objective(
        expr=fixed
        + sum(
            states[s][1]
            * sum(
                DT * PRICE[t] * m.power[s, t]
                + (10 * m.start[s, t] if level == 3 else 0)
                for t in m.T
            )
            for s in m.S
        )
    )
    m._states = states
    return m


def check(m, level):
    for s, (factor, prob) in m._states.items():
        production = sum(DT * value(m.power[s, t]) / SPECIFIC_ENERGY for t in m.T)
        assert abs(production - factor * sum(DEMAND)) < 1e-6
        assert abs(value(m.stock[s, 5]) - 50) < 1e-6
        if level == 3:
            for t in m.T:
                power = value(m.power[s, t])
                assert power < 1e-6 or power >= 1 - 1e-6


def report(m, level):
    return {
        "objective": value(m.obj),
        "units": "USD/d",
        "rows": [
            {
                "State": s,
                "Period": t + 1,
                "Power (MW)": value(m.power[s, t]),
                "Demand (kg)": DEMAND[t] * m._states[s][0],
                "End stock (kg)": value(m.stock[s, t]),
            }
            for s in m.S
            for t in m.T
        ],
        "metrics": {
            "Tank capacity (kg)": value(m.k),
            "Expected electricity (MWh/d)": sum(
                p * sum(DT * value(m.power[s, t]) for t in m.T)
                for s, (a, p) in m._states.items()
            ),
        },
    }


if __name__ == "__main__":
    import sys
    from models.common import cli

    cli(sys.modules[__name__])
