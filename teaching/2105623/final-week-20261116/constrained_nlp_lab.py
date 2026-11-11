"""Final-class example. Requires NumPy and SciPy. Run top to bottom."""
import numpy as np
from scipy.optimize import minimize

def objective(r):
    x,y=r
    return (x-3)**2+(y-2)**2

def gradient(r):
    return 2*(np.asarray(r)-[3,2])

def solve_capacity(b=3.0,start=(0.5,0.5)):
    constraint={"type":"ineq","fun":lambda r:b-r[0]-r[1],
                "jac":lambda r:np.array([-1.,-1.])}
    return minimize(objective,start,jac=gradient,method="SLSQP",
                    bounds=[(0,None),(0,None)],constraints=[constraint],
                    options={"ftol":1e-12,"maxiter":200})

def audit(r,b,multipliers):
    x,y=r
    lam=np.asarray(multipliers)
    g=np.array([x+y-b,-x,-y])
    normals=np.array([[1,1],[-1,0],[0,-1]])
    return {"objective":objective(r),
            "primal_violation":max(0.,float(np.max(g))),
            "dual_violation":max(0.,float(-np.min(lam))),
            "stationarity":float(np.max(np.abs(gradient(r)+lam@normals))),
            "complementarity":float(np.max(np.abs(lam*g)))}

if __name__=="__main__":
    for start in [(0.5,0.5),(3,2),(0,0),(4,0)]:
        result=solve_capacity(start=start)
        print("start",start,"success",result.success,"message",result.message)
        print("point",result.x,"audit",audit(result.x,3,[2,0,0]))
        assert result.success and np.allclose(result.x,[2,1],atol=1e-6)
    print("Sensitivity: compare actual values with V(3)-2*(b-3).")
    for b in [0.5,1,3,3.2,5,6]:
        result=solve_capacity(b)
        print("capacity",b,"point",result.x,"objective",result.fun)
    print("Try different starts and verify bounds, not only the capacity residual.")

# Independent piecewise certificate, including active lower bounds.
def analytic_capacity(b):
    if b < 0:
        raise ValueError('Capacity b must be nonnegative')
    if b <= 1:
        return np.array([b,0.]), np.array([6-2*b,0.,2-2*b])
    if b <= 5:
        return np.array([(b+1)/2,(b-1)/2]), np.array([5-b,0.,0.])
    return np.array([3.,2.]), np.zeros(3)

if __name__ == '__main__':
    print('\nFull analytic certificates compared with SLSQP')
    for b in [0.5,1.,3.,3.2,5.,6.]:
        expected, multipliers = analytic_capacity(b)
        result = solve_capacity(b)
        residuals = audit(result.x,b,multipliers)
        print('b',b,'expected',expected,'computed',result.x,'lambda',multipliers)
        print('status',result.success,result.message,'audit',residuals)
        assert result.success and np.allclose(result.x,expected,atol=1e-6)
        assert max(v for k,v in residuals.items() if k!='objective')<1e-6
    b0,b1=3.,3.2
    old,_=analytic_capacity(b0);new,_=analytic_capacity(b1)
    print('Value change: exact',objective(new)-objective(old),'linear',-2*(b1-b0))
    # This manual feasible path is not the SLSQP iteration trace.
    for alpha in [.1,.3,.5]:
        point=alpha*np.array([6.,4.])
        print('manual alpha',alpha,'point',point,'objective',objective(point),
              'feasible',point.sum()<=3+1e-12)
    s=.3;g=4*s*(s*s-1);h=12*s*s-4;p=-g/h
    print('nonconvex Newton','gradient',g,'Hessian',h,'direction',p,'slope',g*p)
    assert g*p>0
