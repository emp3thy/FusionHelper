"""Render a findings list. HARD INVARIANT: verdict, counts and coverage line
are derived from the findings list at render time — never from a counter
maintained alongside. A PASS header above a list of errors would destroy the
gate's credibility in one sighting."""
from fusionhelper.lint.findings import RULES

COVERAGE = ("checked: R1 R2 R4 R5 R6 R7 R8 · not checked: R3 R9 R10 · "
            "R5 covers parameter-change only")


def report(findings, waivers, source, path, coverage=COVERAGE):
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
    out.append(coverage)
    return "\n".join(out)
