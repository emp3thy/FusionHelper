"""Supernova repair v2 (sign-preserving). The blind-cut extents encode
direction in the distance SIGN (window is '-( sn_ceiling_t )'); repair
v1 wrote a positive expression and flipped the cut into air. This time:
- slot cavity extent -> derived '14 mm - sn_floor_t - sn_ceiling_t'
  (sign-preserved), so sn_ceiling_t genuinely drives the ceiling;
- window extent -> sign-preserved 'sn_ceiling_t + 0.5 mm' (over-cuts
  into the void so the window always clears);
- delete now-redundant sn_cavity_h."""
import adsk.core
import adsk.fusion

FH_ATTEMPT = 3
FH_OPTS = {
    "only_params": ["sn_floor_t", "sn_ceiling_t",
                    "sn_g_float", "sn_roll_d", "sn_cap_ch", "sn_fuse_ch"],
}
INTERFERENCE_ALLOWED = []


def _set_extent(root, name, magnitude_expr):
    feat = adsk.fusion.ExtrudeFeature.cast(root.features.itemByName(name))
    ext = adsk.fusion.DistanceExtentDefinition.cast(feat.extentOne)
    old = ext.distance.expression.strip()
    neg = old.startswith("-")
    new = "-( %s )" % magnitude_expr if neg else magnitude_expr
    ext.distance.expression = new
    adsk.doEvents()
    print("FH %s: '%s' -> '%s' = %.4f cm (health %d)"
          % (name, old, new, ext.distance.value, feat.healthState))
    if feat.healthState not in (
            adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
            adsk.fusion.FeatureHealthStates.WarningFeatureHealthState):
        raise RuntimeError("%s unhealthy after extent edit" % name)


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    up = des.userParameters

    _set_extent(root, "slot_seed_cut", "14 mm - sn_floor_t - sn_ceiling_t")
    _set_extent(root, "window_seed_cut", "sn_ceiling_t + 0.5 mm")

    pat = root.features.itemByName("cutout_pattern")
    if pat.healthState not in (
            adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
            adsk.fusion.FeatureHealthStates.WarningFeatureHealthState):
        raise RuntimeError("cutout_pattern unhealthy after edits")
    print("FH pattern healthy")

    dead = up.itemByName("sn_cavity_h")
    dead.deleteMe()
    print("FH sn_cavity_h deleted")


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
