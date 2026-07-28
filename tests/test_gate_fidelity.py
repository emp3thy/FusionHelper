"""Gate fidelity against Autodesk's REAL stubs. Local-only: skipped when the
stubs are absent (CI has only synthetic stubs)."""
from pathlib import Path

import pytest

from fusionhelper import preflight, stubs, verify

pytestmark = pytest.mark.skipif(stubs.discover_defs() is None,
                                reason="Autodesk stubs not installed")

SEVEN = [
    "des.userParameters.addd('w', v, 'mm', '')",
    "adsk.core.ValueInput.createByExpression('60 mm')",
    "sk.geometricConstraints.addFixed(pt)",
    "sk.isFullyConstrainedd",
    "sk.sketchCurves.sketchPolylines",
    "app.activeProduct.rootComponentt",
    "import adsk.geometry",
]


@pytest.mark.parametrize("bad", SEVEN)
def test_hallucination_caught(tmp_path, bad, monkeypatch):
    monkeypatch.delenv("FUSIONHELPER_DEFS", raising=False)
    body = ("import adsk.core\nimport adsk.fusion\n\n\n"
            "def run(_context: str):\n"
            "    app = adsk.core.Application.get()\n"
            "    des = adsk.fusion.Design.cast(app.activeProduct)\n"
            "    sk = des.rootComponent.sketches.item(0)\n"   # sketches/sketchPoints are
            "    pt = sk.sketchPoints.item(0)\n"              # not R4 collections: no waiver
            f"    v = None\n    {bad}\n")
    if bad.startswith("import "):
        body = bad + "\n" + body
    p = tmp_path / "script.py"
    p.write_text(verify.append_to(body), encoding="utf-8")
    r = preflight.run_preflight(p)
    assert r.outcome is preflight.Outcome.FAIL, r.report


def test_stub_tail_passes_real_preflight(tmp_path):
    good = (Path(__file__).parent / "fixtures" / "lint" / "good" /
           "corpus_verify_tail.py").read_text(encoding="utf-8")
    p = tmp_path / "script.py"
    p.write_text(good, encoding="utf-8")
    r = preflight.run_preflight(p)
    assert r.outcome is preflight.Outcome.PASS, r.report
