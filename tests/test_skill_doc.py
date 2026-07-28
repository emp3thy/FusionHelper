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
    for ref in ("api-recipes.md", "axis-mapping.md", "limits.md"):
        assert ref in text
        assert (SKILL.parent / "reference" / ref).is_file()


def test_repair_budgets_match_design():
    text = SKILL.read_text(encoding="utf-8")
    assert "5" in text and "identical failure signature twice" in text
