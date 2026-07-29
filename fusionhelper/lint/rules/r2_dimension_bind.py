import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "dimension-must-bind"
NUMBER = "R2"
RESTATEMENT = "Every sketchDimensions.add* must have .parameter.expression assigned"

KNOWN_BINDERS: set[str] = set()  # emit's helpers register here in phase 3

_FIX = "<var>.parameter.expression = '<parameter name or expression>'"


def _is_dim_create(call: ast.expr) -> bool:
    return (isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr.startswith("add")
            and isinstance(call.func.value, ast.Attribute)
            and call.func.value.attr == "sketchDimensions")


def check(tree: ast.AST, source: str) -> list[Finding]:
    creations: dict[str, ast.Assign] = {}
    bound: set[str] = set()
    escaped: set[str] = set()
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _is_dim_create(node.value):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                creations[node.targets[0].id] = node
        elif isinstance(node, ast.Expr) and _is_dim_create(node.value):
            findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset,
                                    "error", "dimension created and discarded — it can "
                                    "never be bound to a parameter (partially-bound "
                                    "dead-timeline trap)", _FIX))
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Attribute):
            tgt = node.targets[0]
            if (tgt.attr == "expression" and isinstance(tgt.value, ast.Attribute)
                    and tgt.value.attr == "parameter"
                    and isinstance(tgt.value.value, ast.Name)):
                bound.add(tgt.value.value.id)
        elif isinstance(node, ast.Call):
            for arg in list(node.args) + [kw.value for kw in node.keywords]:
                if isinstance(arg, ast.Name):
                    escaped.add(arg.id)
                elif isinstance(arg, (ast.List, ast.Tuple)):
                    escaped.update(e.id for e in arg.elts if isinstance(e, ast.Name))

    for name, assign in creations.items():
        if name not in bound and name not in escaped:
            findings.append(Finding(RULE_ID, NUMBER, assign.lineno, assign.col_offset,
                                    "error", f"dimension {name!r} is never bound — "
                                    "its .parameter.expression is never assigned "
                                    "(model looks parametric; this dimension is dead)",
                                    _FIX.replace("<var>", name)))
    return findings
