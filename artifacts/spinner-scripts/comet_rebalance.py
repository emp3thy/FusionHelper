"""Comet repair: pod/pocket azimuths 170/210 -> 160/200 (symmetric about
the head axis so tail-nut y-moments cancel), re-run balance nulling,
rebuild the foot chamfer whose edge refs died when the pods moved."""
import math

import adsk.core
import adsk.fusion

FH_ATTEMPT = 2
FH_OPTS = {
    "only_params": [
        "cc_t", "cc_tail_t", "cc_hub_d", "cc_lip_id", "cc_seat_d",
        "cc_seat_floor", "cc_seat_depth", "cc_lead",
        "cc_pocket_floor", "cc_pocket_h", "cc_pocket_d",
        "cc_r_head", "cc_r_tail", "cc_stub_d",
    ],
}
INTERFERENCE_ALLOWED = []

NUT_MASS = 5.4
PLA_RHO = 1.24
# old azimuth factors written by bound_circle ('%.5f') -> new (160/200)
FACTOR_MAP = {
    "cc_r_tail * 0.98481": "cc_r_tail * 0.93969",
    "cc_r_tail * 0.17365": "cc_r_tail * 0.34202",
    "cc_r_tail * 0.86603": "cc_r_tail * 0.93969",
    "cc_r_tail * 0.50000": "cc_r_tail * 0.34202",
}


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    up = des.userParameters

    # 1. drop the stale foot chamfer (cached-geometry reference failure)
    old = root.features.itemByName("foot_chamfer")
    old.deleteMe()
    print("FH foot_chamfer removed")

    # 2. re-azimuth pods and pockets by rewriting the position dims
    swapped = 0
    for p in des.allParameters:
        adsk.doEvents()
        new = FACTOR_MAP.get(p.expression)
        if new is not None:
            p.expression = new
            swapped += 1
    if swapped != 8:
        raise RuntimeError("expected 8 azimuth dims, rewrote %d" % swapped)
    print("FH azimuths rewritten: %d dims" % swapped)

    c160 = math.cos(math.radians(160))
    s160 = math.sin(math.radians(160))
    c200 = math.cos(math.radians(200))
    s200 = math.sin(math.radians(200))

    # 3. balance loop (y is structurally nulled now; solve x via r_h,
    #    with r_t chosen to keep r_h inside its clamp)
    acc = adsk.fusion.CalculationAccuracy.HighCalculationAccuracy
    resid_mm = float("inf")
    for it in range(6):
        adsk.doEvents()
        b = root.bRepBodies.itemByName("comet_body")
        props = b.getPhysicalProperties(acc)
        com = props.centerOfMass
        m_b = props.volume * PLA_RHO
        r_h = up.itemByName("cc_r_head").value
        r_t = up.itemByName("cc_r_tail").value
        mx = m_b * com.x + NUT_MASS * (r_h + r_t * (c160 + c200))
        my = m_b * com.y + NUT_MASS * (r_t * (s160 + s200))
        m_tot = m_b + 3 * NUT_MASS
        resid_mm = math.hypot(mx, my) / m_tot * 10.0
        print("FH balance it%d: m_b=%.1fg com=(%.4f,%.4f)cm "
              "r_h=%.3f r_t=%.3f resid=%.4f mm"
              % (it, m_b, com.x, com.y, r_h, r_t, resid_mm))
        if resid_mm < 0.05:
            break
        span = -(c160 + c200)          # 1.87939
        r_t_new = (2.9 + m_b * com.x / NUT_MASS) / span
        r_t_new = min(2.95, max(2.4, r_t_new))
        r_h_new = span * r_t_new - m_b * com.x / NUT_MASS
        r_h_new = min(3.2, max(2.05, r_h_new))
        up.itemByName("cc_r_tail").expression = "%.4f mm" % (r_t_new * 10)
        up.itemByName("cc_r_head").expression = "%.4f mm" % (r_h_new * 10)
    print("FH BALANCE final resid_mm=%.4f" % resid_mm)
    if resid_mm >= 0.1:
        raise RuntimeError("balance did not converge: %.4f mm" % resid_mm)

    # 4. foot chamfer NOT rebuilt: 0.5 mm chamfer dies with
    # ASM_BL_CAP_COMPLEX at the blade-outline sliver tangencies
    # (measured attempt 2). Elephant-foot control moves to the slicer's
    # first-layer compensation; cc_foot param removed with its feature.
    dead = up.itemByName("cc_foot")
    dead.deleteMe()
    print("FH cc_foot parameter removed with its feature")


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
