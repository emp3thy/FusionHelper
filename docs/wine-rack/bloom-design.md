# Bloom - design note, rev 2 (pretty / decorative direction)

Slug `bloom`. Files: `artifacts/wine-rack/bloom_author.py` (author),
`artifacts/wine-rack/bloom_author.bundled.py` (gated artifact),
`artifacts/wine-rack/bloom.html` (design page). Execution in Fusion and
the numeric verification are pending (no Fusion MCP this session).

## Rev 2: what changed and why

Rev 1 held each bottle on a rear ring and a front ring 256 mm apart. On a
320 mm Bordeaux the front ring sits past the shoulder, under the neck,
so only the rear ring touched the body and the bottle rested on its
shoulder taper. Rev 2 adds a MIDDLE RING per cell and replaces the
integral posts with four pass-through RODS. The rear ring (0-16 from
the bottle base) and the middle ring (156-172) now both bear on the body
either side of the centre of gravity (130-145), so bottles lie level.
Rods print lying flat, so no 240 mm towers stand on the plate.

## Concept

A 3 x 3 grid of identical cells. Each cell: three flat PETG-CF rings
(110.8 square outline, 92 bore, 16 thick) on four 10 mm square rods.
End rings carry blind pockets (12 deep, 0.5 mm mouth chamfer); the
middle ring has through holes; the rods carry a 0.4 mm tick groove at
the middle-ring station. Dovetail grooves on every ring face take bowtie
keys at all three planes (36 keys). A separate wood-PLA bezel tile pins
onto each front ring and carries everything decorative: the flared
entry, a two-colour leaf relief and an optional COB-LED rebate. Four
tiles meet at every grid node and their half-leaves form a four-petal
bloom whose midrib is the tile seam. The tile never carries load.

## Parameter table (user parameters in the script)

| Name | Default | Drives |
|---|---|---|
| space_w | 335 mm | cube opening |
| fit_gap | 1.25 mm | clearance per side; envelope = 332.5 |
| rack_d | 280 mm | total depth incl. tile (320 bottle protrudes 40) |
| bezel_t | 8 mm | tile thickness |
| slot_clear | 92 mm | clear bore, rings and tile |
| flare_r / flare_h | 4 / 6 mm | entry flare (33.7 deg, asserted <= 45) |
| ring_d | 16 mm | thickness of all three rings |
| mid_z | 140 mm | rear ring inner face to middle ring rear face |
| rod_w / rod_gap / rod_in | 10 / 0.1 / 3 mm | rod section, fit per side, inset from the outer faces |
| rod_ch | 1 mm | 45 deg chamfer on all rod end edges |
| pocket_d / pocket_ch | 12 / 0.5 mm | blind pocket depth, mouth chamfer |
| tick_w / tick_d | 0.8 / 0.4 mm | rod tick groove |
| dt_mouth / dt_base / dt_depth | 7 / 8.3 / 3 mm | dovetail groove (12 deg flank) |
| dt_clr | 0.25 mm | key clearance per side |
| dt_ovr / key_short | 1 / 0.5 mm | cut overshoot; key shortfall |
| pin_d / pin_h / pin_inset | 6 / 5 / 13 mm | tile locating pins |
| fit_push / hole_comp | 0.1 / 0.4 mm | pin push fit, round-hole undersize |
| tile_gap | 0.3 mm | seam between tiles |
| relief_h / relief_in | 1.2 / 0.6 mm | relief height, leaf inset from seam |
| leaf_s0 / leaf_len / leaf_w | 3 / 38 / 7 mm | leaf start, length, half-width |
| collar_w / collar_gap | 2 / 0.5 mm | collar ring |
| led_w / led_d | 11 / 3.2 mm | LED rebate (10 mm COB strip) |
| coupon_w / coupon_h / coupon_z / stub_len | 56 / 24 / 20 / 20 mm | coupon block, rod stub |
| layout_gap, lay_ky, lay_kx | 40 / 45 / 20 mm | document layout only |

