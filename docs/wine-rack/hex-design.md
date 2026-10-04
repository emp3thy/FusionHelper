# Hex Eight - design note (modern direction, slug `hex`)

One hexagonal ring, printed flat, sixteen times. A 3-2-3 honeycomb of
pointy-top rings in two plates (back and front), tied by nineteen
identical double-dovetail keys that run the full rack depth, standing on
a zig-zag plinth rail. Eight bottles, three part types, one colour.

Files: `artifacts/wine-rack/hex_author.py` (author), `hex_author.bundled.py`
(gated artifact, preflight PASS exit 0), `artifacts/wine-rack/hex.html`
(design page). Fusion execution and the numeric verdict are pending (no
Fusion MCP in this session).

## Decisions and reasons

| Decision | Reason |
|---|---|
| Hex 3-2-3 (8 bottles) rather than 3 x 3 square (9) | A pointy-top cell is a 120-degree V-cradle: two-line contact and self-centring for 74-96 mm bottles, nothing rolls, no saddle insert. The middle row bears on the diagonal flats of the row below in compression; the load stays in the hoop of a flat-printed ring (XY). Cost: one bottle (11 %). |
| Pitch 110 = (332 - 2) / 3, wall 7, slot 96 | Width governs: 3 x 110 = 330 in a 332 envelope. 96 clear across flats takes every standard 750 ml incl. 93 mm Burgundy and 88-91 Champagne; 14 mm web (two 7 mm walls) is inside the brief's <= 12 mm-per-wall budget at this pitch. Height 6 x 31.75 + 127 + 6 = 323.5 < 332. |
| Two 30 mm ring plates at z 0-30 and 150-180, rack depth 180 | Full-bottle CoG at 130-145 mm sits between the bands; the front band's rear edge (144) is still on the cylindrical body of a Burgundy, so bottles sit level and the shoulder is caught by the front ring (cannot slide forward). A 320 bottle reaches 320 from the back of a ~390 cube. `rack_d` is the single knob if the cube is shallower (min 150). |
| Full-depth keys as the only depth members | 19 bow-tie keys of 174 mm tie back ring to front ring through 27 mm of blind groove at each end. One key part for every joint (13 ring-ring, 6 ring-rail). Rings are flip-symmetric, keys end- and side-symmetric: no wrong orientation exists. |
| Blind grooves (3 mm floor at the show face) | Hides every key end, makes keys captive, keeps the show-face hex edges continuous for the chamfers, and puts the groove mouth on the top of the print (no bed-side holes). |
| Prismatic dovetail, 0.25 mm/side, no taper | Brief: sliding dovetail 0.20-0.30. Keys print flat with flank layer lines along the slide; ring grooves are vertical so their 0.3 mm layer ridges are across the slide, which the 0.25 covers. Taper omitted because the blind floor already locates the key; a tapered double-ended key needs a bulged mid-section (offset math shown in the author script history) and buys nothing on a gravity-held lattice. Coupon tunes `dt_gap`. |
| Zig-zag base rail (plinth), 2 off, 330 x 37.75 x 30 | Pointy-top rings stand on vertices; the rail gives a flat foot, ties the bottom row horizontally (brief: a tie per layer or users report tipping) and is the one non-hex line. Prints on the bed diagonal (330 long, 38 wide, inside the 121 mm rule). |
| Chamfers: 1 mm reveal outside, 2.5 mm flare inside, show face only | The 1 mm bed-side chamfer kills elephant foot and, where two rings meet, becomes a 2 mm V reveal at every seam - the only "detail" on the face. The flare takes a 101 mm entry to the 96 slot. Both are 45-degree overhangs on the bed side, the brief's recommended bed-edge treatment. |
| PETG-CF Black, 0.6 HF nozzle, 0.3 layers, 5 walls | Stiffest easy-print option (2910 MPa), satin hides layers, no chamber heat. 7 mm walls become solid perimeter so the load path is all wall. Keys hidden: any PETG. Optional free two-tone: rails in white. |
| 7 plates, ~2.0 kg, ~20 h | 4 ring plates (4 rings each), 2 key plates (10 + 9 + coupon), 1 rail plate. 250 g / 2.5 h per bottle: heavier than the brief's 100-150 g target (solid 7 mm walls), well under its 4-8 h. `wall_t` 6 saves ~200 g and keeps a 98 slot. |

## Parameter table (Fusion user parameters)

