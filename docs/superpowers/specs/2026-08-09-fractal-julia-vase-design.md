# Fractal Julia Vase — "Douady Helix"

**Status:** design approved, spec under review
**Date:** 2026-08-09
**Envelope:** 135 × 135 × 300 mm FDM, 0.4 mm nozzle
**Deliverable:** a single generator script producing a slicer-ready 3MF

---

## Guardrails

Surfaced from better-memory before drafting, per the planning-retrieval standard.

| Guardrail | Confidence | Applies here |
|---|---|---|
| [[keep-docs-in-sync]] — website/README sync on every code change | 1.00 (22 uses) | The generator adds a new module. README "What ships" table and `docs/README.md` must be updated in the same PR, not deferred. |
| [[startup-knowledge-retrieval]] — `knowledge_list` + `memory_retrieve` at session start | 0.90 (48 uses) | Done. `standards/ralph-runtime.md` read before drafting. |
| [[planning-memory-retrieval]] — surface guardrails at top of plan | 0.90 (19 uses) | This section. |
| [[verify-before-commit]] (ralph-runtime standard) | standard | Every fractal constant in this spec was computed on this machine, not recalled. Scripts named in Appendix A. |
| [[confidence-scoring]] (ralph-runtime standard) | standard | Applies to the implementation plan, not this spec. Deferred to writing-plans. |

Dismissed as not applicable: ralph-queue dispatch boundary (no queue involved); PR bot-watch loop (applies at PR time, not now); Playwright/TypeScript/tempfile reflections (wrong stack).

---

## 1. Requirements

| # | Requirement | Source |
|---|---|---|
| R1 | Fits 135 × 135 × 300 mm build volume | user |
| R2 | Sculptural / dry-stem object. Not required to hold water. | user, 2026-08-09 |
| R3 | Fractal must be a genuine Julia set, not a fractal-flavoured pattern | user |
| R4 | Organic character — grown, not computed | user |
| R5 | Multi-wall print. Spiral vase mode explicitly dropped. | user, 2026-08-09 |
| R6 | Helical twist | user, 2026-08-09 |
| R7 | Zero supports | design constraint, carried from R2's print-quality goal |
| R8 | Mesh manifold and watertight before it reaches the slicer | FusionHelper house rule: errors impossible to express or impossible to miss |

Explicit non-goals: water retention; a Fusion 360 parametric body; resizability (cell sizes are tuned to extrusion width).

---

## 2. Verified mathematics

### 2.1 The set

`f(z) = z² + c`, **c = −0.123 + 0.745i** — the Douady rabbit.

| Quantity | Value | How verified |
|---|---|---|
| In Mandelbrot set | **yes** | critical orbit z₀ = 0 bounded to n = 20 000, R = 4 |
| area(K_c) / area(\|z\|<2) | **0.1039** | 800² grid, 3 000 iterations |
| Repelling fixed point α = (1+√(1−4c))/2 | 1.2765819495 − 0.4796660549i | closed form |
| Koenigs multiplier μ = 2α | 2.5531638989 − 0.9593321098i | closed form |
| \|μ\| | **2.7274464232** | |
| arg μ | **−0.3594214440 rad = −20.5933°** | |
| ln\|μ\| | 1.0033657954 | |

**Why this c and not a prettier one.** Four of the most-published Julia constants are outside the Mandelbrot set — their filled sets are Cantor dust with zero area and no printable interior. `c = −0.8 + 0.156i` ("spiral galaxy") escapes at n = 252; `c = 0.285 + 0.013i` at n = 542. A large escape index means the dust is finer than render resolution, so the set *photographs* as connected. Every candidate here was screened for membership **and** interior area before use.

**Why the rabbit over the fatter alternatives.** San Marco (`c = −0.75`, area 0.1675) and the basilica (`c = −1`, area 0.1124) are fatter, but both have **arg μ = 0** — no twist, which R6 rules out. Among connected, fat, twisting values the rabbit has the best area and the most legible three-lobe character (R4).

