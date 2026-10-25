# 1. Setup and prediction
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import skh_palette as skh
skh.use()
C = skh.C
np.set_printoptions(precision=8, suppress=True)

def f(x):
    u, v = np.asarray(x, dtype=float)
    return (u - 1)**2 + 4*(v + 2)**2

def grad(x):
    u, v = np.asarray(x, dtype=float)
    return np.array([2*(u - 1), 8*(v + 2)])

def hess(x):
    return np.diag([2.0, 8.0])

x0 = np.array([3.0, 0.0])
xstar = np.array([1.0, -2.0])
print("f(x0) =", f(x0))
print("gradient =", grad(x0))
print("Hessian =\n", hess(x0))
assert f(x0) == 20
np.testing.assert_allclose(grad(x0), [4,16])
np.testing.assert_allclose(np.linalg.eigvalsh(hess(x0)), [2,8])

# 2. Derivative checks
def fd_gradient(fun, x, eps=1e-6):
    eye = np.eye(len(x))
    return np.array([(fun(x+eps*d)-fun(x-eps*d))/(2*eps) for d in eye])

def fd_hessian(gradient, x, eps=1e-6):
    eye = np.eye(len(x))
    return np.column_stack([(gradient(x+eps*d)-gradient(x-eps*d))/(2*eps) for d in eye])

for x in [x0, np.array([-0.7, 1.2])]:
    ge = np.linalg.norm(fd_gradient(f,x)-grad(x))
    he = np.linalg.norm(fd_hessian(grad,x)-hess(x))
    print("x =", x, "gradient error =", ge, "Hessian error =", he)
    assert ge < 1e-6 and he < 1e-6

# 3. Two steps by hand and in Python
alpha = 0.1
x1 = x0-alpha*grad(x0)
x2 = x1-alpha*grad(x1)
for k,x in enumerate([x0,x1,x2]):
    print(k, "x =", x, "f =", f(x), "g =", grad(x))
np.testing.assert_allclose(x1,[2.6,-1.6])
np.testing.assert_allclose(x2,[2.28,-1.92])
np.testing.assert_allclose([f(x0),f(x1),f(x2)],[20,3.2,1.664])

# 4. A reusable fixed-step gradient loop
def fixed_gd(fun, gradient, initial, alpha, tol=1e-8, maxiter=3000):
    x = np.asarray(initial,dtype=float).copy()
    trace = []
    for k in range(maxiter+1):
        value = float(fun(x))
        g = np.asarray(gradient(x),dtype=float)
        norm = float(np.linalg.norm(g))
        trace.append((k, x.copy(), value, norm))
        if not np.isfinite(value) or not np.all(np.isfinite(g)):
            return trace, "nonfinite"
        if norm <= tol:
            return trace, "gradient_tolerance"
        if abs(value)>1e12:
            return trace, "large_objective_guard"
        if k == maxiter:
            return trace, "iteration_limit"
        x = x-alpha*g
    raise RuntimeError("Unreachable")

trace, reason = fixed_gd(f,grad,x0,0.1)
k,x,value,gnorm = trace[-1]
print("reason =", reason, "iterations =", k)
print("x =", x, "f =", value, "gradient norm =", gnorm)
assert reason == "gradient_tolerance"
np.testing.assert_allclose(x,xstar,atol=1e-7)
assert value < 1e-14

# 5. Paths and function values
path = np.array([row[1] for row in trace])
u,v = np.meshgrid(np.linspace(-0.3,3.7,150),np.linspace(-3.9,1,150))
z = (u-1)**2+4*(v+2)**2
fig,axs = plt.subplots(1,2,figsize=(10,4))
axs[0].contour(u,v,z,levels=[0.2,0.5,1,2,4,8,16,24],colors=C['teal'],linewidths=1.5)
axs[0].plot(path[:,0],path[:,1],'-o',color=C['amber'],lw=2,ms=4)
axs[0].plot([1],[-2],'*',color=C['graphite'],ms=12)
axs[0].set(xlabel='u',ylabel='v',title='Gradient descent, alpha=0.1')
axs[1].semilogy([r[0] for r in trace],[max(r[2],1e-30) for r in trace],color=C['teal'],lw=2)
axs[1].set(xlabel='Iteration',ylabel='f(x)-f*',title='Objective error')
plt.tight_layout()
plt.show()

# 6. Fixed step-size experiments
runs = {}
for alpha in [0.05,0.1,0.24,0.25,0.3]:
    tr,rs = fixed_gd(f,grad,x0,alpha)
    runs[alpha]=(tr,rs)
    k,x,val,gn=tr[-1]
    print(f"alpha={alpha:.2f}  {rs:23s}  k={k:4d}  f={val:.6g}  ||g||={gn:.6g}")
