from fusionhelper import lint
from fusionhelper.lint import render

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
    assert lines[-1].startswith("checked: R1 R2 R4 R5 R6 R7 R8")
    assert "not checked: R3 R9 R10" in lines[-1]
    assert "R5 covers parameter-change only" in lines[-1]


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