### 2.2 The coincidence that decides the proportions

```
|μ| = 2.7274464       e = 2.7182818       |μ|/e = 1.003371   (+0.337 %)
```

Salingaros's universal scaling factor for ornament hierarchy is *e*, with 2–4 the usable band. The rabbit's own Koenigs multiplier lands on it to within a third of a percent. **The scale ratio between successive ornament levels is not chosen — it is inherited from the dynamics.**

Scale ladder from the 116 mm silhouette, dividing by |μ|:

| Level | Size | Reads as |
|---|---|---|
| 0 | 116.000 mm | silhouette (3 m) |
| 1 | 42.531 mm | primary lobes (1 m) |
| 2 | 15.594 mm | secondary buds |
| 3 | 5.717 mm | surface relief (30 cm) |
| 4 | 2.096 mm | finest resolved detail |
| (5) | 0.769 mm | **below minimum ridge — iteration stops here** |

Five levels, ≈1.7 decades, matching the empirical span of natural fractals.

### 2.3 Mapping

> **Corrected 2026-08-09 after numerical prototyping.** An earlier draft of this
> section gave the map as `z = exp(k·h + iθ)`. That is wrong. Over the band it
> produces |z| from 2.2 to 123, while K_c lives inside |z| ≲ 1.5 — every sample
> escapes at iteration 1–2 and the vase comes out a smooth cone with no fractal
> on it. Koenigs linearisation describes the neighbourhood of **α**, so the map
> must be centred there. The corrected form is below and is numerically verified.

Self-similarity lives at the repelling fixed point: near α the set is asymptotically invariant under `ζ → μζ`, where `ζ = z − α`. Writing `ζ = e^{u+iv}`, that invariance is a **translation** `u → u + ln|μ|`, `v → v + arg μ`.

Mapping the vase's (θ, h) into those coordinates:

```
u(h) = ln(ζ_min) + k·(h − h_lo)
v(θ,h) = θ + (arg μ / ln|μ|)·k·(h − h_lo)
z(θ,h) = α + exp( u(h) + i·v(θ,h) )
```

with `ζ_min = 0.02`, `h_lo = 40 mm`, `k = 0.0200673 mm⁻¹`.

Rising by one period `Δh = ln|μ|/k = 50 mm` advances `u` by exactly `ln|μ|` **and** `v` by exactly `arg μ` — which *is* the Koenigs map. The pattern therefore reproduces itself once per period, rotated by arg μ. The twist is not decoration added afterwards; it is the second component of the same invariance.

`v` is 2π-periodic in θ, so **the seam cannot exist** — verified exactly, not approximately (see below).

The twist coefficient `(arg μ / ln|μ|)·k = arg μ / Δh = −0.0071884 rad/mm = −0.4119°/mm`, which reproduces the twist rate in §3.4 independently.

**Numerically verified** (`proto_field.py`, Nθ=256, Nz=200):

| Check | Result | Wanted |
|---|---|---|
| \|ζ\| range | 0.0200 → 1.1068 | = ζ_min × \|μ\|⁴ ✓ |
| Interior fraction of grid | **0.1057** | neither 0 nor 1 ✓ |
| Escaped ν spread | 0.227 → 79.118, σ = 3.751 | real structure ✓ |
| Self-similarity across one period | **r = 0.9866** | high; mis-rolled control 0.7792 ✓ |
| Seam ν(θ=0) vs ν(θ=2π) | **Δ = 0.00e+00** | exact ✓ |

### 2.3.1 Direction and normalisation

`u` increases with height, so **ζ moves away from α as the vase rises** — coarser structure at the top, finest near the foot. This is a free sign choice (`k → −k` inverts it) and should be settled from a render, not from theory. Exposed as a config flag.

ν is heavy-tailed (max 79 against σ 3.75), so normalise with a clamp rather than by the maximum:

```
ν̂ = clip(ν / ν_ref, 0, 1)        ν_ref = 12 (config)
ν̂ = 1 for interior points        (interior is solid → maximum radius)
```

