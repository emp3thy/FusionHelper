import adsk.fusion


def run(_context: str):
    root = adsk.fusion.Design.cast(None).rootComponent
    body = root.bRepBodies.item(0)  # EXPECT: R4
    faces = body.faces
    top = faces[4]  # EXPECT: R4
    faces.some_attr = 5  # attribute store THROUGH the alias — not a rebind
    faces[0] = None  # EXPECT: R4 — subscript store THROUGH the alias — not a rebind
    sneaky = faces[7]  # EXPECT: R4 — alias must still be tracked after both stores above
    edges = body.edges
    rim = edges.item(2)  # EXPECT: R4
    print(top, rim, sneaky)
