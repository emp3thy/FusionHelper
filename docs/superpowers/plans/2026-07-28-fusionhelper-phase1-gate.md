# FusionHelper Phase 1 — The Gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the offline gate — `fusionhelper.preflight` (pyright + seven lint rules), `fusionhelper.verify` (wire the existing 1253-line verification block into the package), and the `fusion-design` skill's standing rules — so a generated Fusion script is statically checked before Fusion sees it and numerically verified after it runs.

**Architecture:** A plain Python package (`fusionhelper/`) plus a Claude Code skill (`skills/fusion-design/SKILL.md`). Lint rules are `ast.NodeVisitor` passes over one shared parse. Preflight stages the script into an isolated temp dir, generates `pyrightconfig.json` programmatically, runs pyright against Autodesk's shipped stubs, and runs a canary on every invocation — three outcomes: `PASS` / `FAIL` / `GATE_BROKEN`. The verification block already exists at `design/verify/` (43 offline tests passing) and is moved into the package, not rewritten. Transport is Autodesk's own Fusion MCP; we build nothing there.

**Tech Stack:** Python ≥3.12 (dev machine; the verify block itself runs inside Fusion's CPython 3.14 and stays 3.8-compatible as written), pyright (runtime dep, pinned), pytest, ruff, GitHub Actions (ubuntu + windows).

**Scope note:** This plan is Phase 1 only, per the spec's own phasing ("The three components are not equally urgent and should not be one undifferentiated plan"). Phase 2 (declaration block, dimensional-chain check, full skill workflow) and Phase 3 (`emit`) get their own plans. `pyyaml` is deliberately NOT a Phase 1 dependency.

## Global Constraints

Copied verbatim from the spec and `docs/detailed-design.md`; every task's requirements implicitly include these.

- **The gate fails OPEN** — a malformed `pyrightconfig.json` makes pyright fall back to defaults and exit normally. Therefore: config generated programmatically with `json.dump` (never templated, never hand-maintained); a **canary on every invocation** (a known-bad probe asserted to be flagged); three outcomes `PASS` / `FAIL` / `GATE_BROKEN`, and `GATE_BROKEN` is never reported as a pass.
- **Pyright config, exact values:** `"include"` names the single staged file (never `["."]`), `"typeCheckingMode": "basic"`, `"pythonVersion": "3.14"` (Fusion's measured runtime), `"reportMissingImports": "error"`, `"reportAttributeAccessIssue": "error"`, `"reportArgumentType": "none"` (not optional — Fusion enum false positives), `"reportSelfClsParameterName": "none"`.
- **Stub sentinel:** any `Import "adsk…" could not be resolved` diagnostic ⇒ environment error; suppress all other diagnostics.
- **Exit codes:** 0 = PASS (send to Fusion), 1 = FAIL (fix the script), 2 = usage error, 3 = environment error / GATE_BROKEN (fix the machine, do NOT edit the script).
- **Timing budget:** publish ≤ 2.5 s per preflight run. Cache the pyright version probe (a fresh `pyright --version` is ~900 ms). Never invoke `dist/pyright.js` with node directly.
- **Lint is fixed, not configurable.** No config file, no severity overrides. Only escape: line-scoped suppression `# fusionhelper: allow <rule-id-or-number> — <reason>`; reason under 12 characters is itself an error; unknown rule id is an error; unused suppression is a warning; waivers print on every run including PASS.
- **R4 collections set:** `{faces, edges, vertices, bRepBodies, shells, lumps}` — NOT `bodies` (caused a live false positive). Matching requires a dotted chain. `sketch.profiles.item(0)` is deliberately excluded.
- **R6 must NOT match `Point3D.create(...)`** — literal seed coordinates are the endorsed pattern.
- **Coverage line on every run including PASS:** `checked: R1 R2 R4 R5 R6 R7 R8 · not checked: R3 R9 R10 · R5 covers parameter-change only`.
- **Renderer invariant:** verdict, counts and coverage line are derived from the findings list at render time, never from a counter maintained alongside.
- **R8 normalisation:** absorb CRLF, trailing blank lines, trailing whitespace — scripts are written on Windows.
- **Rule numbering is load-bearing:** every finding cites its rule number and restates the rule in one line (anti-drift: rules re-enter context at the moment of violation).
- **The existing `design/verify/` code is moved, not rewritten.** `stub_text.py` is the single source of truth for the stub; nothing else may hold a copy.
- **Documents are never saved.** Integration tests use scratch documents tagged via `des.attributes.add`; cleanup is harness-driven (4 layers), never script-driven.
- **Autodesk stubs are never vendored into the repo** (no licence). CI uses synthetic stubs we author; gate *fidelity* tests are local-only.
- **Definition of done (from detailed-design §10):** three outcomes with canary green; config generated programmatically; every rule has ≥1 known-bad fixture matching exactly on rule and line; the good corpus produces zero findings; suppression both directions; `verify` stub output parses, passes lint, passes preflight; P1–P8 pass against live Fusion asserting on parsed JSON; zero leaked documents after a full run and an interrupted one; CI green on ubuntu + windows.

## Guardrails (from persistent memory — surfaced before drafting, per process standard)

High-confidence reflections applied to this plan, with confidence/evidence visible:

- **[[confidence-scoring]]** (ralph-runtime standard): every task below carries a confidence %. Sub-90% tasks embed their mitigation inside the task body (Step 0 spikes), not as follow-ups. The sub-90% tasks in this plan (12, 16, 17) carry Step 0 spikes or an explicit live-variance bound.
- **[[docs-in-sync]]** (mem-f3ce58e6, conf 0.95, used 19×): `docs/README.md` lists `design/verify/` paths that Task 4 moves — the same commit updates those references. Task 15 re-checks all doc paths.
- **[[red-step-genuinely-red]]** (mem-66b096bf, conf 0.75): each rule's RED step asserts on an **exact `(line, rule-id)` set**, not on a substring — a neighbouring rule's finding cannot fake a pass.
- **[[spec-code-not-lint-clean]]** (ralph-runtime standard): all test code below was swept for ruff traps (no unused `import pytest`, no `(str, Enum)`, no `timezone.utc`). Executors: run `ruff check` before every commit anyway.
- **[[mkstemp-fd-leak]]** (mem-4bc9a9b6, conf 0.6): preflight staging uses `tempfile.mkdtemp()` + ordinary `open()`, never the `mkstemp`+`fdopen` idiom.
- **[[cross-read-prose-vs-code]]** (ralph-runtime standard): self-review section includes a prose-vs-code-block contradiction pass; it was run on this plan.

Dismissed as not applicable: TS `Partial<T>` reflection (no TypeScript in this plan); ralph-queue dispatch reflection (this is not a queue dispatch); Playwright text-transform reflection (no browser tests).

## File Structure

```
FusionHelper/
├── pyproject.toml                     Task 1
├── .github/workflows/ci.yml           Task 1
├── fusionhelper/
│   ├── __init__.py                    Task 1
│   ├── stubs.py                       Task 11  (defs discovery, version, lock)
│   ├── lint/
│   │   ├── __init__.py                Task 2   (run(), one shared parse)
│   │   ├── findings.py                Task 2   (Finding, RULES registry)
│   │   ├── suppress.py                Task 3   (line-scoped waivers)
│   │   ├── render.py                  Task 10  (report text, coverage line)
│   │   └── rules/
│   │       ├── __init__.py            Task 2   (ALL_RULES, grows per task)
│   │       ├── r1_create_by_real.py   Task 2
│   │       ├── r7_param_names.py      Task 5
│   │       ├── r2_dimension_bind.py   Task 6
│   │       ├── r4_index_topology.py   Task 7
│   │       ├── r5_stale_brep.py       Task 8
│   │       ├── r6_hardcoded_axis.py   Task 8
│   │       └── r8_stub_intact.py      Task 9
│   ├── verify/
│   │   ├── __init__.py                Task 4   (STUB_TEXT, append_to, install)
│   │   ├── fh_verify.py               Task 4   (moved from design/verify/)
│   │   └── stub_text.py               Task 4   (moved from design/verify/)
│   └── preflight/
│       ├── __init__.py                Task 12  (Outcome, run_preflight)
│       ├── __main__.py                Task 13  (CLI, exit codes)
│       ├── staging.py                 Task 12  (mkdtemp, config json.dump)
│       └── canary.py                  Task 12  (known-bad probe text)
├── skills/fusion-design/
│   ├── SKILL.md                       Task 14  (reference/ already written)
│   └── reference/                     exists — untouched
├── tests/
│   ├── markers.py                     Task 2   (# EXPECT: loader)
│   ├── test_lint_fixtures.py          Task 2   (one test serves all fixtures)
│   ├── test_suppression.py            Task 3
│   ├── test_verify_offline.py         Task 4   (ported 43 assertions)
│   ├── test_stub_wiring.py            Task 4
│   ├── test_render.py                 Task 10
│   ├── test_stubs_discovery.py        Task 11
│   ├── test_preflight.py              Task 12–13
│   ├── fixtures/lint/bad/*.py         Tasks 2,5–9
│   ├── fixtures/lint/good/*.py        Tasks 2,5–9,15
│   ├── synthetic_stubs/adsk/          Task 12  (~15 symbols, CI-safe)
│   ├── api_version.lock               Task 11
│   └── integration/                   Task 16–17 (opt-in, live Fusion)
│       ├── conftest.py, mcp_client.py, scratch.py
│       └── test_p1_parametric.py … test_p8_sweep.py
└── docs/                              paths updated in Tasks 4, 15
```

Interface conventions used throughout (defined once here, cited per task):

- `Finding(rule: str, line: int, col: int, severity: str, message: str, fix: str | None = None)` — frozen dataclass; `severity` is `"error"` or `"warn"`.
- `fusionhelper.lint.run(source: str, path: str = "<script>") -> LintResult` where `LintResult` has `.findings: list[Finding]`, `.waivers: list[Waiver]`, `.parse_error: Finding | None`.
- Rule module contract: each `rules/r*.py` exposes `RULE_ID: str`, `NUMBER: str` (e.g. `"R1"`), `RESTATEMENT: str` (one line), and `check(tree: ast.AST, source: str) -> list[Finding]`.
- `fusionhelper.preflight.run_preflight(script_path: Path) -> PreflightResult` with `.outcome: Outcome` (`PASS`/`FAIL`/`GATE_BROKEN`/`USAGE`), `.findings`, `.report: str`, `.exit_code: int`.

---

### Task 1: Package scaffold + CI skeleton — confidence 95%

**Files:**
- Create: `pyproject.toml`, `fusionhelper/__init__.py`, `tests/__init__.py`, `.github/workflows/ci.yml`, `.gitignore`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: importable `fusionhelper` package; `pytest`, `ruff check .`, `pyright fusionhelper` runnable; CI running all three on ubuntu + windows

- [ ] **Step 1: Write the failing test**

`tests/test_package.py`:

```python
import fusionhelper


def test_package_importable():
    assert fusionhelper.__version__ == "0.1.0"
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python -m pytest tests/test_package.py -v` → FAIL (`ModuleNotFoundError: fusionhelper`)

- [ ] **Step 3: Create the scaffold**

`pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "fusionhelper"
version = "0.1.0"
description = "Offline gate + verification block for Claude-generated Fusion 360 scripts"
requires-python = ">=3.12"
dependencies = ["pyright==1.1.408"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.6"]

[tool.hatch.build.targets.wheel]
packages = ["fusionhelper"]

[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM"]

# verify-block code runs inside Fusion's interpreter and predates the package;
# it keeps its own conservative style
[tool.ruff.lint.per-file-ignores]
"fusionhelper/verify/fh_verify.py" = ["UP", "SIM", "E501", "B"]
"fusionhelper/verify/stub_text.py" = ["E501"]

[tool.pyright]
include = ["fusionhelper", "tests"]
exclude = ["tests/fixtures", "tests/synthetic_stubs", "fusionhelper/verify/fh_verify.py"]
typeCheckingMode = "basic"
```

`fusionhelper/__init__.py`:

```python
"""Offline gate + verification block for Claude-generated Fusion 360 scripts."""

__version__ = "0.1.0"
```

`tests/__init__.py`: empty file. `.gitignore`: `__pycache__/`, `*.egg-info/`, `.venv/`, `dist/`.

Pin note: pyright is pinned exactly (`==1.1.408`, the version all gate measurements used); gate expectations are version-sensitive per detailed-design §7.

- [ ] **Step 4: Install editable and verify the test passes**

Run: `pip install -e .[dev]` then `python -m pytest tests/test_package.py -v` → PASS.
Run: `ruff check .` → clean. Run: `pyright fusionhelper` → 0 errors.

- [ ] **Step 5: Add CI**

`.github/workflows/ci.yml`:

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e .[dev]
      - run: ruff check .
      - run: pyright fusionhelper
      - run: python -m pytest -v
```

Both OSes matter: `stubs.py` resolves `%APPDATA%` paths and the historical fail-open bug was a Windows path bug (detailed-design §7).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml fusionhelper tests .github .gitignore
git commit -m "feat: package scaffold, ruff+pyright config, CI on ubuntu+windows"
```

### Task 2: Lint engine + R1 no-create-by-real + fixture harness — confidence 93%

The engine, the marker loader and the simplest rule land together so the harness has real signal from day one. One test function serves every fixture forever after.

**Files:**
- Create: `fusionhelper/lint/__init__.py`, `fusionhelper/lint/findings.py`, `fusionhelper/lint/rules/__init__.py`, `fusionhelper/lint/rules/r1_create_by_real.py`, `tests/markers.py`, `tests/test_lint_fixtures.py`, `tests/fixtures/lint/bad/r1_create_by_real.py`, `tests/fixtures/lint/good/r1_clean.py`

**Interfaces:**
- Consumes: nothing
- Produces: `lint.run(source, path) -> LintResult`; `Finding`; `RULES` registry `{number: RuleInfo}`; rule-module contract (`RULE_ID`, `NUMBER`, `RESTATEMENT`, `check(tree, source)`); `markers.parse(path) -> set[tuple[int, str]]`

- [ ] **Step 1: Write the fixtures and harness (they ARE the failing test)**

`tests/fixtures/lint/bad/r1_create_by_real.py`:

```python
import adsk.core


def run(_context: str):
    v = adsk.core.ValueInput.createByReal(0.6)  # EXPECT: R1
    vi = adsk.core.ValueInput
    w = vi.createByReal(1.0)  # EXPECT: R1
    print(v, w)
```

`tests/fixtures/lint/good/r1_clean.py`:

```python
import adsk.core


def run(_context: str):
    v = adsk.core.ValueInput.createByString("60 mm")
    print(v)
```

`tests/markers.py`:

```python
"""Loader for inline `# EXPECT: <rule>` markers in lint fixtures."""
import re
from pathlib import Path

_MARKER = re.compile(r"#\s*EXPECT:\s*(R\d+)")


def parse(path: Path) -> set[tuple[int, str]]:
    expected = set()
    for lineno, text in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for m in _MARKER.finditer(text):
            expected.add((lineno, m.group(1)))
    return expected
```

`tests/test_lint_fixtures.py` — exact set equality, both directions, so the false-positive guard is the same assertion as the true-positive one; a good fixture simply contains zero markers:

```python
from pathlib import Path

import pytest

from fusionhelper import lint
from tests import markers

FIXTURES = sorted((Path(__file__).parent / "fixtures" / "lint").rglob("*.py"))


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: f"{p.parent.name}/{p.name}")
def test_fixture(path: Path):
    result = lint.run(path.read_text(encoding="utf-8"), str(path))
    found = {(f.line, f.rule_number) for f in result.findings}
    assert found == markers.parse(path)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_lint_fixtures.py -v` → FAIL (`ImportError` — `fusionhelper.lint` does not exist). Genuinely red: nothing else can satisfy the import.

- [ ] **Step 3: Implement findings registry + engine + R1**

`fusionhelper/lint/findings.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RuleInfo:
    rule_id: str
    number: str
    restatement: str
    checked: bool  # False for R3/R9/R10 — runtime/convention; named in the coverage line


@dataclass(frozen=True)
class Finding:
    rule_id: str
    rule_number: str
    line: int
    col: int
    severity: str  # "error" | "warn"
    message: str
    fix: str | None = None


RULES: dict[str, RuleInfo] = {
    "R1": RuleInfo("no-create-by-real", "R1",
                   "Never ValueInput.createByReal — use createByString, always", True),
    "R2": RuleInfo("dimension-must-bind", "R2",
                   "Every sketchDimensions.add* must have .parameter.expression assigned", True),
    "R3": RuleInfo("constrain-then-dimension", "R3",
                   "Constrain, check isFullyConstrained, dimension the residual (runtime)", False),
    "R4": RuleInfo("no-index-topology", "R4",
                   "Never select topology by index — geometric predicate or entityToken", True),
    "R5": RuleInfo("no-stale-brep", "R5",
                   "Never use a BRep reference across a parameter change", True),
    "R6": RuleInfo("no-hardcoded-axis", "R6",
                   "Derive axis mapping from sketchToModelSpace() at runtime", True),
    "R7": RuleInfo("param-name-safe", "R7",
                   "Parameter names are multi-character snake_case", True),
    "R8": RuleInfo("verify-stub-intact", "R8",
                   "The file ends with the verification stub, unmodified", True),
    "R9": RuleInfo("no-catch", "R9",
                   "Never catch exceptions in generated scripts (convention)", False),
    "R10": RuleInfo("no-save", "R10",
                    "Never save the document (convention)", False),
}
BY_ID = {info.rule_id: info for info in RULES.values()}
```

`fusionhelper/lint/rules/r1_create_by_real.py` — receiver-blind on the `Attribute` (there is no other `createByReal` in the API; checking the receiver only creates escapes), plus a `tokenize` backstop for `getattr` forms at WARN:

```python
import ast
import io
import tokenize

from fusionhelper.lint.findings import Finding

RULE_ID = "no-create-by-real"
NUMBER = "R1"
RESTATEMENT = "Never ValueInput.createByReal — use createByString, always"

_FIX = "adsk.core.ValueInput.createByString('<value with unit, or parameter expression>')"


def check(tree: ast.AST, source: str) -> list[Finding]:
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "createByReal":
            findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset,
                                    "error", "createByReal bakes a literal; the timeline "
                                    "looks parametric and dies on first edit", _FIX))
    ast_lines = {f.line for f in findings}
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.STRING and "createByReal" in tok.string:
            if tok.start[0] not in ast_lines:
                findings.append(Finding(RULE_ID, NUMBER, tok.start[0], tok.start[1],
                                        "warn", "string mentions createByReal — possible "
                                        "getattr evasion of R1", _FIX))
    return findings
