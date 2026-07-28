import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    up = des.userParameters
    up.add("W", adsk.core.ValueInput.createByString("60 mm"), "mm", "")  # EXPECT: R7
    up.add("PI", adsk.core.ValueInput.createByString("3 mm"), "mm", "")  # EXPECT: R7
    up.add("box w", adsk.core.ValueInput.createByString("3 mm"), "mm", "")  # EXPECT: R7
    up.add("0box", adsk.core.ValueInput.createByString("3 mm"), "mm", "")  # EXPECT: R7
    up.add("outer_w", adsk.core.ValueInput.createByString("60 mm"), "mm", "")
    up.add("outer_w", adsk.core.ValueInput.createByString("9 mm"), "mm", "")  # EXPECT: R7
    up.add("outerW", adsk.core.ValueInput.createByString("60 mm"), "mm", "")  # EXPECT: R7
    des.userParameters.add("t", adsk.core.ValueInput.createByString("2 mm"), "mm", "")  # EXPECT: R7
