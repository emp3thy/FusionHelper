# Spinner build scripts

Recovered from a session scratchpad that no longer exists. These are the only
way to rebuild any of the designs, so treat them as source.

Read `docs/fidget-spinner-handoff.md` first. Every script is an authoring
script: bundle it, preflight it, then execute the bundled artifact through a
loader.

```
python -m fusionhelper.bundle artifacts\spinner-scripts\<name>.py
python -m fusionhelper.preflight artifacts\spinner-scripts\<name>.bundled.py
```

## Current

| Script | Builds |
|---|---|
| `or3_build.py` | Orrery mk3 — double-mesh ring, planets inside and outside. **The live design.** |
| `supernova3_author.py` | Supernova 72 rev C/D — twin V-ways, open-top slots |
| `supernova3_component.py` | packages rev D bodies into one component |
| `ornament_supernova3.py` | rev D engraving |

## Earlier designs, still buildable

| Script | Builds |
|---|---|
| `supernova2_author.py` + `ornament_supernova2.py` | rev B — **the design that was physically printed** |
| `or2_lib.py`, `or2_build.py`, `or2_parts.py` | Orrery mk2, inner mesh only |
| `orrery_stator2.py` | mk1 stator; the reference implementation of the fast idempotent gear technique |
| `haywire_p1/p2/p3.py`, `haywire_fix.py` | Haywire Gearworks 76 |
| `cicada_author.py`, `ornament_cicada.py` | Cicada 75 — no archive exists, script only |
| `pulsar_p1.py`, `pulsar_p2.py`, `ornament_pulsar.py` | Pulsar Bloom 78 |
| `pentaroule_author.py`, `comet_author.py` | two of the five lost designs |
| `pentaroule_pip_author.py`, `comet_pip_author.py` | their print-in-place variants |
| `vernier_author.py`, `governor_author.py` | the remaining lost designs |

## Probes and analysis

Reusable, not tied to one design.

| Script | Does |
|---|---|
| `overhang_probe2.py` | sweeps faces for `normal.z < -0.7075` (steeper than 45° overhang) |
| `vway_probe.py` | measures V-way engagement and play |
| `planet_gap_probe.py`, `orrery_probe.py` | planetary mesh and clearance |
| `abs_probe.py` | confirmed the `bound_rect2` sign bug |
| `gapforensics.py`, `bodyprofile.py`, `zray.py` | clearance and cross-section forensics |
| `meshlib.py`, `analyze.py`, `measure.py`, `batch.py`, `rasterlib.py` | trimesh scanning of the downloaded competitor corpus |
| `refgear.py` | teardown of the reference `Gear+fidget+spinner.3mf` (the committed `.out` is a failed run; the useful table is in the handoff doc) |

Superseded intermediates (`*_fix*.py`, `orrery_p1..p5.py`, `pulsar_continue.py`,
`supernova_author.py`, `orrery_stator.py`) are kept because they document what
was tried and why it was replaced.
