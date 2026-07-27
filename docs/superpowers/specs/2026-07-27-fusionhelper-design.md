# FusionHelper — Design

**Date:** 2026-07-27
**Status:** Approved design, pending implementation plan
**Evidence base:** [`docs/probe-results.md`](../../probe-results.md) — eight probes run against a live Fusion 360 install (API 2703.1.20)

---

## What we are building

**A Claude Code skill and a small Python library. We are not building an MCP server.**

Autodesk already ships one, it is built into Fusion (Preferences > General > API >
"Fusion MCP Server"), and it already works — every probe in the evidence base was run
through it. It exposes `fusion_mcp_execute`, which runs arbitrary Python against the live
Fusion API, so there is no capability gap for us to fill at the transport layer.

What ships:

```
FusionHelper/
├── skills/fusion-design/SKILL.md   ← the procedure Claude follows
└── fusionhelper/
    ├── preflight.py                ← pyright + lint on the script BEFORE Fusion sees it
    ├── lint.py                     ← the five rules (no createByReal, no index picks, …)
    ├── verify.py                   ← generates the assertion block appended to each script
    └── emit.py                     ← correct-pattern helpers (phase 3)
```

A markdown file and a small Python package. Nothing else.

**In use:**

1. User describes a part.
2. Claude loads the `fusion-design` skill — the rules are now resident in context.
3. Claude writes the declaration block (parameters, datums, clearances) and checks the
   dimensional chain, before any geometry.
4. Claude generates Fusion Python.
5. `python -m fusionhelper.preflight box.py` — **local, no Fusion involved**, ~2 s.
6. Script goes to Fusion through **Autodesk's** MCP.
7. The appended verification block prints a JSON verdict.
8. Renders shown to the user.

Steps 2–5 and 7 are what this project builds. Step 6 already exists.

**Why a skill rather than our own MCP server** is argued in *Architecture* below; the short
version is that the problem is Claude failing to follow a discipline across a long session,
and a skill body is the only vehicle that stays resident in context for the whole session.

---

## Problem

Claude Code can generate Fusion 360 Python that executes without error and produces
geometry that is wrong. The observed failures are positional (parts misaligned, wrongly
oriented, intersecting, floating) and dimensional (sizes drifting, holes not lining up,
parts not fitting).

The failures are not caused by ignorance of CAD or of the Fusion API. They are caused by
Claude computing coordinates, composing transforms, and restating dimensions across a long
generation — and by nothing in the toolchain objecting when the result is wrong.

**The defining characteristic of the problem is silence.** In probe P5 an identical bracket
was built two ways; after one parameter edit the raw-coordinate version was 40 mm off the
plate edge and 8 mm embedded in the plate. Fusion reported zero errors. In P8, 60 mm holes
on an 80 mm plate reported healthy. In the partially-bound case, changing a parameter
produced byte-identical geometry and no warning.

FusionHelper exists to make those errors either impossible to express or impossible to miss.

## Goals

1. Generated models are **correct at build time** — no interference, no floating parts,
   dimensions matching the declared intent.
2. Generated models **stay editable** — a real parametric timeline with named user
   parameters, so changing `wall_t` rebuilds the model rather than requiring a rewrite.
3. Failures are **loud and specific** — the loose sketch entity is named, the clashing pair
   is named with its overlap volume, the drifted dimension is named with its error.
4. Iteration cost drops. `claude trophy v5` took five attempts; the target is that a
   correct-and-editable result is the normal first outcome.

## Non-goals

- Freeform and organic surfacing (lofts over sculpted surfaces, class-A surfacing). The
  research explicitly excluded it and the interventions here do not transfer.
- Replacing Fusion's solver, or shipping a second geometry kernel.
- Simulation, FEA, manufacturability analysis, or cost estimation.
- Supporting Fusion Personal licence in v1. The transport depends on the official MCP, which
  requires a subscription. A degradation path exists (see *Portability*) but is not built first.

---

## Principle

**Make the error inexpressible rather than detectable; where it must remain expressible,
make it impossible to miss.**

