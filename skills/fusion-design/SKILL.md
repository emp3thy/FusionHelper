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
  `fusionhelper.verify.append_to()`, unmodified, last in the file. Not waivable —
  the finding sits past the last line, so there is no line to attach a suppression
  to; regenerate the tail instead.
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
   - exit 1 FAIL → fix the script (findings cite rule numbers). A pyright attribute error on a
     call you have verified live may be a **STUB GAP**, not a hallucination — check
     `reference/api-recipes.md` (the `setDistanceExtent` precedent) before editing; lint
     suppressions do not apply to pyright findings.
   - exit 3 GATE_BROKEN / environment → fix the machine. **Do not edit the script.**
6. **Execute** via the official Fusion MCP (`fusion_mcp_execute`,
   `featureType: "script"`). The stub prints one `FH_VERDICT1 {...}` JSON line.
7. **Verify:** parse the verdict — AND the `FH_CHECK1 {...}` lines above it: the
   verdict carries only check statuses and hint codes; the per-finding detail
   (which sketch, which entities, which parameter) is in the `FH_CHECK1` lines.
   `pass` → render screenshots *for the user* (renders are for the human —
   numeric read-back is the oracle, not your eyes). Anything else → repair loop.
   Verify options go in module globals: `FH_OPTS = {...}` before `run`, keys:
   `force_liveness` (run liveness even after a cheap-check failure — essential in
   a pre-existing document, see below), `only_params` (scope liveness to YOUR
   parameters), `liveness_budget_s` (default 20 s samples large tables — raise it
   to cover every parameter), `liveness: False`, `canary`, `max_bodies`.
8. **Repair loop.** Budgets: preflight fixes 3 (offline, separate); runtime with
   a taxonomy code 3; unclassified runtime 2; verification failures 2; hard cap
   **5 `fusion_mcp_execute` calls per request**. Abort early when: identical failure signature twice;
   an A→B→A recurrence appears; error count fails to strictly decrease twice;
   a repair introduces a new error code without clearing the old one (counts as no progress).
   Third attempt is always a from-scratch regeneration, never a patch.
   `model.not_restored`, `model.inert`, `edit.introduces_clash`, or a timeline error state → undo
   (`fusion_mcp_update`) and regenerate.
9. **When giving up:** say what is wrong in plain language, show the attempt
   history, state the document's condition, ask one specific question, and
   attach a render.

## Working in an existing document (calibrated live, 2026-07-28)

The five checks sweep the WHOLE document, so a user's pre-existing unconstrained
sketches fail your build's verdict and skip liveness with `prior_failure`. In an
existing document: expect `constraints: fail` from entities you did not create,
read the `FH_CHECK1` sketch names to separate yours from theirs, and re-verify
with `FH_OPTS = {"force_liveness": True, "only_params": [<your params>]}`.

Timeline hazards in someone else's document:
- `healthState 4` = a feature the USER rolled back (deliberate state, not damage).
- **Never call `timeline.moveToEnd()` blindly** — it rolls past and ACTIVATES the
  user's rolled-back tail, changing their model. Record `timeline.markerPosition`
  before any history edit and restore it (marker position is NOT part of the
  script transaction, and verify does not yet detect a moved marker).
- New features insert AT the marker, and `feature.timelineObject.rollTo(True)`
  plus delete/re-add replaces a feature in place — the right way to fix a
  committed-but-wrong feature without rebuilding.

Recovery semantics (measured): a FAILED `fusion_mcp_execute` rolls back
atomically — its parameter adds, deletes, and features all revert, so a crashed
attempt leaves the document as it was. Undo of COMMITTED calls goes through
`fusion_mcp_update` with `{"featureType": "undo"}`. Read-only survey/probe
scripts (gate them with `--no-stub`) do not count against the 5-execute repair
cap — the cap governs build/repair attempts.

Waivers (`# fusionhelper: allow ...`) apply only to the checked lint rules
(R1 R2 R4 R5 R6 R7); waiving R3/R9/R10 always reports "unused suppression"
because nothing fires for them — they are runtime/convention rules.

## Honest limits

Every check verifies the model against what was *declared*. A green verdict
means: built correctly, stays editable, matches the stated numbers. It does NOT
mean "this is the part you wanted" — that judgement belongs to the human, from
the renders. Say it that way. See `reference/limits.md`.
