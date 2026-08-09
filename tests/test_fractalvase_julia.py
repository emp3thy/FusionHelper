"""The mapping was wrong once already (see spec 2.3). These tests pin it."""
import numpy as np
import pytest

import fractalvase.julia as julia
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
    """theta = 0 and theta = 2pi must give the identical value, not merely close.

    exp(2*pi*i) == 1 to float precision no matter how the mapping is coded,
    so this only proves the complex exponential is periodic -- it does not
    prove koenigs_grid's own theta axis avoids emitting both endpoints as
    separate columns. See test_koenigs_grid_theta_axis_has_no_duplicate_seam
    for the test that actually exercises koenigs_grid.
    """
    cfg = CFG
    h = 120.0
    u = np.log(cfg.zeta_min) + cfg.k * (h - cfg.band_lo)
    v0 = 0.0 + cfg.twist_rate_rad_per_mm * (h - cfg.band_lo)
    v1 = 2 * np.pi + cfg.twist_rate_rad_per_mm * (h - cfg.band_lo)
    z = np.array([cfg.alpha + np.exp(u + 1j * v0), cfg.alpha + np.exp(u + 1j * v1)])
    nu, _ = smooth_escape(z, cfg)
    assert nu[0] == pytest.approx(nu[1], abs=1e-9)


def test_koenigs_grid_theta_axis_has_no_duplicate_seam():
    """koenigs_grid must build theta via linspace(..., endpoint=False). Using
    endpoint=True would emit theta=0 and theta=2pi as two separate rows -- the
    exact duplicate-seam bug this test file's docstring warns about -- and
    nothing else in this suite exercises koenigs_grid's own theta axis to
    catch it (test_seam_closes_exactly checks exp()'s periodicity, not this)."""
    cfg = CFG
    n_theta, n_z = 64, 5
    zc = koenigs_grid(cfg, n_theta, n_z)
    # at h = band_lo the twist term vanishes (h - band_lo == 0), so
    # angle(zc[:, 0] - alpha) recovers theta directly
    theta = np.mod(np.angle(zc[:, 0] - cfg.alpha), 2 * np.pi)

    distinct = len(np.unique(np.round(theta, 9)))
    assert distinct == n_theta, f"only {distinct}/{n_theta} distinct theta columns: seam duplicated"

    uniform_step = 2 * np.pi / n_theta
    ordered = np.sort(theta)
    assert np.allclose(np.diff(ordered), uniform_step, rtol=1e-9), "theta steps are not uniform"
    wrap_step = (2 * np.pi - ordered[-1]) + ordered[0]
    assert wrap_step == pytest.approx(uniform_step, rel=1e-9), "wrap-around step is not uniform"


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
    # The Gaussian low-pass (spec 4 step 2) legitimately blurs interior cells
    # that border the exterior below 1.0 -- that is the low-pass working as
    # intended, not a regression. A cell deep inside the interior blob, away
    # from any boundary, is surrounded entirely by other 1.0 cells and stays
    # exactly 1.0, which is what actually has to drive the maximum radius.
    assert f[interior].max() == pytest.approx(1.0)


def test_supersample_evaluates_s_squared_distinct_points(monkeypatch):
    """The offsets used to reach a hardcoded 4-item list; supersample=3 silently
    reused those same 4 points instead of genuinely sampling 9. Pin the fix by
    spying on every raw-field evaluation the supersample loop performs."""
    seen: list[np.ndarray] = []
    original = julia._raw_field

    def spy(cfg, zc):
        seen.append(np.array(zc))
        return original(cfg, zc)

    monkeypatch.setattr(julia, "_raw_field", spy)
    julia.normalised_field(CFG, 32, 20, supersample=3)

    assert len(seen) == 9
    for i in range(len(seen)):
        for j in range(i + 1, len(seen)):
            assert not np.array_equal(seen[i], seen[j]), "supersample reused a sample grid"


def test_lowpass_reduces_gradient_without_flattening_the_field():
    """Spec 4 step 2's Gaussian low-pass is a real overhang mitigation, not
    decoration: the field's z-gradient (a proxy for surface overhang before
    profile.py maps it to a radius) must drop, while the field's own range
    and spread -- the relief the low-pass must not erase -- stay close."""
    cfg = CFG
    n_theta, n_z = 256, 200
    raw = julia._supersampled_field(cfg, n_theta, n_z, supersample=2)
    filtered = normalised_field(cfg, n_theta, n_z, supersample=2)

    raw_grad = np.abs(np.diff(raw, axis=1)).max()
    filtered_grad = np.abs(np.diff(filtered, axis=1)).max()
    assert filtered_grad < raw_grad, "low-pass did not reduce the z-gradient"

    raw_pp = raw.max() - raw.min()
    filtered_pp = filtered.max() - filtered.min()
    assert filtered_pp == pytest.approx(raw_pp, rel=0.05), "low-pass flattened the field's range"
    assert filtered.std() == pytest.approx(raw.std(), rel=0.05), "low-pass flattened the spread"
