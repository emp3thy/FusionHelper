# FusionHelper — Detailed Design

Reconciled output of a six-agent design pass, one agent per component, all working from the
committed evidence base. Interfaces between components were cross-checked against actual code,
not assumed, and several claims were verified against a live Fusion install during the pass.

Read [`README.md`](README.md) first for orientation, and
[`superpowers/specs/2026-07-27-fusionhelper-design.md`](superpowers/specs/2026-07-27-fusionhelper-design.md)
for the design rationale. This document is the implementation-level detail.

**Companion artefacts on disk:**

| Path | What |
|---|---|
| `skills/fusion-design/reference/` | The skill's reference bundle — 740 lines, written |
| `fusionhelper/verify/fh_verify.py` | The verification block — 995 lines, written |
| `tests/test_verify_offline.py` | 43 offline assertions, passing without Fusion |

---

## 1. What is built

**A Claude Code skill and a Python library. Not an MCP server** — Autodesk ships one, it is
built into Fusion, and it already works.

```
FusionHelper/
├── skills/fusion-design/
│   ├── SKILL.md                     the procedure, always resident
│   └── reference/                   loaded on demand, zero cost until read
├── fusionhelper/
│   ├── preflight/                   the offline gate
│   ├── lint/                        the discipline rules
│   ├── verify.py                    the assertion block generator
│   ├── declare/                     the declaration block
│   ├── emit.py                      code generators (phase 3)
│   ├── stubs.py                     stub discovery, API version, fingerprint
│   └── install.py                   skill installer
└── tests/                           three tiers; only one needs Fusion
```

Flow, with ownership marked:

```
description
  → declaration block  (Claude writes, declare validates)      OURS
  → dimensional chain check, before any geometry               OURS
  → generated Fusion Python                                    OURS
  → preflight: pyright + lint,  ~2 s, offline                  OURS
  → fusion_mcp_execute                                         AUTODESK
  → verification block prints a JSON verdict                   OURS
  → repair loop, or renders for the human                      OURS
```

---

## 2. Component: the `fusion-design` skill

### The ten standing rules

Numbered because the gate cites them by number — see §3.

| # | Rule | Enforced by |
|---|---|---|
| R1 | Never `ValueInput.createByReal` — use `createByString`, always | gate |
| R2 | Every `sketchDimensions.add*` followed by `.parameter.expression = '<param>'` | gate |
| R3 | Constrain → check `isFullyConstrained` → dimension only the residual | **runtime** |
| R4 | Never select topology by index — geometric predicate or `entityToken` | gate |
| R5 | Never use a BRep reference across a parameter change | gate (parameter trigger only) |
| R6 | Derive axis mapping from `sketchToModelSpace()` at runtime | gate |
| R7 | Parameter names are multi-character `snake_case` | gate |
| R8 | The verification stub is present and its rebinding is last in the file | gate |
| R9 | Never catch exceptions in generated scripts | convention |
| R10 | Never save the document | convention |

### Progressive disclosure — and why the split is not just about tokens

Only two categories belong in the always-loaded body: things that must hold at *every* token and
cannot be looked up because you do not know you need them (the rules), and the workflow sequence,
because you cannot look up a step you have forgotten exists. Everything else is reference.

Two arguments beyond cost, and they are the stronger ones:

1. **Freshness beats residency for lookup content.** A recipe read at the moment of use enters
   context ~200 tokens before it is applied. The same recipe carried from turn 1 is competing
   with tens of thousands of tokens of newer chatter by the time it matters. Residency helps
   rules; freshness helps recipes.
2. **Inlining the axis table would defeat R6.** R6 says derive the mapping at runtime. If the
   measured XY/XZ/YZ table sits in the body, it will be used — it is right there and it is
   correct on this machine. Behind `reference/axis-mapping.md`, labelled *for diagnosing an
   inversion, never for computing a placement*, the compliant path becomes the available one.
   This is the project's own make-it-inexpressible principle applied to skill authoring.

Budget: body ~3.6k tokens once per session; references ~1.5–2k each, typically one or two read
per part. Inlining everything would cost ~11k up front.

### Anti-drift

Skill discipline is advisory and decays as context fills. The measures, in order of expected
value:

1. **Push the rules into the gate's output.** The strongest lever, and it is a requirement on
   preflight rather than on the skill file: every finding cites its rule number and restates the
   rule in one line. Rules then re-enter context *at the moment of violation*, as recent tool
   output — not as a turn-1 message competing with 40k tokens of newer text. This is why the
   rules are numbered at all.
2. Rules stated as forbidden **token sequences**, not concepts. "Never `createByReal`" is
   checkable mid-generation; "prefer parametric expressions" is not.
