import numpy as np
import pytest

from fractalvase.config import DOUADY_HELIX
from fractalvase.profile import (
    BREAKPOINTS,
    max_envelope_slope,
    radius_at,
    relief_amplitude,
    smooth_radius,
)

CFG = DOUADY_HELIX


def test_breakpoints_match_spec():
    assert BREAKPOINTS[0] == (0.0, 70.0)
    assert (185.0, 116.0) in BREAKPOINTS  # widest point
    assert BREAKPOINTS[-1] == (300.0, 68.0)


def test_widest_point_is_at_the_golden_section():
    z = np.linspace(0, 300, 3001)
    widest_z = z[np.argmax(radius_at(z))]
    assert widest_z == pytest.approx(185.0, abs=1.0)
    assert widest_z / 300.0 == pytest.approx(0.617, abs=0.005)


def test_envelope_is_never_exceeded():
    z = np.linspace(0, 300, 3001)
    assert radius_at(z).max() * 2 <= 116.0 + 1e-9
    assert (radius_at(z).max() * 2 + 2 * CFG.relief_peak) <= 135.0


def test_relief_is_zero_in_the_quiet_zones():
    quiet = np.array([0.0, 20.0, 39.9, 240.1, 270.0, 300.0])
    assert np.allclose(relief_amplitude(quiet, CFG), 0.0)


def test_relief_peaks_at_the_specified_height():
    z = np.linspace(40, 240, 20001)
    a = relief_amplitude(z, CFG)
    assert a.max() == pytest.approx(CFG.relief_peak, abs=1e-6)
    assert z[np.argmax(a)] == pytest.approx(CFG.relief_peak_z, abs=0.05)


def test_relief_samples_match_spec():
    for z, expected in [(150.0, 6.4444), (185.0, 3.5000), (225.0, 0.3163)]:
        got = relief_amplitude(np.array([z]), CFG)[0]
        assert got == pytest.approx(expected, abs=1e-3)


def test_relief_derivative_vanishes_at_both_band_ends():
    """Zero-slope entry is what stops a visible start line.

    A(z) is a raised cosine, so its value near an edge falls off
    quadratically, not linearly: A(edge + 0.01) is ~2e-7, not merely
    "< 0.01". A value-only check at that scale has four orders of
    magnitude of slack -- a regression that swapped in a *linear* onset
    with slope up to ~0.9 mm/mm would still satisfy "< 0.01" at eps=0.01.
    Check the derivative itself instead, via a tight central difference
    (h=1e-5, chosen because the analytic derivative is exactly 0 at both
    edges -- sin(0) and sin(pi) -- so the central-difference estimate is
    itself O(h) and shrinks with h; 1e-5 keeps float noise well below the
    1e-4 threshold while staying far above where dA/dz would land under a
    genuine abrupt-onset regression).
    """
    h = 1e-5
    for edge in (CFG.band_lo, CFG.band_hi):
        d = (
            relief_amplitude(np.array([edge + h]), CFG)[0]
            - relief_amplitude(np.array([edge - h]), CFG)[0]
        ) / (2 * h)
        assert abs(d) < 1e-4, f"relief slope at z={edge} is {d}, not ~0"


def test_relief_is_continuous_in_value_and_slope_at_the_peak():
    """relief_amplitude only ever evaluates the rise formula at z ==
    relief_peak_z (rise: z <= pk, fall: z > pk). Exercise the SHIPPED
    function on both sides of that join -- every value below comes from a
    call to relief_amplitude itself, not a local restatement of the
    raised-cosine algebra. (A prior version of this test defined rise_only
    and fall_only closures and compared them to each other; that never
    called relief_amplitude at all, so it verified an identity that holds
    for any coefficients -- cos(pi)=-1, cos(0)=1 -- regardless of what the
    shipped fall branch actually does. Confirmed a hand-mutated fall
    branch with a real slope discontinuity still passed it.)
    """
    pk = CFG.relief_peak_z
    h = 1e-4

    peak_val = relief_amplitude(np.array([pk]), CFG)[0]
    # value continuity: the fall branch's own limit as z -> pk+ must land
    # on the value the rise branch produces at pk itself
    assert relief_amplitude(np.array([pk + h]), CFG)[0] == pytest.approx(peak_val, abs=1e-6)

    # one-sided slopes: each estimate uses two points strictly on one side
    # of the join, so the left estimate exercises only the rise branch and
    # the right estimate only the fall branch
    left_slope = (
        relief_amplitude(np.array([pk - h]), CFG)[0]
        - relief_amplitude(np.array([pk - 2 * h]), CFG)[0]
    ) / h
    right_slope = (
        relief_amplitude(np.array([pk + 2 * h]), CFG)[0]
        - relief_amplitude(np.array([pk + h]), CFG)[0]
    ) / h
    assert left_slope == pytest.approx(right_slope, abs=1e-3)


