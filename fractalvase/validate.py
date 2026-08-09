"""The gate. Nothing reaches a slicer without passing.

House rule: a CAD error should be impossible to express or impossible to
miss. This module chooses impossible to miss -- it raises, it does not
return a warning that a caller can ignore.

The genus check (``euler_number == 2 - 2 * n_holes``) is the only cheap
invariant that separates "the boolean did the work" from "the boolean
silently did nothing": a cutter too shallow to span the wall leaves
``is_watertight``, ``is_winding_consistent``, ``is_volume``, ``body_count``,
and positive volume all green on an effectively unpierced solid (see
holes.pierce's docstring and task-5-report.md for a measured case). Every
other check here guards a distinct, independently-triggerable defect: a
flipped single face leaves a mesh watertight with a volume that is still
positive but wrong (measured: 500 mm^3 instead of 1000 mm^3 for a 10x10x10
box with one face reversed) and only ``is_winding_consistent`` catches it.
"""

from __future__ import annotations

import trimesh

from fractalvase.config import VaseConfig


class MeshInvalid(Exception):
    """Raised when a mesh must not be exported."""


def validate(mesh: trimesh.Trimesh, cfg: VaseConfig, n_holes: int) -> dict[str, object]:
    """Check a finished mesh. Raises MeshInvalid on the first failure."""
    problems: list[str] = []

    if not mesh.is_watertight:
        problems.append("not watertight: some edge is not shared by exactly two faces")
    if not mesh.is_winding_consistent:
        problems.append("winding is inconsistent")
    if mesh.volume <= 0:
        problems.append(f"volume is {mesh.volume:.3f}: mesh is inside-out")
    if mesh.body_count != 1:
        problems.append(f"{mesh.body_count} bodies: expected exactly 1")

    expected_euler = 2 - 2 * n_holes
    if mesh.euler_number != expected_euler:
        problems.append(
            f"euler_number {mesh.euler_number} != {expected_euler} "
            f"(genus mismatch for {n_holes} holes): hole topology is wrong"
        )

    broken = trimesh.repair.broken_faces(mesh)
    if len(broken):
        problems.append(f"{len(broken)} broken faces")

    x, y, z = mesh.extents
    if x > 135.0 or y > 135.0 or z > cfg.height:
        problems.append(f"outside build envelope: {x:.1f} x {y:.1f} x {z:.1f} mm")

    if problems:
        raise MeshInvalid("; ".join(problems))

    return {
        "watertight": mesh.is_watertight,
        "volume_mm3": float(mesh.volume),
        "triangles": int(len(mesh.faces)),
        "euler_number": int(mesh.euler_number),
        "extents_mm": [round(float(v), 2) for v in mesh.extents],
        "holes": n_holes,
    }
