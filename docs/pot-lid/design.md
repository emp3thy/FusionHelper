# Pot lid rebuild: design note

Date: 2026-10-04. Script: `artifacts/pot-lid/pot_lid_author.py`.

## Why this exists

The lid's authoring script was written in a Remote Control Claude Code
session on a PC that a BIOS update later bricked. The script, its
`feature/potlid` branch and the session transcript all lived on that machine
and were never pushed; GitHub has no trace of the branch, teleporting the
session returns a stub, and the cloud copy of the transcript is empty. What
survived is the printer's `pot_lid.gcode.3mf` and the "Pot Lid Relief
Options" artifact of 2026-09-13.

Lesson recorded in memory: every CAD authoring script is committed and
pushed in the session that writes it.

## What the gcode gave us

The lid is a solid of revolution, so the gcode is a complete description of
the printed geometry. `gcode_section.py` reads every extrusion move, takes
its distance from the plate centre (from `plate_1.json`'s bbox), and keeps
the slicer's feature label. Outer-wall centrelines sit 0.21 mm (half the
0.42 mm line) inside the true surface; top skins sit 0.08 mm (half a layer)
below it.

Reading the wall loops layer by layer:

| Feature | Measured | Parameter |
|---|---|---|
| Central plug, outer face | outer wall at r 27.09 at every layer 0.2 to 6.9 | `PLUG_R = 27.30` |
| Groove outer face at base | outer wall 32.45 at z 0.52, 31.84 at 3.08, 30.93 at 6.92 | `GROOVE_R0 = 32.36`, slope 0.2375 |
| Groove ceiling | bridge over r 26.2 to 31.6 at z 7.08 | `GROOVE_DEPTH = 7.00` |
| Collar outer face | 36.44 at z 0.52, 35.83 at 3.08, 34.92 at 6.92, 34.65 at 8.04 | `COLLAR_R0 = 36.77`, same slope |
| Draft | both faces slope 0.2375 mm per mm | `DRAFT_DEG = 13.4` |
| Outer plateau | top skin at z 10.76 from r 23.0 to 30.9 | `LID_H = 10.84` |
| Hairline beads | bumps peaking z 11.4 centred r 27.0, 29.5, 30.75, each about 1.2 wide | `BEAD_CENTRES`, `BEAD_R = 0.6` |
| Raised disc side | outer wall 23.36 at z 11.08 to 22.47 at 12.84 | `DISC_R = 23.70`, `DISC_TOP_R = 22.60`, `DISC_TOP_Z = 12.92` |
| Ring bead | peak z 13.96 at r 20.0, base 18.5 to 21.5 at z 12.92 | `RING_R = 20.0`, `RING_BEAD_R = 1.6`, `RING_PEAK_Z = 14.04` |
| Inner dish | top skin steps 12.92 at r 17 down to 12.44 at r 10 | `SHELF_IN_R`, `DISH_R`, `DISH_Z` |
| Boss ring | flat top at z 13.24 from r 6.9 to 9.6, side 9.97 to 9.75 | `BOSS_*` |
| Two small rings | peaks 13.40 at r 5.85 and 13.56 at r 4.5, valleys 12.92 at 5.2 and 6.5 | `MICRO_RINGS` |
| Centre dimple | floor z 11.64 at r 0, rim r 4.5 at z 13.56; sphere fit R 6.2 | `DIMPLE_*` |

The artifact's numbers agree where they overlap: Ø73.5 at the collar base
(measured 73.54), relief on the top face, R2.5 rounded edge (adopted; see
assumptions).

## How it is built

One sketch on the XZ plane, placed through `modelToSketchSpace` (R6), drawn
as chained lines and three-point arcs from the parameter table, fixed as art
(curves and points), revolved 360° about Z as a new body. The script
computes the Pappus volume of the same profile and raises if Fusion's body
volume differs by more than 0.5 %; it also checks the bounding box against
the table. No user parameters are created: nothing would bind to them and
liveness would rightly flag them dead. Editing means changing the table and
re-running, which is how the lost script worked ("one profile in profile.py,
revolved in Fusion, volume checked by Pappus").

`check_profile.py` runs the same profile code offline, checks it is a
simple closed polygon, and measures the printed walls against it.

## Results

| Check | Result |
|---|---|
| Preflight gate | PASS, lint 0 errors 0 warnings |
| Fusion execute | 1 of 1, green |
| Volume | Fusion 41.2919 cm³, Pappus 41.2914 cm³, 0.001 % |
| Bounding box | 73.54 × 73.54 × 14.04 mm (gcode max z 13.96 + half layer) |
| Printed outer walls vs profile | n 587, mean 0.16 mm, p95 0.42 mm, max 0.72 mm |
| Printed top skin vs profile | n 2262, mean 0.18 mm, p95 0.80 mm, max 0.86 mm |

## Assumptions

One per line: what the design rests on, its status, and what it costs if
wrong.

- **The printed lid fitted the pot.** Unverified. The rebuild copies the
  printed fit surfaces exactly; if the print was loose or tight, the same
  correction is needed in `PLUG_R` / `GROOVE_R0`. Cost if wrong: one reprint
  after measuring the pot rim.
- **The lid is a true solid of revolution.** Verified from the gcode: every
  wall loop is a circle about one centre and no feature varies with angle.
  Cost if wrong: none observed.
- **Half-line-width surface offset of 0.21 mm.** Measured from the slicer
  config (`outer_wall_line_width = 0.42`). Cost if wrong: a 0.1 mm bias on
  every diameter.
- **Collar draft is the same on both faces, 13.4°.** Measured: both faces
  slope 0.2375 mm per mm across z 0.5 to 6.9 within 0.02 mm. Cost if wrong:
  groove width error of about 0.1 mm per degree.
- **Top outer edge is an R2.5 fillet tangent to side and plateau.** Taken
  from the artifact. The print is fuller: its skin at r 31 to 33 sits 0.8 mm
  below this fillet, and a circle fit through the printed edge gives R 3.0 to
  3.5. Cosmetic only; the plateau and fit surfaces are unaffected. Cost if
  wrong: 0.8 mm of edge shape. Set `EDGE_R` to 3.2 to match the print
  instead of the artifact.
- **Three hairline beads, not two.** The artifact says two beads of 0.8 mm;
  the gcode shows three bumps 0.5 to 0.6 mm high at r 27.0, 29.5 and 30.75.
  The gcode is the part that printed, so three were kept. Cost if wrong: a
  cosmetic ring.
- **Bead and ring profiles are circular arcs.** Inferred from layer
  stepping; the ring bead's chord widths at three heights fit R 1.56 to
  1.67. Cost if wrong: under 0.2 mm on the relief.
- **The inner dish is a straight slope from r 17 to r 10.** The skin steps
  12.92, 12.76, 12.60, 12.44 at 0.16 mm layers, consistent with a plane cone;
  a gentle curve would fit equally well. Cost if wrong: under 0.2 mm.
- **Centre dimple is spherical, R 6.2.** Fitted to five skin heights within
  0.2 mm. Cost if wrong: under 0.2 mm at the rim.
- **No user parameters is acceptable for this part.** Decision, matching the
  lost script's method. Cost: parameter edits need a re-run rather than a
  Fusion parameter change.
