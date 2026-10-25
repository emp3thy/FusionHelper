# Pot lid (pot_lid_std)

Lid for a celadon pottery jar. Ø73.5 tapered collar, open annular groove
underneath that drops over the pot's rim, concentric relief on top.

**Provenance.** The original authoring script and its `feature/potlid`
branch lived only on a PC that a BIOS update bricked on 2026-10-04; they were
never pushed. Two things survived: the printer's sliced archive
`pot_lid.gcode.3mf` (Bambu Studio 02.07.01.57, H2C, 0.16 mm layers, sliced
2026-09-13 from `pot_lid_std.step`) and the design-intent artifact
[Pot Lid Relief Options](https://claude.ai/artifact/Dy8yfSY1tPcDcQ6M2bWiHy).
`pot_lid_author.py` is a rebuild from those: the part is a solid of
revolution, so every wall loop in the gcode is a point on the profile.

## Files

| File | What |
|---|---|
| `pot_lid_author.py` | Authoring script. Parameter table at the top, one fixed-art profile, one revolve, Pappus volume oracle. **Source of truth.** |
| `pot_lid_author.bundled.py` | Bundled artifact (buildkit inlined, verification stub appended). What is sent to Fusion. Generated, not committed: run the bundle command below. |
| `check_profile.py` | Offline check: Pappus volume, key dimensions, simple-polygon test, and deviation of the printed walls from the profile. Writes `profile_vs_printed.png`. |
| `gcode_section.py` | Recovers the (r, z) section of any rotationally symmetric print from a Bambu `.gcode.3mf`. Writes `printed_section.csv/.png`. |
| `pot_lid.gcode.3mf` | The printer's archive. Printable as-is; the only surviving copy of the original geometry. |
| `printed_section.png` | Section recovered from that archive. The matching `.csv` that `check_profile.py` reads is generated, not committed: run `gcode_section.py` first. |
| `profile_vs_printed.png` | The rebuilt profile over the printed walls. |
| `render_*.png` | Fusion screenshots of the rebuilt body. |

## Rebuild

```
python -m fusionhelper.bundle artifacts/pot-lid/pot_lid_author.py
python -m fusionhelper.preflight artifacts/pot-lid/pot_lid_author.bundled.py   # must exit 0
python artifacts/pot-lid/check_profile.py                                        # offline oracle
```

Then, with Fusion running (MCP server at `http://127.0.0.1:27182/mcp`) and a
new empty document active, run a loader through `fusion_mcp_execute`:

```python
ARTIFACT = r"C:\Users\gethi\sources\FusionHelper\artifacts\pot-lid\pot_lid_author.bundled.py"

def run(_context: str):
    with open(ARTIFACT, encoding="utf-8") as f:
        src = f.read()
    ns = {"__name__": "fh_bundled"}
    exec(compile(src, ARTIFACT, "exec"), ns)
    ns["run"](_context)
```

The script prints its own Pappus volume, the Fusion body volume and the
bounding box, and raises if they disagree. The verification stub then prints
`FH_CHECK1` lines and one `FH_VERDICT1` line.

## Result on 2026-10-04

Green on the first execute: one body `pot_lid`, Fusion volume 41.2919 cm³
against Pappus 41.2914 cm³ (0.001 %), bbox 73.54 × 73.54 × 14.04 mm,
constraints and timeline pass. Liveness is skipped by design (no user
parameters: the profile is fixed art driven from the table). Against the
printed walls the profile deviates by 0.16 mm mean (p95 0.42 mm); the top
skin by 0.18 mm mean. The one band above 0.8 mm is the top outer edge, where
the print's round is fuller than the artifact's R2.5.

## Changing the fit

The groove is the only fit-critical feature. In the parameter table:
`PLUG_R` (inside the pot's rim), `GROOVE_R0` (outside the rim, at the base),
`GROOVE_DEPTH`, and `DRAFT_DEG` (both collar faces lean by this). Edit, then
re-bundle, re-gate, re-run. See `docs/pot-lid/design.md` for what each number
was measured from and how sure it is.
