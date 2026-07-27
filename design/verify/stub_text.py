"""Canonical text of the verification stub appended to every generated script.

This is the single source of truth. `fusionhelper.verify` re-exports it as
`STUB_TEXT`; preflight appends it and lints against it; nothing else may hold a
copy, because a copy can drift and the drift is silent.

The text is BYTE-CONSTANT by design. Everything that varies between runs --
the attempt number, per-run options such as `only_params` -- is read from module
globals the compiler writes (`FH_ATTEMPT`, `FH_OPTS`), never edited into the stub
itself. That is what makes an exact-compare immutability check possible without
breaking the legitimate parameterisations the repair loop depends on.

Verified with pyright 1.1.408 against Autodesk's shipped stubs, using the
project's own config: 0 errors, 0 warnings.
"""

STUB_SENTINEL = '# fusionhelper: verification stub v1'

STUB_TEXT = """# fusionhelper: verification stub v1
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
"""


def append_to(script_text):
    """Append the stub to a generated script, normalising the seam."""
    return script_text.rstrip('\n') + '\n\n\n' + STUB_TEXT