```

`fusionhelper/lint/rules/__init__.py`:

```python
from fusionhelper.lint.rules import r1_create_by_real

ALL_RULES = [r1_create_by_real]  # grows: r7 (Task 5), r2 (6), r4 (7), r5+r6 (8), r8 (9)
```

`fusionhelper/lint/__init__.py` — one shared parse; a syntax error is a result, not an exception:

```python
import ast
from dataclasses import dataclass, field

from fusionhelper.lint.findings import Finding
from fusionhelper.lint.rules import ALL_RULES


@dataclass
class LintResult:
    findings: list[Finding] = field(default_factory=list)
    waivers: list = field(default_factory=list)   # populated in Task 3
    parse_error: Finding | None = None


def run(source: str, path: str = "<script>") -> LintResult:
    result = LintResult()
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        result.parse_error = Finding("syntax", "SYNTAX", e.lineno or 1, e.offset or 0,
                                     "error", f"script does not parse: {e.msg}")
        result.findings.append(result.parse_error)
        return result
    for rule in ALL_RULES:
        result.findings.extend(rule.check(tree, source))
    result.findings.sort(key=lambda f: (f.line, f.col, f.rule_number))
    return result
```

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_lint_fixtures.py -v` → 2 PASS. The bad fixture's markers sit on the violation lines, so the expected set is `{(5, "R1"), (7, "R1")}` — an off-by-one in harness or rule fails loudly.

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/lint tests
git commit -m "feat: lint engine, EXPECT-marker fixture harness, R1 no-create-by-real"
```

### Task 3: Suppression handling — confidence 92%

**Files:**
- Create: `fusionhelper/lint/suppress.py`, `tests/test_suppression.py`
- Modify: `fusionhelper/lint/__init__.py` (apply waivers after rules run)

**Interfaces:**
- Consumes: `LintResult`, `Finding`, `RULES`/`BY_ID` from Task 2
- Produces: `Waiver(line, rule_number, reason)`; `suppress.apply(source, findings) -> (kept, honoured, defects)`; `LintResult.waivers` populated

- [ ] **Step 1: Write the failing tests**

`tests/test_suppression.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_suppression.py -v` → all 4 FAIL. The first fails on `findings == []` (R1 still fires — the waiver comment is currently ignored), which proves the R1 detection is live and the suppression behaviour is genuinely absent.

- [ ] **Step 3: Implement**

`fusionhelper/lint/suppress.py`:

```python
"""Line-scoped waivers: `# fusionhelper: allow <rule-id-or-number> — <reason>`.

No file-level pragma, no --ignore flag (spec: a file-level waiver is one edit
that silently disables a rule for a 400-line script). Waivers print on every
run including PASS — a waiver nobody sees is the same as no rule.
"""
import re
from dataclasses import dataclass

from fusionhelper.lint.findings import BY_ID, RULES, Finding

_WAIVER = re.compile(r"#\s*fusionhelper:\s*allow\s+(\S+)\s*[—-]\s*(.*)$")
MIN_REASON = 12


@dataclass(frozen=True)
class Waiver:
    line: int
    rule_number: str
    reason: str


def apply(source, findings):
    kept, honoured, defects = list(findings), [], []
    for lineno, text in enumerate(source.splitlines(), start=1):
        m = _WAIVER.search(text)
        if not m:
            continue
        raw, reason = m.group(1), m.group(2).strip()
        info = RULES.get(raw) or BY_ID.get(raw)
        if info is None:
            defects.append(Finding("waiver", "WAIVER", lineno, 0, "error",
                                   f"unknown rule id {raw!r} in suppression"))
            continue
        if len(reason) < MIN_REASON:
            defects.append(Finding("waiver", "WAIVER", lineno, 0, "error",
                                   f"suppression reason too short (<{MIN_REASON} chars); "
                                   "state why the exception is safe"))
            continue
        matched = [f for f in kept if f.line == lineno and f.rule_number == info.number]
        if not matched:
            defects.append(Finding("waiver", "WAIVER", lineno, 0, "warn",
                                   f"unused suppression for {info.number}"))
            continue
        for f in matched:
            kept.remove(f)
        honoured.append(Waiver(lineno, info.number, reason))
    return kept, honoured, defects
```

In `fusionhelper/lint/__init__.py`, after the rule loop and before the sort:

```python
    from fusionhelper.lint import suppress
    result.findings, result.waivers, defects = suppress.apply(source, result.findings)
    result.findings.extend(defects)
```

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_suppression.py tests/test_lint_fixtures.py -v` → all PASS.

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/lint tests/test_suppression.py
git commit -m "feat: line-scoped suppression with mandatory reasons, both-direction checks"
```

### Task 4: Move `design/verify/` into the package — confidence 94%

The verification block exists and its 43 offline assertions pass. This task relocates it, re-exports the public names, adds the installer the stub depends on, and updates every doc path in the same commit ([[docs-in-sync]]).

**Files:**
- Move (git mv): `design/verify/fh_verify.py` → `fusionhelper/verify/fh_verify.py`; `design/verify/stub_text.py` → `fusionhelper/verify/stub_text.py`; `design/verify/test_fh_verify_offline.py` → `tests/test_verify_offline.py`; `design/verify/stub_example.py` → `tests/fixtures/verify/stub_example.py`
- Create: `fusionhelper/verify/__init__.py`, `tests/test_stub_wiring.py`
- Modify: `docs/README.md` (three `design/verify/` path references), `docs/detailed-design.md` (companion-artefacts table)

**Interfaces:**
- Consumes: package from Task 1
- Produces: `fusionhelper.verify.STUB_TEXT`, `.STUB_SENTINEL`, `.append_to(script_text) -> str`, `.install_block(home: Path | None = None) -> Path`, `.block_source() -> str`. R8 (Task 9) and preflight (Task 12) consume `STUB_TEXT` and `install_block`.

- [ ] **Step 1: Write the failing wiring test**

`tests/test_stub_wiring.py`:

```python
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
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_stub_wiring.py -v` → FAIL (`ModuleNotFoundError: fusionhelper.verify`).

- [ ] **Step 3: Move files and write the package front**

```bash
git mv design/verify/fh_verify.py fusionhelper/verify/fh_verify.py
git mv design/verify/stub_text.py fusionhelper/verify/stub_text.py
git mv design/verify/test_fh_verify_offline.py tests/test_verify_offline.py
mkdir -p tests/fixtures/verify
git mv design/verify/stub_example.py tests/fixtures/verify/stub_example.py
```

`fusionhelper/verify/__init__.py`:

```python
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
```

Fix the moved test's import: `tests/test_verify_offline.py` loads `fh_verify.py` by path — change its loader line to `Path(__file__).parents[1] / "fusionhelper" / "verify" / "fh_verify.py"` (read the file's existing loader first; it already execs from a path, keep its mechanism and change only the path).

Update `docs/README.md` and `docs/detailed-design.md`: replace `design/verify/fh_verify.py` → `fusionhelper/verify/fh_verify.py`, `design/verify/test_fh_verify_offline.py` → `tests/test_verify_offline.py`, and note the reference bundle path is unchanged.

- [ ] **Step 4: Run the full suite, verify pass**

Run: `python -m pytest -v` → all pass, including the ported 43 offline assertions. Run: `ruff check .` (the per-file-ignores from Task 1 cover the moved files). Run: `grep -rn "design/verify" docs/ fusionhelper/ tests/` → only historical mentions in probe/design narrative remain, no live paths.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor: move verification block into fusionhelper.verify, add installer, update doc paths"
```

