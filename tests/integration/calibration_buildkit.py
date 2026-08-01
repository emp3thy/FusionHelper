"""Live calibration for the buildkit (run bundled, against real Fusion,
in a scratch document - NOT part of the pytest suite).

Builds: 40x30x3 plate, one 4mm through-hole patterned x3, one joined
boss, then prints the marker line the runner greps for."""
FH_ATTEMPT = 1
FH_OPTS = {"liveness": False}

import adsk.core
import adsk.fusion

from fusionhelper.buildkit import *


def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    if ctx.up.itemByName("cal_w") is None:
        ctx.up.add("cal_w", ctx.cbs("40 mm"), "mm", "calibration plate")
    front = ctx.plane_at_z("0 mm", "cal_front")
    sk = ctx.root.sketches.add(front)
    sk.name = "cal_plate"
    ctx.bound_rect2(sk, (2.0, 1.5, 0), 2.0, 1.5,
                    u_size="cal_w", v_size="30 mm",
                    u_pos=("cal_w / 2", "cal_w / 2"),
                    v_pos=("15 mm", "15 mm"))
    feat, plate = ctx.checked_newbody(
        ctx.all_profiles(sk), "3 mm",
        lambda b: b.boundingBox.minPoint.z < -0.01, "cal_plate")
    plate.name = "cal_plate"
    sk = ctx.root.sketches.add(front)
    sk.name = "cal_hole"
    ctx.bound_circle(sk, (1.0, 1.5, 0), 0.2, "4 mm",
                     x_pos="10 mm", v_pos="15 mm")
    cut = ctx.sym_cut(ctx.all_profiles(sk), "10 mm", [plate])
    ctx.pattern_cut([cut], ctx.x_axis, "3", "10 mm", [plate],
                    min_vol_cm3=2 * 0.03)
    sk = ctx.root.sketches.add(front)
    sk.name = "cal_boss"
    ctx.bound_circle(sk, (3.5, 2.5, 0), 0.3, "6 mm",
                     x_pos="35 mm", v_pos="25 mm")
    ctx.checked_join(ctx.all_profiles(sk), "5 mm", plate,
                     lambda b: b.boundingBox.maxPoint.z > 0.01, "cal_boss")
    print("buildkit calibration: plate + 3 holes + boss, vol %.3f cm3"
          % plate.volume)
