import numpy as np
import pytest
import trimesh

from fractalvase.config import VaseConfig
from fractalvase.surface import (
    _assemble,
    _bridge_rings,
    _fan,
    _inner_radius,
    build_shell,
    revolve_grid,
)

# small grid: these tests check topology, not detail
SMALL = VaseConfig(n_theta=96, n_z=80)


def test_revolve_grid_seam_has_no_duplicate_vertices():
    """revolve_grid must build theta via linspace(..., endpoint=False). Using
    endpoint=True instead would emit theta=0 and theta=2*pi as two separate
    columns -- the exact duplicate-seam bug this test names -- but
    len(v) == n_theta * n_z stays true either way, since linspace always
    returns n_theta points regardless of endpoint; that assertion alone
    counts rows, it never looks at what angle any of them land on. Checks
    the theta axis itself instead, the way
    test_koenigs_grid_theta_axis_has_no_duplicate_seam does for koenigs_grid:
    distinct angles, a uniform step between them, and a wrap-around step
    that matches.
    """
    n_t, n_z = 16, 5
    r = np.full((n_t, n_z), 5.0)
    z = np.linspace(0, 10, n_z)
    v, f = revolve_grid(r, z)
    assert len(v) == n_t * n_z, "seam vertex duplicated; theta must not include 2pi"

    # z index 0 column: vertex i*n_z + 0 is theta index i
    theta = np.mod(np.arctan2(v[::n_z, 1], v[::n_z, 0]), 2 * np.pi)
    distinct = len(np.unique(np.round(theta, 9)))
    assert distinct == n_t, f"only {distinct}/{n_t} distinct theta columns: seam duplicated"

    uniform_step = 2 * np.pi / n_t
    ordered = np.sort(theta)
    assert np.allclose(np.diff(ordered), uniform_step, rtol=1e-9), "theta steps are not uniform"
    wrap_step = (2 * np.pi - ordered[-1]) + ordered[0]
    assert wrap_step == pytest.approx(uniform_step, rel=1e-9), "wrap-around step is not uniform"


def test_revolve_grid_winding_is_outward():
    """is_winding_consistent alone passes for a consistently-wound but
    globally INWARD mesh too -- it only checks that adjacent faces agree
    with each other, not which way they face. Ports the brief's own Step 1
    spike check (never committed as a test, per the team lead's review):
    face normals must point away from the rotation axis, not merely agree.
    """
    n_t, n_z = 32, 4
    r = np.full((n_t, n_z), 10.0)
    z = np.linspace(0, 20, n_z)
    m = trimesh.Trimesh(*revolve_grid(r, z), process=False)
    assert m.is_winding_consistent

    radial_dot = np.einsum(
        "ij,ij->i",
        m.face_normals,
        m.triangles_center
        / np.linalg.norm(m.triangles_center[:, :2], axis=1, keepdims=True).clip(1e-9),
    )
    assert radial_dot.mean() > 0, "normals point toward the axis, not away from it"


def test_shell_is_a_valid_solid():
    m = build_shell(SMALL)
    assert m.is_watertight, "shell is not watertight"
    assert m.is_winding_consistent
    assert m.is_volume
    assert m.volume > 0, "mesh is inside-out"
    assert m.body_count == 1, "stray disconnected shells"


def test_shell_is_genus_zero_before_piercing():
    m = build_shell(SMALL)
    assert m.euler_number == 2, f"expected genus 0, got euler {m.euler_number}"


def test_shell_winding_is_correct_before_repair():
    """build_shell calls trimesh.repair.fix_winding then fix_normals
    unconditionally. On a single connected component those calls silently
    normalise ANY winding error into a valid, correctly-signed mesh -- so
    checking build_shell's return value proves the repair worked, not that
    the construction itself got winding right. Check the raw assembly
    directly, with process=False, the same technique the brief's Step 1
    spike used for revolve_grid alone.
    """
    v, f = _assemble(SMALL)
    m = trimesh.Trimesh(v, f, process=False)
    assert m.is_winding_consistent, "raw construction has inconsistent winding"
    assert m.is_watertight, "raw construction is not watertight before repair"
    assert m.is_volume, "raw construction is not a valid solid before repair"
    assert m.volume > 0, "raw construction is inside-out before repair"


