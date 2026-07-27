# Sketch-plane axis mapping

> ## Read this before the table below
>
> **This table is for diagnosing an inversion. It is never for computing a placement.**
>
> **R6 stands: derive placement from `sketch.sketchToModelSpace()` at runtime.**
>
> These numbers were measured on one machine, on one Fusion build, in one configuration.
> They are here so that when geometry comes back upside-down you can recognise the shape of
> the failure immediately. The moment you use them to decide where to draw something, you
> have hardcoded a machine-specific assumption into the user's model and you have written
> the exact bug this file exists to help you find.
>
> Two public Fusion MCP projects ship contradictory hardcoded tables — one documenting Y-up,
> the other Z-up — and both were field-derived. Do not add a third.

## The correct approach

```python
m = sk.sketchToModelSpace()      # Matrix3D: sketch space -> world
```

Read the mapping from this in the generated script and derive the placement from it. It is
correct on whatever machine the script runs on, which the table below is not.

## Measured mapping

Via `sketch.sketchToModelSpace()` on the probe machine, Fusion API 2703.1.20, Windows 11:

| Sketch plane | sketch +X → world | sketch +Y → world | Plane normal |
|---|---|---|---|
| **XY** | `(1, 0, 0)` | `(0, 1, 0)` | `(0, 0, 1)` |
| **XZ** | `(1, 0, 0)` | **`(0, 0, −1)`** | `(0, 1, 0)` |
| **YZ** | **`(0, 0, −1)`** | `(0, 1, 0)` | `(1, 0, 0)` |

Stated as rules:

- **On the XZ plane, `world_z = −sketch_y`.**
- **On the YZ plane, `world_z = −sketch_x`.**

Geometry drawn "upright" on XZ lands upside-down in world Z. To place a feature at world
height *h* on XZ you would sketch it at `y = −h` — which is precisely the arithmetic **R6**
exists to keep out of the generated script.

Autodesk has confirmed on their forums that this is by design, forced by two simultaneous
requirements: that positive extrusion on XZ goes toward +Y, and that all frames remain
right-handed. (Forum-derived; `forums.autodesk.com` returned 403 to every fetch attempt, so
this claim comes from search extracts rather than a full read.)

## Extrude direction is clean

**A positive distance always follows the plane normal.** This one is safe and needs no
derivation. The inversion is a sketch-space phenomenon, not an extrude-direction one.

## The modelling-orientation preference is not a reliable proxy either

```python
o = app.preferences.generalPreferences.defaultModelingOrientation
# adsk.core.DefaultModelingOrientations.YUpModelingOrientation == 0
# adsk.core.DefaultModelingOrientations.ZUpModelingOrientation == 1
```

**Caveat, and it is the important part of this file.** The probe machine reads **0 (YUp)**,
yet the construction planes still measured exactly as tabled above, with the XY normal at
`+Z`. The orientation preference did **not** remap the API's construction planes in this
configuration.

So querying the preference does not tell you the mapping. Only
`sketchToModelSpace()` does.

**ZUp was never tested.** Testing it would mean changing a user preference, which the probe
run declined to do. The behaviour of this table under ZUp is therefore unknown — one more
reason not to depend on it.

## Diagnosing an inversion

Symptoms that should send you here:

- A feature is at `−h` in world Z where you expected `+h`, and the magnitude is right.
- A part is mirrored about the world XY plane relative to what you intended.
- Interference reports a clash with something that should be directly above it.

The fix is never to negate a coordinate to compensate. The fix is to derive the placement
from `sketchToModelSpace()` and let it be correct on every machine (**R6**).
