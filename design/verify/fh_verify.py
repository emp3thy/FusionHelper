# fh_verify.py --- FusionHelper verification block, contract v1
#
# Installed by the fusionhelper package to %LOCALAPPDATA%\FusionHelper\fh_verify.py.
# NEVER pasted into a generated script: generated scripts carry a ~16-line stub that
# exec()s this file at run time. fusion_mcp_execute takes the script as a *string*, so
# every byte of an inlined block would cost Claude context on every repair attempt.
#
# Entry points:
#   fh_verify(decl_path=None, decl=None, refs=None, attempt=1, **opts) -> str
#       one-line JSON verdict, prefixed 'FH_VERDICT1 '
#   fh_state() -> str
#       cheap state probe (timeline count + health only). Used after a raw build
#       exception and to drive undo-to-depth. No rebuilds.

import adsk.core
import adsk.fusion
import json
import math
import os
import re
import time
import traceback

FH_CONTRACT = 1
VERDICT_PREFIX = 'FH_VERDICT1 '

# Change detection thresholds, in internal units (cm / cm2 / cm3).
# A genuinely dead parameter reproduces byte-identical metrics (probe: volume equal to
# four decimal places, all 12 faces unchanged), while a live one moves by percent-scale.
# The margin between signal and noise is ~6 orders of magnitude, so these are not delicate.
ABS_TOL = 1e-7
REL_TOL = 1e-9

# Perturbation sizing, internal units.
LEN_STEP_FRAC = 0.05
LEN_STEP_MIN_CM = 0.02          # 0.2 mm
LEN_STEP_MAX_CM = 1.0           # 10 mm
ANG_STEP_MIN_RAD = 0.0175       # 1 deg
ANG_STEP_MAX_RAD = 0.0873       # 5 deg

MAX_FINDINGS_PER_CHECK = 5
MAX_FINDINGS_TOTAL = 12
MSG_CLIP = 180

CHECKS = ('constraints', 'liveness', 'timeline', 'interference', 'clearance')

# Tokens that appear in a dimension expression without making it parametric.
_UNIT_TOKENS = {'mm', 'cm', 'm', 'um', 'nm', 'in', 'ft', 'yd', 'mil', 'thou',
                'deg', 'rad', 'grad', 'r', 'e', 'pi', 'PI'}
_FUNC_TOKENS = {'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sqrt', 'abs',
                'ln', 'log', 'exp', 'pow', 'min', 'max', 'round', 'floor', 'ceil'}
_IDENT_RE = re.compile(r'[A-Za-z_][A-Za-z_0-9]*')

# In-block message classifier. Only patterns verified verbatim against a live install
# are matched to a specific code; anything else falls through to a generic code and is
# classified host-side by the skill's taxonomy, which holds the remediation text.
_MSG_CODES = (
    (re.compile(r'Already has same dimension', re.I), 'sketch.redundant_dimension'),
    (re.compile(r'Constraint has already been applied', re.I), 'sketch.redundant_constraint'),
    (re.compile(r'VCS_SKETCH_SOLVING_FAILED', re.I), 'sketch.conflicting_constraint'),
    (re.compile(r'InternalValidationError', re.I), 'ref.stale_brep'),
    (re.compile(r'invalid input collections', re.I), 'interference.insufficient_bodies'),
    (re.compile(r'Reference Failure', re.I), 'timeline.reference_failure'),
    (re.compile(r'falls outside the boundary', re.I), 'timeline.reference_failure'),
    (re.compile(r'param name is not valid', re.I), 'param.invalid_name'),
    (re.compile(r'invalid expression', re.I), 'param.invalid_expression'),
)


def classify(msg):
    if not msg:
        return None
    for rx, code in _MSG_CODES:
        if rx.search(msg):
            return code
    return None


# --------------------------------------------------------------------------- helpers

def _n(x, p=4):
    """Round and integer-collapse, so the JSON stays short."""
    if x is None:
        return None
    try:
        v = round(float(x), p)
    except Exception:
        return None
    if v != v or v in (float('inf'), float('-inf')):
        return None
    return int(v) if v == int(v) and abs(v) < 1e15 else v


def _mm(cm, p=3):
    return _n(None if cm is None else cm * 10.0, p)


def _mm2(cm2, p=2):
    return _n(None if cm2 is None else cm2 * 100.0, p)


