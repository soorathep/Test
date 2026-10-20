"""Independent practice. Fill the None values, run, then compare answers.py.
Use the original A=[[1,1],[2,1]], c=[3,2], b=[4,5] unless stated.
All values are in hundreds of dollars, except the dollar questions.
"""
import numpy as np
from scipy.optimize import linprog
A = np.array([[1.,1.],[2.,1.]])
# Use linprog(-c, A_ub=A, b_ub=b, bounds=(0,None), method="highs").
# Check success before reading x, fun, or marginals.

# 1. b=(4.6,5). Predict and solve: x, y, z.
answer_1 = None

# 2. Reset b1=4; change b2 to 7. Find x, y, z.
answer_2 = None

# 3. Reset b=(4,5); change c=(4.5,2). Find x, y, z.
answer_3 = None

# 4. Original x,y products; add t with resource column (1,2)
#    and contribution 3.5. Find (x,y,t), z, and feasible dual prices.
answer_4 = None

# 5. Original model: buy q=1.4 extra units of resource 1 for $80/day.
#    Reoptimize. Report gross gain, net benefit, and buy/reject.
answer_5 = None

# 6. Original model: prices (u,v)=(0,2) give a bound of 10.
#    Are these prices dual feasible? Are they optimal? Explain.
answer_6 = None

for number in range(1,7):
    value = globals()[f"answer_{number}"]
    print(number, "Not attempted yet" if value is None else value)