Without the clamp a handful of slow-escaping samples would compress all the visible structure into the bottom few percent of the range.

Fractal band z = 40…240 mm (200 mm), **P = 4 periods**:

| Constant | Value |
|---|---|
| Period Δh | **50.0000 mm** |
| k | **0.0200673 mm⁻¹** |
| Twist per period | −20.5933° |
| **Total twist over the band** | **−82.37°** |

Slightly under a quarter turn over the full body — legible as a helix without reading as a novelty twisted vase.

### 2.4 Field

Smooth (renormalised) escape time, **not** integer iteration count — the integer count is a step function and produces terraces that beat against layer lines:

```
ν = n + 1 − log(log|z_n|) / log 2        escape radius R = 128,  N_max = 100
```

Normalise to ν̂ ∈ [0,1] over the band actually occupied, then:

```
r(θ, z) = r₀(z) + A(z) · tanh(1.6 · ν̂)
```

`tanh` compresses the gradient, which is what keeps the slope constraint satisfiable without clipping the field flat.

---

## 3. Form

### 3.1 Profile

Widest point at z = 185 mm = 0.617 H ≈ H/φ. Foot Ø is 0.233 H for tipping stability.

| z (mm) | Band | Ø (mm) | Relief A(z) | Wall |
|---|---|---|---|---|
| 0–40 | foot, solid | 70 → 80 | 0 | 2.0 mm wall, **3.0 mm floor** |
| 40–150 | belly, solid | 80 → 112 | 0 → **7.00** (peak at 130) → 6.44 | 2.0 mm |
| **150–225** | **pierced lattice** | 112 → **116** at 185 → 96 | 6.44 → 0.32 | 2.0 mm |
| 225–240 | shoulder, closes | 96 → 78 | 0.32 → 0 | 2.0 mm |
| 240–262 | neck | 78 → 58 | 0 | 2.0 mm |
| 262–300 | lip | 58 → 68 | 0 | 3.0 mm solid rim, ironed |

Relief runs over exactly the fractal band z = 40…240 defined in §2.3 — the two are the same interval by construction.

```
A(z) = 7.0 · (1 − cos(π(z−40)/90))  / 2      40 ≤ z ≤ 130     rise
A(z) = 7.0 · (1 + cos(π(z−130)/110)) / 2     130 < z ≤ 240    fall
A(z) = 0                                      otherwise
```

Raised cosine on both sides: zero-valued **and** zero-slope at z = 40 and z = 240, so relief emerges from and returns to the quiet zones with no visible start line. Sampled: A(150) = 6.44, **A(185) = 3.50**, A(225) = 0.32.

Note the peak sits at z = 130, *below* the widest point. At the widest point (185) relief has fallen to 3.5 mm and the **piercing takes over as the visual event**. Two different mechanisms carry the two zones rather than both competing at once.

**Quiet zones are load-bearing, not leftover.** Foot (0–40) and neck/lip (240–300) carry no relief at all. Figure needs ground; uniform all-over texture reads as noise regardless of how good the fractal is.

### 3.2 Three viewing distances

- **3 m — silhouette.** Must work as a black outline with zero texture. Foot 70, belly 116 at 0.617 H, throat 58, flared lip 68.
- **1 m — profile.** The 42.5 mm primary lobes and the −82° helix.
- **30 cm — texture.** 5.7 mm and 2.1 mm relief, and the pierced lattice.

### 3.3 Piercing

> **Rewritten 2026-08-09 after measuring the level sets.** The original rule
> was "punch through where ν̂ > 0.62". That cannot work, and not for want of a
> better threshold. ν̂ = 1 on the interior of K_c and high near its boundary,
> and **K_c is connected by construction** — precisely why the Douady rabbit
> was chosen over the Cantor-dust values in §2.1. Every super-level set of a
> connected smooth field is therefore connected, and the low-pass in §4 makes
> it smoother still. Measured over the band: ν̂ > 0.62 selects **one** region,
> 75.38 mm tall × 87.24 mm of arc — a single opening that would cut the vase
> apart. Twelve variants tested (three high thresholds, five low, four
> mid-bands); all give 1–2 giant regions and **zero** inside the ligament and
> span bounds. Evidence: `pierce_rule.py`.
>
> Thresholding is the wrong instrument. A lattice fixes the topology; the
> field decides what happens at each site.

