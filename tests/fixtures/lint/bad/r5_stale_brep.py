import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    held = None
    for body in des.rootComponent.bRepBodies:  # direct iteration: no R4 subscript
        for f in body.faces:
            held = f
    des.userParameters.itemByName("outer_w").expression = "80 mm"  # EXPECT: R5
    print(held.area)
