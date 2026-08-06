import adsk.core


def run(_context: str):
    app = adsk.core.Application.get()
    try:  # EXPECT: R9
        app.log("x")
    except Exception:
        pass
    try:  # fusionhelper: allow R9 — probe characterises over-constraint error text
        app.log("y")
    except RuntimeError:
        raise
