"""The spec's constants are load-bearing. A silent change here changes the vase."""
import dataclasses
import math

import pytest

from fractalvase.config import DOUADY_HELIX, VaseConfig


def test_alpha_is_the_repelling_fixed_point():
    cfg = DOUADY_HELIX
    # alpha must satisfy alpha^2 + c = alpha
    assert abs(cfg.alpha**2 + cfg.c - cfg.alpha) < 1e-12


def test_koenigs_constants_match_spec():
    cfg = DOUADY_HELIX
    assert cfg.alpha.real == pytest.approx(1.2765819495, abs=1e-9)
    assert cfg.alpha.imag == pytest.approx(-0.4796660549, abs=1e-9)
    assert abs(cfg.mu) == pytest.approx(2.7274464232, abs=1e-9)
    assert cfg.arg_mu == pytest.approx(-0.3594214440, abs=1e-9)
    assert cfg.ln_mu == pytest.approx(1.0033657954, abs=1e-9)


def test_scale_ratio_is_within_a_percent_of_e():
    # the design rests on this: the ornament ratio is inherited, not chosen
    assert abs(abs(DOUADY_HELIX.mu) / math.e - 1.0) < 0.005


def test_mapping_constants():
    cfg = DOUADY_HELIX
    assert cfg.period == pytest.approx(50.0)
    assert cfg.k == pytest.approx(0.0200673, abs=1e-7)
    # twist rate reproduces section 3.4 independently
    assert math.degrees(cfg.twist_rate_rad_per_mm) == pytest.approx(-0.4119, abs=1e-4)
    assert math.degrees(cfg.arg_mu) * cfg.periods == pytest.approx(-82.37, abs=0.01)


def test_c_is_inside_the_mandelbrot_set():
    """Outside M means Cantor dust: zero area, nothing to build a wall from."""
    z = 0j
    for _ in range(2000):
        z = z**2 + DOUADY_HELIX.c
        assert abs(z) <= 4.0, "critical orbit escaped: c is outside M"


def test_scale_ladder_stops_above_the_minimum_ridge():
    cfg = DOUADY_HELIX
    size = 116.0
    levels = []
    while size >= 1.0:
        levels.append(size)
        size /= abs(cfg.mu)
    assert len(levels) == 5
    assert levels[-1] == pytest.approx(2.096, abs=0.001)


def test_config_is_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        DOUADY_HELIX.c = 0j  # type: ignore[misc]


def test_envelope_is_respected_by_construction():
    cfg = VaseConfig()
    assert cfg.height <= 300.0
    assert cfg.band_lo < cfg.band_hi <= cfg.height
