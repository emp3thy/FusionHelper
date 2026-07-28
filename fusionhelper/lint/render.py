"""Render a findings list. HARD INVARIANT: verdict, counts and coverage line
are derived from the findings list at render time — never from a counter
maintained alongside. A PASS header above a list of errors would destroy the
gate's credibility in one sighting.

The coverage line is likewise derived, never hardcoded: it must tell the
truth about what THIS run actually checked, not what the rule set could check
in the best case (e.g. R8 only fires when the caller asked for it — printing
it as "checked" on a run that skipped it would be a silent lie)."""
from fusionhelper.lint.findings import RULES

# Bare renderer / bare lint.run default: every rule the engine can check,
# except R8 — R8 only runs when a caller (preflight, with expect_stub=True)
# opts in explicitly and says so via the `checked` argument.
_DEFAULT_CHECKED = frozenset(n for n, info in RULES.items() if info.checked) - {"R8"}


def _coverage_line(checked):
    if checked is None:
        checked = _DEFAULT_CHECKED
    checked = {n for n in checked if RULES.get(n) is not None and RULES[n].checked}
    checked_line = " ".join(n for n in RULES if n in checked)
    not_checked_line = " ".join(n for n in RULES if n not in checked)
    return (f"checked: {checked_line} · not checked: {not_checked_line} · "
            "R5 covers parameter-change only")


def report(findings, waivers, source, path, checked=None):
    errors = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]
    verdict = "PASS" if not errors else "FAIL"
    out = [f"LINT {verdict} errors={len(errors)} warns={len(warns)}"]
    lines = source.splitlines()
    by_rule: dict[str, list] = {}
    for f in sorted(findings, key=lambda f: (f.rule_number, f.line, f.col)):
        by_rule.setdefault(f.rule_number, []).append(f)
    for number, group in by_rule.items():
        info = RULES.get(number)
        out.append("")
        out.append(f"{number} {info.restatement if info else ''}".rstrip())
        for f in group:
            out.append(f"  {path}:{f.line}:{f.col + 1} [{f.severity}] {f.message}")
            if 1 <= f.line <= len(lines):
                excerpt = lines[f.line - 1]
                out.append(f"    {excerpt}")
                out.append(f"    {' ' * f.col}^")
            if f.fix:
                out.append(f"    fix: {f.fix}")
    for w in waivers:
        out.append(f"waiver: line {w.line} {w.rule_number} — {w.reason}")
    out.append(_coverage_line(checked))
    return "\n".join(out)