3. The correct form sits adjacent to every forbidden form, so compliance never requires
   recalling a second fact.
4. A copy-in workflow checklist, re-copied per part, which re-emits the procedure into Claude's
   own most recent tokens.
5. Artefacts on disk, not in memory — the declaration, the script and the verdict are all files.
   State is re-read, never recalled.
6. No optional paths. One way to do each thing; options are where discipline leaks.

**Honest limit:** none of this is enforcement. The escalation — a wrapper refusing
`fusion_mcp_execute` without a passing pre-flight — remains the only structural fix, and measure 1
is its closest advisory approximation. If phase-1 telemetry shows steps being skipped, that is
the v2 trigger and it should be built before anything is added to the skill.

---

## 3. Component: `preflight` + `lint`

### The gate fails open — the defining constraint

**A malformed `pyrightconfig.json` does not stop pyright.** It prints one line to stderr, falls
back to defaults, and exits *normally* — losing `extraPaths` and weakening
`reportAttributeAccessIssue`. Measured: 3 errors instead of 7, with all seven genuine
hallucinations undetected, while looking like a clean run. Found independently by two agents.

Three mandatory consequences:

1. The config is **generated programmatically** with `json.dump`. Never templated, never
   hand-maintained.
2. Every invocation runs a **canary** — a known-bad probe it asserts pyright flagged — proving
   config parse, stub resolution and rule severity together. A `PASS` is only meaningful if a
   known-bad probe simultaneously `FAIL`s.
3. **Three outcomes: `PASS` / `FAIL` / `GATE_BROKEN`.** `GATE_BROKEN` is never reported as a pass.

Plus a **stub sentinel**: any `Import "adsk.* could not be resolved"` means the stub path did not
take effect. Report an *environment* error and suppress all other diagnostics — they are noise
from an unresolved import and will send a repair loop chasing phantoms.

### Exit codes

| Code | Meaning | What the reader does |
|---|---|---|
| 0 | PASS | Send the script to Fusion |
| 1 | FAIL — script defect | Fix the script |
| 2 | Usage error | Fix the command |
| 3 | **Environment error** | Fix the machine. **Do not edit the script.** |

The 1/3 split exists for a specific failure: without it, a missing-stubs run reports
`Import "adsk.core" could not be resolved` and a repair loop spends attempts "fixing" a perfectly
good import.

### Rules — mechanism and false-positive control

All rules are `ast.NodeVisitor` passes over **one** shared parse. Parsing costs ~1 ms and is
amortised, so a single `ast.parse` is cheaper than five regex sweeps.

**R1 `no-create-by-real`** — matches any `Attribute` with `attr == "createByReal"`, deliberately
receiver-blind (there is no other `createByReal` in the API, so the receiver carries no
information and checking it only creates escapes). A `tokenize`-based text backstop catches
`getattr` forms at WARN.

**R2 `dimension-must-bind`** — genuine dataflow, prototyped and verified. Three sets in one pass:
*creations* (`x = <...>.sketchDimensions.add*(...)`), *bound* (`x.parameter.expression = ...`),
*escaped* (passed to any call — conservative, so helper functions are never false-flagged), plus
*discarded* (a bare `add*` expression statement, which can never be bound and is the
highest-confidence finding the rule produces). Violations = creations − bound − escaped.

**R4 `no-index-topology`** — the rule with the real false-positive problem, because iterating all
faces to apply a geometric predicate is the *recommended* pattern and flagging it would invert
the rule's meaning. A `RangeIterationTracker` exempts `for i in range(<same receiver>.count)`,
matching on the receiver chain textually. Direct iteration (`for f in body.faces:`) produces no
subscript and is never visited. Verified zero false positives on a mixed fixture.

Collections: `{faces, edges, vertices, bRepBodies, shells, lumps}` — **not** `bodies` (Fusion's
collection is `bRepBodies`; leaving `bodies` in caused a live false positive on a local variable
matching by name alone), and matching **requires a dotted chain** so a bare `faces` does not
match. `sketch.profiles.item(0)` is deliberately excluded — it is the universal idiom with no
durable alternative in the API. Flagged as an open question.