Derived: `cell_w = (space_w - 2 fit_gap)/3` = 110.83; `cell_d = rack_d -
bezel_t` = 272; `pocket_floor = ring_d - pocket_d` = 4; `rod_len = cell_d
- 2 pocket_floor` = 264; `hole_w = rod_w + 2 rod_gap` = 10.2; `post_c =
cell_w/2 - rod_w/2 - rod_in` = 47.4 (rod centre offset); `tick_z = ring_d
+ mid_z - pocket_floor` = 152 from the rod's rear end; `tile_w = cell_w -
tile_gap` = 110.53; `hole_d = pin_d + 2 fit_push + hole_comp` = 6.6;
`key_len = ring_d - key_short` = 15.5. Removed from rev 1: tongue_w,
sock_d, tongue_ch, stub_h, post_w, post_len, tongue_l, sock_w.

## Module list

| Part | Size (mm) | Orientation | Count | Material | est. g | est. h |
|---|---|---|---|---|---|---|
| ring_f | 110.8 x 110.8 x 16 (+5 pins) | face up; pockets on the bed side | 9 | PETG-CF | 55 | 0.6 |
| ring_m | 110.8 x 110.8 x 16 | flat; through holes | 9 | PETG-CF | 53 | 0.6 |
| ring_r | 110.8 x 110.8 x 16 | flat; pockets open upward | 9 | PETG-CF | 54 | 0.6 |
| rod | 10 x 10 x 264 | lying flat, tick at 152 from one end | 36 | PETG-CF | 26 | 0.3 |
| tile + 8 leaves + collar | 110.5 x 110.5 x 8 (+1.2 relief) | face up | 9 | PLA Wood + PLA Marble | 38 | 0.8 |
| key | 6 x 7.8 x 15.5 bowtie | standing | 36 (+4 spare) | PETG-CF | 0.8 | - |
| coupon, rod_stub, key_tight, key_loose | 56 x 24 x 20; 10 x 10 x 20 | flat / standing | 1 each | PETG-CF | 19 | 0.3 |

Bodies in the document (19): ring_f, ring_m, ring_r, rod, tile,
tile_leaf_1..8, tile_collar, key, key_tight, key_loose, coupon, rod_stub.

Plates (H2D 325 x 320): rings go 2 x 2 per plate (221.7 square) with up
to 8 rods lying along Y in the remaining 103 x 320 strip. R1-R4: 4 rings
+ 8 rods (422 g, 4.6 h each); R5: 4 rings + 4 rods (319 g, 3.5 h); R6:
4 rings (216 g, 2.4 h); R7: 3 rings + 40 keys + coupon + rod_stub
(215 g, 2.4 h); F, G: 4 tiles each in the 300 x 320 dual-colour zone
(152 g, 3.1 h); H: 1 tile (38 g, 0.8 h). Totals: ~2.78 kg (2.39 kg
skeleton, 0.34 kg tiles, 0.05 kg keys and coupons), ~34 h, 10 plates.
Rates from the brief: 11 h/kg at 0.6/0.3 mm, 17 h/kg + 20 % colour
overhead at 0.4/0.2 mm. Rev 1 was 2.29 kg / 28 h; the third ring and
the longer rods cost 0.5 kg and 6 h.

## Joint spec

- Cell-to-cell: double-dovetail keys, 12 deg flank, groove 7 mouth /
  8.3 base / 3 deep on every face of all three rings, key 15.5 long at
  0.25 mm per side (sliding, brief 0.20-0.30), slid in front-to-back.
  12 internal edges x 3 planes = 36 keys. Tiles cover the front mouths.
- Rod to end ring: 10 mm square rod with 1 mm 45 deg end chamfers into a
  10.2 square blind pocket 12 deep (4 mm floor), 0.5 mm mouth chamfer;
  0.1 mm per side push fit. Front ring pockets open on its bed face (the
  pocket roof is a 10.2 mm bridge); rear ring pockets open upward.
- Rod to middle ring: 10.2 square through hole, 0.1 per side; the ring's
  rear face sits on the rod's tick groove (152 from the rod's rear end).
  Held by friction and the keys; a drop of CA in each hole is optional.
- Tile to front ring: four 6 mm pins, 5 tall, into 6.6 blind holes.
- Coupon: production groove, pin hole, 10.2 pocket (chamfered, 12 deep),
  10.2 through hole; rod_stub (20 mm, chamfered) and keys at dt_clr
  -0.1 / 0 / +0.1. Print and test before any plate.

## Filament

- Skeleton: Bambu PETG-CF, 0.6 HF hardened nozzle, 0.3 mm, 250-260 C, bed
  70 C textured PEI with glue release, 4 walls, 15 % gyroid, 5
  top/bottom, 5 mm brim, dry 65 C 8 h. Budget alternative PETG HF, 5
  walls. Rods: seam aligned to one edge, 100 % solid is not needed.
- Tiles: Bambu PLA Wood Black Walnut (tile body, nozzle 1) + Bambu PLA
  Marble white (leaves, collar, nozzle 2); 0.4 nozzle, 0.2 mm, 215 C, bed
  55 C, 4 walls, 20 % gyroid, ironing on, chamber vented, dry 55 C 8 h.
  Lit alternative: Bambu PETG Translucent tiles, PETG HF white relief,
  10 mm COB strip in the 11 x 3.2 rebates behind each row seam.

## Decisions and reasons

- 3 x 3 at 110.8 pitch, 92 clear bore: the brief's mixed-cellar grid.
- Middle ring at mid_z 140 (contact 156-172 from the base): a Bordeaux
  body is cylindrical to ~195-205, so the ring sits on the body;
  Burgundy and Champagne shoulders start sloping at ~150-165, so the
  ring catches the top of the slope and those bottles sit up to ~2 mm
  lower there (about 1 deg nose-down over the 156 mm span). For a
  Burgundy-heavy cellar set mid_z 125 (contact 141-157), which still
  brackets a 320 mm bottle's CoG.
- Rods separate and flat instead of integral towers: every skeleton
  part now prints under 21 mm tall; rods are the strongest orientation
  (layers along the length) and ride in the spare strip of each plate.
- Square rods and square pockets: squares print truer than round holes
  and the rod cannot rotate. 0.1 per side is the brief's push band;
  the pocket mouth and rod end chamfers give lead-in.
- Pockets 3 mm in from the outer faces (rod_in) so a 10.2 pocket keeps a
  2.9 mm outer wall; the inner corner is 14 mm from the bore.
- Decorative field on the grid nodes (the mid-side annulus is 5 mm),
  relief extruded straight up, two colours one per nozzle, tiles in the
  300 x 320 zone. Unchanged from rev 1.
- Bed-edge chamfers left to the slicer (elephant-foot 0.15); only
  pocket mouths and rod ends are chamfered in the model.

## Risks

1. Shelf depth unknown: rack 280 deep; a 320 bottle protrudes 40 mm.
   Lower rack_d if needed; rods and tick position follow.
2. Three printed fits decide assembly: 0.1 rod, 0.25 key, 0.1 pin. The
   coupon set exists so no full plate is the test.
3. Middle ring is located by the tick and held by friction plus the
   keys to its neighbours; if a ring walks on its rods, add CA. The
   outer cells' outer faces have no neighbour, so the tick matters there.
4. The front ring's pocket roofs are 10.2 mm bridges; PETG-CF bridges
   this cleanly, but check the first ring_f plate's underside.
5. PLA tiles near an oven or in sun will soften; the skeleton will not.
6. Creep: bearing stress ~0.02 MPa, hoops loaded in XY, no PLA in the
   load path.
