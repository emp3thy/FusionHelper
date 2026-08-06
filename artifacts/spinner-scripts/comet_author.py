"""Counterfeit Comet - asymmetric-looking, CoM-nulled fidget spinner.

One heavy head lobe (R18 at x=24), a tapering swept tail blade (arc
centerline r=30, 130-250 deg) with two pod "knots", three hidden M8 nut
pockets. The nut radii cc_r_head / cc_r_tail are live parameters; the
script closes with an analytic balance loop that drives them until the
combined CoM (PLA body + 3 steel nuts) sits on the bearing axis.

Deviations from the paper spec, deliberate:
- nut pockets are circular (dia 15.7 = hex corner circle + clearance),
  not hex - lets the pocket position be dimension-driven for nulling;
- pocket stack corrected to floor 1.2 + void 6.8 + roof 1.0 = 9.0
  (spec's 1.2+7.0+1.0 = 9.2 overflows the body);
- BB trim ring and button dish omitted from v1 (post-print tuning aids);
- head/hub blend fillets omitted from v1 (overlapping-circle union).
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {
    "only_params": [
        "cc_t", "cc_tail_t", "cc_hub_d", "cc_lip_id", "cc_seat_d",
        "cc_seat_floor", "cc_seat_depth", "cc_lead", "cc_foot",
        "cc_pocket_floor", "cc_pocket_h", "cc_pocket_d",
        "cc_r_head", "cc_r_tail", "cc_stub_d",
    ],
}
INTERFERENCE_ALLOWED = []

# Fixed art constants (cm).
HEAD_X = 2.4        # head circle centre
HEAD_R = 1.8        # head circle radius
TAIL_CL_R = 3.0     # tail centreline radius (for pod azimuths)
TAIL_TH0 = 130.0    # tail root azimuth (deg)
TAIL_TH1 = 250.0    # tail tip azimuth (deg)
ROOT_RIN = 1.2      # blade inner radius at root (inside hub - attaches)
ROOT_ROUT = 3.7
TIP_RIN = 2.75
TIP_ROUT = 3.25
POD_AZ = (170.0, 210.0)
POD_D = 1.8         # pod boss dia (cm)
NUT_MASS = 5.4      # g, M8 DIN 934
PLA_RHO = 1.24      # g/cm3
BTN_Y = 6.0         # button placement row


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


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs

    # ---- parameter table first ----------------------------------------
    up.add("cc_t", cbs("9 mm"), "mm", "body thickness")
    up.add("cc_tail_t", cbs("5 mm"), "mm", "tail blade thickness")
    up.add("cc_hub_d", cbs("30 mm"), "mm", "hub boss dia")
    up.add("cc_lip_id", cbs("19.5 mm"), "mm", "bearing retaining lip ID")
    up.add("cc_seat_d", cbs("21.85 mm"), "mm", "608 seat dia (PLA)")
    up.add("cc_seat_floor", cbs("1 mm"), "mm", "seat lip height")
    up.add("cc_seat_depth", cbs("7 mm"), "mm", "seat height (608 width)")
    up.add("cc_lead", cbs("0.5 mm"), "mm", "bore lead chamfer")
    up.add("cc_foot", cbs("0.5 mm"), "mm", "elephant-foot chamfer")
    up.add("cc_pocket_floor", cbs("1.2 mm"), "mm", "nut pocket floor")
    up.add("cc_pocket_h", cbs("6.8 mm"), "mm", "nut pocket void height")
    up.add("cc_pocket_d", cbs("15.7 mm"), "mm", "nut pocket dia")
    up.add("cc_r_head", cbs("26 mm"), "mm", "head nut radius (balance)")
    up.add("cc_r_tail", cbs("28 mm"), "mm", "tail nut radius (balance)")
    up.add("cc_stub_d", cbs("8.1 mm"), "mm", "button stub dia")
    print("FH params added")

    c170, s170 = math.cos(math.radians(170)), math.sin(math.radians(170))
    c210, s210 = math.cos(math.radians(210)), math.sin(math.radians(210))

    # ---- main silhouette: hub + head (overlapping circles) ------------
    sk = root.sketches.add(root.xYConstructionPlane)
    sk.name = "hub_head"
    ctx.bound_circle(sk, (0, 0, 0), 1.5, "cc_hub_d",
                     x_pos="0 mm", v_pos="0 mm")
    ctx.bound_circle(sk, (HEAD_X, 0, 0), HEAD_R, "36 mm",
                     x_pos="24 mm", v_pos="0 mm")

    def main_ok(b):
        bb = b.boundingBox
        return bb.maxPoint.z > 0.85 and 10.0 < b.volume < 16.0

    f, body = ctx.checked_newbody(ctx.all_profiles(sk), "cc_t",
                                  main_ok, "comet_main")
    f.name = "hub_head_extrude"
    body.name = "comet_body"
    print("FH main vol: %.3f" % body.volume)

    # ---- tail blade (fixed-art splines, root buried in the hub) -------
    skt = root.sketches.add(root.xYConstructionPlane)
    skt.name = "tail_blade"
    n_pts = 13
    outer_pts = adsk.core.ObjectCollection.create()
    inner_pts = adsk.core.ObjectCollection.create()
    for i in range(n_pts):
        t = i / (n_pts - 1.0)
        th = math.radians(TAIL_TH0 + t * (TAIL_TH1 - TAIL_TH0))
        r_in = ROOT_RIN + t * (TIP_RIN - ROOT_RIN)
        r_out = ROOT_ROUT + t * (TIP_ROUT - ROOT_ROUT)
        outer_pts.add(skt.modelToSketchSpace(
            pt(r_out * math.cos(th), r_out * math.sin(th), 0)))
        inner_pts.add(skt.modelToSketchSpace(
            pt(r_in * math.cos(th), r_in * math.sin(th), 0)))
    # inner spline reversed so the loop chains tip -> root
    inner_rev = adsk.core.ObjectCollection.create()
    for i in range(n_pts - 1, -1, -1):  # fusionhelper: allow R11 — collection add, not a document mutation
        inner_rev.add(inner_pts.item(i))
    spl = skt.sketchCurves.sketchFittedSplines
    sp_out = spl.add(outer_pts)
    sp_in = spl.add(inner_rev)
    tl = skt.sketchCurves.sketchLines
    tl.addByTwoPoints(sp_out.endSketchPoint, sp_in.startSketchPoint)
    tl.addByTwoPoints(sp_in.endSketchPoint, sp_out.startSketchPoint)
    _fix_sketch(skt)
    if skt.profiles.count != 1:
        raise RuntimeError("blade profiles %d != 1" % skt.profiles.count)
    v0 = body.volume
    fb = ctx.checked_join(ctx.all_profiles(skt), "cc_tail_t", body,
                          lambda b: b.volume - v0 > 3.0, "blade")
    fb.name = "tail_blade_extrude"
    print("FH blade vol: %.3f" % body.volume)

    # ---- pods (knots) on the tail, positions driven by cc_r_tail ------
    skp = root.sketches.add(root.xYConstructionPlane)
    skp.name = "tail_pods"
    ctx.bound_circle(skp, (TAIL_CL_R * c170, TAIL_CL_R * s170, 0),
                     POD_D / 2, "18 mm",
                     x_pos="cc_r_tail * %.5f" % abs(c170),
                     v_pos="cc_r_tail * %.5f" % abs(s170))
    ctx.bound_circle(skp, (TAIL_CL_R * c210, TAIL_CL_R * s210, 0),
                     POD_D / 2, "18 mm",
                     x_pos="cc_r_tail * %.5f" % abs(c210),
                     v_pos="cc_r_tail * %.5f" % abs(s210))
    v1 = body.volume
    fpod = ctx.checked_join(ctx.all_profiles(skp), "cc_t", body,
                            lambda b: b.volume - v1 > 1.5, "pods")
    fpod.name = "pod_extrude"
    print("FH pods vol: %.3f" % body.volume)

    # ---- bearing bore: lip through-bore + internal seat ---------------
    skb = root.sketches.add(root.xYConstructionPlane)
    skb.name = "lip_bore"
    circ = skb.sketchCurves.sketchCircles.addByCenterRadius(
        pt(0.05, 0.08, 0), 0.975)
    skb.geometricConstraints.addCoincident(
        circ.centerSketchPoint, skb.originPoint)
    dd = skb.sketchDimensions.addDiameterDimension(circ, pt(1.6, -1.6, 0))
    dd.parameter.expression = "cc_lip_id"
    fb2 = ctx.blind_cut(ctx.all_profiles(skb), "cc_t + 1 mm", [body],
                        "bore", min_vol_cm3=2.0)
    fb2.name = "lip_bore_cut"

    pls = ctx.plane_at_z("cc_seat_floor", "seat_floor_plane")
    sks = root.sketches.add(pls)
    sks.name = "seat"
    circ2 = sks.sketchCurves.sketchCircles.addByCenterRadius(
        pt(0.06, 0.09, 0), 1.0925)
    sks.geometricConstraints.addCoincident(
        circ2.centerSketchPoint, sks.originPoint)
    dd2 = sks.sketchDimensions.addDiameterDimension(circ2, pt(1.7, -1.7, 0))
    dd2.parameter.expression = "cc_seat_d"
    fs = ctx.blind_cut(ctx.all_profiles(sks), "cc_seat_depth", [body],
                       "seat", min_vol_cm3=0.3)
    fs.name = "seat_cut"
    print("FH bore+seat vol: %.3f" % body.volume)

    # ---- nut pockets (positions driven by the balance parameters) -----
    plp = ctx.plane_at_z("cc_pocket_floor", "pocket_floor_plane")
    skn = root.sketches.add(plp)
    skn.name = "nut_pockets"
    ctx.bound_circle(skn, (2.6, 0, 0.12), 0.785, "cc_pocket_d",
                     x_pos="cc_r_head", v_pos="0 mm")
    ctx.bound_circle(skn, (2.8 * c170, 2.8 * s170, 0.12), 0.785,
                     "cc_pocket_d",
                     x_pos="cc_r_tail * %.5f" % abs(c170),
                     v_pos="cc_r_tail * %.5f" % abs(s170))
    ctx.bound_circle(skn, (2.8 * c210, 2.8 * s210, 0.12), 0.785,
                     "cc_pocket_d",
                     x_pos="cc_r_tail * %.5f" % abs(c210),
                     v_pos="cc_r_tail * %.5f" % abs(s210))
    fn = ctx.blind_cut(ctx.all_profiles(skn), "cc_pocket_h", [body],
                       "pockets", min_vol_cm3=3.0)
    fn.name = "nut_pocket_cut"
    print("FH pockets vol: %.3f" % body.volume)

    # ---- chamfers ------------------------------------------------------
    chf = root.features.chamferFeatures

    def bore_edges():
        out = adsk.core.ObjectCollection.create()
        for e in body.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            g = e.geometry
            r = getattr(g, "radius", None)
            if r is None or not (0.93 < r < 1.02):
                continue
            bb = e.boundingBox
            if (abs(bb.maxPoint.z - bb.minPoint.z) < 0.02 and
                    (abs(bb.minPoint.z) < 0.02 or
                     abs(bb.maxPoint.z - 0.9) < 0.02)):
                out.add(e)
        return out

    be = bore_edges()
    if be.count != 2:
        raise RuntimeError("bore edge count %d != 2" % be.count)
    cinp = chf.createInput2()
    cinp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        be, cbs("cc_lead"), True)
    cf = chf.add(cinp)
    cf.name = "bore_lead_chamfer"

    def foot_edges():
        out = adsk.core.ObjectCollection.create()
        for e in body.edges:  # fusionhelper: allow R11 — collection add, not a document mutation
            bb = e.boundingBox
            if abs(bb.minPoint.z) > 0.02 or abs(bb.maxPoint.z) > 0.02:
                continue
            g = e.geometry
            r = getattr(g, "radius", None)
            if r is not None and 0.93 < r < 1.02:
                continue  # bore lip already chamfered
            out.add(e)
        return out

    fe = foot_edges()
    if fe.count < 3:
        raise RuntimeError("foot edge count %d < 3" % fe.count)
    cinp2 = chf.createInput2()
    cinp2.chamferEdgeSets.addEqualDistanceChamferEdgeSet(
        fe, cbs("cc_foot"), True)
    cf2 = chf.add(cinp2)
    cf2.name = "foot_chamfer"
    print("FH chamfers vol: %.3f" % body.volume)

    # ---- balance nulling loop -----------------------------------------
    acc = adsk.fusion.CalculationAccuracy.HighCalculationAccuracy
    resid_mm = None
    for it in range(6):
        adsk.doEvents()
        b = root.bRepBodies.itemByName("comet_body")
        props = b.getPhysicalProperties(acc)
        com = props.centerOfMass
        m_b = props.volume * PLA_RHO
        r_h = up.itemByName("cc_r_head").value
        r_t = up.itemByName("cc_r_tail").value
        mx = m_b * com.x + NUT_MASS * (r_h + r_t * (c170 + c210))
        my = m_b * com.y + NUT_MASS * (r_t * (s170 + s210))
        m_tot = m_b + 3 * NUT_MASS
        resid_mm = math.hypot(mx, my) / m_tot * 10.0
        print("FH balance it%d: m_b=%.1fg com=(%.4f,%.4f)cm "
              "r_h=%.2f r_t=%.2f resid=%.4f mm"
              % (it, m_b, com.x, com.y, r_h, r_t, resid_mm))
        if resid_mm < 0.05:
            break
        r_t_new = m_b * com.y / (-(s170 + s210) * NUT_MASS)
        r_t_new = min(2.95, max(2.4, r_t_new))
        r_h_new = (-(c170 + c210) * r_t_new * NUT_MASS
                   - m_b * com.x) / NUT_MASS
        r_h_new = min(3.2, max(2.05, r_h_new))
        up.itemByName("cc_r_tail").expression = "%.4f mm" % (r_t_new * 10)
        up.itemByName("cc_r_head").expression = "%.4f mm" % (r_h_new * 10)
    print("FH BALANCE final resid_mm=%.4f" % resid_mm)

    # ---- grip buttons (printed separately, placed clear) --------------
    body = root.bRepBodies.itemByName("comet_body")
    skc = root.sketches.add(root.xYConstructionPlane)
    skc.name = "button_discs"
    ctx.bound_circle(skc, (6.0, BTN_Y, 0), 1.4, "28 mm",
                     x_pos="60 mm", v_pos="60 mm")
    ctx.bound_circle(skc, (-6.0, BTN_Y, 0), 1.4, "28 mm",
                     x_pos="60 mm", v_pos="60 mm")
    dinp = ctx.extrudes.createInput(ctx.all_profiles(skc),
                                    ctx.ops.NewBodyFeatureOperation)
    ext = adsk.fusion.DistanceExtentDefinition.create(cbs("3.5 mm"))
    dinp.setOneSideExtent(ext, ctx.dirs.PositiveExtentDirection)
    fbtn = ctx.extrudes.add(dinp)
    fbtn.name = "button_discs_extrude"
    btns = [fbtn.bodies.item(i) for i in range(fbtn.bodies.count)]
    if len(btns) != 2:
        raise RuntimeError("expected 2 buttons, got %d" % len(btns))
    btns[0].name = "button_a"
    btns[1].name = "button_b"

    plb = ctx.plane_at_z("3.5 mm", "button_stub_plane")
    skst = root.sketches.add(plb)
    skst.name = "button_stubs"
    ctx.bound_circle(skst, (6.0, BTN_Y, 0.35), 0.405, "cc_stub_d",
                     x_pos="60 mm", v_pos="60 mm")
    ctx.bound_circle(skst, (-6.0, BTN_Y, 0.35), 0.405, "cc_stub_d",
                     x_pos="60 mm", v_pos="60 mm")
    vb0 = sum(b.volume for b in btns)
    sinp = ctx.extrudes.createInput(ctx.all_profiles(skst),
                                    ctx.ops.JoinFeatureOperation)
    ext2 = adsk.fusion.DistanceExtentDefinition.create(cbs("4 mm"))
    sinp.setOneSideExtent(ext2, ctx.dirs.PositiveExtentDirection)
    sinp.participantBodies = btns
    fst = ctx.extrudes.add(sinp)
    fst.name = "button_stub_extrude"
    if sum(b.volume for b in btns) - vb0 < 0.2:
        raise RuntimeError("stub join added too little volume")
    print("FH buttons done")

    print("FH BUILD OK: comet %.3f cm3, %d bodies, resid %.4f mm"
          % (body.volume, root.bRepBodies.count, resid_mm))
