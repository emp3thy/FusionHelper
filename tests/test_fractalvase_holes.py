import numpy as np
import pytest
import trimesh

from fractalvase.config import DOUADY_HELIX, VaseConfig
from fractalvase.holes import arch_prism, hole_sites, pierce
from fractalvase.profile import radius_at, relief_amplitude

SMALL = VaseConfig(n_theta=96, n_z=80)


def test_boolean_engine_is_available():
    a = trimesh.creation.box(extents=(10, 10, 10))
    b = trimesh.creation.box(extents=(4, 4, 20))
    c = trimesh.boolean.difference([a, b], engine="manifold")
    assert c.is_watertight
    assert c.volume == pytest.approx(840.0, abs=1.0)


def test_lattice_produces_discrete_holes_not_one_blob():
    """The whole reason for the seeded lattice. A threshold rule gave ONE
    region 75.38 mm x 87.24 mm; this must give many small ones."""
    sites = hole_sites(DOUADY_HELIX)
    assert len(sites) > 20, f"only {len(sites)} holes: lattice is not opening"
    assert len(sites) < 500, f"{len(sites)} holes: boolean will be the bottleneck"


def test_hole_count_and_sizes_match_the_measured_reference():
    """Pinned to seed_lattice.py's independently measured figures."""
    sites = hole_sites(DOUADY_HELIX)
    sizes = np.array([s["size"] for s in sites])
    assert len(sites) == 43
    assert sizes.min() == pytest.approx(3.09, abs=0.05)
    assert sizes.max() == pytest.approx(8.00, abs=0.05)
    assert len(np.unique([s["z"] for s in sites])) == 6  # rows


def test_every_hole_is_inside_the_span_bounds():
    for s in hole_sites(DOUADY_HELIX):
        assert DOUADY_HELIX.min_ligament <= s["size"] <= DOUADY_HELIX.max_hole_span


def test_ligament_between_holes_clears_the_floor():
    """Measured 4.62 mm at the shipped pitch. Below min_ligament the lattice
    snaps in hand, so this is a structural assertion, not a cosmetic one."""
    cfg = DOUADY_HELIX
    sites = hole_sites(cfg)
    z = np.array([s["z"] for s in sites])
    t = np.array([s["theta"] for s in sites])
    size = np.array([s["size"] for s in sites])
    r = radius_at(z) + relief_amplitude(z, cfg)
    pts = np.stack([r * np.cos(t), r * np.sin(t), z], axis=1)
    d = np.linalg.norm(pts[:, None, :] - pts[None, :, :], axis=2)
    np.fill_diagonal(d, np.inf)
    gap = (d - size[:, None] / 2 - size[None, :] / 2).min()
    assert gap >= cfg.min_ligament, f"ligament {gap:.2f} mm below floor"
    assert gap == pytest.approx(4.62, abs=0.15)


def test_arch_prism_is_a_valid_solid():
    p = arch_prism(0.0, 185.0, 8.0, 58.0, SMALL)
    assert p.is_watertight
    assert p.is_volume
    assert p.volume > 0


def test_arch_apex_points_up():
    """A pointed crown is what makes the hole self-supporting."""
    p = arch_prism(0.0, 185.0, 8.0, 58.0, SMALL)
    v = p.vertices
    top = v[:, 2].max()
    near_top = v[np.abs(v[:, 2] - top) < 0.05]
    widest = np.ptp(v[:, 1])
    assert np.ptp(near_top[:, 1]) < 0.4 * widest, "crown is flat: it will bridge"


def test_pierce_produces_a_valid_solid_with_the_expected_genus():
    """euler_number is the gate that catches a boolean that succeeds and
    does nothing: a cutter tangent to (or shallow against) the wall leaves
    is_watertight/is_volume/body_count all green with the genus unchanged.
    See task-5-brief.md and holes.pierce's docstring for the measured case."""
    from fractalvase.surface import build_shell

    shell = build_shell(SMALL)
    assert shell.euler_number == 2, "unpierced solid must be genus 0"
    pierced, n = pierce(shell, SMALL)
    assert n > 0, "nothing was pierced"
    assert pierced.is_watertight
    assert pierced.is_volume
    assert pierced.volume > 0
    assert pierced.volume < shell.volume, "piercing did not remove material"
    assert pierced.body_count == 1
    assert pierced.euler_number == 2 - 2 * n, (
        f"euler {pierced.euler_number} != {2 - 2 * n}: boolean did not "
        "genuinely pierce every site"
    )


def test_pierced_mesh_stays_in_the_envelope():
    from fractalvase.surface import build_shell

    pierced, _ = pierce(build_shell(SMALL), SMALL)
    x, y, z = pierced.extents
    assert x <= 135.0 and y <= 135.0 and z <= 300.0
