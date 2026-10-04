# Wine rack design brief (research synthesis, 2026-10-03)

Target: a wine rack that fits a 335 mm x 335 mm square opening (depth not given;
the dimensions match a KALLAX-class cube shelf, inner 330-335 mm square, about
390 mm deep - treat depth as a parameter, default rack depth 280-300 mm so a
300-330 mm bottle sits flush or protrudes <= 40 mm). Printed on a Bambu Lab
H2D or H2C. Three design directions: unobtrusive, modern, pretty.

Full reports in this folder: research-bottles-slots.md, research-printer.md,
research-filament.md, research-existing-designs.md. Read them; the numbers
below are the headline constraints every design must respect.

## Geometry that must hold

| Item | Value |
|---|---|
| Opening | 335 x 335 mm; make the rack outer envelope 332-333 mm (1-1.5 mm per side) and parametrise `space_w`, `fit_gap`. PETG/PLA shrink ~0.2-0.3 % (0.7-1 mm over 335 mm) |
| Bottle diameters | Bordeaux 74-81 (typ 75-77); Burgundy 82-93 (typ 82-88); Champagne 88-101 (typ 88-91); Alsace flute 75-79 but 329-357 long |
| Bottle length | 280-357 mm; 750 ml typ 300-330 |
| Full-bottle mass | still 1.5 kg design value; Champagne 1.7 kg; magnum 2.1-3.3 kg |
| Clear slot | >= 92 mm with a flared entry fits nearly everything (Burgundy + standard Champagne). 76-85 mm slots draw "fits none of my bottles" complaints |
| Grids that fit 335 | 3 x 3 at 105-112 mm pitch with walls <= 12 mm (mixed cellar, recommended); 4 x 4 at 80-85 mm pitch with walls <= 6 mm (Bordeaux-only); 2 x 2 at >= 125 mm (magnums). 45-degree lattices never beat the square grid in a square |
| Support | two-point cradle or ring; supports must straddle the full-bottle centre of gravity (~130-145 mm from the base of a 320 mm bottle); front support under the shoulder so the bottle cannot slide forward; flat shelves let bottles roll |
| Storage angle | level or <= 15 degrees neck-up; never neck-down |

Total load: 9 Champagne ~15 kg; 16 Bordeaux ~24 kg.

## Printer envelope (H2D / H2C)

- Single-nozzle usable bed: 325 x 320 x 325 mm (H2D); H2C left nozzle the
  same, Vortek side ~305 mm wide. Dual-colour overlap 300 x 320 x 325.
  **Nothing 335 mm square prints in one piece at any rotation (max square 320).
  Nothing 335 mm tall prints upright (Z 325).**
- Diagonal bars work: a 335 mm bar can be ~110 mm wide (practical) on the
  single-nozzle bed, ~95 mm in the dual-colour zone; 20 mm rails reach ~436 mm.
- Front 15 mm strip is the calibration zone; multi-colour needs prime-tower
  room (worst case ~290 x 280 effective).
- Two-colour is near waste-free on both machines (one colour per nozzle on
  H2D; fixed + one Vortek hotend on H2C) but confines the part to the
  300 x 320 overlap. 3+ colours: cheap on H2C (8 s hotend swap), expensive on
  H2D (AMS purge can double time on a big part).
- Nozzles 0.4/0.6 (HF variants). 0.6 at 0.3 mm layers is the time-saver for
  structural parts; wall thicknesses in multiples of 0.6 mm then.
- Design rules: overhangs <= 45 degrees (PETG is strict); bridges <= 30 mm
  clean; walls 2.4-3.2 mm structural; 0.5-1 mm 45-degree chamfer (not fillet)
  on bed-side edges; elephant-foot comp 0.15 mm; round holes print 0.3-0.5 mm
  undersize.
- Fit clearances per side: press 0-0.05; push/snap 0.05-0.10; slip 0.20;
  loose 0.30-0.50; sliding dovetail 0.20-0.30 with 1-2 degree taper. Ship a
  tolerance coupon. Keyed/conical/double-dovetail joints get no breakage
  complaints; rectangular tabs fall apart; tight press-fits crack.
- Warping: 5 mm brim, reduced brim gap; PETG on textured PEI with glue
  release, low fan; ASA/ABS chamber 50-65 C. Avoid big flat bases (ribbed
  or lattice bases, chamfers, no supports).
- Time/material: 1.5-2 kg of filament is 14-25 h at 0.6/0.3 mm, 22-37 h at
  0.4/0.2 mm; plan 4-6 plates of 6-12 h. Budget ~100-150 g and 4-8 h per
  bottle position; thin rings and short cells win.

## Filament (creep governs, not strength)

Creep resistance PC > ABS/ASA > nylon > PLA. PLA sags in 3-6 months under
constant load; keep PLA stress < ~10 % of yield, PETG/ASA < 20-25 %. Walls
carry load (5-6 walls, 30-40 % gyroid), load path in XY, layer lines along
the span, generous fillets, no thin cantilevers.

| Role | Pick | Notes |
|---|---|---|
| Structural default | Bambu PETG-CF | flex modulus 2910 MPa, HDT 74 C, stock hardened nozzle, no chamber heat, ~GBP 29/kg |
| Structural budget | PETG HF | 2050 MPa, GBP 18/kg, "creeps only slightly" |
| Heat + UV (window / by oven) | Bambu ASA | HDT 100 C, naturally matte, needs chamber 50-60 C, brim, glue |
| Unobtrusive matte neutral | ASA (grey/white/black) or Prusament PETG Matte / Panchroma Matte PLA | Bambu PLA Matte has weak layer bonding - avoid for load |
| Modern | PETG-CF Black (satin, hides layers) or PET-CF; ASA/PETG HF White | PLA-CF trim only |
| Pretty | Bambu PLA Marble / Panchroma Marble (stone); Bambu PLA Wood Black Walnut / Rosewood / Fiberlogy FiberWood (wood); Bambu PETG Translucent (lit) | all PLA - over-build or use as a skin over a PETG-CF skeleton |

Avoid silk PLA (brittle). Dry PETG/PETG-CF 65 C 8 h; ASA 80 C 8 h. Skip nylon
(absorbs water). All rigid candidates are plasticiser-free, safe on labels.

## Lessons from existing printed racks

- Honeycomb rings printed flat (hoop in XY, bottle axis vertical on the bed)
  are the most-printed, most-praised architecture; two rings + ribs beats a
  full tube for material.
- Stacked cells need a positive lock or frame; provide a horizontal tie per
  layer or an outer frame, or users report tipping.
- Vertical layers are ~50 % of flat strength; a 45-degree tilt recovers +27 %.
- Reference looks: unobtrusive = KALLAX 3x3 insert, Vinotemp peg pairs, white
  fridge cradle; modern = WineHive honeycomb, Johansson bentwood honeycomb,
  Koziol 36 x 35 cm module; pretty = GustaVino Gaudi cells, Alessi Barkcellar,
  Voronoi hex modules, LED-backlit edges. Decorative skin over a plain PETG
  skeleton so the pretty part never carries load.

## Deliverables per design

1. A parametric Fusion 360 build script per the fusion-design skill (buildkit
   author script, bundled, preflight PASS).
2. A design page (HTML artifact) that sells the design and gives the maker
   everything: concept, views, bottle fit, module/plate plan, joints, filament
   and settings, time/material, assembly, risks.
