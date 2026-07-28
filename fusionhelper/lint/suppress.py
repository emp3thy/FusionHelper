"""Line-scoped waivers: `# fusionhelper: allow <rule-id-or-number> — <reason>`.

No file-level pragma, no --ignore flag (spec: a file-level waiver is one edit
that silently disables a rule for a 400-line script). Waivers print on every
run including PASS — a waiver nobody sees is the same as no rule.
"""
import re
from dataclasses import dataclass

from fusionhelper.lint.findings import BY_ID, RULES, Finding

_WAIVER = re.compile(r"#\s*fusionhelper:\s*allow\s+(\S+)\s*[—-]\s*(.*)$")
MIN_REASON = 12


@dataclass(frozen=True)
class Waiver:
    line: int
    rule_number: str
    reason: str


def apply(source, findings):
    kept, honoured, defects = list(findings), [], []
    for lineno, text in enumerate(source.splitlines(), start=1):
        m = _WAIVER.search(text)
        if not m:
            continue
        raw, reason = m.group(1), m.group(2).strip()
        info = RULES.get(raw) or BY_ID.get(raw)
        if info is None:
            defects.append(Finding("waiver", "WAIVER", lineno, 0, "error",
                                   f"unknown rule id {raw!r} in suppression"))
            continue
        if len(reason) < MIN_REASON:
            defects.append(Finding("waiver", "WAIVER", lineno, 0, "error",
                                   f"suppression reason too short (<{MIN_REASON} chars); "
                                   "state why the exception is safe"))
            continue
        matched = [f for f in kept if f.line == lineno and f.rule_number == info.number]
        if not matched:
            defects.append(Finding("waiver", "WAIVER", lineno, 0, "warn",
                                   f"unused suppression for {info.number}"))
            continue
        for f in matched:
            kept.remove(f)
        honoured.append(Waiver(lineno, info.number, reason))
    return kept, honoured, defects
