# Fidget spinner programme — handoff

Written 2026-08-06, at the end of a long session that ran research → design →
build → print → redesign. This file is the entry point for whoever picks the
work up. Read this first, then the linked documents as needed.

## 1. Where everything lives

| What | Path | Committed? |
|---|---|---|
| Build scripts (61 files) | `artifacts/spinner-scripts/` | yes |
| Exported Fusion archives (10 `.f3d`) | `artifacts/spinners/` | no — gitignored, ~12 MB |
| Research corpus and judging | `docs/fidget-spinner-research.md` | yes |
| Competitor teardown (30 downloads) | `docs/fidget-spinner-competitor-scan.md` | yes |
| Consolidated design lessons | `docs/fidget-spinner-lessons.md` | yes |
| Flagship spec + judge verdicts | `docs/supernova-72-spec.md` | yes |
| Print-in-place skill | `skills/print-in-place-design/` | yes |
| Fusion scripting discipline | `skills/fusion-design/` | yes |

The build scripts were copied out of a session scratchpad that no longer
exists. They are the only way to rebuild any design, so treat
`artifacts/spinner-scripts/` as source, not as a dump.

## 2. State of the Fusion documents

**Cloud `saveAs` does not work in this install.** `Document.saveAs(name,
folder, desc, tag)` returns `True`, renames the document to `<name> v0`, and
then never registers a `DataFile`. Afterwards `doc.isSaved` is still `False`,
`doc.dataFile` raises `3 : Failed to get temporary file`, and the project
folder listing is unchanged. Do not trust its return value.

The working substitute, which was used here and did work, is a local archive
export:

```python
em = design.exportManager
opts = em.createFusionArchiveExportOptions(r"C:\...\name.f3d")
em.execute(opts)
```

Ten documents were exported that way. Only one of them — `supernova` v1, the
printed rev B — is also genuinely saved in the cloud.

| Archive | Bodies | Notes |
|---|---|---|
| `supernova-72-revB-PRINTED.f3d` | 8 | **the only design physically printed** |
| `supernova-72-revC.f3d` | 8 | twin V-ways, first attempt |
| `supernova-72-revD.f3d` | 8 | twin V-ways, open-top slots, packaged as one component |
| `cicada-75` | — | *not exported; document was already closed* |
| `pulsar-bloom-78.f3d` | 6 | |
| `haywire-gearworks-76.f3d` | 7 | |
| `orrery-mk1-7body.f3d` | 7 | |
| `orrery-mk1-12body.f3d` | 12 | |
| `orrery-mk1-12body-grouped.f3d` | 12 | component `orrery_90` |
| `orrery-mk2-sun-ring.f3d` | 13 | sun + planets + ring, inner mesh only |
| `orrery-mk3-double-mesh.f3d` | 13 | rev 1 — mid-band retention, 8.43 mm³ interference |
| `orrery-mk3-double-mesh-rev2.f3d` | 13 | end-flange retention, interference PASS (2026-08-06) |
| `orrery-mk3-rev3-component-decor.f3d` | 13 | rev 2 + raised top decor, component `orrery_mk3_90` — **PRINTED; gears fell out, see 2b** |
| `orrery-mk3-rev4-square-retention.f3d` | 13 | **current** — lip-and-groove square retention |

Five earlier designs (Pentaroule, Comet, both print-in-place variants, Vernier,
Governor) were lost by closing their documents unsaved before archives were
being taken. Their author scripts survive in `artifacts/spinner-scripts/` and
each rebuilds in about two minutes.

Body-name prefixes identify a document when the title does not: `sn2_` rev B,
`sn3_` rev C/D, `ci_` Cicada, `pb_` Pulsar, `hw_` Haywire, `or_` Orrery mk1,
`o2_` mk2, `o3_` mk3.

## 2b. Orrery mk3 rev 3 — PRINTED, and what it taught (2026-08-07)

