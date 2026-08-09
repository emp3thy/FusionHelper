import trimesh

from fractalvase import build_vase
from fractalvase.config import VaseConfig

FAST = VaseConfig(n_theta=96, n_z=80)


def test_end_to_end_build_passes_its_own_gate():
    mesh, report = build_vase(FAST)
    assert isinstance(mesh, trimesh.Trimesh)
    assert report["watertight"] is True
    assert report["triangles"] > 0
    assert report["holes"] > 0


def test_build_exports_3mf(tmp_path):
    mesh, _ = build_vase(FAST)
    out = tmp_path / "vase.3mf"
    mesh.export(out)
    assert out.exists() and out.stat().st_size > 1000


def test_build_respects_the_envelope():
    _, report = build_vase(FAST)
    x, y, z = report["extents_mm"]
    assert x <= 135.0 and y <= 135.0 and z <= 300.0
