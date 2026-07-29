# fh_verify.py --- FusionHelper verification block, contract v1
#
# Installed by the fusionhelper package to %LOCALAPPDATA%\FusionHelper\fh_verify.py.
# NEVER pasted into a generated script: generated scripts carry a ~20-line stub that
# exec()s this file at run time. Two reasons, both hard:
#   1. fusion_mcp_execute takes the script as a *string*, so every byte of an inlined
#      block would cost Claude context on every repair attempt (~9,000 tokens x N).
#   2. No user site-packages is importable inside Fusion, so `import fusionhelper`
#      cannot work. exec() of a read file bypasses the import system entirely.
#
# Runs on CPython 3.14 inside Fusion360.exe. Stdlib only, no package imports.
#
# OUTPUT PROTOCOL --- incremental, because a failing script never reaches its last line.
#   FH_CHECK1   {...}  one per check, printed as that check completes
#   FH_GUARD1   {...}  restore manifest, printed BEFORE any parameter is perturbed
#   FH_VERDICT1 {...}  final roll-up (does not repeat findings)
# The MCP folds stdout into the `error` field when a script fails, so lines printed
# before a failure survive. That is what makes the guard manifest recoverable.
#
# Entry points:
#   fh_verify(clearances, face_specs, datum_heights_cm, digest, refs, attempt, **opts)
#   fh_state()   cheap probe, no rebuilds: timeline depth, health, bbox

import adsk.core
import adsk.fusion
import json
import math
import re
import time
import traceback

FH_CONTRACT = 1
VERDICT_PREFIX = 'FH_VERDICT1 '
CHECK_PREFIX = 'FH_CHECK1 '
GUARD_PREFIX = 'FH_GUARD1 '

# Change detection thresholds, in internal units (cm / cm2 / cm3).
# A genuinely dead parameter reproduces byte-identical metrics (probe: volume equal to
# four decimal places, all 12 faces unchanged), while a live one moves by percent-scale.
# The margin between signal and noise is ~6 orders of magnitude, so these are not delicate.
ABS_TOL = 1e-7
REL_TOL = 1e-9

# measureMinimumDistance returns 0.00000 for BOTH "touching" and "interpenetrating by
# 5 mm" (verified). A zero is therefore uninformative on its own and must be resolved
# against the interference result. See _judge_clearance.
ZERO_MM = 1e-4

# Perturbation sizing, internal units.
LEN_STEP_FRAC = 0.05
LEN_STEP_MIN_CM = 0.02          # 0.2 mm
LEN_STEP_MAX_CM = 1.0           # 10 mm
ANG_STEP_MIN_RAD = 0.0175       # 1 deg
ANG_STEP_MAX_RAD = 0.0873       # 5 deg

MAX_FINDINGS_PER_CHECK = 5
MAX_FINDINGS_TOTAL = 12
MSG_CLIP = 180

CHECKS = ('constraints', 'timeline', 'interference', 'clearance', 'liveness')

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


def _cm_str_to_mm(v):
    """Declaration numerics arrive as decimal strings ALREADY IN CM (Agent D's
    compiler). Convert once, here, at the boundary; nothing downstream sees cm."""
    if v is None:
        return None
    try:
        return float(str(v).strip()) * 10.0
    except Exception:
        return None


def _print(line):
    try:
        print(line)
    except Exception:
        pass


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
    m = {'f': None, 'v': None, 'a': None, 'bb': None, 'c': None}
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
        # centre of mass makes the signature translation-sensitive: a groove
        # field moved by a position parameter keeps volume/area/bbox/face
        # count byte-identical (measured: nook_course_y0 false-negatived as
        # param.dead) but shifts the centroid.
        com = b.physicalProperties.centerOfMass
        m['c'] = (com.x, com.y, com.z)
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
        ca, cb = ma.get('c'), mb.get('c')
        if (ca is None) != (cb is None):
            return True
        if ca is not None:
            for i in range(3):
                if _num_differs(ca[i], cb[i]):
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
        self.status = dict((c, 'pass') for c in CHECKS)
        self.skips = {}
        self.counts = {}
        self.emitted = set()
        # Cross-check state: clearance needs to know what interference concluded.
        self.interference_ran = False
        self.clash_bodies = set()

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

    def emit_check(self, check):
        """Print this check's result the moment it completes. A script that dies at
        check 4 still surfaces checks 1-3; a consolidated final print would lose them."""
        if check in self.emitted:
            return
        self.emitted.add(check)
        line = {'c': check, 's': self.status[check]}
        if check in self.skips:
            line['why'] = self.skips[check]
        fs = [dict((k, v) for k, v in f.items() if k != 'check')
              for f in self.findings if f['check'] == check]
        if fs:
            line['f'] = fs
        total = self.counts.get(check, 0)
        if total > len(fs):
            line['more'] = total - len(fs)
        _print(CHECK_PREFIX + json.dumps(line, separators=(',', ':')))

    def failed(self):
        return any(v == 'fail' for v in self.status.values())


