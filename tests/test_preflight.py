import importlib.metadata
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


def test_pyright_version_drift_is_reported_not_absorbed(tmp_path, monkeypatch):
    # Keep the real lock (its pyright_version is the actually-installed, already
    # cached pyright, so PYRIGHT_PYTHON_FORCE_VERSION pinning needs no network
    # fetch) and fake only what "installed" reports, so drift is detected
    # without perturbing the real pyright subprocess invocation. Pointing the
    # lock itself at a nonexistent pyright_version (e.g. "9.9.9") instead would
    # make pyright_pin_env force that version and crash the subprocess — this
    # was verified against a real run before choosing the monkeypatch approach.
    monkeypatch.setattr(preflight.importlib.metadata, "version", lambda _name: "9.9.9")
    r = preflight.run_preflight(write(tmp_path, GOOD))
    assert r.outcome is preflight.Outcome.PASS
    assert r.exit_code == 0
    assert "drift: pyright drifted" in r.report


def test_missing_lock_is_a_visible_warning_not_silent(tmp_path):
    r = preflight.run_preflight(write(tmp_path, GOOD), lock_path=tmp_path / "nowhere.lock")
    assert r.outcome is preflight.Outcome.PASS
    assert r.exit_code == 0
    assert "warning: tests/api_version.lock not found" in r.report


def test_drift_check_failure_is_a_warning_not_a_crash(tmp_path, monkeypatch):
    # A broken drift *computation* (bad install, unreadable metadata, ...) must
    # not crash the whole run with a raw traceback — that would be worse than
    # the silent absorption the drift block exists to fix.
    def _raise(_name):
        raise importlib.metadata.PackageNotFoundError("pyright")
    monkeypatch.setattr(preflight.importlib.metadata, "version", _raise)
    r = preflight.run_preflight(write(tmp_path, GOOD))
    assert r.outcome is preflight.Outcome.PASS
    assert r.exit_code == 0
    assert "drift check failed" in r.report