def _mm3(cm3, p=2):
    return _n(None if cm3 is None else cm3 * 1000.0, p)


def _clip(s, n=MSG_CLIP):
    if not s:
        return None
    s = ' '.join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + '…'


def _short_type(entity):
    try:
        return entity.objectType.split('::')[-1]
    except Exception:
        return None


def _num_differs(a, b):
    if a is None or b is None:
        return a is not b
    d = abs(a - b)
    return d > ABS_TOL and d > REL_TOL * max(abs(a), abs(b), 1.0)


# --------------------------------------------------------------------- model snapshot

def _all_bodies(des):
    """(key, body) for every BRepBody in the design, occurrence proxies included."""
    out = []
    root = des.rootComponent
    for b in root.bRepBodies:
        out.append((b.name, b))
    try:
        occs = root.allOccurrences
        for i in range(occs.count):
            occ = occs.item(i)
            for b in occ.bRepBodies:
                out.append((occ.fullPathName + '/' + b.name, b))
    except Exception:
        pass
    return out


def _body_metrics(b):
    m = {'f': None, 'v': None, 'a': None, 'bb': None}
    try:
        m['f'] = b.faces.count
    except Exception:
        pass
    for attr, key in (('volume', 'v'), ('area', 'a')):
        try:
            m[key] = getattr(b, attr)
        except Exception:
            try:
                m[key] = getattr(b.physicalProperties, attr)
            except Exception:
                pass
    try:
        bb = b.boundingBox
        m['bb'] = (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                   bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)
    except Exception:
        pass
    return m


def _snapshot(des):
    snap = {}
    for i, (key, b) in enumerate(_all_bodies(des)):
        snap['%d|%s' % (i, key)] = _body_metrics(b)
    return snap


def _snapshot_differs(a, b):
    """True if any measurable geometric quantity moved."""
    if set(a.keys()) != set(b.keys()):
        return True
    for k in a:
        ma, mb = a[k], b[k]
        if ma['f'] != mb['f']:
            return True
        if _num_differs(ma['v'], mb['v']) or _num_differs(ma['a'], mb['a']):
            return True
        if (ma['bb'] is None) != (mb['bb'] is None):
            return True
        if ma['bb'] is not None:
            for i in range(6):
                if _num_differs(ma['bb'][i], mb['bb'][i]):
                    return True
    return False


def _model_summary(snap):
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    vol = 0.0
    for m in snap.values():
        if m['v']:
            vol += m['v']
        if m['bb']:
            for i in range(3):
                lo[i] = min(lo[i], m['bb'][i])
                hi[i] = max(hi[i], m['bb'][i + 3])
    out = {'bodies': len(snap), 'volume_mm3': _mm3(vol)}
    if lo[0] != math.inf:
        out['bbox_mm'] = [_mm(hi[i] - lo[i]) for i in range(3)]
        out['origin_mm'] = [_mm(lo[i]) for i in range(3)]
    return out


# --------------------------------------------------------------------------- context

class Ctx(object):
    def __init__(self, decl, refs, opts):
        self.app = adsk.core.Application.get()
        self.des = adsk.fusion.Design.cast(self.app.activeProduct)
        self.decl = decl or {}
        self.refs = refs or {}
        self.opts = opts or {}
        self.findings = []
        self.status = {}          # check -> pass | warn | fail | skip
        self.skips = {}           # check -> reason
        self.counts = {}          # check -> findings emitted (for truncation)
        self.t0 = time.time()
        for c in CHECKS:
            self.status[c] = 'pass'

    def skip(self, check, reason):
        self.status[check] = 'skip'
        self.skips[check] = reason

    def add(self, check, code, sev='error', **kw):
        n = self.counts.get(check, 0)
        self.counts[check] = n + 1
        if self.status[check] != 'fail':
            self.status[check] = 'fail' if sev == 'error' else 'warn'
        if n >= MAX_FINDINGS_PER_CHECK or len(self.findings) >= MAX_FINDINGS_TOTAL:
            return
        f = {'check': check, 'code': code, 'sev': sev}
        for k, v in kw.items():
            if v is not None and v != [] and v != {}:
                f[k] = v
        self.findings.append(f)

    def failed(self):
        return any(v == 'fail' for v in self.status.values())


