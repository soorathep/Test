# Set up the notebook
import numpy as np
import scipy
from scipy.optimize import milp, Bounds, LinearConstraint
print("SciPy", scipy.__version__)

# Define the objective and variable order
c = np.array([-8., -6., 10., 8.])
integrality = [0, 0, 1, 1]
bounds = Bounds([0,0,0,0], [6,8,1,1])
print("Minimize negative net profit; only yA and yB are binary.")

# Build each row of the matrix
A = np.array([[2,1,0,0],
              [1,1,0,0],
              [1,0,-6,0],
              [0,1,0,-8]], dtype=float)
upper = np.array([12,10,0,0], dtype=float)
constraints = LinearConstraint(A, -np.inf, upper)
print(A)

# Solve and interpret status
result = milp(c, integrality=integrality, bounds=bounds,
              constraints=constraints, options={"mip_rel_gap":0})
print("Status:", result.status, result.message)
assert result.success
print("[a,b,yA,yB] =", result.x)
print("Net profit =", -result.fun)
print("Profit upper bound =", -result.mip_dual_bound)
print("MIP gap =", result.mip_gap)
assert np.isclose(-result.fun,46)

# Audit the result independently
v = result.x
tol = 1e-7
print("Row use:", A @ v)
print("Row slack:", upper - A @ v)
assert np.all(A @ v <= upper + tol)
assert np.all(v >= bounds.lb-tol) and np.all(v <= bounds.ub+tol)
assert np.allclose(v[2:], np.round(v[2:]), atol=tol)
profit = 8*v[0]+6*v[1]-10*v[2]-8*v[3]
assert np.isclose(profit,-result.fun)
print("All checks passed; net profit =",profit)

# Enumerate opening choices
from scipy.optimize import linprog
from itertools import product
records = []
for ya,yb in product([0,1], repeat=2):
    r = linprog([-8,-6], A_ub=[[2,1],[1,1]], b_ub=[12,10],
                bounds=[(0,6*ya),(0,8*yb)], method="highs")
    assert r.success
    z = -r.fun-10*ya-8*yb
    records.append(z)
    print((ya,yb), "production",r.x,"net profit",z)
assert np.isclose(max(records),46)

# Relax integrality
relaxed = milp(c, integrality=[0,0,0,0], bounds=bounds,
               constraints=constraints)
assert relaxed.success
print("Relaxed decisions:",relaxed.x)
print("LP upper bound:",-relaxed.fun)
assert np.isclose(-relaxed.fun,158/3)
assert -relaxed.fun >= -result.fun - tol

# Change one assumption at a time
def solve_case(sales=10, fixed_b=8, minimum_a=0, one_line=False):
    rows=A.copy(); rhs=upper.copy(); rhs[1]=sales
    if minimum_a:
        rows=np.vstack([rows,[-1,0,minimum_a,0]])
        rhs=np.r_[rhs,0]
    if one_line:
        rows=np.vstack([rows,[0,0,1,1]])
        rhs=np.r_[rhs,1]
    r=milp([-8,-6,10,fixed_b],integrality=integrality,bounds=bounds,
           constraints=LinearConstraint(rows,-np.inf,rhs),
           options={"mip_rel_gap":0})
    assert r.success
    return r
for label,kwargs,expected in [("Sales cap 8",{"sales":8},40),
                              ("B cost 20",{"fixed_b":20},38),
                              ("A minimum 3",{"minimum_a":3},42)]:
    r=solve_case(**kwargs)
    print(label,r.x,-r.fun)
    assert np.isclose(-r.fun,expected)

# Add a purchasable capacity module
def module_case(price=7, force=None):
    rows=np.column_stack([A,np.zeros(4)])
    rows[0,-1]=-4
    lb=[0,0,0,0,0]; ub=[6,8,1,1,1]
    if force is not None: lb[-1]=ub[-1]=force
    r=milp([-8,-6,10,8,price],integrality=[0,0,1,1,1],
           bounds=Bounds(lb,ub),constraints=LinearConstraint(rows,-np.inf,upper),
           options={"mip_rel_gap":0})
    assert r.success
    return r
for price in [7,8,9,10]:
    r=module_case(price)
    no=module_case(price,0); buy=module_case(price,1)
    print("Price",price,"best",-r.fun,"no buy",-no.fun,"buy",-buy.fun)
    assert np.isclose(-r.fun,max(-no.fun,-buy.fun))
assert np.isclose(-module_case(7).fun,47)
assert np.isclose(-module_case(9).fun,46)

# Complete independent exercises
print("Next: exercises.html and the online Exit Ticket.")
