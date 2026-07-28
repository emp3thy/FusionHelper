import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "no-index-topology"
NUMBER = "R4"
RESTATEMENT = "Never select topology by index — geometric predicate or entityToken"

# NOT "bodies": Fusion's collection is bRepBodies; "bodies" caused a live
# false positive on a local variable matching by name alone.
_COLLECTIONS = {"faces", "edges", "vertices", "bRepBodies", "shells", "lumps"}

_FIX = ("select by geometric predicate (normal / centroid / area) or capture "
        "entityToken and re-resolve with Design.findEntityByToken()")


def _chain_text(node: ast.expr) -> str | None:
    """Dotted-chain source text, or None if anything but Name/Attribute appears."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _collection_receiver(node: ast.expr) -> str | None:
    """Return chain text when node is <dotted chain>.<collection>, else None."""
    if isinstance(node, ast.Attribute) and node.attr in _COLLECTIONS:
        return _chain_text(node)
    return None


class _RangeIterationTracker(ast.NodeVisitor):
    """Collects receiver chains exempted by `for i in range(<recv>.count)`."""

    def __init__(self):
        self.exempt: set[str] = set()

    def visit_For(self, node: ast.For):
        it = node.iter
        if (isinstance(it, ast.Call) and isinstance(it.func, ast.Name)
                and it.func.id == "range" and len(it.args) == 1
                and isinstance(it.args[0], ast.Attribute)
                and it.args[0].attr == "count"):
            recv = _collection_receiver(it.args[0].value)
            if recv:
                self.exempt.add(recv)
        self.generic_visit(node)


def check(tree: ast.AST, source: str) -> list[Finding]:
    tracker = _RangeIterationTracker()
    tracker.visit(tree)
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            recv = _collection_receiver(node.value)
            if recv is not None and recv not in tracker.exempt:
                # profiles.item(0) exclusion is structural: "profiles" is not in _COLLECTIONS
                findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset, "error",
                                        f"index pick on {recv} — breaks when face/edge count "
                                        "changes (P4: face[4] silently became a different face "
                                        "after a chamfer)", _FIX))
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "item"):
            recv = _collection_receiver(node.func.value)
            if recv is not None and recv not in tracker.exempt:
                # profiles.item(0) exclusion is structural: "profiles" is not in _COLLECTIONS
                findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset, "error",
                                        f"index pick on {recv} — breaks when face/edge count "
                                        "changes (P4: face[4] silently became a different face "
                                        "after a chamfer)", _FIX))
    return findings
