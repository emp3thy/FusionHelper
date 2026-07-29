import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    body = des.rootComponent.bRepBodies.item(0)  # EXPECT: R4
    top = body.faces[4]  # EXPECT: R4
    edge = body.edges.item(2)  # EXPECT: R4
    first_body = des.rootComponent.bRepBodies[0]  # EXPECT: R4
    for i in range(body.faces.count):
        print(body.faces[i].area)  # exempt: inside the range-count loop
    leaked = body.faces[4]  # EXPECT: R4
    print(top, edge, first_body, leaked)