This is the single organising idea and it comes from the evidence. The largest measured
effect in the reviewed literature (+28.7 pp) came from removing one axis of reasoning and
having deterministic code derive it. A system in which the LLM declared constraints and a
solver computed coordinates bought +1.14 CLIP points on the one direct ablation available.
The cheap structural intervention outperformed the elaborate one by roughly 25×.

Applied here: Claude does not compute where things go. It declares named parameters and
named datums, and Fusion's own solver places the geometry. A dimension that is stated once
and referenced thereafter cannot drift, because there is no second statement to disagree
with the first.

---

## Architecture

Three layers, **of which we build two.** The transport is Autodesk's and needs no work.

```
  ┌─────────────────────────────────────────────────────────┐
  │ SKILL  fusion-design                                    │
  │   the procedure: parameters → datums → layout →         │
  │   detail → gate → execute → verify → repair             │
  └─────────────────────────────────────────────────────────┘
                            │  Claude writes Python using
                            ▼
  ┌─────────────────────────────────────────────────────────┐
  │ LIBRARY  fusionhelper/                                  │
  │   preflight   pyright gate + lint rules                 │
  │   emit        correct-pattern helpers                   │
  │   verify      the assertion block                       │
  └─────────────────────────────────────────────────────────┘
                            │  script text
                            ▼
  ┌─────────────────────────────────────────────────────────┐
  │ TRANSPORT  official Autodesk Fusion MCP  (exists)       │
  │   fusion_mcp_execute / _read / _update                  │
  └─────────────────────────────────────────────────────────┘
```

### Why a skill for the procedure

A skill body enters the conversation once and stays for the session. The failure being
addressed is drift across a long modelling run, so the discipline has to be resident. An MCP
tool description is not; it is read at call time and forgotten.

The counter-argument is real and worth recording: **procedure in a skill is advisory.**
Claude can read "verify before emitting" and not verify. A server could make it structurally
impossible by refusing to execute unvalidated scripts. The reason the skill is still the
right primary vehicle is that the transport is Autodesk's MCP, which we do not control and
should not fork — so a hard gate would mean building and maintaining a proxy. The mitigation
is that the *pre-flight gate is a library call the skill mandates*, and its output is
unmissable in the transcript. If advisory discipline proves insufficient in practice, the
escalation is a wrapper that refuses to call `fusion_mcp_execute` without a passing
pre-flight result. That is a v2 decision to be made on evidence, not now.

### Why no external geometry kernel

The original design assumed FusionHelper would need `build123d` or `python-solvespace` to
compute coordinates and to report degrees of freedom. Both assumptions were tested and both
failed:

- **Coordinate computation is unnecessary.** Fusion's solver snaps approximate seed
  coordinates to exact. A profile seeded at `(0.1,−0.2) → (4.3,0.15) → (4.1,2.4) → (−0.2,2.6)`
  resolved to exactly `(0,0) → (4,0) → (4,2.5) → (0,2.5)`. Generated coordinates only need to
  be roughly right.
- **DOF diagnostics already exist, per-entity.** Fusion exposes no DOF *count*, but
  `SketchEntity.isFullyConstrained` names the specific under-constrained entities
  (`[True, False, False, True]` → entities 1 and 2 are loose). A count is not actionable;
  naming the entity is. This was the strongest remaining argument for an external solver and
  it does not survive contact with the API.

A second kernel would mean a shadow model that can silently diverge from what Fusion
actually builds — a new class of bug, in exchange for capability Fusion already provides.

---

## Components

### `fusionhelper.preflight`

Runs before any script reaches Fusion. Two independent checks.

**Static type check.** Pyright against Autodesk's shipped stubs at
`%APPDATA%\Autodesk\Autodesk Fusion 360\API\Python\defs`. Verified: 7/7 hallucinated API
calls caught (including `geometricConstraints.addFixed`, a plausible-looking constraint type
that does not exist), 0 false positives, ~2 s, no Fusion round-trip. Because it validates
against the installed stubs it tracks the user's Fusion version automatically.

