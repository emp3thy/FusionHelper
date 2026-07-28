import enum
import shutil
from dataclasses import dataclass
from pathlib import Path

from fusionhelper import lint, stubs
from fusionhelper.lint import render
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
                  defs: Path | None = None) -> PreflightResult:
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
    if expect_stub:
        findings.extend(r8_stub_intact.check_text(source))
    staged = staging.stage(script_path, defs)
    try:
        lock = Path(__file__).parents[2] / "tests" / "api_version.lock"
        env = stubs.pyright_pin_env(lock) if lock.exists() else {}
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
    body = render.report(findings, lint_result.waivers, source, script_path.name)
    errors = [f for f in findings if f.severity == "error"]
    verdict = "PASS" if not errors else "FAIL"
    report = f"PREFLIGHT {verdict} errors={len(errors)}\n{body}"
    return PreflightResult(Outcome.PASS if not errors else Outcome.FAIL, findings, report)