# ------------------------------------------------------------------- check: constraints

def check_constraints(ctx):
    des = ctx.des
    try:
        param_names = set(p.name for p in _user_params(des))
    except Exception:
        param_names = set()

    comps = []
    try:
        for c in des.allComponents:
            comps.append(c)
    except Exception:
        comps = [des.rootComponent]

    for comp in comps:
        for sk in comp.sketches:
            name = comp.name + '/' + sk.name
            _check_dimension_bindings(ctx, sk, name, param_names)
            try:
                full = sk.isFullyConstrained
            except Exception:
                continue
            if full:
                continue
            gc = _count(sk.geometricConstraints)
            dc = _count(sk.sketchDimensions)
            loose = _loose_entities(sk)
            # A sketch with no constraints and no dimensions at all is the
            # raw-coordinate signature: hard error. A partially constrained sketch
            # is a risk indicator, not a build failure (a model can rebuild
            # correctly with one), so it warns.
            if gc == 0 and dc == 0:
                ctx.add('constraints', 'sketch.unconstrained', 'error',
                        sketch=name, entities=len(loose), loose=loose[:4])
            else:
                ctx.add('constraints', 'sketch.under_constrained', 'warn',
                        sketch=name, constraints=gc, dims=dc,
                        entities=len(loose), loose=loose[:4])


def _count(coll):
    try:
        return coll.count
    except Exception:
        return 0


def _loose_entities(sk):
    out = []
    try:
        curves = sk.sketchCurves
        for i in range(curves.count):
            e = curves.item(i)
            try:
                if e.isFullyConstrained:
                    continue
            except Exception:
                continue
            out.append(_entity_desc(i, e))
    except Exception:
        pass
    try:
        pts = sk.sketchPoints
        for i in range(pts.count):
            p = pts.item(i)
            try:
                if p.isFullyConstrained:
                    continue
                g = p.geometry
                if abs(g.x) < 1e-9 and abs(g.y) < 1e-9:
                    continue          # sketch origin
            except Exception:
                continue
            out.append({'i': i, 't': 'SketchPoint',
                        'at': [_mm(g.x), _mm(g.y)]})
    except Exception:
        pass
    return out


def _entity_desc(idx, e):
    t = _short_type(e)
    d = {'i': idx, 't': t}
    try:
        if t == 'SketchLine':
            a, b = e.startSketchPoint.geometry, e.endSketchPoint.geometry
            d['from'] = [_mm(a.x), _mm(a.y)]
            d['to'] = [_mm(b.x), _mm(b.y)]
            d['len_mm'] = _mm(e.length)
        elif t in ('SketchCircle', 'SketchArc'):
            c = e.centerSketchPoint.geometry
            d['c'] = [_mm(c.x), _mm(c.y)]
            d['r_mm'] = _mm(e.radius)
        else:
            bb = e.boundingBox
            d['bb_mm'] = [_mm(bb.minPoint.x), _mm(bb.minPoint.y),
                          _mm(bb.maxPoint.x), _mm(bb.maxPoint.y)]
    except Exception:
        pass
    return d


def _check_dimension_bindings(ctx, sk, name, param_names):
    """A dimension whose expression names no user parameter is a literal.

    Static half of the partially-bound trap: free, no rebuild. The liveness check
    is still required, because a bound dimension does not prove the profile is
    positioned parametrically.
    """
    try:
        dims = sk.sketchDimensions
    except Exception:
        return
    for i in range(_count(dims)):
        try:
            expr = dims.item(i).parameter.expression
        except Exception:
            continue
        toks = set(_IDENT_RE.findall(expr or ''))
        if toks & param_names:
            continue
        toks -= _UNIT_TOKENS
        toks -= _FUNC_TOKENS
        if toks:
            continue          # references something we cannot see; do not cry wolf
        ctx.add('constraints', 'dimension.literal_expression', 'warn',
                sketch=name, dim=i, expr=_clip(expr, 40))


# ---------------------------------------------------------------------- check: timeline

_HEALTH = {0: 'healthy', 1: 'warning', 2: 'error', 3: 'suppressed'}


