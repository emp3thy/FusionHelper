import ast
import io
import tokenize

from fusionhelper.lint.findings import Finding

RULE_ID = "no-create-by-real"
NUMBER = "R1"
RESTATEMENT = "Never ValueInput.createByReal — use createByString, always"

_FIX = "adsk.core.ValueInput.createByString('<value with unit, or parameter expression>')"


def check(tree: ast.AST, source: str) -> list[Finding]:
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "createByReal":
            findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset,
                                    "error", "createByReal bakes a literal; the timeline "
                                    "looks parametric and dies on first edit", _FIX))
    ast_lines = {f.line for f in findings}
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if (tok.type == tokenize.STRING and "createByReal" in tok.string
                and tok.start[0] not in ast_lines):
            findings.append(Finding(RULE_ID, NUMBER, tok.start[0], tok.start[1],
                                    "warn", "string mentions createByReal — possible "
                                    "getattr evasion of R1", _FIX))
    return findings
