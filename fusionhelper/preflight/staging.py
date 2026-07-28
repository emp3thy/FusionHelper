"""Stage script + canary into an isolated temp dir and generate the config.

mkdtemp + ordinary open() (never mkstemp+fdopen). The isolated dir escapes any
ancestor pyrightconfig.json / pyproject [tool.pyright]. include names the two
staged files explicitly — NEVER ["."] (measured: 4 files / 1168 diagnostics)."""
import json
import shutil
import tempfile
from pathlib import Path

from fusionhelper.preflight import canary

SCRIPT_NAME = "script.py"


def stage(script_path: Path, defs: Path) -> Path:
    d = Path(tempfile.mkdtemp(prefix="fh_preflight_"))
    shutil.copyfile(script_path, d / SCRIPT_NAME)
    # Module-qualified access (not a direct name import): tests monkeypatch
    # preflight.canary.CANARY_TEXT to simulate a neutered probe, which only
    # takes effect if this reads the attribute off the module at call time.
    (d / canary.CANARY_NAME).write_text(canary.CANARY_TEXT, encoding="utf-8")
    config = {
        "include": [SCRIPT_NAME, canary.CANARY_NAME],
        "extraPaths": [str(defs)],
        "typeCheckingMode": "basic",
        "pythonVersion": "3.14",
        "reportMissingImports": "error",
        "reportAttributeAccessIssue": "error",
        "reportArgumentType": "none",
        "reportSelfClsParameterName": "none",
    }
    with open(d / "pyrightconfig.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return d
