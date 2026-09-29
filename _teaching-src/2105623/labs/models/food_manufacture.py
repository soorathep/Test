"""Food Manufacture 1: six-month LP adapted from Williams (2013), §12.1.
Run using ~/.venvs/optim/bin/python models/food_manufacture.py.
"""
from pathlib import Path
import json
import platform
import importlib.metadata
import pandas as pd
import pyomo.environ as pyo

ROOT = Path(__file__).resolve().parents[1]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
OILS = ["VEG1", "VEG2", "OIL1", "OIL2", "OIL3"]
VEGETABLE = ["VEG1", "VEG2"]
NONVEGETABLE = ["OIL1", "OIL2", "OIL3"]
PRICES = [
    [110, 120, 130, 110, 115],
    [130, 130, 110, 90, 115],
    [110, 140, 130, 100, 95],
    [120, 110, 120, 120, 125],
    [100, 120, 150, 110, 105],
    [90, 100, 140, 80, 135],
]
HARDNESS = dict(zip(OILS, [8.8, 6.1, 2.0, 4.2, 5.0]))


def build_model(storage_cost=5.0, vegetable_capacity=200.0,
                nonvegetable_capacity=250.0, carryover=True):
    m = pyo.ConcreteModel(name="Food manufacture: blending and inventory")
    m.I = pyo.Set(initialize=OILS, ordered=True)
    m.T = pyo.RangeSet(1, 6)
    m.V = pyo.Set(initialize=VEGETABLE)
    m.N = pyo.Set(initialize=NONVEGETABLE)
    m.price = pyo.Param(m.I, m.T,
        initialize={(i, t): PRICES[t-1][OILS.index(i)] for i in OILS for t in range(1, 7)})
    m.hardness = pyo.Param(m.I, initialize=HARDNESS)
    m.storage_cost = pyo.Param(initialize=storage_cost)
    m.vegetable_capacity = pyo.Param(initialize=vegetable_capacity)
    m.nonvegetable_capacity = pyo.Param(initialize=nonvegetable_capacity)
    m.buy = pyo.Var(m.I, m.T, domain=pyo.NonNegativeReals)
    m.use = pyo.Var(m.I, m.T, domain=pyo.NonNegativeReals)
    m.stock = pyo.Var(m.I, m.T, bounds=(0, 1000))
    m.product = pyo.Var(m.T, domain=pyo.NonNegativeReals)

    def inventory_rule(m, i, t):
        previous = 500 if t == 1 else m.stock[i, t-1]
        return previous + m.buy[i, t] == m.use[i, t] + m.stock[i, t]
    m.inventory = pyo.Constraint(m.I, m.T, rule=inventory_rule)
    m.terminal = pyo.Constraint(m.I, rule=lambda m, i: m.stock[i, 6] == 500)
    m.mass_balance = pyo.Constraint(m.T,
        rule=lambda m, t: m.product[t] == sum(m.use[i, t] for i in m.I))
    m.vegetable_limit = pyo.Constraint(m.T,
        rule=lambda m, t: sum(m.use[i, t] for i in m.V) <= m.vegetable_capacity)
    m.nonvegetable_limit = pyo.Constraint(m.T,
        rule=lambda m, t: sum(m.use[i, t] for i in m.N) <= m.nonvegetable_capacity)
    m.hardness_min = pyo.Constraint(m.T,
        rule=lambda m, t: sum(m.hardness[i]*m.use[i, t] for i in m.I) >= 3*m.product[t])
    m.hardness_max = pyo.Constraint(m.T,
        rule=lambda m, t: sum(m.hardness[i]*m.use[i, t] for i in m.I) <= 6*m.product[t])
    if not carryover:
        # Keep the initial reserve unchanged each month: purchases equal use.
        m.fixed_stock = pyo.Constraint(m.I, m.T,
            rule=lambda m, i, t: m.stock[i, t] == 500)
    m.revenue = pyo.Expression(expr=150*sum(m.product[t] for t in m.T))
    m.purchase_cost = pyo.Expression(expr=sum(m.price[i,t]*m.buy[i,t] for i in m.I for t in m.T))
    m.holding_cost = pyo.Expression(expr=m.storage_cost*sum(m.stock[i,t] for i in m.I for t in m.T))
    m.profit = pyo.Objective(expr=m.revenue-m.purchase_cost-m.holding_cost, sense=pyo.maximize)
    return m


