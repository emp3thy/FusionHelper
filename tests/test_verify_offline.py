"""Offline exercise of fh_verify's Fusion-independent logic, with adsk stubbed.

Runs anywhere Python runs -- no Fusion, no subscription, no document. Covers the
pure logic: unit conversion, change detection, message classification, dependency
analysis, perturbation sizing, reference multiplicity, the clearance/interference
coupling, and the output protocol.
"""
import sys, os, types, json, io, contextlib, importlib.util
from pathlib import Path

adsk = types.ModuleType('adsk')
core = types.ModuleType('adsk.core')
fusion = types.ModuleType('adsk.fusion')
adsk.core, adsk.fusion = core, fusion
adsk.doEvents = lambda: None
sys.modules['adsk'] = adsk
sys.modules['adsk.core'] = core
sys.modules['adsk.fusion'] = fusion

_VERIFY_DIR = Path(__file__).parents[1] / "fusionhelper" / "verify"
_fh_verify_path = _VERIFY_DIR / "fh_verify.py"
_spec = importlib.util.spec_from_file_location("fh_verify", _fh_verify_path)
V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V)

RESULTS = []


def ok(cond, msg):
    RESULTS.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + msg)


# ----------------------------------------------------------------- unit conversion
# Agent D's compiler emits decimal strings ALREADY IN CM. Getting this edge wrong is
# a silent 10x error in exactly the dimension the project exists to protect.
ok(V._cm_str_to_mm('0.08') == 0.8, "cm string '0.08' -> 0.8 mm")
ok(V._cm_str_to_mm('2.5') == 25.0, "cm string '2.5' -> 25 mm")
ok(V._cm_str_to_mm(0.08) == 0.8, "bare number treated as cm")
ok(V._cm_str_to_mm('  1.0  ') == 10.0, "whitespace tolerated")
ok(V._cm_str_to_mm('nonsense') is None, "junk rejected")
ok(V._cm_str_to_mm(None) is None, "None passes through")

ok(V._mm(1.0) == 10, "cm->mm integer collapse")
ok(V._mm3(3.2) == 3200, "cm3->mm3")
ok(V._n(2.50000001) == 2.5, "rounding")

# ----------------------------------------------------------------- change detection
ok(V._num_differs(1.0, 1.0000001) is True, "1e-7 detected")
ok(V._num_differs(1.0, 1.0 + 1e-12) is False, "float noise ignored")

a = {'b0': {'f': 12, 'v': 12.0, 'a': 30.0, 'bb': (0, 0, 0, 6, 4, .5)}}
b = {'b0': {'f': 12, 'v': 12.0, 'a': 30.0, 'bb': (0, 0, 0, 6, 4, .5)}}
ok(V._snapshot_differs(a, b) is False, "identical snapshot -> dead")
ok(V._snapshot_differs(a, {'b0': dict(b['b0'], v=12.0001)}) is True, "volume moved -> live")
ok(V._snapshot_differs(a, {'b0': dict(b['b0'], f=13)}) is True, "face count moved -> live")
ok(V._snapshot_differs(a, {}) is True, "body vanished -> live")

# ----------------------------------------------------------------- classifier
cases = [
    ('3 : Already has same dimension on referenced geometry!', 'sketch.redundant_dimension'),
    ('3 : failed to create offset: Constraint has already been applied to the selected sketch object.', 'sketch.redundant_constraint'),
    ('3 : failed to create offset: VCS_SKETCH_SOLVING_FAILED - Failed to solve.', 'sketch.conflicting_constraint'),
    ('2 : InternalValidationError : asmFace', 'ref.stale_brep'),
    ('2 : InternalValidationError : pFace', 'ref.stale_brep'),
    ('3 : invalid input collections', 'interference.insufficient_bodies'),
    ('The extrusion profile falls outside the boundary of the selected body. 2 Reference Failures', 'timeline.reference_failure'),
    ('3 : param name is not valid', 'param.invalid_name'),
    ('3 : invalid expression', 'param.invalid_expression'),
    ('something entirely new', None),
]
for msg, want in cases:
    ok(V.classify(msg) == want, "classify %r" % msg[:38])


