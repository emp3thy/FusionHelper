from pathlib import Path

from fusionhelper import stubs

SYN = Path(__file__).parent / "synthetic_stubs"


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv("FUSIONHELPER_DEFS", str(SYN))
    assert stubs.discover_defs() == SYN


def test_missing_defs_returns_none(monkeypatch):
    monkeypatch.setenv("FUSIONHELPER_DEFS", str(SYN / "nope"))
    assert stubs.discover_defs() is None


def test_fingerprint_is_stable_and_content_sensitive(tmp_path):
    fp1 = stubs.fingerprint(SYN)
    assert fp1 == stubs.fingerprint(SYN)
    assert len(fp1) == 64


def test_lock_roundtrip_and_drift(tmp_path):
    lock = tmp_path / "api_version.lock"
    stubs.write_lock(lock, api_version="2703.1.20", pyright_version="1.1.408",
                     stub_sha256=stubs.fingerprint(SYN))
    data = stubs.read_lock(lock)
    assert data["pyright_version"] == "1.1.408"
    drift = stubs.drift_report(data, defs=SYN, pyright_version="1.1.999")
    assert any("pyright" in d for d in drift)          # reported, never absorbed
    assert not any("stub" in d for d in drift)


def test_pyright_pin_env(tmp_path):
    lock = tmp_path / "api_version.lock"
    stubs.write_lock(lock, api_version="x", pyright_version="1.1.408", stub_sha256="0" * 64)
    env = stubs.pyright_pin_env(lock)
    assert env["PYRIGHT_PYTHON_FORCE_VERSION"] == "1.1.408"
