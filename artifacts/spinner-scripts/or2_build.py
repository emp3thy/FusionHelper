"""ORRERY mk2 - stator sun pillar + rotor ring, both on the build plate.

The mk1 rotor's hub tier floated 9 mm above the plate because the
rotating interface was horizontal. Here it is vertical: the stator is a
central sun pillar standing on the plate, the rotor is an outer ring
standing on the plate, and six planets stand between them. Nothing is
unanchored at any height.

The planets are located by their two meshes and retained axially by a
mid-height band: each planet bulges 0.5 mm past its tooth tips into
matching recesses in the sun and the ring, with 45-degree cones either
side. Teeth still engage above and below the band - the three-zone stack
the leaderboard designs use.
"""
import math

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import BuildCtx

FH_ATTEMPT = 1
FH_OPTS = {"liveness": False}
INTERFERENCE_ALLOWED = []

MODULE = 0.10
PANG = math.radians(20)
BACKLASH = 0.020
SUN_N, SUN_RP, SUN_TIP, SUN_ROOT = 20, 1.00, 1.10, 0.875
RING_N, RING_RP, RING_TIP, RING_ROOT = 40, 2.00, 1.90, 2.125
GEAR_TOP, H = 1.10, 1.45
SUN_BAND, RING_BAND = 0.83, 2.17
BAND_LO, BAND_MID, BAND_HI = 0.29, 0.56, 0.83
SLOT_RIN, SLOT_ROUT = 2.25, 3.80        # race at r38
RIM_ROUT = 4.50
SLOT_HALF, THROAT_HALF, RAIL_T = 0.35, 0.23, 0.12
VWAY_ZS = (0.45, 1.10)
RIDGE_TIP = 0.26
RIDGE_H = SLOT_HALF - RIDGE_TIP
N_SLOT = 6


def _inv(a):
    return math.tan(a) - a


def _psi(N, rp, r, internal):
    rb = rp * math.cos(PANG)
    ap = math.acos(min(1.0, rb / rp))
    ar = math.acos(min(1.0, rb / max(r, rb)))
    psi_p = math.pi / (2 * N) - BACKLASH / (2 * rp)
    if internal:
        return psi_p - _inv(ap) + _inv(ar)
    return psi_p + _inv(ap) - _inv(ar)


def tooth_space(N, rp, r_tip, r_root, internal):
    half = math.pi / N
    lo, hi = (r_tip, r_root) if internal else (r_root, r_tip)
    rs = [lo, (lo + hi) / 2, hi]
    pts = []
    for r in rs:
        a = half - _psi(N, rp, r, internal)
        pts.append((r * math.cos(a), r * math.sin(a)))
    for r in reversed(rs):
        a = -(half - _psi(N, rp, r, internal))
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def _fix(sk):
    for c in sk.sketchCurves:
        if not c.isFixed:
            c.isFixed = True
    for sp in sk.sketchPoints:
        if not (sp.isFullyConstrained or sp.isFixed):
            sp.isFixed = True
    adsk.doEvents()


def _poly_xy(sk, pt, pts, z):
    sp = [sk.modelToSketchSpace(pt(x, y, z)) for x, y in pts]
    ln = sk.sketchCurves.sketchLines
    first = ln.addByTwoPoints(sp[0], sp[1])
    prev = first
    for i in range(2, len(sp)):
        prev = ln.addByTwoPoints(prev.endSketchPoint, sp[i])
    ln.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)


def _poly_rz(sk, pt, rz):
    sp = [sk.modelToSketchSpace(pt(r, 0, z)) for r, z in rz]
    ln = sk.sketchCurves.sketchLines
    first = ln.addByTwoPoints(sp[0], sp[1])
    prev = first
    for i in range(2, len(sp)):
        prev = ln.addByTwoPoints(prev.endSketchPoint, sp[i])
    ln.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    adsk.doEvents()


