from fusionhelper.bundle import MARK_BEGIN, MARK_END
from fusionhelper.lint import regions
from fusionhelper.verify.stub_text import STUB_SENTINEL


def test_plain_script_has_no_exempt_lines():
    assert regions.exempt_lines("x = 1\ny = 2\n") == set()


def test_stub_region_runs_from_sentinel_to_eof():
    src = "x = 1\n\n\n" + STUB_SENTINEL + "\ntry:\n    pass\nexcept Exception:\n    pass\n"
    exempt = regions.exempt_lines(src)
    assert 4 in exempt and 5 in exempt and 8 in exempt
    assert 1 not in exempt


def test_kit_region_is_bounded_by_markers():
    src = "\n".join([
        "a = 1",
        MARK_BEGIN % ("2", "abc123"),
        "try:",
        "    pass",
        "except Exception:",
        "    pass",
        MARK_END,
        "b = 2",
    ]) + "\n"
    exempt = regions.exempt_lines(src)
    assert exempt == {2, 3, 4, 5, 6, 7}


def test_unterminated_kit_region_extends_to_eof():
    src = "a = 1\n" + (MARK_BEGIN % ("2", "abc123")) + "\ntry:\n    pass\n"
    assert regions.exempt_lines(src) == {2, 3, 4}