assert runs[0.1][1]=='gradient_tolerance'
assert runs[0.24][1]=='gradient_tolerance'
assert runs[0.25][1]=='iteration_limit'
assert runs[0.3][1]=='large_objective_guard'
np.testing.assert_allclose(runs[0.25][0][-1][2],16,atol=1e-9)

fig,ax=plt.subplots(figsize=(7,4))
for alpha,color,style in [(0.1,C['teal'],'-'),(0.25,C['amber'],'--'),(0.3,C['graphite'],':')]:
    tr=runs[alpha][0][:36]
    ax.semilogy([r[0] for r in tr],[max(r[2],1e-30) for r in tr],color=color,ls=style,lw=2,label=f'alpha={alpha}')
ax.set(xlabel='Iteration',ylabel='f(x)-f*',title='Same starting point for every run')
ax.legend()
plt.tight_layout()
plt.show()

# 7. Newton and a solver reference
p = np.linalg.solve(hess(x0),-grad(x0))
xnew = x0+p
print("p =",p, "xnew =",xnew,"f =",f(xnew))
np.testing.assert_allclose(p,[-2,-2])
np.testing.assert_allclose(xnew,xstar)
assert f(xnew)==0

reference = minimize(f,x0,method='trust-exact',jac=grad,hess=hess,options={'gtol':1e-9})
print("SciPy:",reference.success,reference.message)
print("x =",reference.x,"f =",reference.fun,"gradient norm =",np.linalg.norm(grad(reference.x)))
assert reference.success
np.testing.assert_allclose(reference.x,xstar,atol=1e-7)

# 8. Nonconvex starting points
def q(x):
    t=float(x[0]); return (t*t-1)**2

def qgrad(x):
    t=float(x[0]); return np.array([4*t*(t*t-1)])

def qsecond(t): return 12*t*t-4

for start in [-1.5,-0.2,0,0.2,1.5]:
    tr,rs=fixed_gd(q,qgrad,[start],0.05)
    k,x,val,gn=tr[-1]; curvature=qsecond(x[0])
    kind='strict local minimum' if curvature>0 else 'strict local maximum' if curvature<0 else 'inconclusive'
    print(f"start={start:4.1f} end={x[0]: .8f} f={val:.5g} H={curvature:.5g} {rs}: {kind}")
    if start==0: assert x[0]==0 and val==1 and curvature==-4
    else: assert abs(abs(x[0])-1)<1e-7 and val<1e-14
# At +/-1, q=0 and q is nonnegative everywhere: these minima are global.

# 9. A failed Newton step
start=0.2
g0=qgrad([start])[0]
H0=qsecond(start)
p=-g0/H0
new=start+p
print("gradient =",g0,"Hessian =",H0,"direction =",p,"g*p =",g0*p)
print("old x, f:",start,q([start]),"new x, f:",new,q([new]))
np.testing.assert_allclose(new,-1/55)
assert g0*p>0 and q([new])>q([start])
xx=np.linspace(-1.5,1.5,400)
fig,ax=plt.subplots(figsize=(7,4))
ax.plot(xx,(xx**2-1)**2,color=C['teal'],lw=2,label='q(x)')
ax.scatter([start,new],[q([start]),q([new])],color=[C['teal'],C['amber']],s=55)
ax.annotate('Newton step',xy=(new,q([new])),xytext=(-1.2,1.5),arrowprops={'arrowstyle':'->','color':C['graphite']})
ax.set(xlabel='x',ylabel='q(x)',title='A step toward the local maximum')
plt.tight_layout()
plt.show()

# 10. Independent practice checks
H=np.array([[2.,2.],[2.,6.]])
c=np.array([-4.,-8.])
solution=np.linalg.solve(H,-c)
value=0.5*solution@H@solution+c@solution+7
print("Practice A:",solution,"value =",value,"eigenvalues =",np.linalg.eigvalsh(H))
np.testing.assert_allclose(solution,[1,1])
np.testing.assert_allclose(value,1)
np.testing.assert_allclose(np.linalg.eigvalsh(H),[4-2*np.sqrt(2),4+2*np.sqrt(2)])

x=2.; direction=-(4*x**3+2*x)/(12*x*x+2); xnew=x+direction
print("Practice B:","p =",direction,"xnew =",xnew,"value =",xnew**4+xnew*xnew)
np.testing.assert_allclose(xnew,1.28)
np.testing.assert_allclose(xnew**4+xnew*xnew,4.32275456)
print("Practice C: x^4 has a minimum and -x^4 a maximum at 0, although both first and second derivatives vanish there.")