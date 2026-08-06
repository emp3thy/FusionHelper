"""Supernova repair: sn_ceiling_t is redundant - ceiling thickness is
derived (H - floor - cavity), and the window cut bottoms out into the
slot void so stepping the param changes nothing (liveness param.dead).
Rewrite the window cut extent as the derived expression (over-cut 0.5
into the void so it always clears), then delete the parameter."""
import adsk.core
import adsk.fusion

FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["sn_floor_t", "sn_cavity_h",
                    "sn_g_float", "sn_roll_d", "sn_cap_ch", "sn_fuse_ch"],
}
INTERFERENCE_ALLOWED = []


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    up = des.userParameters

    feat = adsk.fusion.ExtrudeFeature.cast(
        root.features.itemByName("window_seed_cut"))
    ext = adsk.fusion.DistanceExtentDefinition.cast(feat.extentOne)
    ext.distance.expression = "14 mm - sn_floor_t - sn_cavity_h + 0.5 mm"
    print("FH window extent now:", ext.distance.expression,
          "=", ext.distance.value)

    dead = up.itemByName("sn_ceiling_t")
    dead.deleteMe()
    print("FH sn_ceiling_t deleted")


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
