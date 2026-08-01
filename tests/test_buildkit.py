"""Offline exercise of the buildkit with adsk faked (no Fusion needed)."""
import sys
import types

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

from fusionhelper import buildkit  # noqa: E402


class FakeParam:
    def __init__(self, value):
        self.value = value


class FakeApp:
    """Minimal shape BuildCtx reads in __init__."""
    def __init__(self):
        feats = types.SimpleNamespace(
            extrudeFeatures="EXT", rectangularPatternFeatures="PAT")
        self.activeProduct = types.SimpleNamespace(
            rootComponent=types.SimpleNamespace(
                features=feats,
                constructionPlanes="PLANES",
                xConstructionAxis="XAX",
                yConstructionAxis="YAX",
                xYConstructionPlane="XY"),
            userParameters=types.SimpleNamespace(
                itemByName=lambda n: FakeParam(4.2) if n == "p" else None))


def test_buildctx_binds_handles():
    ctx = buildkit.BuildCtx(FakeApp())
    assert ctx.extrudes == "EXT"
    assert ctx.patterns == "PAT"
    assert ctx.x_axis == "XAX"
    assert ctx.U == (1.0, 0.0, 0.0)
    assert ctx.val("p") == 4.2


def test_kit_version_is_string():
    assert isinstance(buildkit.KIT_VERSION, str)