The user printed rev 3. It came off the plate well and the gears meshed and
turned. **Then every planet fell out** the first time it was held horizontally
and spun — the outer stage first, the inner stage the same way.

The cause was not clearance and not the mesh. Every retention face in rev 3
was a **45° ramp**, and a 45° face has a camming ratio of 1.0: axial load
converts one-for-one into radial load, so the flange was actively driven out
of its own capture. With 0.75 mm of axial float and a 0.6 mm flange, gravity
plus gyroscopic wobble was enough.

**Rev 4 replaces it with lip-and-groove and square shoulders** — see section 4.
The lesson is now in `skills/print-in-place-design/SKILL.md` as PRINT-PROVEN:
*ramps are for entry, never for holding.*

## 3. The one piece of empirical data

Everything else in this programme is simulation. The user printed **Supernova
72 rev B** and reported:

- Plate-referenced rollers came out **free and sliding**. The plate-reference
  technique is print-proven.
- The 45° diamond journal at **0.177 mm normal flank clearance** spins freely,
  and "really well" with WD40 silicone lubricant. That 0.177 comes from a
  0.25 mm *radial* offset on a 45° face (× cos 45°). It is a proven working
  value, not a defect to correct.
- Defect: the rollers **rattled**. They were located only by gravity on two
  rail edges, leaving roughly 1.1 mm vertical and 1.0 mm lateral play.

The rattle is what drove rev C/D and the twin V-way capture.

### V-way sizing (used in rev C/D and Orrery)

With wall-to-part gap `g`, ridge protrusion `p` and groove depth `d`, the two
flank lines separate by `d − (p − g)`. That separation is the vertical play,
and play × cos 45° is the normal clearance. Worked example, as built:

    g 0.5, p 0.9, d 0.65  →  0.25 mm play, 0.177 mm normal, 0.4 mm engagement

Two V-ways are required, not one. A single mid-height capture stops the part
dropping and shifting but does not stop it **cocking**.

## 4. Orrery mk3 retention — rev 4, square shoulders (2026-08-07)

Rev 4 is the answer to the rev 3 print failure in section 2b. Retention is now
**lip-and-groove with square blocking faces**, sized off the planet flange:

| | value |
|---|---|
| Planet flange | tip + 1.0 mm, 1.2 mm tall, **square both faces** |
| Gear lip | overlaps the flange by 0.5 mm, 1.0 mm tall, z 1.5–2.5 and 12.0–13.0 |
| Groove | flange + 0.2 mm radial |
| Axial float | 0.3 mm per end (was 0.75 mm) |
| Entry ramp | 45.6–48.0°, self-supporting, measured per gear |
| Tip band | z 5.0–9.5 mm |

Measured radii (mm): sun groove 7.80 / lip 8.50; ring-int groove 22.20 /
lip 21.50; ring-ext groove 25.30 / lip 26.00; housing groove 39.70 /
lip 39.00. Every lip lands **inside its own gear's root circle**, so the
tooth-space cut never crosses it and each lip is one uninterrupted annulus.

Retention verified by an axial **lift test** — translate a planet and re-run
the interference check:

| offset | inner planet vs sun+ring | outer planet vs ring+housing |
|---|---|---|
| rest | 0.000 mm³ | 0.000 mm³ |
| ±0.2 mm (inside float) | 0.000 mm³ | 0.000 mm³ |
| ±0.4 mm (past float) | 0.340 mm³ | 0.347 mm³ |

Free to float, blocked beyond it, symmetric in both directions and on both
stages. Overhang sweep: **14 faces**, exactly the designed shoulders (four
0.7 mm gear-lip ledges at z1.5, ten 1.0 mm planet-flange ledges at z13.3) —
down from 100 in rev 3. Archive: `orrery-mk3-rev4-square-retention.f3d`.

## 4b. Rev 2/3 retention — historical (RESOLVED 2026-08-06)

