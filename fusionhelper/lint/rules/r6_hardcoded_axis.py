import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "no-hardcoded-axis"
NUMBER = "R6"
RESTATEMENT = "Derive axis mapping from sketchToModelSpace() at runtime"

_INVERTING_PLANES = {"xZConstructionPlane", "yZConstructionPlane"}


def _is_all_literal_vector(node: ast.expr) -> bool:
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "Vector3D"):  # NOT Point3D: seeds are endorsed
        return False
    if not node.args:
        return False
    return all(isinstance(a, ast.Constant) or
               (isinstance(a, ast.UnaryOp) and isinstance(a.operand, ast.Constant))
               for a in node.args)


def check(tree: ast.AST, source: str) -> list[Finding]:
    findings = []
    calls_sketch_to_model = any(
        isinstance(n, ast.Attribute) and n.attr == "sketchToModelSpace"
        for n in ast.walk(tree))
    for node in ast.walk(tree):
        if isinstance(node, ast.expr) and _is_all_literal_vector(node):
            findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset,
                                    "error", "all-literal Vector3D.create — hardcoded "
                                    "axis assumption (the XZ inversion trap: on XZ, "
                                    "world_z = -sketch_y)",
                                    "derive the direction from sketch.sketchToModelSpace() "
                                    "or sketch.xDirection/yDirection at runtime"))
        elif (isinstance(node, ast.Attribute) and node.attr in _INVERTING_PLANES
              and not calls_sketch_to_model):
            findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset,
                                    "warn", f"{node.attr} used and sketchToModelSpace() "
                                    "never called — geometry drawn 'upright' on this "
                                    "plane lands inverted in world Z",
                                    "map sketch coords through sketch.sketchToModelSpace()"))
    return findings
