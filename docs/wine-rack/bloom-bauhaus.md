# Bloom - Bauhaus front-plate variants

Third study, Bauhaus only (after `bloom-patterns.md` and `bloom-geometric.md`).
Page: `artifacts/wine-rack/bloom-bauhaus.html`: contact sheet, ten variants
rendered to scale on the 3 x 3 front plus one-tile close-ups, a primaries /
muted palette toggle (a different spool set, not a theme), comparison table,
H2C/H2D note, top 3. One geometry routine (pitch 110.833, tile 110.53, seam
0.3, bore r 46, face r 50) extended with per-tile body colour and per-tile
rotation so the nine separate prints can be used compositionally.

## Rules used

- All ten are flat two-colour-per-layer inlays printed face-down: 0 g extra,
  crisp 0.8 mm edges, no layer lines on the face. Shapes stay outside r 53.5.
- The bottle is the blue circle of Kandinsky's trio: the collar ring is the
  circle wherever a ring is drawn.
- H2D: body + one accent per tile (zero purge), different pairs on different
  tiles, so the rack shows 4-5 colours from two-colour plates. Three or more
  colours on one tile need the H2C (8 s swaps on the first two layers).
- Seams: figures sit on nodes (quarter per tile, neighbours' colours compose),
  run along seams as bars that swallow them, or frame each tile deliberately.

## Palette

- Primaries: Bambu PLA Matte (tiles only; no load) Scarlet Red, Lemon Yellow,
  Marine Blue, Charcoal, Ivory White. PETG HF white/black for a satin face.
- Muted: Polymaker Panchroma Matte in the nearest brick, ochre / mustard,
  slate grey and cream; walnut body + marble lines on the frame-based variants
  (Breuer, Seal, Stijl); walnut / marble / ochre for Stolzl.

## Comparison

Minutes = colour-change overhead on the first two layers against the 38 g /
48 min base tile. Brackets = H2D version. Col/rack counts body colours. Hides =
seam hiding. Nothing printed; designer estimates.

| # | Variant | Source | Layout | Col/tile | Col/rack | Printer | Min mm | +min | Looks | Print | Hides | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Trio | Kandinsky trio | rotation of identical tiles | 4 | 4 | H2C | 3.5 | 6 | 5 | 4 | 3 | 12 |
| 2 | Rotation | Kandinsky / Itten | 3 x 3 colour rotation | 2 | 4 | H2D | 3.5 | 3 | 4 | 5 | 3 | 12 |
| 3 | Homage | Albers | uniform | 4 (2) | 4 (2) | H2C (H2D fallback) | 12 | 6 (3) | 4 | 4 | 3 | 11 |
| 4 | Bayer | Bayer posters | single diagonal accent + rotation | 2 | 3 | H2D | 2.5 | 3 | 5 | 5 | 3 | 13 |
| 5 | Moholy | Moholy-Nagy | rotation | 5 (2) | 5 (2) | H2C (H2D loses overlap) | 3.0 | 7 (3) | 4 | 3 | 4 | 11 |
| 6 | Stolzl | Stolzl weavings | uniform | 3 (2) | 3 (2) | H2C (H2D slit) | 2.0 | 5 | 4 | 4 | 4 | 12 |
| 7 | Schlemmer | Triadic Ballet | uniform | 3 (2) | 3 (2) | H2C | 1.6 | 5 | 3 | 4 | 2 | 9 |
| 8 | Breuer | B3 / B33 tube | one odd tile (centre inverted) | 2 (3) | 3 (4) | H2D (arc needs H2C) | 2.6 | 3 | 4 | 5 | 4 | 13 |
| 9 | Seal | 1922 Bauhaus seal | uniform | 3 (2) | 3 (2) | H2C (H2D no disc) | 1.5 | 5 | 4 | 4 | 4 | 12 |
| 10 | Stijl | De Stijl contrast | colour fields | 2 | 5 | H2D | 3.0 | 3 | 5 | 5 | 5 | 15 |

Geometry per variant:

- Trio: blue ring 3.5 mm (r 50.75-54.25), red quarter square 14 mm at (+,+),
  yellow right triangle legs 24 inset 1.5 at (-,-); tiles rotated idx x 90.
- Rotation: accent by (row + col) mod 3; red = quarter squares at two opposite
  corners, yellow = triangles at the other two, blue = ring only.
- Homage: node-centred squares 30 / 21 / 12 mm stepped 0 / 1.5 / 3 mm down;
  outer corner 3.4 mm clear of the collar.
- Bayer: ring 2.5 + quarter disc r 24 at (+,+) + quarter disc r 13 at (-,-),
  rotated; red on the diagonal tiles, black elsewhere (two files, one spool
  change).
- Moholy: 3 mm bar from (0,30) to (30,0) corner-frame on all four corners (four
  tiles close a diamond on each node); red disc r 10 at (9,9), yellow r 7 at
  (20,5), overlap in orange via a clip.
- Stolzl: stripe set period P/2 (heights 2-8 mm), left 32 mm block swaps colour
  and shifts 10 mm; clearance disc r 54.
- Schlemmer: per lobe on the diagonal: head r 3.5 at 21, red cone 17 -> 7 (half
  width 0.8 -> 4.2), foot bar 3 x 2 at 3-6.
- Breuer: rounded-rect tube 2.6 mm, inset 2, r 10 corners, no collar ring (tube
  passes 2 mm outside the lip at mid-side); red quarter arc r 20 (H2C); centre
  tile body black / tube white.
- Seal: square frame 1.5 mm inset 1.5 kisses a 2 mm ring at r 51.5 (0.5 mm gap
  at mid-sides); red quarter discs r 9 on all corners = 18 mm disc per node.
- Stijl: 3 mm black bars along top and left edges of every tile (right / bottom
  on the last column / row), ring 2.5 merging with the bar at mid-side; body
  colours [red, W, W, W, W, blue, W, yellow, W].

## H2C vs H2D

- H2D native, zero purge: Rotation, Bayer, Stijl, Breuer (without arc). Any
  layout where each tile is body + one accent.
- H2C only: Trio, Moholy's overlap, Stolzl's two stripe colours, Schlemmer,
  Seal's red disc, Homage in three tones (each has a two-colour fallback).
- H2D with AMS purge is not recommended: ~5 g and 4 min per colour change per
  tile for a first-layer effect.

## Top three

1. **Stijl** (15). Seams vanish under the bars; five colours on the rack from
   two-colour prints; four files differing only by spool. Muted set + walnut
   bars if primaries are too loud.
2. **Bayer** (13). The most Bauhaus-looking front the H2D prints natively:
   quarter-discs composing differently at every node, ring on every bottle,
   one red diagonal as the whole colour budget.
3. **Breuer** (13). The furniture reading: tube frame per tile makes the seam a
   drawn double line, the inverted centre tile is a free focal point, and as a
   half-round relief it reads as steel rather than print.

With an H2C: Trio (the literal brief) and Stolzl (warmest). Seal for a calm
room. Rotation is Trio for the H2D and the easiest production run.

Before modelling: print one Ivory White tile with Charcoal bars (Stijl) and one
with a Scarlet Red quarter-disc (Bayer), face-down, and judge the textured-PEI
finish on the matte filaments in the room.
