# Enforcement Round 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the enforcement gaps an external review found: lint-enforce R10 (no save) and R9 (no catch, with stub/kit region scoping), close R4's alias false negative, split SKILL.md's diagnosis lore into a reference file, and add session telemetry so the skill's effect is measurable.

**Architecture:** Three new/extended AST lint rules follow the existing one-module-per-rule pattern under `fusionhelper/lint/rules/`, registered in the three mandatory places (rule module, `rules/__init__.py:ALL_RULES`, `findings.py:RULES`). A new `lint/regions.py` computes stub/kit exempt line ranges from existing markers. Telemetry is a small JSONL append + summary CLI. SKILL.md is restructured by an explicit move map into `reference/hazards.md`.

**Tech Stack:** Python 3.12, stdlib `ast`/`argparse`/`json`, pytest 8, ruff (E,F,I,B,UP,SIM, line-length 100), pyright basic.

## Guardrails (from project memory, surface before executing)

- **[[three-place-rule-registration]]** (conf ≈1.0, BugBot-proven on R11/PR #5): a new rule MUST be registered in `fusionhelper/lint/rules/<file>.py`, `fusionhelper/lint/rules/__init__.py` (import + `ALL_RULES`), AND `fusionhelper/lint/findings.py` (`RULES` entry / `checked` flag). Missing the third silently breaks coverage lines, restatements, and waiver suppression.
- **[[docs-in-same-pr]]** (conf 0.95, evidence 7): doc/docstring updates land in the same task as the behavior change, or in this branch's explicit docs-sweep task — never a follow-up PR. Verify every factual token in rewritten doc lines against source.
- **[[no-git-add-A]]** (process post-mortem): stage explicit paths only. The working tree contains unrelated untracked user files (`banana_*.jpg/png`, `fidgetspinners/`, `docs/fidget-*`, `docs/supernova-72-spec.md`, `skills/print-in-place-design/`) that must never be committed by this branch.
- **[[ruff-py312-idioms]]** (conf 0.9): `from datetime import UTC` (UP017), no `(str, Enum)` (UP042). Run `python -m ruff check .` before every commit; spec-provided code is not lint-clean by default.
- **[[coverage-line-derived]]** (repo invariant, `render.py` docstring): verdicts and coverage lines are derived from `RULES` at render time. Flipping `checked` flags changes coverage text — the literal assertions in `tests/test_render.py` and `tests/test_preflight.py` must be updated to the new truth in the SAME task as the flip.

## Global Constraints

- Python ≥3.12 (`pyproject.toml`), ruff select E,F,I,B,UP,SIM, line-length 100.
- Shell is Windows PowerShell 5.1: no `&&` chaining; run commands separately.
- Test gate for every task: `python -m pytest -q` (all pass) and `python -m ruff check .` (clean), run before each commit.
- New lint rules: severity conventions match existing rules (R-rules are `"error"` except R11 `"warn"`); findings carry `rule_id`, `NUMBER`, line, col, message, fix.
- Fixture contract: every file under `tests/fixtures/lint/` is linted by `tests/test_lint_fixtures.py`; expected findings are inline `# EXPECT: R<n>` markers on the finding's line (`tests/markers.py`). A new rule that fires on EXISTING fixtures without markers breaks the suite — run the suite and reconcile.
- Do not modify `fusionhelper/verify/fh_verify.py` or `fusionhelper/verify/stub_text.py` stub text (byte-constant by design).
- Commit messages: conventional commits, end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: R10 no-save lint rule

**Confidence:** 95%

**Files:**
- Create: `fusionhelper/lint/rules/r10_no_save.py`
- Modify: `fusionhelper/lint/rules/__init__.py` (import + `ALL_RULES`)
- Modify: `fusionhelper/lint/findings.py` (R10 entry: `checked=True`, restatement; comment on line 9)
- Modify: `tests/test_render.py:28-29,49`, `tests/test_preflight.py:84,91` (coverage strings)
- Create: `tests/fixtures/lint/bad/r10_no_save.py`, `tests/fixtures/lint/good/r10_no_save.py`

**Interfaces:**
- Produces: module `r10_no_save` with `RULE_ID = "no-save"`, `NUMBER = "R10"`, `RESTATEMENT`, `check(tree, source) -> list[Finding]` (the shape `ALL_RULES` iterates).

- [ ] **Step 1: Write the failing fixtures**

`tests/fixtures/lint/bad/r10_no_save.py`:
```python
import adsk.core


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    doc.save("checkpoint: wall v3")  # EXPECT: R10
    app.activeDocument.saveAs("copy", None, "", "")  # EXPECT: R10
```

`tests/fixtures/lint/good/r10_no_save.py`:
```python
import adsk.core


def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    doc.save("checkpoint: rim v2")  # fusionhelper: allow R10 — user consented checkpoint after green verdict
    state = {"phase": "done"}
    print(state)
```

- [ ] **Step 2: Run to verify fixtures fail**

Run: `python -m pytest tests/test_lint_fixtures.py -q -k r10`
Expected: FAIL — bad fixture expects `(7, "R10")`/`(8, "R10")` but no rule produces them; good fixture reports an unknown-suppression? No — R10 already exists in `RULES`, so the good fixture fails with an "unused suppression" WAIVER finding instead (nothing fires yet). Both failures confirm the rule is missing.

- [ ] **Step 3: Implement the rule**

`fusionhelper/lint/rules/r10_no_save.py`:
```python
import ast

from fusionhelper.lint.findings import Finding

RULE_ID = "no-save"
NUMBER = "R10"
RESTATEMENT = "Never save the document — checkpoint saves need a waiver naming user consent"

# Any attribute call named save/saveAs. A non-document .save() (rare in
# generated scripts) is a tolerable false positive: the waiver is the escape
# and it forces the reason to be stated.
_SAVERS = {"save", "saveAs"}

_FIX = ("remove the save; a consented checkpoint save is waived per line: "
        "# fusionhelper: allow R10 — user consented checkpoint after green verdict")


def check(tree: ast.AST, source: str) -> list[Finding]:
    findings = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr in _SAVERS):
            findings.append(Finding(
                RULE_ID, NUMBER, node.lineno, node.col_offset, "error",
                f"{node.func.attr}() call — R10: saving is the user's decision; "
                "an unconsented save creates a cloud version the user did not ask for",
                _FIX))
    return findings
```

- [ ] **Step 4: Register in the three places**

`fusionhelper/lint/rules/__init__.py`: add `r10_no_save` to the import block and to `ALL_RULES` (keep numeric order: after `r8_stub_intact`, before `r11_ui_breathing`).

`fusionhelper/lint/findings.py`: change the R10 entry to
```python
    "R10": RuleInfo("no-save", "R10",
                    "Never save the document — checkpoint saves need a waiver "
                    "naming user consent", True),
```
and update the line-9 comment to `checked: bool  # False for R3/R9 — runtime/convention; named in the coverage line`.

- [ ] **Step 5: Update coverage-string assertions**

- `tests/test_render.py:29` → `assert "not checked: R3 R8 R9" in lines[-1]`
- `tests/test_render.py:28` → `assert lines[-1].startswith("checked: R1 R2 R4 R5 R6 R7 R10 R11 ·")`
- `tests/test_render.py:48` → `assert last.startswith("checked: R1 R2 R4 R5 R6 R7 R8 R10 R11 ·")`
- `tests/test_render.py:49` → `assert "not checked: R3 R9" in last`
- `tests/test_preflight.py:84` → `"not checked: R3 R9"`; `tests/test_preflight.py:91` → `"not checked: R3 R8 R9"`

- [ ] **Step 6: Full suite + lint, reconcile any fixture that now trips R10**

Run: `python -m pytest -q` then `python -m ruff check .`
Expected: PASS (no existing fixture or corpus file calls `.save(` — verified by grep at plan time).

- [ ] **Step 7: Commit**

```
git add fusionhelper/lint/rules/r10_no_save.py fusionhelper/lint/rules/__init__.py fusionhelper/lint/findings.py tests/fixtures/lint/bad/r10_no_save.py tests/fixtures/lint/good/r10_no_save.py tests/test_render.py tests/test_preflight.py
git commit -m "feat(lint): R10 no-save is now checked ..."
```

---

### Task 2: Region exemptions + R9 no-catch lint rule

**Confidence:** 92%

**Files:**
- Modify: `fusionhelper/bundle.py` (extract `MARK_BEGIN_PREFIX`)
- Create: `fusionhelper/lint/regions.py`
- Create: `fusionhelper/lint/rules/r9_no_catch.py`
- Modify: `fusionhelper/lint/rules/__init__.py`, `fusionhelper/lint/findings.py`
- Modify: `tests/test_render.py`, `tests/test_preflight.py` (coverage strings again)
- Create: `tests/test_regions.py`, `tests/fixtures/lint/bad/r9_no_catch.py`, `tests/fixtures/lint/good/r9_bundled_kit.py`

**Interfaces:**
- Consumes: `STUB_SENTINEL` from `fusionhelper.verify.stub_text`; `MARK_BEGIN_PREFIX`/`MARK_END` from `fusionhelper.bundle`.
- Produces: `regions.exempt_lines(source: str) -> set[int]` (1-based line numbers inside the appended stub and/or bundled-kit block); module `r9_no_catch` with the standard rule shape.

- [ ] **Step 1: Extract the marker prefix constant**

In `fusionhelper/bundle.py`, replace lines 15-16 with:
```python
MARK_BEGIN_PREFIX = "# fh-bundle: kit begin"
MARK_BEGIN = MARK_BEGIN_PREFIX + " v%s %s"
MARK_END = "# fh-bundle: kit end"
```
and in `bundle_text` replace the literal `"# fh-bundle: kit begin"` (line 42) with `MARK_BEGIN_PREFIX`.

- [ ] **Step 2: Write failing region tests**

`tests/test_regions.py`:
```python
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
```

- [ ] **Step 3: Run to verify they fail**

Run: `python -m pytest tests/test_regions.py -q`
Expected: FAIL with `ModuleNotFoundError`/`ImportError` (no `regions` module).

- [ ] **Step 4: Implement regions**

`fusionhelper/lint/regions.py`:
```python
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
```

- [ ] **Step 5: Run region tests to verify they pass**

Run: `python -m pytest tests/test_regions.py -q` — Expected: PASS.

- [ ] **Step 6: Write failing R9 fixtures**

`tests/fixtures/lint/bad/r9_no_catch.py`:
```python
import adsk.core


def run(_context: str):
    app = adsk.core.Application.get()
    try:  # EXPECT: R9
        app.log("x")
    except Exception:
        pass
    try:  # fusionhelper: allow R9 — probe characterises over-constraint error text
        app.log("y")
    except RuntimeError:
        raise
```
(The waived `try` produces no expected marker — the waiver consumes it; the first one must fire.)

`tests/fixtures/lint/good/r9_bundled_kit.py`:
```python
# fh-bundle: kit begin v2 deadbeef0000
try:
    KIT_FLAG = True
except Exception:
    KIT_FLAG = False
# fh-bundle: kit end
x = 1

# fusionhelper: verification stub v1
try:
    pass
except Exception:
    pass
```
Also confirm `tests/fixtures/lint/good/corpus_verify_tail.py` (real appended stub with try/except at lines 66-85) still reports zero findings — it is the live regression for stub exemption.

- [ ] **Step 7: Run to verify fixtures fail**

Run: `python -m pytest tests/test_lint_fixtures.py -q -k r9`
Expected: FAIL (no R9 finding produced yet; waiver in bad fixture reports unused suppression).

- [ ] **Step 8: Implement R9**

`fusionhelper/lint/rules/r9_no_catch.py`:
```python
import ast

from fusionhelper.lint.findings import Finding
from fusionhelper.lint import regions

RULE_ID = "no-catch"
NUMBER = "R9"
RESTATEMENT = "Never catch exceptions in generated scripts — the traceback is the diagnostic"

_FIX = ("delete the handler and let the exception escape (Autodesk guidance: the "
        "traceback is the diagnostic); a probe that must characterise an exception "
        "waives per line with the reason")


def check(tree: ast.AST, source: str) -> list[Finding]:
    exempt = regions.exempt_lines(source)
    findings = []
    for node in ast.walk(tree):
        if (isinstance(node, (ast.Try, ast.TryStar)) and node.handlers
                and node.lineno not in exempt):
            findings.append(Finding(
                RULE_ID, NUMBER, node.lineno, node.col_offset, "error",
                "try/except in a generated script — a swallowed exception turns a "
                "loud failure into silent wrong geometry", _FIX))
    return findings
```
(`try/finally` with no `except` clause has empty `handlers` and is allowed.)

- [ ] **Step 9: Register in the three places + flip checked**

`rules/__init__.py`: import `r9_no_catch`, insert in `ALL_RULES` after `r8_stub_intact`, before `r10_no_save`.
`findings.py`: R9 entry becomes
```python
    "R9": RuleInfo("no-catch", "R9",
                   "Never catch exceptions in generated scripts — the traceback "
                   "is the diagnostic", True),
```
and the line-9 comment becomes `checked: bool  # False only for R3 — runtime rule; named in the coverage line`.

- [ ] **Step 10: Update coverage-string assertions to final truth**

- `tests/test_render.py:28` → `checked: R1 R2 R4 R5 R6 R7 R9 R10 R11 ·`
- `tests/test_render.py:29` → `"not checked: R3 R8"`
- `tests/test_render.py:48` → `checked: R1 R2 R4 R5 R6 R7 R8 R9 R10 R11 ·`
- `tests/test_render.py:49` → `"not checked: R3"`
- `tests/test_preflight.py:84` → `"not checked: R3"`; `:91` → `"not checked: R3 R8"`

- [ ] **Step 11: Full suite + lint; reconcile fixture drift**

Run: `python -m pytest -q` then `python -m ruff check .`
Watch: `tests/fixtures/verify/stub_example.py` is under `fixtures/verify/`, NOT `fixtures/lint/`, so it is not linted by the fixture test — no marker needed. `corpus_verify_tail.py` must stay green via the stub exemption.

- [ ] **Step 12: Commit**

Stage exactly: `fusionhelper/bundle.py fusionhelper/lint/regions.py fusionhelper/lint/rules/r9_no_catch.py fusionhelper/lint/rules/__init__.py fusionhelper/lint/findings.py tests/test_regions.py tests/fixtures/lint/bad/r9_no_catch.py tests/fixtures/lint/good/r9_bundled_kit.py tests/test_render.py tests/test_preflight.py`

---

### Task 3: R4 alias tracking (close the local-alias false negative)

**Confidence:** 90% (risk: range-loop tracker interplay; mitigated by the fixture matrix below and the single-assignment restriction)

**Files:**
- Modify: `fusionhelper/lint/rules/r4_index_topology.py`
- Create: `tests/fixtures/lint/bad/r4_alias.py`, `tests/fixtures/lint/good/r4_alias.py`

**Interfaces:**
- Produces: unchanged rule shape; new internal `_alias_map(tree) -> dict[str, str]` and `_receiver(node, aliases) -> str | None` replacing `_collection_receiver` call sites.

- [ ] **Step 1: Write failing fixtures**

`tests/fixtures/lint/bad/r4_alias.py`:
```python
import adsk.fusion


def run(_context: str):
    root = adsk.fusion.Design.cast(None).rootComponent
    body = root.bRepBodies.item(0)  # EXPECT: R4
    faces = body.faces
    top = faces[4]  # EXPECT: R4
    edges = body.edges
    rim = edges.item(2)  # EXPECT: R4
    print(top, rim)
```

`tests/fixtures/lint/good/r4_alias.py`:
```python
import adsk.fusion


def run(_context: str):
    root = adsk.fusion.Design.cast(None).rootComponent
    body = root.bRepBodies[0]  # fusionhelper: allow R4 — fixture needs one seeded body
    faces = body.faces
    for i in range(faces.count):
        f = faces[i]
        print(f.area)
    faces = None  # second assignment: name no longer a trusted alias
    items = [1, 2, 3]
    print(items[0])
```
(Second assignment drops `faces` from the alias map — indexing a reassigned name must NOT fire. `items[0]` is a plain list.)

- [ ] **Step 2: Run to verify fixtures fail**

Run: `python -m pytest tests/test_lint_fixtures.py -q -k r4_alias`
Expected: bad fixture FAILS (alias picks at `faces[4]` / `edges.item(2)` produce no findings today). NOTE: the good fixture may PASS already — the regression it guards (range-count exemption over an alias, reassignment) only matters after Step 3; keep it.

- [ ] **Step 3: Implement alias tracking**

In `r4_index_topology.py`:

```python
def _collection_chain(node: ast.expr) -> str | None:
    """Chain text when node is a pure dotted chain ending in a collection."""
    if isinstance(node, ast.Attribute) and node.attr in _COLLECTIONS:
        return _chain_text(node)
    return None


def _alias_map(tree: ast.AST) -> dict[str, str]:
    """Names assigned EXACTLY ONCE in the file, to a collection chain.

    Whole-file, single-assignment scope on purpose: generated scripts are
    flat, and a name rebound anywhere is no longer a trusted alias (the
    false-positive guard). A local alias walking past the rule was the
    review-confirmed false negative this closes.
    """
    counts: dict[str, int] = {}
    values: dict[str, str] = {}

    def _bind(name: str) -> None:
        counts[name] = counts.get(name, 0) + 1

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        _bind(n.id)
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                chain = _collection_chain(node.value)
                if chain:
                    values[node.targets[0].id] = chain
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.For, ast.AsyncFor)):
            for n in ast.walk(node.target):
                if isinstance(n, ast.Name):
                    _bind(n.id)
        elif isinstance(node, ast.comprehension):
            for n in ast.walk(node.target):
                if isinstance(n, ast.Name):
                    _bind(n.id)
        elif isinstance(node, ast.arg):
            _bind(node.arg)
    return {name: chain for name, chain in values.items() if counts.get(name) == 1}


def _receiver(node: ast.expr, aliases: dict[str, str]) -> str | None:
    chain = _collection_chain(node)
    if chain is not None:
        return chain
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    return None
```

Then thread `aliases` through:
- `check()` computes `aliases = _alias_map(tree)` first, passes it to the tracker (`_RangeIterationTracker(aliases)`), and replaces both `_collection_receiver(...)` call sites with `_receiver(..., aliases)`.
- `_RangeIterationTracker.__init__(self, aliases)` stores it; `visit_For` replaces its `_collection_receiver(it.args[0].value)` and the two exemption-matching calls with `_receiver(..., self.aliases)`. Keep `_collection_receiver` deleted (no dead code); keep the node-identity exemption discipline unchanged.

- [ ] **Step 4: Run fixture tests**

Run: `python -m pytest tests/test_lint_fixtures.py -q`
Expected: PASS — including all pre-existing r4 fixtures (`bad/r4_index_topology.py`, `good/r4_index_topology.py`, corpus files: `rect = lines.addTwoPointRectangle(...)` is a Call value, never aliased).

- [ ] **Step 5: Full suite + lint + commit**

`python -m pytest -q`; `python -m ruff check .`
Stage exactly: `fusionhelper/lint/rules/r4_index_topology.py tests/fixtures/lint/bad/r4_alias.py tests/fixtures/lint/good/r4_alias.py`

---

### Task 4: Telemetry (record + summary CLI)

**Confidence:** 93%

**Files:**
- Create: `fusionhelper/telemetry.py`
- Create: `tests/test_telemetry.py`

**Interfaces:**
- Consumes: `fusionhelper.verify.default_home()` for the default location.
- Produces: `record_entry(...) -> Path`, `summarize(path) -> dict`, `main(argv) -> int`; CLI `python -m fusionhelper.telemetry record|summary`; JSONL at `%FH_TELEMETRY%` or `<default_home()>/telemetry.jsonl`. Task 5's SKILL.md step cites the `record` command verbatim.

- [ ] **Step 1: Write failing tests**

`tests/test_telemetry.py`:
```python
import json

from fusionhelper import telemetry


def test_record_appends_one_json_line(tmp_path):
    path = tmp_path / "t.jsonl"
    out = telemetry.record_entry(script="box.py", verdict="pass", executes=1,
                                 preflight_attempts=2, rules_fired=["R2", "R4"],
                                 notes="", path=path)
    assert out == path
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["script"] == "box.py"
    assert entry["verdict"] == "pass"
    assert entry["executes"] == 1
    assert entry["preflight_attempts"] == 2
    assert entry["rules_fired"] == ["R2", "R4"]
    assert entry["ts"].endswith("+00:00") or entry["ts"].endswith("Z")


def test_env_var_overrides_default_path(tmp_path, monkeypatch):
    target = tmp_path / "override.jsonl"
    monkeypatch.setenv("FH_TELEMETRY", str(target))
    telemetry.record_entry(script="a.py", verdict="fail", executes=3)
    assert target.is_file()


def test_summarize_math(tmp_path):
    path = tmp_path / "t.jsonl"
    telemetry.record_entry(script="a.py", verdict="pass", executes=1,
                           rules_fired=["R4"], path=path)
    telemetry.record_entry(script="b.py", verdict="pass", executes=3,
                           rules_fired=["R4", "R2"], path=path)
    telemetry.record_entry(script="c.py", verdict="abandoned", executes=5, path=path)
    s = telemetry.summarize(path)
    assert s["sessions"] == 3
    assert s["first_execute_green"] == 1
    assert s["mean_executes"] == 3.0
    assert s["rule_counts"] == {"R4": 2, "R2": 1}


def test_cli_record_then_summary(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("FH_TELEMETRY", str(tmp_path / "t.jsonl"))
    rc = telemetry.main(["record", "--script", "box.py", "--verdict", "pass",
                         "--executes", "1", "--preflight-attempts", "0",
                         "--rules-fired", "R2,R4"])
    assert rc == 0
    rc = telemetry.main(["summary"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "sessions: 1" in out
    assert "first-execute green: 1/1" in out


def test_cli_summary_with_no_file_reports_zero_sessions(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("FH_TELEMETRY", str(tmp_path / "missing.jsonl"))
    assert telemetry.main(["summary"]) == 0
    assert "sessions: 0" in capsys.readouterr().out
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/test_telemetry.py -q`
Expected: FAIL with `ImportError` (`telemetry` missing).

- [ ] **Step 3: Implement**

`fusionhelper/telemetry.py`:
```python
"""Session telemetry: one JSONL line per part-request, so the skill's effect
is a number, not folklore. The metric the external review asked for —
green-verdict-on-first-execute — is `summary`'s first line. Location:
FH_TELEMETRY env var, else <FUSIONHELPER_HOME>/telemetry.jsonl (same home
the verify block installs to)."""
import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from fusionhelper import verify

ENV_VAR = "FH_TELEMETRY"
VERDICTS = ("pass", "fail", "abandoned")


def default_path() -> Path:
    env = os.environ.get(ENV_VAR)
    if env:
        return Path(env)
    return verify.default_home() / "telemetry.jsonl"


def record_entry(*, script: str, verdict: str, executes: int,
                 preflight_attempts: int = 0, rules_fired: list[str] | None = None,
                 notes: str = "", ts: str | None = None,
                 path: Path | None = None) -> Path:
    if verdict not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}, got {verdict!r}")
    target = path if path is not None else default_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": ts if ts is not None else datetime.now(UTC).isoformat(),
        "script": script,
        "verdict": verdict,
        "executes": executes,
        "preflight_attempts": preflight_attempts,
        "rules_fired": rules_fired or [],
        "notes": notes,
    }
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")
    return target


def summarize(path: Path | None = None) -> dict:
    target = path if path is not None else default_path()
    entries = []
    if target.is_file():
        for line in target.read_text(encoding="utf-8").splitlines():
            if line.strip():
                entries.append(json.loads(line))
    sessions = len(entries)
    green = sum(1 for e in entries
                if e.get("verdict") == "pass" and e.get("executes") == 1)
    mean = (sum(e.get("executes", 0) for e in entries) / sessions) if sessions else 0.0
    rule_counts: dict[str, int] = {}
    for e in entries:
        for r in e.get("rules_fired", []):
            rule_counts[r] = rule_counts.get(r, 0) + 1
    return {"sessions": sessions, "first_execute_green": green,
            "mean_executes": mean, "rule_counts": rule_counts}


def _render_summary(s: dict) -> str:
    rate = f"{s['first_execute_green']}/{s['sessions']}"
    pct = (100.0 * s["first_execute_green"] / s["sessions"]) if s["sessions"] else 0.0
    rules = " ".join(f"{k}={v}" for k, v in
                     sorted(s["rule_counts"].items(), key=lambda kv: -kv[1]))
    return "\n".join([
        f"sessions: {s['sessions']}",
        f"first-execute green: {rate} ({pct:.0f}%)",
        f"mean executes: {s['mean_executes']:.1f}",
        f"rules fired: {rules or '(none)'}",
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m fusionhelper.telemetry")
    sub = parser.add_subparsers(dest="cmd", required=True)
    rec = sub.add_parser("record", help="append one session entry")
    rec.add_argument("--script", required=True)
    rec.add_argument("--verdict", required=True, choices=VERDICTS)
    rec.add_argument("--executes", required=True, type=int)
    rec.add_argument("--preflight-attempts", type=int, default=0)
    rec.add_argument("--rules-fired", default="",
                     help="comma-separated rule numbers that fired during preflight")
    rec.add_argument("--notes", default="")
    sub.add_parser("summary", help="print aggregate metrics")
    args = parser.parse_args(argv)
    try:
        if args.cmd == "record":
            rules = [r for r in args.rules_fired.split(",") if r]
            out = record_entry(script=args.script, verdict=args.verdict,
                               executes=args.executes,
                               preflight_attempts=args.preflight_attempts,
                               rules_fired=rules, notes=args.notes)
            print(out)
        else:
            print(_render_summary(summarize()))
    except OSError as e:
        print(f"TELEMETRY FAILED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_telemetry.py -q` — Expected: PASS.

- [ ] **Step 5: Full suite + lint + commit**

`python -m pytest -q`; `python -m ruff check .`
Stage exactly: `fusionhelper/telemetry.py tests/test_telemetry.py`

---

### Task 5: SKILL.md split + hazards reference + doc-test upgrade

**Confidence:** 90%

**Files:**
- Modify: `skills/fusion-design/SKILL.md`
- Create: `skills/fusion-design/reference/hazards.md`
- Modify: `tests/test_skill_doc.py`

**Interfaces:**
- Consumes: Task 4's CLI (`python -m fusionhelper.telemetry record ...` cited verbatim); Tasks 1-2's rule status (waiver paragraph rewrite).

The split criterion: **rules that change what you GENERATE stay in SKILL.md (compressed); diagnosis/recovery/heavy-document-operations lore MOVES to `reference/hazards.md`**, loaded by symptom.

- [ ] **Step 1: Update `tests/test_skill_doc.py` first (failing)**

Apply these edits:
```python
def test_skill_cites_the_real_cli_and_reference_files():
    text = SKILL.read_text(encoding="utf-8")
    assert "python -m fusionhelper.preflight" in text
    assert "python -m fusionhelper.telemetry record" in text
    for ref in ("api-recipes.md", "axis-mapping.md", "limits.md", "hazards.md"):
        assert ref in text
        assert (SKILL.parent / "reference" / ref).is_file()


def test_skill_stays_resident_sized():
    # The external review's finding: appended lab-notebook sections were
    # diluting the ten rules. Hazard lore lives in reference/hazards.md.
    text = SKILL.read_text(encoding="utf-8")
    assert len(text.splitlines()) <= 240, "SKILL.md is regrowing — move lore to reference/"


def test_waiver_scope_names_the_checked_rules():
    text = SKILL.read_text(encoding="utf-8")
    assert "R1 R2 R4 R5 R6 R7 R9 R10 R11" in text  # waivable checked rules
```
Keep the four existing tests unchanged. Run `python -m pytest tests/test_skill_doc.py -q` — Expected: FAIL (hazards.md missing, telemetry line missing, size over).

- [ ] **Step 2: Create `reference/hazards.md`** — move these SKILL.md sections verbatim (headings preserved, one intro line at top: "Symptom-triggered lore. Read the section your symptom names; do not carry the whole file."):

Move map (line numbers = current SKILL.md):
- Lines 156-179 — whole "Working in an existing document" section (prior-failure verdicts, FH_CHECK1 separation, timeline hazards, `healthState 4`, `moveToEnd`, `markerPosition`, `rollTo` replace-in-place, recovery semantics, atomic rollback, undo, no-stub probes).
- Lines 185-201 — whole "Checkpoint versioning (the reset story)" section.
- From "Heavy documents and transport discipline": the dead-client bullet (205-212), orphaned-requests bullet (213-217), instanced-component-count bullet (223-228), the liveness-budget tail of the R11 bullet (the sentence starting "Liveness on instanced-heavy documents remains budget-limited" through "say so in the report", 248-252), light-bulbs bullet (253-255).
- From "Editing a committed model": the `param.dead` diagnosis bullet (277-279).

- [ ] **Step 3: Rewrite SKILL.md**

Keep: frontmatter, intro, the ten rules (R1-R10 unchanged), Workflow, Buildkit workflow, repair budgets, Honest limits — all verbatim except the edits below.

(a) Replace the waiver paragraph (lines 181-183) with:
```
Waivers (`# fusionhelper: allow ...`) apply to the checked rules
(R1 R2 R4 R5 R6 R7 R9 R10 R11). R3 is a runtime rule — nothing fires, so
waiving it reports "unused suppression". R8 is not waivable by design.
Checkpoint saves are the sanctioned R10 waiver: state the user's consent in
the reason.
```

(b) Add workflow step 10 after step 9:
```
10. **Record telemetry** (final act, pass or give-up):
    `python -m fusionhelper.telemetry record --script <file> --verdict pass|fail|abandoned --executes <n> --preflight-attempts <n> --rules-fired R2,R4`
    — one line per part request. `python -m fusionhelper.telemetry summary`
    prints the green-on-first-execute rate this skill is judged by.
```

(c) Replace the moved sections with a compact trigger table:
```
## When something is off, read the hazard file

Symptom-triggered lore lives in `reference/hazards.md` — read the section
your symptom names, not the whole file:
- pre-existing document (constraints fail you didn't cause, prior_failure,
  someone else's timeline, healthState 4) → "Working in an existing document"
- teardown / rebuild / duplicate " (N)" bodies → "Checkpoint versioning"
- client timeout, orphaned request, busy-vs-frozen, instanced-heavy cost,
  geometry gone dark (light bulbs) → "Heavy documents"
- `param.dead` on a parameter you believe is live → "Editing a committed model"
```

(d) Compress the surviving generation-time bullets, keeping every rule and measured number, dropping narrative: namespace reuse / FH_ATTEMPT globals; feature-add-can-error-in-timeline + fillet shortest-edge bound; delete params with features; embed-depth-from-thinnest-layer; patch-gate-launch three commands + captured-text patching; measured-signatures-not-renders; overlay overlap check; never gate through a pipe; jittered circles; pattern validation (AdjustPatternCompute, face-count delta, flipped distances); chunked executes + R11 doEvents batching (~20-op executes; doEvents every ~20 entities on dense sketch loops); abs() for possibly-negative dimension expressions (kit v2 handles `bound_rect2`); preserve the sign rewriting committed extents; derive clearance stacks / pin the far face; overshoot cut profiles past parametric surfaces; volume-delta check on every feature; `isFixed` doesn't fix points; collect bodies into a list before `moveToComponent`; overhang audit via `getNormalsAtParameters` (`normal.z < -0.7075`).

Target: SKILL.md ≤ 240 lines total.

- [ ] **Step 4: Run doc tests**

Run: `python -m pytest tests/test_skill_doc.py -q` — Expected: PASS.

- [ ] **Step 5: Full suite + lint + commit**

`python -m pytest -q`; `python -m ruff check .`
Stage exactly: `skills/fusion-design/SKILL.md skills/fusion-design/reference/hazards.md tests/test_skill_doc.py`

---

### Task 6: Docs sweep for stale enforcement claims

**Confidence:** 92%

**Files:**
- Modify: `docs/detailed-design.md` (and any other CURRENT-state doc the grep finds; dated probe/plan/spec history files stay untouched)

- [ ] **Step 1: Find stale claims**

Run: `grep -rn "R9\|R10\|honour\|unenforced\|not checked" docs/ README.md 2>$null` (PowerShell: `Get-ChildItem docs -Recurse -Include *.md | Select-String -Pattern "R9|R10|honour|unenforced|not checked"`).

- [ ] **Step 2: Update current-state docs only**

In `docs/detailed-design.md` (a living architecture doc): any sentence claiming R9/R10 are unchecked/honour-system/convention-only now reads that they are lint-enforced (R9 with stub/kit region exemptions via `lint/regions.py`; R10 waivable for consented checkpoints), and R3 is the only unchecked rule. Do NOT edit `docs/probe-results.md`, `docs/superpowers/specs/*`, or `docs/superpowers/plans/*` — dated records.

- [ ] **Step 3: Verify tokens against source, run gates, commit**

Every rewritten sentence's factual tokens (module names, rule ids, flag names) verified against the code. `python -m pytest -q`; `python -m ruff check .`
Stage exactly the edited doc files.

---

## Self-Review (done at plan time)

1. **Spec coverage:** R10 rule → Task 1. R9 + region scoping → Task 2. R4 alias FN → Task 3. Telemetry → Task 4. SKILL.md split → Task 5. Docs honesty (the "loudest inconsistency" claim) → Tasks 1-2 flip + Task 6 sweep. Declaration-block/oracle redesign was assessed as partial and is deliberately OUT of scope (not on the approved list).
2. **Placeholder scan:** all code steps carry full code; fixture files complete; no TBDs.
3. **Type consistency:** `exempt_lines(source: str) -> set[int]` consumed identically in Task 2 Steps 2/4/8; `record_entry` kwargs in Task 4 Steps 1/3 match; `MARK_BEGIN_PREFIX` produced in Step 1, consumed in Step 4; rule module shape (`RULE_ID`/`NUMBER`/`RESTATEMENT`/`check`) matches `ALL_RULES` iteration and `render.py` expectations.
