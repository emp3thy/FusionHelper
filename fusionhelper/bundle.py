"""Bundle an author script into the single self-contained artifact that
reaches Fusion: the `from fusionhelper.buildkit import ...` line is
replaced by the kit source (wrapped in versioned markers) and the
verification stub is appended. Deterministic: same author + same kit ->
byte-identical artifact. Preflight/lint gate the ARTIFACT."""
import hashlib
import re
import sys
from pathlib import Path

from fusionhelper import verify

IMPORT_RE = re.compile(
    r"^from fusionhelper\.buildkit import .+$", re.MULTILINE)
MARK_BEGIN = "# fh-bundle: kit begin v%s %s"
MARK_END = "# fh-bundle: kit end"

# Top-level names the kit injects; an author redefining one shadows the
# kit silently at runtime, so it is a bundling error.
_KIT_NAMES = ("BuildCtx", "KIT_VERSION")


class BundleError(RuntimeError):
    pass


def _kit_source() -> str:
    kit_path = Path(__file__).parent / "buildkit.py"
    return kit_path.read_text(encoding="utf-8")


def _extract_kit_version(kit_source: str) -> str:
    match = re.search(r'^KIT_VERSION = "(.+)"$', kit_source, re.MULTILINE)
    if match is None:
        raise BundleError(
            "kit source missing KIT_VERSION assignment - "
            "expected: KIT_VERSION = \"...\"")
    return match.group(1)


def bundle_text(author_text: str, kit_source: str) -> str:
    if MARK_END in author_text or "# fh-bundle: kit begin" in author_text:
        raise BundleError("input is already bundled")
    if verify.STUB_SENTINEL in author_text:
        raise BundleError(
            "author script contains the verification stub - the bundler "
            "owns the stub; remove it from the author")
    m = IMPORT_RE.search(author_text)
    if m is None:
        raise BundleError(
            "no buildkit import found - author scripts must contain "
            "'from fusionhelper.buildkit import ...'")
    for name in _KIT_NAMES:
        if re.search(rf"^((class|def) {name}\b|{name}\s*=)", author_text,
                     re.MULTILINE):
            raise BundleError(f"kit name collision: author defines {name!r}")
    kit_version = _extract_kit_version(kit_source)
    kit_hash = hashlib.sha256(kit_source.encode("utf-8")).hexdigest()[:12]
    block = "\n".join((
        MARK_BEGIN % (kit_version, kit_hash),
        kit_source.rstrip("\n"),
        MARK_END,
    ))
    expanded = author_text[:m.start()] + block + author_text[m.end():]
    return verify.append_to(expanded)


def bundle_file(path: Path) -> Path:
    out = path.with_name(path.stem + ".bundled.py")
    artifact = bundle_text(path.read_text(encoding="utf-8"), _kit_source())
    out.write_text(artifact, encoding="utf-8", newline="\n")
    return out


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python -m fusionhelper.bundle <author-script.py>")
        return 2
    try:
        out = bundle_file(Path(args[0]))
    except (BundleError, OSError) as e:
        print(f"BUNDLE FAILED: {e}")
        return 1
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
