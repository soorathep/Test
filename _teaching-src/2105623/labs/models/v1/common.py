"""Shared solution and numerical feasibility checks for the workbook."""

from pathlib import Path
import json
import importlib
import importlib.metadata
import pyomo.environ as pyo
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def solve(m):
    opt = pyo.SolverFactory("appsi_highs")
    opt.options["mip_rel_gap"] = 1e-9
    result = opt.solve(m, load_solutions=False)
    if not pyo.check_optimal_termination(result):
        raise RuntimeError(f"{m.name}: {result.solver.termination_condition}")
    m.solutions.load_from(result)
    audit(m)
    return m


def audit(m, tolerance=1e-6):
    violations = []
    for c in m.component_data_objects(pyo.Constraint, active=True):
        body = pyo.value(c.body)
        if c.has_lb():
            violations.append(max(0.0, pyo.value(c.lower) - body))
        if c.has_ub():
            violations.append(max(0.0, body - pyo.value(c.upper)))
    for x in m.component_data_objects(pyo.Var, active=True):
        value = pyo.value(x)
        if x.has_lb():
            violations.append(max(0.0, pyo.value(x.lb) - value))
        if x.has_ub():
            violations.append(max(0.0, value - pyo.value(x.ub)))
        if x.is_integer():
            violations.append(abs(value - round(value)))
    worst = max(violations, default=0.0)
    if worst > tolerance:
        raise AssertionError(f"{m.name}: violation {worst}")
    return worst


def frame(rows, columns):
    return pd.DataFrame(rows, columns=columns)


def run(number):
    module = importlib.import_module(f"models.v1.problem{number:02d}")
    model = solve(module.build())
    violation = audit(model)
    module.check(model)
    output = ROOT / "results" / f"{number:02d}"
    output.mkdir(parents=True, exist_ok=True)
    tables = module.tables(model)
    for name, table in tables.items():
        table.to_csv(output / f"{name}.csv", index=False)
    objective = next(model.component_data_objects(pyo.Objective, active=True))
    result = {
        "problem": number,
        "title": module.TITLE,
        "objective": pyo.value(objective),
        "objective_units": module.UNITS,
        "sense": "minimize" if objective.sense == pyo.minimize else "maximize",
        "termination": "optimal",
        "max_violation": violation,
        "domain_checks": "passed",
        "pyomo": importlib.metadata.version("pyomo"),
        "highspy": importlib.metadata.version("highspy"),
    }
    (output / "solution.json").write_text(json.dumps(result, indent=2) + "\n")
    return module, model, tables, result


if __name__ == "__main__":
    import sys

    module, model, tables, result = run(int(sys.argv[1]))
    print(json.dumps(result, indent=2))
    for name, table in tables.items():
        print("\n" + name + "\n" + table.to_string(index=False))