### Task 5: R7 param-name-safe — confidence 90%

ERROR must always mean "this will throw at runtime" (the rejected set); WARN is policy (non-`snake_case`). A script with zero WARNs provably cannot trip the ERROR set — that asymmetry is the point.

**Files:**
- Create: `fusionhelper/lint/rules/r7_param_names.py`, `tests/fixtures/lint/bad/r7_param_names.py`, `tests/fixtures/lint/good/r7_param_names.py`
- Modify: `fusionhelper/lint/rules/__init__.py` (register)

**Interfaces:**
- Consumes: rule-module contract from Task 2
- Produces: R7 findings; the fixture harness from Task 2 needs no changes

- [ ] **Step 1: Write the fixtures**

`tests/fixtures/lint/bad/r7_param_names.py`:

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    up = des.userParameters
    up.add("W", adsk.core.ValueInput.createByString("60 mm"), "mm", "")  # EXPECT: R7
    up.add("PI", adsk.core.ValueInput.createByString("3 mm"), "mm", "")  # EXPECT: R7
    up.add("box w", adsk.core.ValueInput.createByString("3 mm"), "mm", "")  # EXPECT: R7
    up.add("0box", adsk.core.ValueInput.createByString("3 mm"), "mm", "")  # EXPECT: R7
    up.add("outer_w", adsk.core.ValueInput.createByString("60 mm"), "mm", "")
    up.add("outer_w", adsk.core.ValueInput.createByString("9 mm"), "mm", "")  # EXPECT: R7
    up.add("outerW", adsk.core.ValueInput.createByString("60 mm"), "mm", "")  # EXPECT: R7
    des.userParameters.add("t", adsk.core.ValueInput.createByString("2 mm"), "mm", "")  # EXPECT: R7
```

Line-by-line intent: `W` unit symbol (ERROR), `PI` function/constant (ERROR), `box w` malformed (ERROR), `0box` malformed (ERROR), `outer_w` twice = duplicate (ERROR on the second), `outerW` camelCase (WARN), `t` single-char via a direct dotted call (WARN) — the last also proves the rule sees both the aliased (`up = des.userParameters`) and direct receiver forms.

`tests/fixtures/lint/good/r7_param_names.py`:

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    up = des.userParameters
    up.add("outer_w", adsk.core.ValueInput.createByString("60 mm"), "mm", "outer width")
    up.add("wall_t", adsk.core.ValueInput.createByString("outer_w / 20"), "mm", "derived")
    holes = [1, 2]
    holes.add = None  # not a userParameters receiver: attribute add on a non-tracked name
```

(The last line is deliberate noise proving the rule does not fire on arbitrary `.add` calls — remove it if `ruff` objects to the pattern and replace with `data = {"add": 1}` plus `data["add"]`.)

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_lint_fixtures.py -v` → the two new fixture cases FAIL (expected marker sets are non-empty / rule not registered).

- [ ] **Step 3: Implement**

`fusionhelper/lint/rules/r7_param_names.py`:

```python
import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "param-name-safe"
NUMBER = "R7"
RESTATEMENT = "Parameter names are multi-character snake_case"

# Case-sensitive, from fusion-api-notes §3: these throw at runtime.
_UNIT_SYMBOLS = {"W", "H", "R", "T", "mm", "cm", "m", "um", "nm", "in", "ft",
                 "yd", "mil", "thou", "deg", "rad"}
_FUNC_NAMES = {"PI", "E", "abs", "cos", "sin", "tan", "asin", "acos", "atan",
               "sqrt", "min", "max", "if", "floor", "ceil", "round", "log",
               "exp", "pow", "sign"}
_SNAKE = r"^[a-z_][a-z0-9_]*$"


def _receiver_is_user_parameters(func: ast.expr, aliases: set[str]) -> bool:
    if not (isinstance(func, ast.Attribute) and func.attr == "add"):
        return False
    recv = func.value
    if isinstance(recv, ast.Name):
        return recv.id in aliases
    return isinstance(recv, ast.Attribute) and recv.attr == "userParameters"


def check(tree: ast.AST, source: str) -> list[Finding]:
    import re
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Attribute)
                and node.value.attr == "userParameters"):
            aliases.add(node.targets[0].id)

    findings, seen = [], {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and node.args
                and _receiver_is_user_parameters(node.func, aliases)):
            continue
        arg = node.args[0]
        if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str)):
            continue  # dynamic name: nothing static to check
        name = arg.value
        loc = (node.lineno, node.col_offset)
        if name in _UNIT_SYMBOLS or name in _FUNC_NAMES:
            findings.append(Finding(RULE_ID, NUMBER, *loc, "error",
                                    f"Fusion rejects parameter name {name!r} "
                                    "(unit symbol / function name) with a misleading "
                                    "'param name is not valid'",
                                    f"rename to a multi-character snake_case name, "
                                    f"e.g. '{name.lower()}_val'"))
        elif not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
            findings.append(Finding(RULE_ID, NUMBER, *loc, "error",
                                    f"malformed parameter name {name!r} — Fusion will "
                                    "throw 'param name is not valid'",
                                    "use letters, digits and underscores; start with a letter"))
        elif name in seen:
            findings.append(Finding(RULE_ID, NUMBER, *loc, "error",
                                    f"duplicate parameter name {name!r} (first added on "
                                    f"line {seen[name]}) — Fusion throws the same "
                                    "misleading 'param name is not valid'",
                                    "reference the existing parameter instead of re-adding"))
        elif not re.match(_SNAKE, name) or len(name) < 2:
            findings.append(Finding(RULE_ID, NUMBER, *loc, "warn",
                                    f"parameter name {name!r} is not multi-character "
                                    "snake_case (project policy avoids the whole "
                                    "rejected-name class)",
                                    "rename, e.g. 'outer_w', 'wall_t'"))
        if name not in seen:
            seen[name] = node.lineno
    return findings
```

Register in `rules/__init__.py`: append `r7_param_names` to `ALL_RULES`.

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_lint_fixtures.py -v` → all fixture cases PASS, including all pre-existing ones (no cross-rule regressions — exact-set matching guarantees it).

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/lint/rules tests/fixtures
git commit -m "feat: R7 param-name-safe — runtime-reject set as ERROR, policy as WARN"
```

### Task 6: R2 dimension-must-bind — confidence 88% → mitigated to 92%

The one rule doing genuine dataflow. Mitigation for the flow-analysis risk is built into the mechanism: three sets in one pass with **conservative escape** — any created dimension passed to any call is treated as bound, so helper functions are never false-flagged. The cost is missed violations inside helpers, which is the accepted trade (detailed-design §3).

**Files:**
- Create: `fusionhelper/lint/rules/r2_dimension_bind.py`, `tests/fixtures/lint/bad/r2_dimension_bind.py`, `tests/fixtures/lint/good/r2_dimension_bind.py`
- Modify: `fusionhelper/lint/rules/__init__.py`

**Interfaces:**
- Consumes: rule-module contract
- Produces: R2 findings; module-level `KNOWN_BINDERS: set[str]` (empty in phase 1; `emit` extends it in phase 3 per detailed-design §8)

- [ ] **Step 1: Write the fixtures**

`tests/fixtures/lint/bad/r2_dimension_bind.py`:

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    sk = des.rootComponent.sketches.item(0)
    p0 = sk.sketchPoints.item(0)
    p1 = sk.sketchPoints.item(1)
    anchor = adsk.core.Point3D.create(3, -1.5, 0)
    orient = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    d1 = sk.sketchDimensions.addDistanceDimension(p0, p1, orient, anchor)  # EXPECT: R2
    d2 = sk.sketchDimensions.addDistanceDimension(p0, p1, orient, anchor)
    d2.parameter.expression = "outer_w"
    sk.sketchDimensions.addDistanceDimension(p0, p1, orient, anchor)  # EXPECT: R2
    print(d1)
```

Line 14 (`d1`): created, never bound → violation. Line 15–16 (`d2`): created and bound → clean. Line 17: bare expression statement — *discarded*, can never be bound, the highest-confidence finding the rule produces.

`tests/fixtures/lint/good/r2_dimension_bind.py`:

```python
import adsk.core
import adsk.fusion


def bind_all(dims, exprs):
    for d, e in zip(dims, exprs):
        d.parameter.expression = e


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    sk = des.rootComponent.sketches.item(0)
    p0 = sk.sketchPoints.item(0)
    p1 = sk.sketchPoints.item(1)
    anchor = adsk.core.Point3D.create(3, -1.5, 0)
    orient = adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
    d1 = sk.sketchDimensions.addDistanceDimension(p0, p1, orient, anchor)
    d1.parameter.expression = "outer_w"
    d2 = sk.sketchDimensions.addDistanceDimension(p0, p1, orient, anchor)
    bind_all([d2], ["outer_d"])
```

`d2` escapes into `bind_all` → conservatively counted as bound → good fixture stays clean.

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_lint_fixtures.py -v` → the two new cases FAIL (rule not registered; expected sets `{(14, "R2"), (17, "R2")}` and `set()` unmet).

- [ ] **Step 3: Implement**

`fusionhelper/lint/rules/r2_dimension_bind.py`:

```python
import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "dimension-must-bind"
NUMBER = "R2"
RESTATEMENT = "Every sketchDimensions.add* must have .parameter.expression assigned"

KNOWN_BINDERS: set[str] = set()  # emit's helpers register here in phase 3

_FIX = "<var>.parameter.expression = '<parameter name or expression>'"


def _is_dim_create(call: ast.expr) -> bool:
    return (isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr.startswith("add")
            and isinstance(call.func.value, ast.Attribute)
            and call.func.value.attr == "sketchDimensions")


def check(tree: ast.AST, source: str) -> list[Finding]:
    creations: dict[str, ast.Assign] = {}
    bound: set[str] = set()
    escaped: set[str] = set()
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and _is_dim_create(node.value):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                creations[node.targets[0].id] = node
        elif isinstance(node, ast.Expr) and _is_dim_create(node.value):
            findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset,
                                    "error", "dimension created and discarded — it can "
                                    "never be bound to a parameter (partially-bound "
                                    "dead-timeline trap)", _FIX))
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Attribute):
            tgt = node.targets[0]
            if (tgt.attr == "expression" and isinstance(tgt.value, ast.Attribute)
                    and tgt.value.attr == "parameter"
                    and isinstance(tgt.value.value, ast.Name)):
                bound.add(tgt.value.value.id)
        elif isinstance(node, ast.Call):
            for arg in list(node.args) + [kw.value for kw in node.keywords]:
                if isinstance(arg, ast.Name):
                    escaped.add(arg.id)
                elif isinstance(arg, (ast.List, ast.Tuple)):
                    escaped.update(e.id for e in arg.elts if isinstance(e, ast.Name))

    for name, assign in creations.items():
        if name not in bound and name not in escaped:
            findings.append(Finding(RULE_ID, NUMBER, assign.lineno, assign.col_offset,
                                    "error", f"dimension {name!r} is never bound — "
                                    "its .parameter.expression is never assigned "
                                    "(model looks parametric; this dimension is dead)",
                                    _FIX.replace("<var>", name)))
    return findings
