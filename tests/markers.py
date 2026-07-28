"""Loader for inline `# EXPECT: <rule>` markers in lint fixtures."""
import re
from pathlib import Path

_MARKER = re.compile(r"#\s*EXPECT:\s*(R\d+)")


def parse(path: Path) -> set[tuple[int, str]]:
    expected = set()
    for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for m in _MARKER.finditer(text):
            expected.add((lineno, m.group(1)))
    return expected