| Name | Default | Drives |
|---|---|---|
| space_w | 335 mm | opening width and height |
| fit_gap | 1.5 mm | clearance per side to the opening |
| edge_gap | 1 mm | honeycomb-to-envelope reveal per side |
| wall_t | 7 mm | ring wall (two rings meet as a 14 mm web) |
| ring_d | 30 mm | ring depth = print height; rail depth |
| floor_t | 3 mm | blind-groove floor behind the show face |
| rack_d | 180 mm | overall depth, back face to front face |
| dt_neck / dt_d / dt_ang | 10 mm / 4 mm / 20 deg | dovetail neck, depth per side, flank angle |
| dt_gap | 0.25 mm | groove clearance per side (coupon tunes this) |
| grv_over | 0.6 mm | groove profile overshoot outside the flat |
| base_t | 6 mm | rail thickness under a ring vertex |
| ch_reveal / ch_flare | 1 mm / 2.5 mm | show-face chamfers |
| cp_w / cp_h / cp_key_len | 30 / 20 / 40 mm | tolerance coupon |
| lay_gap / lay_key_x / lay_rail_y / lay_cp_y | 6 / 220 / 250 / 250 mm | document layout only |
| rack_w | space_w - 2 fit_gap = 332 | envelope |
| pitch | (rack_w - 2 edge_gap) / 3 = 110 | cell pitch = ring outer flat-to-flat |
| slot_clear | pitch - 2 wall_t = 96 | clear slot across flats |
| hex_r / hex_ri / hex_v | 63.5 / 55.4 / 127.0 | outer, inner circumradius; vertex-to-vertex |
| notch_h | hex_r / 2 = 31.75 | lower-flat rise; row spacing = 3 notch_h |
| rack_h | 6 notch_h + hex_v + base_t = 323.5 | overall height (script refuses > rack_w) |
| key_len | rack_d - 2 floor_t = 174 | key length |
| dt_base | dt_neck + 2 dt_d tan(dt_ang) = 12.91 | dovetail base width |
| grv_d / grv_neck / grv_base | 4.25 / 10.53 / 13.63 | groove = key offset by dt_gap |
| grv_cut | ring_d - floor_t = 27 | groove depth from the mouth |
| rail_w / rail_h | 3 pitch = 330 / base_t + notch_h = 37.75 | base rail |

The script also refuses to build if `slot_clear` < 92 mm.

## Module list

| Part | Size (mm) | Print orientation | Qty | Plate | g each |
|---|---|---|---|---|---|
| hex_ring | 110 x 127 x 30 | show face (floor side) on the bed, groove mouths up | 16 | A-D, 4 per plate | 85 |
| hex_key | 174 x 12.9 x 8 | flat, wide base down, length along X | 19 (+1 spare) | E (10), F (10) | 20 |
| hex_rail | 330 x 37.75 x 30 | flat, on the bed diagonal, 5 mm brim | 2 | G | 145 |
| hex_coupon_block / hex_coupon_key | 30 x 20 x 30 / 40 x 12.9 x 8 | as ring / as key | 1 + 1 | with F | 23 + 5 |

Totals: 40 parts, 7 plates, ~1.99 kg, ~20 h at 0.6 mm / 0.3 mm (~30 h at
0.4 / 0.2). The Fusion document holds one plate of rings (4), one plate of
keys (10), both rails and the coupon: 18 bodies.

## Joint spec

- Double-dovetail (bow-tie) key: neck 10 at the interface, base 12.91,
  4.0 mm into each wall, flanks 20 degrees from the depth axis.
- Groove: key offset outward by 0.25 mm per side: opening 10.53 at the flat,
  base 13.63, depth 4.25; 2.75 mm of wall remains behind it. Cut 27 mm from
  the mouth, blind 3 mm behind the show face. Six per ring (circular pattern
  of one cut), six per rail (mirror pair patterned x3 at `pitch`).
- Engagement 27 mm per ring end; key spans 120 mm between plates.
- No backwards: key symmetric end-to-end and side-to-side; ring symmetric when
  flipped (back plate rings face forward, front plate rings face back).
- Coupon: block with one groove + 40 mm key. Slides home by hand with no
  seated play -> print at 0.25; mallet -> 0.35; rattles -> 0.15-0.20; binds
  near the floor -> elephant-foot compensation 0.2 or chamfer the key base.

## Filament and settings

Bambu PETG-CF Black (alternative PETG HF White or ASA White; rails in white
as a free accent). 0.6 HF hardened nozzle, 0.30 mm layers, 5 walls (3.0 mm),
Arachne, 30 % gyroid (rails only have any), 6 top / 6 bottom, 255 C / bed
70 C textured PEI with glue-stick release, chamber closed unheated, part fan
low, seam aligned rear (lands on a hex vertex), elephant-foot 0.15, no
supports, no brim except 5 mm on the diagonal rails, dry 65 C / 8 h.

## Assembly

Rail 1 show-face down; 6 keys in its grooves; bottom row of 3 rings on;
2 + 4 keys; middle row of 2; 1 + 4 keys; top row of 3. Place rail 2 and the
8 front rings over the key ends, bottom row first, press to the floor.
Stand up, bumpers under the rails, slide to the back of the cube. Retained
by the 332 envelope, 180 depth and 12 kg of bottles.

## Risks

1. Cube depth unknown: set `rack_d` = cube depth - 150 (min 150).
2. Fit: 19 keys at 0.25 mm; print the coupon first; the front plate engages
   up to six keys at once.
3. Chamfer features on the hex / zig-zag loops may error in the timeline
   (runtime, unverified); fall back to 0.6 mm or slicer compensation.
4. Rails on the diagonal need manual placement in Bambu Studio.
5. Grams per bottle (250) above the brief's target; `wall_t` 6 is the lever.
6. A bottle pulled 40 mm forward moves its CoG past the front ring.
