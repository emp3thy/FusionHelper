# Bloom - ethereal front-plate variants

Fourth study (after patterns, geometric, Bauhaus): soft, luminous, airy fronts
made by form and light. Page: `artifacts/wine-rack/bloom-ethereal.html`:
constraints note, contact sheet, nine variants rendered to scale on the 3 x 3
front (lit ones at night with the same tile lights-off beside them), comparison
table, lit-vs-unlit note, top 3, pre-modelling tests. One geometry routine
(pitch 110.833, tile 110.53, seam 0.3, bore r 46, face r 50) with lit and
unlit modes.

## Constraints

- **No colour fades.** Tiles are 3D printed: no gradient spools, no halftone
  or dithered tone, no blended filaments. Softness comes from discrete stepped
  bands, from form (thickness, grooves, ridges, relief) and from light.
- **1-2 colours per tile by default, never more than 3.** Two colours print one
  per nozzle on the H2D with near-zero purge; every extra colour is an AMS swap
  with purge on each layer that carries it, which can double print time and
  waste more filament than the tile weighs. All nine tiles are the same file,
  so colours per rack = colours per tile. No variant here needs a third colour.
- Renderings: glow and translucency are simulated with blur/opacity so the lit
  effect reads; every filament is drawn as one flat colour. The only SVG
  gradients on the page are light (edge-lit fall-off, the Halo lithophane
  glow), never filament.

## Changes from the draft

- **Removed:** Breath (halftone dot fade from the bore: a dithered gradient)
  and Aurora (gradient-spool body: the fade is the filament).
- **Reworked:** Mist (dot screen growing toward the edge -> three stepped
  white bands); Nimbus (dithered cloud field -> solid outlined clouds, Japanese
  kumo style); Pearl (dual-colour silk with hue cycling -> one pearl silk, sheen
  and shadow from ridge angle); Ripple (outer rings drawn fading -> every ring
  identical, shadow line for relief).
- **Added:** Lantern (opaque tracery inlaid on a translucent tile).
- Halo, Dandelion, Frost and Constellation kept; Halo/Dandelion/Frost now show
  a lights-off tile, Constellation a daylight tile. Silk Multi-Color and PLA
  Basic Gradient dropped from the filament list.

## Light paths

- **Edge light (as designed):** 10 mm COB strips in the 11 x 3.2 mm rebates
  along the two internal row seams. Light travels in the translucent tile as a
  light guide; the 33.7 deg flare scatters it (a free bright ring per bottle)
  and back grooves leak it forward. Brightest within ~20 mm of the lit edges;
  rack top and bottom have no strip (a third strip evens it). No diffuser gap:
  the tile is the diffuser.
- **Back light (needs a change):** a lithophane needs light behind the lobes;
  the solid PETG-CF front ring blocks it. Halo needs a 6 mm pocket in the ring
  under each lobe with a 25 mm 5 mm-wide COB segment or LED filament and at
  least 5 mm of air to the tile back.
- **No light:** relief and hairlines that catch a window, frosted face from the
  textured plate or 0.08 mm layers, single silk sheen, Galaxy sparkle, PLA Glow.
  Fuzzy skin applies to walls only in Bambu Studio: it frosts the bore/flare
  wall, not the flat face.

Off-brief filaments and why acceptable (tiles carry no load; pinned to the
front ring, nothing bears on them): PLA Silk+ pearl (brittle, weak layer bond),
PLA Glow (abrasive; stock hardened nozzle fine, not AMS Lite), PLA Galaxy
(glass flecks, mildly abrasive). On-brief: PLA/PETG Translucent, PLA Marble,
Panchroma/Bambu Matte, PETG HF.

## Comparison

Grams = carved/relief volume at 1.24 g/cm3; minutes = extra/finer layers and
nozzle changes on an H2D at 0.4 against the 38 g / 48 min base tile. Lit /
Unlit = looks ratings in each state (- = no light source). Bracketed = the
alternative make. Nothing printed.

| # | Variant | Make | Light | Filaments | Col/tile | Col/rack | Min mm | Layer | +g | +min | Lit | Unlit | Print | Hides |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Halo | back lithophane | back-lit, ring pockets, 5 mm gap | PLA Translucent | 1 | 1 | 0.8 | 0.1 | -2.4 | 18 | 5 | 1 | 3 | 4 |
| 2 | Dandelion | back engraving | edge-lit, existing strips | PLA Translucent | 1 | 1 | 0.8 | 0.2 | 0 | 4 | 5 | 2 | 4 | 3 |
| 3 | Frost | back engraving | edge-lit, existing strips | PLA Translucent | 1 | 1 | 0.8 | 0.2 | 0 | 2 | 4 | 1 | 5 | 2 |
| 4 | Lantern | opaque inlay on translucent | edge-lit, existing strips | PLA Translucent + Matte grey | 2 | 2 | 1.0 | 0.2 | 0 | 6 | 5 | 4 | 4 | 4 |
| 5 | Mist | stepped-band inlay | none | Matte blue + PETG HF white | 2 | 2 | 0.8 | 0.2 | 0 | 4 | - | 4 | 5 | 5 |
| 6 | Nimbus | outlined-cloud inlay | none | Matte blue + PETG HF white | 2 | 2 | 0.8 | 0.2 | 0 | 5 | - | 4 | 4 | 4 |
| 7 | Constellation | point inlay | phosphorescent, no wiring | PLA Galaxy + PLA Glow | 2 | 2 | 0.8 | 0.2 | 0 | 4 | 4 | 4 | 4 | 5 |
| 8 | Ripple | relief hairlines | none (edge-lit option) | Matte grey + Silk+ pearl | 2 (1) | 2 (1) | 1.0 | 0.12 | 0.9 | 8 | - | 4 | 3 | 3 |
| 9 | Pearl | relief flutes, silk | none | Silk+ pearl | 1 (2) | 1 (2) | 1.0 | 0.08 | 1.6 | 12 | - | 5 | 3 | 3 |

