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
- **Why R11 matters:** scripts run on Fusion's UI thread — an unbroken
  mutating loop freezes the window for its whole duration, which is why
  `adsk.doEvents()` per iteration (SKILL.md) is not optional. The verify
  block breathes on its own (between checks, per liveness step, every 25
  snapshot bodies).
- **After body moves/deletes, check the light bulbs.** Fusion spontaneously
  switches off component/occurrence `isLightBulbOn` after heavy
  reorganizations — geometry looks deleted but is only dark.

## Editing a committed model

- **A parameter whose feature bottoms out in a void reads as `param.dead`.**
  Parameterise the member that actually drives the stack, not the cut that is
  insensitive to it.

## Art sketches at scale (measured 2026-08-06)

Decorative line-art (engraved scrollwork, logos, guilloche) breaks assumptions
that hold fine for a dozen feature sketches.

- **Sketch cost is superlinear; deletion is pathological.** ~300-line sketches
  solve in seconds; one 2680-line sketch ground the UI for 70+ minutes; and
  DELETING a ~1200-curve fixed sketch took ~20 minutes. Chunk line-art to <=300
  lines per sketch, set `isComputeDeferred` while adding entities, and on
  re-entry RESUME drawing at the first undrawn polygon — never delete-and-redraw
  a big sketch to recover.
- **Sketches and features share one name namespace.** An extrude named
  identically to its sketch is silently auto-suffixed "name (1)", and an
  `itemByName` idempotency guard then misses it and re-runs the stage. Suffix
  feature names (`_join`).
- **A feature whose participants live inside a component lands in THAT
  component's feature collection**, not root's — a root-only `itemByName` guard
  misses it and the stage re-runs into a zero-volume join. Search root plus
  every `allOccurrences` component.
- **Orphaned timed-out requests execute later in whatever document is active at
  that moment.** After any client timeout, re-probe the active document's
  identity before trusting state or launching anything: a "vanished" build had
  in fact been completed by an orphan while a different document was in front.
- **Some documents are "Part Design" type** — `occurrences.addNewComponent`
  raises "Part Design documents can only contain one component". A document
  created via `documents.add(FusionDesignDocumentType)` allowed components.
  Probe with a throwaway `addNewComponent` + `deleteMe` before building
  anything that groups bodies.
- **Extruding every profile of a stroke-art sketch fills the enclosed voids**
  (each closed region is its own profile, so curl eyes come out solid). Do not
  try to classify profiles after the fact — an area match misses fragments and
  a centroid test fails outright, because a C-shaped strip's centroid lies in
  its own eye. Design the strokes pairwise-disjoint with open curls, and the
  sketch yields exactly one profile per polygon. See `print-in-place-design`.

## Sharing Fusion with the user (measured 2026-11-22)

The user is in the same Fusion session, clicking, while your scripts run.

- **Verify checks whatever document is in front when it starts.** Scripts run
  on the UI thread and every `adsk.doEvents()` lets the user's clicks through.
  A tab switched mid-build returned a complete verdict — bounding box,
  parameter count, a full liveness pass that stepped parameters — for the
  document in the next tab. Kit v3 records the build document
  (`FH_OPTS['built_root_id']`, the root component's GUID) and `fh_verify`
  answers `verify.wrong_document` without checking or stepping anything. A
  script that does not use the kit has no such guard: set
  `FH_OPTS["built_root_id"] = des.rootComponent.id` at the top of `run`, and
  compare the verdict's `bbox_mm` / `params` with what you built.
- **The same applies to every utility script.** A colouring pass reported
  "painted 0 of 0" because it ran against another tab. Have utilities print
  what they acted on, and read it.
- **Never address a document by position.** `app.documents.item(i)` changes
  meaning when the user closes a superseded document — and they will. Find a
  document by what is in it (body names at root AND inside components) and
  refuse unless exactly one matches.
- **Reusing a document for a rebuild:** loop `fusion_mcp_update` undo until
  `canUndo` is false, then probe for `timeline 0 / bodies 0` before building.
  This beats opening a new document per attempt, which leaves the user a
  stack of anonymous "Untitled" tabs to sort out.
- **Post-build steps act on components too.** Once bodies are grouped into
  components, `root.bRepBodies` is empty; walk `root.occurrences` as well.

## Derived and fixed-height geometry (measured 2026-11-22)

- **Liveness steps derived parameters, not just root ones.** A derived
  `total_t = 2 * bis_t + fill_t` was overridden with a literal step, moved an
  inlay plane above the body, and read as `param.fragile` ("No target
  body"). Do not create derived convenience parameters for stack heights or
  datum offsets; write the expression inline in the plane offset or dimension.
- **A fixed-height feature in a parameter-driven pocket clashes.** A revolved
  profile lives at absolute z. Its pocket, cut from a plane at
  `thickness - depth`, rises when thickness is stepped and buries the fixed
  plug: `edit.introduces_clash`. Cut the pocket with a revolve at the same
  fixed heights, open upward — then a thickness edit leaves the feature proud
  or recessed, but never inside material. State in the report that it is
  fixed art.
- **Fixed art is a legitimate choice — say so.** Outlines and decor mapped
  through `modelToSketchSpace` and fixed do not follow parameters. Use literal
  expressions for their sizes rather than a parameter that only half-drives
  the part, and tell the user which things the parameters do and do not move.
- **A fillet or taper sized near its limit is fragile under stepping.** Leave
  headroom, or use a literal where a parameter could only break it.

## Booleans, tapers and fillets on decorative geometry (measured 2026-11-22)

- **A cut exactly tangent to, or coincident with, an existing surface returns
  garbage.** A revolve-cut whose sides lay on an existing cone left the
  bodies' summed volume 55 mm³ HIGHER after later cuts. Keep cut profiles
  0.1–0.2 mm proud of what they meet, with their open edge well inside the
  existing void — and gate every cut on a plausible volume range, both ends.
- **A profile edge just outside an existing cavity leaves hanging slivers**
  (0.38 mm wide, found only by an overhang sweep).
- **A tapered extrude with the WIDENING sign raises** (`ASM_INCONS_REL`) on
  tight strokes instead of returning something checkable. Learn the narrowing
  sign once, on a simple shape (ring, frame), and reuse it for the rest.
- **Taper limits depend on what is joined together.** Four mirrored spiral
  strokes failed a 30° tapered join as a set, passed individually, and passed
  as a set at 20°.
- **Spline outlines fillet; polyline outlines barely do.** Tops of tapered
  relief: polyline swirls took 0.12 mm, the same swirls as closed fitted
  splines took 0.3 mm (2–4 edges per set instead of 68–216). Rim fillet on a
  24-lobe crimped spline, r 29 mm: 0.7 mm crimp amplitude took 1.3 mm, 0.5 mm
  amplitude took 2.0 mm.
- **Fillet only what is new.** Rounded relief keeps flat-top edges at the
  same height, so a second fillet selected by height re-selects them and
  fails. Key the top edges (plan bounding box) before the emboss and fillet
  the ones that appeared.
- **Measure limits with a spike, not by patching.** When a fillet, taper or
  boolean refuses twice, run one probe in an empty document that tries the
  candidate values under `try`/`except` and reports which pass, then undo it.
  A spike is a probe, not a part build: it carries no stub, does not count
  against the execute cap, and catching the failures is its whole purpose.