def test_shell_fits_the_build_envelope():
    m = build_shell(SMALL)
    x, y, z = m.extents
    assert x <= 135.0 and y <= 135.0, f"footprint {x:.1f} x {y:.1f} exceeds plate"
    assert z <= 300.0, f"height {z:.1f} exceeds plate"


def test_shell_sits_on_the_plate():
    m = build_shell(SMALL)
    assert m.bounds[0][2] == pytest.approx(0.0, abs=1e-6)


def test_shell_is_hollow_with_the_specified_wall():
    """A solid vase would have far more volume than a 2mm shell."""
    m = build_shell(SMALL)
    solid_estimate = np.pi * (58.0**2) * 300.0
    assert m.volume < 0.25 * solid_estimate, "vase appears solid, not shelled"


def test_wall_is_never_thinner_than_specified():
    """The throat is where this fails, and where the vase would snap.

    smooth_radius bulges OUTWARD at concave kinks; at z = 262 mm it exceeds
    the raw profile by 1.4202 mm at that exact z. What that does to the
    built wall depends on the sampling grid it's measured at, since the
    formula is only ever evaluated where a real config actually places a z
    sample: production's own 166-point grid measures 0.6339 mm at z=262.2 mm
    (see _inner_radius's docstring); the SMALL config this test actually
    uses, at its own coarser 26-point grid, measures **1.1794 mm at
    z=264.4 mm** instead -- still well under the 2.0 mm nominal, just not
    the exact worst point, because 26 samples over 297 mm don't land on
    z=262. If this assertion ever fires, expect a number near 1.18 mm, not
    0.58 or 0.63 -- those are what finer grids see, and this test doesn't
    use one. _inner_radius clamps against the raw profile to prevent all of
    the above.

    Calls the real _inner_radius rather than recomputing its formula inline:
    an inline copy of the clamp formula would still pass this test even if
    the actual _inner_radius's clamp were removed, since the two would then
    disagree and only the (correct) copy would be checked -- the failure
    mode this test previously had. Mutation-verified (see task-4-report.md):
    removing the clamp from the real _inner_radius makes this test fail.
    """
    from fractalvase.profile import radius_at

    cfg = VaseConfig(n_theta=96, n_z=80)
    r_in, z_in = _inner_radius(cfg)

    # outer at its thinnest over theta is the bare profile (field contributes >= 0)
    outer_min = radius_at(z_in)
    # inner is uniform across theta today (see _inner_radius); max() is the
    # conservative (thinnest-wall) reading if that ever changes
    clearance = outer_min - r_in.max(axis=0)

    assert clearance.min() >= cfg.wall - 1e-9, (
        f"wall thins to {clearance.min():.4f} mm at z = {z_in[np.argmin(clearance)]:.1f} mm"
    )


def test_no_degenerate_faces():
    m = build_shell(SMALL)
    areas = m.area_faces
    assert (areas > 1e-10).all(), "zero-area triangles present"


def test_base_has_a_genuinely_solid_floor():
    """A vase whose inner surface ran to z=0 had a zero-thickness base: the
    cavity floor and the outer bottom face were the same membrane, and the
    cavity was open underneath. base_thickness fixes this by starting the
    inner surface higher up, leaving a solid slab below it -- check that
    slab is actually solid material, not just a mesh that happens to be
    watertight for unrelated reasons.

    Both probe points below were originally derived from SMALL.base_thickness
    itself (base_thickness/2, base_thickness+10), so the test passed
    identically whether the real floor was 2, 3 or 8 mm thick -- it proved
    SOME positive floor under SOME cavity, never that the floor is the 3.0 mm
    base_thickness actually specifies, which is pinned nowhere else in the
    tree. Measures the real floor thickness independently via a ray cast
    along the z-axis (not m.contains at a config-derived height) and pins it
    to the literal 3.0 mm value.
    """
    m = build_shell(SMALL)
    below = np.array([[0.0, 0.0, SMALL.base_thickness / 2]])
    above = np.array([[0.0, 0.0, SMALL.base_thickness + 10.0]])
    assert m.contains(below)[0], "point under the floor should be inside solid material"
    assert not m.contains(above)[0], "point above the floor should be inside the hollow cavity"

    origins = np.array([[0.0, 0.0, -10.0]])
    directions = np.array([[0.0, 0.0, 1.0]])
    locations, _, _ = m.ray.intersects_location(origins, directions)
    assert len(locations) >= 2, "expected at least an outer-floor and an inner-floor crossing"
    z_hits = np.sort(locations[:, 2])
    floor_thickness = z_hits[1] - z_hits[0]
    assert floor_thickness == pytest.approx(3.0, abs=1e-6), (
        f"measured floor thickness {floor_thickness:.4f} mm, expected exactly 3.0 mm"
    )


