# Quiet Nine - design note (slug `quiet`, direction: unobtrusive)

A nine-bottle 3 x 3 insert that sits at the BACK of the 335 x 335 cube and
disappears behind the bottles. 164 mm deep, matte grey ASA, no frame, no
fastener, no pattern. Every part prints flat with the ring hoop in XY.

Files: `artifacts/wine-rack/quiet_author.py` (author),
`artifacts/wine-rack/quiet_author.bundled.py` (gated artifact, preflight
PASS exit 0), `artifacts/wine-rack/quiet.html` (design page). Fusion
execution and numeric verification are pending (no Fusion MCP this session).

## Decisions and reasons

| Decision | Reason |
|---|---|
| Short rack at the back of the cube (164 deep) rather than a flush 280-300 insert | The cube is ~390 deep and a bottle 300-330 long; the rack never needs to reach the face. From the front only shoulders and necks show - the literal reading of "disappear". In a 335-deep niche bottles still end flush (357 flutes protrude 25). `half_d` is the lever. |
| 3 x 3 at pitch = (335 - 2 x 1.25) / 3 = 110.83 | The brief's mixed-cellar grid; 4 x 4 is Bordeaux-only, 2 x 2 wastes the cube. |
| Bore 94, 5 mm 45-degree flare to 104 at the face | >= 92 floor; Burgundy to 93 and standard Champagne fit; wall 8.4 (<= 12). The flare thins the visible land to 3.4 mm so the lattice reads as lines, and is exactly the overhang limit printed face-down. |
| Two rings + four corner ribs per cell, split into two 82 mm halves | Rings on the bed carry the load in XY; two 82 mm halves avoid a 164 mm tall thin-column print and any ring underside overhang. Half-cells are 2 x 2 per plate. |
| Front ring centred 155 mm from the bottle base | Ahead of the full-bottle CoG (130-145) and still under the cylindrical body of Bordeaux, Burgundy and Champagne shapes. |
| Rear bore dropped 4 mm (`rear_drop`) | A bottle whose shoulder taper has started by the front ring still sits level or ~1.5 deg neck-up, never neck-down. Rear bottom wall stays 4.4 mm (the ring carries almost nothing). |
| Rear ring carries a 70 mm stop plate, 3 mm | KALLAX-class cubes are open-backed; a bottle must not be pushable through. 70 < any base (74+). |
| Rear ribs are 12 mm hollow square tubes (2.4 wall, 7.2 bore); the bore IS the peg socket | No boss, no overhang; 4 x 0.6 mm walls. Front ribs 10 mm solid with a 6.7 mm square peg, 10 long, 1 mm chamfer. |
| Ring-to-ring "bone" keys (two 8 mm discs at +-5.5, 5 mm neck) in sockets open at the ring top, blind 2 mm at the visible face | Keyed double-disc resists pull-out by shoulders, not by a tab; slides in along print Z so flanks are XY perimeters; nothing shows on the front. Socket at +30 mm from each side centre so every cell is identical (translation-symmetric). |
| Retention in the opening: 1.25 mm gap per side + 2 mm felt pads | Positive push fit without screws; the slab is boxed in by the cube walls so it cannot tip. |
| ASA grey (alt PETG matte) | Matte neutral, no yellowing, HDT 100 C. Stresses are < 1 % of yield (bottom-row rings see 5.1 kg over a full square perimeter), so creep is not the governing case. |

## Parameter table (Fusion user parameters)

