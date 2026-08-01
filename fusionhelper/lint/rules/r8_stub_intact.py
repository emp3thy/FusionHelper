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
    msg += " (R8 is not waivable — regenerate the tail)"
    return [Finding(RULE_ID, NUMBER, last_line, 0, "error", msg, _FIX)]


def check(tree, source):  # rule-contract shim; engine-level runs skip R8
    return []


# ---- author mode (buildkit workflow) ------------------------------------
# An AUTHOR script (buildkit import present, no bundle markers) must NOT
# contain the stub or kit-level defs: the bundler owns both. The bundled
# ARTIFACT keeps the original rule above. Mode is selected by marker
# presence — see fusionhelper.bundle.

_KIT_DEF_NAMES = ("BuildCtx", "KIT_VERSION")


def is_author(source: str) -> bool:
    from fusionhelper import bundle
    return (bundle.IMPORT_RE.search(source) is not None
            and bundle.MARK_END not in source
            and "# fh-bundle: kit begin" not in source)


def check_author_text(source: str) -> list[Finding]:
    import re
    findings = []
    if verify.STUB_SENTINEL in source:
        line = source[:source.rfind(verify.STUB_SENTINEL)].count("\n") + 1
        findings.append(Finding(
            RULE_ID, NUMBER, line, 0, "error",
            "author script contains the verification stub - the bundler "
            "owns the stub in the buildkit workflow (R8 author mode)",
            "delete the stub block; python -m fusionhelper.bundle appends it"))
    for name in _KIT_DEF_NAMES:
        m = re.search(rf"^((class|def) {name}\b|{name}\s*=)", source,
                      re.MULTILINE)
        if m:
            line = source[:m.start()].count("\n") + 1
            findings.append(Finding(
                RULE_ID, NUMBER, line, 0, "error",
                f"author script defines kit name {name!r} - it would shadow the "
                f"inlined kit at runtime",
                f"rename the local definition; the kit provides {name}"))
    return findings
