"""Bundler contract: expand the kit import, append the stub, refuse
invalid input, stay deterministic."""
import re
import sys
import types
from pathlib import Path

import pytest

adsk = types.ModuleType("adsk")
core = types.ModuleType("adsk.core")
fusion = types.ModuleType("adsk.fusion")
adsk.core, adsk.fusion = core, fusion
adsk.doEvents = lambda: None
sys.modules["adsk"] = adsk
sys.modules["adsk.core"] = core
sys.modules["adsk.fusion"] = fusion


class _Enum:
    def __getattr__(self, name):
        return name


core.ValueInput = types.SimpleNamespace(createByString=lambda s: ("VI", s))
core.Point3D = types.SimpleNamespace(create=lambda x, y, z: (x, y, z))
core.ObjectCollection = types.SimpleNamespace(
    create=lambda: types.SimpleNamespace(_items=[], add=lambda *a: None))
fusion.FeatureOperations = _Enum()
fusion.DimensionOrientations = _Enum()
fusion.ExtentDirections = _Enum()
fusion.FeatureHealthStates = _Enum()
fusion.PatternComputeOptions = _Enum()
fusion.PatternDistanceType = _Enum()
fusion.DistanceExtentDefinition = types.SimpleNamespace(
    create=lambda v: ("DIST", v))
fusion.Design = types.SimpleNamespace(cast=lambda p: p)

from fusionhelper import bundle, buildkit, verify  # noqa: E402, I001

FIX = Path(__file__).parent / "fixtures" / "bundle"
AUTHOR = (FIX / "author_ok.py").read_text(encoding="utf-8")
KIT = Path(buildkit.__file__).read_text(encoding="utf-8")


def test_bundle_expands_import_and_appends_stub():
    out = bundle.bundle_text(AUTHOR, KIT)
    assert not re.search(r"^\s*from fusionhelper\.buildkit import", out, re.MULTILINE)
    assert "class BuildCtx" in out
    assert out.rstrip().endswith(verify.STUB_TEXT.rstrip())
    assert f"# fh-bundle: kit begin v{buildkit.KIT_VERSION}" in out
    assert "# fh-bundle: kit end" in out


def test_bundle_is_deterministic():
    assert bundle.bundle_text(AUTHOR, KIT) == bundle.bundle_text(AUTHOR, KIT)


def test_refuses_already_bundled():
    once = bundle.bundle_text(AUTHOR, KIT)
    with pytest.raises(bundle.BundleError, match="already bundled"):
        bundle.bundle_text(once, KIT)


def test_refuses_missing_import():
    with pytest.raises(bundle.BundleError, match="buildkit import"):
        bundle.bundle_text("def run(_c):\n    pass\n", KIT)


def test_refuses_author_with_stub():
    with_stub = verify.append_to(AUTHOR)
    with pytest.raises(bundle.BundleError, match="stub"):
        bundle.bundle_text(with_stub, KIT)


def test_refuses_kit_name_collision():
    author = AUTHOR + "\n\nclass BuildCtx:\n    pass\n"
    with pytest.raises(bundle.BundleError, match="collision"):
        bundle.bundle_text(author, KIT)


def test_bundle_file_writes_artifact(tmp_path):
    src = tmp_path / "myscript.py"
    src.write_text(AUTHOR, encoding="utf-8")
    out_path = bundle.bundle_file(src)
    assert out_path == tmp_path / "myscript.bundled.py"
    assert "class BuildCtx" in out_path.read_text(encoding="utf-8")


def test_artifact_compiles():
    compile(bundle.bundle_text(AUTHOR, KIT), "artifact.py", "exec")
