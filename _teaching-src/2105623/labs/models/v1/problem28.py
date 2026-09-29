TITLE = "Hydrophobic Contact Maximization on a Lattice"
SOURCE = "Protein folding"
ADAPTATION = "New eight-residue, two-dimensional square-lattice HP toy model. Explicitly replaces the source 50-residue non-lattice example."
UNITS = "nonbonded hydrophobic contacts"
PROBLEM = """Fold the sequence H–P–H–H–P–P–H–H on a two-dimensional square lattice. Consecutive residues occupy adjacent lattice sites, no site may contain two residues, and a contact is a pair of H residues at Manhattan distance one that are not consecutive along the chain. Maximize the number of contacts, equivalent to minimizing energy of −1 per contact. Fix residue 1 at (0,0) and residue 2 at (1,0) to remove translation and rotation. Reflections remain allowed. This model illustrates a discrete optimization idea; it is not a realistic protein-structure predictor."""
FORMULATION = r"""Enumerate all self-avoiding lattice conformations of this eight-residue chain with the first bond fixed. Let $K$ be this finite set and $c_k$ the number of nonbonded H–H contacts in conformation $k$.

$$\sum_{k\in K}y_k=1,\qquad y_k\in\{0,1\},\qquad\max\sum_{k\in K}c_ky_k.$$

The enumeration enforces chain connectivity and excluded volume before the optimization is built. The one-hot model selects a configuration; it is an exact but deliberately elementary formulation for this small lattice problem. It is not a scalable residue-placement MILP and makes no claim about the source non-lattice model."""
DISCUSSION = """Excluding covalently adjacent residues prevents every H–H bond from being counted as a folding benefit. Several conformations can share the best contact score. Enumeration grows rapidly with chain length; the small example makes the feasible set and contact definition auditable. Experiment: change one polar residue to H and compare both the optimal score and geometry."""
# MODEL CODE
import pyomo.environ as pyo
from models.v1.common import frame

SEQUENCE = "HPHHPPHH"
CONFORMATIONS = []


def enumerate_paths(path):
    if len(path) == len(SEQUENCE):
        CONFORMATIONS.append(tuple(path))
        return
    x, y = path[-1]
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        point = (x + dx, y + dy)
        if point not in path:
            enumerate_paths(path + [point])


enumerate_paths([(0, 0), (1, 0)])


def contacts(path):
    return [
        (i, j)
        for i in range(len(path))
        for j in range(i + 2, len(path))
        if SEQUENCE[i] == SEQUENCE[j] == "H"
        and sum(abs(path[i][k] - path[j][k]) for k in [0, 1]) == 1
    ]


def build():
    m = pyo.ConcreteModel()
    m.K = pyo.RangeSet(0, len(CONFORMATIONS) - 1)
    m.y = pyo.Var(m.K, domain=pyo.Binary)
    m.one = pyo.Constraint(expr=sum(m.y[k] for k in m.K) == 1)
    m.obj = pyo.Objective(
        expr=sum(len(contacts(path)) * m.y[k] for k, path in enumerate(CONFORMATIONS)),
        sense=pyo.maximize,
    )
    return m


def chosen(m):
    return CONFORMATIONS[next(k for k in m.K if pyo.value(m.y[k]) > 0.5)]


def check(m):
    path = chosen(m)
    assert len(set(path)) == 8
    assert all(
        sum(abs(a[k] - b[k]) for k in [0, 1]) == 1 for a, b in zip(path, path[1:])
    )
    assert len(contacts(path)) == max(map(lambda p: len(contacts(p)), CONFORMATIONS))


def tables(m):
    path = chosen(m)
    return {
        "conformation": frame(
            [[i + 1, SEQUENCE[i], *point] for i, point in enumerate(path)],
            ["Residue", "Type", "x", "y"],
        ),
        "contacts": frame(
            [[i + 1, j + 1] for i, j in contacts(path)], ["Residue i", "Residue j"]
        ),
        "enumeration": frame(
            [[len(CONFORMATIONS), pyo.value(m.obj)]],
            ["Conformations tested", "Maximum contacts"],
        ),
    }


def plot(m):
    path = chosen(m)
    return (
        [str(i + 1) for i in range(8)],
        [sum(i in pair for pair in contacts(path)) for i in range(8)],
        "Nonbonded H contacts per residue",
    )
