import adsk.fusion


def run(_context: str):
    root = adsk.fusion.Design.cast(None).rootComponent
    body = root.bRepBodies.item(0)  # EXPECT: R4
    faces = body.faces
    top = faces[4]  # EXPECT: R4
    edges = body.edges
    rim = edges.item(2)  # EXPECT: R4
    print(top, rim)
