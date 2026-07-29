from fusionhelper.preflight.pyright_gate import (
    GateBroken,
    assert_canary_fired,
    split_diagnostics,
)

SCRIPT_NAME = "script.py"
CANARY_NAME = "fh_canary_bad.py"


def _diag(file, message, severity="error", line=0, char=0):
    return {
        "file": file,
        "message": message,
        "severity": severity,
        "range": {"start": {"line": line, "character": char}},
    }


def test_script_and_canary_diagnostics_are_split():
    payload = {"generalDiagnostics": [
        _diag(f"C:/tmp/{SCRIPT_NAME}", "script problem"),
        _diag(f"C:/tmp/{CANARY_NAME}", "canary problem"),
    ]}
    script, canary = split_diagnostics(payload, SCRIPT_NAME, CANARY_NAME)
    assert [f.message for f in script] == ["script problem"]
    assert [f.message for f in canary] == ["canary problem"]


def test_unexpected_third_file_never_counts_toward_canary_fired():
    # Doctored payload: pyright reports a diagnostic against a file that is
    # neither the staged script nor the canary probe, and the real canary
    # produced nothing. Before the fix this diagnostic fell into the canary
    # bucket by default (the `else` branch), which would make assert_canary_fired
    # wrongly conclude the canary fired.
    payload = {"generalDiagnostics": [
        _diag("C:/tmp/pyrightconfig.json", "stray diagnostic from an unrelated file"),
    ]}
    script, canary = split_diagnostics(payload, SCRIPT_NAME, CANARY_NAME)
    assert canary == []
    try:
        assert_canary_fired(canary)
    except GateBroken:
        pass
    else:
        raise AssertionError("expected GateBroken: canary produced no error")


def test_unexpected_third_file_is_surfaced_as_visible_engine_warning():
    payload = {"generalDiagnostics": [
        _diag("C:/tmp/pyrightconfig.json", "stray diagnostic from an unrelated file"),
    ]}
    script, _canary = split_diagnostics(payload, SCRIPT_NAME, CANARY_NAME)
    engine = [f for f in script if f.rule_number == "ENGINE"]
    assert len(engine) == 1
    assert engine[0].severity == "warn"
    assert "pyrightconfig.json" in engine[0].message


def test_canary_sentinel_still_raises_gate_broken():
    payload = {"generalDiagnostics": [
        _diag(f"C:/tmp/{CANARY_NAME}", 'Import "adsk.core" could not be resolved'),
    ]}
    try:
        split_diagnostics(payload, SCRIPT_NAME, CANARY_NAME)
    except GateBroken:
        pass
    else:
        raise AssertionError("expected GateBroken: canary import sentinel unresolved")