def solve_model(m):
    solver = pyo.SolverFactory("appsi_highs")
    if not solver.available(exception_flag=False):
        raise RuntimeError("HiGHS is unavailable. Install highspy in the active environment.")
    result = solver.solve(m, load_solutions=False)
    if not pyo.check_optimal_termination(result):
        raise RuntimeError(f"No verified optimum: {result.solver.termination_condition}")
    m.solutions.load_from(result)
    return m


def validate(m, tol=1e-6):
    """Independently recompute physical balances, bounds and the objective."""
    v = pyo.value
    residuals = []
    for i in OILS:
        previous = 500.0
        for t in m.T:
            b, u, s = [v(x[i,t]) for x in (m.buy, m.use, m.stock)]
            residuals.append(abs(previous+b-u-s))
            assert b >= -tol and u >= -tol and -tol <= s <= 1000+tol
            previous = s
            if hasattr(m, "fixed_stock"):
                assert abs(s-500) < tol
        assert abs(previous-500) < tol
        assert abs(sum(v(m.buy[i,t])-v(m.use[i,t]) for t in m.T)) < tol
    for t in m.T:
        quantity = sum(v(m.use[i,t]) for i in OILS)
        residuals.append(abs(quantity-v(m.product[t])))
        quality = sum(HARDNESS[i]*v(m.use[i,t]) for i in OILS)
        assert 3*quantity-tol <= quality <= 6*quantity+tol
        assert sum(v(m.use[i,t]) for i in VEGETABLE) <= v(m.vegetable_capacity)+tol
        assert sum(v(m.use[i,t]) for i in NONVEGETABLE) <= v(m.nonvegetable_capacity)+tol
    recomputed = sum(150*v(m.product[t]) for t in m.T) - sum(
        PRICES[t-1][OILS.index(i)]*v(m.buy[i,t])+v(m.storage_cost)*v(m.stock[i,t])
        for i in OILS for t in m.T)
    assert abs(recomputed-v(m.profit)) < tol
    assert max(residuals) < tol
    return {"max_balance_residual_t": max(residuals), "objective_residual_gbp": abs(recomputed-v(m.profit)),
            "checks_passed": True}


def export_results():
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    m = solve_model(build_model())
    checks = validate(m)
    v = pyo.value
    for name in ["buy", "use", "stock"]:
        pd.DataFrame([[v(getattr(m,name)[i,t]) for i in OILS] for t in m.T],
                     index=pd.Index(MONTHS, name="Month"), columns=OILS).to_csv(out / f"{name}.csv")
    rows = []
    for t, month in enumerate(MONTHS, 1):
        q = v(m.product[t])
        veg = sum(v(m.use[i,t]) for i in VEGETABLE)
        nonveg = sum(v(m.use[i,t]) for i in NONVEGETABLE)
        rows.append([month, q, veg, nonveg, sum(HARDNESS[i]*v(m.use[i,t]) for i in OILS)/q if q else None,
                     200-veg, 250-nonveg])
    pd.DataFrame(rows, columns=["Month", "Product (t)", "Vegetable (t)", "Nonvegetable (t)",
                               "Hardness", "Vegetable slack (t)", "Nonvegetable slack (t)"]).to_csv(out/"summary.csv", index=False)
    scenarios = []
    for label, kwargs in [
        ("Reference", {}), ("Fixed monthly reserves", {"carryover": False}),
        ("Holding cost = 2", {"storage_cost": 2}), ("Holding cost = 10", {"storage_cost": 10}),
        ("Vegetable capacity +1", {"vegetable_capacity": 201}),
        ("Nonvegetable capacity +1", {"nonvegetable_capacity": 251}),
    ]:
        alternative = solve_model(build_model(**kwargs))
        validate(alternative)
        scenarios.append([label, v(alternative.profit), v(alternative.profit)-v(m.profit)])
    pd.DataFrame(scenarios, columns=["Scenario", "Profit (GBP)", "Change (GBP)"]).to_csv(out/"scenarios.csv", index=False)
    metadata = {"profit": v(m.profit), "revenue": v(m.revenue), "purchase_cost": v(m.purchase_cost),
                "holding_cost": v(m.holding_cost), "total_product": sum(v(m.product[t]) for t in m.T),
                "validation": checks, "python": platform.python_version(),
                "packages": {name: importlib.metadata.version(name) for name in ["pyomo", "highspy", "pandas", "matplotlib"]}}
    (out/"solution.json").write_text(json.dumps(metadata, indent=2)+"\n")
    print(json.dumps(metadata, indent=2))
    return m


if __name__ == "__main__":
    export_results()
