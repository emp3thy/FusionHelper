import re
from pathlib import Path

SKILL = Path(__file__).parents[1] / "skills" / "fusion-design" / "SKILL.md"


def test_skill_exists_with_frontmatter():
    text = SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    assert "name: fusion-design" in text


def test_all_ten_rules_present_and_numbered():
    text = SKILL.read_text(encoding="utf-8")
    for n in range(1, 11):
        assert re.search(rf"\bR{n}\b", text), f"R{n} missing"


def test_skill_cites_the_real_cli_and_reference_files():
    text = SKILL.read_text(encoding="utf-8")
    assert "python -m fusionhelper.preflight" in text
    assert "python -m fusionhelper.telemetry record" in text
    for ref in ("api-recipes.md", "axis-mapping.md", "limits.md", "hazards.md"):
        assert ref in text
        assert (SKILL.parent / "reference" / ref).is_file()


def test_repair_budgets_match_design():
    text = SKILL.read_text(encoding="utf-8")
    assert "5" in text and "identical failure signature twice" in text


def test_stub_gap_escape_route_documented():
    text = SKILL.read_text(encoding="utf-8")
    assert "stub gap" in text.lower()
    assert "setDistanceExtent" in text
    assert re.search(r"lint\s+suppressions do not apply to pyright findings", text)


def test_skill_stays_resident_sized():
    # The external review's finding: appended lab-notebook sections were
    # diluting the ten rules. Hazard lore lives in reference/hazards.md.
    text = SKILL.read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 240, "SKILL.md is regrowing — move lore to reference/"


def test_waiver_scope_names_the_checked_rules():
    text = SKILL.read_text(encoding="utf-8")
    assert "R1 R2 R4 R5 R6 R7 R9 R10 R11" in text  # waivable checked rules