# ----------------------------------------------------------------- dependency map
class P:
    def __init__(self, n, e, u='mm', v=1.0):
        self.name, self.expression, self.unit, self.value = n, e, u, v


params = [P('outer_w', '60 mm'), P('outer_h', '25 mm'),
          P('wall_t', 'outer_w / 20'), P('cavity_w', 'outer_w - 2 * wall_t'),
          P('rib_n', '4', '', 4.0)]
refby, roots = V._dependency_map(params)
ok(sorted(roots) == ['outer_h', 'outer_w', 'rib_n'], "roots = literal-only params")
ok(refby['outer_w'] == {'wall_t', 'cavity_w'}, "referenced_by outer_w")
ok(refby['cavity_w'] == set(), "cavity_w is a leaf")


# ----------------------------------------------------------------- perturbation step
class UM:
    internalUnits = 'cm'

    @staticmethod
    def convert(v, frm, to):
        return v * {'cm': 1.0, 'mm': 10.0, 'm': 0.01, 'in': 1 / 2.54}[to]


class D:
    unitsManager = UM


class DNoUM:
    unitsManager = None


d, dn = D(), DNoUM()
s, u = V._step_for(d, P('outer_w', '60 mm', 'mm', 6.0))     # 6 cm -> 5% = 0.3 cm = 3 mm
ok(u == 'mm' and float(s) == 3.0, "length step = 5%% clamped (%s %s)" % (s, u))
s, u = V._step_for(d, P('wall_t', '0.4 mm', 'mm', 0.04))    # tiny -> floor 0.02 cm
ok(float(s) == 0.2 and u == 'mm', "length floor applied (%s %s)" % (s, u))
s, u = V._step_for(d, P('big', '900 mm', 'mm', 90.0))       # huge -> cap 1.0 cm
ok(float(s) == 10.0 and u == 'mm', "length cap applied (%s %s)" % (s, u))
s, u = V._step_for(d, P('rib_n', '4', '', 4.0))
ok(s == '1' and u == '', "integer count steps by 1")
s, u = V._step_for(d, P('draft', '3 deg', 'deg', 0.0524))
ok(V.ANG_STEP_MIN_RAD <= float(s) <= V.ANG_STEP_MAX_RAD, "angle step in range (%s)" % s)
s, u = V._step_for(dn, P('outer_w', '60 mm', 'mm', 6.0))
ok(u == 'cm' and float(s) == 0.3, "no unitsManager -> internal units, labelled cm")

ok(V._perturbed_expr('outer_w / 20', '0.02', 'mm') == '(outer_w / 20) + 0.02 mm',
   "derived expression stays derived")
ok(V._perturbed_expr('4', '1', '') == '(4) + 1', "unitless expression")

# ----------------------------------------------------------------- literal dimensions
names = {'outer_w', 'wall_t'}


def is_literal(expr):
    toks = set(V._IDENT_RE.findall(expr))
    if toks & names:
        return False
    toks -= V._UNIT_TOKENS
    toks -= V._FUNC_TOKENS
    return not toks


ok(is_literal('60 mm') is True, "'60 mm' is literal")
ok(is_literal('outer_w') is False, "'outer_w' is bound")
ok(is_literal('outer_w * 2 + 1 mm') is False, "mixed is bound")
ok(is_literal('sqrt(2) * 10 mm') is True, "function of literals is literal")


# ----------------------------------------------------- reference resolution (Agent E)
# findEntityByToken returns a LIST; a face split by later features returns every
# piece. A blind [0] is silently wrong in exactly the case tokens exist to protect.
class FakeDes:
    def __init__(self, table):
        self.table = table

    def findEntityByToken(self, tok):
        v = self.table.get(tok)
        if isinstance(v, Exception):
            raise v
        return v


