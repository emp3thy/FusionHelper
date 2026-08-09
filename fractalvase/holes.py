"""Pierced lattice, cut by boolean subtraction (decision C1-B).

Holes are pointed arches, not round: a round hole's crown is an unsupported
bridge, while a gothic arch is self-supporting. Each cutter's crown is built
against GLOBAL Z, not the local surface normal -- decision C4-A tried the
opposite (leaning the crown to follow the helix, on the theory that a
globally-oriented arch degrades toward a bridge on the leaning face) and
is now known to be wrong, for a reason more basic than any one measurement:
there is no lean to correct for. ``surface.revolve_grid`` places every
vertex at ``(r*cos(theta), r*sin(theta), z)`` with ``theta`` from a plain
``linspace`` that never depends on ``z`` -- the shell is a plain surface of
revolution around the Z axis, with zero shear. ``twist_rate_rad_per_mm``
only appears in ``julia._map_to_plane``, where it steers which point of the
complex plane gets SAMPLED at a given (theta, z) -- it rotates which piece
of the fractal pattern is drawn there, not where any vertex of the printed
solid actually sits. Because the geometry itself never leans, global
vertical is the only physically correct reference frame for an overhang
check, and correcting a hole's crown for the pattern's rotation was
correcting for something that isn't there. It also actively broke the
apex's built-in left/right symmetry -- one roof face pushed toward
horizontal (needs support), the other went needlessly steep, at every
non-zero lean angle and for either sign of the correction. See
``arch_prism`` for the measured angles. C4-A is superseded; do not
reinstate the lean correction.
"""

from __future__ import annotations

import numpy as np
import trimesh

from fractalvase.config import VaseConfig
from fractalvase.julia import normalised_field
from fractalvase.profile import radius_at, relief_amplitude, smooth_radius


def _field_grid(cfg: VaseConfig) -> tuple[np.ndarray, np.ndarray]:
    """The full band-limited field plus its z axis, computed once per pierce
    pass and shared between site selection and cutter sizing so both read
    the exact same samples (see ``_hole_sites_and_field``)."""
    full = normalised_field(cfg, cfg.n_theta, cfg.n_z)
    zf = np.linspace(cfg.band_lo, cfg.band_hi, cfg.n_z)
    return full, zf


def _field_at(cfg: VaseConfig, full: np.ndarray, zf: np.ndarray, theta, z):
    """Nearest-neighbour lookup into ``full`` at arbitrary (theta, z)."""
    ti = np.round(np.asarray(theta) / (2 * np.pi) * cfg.n_theta).astype(int) % cfg.n_theta
    zi = np.clip(np.searchsorted(zf, z), 0, cfg.n_z - 1)
    return full[ti, zi]


def _hole_sites_and_field(
    cfg: VaseConfig,
) -> tuple[list[dict], np.ndarray, np.ndarray]:
    """Shared implementation behind ``hole_sites``: also hands back the field
    grid so ``pierce`` can size cutters from the same samples that opened
    each site, instead of recomputing (and potentially drifting from) it.
    """
    full, zf = _field_grid(cfg)

    rows = np.arange(
        cfg.pierce_lo + cfg.hole_row_pitch / 2, cfg.pierce_hi, cfg.hole_row_pitch
    )
    sites: list[dict] = []
    for i, z in enumerate(rows):
        r = float(radius_at(np.array([z]))[0]) + float(
            relief_amplitude(np.array([z]), cfg)[0]
        )
        n = max(int(round(2 * np.pi * r / cfg.hole_col_pitch)), 3)
        theta = np.linspace(0, 2 * np.pi, n, endpoint=False) + (i % 2) * (np.pi / n)
        f = _field_at(cfg, full, zf, theta, np.full(n, z))
        keep = f >= cfg.hole_open_cut
        frac = (f[keep] - cfg.hole_open_cut) / max(1e-9, 1.0 - cfg.hole_open_cut)
        size = cfg.hole_size_min + frac * (cfg.hole_size_max - cfg.hole_size_min)
        for t, s in zip(theta[keep], size, strict=True):
            sites.append({"theta": float(t), "z": float(z), "size": float(s)})
    return sites, full, zf