def _fixed_rect(sk, pt, x0, y0, x1, y1, z):
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        sk.modelToSketchSpace(pt(x0, y0, z)),
        sk.modelToSketchSpace(pt(x1, y1, z)))


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    root = ctx.root
    up = ctx.up
    pt = ctx.pt
    cbs = ctx.cbs
    rev = root.features.revolveFeatures
    cpats = root.features.circularPatternFeatures
    popts = adsk.fusion.PatternComputeOptions
    healthy = (adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,
               adsk.fusion.FeatureHealthStates.WarningFeatureHealthState)

    for nm, val, desc in (("o2_gear_top", "11 mm", "gear band top"),
                          ("o2_roll_d", "6 mm", "roller dia"),
                          ("o2_stub_d", "3.4 mm", "roller stub dia"),
                          ("o2_fuse_ch", "0.3 mm", "anti-fuse chamfer")):
        if up.itemByName(nm) is None:
            up.add(nm, cbs(val), "mm", desc)

    def pattern(feats, n, watch, min_dv, name, cut=True):
        v0 = sum(b.volume for b in watch)
        coll = adsk.core.ObjectCollection.create()
        for f in feats:  # fusionhelper: allow R11 — collection add, not a document mutation
            coll.add(f)
        pin = cpats.createInput(coll, root.zConstructionAxis)
        pin.quantity = cbs(str(n))
        pin.totalAngle = cbs("360 deg")
        pin.isSymmetric = False
        pin.patternComputeOption = popts.AdjustPatternCompute  # pyright: ignore[reportAttributeAccessIssue]
        pf = cpats.add(pin)
        dv = v0 - sum(b.volume for b in watch)
        if pf.healthState not in healthy or (dv if cut else -dv) < min_dv:
            raise RuntimeError("%s pattern dv=%.4f" % (name, dv))
        pf.name = name
        return pf

    # ================= STATOR: sun pillar =============================
    sks = root.sketches.add(root.xZConstructionPlane)
    sks.name = "sun_profile"
    _poly_rz(sks, pt, [
        (0.0, 0.0), (SUN_TIP, 0.0),
        (SUN_TIP, BAND_LO), (SUN_BAND, BAND_MID), (SUN_TIP, BAND_HI),
        (SUN_TIP, GEAR_TOP), (SUN_ROOT, GEAR_TOP), (SUN_ROOT, H), (0.0, H),
    ])
    _fix(sks)
    if sks.profiles.count != 1:
        raise RuntimeError("sun profiles %d" % sks.profiles.count)
    rin = rev.createInput(sks.profiles.item(0), root.zConstructionAxis,
                          ctx.ops.NewBodyFeatureOperation)
    rin.setAngleExtent(False, cbs("360 deg"))
    fs = rev.add(rin)
    fs.name = "sun_revolve"
    stator = fs.bodies.item(0)
    stator.name = "o2_stator"

    skt = root.sketches.add(root.xYConstructionPlane)
    skt.name = "sun_tooth_space"
    _poly_xy(skt, pt, tooth_space(SUN_N, SUN_RP, SUN_TIP, SUN_ROOT, False),
             0.0)
    _fix(skt)
    fcut = ctx.blind_cut(ctx.all_profiles(skt), "o2_gear_top", [stator],
                         "sun_tooth", min_vol_cm3=0.0005)
    fcut.name = "sun_tooth_cut"
    pattern([fcut], SUN_N, [stator], 0.05, "sun_tooth_pattern")
    print("FH stator (sun pillar) %.3f cm3" % stator.volume)

    # ================= ROTOR: ring + outer band =======================
    skr = root.sketches.add(root.xZConstructionPlane)
    skr.name = "ring_profile"
    _poly_rz(skr, pt, [
        (RING_TIP, 0.0), (RIM_ROUT, 0.0), (RIM_ROUT, H),
        (RING_ROOT, H), (RING_ROOT, GEAR_TOP),
        (RING_TIP, GEAR_TOP), (RING_TIP, BAND_HI),
        (RING_BAND, BAND_MID), (RING_TIP, BAND_LO),
    ])
    _fix(skr)
    if skr.profiles.count != 1:
        raise RuntimeError("ring profiles %d" % skr.profiles.count)
    rin2 = rev.createInput(skr.profiles.item(0), root.zConstructionAxis,
                           ctx.ops.NewBodyFeatureOperation)
    rin2.setAngleExtent(False, cbs("360 deg"))
    fr = rev.add(rin2)
    fr.name = "ring_revolve"
    rotor = fr.bodies.item(0)
    rotor.name = "o2_rotor"

    skrt = root.sketches.add(root.xYConstructionPlane)
    skrt.name = "ring_tooth_space"
    _poly_xy(skrt, pt,
             tooth_space(RING_N, RING_RP, RING_TIP, RING_ROOT, True), 0.0)
    _fix(skrt)
    frc = ctx.blind_cut(ctx.all_profiles(skrt), "o2_gear_top", [rotor],
                        "ring_tooth", min_vol_cm3=0.0005)
    frc.name = "ring_tooth_cut"
    pattern([frc], RING_N, [rotor], 0.10, "ring_tooth_pattern")
    print("FH rotor ring %.3f cm3" % rotor.volume)

    # ---- roller slots, open top, throat, twin V-ways ------------------
    plc = ctx.plane_at_z("1.2 mm", "cavity_plane")
    skc = root.sketches.add(plc)
    skc.name = "slot_seed"
    _fixed_rect(skc, pt, -SLOT_HALF, SLOT_RIN, SLOT_HALF, SLOT_ROUT, RAIL_T)
    _fix(skc)
    fslot = ctx.blind_cut(ctx.all_profiles(skc), "14.5 mm - 1.2 mm",
                          [rotor], "slot", min_vol_cm3=1.0)
    fslot.name = "slot_seed_cut"

    skth = root.sketches.add(root.xYConstructionPlane)
    skth.name = "throat_seed"
    _fixed_rect(skth, pt, -THROAT_HALF, SLOT_RIN, THROAT_HALF,
                SLOT_ROUT, 0.0)
    _fix(skth)
    fthr = ctx.blind_cut(ctx.all_profiles(skth), "1.2 mm", [rotor],
                         "throat", min_vol_cm3=0.03)
    fthr.name = "throat_seed_cut"

    skv = root.sketches.add(root.xZConstructionPlane)
    skv.name = "vway_ridge"
    for zc in VWAY_ZS:
        for sgn in (1, -1):
            tri = [(sgn * SLOT_HALF, zc - RIDGE_H),
                   (sgn * RIDGE_TIP, zc),
                   (sgn * SLOT_HALF, zc + RIDGE_H)]
            sp = [skv.modelToSketchSpace(pt(x, 0, z)) for x, z in tri]
            vl = skv.sketchCurves.sketchLines
            a = vl.addByTwoPoints(sp[0], sp[1])
            b = vl.addByTwoPoints(a.endSketchPoint, sp[2])
            vl.addByTwoPoints(b.endSketchPoint, a.startSketchPoint)
    _fix(skv)
    if skv.profiles.count != 4:
        raise RuntimeError("vway profiles %d != 4" % skv.profiles.count)
    v1 = rotor.volume
    vin = ctx.extrudes.createInput(ctx.all_profiles(skv),
                                   ctx.ops.JoinFeatureOperation)
    vin.startExtent = adsk.fusion.OffsetStartDefinition.create(
        cbs("22.5 mm"))
    vex = adsk.fusion.DistanceExtentDefinition.create(cbs("15.5 mm"))
    vin.setOneSideExtent(vex, ctx.dirs.PositiveExtentDirection)
    vin.participantBodies = [rotor]
    fv = ctx.extrudes.add(vin)
    fv.name = "vway_ridge_extrude"
    if rotor.volume - v1 < 0.01:
        raise RuntimeError("vway added %.4f" % (rotor.volume - v1))

    pattern([fslot, fthr], N_SLOT, [rotor], 4.0, "slot_pattern")
    pattern([fv], N_SLOT, [rotor], 0.04, "vway_pattern", cut=False)

    print("FH BUILD OK: stator %.3f rotor %.3f cm3, %d bodies"
          % (stator.volume, rotor.volume, root.bRepBodies.count))
