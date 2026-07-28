from pathlib import Path

import pytest

from fusionhelper import preflight, verify

SYN = Path(__file__).parent / "synthetic_stubs"

GOOD = """import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    print(des)
"""

HALLUCINATED = GOOD.replace("Application.get()", "Application.getInstance()")


def write(tmp_path, body, stub=True):
    p = tmp_path / "script.py"
    p.write_text(verify.append_to(body) if stub else body, encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _defs(monkeypatch):
    monkeypatch.setenv("FUSIONHELPER_DEFS", str(SYN))


def test_good_script_passes(tmp_path):
    r = preflight.run_preflight(write(tmp_path, GOOD))
    assert r.outcome is preflight.Outcome.PASS
    assert r.exit_code == 0
    assert r.report.splitlines()[0].startswith("PREFLIGHT PASS")


def test_hallucinated_api_fails(tmp_path):
    r = preflight.run_preflight(write(tmp_path, HALLUCINATED))
    assert r.outcome is preflight.Outcome.FAIL
    assert r.exit_code == 1
    assert "getInstance" in r.report


def test_missing_defs_is_gate_broken(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSIONHELPER_DEFS", str(tmp_path / "nowhere"))
    r = preflight.run_preflight(write(tmp_path, GOOD))
    assert r.outcome is preflight.Outcome.GATE_BROKEN
    assert r.exit_code == 3
    assert "do not edit the script" in r.report.lower()


def test_dead_canary_is_gate_broken(tmp_path, monkeypatch):
    # neuter the canary: if pyright stops flagging the known-bad probe,
    # a clean run must NOT be reported as PASS
    monkeypatch.setattr(preflight.canary, "CANARY_TEXT", "x = 1\n")
    r = preflight.run_preflight(write(tmp_path, GOOD))
    assert r.outcome is preflight.Outcome.GATE_BROKEN
    assert r.exit_code == 3


def test_lint_findings_fail_before_pyright_matters(tmp_path):
    r = preflight.run_preflight(write(tmp_path, GOOD.replace(
        "print(des)", "print(adsk.core.ValueInput.createByReal(1.0))")))
    assert r.outcome is preflight.Outcome.FAIL
    assert "R1" in r.report


def test_missing_stub_fails_when_expected(tmp_path):
    r = preflight.run_preflight(write(tmp_path, GOOD, stub=False))
    assert r.outcome is preflight.Outcome.FAIL
    assert "R8" in r.report
