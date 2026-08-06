---
name: print-in-place-design
description: Use when designing a 3D-printable mechanism that comes off the plate already moving — print-in-place joints, captive parts, gear trains, sliders, fidget toys. Supplies the clearance rules, the capture primitives, and the force-budget check that decide whether it frees itself or welds solid.
---

# print-in-place-design

Print-in-place mechanisms fail in one specific way: a part that was supposed to
move comes off the plate welded to its neighbour, and no amount of CAD review
predicts it. This skill carries the rules and the verified primitives that decide
that outcome. Use it alongside `fusion-design`, which governs how the script
itself is written.

Everything marked **PRINT-PROVEN** has been printed and confirmed. Everything
else is measured from shipped designs or sourced research — treat the difference
as real.

## The question that decides the design

**What force frees this part?** Ask it before drawing anything.

| | Rotates in place (gear, hinge, journal) | Must move under low force (roller, slider, loose mass) |
|---|---|---|
| Freed by | a human, once, high torque | its own inertia or gravity, every use |
| Break-away tack | acceptable, normal, expected | **fatal** |
| Vertical gap | 1× layer height | 2× layer height **and** plate-referenced |

Get this wrong and it is invisible in CAD. A centrifugal roller of 0.62 g at
3 rev/s and r = 15 mm generates **3.3 mN**. A 1 mm² weld is worth several newtons.
It can never free itself. **Compute the available force in newtons before you
rely on it.**

Corollary worth knowing: a part slides outward when `ω²r > µg` — **mass cancels**.
You cannot fix a sluggish centrifugal mechanism by making the mass heavier. Only
friction and rest-radius are levers.

## The structural fact everything follows from

**An unanchored floating first layer cannot be printed.** Bridging is only
reliable *between two anchors*; an island with no anchor droops 0.1–0.2 mm, lands
on whatever is below, and tacks. So a free part must be one of:

1. **Plate-referenced** — a pilot stub reaching z0 through a through-slot, so its
   first layer is a solid disc on glass. **PRINT-PROVEN**: rollers built this way
   came off free and slid without a break-in twist.
2. **Mesh-captured** — a gear trapped between sun and ring, or on a journal.
3. **Tacked** — accepted break-away, freed once by hand. Only legitimate for the
   rotate-in-place column above.

Note that the proven leaderboard planetaries put their planet gears **on the build
plate**, not floating above a carrier. Copy that.

## Clearances

**Gaps must be integer multiples of layer height.** Slicers quantise on a global
Z grid, so a 0.3 mm gap at 0.2 mm layers lands on 0.2 (fused) or 0.4 (free)
non-deterministically across re-slices.

Clearance is not one number — it depends on contact type. Measured from shipped
designs:

| Interface | Clearance |
|---|---|
| Gear flanks | 0.09–0.15 mm |
| Flat nested rings | 0.15 mm |
| 45° journal flanks | 0.177 mm normal — **PRINT-PROVEN** |
| Heavy gimbal rings | 0.375 mm |
| Contact-lobe cams (point contact) | 0.02–0.06 mm |

Once contact is unavoidable, **contact area is the lever, not gap size** —
printed ball bearings run at 0.064 mm because the contact is a point.

Ship clearance as a named parameter with variants (0.20 / 0.25 / 0.30). Machine
calibration is not optional: the same lab needed 2.5× the clearance on a
different printer.

**Lubricant is a legitimate shipped instruction**, not an admission of failure —
the top nested-ring and roller-bearing spinners both ship it. **PRINT-PROVEN**:
silicone lubricant took a working journal to "spins really well".

## Verified primitives

**45° diamond journal** — the workhorse rotating joint. Column radius R, ridge
1.2 mm deep at mid-height, 45° flanks, 8–9 mm stack, 0.3 mm anti-fuse chamfers on
both bottom gap edges.

> **Offset the female side 0.354 mm RADIALLY.** A radial offset on a 45° face is
> multiplied by cos45°, so a "0.25 mm" radial clearance is really 0.177 mm normal.
> 0.354 radial gives a true 0.25 normal. Both values work; know which you have.

**Plate-referenced pilot stub** — for a part that must translate. Through-slot
between two rails, stub reaching z0, 45° cone above it seating on the rail edges
as a self-centring V.

**Twin V-way capture** — stops a sliding part rattling. A 45° ridge along both
slot walls, matching circumferential V-grooves on the part, **at two heights**. A
single mid-height capture stops it dropping and shifting but not *cocking*, which
is most of what rattle is. Solve: with wall-to-part gap `g`, ridge protrusion `p`
and groove depth `d`, the flank lines separate by `d − (p − g)`; that separation
is the vertical play, and play·cos45° is the normal clearance. Worked example:
g 0.5, p 0.9, d 0.65 → 0.25 mm play, 0.177 mm normal, 0.4 mm engagement past the
surface so print variation cannot disengage it.

