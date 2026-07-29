import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "no-stale-brep"
NUMBER = "R5"
RESTATEMENT = "Never use a BRep reference across a parameter change"

_FIX = ("capture entityToken before the parameter write and re-resolve with "
        "Design.findEntityByToken() after")


def check(tree: ast.AST, source: str) -> list[Finding]:
    findings = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Attribute)):
            continue
        tgt = node.targets[0]
        if tgt.attr not in {"expression", "value"}:
            continue
        # Immediate-receiver test: excluding receiver `parameter` (R2's binding)
        # catches des.userParameters.itemByName('w').expression = ... which a
        # full-chain test misses (attr_chain bails on the call mid-chain).
        recv = tgt.value
        if isinstance(recv, ast.Attribute) and recv.attr == "parameter":
            continue
        if isinstance(recv, ast.Name) and recv.id == "parameter":
            continue
        # False positive: plain-local .expression/.value writes (e.g., `param.expression = ...`)
        # are syntactically caught but semantically invalid (no such Fusion object). Accepted
        # trade-off: catches the hazardous case (itemByName().expression) and guides correct use.
        findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset, "warn",
                                "parameter write — any BRepFace/Edge held in a variable "
                                "is now dead document-wide (InternalValidationError on "
                                "next use)", _FIX))
    return findings
