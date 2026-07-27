"""Offline exercise of fh_verify's Fusion-independent logic, with adsk stubbed."""
import sys, types, json

adsk = types.ModuleType('adsk')
core = types.ModuleType('adsk.core')
fusion = types.ModuleType('adsk.fusion')
adsk.core, adsk.fusion = core, fusion
adsk.doEvents = lambda: None
sys.modules['adsk'] = adsk
sys.modules['adsk.core'] = core
sys.modules['adsk.fusion'] = fusion

import fh_verify as V

ok = lambda c, m: print(("PASS " if c else "FAIL ") + m)

# unit parsing
ok(V._parse_len_mm('0.8 mm') == 0.8, "parse '0.8 mm'")
ok(V._parse_len_mm('1 cm') == 10.0, "parse '1 cm'")
ok(V._parse_len_mm(0.5) == 0.5, "bare number -> mm")
ok(V._parse_len_mm('0.25in') == 6.35, "parse inches")
ok(V._parse_len_mm('nonsense') is None, "reject junk")

# unit conversion / rounding
ok(V._mm(1.0) == 10, "cm->mm integer collapse")
ok(V._mm3(3.2) == 3200, "cm3->mm3")
ok(V._n(2.50000001) == 2.5, "rounding")

# change detection
ok(V._num_differs(1.0, 1.0000001) is True, "1e-7 detected")
ok(V._num_differs(1.0, 1.0 + 1e-12) is False, "float noise ignored")

a = {'b0': {'f': 12, 'v': 12.0, 'a': 30.0, 'bb': (0, 0, 0, 6, 4, .5)}}
b = {'b0': {'f': 12, 'v': 12.0, 'a': 30.0, 'bb': (0, 0, 0, 6, 4, .5)}}
ok(V._snapshot_differs(a, b) is False, "identical snapshot -> dead")
b2 = {'b0': dict(b['b0'], v=12.0001)}
ok(V._snapshot_differs(a, b2) is True, "volume moved -> live")
b3 = {'b0': dict(b['b0'], f=13)}
ok(V._snapshot_differs(a, b3) is True, "face count moved -> live")
ok(V._snapshot_differs(a, {}) is True, "body vanished -> live")

# message classifier, against the verbatim probe strings
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

# dependency map / root detection
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

# step sizing (unitsManager absent -> falls back to internal units)
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
s, u = V._step_for(d, P('outer_w', '60 mm', 'mm', 6.0))   # 6 cm -> 5% = 0.3 cm = 3 mm
ok(u == 'mm' and float(s) == 3.0, "length step = 5%% clamped (%s %s)" % (s, u))
s, u = V._step_for(d, P('wall_t', '0.4 mm', 'mm', 0.04))  # tiny -> floor 0.02 cm = 0.2 mm
ok(float(s) == 0.2 and u == 'mm', "length floor applied (%s %s)" % (s, u))
s, u = V._step_for(d, P('big', '900 mm', 'mm', 90.0))     # huge -> cap 1.0 cm = 10 mm
ok(float(s) == 10.0 and u == 'mm', "length cap applied (%s %s)" % (s, u))
s, u = V._step_for(dn, P('outer_w', '60 mm', 'mm', 6.0))
ok(u == 'cm' and float(s) == 0.3, "no unitsManager -> internal units, correctly labelled (%s %s)" % (s, u))
s, u = V._step_for(d, P('rib_n', '4', '', 4.0))
ok(s == '1' and u == '', "integer count steps by 1")
s, u = V._step_for(d, P('draft', '3 deg', 'deg', 0.0524))
ok(V.ANG_STEP_MIN_RAD <= float(s) <= V.ANG_STEP_MAX_RAD, "angle step in range (%s)" % s)

# perturbed expression preserves the derivation
ok(V._perturbed_expr('outer_w / 20', '0.02', 'mm') == '(outer_w / 20) + 0.02 mm',
   "derived expression stays derived")
ok(V._perturbed_expr('4', '1', '') == '(4) + 1', "unitless expression")

# literal-vs-parametric dimension expression detection
names = {'outer_w', 'wall_t'}
def is_literal(expr):
    toks = set(V._IDENT_RE.findall(expr))
    if toks & names: return False
    toks -= V._UNIT_TOKENS; toks -= V._FUNC_TOKENS
    return not toks
ok(is_literal('60 mm') is True, "'60 mm' is literal")
ok(is_literal('outer_w') is False, "'outer_w' is bound")
ok(is_literal('outer_w * 2 + 1 mm') is False, "mixed is bound")
ok(is_literal('sqrt(2) * 10 mm') is True, "function of literals is literal")

# verdict roll-up
class FakeCtx:
    def __init__(self, st): self.status = st
mk = lambda **kw: FakeCtx(dict({c: 'pass' for c in V.CHECKS}, **kw))
ok(V._roll_up(mk()) == 'pass', "all pass")
ok(V._roll_up(mk(liveness='skip')) == 'pass_partial', "skip never reads as pass")
ok(V._roll_up(mk(constraints='warn')) == 'warn', "warn")
ok(V._roll_up(mk(constraints='warn', interference='fail')) == 'fail', "fail dominates")

# verdict size, passing case
passing = {'v':1,'status':'pass','attempt':1,'units':'mm',
  'checks':{'constraints':'pass','liveness':'pass','timeline':'pass',
            'interference':'pass','clearance':'skip'},
  'model':{'bodies':3,'volume_mm3':18240,'bbox_mm':[60,40,25],'origin_mm':[0,0,0]},
  'stats':{'timeline':11,'params':6,'sec':3.4},
  'skipped':{'clearance':'none_declared'}}
s = V.VERDICT_PREFIX + json.dumps(passing, separators=(',',':'))
print("passing verdict: %d chars ~= %d tokens" % (len(s), len(s)//4))
print(s)
