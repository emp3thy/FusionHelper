"""Bundler contract: expand the kit import, append the stub, refuse
invalid input, stay deterministic."""
import re
import subprocess
import sys
from pathlib import Path

import pytest

from fusionhelper import bundle, verify

FIX = Path(__file__).parent / "fixtures" / "bundle"
AUTHOR = (FIX / "author_ok.py").read_text(encoding="utf-8")
KIT = bundle._kit_source()
KIT_VERSION = bundle._extract_kit_version(KIT)


def test_bundle_expands_import_and_appends_stub():
    out = bundle.bundle_text(AUTHOR, KIT)
    assert not re.search(r"^\s*from fusionhelper\.buildkit import", out, re.MULTILINE)
    assert "class BuildCtx" in out
    assert out.rstrip().endswith(verify.STUB_TEXT.rstrip())
    assert f"# fh-bundle: kit begin v{KIT_VERSION}" in out
    assert "# fh-bundle: kit end" in out


def test_bundle_is_deterministic():
    assert bundle.bundle_text(AUTHOR, KIT) == bundle.bundle_text(AUTHOR, KIT)


def test_refuses_already_bundled():
    once = bundle.bundle_text(AUTHOR, KIT)
    with pytest.raises(bundle.BundleError, match="already bundled"):
        bundle.bundle_text(once, KIT)


def test_refuses_missing_import():
    with pytest.raises(bundle.BundleError, match="buildkit import"):
        bundle.bundle_text("def run(_c):\n    pass\n", KIT)


def test_refuses_author_with_stub():
    with_stub = verify.append_to(AUTHOR)
    with pytest.raises(bundle.BundleError, match="stub"):
        bundle.bundle_text(with_stub, KIT)


def test_refuses_kit_name_collision():
    author = AUTHOR + "\n\nclass BuildCtx:\n    pass\n"
    with pytest.raises(bundle.BundleError, match="collision"):
        bundle.bundle_text(author, KIT)


def test_bundle_file_writes_artifact(tmp_path):
    src = tmp_path / "myscript.py"
    src.write_text(AUTHOR, encoding="utf-8")
    out_path = bundle.bundle_file(src)
    assert out_path == tmp_path / "myscript.bundled.py"
    assert "class BuildCtx" in out_path.read_text(encoding="utf-8")


def test_artifact_compiles():
    compile(bundle.bundle_text(AUTHOR, KIT), "artifact.py", "exec")


def test_bundle_import_has_no_side_effects():
    """Verify importing bundle does not pollute sys.modules with adsk."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import fusionhelper.bundle; exit(1 if 'adsk' in __import__('sys').modules else 0)",
        ],
        cwd=Path(__file__).parent.parent,
    )
    assert result.returncode == 0, "importing bundle must not inject adsk into sys.modules"


def test_cli_works_in_clean_process(tmp_path):
    """Verify the bundler CLI works in a fresh process without Fusion."""
    author_file = tmp_path / "test_author.py"
    author_file.write_text(AUTHOR, encoding="utf-8")
    bundled_file = tmp_path / "test_author.bundled.py"

    result = subprocess.run(
        [sys.executable, "-m", "fusionhelper.bundle", str(author_file)],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert bundled_file.exists(), f"artifact not created; output: {result.stdout}"
    assert "class BuildCtx" in bundled_file.read_text(encoding="utf-8")

    bundled_file.unlink()
