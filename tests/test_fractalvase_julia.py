"""The mapping was wrong once already (see spec 2.3). These tests pin it."""
import numpy as np
import pytest
from scipy.ndimage import binary_erosion

import fractalvase.julia as julia
from fractalvase.config import DOUADY_HELIX
from fractalvase.julia import koenigs_grid, normalised_field, smooth_escape

CFG = DOUADY_HELIX


def _erode_wrapping_theta(mask: np.ndarray, iterations: int) -> np.ndarray:
    """Erode a boolean (theta, h) mask, treating theta (axis 0) as periodic
    and h (axis 1) as a hard boundary. binary_erosion has no periodic-mode
    argument, so theta is padded by wrapping before eroding and the padding
    is sliced back off afterward; h is left unpadded so border_value=0
    correctly treats cells beyond band_lo/band_hi as exterior."""
    padded = np.pad(mask, ((iterations, iterations), (0, 0)), mode="wrap")
    eroded = binary_erosion(padded, iterations=iterations, border_value=0)
    return eroded[iterations:-iterations, :]


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
    """Interior is solid, so it must drive maximum radius.

    The Gaussian low-pass (spec 4 step 2) legitimately blurs interior cells
    that border the exterior below 1.0 -- that is the low-pass working as
    intended, not a regression, so f[interior].min() == 1.0 no longer holds.
    But f[interior].max() == 1.0 is too weak: it would still pass if the
    low-pass were far too aggressive and flattened almost the entire
    interior, since a single surviving 1.0 cell is enough. Erode the
    interior mask instead: a cell several cells deep, away from any
    boundary, is surrounded entirely by other 1.0 cells, so a local
    averaging filter cannot move it -- that is what actually has to drive
    the maximum radius, and every one of those cells must be exactly 1.0.
    """
    n_theta, n_z = 128, 100
    zc = koenigs_grid(CFG, n_theta, n_z)
    _, interior = smooth_escape(zc, CFG)
    f = normalised_field(CFG, n_theta, n_z, supersample=1)

    deep_interior = _erode_wrapping_theta(interior, iterations=3)
    assert deep_interior.sum() > 0, "erosion removed the entire interior; test proves nothing"
    assert f[deep_interior].min() == pytest.approx(1.0)


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


def test_normalised_field_output_seam_is_continuous():
    """The seam is the exact defect the log-polar mapping exists to
    eliminate, and the Gaussian low-pass (spec 4 step 2) runs after
    everything else -- if its theta-axis mode ever stopped being periodic
    (currently mode="wrap"), it could reintroduce a seam that neither
    koenigs_grid's nor smooth_escape's own seam tests would catch, since
    both of those run pre-low-pass. If theta wraps correctly, the
    wrap-around pair (column 0, column -1) is just another adjacent pair
    and should not stand out against nearby ordinary adjacent pairs.

    Uses cfg.n_theta/n_z (the shipped resolution), not a smaller test
    grid: the low-pass sigma expressed in cells scales with n_theta (see
    _lowpass_sigma_cells), and below roughly 1 cell of sigma a wrap-vs-
    non-wrap difference is too small to show up in this comparison at all
    -- checked empirically at 64/128/256/640 before picking this one.

    That resolution-dependence means the test can go quiet with no
    failure if a future change lowers n_theta: below the floor it just
    stops discriminating rather than raising an error. Guard against that
    directly by asserting sigma-in-cells clears a floor known to work.

    An initial sweep at n_theta = 256/320/384/450/512/576/640 (sigma
    0.351/0.439/0.527/0.617/0.702/0.790/0.878 cells) only bracketed the
    crossover to the interval (0.527, 0.617) -- nothing in between was
    measured, so a floor picked inside that gap (0.6 was picked first)
    would rest on an unmeasured assumption, not evidence. Bisected the
    gap: n_theta=410 (0.5625 cells) is the highest confirmed-FAILING
    value (nearest-mode ratio 1.198, still <= the 1.2 threshold);
    n_theta=415 (0.5694 cells) is the lowest confirmed-PASSING value
    (ratio 1.207). The true crossover lies in (0.5625, 0.5694). The
    floor below, 0.6, sits above 0.5694 with real margin -- inside the
    confirmed-separating region this time, not the unmeasured gap.
    """
    cfg = CFG
    n_theta, n_z = cfg.n_theta, cfg.n_z
    sigma_theta_cells, _ = julia._lowpass_sigma_cells(cfg, n_theta, n_z)
    assert sigma_theta_cells > 0.6, (
        f"sigma is only {sigma_theta_cells:.3f} cells at n_theta={n_theta} -- "
        "below the measured ~0.6-cell discrimination floor, wrap vs nearest "
        "would be indistinguishable and this test would pass without "
        "actually checking anything"
    )

    f = normalised_field(cfg, n_theta, n_z, supersample=2)

    seam_diff = np.abs(f[0] - f[-1])
    nearby = []
    for i in range(3):
        nearby.append(np.abs(f[i] - f[i + 1]))
        nearby.append(np.abs(f[-1 - i] - f[-2 - i]))
    nearby_diff = np.concatenate(nearby)

    assert seam_diff.max() <= 1.2 * nearby_diff.max(), (
        f"seam is an outlier against its own neighbourhood: seam max diff "
        f"{seam_diff.max():.6f} vs nearby max diff {nearby_diff.max():.6f}"
    )