# ------------------------------------------------------------------- check: constraints

def check_constraints(ctx):
    des = ctx.des
    try:
        param_names = set(p.name for p in _user_params(des))
    except Exception:
        param_names = set()

    try:
        comps = list(des.allComponents)
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
            out.append({'i': i, 't': 'SketchPoint', 'at': [_mm(g.x), _mm(g.y)]})
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

# 4 measured live 2026-07-28: features beyond the timeline marker (rolled back)
# report healthState 4 -- deliberate user state, not a build failure
_HEALTH = {0: 'healthy', 1: 'warning', 2: 'error', 3: 'suppressed', 4: 'rolled_back'}


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


def _leaf(name):
    return (name or '').split('/')[-1]


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
    ctx.interference_ran = True
    exempt = 0
    for i in range(res.count):
        r = res.item(i)
        n1 = _name_of(r.entityOne)
        n2 = _name_of(r.entityTwo)
        if _pair_key(n1, n2) in allowed:
            exempt += 1
            continue
        # Recorded even when the finding list is truncated: the clearance check
        # consults this set, and truncation must not silently downgrade a zero
        # clearance from error to warning.
        ctx.clash_bodies.add(_leaf(n1))
        ctx.clash_bodies.add(_leaf(n2))
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


def _allowed_pairs(decl):
    allowed = set()
    for pair in (decl.get('interference_allowed') or []):
        try:
            allowed.add(_pair_key(pair[0], pair[1]))
        except Exception:
            pass
    return allowed


def _clash_count(des, allowed=None):
    """Cheap yes/no used by the edit canary. Returns -1 when not analysable.

    Skips declared-intent pairs (interference_allowed) -- measured 2026-07-28:
    without the filter, 27 intended icing overlaps inflated the before/after
    counts and an allowed-pair contact appearing under perturbation read as a
    regression.
    """
    bodies = [b for _, b in _all_bodies(des) if _is_solid(b)]
    if len(bodies) < 2:
        return -1
    try:
        res = _analyze(des, bodies)
        if not res:
            return 0
        if not allowed:
            return res.count
        n = 0
        for i in range(res.count):
            r = res.item(i)
            if _pair_key(_name_of(r.entityOne), _name_of(r.entityTwo)) in allowed:
                continue
            n += 1
        return n
    except Exception:
        return -1


# -------------------------------------------------------------- reference resolution

def _resolve_role(des, refs, role):
    """role -> (entities, err).

    Design.findEntityByToken returns a LIST. Where a face has been split by later
    features it returns every resulting piece, the first being the "most logical
    match". A blind [0] is therefore silently wrong in exactly the case durable
    tokens exist to protect against, so every caller gets the whole list and decides.
    """
    tok = refs.get(role)
    if not tok:
        return [], 'not_registered'
    try:
        found = des.findEntityByToken(tok)
    except Exception as e:
        msg = str(e)
        return [], ('stale_brep' if classify(msg) == 'ref.stale_brep' else _clip(msg, 80))
    if found is None:
        return [], 'token_unresolved'
    try:
        ents = [found[i] for i in range(len(found))]
    except TypeError:
        ents = [found]
    if not ents:
        return [], 'token_unresolved'
    return ents, None


def _owning_body(entity):
    """Body name for a face/edge/body, for cross-referencing against clash pairs."""
    try:
        return entity.body.name
    except Exception:
        pass
    try:
        n = entity.name
        return n if isinstance(n, str) else None
    except Exception:
        return None


# -------------------------------------------------------------------- check: clearance

def _clearance_items(decl):
    """Accept a list of dicts or a dict of name -> dict; Agent D's exact shape is
    still to be confirmed, so parse defensively rather than assume."""
    raw = decl.get('clearances')
    if not raw:
        return []
    if isinstance(raw, dict):
        return [dict(v, _name=k) for k, v in raw.items() if isinstance(v, dict)]
    return [c for c in raw if isinstance(c, dict)]