> **Status update.** The section 4 rebuild below was executed and it worked,
> with one major addition. The "~8.43 mm³ mesh interference" was NOT the
> retention recess and NOT the involute math: the tooth-space cut polygon
> closed the space mouth with a straight chord between the two tip points,
> leaving an uncut crescent inside the tip circle (sagitta up to 0.29 mm on
> the 10T planets) that the mating tooth sweeps through. A 2D offline replica
> of the exact polygon measured 1.22 mm² of overlap per mesh (≈ the 8–9 mm³);
> the continuous involute showed zero. Fix in `space()`: external gears close
> the mouth at tip + 0.8 mm so the chord lies outside the material. Internal
> gears need nothing. Additionally the mesh moved to 25° pressure angle,
> 0.20 mm backlash, tips shortened (sun 10.95, ring-int 19.25, ring-ext
> 28.40, housing 36.70) to clear line-of-action tip-interference limits for
> the 10T planets (margins 0.10–0.19 mm, contact ratios 1.31–1.43, planet
> tip land ~0.16 mm). Result: interference check PASS across all 20 pairs,
> overhang sweep clean except 100 accepted ≤1.8 mm both-end-anchored bridges
> (top-flange fill over tooth spaces at z12.7, ≥0.75 mm clear air below —
> same feature the commercial reference ships). Archive:
> `orrery-mk3-double-mesh-rev2.f3d`. Cloud doc NOT saved (R10).

### Original problem statement (historical)

mk3 is a five-stage coaxial train where every stage stands on the build plate:

    housing (75T internal, the part you hold)
      → 5 outer planets (10T)
        → ring: 55T external / 40T internal   ← the flywheel
          → 5 inner planets (10T)
            → sun (20T, a free idler)

Module 1.0, backlash 0.035 cm, Ø90 × 14.5 mm. Stations: inner planets 15,
outer planets 32.5.

| Gear | N | rp | tip | root |
|---|---|---|---|---|
| sun | 20 | 10 | 11 | 8.75 |
| inner planet | 10 | 5 | 6 | 3.75 |
| ring internal | 40 | 20 | 19 | 21.25 |
| ring external | 55 | 27.5 | 28.5 | 26.25 |
| outer planet | 10 | 5 | 6 | 3.75 |
| housing internal | 75 | 37.5 | 36.5 | 38.75 |

Both stages satisfy the assembly condition ((20+40)/5 = 12, (55+75)/5 = 26)
and the circular-pattern phase condition (deficits 4.00 and 11.00 planet
pitches). Letting the sun float is what makes the whole thing printable: a
fixed sun would need a bridge to the housing, and any such bridge has to cross
the rotating ring.

### What is wrong

Two defects, probably the same defect:

1. **~8.43 mm³ of per-planet mesh interference** that survived three separate
   fixes (tooth phase, backlash, 3 → 5 flank samples).
2. **Visible rail artefacts** in the tooth band.

The current retention is a mid-height bulge sitting in a mid-height recess.
The recess is 5.4 mm tall for a 1 mm bulge, so it gives about 2 mm of axial
float — and because it is cut at mid height it **cuts across the tooth band**.
That is the rail artefact, and it is very likely a chunk of the 8.43 mm³ as
well. The interference may not be an involute problem at all.

### The discovery that unblocks it

A recess only needs to clear the mating flange by **0.55 mm when measured
from the tooth ROOT**, not from the tip. Sizing recesses from the tip is what
produced 2.8 mm-deep grooves, which forced 5.4 mm-tall ramps, which is why the
recess had to invade the tooth band. **That single error is behind most of the
geometry that was being fought.**

### Reference: how a working commercial design does it

Measured from `C:\Users\gethi\Downloads\Gear+fidget+spinner.3mf` (Ø58 × 12 mm).
Innermost radius of the outer housing against height:

| Height (mm) | Inner radius | Feature |
|---|---|---|
| 0 – 0.5 | 24.0 | lip |
| 0.5 – 1.5 | 27.5 – 28.0 | groove behind the lip |
| 1.5 – 2.75 | 28 → 24 | ramp |
| 3.75 – 4.25 | 23.33 | teeth |
| 5.25 – 6.25 | 24.1 – 24.3 | smooth band |
| 7.75 – 8.25 | 23.33 | teeth |
| 10.5 – 12 | mirrors the bottom | groove, then lip |

The centre bore mirrors the same scheme: 3.00 at z0.25, 2.00 at z0.75–1.25,
6.8 through the gear zone. The ramp out of the groove is about 62° from
horizontal, so it is self-supporting. **Every body is full height, z0 to z12.
There are no caps.** Teeth are split into a top band and a bottom band with a
smooth band between them — retention lives at the *ends*, never in the middle.

### The rebuild the user authorised

This was agreed but deliberately not started, because it changes the mesh and
wanted a clean run:

1. Delete `BAND` / `RECESS` mid-height retention from `or3_build.py`.
2. Add per-stage **end flanges**: rotating part at tip + 0.6 mm, over z0–1.2
   and z13.3–14.5.
3. Make recesses **root-referenced** — 0.55 mm beyond the mating gear's root.
4. Add **45° tooth-entry chamfers**. An end flange forces its neighbour to be
   recessed at that height, which leaves tooth tips with nothing under their
   first layer. The corpus forensics independently found the same thing:
   "teeth full height with ~3 mm chamfered entry at both faces".
5. That shortens the tooth band from ~11 mm to about z4.0–10.5, so re-measure
   the mesh afterwards. Expect the 8.43 mm³ to move or clear.

## 5. How to resume, concretely

```
cd C:\Users\gethi\source\fusionhelper
python -m fusionhelper.bundle artifacts\spinner-scripts\or3_build.py
python -m fusionhelper.preflight artifacts\spinner-scripts\or3_build.bundled.py   # must exit 0
```

Then open a new empty Fusion document and run a loader script through MCP —
never paste a 700-line script through the tool:

```python
ARTIFACT = r"C:\Users\gethi\source\fusionhelper\artifacts\spinner-scripts\or3_build.bundled.py"


def run(_context: str):
    with open(ARTIFACT, encoding="utf-8") as f:
        src = f.read()
    ns = {"__name__": "fh_bundled"}
    exec(compile(src, ARTIFACT, "exec"), ns)
    ns["run"](_context)
```

Afterwards, run the overhang sweep and the interference check, then export an
archive before doing anything else.

Overhang sweep — flag any face whose downward normal is steeper than 45°:

```python
prange = f.evaluator.parametricRange()          # returns the range DIRECTLY
res = f.evaluator.getNormalsAtParameters(pts)   # pts is a plain LIST
normals = res[1]                                # [ok, [Vector3D, ...]]
# flag normal.z < -0.7075 ; skip faces lying on z = 0
```

## 6. Gotchas that will bite

- **A timed-out MCP request re-runs.** Fusion completes the script *and* the
  killed client's request is retried, duplicating geometry. Every build script
  here is therefore **idempotent** — each stage checks committed volume first
  and skips. Keep it that way; a re-entry should be a clean no-op.
- **Build gears as a cylinder at the tip radius, one tooth-space cut, then a
  circular pattern ×N.** About ten API calls instead of four hundred. Drawing a
  full outline is what blew the timeout in the first place. Stator build time
  went from repeated timeouts to 0.1 s.
- **The cut start plane matters as much as the depth.** A tooth space sketched
  on z0 and cut upward perforated the base disc *and* left the ring wall solid
  above the cut.
- **Internal gear teeth point inward.** Anything outboard of the tip radius
  inside the tooth z-band collides. This caused two separate clashes.
- **A JOIN extrude whose start extent leaves a gap adds zero volume and
  silently no-ops.** Check the volume delta on every feature.
- **Backlash has a ceiling.** 0.6 mm made 10-tooth planets pointed (negative
  tip land), so the retention bulge had nothing to join to. Max ≈ 0.52 mm;
  0.35 mm was used.
