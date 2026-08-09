"""Verify candidate c values: membership, fatness, Koenigs multiplier.

Reproduces the figures quoted in 2026-08-09-fractal-julia-vase-design.md section 2.1.
Settings below are the ones those figures were computed at (20000-iteration
membership, 800^2 area grid at 3000 iterations). Runtime is several minutes;
drop to N=420/nmax=400 for a fast smoke check, which shifts areas by <0.001.
"""
import numpy as np


def in_set(c, d=2, nmax=20000, R=4.0):
    """Critical orbit bounded? For z^d+c the critical point is 0."""
    z = 0j
    for n in range(nmax):
        z = z**d + c
        if abs(z) > R:
            return False, n
    return True, nmax

def area_frac(c, d=2, N=800, nmax=3000, R=4.0):
    """Fraction of disk |z|<2 whose orbit stays bounded = fatness of K_c."""
    ax = np.linspace(-2, 2, N)
    X, Y = np.meshgrid(ax, ax)
    Z = X + 1j * Y
    inside_disk = (np.abs(Z) < 2.0)
    Z = Z.copy()
    alive = inside_disk.copy()
    for _ in range(nmax):
        Z[alive] = Z[alive]**d + c
        esc = alive & (np.abs(Z) > R)
        alive &= ~esc
        Z[~alive] = 0
    return alive.sum() / inside_disk.sum()

def koenigs(c):
    """Repelling fixed point alpha of z^2+c and its multiplier mu=2*alpha."""
    a = (1 + np.sqrt(complex(1 - 4 * c))) / 2
    mu = 2 * a
    return a, mu

print("=== quadratic z^2+c candidates ===")
cands2 = {
    "basilica  c=-1":            -1 + 0j,
    "San Marco c=-0.75":         -0.75 + 0j,
    "rabbit    c=-0.123+0.745i": -0.123 + 0.745j,
    "Siegel    c=-0.3905-0.5868i": -0.3905408 - 0.5867879j,
    "MINE#2    c=-0.62+0.44i":   -0.62 + 0.44j,
    "MINE#1    c=-0.12+0.74i":   -0.12 + 0.74j,
    "popular   c=-0.8+0.156i":   -0.8 + 0.156j,
}
for name, c in cands2.items():
    ok, n = in_set(c)
    af = area_frac(c) if ok else 0.0
    a, mu = koenigs(c)
    print(f"{name:28s} inM={str(ok):5s} escN={n:6d} area={af:.4f} "
          f"alpha={a.real:+.4f}{a.imag:+.4f}i  |mu|={abs(mu):.4f} argmu={np.angle(mu):+.4f}rad")

print()
print("=== degree-6 multibrot z^6+c candidates (6-fold symmetry) ===")
for cr in [-0.5, -0.45, -0.4, -0.35, -0.3, -0.2, -0.1, 0.0, 0.2, 0.4, 0.5, 0.6]:
    c = complex(cr, 0)
    ok, n = in_set(c, d=6)
    af = area_frac(c, d=6) if ok else 0.0
    print(f"  z^6 + ({cr:+.2f})  inM={str(ok):5s} escN={n:6d} area={af:.4f}")

print()
print("=== golden-ratio check for basilica ===")
a, mu = koenigs(-1 + 0j)
phi = (1 + 5**0.5) / 2
print(f"  alpha       = {a.real:.10f}  (phi = {phi:.10f})  match={abs(a.real-phi)<1e-12}")
print(f"  mu          = {mu.real:.10f}  (1+sqrt5 = {1+5**0.5:.10f})")
print(f"  arg(mu)     = {np.angle(mu):.10f} rad  -> pure vertical repeat, no twist")
print(f"  log|mu|     = {np.log(abs(mu)):.6f}")
print(f"  scale ratio = {abs(mu):.4f}  (Salingaros optimal band 2-4, e={np.e:.4f})")