refs = {'lid.inner_face': 'TOK_A', 'boss.top_face': 'TOK_B', 'split.face': 'TOK_C'}
des = FakeDes({'TOK_A': ['faceA'], 'TOK_B': [], 'TOK_C': ['p0', 'p1', 'p2']})
ents, err = V._resolve_role(des, refs, 'lid.inner_face')
ok(ents == ['faceA'] and err is None, "single resolution")
ents, err = V._resolve_role(des, refs, 'boss.top_face')
ok(ents == [] and err == 'token_unresolved', "empty list -> token_unresolved")
ents, err = V._resolve_role(des, refs, 'split.face')
ok(len(ents) == 3 and err is None, "split face returns ALL pieces, not just [0]")
ents, err = V._resolve_role(des, refs, 'never_registered')
ok(err == 'not_registered', "unregistered role named")
ents, err = V._resolve_role(
    FakeDes({'TOK_A': RuntimeError('2 : InternalValidationError : pFace')}),
    {'r': 'TOK_A'}, 'r')
ok(err == 'stale_brep', "InternalValidationError mapped to stale_brep")


# --------------------------------------------- clearance / interference coupling
# measureMinimumDistance returns 0.00000 for BOTH touching and interpenetrating,
# so a zero must never be allowed to read as a pass.
class FakeCtx:
    def __init__(self, interference_ran=True, clash=()):
        self.interference_ran = interference_ran
        self.clash_bodies = set(clash)
        self.out = []

    def add(self, check, code, sev='error', **kw):
        self.out.append((check, code, sev, kw))


def judge(measured_mm, decl, interference_ran=True, clash=(), bodies=('Lid', 'Boss')):
    c = FakeCtx(interference_ran, clash)
    V._judge_clearance(c, decl, 'lid.inner_face', 'boss.top_face', measured_mm,
                       {'bodies': list(bodies)})
    return c.out


# 0 mm, and interference says these very bodies clash -> interpenetrating, error
r = judge(0.0, {'min': '0.08'}, clash=('Lid', 'Boss'))
ok(r and r[0][1] == 'clearance.zero' and r[0][2] == 'error',
   "zero + clash on same bodies -> clearance.zero error")
ok('interpenetrating' in r[0][3].get('note', ''), "note says interpenetrating")

# 0 mm, but interference never ran -> cannot distinguish, so error
r = judge(0.0, {'min': '0.08'}, interference_ran=False)
ok(r and r[0][1] == 'clearance.zero' and r[0][2] == 'error',
   "zero + interference skipped -> error (skip is not pass)")

# 0 mm, interference clean, but a gap was declared -> still a violation
r = judge(0.0, {'min': '0.08'})
ok(r and r[0][1] == 'clearance.violated' and r[0][2] == 'error',
   "zero where a gap was declared -> violation")

# 0 mm, interference clean, contact declared (min 0) -> warn, never pass
r = judge(0.0, {'min': '0'})
ok(r and r[0][1] == 'clearance.zero' and r[0][2] == 'warn',
   "declared contact -> warn, still not a pass")

# the P5 trap: min 0 on a fully embedded part must NOT come back clean
r = judge(0.0, {'min': '0'}, clash=('Lid', 'Boss'))
ok(r and r[0][2] == 'error', "min:0 on an embedded part is an error, not a pass")

# ordinary violation, ordinary pass, and a max bound
r = judge(0.31, {'min': '0.08'})
ok(r and r[0][1] == 'clearance.violated' and r[0][3]['short_by_mm'] == 0.49,
   "short_by_mm computed against a cm-declared minimum")
ok(judge(1.2, {'min': '0.08'}) == [], "comfortable clearance emits nothing")
r = judge(9.0, {'max': '0.5'})
ok(r and r[0][3]['over_by_mm'] == 4.0, "max violation reports over_by_mm")

# the canary reports the same conditions under a distinct edit. prefix
c = FakeCtx()
V._judge_clearance(c, {'min': '0.08'}, 'a', 'b', 0.2, {'bodies': ['Lid', 'Boss']},
                   check='liveness', prefix='edit.')
