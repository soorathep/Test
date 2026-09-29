TITLE = "Robust Calibration by Linear Programming"
SOURCE = "Curve fitting"
ADAPTATION = "New eight-point sensor-calibration dataset; compares straight and quadratic curves under absolute and maximum absolute error."
UNITS = "sum of absolute response errors for the reference fit"
PROBLEM = """Calibrate a sensor from input x=[0,1,2,3,4,5,6,7] and response y=[1.0,1.7,2.8,3.1,7.5,4.8,5.5,6.2]. Input and response use normalized laboratory units. Fit (a) a straight line and (b) a quadratic curve, using both minimum total absolute error (L1) and minimum maximum absolute error (L-infinity). No coefficient bounds or monotonicity restrictions are imposed. The unusually large response at x=4 is retained, not silently discarded. The reference objective reported below is the straight-line L1 fit."""
FORMULATION = r"""For fixed data $x_j,y_j$, let $\hat y_j=a+bx_j+cx_j^2$, setting $c=0$ for a line. Coefficients are unrestricted real variables. Introduce $e_j\ge0$ with

$$e_j\ge y_j-\hat y_j,\qquad e_j\ge\hat y_j-y_j.$$

For L1 minimize $\sum_j e_j$. For L-infinity introduce $E\ge e_j$ for every observation and minimize $E$. Both problems are LPs, even for a quadratic curve, because $x_j^2$ is known data. A curve nonlinear in its input is not necessarily nonlinear in its fitted coefficients."""
DISCUSSION = """The L-infinity fit spreads the worst error, while L1 does not square large residuals. Neither method establishes that the high reading is erroneous. The quadratic may improve fit without being a better extrapolation model. Experiment: remove the high observation only as a labeled sensitivity case and compare coefficients."""
# MODEL CODE
import pyomo.environ as pyo
from models.v1.common import frame, solve

X = list(range(8))
Y = [1, 1.7, 2.8, 3.1, 7.5, 4.8, 5.5, 6.2]


def build(degree=1, norm="L1"):
    m = pyo.ConcreteModel()
    m.J = pyo.RangeSet(0, 7)
    m.K = pyo.RangeSet(0, degree)
    m.beta = pyo.Var(m.K, domain=pyo.Reals)
    m.e = pyo.Var(m.J, domain=pyo.NonNegativeReals)
    m.E = pyo.Var(domain=pyo.NonNegativeReals)
    m.fit = pyo.Expression(
        m.J, rule=lambda m, j: sum(m.beta[k] * X[j] ** k for k in m.K)
    )
    m.pos = pyo.Constraint(m.J, rule=lambda m, j: m.e[j] >= Y[j] - m.fit[j])
    m.neg = pyo.Constraint(m.J, rule=lambda m, j: m.e[j] >= m.fit[j] - Y[j])
    m.maximum = pyo.Constraint(m.J, rule=lambda m, j: m.E >= m.e[j])
    m.obj = pyo.Objective(expr=sum(m.e[j] for j in m.J) if norm == "L1" else m.E)
    return m


def check(m):
    assert (
        abs(sum(abs(Y[j] - pyo.value(m.fit[j])) for j in m.J) - pyo.value(m.obj)) < 1e-6
    )


def tables(m):
    rows = []
    for degree in [1, 2]:
        for norm in ["L1", "Linf"]:
            a = solve(build(degree, norm))
            residual = [abs(Y[j] - pyo.value(a.fit[j])) for j in a.J]
            rows.append(
                [
                    degree,
                    norm,
                    *[pyo.value(a.beta[k]) if k in a.K else 0 for k in range(3)],
                    sum(residual),
                    max(residual),
                ]
            )
    return {
        "fits": frame(
            rows,
            ["Degree", "Loss", "a", "b", "c", "Total absolute error", "Maximum error"],
        ),
        "observations": frame(
            [
                [X[j], Y[j], pyo.value(m.fit[j]), Y[j] - pyo.value(m.fit[j])]
                for j in m.J
            ],
            ["Input", "Observed response", "Reference prediction", "Residual"],
        ),
    }


def plot(m):
    return (
        [str(x) for x in X],
        [Y[j] - pyo.value(m.fit[j]) for j in m.J],
        "Reference residual (response units)",
    )
