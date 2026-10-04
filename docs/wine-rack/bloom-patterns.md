# Bloom - front-plate pattern study

Companion to `bloom-design.md`. Page: `artifacts/wine-rack/bloom-patterns.html`
(to-scale 3 x 3 renderings and one-tile close-ups of every direction, all drawn
from one geometry routine: pitch 110.833, tile 110.53, seam 0.3, bore r 46,
face r 50).

## The field

Between the 100 mm face opening and the 110.53 tile edge there is 5.3 mm at
mid-side and 28 mm on the diagonal, so a pattern lives in four corner lobes plus
a collar. Four tiles meet at every node, so a motif built on the node (one
quarter per tile) appears 16 times. Three ways to make it:

- relief up (face-up print, 0.6-2 mm, ironed tops, 2 colours free per nozzle);
- flat inlay (face-down print, first layer on textured PEI, crisp 0.8 mm
  colour edges, 2 colours on H2D / up to 7 on H2C, zero extra material; the
  flare becomes a 33.7 deg inward overhang, inside the 45 limit);
- through-cut (translucent PETG lit variant only).

## Comparison

Grams = relief volume at 1.24 g/cm3; minutes = relief layers + colour-change
overhead on an H2D at 0.4/0.2 against the 38 g / 48 min base tile. Bracketed
values are the H2D reduction (colours) or H2D cost with AMS purge (minutes).
Ratings 1-5; Hides = how well seams and layer lines disappear. Nothing has been
printed; these are designer estimates.

| # | Pattern | Made | Colours | Filament | +g | +min | Looks | Print | Hides | Total |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Reed (fluted) | relief up | 1 | walnut | 5.9 | 9 | 4 | 5 | 4 | 13 |
| 2 | Cells (Voronoi) | relief up | 2 | walnut + marble | 0.8 | 7 | 4 | 3 | 4 | 11 |
| 3 | Sunburst (deco) | flat inlay | 2 | PETG-CF black + PETG HF white | 0 | 4 | 5 | 4 | 4 | 13 |
| 4 | Asanoha | flat inlay | 2 | walnut + marble | 0 | 5 | 4 | 5 | 4 | 13 |
| 5 | Khatem (zellige) | flat inlay | 3 (2) | matte terracotta / sage / cream | 0 | 6 | 5 | 3 | 4 | 12 |
| 6 | Terrazzo | flat inlay | 5 (3) | marble + 4 matte | 0 | 3 (12) | 4 | 3 | 5 | 12 |
| 7 | Halo (minimal) | inlay / relief | 2 | walnut + marble | 0 | 2 | 3 | 5 | 2 | 10 |
| 8 | Ginkgo | relief up | 2 | walnut + marble | 2.1 | 6 | 5 | 4 | 3 | 12 |
| 9 | Lantern (lit through-cut) | through-cut | 1 (+1) | PETG translucent | -1.5 | 4 | 4 | 3 | 3 | 10 |
| 10 | Kintsugi (wildcard) | relief / inlay | 2 | CF black + gold PLA | 1.2 | 5 | 4 | 5 | 5 | 14 |

Key geometric facts per pattern:

- Reed: pitch TW/27 = 4.094 so a groove sits on every column seam; trapezoid
  reeds 3.0 base / 1.0 top / 1.0 high; needs 0.08-0.12 layers on the relief band.
- Cells: seeds periodic with the pitch (translates, not mirrors) so no ridge lies
  on a seam; 1.2 x 1.0 mm ridges; merge segments under 1.5 mm.
- Sunburst: rays at 11.25 deg off the seams so the gap is always in a dark gap;
  0.94 mm ray tips; stepped collar 2.0 + 1.0 mm.
- Asanoha: lattice side P/7, row P/8 (1 percent off equilateral) so seven
  columns and eight rows fit one pitch and the lattice never breaks at a seam.
  Seigaiha also period-locks but mirrors badly at column seams; not built.
- Khatem: star-and-cross with stars on the nodes and the bottle in the cross
  (same geometry, not an imitation); seams fall on grout; diagonal point 2.4 mm
  short of the flare.
- Terrazzo: one chip map, four rotations; only the first two layers are
  multicolour; cap at 3 colours on H2D.
- Ginkgo: fan r 5-23, 82 deg, cleft 4 mm, veins 0.8 mm grooves; four stems meet
  on the seam crossing.
- Lantern: through-cut arcs 2.6 mm at r 9/15/21 from each node; collar must be
  a clear-PETG inlay (a through-cut ring would sever the tile); strip behind the
  row seam lights the inner arcs hardest.
- Kintsugi: exits at 16 and 38 mm from every corner on every edge so cracks
  match across all twelve seams; knot ring on each node, gold rim on each bore.

## Top three

1. **Kintsugi** (14). Turns the nine-piece front into the ornament: the seams
   are part of the crack map. 1.2 g, 2 colours, no purge on H2D, a few
   polylines and a ring in the author script. Needs one gold metal-fill spool
   (not silk) or, on-brief, marble "milk" cracks on walnut.
2. **Reed** (13). The 2026 furniture look, single colour, column seams vanish
   in grooves, nothing to align. Only cost is fine layers on the top 1.2 mm.
3. **Asanoha** (13). Best flat-inlay candidate: zero extra material, one
   continuous 1 mm line network locked to the pitch, no layer lines on the face,
   and the natural pattern for the lit PETG variant.

Also: Terrazzo if printing on an H2C; Ginkgo if Bloom's botanical identity
stays (direct successor to the current leaf); Sunburst for a dark deco room.

## Before modelling

Print one face-down and one face-up tile of the current design and compare
under room light. The inlay half of the list (Sunburst, Asanoha, Khatem,
Terrazzo) depends on wanting the textured-PEI finish; the relief half (Reed,
Cells, Ginkgo, Kintsugi) depends on ironing hiding the top-layer lines.
