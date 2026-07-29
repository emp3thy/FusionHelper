import enum
import importlib.metadata
import shutil
from dataclasses import dataclass
from pathlib import Path

from fusionhelper import lint, stubs
from fusionhelper.lint import render
from fusionhelper.lint.findings import RULES
from fusionhelper.lint.rules import r8_stub_intact
from fusionhelper.preflight import canary, staging
from fusionhelper.preflight.pyright_gate import (
    GateBroken,
    assert_canary_fired,
    run_pyright,
    split_diagnostics,
)


class Outcome(enum.Enum):
    PASS = 0
    FAIL = 1
    USAGE = 2
    GATE_BROKEN = 3


@dataclass
class PreflightResult:
    outcome: Outcome
    findings: list
    report: str

    @property
    def exit_code(self) -> int:
        return self.outcome.value


def run_preflight(script_path: Path, *, expect_stub: bool = True,
                  defs: Path | None = None, lock_path: Path | None = None) -> PreflightResult:
    script_path = Path(script_path)
    if not script_path.is_file():
        return PreflightResult(Outcome.USAGE, [], f"no such script: {script_path}")
    defs = defs or stubs.discover_defs()
    if defs is None:
        return PreflightResult(
            Outcome.GATE_BROKEN, [],
            "PREFLIGHT GATE_BROKEN\nAutodesk API stubs not found (set FUSIONHELPER_DEFS "
            "or install Fusion). Environment error - fix the machine, do NOT edit the "
            "script.")
    source = script_path.read_text(encoding="utf-8")
    lint_result = lint.run(source, script_path.name)
    findings = list(lint_result.findings)
    checked = {n for n, info in RULES.items() if info.checked}
    if expect_stub:
        findings.extend(r8_stub_intact.check_text(source))
    else:
        checked.discard("R8")
    lock = lock_path if lock_path is not None else stubs.default_lock_path()
    staged = staging.stage(script_path, defs)
    lock_warning = None
    try:
        try:
            env = stubs.pyright_pin_env(lock) if lock.exists() else {}
        except Exception as e:  # corrupt/foreign lock: unpinned, never a crash
            env = {}
            lock_warning = f"warning: {lock} unreadable ({e}) - pyright version unpinned"
        payload = run_pyright(staged, env)
        script_diags, canary_diags = split_diagnostics(
            payload, staging.SCRIPT_NAME, canary.CANARY_NAME)
        assert_canary_fired(canary_diags)
        findings.extend(script_diags)
    except GateBroken as e:
        return PreflightResult(
            Outcome.GATE_BROKEN, findings,
            f"PREFLIGHT GATE_BROKEN\n{e}\nExit 3: fix the machine, do NOT edit the script.")
    finally:
        shutil.rmtree(staged, ignore_errors=True)
    body = render.report(findings, lint_result.waivers, source, script_path.name,
                         checked=checked)
    errors = [f for f in findings if f.severity == "error"]
    verdict = "PASS" if not errors else "FAIL"
    lines = [f"PREFLIGHT {verdict} errors={len(errors)}", body]
    if lock_warning:
        lines.append(lock_warning)
    # Drift is REPORTED, never silently absorbed — but it never changes the
    # outcome: the canary above already proves the gate functions correctly.
    # A failure *computing* drift (bad install, unreadable lock, filesystem
    # error) must not crash the whole preflight run with a raw traceback —
    # that would be worse than the silent absorption this block exists to fix.
    if lock.exists():
        try:
            installed_pyright = importlib.metadata.version("pyright")
            drift = stubs.drift_report(stubs.read_lock(lock), defs=defs,
                                       pyright_version=installed_pyright)
            lines.extend(f"drift: {d}" for d in drift)
        except Exception as e:
            lines.append(f"warning: drift check failed: {e}")
    else:
        lines.append("warning: api_version.lock not found (expected "
                     "fusionhelper/api_version.lock unless overridden) - pyright "
                     "version unpinned, gate results may drift")
    report = "\n".join(lines)
    return PreflightResult(Outcome.PASS if not errors else Outcome.FAIL, findings, report)