```

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_lint_fixtures.py -v` → all PASS.

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/lint/rules tests/fixtures
git commit -m "feat: R2 dimension-must-bind — creations/bound/escaped/discarded dataflow"
```

### Task 7: R4 no-index-topology — confidence 90%

The rule with the real false-positive problem: iterating all faces to apply a geometric predicate is the *recommended* pattern. A `RangeIterationTracker` exempts `for i in range(<same receiver>.count)`, and direct iteration produces no subscript so it is never visited.

**Files:**
- Create: `fusionhelper/lint/rules/r4_index_topology.py`, `tests/fixtures/lint/bad/r4_index_topology.py`, `tests/fixtures/lint/good/r4_index_topology.py`
- Modify: `fusionhelper/lint/rules/__init__.py`

**Interfaces:**
- Consumes: rule-module contract
- Produces: R4 findings

- [ ] **Step 1: Write the fixtures**

`tests/fixtures/lint/bad/r4_index_topology.py`:

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    body = des.rootComponent.bRepBodies.item(0)  # EXPECT: R4
    top = body.faces[4]  # EXPECT: R4
    edge = body.edges.item(2)  # EXPECT: R4
    first_body = des.rootComponent.bRepBodies[0]  # EXPECT: R4
    print(top, edge, first_body)
```

`tests/fixtures/lint/good/r4_index_topology.py`:

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    sk = root.sketches.item(0)
    prof = sk.profiles.item(0)  # the universal idiom — deliberately excluded from R4
    for body in root.bRepBodies:
        for f in body.faces:
            if f.geometry.normal.z > 0.99:
                print("top face", f.tempId)
        for i in range(body.faces.count):
            print(body.faces[i].area)  # exempt: range(<same receiver>.count)
    faces = [1, 2, 3]
    print(faces[0])  # bare name, no dotted chain — never matches
    print(prof)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_lint_fixtures.py -v` → the two new cases FAIL (expected `{(8, "R4"), (9, "R4"), (10, "R4"), (11, "R4")}` and `set()`).

- [ ] **Step 3: Implement**

`fusionhelper/lint/rules/r4_index_topology.py`:

```python
import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "no-index-topology"
NUMBER = "R4"
RESTATEMENT = "Never select topology by index — geometric predicate or entityToken"

# NOT "bodies": Fusion's collection is bRepBodies; "bodies" caused a live
# false positive on a local variable matching by name alone.
_COLLECTIONS = {"faces", "edges", "vertices", "bRepBodies", "shells", "lumps"}

_FIX = ("select by geometric predicate (normal / centroid / area) or capture "
        "entityToken and re-resolve with Design.findEntityByToken()")


def _chain_text(node: ast.expr) -> str | None:
    """Dotted-chain source text, or None if anything but Name/Attribute appears."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _collection_receiver(node: ast.expr) -> str | None:
    """Return chain text when node is <dotted chain>.<collection>, else None."""
    if isinstance(node, ast.Attribute) and node.attr in _COLLECTIONS:
        return _chain_text(node)
    return None


class _RangeIterationTracker(ast.NodeVisitor):
    """Collects receiver chains exempted by `for i in range(<recv>.count)`."""

    def __init__(self):
        self.exempt: set[str] = set()

    def visit_For(self, node: ast.For):
        it = node.iter
        if (isinstance(it, ast.Call) and isinstance(it.func, ast.Name)
                and it.func.id == "range" and len(it.args) == 1
                and isinstance(it.args[0], ast.Attribute)
                and it.args[0].attr == "count"):
            recv = _collection_receiver(it.args[0].value)
            if recv:
                self.exempt.add(recv)
        self.generic_visit(node)


def check(tree: ast.AST, source: str) -> list[Finding]:
    tracker = _RangeIterationTracker()
    tracker.visit(tree)
    findings = []
    for node in ast.walk(tree):
        recv = None
        if isinstance(node, ast.Subscript):
            recv = _collection_receiver(node.value)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "item"):
            recv = _collection_receiver(node.func.value)
        if recv is None or recv in tracker.exempt:
            continue
        # profiles.item(0) exclusion is structural: "profiles" is not in _COLLECTIONS
        findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset, "error",
                                f"index pick on {recv} — breaks when face/edge count "
                                "changes (P4: face[4] silently became a different face "
                                "after a chamfer)", _FIX))
    return findings
```

Register in `rules/__init__.py`.

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_lint_fixtures.py -v` → all PASS. The good fixture is the false-positive claim under test: predicate iteration, range-count iteration, bare-name subscript and `profiles.item(0)` all produce zero findings.

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/lint/rules tests/fixtures
git commit -m "feat: R4 no-index-topology with range-iteration exemption"
```

### Task 8: R5 no-stale-brep + R6 no-hardcoded-axis — confidence 91%

Two small rules, one commit. R5's trigger is purely syntactic (any assignment to a parameter's `.expression`/`.value` invalidates held BReps document-wide — measured). R6 must not match `Point3D.create` — identical shape, opposite meaning.

**Files:**
- Create: `fusionhelper/lint/rules/r5_stale_brep.py`, `fusionhelper/lint/rules/r6_hardcoded_axis.py`, `tests/fixtures/lint/bad/r5_stale_brep.py`, `tests/fixtures/lint/good/r5_stale_brep.py`, `tests/fixtures/lint/bad/r6_hardcoded_axis.py`, `tests/fixtures/lint/good/r6_hardcoded_axis.py`
- Modify: `fusionhelper/lint/rules/__init__.py`

**Interfaces:**
- Consumes: rule-module contract
- Produces: R5, R6 findings

- [ ] **Step 1: Write the fixtures**

`tests/fixtures/lint/bad/r5_stale_brep.py`:

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    held = None
    for body in des.rootComponent.bRepBodies:  # direct iteration: no R4 subscript
        for f in body.faces:
            held = f
    des.userParameters.itemByName("outer_w").expression = "80 mm"  # EXPECT: R5
    print(held.area)
```

`tests/fixtures/lint/good/r5_stale_brep.py`:

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    sk = des.rootComponent.sketches.item(0)
    dim = sk.sketchDimensions.item(0)
    dim.parameter.expression = "outer_w"  # R2's mandated binding — receiver is `parameter`
```

`tests/fixtures/lint/bad/r6_hardcoded_axis.py`:

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    up = adsk.core.Vector3D.create(0.0, 0.0, 1.0)  # EXPECT: R6
    sk = root.sketches.add(root.xZConstructionPlane)  # EXPECT: R6
    print(up, sk)
```

(The `xZConstructionPlane` finding is a WARN and lands on its own line: the script references an inverting plane and never calls `sketchToModelSpace`.)

`tests/fixtures/lint/good/r6_hardcoded_axis.py`:

```python
import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    root = des.rootComponent
    sk = root.sketches.add(root.xZConstructionPlane)
    origin_world = sk.sketchToModelSpace(adsk.core.Point3D.create(0, 0, 0))
    seed = adsk.core.Point3D.create(0.1, -0.2, 0)  # literal SEED coords: endorsed
    direction = sk.xDirection  # derived, not literal
    print(origin_world, seed, direction)
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_lint_fixtures.py -v` → four new cases FAIL.

- [ ] **Step 3: Implement**

`fusionhelper/lint/rules/r5_stale_brep.py`:

```python
import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "no-stale-brep"
NUMBER = "R5"
RESTATEMENT = "Never use a BRep reference across a parameter change"

_FIX = ("capture entityToken before the parameter write and re-resolve with "
        "Design.findEntityByToken() after")


def check(tree: ast.AST, source: str) -> list[Finding]:
    findings = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Attribute)):
            continue
        tgt = node.targets[0]
        if tgt.attr not in {"expression", "value"}:
            continue
        # Immediate-receiver test: excluding receiver `parameter` (R2's binding)
        # catches des.userParameters.itemByName('w').expression = ... which a
        # full-chain test misses (attr_chain bails on the call mid-chain).
        recv = tgt.value
        if isinstance(recv, ast.Attribute) and recv.attr == "parameter":
            continue
        if isinstance(recv, ast.Name) and recv.id == "parameter":
            continue
        findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset, "warn",
                                "parameter write — any BRepFace/Edge held in a variable "
                                "is now dead document-wide (InternalValidationError on "
                                "next use)", _FIX))
    return findings
```

Severity note: R5 is WARN, not ERROR — the write itself is legal and required; the hazard is *held references after it*. Detailed-design labels R5 "parameter trigger only" and open question 8 anticipates dropping it on phase-1 evidence; a WARN keeps the signal without blocking a PASS→send. The coverage line's "R5 covers parameter-change only" states the boundary.

`fusionhelper/lint/rules/r6_hardcoded_axis.py`:

```python
import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "no-hardcoded-axis"
NUMBER = "R6"
RESTATEMENT = "Derive axis mapping from sketchToModelSpace() at runtime"

_INVERTING_PLANES = {"xZConstructionPlane", "yZConstructionPlane"}


def _is_all_literal_vector(node: ast.expr) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create"
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "Vector3D"   # NOT Point3D: seeds are endorsed
            and node.args
            and all(isinstance(a, ast.Constant) or
                    (isinstance(a, ast.UnaryOp) and isinstance(a.operand, ast.Constant))
                    for a in node.args))


def check(tree: ast.AST, source: str) -> list[Finding]:
    findings = []
    calls_sketch_to_model = any(
        isinstance(n, ast.Attribute) and n.attr == "sketchToModelSpace"
        for n in ast.walk(tree))
    for node in ast.walk(tree):
        if _is_all_literal_vector(node):
            findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset,
                                    "error", "all-literal Vector3D.create — hardcoded "
                                    "axis assumption (the XZ inversion trap: on XZ, "
                                    "world_z = -sketch_y)",
                                    "derive the direction from sketch.sketchToModelSpace() "
                                    "or sketch.xDirection/yDirection at runtime"))
        elif (isinstance(node, ast.Attribute) and node.attr in _INVERTING_PLANES
              and not calls_sketch_to_model):
            findings.append(Finding(RULE_ID, NUMBER, node.lineno, node.col_offset,
                                    "warn", f"{node.attr} used and sketchToModelSpace() "
                                    "never called — geometry drawn 'upright' on this "
                                    "plane lands inverted in world Z",
                                    "map sketch coords through sketch.sketchToModelSpace()"))
    return findings
```

Register both in `rules/__init__.py`.

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_lint_fixtures.py tests/test_suppression.py -v` → all PASS. Note the R5 bad fixture also exercises a live waiver (the R4 suppression) inside a fixture — the harness sees only the R5 marker, proving waivers and markers compose.

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/lint/rules tests/fixtures
git commit -m "feat: R5 stale-brep (warn, parameter trigger) and R6 hardcoded-axis"
```

### Task 9: R8 verify-stub-intact — confidence 92%

One invariant: the file ends with the stub, unmodified — a normalised suffix comparison against `fusionhelper.verify.STUB_TEXT`. The sentinel and AST are used only to diagnose *which* failure it is. The silent case this rule exists for: a `def run` appended after the stub wins, the wrapper is discarded, the script builds and prints nothing — indistinguishable from a quiet pass.

**Files:**
- Create: `fusionhelper/lint/rules/r8_stub_intact.py`, `tests/test_r8_stub.py`
- Modify: `fusionhelper/lint/rules/__init__.py`; add `tests/fixtures/verify/stub_example.py` to the good corpus check (Task 15 wires the corpus; here just ensure R8 passes on it)

**Interfaces:**
- Consumes: `verify.STUB_TEXT`, `verify.STUB_SENTINEL` (Task 4), rule contract
- Produces: R8 findings. R8 runs only when preflight is invoked with `expect_stub=True` (Task 12/13 wires the flag); bare `lint.run` skips it so ordinary fixtures don't all fail R8.

- [ ] **Step 1: Write the failing tests**

R8 is positional, so marker fixtures fit badly; it gets a dedicated test file. `tests/test_r8_stub.py`:

```python
from fusionhelper import verify
from fusionhelper.lint.rules import r8_stub_intact

GOOD_BODY = "def run(_context: str):\n    print('build')\n"


def findings_for(text):
    return r8_stub_intact.check_text(text)


def test_intact_stub_passes():
    assert findings_for(verify.append_to(GOOD_BODY)) == []


def test_crlf_and_trailing_whitespace_pass():
    windows = verify.append_to(GOOD_BODY).replace("\n", "\r\n") + "\r\n\r\n"
    assert findings_for(windows) == []


def test_missing_stub_fails_with_diagnosis():
    (f,) = findings_for(GOOD_BODY)
    assert f.rule_number == "R8"
    assert "stub" in f.message and "missing" in f.message


def test_code_after_stub_fails_as_the_silent_case():
    text = verify.append_to(GOOD_BODY) + "\n\ndef run(_context: str):\n    pass\n"
    (f,) = findings_for(text)
    assert f.rule_number == "R8"
    assert "after the stub" in f.message


def test_edited_stub_fails():
    text = verify.append_to(GOOD_BODY).replace("_fh_wrap", "_fh_wrap2")
    (f,) = findings_for(text)
    assert f.rule_number == "R8"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_r8_stub.py -v` → FAIL (`ImportError: r8_stub_intact`).

- [ ] **Step 3: Implement**

`fusionhelper/lint/rules/r8_stub_intact.py`:

```python
from fusionhelper import verify
from fusionhelper.lint.findings import Finding

RULE_ID = "verify-stub-intact"
NUMBER = "R8"
RESTATEMENT = "The file ends with the verification stub, unmodified"

_FIX = "regenerate the script tail with fusionhelper.verify.append_to(script_text)"


def _norm(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def check_text(source: str) -> list[Finding]:
    """Positional rule: called by preflight when expect_stub=True, not from ALL_RULES."""
    if _norm(source).endswith(_norm(verify.STUB_TEXT)):
        return []
    last_line = source.count("\n") + 1
    if verify.STUB_SENTINEL not in source:
        msg = "verification stub missing — the script will build and never verify"
    elif source.rfind(verify.STUB_SENTINEL) < len(source.rstrip()) - len(verify.STUB_TEXT):
        msg = ("code appears after the stub — a later `def run` would discard the "
               "wrapper: the script builds geometry and prints nothing (the silent case)")
    else:
        msg = "verification stub present but modified — exact stub text required"
    return [Finding(RULE_ID, NUMBER, last_line, 0, "error", msg, _FIX)]


def check(tree, source):  # rule-contract shim; engine-level runs skip R8
    return []
```

Wire-up note: `ALL_RULES` gets `r8_stub_intact` (so the coverage line lists it), but its `check` is a no-op; preflight calls `check_text` explicitly when `expect_stub=True`. The heuristic in the "after the stub" branch only chooses the *message*; the verdict came from the suffix compare.

- [ ] **Step 4: Run tests, verify pass**

Run: `python -m pytest tests/test_r8_stub.py tests/test_lint_fixtures.py -v` → all PASS (fixture cases unaffected — `check` is a no-op there). Also run: `python -c "from fusionhelper import verify; from fusionhelper.lint.rules.r8_stub_intact import check_text; import pathlib; print(check_text(pathlib.Path('tests/fixtures/verify/stub_example.py').read_text(encoding='utf-8')))"` → `[]` (the shipped example ends with the intact stub; if it doesn't, fix the example, not the rule).

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/lint/rules tests/test_r8_stub.py
git commit -m "feat: R8 verify-stub-intact — normalised suffix compare, diagnosis-only AST"
```

### Task 10: Report renderer — confidence 93%

**Files:**
- Create: `fusionhelper/lint/render.py`, `tests/test_render.py`

**Interfaces:**
- Consumes: `LintResult`, `Finding`, `Waiver`, `RULES`
- Produces: `render.report(findings, waivers, source, path, checked=(...), extra_note=...) -> str`. Line 1 is the verdict in a fixed grammar; last line is the coverage line. Preflight (Task 13) prints this verbatim.

- [ ] **Step 1: Write the failing tests**

`tests/test_render.py`:

```python
from fusionhelper import lint
from fusionhelper.lint import render

BAD = (
    "import adsk.core\n\n\n"
    "def run(_context: str):\n"
    "    v = adsk.core.ValueInput.createByReal(0.6)\n"
    "    print(v)\n"
)

CLEAN = "print('hello')\n"


def test_fail_report_shape():
    r = lint.run(BAD, "box.py")
    text = render.report(r.findings, r.waivers, BAD, "box.py")
    lines = text.splitlines()
    assert lines[0] == "LINT FAIL errors=1 warns=0"
    assert any(ln.startswith("R1 ") for ln in lines)          # restatement header first
    assert any("box.py:5:" in ln for ln in lines)             # path:line:col
    assert any(ln.strip().startswith("^") for ln in lines)    # caret excerpt
    assert any(ln.strip().startswith("fix:") for ln in lines) # code, not advice
    assert lines[-1].startswith("checked: R1 R2 R4 R5 R6 R7 R8")
    assert "not checked: R3 R9 R10" in lines[-1]
    assert "R5 covers parameter-change only" in lines[-1]


def test_pass_report_still_has_coverage_and_waivers():
    # a USED waiver: R1 fires on this line and is suppressed with a valid reason
    src = ("import adsk.core\n"
           "v = adsk.core.ValueInput.createByReal(0.6)"
           "  # fusionhelper: allow R1 — legacy shim kept verbatim\n")
    r = lint.run(src, "box.py")
    text = render.report(r.findings, r.waivers, src, "box.py")
    assert text.splitlines()[0] == "LINT PASS errors=0 warns=0"
    assert "waiver" in text.lower()           # waivers print even on PASS


def test_verdict_is_derived_not_counted():
    # renderer must recompute from the findings list: hand it a doctored list
    r = lint.run(BAD, "box.py")
    text = render.report([], r.waivers, BAD, "box.py")
    assert text.splitlines()[0].startswith("LINT PASS")
```

Decision, fixed here: **warns do not fail the gate** — the verdict is `PASS` when `errors == 0`, and the grammar is `LINT PASS|FAIL errors=<n> warns=<n>`. (R5 being WARN-only depends on this; an all-warn script must still exit 0.)

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_render.py -v` → FAIL (no `render` module).

- [ ] **Step 3: Implement**

`fusionhelper/lint/render.py`:

```python
"""Render a findings list. HARD INVARIANT: verdict, counts and coverage line
are derived from the findings list at render time — never from a counter
maintained alongside. A PASS header above a list of errors would destroy the
gate's credibility in one sighting."""
from fusionhelper.lint.findings import RULES