def test_physical_lowpass_sigma_at_relief_peak_is_close_to_nominal():
    """_lowpass_sigma_cells fixes a cell count from lowpass_sigma_mm at the
    MAXIMUM radius (lowpass_ref_radius_mm); the physical width achieved at
    any other radius is smaller (see its docstring). That is only an
    acceptable trade because the shortfall is worst where relief is zero
    and small where relief peaks. This guards the favourable case: if a
    future profile.py changed the belly's diameters enough to move the
    radius at relief_peak_z much below the ~53 mm it is today, the physical
    sigma there would drift further from nominal than the design assumed,
    and this should fail loudly rather than silently degrade the print.

    profile.py doesn't exist yet (Task 3), so the radius at relief_peak_z
    is derived here from spec 3.1's belly-band table directly (Ø 80mm at
    z=40 rising linearly to Ø 112mm at z=150 -- relief_peak_z=130 falls
    inside that band). When profile.py exists, this should import its real
    radius function instead of re-deriving the interpolation.
    """
    cfg = CFG
    belly_z_lo, belly_diam_lo = 40.0, 80.0
    belly_z_hi, belly_diam_hi = 150.0, 112.0
    frac = (cfg.relief_peak_z - belly_z_lo) / (belly_z_hi - belly_z_lo)
    r_at_relief_peak = (belly_diam_lo + frac * (belly_diam_hi - belly_diam_lo)) / 2

    physical_sigma = julia._lowpass_sigma_mm_at_radius(cfg, r_at_relief_peak)
    # r_at_relief_peak (~53mm) < lowpass_ref_radius_mm (58mm), so the
    # physical sigma there MUST be strictly smaller than nominal -- this
    # kills an inverted ref/r formula on its own (inversion would make it
    # larger). See test_lowpass_sigma_mm_at_radius_formula_is_not_inverted
    # for why a magnitude-only check like the one below cannot, by itself,
    # tell the correct formula from an inverted one this close to 1.0.
    assert physical_sigma < cfg.lowpass_sigma_mm, (
        f"physical sigma ({physical_sigma:.4f}mm) at a radius below the "
        f"reference must be smaller than nominal ({cfg.lowpass_sigma_mm}mm), "
        "not larger -- check for an inverted r/ref formula"
    )
    relative_error = abs(physical_sigma / cfg.lowpass_sigma_mm - 1.0)
    # measured ~8.5% at today's profile; 15% leaves headroom without being
    # so loose it stops catching a real regression
    assert relative_error <= 0.15, (
        f"physical sigma at relief_peak_z drifted too far from nominal: "
        f"{physical_sigma:.4f}mm vs nominal {cfg.lowpass_sigma_mm}mm "
        f"({relative_error:.1%} off, radius {r_at_relief_peak:.2f}mm)"
    )


