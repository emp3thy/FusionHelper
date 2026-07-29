import ast
import re

from fusionhelper.lint.findings import Finding

RULE_ID = "param-name-safe"
NUMBER = "R7"
RESTATEMENT = "Parameter names are multi-character snake_case"

# Case-sensitive, from fusion-api-notes §3: these throw at runtime.
_UNIT_SYMBOLS = {"W", "H", "R", "T", "mm", "cm", "m", "um", "nm", "in", "ft",
                 "yd", "mil", "thou", "deg", "rad"}
_FUNC_NAMES = {"PI", "E", "abs", "cos", "sin", "tan", "asin", "acos", "atan",
               "sqrt", "min", "max", "if", "floor", "ceil", "round", "log",
               "exp", "pow", "sign"}
_SNAKE = r"^[a-z_][a-z0-9_]*$"


def _receiver_is_user_parameters(func: ast.expr, aliases: set[str]) -> bool:
    if not (isinstance(func, ast.Attribute) and func.attr == "add"):
        return False
    recv = func.value
    if isinstance(recv, ast.Name):
        return recv.id in aliases
    return isinstance(recv, ast.Attribute) and recv.attr == "userParameters"


def check(tree: ast.AST, source: str) -> list[Finding]:
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Attribute)
                and node.value.attr == "userParameters"):
            aliases.add(node.targets[0].id)

    findings, seen = [], {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and node.args
                and _receiver_is_user_parameters(node.func, aliases)):
            continue
        arg = node.args[0]
        if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str)):
            continue  # dynamic name: nothing static to check
        name = arg.value
        loc = (node.lineno, node.col_offset)
        if name in _UNIT_SYMBOLS or name in _FUNC_NAMES:
            findings.append(Finding(RULE_ID, NUMBER, *loc, "error",
                                    f"Fusion rejects parameter name {name!r} "
                                    "(unit symbol / function name) with a misleading "
                                    "'param name is not valid'",
                                    f"rename to a multi-character snake_case name, "
                                    f"e.g. '{name.lower()}_val'"))
        elif not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            findings.append(Finding(RULE_ID, NUMBER, *loc, "error",
                                    f"malformed parameter name {name!r} — Fusion will "
                                    "throw 'param name is not valid'",
                                    "use letters, digits and underscores; start with a letter"))
        elif name in seen:
            findings.append(Finding(RULE_ID, NUMBER, *loc, "error",
                                    f"duplicate parameter name {name!r} (first added on "
                                    f"line {seen[name]}) — Fusion throws the same "
                                    "misleading 'param name is not valid'",
                                    "reference the existing parameter instead of re-adding"))
        elif not re.match(_SNAKE, name) or len(name) < 2:
            findings.append(Finding(RULE_ID, NUMBER, *loc, "warn",
                                    f"parameter name {name!r} is not multi-character "
                                    "snake_case (project policy avoids the whole "
                                    "rejected-name class)",
                                    "rename, e.g. 'outer_w', 'wall_t'"))
        if name not in seen:
            seen[name] = node.lineno
    return findings