COVERAGE = ("checked: R1 R2 R4 R5 R6 R7 R8 · not checked: R3 R9 R10 · "
            "R5 covers parameter-change only")


def report(findings, waivers, source, path, coverage=COVERAGE):
    errors = [f for f in findings if f.severity == "error"]
    warns = [f for f in findings if f.severity == "warn"]
    verdict = "PASS" if not errors else "FAIL"
    out = [f"LINT {verdict} errors={len(errors)} warns={len(warns)}"]
    lines = source.splitlines()
    by_rule: dict[str, list] = {}
    for f in sorted(findings, key=lambda f: (f.rule_number, f.line, f.col)):
        by_rule.setdefault(f.rule_number, []).append(f)
    for number, group in by_rule.items():
        info = RULES.get(number)
        out.append("")
        out.append(f"{number} {info.restatement if info else ''}".rstrip())
        for f in group:
            out.append(f"  {path}:{f.line}:{f.col + 1} [{f.severity}] {f.message}")
            if 1 <= f.line <= len(lines):
                excerpt = lines[f.line - 1]
                out.append(f"    {excerpt}")
                out.append(f"    {' ' * f.col}^")
            if f.fix:
                out.append(f"    fix: {f.fix}")
    for w in waivers:
        out.append(f"waiver: line {w.line} {w.rule_number} — {w.reason}")
    out.append(coverage)
    return "\n".join(out)
```

- [ ] **Step 4: Run tests, verify pass** — `python -m pytest tests/test_render.py -v` → PASS. Deterministic-ordering check: run twice, diff identical.

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/lint/render.py tests/test_render.py
git commit -m "feat: report renderer - fixed verdict grammar, caret excerpts, coverage line"
```

### Task 11: `stubs.py` — discovery, version, lock — confidence 90%

**Files:**
- Create: `fusionhelper/stubs.py`, `tests/test_stubs_discovery.py`, `tests/api_version.lock` (generated), `tests/synthetic_stubs/adsk/__init__.py`, `tests/synthetic_stubs/adsk/core.py`, `tests/synthetic_stubs/adsk/fusion.py`

**Interfaces:**
- Consumes: nothing in-package
- Produces: `discover_defs() -> Path | None` (honours `FUSIONHELPER_DEFS` override, else `%APPDATA%/Autodesk/Autodesk Fusion 360/API/Python/defs`); `api_version(defs) -> str | None` (reads `API/version.txt` two levels up); `fingerprint(defs) -> str` (sha256 over `adsk/core.py` + `adsk/fusion.py`); `read_lock()/write_lock(path, data)` for `tests/api_version.lock` (JSON: `api_version`, `pyright_version`, `stub_sha256`); `pyright_pin_env() -> dict` (sets `PYRIGHT_PYTHON_FORCE_VERSION` from the lock so the PyPI wrapper cannot auto-upgrade)