def _timeline_problems(des, limit=8):
    out = []
    try:
        tl = des.timeline
    except Exception:
        return out
    for i in range(tl.count):
        try:
            o = tl.item(i)
            hs = o.healthState
        except Exception:
            continue
        if hs == 0:
            continue
        rec = {'i': i, 'state': _HEALTH.get(hs, hs)}
        try:
            rec['name'] = o.name
        except Exception:
            pass
        try:
            rec['type'] = _short_type(o.entity)
        except Exception:
            pass
        try:
            rec['msg'] = _clip(o.errorOrWarningMessage)
        except Exception:
            pass
        code = classify(rec.get('msg'))
        if code:
            rec['code'] = code
        out.append(rec)
        if len(out) >= limit:
            break
    return out


def check_timeline(ctx):
    des = ctx.des
    try:
        if des.designType != adsk.fusion.DesignTypes.ParametricDesignType:
            ctx.skip('timeline', 'direct_design_no_timeline')
            return
    except Exception:
        pass
    for rec in _timeline_problems(des):
        sev = 'error' if rec['state'] == 'error' else 'warn'
        ctx.add('timeline', rec.pop('code', 'timeline.unhealthy'), sev, **rec)


# ------------------------------------------------------------------ check: interference

def _pair_key(a, b):
    return '|'.join(sorted([a or '', b or '']))


def check_interference(ctx):
    des = ctx.des
    bodies = [b for _, b in _all_bodies(des) if _is_solid(b)]
    if len(bodies) < 2:
        ctx.skip('interference', 'fewer_than_two_bodies')
        return
    cap = int(ctx.opts.get('max_bodies', 60))
    if len(bodies) > cap:
        ctx.skip('interference', 'too_many_bodies_%d' % len(bodies))
        return
    allowed = set()
    for pair in (ctx.decl.get('interference_allowed') or []):
        try:
            allowed.add(_pair_key(pair[0], pair[1]))
        except Exception:
            pass

    res = _analyze(des, bodies)
    if res is None:
        ctx.skip('interference', 'analyze_returned_none')
        return
    exempt = 0
    for i in range(res.count):
        r = res.item(i)
        n1 = _name_of(r.entityOne)
        n2 = _name_of(r.entityTwo)
        if _pair_key(n1, n2) in allowed:
            exempt += 1
            continue
        rec = {'pair': [n1, n2]}
        try:
            ib = r.interferenceBody
            rec['vol_mm3'] = _mm3(ib.volume)
            bb = ib.boundingBox
            rec['at_mm'] = [_mm((bb.minPoint.x + bb.maxPoint.x) / 2.0),
                            _mm((bb.minPoint.y + bb.maxPoint.y) / 2.0),
                            _mm((bb.minPoint.z + bb.maxPoint.z) / 2.0)]
            rec['size_mm'] = [_mm(bb.maxPoint.x - bb.minPoint.x),
                              _mm(bb.maxPoint.y - bb.minPoint.y),
                              _mm(bb.maxPoint.z - bb.minPoint.z)]
        except Exception:
            pass
        ctx.add('interference', 'interference.clash', 'error', **rec)
    if exempt:
        ctx.opts['_exempt_clashes'] = exempt


def _is_solid(b):
    try:
        return b.isSolid
    except Exception:
        return True


def _name_of(entity):
    for attr in ('fullPathName', 'name'):
        try:
            v = getattr(entity, attr)
            if v:
                return v
        except Exception:
            pass
    return _short_type(entity)


def _analyze(des, bodies):
    coll = adsk.core.ObjectCollection.create()
    for b in bodies:
        coll.add(b)
    ii = des.createInterferenceInput(coll)
    ii.areCoincidentFacesIncluded = False       # else a seated bracket reads as a clash
    return des.analyzeInterference(ii)


def _clash_count(des):
    """Cheap yes/no used by the edit canary. Returns -1 when not analysable."""
    bodies = [b for _, b in _all_bodies(des) if _is_solid(b)]
    if len(bodies) < 2:
        return -1
    try:
        res = _analyze(des, bodies)
        return res.count if res else 0
    except Exception:
        return -1


# -------------------------------------------------------------------- check: clearance

_LEN_UNITS = {'mm': 1.0, 'cm': 10.0, 'm': 1000.0, 'in': 25.4, 'ft': 304.8}


