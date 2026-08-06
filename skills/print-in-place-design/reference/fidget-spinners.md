# Fidget spinners: the domain layer

Read this on top of the parent skill, which carries the print-in-place mechanics.
Numbers here come from a teardown of 30 top-ranked MakerWorld designs plus sourced
research; see `docs/fidget-spinner-research.md` and
`docs/fidget-spinner-competitor-scan.md` in this repo for the full workings.

## Physics that changes decisions

- `I = Σmr²`. Rim-weighting is the whole game. Spin decays roughly exponentially,
  so doubling flick speed buys about one time constant — inertia and low friction
  beat effort.
- **Rim ratio** (`I / 0.5mR²`) is the diagnostic number:

  | Design class | Rim ratio |
  |---|---|
  | Nested rings (the ideal) | 1.65–1.70 |
  | Gear/planetary designs | 1.0–1.2 |
  | Novelty sculpture — feels dead | 0.45–0.70 |

  A uniform disc puts 36% of its volume beyond 0.8R. The corpus flywheel
  benchmark reaches 50.7% via an 11.3 mm deep rim.
- Size and mass: 40–90 mm diameter, 14–15 mm tall, 40–70 g. Above ~90 mm it stops
  being pocketable and becomes a desk toy — which is a valid choice, but say so.
- Bearings: R188 (12.7 mm OD) beats 608 (22 mm OD) on mass budget because the
  smaller race leaves more of the mass at the rim. Run open and dry — lubricant
  costs 30–70% of spin time in a steel bearing. (Note the opposite is true of a
  *printed* journal, where lubricant helps.)

## What the market rewards

The measured formula: **a flat, rim-weighted, rotationally symmetric
print-in-place mechanism, 40–90 mm, that photographs as motion.**

- Zero hardware is the single strongest shared trait — 29 of the top 30 need no
  bearing at all.
- Two families dominate: planetary gear trains (9 of 30) and nested gyro rings
  (7 of 30).
- Variant breadth — ring counts, sizes, textures, clearance profiles — feeds the
  ranking flywheel. Ship a ladder, not one file.

**The tension to name out loud:** a real steel bearing wins on physics; zero
hardware wins on popularity. A 608-and-steel-nuts design will out-spin anything
printed and is also the least likely to chart. That is a positioning decision,
not an engineering one — make it deliberately.

## Corpus reference numbers

- Planetary: ring 72T / sun 36T / 6 planets 18T at module 1.0, centre distance
  27.2 mm. Another proven train: ring 54T / 3 planets 18T / sun 18T at module 1.2,
  centre distance 21.60 mm, tooth whole depth 2.72 mm.
- Flat nested rings: radial pitch exactly 3.5 mm = 2.95 mm wall + 0.15 mm gap.
- Finger interfaces: hub bore ⌀18.5 with a hex boss 21.4 across flats; knurled
  buttons ⌀20 with 24 splines.

## Design lessons

**Novelty and print reliability are inversely correlated** — every judging round
found it. The exciting designs all rode on a clearance that had to be right first
try. The escape is not to be less ambitious: make the *ambitious* part pure
geometry and the *mechanical* part boring, built from the verified primitives.

**The illusion is cheaper than the mechanism.** The strongest reaction in this
project came from a rim shattered into five chunks held by what reads as extruder
stringing — all plain vertical extrusions with essentially zero print risk — where
persistence of vision fuses the chunks into a solid ring at speed. Far better
astonishment-per-unit-risk than inventing a new joint.

**A design that "looks broken" is a listing hazard.** Lead the cover image with the
transformation or the spinning state, and name the deliberate defect in the
description, or it gets reported as a failed model.
