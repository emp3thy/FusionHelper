"""Supernova repair v3: roller height was a literal 10.4 mm, so verify's
combined param step (floor + float + ceiling all +0.2) jammed the
rollers into the slot ceiling (edit.introduces_clash x6). Derive the
roller extent so the 0.5 mm top gap is preserved under any edit."""
import adsk.core
import adsk.fusion

FH_ATTEMPT = 5
FH_OPTS = {
    "only_params": ["sn_floor_t", "sn_ceiling_t",
                    "sn_g_float", "sn_roll_d", "sn_cap_ch", "sn_fuse_ch"],
}
INTERFERENCE_ALLOWED = []

HEALTHY = None

DERIVED = "14 mm - sn_floor_t - sn_g_float - sn_ceiling_t - 0.5 mm"


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    feat = adsk.fusion.ExtrudeFeature.cast(
        root.features.itemByName("roller_extrude"))
    ext = adsk.fusion.DistanceExtentDefinition.cast(feat.extentOne)
    old = ext.distance.expression.strip()
    new = "-( %s )" % DERIVED if old.startswith("-") else DERIVED
    ext.distance.expression = new
    adsk.doEvents()
    print("FH roller extent: '%s' -> '%s' = %.4f cm (health %d)"
          % (old, new, ext.distance.value, feat.healthState))
    if feat.healthState not in healthy:
        raise RuntimeError("roller_extrude unhealthy after edit")
    pat = root.features.itemByName("roller_pattern")
    if pat.healthState not in healthy:
        raise RuntimeError("roller_pattern unhealthy after edit")
    print("FH roller pattern healthy")


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
