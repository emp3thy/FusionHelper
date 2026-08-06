import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "no-save"
NUMBER = "R10"
RESTATEMENT = "Never save the document — checkpoint saves need a waiver naming user consent"

# Any attribute call named save/saveAs. A non-document .save() (rare in
# generated scripts) is a tolerable false positive: the waiver is the escape
# and it forces the reason to be stated.
_SAVERS = {"save", "saveAs"}

_FIX = ("remove the save; a consented checkpoint save is waived per line: "
        "# fusionhelper: allow R10 — user consented checkpoint after green verdict")


def check(tree: ast.AST, source: str) -> list[Finding]:
    findings = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in _SAVERS):
            findings.append(Finding(
                RULE_ID, NUMBER, node.lineno, node.col_offset, "error",
                f"{node.func.attr}() call — R10: saving is the user's decision; "
                "an unconsented save creates a cloud version the user did not ask for",
                _FIX))
    return findings
