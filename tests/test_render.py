from fusionhelper import lint
from fusionhelper.lint import render
from fusionhelper.lint.findings import RULES

BAD = (
    "import adsk.core\n\n\n"
    "def run(_context: str):\n"
    "    v = adsk.core.ValueInput.createByReal(0.6)\n"
    "    print(v)\n"
)

CLEAN = "print('hello')\n"


def test_fail_report_shape():
    r = lint.run(BAD, "box.py")
    text = render.report(r.findings, r.waivers, BAD, "box.py")
    lines = text.splitlines()
    assert lines[0] == "LINT FAIL errors=1 warns=0"
    assert any(ln.startswith("R1 ") for ln in lines)          # restatement header first
    assert any("box.py:5:" in ln for ln in lines)             # path:line:col
    assert any(ln.strip().startswith("^") for ln in lines)    # caret excerpt
    assert any(ln.strip().startswith("fix:") for ln in lines) # code, not advice
    # Bare lint.run/render.report call: no caller told the renderer R8 was
    # checked (that only happens via preflight's expect_stub=True), so R8
    # belongs in "not checked" here, not "checked" — see test_preflight.py's
    # test_expect_stub_true_default_checks_r8 for the case where it moves.
    assert lines[-1].startswith("checked: R1 R2 R4 R5 R6 R7 R9 R10 R11 ·")
    assert "not checked: R3 R8" in lines[-1]
    assert "R5 covers parameter-change only" in lines[-1]


def test_default_coverage_line_matches_derivation_from_rules():
    expected_checked = [n for n in RULES if RULES[n].checked and n != "R8"]
    expected_not_checked = [n for n in RULES if n not in expected_checked]
    expected = (f"checked: {' '.join(expected_checked)} · "
               f"not checked: {' '.join(expected_not_checked)} · "
               "R5 covers parameter-change only")
    r = lint.run(CLEAN, "box.py")
    text = render.report(r.findings, r.waivers, CLEAN, "box.py")
    assert text.splitlines()[-1] == expected


def test_explicit_checked_set_moves_r8_into_checked():
    all_checked = {n for n, info in RULES.items() if info.checked}
    text = render.report([], [], CLEAN, "box.py", checked=all_checked)
    last = text.splitlines()[-1]
    assert last.startswith("checked: R1 R2 R4 R5 R6 R7 R8 R9 R10 R11 ·")
    assert "not checked: R3" in last


def test_pass_report_still_has_coverage_and_waivers():
    # a USED waiver: R1 fires on this line and is suppressed with a valid reason
    src = ("import adsk.core\n"
           "v = adsk.core.ValueInput.createByReal(0.6)"
           "  # fusionhelper: allow R1 — legacy shim kept verbatim\n")
    r = lint.run(src, "box.py")
    text = render.report(r.findings, r.waivers, src, "box.py")
    assert text.splitlines()[0] == "LINT PASS errors=0 warns=0"
    assert "waiver" in text.lower()           # waivers print even on PASS


def test_verdict_is_derived_not_counted():
    # renderer must recompute from the findings list: hand it a doctored list
    r = lint.run(BAD, "box.py")
    text = render.report([], r.waivers, BAD, "box.py")
    assert text.splitlines()[0].startswith("LINT PASS")
