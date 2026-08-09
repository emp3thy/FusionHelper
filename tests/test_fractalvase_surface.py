import numpy as np
import pytest
import trimesh

from fractalvase.config import VaseConfig
from fractalvase.surface import build_shell, revolve_grid

# small grid: these tests check topology, not detail
SMALL = VaseConfig(n_theta=96, n_z=80)


def test_revolve_grid_seam_has_no_duplicate_vertices():
    n_t, n_z = 16, 5
    r = np.full((n_t, n_z), 5.0)
    z = np.linspace(0, 10, n_z)
    v, f = revolve_grid(r, z)
    assert len(v) == n_t * n_z, "seam vertex duplicated; theta must not include 2pi"


def test_revolve_grid_winding_is_outward():
    n_t, n_z = 32, 4
    r = np.full((n_t, n_z), 10.0)
    z = np.linspace(0, 20, n_z)
    m = trimesh.Trimesh(*revolve_grid(r, z), process=False)
    assert m.is_winding_consistent


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
    the raw profile by 1.4202 mm, which would leave a 0.5798 mm wall -- about
    1.3 extrusion widths -- at the vase's narrowest point. _inner_radius
    clamps against the raw profile to prevent exactly this.
    """
    import numpy as np

    from fractalvase.profile import radius_at, smooth_radius

    cfg = VaseConfig(n_theta=96, n_z=80)
    z = np.linspace(0.0, cfg.height, 3001)

    # outer at its thinnest over theta is the bare profile (field contributes >= 0)
    outer_min = radius_at(z)
    inner = np.clip(np.minimum(smooth_radius(z), radius_at(z)) - cfg.wall, 0.5, None)
    clearance = outer_min - inner

    assert clearance.min() >= cfg.wall - 1e-9, (
        f"wall thins to {clearance.min():.4f} mm at z = {z[np.argmin(clearance)]:.1f} mm"
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
    """
    m = build_shell(SMALL)
    below = np.array([[0.0, 0.0, SMALL.base_thickness / 2]])
    above = np.array([[0.0, 0.0, SMALL.base_thickness + 10.0]])
    assert m.contains(below)[0], "point under the floor should be inside solid material"
    assert not m.contains(above)[0], "point above the floor should be inside the hollow cavity"


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
