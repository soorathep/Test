TITLE = "Finding an Equivalent Binary Inequality"
SOURCE = "Optimising a constraint"
ADAPTATION = "Uses the source eight-variable inequality. Adds explicit integer coefficient magnitudes of 1–40 and minimizes the absolute right-hand side."
UNITS = "absolute right-hand side"
PROBLEM = """The original binary inequality is 9x1+13x2−14x3+17x4+13x5−19x6+23x7+21x8 ≤ 37. Every x is zero or one. Find an equivalent inequality with the same strict coefficient signs, integer coefficient magnitudes from 1 to 40, and integer right-hand side. Equivalent means accepting exactly the same binary assignments. Minimize the absolute right-hand side. There may be multiple equally simple answers. The coefficient bound is a teaching restriction, not a theorem about the unrestricted source problem."""
FORMULATION = r"""Enumerate the 256 binary vectors. Partition them into $F$ (originally feasible) and $N$ (originally infeasible). Unknown signed integer coefficients $a_j$ have their prescribed signs and magnitudes 1–40. Let integer $b$ be the right-hand side and $B\ge0$.

$$\sum_j a_jx_j\le b\ (x\in F),\qquad \sum_j a_jx_j\ge b+1\ (x\in N),$$
$$B\ge b,\quad B\ge-b,\qquad\min B.$$

The unit separation for infeasible points is exact because coefficients, binary inputs, and $b$ are integer. Here the truth-table assignments are data; the decision variables are coefficients of a new constraint."""
DISCUSSION = """Scaling an inequality by a positive constant preserves feasibility but need not give the simplest integer representation. Exact truth-table matching protects both feasible and infeasible assignments. The result is optimal within the stated coefficient bounds. Experiment: change the objective to the sum of coefficient magnitudes and compare the resulting inequality."""
# MODEL CODE
import itertools
import pyomo.environ as pyo
from models.v1.common import frame

ORIGINAL = [9, 13, -14, 17, 13, -19, 23, 21]
POINTS = list(itertools.product([0, 1], repeat=8))


def build():
    m = pyo.ConcreteModel()
    m.a = pyo.Var(
        range(8),
        domain=pyo.Integers,
        bounds=lambda m, j: (1, COEFFICIENT_BOUND) if ORIGINAL[j] > 0 else (-COEFFICIENT_BOUND, -1),
    )
    m.b = pyo.Var(domain=pyo.Integers)
    m.B = pyo.Var(domain=pyo.NonNegativeReals)
    m.c = pyo.ConstraintList()
    for x in POINTS:
        lhs = sum(m.a[j] * x[j] for j in range(8))
        m.c.add(
            lhs <= m.b
            if sum(ORIGINAL[j] * x[j] for j in range(8)) <= 37
            else lhs >= m.b + 1
        )
    m.c.add(m.B >= m.b)
    m.c.add(m.B >= -m.b)
    m.obj = pyo.Objective(expr=m.B)
    return m


def check(m):
    a = [round(pyo.value(m.a[j])) for j in range(8)]
    b = round(pyo.value(m.b))
    assert all(
        (sum(ORIGINAL[j] * x[j] for j in range(8)) <= 37)
        == (sum(a[j] * x[j] for j in range(8)) <= b)
        for x in POINTS
    )


def tables(m):
    return {
        "coefficients": frame(
            [[f"x{j + 1}", ORIGINAL[j], pyo.value(m.a[j])] for j in range(8)]
            + [["RHS", 37, pyo.value(m.b)]],
            ["Term", "Original", "Equivalent"],
        )
    }


def plot(m):
    return (
        [f"x{j + 1}" for j in range(8)],
        [pyo.value(m.a[j]) for j in range(8)],
        "Equivalent signed coefficient",
    )

COEFFICIENT_BOUND=40