ok(c.out and c.out[0][0] == 'liveness' and c.out[0][1] == 'edit.clearance.violated',
   "post-edit clearance failure is distinguishable from a nominal one")

# ----------------------------------------------------------------- declaration shapes
ok(len(V._clearance_items({'clearances': [{'between': ['a', 'b'], 'min': '0.08'}]})) == 1,
   "clearances as a list")
ok(len(V._clearance_items({'clearances': {'gap1': {'between': ['a', 'b']}}})) == 1,
   "clearances as a dict")
ok(V._clearance_items({'clearances': None}) == [], "absent clearances")
ok(V._leaf('Component1:1/Lid') == 'Lid', "body leaf name for clash matching")

# ----------------------------------------------------------------- roll-up
mk = lambda **kw: types.SimpleNamespace(
    status=dict(dict((c, 'pass') for c in V.CHECKS), **kw))
ok(V._roll_up(mk()) == 'pass', "all pass")
ok(V._roll_up(mk(liveness='skip')) == 'pass_partial', "skip never reads as pass")
ok(V._roll_up(mk(constraints='warn')) == 'warn', "warn")
ok(V._roll_up(mk(constraints='warn', interference='fail')) == 'fail', "fail dominates")


# ----------------------------------------------------------------- output protocol
def fresh_ctx():
    c = V.Ctx.__new__(V.Ctx)
    c.findings = []
    c.status = dict((x, 'pass') for x in V.CHECKS)
    c.skips, c.counts, c.emitted = {}, {}, set()
    return c


c = fresh_ctx()
c.add('clearance', 'clearance.violated', 'error', between=['a', 'b'], short_by_mm=0.49)
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    c.emit_check('clearance')
    c.emit_check('clearance')      # must not double-print
out = buf.getvalue().strip()
ok(out.count(V.CHECK_PREFIX) == 1, "each check emits exactly once")
payload = json.loads(out[len(V.CHECK_PREFIX):])
ok(payload['c'] == 'clearance' and payload['s'] == 'fail', "check line carries status")
ok(payload['f'][0]['code'] == 'clearance.violated', "check line carries its findings")
ok('check' not in payload['f'][0], "finding does not repeat its own check name")

c = fresh_ctx()
for i in range(9):
    c.add('interference', 'interference.clash', 'error', pair=['A%d' % i, 'B'])
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    c.emit_check('interference')
payload = json.loads(buf.getvalue().strip()[len(V.CHECK_PREFIX):])
ok(len(payload['f']) == V.MAX_FINDINGS_PER_CHECK, "findings capped per check")
ok(payload['more'] == 9 - V.MAX_FINDINGS_PER_CHECK, "truncation counted, not hidden")

c = fresh_ctx()
c.skip('liveness', 'prior_failure')
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    c.emit_check('liveness')
payload = json.loads(buf.getvalue().strip()[len(V.CHECK_PREFIX):])
ok(payload['s'] == 'skip' and payload['why'] == 'prior_failure',
   "a skipped check states why, so it cannot be read as a pass")

# every error code the block can emit has a remediation hint
emitted_codes = {
    'sketch.unconstrained', 'param.dead', 'model.inert', 'model.not_restored',
    'param.restore_failed', 'interference.clash', 'clearance.violated',
    'clearance.zero', 'face.unresolved', 'face.ambiguous', 'datum.missing',
    'edit.introduces_clash', 'edit.clearance.violated', 'edit.clearance.zero',
    'ref.stale_brep', 'timeline.reference_failure',
}
missing = sorted(emitted_codes - set(V.HINTS))
ok(not missing, "every error code has a hint (missing: %s)" % missing)

# ------------------------------------------------- sweep invariant (interleaved form)
# The sweep restores parameter i and perturbs i+1 before a single settle. That is
# only safe if the restore is WRITTEN FIRST, so that at no instant is more than one
# parameter perturbed. These tests replay the write log and assert exactly that.
class LoggingParam:
    def __init__(self, log, name, expr, unit='mm', value=6.0):
        self._log, self.name, self._expr = log, name, expr
        self.unit, self.value, self.original = unit, value, expr

    @property
    def expression(self):
        return self._expr

    @expression.setter
    def expression(self, v):
        self._expr = v
        self._log.append((self.name, v))