def test_lowpass_sigma_mm_at_radius_formula_is_not_inverted():
    """_physical_sigma = lowpass_sigma_mm * r / ref: near the reference
    radius (58mm), r/ref and its reciprocal ref/r are close enough to 1.0
    that a generous design-tolerance check can't distinguish them -- at
    r_at_relief_peak (~53.09mm) the correct ratio is 0.9153 (8.5% low) and
    the inverted ratio is 1.0924 (9.2% high), both inside the 15% band the
    test above uses for a different purpose (verifying the design's
    self-mitigation, not the formula's correctness). Pin the formula
    itself at radii where the two diverge sharply enough that no shared
    threshold could let both through.
    """
    cfg = CFG

    # r=40mm is a spec 3.1 band anchor (Ø=80mm at z=40, no interpolation
    # needed): r/ref = 0.690 vs ref/r = 1.450 -- unambiguous either way
    sigma_at_40 = julia._lowpass_sigma_mm_at_radius(cfg, 40.0)
    expected_at_40 = cfg.lowpass_sigma_mm * 40.0 / cfg.lowpass_ref_radius_mm
    assert sigma_at_40 == pytest.approx(expected_at_40, rel=1e-9)
    assert sigma_at_40 < cfg.lowpass_sigma_mm, "r < ref must give a smaller physical sigma"

    # no radius on this vase actually exceeds lowpass_ref_radius_mm (58mm
    # is defined as the maximum), but the FORMULA must still get the
    # direction right there -- an inverted ref/r formula would (wrongly)
    # shrink instead of grow past the reference
    sigma_above_ref = julia._lowpass_sigma_mm_at_radius(cfg, 100.0)
    expected_above_ref = cfg.lowpass_sigma_mm * 100.0 / cfg.lowpass_ref_radius_mm
    assert sigma_above_ref == pytest.approx(expected_above_ref, rel=1e-9)
    assert sigma_above_ref > cfg.lowpass_sigma_mm, "r > ref must give a larger physical sigma"


def test_lowpass_sigma_cells_matches_lowpass_sigma_mm_at_radius():
    """_lowpass_sigma_cells is what normalised_field actually calls;
    _lowpass_sigma_mm_at_radius is what the guard tests above call. They
    are documented as two views of the same physics, but nothing pinned
    them together -- if someone edited one formula and not the other,
    every test above would keep passing while normalised_field silently
    used a different sigma than the guards believe it does.

    Convert _lowpass_sigma_cells's actual returned cell count back to
    millimetres at a radius, using the actual arc length per cell AT THAT
    RADIUS (not at the reference radius), and compare against
    _lowpass_sigma_mm_at_radius for the same radius. Checked at two
    different n_theta to confirm the result really is independent of grid
    resolution (the cell count and the arc length per cell both scale
    with n_theta and should cancel), not just assumed.
    """
    cfg = CFG
    r = 40.0

    for n_theta, n_z in [(128, 100), (640, 500)]:
        sigma_theta_cells, _ = julia._lowpass_sigma_cells(cfg, n_theta, n_z)
        arc_length_per_cell_at_r = (2 * np.pi * r) / n_theta
        sigma_mm_from_cells = sigma_theta_cells * arc_length_per_cell_at_r
        assert sigma_mm_from_cells == pytest.approx(
            julia._lowpass_sigma_mm_at_radius(cfg, r), rel=1e-9
        ), f"_lowpass_sigma_cells and _lowpass_sigma_mm_at_radius disagree at n_theta={n_theta}"


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