**Seeded lattice.** Candidate sites lie on a hexagonally-staggered grid over the band — rows pitched in z, each row offset half a column from its neighbour, with the column count derived from the *local* circumference so spacing is uniform in millimetres on the surface rather than in angle.

Each site samples ν̂. Below the cut it stays closed; above it, the site opens to an arch whose size scales with how far above the cut the field sits:

```
size = size_min + (ν̂ − cut)/(1 − cut) · (size_max − size_min)
```

Placement and scale are both genuinely fractal-derived — the field decides which sites open and how wide — while the lattice guarantees discrete holes with a ligament floor that a level set cannot provide.

| Parameter | Value | Measured result |
|---|---|---|
| Row pitch (z) | **12.0 mm** | 6 rows over the 75 mm band |
| Column pitch (arc) | **14.0 mm** | staggered, hex packing |
| Open cut | **0.35** | **43 holes** open of the candidate sites |
| Size range | **3.0 → 8.0 mm** | realised 3.09 → 8.00 mm, a 2.6× spread so the field's variation reads |
| **Minimum ligament, measured** | — | **4.62 mm** against the 2.0 mm floor |

**The lattice ornaments one face, not the full circumference — accepted 2026-08-09.**
Measured on the shipped lattice, all 43 holes fall inside a single **~103° arc**
(θ 3.590 → 5.386 of 2π). Per row: 103°, 90°, 77°, 80°, 86°, 63°, all centred on
roughly the same side. Every site is independently field-gated; the Julia field's
high region simply sits in one sector at every pierced height, and the −82° helix
rotates it only about 25° across the 60 mm band — not enough to wrap.

The user was shown this and **chose to keep it**: one face reads as pierced
openwork, the remaining two-thirds as unbroken fractal relief, and the unpierced
side stays structurally stronger. This is intended behaviour, not a defect to
correct. Do not "fix" the clustering by decoupling site placement from the field.

Alternatives measured, for the record: 10 × 12 mm pitch at the same cut gives 55 holes but only **2.25 mm** of ligament — 0.25 mm of margin, too little on a part that must also survive printing. 14 × 16 mm gives 20 holes and 6.31 mm. Evidence: `seed_lattice.py`.

| Rule | Value | Reason |
|---|---|---|
| Hole shape | **pointed arch (gothic), apex ≥ 45°** | A round hole's crown is an unsupported bridge. A pointed arch is self-supporting — this is what buys R7 despite the piercing. |
| **Arch apex measured against GLOBAL Z** — see the correction below | no lean correction | FDM layers are horizontal in global Z and do not tilt with the surface. |
> **C4-A REVERSED 2026-08-09 after measurement.** The decision recorded below —
> orienting each arch crown against the LOCAL surface tangent — is wrong and has
> been removed from the code. Two independent reviewers found it, and it was
> verified directly on real cutter output: with the lean correction every one of
> the 43 holes had a roof face at **49.90° from vertical**, over the 45° limit —
> a near-flat unsupported bridge, on the very feature the pointed arch exists to
> avoid. With the correction removed both faces sit at **26.57°, symmetric**.
>
> The reasoning error: FDM layers are horizontal in **global Z** and do not tilt
> with the surface, so a crown is self-supporting relative to the *build
> direction*, not to the wall. Worse, the premise was false to begin with —
> `revolve_grid` places vertices at `(r cosθ, r sinθ, z)` with θ from a plain
> linspace that never depends on z, and `twist_rate_rad_per_mm` only steers which
> point of the *field* is sampled. **The solid is a plain surface of revolution
> with no shear; there was never a lean to correct for.**
>
> The failure was also mathematically forced: rotating a symmetric 45°/45° apex
> about that axis pushes one roof line toward horizontal and the other toward
> vertical by the same amount, for either sign. No magnitude of the mechanism
> keeps both sides under 45°.

