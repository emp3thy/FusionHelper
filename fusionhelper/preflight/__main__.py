import argparse
import sys
from pathlib import Path

from fusionhelper.preflight import Outcome, run_preflight


def main(argv: list[str] | None = None) -> int:
    # A narrow console codepage (e.g. Windows' legacy cp437/cp850) cannot encode
    # the em dashes and middle dots used throughout rule restatements and the
    # coverage line. Without this, a real gate result would crash on print()
    # with a raw UnicodeEncodeError instead of ever reaching the user.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(errors="replace")
    ap = argparse.ArgumentParser(prog="python -m fusionhelper.preflight",
                                 description="Offline gate: pyright + lint + canary")
    ap.add_argument("script", nargs="?", help="generated Fusion script to check")
    ap.add_argument("--no-stub", action="store_true",
                    help="do not require the verification stub (R8)")
    args = ap.parse_args(argv)
    if not args.script:
        ap.print_usage(sys.stderr)
        return Outcome.USAGE.value
    result = run_preflight(Path(args.script), expect_stub=not args.no_stub)
    print(result.report)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
