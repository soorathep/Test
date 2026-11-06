"""Line search lab. Python standard library only. Run top to bottom."""
from math import isfinite, sqrt

def objective(r):
    u, v = r
    return (u - 1)**2 + 4*(v + 2)**2

def gradient(r):
    u, v = r
    return [2*(u-1), 8*(v+2)]

def backtracking(r, p, c1=0.1, rho=0.5, max_trials=40):
    if not (0 < c1 < 1 and 0 < rho < 1):
        raise ValueError("Require 0 < c1,rho < 1")
    g = gradient(r)
    slope = sum(a*b for a,b in zip(g,p))
    if not isfinite(slope) or slope >= 0:
        raise ValueError("Require a finite descent direction; classify zero gradient separately")
    alpha = 1.0
    trace = []
    for trial in range(max_trials):
        candidate = [x + alpha*d for x,d in zip(r,p)]
        actual = objective(candidate)
        target = objective(r) + c1*alpha*slope
        accepted = isfinite(actual) and actual <= target
        trace.append((alpha, actual, target, accepted))
        if accepted:
            return candidate, alpha, trace
        alpha *= rho
    raise RuntimeError("No step accepted within the trial limit")

def solve(start=(3.0,0.0), c1=0.1, rho=0.5, tol=1e-8, max_iterations=1000):
    r = list(start)
    history = [(0, r[:], objective(r))]
    trials = []
    for k in range(max_iterations):
        g = gradient(r)
        if not all(isfinite(x) for x in r+g):
            return r, history, trials, "nonfinite values"
        if sqrt(sum(x*x for x in g)) <= tol:
            return r, history, trials, "gradient tolerance"
        r, alpha, trace = backtracking(r, [-x for x in g], c1, rho)
        trials.append(trace)
        history.append((k+1,r[:],objective(r)))
    return r, history, trials, "iteration limit"

if __name__ == "__main__":
    r, history, trials, reason = solve()
    for k, trace in enumerate(trials):
        print(f"Iteration {k}: alpha | actual | target | accepted")
        for alpha, actual, target, accepted in trace:
            print(f"{alpha:.6g} | {actual:.6g} | {target:.6g} | {accepted}")
    print("History:", history)
    print("Stop:", reason, "gradient:", gradient(r))
    assert history[1][1] == [2.5,-2.0]
    assert r == [1.0,-2.0]
    assert [row[0] for row in trials[0]] == [1,.5,.25,.125]
    print("Practice: rerun solve(start=(0,0)); then change c1 to 0.4.")
