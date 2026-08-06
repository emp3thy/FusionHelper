"""HAYWIRE repair: (1) pin the ring-gear wall TOP rather than its height,
so stepping the base thickness can never push the wall up into the web
(that was the edit.introduces_clash); (2) give hw_fuse_ch real work -
an anti-fuse chamfer on the stator base rim, the z0 edge that faces the
chunks across a 0.5 mm gap; (3) drop the now-redundant hw_wall_h."""
import adsk.core
import adsk.fusion

FH_ATTEMPT = 4
FH_OPTS = {"only_params": ["hw_base_t", "hw_fuse_ch"]}
INTERFERENCE_ALLOWED = []


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    up = des.userParameters
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    feat = adsk.fusion.ExtrudeFeature.cast(
        root.features.itemByName("ring_teeth_extrude"))
    ext = adsk.fusion.DistanceExtentDefinition.cast(feat.extentOne)
    old = ext.distance.expression.strip()
    new = "11 mm - hw_base_t"
    ext.distance.expression = ("-( %s )" % new if old.startswith("-")
                               else new)
    adsk.doEvents()
    print("FH wall: '%s' -> '%s' = %.4f cm (health %d)"
          % (old, ext.distance.expression, ext.distance.value,
             feat.healthState))
    if feat.healthState not in healthy:
        raise RuntimeError("ring_teeth_extrude unhealthy")

    stator = root.bRepBodies.itemByName("hw_stator")
    out = adsk.core.ObjectCollection.create()
    for e in stator.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
        g = e.geometry
        r = getattr(g, "radius", None)
        if r is None or not (3.10 < r < 3.20):
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
        out, adsk.core.ValueInput.createByString("hw_fuse_ch"), True)
    cf = chf.add(ci)
    cf.name = "base_antifuse_chamfer"
    print("FH anti-fuse chamfer added to the stator base rim")

    up.itemByName("hw_wall_h").deleteMe()
    print("FH hw_wall_h deleted (wall top now pinned at 11 mm)")


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
