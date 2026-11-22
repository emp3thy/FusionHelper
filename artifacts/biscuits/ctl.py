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

DOCS = '''
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    out = []
    for i in range(app.documents.count):
        d = app.documents.item(i)
        des = adsk.fusion.Design.cast(d.products.itemByProductType("DesignProductType"))
        out.append([d.name, d.isSaved, des.rootComponent.bRepBodies.count if des else -1])
    print("FH_RESULT " + json.dumps(out))
'''

CLOSE_UNSAVED = '''
import adsk.core, adsk.fusion
def run(_context: str):
    app = adsk.core.Application.get()
    victims = []
    for i in range(app.documents.count):
        d = app.documents.item(i)
        if not d.isSaved and d.name.startswith("Untitled"):
            victims.append(d)
    n = 0
    for d in victims:
        adsk.doEvents()
        d.close(False)
        n += 1
    print("FH_RESULT closed", n, "remaining", app.documents.count)
'''

GROUP = '''
import adsk.core, adsk.fusion, json
def run(_context: str):
    app = adsk.core.Application.get()
    docs = [app.documents.item(i) for i in range(app.documents.count)]
    last = app.activeDocument
    report = []
    for d in docs:
        d.activate()
        adsk.doEvents()
        des = adsk.fusion.Design.cast(app.activeProduct)
        if des is None:
            continue
        root = des.rootComponent
        bodies = [b for b in root.bRepBodies]      # list first: moves mutate the collection
        names = sorted(b.name for b in bodies)
        if not any(n.startswith("foot_disc") for n in names):
            report.append([d.name, "skipped: no loose feet at root", len(names)])
            continue
        kind = ("Pink wafer" if any(n.startswith("wafer") for n in names) else
                "Custard cream" if "cream" in names else "Jam biscuit")
        v0 = sum(b.volume for b in bodies)
        occ_c = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ_c.component.name = kind
        occ_f = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ_f.component.name = "Feet"
        for b in bodies:
            adsk.doEvents()
            b.moveToComponent(occ_f if b.name.startswith("foot_") else occ_c)
        cb = [b for b in occ_c.component.bRepBodies]
        fb = [b for b in occ_f.component.bRepBodies]
        v1 = sum(b.volume for b in cb) + sum(b.volume for b in fb)
        same = sorted(b.name for b in cb + fb) == names
        occ_c.isLightBulbOn = True
        occ_f.isLightBulbOn = True
        report.append([d.name, kind, len(cb), "Feet", len(fb),
                       "left at root", root.bRepBodies.count,
                       "names kept", same, "dvol_mm3", round((v1 - v0) * 1000, 4)])
    last.activate()
    print("FH_RESULT " + json.dumps(report))
'''

PAINT = '''
import adsk.core, adsk.fusion
COLOURS = {
    "biscuit": (222, 190, 130), "foot_disc": (222, 190, 130),
    "thigh": (205, 170, 115), "shin": (205, 170, 115), "jam": (214, 60, 80), "wafer": (242, 172, 160),
    "ink": (25, 22, 22), "cheek": (236, 120, 150), "cream": (250, 246, 236),
    "foot_cream": (250, 246, 236), "scroll": (92, 52, 30),
    "wafer_cream": (250, 246, 236),
    "print_brace": (120, 125, 135),
}
WAFER_LEGS = (250, 246, 236)   # the pink wafer has white legs
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
    # bodies at root AND inside components (after `group`)
    todo = [b for b in root.bRepBodies]
    for o in root.occurrences:
        todo += [b for b in o.component.bRepBodies]
    is_wafer = any(b.name.startswith("wafer") for b in todo)
    for b in todo:
        adsk.doEvents()
        key = None
        for k in sorted(COLOURS, key=len, reverse=True):
            if b.name.startswith(k):
                key = k
                break
        if key is None:
            continue
        nm = "fh_" + key
        rgb = COLOURS[key]
        if is_wafer and key in ("thigh", "shin"):
            nm = "fh_white_leg"
            rgb = WAFER_LEGS
        ap = None
        for j in range(des.appearances.count):
            if des.appearances.item(j).name == nm:
                ap = des.appearances.item(j)
        if ap is None:
            ap = des.appearances.addByCopy(base, nm)
            prop = adsk.core.ColorProperty.cast(
                ap.appearanceProperties.itemByName("Color"))
            r, g, bl = rgb
            prop.value = adsk.core.Color.create(r, g, bl, 255)
        b.appearance = ap
        done += 1
    print("FH_RESULT painted", done, "of", len(todo))
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

ACTIVATE = '''
import adsk.core, adsk.fusion, json
KIND = "%s"
def run(_context: str):
    # Find the document by CONTENT, never by position: the user closes
    # and reorders documents while we work.
    app = adsk.core.Application.get()
    hits = []
    for i in range(app.documents.count):
        d = app.documents.item(i)
        des = adsk.fusion.Design.cast(d.products.itemByProductType("DesignProductType"))
        if des is None:
            continue
        root = des.rootComponent
        names = [b.name for b in root.bRepBodies]
        for o in root.occurrences:
            names += [b.name for b in o.component.bRepBodies]
        kind = ("wafer" if any(n.startswith("wafer") for n in names) else
                "custard" if "cream" in names else
                "jam" if "jam" in names else
                "empty" if not names else "other")
        if kind == KIND:
            hits.append(d)
    if len(hits) != 1:
        print("FH_RESULT " + json.dumps({"ok": False, "kind": KIND, "matches": len(hits)}))
        return
    hits[0].activate()
    adsk.doEvents()
    print("FH_RESULT " + json.dumps({"ok": True, "kind": KIND, "active": app.activeDocument.name}))
'''

cmd = sys.argv[1]
c = McpClient("http://127.0.0.1:27182/mcp")
c.initialize()
if cmd == "undo":
    print(c.undo())
elif cmd == "undoall":
    n = 0
    while n < 40:
        out = c.undo()
        text = out["result"]["content"][0]["text"]
        n += 1
        if '"canUndo": false' in text or '"success": false' in text:
            break
    print("undid", n, "steps;", " ".join(text.split())[:160])
elif cmd == "activate":
    r = c.execute(ACTIVATE % sys.argv[2])
    print("SUCCESS", r.success, (r.message if r.success else r.error)[-300:])
else:
    if cmd == "shot":
        out = str(Path(sys.argv[2]).resolve())
        view = sys.argv[3] if len(sys.argv) > 3 else "6, -14, 28"
        text = SHOT % (view, out)
    else:
        text = {"probe": PROBE, "newdoc": NEWDOC, "paint": PAINT, "docs": DOCS, "group": GROUP, "close_unsaved": CLOSE_UNSAVED}[cmd]
    r = c.execute(text)
    print("SUCCESS", r.success)
    print((r.message if r.success else r.error)[-1500:])
