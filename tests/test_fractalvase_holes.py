import numpy as np
import pytest
import trimesh

from fractalvase.config import DOUADY_HELIX, VaseConfig
from fractalvase.holes import (
    _hole_sites_and_field,
    _local_inner_radius,
    _local_outer_radius,
    arch_prism,
    hole_sites,
    pierce,
)
from fractalvase.profile import radius_at, relief_amplitude

SMALL = VaseConfig(n_theta=96, n_z=80)


def _roof_angles_from_vertical(prism: trimesh.Trimesh, theta: float) -> list[float]:
    """Measure the real overhang angle (from vertical, 0=wall/45=limit/90=flat
    ceiling) of ``arch_prism``'s two roof faces directly from mesh geometry --
    un-rotate the cutter by -theta to its own local frame, find the two
    triangles touching the apex ridge that aren't the flat depth-end caps,
    and take each face normal's angle from the global Z axis. This reads the
    real triangle normals rather than reimplementing the outline's nominal
    formula, so it can't hide the same bug the formula would (see
    task-5-report.md's roof-angle finding).
    """
    v = prism.vertices.copy()
    c, s = np.cos(-theta), np.sin(-theta)
    rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    v_local = v @ rot.T
    top_z = v_local[:, 2].max()
    apex_idx = set(np.where(np.abs(v_local[:, 2] - top_z) < 1e-6)[0])

    seen_normals: list[np.ndarray] = []
    angles = []
    for face in prism.faces:
        if not (set(face) & apex_idx):
            continue
        tri = v_local[face]
        if np.ptp(tri[:, 0]) < 1e-9:  # flat depth-end cap, not a roof face
            continue
        normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        normal = normal / np.linalg.norm(normal)
        # dedupe the two triangles making up each planar roof quad (same
        # normal vector), NOT by the derived angle -- a symmetric pair of
        # roof faces can share the same angle-from-vertical while still
        # being two distinct faces (mirror images in Y), and collapsing by
        # angle would wrongly merge them into one
        if any(np.allclose(normal, n, atol=1e-6) for n in seen_normals):
            continue
        seen_normals.append(normal)
        angle_from_z_axis = np.degrees(np.arccos(np.clip(abs(normal[2]), 0, 1)))
        angles.append(round(90.0 - angle_from_z_axis, 4))
    return sorted(angles)


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


def test_arch_roof_faces_stay_within_the_self_support_limit():
    """Former decision C4-A leaned the crown to follow the helix's local
    surface normal. Review measurement showed that backwards: FDM layers
    are horizontal in global Z regardless of how the wall leans, so a
    crown's self-support is a global-Z property. The lean correction broke
    the apex's built-in left/right symmetry and pushed one roof face past
    the 45 degree limit at every real site checked (up to ~67 degrees at
    the belly, where the lean is largest) while leaving the other needlessly
    steep. Removing the correction restores both faces to exactly
    ``arch_apex_deg`` from vertical, by construction, independent of theta
    or z. Checked across real sites spanning both size extremes and both
    ends of the pierced band, using the SAME centring pierce() uses.
    """
    cfg = DOUADY_HELIX
    sites = hole_sites(cfg)
    _, full, zf = _hole_sites_and_field(cfg)

    by_size = sorted(sites, key=lambda s: s["size"])
    by_z = sorted(sites, key=lambda s: s["z"])
    sample = {id(s): s for s in (by_size[0], by_size[-1], by_z[0], by_z[-1])}.values()

    for s in sample:
        r_out = _local_outer_radius(cfg, full, zf, s["theta"], s["z"])
        r_in = _local_inner_radius(cfg, s["z"])
        center = (r_in + r_out) / 2.0
        prism = arch_prism(s["theta"], s["z"], s["size"], center, cfg)
        angles = _roof_angles_from_vertical(prism, s["theta"])
        assert len(angles) == 2, f"expected 2 roof faces, got {angles} for site {s}"
        for angle in angles:
            assert angle <= cfg.arch_apex_deg + 1e-6, (
                f"roof face at {angle:.2f} deg exceeds the "
                f"{cfg.arch_apex_deg} deg self-support limit for site {s}"
            )
        # symmetric by construction once the crown tracks global Z, not
        # merely "under the limit" -- both faces should land at the same
        # angle, matching arch_apex_deg exactly
        assert angles[0] == pytest.approx(angles[1], abs=1e-3)
        assert angles[0] == pytest.approx(cfg.arch_apex_deg, abs=1e-3)


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


def test_pierce_lo_must_be_below_pierce_hi():
    """Demonstrated: VaseConfig(pierce_lo=225, pierce_hi=150) constructed
    silently before this validation existed."""
    with pytest.raises(ValueError, match="pierce_lo"):
        VaseConfig(pierce_lo=225.0, pierce_hi=150.0)


def test_hole_row_pitch_must_be_positive():
    with pytest.raises(ValueError, match="hole_row_pitch"):
        VaseConfig(hole_row_pitch=0.0)


def test_hole_col_pitch_must_be_positive():
    """Demonstrated: VaseConfig(hole_col_pitch=0.0) constructed silently
    and then raised a raw ZeroDivisionError deep inside hole_sites, instead
    of a clean error at construction time."""
    with pytest.raises(ValueError, match="hole_col_pitch"):
        VaseConfig(hole_col_pitch=0.0)


def test_hole_size_min_must_be_below_hole_size_max():
    """Demonstrated: VaseConfig(hole_size_min=8, hole_size_max=3)
    constructed silently before this validation existed."""
    with pytest.raises(ValueError, match="hole_size_min"):
        VaseConfig(hole_size_min=8.0, hole_size_max=3.0)


def test_min_ligament_must_be_positive():
    with pytest.raises(ValueError, match="min_ligament"):
        VaseConfig(min_ligament=0.0)


def test_max_hole_span_must_exceed_min_ligament():
    with pytest.raises(ValueError, match="max_hole_span"):
        VaseConfig(max_hole_span=1.0, min_ligament=2.0)


def test_arch_apex_deg_must_be_a_genuine_point_angle():
    """0 divides by zero in apex = half_w/tan(deg); 90 flattens the crown to
    a horizontal ridge, defeating the whole point of a pointed arch."""
    with pytest.raises(ValueError, match="arch_apex_deg"):
        VaseConfig(arch_apex_deg=0.0)
    with pytest.raises(ValueError, match="arch_apex_deg"):
        VaseConfig(arch_apex_deg=90.0)
