import adsk.fusion


def run(_context: str):
    root = adsk.fusion.Design.cast(None).rootComponent
    body = root.bRepBodies[0]  # fusionhelper: allow R4 — fixture needs one seeded body
    edges = body.edges
    for i in range(edges.count):
        e = edges[i]
        it = edges.item(i)
        print(e, it)