- **Circular-pattern phase condition.** A rigid pattern rotates each planet by
  θ, but correct mesh needs θ·(Ns+Np)/Np; the deficit must be a whole number of
  planet pitches. 4, 5 and 10 planets work; 6, 7 and 8 clash.
- **`constructionAxes.add` raises "Environment is not supported".** Build the
  planet at the origin, pattern its teeth about Z, then translate it out with
  `moveFeatures.createInput2` + `defineAsTranslateXYZ`.
- **When scaling the 45° journal recipe, dr and dz must scale together.** Mini
  diamond stubs came out at 37° because only one was scaled.
- **New Fusion docs can be "Part Design" type — `occurrences.addNewComponent`
  raises "Part Design documents can only contain one component".** A doc
  created via `app.documents.add(FusionDesignDocumentType)` allowed
  components; a pre-existing Untitled did not. Probe with a throwaway
  `addNewComponent` + `deleteMe` before building anything that groups
  bodies into a component.
- **Sketch cost is superlinear and deletion is pathological.** ~300-line
  sketches solve in seconds; one 2680-line decor sketch ground the UI for
  70+ minutes, and deleting a ~1200-curve fixed sketch took ~20 minutes.
  Chunk art sketches to ≤300 lines, set `isComputeDeferred` while adding,
  and on re-entry RESUME drawing at the first undrawn polygon — never
  delete-and-redraw. Guard each stage on its JOIN feature, not its sketch.
- **Sketches and features share one name namespace.** An extrude named
  like its sketch silently becomes "name (1)" and `itemByName` guards
  miss it. Suffix join features `_join`.
- **Extruding all profiles of a curl-strip sketch fills the curl eyes**
  (each enclosed region is its own profile — reads as solid blobs).
  Filter profiles by area against the polygon's shoelace area; a
  centroid-in-polygon test fails because a C-strip's centroid lies in
  its own eye.
- **Orphaned timed-out MCP requests run later in whatever document is
  active at that moment.** After any timeout, re-probe the active doc's
  identity before trusting state; a "vanished" build had been completed
  by an orphan while a different doc was in front.
- **A rotor hub or carrier tier that starts above a stator base is a
  free-floating island** — 1101 mm² unanchored, found in Pulsar, Haywire and
  Orrery mk1 alike. The root cause is a *horizontal* rotating interface. mk2
  and mk3 fixed it by making the interface vertical, so everything stands on
  the plate.

`skills/fusion-design/SKILL.md` holds the standing rules R1–R11 and a section
on editing a committed model; `skills/print-in-place-design/SKILL.md` holds the
mechanism rules. Anything labelled PRINT-PROVEN there is backed by the rev B
print; everything else is analysis.

## 7. Standing constraints

- **R10: never save a Fusion document on your own judgement.** The exports in
  section 2 were made because the user explicitly asked for them.
- Keep the author → `bundle` → `preflight` (exit 0) → loader discipline. Do not
  execute an unbundled or ungated script.
- The verify block must emit `FH_CHECK1` / `FH_VERDICT1` JSON lines covering
  constraints, timeline, interference, clearance and liveness.

## 8. Still outstanding

1. ~~Rebuild Orrery mk3 retention per section 4~~ — DONE 2026-08-06, see
   section 4 status update.
2. ~~Re-measure the 8.43 mm³ interference~~ — DONE: root cause was the
   space-mouth chord crescent in `space()`, now fixed; interference PASS.
3. ~~Fold Orrery lessons into `skills/print-in-place-design/SKILL.md`~~ —
   DONE 2026-08-06: gear-as-patterned-tooth-space, cut start plane,
   idempotent stages, space-mouth crescent, line-of-action tip
   interference, end-of-band retention and decor-disjointness rules all
   landed in the skill (plus sketch-scale rules in `fusion-design`).
4. Optionally rebuild the five lost designs from their author scripts.