| Min ligament between holes | **2.0 mm** (5 lines) — realised 4.62 mm | Below this the lattice snaps in hand. Now guaranteed by the lattice pitch rather than hoped for from a level set. |
| Max hole span | **12 mm** | Well inside the 30–40 mm bridging limit even if an arch degrades. |
| Edge fillet | 1.2 mm | Prevents knife-edges slicing to zero width. |
| Min ridge (anywhere) | 1.0 mm wide × 0.8–1.5 mm proud | Below 2.5 × nozzle a feature vanishes or becomes a gap. |
| Spike tips | blunted to ≥ 2.4 mm | Needle tips starve of cooling (15 s min layer time) and blob. |

Pierced band deliberately spans the widest point — maximum effect where the eye lands, and it reads as light through the form rather than texture on it.

### 3.4 Slope constraint

`|dr/dz| ≤ 1.0` everywhere (45° from vertical), enforced by clamping the field gradient before it becomes geometry, not by inspecting the mesh afterwards.

Three things consume the overhang budget and they are not independent — the profile taper, the relief gradient, and the helical lean. Composed:

| Contribution | Value | Where |
|---|---|---|
| Steepest profile slope | 0.6000 (30.96°) | shoulder, z 225–240, Ø 96 → 78 |
| Max relief slope, max \|dA/dz\| | 0.1222 | z ≈ 85 and z ≈ 185 |
| Meridional total | 0.7222 | |
| Tangential drift from twist at r = 58 | 0.4169 (22.63°) | widest point |
| **Combined \|∇r\|** | **0.8339** | |
| **Angle from vertical** | **39.82°** | envelope only — **see correction below** |

> **Corrected 2026-08-09 after measuring the real surface.** The table above,
> and the `max_envelope_slope` function derived from it, bound the **smooth
> envelope** — `radius_at` + `relief_amplitude` — and **do not bound the
> textured surface**. They never see the Julia field's own z-gradient, which is
> what drives the steepest local slopes. Two corrections:
>
> 1. The tangential term used r = 58.0 mm, the profile-only maximum. The true
>    maximum combined radius is **62.446 mm at z ≈ 151.3**, raising the
>    envelope bound to 0.8503 → **40.38°**.
> 2. The real textured surface measures **43.71°** (`predict_shell.py`,
>    production grid, |dr/dz| at fixed θ). The envelope figure understates it
>    by 3.33° even after correction (1).
>
> **The true margin against the 45° limit is 1.29°, not 5.18°.** Still passing,
> and passing on the number that matters — the measured surface, not the
> envelope — but four times tighter than this table originally implied.
>
> The envelope bound is retained because it is cheap and catches gross profile
> errors, but it is renamed `max_envelope_slope` so nothing mistakes it for the
> printability gate. The gate is `test_real_surface_respects_the_overhang_limit`
> in Task 4, which measures the actual radius field.

Why 43.71° and not worse: the Gaussian low-pass (§4 step 2) is what holds it there. Without it the same surface measures 52.88°, over the limit — see the band-limiting note in §4.

Per-segment profile slopes, all individually well inside limit:

| z | Ø | dr/dz | From vertical |
|---|---|---|---|
| 0 → 40 | 70 → 80 | +0.1250 | 7.13° |
| 40 → 150 | 80 → 112 | +0.1455 | 8.28° |
| 150 → 185 | 112 → 116 | +0.0571 | 3.27° |
| 185 → 225 | 116 → 96 | −0.2500 | 14.04° |
| 225 → 240 | 96 → 78 | −0.6000 | **30.96°** |
| 240 → 262 | 78 → 58 | −0.4545 | 24.44° |
| 262 → 300 | 58 → 68 | +0.1316 | 7.50° (lip flare, self-supporting) |

---

## 4. Generation pipeline

