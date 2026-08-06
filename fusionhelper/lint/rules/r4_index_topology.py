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


def _collection_chain(node: ast.expr) -> str | None:
    """Chain text when node is a pure dotted chain ending in a collection."""
    if isinstance(node, ast.Attribute) and node.attr in _COLLECTIONS:
        return _chain_text(node)
    return None


def _alias_map(tree: ast.AST) -> dict[str, str]:
    """Names assigned EXACTLY ONCE in the file, to a collection chain.

    Whole-file, single-assignment scope on purpose: generated scripts are
    flat, and a name rebound anywhere is no longer a trusted alias (the
    false-positive guard). A local alias walking past the rule was the
    review-confirmed false negative this closes.
    """
    counts: dict[str, int] = {}
    values: dict[str, str] = {}

    def _bind(name: str) -> None:
        counts[name] = counts.get(name, 0) + 1

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        _bind(n.id)
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                chain = _collection_chain(node.value)
                if chain:
                    values[node.targets[0].id] = chain
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.For, ast.AsyncFor,
                                ast.comprehension)):
            for n in ast.walk(node.target):
                if isinstance(n, ast.Name):
                    _bind(n.id)
        elif isinstance(node, ast.arg):
            _bind(node.arg)
    return {name: chain for name, chain in values.items() if counts.get(name) == 1}


def _receiver(node: ast.expr, aliases: dict[str, str]) -> str | None:
    chain = _collection_chain(node)
    if chain is not None:
        return chain
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    return None


class _RangeIterationTracker(ast.NodeVisitor):
    """Collects the nodes exempted by `for i in range(<recv>.count)` loops.

    The exemption is scoped to the matched loop's OWN subtree, keyed by node
    identity — never by receiver-chain text globally. (BugBot on PR #1 proved
    the text-global version silently exempted a literal `body.faces[4]`
    elsewhere in the file once any range-count loop over that chain existed.)
    """

    def __init__(self, aliases: dict[str, str]):
        self.aliases = aliases
        self.exempt_nodes: set[int] = set()

    def visit_For(self, node: ast.For):
        it = node.iter
        if (isinstance(it, ast.Call) and isinstance(it.func, ast.Name)
                and it.func.id == "range" and len(it.args) == 1
                and isinstance(it.args[0], ast.Attribute)
                and it.args[0].attr == "count"
                and isinstance(node.target, ast.Name)):
            recv = _receiver(it.args[0].value, self.aliases)
            loop_var = node.target.id

            def _is_loop_var(expr):
                return isinstance(expr, ast.Name) and expr.id == loop_var

            if recv:
                # exempt only <recv>[<loop var>] / <recv>.item(<loop var>)
                # inside THIS loop -- a literal index in the loop body is
                # still the P4 hazard (BugBot, PR #1, second pass)
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Subscript):
                        if (_receiver(sub.value, self.aliases) == recv
                                and _is_loop_var(sub.slice)):
                            self.exempt_nodes.add(id(sub))
                    elif (isinstance(sub, ast.Call)
                          and isinstance(sub.func, ast.Attribute)
                          and sub.func.attr == "item"
                          and _receiver(sub.func.value, self.aliases) == recv
                          and len(sub.args) == 1
                          and _is_loop_var(sub.args[0])):
                        self.exempt_nodes.add(id(sub))
        self.generic_visit(node)


def check(tree: ast.AST, source: str) -> list[Finding]:
    aliases = _alias_map(tree)
    tracker = _RangeIterationTracker(aliases)
    tracker.visit(tree)
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript):
            recv = _receiver(node.value, aliases)
            if recv is not None and id(node) not in tracker.exempt_nodes:
                # profiles.item(0) exclusion is structural: "profiles" is not in _COLLECTIONS
                findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset, "error",
                                        f"index pick on {recv} — breaks when face/edge count "
                                        "changes (P4: face[4] silently became a different face "
                                        "after a chamfer)", _FIX))
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "item"):
            recv = _receiver(node.func.value, aliases)
            if recv is not None and id(node) not in tracker.exempt_nodes:
                # profiles.item(0) exclusion is structural: "profiles" is not in _COLLECTIONS
                findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset, "error",
                                        f"index pick on {recv} — breaks when face/edge count "
                                        "changes (P4: face[4] silently became a different face "
                                        "after a chamfer)", _FIX))
    return findings
