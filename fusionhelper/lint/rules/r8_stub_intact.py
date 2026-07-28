from fusionhelper import verify
from fusionhelper.lint.findings import Finding

RULE_ID = "verify-stub-intact"
NUMBER = "R8"
RESTATEMENT = "The file ends with the verification stub, unmodified"

_FIX = "regenerate the script tail with fusionhelper.verify.append_to(script_text)"


def _norm(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def check_text(source: str) -> list[Finding]:
    """Positional rule: called by preflight when expect_stub=True, not from ALL_RULES."""
    if _norm(source).endswith(_norm(verify.STUB_TEXT)):
        return []
    last_line = source.count("\n") + 1
    if verify.STUB_SENTINEL not in source:
        msg = "verification stub missing — the script will build and never verify"
    else:
        # Sentinel is present; examine the tail from its last occurrence
        pos = source.rfind(verify.STUB_SENTINEL)
        tail = source[pos:]
        norm_tail = _norm(tail)
        norm_stub = _norm(verify.STUB_TEXT)
        # If tail starts with the intact stub and is longer, code was appended
        if norm_tail.startswith(norm_stub) and len(norm_tail) > len(norm_stub):
            msg = ("code appears after the stub — a later `def run` would discard the "
                   "wrapper: the script builds geometry and prints nothing (the silent case)")
        else:
            msg = "verification stub present but modified — exact stub text required"
    return [Finding(RULE_ID, NUMBER, last_line, 0, "error", msg, _FIX)]


def check(tree, source):  # rule-contract shim; engine-level runs skip R8
    return []
