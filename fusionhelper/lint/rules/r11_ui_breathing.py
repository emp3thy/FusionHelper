import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "loops-must-breathe"
NUMBER = "R11"
RESTATEMENT = "Loops that mutate the document call adsk.doEvents() per iteration"

# Calls that block the UI thread for noticeable time per invocation.
# Scripts run ON Fusion's UI thread: a loop of these with no doEvents()
# freezes the window for the loop's whole duration (measured 2026-07-31:
# an unbroken run of component ops froze Fusion for an hour and the user
# force-killed it; the identical work with per-iteration doEvents ran
# with a live window).
_MUTATING = {
    "add", "deleteMe", "moveToComponent", "addExistingComponent",
    "addNewComponent", "copyToComponent",
}


def _loop_calls(node):
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            yield n.func.attr


def check(tree: ast.AST, source: str) -> list[Finding]:
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.For, ast.While)):
            continue
        attrs = list(_loop_calls(node))
        if "doEvents" in attrs:
            continue
        hits = [a for a in attrs if a in _MUTATING]
        if len(hits) == 0:
            continue
        findings.append(Finding(
            RULE_ID, NUMBER, node.lineno, node.col_offset, "warn",
            "loop mutates the document (%s) without adsk.doEvents() — "
            "scripts run on the UI thread and an unbroken loop freezes "
            "the window for its whole duration" % ", ".join(sorted(set(hits))[:3]),
            "call adsk.doEvents() once per iteration (or per small batch) "
            "inside the loop body"))
    return findings
