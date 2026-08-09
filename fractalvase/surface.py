"""Structured (theta, z) grid to a closed, manifold shell.

Cheaper than marching cubes by roughly three orders of magnitude, and
manifold by construction rather than by repair. Requires the radius to be
single-valued in theta -- true for this design by the slope constraint.
"""

from __future__ import annotations

import numpy as np
import trimesh

from fractalvase.config import VaseConfig
from fractalvase.julia import normalised_field
from fractalvase.profile import radius_at, relief_amplitude, smooth_radius


def revolve_grid(
    radius: np.ndarray, z: np.ndarray, flip: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Open tube from a radius field.

    ``radius`` is ``(n_theta, n_z)``. Theta excludes 2*pi, so the seam closes
    by index wrap with no duplicate vertices to merge later. ``flip``
    reverses winding, for inward-facing surfaces.
    """
    n_theta, n_z = radius.shape
    theta = np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False)

    ct, st = np.cos(theta)[:, None], np.sin(theta)[:, None]
    zz = np.broadcast_to(z[None, :], radius.shape)
    verts = np.stack([(radius * ct).ravel(), (radius * st).ravel(), zz.ravel()], axis=1)

    i = np.arange(n_theta)[:, None]
    j = np.arange(n_z - 1)[None, :]
    i1 = (i + 1) % n_theta

    a = (i * n_z + j).ravel()
    b = (i1 * n_z + j).ravel()
    c = (i1 * n_z + j + 1).ravel()
    d = (i * n_z + j + 1).ravel()

    faces = np.concatenate([np.stack([a, b, c], axis=1), np.stack([a, c, d], axis=1)], axis=0)
    if flip:
        faces = faces[:, ::-1]
    return verts, faces


def _bridge_rings(outer: np.ndarray, inner: np.ndarray) -> np.ndarray:
    """Manifold triangle strip between two coplanar closed loops of possibly
    different vertex counts, e.g. the rim where a 640-point outer ring meets
    a 213-point inner ring.

    ``outer`` and ``inner`` are 1-D arrays of global vertex indices, ordered
    the same way around theta. A classic merge walk: at each step, advance
    whichever ring is further behind in fractional progress around the loop,
    emitting one triangle per advance. This uses every outer edge and every
    inner edge EXACTLY once (``len(outer) + len(inner)`` triangles total),
    so combined with each ring's own tube -- which also touches its edges
    exactly once, at its open end -- every edge reaches count 2 and the seam
    closes with no gaps and no double coverage.

    Do not use this to close two rings that are ALSO each independently
    fanned to a centre point (see ``build_shell``) -- that would touch the
    inner ring's edges a third time. A ring may be closed by bridging XOR by
    fanning, never both.
    """
    n_o, n_i = len(outer), len(inner)
    tris = []
    io = ii = 0
    while io < n_o or ii < n_i:
        step_outer = ii == n_i or (io < n_o and io / n_o <= ii / n_i)
        if step_outer:
            o0, o1 = outer[io % n_o], outer[(io + 1) % n_o]
            tris.append((o0, o1, inner[ii % n_i]))
            io += 1
        else:
            i0, i1 = inner[ii % n_i], inner[(ii + 1) % n_i]
            tris.append((outer[io % n_o], i1, i0))
            ii += 1
    return np.array(tris)


def _fan(rim: np.ndarray, apex_idx: int, flip: bool = False) -> np.ndarray:
    """Triangle fan closing a ring's boundary onto a single apex vertex."""
    nxt = np.roll(rim, -1)
    faces = np.stack([np.full(len(rim), apex_idx), nxt, rim], axis=1)
    return faces[:, ::-1] if flip else faces


def _outer_radius(cfg: VaseConfig) -> tuple[np.ndarray, np.ndarray]:
    """Radius field for the fractal-bearing outer surface."""
    z = np.linspace(0.0, cfg.height, cfg.n_z)
    base = radius_at(z)[None, :]
    amp = relief_amplitude(z, cfg)[None, :]

    field = np.zeros((cfg.n_theta, cfg.n_z), dtype=float)
    in_band = (z >= cfg.band_lo) & (z <= cfg.band_hi)
    band_field = normalised_field(cfg, cfg.n_theta, int(in_band.sum()))
    field[:, in_band] = band_field

    # tanh compresses the gradient so the slope clamp is satisfiable
    # without flattening the field
    return base + amp * np.tanh(1.6 * field), z


def _inner_radius(cfg: VaseConfig) -> tuple[np.ndarray, np.ndarray]:
    """Inner wall: smoothed profile offset inward, clamped so it can never
    bulge past the raw profile.

    Never offset the DETAILED outer surface -- that self-intersects wherever
    wall thickness exceeds the local radius of curvature.

    The ``minimum`` is load-bearing, not defensive. ``smooth_radius`` bulges
    OUTWARD at concave kinks, and at the throat (z = 262 mm, the vase's
    narrowest point) it exceeds the raw profile by 1.4202 mm -- which eats
    the wall down to 0.5798 mm, about 1.3 extrusion widths, exactly where the
    vase is most likely to snap. Clamping to the raw profile restores a full
    2.0000 mm minimum and costs 0.13% of interior volume.

    Starts at ``z = cfg.base_thickness``, not 0: running the cavity to z=0
    leaves a zero-thickness floor (the base membrane and the cavity floor
    are the same surface) and the vase is open underneath. Uses the SAME
    ``n_theta`` as the outer surface, not a coarser one: a resample between
    mismatched ring sizes (``round(i * n_in/n_out)``) produces long runs of
    duplicate indices -- 48 consecutive duplicates out of 96 for a 2:1 ratio
    -- which are degenerate (zero-area) triangles in the rim and get
    stripped by ``nondegenerate_faces``, leaving the mesh open. Matching
    ``n_theta`` removes the resample entirely; the z resolution may still be
    coarse, only theta has to match.
    """
    z = np.linspace(cfg.base_thickness, cfg.height, max(cfg.n_z // 3, 24))
    r = np.clip(np.minimum(smooth_radius(z), radius_at(z)) - cfg.wall, 0.5, None)
    return np.broadcast_to(r[None, :], (cfg.n_theta, z.size)).copy(), z


def build_shell(cfg: VaseConfig) -> trimesh.Trimesh:
    """Closed vase shell: outer tube, inner tube, a rim bridge at the top,
    and two independent fan caps at the bottom.

    Topology, not just index bookkeeping, drives this shape. The outer and
    inner walls are each open tubes (Euler characteristic 0). Bridging their
    top rings together (see ``_bridge_rings``) folds them into a single tube
    with two remaining open ends at the bottom: the outer ring (radius ~
    ``radius_at(0)``) and the inner ring (radius ~ that minus ``wall``).

    A first draft closed those two bottom rings with a second bridge (an
    annulus) plus a fan filling the annulus's inner hole -- the design intent
    described in earlier drafts as "annulus ... closed by a disc". That
    construction is topologically impossible without corrupting the mesh:
    revolving a closed profile curve around an axis it never touches always
    yields genus 1 (a torus, Euler characteristic 0), regardless of how
    carefully the index arithmetic is done, because gluing two open tubes at
    BOTH ends is exactly the standard construction of a torus. Confirmed by
    direct V - E + F computation on a bridged-only mesh (annulus, no fan):
    8928 - 26784 + 17856 = 0, not 2. Independently, adding a fan on top of
    an already-bridged inner ring makes that ring's edges shared by 3 faces
    (tube + bridge + fan), which is not a valid 2-manifold -- trimesh
    reports edges with multiplicity 3 there, not the 2 required.

    The actual fix has two parts (matches the ``base_thickness`` design
    correction -- see ``VaseConfig.base_thickness`` and ``_inner_radius``):

    1. The inner surface starts at ``z = base_thickness``, not 0, so the
       base is a genuinely solid disc rather than a zero-thickness membrane
       the cavity is open through. This also means the outer bottom ring
       (z=0) and the inner bottom ring (z=base_thickness) are two DIFFERENT
       rings at two different heights -- not one ring needing to serve both
       an annulus and a fan.
    2. Each of those two rings is closed by its OWN independent fan straight
       to the rotation axis (the outer ring to the true origin, the inner
       ring to a point directly above it at z=base_thickness) -- not bridged
       to each other. A bridge between them would touch the inner ring's
       edges a second time (on top of its own tube), reproducing the
       3-faces-per-edge defect above. The solid slab between the two flat
       caps needs no extra geometry: it is bounded on the sides by the
       outer wall's own continuous surface, unbroken across z=0..base_thickness.

    Both fans reaching the axis is what makes this genus 0 (each fan-closed
    ring contributes +1 to the Euler characteristic; the two open tubes and
    the rim bridge contribute 0 each: 0+0+0+1+1 = 2), which the
    bridge-only construction above could never do. Verified by
    ``test_shell_is_genus_zero_before_piercing`` and by direct V - E + F
    computation equalling 2 for both the SMALL test config and production.
    """
    r_out, z_out = _outer_radius(cfg)
    r_in, z_in = _inner_radius(cfg)

    v_out, f_out = revolve_grid(r_out, z_out)
    v_in, f_in = revolve_grid(r_in, z_in, flip=True)

    n_out_t, n_out_z = r_out.shape
    n_in_t, n_in_z = r_in.shape
    off_in = len(v_out)

    verts = [v_out, v_in]
    faces = [f_out, f_in + off_in]

    # --- rim: bridge the top rings directly together (a real, load-bearing
    # lip of thickness `wall`); no cap needed since it fully closes both.
    # n_in_t == n_out_t (see _inner_radius), so this degenerates to a plain
    # 1:1 quad strip -- _bridge_rings still handles it correctly.
    top_out = np.arange(n_out_t) * n_out_z + (n_out_z - 1)
    top_in = off_in + np.arange(n_in_t) * n_in_z + (n_in_z - 1)
    faces.append(_bridge_rings(top_out, top_in))

    # --- base: two independent fans, NOT a bridge (see build_shell's
    # docstring for why). The outer fan is the vase's true bottom face at
    # z=0; the inner fan caps the cavity floor at z=base_thickness, exactly
    # where the inner tube's own first ring already sits.
    bot_out = np.arange(n_out_t) * n_out_z
    bot_in = off_in + np.arange(n_in_t) * n_in_z
    apex_outer = len(v_out) + len(v_in)
    apex_inner = apex_outer + 1
    verts.append(np.array([[0.0, 0.0, 0.0], [0.0, 0.0, cfg.base_thickness]]))

    faces.append(_fan(bot_out, apex_outer))
    faces.append(_fan(bot_in, apex_inner, flip=True))

    mesh = trimesh.Trimesh(np.concatenate(verts), np.concatenate(faces), process=True)
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-8))
    mesh.remove_unreferenced_vertices()
    trimesh.repair.fix_winding(mesh)
    trimesh.repair.fix_normals(mesh)
    return mesh
