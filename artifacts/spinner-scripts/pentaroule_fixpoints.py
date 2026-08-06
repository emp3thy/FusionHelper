"""Repair: fix loose sketch points left by isFixed-on-curves-only in the
fixed-art sketches (reuleaux_profile, nut_pockets, dimple_seed_profile),
then re-verify. Curves were fixed; their endpoints/centres were not."""
import adsk.core
import adsk.fusion

FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": [
        "pr_t", "pr_seat_d", "pr_lead", "pr_chamf",
        "pr_pocket_floor", "pr_pocket_h", "pr_stem_d",
    ],
}
INTERFERENCE_ALLOWED = []

TARGET_SKETCHES = ("reuleaux_profile", "nut_pockets", "dimple_seed_profile")


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    fixed = 0
    for sk in root.sketches:
        if sk.name not in TARGET_SKETCHES:
            continue
        for sp in sk.sketchPoints:
            adsk.doEvents()
            if sp.isFullyConstrained or sp.isFixed:
                continue
            sp.isFixed = True
            fixed += 1
    print("FH fixed %d loose sketch points" % fixed)


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
