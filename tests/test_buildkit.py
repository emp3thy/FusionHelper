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


class FakeBody:
    def __init__(self, volume, face_count=6):
        self.volume = volume
        self.faces = types.SimpleNamespace(count=face_count)


class FakeExtrudes:
    """Scripted extrude factory: each add() runs its side-effect."""
    def __init__(self, effects):
        self._effects = list(effects)
        self.deleted = 0

    def createInput(self, profs, op):
        return types.SimpleNamespace(
            profs=profs, op=op, participantBodies=None,
            setSymmetricExtent=lambda v, b: None,
            setOneSideExtent=lambda e, d: None)

    def add(self, inp):
        effect = self._effects.pop(0)
        effect()
        feat = types.SimpleNamespace(
            deleteMe=lambda: setattr(self, "deleted", self.deleted + 1),
            bodies=types.SimpleNamespace(
                item=lambda i: FakeBody(1.0), count=1))
        return feat


def _ctx_with_extrudes(effects):
    ctx = buildkit.BuildCtx(FakeApp())
    ctx.extrudes = FakeExtrudes(effects)  # type: ignore
    return ctx


def test_sym_cut_volume_gate_fires_on_noop():
    body = FakeBody(volume=10.0)
    ctx = _ctx_with_extrudes([lambda: None])   # cut removes nothing
    try:
        ctx.sym_cut("PROFS", "2 mm", [body])
        raise AssertionError("expected RuntimeError")
    except RuntimeError as e:
        assert "removed no volume" in str(e)
    assert ctx.extrudes.deleted == 1   # failed feature cleaned up


def test_sym_cut_passes_when_volume_drops():
    body = FakeBody(volume=10.0)
    ctx = _ctx_with_extrudes(
        [lambda: setattr(body, "volume", 9.0)])
    feat = ctx.sym_cut("PROFS", "2 mm", [body])
    assert feat is not None


def test_blind_cut_flips_direction_then_caches():
    body = FakeBody(volume=10.0)
    ctx = _ctx_with_extrudes([
        lambda: None,                                # first direction: no-op
        lambda: setattr(body, "volume", 9.5),        # flipped: works
        lambda: setattr(body, "volume", 9.0),        # cached dir next call
    ])
    ctx.blind_cut("P", "1 mm", [body], kind="k")
    assert ctx.extrudes.deleted == 1  # type: ignore       # failed attempt removed
    ctx.blind_cut("P", "1 mm", [body], kind="k")     # one effect consumed
    assert not ctx.extrudes._effects  # type: ignore       # cache: no retry spent


def test_checked_newbody_predicate_flip():
    ctx = _ctx_with_extrudes([lambda: None, lambda: None])
    calls = []

    def predicate(b):
        calls.append(b)
        return len(calls) == 2                        # reject first direction
    feat, body = ctx.checked_newbody("P", "1 mm", predicate, "nb")
    assert feat is not None and body is not None
    assert ctx.extrudes.deleted == 1  # type: ignore


class FakePatterns:
    """Scripted pattern factory. Each add() consumes (raises, health,
    effect); effect mutates watched bodies."""
    def __init__(self, script):
        self._script = list(script)
        self.inputs = []
        self.deleted = 0

    def createInput(self, coll, ax, n, dd, dist_type):
        inp = types.SimpleNamespace(
            coll=coll, ax=ax, n=n, dd=dd,
            patternComputeOption=None,
            setDirectionTwo=lambda *a: None)
        self.inputs.append(inp)
        return inp

    def add(self, inp):
        raises, health, effect = self._script.pop(0)
        if raises:
            raise RuntimeError("R-Pattern85 / Compute Failed")
        effect()
        return types.SimpleNamespace(
            healthState="HealthyFeatureHealthState",
            deleteMe=lambda: setattr(self, "deleted", self.deleted + 1),
            bodies=types.SimpleNamespace(count=0, item=lambda i: None))


def _ctx_with_patterns(script):
    ctx = buildkit.BuildCtx(FakeApp())
    ctx.patterns = FakePatterns(script)  # type: ignore
    return ctx


def test_pattern_cut_requires_exactly_one_threshold():
    ctx = buildkit.BuildCtx(FakeApp())
    try:
        ctx.pattern_cut([], "AX", "3", "10 mm", [])
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    try:
        ctx.pattern_cut([], "AX", "3", "10 mm", [],
                        min_vol_cm3=1.0, min_new_faces=4)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_pattern_cut_volume_threshold_validates():
    body = FakeBody(volume=10.0)
    ctx = _ctx_with_patterns(
        [(False, None, lambda: setattr(body, "volume", 8.0))])
    f = ctx.pattern_cut(["CUT"], ctx.x_axis, "3", "10 mm", [body],
                        min_vol_cm3=1.5)
    assert f is not None


def test_pattern_retries_flipped_distance_on_raise():
    body = FakeBody(volume=10.0)
    ctx = _ctx_with_patterns([
        (True, None, None), (True, None, None),   # +d: both modes raise
        (False, None, lambda: setattr(body, "volume", 8.0)),  # -d works
    ])
    ctx.pattern_cut(["CUT"], ctx.x_axis, "3", "10 mm", [body],
                    min_vol_cm3=1.5)
    dds = [inp.dd for inp in ctx.patterns.inputs]  # type: ignore
    assert any(d[1].startswith("-(") for d in dds)


def test_pattern_bodies_requires_predicate():
    ctx = _ctx_with_patterns([(False, None, lambda: None)])
    out = ctx.pattern_bodies([FakeBody(1.0)], ctx.x_axis, "2", "5 mm",
                             lambda f: True)
    assert out == []          # fake pattern has zero result bodies