def _parse_len_mm(v):
    """Declaration lengths arrive as '0.8 mm' or as a bare number meaning mm."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.match(r'\s*([-+0-9.eE]+)\s*([a-zA-Z]*)\s*$', str(v))
    if not m:
        return None
    try:
        val = float(m.group(1))
    except Exception:
        return None
    return val * _LEN_UNITS.get(m.group(2) or 'mm', 1.0)


def _resolve_role(des, refs, role):
    tok = refs.get(role)
    if not tok:
        return None, 'not_registered'
    try:
        found = des.findEntityByToken(tok)
    except Exception as e:
        return None, _clip(str(e), 80)
    if not found:
        return None, 'token_unresolved'
    try:
        return (found[0] if len(found) else None), None
    except TypeError:
        return found, None


def check_clearance(ctx):
    decls = ctx.decl.get('clearances') or []
    if not decls:
        ctx.skip('clearance', 'none_declared')
        return
    des, refs = ctx.des, ctx.refs
    available = sorted(refs.keys())
    for c in decls:
        try:
            a_role, b_role = c['between'][0], c['between'][1]
        except Exception:
            ctx.add('clearance', 'clearance.malformed', 'error', decl=_clip(str(c), 80))
            continue
        ea, err_a = _resolve_role(des, refs, a_role)
        eb, err_b = _resolve_role(des, refs, b_role)
        if ea is None or eb is None:
            ctx.add('clearance', 'ref.unresolved', 'error',
                    role=(a_role if ea is None else b_role),
                    reason=(err_a if ea is None else err_b),
                    registered=available[:8])
            continue
        try:
            dist_mm = _mm(ctx.app.measureManager.measureMinimumDistance(ea, eb).value)
        except Exception as e:
            ctx.add('clearance', 'clearance.measure_failed', 'error',
                    between=[a_role, b_role], msg=_clip(str(e), 120))
            continue
        lo = _parse_len_mm(c.get('min'))
        hi = _parse_len_mm(c.get('max'))
        if lo is not None and dist_mm < lo - 1e-6:
            ctx.add('clearance', 'clearance.violated', 'error',
                    between=[a_role, b_role], min_mm=_n(lo),
                    measured_mm=dist_mm, short_by_mm=_n(lo - dist_mm))
        elif hi is not None and dist_mm > hi + 1e-6:
            ctx.add('clearance', 'clearance.exceeded', 'error',
                    between=[a_role, b_role], max_mm=_n(hi),
                    measured_mm=dist_mm, over_by_mm=_n(dist_mm - hi))


# --------------------------------------------------------------------- check: liveness

def _user_params(des):
    out = []
    ups = des.userParameters
    for i in range(ups.count):
        out.append(ups.item(i))
    return out


def _is_angle(unit):
    return (unit or '').strip() in ('deg', 'rad', 'degree', 'radian')


def _step_for(des, p):
    """Perturbation step, returned as an expression fragment in the parameter's unit.

    Sized in internal units so it is unit-agnostic, then converted. Floors keep it
    above solver noise; caps keep it small enough that a healthy model does not
    develop reference failures purely because we poked it.
    """
    unit = (p.unit or '').strip()
    v = abs(p.value or 0.0)
    if _is_angle(unit):
        step_internal = min(max(v * LEN_STEP_FRAC, ANG_STEP_MIN_RAD), ANG_STEP_MAX_RAD)
    elif unit == '':
        # Unitless. Integer-valued parameters drive counts (patterns, teeth) and must
        # stay integral, so step by exactly 1.
        if abs(p.value - round(p.value)) < 1e-9:
            return '1', ''
        return '0.1', ''
    else:
        step_internal = min(max(v * LEN_STEP_FRAC, LEN_STEP_MIN_CM), LEN_STEP_MAX_CM)
    try:
        um = des.unitsManager
        step = um.convert(step_internal, um.internalUnits, unit)
    except Exception:
        # Conversion unavailable: emit the step in internal units rather than
        # mislabelling a centimetre figure as the parameter's unit.
        return repr(round(step_internal, 6)), ('rad' if _is_angle(unit) else 'cm')
    return repr(round(step, 6)), unit


def _perturbed_expr(orig, step_txt, unit):
    return '(%s) + %s%s' % (orig, step_txt, (' ' + unit) if unit else '')


def _settle(des):
    adsk.doEvents()
    if _STRICT_RECOMPUTE:
        try:
            des.computeAll()
        except Exception:
            pass


_STRICT_RECOMPUTE = False       # see notes: computeAll() is not verified as required


def _dependency_map(params):
    """name -> set(names referencing it). Used to order the sample and to pick roots."""
    names = set(p.name for p in params)
    referenced_by = dict((n, set()) for n in names)
    roots = []
    for p in params:
        toks = set(_IDENT_RE.findall(p.expression or '')) & names
        toks.discard(p.name)
        if not toks:
            roots.append(p.name)
        for t in toks:
            referenced_by[t].add(p.name)
    return referenced_by, roots


def check_liveness(ctx):
    des = ctx.des
    if ctx.opts.get('liveness') is False:
        ctx.skip('liveness', 'disabled')
        return
    if ctx.failed() and not ctx.opts.get('force_liveness'):
        # The model is already known wrong. Spending 2N rebuilds proving it is also
        # dead buys nothing; fix the known failure and re-verify.
        ctx.skip('liveness', 'prior_failure')
        return
    try:
        params = _user_params(des)
    except Exception as e:
        ctx.skip('liveness', 'no_user_parameters: ' + _clip(str(e), 60))
        return
    expected = ctx.decl.get('parameters') or {}
    params = [p for p in params
              if not _decl_flag(expected, p.name, 'expect_live') is False]
    only = ctx.opts.get('only_params')
    if only:
        params = [p for p in params if p.name in set(only)]
    if not params:
        ctx.skip('liveness', 'no_parameters_to_test')
        return

    base = _snapshot(des)
    saved = dict((p.name, p.expression) for p in params)
    referenced_by, roots = _dependency_map(params)
    sick0 = _unhealthy_keys(des)
    detail = {}

    try:
        if ctx.opts.get('canary', True) and len(params) > 1:
            _edit_canary(ctx, des, params, roots, base, detail)

        order = sorted(params, key=lambda p: (len(referenced_by.get(p.name, ())), p.name))
        budget = float(ctx.opts.get('liveness_budget_s', 20.0))
        tested, untested = [], []
        t_start = time.time()
        per = None
        for idx, p in enumerate(order):
            if per is not None:
                projected = per * (len(order) - idx)
                if (time.time() - t_start) + projected > budget:
                    untested = [q.name for q in order[idx:]]
                    break
            t_p = time.time()
            _test_one(ctx, des, p, base, sick0)
            per = max(time.time() - t_p, 1e-6) if per is None else max(per, time.time() - t_p)
            tested.append(p.name)
        detail['tested'] = len(tested)
        detail['of'] = len(order)
        if untested:
            detail['mode'] = 'sampled'
            detail['untested'] = untested[:12]
            ctx.add('liveness', 'liveness.budget_exhausted', 'warn',
                    tested=len(tested), of=len(order), untested=untested[:12])
    finally:
        _restore_all(ctx, des, params, saved, base)

    ctx.opts['_liveness_detail'] = detail


def _decl_flag(expected, name, key):
    v = expected.get(name)
    return v.get(key) if isinstance(v, dict) else None


def _unhealthy_keys(des):
    return set((r.get('i'), r.get('name')) for r in _timeline_problems(des, limit=40))


def _test_one(ctx, des, p, base, sick0=frozenset()):
    orig = p.expression
    v0 = p.value
    step_txt, unit = _step_for(des, p)
    try:
        try:
            p.expression = _perturbed_expr(orig, step_txt, unit)
        except Exception as e:
            ctx.add('liveness', 'param.perturbation_rejected', 'warn',
                    param=p.name, expr=_clip(orig, 40), msg=_clip(str(e), 100))
            return
        _settle(des)
        if not _num_differs(p.value, v0):
            ctx.add('liveness', 'param.perturbation_rejected', 'warn',
                    param=p.name, expr=_clip(orig, 40), reason='value_unchanged')
            return
        after = _snapshot(des)
        # Only features that became unhealthy *because of this perturbation*.
        broke = [r for r in _timeline_problems(des, limit=40)
                 if (r.get('i'), r.get('name')) not in sick0]
        if broke:
            # Live, but fragile: a 5% nudge already breaks it. Worth saying.
            ctx.add('liveness', 'param.fragile', 'warn',
                    param=p.name, step=(step_txt + ' ' + unit).strip(),
                    feature=broke[0].get('name'), msg=broke[0].get('msg'))
            return
        if not _snapshot_differs(base, after):
            ctx.add('liveness', 'param.dead', 'error',
                    param=p.name, step=(step_txt + ' ' + unit).strip(),
                    expr=_clip(orig, 40))
    finally:
        try:
            p.expression = orig
        except Exception:
            pass
        _settle(des)


def _edit_canary(ctx, des, params, roots, base, detail):
    """Perturb every root parameter at once, then look for a clash that only appears
    after an edit. This is the P5 failure mode exactly: geometry pinned to literal
    coordinates does not follow when the parts around it grow. Costs two rebuilds.
    Roots only, so derived parameters are not perturbed twice.
    """
    by_name = dict((p.name, p) for p in params)
    targets = [by_name[n] for n in roots if n in by_name]
    if not targets:
        return
    saved = dict((p.name, p.expression) for p in targets)
    clash_before = _clash_count(des)
    try:
        for p in targets:
            step_txt, unit = _step_for(des, p)
            try:
                p.expression = _perturbed_expr(saved[p.name], step_txt, unit)
            except Exception:
                pass
        _settle(des)
        after = _snapshot(des)
        detail['canary'] = 'ran'
        if not _snapshot_differs(base, after):
            ctx.add('liveness', 'model.inert', 'error',
                    params=len(targets),
                    note='no root parameter changed any geometry')
            return
        clash_after = _clash_count(des)
        if clash_after > max(clash_before, 0):
            ctx.add('liveness', 'edit.introduces_clash', 'error',
                    clashes_before=max(clash_before, 0), clashes_after=clash_after,
                    note='geometry does not follow a parameter edit')
        for rec in _timeline_problems(des, limit=2):
            if rec['state'] == 'error':
                ctx.add('liveness', 'edit.breaks_feature', 'warn',
                        feature=rec.get('name'), msg=rec.get('msg'))
    finally:
        for p in targets:
            try:
                p.expression = saved[p.name]
            except Exception:
                pass
        _settle(des)


def _restore_all(ctx, des, params, saved, base):
    """Belt and braces. Every perturbation restores itself in its own finally; this
    re-asserts every expression and then proves, geometrically, that the document was
    left as it was found. If it was not, the verdict says so and the caller must undo.
    """
    bad = []
    for p in params:
        want = saved.get(p.name)
        if want is None:
            continue
        try:
            if p.expression != want:
                p.expression = want
        except Exception:
            bad.append(p.name)
    _settle(des)
    if bad:
        ctx.add('liveness', 'param.restore_failed', 'error', params=bad[:6])
    if _snapshot_differs(base, _snapshot(des)):
        ctx.add('liveness', 'model.not_restored', 'error',
                note='geometry differs from pre-verification state; undo before continuing')


# ----------------------------------------------------------------------------- verdict

def _load_decl(decl, decl_path):
    if decl is not None:
        return decl, None
    if not decl_path:
        return {}, None
    try:
        with open(decl_path, encoding='utf-8') as f:
            return json.load(f), None
    except Exception as e:
        return {}, _clip(str(e), 120)


def _roll_up(ctx):
    vals = ctx.status.values()
    if any(v == 'fail' for v in vals):
        return 'fail'
    if any(v == 'warn' for v in vals):
        return 'warn'
    if any(v == 'skip' for v in vals):
        return 'pass_partial'      # a skipped check is never a passing check
    return 'pass'


# One short remediation line per distinct error code, emitted only on failure and only
# once. The full taxonomy lives in the skill body, which is already resident; this is
# the fallback for when it is not.
HINTS = {
    'sketch.unconstrained': 'sketch has no constraints at all: constrain to origin, add H/V, then bind dimensions',
    'sketch.under_constrained': 'add constraints to the named entities, then dimension while the flag still reads False',
    'dimension.literal_expression': 'set dim.parameter.expression to a named user parameter',
    'param.dead': 'parameter drives nothing: bind a sketch dimension or a feature extent to it',
    'model.inert': 'no parameter drives any geometry: profile is at literal Point3D coordinates',
    'edit.introduces_clash': 'geometry is placed by coordinates, not datums: re-place against named construction planes',
    'model.not_restored': 'call fusion_mcp_update undo until timeline count returns to its pre-run value',
    'param.restore_failed': 'undo, then re-run; do not build on this document state',
    'interference.clash': 'bodies overlap: move or resize against the declared chain, do not nudge coordinates',
    'clearance.violated': 'declared clearance not met: change the parameter that sets the gap',
    'ref.unresolved': 'register the face at authoring time with fh_ref(role, entity)',
    'timeline.reference_failure': 'a feature can no longer find its reference: check the profile fits the target body',
    'ref.stale_brep': 'BRep object held across a rebuild: capture entityToken and re-resolve',
}


def fh_verify(decl_path=None, decl=None, refs=None, attempt=1, **opts):
    t0 = time.time()
    try:
        decl_obj, decl_err = _load_decl(decl, decl_path)
        ctx = Ctx(decl_obj, refs, opts)
        if decl_err:
            ctx.add('clearance', 'decl.unreadable', 'warn', msg=decl_err)

        for fn, name in ((check_constraints, 'constraints'),
                         (check_timeline, 'timeline'),
                         (check_interference, 'interference'),
                         (check_clearance, 'clearance')):
            try:
                fn(ctx)
            except Exception as e:
                ctx.add(name, 'check.crashed', 'warn', msg=_clip(str(e), 140))
        try:
            check_liveness(ctx)
        except Exception as e:
            ctx.add('liveness', 'check.crashed', 'warn', msg=_clip(str(e), 140))

        base_snapshot = _snapshot(ctx.des)
        verdict = {
            'v': FH_CONTRACT,
            'status': _roll_up(ctx),
            'attempt': attempt,
            'units': 'mm',
            'checks': dict(ctx.status),
            'model': _model_summary(base_snapshot),
            'stats': {'timeline': _timeline_count(ctx.des),
                      'params': _param_count(ctx.des),
                      'sec': _n(time.time() - t0, 1)},
        }
        if ctx.skips:
            verdict['skipped'] = ctx.skips
        det = ctx.opts.get('_liveness_detail')
        if det and det.get('mode') == 'sampled':
            verdict['liveness'] = det
        if ctx.findings:
            verdict['findings'] = ctx.findings
            n_emitted = sum(ctx.counts.values())
            if n_emitted > len(ctx.findings):
                verdict['truncated'] = n_emitted - len(ctx.findings)
            codes = []
            for f in ctx.findings:
                if f['sev'] == 'error' and f['code'] in HINTS and f['code'] not in codes:
                    codes.append(f['code'])
            if codes:
                verdict['hints'] = dict((c, HINTS[c]) for c in codes[:4])
        return VERDICT_PREFIX + json.dumps(verdict, separators=(',', ':'))
    except Exception:
        # Deliberate deviation from "do not catch exceptions": by the time this runs
        # the model is already built, and an uncaught throw here would discard every
        # check that already passed. The build itself is never wrapped.
        return VERDICT_PREFIX + json.dumps(
            {'v': FH_CONTRACT, 'status': 'error', 'code': 'verify.internal',
             'msg': _clip(traceback.format_exc(), 500)}, separators=(',', ':'))


def _timeline_count(des):
    try:
        return des.timeline.count
    except Exception:
        return None


def _param_count(des):
    try:
        return des.userParameters.count
    except Exception:
        return None


def fh_state():
    """Cheap probe. No rebuilds. Used after a raw build exception, and to drive
    undo-to-depth (undo until 'timeline' matches the value from the previous verdict)."""
    try:
        app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)
        out = {'v': FH_CONTRACT, 'status': 'state',
               'stats': {'timeline': _timeline_count(des),
                         'params': _param_count(des),
                         'bodies': len(_all_bodies(des))},
               'model': _model_summary(_snapshot(des))}
        probs = _timeline_problems(des)
        if probs:
            out['findings'] = [dict(p, check='timeline',
                                    code=p.pop('code', 'timeline.unhealthy'),
                                    sev='error' if p.get('state') == 'error' else 'warn')
                               for p in probs]
        return VERDICT_PREFIX + json.dumps(out, separators=(',', ':'))
    except Exception:
        return VERDICT_PREFIX + json.dumps(
            {'v': FH_CONTRACT, 'status': 'error', 'code': 'verify.internal',
             'msg': _clip(traceback.format_exc(), 400)}, separators=(',', ':'))
