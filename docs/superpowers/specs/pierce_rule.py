"""The spec's piercing rule gives ONE connected hole, not a lattice.

nu_hat = 1 on the interior of K_c and high near its boundary, and K_c is
connected by construction (that is why the rabbit was chosen). So
"pierce where nu_hat > t" selects one connected mass. Test the alternatives.
"""
import numpy as np
from scipy import ndimage

from fractalvase.config import DOUADY_HELIX as C
from fractalvase.julia import normalised_field
from fractalvase.profile import radius_at

BAND_LO, BAND_HI, NZ = 150.0, 225.0, 200

full = normalised_field(C, C.n_theta, C.n_z)
zf = np.linspace(C.band_lo, C.band_hi, C.n_z)
z = np.linspace(BAND_LO, BAND_HI, NZ)
F = full[:, np.searchsorted(zf, z).clip(0, C.n_z - 1)]
dz = float(z[1] - z[0])
dth = 2 * np.pi / C.n_theta


def analyse(mask, name):
    labels, _ = ndimage.label(mask)
    for j in range(mask.shape[1]):
        a, b = labels[0, j], labels[-1, j]
        if a and b and a != b:
            labels[labels == b] = a
    stats = []
    for lab in np.unique(labels):
        if lab == 0:
            continue
        ti, zi = np.nonzero(labels == lab)
        zc = float(z[int(round(zi.mean()))])
        r = float(radius_at(np.array([zc]))[0])
        stats.append(((np.ptp(zi) + 1) * dz, (np.ptp(ti) + 1) * dth * r))
    if not stats:
        print(f"  {name:34s} open {100*mask.mean():5.2f}%  NO regions")
        return
    sz = np.array([s[0] for s in stats])
    ar = np.array([s[1] for s in stats])
    usable = ((sz >= C.min_ligament) & (ar >= C.min_ligament)
              & (sz <= C.max_hole_span) & (ar <= C.max_hole_span)).sum()
    print(f"  {name:34s} open {100*mask.mean():5.2f}%  {len(stats):5d} regions  "
          f"median {np.median(sz):5.2f}x{np.median(ar):5.2f}mm  "
          f"max {sz.max():6.2f}x{ar.max():6.2f}  usable {usable:4d}")


print("SPEC RULE -- pierce where the field is HIGH (nu_hat > t):")
for t in (0.62, 0.80, 0.90):
    analyse(t < F, f"nu_hat > {t}")

print("\nINVERTED -- pierce where the field is LOW (deep exterior, t < nu_hat):")
for t in (0.05, 0.10, 0.15, 0.20, 0.30):
    analyse(t > F, f"nu_hat < {t}")

print("\nBAND -- pierce a mid range (a < nu_hat < b):")
for a, b in ((0.20, 0.35), (0.30, 0.45), (0.40, 0.55), (0.25, 0.40)):
    analyse((a < F) & (b > F), f"{a} < nu_hat < {b}")

print(f"\nmin_ligament {C.min_ligament} mm, max_hole_span {C.max_hole_span} mm")
print("'usable' = regions within BOTH bounds in z and arc.")
