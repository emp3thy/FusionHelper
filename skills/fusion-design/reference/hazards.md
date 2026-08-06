Symptom-triggered lore. Read the section your symptom names; do not carry the whole file.

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

## Checkpoint versioning (the reset story)

Scripts build from a BASELINE, not from an empty file: v1 = the user's
hand-made parts and nothing else; later checkpoints layer verified script
output on top (v2 = v1 + sub-assembly, v3 = v2 + main build, each saved
only on a green verdict, with consent — see R10). This changes what
"regenerate from zero" costs:

- Architecture change / teardown: NEVER surgically delete generated bodies
  in a live heavy document (measured: ~20-30 s per `deleteMe` in a
  361-feature / 11k-occurrence doc — a wall teardown cost ~40 min).
  Restore the baseline version from the Data Panel and re-run the scripts.
- Never re-run a build script on a document that already contains its
  output — name collisions produce silently coincident " (N)"-suffixed
  duplicate bodies that renders and the current attempt's interference
  check cannot see. Version-restore makes this scenario impossible.
- Parameter-level changes never need a rebuild at all: edit the parameter.

## Heavy documents

- **A dead client is NOT a rolled-back script.** A client that times out or
  is killed mid-`fusion_mcp_execute` may leave Fusion to finish and COMMIT
  the script — or abort partway with no rollback. Measured leaks: stepped
  parameters left as `( 5 mm ) + 0.25 mm`, duplicate body sets, and
  half-applied reorganizations. After ANY client timeout: probe before
  re-running (double-build hazard), audit parameter expressions for step
  wrappers, and audit body counts for " (N)" suffixes and unexpected root
  bodies.
- **Orphaned requests still run.** Requests queued by killed clients
  execute in order when Fusion frees up. Never stack retries while Fusion
  is busy; poll with a single patient probe. Distinguish busy from frozen
  from outside: process CPU + `Responding` (a script on the UI thread
  shows a white window while working).
- **Instanced-component count dominates every cost.** 60 instances of a
  180-part component (≈11k leaf occurrences) took each verify liveness
  step to ~6 min (snapshot mass-properties) and each body delete to ~30 s.
  Exclude visual-only instanced components from verification with
  `FH_OPTS = {"snapshot_exclude": ["<component name prefix>", ...]}`, and
  scope `only_params` to what the step can actually exercise.
- Liveness on instanced-heavy documents remains budget-limited regardless:
  each parameter step forces a full document recompute that
  `snapshot_exclude` cannot avoid — expect `sampled` mode and say so in
  the report.
- **After body moves/deletes, check the light bulbs.** Fusion spontaneously
  switches off component/occurrence `isLightBulbOn` after heavy
  reorganizations — geometry looks deleted but is only dark.

## Editing a committed model

- **A parameter whose feature bottoms out in a void reads as `param.dead`.**
  Parameterise the member that actually drives the stack, not the cut that is
  insensitive to it.
