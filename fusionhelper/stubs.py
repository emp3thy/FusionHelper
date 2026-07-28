"""Autodesk stub discovery, API version, and drift lock.

Drift is REPORTED, never silently absorbed: a Fusion update changes the stubs
and therefore what the gate catches; the lock records what the suite last ran
against (api version, pyright version, stub sha256)."""
import hashlib
import json
import os
from pathlib import Path

_DEFAULT = Path(os.environ.get("APPDATA", "")) / "Autodesk" / "Autodesk Fusion 360" / \
    "API" / "Python" / "defs"


def discover_defs() -> Path | None:
    override = os.environ.get("FUSIONHELPER_DEFS")
    cand = Path(override) if override else _DEFAULT
    return cand if (cand / "adsk").is_dir() else None


def api_version(defs: Path) -> str | None:
    vt = defs.parent.parent / "version.txt"   # .../API/version.txt
    try:
        return vt.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def fingerprint(defs: Path) -> str:
    h = hashlib.sha256()
    for name in ("core.py", "fusion.py"):
        p = defs / "adsk" / name
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()


def write_lock(path: Path, *, api_version: str | None, pyright_version: str,
               stub_sha256: str) -> None:
    path.write_text(json.dumps({"api_version": api_version,
                                "pyright_version": pyright_version,
                                "stub_sha256": stub_sha256}, indent=2) + "\n",
                    encoding="utf-8")


def read_lock(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def drift_report(lock: dict, *, defs: Path | None, pyright_version: str) -> list[str]:
    drift = []
    if pyright_version != lock["pyright_version"]:
        drift.append(f"pyright drifted: lock {lock['pyright_version']}, "
                     f"installed {pyright_version}")
    if defs is not None and fingerprint(defs) != lock["stub_sha256"]:
        drift.append("stub fingerprint drifted: Fusion update changed the API defs; "
                     "re-run gate fidelity tests and re-bless the lock")
    return drift


def pyright_pin_env(lock_path: Path) -> dict[str, str]:
    lock = read_lock(lock_path)
    return {"PYRIGHT_PYTHON_FORCE_VERSION": lock["pyright_version"],
            "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1"}
