"""Package rev D's eight bodies into one named component.

Bodies are collected into a Python list BEFORE moving: moveToComponent
mutates root.bRepBodies, so iterating it live drops bodies. Volume and
name set are compared before/after, because moveToComponent has a known
body-resurfacing failure mode."""
import adsk.core
import adsk.fusion

FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": ["sn_rail_t", "sn_roll_d", "sn_stub_d",
                    "sn_cap_ch", "sn_fuse_ch", "sn3_engrave_d"],
}
INTERFERENCE_ALLOWED = []


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent

    bodies = []
    for b in root.bRepBodies:
        bodies.append(b)
    if not bodies:
        raise RuntimeError("no root bodies to package")
    before_names = sorted(b.name for b in bodies)
    before_vol = sum(b.volume for b in bodies)
    print("FH packaging %d bodies, %.3f cm3" % (len(bodies), before_vol))

    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = "supernova_72_revD"

    for b in bodies:
        adsk.doEvents()
        b.moveToComponent(occ)

    comp = occ.component
    after_names = sorted(b.name for b in comp.bRepBodies)
    after_vol = sum(b.volume for b in comp.bRepBodies)
    print("FH component '%s': %d bodies, %.3f cm3"
          % (comp.name, comp.bRepBodies.count, after_vol))
    print("FH bodies left at root: %d" % root.bRepBodies.count)

    if root.bRepBodies.count != 0:
        raise RuntimeError("%d bodies stranded at root"
                           % root.bRepBodies.count)
    if after_names != before_names:
        raise RuntimeError("body set changed: %s -> %s"
                           % (before_names, after_names))
    if abs(after_vol - before_vol) > 1e-6:
        raise RuntimeError("volume changed %.6f -> %.6f"
                           % (before_vol, after_vol))
    print("FH PACKAGE OK: names and volume identical")


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
