import adsk.fusion


def run(_context: str):
    root = adsk.fusion.Design.cast(None).rootComponent
    body = root.bRepBodies[0]  # fusionhelper: allow R4 — fixture needs one seeded body
    faces = body.faces
    for i in range(faces.count):
        f = faces[i]
        print(f.area)
    faces = None  # second assignment: name no longer a trusted alias
    items = [1, 2, 3]
    print(items[0])
