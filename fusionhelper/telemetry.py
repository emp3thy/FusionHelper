"""Session telemetry: one JSONL line per part-request, so the skill's effect
is a number, not folklore. The metric the external review asked for —
green-verdict-on-first-execute — is `summary`'s first line. Location:
FH_TELEMETRY env var, else <FUSIONHELPER_HOME>/telemetry.jsonl (same home
the verify block installs to)."""
import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from fusionhelper import verify

ENV_VAR = "FH_TELEMETRY"
VERDICTS = ("pass", "fail", "abandoned")


def default_path() -> Path:
    env = os.environ.get(ENV_VAR)
    if env:
        return Path(env)
    return verify.default_home() / "telemetry.jsonl"


def record_entry(*, script: str, verdict: str, executes: int,
                 preflight_attempts: int = 0, rules_fired: list[str] | None = None,
                 notes: str = "", ts: str | None = None,
                 path: Path | None = None) -> Path:
    if verdict not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}, got {verdict!r}")
    target = path if path is not None else default_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": ts if ts is not None else datetime.now(UTC).isoformat(),
        "script": script,
        "verdict": verdict,
        "executes": executes,
        "preflight_attempts": preflight_attempts,
        "rules_fired": rules_fired or [],
        "notes": notes,
    }
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    return target


def summarize(path: Path | None = None) -> dict:
    target = path if path is not None else default_path()
    entries = []
    skipped_lines = 0
    if target.is_file():
        for line in target.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    skipped_lines += 1
    sessions = len(entries)
    green = sum(1 for e in entries
                if e.get("verdict") == "pass" and e.get("executes") == 1)
    mean = (sum(e.get("executes", 0) for e in entries) / sessions) if sessions else 0.0
    rule_counts: dict[str, int] = {}
    for e in entries:
        for r in e.get("rules_fired", []):
            rule_counts[r] = rule_counts.get(r, 0) + 1
    return {"sessions": sessions, "first_execute_green": green,
            "mean_executes": mean, "rule_counts": rule_counts,
            "skipped_lines": skipped_lines}


def _render_summary(s: dict) -> str:
    rate = f"{s['first_execute_green']}/{s['sessions']}"
    pct = (100.0 * s["first_execute_green"] / s["sessions"]) if s["sessions"] else 0.0
    rules = " ".join(f"{k}={v}" for k, v in
                     sorted(s["rule_counts"].items(), key=lambda kv: -kv[1]))
    lines = [
        f"sessions: {s['sessions']}",
        f"first-execute green: {rate} ({pct:.0f}%)",
        f"mean executes: {s['mean_executes']:.1f}",
        f"rules fired: {rules or '(none)'}",
    ]
    if s.get("skipped_lines", 0) > 0:
        lines.append(f"skipped lines: {s['skipped_lines']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m fusionhelper.telemetry")
    sub = parser.add_subparsers(dest="cmd", required=True)
    rec = sub.add_parser("record", help="append one session entry")
    rec.add_argument("--script", required=True)
    rec.add_argument("--verdict", required=True, choices=VERDICTS)
    rec.add_argument("--executes", required=True, type=int)
    rec.add_argument("--preflight-attempts", type=int, default=0)
    rec.add_argument("--rules-fired", default="",
                     help="comma-separated rule numbers that fired during preflight")
    rec.add_argument("--notes", default="")
    sub.add_parser("summary", help="print aggregate metrics")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "record":
            rules = [r for r in args.rules_fired.split(",") if r]
            out = record_entry(script=args.script, verdict=args.verdict,
                               executes=args.executes,
                               preflight_attempts=args.preflight_attempts,
                               rules_fired=rules, notes=args.notes)
            print(out)
        else:
            print(_render_summary(summarize()))
    except OSError as e:
        print(f"TELEMETRY FAILED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
