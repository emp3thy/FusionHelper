"""Prototype the log-polar field. Checks the mapping actually lands on the set."""
import numpy as np

C = -0.123 + 0.745j
ALPHA = (1 + np.sqrt(complex(1 - 4 * C))) / 2
MU = 2 * ALPHA
LNMU, ARGMU = np.log(abs(MU)), np.angle(MU)

Z_LO, Z_HI, P = 40.0, 240.0, 4
DH = (Z_HI - Z_LO) / P
K = LNMU / DH


def smooth_nu(z0, max_iter=100, R=128.0):
    """Renormalised escape time. Interior -> max_iter."""
    z = z0.astype(np.complex128).copy()
    nu = np.full(z0.shape, float(max_iter))
    alive = np.ones(z0.shape, bool)
    for n in range(max_iter):
        z[alive] = z[alive] ** 2 + C
        mag = np.abs(z)
        esc = alive & (mag > R)
        if esc.any():
            nu[esc] = n + 1 - np.log(np.log(mag[esc])) / np.log(2.0)
            alive &= ~esc
        if not alive.any():
            break
    return nu, alive


def field(ntheta, nz, zeta_min=0.02):
    th = np.linspace(0, 2 * np.pi, ntheta, endpoint=False)
    hh = np.linspace(Z_LO, Z_HI, nz)
    T, H = np.meshgrid(th, hh, indexing="ij")
    u = np.log(zeta_min) + K * (H - Z_LO)
    v = T + (ARGMU / LNMU) * K * (H - Z_LO)
    zc = ALPHA + np.exp(u + 1j * v)
    return smooth_nu(zc), zc


print(f"alpha = {ALPHA:.6f}   |mu| = {abs(MU):.6f}   arg mu = {ARGMU:.6f}")
print(f"k = {K:.7f} /mm   period = {DH} mm")

(nu, interior), zc = field(256, 200)
print(f"\n|zeta| range   : {abs(zc - ALPHA).min():.4f} .. {abs(zc - ALPHA).max():.4f}")
print(f"|z| range      : {abs(zc).min():.4f} .. {abs(zc).max():.4f}")
print(f"interior frac  : {interior.mean():.4f}   <- want neither 0 nor 1")
print(f"nu range       : {nu.min():.3f} .. {nu.max():.3f}")

esc = nu[~interior]
if esc.size:
    print(f"escaped nu     : {esc.min():.3f} .. {esc.max():.3f}, "
          f"std {esc.std():.3f}  <- want real spread")

# does the field actually repeat with the Koenigs period + twist?
h0, h1 = 60.0, 60.0 + DH
th = np.linspace(0, 2 * np.pi, 512, endpoint=False)


def ring(h, theta):
    u = np.log(0.02) + K * (h - Z_LO)
    v = theta + (ARGMU / LNMU) * K * (h - Z_LO)
    return smooth_nu(ALPHA + np.exp(u + 1j * v))[0]


r0 = ring(h0, th)
r1 = ring(h1, th)
print(f"\nself-similarity across one {DH:.0f}mm period:")
print(f"  correlation r0 vs r1 = {np.corrcoef(r0, r1)[0, 1]:.4f}  <- want high")
rolled = np.corrcoef(r0, np.roll(r1, 13))[0, 1]
print(f"  vs mis-rolled control = {rolled:.4f}")

# seam closure: theta=0 and theta=2pi must agree exactly
a = ring(120.0, np.array([0.0]))
b = ring(120.0, np.array([2 * np.pi]))
print(f"\nseam: nu(theta=0) = {a[0]:.9f}  nu(theta=2pi) = {b[0]:.9f}  "
      f"delta = {abs(a[0]-b[0]):.2e}")
