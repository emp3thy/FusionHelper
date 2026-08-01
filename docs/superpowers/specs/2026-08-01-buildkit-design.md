# Buildkit Design

**Goal:** extract the build helpers that every Fusion build script
copy-pastes into a single canonical module (`fusionhelper/buildkit.py`),
plus a bundler that inlines the kit and the verification stub into the
single file that reaches Fusion over the MCP.

**Problem (measured, LED-wall project):** build16.py carries 15 shared
helper defs, back_splices.py 11, wall_bar.py 3 — and the copies have
drifted. back_splices.py still has the older face-count `blind_cut` and a
`plane_off` variant; the volume-validation fixes exist only in build16.py.
A bug fixed in one copy silently does not reach the others. The cost is
drift, not line count.

## Decisions (user-approved 2026-08-01)

1. **Explicit bundle step.** A `fusionhelper.bundle` command produces a
   bundled artifact; preflight/lint gate the ARTIFACT; the artifact is
   what is sent. What is gated is exactly what runs.
2. **Normalized API.** Signatures are redesigned around an explicit
   `BuildCtx`; drifted variants fold into one canonical version each.
   Existing scripts (checkpointed in their documents) port only if
   ever re-run.
3. **Bundler owns the verification stub.** Author scripts contain only
   `run()` plus declarations. R8 inverts: author scripts must NOT
   contain the stub (or kit-named defs).

## Module layout

```
fusionhelper/
  buildkit.py      # the kit: BuildCtx + helpers (single canonical copy)
  bundle.py        # CLI: python -m fusionhelper.bundle script.py
  lint/rules/r8_stub_intact.py   # inverted (see Lint changes)
```

An author script contains, in order: module docstring; declarations
(`FH_ATTEMPT`, `FH_OPTS`, `INTERFERENCE_ALLOWED`, `FH_REFS`, ... as
needed); `import adsk.core` / `import adsk.fusion`;
`from fusionhelper.buildkit import *` (or named imports); `run()`.

The import line doubles as the bundler's expansion marker. It is a real,
resolvable import, so pyright and the editor see true signatures while
authoring — no magic comments, no new syntax.

## Kit API

`BuildCtx` is created once at the top of `run()` and replaces today's
closure captures:

```python
def run(_context: str):
    app = adsk.core.Application.get()
    ctx = BuildCtx(app)
    # ctx exposes: des, root, up, extrudes, cbs, pt, dims_or, dirs, ops
```

Helpers are methods on `ctx` so state never threads through call sites.

Canonical helper set (one version each; drifted variants folded):

| Area | Methods | Notes |
|------|---------|-------|
| Sketch | `bound_rect2`, `bound_circle`, `all_profiles`, `plane_at_z` | jittered circle creation built in; `plane_at_z` absorbs `plane_off`; position-expression contract unchanged (base = CENTRE coordinate expression) |
| Cuts | `through_cut`, `sym_cut`, `blind_cut` | **volume-threshold validation only** — face-count opt-in lives on `pattern_cut` (`min_new_faces`), not on the cut helpers (api-notes §14/§15) |
| Joins/bodies | `checked_join`, `checked_newbody` | direction try-flip with caller predicate, resolved-direction cache |
| Patterns | `pattern_cut`, `pattern_bodies` | `pattern_cut` validates by volume threshold (absorbs `pattern_cut_vol`); internal `_pattern` keeps the direction/compute-mode retry ladder incl. degenerate `setDirectionTwo` |
| Utility | `val` | dead `seed_faces` returns dropped |

API rules carried over from measured findings: pattern seed cuts must cut
exactly one body (documented on `pattern_cut`); `AdjustPatternCompute`
for feature patterns only; per-iteration `adsk.doEvents()` inside any
loop the kit owns (R11).

## Bundler contract

`python -m fusionhelper.bundle path/to/script.py` writes
`path/to/script.bundled.py`:

1. **Validate the author script**: must contain a
   `from fusionhelper.buildkit import` line; must not contain the stub
   block or kit-named defs (same checks as inverted R8, enforced here
   too so bundling fails fast without the lint step).
2. **Expand**: replace the import line with the kit source, wrapped in
   `# fh-bundle: kit begin vN <hash>` / `# fh-bundle: kit end` markers
   (kit version + content hash).
3. **Append the stub**: the `# fusionhelper: verification stub` block
   after `run()`, exactly as today's pasted block.
4. **Deterministic**: same input + same kit → byte-identical artifact.
5. **Refuse already-bundled input** (marker detection) — no
   double-inlining.

Tracebacks: Fusion reports artifact line numbers; the artifact is a real
gated file on disk, so `line N` maps directly onto it.

## Gate workflow

```
author script.py → bundle → script.bundled.py → preflight+lint (artifact) → send artifact
```

- Preflight/lint always gate the artifact — the exact text Fusion
  executes. R1–R11 sweep kit code too; kit-internal waivers live once in
  `buildkit.py`.
- The driver's `step()` is unchanged; it points at bundled artifacts.
- SKILL.md workflow section gets the one-line pipeline update, and the
  patch/gate/launch rule extends naturally: edit author script →
  re-bundle → grep the artifact for the patched symbol → launch.

## Lint changes

R8 (`stub_intact`) inverts for author scripts: error if the stub block or
any kit-named top-level def appears in a file that has the buildkit
import. For bundled artifacts (detected by the `fh-bundle` markers) R8
keeps its current meaning: stub present and intact. One rule, two modes,
selected by marker presence.

## Testing

- **Offline pytest against `stubs.py`**: kit imports cleanly; `BuildCtx`
  constructs; each helper's validation math (volume thresholds, retry
  predicates, jitter uniqueness) unit-tested with fake bodies.
- **Bundler golden tests**: author fixture → expected artifact byte-for-
  byte; idempotency (re-bundle refused); failure cases (missing import,
  stub present in author, kit-name collision).
- **Lint tests**: inverted-R8 author-mode and artifact-mode cases.
- **Live calibration**: one trophy-style exercise script rebuilt kit-
  style, run once against real Fusion to prove the end-to-end path
  before any real project depends on the kit.

## Out of scope

- Porting the LED-wall scripts (checkpointed; port only if re-run).
- Any transport change to `run_script.py` / the MCP client.
- Splitting the skill; SKILL.md gets only the workflow line update.
