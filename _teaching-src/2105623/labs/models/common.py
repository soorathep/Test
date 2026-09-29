"""Solver and numerical audit shared by every worked problem."""

import json
from pathlib import Path
import pyomo.environ as pyo

ROOT = Path(__file__).resolve().parents[1]


def audit(m, tol=1e-6):
    errors = []
    for c in m.component_data_objects(pyo.Constraint, active=True):
        v = pyo.value(c.body)
        if c.has_lb():
            errors.append(max(0, pyo.value(c.lower) - v))
        if c.has_ub():
            errors.append(max(0, v - pyo.value(c.upper)))
    for x in m.component_data_objects(pyo.Var):
        v = pyo.value(x)
        if x.has_lb():
            errors.append(max(0, pyo.value(x.lb) - v))
        if x.has_ub():
            errors.append(max(0, v - pyo.value(x.ub)))
        if x.is_integer():
            errors.append(abs(v - round(v)))
    worst = max(errors, default=0)
    assert worst <= tol, (m.name, worst)
    return worst


def solve(m):
    solver = pyo.SolverFactory("appsi_highs")
    solver.options["mip_rel_gap"] = 1e-9
    result = solver.solve(m, load_solutions=False)
    if not pyo.check_optimal_termination(result):
        raise RuntimeError(str(result.solver.termination_condition))
    m.solutions.load_from(result)
    audit(m)
    return m


def value(x):
    return float(pyo.value(x))


def cli(module):
    import sys

    level = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    model = solve(module.build(level))
    module.check(model, level)
    print(json.dumps(module.report(model, level), indent=2))
