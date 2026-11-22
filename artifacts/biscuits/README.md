# Dangly biscuit ornaments

Three printable biscuit characters modelled from shop photos (2026-11-22):
a round jam sandwich, a pink wafer and a custard cream. Each has two
6.5 mm sockets in its bottom edge for rope legs, two biscuit feet with
piped-cream tops, and two optional printed octagonal legs.

All three print flat, face up. Every colour is its own flush body
(inlay depth `inlay_d`, 0.6 mm) so filaments can be assigned per body.

| File | Role |
|---|---|
| `common.py` | shared art generators and Fusion helpers (feet, legs, sockets, inlays) |
| `jammie_part.py`, `wafer_part.py`, `custard_part.py` | one biscuit each |
| `make.py` | concatenates `common.py` + part into `<name>_author.py` |
| `<name>_author.bundled.py` | the artifact that ran in Fusion (kit + stub) |
| `<name>_author.bundled.log` | build output and `FH_VERDICT1` |
| `ctl.py` | session utilities: probe, undo, newdoc, paint, shot |
| `preview_art.py` | offline matplotlib preview of the 2D art |

Rebuild: `python make.py`, `python -m fusionhelper.bundle <author>`,
`python -m fusionhelper.preflight <bundled>`, then in an EMPTY Fusion
document `python run_fusion.py <bundled>` and `python ctl.py paint`.

Outline and artwork coordinates are fixed constants in the part files;
the user parameters drive thicknesses, inlay depth, relief heights,
socket size/depth and the feet and legs.

Verdicts (2026-11-22): all three `warn` only for
`dimension.literal_expression` (layout positions are literals by
design); timeline, interference and liveness pass.

## Revision 2 (2026-11-22, same day)

- Jam biscuit and custard cream: bevelled rims (`edge_fillet`,
  `under_fillet`), embossed front patterns with a bevel (`relief_h`,
  `emboss_taper`), domed dimples on the jam biscuit, rounded corners on
  the custard cream.
- Rope sockets and loose legs replaced by print-in-place ball-jointed
  legs (`jointed_legs` in `common.py`): hip socket inside the biscuit,
  knee bowl on the thigh, teardrop balls, tip relief channels, one
  break-away tab per joint. Feet still push on (`foot_hole_d`).
- `probe_joints.py` measures retention (lift), swing clash (rotate) and
  overhangs; `spike_*_part.py` are the probes behind the fillet and
  taper limits; `ctl.py` gained `docs`.

Built and verified in Fusion with jointed legs: jam biscuit only.
Wafer and custard cream artifacts are gated but not yet rebuilt with
the jointed legs (print orientation still to be decided).
