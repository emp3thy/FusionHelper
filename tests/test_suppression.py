from fusionhelper import lint

SUPPRESSED = (
    "import adsk.core\n\n\n"
    "def run(_context: str):\n"
    "    v = adsk.core.ValueInput.createByReal(0.6)"
    "  # fusionhelper: allow R1 — legacy shim kept verbatim\n"
    "    print(v)\n"
)

SHORT_REASON = (
    "import adsk.core\n\n\n"
    "def run(_context: str):\n"
    "    v = adsk.core.ValueInput.createByReal(0.6)  # fusionhelper: allow R1 — because\n"
    "    print(v)\n"
)

UNKNOWN_RULE = "x = 1  # fusionhelper: allow R99 — this rule id does not exist anywhere\n"
UNUSED = "x = 1  # fusionhelper: allow R1 — nothing on this line violates anything\n"


def test_valid_waiver_suppresses_and_is_reported():
    r = lint.run(SUPPRESSED)
    assert [f.rule_number for f in r.findings] == []
    assert len(r.waivers) == 1
    assert r.waivers[0].rule_number == "R1"


def test_reason_under_12_chars_is_an_error_and_does_not_suppress():
    r = lint.run(SHORT_REASON)
    assert sorted(f.rule_number for f in r.findings) == ["R1", "WAIVER"]


def test_unknown_rule_id_is_an_error():
    r = lint.run(UNKNOWN_RULE)
    assert [(f.rule_number, f.severity) for f in r.findings] == [("WAIVER", "error")]


def test_unused_suppression_is_a_warning():
    r = lint.run(UNUSED)
    assert [(f.rule_number, f.severity) for f in r.findings] == [("WAIVER", "warn")]
