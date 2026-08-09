"""The mapping was wrong once already (see spec 2.3). These tests pin it."""
import numpy as np
import pytest

from fractalvase.config import DOUADY_HELIX
from fractalvase.julia import koenigs_grid, normalised_field, smooth_escape

CFG = DOUADY_HELIX


def test_smooth_escape_interior_is_flagged():
    # 0 is the critical point; for c in M its orbit stays bounded
    nu, interior = smooth_escape(np.array([0j]), CFG)
    assert interior[0]


def test_smooth_escape_far_point_escapes_immediately():
    nu, interior = smooth_escape(np.array([1000 + 0j]), CFG)
    assert not interior[0]
    assert nu[0] < 2.0


def test_smooth_escape_is_continuous_not_terraced():
    """Integer iteration count steps; the renormalised count must not."""
    r = np.linspace(1.40, 1.60, 4000)
    nu, interior = smooth_escape(r.astype(complex), CFG)
    outside = ~interior
    jumps = np.abs(np.diff(nu[outside]))
    # a terraced field jumps by ~1.0 at every band edge
    assert jumps.max() < 0.5, f"field is terracing: max jump {jumps.max()}"


def test_koenigs_grid_lands_on_the_set_not_miles_away():
    """The bug that was caught: an origin-centred map puts every sample outside."""
    zc = koenigs_grid(CFG, 128, 100)
    zeta = np.abs(zc - CFG.alpha)
    assert zeta.min() == pytest.approx(CFG.zeta_min, rel=1e-6)
    assert zeta.max() == pytest.approx(CFG.zeta_min * abs(CFG.mu) ** CFG.periods, rel=1e-6)
    assert np.abs(zc).max() < 3.0, "samples are far outside K_c"


def test_grid_has_real_interior_and_real_exterior():
    zc = koenigs_grid(CFG, 256, 200)
    _, interior = smooth_escape(zc, CFG)
    frac = interior.mean()
    assert 0.02 < frac < 0.5, f"interior fraction {frac} is degenerate"


def test_seam_closes_exactly():
    """theta = 0 and theta = 2pi must give the identical value, not merely close."""
    cfg = CFG
    h = 120.0
    u = np.log(cfg.zeta_min) + cfg.k * (h - cfg.band_lo)
    v0 = 0.0 + cfg.twist_rate_rad_per_mm * (h - cfg.band_lo)
    v1 = 2 * np.pi + cfg.twist_rate_rad_per_mm * (h - cfg.band_lo)
    z = np.array([cfg.alpha + np.exp(u + 1j * v0), cfg.alpha + np.exp(u + 1j * v1)])
    nu, _ = smooth_escape(z, cfg)
    assert nu[0] == pytest.approx(nu[1], abs=1e-9)


def test_pattern_reproduces_itself_after_one_period():
    """The Koenigs screw is the whole design. If this fails, the vase is not fractal."""
    cfg = CFG
    theta = np.linspace(0, 2 * np.pi, 512, endpoint=False)

    def ring(h):
        u = np.log(cfg.zeta_min) + cfg.k * (h - cfg.band_lo)
        v = theta + cfg.twist_rate_rad_per_mm * (h - cfg.band_lo)
        return smooth_escape(cfg.alpha + np.exp(u + 1j * v), cfg)[0]

    a, b = ring(60.0), ring(60.0 + cfg.period)
    match = np.corrcoef(a, b)[0, 1]
    control = np.corrcoef(a, np.roll(b, 13))[0, 1]
    assert match > 0.95, f"period does not reproduce: r={match}"
    assert match > control


def test_normalised_field_is_bounded_and_uses_the_full_range():
    f = normalised_field(CFG, 256, 200)
    assert f.shape == (256, 200)
    assert f.min() >= 0.0 and f.max() <= 1.0
    # a clamp at nu_ref is what stops the heavy tail flattening everything
    assert f.std() > 0.05, "field is nearly constant; check nu_ref clamping"


def test_normalised_field_interior_is_maximal():
    """Interior is solid, so it must drive maximum radius."""
    zc = koenigs_grid(CFG, 128, 100)
    _, interior = smooth_escape(zc, CFG)
    f = normalised_field(CFG, 128, 100, supersample=1)
    assert f[interior].min() == pytest.approx(1.0)