def _measure_pair(ctx, a_role, b_role):
    """Minimum distance in mm over every resolved piece of both roles.

    Returns (mm, info, err). `info` records multiplicity and the spread across
    pieces, because when a role resolves to several faces the answer depends on
    which one was meant, and that is worth surfacing rather than hiding.
    """
    des = ctx.des
    ea, err_a = _resolve_role(des, ctx.refs, a_role)
    if err_a:
        return None, {'role': a_role}, err_a
    eb, err_b = _resolve_role(des, ctx.refs, b_role)
    if err_b:
        return None, {'role': b_role}, err_b
    mm_values = []
    for x in ea:
        for y in eb:
            try:
                d = ctx.app.measureManager.measureMinimumDistance(x, y).value
            except Exception as e:
                msg = str(e)
                return None, {}, ('stale_brep' if classify(msg) == 'ref.stale_brep'
                                  else _clip(msg, 100))
            v = _mm(d)
            if v is not None:
                mm_values.append(v)
    if not mm_values:
        return None, {}, 'measure_failed'
    info = {'bodies': [_owning_body(ea[0]), _owning_body(eb[0])]}
    if len(ea) > 1 or len(eb) > 1:
        info['pieces'] = [len(ea), len(eb)]
        info['spread_mm'] = [min(mm_values), max(mm_values)]
    return min(mm_values), info, None


def check_clearance(ctx):
    items = _clearance_items(ctx.decl)
    specs = ctx.decl.get('face_specs') or {}
    _check_datums(ctx)
    _check_declared_roles(ctx, specs, items)
    if not items:
        if ctx.status['clearance'] == 'pass':
            ctx.skip('clearance', 'none_declared')
        return
    for c in items:
        try:
            a_role, b_role = c['between'][0], c['between'][1]
        except Exception:
            ctx.add('clearance', 'decl.malformed', 'error', decl=_clip(str(c), 80))
            continue
        mm, info, err = _measure_pair(ctx, a_role, b_role)
        if err:
            code = ('face.unresolved' if err in ('not_registered', 'token_unresolved')
                    else 'ref.stale_brep' if err == 'stale_brep'
                    else 'clearance.measure_failed')
            ctx.add('clearance', code, 'error', between=[a_role, b_role],
                    role=info.get('role'), reason=err,
                    registered=sorted(ctx.refs.keys())[:8])
            continue
        if 'pieces' in info:
            # The role resolved to several faces: it was split after registration.
            # Only an error if which piece was meant would change the verdict.
            lo_mm = _cm_str_to_mm(c.get('min'))
            straddles = (lo_mm is not None and
                         info['spread_mm'][0] < lo_mm <= info['spread_mm'][1])
            ctx.add('clearance', 'face.ambiguous', 'error' if straddles else 'warn',
                    between=[a_role, b_role], pieces=info['pieces'],
                    spread_mm=info['spread_mm'],
                    note='pieces straddle the threshold' if straddles else None)
        _judge_clearance(ctx, c, a_role, b_role, mm, info)


def _judge_clearance(ctx, c, a_role, b_role, mm, info, check='clearance', prefix=''):
    lo = _cm_str_to_mm(c.get('min'))
    hi = _cm_str_to_mm(c.get('max'))
    declared = c.get('min') if lo is not None else c.get('max')

    if mm is not None and mm <= ZERO_MM:
        # measureMinimumDistance cannot distinguish touching from interpenetrating,
        # so a zero is resolved against the interference result and never passes.
        bodies = set(b for b in (info.get('bodies') or []) if b)
        if bodies & ctx.clash_bodies:
            ctx.add(check, prefix + 'clearance.zero', 'error',
                    between=[a_role, b_role], measured_mm=0, declared_cm=declared,
                    bodies=sorted(bodies),
                    note='interpenetrating: interference reports a clash on these bodies')
        elif not ctx.interference_ran:
            ctx.add(check, prefix + 'clearance.zero', 'error',
                    between=[a_role, b_role], measured_mm=0, declared_cm=declared,
                    note='interference not analysed; touching and interpenetrating are indistinguishable')
        elif lo is not None and lo > ZERO_MM:
            ctx.add(check, prefix + 'clearance.violated', 'error',
                    between=[a_role, b_role], min_mm=_n(lo), measured_mm=0,
                    short_by_mm=_n(lo), note='contact where a gap was declared')
        else:
            ctx.add(check, prefix + 'clearance.zero', 'warn',
                    between=[a_role, b_role], measured_mm=0, declared_cm=declared,
                    note='touching; interference clean, but the distance oracle is blind here')
        return

    if mm is None:
        return
    if lo is not None and mm < lo - 1e-6:
        ctx.add(check, prefix + 'clearance.violated', 'error',
                between=[a_role, b_role], min_mm=_n(lo), measured_mm=mm,
                short_by_mm=_n(lo - mm))
    elif hi is not None and mm > hi + 1e-6:
        ctx.add(check, prefix + 'clearance.violated', 'error',
                between=[a_role, b_role], max_mm=_n(hi), measured_mm=mm,
                over_by_mm=_n(mm - hi))


