import adsk.core


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    doc.save("checkpoint: wall v3")  # EXPECT: R10
    app.activeDocument.saveAs("copy", None, "", "")  # EXPECT: R10