**R5 `no-stale-brep`** — parameter-change trigger only. Triggers on an `Assign` whose target is an
`Attribute` with `attr in {expression, value}`, *excluding* a receiver named `parameter` (which is
R2's mandated binding). Testing the immediate receiver rather than the full dotted chain is both
simpler and strictly more robust — it catches
`des.userParameters.itemByName('w').expression = ...`, which a chain-based test misses because
`attr_chain` bails on a call mid-chain.

**R6 `no-hardcoded-axis`** — ERROR on an all-literal `Vector3D.create`; WARN when a script
references `xZConstructionPlane`/`yZConstructionPlane` and never calls `sketchToModelSpace`.
Critically must **not** match `Point3D.create(0, 0, 0)`: identical shape, opposite meaning.
Literal seed *coordinates* are the endorsed pattern, because the solver snaps them to exact.

**R7 `param-name-safe`** — ERROR for names Fusion rejects (unit symbols, function names,
malformed, **duplicates** — all with the same misleading message); WARN for non-`snake_case`. The
split matters: an ERROR must always mean "this will throw at runtime". And it makes the
incomplete rejected-set tolerable — a script with zero WARNs provably cannot trip the ERROR set,
which is a stronger guarantee than enumerating Fusion's reserved words.

**R8 `verify-stub-intact`** — one invariant: **the file ends with the stub, unmodified.** A
normalised suffix comparison against `fusionhelper.verify.STUB_TEXT` gives the verdict; the AST
and a sentinel comment are used only to diagnose *which* failure it is, so the message stays
actionable rather than a bare "stub check failed".

```python
ok = _norm(source).endswith(_norm(verify.STUB_TEXT))
```

Normalisation absorbs CRLF, trailing blank lines and trailing whitespace — the things an editor
or generator varies without meaning to. CRLF is not incidental: the script is written on Windows
and a naive comparison would fail on every real file.

This deliberately makes the check **indifferent to the stub's syntactic shape**, so it passes both
`def run(_context):` and `run = _fh_wrap(run)`. The alternative — matching an AST pattern — would
have coupled the lint rule to a choice that belongs to whoever owns the stub.

Why the rule earns its place, which is not obvious from the check's shape. Ordering failures split
cleanly:

- Stub placed *before* the user's `def run` → `_fh_user_run = run` runs before `run` exists →
  `NameError` at module load. **Loud**, and the repair loop handles it.
- A `def run` appended *after* the stub → the later definition wins, the wrapper is discarded, the
  script builds geometry and prints nothing. **Silent**, and it looks exactly like a script whose
  verification passed quietly.

Only the second needs a gate — and it is this component's own failure mode appearing in its own
scaffolding: a preflight PASS asserting "this model was verified" when nothing verified it.

If the stub is ever to be hand-editable, R8 degrades cleanly to a position check (the last
top-level statement's `lineno` at or after the sentinel), keeping the silent case and giving up
only modification detection.

### Suppression

`# fusionhelper: allow <rule-id-or-number> — <reason>`, line-scoped only. No file-level pragma
and no `--ignore` flag: a file-level waiver is one edit that silently disables a rule for a
400-line script. A reason under 12 characters is itself an error. Unknown rule id is an error;
unused suppression is a warning. **Waivers print on every run including PASS** — a waiver nobody
sees is the same as no rule.

### Fixed, not configurable

No config file, no severity overrides. The first use of a config file is switching off the rule
that is complaining, and these rules exist precisely because Fusion is silent about these
failures. A fixed set also makes exit 0 mean the same thing on every machine. The pressure valve
already exists and is strictly better: a per-line suppression lives in the script the user reads,
names the rule, and explains itself.

If a rule proves noisy, the correct response is to **tighten it**, not to make it mutable.

### Output

Verdict on line 1 in a fixed grammar. Every finding carries `path:line:col`, a source excerpt with
a caret, and a `fix:` containing **code, not advice**. Grouped by rule with the restatement first
and the remediation stated once. Deterministic ordering so two runs are diffable.

Every run, including green ones, ends with the coverage line:

```
checked: R1 R2 R4 R5 R6 R7 R8 · not checked: R3 · R5 covers parameter-change only
```

This closes a hole that follows from the anti-drift design itself: if rules re-enter context by
firing, a rule the gate never checks never re-enters at all. The line states the boundary rather
than letting a green gate imply full compliance.

**Hard invariant:** the renderer derives the verdict, every count and the coverage line from the
findings list *at render time*, never from a counter maintained alongside. A `PASS` header above a
list of errors would destroy the gate's credibility in one sighting.

### Performance

**~2 s, not 0.3 s.** Measured 1.6–2.2 s wall; the 0.3 s figure was pyright's self-reported
analysis time and excludes node startup. Lint is ~5 ms, i.e. 0.3% of the total.

What blows it: `"include": ["."]` (4 files / 1168 diagnostics instead of 1 / 7 — the script must
be staged into an isolated temp dir, which also escapes ancestor pyright config); re-running
`pyright --version` per check (~900 ms — cache it); invoking `dist/pyright.js` with node directly
to "skip the wrapper" (measured *slower* and functionally broken).

---

## 4. Component: `verify` + the repair loop

### The block is exec'd from disk, not inlined

`fusion_mcp_execute`'s `object.script` is a **string** — there is no file-path form. An inlined
995-line block would therefore cross Claude's context on **every repair attempt**: ~9,000 tokens
each, against ~330 for the verdict itself. A 16-line stub costs ~230.

Three further benefits: the logic is versioned in the package rather than retyped each run, so it
cannot be paraphrased or truncated; a fix reaches already-generated scripts; and the block is
unit-testable offline — which is how two defects were caught during authoring.

The stub **wraps `run` by rebinding**, so it is purely appended text. Build exceptions are never
caught — only the verification code is guarded. The `exec` is lazy, inside the wrapper, after the
build, so a missing block does not destroy a successful build. `exec` rather than `import`,
because Fusion caches modules across script runs and an `import` would serve a stale block.

**The stub must `exec` into an explicit dict, never `globals()`.** Verified: the `globals()` form
produces `reportUndefinedVariable` on **100% of generated scripts**. The alternative fix —
suppressing `reportUndefinedVariable` — was rejected, because it catches genuine typos in
generated code.

### The five checks

Cheap checks first (no rebuilds), then liveness. **If a cheap check errors, liveness is skipped**
with `reason: prior_failure` — the model is already known wrong, and spending N rebuilds proving
it is also dead buys nothing. This is the largest cost saving in the design.

1. **Constraint state** — per-sketch `isFullyConstrained`; on failure, per-entity
   `SketchEntity.isFullyConstrained` to *name* the loose entities. Severity is split: zero
   constraints **and** zero dimensions is an error (the P5 raw-coordinate signature); otherwise a
   warning, because P1 showed a model rebuilding correctly while under-constrained. A bonus check
   tokenises every dimension expression against the live parameter set — the static half of the
   partially-bound trap, at zero rebuild cost.
2. **Parameter liveness** — the only check that catches a partially-bound dead timeline. Detail
   below.
3. **Timeline health** — reports only non-healthy objects, with messages matched against a
   nine-entry regex table to attach a taxonomy code.
4. **Interference** — `areCoincidentFacesIncluded = False`; guarded for <2 bodies (which raises)
   and skipped above 60 bodies (the analysis is O(N²) inside Fusion).
5. **Clearance** — declared roles resolved via an `entityToken` registry, below.

### Liveness, in detail

**Perturb by expression rewrite, not by value**: `p.expression = '(outer_w / 20) + 0.2 mm'`. A
value write would flatten a derived parameter into a literal and the restore would be lossy. Step
is 5% of value, floored at 0.2 mm / 1° and capped at 10 mm / 5° — the floor clears solver noise on
a 0.4 mm wall, the cap stops a large parameter developing reference failures that are an artefact
of the test.

**Change detection** is per-body face count, volume, area and bounding box, compared with
`abs > 1e-7` **and** `rel > 1e-9`. A dead parameter reproduces byte-identical metrics; a live one
moves by percent-scale. The margin is about six orders of magnitude, so the tolerance is not
delicate.

**Three outcomes, not two:** `dead` (error), `fragile` (warn — a 5% nudge already breaks a
feature; live, but real signal a pass/fail would discard), `perturbation_rejected` (warn — locked
or invalid; reporting it as dead would be wrong).

**Restoration is guaranteed at three levels:** a per-perturbation `finally`; a `_restore_all`
re-assertion reporting any parameter that would not take; and a final re-snapshot against the
pre-verification baseline, emitting `model.not_restored` on mismatch. **The verdict always states
whether the document was left as it was found** — Claude never has to assume.

**Cost: 2N rebuilds and N+1 settles.** Interleaving restore-then-perturb is *safe* — measured —
but it is not cheaper in rebuilds. The rebuild is **eager, on the write itself**: a bare
`p.expression = ...` with no settle and no read costs ~76 ms on a 6-parameter model, while the
subsequent read costs 0.7 ms. Since restore-then-perturb is two writes either way, grouping them
under one `doEvents()` cannot remove a rebuild. Measured wall clock: isolated 1507 ms, interleaved
1263 ms — a ratio of 1.19, which is the `doEvents()` overhead alone.

Take the interleaving for the ~19%, but the sweep does not halve. An earlier draft of this
document claimed "N+1 rebuilds, not 2N" by conflating *safe to interleave* with *cheaper to
interleave*; the test that appeared to show coalescing read a value immediately after a write,
which a lazy-on-read implementation would also produce, so it could not separate the hypotheses.

**The edit canary** (2 rebuilds, default on): perturb every *root* parameter simultaneously, then
re-run interference. This reproduces P5's flagship failure directly — geometry pinned to literal
coordinates does not follow when the parts around it grow. It also gives a fast exit: if nothing
moves when every root moves, emit `model.inert` and stop.

### The verdict

One line, compact JSON, sentinel-prefixed `FH_VERDICT1 `. **In millimetres**, converted at the
boundary, with `"units": "mm"` stated — Claude must never do a unit conversion in its head to
compare a verdict against a declaration.

- **Pass carries no detail** — a check roll-up plus four numbers (bodies, volume, bbox, origin) as
  the cheapest possible cross-check against declared dimensions. ~83 tokens.
- **A four-failure verdict is ~330 tokens** and is diagnosable without a follow-up read.
- **`skip` is never `pass`** — any skipped check caps the status at `pass_partial`.
- **Findings capped** at 5 per check, 12 overall. Twelve simultaneous failures means the approach
  is wrong, not that twelve things need fixing.
- Remediation text is **not** in the verdict by default — the taxonomy lives in the skill body,
  already resident at zero marginal cost. `hints` appear only on errors, capped at four.

Localisation is designed per code: `interference.clash` carries the overlap **bounding box**
(`size_mm:[5.5,5.5,1.5]` at `at_mm:[30,20,23.2]` says a boss is 1.5 mm too tall, which the volume
alone does not); `clearance.violated` carries `short_by_mm`, the number that goes straight into a
parameter edit; loose sketch entities carry geometry, not just an index, so Claude can match the
entity to the line that created it.

### Repair loop

| Failure class | Budget |
|---|---|
| Preflight (offline) | 3, separate budget |
| Runtime, mechanical taxonomy code | 3 |
| Runtime, unclassified | 2 |
| Verification failure | 2 |
| **Hard cap, all classes** | **5 `fusion_mcp_execute` calls per request** |

Five is the empirical ceiling: `claude trophy v5` took five attempts with *no structured signal
at all*. With a named failure the first repair should usually work.

**Non-convergence, four rules:** identical failure signature twice → abort immediately;
non-consecutive recurrence (A→B→A) → abort, the two fixes undo each other and the model is
over-determined; error count failing to strictly decrease for two attempts → abort; a repair
introducing a new error code without clearing the old one counts as no progress.

**Forward fix** for local, additive failures where the structure is right. **Undo and regenerate**
when `model.not_restored` (mandatory and immediate), `model.inert` or `edit.introduces_clash`
(the *placement mechanism* is wrong, and a forward fix can only pile features onto
coordinate-placed geometry), or a timeline feature is in error state. **The third attempt is
always a from-scratch regeneration, never a patch** — by then the patch hypothesis has failed
twice.

Undo is one committed transaction per call, so rollback is driven by timeline depth: each verdict
carries `stats.timeline`, and the previous attempt's value is the target. Issue undos without
probing between them, then confirm once with a 3-line state probe.

**When the loop gives up** it reports six things in order: what is wrong in plain language using
the localisation fields; the implicated declaration excerpt; one line per attempt; the document
state explicitly; **a specific question, not a report of failure**; and a render — this is
precisely when the screenshot earns its cost, because what remains is "is this the object you
wanted", which assertions structurally cannot answer.

---

## 5. Component: the declaration block

CRANE-shaped: Claude reasons in prose, then emits one fenced YAML block whose first line is the
comment `# fusion-decl v1`. Written to `<name>.decl.yaml` — the emission *is* the `Write` call, so
one action satisfies both the transcript and the file, avoiding the two-copies drift failure.

Sections: `meta`, `defaults`, `parameters`, `datums`, `bodies`, `chains`, `clearances`. **Unknown
keys are errors, not ignored** — a silently dropped typo'd section is a silent failure.

### The expression evaluator

Hand-written tokenizer and recursive-descent parser over a narrow subset. No `eval`. Canonical
length unit is **cm** (matching the API), with exact `Fraction` conversions, so compiled numbers
hand straight to `measureMinimumDistance` comparisons.

`Quantity` carries value, dimension and an `exact` flag; irrational operations taint it.
Dimension rules are enforced per operator and per function. **A bare numeric literal is
dimensionless everywhere**, so `outer_w: 80` is rejected with "add a unit" — deliberate friction
at exactly the point every Fusion MCP project independently names as its top error source.

Parameters are emitted in **topological order**, which is a real deliverable: Fusion requires a
referenced parameter to exist first, and hand-ordering is exactly the bookkeeping that drifts.
Cycles report the actual path.

### The dimensional chain check

The cheapest verification in the system — pure arithmetic, no geometry, sub-millisecond, and it
runs *before any sketch exists*.

`Fraction` arithmetic matters here: `wall_t = outer_w / 20` with `outer_w = 80 mm` is exactly
4 mm, and `4 + 72 + 4 == 80` is an exact identity. With floats, a chain built from thirds would
fail on the last bit and need an arbitrary epsilon — which then hides real 0.001 mm errors.
`Fraction` removes the tolerance judgement entirely for the common case, and `exact=False` marks
precisely the cases where a tolerance is genuinely needed.

Relations are `eq` (default), `gte`, `lte`, because real chains are often inequalities. The
failure report names the residual with its sign and exactness, then lists **which parameter to
change and to what** — following a derived parameter back to the root it would have to move.

### Face naming — the open question, resolved

> **A face is nameable if and only if it is coplanar with a declared datum, or is a cylinder about
> a named axis at a declared radius.**

Tokens cannot appear in the declaration because it precedes geometry. Index picks are forbidden.
So the declaration carries a *predicate* — and rather than build a heuristic resolving arbitrary
face descriptions, the unnameable face is made **inexpressible**. If you want to constrain a boss
top, declare a datum at the boss top — which layout-before-detail already required.

`expect` is **required** on every selector. Four identical bosses genuinely cannot be told apart
by any stable predicate, and they should not be: the useful statement is about the *set*. So a
selector legitimately yields a set, `expect: 4` asserts the cardinality, and ambiguity becomes a
declared, checked fact rather than a silent hazard.

**No escape hatch.** No `extreme: max_z`, no `area:` predicate. A weak selector gets used, and its
failure mode is silent — it resolves to *a* face, just the wrong one.

### Validation order

Extract → parse (with a duplicate-key-raising loader) → names → syntax → references and cycles →
dimensions → values → chains → compile. Cheapest and most informative first; **each stage runs to
completion and reports every finding at that stage** before stopping. Reporting one error per
round trip is the main avoidable cost in an agent loop.

The duplicate-key loader deserves specific mention: YAML's default is to silently take the last
value, which would launder a genuine duplicate into a wrong-but-quiet declaration — and Fusion
reports duplicate parameter names with the *same* misleading message it uses for unit symbols and
function names.

---

## 6. Component: `emit`

### The selection principle

> **A helper must add an executable guarantee, not a shorter spelling.**

An executable guarantee is exactly one of: asserting a postcondition the API does not; making an
omission impossible by construction; or computing at runtime what would otherwise be a hardcoded
literal. Plus four conditions, all of which must hold: multi-step with a mandatory order; silent
on omission; empirically derived (if the docs get it right, it is a SKILL.md rule, not a library);
and **not the load-bearing design intent** — if the emitted code is what the user will want to
edit, it stays visible. A helper may *write* it; it may not *hide* it.

That last condition does the most rejecting, and it is what keeps the output handoverable.

### Code generation, not a runtime library

Measured: Fusion embeds its own CPython 3.14 (`sys.executable` is `Fusion360.exe`) and no user
site-packages is importable. `%APPDATA%\...\MyScripts\` *is* on `sys.path` and writable, so a
runtime package is technically distributable — **but `pip` and `setuptools` are both absent from
Fusion's interpreter**, so a user receiving such a script has no ordinary way to install anything.
That is what decides it, not impossibility.

So every `emit` function returns **source text**. Three categories, ranked by footprint in the
user's file:

| | Category | Footprint | Examples |
|---|---|---|---|
| 1 | Generation-time compute/validate, emit plain API | **zero** | parameter-name validation, mm→cm conversion, chain check |
| 2 | Emitted inline block | short, per call site | `datum_plane`, `sketch_on` |
| 3 | Emitted `_fh_` prelude function | fixed, once | `constrained_rect`, `find_face` |

**Prefer 1, accept 2, justify 3.** Prelude functions are `_fh_`-prefixed — greppable for
tree-shaking, unmistakably not Autodesk API, and trivially deletable. `render()` emits only the
definitions actually referenced.

### Accepted, rejected, and one demotion

**Accepted:** `parameters` (category 1 — raises at authoring time on the whole naming-trap class);
`seed_point` (category 1); `datum_plane` (asserts the `setByOffset` bool return, which **can fail
silently and nothing else checks it**); `constrained_rect`; `find_face`; `closed_polyline`
(deprioritised until phases 1–2 show polyline profiles are common).

**Rejected:** `bound_dimension` — it wraps one assignment, and R2's lint catches the omission
statically, offline, in *all* code rather than only in code that used the helper. `token_ref` —
an attribute read. **Extrudes and all feature creation** — `NewBodyFeatureOperation` vs `Join` vs
`Cut` is exactly the design intent the user must see. **A general `mm()` helper** — it makes
raw-float dimensions *easy*, which is the failure mode the design exists to prevent. **Part-level
helpers** (`make_box`, `make_bracket`) — `emit`'s scope stops at a single API *sequence*.

**One demotion worth recording:** `_fh_placer`, initially the strongest candidate, was demoted to
category 1 when `Sketch.modelToSketchSpace()` turned out to exist as a direct method. The XZ
inversion trap collapses to one line of plain API, so the prelude never pays for itself. **The
most valuable guarantee in the set turned out to need no helper at all.**

### The verbosity claim, corrected

An early comparison reported 88 lines with helpers against 32 without. That was unfair to the
helpers: the 32-line version had **seven silent defects**. Against *correct* hand-written output:

| | Lines | Silent defects |
|---|---|---|
| Naive hand-written | 32 | 7 |
| Correct hand-written | ~95 | 0 |
| Generated with helpers | ~78 | 0 |

**Helpers are shorter than correct code, and the gap widens with each additional sketch.**
"Verbose output" is only true against defective output.

---

## 7. Component: testing and packaging

### Three tiers

**Unit (no Fusion, runs in CI)** — the bulk. Lint rules against fixtures, the pyright gate against
known-good and known-bad inputs, chain arithmetic, schema validation, verdict parsing.

Expectations live **on the offending line** as `# EXPECT: <rule-id>` markers, not in a sidecar and
not as line numbers in a header — an inline marker moves with the code when a fixture is edited. A
good fixture simply contains zero markers, so one loader serves both corpora and the
false-positive guard is the *same assertion* as the true-positive one:

```python
assert {(f.line, f.rule) for f in lint.run(src)} == markers.parse(path)
```

Exact set equality, both directions. Adding a fixture needs no test edit.

**Integration (Fusion required, opt-in)** — P1–P8 become regression tests, asserting on parsed
`FH_RESULT` JSON, never on prose. P5's test explicitly asserts `unhealthy_features == 0` — the
test asserts Fusion *fails to complain*, so if a future version starts complaining, we find out.

**Golden/snapshot** — never asserted by equality alone. Every golden must also satisfy properties
that survive re-blessing: `ast.parse` succeeds, lint returns clean, preflight passes, and the
expected check names are present. That is what stops a careless `--snapshot-update` blessing
broken output.

### Scratch document lifecycle

Measured constraints: there is **no `new` document operation** in the MCP (`open` requires a
`fileId`), so scratch documents can only be created from inside a script. The root component
**cannot be renamed** (`RuntimeError: 3 : root component name cannot be changed`), so tagging uses
`des.attributes.add(...)`, which is also enumerable across open documents.

**Cleanup must be harness-driven, not script-driven** — proven by accident when a probe raised
before reaching its own `doc.close(False)` and leaked a document. Any failing script leaks,
because the failing script never reaches its own cleanup. Four layers: per-test `finally`,
session-end sweep, pre-session sweep for previous sessions' leaks, and `atexit`.

The close guard refuses three ways: never touch a saved document, never an untagged one, never
another session's tag.

### The MCP result envelope

`result.content[0].text` is a JSON **string** containing `{"message": <stdout>, "success": true}`
or `{"error": <stdout + traceback>, "success": false}`. **Script failures return HTTP 200 with
`success: false`**, never a JSON-RPC error, and anything printed before the exception lands in
`error`, not `message`. `notifications/initialized` returns 202 with an **empty body** — a client
that JSON-parses every response crashes on the handshake.

### CI split

Ruff, pyright-on-our-own-source, unit, golden, and gate **plumbing** run on GitHub Actions
(ubuntu + windows — `stubs.py` resolves `%APPDATA%` paths and the fail-open bug was a Windows path
bug). Gate **fidelity** and P1–P8 stay local.

Gate plumbing is testable in CI without Autodesk's stubs by using **synthetic stubs we author**
covering the ~15 symbols the fixtures touch. Fidelity ("does it catch `addFixed`?") needs the real
stubs; plumbing ("is the config parsed, does the canary fire, is `GATE_BROKEN` raised?") does not
— and plumbing is where the fail-open regression protection lives.

### Dependencies

Two, each justified: **pyright** (preflight cannot function without it; runtime, not dev, because
it runs on the user's machine — pinned exactly in dev because gate expectations are
version-sensitive) and **pyyaml** (the declaration is YAML; phase 1 does not need it).

Deliberately absent: build123d/CadQuery/solvespace (rejected in the design), sympy (`Fraction` is
stdlib and exact), httpx/requests (the MCP client is test-only; `urllib` is proven sufficient),
syrupy (~30 lines of snapshot helper).

### API-version drift

`tests/api_version.lock` records API version, pyright version and stub sha256. Drift is
**reported, never silently absorbed**. Pyright drifts by itself — the PyPI wrapper auto-upgrades
unless pinned — so `PYRIGHT_PYTHON_FORCE_VERSION` is set from the lock file inside preflight.

---

## 8. Cross-component interfaces

| From | To | Contract |
|---|---|---|
| skill | preflight | exit 0/1/3 = send / fix script / fix machine; `signature` detects a stalled loop |
| preflight | skill | every finding cites its rule number and restates the rule in one line |
| preflight | verify | installs `fh_verify.py`, converts declaration to `decl.json`, lints the stub |
| verify | skill | verdict carries `code` only; the skill body holds remediation |
| verify | emit | `Script.render(verify=<block text>)` — emit owns placement, verify owns content |
| declare | verify | `FACE_SPECS`, `CLEARANCES`, `DATUM_HEIGHTS_CM` as decimal strings **already in cm**, plus a `digest` echoed in the verdict |
| declare | preflight | `--declaration` enables declared-vs-script parameter cross-checks |
| emit | preflight | `KNOWN_BINDERS` so escape into a known binder counts as bound |

**One coupling that must be wired explicitly:** `measureMinimumDistance` returns `0.00000` for
both "touching" and "interpenetrating by 5 mm". So **a clearance measuring 0 must never report
PASS while interference is non-empty for the same bodies** — otherwise a `min: 0 mm` clearance
passes on a fully embedded part, which is exactly the P5 defect.

---

## 9. Open questions

Ordered by consequence. Several were closed during the design pass by direct measurement; those
are recorded in [`fusion-api-notes.md`](fusion-api-notes.md).

1. **Autodesk stub licensing.** No LICENSE, no copyright header, no redistribution grant. Do not
   vendor into a public repo without a human decision. Synthetic stubs cover CI regardless.
2. **Is `sketch.profiles` ordering stable across rebuilds?** Every recipe uses `profiles.item(0)`
   and it is the one index pick the design cannot currently eliminate. If unstable,
   `find_profile(sketch, predicate)` is needed and becomes the strongest remaining helper
   candidate. **The largest open technical risk.**
3. **Is `sketch.profiles.item(0)` in or out of R4?** Currently excluded as the universal idiom.
   A profile index *does* shift when a sketch gains geometry. Needs phase-1 evidence.
4. **The `profile-not-closed` taxonomy regex is unverified.** Provisional.
5. **`boolean.no_op` has no message** and must be detected by post-condition (pre/post volume),
   which requires an `emit` assertion.
6. **Does `modelToSketchSpace` project an off-plane point or error?** If it silently projects,
   `seed_point` should assert the round-trip.
7. **Does chaining `endSketchPoint` create a real constraint, or are the points merely the same
   object?** Affects DOF arithmetic for `closed_polyline` only.
8. **R5's falsifier:** if phase-1 evidence shows repair scripts never hold BRep references across
   a parameter write, R5 should be dropped.
9. **Compound and negative `setByOffset` expressions** are unprobed; only a bare parameter name is
   verified.
10. **`expect` cardinality after boolean joins** — that joining four bosses leaves the floor as one
    face with four inner loops is likely but unverified.

---

## 10. Build order

**Phase 1 — the gate.** `preflight` + `lint` + `verify` + the skill's standing rules. Independently
useful, every piece already verified, and it is the part that catches silent failure.

Definition of done, abbreviated from the full 18 points:

- Three outcomes, with `GATE_BROKEN` never reported as a pass; canary green; malformed config,
  missing stubs and unresolvable imports each raise `GateBroken` with a specific message
- Config generated programmatically; no hand-maintained path in the repo
- Every rule has ≥1 known-bad fixture matching exactly on rule and line
- **The good corpus — including all eight probe scripts — produces zero findings.** The
  false-positive claim under test rather than asserted
- Suppression handling, both directions
- `verify.generate_block()` output parses, passes lint, passes preflight, contains all five checks
- P1–P8 pass against live Fusion, asserting on parsed JSON
- **Zero leaked documents** after a full run *and* a deliberately interrupted one
- CI green on ubuntu + windows

**Phase 2 — the procedure.** The declaration block, the dimensional-chain check, the full skill
workflow.

**Phase 3 — the helpers.** `emit`, scoped by what phases 1 and 2 show Claude actually getting
wrong repeatedly. Building these first would be guessing.