| Name | Default | Drives |
|---|---|---|
| `space_w` | 335 mm | opening; `rack_w = space_w - 2 * fit_gap` |
| `fit_gap` | 1.25 mm | clearance per side |
| `n_cells` | 3 | `pitch = rack_w / n_cells` = 110.83 |
| `slot_clear` | 94 mm | bore; `ring_wall = (pitch - slot_clear) / 2` = 8.42 |
| `flare` | 5 mm | 45-degree entry chamfer, front bore |
| `rear_drop` | 4 mm | rear bore offset down |
| `stop_bore`, `stop_t` | 70, 3 mm | base stop plate |
| `ring_d` | 12 mm | ring depth |
| `half_d` | 82 mm | half-cell depth; `cell_d = 2 * half_d` = 164 |
| `sock_w`, `rib_t` | 7.2, 2.4 mm | peg bore, rear rib wall; `rib_w = sock_w + 2 * rib_t` = 12 |
| `frib_w` | 10 mm | front rib (solid) |
| `peg_gap`, `peg_l`, `peg_ch`, `sock_ch` | 0.25, 10, 1, 0.8 mm | `peg_w = sock_w - 2 * peg_gap` = 6.7 |
| `key_d`, `key_neck`, `key_in`, `key_off` | 8, 5, 5.5, 30 mm | bone key and socket position |
| `key_blind`, `dt_gap`, `key_slack` | 2, 0.2, 0.3 mm | `key_len = ring_d - key_blind - key_slack` = 9.7 |
| `edge_ch` | 1.5 mm | outer vertical corner chamfer |
| `gap_step`, `coup_w`, `coup_t`, `coup_pitch`, `cpeg_t` | 0.1, 18, 12, 18, 3 mm | coupon; `coup_l = 7 * coup_pitch` |
| `lay_gap`, `cell_cy`, `cell_a_x`, `cell_b_x`, `key_x`, `coup_x`, `cpeg_y` | derived | module layout in the document |

## Module list

| Body | Count | Size (mm) | Print orientation | g (est.) |
|---|---|---|---|---|
| `quiet_rear` | 9 | 110.8 x 110.8 x 82 | stop plate on the bed, ribs up | 82 |
| `quiet_front` | 9 | 110.8 x 110.8 x 92 | flare on the bed, pegs up | 65 |
| `quiet_key` | 24 (+3 coupon) | 19 x 8 x 9.7 | flat | 1.2 |
| `quiet_coupon` + `quiet_coupon_peg` | 1 + 1 | 126 x 18 x 12 | flat | 30 |

Totals: rack ~1.35 kg (150 g per bottle position), with coupon ~1.39 kg;
6 plates, ~23 h at 0.4 / 0.2 mm (~14 h at 0.6 / 0.3 mm). Plate plan:
P0 coupon + 3 keys; P1, P2 4 x rear; P3 1 rear + 3 front; P4 4 x front;
P5 2 x front + 24 keys.

## Joint spec

| Joint | Geometry | Clearance / side |
|---|---|---|
| Half to half | 6.7 sq peg x 10, 1 mm tip chamfer, into 7.2 sq rib bore with 0.8 mouth chamfer; 4 per cell | 0.25 (loose push: 36 engage at once) |
| Ring to ring | bone key 8 / 5 / +-5.5, 9.7 tall; socket 8.4 / 5.4, 10 deep, 2 mm floor; 12 per ring plane | 0.20 (sliding along print Z) |
| Rack to cube | 332.5 envelope, 8 + 2 felt pads 2 mm | 1.25 |

Coupon: three key sockets at `dt_gap` -0.1 / 0 / +0.1 and three peg bores
at `peg_gap` -0.1 / 0 / +0.1, plus one loose peg and three keys.

## Filament

Primary Bambu ASA (grey / white / black): 0.4 hardened nozzle, 0.2 mm,
6 walls, 30 % gyroid, 5/5 top-bottom, 260 C / bed 95-100 C / chamber
55-60 C preheated, textured PEI + glue, 5 mm brim with 0 gap, cooling
<= 30 %, dry 80 C 8 h. Alternative Prusament PETG Matte or Bambu PETG HF
dark: 250 C / 70 C, lid vented, no chamber heat, dry 65 C 8 h.

## Build script notes

- Five unique bodies laid out side by side on XY in print orientation
  (rear half at the origin corner, then front half, key, coupon strip,
  coupon peg) so the stub's interference check is meaningful and the body
  count stays at 5.
- Rings are one extrude each of the annulus profile picked by area
  (rect + circle in one sketch), so no bore cut and no cut-direction
  ambiguity. Every join/new-body is predicate-validated on volume and
  bed contact; cuts on removed volume.
- Chamfers via `createInput2` with edge sets selected by geometry
  (circle at z = 0 with the bore radius; lines at the peg tip height;
  Z-parallel lines at the four corners).
- First gate run returned exit 3 (pyright module not found) and an
  identical rerun passed; treat a first exit 3 as possibly transient.

## Risks

1. Cube depth is unknown; the back-of-cube concept assumes ~390.
2. Front support may land on the shoulder taper of short-bodied bottles;
   the 4 mm rear drop covers 4 mm of taper. Check the fattest short bottle.
3. One clearance repeats 36 (pegs) and 24 (keys) times: print the coupon
   first, from the same spool and plate temperature as the halves.