def _toy_shell(n_o: int, n_i: int) -> tuple[trimesh.Trimesh, np.ndarray]:
    """Minimal two-ring shell exercising _bridge_rings's general (mismatched
    ring size) path directly -- the same shape build_shell uses (tube + tube
    + rim bridge + two independent fans), scaled down and parametrised by an
    arbitrary (n_o, n_i) pair instead of the matched n_theta build_shell
    always uses today. See test_bridge_rings_handles_mismatched_ring_sizes.
    """
    r_out = np.full((n_o, 2), 10.0)
    z_out = np.array([0.0, 5.0])
    r_in = np.full((n_i, 2), 6.0)
    z_in = np.array([2.0, 5.0])

    v_out, f_out = revolve_grid(r_out, z_out)
    v_in, f_in = revolve_grid(r_in, z_in, flip=True)
    off_in = len(v_out)

    verts = [v_out, v_in]
    faces = [f_out, f_in + off_in]

    top_out = np.arange(n_o) * 2 + 1
    top_in = off_in + np.arange(n_i) * 2 + 1
    bridge = _bridge_rings(top_out, top_in)
    faces.append(bridge)

    bot_out = np.arange(n_o) * 2
    bot_in = off_in + np.arange(n_i) * 2
    apex_outer = off_in + len(v_in)
    apex_inner = apex_outer + 1
    verts.append(np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 2.0]]))
    faces.append(_fan(bot_out, apex_outer))
    faces.append(_fan(bot_in, apex_inner, flip=True))

    mesh = trimesh.Trimesh(np.concatenate(verts), np.concatenate(faces), process=False)
    return mesh, bridge


@pytest.mark.parametrize("n_o, n_i", [(13, 4), (100, 3)])
def test_bridge_rings_handles_mismatched_ring_sizes(n_o, n_i):
    """_bridge_rings's general merge-walk path is otherwise dead code by
    coverage: _inner_radius sets n_in_t = cfg.n_theta today, so every real
    VaseConfig only ever exercises the degenerate equal-size case. This test
    is what protects the triangle-budget lever documented in
    task-4-report.md ("Triangle budget lever for Task 5/7") -- reverting the
    inner surface to a coarser n_theta stays safe only as long as this path
    is known to still be correct, which nothing else here checks.
    """
    m, bridge = _toy_shell(n_o, n_i)
    assert len(bridge) == n_o + n_i, "bridge must use every ring edge exactly once"
    assert m.is_watertight
    assert m.is_winding_consistent
    assert m.euler_number == 2, f"expected genus 0, got euler {m.euler_number}"


def test_real_surface_respects_the_overhang_limit():
    """The design's central claim is that printability is a clamp on a scalar
    field. Nothing enforced it until here: profile.max_envelope_slope() measures the
    ENVELOPE, not the actual fractal surface. This measures |dr/dz| at fixed
    theta -- what the nozzle actually experiences as it climbs.

    Measured on the un-low-passed field this failed at 52.88 deg; the spec's
    Gaussian sigma = 0.5 mm brings it to 44.10 deg with zero loss of relief.
    """
    import numpy as np

    from fractalvase.julia import normalised_field
    from fractalvase.profile import radius_at, relief_amplitude

    cfg = VaseConfig(n_theta=320, n_z=400)
    z = np.linspace(cfg.band_lo, cfg.band_hi, cfg.n_z)
    field = normalised_field(cfg, cfg.n_theta, cfg.n_z)
    r = radius_at(z)[None, :] + relief_amplitude(z, cfg)[None, :] * np.tanh(1.6 * field)

    drdz = np.gradient(r, z[1] - z[0], axis=1)
    worst = np.degrees(np.arctan(np.abs(drdz).max()))
    assert worst <= 45.0, f"real surface overhangs at {worst:.2f} deg (limit 45)"