> **The gate fails OPEN, and this is the most important constraint on its implementation.**
> A malformed `pyrightconfig.json` makes pyright print one line to stderr, fall back to
> default settings, and **exit normally** — losing `extraPaths` and weakening
> `reportAttributeAccessIssue`. Measured consequence: 3 errors instead of 7, with all seven
> genuine hallucinations undetected, while looking like a clean run.
>
> Therefore: the config is **generated programmatically** (never hand-maintained, never
> string-templated); every invocation runs a **canary** — a known-bad probe it asserts pyright
> flagged — proving config parse, stub resolution and rule severity together; and preflight
> returns **three** outcomes, `PASS` / `FAIL` / `GATE_BROKEN`, where `GATE_BROKEN` is never
> reported as a pass. A gate that can silently stop working converts "unchecked" into
> "checked and clean", which is the exact failure class this project exists to eliminate.

Required configuration — two settings are load-bearing. `reportArgumentType: "none"` is not
optional: Fusion enums are plain classes with `int` attributes while parameters are annotated
with the enum class type, so every enum argument otherwise raises a false positive and drowns
the signal. And `include` must name the single **staged** file — with `["."]`, pyright analysed
4 files and produced 1168 diagnostics instead of 1 and 7, which makes the gate unusable in a
real project directory. Stage the script into an isolated temp directory, which also escapes
any ancestor `pyrightconfig.json` or `pyproject.toml` `[tool.pyright]`.

```json
{
  "include": ["script.py"],
  "extraPaths": ["<discovered defs path>"],
  "typeCheckingMode": "basic",
  "pythonVersion": "3.12",
  "reportMissingImports": "error",
  "reportAttributeAccessIssue": "error",
  "reportArgumentType": "none",
  "reportSelfClsParameterName": "none"
}
```

**Lint rules.** These catch what type-checking structurally cannot, because the offending
calls are all well-typed:

| Rule | Detects | Why it matters |
|---|---|---|
| `no-create-by-real` | **Any** `ValueInput.createByReal` call | Bakes a literal; the timeline looks parametric and dies on first edit |
| `no-index-topology` | `body.faces[n]`, `body.edges[n]` | Breaks when face count changes (P4) |
| `no-hardcoded-axis` | Literal axis vectors / assumed up-direction | The XZ inversion trap |
| `dimension-must-bind` | A `sketchDimensions.add*` whose `.parameter.expression` is never assigned | The partially-bound dead-timeline case |
| `param-name-safe` | Parameter names that Fusion rejects | Unit symbols, function names, duplicates — all fail with the same misleading message |

`no-create-by-real` is deliberately absolute rather than "on dimensional values". Deciding
whether a given value is dimensional requires understanding what the call means, which a
lint rule cannot do reliably — and the failure it prevents is silent and only surfaces at
the user's first edit. Any genuinely non-parametric constant is expressible as
`createByString('3')`, so the strict rule costs nothing. A script needing an exception
declares it explicitly with a suppression comment naming the reason; a suppression without
a reason is itself a lint failure.

### `fusionhelper.emit`

Helpers that make the correct pattern the path of least resistance. Not an abstraction over
Fusion — generated scripts remain readable Fusion API code the user can edit. These exist
because the correct sequences were established empirically and are easy to get subtly wrong.

- `constrained_rect(sketch, w_expr, d_expr, ...)` — the P2 recipe: rectangle, coincident to
  origin, two horizontals, two verticals, two parameter-bound dimensions. Reaches
  `isFullyConstrained=True`.
- `bound_dimension(dim, expr)` — creates the dimension and asserts the expression binding in
  one call, so the partially-bound case cannot arise by omission.
- `datum_plane(root, offset_expr, name)` — named construction plane at a parameter-bound
  offset. Named, because sketching on `body.faces[n]` is the fragile alternative.
- `sketch_on(plane)` — returns a placement helper that derives axis mapping from
  `sketch.sketchToModelSpace()` at runtime rather than assuming the table.

### `fusionhelper.verify`

Generates the verification block appended to every script. All five checks verified working
and returning through `print()`:

1. **Constraint state** — `sketch.isFullyConstrained` per sketch; on failure, iterate
   `SketchEntity.isFullyConstrained` and name the loose entities.
2. **Parameter liveness** — perturb each user parameter, `adsk.doEvents()`, re-measure bbox
   and volume, restore. *This is the only check that catches partial binding*, where the
   model looks parametric and some dimensions silently do nothing.
