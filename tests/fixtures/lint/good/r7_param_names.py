import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    up = des.userParameters
    up.add("outer_w", adsk.core.ValueInput.createByString("60 mm"), "mm", "outer width")
    up.add("wall_t", adsk.core.ValueInput.createByString("outer_w / 20"), "mm", "derived")
    holes = [1, 2]
    holes.add = None  # not a userParameters receiver: attribute add on a non-tracked name
