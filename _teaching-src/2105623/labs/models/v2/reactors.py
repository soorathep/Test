"""Finite operating-menu reactor design with explicit kinetic assumptions."""

import math
import pyomo.environ as pyo
from models.v2.common import value

FEED_MAX = 100.0  # kmol/h
VOLUME_MAX = 250.0  # flow-residence surrogate in kmol
DEMAND = 35.0  # kmol/h desired product


def yields(kind, temp, tau, activity=1.0):
    kd = activity * 0.5 * math.exp(0.025 * (temp - 330))
    ku = 0.08 * math.exp(0.055 * (temp - 330))
    k = kd + ku
    conversion = 1 - math.exp(-k * tau) if kind == "PFR" else k * tau / (1 + k * tau)
    return conversion * kd / k, conversion * ku / k


def menu(level):
    return [
        (kind, t, tau)
        for kind in (["PFR"] if level == 1 else ["PFR", "CSTR"])
        for t in ([330] if level == 1 else [320, 330, 340, 350])
        for tau in ([1, 2, 3, 4] if level == 1 else [0.5, 1, 2, 3, 4])
    ]


def build(level):
    modes = menu(level)
    states = (
        {"nominal": 1.0} if level < 3 else {"low_activity": 0.8, "high_activity": 1.2}
    )
    m = pyo.ConcreteModel(name="Reactor operating menu")
    m.J = pyo.RangeSet(0, len(modes) - 1)
    m.S = pyo.Set(initialize=list(states))
    m.z = pyo.Var(m.J, domain=pyo.Binary)
    m.f = pyo.Var(m.J, domain=pyo.NonNegativeReals)
    m.one = pyo.Constraint(expr=sum(m.z[j] for j in m.J) == 1)
    m.bound = pyo.Constraint(m.J, rule=lambda m, j: m.f[j] <= FEED_MAX * m.z[j])
    m.holdup = pyo.Constraint(expr=sum(modes[j][2] * m.f[j] for j in m.J) <= VOLUME_MAX)
    yd = {(s, j): yields(*modes[j], states[s])[0] for s in states for j in m.J}
    yu = {(s, j): yields(*modes[j], states[s])[1] for s in states for j in m.J}
    m.product = pyo.Constraint(
        m.S, rule=lambda m, s: sum(yd[s, j] * m.f[j] for j in m.J) >= DEMAND
    )

    def profit(m, s):
        return sum(
            (5 * yd[s, j] + yu[s, j] - 1.2 - 0.006 * (modes[j][1] - 320)) * m.f[j]
            - (20 if modes[j][0] == "PFR" else 10) * m.z[j]
            for j in m.J
        )

    m.profit = pyo.Expression(m.S, rule=profit)
    m.eta = pyo.Var(bounds=(-1000, 1000))
    m.floor = pyo.Constraint(m.S, rule=lambda m, s: m.eta <= m.profit[s])
    m.obj = pyo.Objective(expr=m.eta, sense=pyo.maximize)
    m._modes = modes
    m._states = states
    return m


def check(m, level):
    # Independent enumeration: each fixed mode has a one-dimensional linear problem.
    profits = []
    for kind, t, tau in m._modes:
        ys = [yields(kind, t, tau, a) for a in m._states.values()]
        lo = max(DEMAND / d for d, u in ys)
        hi = min(FEED_MAX, VOLUME_MAX / tau)
        if lo <= hi:
            slopes = [5 * d + u - 1.2 - 0.006 * (t - 320) for d, u in ys]
            slope = min(slopes)
            f = hi if slope >= 0 else lo
            profits.append(slope * f - (20 if kind == "PFR" else 10))
    assert abs(max(profits) - value(m.obj)) < 1e-6
    for s, a in m._states.items():
        f = sum(value(m.f[j]) for j in m.J)
        d = sum(yields(*m._modes[j], a)[0] * value(m.f[j]) for j in m.J)
        u = sum(yields(*m._modes[j], a)[1] * value(m.f[j]) for j in m.J)
        assert d >= DEMAND - 1e-6 and d + u <= f + 1e-6


def report(m, level):
    j = max(m.J, key=lambda j: value(m.z[j]))
    kind, t, tau = m._modes[j]
    f = value(m.f[j])
    return {
        "objective": value(m.obj),
        "units": "USD/h",
        "rows": [
            {
                "State": s,
                "Desired (kmol/h)": yields(kind, t, tau, a)[0] * f,
                "Undesired (kmol/h)": yields(kind, t, tau, a)[1] * f,
                "Profit (USD/h)": value(m.profit[s]),
            }
            for s, a in m._states.items()
        ],
        "metrics": {
            "Reactor": kind,
            "Temperature (K)": t,
            "Residence time (h)": tau,
            "Feed (kmol/h)": f,
            "Holdup (kmol)": f * tau,
        },
    }


if __name__ == "__main__":
    import sys
    from models.v2.common import cli

    cli(sys.modules[__name__])
