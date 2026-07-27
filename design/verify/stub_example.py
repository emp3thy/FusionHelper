import adsk.core, adsk.fusion

FH_REFS = {}


def fh_ref(role: str, entity):
    """Register a role -> entityToken at authoring time, for the verification block."""
    FH_REFS[role] = entity.entityToken
    return entity


CLEARANCES = [{'between': ['lid.inner_face', 'boss.top_face'], 'min': '0.08'}]
FACE_SPECS = {'lid.inner_face': {}, 'boss.top_face': {}}
DATUM_HEIGHTS_CM = {'lid_plane': '2.5'}
DIGEST = 'a1b2c3d4'


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    up = des.userParameters
    up.add('outer_w', adsk.core.ValueInput.createByString('60 mm'), 'mm', '')
    print('built')


# --- FusionHelper verification block (generated; do not edit) ----------------------
def _fh_run_verify(attempt: int = 1):
    import os, json, traceback
    home = os.environ.get('FUSIONHELPER_HOME') or os.path.join(
        os.environ.get('LOCALAPPDATA', ''), 'FusionHelper')
    def bail(code, msg):
        return 'FH_VERDICT1 ' + json.dumps(
            {'v': 1, 'status': 'error', 'code': code, 'msg': msg, 'home': home},
            separators=(',', ':'))
    try:
        with open(os.path.join(home, 'fh_verify.py'), encoding='utf-8') as f:
            src = f.read()
    except Exception as e:
        return bail('verify.block_missing', str(e))
    ns: dict = {'__name__': 'fh_verify'}   # annotated: else pyright infers dict[str,str]
    try:
        exec(compile(src, 'fh_verify.py', 'exec'), ns)
        return ns['fh_verify'](
            clearances=globals().get('CLEARANCES'),
            face_specs=globals().get('FACE_SPECS'),
            datum_heights_cm=globals().get('DATUM_HEIGHTS_CM'),
            digest=globals().get('DIGEST'),
            refs=globals().get('FH_REFS', {}),
            attempt=attempt)
    except Exception:
        return bail('verify.internal', traceback.format_exc()[-600:])


def _fh_wrapped_run(_context: str):
    _fh_user_run(_context)          # never wrapped in try: build exceptions must escape
    print(_fh_run_verify(attempt=1))


_fh_user_run = run
globals()['run'] = _fh_wrapped_run     # rebind, not redefine: `def run` twice trips reportRedeclaration