def test_smoothing_does_not_move_the_widest_point_much():
    z = np.linspace(0, 300, 3001)
    assert z[np.argmax(smooth_radius(z))] == pytest.approx(185.0, abs=6.0)


def test_smoothing_reproduces_the_edge_value_exactly():
    """At the exact domain edges, slope-preserving (odd) reflection is
    exact for ANY window: the reflected term and the direct term it's
    paired with are the same sampled values reindexed, so they cancel
    algebraically regardless of window size (see smooth_radius's
    docstring). 1e-9 covers float roundoff only, with no slack for a
    systematic bias: clamping the old way was off by +0.30 mm / -0.32 mm,
    and naive coordinate mirroring is off by +0.61 mm / -0.64 mm (both
    measured independently), so any regression back to either would fail
    this by six orders of magnitude."""
    assert smooth_radius(np.array([0.0]))[0] == pytest.approx(
        radius_at(np.array([0.0]))[0], abs=1e-9
    )
    assert smooth_radius(np.array([300.0]))[0] == pytest.approx(
        radius_at(np.array([300.0]))[0], abs=1e-9
    )


def test_smoothing_rejects_a_window_wider_than_the_boundary_segments():
    """A window that reaches past the first (40 mm) or last (38 mm)
    BREAKPOINTS segment span makes the boundary reflection pull in
    mirrored geometry from a different, unrelated segment -- silently, if
    unguarded. window=45 exceeds both spans."""
    with pytest.raises(ValueError, match="window"):
        smooth_radius(np.array([0.0]), window=45.0)


def test_default_window_is_genuinely_inside_the_boundary_segment_spans():
    """Non-vacuous companion to the rejection test above: confirm the
    default window (9.0 mm) sits with real margin inside both the first
    (z 0->40, 40 mm) and last (z 262->300, 38 mm) segment spans -- not
    merely that smooth_radius(z) happens not to raise for it."""
    lo_span = BREAKPOINTS[1][0] - BREAKPOINTS[0][0]
    hi_span = BREAKPOINTS[-1][0] - BREAKPOINTS[-2][0]
    assert lo_span > 9.0
    assert hi_span > 9.0
    smooth_radius(np.linspace(0.0, 300.0, 11))  # must not raise


def test_combined_slope_stays_within_the_overhang_limit():
    """Profile taper + relief gradient + helical lean, composed.

    This is a bound on the smooth envelope only -- see max_envelope_slope's
    docstring for why it does not, and cannot, bound the actual textured
    surface (that check is Task 4's).
    """
    assert max_envelope_slope(CFG) < 1.0
    assert np.degrees(np.arctan(max_envelope_slope(CFG))) < 45.0


def test_envelope_slope_matches_the_corrected_reference_value():
    """Pins the corrected value so a future change (e.g. reverting to the
    profile-only r_max, or changing BREAKPOINTS/relief_peak) cannot move it
    silently. Corrected for the true profile+relief combined maximum radius
    (62.446 mm at z~151.3) rather than the profile-only maximum (58 mm);
    the uncorrected figure was 0.8339 (39.82 deg)."""
    assert max_envelope_slope(CFG) == pytest.approx(0.8503, abs=1e-3)
    assert np.degrees(np.arctan(max_envelope_slope(CFG))) == pytest.approx(40.38, abs=0.01)