**Not Fusion 360, and not marching cubes.** A full voxel grid at 0.2 mm over this envelope is 683 M voxels (2.73 GB float32) and yields ~14 M triangles / 675 MB STL — past the point where slicers warn. Fusion's mesh-to-BRep warns at 10 k triangles, two orders below what this needs.

Structured `(θ, z)` grid, triangles emitted directly. Manifold by construction.

| | Nθ | Nz | Triangles |
|---|---|---|---|
| Outer surface | 640 | 500 | 638 720 |
| Inner surface (smoothed profile, reversed winding, **Nθ must match outer**) | 640 | 166 | 211 200 |
| Rim ring + base annulus + centre fan | — | — | 3 200 |
| **Shell total (measured, pre-boolean)** | | | **~853 120** |
| Hole boolean (C1-B) | — | — | measure, do not assume |

**Measured, not estimated** — `predict_shell.py` builds the real radius field and counts faces. Binary STL at ~853 120 triangles would be ~42.7 MB; 3MF ≈ 11 MB. Task 7 measures the post-boolean total and decimates if it crosses 1 M.

Same run, on the production config: max diameter **123.904 mm** against the 135 plate, height 300.0 mm, max overhang on the real surface **43.71°** against the 45° limit, minimum wall **2.0000 mm** after the `_inner_radius` clamp described in §4 step 4.

Sampling checks: arc step 0.5694 mm at r = 58 (at or below nozzle width, so nothing printable is lost); chord sagitta **0.000699 mm** (faceting invisible); **83.3 z-steps per fractal period** against a ≥50 minimum — coarse z-interpolation is the documented cause of horizontal banding in this class of model.

### Steps