- [ ] **Step 1: Author the synthetic stubs** (~15 symbols the fixtures touch — CI never sees Autodesk's stubs, which must not be vendored). `tests/synthetic_stubs/adsk/__init__.py` empty; `core.py`:

```python
class Application:
    @staticmethod
    def get() -> "Application": ...
    @property
    def activeProduct(self) -> object: ...
    @property
    def measureManager(self) -> object: ...


class ValueInput:
    @staticmethod
    def createByString(s: str) -> "ValueInput": ...
    @staticmethod
    def createByReal(v: float) -> "ValueInput": ...


class Point3D:
    @staticmethod
    def create(x: float, y: float, z: float) -> "Point3D": ...


class Vector3D:
    @staticmethod
    def create(x: float, y: float, z: float) -> "Vector3D": ...


class ObjectCollection:
    @staticmethod
    def create() -> "ObjectCollection": ...
    def add(self, item: object) -> bool: ...
```

`fusion.py` with `Design` (`cast`, `rootComponent`, `userParameters`, `timeline`, `attributes`), `Component` (`sketches`, `bRepBodies`, `xZConstructionPlane`...), `Sketch` (`sketchDimensions`, `geometricConstraints`, `isFullyConstrained`, `sketchToModelSpace`, `profiles`), `SketchDimensions` with the `add*` methods used in fixtures, `DimensionOrientations`. Every symbol the good/bad fixtures reference must resolve; nothing more. (Authoring detail is mechanical: run pyright over the fixture corpus with these stubs and add missing attributes until only the *intended* unknowns remain.)

- [ ] **Step 2: Write the failing tests**

`tests/test_stubs_discovery.py`:

```python
import json
from pathlib import Path

from fusionhelper import stubs

SYN = Path(__file__).parent / "synthetic_stubs"


def test_env_override_wins(monkeypatch):
    monkeypatch.setenv("FUSIONHELPER_DEFS", str(SYN))
    assert stubs.discover_defs() == SYN


def test_missing_defs_returns_none(monkeypatch):
    monkeypatch.setenv("FUSIONHELPER_DEFS", str(SYN / "nope"))
    assert stubs.discover_defs() is None


def test_fingerprint_is_stable_and_content_sensitive(tmp_path):
    fp1 = stubs.fingerprint(SYN)
    assert fp1 == stubs.fingerprint(SYN)
    assert len(fp1) == 64


def test_lock_roundtrip_and_drift(tmp_path):
    lock = tmp_path / "api_version.lock"
    stubs.write_lock(lock, api_version="2703.1.20", pyright_version="1.1.408",
                     stub_sha256=stubs.fingerprint(SYN))
    data = stubs.read_lock(lock)
    assert data["pyright_version"] == "1.1.408"
    drift = stubs.drift_report(data, defs=SYN, pyright_version="1.1.999")
    assert any("pyright" in d for d in drift)          # reported, never absorbed
    assert not any("stub" in d for d in drift)


def test_pyright_pin_env(tmp_path):
    lock = tmp_path / "api_version.lock"
    stubs.write_lock(lock, api_version="x", pyright_version="1.1.408", stub_sha256="0" * 64)
    env = stubs.pyright_pin_env(lock)
    assert env["PYRIGHT_PYTHON_FORCE_VERSION"] == "1.1.408"
```

- [ ] **Step 3: Run to verify failure** — `python -m pytest tests/test_stubs_discovery.py -v` → FAIL (`ModuleNotFoundError: fusionhelper.stubs`).

- [ ] **Step 4: Implement** `fusionhelper/stubs.py`:

```python
"""Autodesk stub discovery, API version, and drift lock.

Drift is REPORTED, never silently absorbed: a Fusion update changes the stubs
and therefore what the gate catches; the lock records what the suite last ran
against (api version, pyright version, stub sha256)."""
import hashlib
import json
import os
from pathlib import Path

_DEFAULT = Path(os.environ.get("APPDATA", "")) / "Autodesk" / "Autodesk Fusion 360" / \
    "API" / "Python" / "defs"


def discover_defs() -> Path | None:
    override = os.environ.get("FUSIONHELPER_DEFS")
    cand = Path(override) if override else _DEFAULT
    return cand if (cand / "adsk").is_dir() else None


def api_version(defs: Path) -> str | None:
    vt = defs.parent.parent / "version.txt"   # .../API/version.txt
    try:
        return vt.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def fingerprint(defs: Path) -> str:
    h = hashlib.sha256()
    for name in ("core.py", "fusion.py"):
        p = defs / "adsk" / name
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()


def write_lock(path: Path, *, api_version: str | None, pyright_version: str,
               stub_sha256: str) -> None:
    path.write_text(json.dumps({"api_version": api_version,
                                "pyright_version": pyright_version,
                                "stub_sha256": stub_sha256}, indent=2) + "\n",
                    encoding="utf-8")


def read_lock(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def drift_report(lock: dict, *, defs: Path | None, pyright_version: str) -> list[str]:
    drift = []
    if pyright_version != lock["pyright_version"]:
        drift.append(f"pyright drifted: lock {lock['pyright_version']}, "
                     f"installed {pyright_version}")
    if defs is not None and fingerprint(defs) != lock["stub_sha256"]:
        drift.append("stub fingerprint drifted: Fusion update changed the API defs; "
                     "re-run gate fidelity tests and re-bless the lock")
    return drift


def pyright_pin_env(lock_path: Path) -> dict[str, str]:
    lock = read_lock(lock_path)
    return {"PYRIGHT_PYTHON_FORCE_VERSION": lock["pyright_version"],
            "PYRIGHT_PYTHON_IGNORE_WARNINGS": "1"}
```

Generate `tests/api_version.lock` once, locally: `python -c "from pathlib import Path; from fusionhelper import stubs; d=stubs.discover_defs(); stubs.write_lock(Path('tests/api_version.lock'), api_version=stubs.api_version(d) if d else None, pyright_version='1.1.408', stub_sha256=stubs.fingerprint(d) if d else '0'*64)"` — on the dev machine this records `2703.1.20` and the real fingerprint.

- [ ] **Step 5: Run tests, verify pass** — `python -m pytest tests/test_stubs_discovery.py -v` → PASS on both a machine with and without Fusion (everything env-driven).

- [ ] **Step 6: Commit**

```bash
git add fusionhelper/stubs.py tests
git commit -m "feat: stub discovery, api-version lock, pyright version pin"
```

### Task 12: Preflight core — staging, config, canary, three outcomes — confidence 85% → mitigated to 90% via Step 0 spike

The risk is the pyright JSON output contract (field names, 0- vs 1-based lines) — verify it empirically before writing the parser, per [[confidence-scoring]].

**Files:**
- Create: `fusionhelper/preflight/__init__.py`, `fusionhelper/preflight/staging.py`, `fusionhelper/preflight/canary.py`, `fusionhelper/preflight/pyright_gate.py`, `tests/test_preflight.py`

**Interfaces:**
- Consumes: `stubs.discover_defs/pyright_pin_env`, `lint.run`, `render.report`, `r8_stub_intact.check_text`
- Produces: `Outcome` enum (`PASS`, `FAIL`, `GATE_BROKEN`, `USAGE`); `run_preflight(script_path, *, expect_stub=True, defs=None) -> PreflightResult(outcome, findings, report, exit_code)`

- [ ] **Step 0: Spike — pin the pyright output contract (do this before any test)**

```bash
python - <<'EOF'
import json, subprocess, sys, tempfile, pathlib
d = pathlib.Path(tempfile.mkdtemp())
(d / "s.py").write_text("import adsk.core\nx: int = 'a'\n")
(d / "pyrightconfig.json").write_text(json.dumps({"include": ["s.py"]}))
p = subprocess.run([sys.executable, "-m", "pyright", "--outputjson", "--project", str(d)],
                   capture_output=True, text=True)
print(p.returncode)
print(p.stdout[:2000])
EOF
```

Record in the task notes: the JSON root keys (`generalDiagnostics`, `summary`), each diagnostic's `file`, `severity`, `message`, `rule`, and `range.start.line` **(0-based — add 1)**. If the shape differs from the parser below, fix the parser to the observed shape before proceeding. Also record wall time; a warm run must be ≤ 2.5 s.

- [ ] **Step 1: Write the failing tests**

`tests/test_preflight.py` — synthetic stubs make these CI-safe; fidelity against Autodesk's stubs is Task 15:

```python
from pathlib import Path

import pytest

from fusionhelper import preflight, verify

SYN = Path(__file__).parent / "synthetic_stubs"

GOOD = """import adsk.core
import adsk.fusion


def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    print(des)
"""

HALLUCINATED = GOOD.replace("Application.get()", "Application.getInstance()")


def write(tmp_path, body, stub=True):
    p = tmp_path / "script.py"
    p.write_text(verify.append_to(body) if stub else body, encoding="utf-8")
    return p


@pytest.fixture(autouse=True)
def _defs(monkeypatch):
    monkeypatch.setenv("FUSIONHELPER_DEFS", str(SYN))


def test_good_script_passes(tmp_path):
    r = preflight.run_preflight(write(tmp_path, GOOD))
    assert r.outcome is preflight.Outcome.PASS
    assert r.exit_code == 0
    assert r.report.splitlines()[0].startswith("PREFLIGHT PASS")


def test_hallucinated_api_fails(tmp_path):
    r = preflight.run_preflight(write(tmp_path, HALLUCINATED))
    assert r.outcome is preflight.Outcome.FAIL
    assert r.exit_code == 1
    assert "getInstance" in r.report


def test_missing_defs_is_gate_broken(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSIONHELPER_DEFS", str(tmp_path / "nowhere"))
    r = preflight.run_preflight(write(tmp_path, GOOD))
    assert r.outcome is preflight.Outcome.GATE_BROKEN
    assert r.exit_code == 3
    assert "do not edit the script" in r.report.lower()


def test_dead_canary_is_gate_broken(tmp_path, monkeypatch):
    # neuter the canary: if pyright stops flagging the known-bad probe,
    # a clean run must NOT be reported as PASS
    monkeypatch.setattr(preflight.canary, "CANARY_TEXT", "x = 1\n")
    r = preflight.run_preflight(write(tmp_path, GOOD))
    assert r.outcome is preflight.Outcome.GATE_BROKEN
    assert r.exit_code == 3


def test_lint_findings_fail_before_pyright_matters(tmp_path):
    r = preflight.run_preflight(write(tmp_path, GOOD.replace(
        "print(des)", "print(adsk.core.ValueInput.createByReal(1.0))")))
    assert r.outcome is preflight.Outcome.FAIL
    assert "R1" in r.report


def test_missing_stub_fails_when_expected(tmp_path):
    r = preflight.run_preflight(write(tmp_path, GOOD, stub=False))
    assert r.outcome is preflight.Outcome.FAIL
    assert "R8" in r.report
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_preflight.py -v` → FAIL (`ModuleNotFoundError: fusionhelper.preflight`).

- [ ] **Step 3: Implement**

`fusionhelper/preflight/canary.py`:

```python
"""The known-bad probe staged next to every checked script.

If pyright, the config, or the stub path silently degrade, these two genuine
hallucinations stop being flagged — and the gate must then report GATE_BROKEN,
never PASS. Both were caught 7/7 in the measurement runs."""

CANARY_NAME = "fh_canary_bad.py"
CANARY_TEXT = """import adsk.core
import adsk.fusion


def run(_context: str):
    v = adsk.core.ValueInput.createByExpression("60 mm")
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)
    sk = des.rootComponent.sketches.item(0)
    sk.geometricConstraints.addFixed(sk.sketchPoints.item(0))
    print(v)
"""
# Expected: >=1 attribute-access diagnostic in this file. createByExpression and
# addFixed do not exist (in the synthetic stubs either — keep it that way).
```

`fusionhelper/preflight/staging.py`:

```python
"""Stage script + canary into an isolated temp dir and generate the config.

mkdtemp + ordinary open() (never mkstemp+fdopen). The isolated dir escapes any
ancestor pyrightconfig.json / pyproject [tool.pyright]. include names the two
staged files explicitly — NEVER ["."] (measured: 4 files / 1168 diagnostics)."""
import json
import shutil
import tempfile
from pathlib import Path

from fusionhelper.preflight.canary import CANARY_NAME, CANARY_TEXT

SCRIPT_NAME = "script.py"


def stage(script_path: Path, defs: Path) -> Path:
    d = Path(tempfile.mkdtemp(prefix="fh_preflight_"))
    shutil.copyfile(script_path, d / SCRIPT_NAME)
    (d / CANARY_NAME).write_text(CANARY_TEXT, encoding="utf-8")
    config = {
        "include": [SCRIPT_NAME, CANARY_NAME],
        "extraPaths": [str(defs)],
        "typeCheckingMode": "basic",
        "pythonVersion": "3.14",
        "reportMissingImports": "error",
        "reportAttributeAccessIssue": "error",
        "reportArgumentType": "none",
        "reportSelfClsParameterName": "none",
    }
    with open(d / "pyrightconfig.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return d
```

Deviation, recorded: the spec's config block says `"include": ["script.py"]`; staging adds the canary as a second *named* file so one pyright process covers both within the ≤2.5 s budget (a second full run would be ~4 s). The constraint's target — never a directory, never ancestor configs — holds. If fidelity testing (Task 15) shows the canary file perturbing script diagnostics, fall back to two sequential runs and raise the published budget; flagged in *Open questions* below.

`fusionhelper/preflight/pyright_gate.py`:

```python
import json
import re
import subprocess
import sys
from pathlib import Path

from fusionhelper.lint.findings import Finding

STUB_SENTINEL_RE = re.compile(r'Import "adsk(\.\w+)?" could not be resolved')


class GateBroken(Exception):
    pass


def run_pyright(staged_dir: Path, env_extra: dict[str, str]) -> dict:
    import os
    env = {**os.environ, **env_extra}
    proc = subprocess.run(
        [sys.executable, "-m", "pyright", "--outputjson", "--project", str(staged_dir)],
        capture_output=True, text=True, env=env)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise GateBroken(f"pyright produced no parseable JSON (stderr: "
                         f"{proc.stderr[:300]!r})") from e


def split_diagnostics(payload: dict, script_name: str, canary_name: str):
    script, canary = [], []
    for d in payload.get("generalDiagnostics", []):
        if STUB_SENTINEL_RE.search(d.get("message", "")):
            raise GateBroken("stub path did not take effect: adsk import unresolved. "
                             "Environment error — fix the machine, do NOT edit the "
                             "script; other diagnostics suppressed as noise.")
        entry = Finding("pyright", d.get("rule") or "PYRIGHT",
                        d["range"]["start"]["line"] + 1,        # 0-based -> 1-based
                        d["range"]["start"]["character"],
                        "error" if d["severity"] == "error" else "warn",
                        d["message"].splitlines()[0])
        name = Path(d["file"]).name
        (script if name == script_name else canary).append(entry)
    return script, canary


def assert_canary_fired(canary_findings) -> None:
    if not any(f.severity == "error" for f in canary_findings):
        raise GateBroken("canary did not fire: the known-bad probe produced no error. "
                         "Config parse, stub resolution or rule severity has silently "
                         "degraded — GATE_BROKEN, never PASS.")
```

`fusionhelper/preflight/__init__.py`:

```python
import enum
import shutil
from dataclasses import dataclass
from pathlib import Path

from fusionhelper import lint, stubs
from fusionhelper.lint import render
from fusionhelper.lint.rules import r8_stub_intact
from fusionhelper.preflight import canary, staging
from fusionhelper.preflight.pyright_gate import (GateBroken, assert_canary_fired,
                                                 run_pyright, split_diagnostics)


class Outcome(enum.Enum):
    PASS = 0
    FAIL = 1
    USAGE = 2
    GATE_BROKEN = 3


@dataclass
class PreflightResult:
    outcome: Outcome
    findings: list
    report: str

    @property
    def exit_code(self) -> int:
        return self.outcome.value


def run_preflight(script_path: Path, *, expect_stub: bool = True,
                  defs: Path | None = None) -> PreflightResult:
    script_path = Path(script_path)
    if not script_path.is_file():
        return PreflightResult(Outcome.USAGE, [], f"no such script: {script_path}")
    defs = defs or stubs.discover_defs()
    if defs is None:
        return PreflightResult(
            Outcome.GATE_BROKEN, [],
            "PREFLIGHT GATE_BROKEN\nAutodesk API stubs not found (set FUSIONHELPER_DEFS "
            "or install Fusion). Environment error - fix the machine, do NOT edit the "
            "script.")
    source = script_path.read_text(encoding="utf-8")
    lint_result = lint.run(source, script_path.name)
    findings = list(lint_result.findings)
    if expect_stub:
        findings.extend(r8_stub_intact.check_text(source))
    staged = staging.stage(script_path, defs)
    try:
        lock = Path(__file__).parents[2] / "tests" / "api_version.lock"
        env = stubs.pyright_pin_env(lock) if lock.exists() else {}
        payload = run_pyright(staged, env)
        script_diags, canary_diags = split_diagnostics(
            payload, staging.SCRIPT_NAME, canary.CANARY_NAME)
        assert_canary_fired(canary_diags)
        findings.extend(script_diags)
    except GateBroken as e:
        return PreflightResult(
            Outcome.GATE_BROKEN, findings,
            f"PREFLIGHT GATE_BROKEN\n{e}\nExit 3: fix the machine, do NOT edit the script.")
    finally:
        shutil.rmtree(staged, ignore_errors=True)
    body = render.report(findings, lint_result.waivers, source, script_path.name)
    errors = [f for f in findings if f.severity == "error"]
    verdict = "PASS" if not errors else "FAIL"
    report = f"PREFLIGHT {verdict} errors={len(errors)}\n{body}"
    return PreflightResult(Outcome.PASS if not errors else Outcome.FAIL, findings, report)
```

- [ ] **Step 4: Run tests, verify pass** — `python -m pytest tests/test_preflight.py -v` → all PASS (uses synthetic stubs; each test spawns one pyright process, so the file takes ~15 s — mark the module `@pytest.mark.slow` if CI minutes matter, but keep it in the default run).

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/preflight tests/test_preflight.py
git commit -m "feat: preflight - staged pyright gate, per-invocation canary, PASS/FAIL/GATE_BROKEN"
```

### Task 13: Preflight CLI + exit codes — confidence 93%

**Files:**
- Create: `fusionhelper/preflight/__main__.py`
- Modify: `tests/test_preflight.py` (add CLI tests)

**Interfaces:**
- Consumes: `run_preflight`
- Produces: `python -m fusionhelper.preflight <script.py> [--no-stub]` printing the report to stdout and exiting 0/1/2/3. This is the exact invocation `SKILL.md` (Task 14) mandates.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_preflight.py`):

