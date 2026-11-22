"""Small Fusion session controls for the biscuit builds (no stub: these
are session utilities, not part builds).
  python ctl.py probe | undo | newdoc | paint | shot <out.png>"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests" / "integration"))
from mcp_client import McpClient  # noqa: E402

PROBE = '''
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    print("FH_RESULT " + json.dumps({
        "name": doc.name, "isSaved": doc.isSaved,
        "bodies": [b.name for b in root.bRepBodies],
        "sketches": root.sketches.count, "timeline": des.timeline.count,
        "params": des.userParameters.count, "docs": app.documents.count}))
'''

NEWDOC = '''
import adsk.core, adsk.fusion
def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    des = adsk.fusion.Design.cast(app.activeProduct)
    des.designType = adsk.fusion.DesignTypes.ParametricDesignType
    print("FH_RESULT new doc", doc.name, "bodies", des.rootComponent.bRepBodies.count)
'''

PAINT = '''
import adsk.core, adsk.fusion
COLOURS = {
    "biscuit": (222, 190, 130), "foot_disc": (222, 190, 130),
    "leg": (205, 170, 115), "jam": (214, 60, 80), "wafer": (242, 172, 160),
    "ink": (25, 22, 22), "cheek": (236, 120, 150), "cream": (250, 246, 236),
    "foot_cream": (250, 246, 236), "scroll": (92, 52, 30),
}
def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    base = None
    libs = app.materialLibraries
    for i in range(libs.count):
        lib = libs.item(i)
        if "ppearance" not in lib.name:
            continue
        aps = lib.appearances
        for j in range(aps.count):
            cand = aps.item(j)
            if cand.name.startswith("Plastic - Matte"):
                base = cand
                break
        if base:
            break
    if base is None:
        print("FH_RESULT no base appearance found; nothing painted")
        return
    done = 0
    for b in root.bRepBodies:
        adsk.doEvents()
        key = None
        for k in sorted(COLOURS, key=len, reverse=True):
            if b.name.startswith(k):
                key = k
                break
        if key is None:
            continue
        nm = "fh_" + key
        ap = None
        for j in range(des.appearances.count):
            if des.appearances.item(j).name == nm:
                ap = des.appearances.item(j)
        if ap is None:
            ap = des.appearances.addByCopy(base, nm)
            prop = adsk.core.ColorProperty.cast(
                ap.appearanceProperties.itemByName("Color"))
            r, g, bl = COLOURS[key]
            prop.value = adsk.core.Color.create(r, g, bl, 255)
        b.appearance = ap
        done += 1
    print("FH_RESULT painted", done, "of", root.bRepBodies.count)
'''

SHOT = '''
import adsk.core, adsk.fusion
def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    for sk in des.rootComponent.sketches:
        sk.isLightBulbOn = False
    for pl in des.rootComponent.constructionPlanes:
        pl.isLightBulbOn = False
    vp = app.activeViewport
    cam = vp.camera
    cam.target = adsk.core.Point3D.create(0, -1, 0)
    cam.eye = adsk.core.Point3D.create(%s)
    cam.upVector = adsk.core.Vector3D.create(0, 1, 0)
    cam.isFitView = True
    cam.isSmoothTransition = False
    vp.camera = cam
    adsk.doEvents()
    vp.fit()
    adsk.doEvents()
    ok = vp.saveAsImageFile(r"%s", 1400, 1000)
    print("FH_RESULT shot", ok)
'''

cmd = sys.argv[1]
c = McpClient("http://127.0.0.1:27182/mcp")
c.initialize()
if cmd == "undo":
    print(c.undo())
else:
    if cmd == "shot":
        out = str(Path(sys.argv[2]).resolve())
        view = sys.argv[3] if len(sys.argv) > 3 else "6, -14, 28"
        text = SHOT % (view, out)
    else:
        text = {"probe": PROBE, "newdoc": NEWDOC, "paint": PAINT}[cmd]
    r = c.execute(text)
    print("SUCCESS", r.success)
    print((r.message if r.success else r.error)[-1500:])
