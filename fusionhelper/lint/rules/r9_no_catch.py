import ast

from fusionhelper.lint import regions
from fusionhelper.lint.findings import Finding

RULE_ID = "no-catch"
NUMBER = "R9"
RESTATEMENT = "Never catch exceptions in generated scripts — the traceback is the diagnostic"

_FIX = ("delete the handler and let the exception escape (Autodesk guidance: the "
        "traceback is the diagnostic); a probe that must characterise an exception "
        "waives per line with the reason")


def check(tree: ast.AST, source: str) -> list[Finding]:
    exempt = regions.exempt_lines(source)
    findings = []
    for node in ast.walk(tree):
        if (isinstance(node, (ast.Try, ast.TryStar)) and node.handlers
                and node.lineno not in exempt):
            findings.append(Finding(
                RULE_ID, NUMBER, node.lineno, node.col_offset, "error",
                "try/except in a generated script — a swallowed exception turns a "
                "loud failure into silent wrong geometry", _FIX))
    return findings
