import pytest
import trimesh

from fractalvase.config import VaseConfig
from fractalvase.validate import MeshInvalid, validate

CFG = VaseConfig(n_theta=96, n_z=80)


def test_a_good_solid_passes():
    m = trimesh.creation.box(extents=(10, 10, 10))
    report = validate(m, CFG, n_holes=0)
    assert report["watertight"] is True
    assert report["euler_number"] == 2


def test_inside_out_mesh_is_rejected():
    m = trimesh.creation.box(extents=(10, 10, 10))
    m.invert()
    with pytest.raises(MeshInvalid, match="volume"):
        validate(m, CFG, n_holes=0)


def test_open_mesh_is_rejected():
    m = trimesh.creation.box(extents=(10, 10, 10))
    m.update_faces(list(range(len(m.faces) - 2)))
    with pytest.raises(MeshInvalid, match="watertight"):
        validate(m, CFG, n_holes=0)


def test_two_bodies_are_rejected():
    a = trimesh.creation.box(extents=(5, 5, 5))
    b = trimesh.creation.box(extents=(5, 5, 5))
    b.apply_translation([50, 0, 0])
    with pytest.raises(MeshInvalid, match="bod"):
        validate(a + b, CFG, n_holes=0)


def test_wrong_genus_is_rejected():
    """The one cheap check that catches bad hole topology."""
    m = trimesh.creation.box(extents=(10, 10, 10))
    with pytest.raises(MeshInvalid, match="genus|euler"):
        validate(m, CFG, n_holes=7)


def test_oversize_mesh_is_rejected():
    m = trimesh.creation.box(extents=(200, 10, 10))
    with pytest.raises(MeshInvalid, match="envelope"):
        validate(m, CFG, n_holes=0)


def test_torus_with_one_hole_passes():
    t = trimesh.creation.torus(major_radius=10.0, minor_radius=3.0)
    report = validate(t, CFG, n_holes=1)
    assert report["euler_number"] == 0


def test_inconsistent_winding_is_rejected():
    """Watertight and volume alone do not catch this: flipping a single
    face's vertex order leaves every edge shared by exactly two faces (still
    watertight) and can leave the signed volume positive (500 mm^3 instead
    of the true 1000 mm^3 for a 10x10x10 box, measured directly), so only
    ``is_winding_consistent`` sees the defect."""
    m = trimesh.creation.box(extents=(10, 10, 10))
    faces = m.faces.copy()
    faces[0] = faces[0][::-1]
    bad = trimesh.Trimesh(vertices=m.vertices.copy(), faces=faces, process=False)
    assert bad.is_watertight
    assert bad.volume > 0
    with pytest.raises(MeshInvalid, match="winding"):
        validate(bad, CFG, n_holes=0)