class FakeBodies:
    def __iter__(self):
        return iter([])


class FakeRoot:
    bRepBodies = FakeBodies()
    allOccurrences = None       # attribute error inside a guarded block -> no bodies


class FakeDesign:
    rootComponent = FakeRoot()
    unitsManager = UM
    timeline = None


def perturbed_set(log, upto):
    """Replay the first `upto` writes and return the params not at their original."""
    state = {}
    for name, expr in log[:upto]:
        state[name] = expr
    return set(n for n, e in state.items() if e != originals[n])


settles = [0]
adsk.doEvents = lambda: settles.__setitem__(0, settles[0] + 1)

log = []
originals = {'p_a': '60 mm', 'p_b': '25 mm', 'p_c': '8 mm'}
sweep_params = [LoggingParam(log, n, e) for n, e in
                (('p_a', '60 mm'), ('p_b', '25 mm'), ('p_c', '8 mm'))]
fdes = FakeDesign()
ctx = fresh_ctx()
held = [None]
for prm in sweep_params:
    st = V._step_to(ctx, fdes, prm, held)
    ok(st is not None, "perturbation applied to %s" % prm.name)
V._release(fdes, held)

violations = [i for i in range(1, len(log) + 1) if len(perturbed_set(log, i)) > 1]
ok(not violations,
   "INVARIANT: never more than one parameter perturbed at once (violations at %s)" % violations)
ok(perturbed_set(log, len(log)) == set(),
   "every parameter ends at its original expression")
ok(settles[0] == len(sweep_params) + 1,
   "N+1 settles for N parameters, not 2N (got %d for %d params)" % (settles[0], len(sweep_params)))

# The restore of the previous parameter must precede the perturbation of the next.
order_ok = True
for i in range(1, len(sweep_params)):
    prev, cur = sweep_params[i - 1].name, sweep_params[i].name
    restore_at = max(j for j, (n, e) in enumerate(log) if n == prev and e == originals[prev])
    perturb_at = min(j for j, (n, e) in enumerate(log) if n == cur and e != originals[cur])
    if restore_at > perturb_at:
        order_ok = False
ok(order_ok, "restore of parameter i is written before the perturbation of i+1")

# A parameter whose expression cannot be written must not be left held, and must not
# be reported as dead -- it was never actually perturbed.
class RejectingParam(LoggingParam):
    @LoggingParam.expression.setter
    def expression(self, v):
        if v != self.original:
            raise RuntimeError('3 : invalid expression')
        self._expr = v
        self._log.append((self.name, v))


ctx2 = fresh_ctx()
held2 = [None]
rp = RejectingParam([], 'p_locked', '4 mm')
ok(V._step_to(ctx2, fdes, rp, held2) is None, "rejected perturbation returns None")
ok(held2[0] is None, "rejected perturbation leaves nothing held")
codes2 = [f['code'] for f in ctx2.findings]
ok('param.perturbation_rejected' in codes2 and 'param.dead' not in codes2,
   "a locked parameter is 'rejected', never 'dead'")

# _release must restore even when the caller aborted mid-measurement.
log3 = []
originals = {'p_x': '10 mm'}
px = LoggingParam(log3, 'p_x', '10 mm')
held3 = [None]
V._step_to(fresh_ctx(), fdes, px, held3)
ok(px.expression != '10 mm', "p_x is perturbed before the simulated abort")
V._release(fdes, held3)
ok(px.expression == '10 mm' and held3[0] is None,
   "_release restores the held parameter after an abort")