def hole_sites(cfg: VaseConfig) -> list[dict]:
    """Seeded lattice: the lattice fixes topology, the field decides size.

    Thresholding CANNOT be used here. nu_hat is 1 on the interior of K_c and
    high near its boundary, and K_c is connected by construction (that is why
    the rabbit was chosen), so every super-level set is one connected blob.
    Measured: nu_hat > 0.62 selects a single region 75.38 mm tall by 87.24 mm
    of arc, which would cut the vase apart. Twelve threshold variants all give
    1-2 giant regions and zero usable holes. See docs/superpowers/specs/
    pierce_rule.py.

    Instead: rows pitched in z, each row staggered half a column against its
    neighbour (hex packing), column count derived from the LOCAL circumference
    so spacing is uniform in millimetres on the surface rather than in angle.
    Each site samples the field; below the cut it stays closed, above it the
    site opens to an arch sized by how far above the cut the field sits.

    The column count's circumference estimate (``radius_at(z) +
    relief_amplitude(z, cfg)``) uses the UNCOMPRESSED relief envelope, not
    the tanh-compressed true local radius ``pierce()`` actually places
    cutters at (see ``_local_outer_radius``) -- "uniform in millimetres on
    the surface" is therefore approximate, not exact. This is intentional:
    the estimate only sets how many columns a row gets, not where any
    cutter ends up, and the measured 4.62 mm ligament against the 2.0 mm
    floor has enough margin that the approximation costs nothing in
    practice. Tightening it to the exact local radius was considered and
    rejected as not worth the complexity.

    Measured at the shipped parameters: 43 holes over 6 rows, sizes 3.09 to
    8.00 mm, minimum ligament 4.62 mm against the 2.0 mm floor. See
    docs/superpowers/specs/seed_lattice.py.

    All 43 holes fall inside a single ~103 degree arc of theta, not spread
    around the vase -- the field's high region (where nu_hat clears
    ``hole_open_cut``) sits in one sector at this ``c``, so the lattice
    ornaments one face rather than circling the vase. This was measured,
    raised, and reviewed with the user, who chose to KEEP it: a deliberate
    windowed face rather than an all-around pattern. Do not "fix" this by
    spreading the lattice or loosening the cut to open more of the
    circumference -- it is accepted behaviour, not a defect.
    """
    sites, _, _ = _hole_sites_and_field(cfg)
    return sites


def arch_prism(
    theta: float,
    z_c: float,
    size: float,
    r_out: float,
    cfg: VaseConfig,
) -> trimesh.Trimesh:
    """A pointed-arch prism, swept radially through the wall.

    Built in a local frame with +Z along the GLOBAL print direction, then
    placed on the surface at (theta, z_c). The crown is deliberately NOT
    corrected for the helix's local lean (former decision C4-A, superseded
    -- see the module docstring): print layers are horizontal in global Z
    regardless of how the surface leans, so self-support is a global-Z
    property, and leaning the crown to track the surface only breaks the
    apex's built-in 45-degree symmetry. Measured on the real shell: with the
    lean correction, the two roof faces split to roughly 45 +/- lean degrees
    from vertical (about 22 and 67 degrees at production sites, lean being
    ~20-23 degrees near the belly) -- one side comfortably clears the limit,
    the other blows through it by more than 20 degrees, for every real site
    tested and for either sign of the correction. Without it, both roof
    faces sit at exactly ``arch_apex_deg`` from vertical by construction
    (see the outline below: rise and run are both ``half_w``), independent
    of theta or z.

    ``size`` is the hole's width and height in MILLIMETRES on the surface,
    supplied by ``hole_sites`` from the field. It is the same in both axes so
    the arch stays proportioned as it scales.

    ``extrude_polygon`` builds the 2-D arch (width along local X, height
    along local Y) and pushes it along local Z by ``depth`` -- so Z is the
    through-wall punch direction coming out of ``extrude_polygon``, X is
    width, Y is height. Going into the final ``theta`` rotation about the
    global Z axis, whatever sits on local X lands on the RADIAL direction
    and whatever sits on local Y lands on the TANGENTIAL direction (global Z
    is untouched by a rotation about Z, so it stays "up"). The permutation
    matrix below therefore sends depth (old Z) to X (radial-to-be), width
    (old X) to Y (tangential-to-be), and height (old Y) to Z (vertical).
    Measured directly: swapping only the translation offset without this
    permutation put the arch's WIDTH on the radial axis and the PUNCH DEPTH
    on the tangential axis -- a cutter as narrow as 3 mm radially against a
    58+ mm outer radius, exactly the tangent/zero-volume-intersection
    failure this task is built to catch (see holes.py module tests and
    task-5-report.md).
    """
    half_w = max(size / 2.0, cfg.min_ligament / 2.0)
    half_h = max(size / 2.0, cfg.min_ligament / 2.0)
    apex = half_w / np.tan(np.radians(cfg.arch_apex_deg))

    # 2D arch outline: flat bottom, straight sides, pointed crown
    outline = np.array(
        [
            [-half_w, -half_h],
            [half_w, -half_h],
            [half_w, half_h - apex],
            [0.0, half_h],
            [-half_w, half_h - apex],
        ]
    )
    # Comfortably through the wall from both sides regardless of theta or z.
    # ``r_out`` is the TRUE local mid-wall radius (pierce()'s job to compute),
    # and the true local wall thickness (outer surface minus inner surface)
    # is bounded by wall + relief_peak -- outer can bulge out by up to
    # relief_peak, inner never does, and the profile-only difference the
    # inner clamp introduces is small next to that (measured max 7.63 mm
    # against the 9.0 mm bound across the full DOUADY_HELIX lattice). Doubling
    # that bound and centering on the true midpoint leaves roughly a full
    # wall+relief_peak of margin on EACH side even at the worst-case site,
    # not merely a fixed multiple of the nominal wall -- see pierce()'s
    # docstring for the notch-not-a-hole failure this replaced.
    depth = 2.0 * (cfg.wall + cfg.relief_peak)
    # trimesh doesn't declare `path` in its top-level __all__, so pyright
    # can't see the submodule attribute chain even though it resolves fine
    # at runtime (matches this repo's existing convention for third-party
    # stub gaps, e.g. artifacts/spinner-scripts' Autodesk API suppressions)
    polygon = trimesh.path.polygons.Polygon(outline)  # pyright: ignore[reportAttributeAccessIssue]
    prism = trimesh.creation.extrude_polygon(polygon, height=depth)

    # depth(old Z) -> X, width(old X) -> Y, height(old Y) -> Z (see docstring)
    permute = np.eye(4)
    permute[:3, :3] = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    prism.apply_transform(permute)
    prism.apply_translation([-depth / 2.0, 0.0, 0.0])

    # No lean correction here -- see module docstring (former decision
    # C4-A, superseded). The crown stays aligned to global Z: local Z is
    # already the height/apex axis after the permutation above, so the
    # remaining steps just place it on the surface.
    prism.apply_translation([0.0, 0.0, z_c])
    prism.apply_transform(
        trimesh.transformations.rotation_matrix(theta, [0, 0, 1], [0, 0, 0])
    )
    prism.apply_translation(
        [r_out * np.cos(theta), r_out * np.sin(theta), 0.0]
    )
    return prism