1. Evaluate ν̂ on the (θ, z) grid via the log-polar map.
2. Band-limit **before** geometry: 4× rotated-grid supersample, Gaussian low-pass σ = 0.5 mm, gradient clamp. A fractal has unbounded detail — no sample rate is sufficient, so the field must be filtered, not merely sampled finely.
3. Outer vertices `[r cosθ, r sinθ, z]`; `θ = linspace(0, 2π, Nθ, endpoint=False)` with **no duplicate seam vertex** — wrap with `np.roll`.
4. Inner surface from the **smoothed profile offset inward by 2.0 mm**, clamped so it can never bulge past the raw profile: `inner = min(smooth_radius(z), radius_at(z)) − wall`. Never an offset of the detailed outer surface, which self-intersects wherever wall thickness exceeds local curvature radius.

   The clamp is load-bearing. `smooth_radius` bulges *outward* at concave kinks, and at the throat (z = 262 mm, the vase's narrowest point) it exceeds the raw profile by **1.4202 mm**. At the resolution the geometry is actually built at (`_inner_radius` samples 166 points over the height) that leaves a **0.6339 mm** wall at z = 262.2 — roughly 1.4 extrusion widths, precisely where the vase is most likely to snap. (A 3001-point sweep gives 0.5798 mm at z = 262.0; that is the continuum limit, finer than the mesh ever samples, and is quoted here only as the worst case the profile *could* produce.) Clamping restores the full **2.0000 mm** minimum at a cost of 0.13 % of interior volume. Measured in `wall_fix.py`.

   The inner surface **starts at z = `base_thickness` = 3.0 mm**, not z = 0, and carries the **same Nθ as the outer surface**. Both were found by building the shell:

   - Running the inner surface to z = 0 gives a **0.00 mm floor** — the base becomes a zero-thickness membrane and the cavity is open at the bottom. The spec originally specified a wall thickness and never a base thickness; 3.0 mm is the correction.
   - Giving the inner surface a coarser Nθ than the outer forces a ring resampling (`round(i·N_in/N_out)`), which for 96 → 48 produces **48 consecutive duplicate indices**, hence degenerate triangles in both the rim strip and the base annulus. Those get stripped and the mesh is left open — measured as 144 broken faces and `euler_number` 1 instead of 2. Matching Nθ removes the resampling entirely.

   Matching Nθ raises the inner surface from 70 290 to **211 200** triangles and the shell total to **~853 120**, still inside the 1 M slicer threshold. The inner surface may still be coarse in **z**; only θ has to match.
5. Rim: quad strip joining outer and inner top rings. Base: triangle fan to a centre vertex at z = 0. The shell is now closed and manifold.
6. **Holes by boolean subtraction (decision C1-B).** Build one cutter solid per hole — a pointed-arch prism, apex oriented from the *local surface normal* (decision C4-A), swept through the wall — union the cutters, then `trimesh.boolean.difference([shell, cutters])`. The kernel guarantees the result rather than relying on hand-rolled stitching.
7. Validate (§5). Export 3MF.

**Dependencies.** numpy 2.3.3, trimesh 4.11.5, scipy 1.17.0, lxml 6.0.2 are installed. **`manifold3d` is required by C1-B and is NOT currently installed** — `pip install manifold3d`. This is the one new dependency the design takes on; it is the price of the kernel-guaranteed boolean, and it also unlocks the self-intersection check that trimesh cannot do natively.

---

## 5. Validation gate

Nothing reaches the slicer without passing. Consistent with the house rule that CAD errors be impossible to miss.

```python
m = trimesh.Trimesh(V, F, process=True)
m.remove_infinite_values()
m.merge_vertices()
m.update_faces(m.nondegenerate_faces(height=1e-8))
m.remove_unreferenced_vertices()
trimesh.repair.fix_winding(m)
trimesh.repair.fix_normals(m)

assert m.is_watertight
assert m.is_winding_consistent
assert m.is_volume
assert m.volume > 0
assert m.body_count == 1                    # no detached islands
assert m.euler_number == 2 - 2 * n_holes    # genus check — catches bad stitching
assert len(trimesh.repair.broken_faces(m)) == 0
assert m.extents[0] <= 135 and m.extents[1] <= 135 and m.extents[2] <= 300
```

`m.euler_number` is the load-bearing assertion: it is the only cheap check that catches a hole-stitching error, which is the one place this pipeline can produce a plausible-looking broken mesh.

Note: `mesh.remove_degenerate_faces()` does **not** exist in trimesh 4.11.5 — it was removed. Self-intersection is not detectable in trimesh natively; deferred to slicer import.

---

## 6. Print settings

**Scope.** The deliverable is a 3MF carrying geometry: a closed shell with a **2.0 mm wall**. Perimeter count, infill density and pattern are slicer-profile settings the operator owns — this spec does not prescribe them, and the geometry does not depend on them.

Two settings *are* called out, because they are geometry-dependent rather than preference:

| Setting | Value | Why it is not a preference |
|---|---|---|
| **Slice gap closing radius** | **0** | The single most frequently documented failure across published fractal models. At default settings slicers silently merge the intentional gaps, and the lattice fills in. |
| **Supports** | **none** | The pointed-arch hole geometry is designed to be self-supporting (§3.3). Supports would scar the fractal surface unrecoverably, and are not needed. |

Suggested starting profile, offered as a starting point only: 0.15 mm layer, 5 bottom layers, ironed lip rim, 40–60 mm/s outer wall, input shaping on, 10 mm brim, PLA or PETG. Rough order: 30–40 h, ~350 g, before whatever the boolean and infill choices add.

---

## 7. Assumptions

### Resolutions — decided 2026-08-09

| | Concern | Decision | Consequence |
|---|---|---|---|
| **C1** | Hole-boundary stitching can break the mesh | **B — boolean subtraction** | Adds `manifold3d` dependency. Kernel guarantees the result; hand-rolled stitching removed from §4. |
| **C2** | Rabbit has no mirror plane | **A — accept, full 7.0 mm relief** | Design runs deliberately hot on complexity. The −82° helix is the organising rule in place of a reflection. |
| **C3** | Finest level at 2.096 mm, under the 2.2 mm floor | **A — accept** | Non-issue on inspection: 2.2 was an artefact of building the ladder on exactly *e*. The real floor is the 1.0 mm minimum ridge, and 2.096 is 2.1× it. |
| **C4** | Arch apex vs. helical lean | **A — per-hole local normal** | Cutter prisms oriented from the local surface normal, not global Z. |

The original analysis of each is retained below.

### Real concerns — pick a mitigation

**C1. Hole-boundary stitching is where the mesh can break.** Everything else is manifold by construction; the stitch is hand-rolled topology.
- **A (recommended):** assert `euler_number == 2 − 2·n_holes` and `body_count == 1`; add a unit test on a 3-hole toy shell before running the full grid.
- **B:** generate holes by boolean subtraction — requires `pip install manifold3d`, slower, but the kernel guarantees the result.
- **C:** drop piercing.

**C2. The rabbit is not mirror-symmetric.** `c` is complex, so K_c has only the universal z → −z 2-fold symmetry. Mirror symmetry is what research says stops D ≈ 1.6 complexity reading as noise.
- **A (recommended):** accept — the helix supplies a competing global order. Symmetry is a means to legibility, and a −82° screw is legible.
- **B:** cut peak relief 7.0 → 5.5 mm to reduce the complexity being held together.
- **C:** switch to a real c and lose R6.

**C3. Finest level lands at 2.096 mm, under the 2.2 mm floor the aesthetics research set.**
- **A (recommended):** accept — 2.1× the 1.0 mm minimum ridge, comfortably printable. The 2.2 figure came from a ratio-e ladder, and |μ| is 0.34 % off e.
- **B:** stop at four levels, raising the finest to 5.7 mm. Loses the 30 cm reading.
- **C:** raise Ø_max — blocked by R1.

**C4. Twist and arch geometry interact.** Pointed arches must be built against the local surface tangent, not global Z, or they degrade toward bridges on the leaning face (up to 22.63°).
- **A (recommended):** compute apex direction per-hole from the local surface normal. Cheap; already have the derivatives.
- **B:** over-steepen every arch by a global 22.63°, accepting an inconsistent look.

### Verified safe

- `c` in M, area 0.1039 — 20 000-iteration membership, 800² area grid
- Combined overhang worst case 39.82° < 45° limit, on a pessimistic composite of profile taper + relief gradient + helical lean
- 83.3 z-steps per fractal period > 50 minimum
- Chord sagitta 0.000699 mm — faceting invisible
- ~853,120 triangles measured pre-boolean, under the 1 M slicer comfort threshold; ~11 MB 3MF
- |μ|/e within 0.34 %

**Superseded by C1-B:** "no new Python dependencies" was true of the stitching approach and is no longer true. `manifold3d` must be installed. Boolean subtraction will also raise the triangle count above the measured ~853,120 — to be measured, not assumed, and decimated if it crosses 1 M.

### Minor / accepted

- Z-seam exists in multi-wall — align to a lobe cusp or randomise
- 3MF over STL. Measured on THIS mesh at 855,068 triangles: 3MF 13,528,396 bytes against binary STL 42,753,484 — a ratio of **3.16×**, not the 3.8× quoted from an icosphere during toolchain research. The ratio is mesh-specific, not a constant. 3MF also carries units, which STL does not.
- 30–40 h print
- Not resizable — cell sizes tuned to extrusion width

---

## Appendix A — verification scripts

Constants in §2 were computed, not recalled:

Committed alongside this spec in `docs/superpowers/specs/`:

| Script | Produces |
|---|---|
| `verify_c.py` | Mandelbrot membership, K_c area fraction, Koenigs α and μ — 7 quadratic and 12 degree-6 candidates (§2.1). Several minutes at the committed settings. |
| `design_constants.py` | log-polar k, twist per period, scale ladder, lean angle, mesh sampling checks (§2.2, §2.3, §4) |
| `check_slope.py` | A(z) samples, per-segment profile slopes, combined overhang worst case (§3.1, §3.4) |

To be promoted into `tests/` as a regression suite alongside the generator, so a
changed constant fails a test rather than silently shifting the geometry.
