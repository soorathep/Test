TITLE = "Order-Preserving Protein Contact-Map Comparison"
SOURCE = "Protein comparison"
ADAPTATION = "New five-residue versus six-residue contact-map instance; permits partial order-preserving matching and maximizes conserved contacts."
UNITS = "conserved contact edges"
PROBLEM = """Protein A has five ordered residues 1–5 and contacts (1,3), (1,4), (2,4), (3,5). Protein B has six ordered residues 1–6 and contacts (1,3), (1,5), (2,4), (3,5), (4,6). Match any subset of A residues to distinct B residues while preserving sequence order. Unmatched residues are allowed. A contact is conserved when both endpoints of an A contact map to the endpoints of a B contact. Maximize the number of conserved contacts. Extra contacts in either protein are allowed; this is not an induced-subgraph requirement."""
FORMULATION = r"""Binary $x_{ij}$ matches residue $i$ of A to residue $j$ of B. Require $\sum_jx_{ij}\le1$ and $\sum_ix_{ij}\le1$. For $i<k$ and $j\ge l$, forbid crossing or reversed matches with $x_{ij}+x_{kl}\le1$.

For each contact $(i,k)$ in A and $(j,l)$ in B, with both edges oriented in increasing order, introduce $z_{ikjl}\in[0,1]$ and impose $z\le x_{ij}$, $z\le x_{kl}$, $z\ge x_{ij}+x_{kl}-1$. Maximize $\sum z$. Binary endpoint matches force exact conserved-edge indicators. Partial matching permits deletions or insertions while the ordering constraints preserve the sequence."""
DISCUSSION = """Matching many residues is different from preserving many contacts. The objective gives no reward for an isolated matched residue, so equally optimal alignments may differ in their unmatched positions. A secondary objective could maximize matched residues after fixing the best contact score. Experiment: remove order preservation and assess how much the score improves at the cost of losing a sequence-consistent interpretation."""
# MODEL CODE
import itertools
import pyomo.environ as pyo
from models.common import frame

EA = [(0, 2), (0, 3), (1, 3), (2, 4)]
EB = [(0, 2), (0, 4), (1, 3), (2, 4), (3, 5)]


def build():
    m = pyo.ConcreteModel()
    m.I = pyo.RangeSet(0, 4)
    m.J = pyo.RangeSet(0, 5)
    keys = [(i, k, j, l) for i, k in EA for j, l in EB]
    m.x = pyo.Var(m.I, m.J, domain=pyo.Binary)
    m.z = pyo.Var(keys, bounds=(0, 1))
    m.c = pyo.ConstraintList()
    for i in m.I:
        m.c.add(sum(m.x[i, j] for j in m.J) <= 1)
    for j in m.J:
        m.c.add(sum(m.x[i, j] for i in m.I) <= 1)
    for i, k in itertools.combinations(m.I, 2):
        for j in m.J:
            for l in m.J:
                if j >= l:
                    m.c.add(m.x[i, j] + m.x[k, l] <= 1)
    for i, k, j, l in keys:
        m.c.add(m.z[i, k, j, l] <= m.x[i, j])
        m.c.add(m.z[i, k, j, l] <= m.x[k, l])
        m.c.add(m.z[i, k, j, l] >= m.x[i, j] + m.x[k, l] - 1)
    m.obj = pyo.Objective(expr=sum(m.z[key] for key in keys), sense=pyo.maximize)
    return m


def alignment(m):
    return {i: j for i in m.I for j in m.J if pyo.value(m.x[i, j]) > 0.5}


def check(m):
    best = 0
    for size in range(6):
        for aa in itertools.combinations(range(5), size):
            for bb in itertools.combinations(range(6), size):
                mapping = dict(zip(aa, bb))
                best = max(
                    best,
                    sum(
                        i in mapping and k in mapping and (mapping[i], mapping[k]) in EB
                        for i, k in EA
                    ),
                )
    mapping = alignment(m)
    assert all(
        mapping[i] < mapping[k] for i, k in itertools.combinations(sorted(mapping), 2)
    )
    assert abs(pyo.value(m.obj) - best) < 1e-6


def tables(m):
    a = alignment(m)
    return {
        "alignment": frame(
            [[i + 1, j + 1] for i, j in a.items()], ["Residue in A", "Residue in B"]
        ),
        "conserved": frame(
            [
                [i + 1, k + 1, a[i] + 1, a[k] + 1]
                for i, k in EA
                if i in a and k in a and (a[i], a[k]) in EB
            ],
            ["A start", "A end", "B start", "B end"],
        ),
    }


def plot(m):
    a = alignment(m)
    return (
        ["A contacts", "B contacts", "Conserved contacts"],
        [len(EA), len(EB), pyo.value(m.obj)],
        "Contact edges",
    )
