# What we learned: fidget spinners and print-in-place design

Consolidated from one session: 4 research agents, a 30-design mesh teardown of the
MakerWorld leaderboard, 2 rounds of multi-agent design, and 10 spinners built and
verified in Fusion (Pentaroule 60, Counterfeit Comet, two bearingless PiP variants,
Vernier Contra-Ring, Governor, Supernova 72 rev A/B, Cicada 75, Pulsar Bloom 78,
HAYWIRE GEARWORKS 76).

**Standing caveat: none of this has been printed.** Everything below is either
measured from other people's shipped meshes, taken from sourced research, or
verified analytically in CAD. The coupon prints are the missing step.

---

## 1. Spinner physics

- `I = Σmr²`. Rim-weighting is the whole game. Spin decays roughly exponentially,
  so doubling flick speed buys about one time constant — inertia and low friction
  beat effort.
- **Rim ratio** (`I / 0.5mR²`) is the diagnostic. Measured across the corpus:
  nested rings 1.65–1.7 (the ideal), gear designs 1.0–1.2, novelty sculpture
  0.45–0.7 (feels dead in the hand). A uniform disc puts 36% of its volume beyond
  0.8R; the corpus flywheel benchmark hits 50.7% via an 11.3 mm deep rim.
- **Mass cancels.** A part slides outward when `ω²r > µg` — independent of its
  mass. So a centrifugal mechanism cannot be improved by making it heavier; only
  friction and rest-radius matter. This is counter-intuitive and it killed one
  design assumption outright.
- **The force budget is brutal.** A 0.62 g roller at 3 rev/s and r = 15 mm
  generates **3.3 mN**. Any weld, tack or detent is measured in newtons. Compute
  this number *before* drawing a centrifugal mechanism.
- Bearings: R188 (12.7 mm OD) beats 608 (22 mm OD) on mass budget; run open and
  dry, since lubricant costs 30–70% of spin time.

## 2. What the market actually rewards

The leaderboard formula, measured rather than guessed: *a flat, rim-weighted,
rotationally symmetric print-in-place mechanism, 40–90 mm, that photographs as
motion.*

- **Zero hardware is the #1 shared trait** — 29 of 30 top designs need no bearing.
- Two families own the chart: planetary gear trains (9) and nested gyro rings (7).
- Variant breadth (ring counts, sizes, textures, clearance profiles) feeds the
  ranking flywheel.

The tension worth naming: **a real bearing wins on physics, zero hardware wins on
popularity.** Our steel-nut and 608 designs out-spin anything printed, and are
also the least likely to chart.

## 3. Print-in-place: the rules that matter

**The structural fact everything else follows from:** an unanchored floating first
layer cannot be printed. Bridging is only reliable *between two anchors*. A free
part must therefore be one of:

1. **plate-referenced** — a pilot stub reaching the build plate through a
   through-slot, so its first layer is a solid disc on glass;
2. **mesh-captured** — a gear trapped between sun and ring;
3. **tacked** — accepted break-away, freed once by hand.

**The distinction that decides which:**

| | Rotate in place (gears) | Move under low force (rollers, sliders) |
|---|---|---|
| Freed by | a human, high torque, once | its own ~3 mN, every single use |
| Tack acceptable? | yes | **never** |
| Vertical gap | 1× layer height | 2× layer height + plate reference |

Getting this wrong is invisible in CAD and fatal on the printer.

**Other hard rules:**

- **Gaps must be integer multiples of layer height.** Slicers quantise on a global
  Z grid; a 0.3 mm gap at 0.2 mm layers lands on 0.2 (fused) or 0.4 (free)
  non-deterministically.
- **Once contact is unavoidable, contact *area* is the lever, not gap size.**
  Printed ball bearings run at 0.064 mm clearance because the contact is a point.
- Clearance is not one number — it depends on contact type. Measured from shipped
  designs: gear flanks 0.09–0.15, flat nested rings 0.15, heavy gimbal rings
  0.375, contact-lobe cams 0.02–0.06.
- Ship clearance as a **named parameter with variants** (the G-Man moat).
  Machine-specific calibration is not optional.
- Every overhang ≤45°. Short bridges anchored at both ends are fine; flat
  unsupported ceilings and floating islands are not.

## 4. Verified primitives (reuse these)

- **45° diamond journal** — column radius R, ridge 1.2 mm deep at mid-height, 45°
  flanks, 8–9 mm stack, 0.3 mm anti-fuse chamfers on both bottom gap edges.
  *Offset the female side 0.354 mm radially, not 0.25* — see §5.
- **Plate-referenced pilot stub** — through-slot between two rails, stub reaching
  z0, 45° cone seating on the rail edges as a self-centring V.
- **Module-1.0 planetary** — `N_ring = N_sun + 2·N_planet`, and `N_ring` divisible
  by the planet count so every station meshes in phase.
- **Bisection balance loop** — drive a hidden void/mass position parameter, measure
  CoM each recompute, bisect. Converges in ~5 recomputes to <0.05 mm. Newton on an
  analytic mass model oscillates; bisection is overlap-proof.
- **Symmetry-matched engraving** — ornament whose fold count equals the body's own
  symmetry is balance-neutral by construction.

## 5. Measurement beats looking — every single defect proves it

Not one real defect this session was visible in a render. All were caught by
analytic checks:

- **Risers driven straight through internal gear teeth.** Internal teeth point
  *inward* — the tip radius is the innermost point. Cost two separate clashes.
- **Pucks grazing tooth tips** by 0.41 mm³.
- **A join extrude that added zero volume and silently no-oped**, because its start
  extent left a gap to the target.
- **Rollers jammed into the ceiling** only when all parameters were stepped
  together — clearance stacks must be *derived*, not literal. Stepping one
  parameter at a time showed nothing.
- **A "0.25 mm" journal clearance that is really 0.177 mm**, because a radial
  offset on a 45° flank is `0.25·cos45°`. Affects every journal we built.

Two habits fall out of this: audit overhangs by sampling face normals (flag
`nz < −0.7075`), and check a volume delta on every feature rather than trusting
that `add()` returned.

## 6. The two design lessons

**Build novelty out of verified-robust primitives.** The judges' recurring finding
was an inverse correlation between novelty and print reliability — the exciting
designs all rode on a clearance that had to be right first try. The escape is not
to be less ambitious, it is to make the *ambitious* part geometry and the
*mechanical* part boring.

**The illusion is cheaper than the mechanism.** HAYWIRE gets its reaction from a
shattered rim and fake stringing — all plain vertical extrusions with zero print
risk — while persistence of vision does the actual trick. Far better
wow-per-unit-risk than inventing a new joint.

## 7. Open items

- Planets in HAYWIRE float 0.40 mm above the carrier on a 116.8 mm² unanchored
  first layer: tack expected, twist to free. The corpus puts planets on the plate;
  we should too.
- The 0.177 mm flank clearance applies to every journal built this session.
- HAYWIRE's tightest mesh point measures 0.084 mm against a 0.12 mm design intent.
- **Nothing has been printed.** Coupon first: journal pair + one moving element.
