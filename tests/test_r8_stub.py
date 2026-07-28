from fusionhelper import verify
from fusionhelper.lint.rules import r8_stub_intact

GOOD_BODY = "def run(_context: str):\n    print('build')\n"


def findings_for(text):
    return r8_stub_intact.check_text(text)


def test_intact_stub_passes():
    assert findings_for(verify.append_to(GOOD_BODY)) == []


def test_crlf_and_trailing_whitespace_pass():
    windows = verify.append_to(GOOD_BODY).replace("\n", "\r\n") + "\r\n\r\n"
    assert findings_for(windows) == []


def test_missing_stub_fails_with_diagnosis():
    (f,) = findings_for(GOOD_BODY)
    assert f.rule_number == "R8"
    assert "stub" in f.message and "missing" in f.message


def test_code_after_stub_fails_as_the_silent_case():
    text = verify.append_to(GOOD_BODY) + "\n\ndef run(_context: str):\n    pass\n"
    (f,) = findings_for(text)
    assert f.rule_number == "R8"
    assert "after the stub" in f.message


def test_edited_stub_fails():
    text = verify.append_to(GOOD_BODY).replace("_fh_wrap", "_fh_wrap2")
    (f,) = findings_for(text)
    assert f.rule_number == "R8"
