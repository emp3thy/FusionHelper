"""Counterfeit Comet PiP - zero-hardware variant, balanced by hidden
voids instead of hidden steel.

Same asymmetric silhouette as v1 (hub + head lobe + spline tail + two
pod knots, pods at 160/200 deg - the corrected symmetric azimuths), but:
- printed diamond-journal stator replaces the 608 bearing;
- the fat head is secretly hollow: a fixed main void plus a tunable trim
  void, and the balance loop drives cp_trim_x / cp_trim_d until the
  plastic body's CoM sits on the journal axis. The "heavy" side is the
  hollow one - the illusion inverts.

Live parameters: cp_r_tail (pod radius), cp_trim_x, cp_trim_d (balance
knobs), cp_pip_foot (anti-fuse chamfer). Everything else fixed art.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": ["cp_r_tail", "cp_trim_x", "cp_trim_d", "cp_pip_foot"],
}
INTERFERENCE_ALLOWED = []

# Fixed art constants (cm).
T = 0.9
TAIL_T = 0.5
HUB_R = 1.5
HEAD_X = 2.4
HEAD_R = 1.8
JR = 1.1
JD = 0.12
CLR = 0.025
TAIL_TH0, TAIL_TH1 = 130.0, 250.0
ROOT_RIN, ROOT_ROUT = 1.2, 3.7
TIP_RIN, TIP_ROUT = 2.75, 3.25
POD_D = 1.8
VOID_MAIN_D = 1.9   # fixed main head void (2.1 made the body tail-heavy
                    # across the whole trim range - measured attempt 3)
VOID_MAIN_X = 2.4
VOID_FLOOR = 0.12
VOID_H = 0.66       # void z 1.2 - 7.8 mm; roof 1.2 mm
PLA_RHO = 1.24
C160 = math.cos(math.radians(160))
S160 = math.sin(math.radians(160))
C200 = math.cos(math.radians(200))
S200 = math.sin(math.radians(200))


def _fix_sketch(sk):
    for c in sk.sketchCurves:
        adsk.doEvents()
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        adsk.doEvents()
        if sp.isFullyConstrained or sp.isFixed:
            continue
        sp.isFixed = True


def _journal_polyline(sk, pt, base_r):
    mpts = [
        (0.0, 0.0), (base_r, 0.0), (base_r, T / 3),
        (base_r + JD, T / 2), (base_r, 2 * T / 3),
        (base_r, T), (0.0, T),
    ]
    spts = [sk.modelToSketchSpace(pt(x, 0, z)) for x, z in mpts]
    lines = sk.sketchCurves.sketchLines
    first = lines.addByTwoPoints(spts[0], spts[1])
    prev = first
    for i in range(2, len(spts)):
        adsk.doEvents()
        prev = lines.addByTwoPoints(prev.endSketchPoint, spts[i])
    return lines.addByTwoPoints(prev.endSketchPoint,
                                first.startSketchPoint)


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs

    up.add("cp_r_tail", cbs("28 mm"), "mm", "pod centre radius")
    up.add("cp_trim_x", cbs("27.5 mm"), "mm", "trim void x (balance)")
    up.add("cp_trim_d", cbs("16 mm"), "mm", "trim void dia (balance)")
    up.add("cp_pip_foot", cbs("0.3 mm"), "mm", "anti-fuse gap chamfer")
    print("FH params added")

    # ---- hub + head ----------------------------------------------------
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.name = "hub_head"
    ctx.bound_circle(sk, (0, 0, 0), HUB_R, "30 mm",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(sk, (HEAD_X, 0, 0), HEAD_R, "36 mm",
                     x_pos="24 mm", v_pos="0 mm")

    def main_ok(b):
        return b.boundingBox.maxPoint.z > 0.85 and 10.0 < b.volume < 16.0

    f, body = ctx.checked_newbody(ctx.all_profiles(sk), "9 mm",
                                  main_ok, "comet_main")
    f.name = "hub_head_extrude"
    body.name = "comet_body"

    # ---- tail blade ----------------------------------------------------
    skt = root.sketches.add(root.xYConstructionPlane)
    skt.name = "tail_blade"
    n_pts = 13
    outer = adsk.core.ObjectCollection.create()
    inner_rev = []
    for i in range(n_pts):
        t = i / (n_pts - 1.0)
        th = math.radians(TAIL_TH0 + t * (TAIL_TH1 - TAIL_TH0))
        r_in = ROOT_RIN + t * (TIP_RIN - ROOT_RIN)
        r_out = ROOT_ROUT + t * (TIP_ROUT - ROOT_ROUT)
        outer.add(skt.modelToSketchSpace(
            pt(r_out * math.cos(th), r_out * math.sin(th), 0)))
        inner_rev.append(skt.modelToSketchSpace(
            pt(r_in * math.cos(th), r_in * math.sin(th), 0)))
    inner = adsk.core.ObjectCollection.create()
    for p in reversed(inner_rev):  # fusionhelper: allow R11 — collection add, not a document mutation
        inner.add(p)
    spl = skt.sketchCurves.sketchFittedSplines
    sp_out = spl.add(outer)
    sp_in = spl.add(inner)
    tl = skt.sketchCurves.sketchLines
    tl.addByTwoPoints(sp_out.endSketchPoint, sp_in.startSketchPoint)
    tl.addByTwoPoints(sp_in.endSketchPoint, sp_out.startSketchPoint)
    _fix_sketch(skt)
    if skt.profiles.count != 1:
        raise RuntimeError("blade profiles %d" % skt.profiles.count)
    v0 = body.volume
    fb = ctx.checked_join(ctx.all_profiles(skt), "5 mm", body,
                          lambda b: b.volume - v0 > 3.0, "blade")
    fb.name = "tail_blade_extrude"

    # ---- pods (positions driven by cp_r_tail, azimuths 160/200) -------
    skp = root.sketches.add(root.xYConstructionPlane)
    skp.name = "tail_pods"
    ctx.bound_circle(skp, (2.8 * C160, 2.8 * S160, 0), POD_D / 2, "18 mm",
                     x_pos="cp_r_tail * %.5f" % abs(C160),
                     v_pos="cp_r_tail * %.5f" % abs(S160))
    ctx.bound_circle(skp, (2.8 * C200, 2.8 * S200, 0), POD_D / 2, "18 mm",
                     x_pos="cp_r_tail * %.5f" % abs(C200),
                     v_pos="cp_r_tail * %.5f" % abs(S200))
    v1 = body.volume
    fp = ctx.checked_join(ctx.all_profiles(skp), "9 mm", body,
                          lambda b: b.volume - v1 > 1.5, "pods")
    fp.name = "pod_extrude"
    print("FH body assembled vol: %.3f" % body.volume)

    # ---- journal cavity ------------------------------------------------
    skj = root.sketches.add(root.xZConstructionPlane)
    skj.name = "journal_cavity"
    axis_ln = _journal_polyline(skj, pt, JR + CLR)
    _fix_sketch(skj)
    if skj.profiles.count != 1:
        raise RuntimeError("cavity profiles %d" % skj.profiles.count)
    v2 = body.volume
    rev = root.features.revolveFeatures
    rinp = rev.createInput(skj.profiles.item(0), axis_ln,
                           ctx.ops.CutFeatureOperation)
    rinp.setAngleExtent(False, cbs("360 deg"))
    rinp.participantBodies = [body]
    rf = rev.add(rinp)
    rf.name = "journal_cavity_cut"
    if v2 - body.volume < 3.0:
        raise RuntimeError("cavity removed %.3f" % (v2 - body.volume))

    # ---- head voids (sealed; main fixed + tunable trim) ---------------
    plv = ctx.plane_at_z("1.2 mm", "void_floor_plane")
    skv = root.sketches.add(plv)
    skv.name = "head_voids"
    ctx.bound_circle(skv, (VOID_MAIN_X, 0, VOID_FLOOR), VOID_MAIN_D / 2,
                     "19 mm", x_pos="24 mm", v_pos="0 mm")
    ctx.bound_circle(skv, (3.4, 0, VOID_FLOOR), 0.6, "cp_trim_d",
                     x_pos="cp_trim_x", v_pos="0 mm")
    fv = ctx.blind_cut(ctx.all_profiles(skv), "6.6 mm", [body],
                       "voids", min_vol_cm3=1.5)
    fv.name = "head_void_cut"
    print("FH voids cut, vol: %.3f" % body.volume)

    # ---- balance loop: bisection on trim_x ----------------------------
    # com.x is monotone-decreasing in trim_x (moving the void outward
    # removes mass at larger x), even where the trim void overlaps the
    # main void, so bisection is overlap-proof. Newton on an analytic
    # mass model oscillated (measured attempt 1): the model ignored the
    # void-union overlap AND its x_min let the void eat the journal wall.
    # Bracket keeps the void 1 mm clear of the journal (r 1.245) and
    # 2 mm inside the head edge (x 4.2).
    acc = adsk.fusion.CalculationAccuracy.HighCalculationAccuracy

    def measure():
        adsk.doEvents()
        b = root.bRepBodies.itemByName("comet_body")
        props = b.getPhysicalProperties(acc)
        com = props.centerOfMass
        return com.x, com.y, props.volume * PLA_RHO

    def set_x(x):
        up.itemByName("cp_trim_x").expression = "%.4f mm" % (x * 10)

    def set_d(d):
        up.itemByName("cp_trim_d").expression = "%.4f mm" % (d * 10)

    # Outer search over trim diameter: measured attempt 2 showed the body
    # can be tail-heavy across the whole x range at d=16 (voids remove
    # too much head mass without tail steel) - shrink d until the
    # bracket straddles zero, then bisect x.
    lo = hi = 0.0
    fx_lo = fx_hi = 0.0
    bracketed = False
    for d_try in (1.6, 1.4, 1.2, 1.0, 0.8):
        adsk.doEvents()
        set_d(d_try)
        lo = 1.35 + d_try / 2 + 0.1   # journal wall + margin
        hi = 4.0 - d_try / 2          # head edge - wall
        set_x(lo)
        fx_lo, _, _ = measure()
        set_x(hi)
        fx_hi, _, _ = measure()
        print("FH bracket d=%.2f lo=%.3f(%.4f) hi=%.3f(%.4f)"
              % (d_try, lo, fx_lo, hi, fx_hi))
        if fx_lo > 0 and fx_hi < 0:
            bracketed = True
            break
    if not bracketed:
        raise RuntimeError(
            "no root at any trim diameter (last lo=%.4f hi=%.4f)"
            % (fx_lo, fx_hi))
    cx, cy, m_b = fx_hi, 0.0, 0.0
    x = hi
    for it in range(12):
        adsk.doEvents()
        if abs(cx) * 10.0 < 0.03:
            break
        x = (lo + hi) / 2.0
        set_x(x)
        cx, cy, m_b = measure()
        print("FH bisect it%d: x=%.4f com=(%.4f,%.4f) m_b=%.1fg"
              % (it, x, cx, cy, m_b))
        if cx > 0:
            lo = x
        else:
            hi = x
    resid_mm = math.hypot(cx, cy) * 10.0
    print("FH BALANCE final resid_mm=%.4f at trim_x=%.4f" % (resid_mm, x))
    if resid_mm >= 0.1:
        raise RuntimeError("balance did not converge: %.4f mm" % resid_mm)

    # ---- stator --------------------------------------------------------
    body = root.bRepBodies.itemByName("comet_body")
    sks = root.sketches.add(root.xZConstructionPlane)
    sks.name = "stator_profile"
    axis_s = _journal_polyline(sks, pt, JR)
    _fix_sketch(sks)
    if sks.profiles.count != 1:
        raise RuntimeError("stator profiles %d" % sks.profiles.count)
    rinp3 = rev.createInput(sks.profiles.item(0), axis_s,
                            ctx.ops.NewBodyFeatureOperation)
    rinp3.setAngleExtent(False, cbs("360 deg"))
    rf3 = rev.add(rinp3)
    rf3.name = "stator_revolve"
    stator = rf3.bodies.item(0)
    stator.name = "pip_stator"
    if not (3.0 < stator.volume < 4.5):
        raise RuntimeError("stator vol %.3f" % stator.volume)

    # ---- anti-fuse chamfers at the PiP gap ----------------------------
    chf = root.features.chamferFeatures
    out = adsk.core.ObjectCollection.create()
    for bod, lo, hi in ((body, 1.05, 1.20), (stator, 1.02, 1.18)):
        for e in bod.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            g = e.geometry
            r = getattr(g, "radius", None)
            if r is None or not (lo < r < hi):
                continue
            bb = e.boundingBox
            if (abs(bb.maxPoint.z - bb.minPoint.z) < 0.02 and
                    abs(bb.minPoint.z) < 0.02):
                out.add(e)
    if out.count != 2:
        raise RuntimeError("pip gap edges %d != 2" % out.count)
    ci = chf.createInput2()
    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        out, cbs("cp_pip_foot"), True)
    cf = chf.add(ci)
    cf.name = "pip_gap_foot_chamfer"

    print("FH BUILD OK: comet %.3f + stator %.3f cm3, %d bodies, "
          "resid %.4f mm"
          % (body.volume, stator.volume, root.bRepBodies.count, resid_mm))