```python
import subprocess
import sys


def cli(*args):
    return subprocess.run([sys.executable, "-m", "fusionhelper.preflight", *args],
                          capture_output=True, text=True)


def test_cli_pass_exit_0(tmp_path, monkeypatch):
    p = cli(str(write(tmp_path, GOOD)))
    assert p.returncode == 0, p.stdout + p.stderr
    assert p.stdout.startswith("PREFLIGHT PASS")


def test_cli_fail_exit_1(tmp_path):
    assert cli(str(write(tmp_path, HALLUCINATED))).returncode == 1


def test_cli_usage_exit_2():
    assert cli().returncode == 2
    assert cli(str(Path("does_not_exist.py"))).returncode == 2
```

(CLI subprocesses do not inherit the monkeypatched env — pass `env={**os.environ, "FUSIONHELPER_DEFS": str(SYN)}` into `cli()`; write it that way from the start.)

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_preflight.py -k cli -v` → FAIL (`No module named fusionhelper.preflight.__main__`).

- [ ] **Step 3: Implement** `fusionhelper/preflight/__main__.py`:

```python
import argparse
import sys
from pathlib import Path

from fusionhelper.preflight import Outcome, run_preflight


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m fusionhelper.preflight",
                                 description="Offline gate: pyright + lint + canary")
    ap.add_argument("script", nargs="?", help="generated Fusion script to check")
    ap.add_argument("--no-stub", action="store_true",
                    help="do not require the verification stub (R8)")
    args = ap.parse_args(argv)
    if not args.script:
        ap.print_usage(sys.stderr)
        return Outcome.USAGE.value
    result = run_preflight(Path(args.script), expect_stub=not args.no_stub)
    print(result.report)
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
```

`run_preflight` already returns `USAGE` for a missing file, so both usage paths exit 2.

- [ ] **Step 4: Run tests, verify pass** — `python -m pytest tests/test_preflight.py -v` → all PASS. Manually time: `time python -m fusionhelper.preflight <good script>` warm ≤ 2.5 s.

- [ ] **Step 5: Commit**

```bash
git add fusionhelper/preflight tests/test_preflight.py
git commit -m "feat: preflight CLI - exit codes 0/1/2/3, --no-stub flag"
```

### Task 14: `SKILL.md` — the standing rules — confidence 91%

Phase 1 ships the standing rules + gate/verify workflow; the full declaration-block workflow is Phase 2 and the SKILL.md says so rather than pretending. The reference bundle (`skills/fusion-design/reference/`, 740 lines) already exists — SKILL.md points at it, never duplicates it (inlining the axis table would defeat R6 — detailed-design §2).

**Files:**
- Create: `skills/fusion-design/SKILL.md`, `tests/test_skill_doc.py`

**Interfaces:**
- Consumes: preflight CLI (Task 13), `verify.append_to` + `install_block` (Task 4), repair budgets (detailed-design §4)
- Produces: the procedure Claude follows; consumed by no code

- [ ] **Step 1: Write the failing test** — `tests/test_skill_doc.py` keeps the skill honest against the code ([[docs-in-sync]]):

```python
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
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_skill_doc.py -v` → FAIL (no SKILL.md).

- [ ] **Step 3: Write `skills/fusion-design/SKILL.md`** (complete body):

````markdown
---
name: fusion-design
description: Use when generating Fusion 360 Python for a part the user describes — enforces parametric discipline (named parameters, datums, no raw coordinates), an offline preflight gate before any script reaches Fusion, and a numeric verification block after it runs.
---

# fusion-design

Claude generates Fusion 360 Python that Fusion executes without error and that is
still wrong — misplaced, dimensionally drifted, or dead on the first parameter
edit — and **Fusion will not tell you**. A bracket 40 mm out of position and
embedded in its plate reports zero errors (probe P5). This skill exists to make
those failures inexpressible or unmissable.

## The ten standing rules

Every rule traces to a measured probe. The gate cites rules by number.

- **R1** Never `ValueInput.createByReal` — `createByString`, always. A genuinely
  non-parametric constant is `createByString('3')`.
- **R2** Every `sketchDimensions.add*` is followed by
  `<dim>.parameter.expression = '<param>'`. An unbound dimension is silently dead.
- **R3** Apply geometric constraints first, check `sketch.isFullyConstrained`,
  then dimension only the residual. Over-constraint raises *before* mutating —
  attempt-and-recover is safe.
- **R4** Never select topology by index (`faces[4]`, `edges.item(2)`). Use a
  geometric predicate or capture `entityToken` and re-resolve. Index picks break
  when face count changes, silently.
- **R5** Never reuse a held BRep object across ANY parameter write — it is dead
  document-wide (`InternalValidationError`). Re-resolve by token.
- **R6** Never hardcode axis vectors or assume the plane table. Derive mapping
  from `sketch.sketchToModelSpace()` at runtime. (XZ inverts: world_z = −sketch_y.
  Diagnosis only: `reference/axis-mapping.md` — never compute placement from it.)
- **R7** Parameter names: multi-character `snake_case` (`outer_w`, `wall_t`).
  Fusion rejects unit symbols, function names AND duplicates with the same
  misleading message.
- **R8** Every generated script ends with the verification stub, appended by
  `fusionhelper.verify.append_to()`, unmodified, last in the file.
- **R9** Never catch exceptions in generated scripts. The traceback is the
  diagnostic (Autodesk's own guidance).
- **R10** Never save the document. Ever. Only the user saves.

## Workflow (phase 1)

1. **Parameter table first.** Named `snake_case` user parameters before any
   geometry; derived values as expressions (`wall_t = outer_w / 20`). One value,
   stated once, referenced thereafter.
2. **Named datums.** Construction planes at parameter-bound offsets, named.
   Layout major masses against datums; fillets/chamfers last and minimal.
3. **Generate** the script per `reference/api-recipes.md` (read the section you
   need at the moment of use — do not carry the whole file).
4. **Append the stub:** `python -c "from pathlib import Path; from fusionhelper import verify; p=Path('box.py'); p.write_text(verify.append_to(p.read_text(encoding='utf-8')), encoding='utf-8')"`
   — and ensure the block is installed once per machine:
   `python -c "from fusionhelper import verify; print(verify.install_block())"`.
5. **Gate:** `python -m fusionhelper.preflight box.py`
   - exit 0 PASS → send to Fusion
   - exit 1 FAIL → fix the script (findings cite rule numbers)
   - exit 3 GATE_BROKEN / environment → fix the machine. **Do not edit the script.**
6. **Execute** via the official Fusion MCP (`fusion_mcp_execute`,
   `featureType: "script"`). The stub prints one `FH_VERDICT1 {...}` JSON line.
7. **Verify:** parse the verdict. `pass` → render screenshots *for the user*
   (renders are for the human — numeric read-back is the oracle, not your eyes).
   Anything else → repair loop.
8. **Repair loop.** Budgets: preflight fixes 3 (offline, separate); runtime with
   a taxonomy code 3; unclassified runtime 2; verification failures 2; hard cap
   **5 `fusion_mcp_execute` calls per request**. Abort early when: the identical
   failure signature appears twice; an A→B→A recurrence appears; error count
   fails to strictly decrease twice. Third attempt is always a from-scratch
   regeneration, never a patch. `model.not_restored`, `model.inert` or a
   timeline error state → undo (`fusion_mcp_update`) and regenerate.
9. **When giving up:** say what is wrong in plain language, show the attempt
   history, state the document's condition, ask one specific question, and
   attach a render.

## Honest limits

Every check verifies the model against what was *declared*. A green verdict
means: built correctly, stays editable, matches the stated numbers. It does NOT
mean "this is the part you wanted" — that judgement belongs to the human, from
the renders. Say it that way. See `reference/limits.md`.
````

- [ ] **Step 4: Run tests, verify pass** — `python -m pytest tests/test_skill_doc.py -v` → PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/fusion-design/SKILL.md tests/test_skill_doc.py
git commit -m "feat: fusion-design SKILL.md - ten standing rules, gate workflow, repair budgets"
```

### Task 15: Good corpus + local gate fidelity + docs sweep — confidence 90%

The false-positive claim goes under test rather than being asserted. The eight probe *scripts* were never committed — the corpus is built from the verified recipes in `skills/fusion-design/reference/api-recipes.md` (same code, same provenance) and is extended with the real probe scripts if they are recovered later.

**Files:**
- Create: `tests/fixtures/lint/good/corpus_parametric_plate.py` (P1 shape: 3 params, constrained rect recipe, bound extrude), `tests/fixtures/lint/good/corpus_datum_bracket.py` (P5-B shape: datum plane offset by expression, bound dims), `tests/fixtures/lint/good/corpus_predicate_pick.py` (P4 shape: entityToken + predicate selection), `tests/fixtures/lint/good/corpus_verify_tail.py` (a build + intact stub tail), `tests/test_gate_fidelity.py`
- Modify: none

Each corpus file is assembled by pasting the relevant `api-recipes.md` sections into a `run()` skeleton — the recipes are verified live code. Zero `# EXPECT:` markers: the existing harness asserts zero findings automatically.

- [ ] **Step 1: Add the corpus fixtures, run the harness** — `python -m pytest tests/test_lint_fixtures.py -v` → any failure here is a false positive; per the spec the response is to **tighten the rule**, not weaken the fixture (unless the fixture genuinely violates a standing rule — then fix the fixture and say so in the commit).

- [ ] **Step 2: Add local-only fidelity tests** — `tests/test_gate_fidelity.py`:

