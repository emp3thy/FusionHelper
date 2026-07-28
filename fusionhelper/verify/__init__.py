"""Public face of the verification block.

fh_verify.py is DATA to this package: it is read as text and installed to the
user's FUSIONHELPER_HOME, then exec'd inside Fusion by the stub. It is never
imported here — importing would fail outside Fusion (no adsk module) and
Fusion caches imports across script runs, which is why the stub execs.
"""
import os
from pathlib import Path

from fusionhelper.verify.stub_text import STUB_SENTINEL, STUB_TEXT, append_to

__all__ = ["STUB_SENTINEL", "STUB_TEXT", "append_to", "block_source", "install_block"]

_BLOCK = Path(__file__).parent / "fh_verify.py"


def block_source() -> str:
    return _BLOCK.read_text(encoding="utf-8")


def default_home() -> Path:
    env = os.environ.get("FUSIONHELPER_HOME")
    if env:
        return Path(env)
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "FusionHelper"


def install_block(home: Path | None = None) -> Path:
    """Write fh_verify.py where the stub's _fh_verify_entry will look for it."""
    target_dir = Path(home) if home is not None else default_home()
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / "fh_verify.py"
    dest.write_text(block_source(), encoding="utf-8", newline="\n")
    return dest
