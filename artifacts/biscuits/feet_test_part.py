

# ====================== foot socket fit test ============================
# Two pairs of feet, identical except for the socket diameter, to find
# the push fit on the 6.2 mm leg end. 6.5 and 6.4 both printed loose.
# Sole dimples say which is which: 3 dimples = 6.3 mm, 2 dimples = 6.2 mm.

def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    up, cbs = ctx.up, ctx.cbs
    up.add("foot_hole_63", cbs("6.3 mm"), "mm", "socket dia, 3-dimple pair")
    up.add("foot_hole_62", cbs("6.2 mm"), "mm", "socket dia, 2-dimple pair")
    up.add("foot_fillet", cbs("1.2 mm"), "mm", "foot biscuit rim bevel")
    up.add("foot_disc_h", cbs("6 mm"), "mm", "foot biscuit height")
    up.add("foot_cream_h", cbs("7 mm"), "mm", "foot cream height")
    print("FH params added")
    feet(ctx, 12, 12, hole_param="foot_hole_63", tag="_63", marks=3)
    feet(ctx, 12, -12, hole_param="foot_hole_62", tag="_62", marks=2)
    print("FH BUILD OK: %d bodies" % ctx.root.bRepBodies.count)