# ----------------------------------------------------------------- the stub contract
import ast
_stub_text_path = _VERIFY_DIR / "stub_text.py"
_stub_text_spec = importlib.util.spec_from_file_location("stub_text", _stub_text_path)
_stub_text = importlib.util.module_from_spec(_stub_text_spec)
_stub_text_spec.loader.exec_module(_stub_text)
STUB_TEXT, STUB_SENTINEL, append_to = (
    _stub_text.STUB_TEXT, _stub_text.STUB_SENTINEL, _stub_text.append_to)

ok(STUB_TEXT.splitlines()[0] == STUB_SENTINEL,
   "sentinel comment is the stub's first line (Agent B detects on this)")

sample = "import adsk.core\n\n\ndef run(_context: str):\n    print('built')\n"
tree = ast.parse(append_to(sample))
last = tree.body[-1]
ok(isinstance(last, ast.Assign), "last statement is an ast.Assign")
ok(len(last.targets) == 1 and isinstance(last.targets[0], ast.Name)
   and last.targets[0].id == 'run',
   "sole target is Name('run') -- matches Agent B's lint rule exactly")

# Anything after the rebinding wins, and verification silently never runs.
tampered = ast.parse(append_to(sample) + "\ndef run(_context: str):\n    pass\n")
ok(not isinstance(tampered.body[-1], ast.Assign),
   "a later `def run` moves body[-1] off the Assign, so the rule catches it")

ok(append_to(sample).endswith(STUB_TEXT),
   "append_to emits STUB_TEXT verbatim -- no second copy to drift")
ok('attempt=1' not in STUB_TEXT and "g.get('FH_ATTEMPT', 1)" in STUB_TEXT,
   "the attempt number is read from globals, so the stub stays byte-constant")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'fixtures', 'verify', 'stub_example.py'), encoding='utf-8') as f:
    ok(f.read().endswith(STUB_TEXT),
       "the committed stub_example.py has not drifted from STUB_TEXT")

# ----------------------------------------------------------------- cost of the protocol
passing_lines = [
    V.CHECK_PREFIX + json.dumps({'c': c_, 's': 'pass'}, separators=(',', ':'))
    for c_ in ('constraints', 'timeline', 'interference', 'clearance')
] + [
    V.GUARD_PREFIX + json.dumps({'restore': {'outer_w': '60 mm', 'outer_h': '25 mm',
                                             'wall_t': 'outer_w / 20', 'plate_t': '5 mm',
                                             'boss_h': 'outer_h / 4', 'rib_n': '4'}},
                                separators=(',', ':')),
    V.CHECK_PREFIX + json.dumps({'c': 'liveness', 's': 'pass'}, separators=(',', ':')),
    V.GUARD_PREFIX + '{"restore":"released"}',
    V.VERDICT_PREFIX + json.dumps(
        {'v': 1, 'status': 'pass', 'attempt': 1, 'units': 'mm',
         'checks': dict((c_, 'pass') for c_ in V.CHECKS),
         'model': {'bodies': 3, 'volume_mm3': 18240, 'bbox_mm': [60, 40, 25],
                   'origin_mm': [0, 0, 0]},
         'stats': {'timeline': 11, 'params': 6, 'sec': 3.4}, 'decl': 'a1b2c3d4'},
        separators=(',', ':')),
]
total = sum(len(x) + 1 for x in passing_lines)
print("\npassing run: %d lines, %d chars ~= %d tokens" % (len(passing_lines), total, total // 4))
for x in passing_lines:
    print("  " + x)

print("\n%d assertions, %d failures" % (len(RESULTS), RESULTS.count(False)))

if __name__ == "__main__":
    sys.exit(1 if RESULTS.count(False) else 0)


def test_all_offline_assertions_passed():
    """The ok() calls above already ran as a side effect of importing this
    module and populated RESULTS; pytest needs one real assertion to turn
    that outcome into a pass/fail. Failing ok() lines print to stdout, which
    pytest captures and shows on failure.
    """
    assert RESULTS.count(False) == 0, (
        "%d of %d offline fh_verify checks failed (see captured stdout for "
        "the FAIL lines)" % (RESULTS.count(False), len(RESULTS))
    )
