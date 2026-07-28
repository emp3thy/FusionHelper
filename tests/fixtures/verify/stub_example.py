import adsk.core, adsk.fusion

FH_REFS = {}


def fh_ref(role: str, entity):
    """Register role -> entityToken at authoring time, for the verification block."""
    FH_REFS[role] = entity.entityToken
    return entity


CLEARANCES = [{'between': ['lid.inner_face', 'boss.top_face'], 'min': '0.08'}]
FACE_SPECS = {'lid.inner_face': {}, 'boss.top_face': {}}
DATUM_HEIGHTS_CM = {'lid_plane': '2.5'}
DIGEST = 'a1b2c3d4'
FH_ATTEMPT = 1


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    up = des.userParameters
    up.add('outer_w', adsk.core.ValueInput.createByString('60 mm'), 'mm', '')
    fh_ref('lid.inner_face', des.rootComponent.bRepBodies.item(0).faces.item(0))
    print('built')


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