def _check_declared_roles(ctx, specs, items):
    """Every role the declaration names must have been registered by fh_ref during
    the build. Catching this here turns a silent miss into a named one."""
    needed = set(specs or ())
    for c in items:
        try:
            needed.update(c['between'][:2])
        except Exception:
            pass
    missing = sorted(r for r in needed if r not in ctx.refs)
    if missing:
        ctx.add('clearance', 'face.unresolved', 'error', roles=missing[:6],
                registered=sorted(ctx.refs.keys())[:8],
                note='declared role never passed to fh_ref during the build')


def _check_datums(ctx):
    """Declared datum offsets versus the construction planes actually built.

    Reads the offset from the plane's own definition rather than assuming an axis --
    the XZ inversion makes any hardcoded axis assumption unsafe.
    """
    declared = ctx.decl.get('datum_heights_cm') or {}
    if not declared:
        return
    planes = {}
    try:
        for comp in ctx.des.allComponents:
            for i in range(comp.constructionPlanes.count):
                pl = comp.constructionPlanes.item(i)
                planes[pl.name] = pl
    except Exception:
        pass
    for name in sorted(declared):
        pl = planes.get(name)
        if pl is None:
            ctx.add('clearance', 'datum.missing', 'error', datum=name,
                    built=sorted(planes.keys())[:8])
            continue
        want_mm = _cm_str_to_mm(declared[name])
        if want_mm is None:
            continue
        try:
            got_mm = _mm(pl.definition.offset.value)
        except Exception:
            continue          # not an offset-defined plane; the existence check stands
        if got_mm is not None and abs(got_mm - want_mm) > 1e-4:
            ctx.add('clearance', 'datum.missing', 'error', datum=name,
                    declared_mm=_n(want_mm), built_mm=got_mm,
                    note='construction plane offset does not match the declaration')


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
    """Measured: assigning `p.expression` recomputes the model before the next
    statement runs. Reading the volume with no doEvents() already showed the new
    value, and neither doEvents() nor computeAll() produced any further change.

    doEvents() is kept anyway. It costs nothing, it keeps the UI responsive across
    a long sweep, and treating synchronous recompute as a guarantee is more than
    one measurement supports. The computeAll() fallback is gone -- it was dead
    weight standing in for an uncertainty that has now been resolved.
    """
    adsk.doEvents()


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


def _unhealthy_keys(des):
    return set((r.get('i'), r.get('name')) for r in _timeline_problems(des, limit=40))


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
        # _clip returns None for a falsy message, and an exception with no message
        # is entirely possible. Concatenating None here would turn a HANDLED failure
        # into an unhandled TypeError inside the handler, destroying the verdict.
        ctx.skip('liveness', 'no_user_parameters: ' + (_clip(str(e), 60) or type(e).__name__))
        return
    opted_out = set(ctx.decl.get('expect_dead') or ())
    params = [p for p in params if p.name not in opted_out]
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

    # Printed BEFORE anything is perturbed. Python `finally` covers exceptions but
    # not a native crash or a kill, and a failing script never reaches its cleanup.
    # Because the MCP folds stdout into the error field on failure, this manifest
    # survives, and the document can be restored by hand from the transcript.
    _print(GUARD_PREFIX + json.dumps(
        {'restore': dict((k, _clip(v, 60)) for k, v in saved.items())},
        separators=(',', ':')))
    # `held` names the one parameter currently perturbed, or None. It is a single
    # slot by construction, which is what makes the invariant below checkable.
    held = [None]
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
                if (time.time() - t_start) + per * (len(order) - idx) > budget:
                    untested = [q.name for q in order[idx:]]
                    break
            t_p = time.time()
            state = _step_to(ctx, des, p, held)
            if state is not None:
                _judge_one(ctx, des, p, base, sick0, state)
            dt = time.time() - t_p
            per = dt if per is None else max(per, dt)
            tested.append(p.name)
        detail['tested'] = len(tested)
        detail['of'] = len(order)
        if untested:
            detail['mode'] = 'sampled'
            detail['untested'] = untested[:12]
            ctx.add('liveness', 'liveness.budget_exhausted', 'warn',
                    tested=len(tested), of=len(order), untested=untested[:12])
    finally:
        _release(des, held)
        _restore_all(ctx, des, params, saved, base)
        _print(GUARD_PREFIX + '{"restore":"released"}')

    ctx.opts['_liveness_detail'] = detail


