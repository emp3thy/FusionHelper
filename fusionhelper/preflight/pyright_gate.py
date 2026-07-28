import json
import re
import subprocess
import sys
from pathlib import Path

from fusionhelper.lint.findings import Finding

STUB_SENTINEL_RE = re.compile(r'Import "adsk(\.\w+)?" could not be resolved')


class GateBroken(Exception):
    pass


def run_pyright(staged_dir: Path, env_extra: dict[str, str]) -> dict:
    import os
    env = {**os.environ, **env_extra}
    proc = subprocess.run(
        [sys.executable, "-m", "pyright", "--outputjson", "--project", str(staged_dir)],
        capture_output=True, text=True, env=env)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise GateBroken(f"pyright produced no parseable JSON (stderr: "
                         f"{proc.stderr[:300]!r})") from e


def split_diagnostics(payload: dict, script_name: str, canary_name: str):
    """Split pyright diagnostics between the script under test and the canary probe.

    An unresolved "adsk.*" import is only proof of environment breakage (extraPaths
    not wired, stubs missing) when it appears against the CANARY file: the canary's
    two imports (`adsk.core`, `adsk.fusion`) are fixed, known-good text, so if pyright
    cannot resolve them the stub path itself failed. The same message against the
    SCRIPT file can equally be a genuine hallucination — a generated script importing
    a submodule that does not exist (`adsk.geometry`) — and must surface as a finding,
    not be swallowed as GATE_BROKEN. Measured: `import adsk.geometry` (no such stub
    module) previously passed silently through this exact GateBroken path.
    """
    script, canary = [], []
    for d in payload.get("generalDiagnostics", []):
        name = Path(d["file"]).name
        if name == canary_name and STUB_SENTINEL_RE.search(d.get("message", "")):
            raise GateBroken("stub path did not take effect: adsk import unresolved "
                             "in the canary probe, whose imports are fixed known-good "
                             "text. Environment error — fix the machine, do NOT edit "
                             "the script; other diagnostics suppressed as noise.")
        entry = Finding("pyright", d.get("rule") or "PYRIGHT",
                        d["range"]["start"]["line"] + 1,        # 0-based -> 1-based
                        d["range"]["start"]["character"],
                        "error" if d["severity"] == "error" else "warn",
                        d["message"].splitlines()[0])
        (script if name == script_name else canary).append(entry)
    return script, canary


def assert_canary_fired(canary_findings) -> None:
    if not any(f.severity == "error" for f in canary_findings):
        raise GateBroken("canary did not fire: the known-bad probe produced no error. "
                         "Config parse, stub resolution or rule severity has silently "
                         "degraded — GATE_BROKEN, never PASS.")
