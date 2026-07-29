"""The known-bad probe staged next to every checked script.

If pyright, the config, or the stub path silently degrade, these two genuine
hallucinations stop being flagged — and the gate must then report GATE_BROKEN,
never PASS. Both were caught 7/7 in the measurement runs."""

CANARY_NAME = "fh_canary_bad.py"
CANARY_TEXT = """import adsk.core
import adsk.fusion


def run(_context: str):
    v = adsk.core.ValueInput.createByExpression("60 mm")
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    sk = des.rootComponent.sketches.item(0)
    sk.geometricConstraints.addFixed(sk.sketchPoints.item(0))
    print(v)
"""
# Expected: >=1 attribute-access diagnostic in this file. createByExpression and
# addFixed do not exist (in the synthetic stubs either — keep it that way).
