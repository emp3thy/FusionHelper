"""Generator for the Douady Helix fractal Julia vase."""

import trimesh

from fractalvase.config import DOUADY_HELIX, VaseConfig
from fractalvase.holes import pierce
from fractalvase.surface import build_shell
from fractalvase.validate import validate

__all__ = ["DOUADY_HELIX", "VaseConfig", "build_vase"]


def build_vase(cfg: VaseConfig = DOUADY_HELIX) -> tuple[trimesh.Trimesh, dict]:
    """Shell, pierce, gate. Raises MeshInvalid rather than emitting a bad mesh."""
    shell = build_shell(cfg)
    mesh, n_holes = pierce(shell, cfg)
    return mesh, validate(mesh, cfg, n_holes)