**Balance by bisection** — for an asymmetric body that must spin true. Drive a
hidden void or mass position parameter, measure centre of mass each recompute,
bisect. Converges in ~5 recomputes to under 0.05 mm. Newton on an analytic mass
model oscillates; bisection is overlap-proof.

## Gear trains (measured, Orrery mk1–mk3)

- **Build a gear as a cylinder at tip radius, ONE tooth-space cut, then a
  circular pattern ×N.** ~10 API calls instead of ~400; a full-outline
  stator went from repeated client timeouts to 0.1 s.
- **The cut start plane matters as much as the depth** — a tooth space
  sketched on z0 and cut upward perforated the base disc and left the wall
  above solid.
- **Close an external gear's space-cut polygon OUTSIDE the tip circle.** A
  straight chord between the two tip points leaves an uncut crescent inside
  the tip arc (sagitta 0.29 mm on 10T planets, 1.22 mm² per mesh) that the
  mating tooth sweeps through — measured as a systematic ~8–9 mm³ "mesh
  interference" that survived phase, backlash and flank-sample fixes.
  Internal gears need nothing (their mouth chord dips into air).
- **Check tip interference on the line of action for low tooth counts.** At
  20° pressure angle a 10T planet's root sits 0.95 mm below its base circle
  and every mating tip sweeps through that zone even with perfect
  involutes: require `sqrt(tip² − rb²) ≤ CD·sinα` per member (external) /
  ring-tip reach past the pinion tangent point (internal). Orrery fix: 25°
  pressure angle + shortened tips, margins 0.10–0.19 mm, contact ratios
  1.31–1.43.
- **Higher pressure angle sharpens low-count tips: re-check the tip land
  against backlash.** 0.35 mm backlash at 25° makes 10T planets pointed;
  0.20 mm keeps a ~0.16 mm land with 0.10 mm/side flank clearance.
- **Retention lives at the ENDS, never mid-band** (commercial reference:
  full-height bodies, no caps, teeth chamfered ~45° into end recesses).
  Size end recesses from the mating flange past the tooth ROOT (+0.55 mm),
  never from the tip — tip-referenced recesses force deep grooves that
  invade the tooth band.
- **Make build scripts idempotent, stage by stage.** A timed-out MCP client
  leaves the script running AND may retry it; every stage checks its
  committed output (body / join feature by name) and skips, so re-entry is
  a clean no-op.

## Raised decor (measured, Orrery mk3 rev 3)

- Decor fields must be full n-fold circular patterns (balance is free) and
  numerically confined to their own part's top face — validate stroke
  extents offline, plus swept-annulus clearance between neighbouring
  rotating parts.
- **Every polygon in a decor sketch must be pairwise DISJOINT and every
  spiral curl under one turn of self-facing.** Overlapping strokes formed a
  closed ring whose enclosed centre extruded as a solid plateau; touching
  whorls fill their eyes (each enclosed void is its own Fusion profile).
  With disjoint open strokes the sketch yields exactly one profile per
  polygon and no profile classification is needed.

## Geometry rules

- **Every overhang 45° or shallower.** Short bridges anchored at both ends are
  acceptable; flat unsupported ceilings and floating islands are not.
- **When you add a capture feature, re-examine what the old retention was for.**
  It is often now dead weight *and* the source of your worst overhangs. Removing
  a roof beats making a roof printable — deleting a redundant slot ceiling took
  one design from six illegal faces to zero.
- **Internal gear teeth point inward** — the tip radius is the *innermost* point.
  Anything radially outboard of it in the teeth's z-band collides. This caused two
  separate clashes in one build.
- Planetary trains: `N_ring = N_sun + 2·N_planet`, and `N_ring` divisible by the
  planet count so every station meshes in phase. Module 1.0–1.2; below 0.8 the
  teeth print badly.
- Balance is free if every feature array is a full n-fold circular pattern about
  the axis. Ornament that matches the body's own symmetry is balance-neutral by
  construction.

## Verify, do not look

Renders cannot show any of the failure modes above. Every real defect across ten
builds was caught by measurement:

1. **Interference check** every pair — it caught risers driven through gear teeth
   and pucks grazing tooth tips by 0.41 mm³.
2. **Overhang sweep** — sample face normals, flag `normal.z < -0.7075`, skip faces
   on z0.
3. **Minimum-distance probe** — confirm the interface you *intended* to locate the
   part is the tightest one in the model.
4. **Volume delta on every feature** — a join that no-ops returns success.

## Fidget spinners specifically

See `reference/fidget-spinners.md` for the domain layer: inertia and rim-ratio
targets, the measured leaderboard formula, bearing choice, and the corpus
teardown numbers.
