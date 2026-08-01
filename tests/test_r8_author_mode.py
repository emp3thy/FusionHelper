"""Inverted R8: author scripts (buildkit import, no bundle markers) must
NOT contain the stub or kit-named defs; bundled artifacts keep the
existing stub-intact rule."""
from pathlib import Path

from fusionhelper import bundle, verify
from fusionhelper.lint.rules import r8_stub_intact as r8

FIX = Path(__file__).parent / "fixtures" / "bundle"
AUTHOR = (FIX / "author_ok.py").read_text(encoding="utf-8")
KIT = bundle._kit_source()


def test_clean_author_passes():
    assert r8.is_author(AUTHOR)
    assert r8.check_author_text(AUTHOR) == []


def test_author_with_stub_fails():
    (f,) = r8.check_author_text(verify.append_to(AUTHOR))
    assert f.rule_number == "R8"
    assert "bundler owns the stub" in f.message


def test_author_with_kit_def_fails():
    (f,) = r8.check_author_text(AUTHOR + "\nclass BuildCtx:\n    pass\n")
    assert f.rule_number == "R8"
    assert "BuildCtx" in f.message


def test_bundled_artifact_is_not_author_and_passes_stub_mode():
    artifact = bundle.bundle_text(AUTHOR, KIT)
    assert not r8.is_author(artifact)          # markers present
    assert r8.check_text(artifact) == []       # existing mode still green


def test_plain_script_without_kit_import_is_not_author():
    assert not r8.is_author("def run(_c):\n    pass\n")
