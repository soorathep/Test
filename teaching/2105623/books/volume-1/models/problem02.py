TITLE = "Blending with Logical Restrictions"
SOURCE = "Food manufacture 2"
ADAPTATION = "Retains the data and added logical restrictions in Sections 12.1–12.2. The holding-cost convention is the same as Chapter 1."
UNITS = "GBP over six months"
PROBLEM = """Use the five oils, prices, hardness indices, stocks, and refining capacities of Chapter 1. In each month, use at most three oils. If an oil is used, at least 20 t must be processed. Using either VEG1 or VEG2 requires using OIL3 in the same month. Maximize operating profit with the same final stocks. All quantities are tonnes. This chapter depends on the complete input tables in Chapter 1."""
FORMULATION = r"""Retain $b_{it},u_{it},s_{it},q_t$ and all equations of Chapter 1. Add binary $y_{it}$, equal to one if oil $i$ is used in month $t$. Let $M_i=200$ for vegetable oils and $250$ otherwise, using physical processing bounds rather than an arbitrary large constant.

$$20y_{it}\le u_{it}\le M_i y_{it},\qquad \sum_i y_{it}\le3.$$

$$y_{\mathrm{VEG1},t}\le y_{\mathrm{OIL3},t},\qquad y_{\mathrm{VEG2},t}\le y_{\mathrm{OIL3},t}.$$

The lower bound applies only when an oil is selected; setting $y=0$ forces zero consumption. The original profit objective is unchanged. The formulation is a mixed-integer linear program (MILP). The implication is one-way: OIL3 may be used without either vegetable oil."""
DISCUSSION = """The minimum lot size can exclude blends that were attractive in the continuous model. The additional constraints can only reduce or preserve the Chapter 1 optimum. A binary variable represents use during the month, not purchase or storage. Experiment: change the maximum number of oils from three to two and compare the objective and active ingredients."""
# MODEL CODE
import pyomo.environ as pyo
from models.food_manufacture import build_model, OILS, MONTHS, validate
from models.common import frame


def build():
    m = build_model()
    m.selected = pyo.Var(m.I, m.T, domain=pyo.Binary)
    m.minimum_lot = pyo.Constraint(
        m.I, m.T, rule=lambda m, i, t: m.use[i, t] >= 20 * m.selected[i, t]
    )
    m.link = pyo.Constraint(
        m.I,
        m.T,
        rule=lambda m, i, t: (
            m.use[i, t] <= (200 if i in m.V else 250) * m.selected[i, t]
        ),
    )
    m.count = pyo.Constraint(
        m.T, rule=lambda m, t: sum(m.selected[i, t] for i in m.I) <= 3
    )
    m.logic = pyo.Constraint(
        m.V, m.T, rule=lambda m, i, t: m.selected[i, t] <= m.selected["OIL3", t]
    )
    return m


def check(m):
    validate(m)
    for t in m.T:
        used = [i for i in OILS if pyo.value(m.use[i, t]) > 1e-6]
        assert len(used) <= 3
        assert all(pyo.value(m.use[i, t]) >= 20 - 1e-6 for i in used)
        assert not any(i.startswith("VEG") for i in used) or "OIL3" in used


def tables(m):
    return {
        name: frame(
            [
                [MONTHS[t - 1], *[pyo.value(getattr(m, name)[i, t]) for i in OILS]]
                for t in m.T
            ],
            ["Month", *OILS],
        )
        for name in ["use", "buy", "stock"]
    }


def plot(m):
    return (
        MONTHS,
        [sum(pyo.value(m.selected[i, t]) for i in OILS) for t in m.T],
        "Number of oils used",
    )
