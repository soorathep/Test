"""Answer key: attempt exercises.py before opening this file."""
import numpy as np
from scipy.optimize import linprog
A=np.array([[1.,1.],[2.,1.]])
def solve(c=(3,2),b=(4,5),matrix=A):
    r=linprog(-np.asarray(c,dtype=float),A_ub=matrix,b_ub=b,
              bounds=(0,None),method="highs")
    assert r.success,r.message
    return r
r=solve(b=(4.6,5))
assert np.allclose(r.x,[.4,4.2]) and np.isclose(-r.fun,9.6)
print("1:",r.x,"z =",-r.fun,"Old prices remain valid.")
r=solve(b=(4,7))
assert np.allclose(r.x,[3,1]) and np.isclose(-r.fun,11)
print("2:",r.x,"z =",-r.fun,"b2=7 lies inside [4,8].")
r=solve(c=(4.5,2))
assert np.allclose(r.x,[2.5,0]) and np.isclose(-r.fun,11.25)
print("3:",r.x,"z =",-r.fun,"c1=4.5 exceeds the old [2,4] range.")
A3=np.column_stack([A,[1,2]])
r=solve(c=(3,2,3.5),matrix=A3)
assert np.allclose(r.x,[0,3,1]) and np.isclose(-r.fun,9.5)
pi=np.array([.5,1.5])
assert np.all(A3.T@pi >= np.array([3,2,3.5])-1e-9)
assert np.isclose(np.dot([4,5],pi),9.5)
print("4:",r.x,"z =",-r.fun,"dual =",pi)
r=solve(b=(5.4,5))
gross=(-r.fun-9)*100;net=gross-80
assert np.isclose(gross,100) and np.isclose(net,20)
print("5: gross $",gross,"net $",net,"Buy under the stated assumptions.")
print("6: (0,2) is dual feasible and gives bound 10, but is not optimal.")
print("   (1,1) is feasible and gives 9, matching primal (1,3).")
