import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    sk = root.sketches.item(0)
    prof = sk.profiles.item(0)  # the universal idiom — deliberately excluded from R4
    for body in root.bRepBodies:
        for f in body.faces:
            if f.geometry.normal.z > 0.99:
                print("top face", f.tempId)
        for i in range(body.faces.count):
            print(body.faces[i].area)  # exempt: range(<same receiver>.count)
    faces = [1, 2, 3]
    print(faces[0])  # bare name, no dotted chain — never matches
    print(prof)