3. **Timeline health** — sweep `healthState` and `errorOrWarningMessage`.
4. **Interference** — `analyzeInterference` across body pairs with
   `areCoincidentFacesIncluded = False`. The flag is essential: without it, a bracket
   correctly seated on a plate reads as a clash. Guard the call — it raises
   `RuntimeError: 3 : invalid input collections` with fewer than two bodies.
5. **Clearance** — `measureMinimumDistance` against clearances declared in the spec.

Output is a single JSON verdict so the repair loop reads a compact structured result rather
than prose.

### Skill: `fusion-design`

Owns the workflow and the standing rules. Workflow:

1. **Declare the parameter table first**, before any geometry. Named `snake_case`
   parameters, with derived parameters expressed in terms of others (`wall_t = outer_h / 5`,
   verified to recompute live).
2. **Check the dimensional chain** at table level — declared stack sums to declared overall.
   Rational arithmetic on the table, before a single sketch exists.
3. **Declare the datum frame** — named construction planes and axes.
4. **Layout before detail** — place major masses against datums; add fillets, chamfers and
   dress-up features last and minimally, so that when they break the rest of the model stands.
5. **Generate → pre-flight → execute → verify → repair.**
6. **Render for the human** once the numeric checks pass.

Standing rules, each traceable to a probe: never `createByReal`; bind every dimension;
constrain before dimensioning and check the gate between; never select topology by index;
capture `entityToken` and re-resolve rather than holding BRep objects across a rebuild;
derive axis mapping at runtime; `snake_case` parameter names.

---

## Data flow

```
description
  → parameter table + declared clearances/tolerances      (the spec; also the oracle)
  → datum frame declaration
  → generated Python (emit helpers)
  → preflight: pyright + lint                             offline, ~2s
  → fusion_mcp_execute
  → verification block → JSON verdict
  → PASS → renders for the human
  → FAIL → repair loop (exception text or named failure)
  → abort → fusion_mcp_update undo
```

The parameter table is doing double duty: it is the design intent, and it is the ground
truth the assertions check against. This is why it must be declared before geometry rather
than extracted afterwards.

---

## Error handling

| Failure | Detection | Response |
|---|---|---|
| Hallucinated API | Pyright | Fix before sending; never reaches Fusion |
| Banned pattern | Lint | Fix before sending |
| Runtime exception | MCP returns exception text | Repair loop. Do **not** catch exceptions in generated scripts — Autodesk's own guidance, and the message is the diagnostic |
| Over-constraint | `RuntimeError` on the constraint call | Fail-safe: raises *before* mutating, sketch left healthy (P3). Three distinguishable messages drive different responses: redundant dimension, redundant constraint, conflicting constraint |
| Under-constrained sketch | `isFullyConstrained` false | Name loose entities via per-entity flag; constrain and re-check |
| Dead / partially-bound timeline | Parameter perturbation | Report which parameter produced no geometric change |
| Interference | `analyzeInterference` | Report clashing pair and overlap volume |
| Silent nonsense geometry | Assertions vs declared spec | The residual class — see *Limits* |
| Model left in a bad state | — | `fusion_mcp_update` undo |

**Documents are never saved unless the user explicitly asks.** Autodesk's own tool
description states this, and probe work is done in scratch documents.

---

## Testing

The eight probes become the regression suite. They already execute against a real Fusion
install through the same transport the product uses, which makes them integration tests
rather than mocks.

| Test | Asserts |
|---|---|
| P1 | Generated script yields a model that rebuilds on parameter edit |
| P2 | `isFullyConstrained` transitions correctly as constraints are applied |
| P3 | Over-constraint raises without mutating; messages remain distinguishable |
| P4 | Index picks break on topology change; tokens and predicates survive |
| P5 | Datum-placed geometry holds position across an edit; raw coordinates drift |
| P6 | One parameter edit propagates to all dependent features |
| P7 | `analyzeInterference` reports the correct clash volume |
| P8 | Parameter sweep surfaces reference failures |

Unit-testable without Fusion: every lint rule (against fixture scripts), the pyright gate
(against `good_script.py` / `bad_script.py`), and dimensional-chain checking on the parameter
table.