def _step_to(ctx, des, p, held):
    """Restore whatever is perturbed, perturb p, and settle ONCE for both writes.

    Verified: two consecutive expression writes with a single settle both take
    effect, and the interleaved restore-then-perturb case lands correctly -- the
    restore is exact and the perturbation applies.

    This saves SETTLES, not rebuilds, and the distinction is worth stating because
    it is easy to get backwards. Measured on a 6-parameter model with fillets: a
    bare expression write costs ~76 ms with no doEvents() and no read, while a
    read on a settled model costs ~0.7 ms. The recompute is therefore eager, on
    the write. Restore-then-perturb is two writes either way, so grouping them
    under one settle cannot remove a rebuild: isolated 1507 ms vs interleaved
    1263 ms, a ratio of 1.19. The sweep is 2N rebuilds and N+1 settles, and this
    restructure buys the ~19% doEvents() overhead -- not half the work.

    The ordering is load-bearing and is the whole reason this is safe: the restore
    of the previous parameter is written BEFORE the next one is perturbed, and
    `held` is cleared before it is re-set. At no instant is more than one parameter
    perturbed, so the guarantee that made the old per-parameter `finally` valuable
    is preserved exactly rather than traded away for the saved settle.

    Returns the state needed to judge p, or None if p could not be perturbed.
    """
    if held[0] is not None:
        prev, prev_orig = held[0]
        held[0] = None                      # cleared first: a throw below must not
        try:                                # leave a stale slot pointing at prev
            prev.expression = prev_orig
        except Exception:
            ctx.add('liveness', 'param.restore_failed', 'error', params=[prev.name])
    orig = p.expression
    v0 = p.value
    step_txt, unit = _step_for(des, p)
    try:
        p.expression = _perturbed_expr(orig, step_txt, unit)
    except Exception as e:
        ctx.add('liveness', 'param.perturbation_rejected', 'warn', param=p.name,
                expr=_clip(orig, 40), msg=_clip(str(e), 100) or type(e).__name__)
        _settle(des)                        # the restore above still needs settling
        return None
    held[0] = (p, orig)
    _settle(des)
    return (orig, v0, step_txt, unit)


def _judge_one(ctx, des, p, base, sick0, state):
    orig, v0, step_txt, unit = state
    step = (step_txt + ' ' + unit).strip()
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
        ctx.add('liveness', 'param.fragile', 'warn', param=p.name, step=step,
                feature=broke[0].get('name'), msg=broke[0].get('msg'))
        return
    if not _snapshot_differs(base, after):
        ctx.add('liveness', 'param.dead', 'error', param=p.name, step=step,
                expr=_clip(orig, 40))


def _release(des, held):
    """Restore the single held parameter, if any. Runs in the sweep's finally, so
    an exception mid-measurement cannot leave the document perturbed."""
    if held[0] is None:
        return
    p, orig = held[0]
    held[0] = None
    try:
        p.expression = orig
    except Exception:
        pass
    _settle(des)


