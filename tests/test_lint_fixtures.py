from pathlib import Path

import pytest

from fusionhelper import lint
from tests import markers

FIXTURES = sorted((Path(__file__).parent / "fixtures" / "lint").rglob("*.py"))


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_fixture(path: Path):
    result = lint.run(path.read_text(encoding="utf-8"), str(path))
    found = {(f.line, f.rule_number) for f in result.findings}
    assert found == markers.parse(path)


def test_syntax_error_becomes_finding():
    result = lint.run("def broken(:\n", "bad.py")
    (f,) = result.findings
    assert f.rule_number == "SYNTAX"
    assert f.severity == "error"
    assert f.line == 1
    assert f.col == 11
    assert result.parse_error is f
