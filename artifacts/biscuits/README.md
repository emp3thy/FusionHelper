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

Revision 3 (same day): all three biscuits rebuilt on one leg design
(knee bowl r 6.7, hip recess r 4.1) and verified: timeline,
interference and liveness pass; `probe_joints.py` reads 0.0 mm3 clash
at 30/60/90 deg swing and 2.6 mm3 lip engagement at 1 mm lift on each.
Rosy cheeks (jam biscuit, wafer) are spherical caps 0.9 mm proud
(`domed_cheeks`). Print orientation: on the back, legs straight up.
Not yet print-tested.

## Revision 4 (2026-11-22)

- Eyes and smile sit `face_sink` (1.2 mm) below the face; the colour is
  the bottom `inlay_d` of the pocket.
- Foot biscuits have bevelled rims (`foot_fillet`, bed edge at 0.4x).
- Pink wafer is four pink sheets (`wafer_1..4`) with three white cream
  layers (`wafer_cream_1..3`) set back `groove_d`; its legs are painted
  white by `ctl.py paint`.
- Post-build steps per document: `ctl.py paint`, then `ctl.py group`
  (cookie component + Feet component).
- `ctl.py activate jam|wafer|custard` finds a document by its bodies;
  `ctl.py undoall` rolls the active document back to empty for a
  rebuild. Do not switch Fusion tabs during a build: verify reads the
  active document.

## Revision 5 (2026-11-22)

Custard cream relief softened: swirl and tendril outlines are closed
splines (`CC_SMOOTH`), and each embossed set has its ridge tops rounded
by `CC_TOP_ROUND` (0.25 mm) via `soften_new_tops`. `spike_soften_part.py`
is the measurement behind it (polyline swirls take 0.12 mm at most,
spline swirls 0.3 mm). Jam biscuit and wafer geometry unchanged.

Revision 6: the jam biscuit gets the same treatment - rim ring and
splat arms (now spline outlines) have their tops rounded by
`JM_TOP_ROUND` (0.25 mm).
