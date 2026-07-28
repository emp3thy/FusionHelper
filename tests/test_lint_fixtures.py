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