```python
"""Gate fidelity against Autodesk's REAL stubs. Local-only: skipped when the
stubs are absent (CI has only synthetic stubs)."""
from pathlib import Path

import pytest

from fusionhelper import preflight, stubs, verify

pytestmark = pytest.mark.skipif(stubs.discover_defs() is None,
                                reason="Autodesk stubs not installed")

SEVEN = [
    "des.userParameters.addd('w', v, 'mm', '')",
    "adsk.core.ValueInput.createByExpression('60 mm')",
    "sk.geometricConstraints.addFixed(pt)",
    "sk.isFullyConstrainedd",
    "sk.sketchCurves.sketchPolylines",
    "app.activeProduct.rootComponentt",
    "import adsk.geometry",
]


@pytest.mark.parametrize("bad", SEVEN)
def test_hallucination_caught(tmp_path, bad, monkeypatch):
    monkeypatch.delenv("FUSIONHELPER_DEFS", raising=False)
    body = ("import adsk.core\nimport adsk.fusion\n\n\n"
            "def run(_context: str):\n"
            "    app = adsk.core.Application.get()\n"
            "    des = adsk.fusion.Design.cast(app.activeProduct)\n"
            "    sk = des.rootComponent.sketches.item(0)\n"   # sketches/sketchPoints are
            "    pt = sk.sketchPoints.item(0)\n"              # not R4 collections: no waiver
            f"    v = None\n    {bad}\n")
    if bad.startswith("import "):
        body = bad + "\n" + body
    p = tmp_path / "script.py"
    p.write_text(verify.append_to(body), encoding="utf-8")
    r = preflight.run_preflight(p)
    assert r.outcome is preflight.Outcome.FAIL, r.report


def test_stub_tail_passes_real_preflight(tmp_path):
    good = Path("tests/fixtures/lint/good/corpus_verify_tail.py").read_text(encoding="utf-8")
    p = tmp_path / "script.py"
    p.write_text(good, encoding="utf-8")
    r = preflight.run_preflight(p)
    assert r.outcome is preflight.Outcome.PASS, r.report
```

Run locally: `python -m pytest tests/test_gate_fidelity.py -v` → 7/7 hallucinations FAIL the gate, stub tail PASSes. This is the "0 false positives, 7/7 caught" measurement reproduced as a regression test.

- [ ] **Step 3: Docs sweep ([[docs-in-sync]])** — `grep -rn "design/verify\|0.3 s\|createByReal is fine" docs/` → update `docs/README.md`'s "not yet wired together" table (they are wired now) and any stale path. Verify every path named in `docs/README.md` exists on disk.

- [ ] **Step 4: Full suite + lint + types** — `python -m pytest -v && ruff check . && pyright fusionhelper` → green.

- [ ] **Step 5: Commit**

```bash
git add tests docs
git commit -m "test: good corpus from verified recipes, 7/7 fidelity regression, docs sweep"
```

### Task 16: Integration harness — MCP client + scratch-document lifecycle — confidence 82% → mitigated to 88% via Step 0

Opt-in, live Fusion required. Risk: the MCP envelope details and document-lifecycle behaviour are measured facts from the probe run, but the harness itself is new code against a live app. Step 0 re-verifies connectivity and the envelope before any test is written against it.

**Files:**
- Create: `tests/integration/__init__.py`, `tests/integration/conftest.py`, `tests/integration/mcp_client.py`, `tests/integration/scratch.py`

**Interfaces:**
- Consumes: nothing in-package (pure stdlib `urllib` — httpx/requests deliberately absent)
- Produces: `McpClient(url).execute(script_text) -> ExecResult(success, message, error)`; `scratch_doc()` context manager (create-tag-yield-close); `pytest.mark.fusion` marker; env gate `FUSION_MCP_URL` (default `http://127.0.0.1:27182/mcp`), suite skipped entirely when unset/unreachable

- [ ] **Step 0: Spike — connectivity + envelope re-verification**

```bash
FUSION_MCP_URL=http://127.0.0.1:27182/mcp python - <<'EOF'
import json, os, urllib.request
url = os.environ["FUSION_MCP_URL"]
def post(payload, expect_json=True):
    req = urllib.request.Request(url, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json",
                                  "Accept": "application/json, text/event-stream"})
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read()
        return (r.status, json.loads(body) if expect_json and body else body)
print(post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18",
                       "capabilities": {}, "clientInfo": {"name": "fh", "version": "0"}}}))
print(post({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect_json=False))
EOF
```

Confirm: initialize returns the server info; the notification returns **202 with an empty body** (a client that JSON-parses every response crashes on the handshake — measured). Record whether a session id header is required on subsequent calls; adjust `mcp_client.py` to what is observed.

- [ ] **Step 1: Implement the client** — `tests/integration/mcp_client.py`:

```python
"""Minimal MCP client over stdlib urllib. Envelope (measured):
result.content[0].text is a JSON STRING containing
{"message": <stdout>, "success": true} or {"error": <stdout+traceback>,
"success": false}. Script failures are HTTP 200 + success:false, never a
JSON-RPC error."""
import json
import urllib.request
from dataclasses import dataclass


@dataclass
class ExecResult:
    success: bool
    message: str
    error: str


class McpClient:
    def __init__(self, url: str):
        self.url = url
        self._id = 0

    def _post(self, payload: dict, expect_json: bool = True):
        req = urllib.request.Request(
            self.url, json.dumps(payload).encode(),
            {"Content-Type": "application/json",
             "Accept": "application/json, text/event-stream"})
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read()
            return json.loads(body) if expect_json and body else None

    def initialize(self):
        self._id += 1
        out = self._post({"jsonrpc": "2.0", "id": self._id, "method": "initialize",
                          "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                     "clientInfo": {"name": "fusionhelper-tests",
                                                    "version": "0.1.0"}}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"},
                   expect_json=False)   # 202, EMPTY body — do not parse
        return out

    def execute(self, script_text: str) -> ExecResult:
        self._id += 1
        out = self._post({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                          "params": {"name": "fusion_mcp_execute",
                                     "arguments": {"featureType": "script",
                                                   "object": {"script": script_text}}}})
        inner = json.loads(out["result"]["content"][0]["text"])
        return ExecResult(bool(inner.get("success")),
                          inner.get("message", ""), inner.get("error", ""))

    def undo(self):
        self._id += 1
        return self._post({"jsonrpc": "2.0", "id": self._id, "method": "tools/call",
                           "params": {"name": "fusion_mcp_update",
                                      "arguments": {"operation": "undo"}}})
```

- [ ] **Step 2: Scratch lifecycle** — `tests/integration/scratch.py`. Measured constraints: no `new`-document MCP operation (documents are created from inside a script); root component cannot be renamed (tag via `des.attributes.add`); **cleanup is harness-driven** — a failing script never reaches its own cleanup. Four layers: per-test `finally`, session-end sweep, pre-session sweep of previous sessions' leaks, `atexit`. The close guard refuses to touch a saved document, an untagged one, or another session's tag. Session tag: `fh-test-<uuid4>`. Creation script: `app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)` then `des.attributes.add('fusionhelper', 'scratch', '<session-tag>')`; sweep script enumerates `app.documents`, closes (without saving) every unsaved document whose design carries the session's tag (or any `fusionhelper/scratch` attribute in the pre-session sweep).

- [ ] **Step 3: conftest** — `tests/integration/conftest.py`: skip the whole directory unless `FUSION_MCP_URL` is set and `initialize()` succeeds; session-scoped `client` fixture; `scratch` fixture wrapping each test in create/sweep with `finally`; `atexit` sweep registration; pre-session sweep at fixture setup.

- [ ] **Step 4: Smoke test** — one `test_smoke.py`: execute `print('fh-smoke')`, assert `success and 'fh-smoke' in message`; deliberately execute `raise RuntimeError('fh-boom')`, assert `not success and 'fh-boom' in error`. Run with Fusion open: both pass, zero documents leaked (check Fusion's window list).

- [ ] **Step 5: Commit**

```bash
git add tests/integration
git commit -m "test: opt-in Fusion MCP harness - urllib client, tagged scratch docs, 4-layer cleanup"
```

### Task 17: P1–P8 as integration regression tests — confidence 85% (bounded by live-Fusion variance)

Each probe becomes a test that runs its script via the harness and **asserts on parsed `FH_RESULT` JSON, never prose** (the probe run itself caught a script whose pre-written summary contradicted its own data). Scripts print `FH_RESULT {json}` and the test parses that line. One test file per probe; each script body reproduces the probe recipe from `docs/probe-results.md` + `api-recipes.md`.

**Files:**
- Create: `tests/integration/test_p1_parametric.py` … `test_p8_sweep.py`, `tests/integration/probe_scripts.py` (the eight script bodies as string constants, each ending with a `print('FH_RESULT ' + json.dumps(data))`)

Assertions per probe (from the measured results):

| Test | Parses and asserts |
|---|---|
| P1 | after `plate_w` 60→80, `plate_t` 5→8: bbox == (8.0, 4.0, 0.8) ±1e-4; unhealthy == 0 |
| P2 | `isFullyConstrained` sequence [False, False, False, False, True] across the 5 recipe steps |
| P3 | three over-constraint attempts each raise; sketch still fullyConstrained; the three message classes distinguishable (`Already has same dimension`, `already been applied`, `VCS_SKETCH_SOLVING_FAILED`) |
| P4 | after chamfer: index-pick face changed identity; entityToken round-trip still top face; predicate finds top at new index |
| P5 | datum bracket offsets == 0.0 on both axes after the edit; raw bracket off by (40, 8) mm; `unhealthy == 0` **asserted** — if Fusion ever starts complaining, we want to know |
| P6 | all four hole dims follow one `hole_d` edit |
| P7 | interference count == 1, volume ≈ 3.2 cm³, pair attributed |
| P8 | `plate_w=30` sweep step reports the HoleCuts reference failure; the other three extremes stay healthy (same asserted-silence rationale as P5) |

- [ ] **Step 1:** Port each probe script into `probe_scripts.py` with a machine-readable `FH_RESULT` print (the bodies are in `docs/probe-results.md`; keep every measured constant).
- [ ] **Step 2:** Write the eight tests: `res = client.execute(P1); data = parse_fh_result(res.message); assert ...` — `parse_fh_result` lives in `mcp_client.py` and raises if the line is absent.
- [ ] **Step 3:** Run against live Fusion: `FUSION_MCP_URL=... python -m pytest tests/integration -v` → 8 pass, zero leaked documents after the run **and** after a deliberately interrupted run (Ctrl-C mid-P5, then re-run pre-session sweep and count documents).
- [ ] **Step 4:** Update `tests/api_version.lock` if the fidelity run bumped anything; commit:

```bash
git add tests/integration tests/api_version.lock
git commit -m "test: P1-P8 probes as live regression suite asserting parsed FH_RESULT JSON"
```

---

## Open questions carried into execution

1. **Canary staged beside the script** (Task 12 deviation): one pyright process for both files vs the spec's literal single-file `include`. Validated or reversed by Task 15's fidelity run.
2. **`sketch.profiles.item(0)`** stays outside R4 (the universal idiom). Phase-1 usage evidence decides whether it enters R4 or gets a `find_profile` helper (detailed-design open question 2–3).
3. **R5 severity** set to WARN here (the write is legal; the hazard is later use). If phase-1 evidence shows repair scripts never hold BReps across writes, drop R5 (design open question 8).
4. **Probe scripts** are reconstructed from the recipe docs, not recovered originals — the corpus and P-tests are only as faithful as `probe-results.md`'s transcriptions.
5. **Repair-loop bound** (spec open question 1) is answered in SKILL.md as budgets + early-abort rules from detailed-design §4; it is prose discipline in phase 1, enforced by nothing — the v2 wrapper decision waits for evidence.

## Self-review record

Run per writing-plans: spec coverage walked section-by-section (gate ✔ tasks 11–13, lint rules ✔ 2–9, verify ✔ 4, skill rules ✔ 14, testing tiers ✔ 2/15/16–17, CI split ✔ 1/12/15, drift lock ✔ 11; declaration block / chain check / emit — out of scope, Phase 2/3 by design). Placeholder scan clean (every code step carries runnable content; Task 16 steps 2–3 specify exact behaviour and named layers where live-endpoint observation must precede code, with Step 0 capturing the observation). Type consistency: `Finding(rule_id, rule_number, line, col, severity, message, fix)` positional order used identically in Tasks 2, 5–9, 12; `Outcome.value` == exit code; `check_text` vs `check` split declared in Task 9 and consumed in Task 12. Cross-read prose-vs-code ([[cross-read-prose-vs-code]]): Task 10's second test contradiction caught and resolved in-place (warns-don't-gate decision recorded); guardrail task-number references corrected to 12/16.

## Execution

Feature branch per task-start standard is already in place (`plan/fusionhelper-phase1-gate`); implementation should branch `feature/phase1-gate` from main after this plan merges, or continue on a single feature branch if the user prefers.

Suggested batching for review checkpoints: Tasks 1–3 (engine), 4 (verify move), 5–9 (rules), 10–13 (gate), 14–15 (skill + corpus), 16–17 (live Fusion, needs the user's machine).