def _edit_canary(ctx, des, params, roots, base, detail):
    """Perturb every root parameter at once, then re-check interference AND the
    declared clearances. This is the P5 failure mode exactly: geometry pinned to
    literal coordinates does not follow when the parts around it grow, so a clash
    or a closed gap appears only after an edit. Costs two rebuilds.

    Every reference is re-resolved from its token inside the perturbed state --
    nothing resolved before the rebuild is reused after it, because a held BRep
    object dies with InternalValidationError across a rebuild.
    """
    by_name = dict((p.name, p) for p in params)
    targets = [by_name[n] for n in roots if n in by_name]
    if not targets:
        return
    saved = dict((p.name, p.expression) for p in targets)
    clash_before = _clash_count(des, _allowed_pairs(ctx.decl))
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
            ctx.add('liveness', 'model.inert', 'error', params=len(targets),
                    note='no root parameter changed any geometry')
            return
        clash_after = _clash_count(des, _allowed_pairs(ctx.decl))
        if clash_after > max(clash_before, 0):
            ctx.add('liveness', 'edit.introduces_clash', 'error',
                    clashes_before=max(clash_before, 0), clashes_after=clash_after,
                    note='geometry does not follow a parameter edit')
        for c in _clearance_items(ctx.decl):
            try:
                a_role, b_role = c['between'][0], c['between'][1]
            except Exception:
                continue
            mm, info, err = _measure_pair(ctx, a_role, b_role)
            if err or mm is None:
                continue          # already reported at nominal; do not double-report
            _judge_clearance(ctx, c, a_role, b_role, mm, info,
                             check='liveness', prefix='edit.')
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
    'edit.clearance.violated': 'gap holds at nominal and closes on edit: the gap is not parameterised',
    'edit.clearance.zero': 'parts touch only after an edit: re-place against datums',
    'model.not_restored': 'call fusion_mcp_update undo until timeline count returns to its pre-run value',
    'param.restore_failed': 'undo, then re-run; do not build on this document state',
    'interference.clash': 'bodies overlap: move or resize against the declared chain, do not nudge coordinates',
    'clearance.violated': 'declared clearance not met: change the parameter that sets the gap',
    'clearance.zero': 'distance 0 means touching OR interpenetrating: read the interference finding',
    'face.unresolved': 'register the face at authoring time with fh_ref(role, entity)',
    'face.ambiguous': 'token resolved to several faces: the face was split after registration',
    'datum.missing': 'declared datum plane not built, or built at a different offset',
    'timeline.reference_failure': 'a feature can no longer find its reference: check the profile fits the target body',
    'ref.stale_brep': 'BRep object held across a rebuild: capture entityToken and re-resolve',
}


def fh_verify(clearances=None, face_specs=None, datum_heights_cm=None, digest=None,
              interference_allowed=None, expect_dead=None, refs=None, attempt=1, **opts):
    t0 = time.time()
    try:
        decl = {'clearances': clearances, 'face_specs': face_specs,
                'datum_heights_cm': datum_heights_cm,
                'interference_allowed': interference_allowed,
                'expect_dead': expect_dead}
        ctx = Ctx(decl, refs, opts)

        # Order is load-bearing: interference must precede clearance, because a
        # measured distance of 0 is only interpretable against the clash result.
        for fn, name in ((check_constraints, 'constraints'),
                         (check_timeline, 'timeline'),
                         (check_interference, 'interference'),
                         (check_clearance, 'clearance'),
                         (check_liveness, 'liveness')):
            try:
                fn(ctx)
            except Exception as e:
                ctx.add(name, 'check.crashed', 'warn', msg=_clip(str(e), 140))
            ctx.emit_check(name)

        verdict = {
            'v': FH_CONTRACT,
            'status': _roll_up(ctx),
            'attempt': attempt,
            'units': 'mm',
            'checks': dict(ctx.status),
            'model': _model_summary(_snapshot(ctx.des)),
            'stats': {'timeline': _timeline_count(ctx.des),
                      'params': _param_count(ctx.des),
                      'sec': _n(time.time() - t0, 1)},
        }
        if digest:
            verdict['decl'] = digest
        if ctx.skips:
            verdict['skipped'] = ctx.skips
        det = ctx.opts.get('_liveness_detail')
        if det and det.get('mode') == 'sampled':
            verdict['liveness'] = det
        # Findings are NOT repeated here -- they were printed per check as each
        # completed. Only the codes needed to look up remediation are carried.
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
            out['findings'] = [dict(p, code=p.pop('code', 'timeline.unhealthy'),
                                    sev='error' if p.get('state') == 'error' else 'warn')
                               for p in probs]
        return VERDICT_PREFIX + json.dumps(out, separators=(',', ':'))
    except Exception:
        return VERDICT_PREFIX + json.dumps(
            {'v': FH_CONTRACT, 'status': 'error', 'code': 'verify.internal',
             'msg': _clip(traceback.format_exc(), 400)}, separators=(',', ':'))
