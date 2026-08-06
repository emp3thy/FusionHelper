import adsk.core


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    doc.save("checkpoint: rim v2")  # fusionhelper: allow R10 — user consented checkpoint
    state = {"phase": "done"}
    print(state)
