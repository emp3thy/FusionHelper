import numpy as np
import pytest

from fractalvase.config import DOUADY_HELIX
from fractalvase.profile import (
    BREAKPOINTS,
    max_slope,
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


def test_relief_has_zero_slope_at_both_band_ends():
    """Zero-slope entry is what stops a visible start line."""
    eps = 0.01
    for edge in (CFG.band_lo, CFG.band_hi):
        inside = edge + eps if edge == CFG.band_lo else edge - eps
        a = relief_amplitude(np.array([inside]), CFG)[0]
        assert a < 0.01, f"relief enters abruptly at z={edge}"


def test_smoothing_does_not_move_the_widest_point_much():
    z = np.linspace(0, 300, 3001)
    assert z[np.argmax(smooth_radius(z))] == pytest.approx(185.0, abs=6.0)


def test_combined_slope_stays_within_the_overhang_limit():
    """Profile taper + relief gradient + helical lean, composed."""
    assert max_slope(CFG) < 1.0
    assert np.degrees(np.arctan(max_slope(CFG))) < 45.0