Geometry, bore and seam per variant:

- Halo: face 0.8 mm from r 52-56 thickening to 3.0 mm by r 72 and the edges,
  carved on the back of a face-down tile, lobes 100 % infill. Brightest band
  hugs the flare; seams run through the thick dark corners.
- Dandelion: 3 mm node boss, 14 stalks r 6-24 per lobe, 1.2 mm seed dots, all
  0.8 mm grooves 0.6 deep on the back. Clear of the flare; seams pass through
  the seed heads on the lit row seams.
- Frost: textured-plate face; back rings 0.8 wide 0.5 deep at r 53 / 56 / 59.5
  / 63.5; fuzzy skin on the bore/flare wall. Seams not hidden (lit hairlines).
- Lantern: face-down inlay 1.0 mm deep (5 layers, fully opaque); 1.0 mm lines:
  rings r 53 and r 64 with 36 spokes, node rosettes r 5 / r 12 with 24 spokes,
  a quarter per tile. r 53 ring is the collar; seams cut rosettes on a spoke.
- Mist: from the tile edge 4.0 solid white, 2.0 gap, 1.6 line, 2.4 gap, 0.8
  line; corner radii 4 / 9 / 13; collar 1.5 at r 52, field cleared to r 54. At
  the seam two 4 mm bands make an 8.3 mm white bar; at mid-side the band and
  collar merge (the <0.8 mm blue sliver is closed in CAD).
- Nimbus: 7 clouds per pitch, each 4-6 discs r 3.5-7, seed wrapped to the pitch
  (tiles identical, clouds continuous across seams); 0.8 mm outline at 0.8 mm
  offset; cleared to r 54, 1.5 mm collar.
- Constellation: 46 seeded points 1.0-1.8 mm, seed wrapped to the pitch, three
  0.8 mm connecting lines, 2 mm Glow collar; stars outside r 54.
- Ripple: 1.0 mm rings raised 0.5, pitch 2.4 growing 5.5 percent per ring, r 53
  to the corners; first ring is the collar.
- Pearl: 90 radial ridges 1.0 wide, 0.4 high, every 4 deg from r 53.5, one
  silk, single nozzle, 0.08 mm top band; 1.5 mm collar.

## Lit vs unlit

- **Nothing without power:** Halo, Frost, Dandelion (faint ghost lines only).
- **Ethereal with lights off:** Mist, Nimbus, Ripple, Pearl (daylight tiles),
  Constellation (sparkle by day, own glow by night), Lantern (grey tracery on
  frost).
- **Both states well:** Lantern, Constellation.
- **LED layout:** Dandelion, Frost, Lantern use the existing two strips, no
  diffuser gap; a third strip in the top rebate of the top row (and bottom of
  the bottom row) evens the glow. Halo needs ring pockets + COB segments with
  >= 5 mm air gap. The rest need no wiring.
- Rendered glow is a simulation; real edge-lit brightness halves by ~30 mm from
  the strip in frosted PLA.

## Top three

1. **Lantern.** The only lit variant still finished with the power off; two
   colours one per nozzle, existing strips, no diffuser gap, 0 g, 1.0 mm lines.
2. **Dandelion.** Lit showpiece in one filament on the existing strips, seed
   heads on the lit seams, +4 min; near-blank by day.
3. **Mist.** Daylight answer: best seam-hiding of all four studies, two
   on-brief filaments, three hard steps instead of a fade, nothing under 0.8 mm.

Also: Constellation (two faces, no wiring), Halo (if the ring is pocketed; lit
it is the most beautiful), Pearl (window-lit room).

## Test plate before modelling (one plate, about an hour)

1. Lithophane thickness calibration strip, PLA Translucent, 0.6-3.2 mm in 0.2
   steps at 0.1 mm layers, 100 % infill, over a COB offcut at 3 / 5 / 8 mm:
   sets the Halo curve and diffuser gap.
2. Translucency sample, 40 x 40 x 8 mm in PLA and PETG Translucent, edge-lit
   from one side, 0.8 mm back grooves at 5 / 15 / 30 / 45 mm: real fall-off,
   frost vs glass for Dandelion and Frost.
3. Lantern opacity card: grey inlay 0.4 / 0.6 / 1.0 / 1.4 mm deep on PLA
   Translucent over the COB: shallowest inlay that reads as a solid silhouette.
4. Hairline card face-down: 0.6 / 0.8 / 1.0 mm lines and dots in matte blue +
   white and Galaxy + Glow: smallest feature that sticks, Glow duration.
5. Silk swatch face-up at 0.08 mm with ten ridges: Pearl sheen and stringing.
