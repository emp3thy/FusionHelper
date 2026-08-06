"""ORRERY repair: give or_fuse_ch real work - an anti-fuse chamfer on the
stator base rim, the z0 edge facing the outer ring across a 0.5 mm gap."""
import adsk.core
import adsk.fusion

FH_ATTEMPT = 9
FH_OPTS = {"only_params": ["or_base_t", "or_fuse_ch",
                           "or_roll_d", "or_stub_d"]}
INTERFERENCE_ALLOWED = []


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    stator = root.bRepBodies.itemByName("or_stator")
    if stator is None:
        raise RuntimeError("or_stator not found")

    out = adsk.core.ObjectCollection.create()
    for e in stator.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
        g = e.geometry
        r = getattr(g, "radius", None)
        if r is None or not (2.85 < r < 2.95):
            continue
        bb = e.boundingBox
        if (abs(bb.maxPoint.z - bb.minPoint.z) < 0.02
                and abs(bb.minPoint.z) < 0.02):
            out.add(e)
    if out.count != 1:
        raise RuntimeError("base rim edge %d != 1" % out.count)
    chf = root.features.chamferFeatures
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        out, adsk.core.ValueInput.createByString("or_fuse_ch"), True)
    cf = chf.add(ci)
    cf.name = "base_antifuse_chamfer"
    print("FH anti-fuse chamfer added; bodies %d" % root.bRepBodies.count)


# fusionhelper: verification stub v1
def _fh_verify_entry():
    import os, json, traceback
    home = os.environ.get('FUSIONHELPER_HOME') or os.path.join(
        os.environ.get('LOCALAPPDATA', ''), 'FusionHelper')

    def _bail(code, msg):
        return 'FH_VERDICT1 ' + json.dumps(
            {'v': 1, 'status': 'error', 'code': code, 'msg': msg, 'home': home},
            separators=(',', ':'))

    try:
        with open(os.path.join(home, 'fh_verify.py'), encoding='utf-8') as f:
            src = f.read()
    except Exception as e:
        return _bail('verify.block_missing', str(e))
    ns: dict = {'__name__': 'fh_verify'}   # annotated: else pyright infers dict[str, str]
    try:
        exec(compile(src, 'fh_verify.py', 'exec'), ns)
        g = globals()
        return ns['fh_verify'](
            clearances=g.get('CLEARANCES'),
            face_specs=g.get('FACE_SPECS'),
            datum_heights_cm=g.get('DATUM_HEIGHTS_CM'),
            digest=g.get('DIGEST'),
            interference_allowed=g.get('INTERFERENCE_ALLOWED'),
            expect_dead=g.get('EXPECT_DEAD'),
            refs=g.get('FH_REFS', {}),
            attempt=g.get('FH_ATTEMPT', 1),
            **g.get('FH_OPTS', {}))
    except Exception:
        return _bail('verify.internal', traceback.format_exc()[-600:])


def _fh_wrap(inner):
    def _wrapped(_context: str):
        inner(_context)                 # NOT wrapped: build exceptions must escape
        print(_fh_verify_entry())
    return _wrapped


run = _fh_wrap(run)
