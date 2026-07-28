import ast
from pathlib import Path

from fusionhelper import verify


def test_reexports_are_the_single_source_of_truth():
    from fusionhelper.verify import stub_text
    assert verify.STUB_TEXT is stub_text.STUB_TEXT
    assert verify.STUB_SENTINEL in verify.STUB_TEXT


def test_append_to_normalises_the_seam():
    out = verify.append_to("def run(_context: str):\n    pass\n\n\n\n")
    assert out.endswith(verify.STUB_TEXT)
    assert "\n\n\n\n\n" not in out


def test_install_block_writes_the_packaged_source(tmp_path: Path):
    dest = verify.install_block(home=tmp_path)
    assert dest == tmp_path / "fh_verify.py"
    src = dest.read_text(encoding="utf-8")
    assert src == verify.block_source()
    ast.parse(src)  # the installed block must at minimum parse
