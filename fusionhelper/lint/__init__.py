import ast
from dataclasses import dataclass, field

from fusionhelper.lint.findings import Finding
from fusionhelper.lint.rules import ALL_RULES


@dataclass
class LintResult:
    findings: list[Finding] = field(default_factory=list)
    waivers: list = field(default_factory=list)   # populated in Task 3
    parse_error: Finding | None = None


def run(source: str, path: str = "<script>") -> LintResult:
    result = LintResult()
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        # SyntaxError.offset is 1-based; Finding.col is uniformly 0-based
        col = max(0, (e.offset or 1) - 1)
        result.parse_error = Finding("syntax", "SYNTAX", e.lineno or 1, col,
                                     "error", f"script does not parse: {e.msg}")
        result.findings.append(result.parse_error)
        return result
    for rule in ALL_RULES:
        result.findings.extend(rule.check(tree, source))
    result.findings.sort(key=lambda f: (f.line, f.col, f.rule_number))
    return result