def _local_outer_radius(
    cfg: VaseConfig, full: np.ndarray, zf: np.ndarray, theta: float, z: float
) -> float:
    """True local outer radius at (theta, z) -- same formula as
    ``surface._outer_radius``, evaluated at one point instead of the whole
    grid, so ``pierce`` sees exactly the surface ``build_shell`` built.
    """
    f = float(_field_at(cfg, full, zf, theta, z))
    base = float(radius_at(np.array([z]))[0])
    amp = float(relief_amplitude(np.array([z]), cfg)[0])
    return base + amp * np.tanh(1.6 * f)


def _local_inner_radius(cfg: VaseConfig, z: float) -> float:
    """True local inner radius at z -- same formula as
    ``surface._inner_radius`` (theta-independent, matching that the inner
    wall carries no relief), evaluated at one point.
    """
    r = min(float(smooth_radius(np.array([z]))[0]), float(radius_at(np.array([z]))[0]))
    return max(r - cfg.wall, 0.5)


def pierce(shell: trimesh.Trimesh, cfg: VaseConfig) -> tuple[trimesh.Trimesh, int]:
    """Cut the lattice band. Returns (mesh, hole_count).

    Each cutter is centred on the TRUE local mid-wall radius at its own
    (theta, z) -- the midpoint between ``_local_outer_radius`` (which reads
    the field, not just the peak relief) and ``_local_inner_radius``. Using
    a fixed peak-relief estimate (``radius_at(z) + relief_peak``) instead of
    the local field value was tried and measured to fail: relief_peak
    (7.0 mm) is a ceiling reached only where the field saturates, so at a
    typical site the estimate sits several mm further out than the true
    surface, and centering the cutter there put its own inner face INSIDE
    the wall rather than past the cavity -- a shallow notch, not a
    through-hole. Confirmed directly: single-cutter test against the real
    shell removed material (is_watertight stayed True, volume dropped ~16
    mm^3 of ~295000) but left euler_number at 2, unchanged from the
    unpierced solid -- the boolean succeeded and did nothing, exactly the
    failure mode this task is built to catch, just shallower than a literal
    zero-volume tangent case. See task-5-report.md.
    """
    sites, full, zf = _hole_sites_and_field(cfg)
    if not sites:
        return shell, 0

    cutters = []
    for s in sites:
        r_out = _local_outer_radius(cfg, full, zf, s["theta"], s["z"])
        r_in = _local_inner_radius(cfg, s["z"])
        center = (r_in + r_out) / 2.0
        cutters.append(arch_prism(s["theta"], s["z"], s["size"], center, cfg))

    result = trimesh.boolean.difference([shell, *cutters], engine="manifold")
    return result, len(sites)
