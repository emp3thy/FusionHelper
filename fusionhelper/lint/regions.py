"""Line ranges lint must not judge: the appended verification stub and the
bundled kit block. Both are gate-owned text (the stub legitimately catches
exceptions to emit FH_VERDICT1; the kit is source-controlled and gated on
its own) — findings inside them would punish the author for code they
cannot edit."""
from fusionhelper.bundle import MARK_BEGIN_PREFIX, MARK_END
from fusionhelper.verify.stub_text import STUB_SENTINEL


def exempt_lines(source: str) -> set[int]:
    exempt: set[int] = set()
    in_kit = False
    in_stub = False
    for lineno, text in enumerate(source.splitlines(), start=1):
        stripped = text.strip()
        if not in_stub and stripped == STUB_SENTINEL:
            in_stub = True
        if not in_kit and stripped.startswith(MARK_BEGIN_PREFIX):
            in_kit = True
        if in_kit or in_stub:
            exempt.add(lineno)
        if in_kit and stripped == MARK_END:
            in_kit = False
    return exempt