A pinned-version concern: the pyright gate validates against locally installed stubs, so a
Fusion update can change results. The suite should record the API version it ran against
(`API/version.txt`), currently 2703.1.20.

---

## Limits — to be stated in the product, not hidden

**Every check verifies the model against what was declared.** A wrong-but-consistent
declaration passes all of them. If the parameter table says a bracket is 40 mm wide and it
should have been 50 mm, nothing here objects. Autoformalization — translating intent into
formal declarations — runs at 62.5% to 98.7% in the literature depending on domain
complexity, and that is the uncapped error term in this design.

**Fusion tolerates absurd-but-constructible geometry.** P8 caught only 1 of 4 extreme
configurations; 60 mm holes on an 80 mm plate reported healthy. Assertions against declared
intent are required precisely because the application's own health reporting is an
incomplete oracle.

**Renders go to the human, not back to Claude.** On identical spatial content, symbolic
input measured roughly twice as accurate as image input for frontier models
(SpatialEval: 0.957 vs 0.455 for Claude 3 Opus). This was demonstrated again during this
project — a rendered view of a single joined body was misread as two interpenetrating
parts, while the numeric read-back was immediately correct. Renders remain valuable for
the one thing assertions structurally cannot do: catching "this is the wrong object
entirely." That is intent-checking, and it is the human's job.

**Therefore the product must not present a green checklist as proof of correctness.** The
honest claim is: *this model matches the description you gave, and it is built correctly and
remains editable.* Not: *this is the part you wanted.*

---

## Portability

Nothing is locked to Claude Code. The skill follows the Agent Skills open standard; the
library is plain Python; the transport is Autodesk's own MCP, reachable from any MCP client.

**Personal-licence degradation path** (not built in v1): the official MCP requires a
subscription, but self-authored scripts and add-ins work on Personal. The generator is
unaffected — same script, different transport. A watcher add-in (auto-starting via
`runOnStartup`, polling a queue folder, marshalling onto the main thread via `CustomEvent`)
is a confirmed working pattern. Personal users also face a 10-active-document limit, so
iteration must stay within one document.

---

## The declaration block

The parameter table, datum frame, and declared clearances are emitted as a single typed
block, **not** as a whole-output schema. Claude reasons in prose first and then emits the
block between delimiters. This shape is deliberate: strict schema-forced output measured up
to −27 pp on reasoning benchmarks because it forces emission before deliberation completes,
while permitting free reasoning around a constrained block recovered and exceeded the
baseline.

The block is YAML, because it round-trips to a Python dict for the dimensional-chain check
and stays readable when the user edits it by hand:

```yaml
parameters:
  outer_w:  60 mm
  outer_d:  40 mm
  wall_t:   outer_w / 20        # derived; recomputes live
datums:
  base_plane: XY
  lid_plane:  offset(base_plane, outer_h)
clearances:
  - between: [lid.inner_face, boss.top_face]
    min: 0.8 mm
chains:
  - total: outer_w
    parts: [wall_t, cavity_w, wall_t]
```

`chains` is what makes the pre-geometry check possible: the declared stack must sum to the
declared overall, checked with rational arithmetic before any sketch exists.

## Implementation phasing

The three components are not equally urgent and should not be one undifferentiated plan.

**Phase 1 — the gate.** `preflight` (pyright config + the five lint rules) and `verify` (the
five-check assertion block), plus the skill's standing rules. This is the part that catches
silent failure, it is independently useful without anything else, and every piece of it is
already verified working. A generated script that passes phase 1 is already far better than
the status quo.

**Phase 2 — the procedure.** The declaration block, the dimensional-chain check, and the
full skill workflow.

**Phase 3 — the helpers.** `emit`, scoped by what phase 1 and 2 show Claude actually getting
wrong repeatedly. Building these first would be guessing.

## Open questions for the implementation plan

1. **Repair loop bound.** How many automatic repair attempts before surfacing to the user,
   and whether a repeated identical failure should abort earlier.
2. **Clearance target syntax.** The example above writes `lid.inner_face`. How named faces
   are resolved to real topology — by geometric predicate at authoring time, or by a
   registry the generator maintains — is undecided and depends on phase 1 experience.
3. **Scope of `emit`.** Deferred to phase 3 by design.
