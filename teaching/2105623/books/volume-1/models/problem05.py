TITLE = "Workforce Planning and Retraining"
SOURCE = "Manpower planning"
ADAPTATION = "New two-skill, three-year plant workforce instance; deterministic attrition and continuous full-time equivalents replace the larger source workforce."
UNITS = "thousand USD"
PROBLEM = """A plant initially employs 40 general and 20 skilled full-time equivalents (FTE). At the start of each year 10% of each skill group leaves through natural attrition. After this, the plant may hire, lay off, or train general staff into skilled staff. Training is completed before that year’s operations. Required (general,skilled) FTE in years 1–3 are (30,25), (25,30), (20,35). Annual hiring limits are 8 general and 5 skilled FTE, with costs 3 and 8 thousand USD/FTE. Training costs 4 per FTE, is limited to 6 FTE/year, and can use only surviving general staff, not new hires. Layoffs cost 5 per FTE. Surplus operating staff cost 2 per FTE-year. Ordinary wages are excluded. Minimize total adjustment and surplus cost. FTE are continuous planning averages; no integer headcount interpretation is intended."""
FORMULATION = r"""For skill $g$ and year $t$, use closing workforce $w_{gt}$, hires $h_{gt}$, layoffs $l_{gt}$, and general-to-skilled training $v_t$, all nonnegative FTE. With retention $\rho=0.9$,

$$w_{Gt}=\rho w_{G,t-1}+h_{Gt}-l_{Gt}-v_t,\quad w_{St}=\rho w_{S,t-1}+h_{St}-l_{St}+v_t.$$

Require $w_{gt}\ge D_{gt}$, hiring limits, $v_t\le6$, and $v_t+l_{Gt}\le\rho w_{G,t-1}$. Also $l_{St}\le\rho w_{S,t-1}$, so newly hired or trained staff are not immediately laid off.

$$\min\sum_t\left[3h_{Gt}+8h_{St}+5\sum_g l_{gt}+4v_t+2\sum_g(w_{gt}-D_{gt})\right].$$

Demand is a minimum staffing requirement. Explicit event timing makes the attrition and training equations unambiguous."""
DISCUSSION = """Retraining preserves workforce while meeting a shift toward skilled operations, but its cost must be compared with hiring, attrition, and temporary surplus. Fractional FTE are acceptable for strategic averages; a detailed roster would need integer people and a different attrition treatment. Experiment: halve training capacity and measure the cost increase."""
# MODEL CODE
import pyomo.environ as pyo
from models.common import frame

D = {"G": [30, 25, 20], "S": [25, 30, 35]}
INITIAL = {"G": 40, "S": 20}


def build():
    m = pyo.ConcreteModel()
    m.T = pyo.RangeSet(0, 2)
    m.G = pyo.Set(initialize=["G", "S"])
    m.w = pyo.Var(m.G, m.T, domain=pyo.NonNegativeReals)
    m.h = pyo.Var(m.G, m.T, domain=pyo.NonNegativeReals)
    m.l = pyo.Var(m.G, m.T, domain=pyo.NonNegativeReals)
    m.v = pyo.Var(m.T, bounds=(0, 6))
    m.c = pyo.ConstraintList()
    for t in m.T:
        old = {g: 0.9 * (m.w[g, t - 1] if t else INITIAL[g]) for g in m.G}
        for g in m.G:
            m.c.add(
                m.w[g, t]
                == old[g] + m.h[g, t] - m.l[g, t] + (1 if g == "S" else -1) * m.v[t]
            )
            m.c.add(m.w[g, t] >= D[g][t])
            m.c.add(m.h[g, t] <= (8 if g == "G" else 5))
        m.c.add(m.v[t] + m.l["G", t] <= old["G"])
        m.c.add(m.l["S", t] <= old["S"])
    m.obj = pyo.Objective(
        expr=sum(
            (3 if g == "G" else 8) * m.h[g, t]
            + 5 * m.l[g, t]
            + 2 * (m.w[g, t] - D[g][t])
            for g in m.G
            for t in m.T
        )
        + 4 * sum(m.v[t] for t in m.T)
    )
    return m


def check(m):
    for t in m.T:
        previous = sum(pyo.value(m.w[g, t - 1]) if t else INITIAL[g] for g in m.G)
        assert (
            abs(
                sum(pyo.value(m.w[g, t] - m.h[g, t] + m.l[g, t]) for g in m.G)
                - 0.9 * previous
            )
            < 1e-6
        )


def tables(m):
    return {
        "workforce": frame(
            [
                [
                    t + 1,
                    g,
                    pyo.value(m.w[g, t]),
                    D[g][t],
                    pyo.value(m.h[g, t]),
                    pyo.value(m.l[g, t]),
                ]
                for t in m.T
                for g in m.G
            ],
            [
                "Year",
                "Skill",
                "Workforce (FTE)",
                "Required (FTE)",
                "Hired (FTE)",
                "Laid off (FTE)",
            ],
        ),
        "training": frame(
            [[t + 1, pyo.value(m.v[t])] for t in m.T], ["Year", "Retrained (FTE)"]
        ),
    }


def plot(m):
    return (
        ["Year 1", "Year 2", "Year 3"],
        [pyo.value(m.v[t]) for t in m.T],
        "Retrained staff (FTE)",
    )
