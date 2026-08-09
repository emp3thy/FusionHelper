# Douady Helix Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `fractalvase` package that generates the Douady Helix vase as a slicer-ready 3MF, gated on mesh validity.

**Architecture:** A pure-numpy field layer (Julia escape time on a Koenigs-centred log-polar grid) feeds a profile layer (radius and relief as functions of height), which feeds a surface layer (structured `(θ,z)` grid → manifold shell). Holes are cut last, by boolean subtraction of pointed-arch prisms. A validation gate runs before export and fails loudly rather than emitting a broken mesh.

**Tech Stack:** Python 3.12, numpy 2.3.3, scipy 1.17.0, trimesh 4.11.5, manifold3d (new), pytest, ruff, pyright.

**Spec:** `docs/superpowers/specs/2026-08-09-fractal-julia-vase-design.md`

## Global Constraints

- Python `>=3.12`. Ruff `line-length = 100`, `select = ["E","F","I","B","UP","SIM"]`. Pyright `typeCheckingMode = "basic"`.
- `from datetime import UTC` not `timezone.utc`; `StrEnum` not `(str, Enum)` — ruff UP017/UP042 on py3.12.
- All geometry in **millimetres**. Build envelope 135 × 135 × 300 mm, hard limit.
- Deliverable is geometry only: a closed shell with a **2.0 mm wall**. Do not encode slicer settings (infill, perimeters, layer height) anywhere in the package.
- Every fractal constant comes from `fractalvase.config`, never a literal at a call site.
- `trimesh.Trimesh.remove_degenerate_faces()` **does not exist** in 4.11.5. Use `m.update_faces(m.nondegenerate_faces(height=1e-8))`.
- New third-party dependency `manifold3d` is permitted and required (decision C1-B). No others without asking.

## Guardrails

| Guardrail | Confidence | Obligation in this plan |
|---|---|---|
| Keep website and README in sync with every code change | 1.00 (22 uses) | Task 7 updates `README.md` "What ships" table and `docs/README.md`. Not deferrable to a follow-up PR. |
| Spec-provided code is not lint-clean by default | standard | Every task runs `ruff check` before its commit step. Plan code below was written against the repo's rule set but must still be checked. |
| Verify-before-commit applies to internal patterns too | standard | Task 1 reads `fusionhelper/buildkit.py` for the repo's module conventions before writing new modules. |
| Cross-read prose and example code for contradictions | standard | The spec's §2.3 was already corrected once for exactly this. Task 2 asserts the corrected mapping numerically. |

---

## File Structure

| File | Responsibility |
|---|---|
| `fractalvase/__init__.py` | Public exports: `VaseConfig`, `DOUADY_HELIX`, `build_vase` |
| `fractalvase/config.py` | Frozen dataclass of every constant; derived Koenigs quantities as properties |
| `fractalvase/julia.py` | Smooth escape time, Koenigs-centred log-polar map, normalised field, band-limiting |
| `fractalvase/profile.py` | `r0(z)` from breakpoints, smoothing, `A(z)` relief envelope, slope checks |
| `fractalvase/surface.py` | `(θ,z)` grid → vertices/faces; outer, inner, rim, base; closed shell |
| `fractalvase/holes.py` | Threshold → components → pointed-arch cutter prisms → boolean difference |
| `fractalvase/validate.py` | The mesh gate. Raises rather than returns. |
| `fractalvase/__main__.py` | CLI: build and export |
| `tests/test_fractalvase_*.py` | One test module per source module |

---

## Task 1: Package scaffold, config, and constants regression

**Confidence: 95 %** — pure arithmetic against figures already verified twice on this machine.

**Files:**
- Create: `fractalvase/__init__.py`, `fractalvase/config.py`
- Create: `tests/test_fractalvase_config.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Consumes: nothing.
- Produces: `VaseConfig` frozen dataclass with fields `c, zeta_min, nu_ref, max_iter, escape_r, periods, band_lo, band_hi, height, wall, relief_peak, relief_peak_z, pierce_threshold, n_theta, n_z, invert_scale`; properties `alpha, mu, ln_mu, arg_mu, period, k, twist_rate_rad_per_mm`. Module constant `DOUADY_HELIX: VaseConfig`.

- [ ] **Step 1: Read the repo's module conventions**

Read `fusionhelper/buildkit.py` (first 60 lines) and `fusionhelper/telemetry.py` to see how this repo writes module docstrings, type hints, and constants. Match that style. Do not invent a new one.

- [ ] **Step 2: Write the failing test**

Create `tests/test_fractalvase_config.py`:

```python
"""The spec's constants are load-bearing. A silent change here changes the vase."""
import math

import pytest

from fractalvase.config import DOUADY_HELIX, VaseConfig


def test_alpha_is_the_repelling_fixed_point():
    cfg = DOUADY_HELIX
    # alpha must satisfy alpha^2 + c = alpha
    assert abs(cfg.alpha**2 + cfg.c - cfg.alpha) < 1e-12


def test_koenigs_constants_match_spec():
    cfg = DOUADY_HELIX
    assert cfg.alpha.real == pytest.approx(1.2765819495, abs=1e-9)
    assert cfg.alpha.imag == pytest.approx(-0.4796660549, abs=1e-9)
    assert abs(cfg.mu) == pytest.approx(2.7274464232, abs=1e-9)
    assert cfg.arg_mu == pytest.approx(-0.3594214440, abs=1e-9)
    assert cfg.ln_mu == pytest.approx(1.0033657954, abs=1e-9)


def test_scale_ratio_is_within_a_percent_of_e():
    # the design rests on this: the ornament ratio is inherited, not chosen
    assert abs(abs(DOUADY_HELIX.mu) / math.e - 1.0) < 0.005


def test_mapping_constants():
    cfg = DOUADY_HELIX
    assert cfg.period == pytest.approx(50.0)
    assert cfg.k == pytest.approx(0.0200673, abs=1e-7)
    # twist rate reproduces section 3.4 independently
    assert math.degrees(cfg.twist_rate_rad_per_mm) == pytest.approx(-0.4119, abs=1e-4)
    assert math.degrees(cfg.arg_mu) * cfg.periods == pytest.approx(-82.37, abs=0.01)


def test_c_is_inside_the_mandelbrot_set():
    """Outside M means Cantor dust: zero area, nothing to build a wall from."""
    z = 0j
    for _ in range(2000):
        z = z**2 + DOUADY_HELIX.c
        assert abs(z) <= 4.0, "critical orbit escaped: c is outside M"


def test_scale_ladder_stops_above_the_minimum_ridge():
    cfg = DOUADY_HELIX
    size = 116.0
    levels = []
    while size >= 1.0:
        levels.append(size)
        size /= abs(cfg.mu)
    assert len(levels) == 5
    assert levels[-1] == pytest.approx(2.096, abs=0.001)


def test_config_is_frozen():
    with pytest.raises(Exception):
        DOUADY_HELIX.c = 0j  # type: ignore[misc]


def test_envelope_is_respected_by_construction():
    cfg = VaseConfig()
    assert cfg.height <= 300.0
    assert cfg.band_lo < cfg.band_hi <= cfg.height
```

- [ ] **Step 3: Run it to confirm it fails**

Run: `python -m pytest tests/test_fractalvase_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fractalvase'`

- [ ] **Step 4: Write the config module**

Create `fractalvase/config.py`:

```python
"""Every constant the Douady Helix vase is built from.

Derived quantities are properties, not stored fields, so a change to ``c``
propagates rather than leaving stale Koenigs data behind. See
docs/superpowers/specs/2026-08-09-fractal-julia-vase-design.md.
"""

from __future__ import annotations

import cmath
from dataclasses import dataclass


@dataclass(frozen=True)
class VaseConfig:
    """Geometry and field parameters. All lengths in millimetres."""

    # --- the set ---
    c: complex = -0.123 + 0.745j
    max_iter: int = 100
    escape_r: float = 128.0

    # --- log-polar mapping (spec 2.3) ---
    zeta_min: float = 0.02
    nu_ref: float = 12.0
    periods: int = 4
    invert_scale: bool = False

    # --- envelope and bands ---
    height: float = 300.0
    band_lo: float = 40.0
    band_hi: float = 240.0
    wall: float = 2.0

    # --- relief envelope A(z) (spec 3.1) ---
    relief_peak: float = 7.0
    relief_peak_z: float = 130.0

    # --- piercing (spec 3.3) ---
    pierce_threshold: float = 0.62
    min_ligament: float = 2.0
    max_hole_span: float = 12.0
    arch_apex_deg: float = 45.0

    # --- sampling (spec 4) ---
    n_theta: int = 640
    n_z: int = 500

    @property
    def alpha(self) -> complex:
        """Repelling fixed point of z^2 + c."""
        return (1 + cmath.sqrt(1 - 4 * self.c)) / 2

    @property
    def mu(self) -> complex:
        """Koenigs multiplier. |mu| is the ornament scale ratio."""
        return 2 * self.alpha

    @property
    def ln_mu(self) -> float:
        return float(cmath.log(abs(self.mu)).real)

    @property
    def arg_mu(self) -> float:
        return float(cmath.phase(self.mu))

    @property
    def band(self) -> float:
        return self.band_hi - self.band_lo

    @property
    def period(self) -> float:
        """Vertical distance over which the pattern reproduces itself."""
        return self.band / self.periods

    @property
    def k(self) -> float:
        """Log-polar rate. One period advances u by exactly ln|mu|."""
        rate = self.ln_mu / self.period
        return -rate if self.invert_scale else rate

    @property
    def twist_rate_rad_per_mm(self) -> float:
        """Screw component: rising one period rotates by exactly arg mu."""
        return self.arg_mu / self.period


DOUADY_HELIX = VaseConfig()
```

Create `fractalvase/__init__.py`:

```python
"""Generator for the Douady Helix fractal Julia vase."""

from fractalvase.config import DOUADY_HELIX, VaseConfig

__all__ = ["DOUADY_HELIX", "VaseConfig"]
```

- [ ] **Step 5: Wire the package into the build and the gates**

In `pyproject.toml`, make exactly these four edits:

1. Under `[project.optional-dependencies]`, add a new extra beneath the existing `dev` line:
```toml
vase = ["numpy>=2.0", "scipy>=1.14", "trimesh>=4.11", "manifold3d>=3.0", "lxml>=5.0"]
```
2. Under `[tool.hatch.build.targets.wheel]`, change `packages = ["fusionhelper"]` to:
```toml
packages = ["fusionhelper", "fractalvase"]
```
3. Under `[tool.pyright]`, change `include = ["fusionhelper", "tests"]` to:
```toml
include = ["fusionhelper", "fractalvase", "tests"]
```
4. Leave `[tool.ruff] extend-exclude` alone — `fractalvase` is library code and must be linted.

- [ ] **Step 6: Install the new dependency**

Run: `pip install -e ".[vase]"`
Expected: succeeds, `manifold3d` installs. If it fails to build a wheel on this Windows/Python 3.12 combination, **stop and report** — that failure invalidates decision C1-B and the plan needs revisiting, it is not something to work around silently.

- [ ] **Step 7: Run the tests and the gates**

Run: `python -m pytest tests/test_fractalvase_config.py -v`
Expected: 8 passed.

Run: `python -m ruff check fractalvase tests/test_fractalvase_config.py`
Expected: `All checks passed!`

- [ ] **Step 8: Commit**

```bash
git add fractalvase tests/test_fractalvase_config.py pyproject.toml
git commit -m "feat(fractalvase): config dataclass and constants regression"
```

---

## Task 2: The Julia field

**Confidence: 93 %** — the mapping is already numerically validated in `docs/superpowers/specs/proto_field.py`; this task ports a proven prototype and adds band-limiting.

**Files:**
- Create: `fractalvase/julia.py`
- Create: `tests/test_fractalvase_julia.py`
- Reference: `docs/superpowers/specs/proto_field.py` (validated prototype — read it first)

**Interfaces:**
- Consumes: `VaseConfig` from Task 1.
- Produces:
  - `smooth_escape(z0: np.ndarray, cfg: VaseConfig) -> tuple[np.ndarray, np.ndarray]` returning `(nu, interior_mask)`
  - `koenigs_grid(cfg: VaseConfig, n_theta: int, n_z: int) -> np.ndarray` — complex array shape `(n_theta, n_z)`
  - `normalised_field(cfg: VaseConfig, n_theta: int, n_z: int, supersample: int = 2) -> np.ndarray` — float array shape `(n_theta, n_z)` in `[0, 1]`

- [ ] **Step 1: Read the validated prototype**

Read `docs/superpowers/specs/proto_field.py`. It contains the exact mapping and the checks that proved it. Do not re-derive the mapping; port it.

- [ ] **Step 2: Write the failing test**

Create `tests/test_fractalvase_julia.py`:

```python
"""The mapping was wrong once already (see spec 2.3). These tests pin it."""
import numpy as np
import pytest

from fractalvase.config import DOUADY_HELIX
from fractalvase.julia import koenigs_grid, normalised_field, smooth_escape

CFG = DOUADY_HELIX


def test_smooth_escape_interior_is_flagged():
    # 0 is the critical point; for c in M its orbit stays bounded
    nu, interior = smooth_escape(np.array([0j]), CFG)
    assert interior[0]


def test_smooth_escape_far_point_escapes_immediately():
    nu, interior = smooth_escape(np.array([1000 + 0j]), CFG)
    assert not interior[0]
    assert nu[0] < 2.0


def test_smooth_escape_is_continuous_not_terraced():
    """Integer iteration count steps; the renormalised count must not."""
    r = np.linspace(1.40, 1.60, 4000)
    nu, interior = smooth_escape(r.astype(complex), CFG)
    outside = ~interior
    jumps = np.abs(np.diff(nu[outside]))
    # a terraced field jumps by ~1.0 at every band edge
    assert jumps.max() < 0.5, f"field is terracing: max jump {jumps.max()}"


def test_koenigs_grid_lands_on_the_set_not_miles_away():
    """The bug that was caught: an origin-centred map puts every sample outside."""
    zc = koenigs_grid(CFG, 128, 100)
    zeta = np.abs(zc - CFG.alpha)
    assert zeta.min() == pytest.approx(CFG.zeta_min, rel=1e-6)
    assert zeta.max() == pytest.approx(CFG.zeta_min * abs(CFG.mu) ** CFG.periods, rel=1e-6)
    assert np.abs(zc).max() < 3.0, "samples are far outside K_c"


def test_grid_has_real_interior_and_real_exterior():
    zc = koenigs_grid(CFG, 256, 200)
    _, interior = smooth_escape(zc, CFG)
    frac = interior.mean()
    assert 0.02 < frac < 0.5, f"interior fraction {frac} is degenerate"


def test_seam_closes_exactly():
    """theta = 0 and theta = 2pi must give the identical value, not merely close."""
    cfg = CFG
    h = 120.0
    u = np.log(cfg.zeta_min) + cfg.k * (h - cfg.band_lo)
    v0 = 0.0 + cfg.twist_rate_rad_per_mm * (h - cfg.band_lo)
    v1 = 2 * np.pi + cfg.twist_rate_rad_per_mm * (h - cfg.band_lo)
    z = np.array([cfg.alpha + np.exp(u + 1j * v0), cfg.alpha + np.exp(u + 1j * v1)])
    nu, _ = smooth_escape(z, cfg)
    assert nu[0] == pytest.approx(nu[1], abs=1e-9)


def test_pattern_reproduces_itself_after_one_period():
    """The Koenigs screw is the whole design. If this fails, the vase is not fractal."""
    cfg = CFG
    theta = np.linspace(0, 2 * np.pi, 512, endpoint=False)

    def ring(h):
        u = np.log(cfg.zeta_min) + cfg.k * (h - cfg.band_lo)
        v = theta + cfg.twist_rate_rad_per_mm * (h - cfg.band_lo)
        return smooth_escape(cfg.alpha + np.exp(u + 1j * v), cfg)[0]

    a, b = ring(60.0), ring(60.0 + cfg.period)
    match = np.corrcoef(a, b)[0, 1]
    control = np.corrcoef(a, np.roll(b, 13))[0, 1]
    assert match > 0.95, f"period does not reproduce: r={match}"
    assert match > control


def test_normalised_field_is_bounded_and_uses_the_full_range():
    f = normalised_field(CFG, 256, 200)
    assert f.shape == (256, 200)
    assert f.min() >= 0.0 and f.max() <= 1.0
    # a clamp at nu_ref is what stops the heavy tail flattening everything
    assert f.std() > 0.05, "field is nearly constant; check nu_ref clamping"


def test_normalised_field_interior_is_maximal():
    """Interior is solid, so it must drive maximum radius."""
    zc = koenigs_grid(CFG, 128, 100)
    _, interior = smooth_escape(zc, CFG)
    f = normalised_field(CFG, 128, 100, supersample=1)
    assert f[interior].min() == pytest.approx(1.0)
```

- [ ] **Step 3: Run it to confirm it fails**

Run: `python -m pytest tests/test_fractalvase_julia.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fractalvase.julia'`

- [ ] **Step 4: Implement the field**

Create `fractalvase/julia.py`:

```python
"""Julia escape-time field on a Koenigs-centred log-polar grid.

The mapping must be centred on the repelling fixed point alpha. An
origin-centred map (z = exp(k*h + i*theta)) puts every sample far outside
K_c, the field goes flat, and the vase comes out a smooth cone. See spec
section 2.3 and docs/superpowers/specs/proto_field.py.
"""

from __future__ import annotations

import numpy as np

from fractalvase.config import VaseConfig

_LOG2 = np.log(2.0)


def smooth_escape(z0: np.ndarray, cfg: VaseConfig) -> tuple[np.ndarray, np.ndarray]:
    """Renormalised escape time.

    Returns ``(nu, interior)``. ``nu`` is the continuous iteration count
    ``n + 1 - log(log|z_n|)/log 2``; the integer count terraces and would
    beat against layer lines. ``interior`` marks points that never escaped.
    """
    z = np.asarray(z0, dtype=np.complex128).copy()
    nu = np.full(z.shape, float(cfg.max_iter), dtype=np.float64)
    alive = np.ones(z.shape, dtype=bool)

    for n in range(cfg.max_iter):
        z[alive] = z[alive] ** 2 + cfg.c
        mag = np.abs(z)
        escaped = alive & (mag > cfg.escape_r)
        if escaped.any():
            nu[escaped] = n + 1 - np.log(np.log(mag[escaped])) / _LOG2
            alive &= ~escaped
        if not alive.any():
            break

    return nu, alive


def koenigs_grid(cfg: VaseConfig, n_theta: int, n_z: int) -> np.ndarray:
    """Map the vase's (theta, h) onto the complex plane around alpha.

    Rising one period advances u by exactly ln|mu| and v by exactly arg mu,
    which is the Koenigs map itself -- so the pattern reproduces, rotated.
    """
    theta = np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False)
    h = np.linspace(cfg.band_lo, cfg.band_hi, n_z)
    t_grid, h_grid = np.meshgrid(theta, h, indexing="ij")

    dh = h_grid - cfg.band_lo
    u = np.log(cfg.zeta_min) + cfg.k * dh
    v = t_grid + cfg.twist_rate_rad_per_mm * dh
    return cfg.alpha + np.exp(u + 1j * v)


def _raw_field(cfg: VaseConfig, zc: np.ndarray) -> np.ndarray:
    """nu clamped at nu_ref and normalised to [0, 1]; interior is 1.0."""
    nu, interior = smooth_escape(zc, cfg)
    field = np.clip(nu / cfg.nu_ref, 0.0, 1.0)
    field[interior] = 1.0
    return field


def normalised_field(
    cfg: VaseConfig, n_theta: int, n_z: int, supersample: int = 2
) -> np.ndarray:
    """Band-limited field in [0, 1].

    A fractal has unbounded detail, so no sample rate is sufficient -- the
    field must be filtered, not merely sampled finely. Supersampling on a
    rotated offset grid averages the sub-sample detail away rather than
    aliasing it into the geometry.
    """
    if supersample <= 1:
        return _raw_field(cfg, koenigs_grid(cfg, n_theta, n_z))

    acc = np.zeros((n_theta, n_z), dtype=np.float64)
    # rotated-grid offsets: fractions of one cell in (theta, h)
    offsets = [(0.25, 0.25), (0.75, -0.25), (-0.25, 0.75), (-0.75, -0.75)][:supersample**2]
    dtheta = (2 * np.pi) / n_theta
    dh = (cfg.band_hi - cfg.band_lo) / max(n_z - 1, 1)

    theta = np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False)
    h = np.linspace(cfg.band_lo, cfg.band_hi, n_z)
    t_grid, h_grid = np.meshgrid(theta, h, indexing="ij")

    for ot, oh in offsets:
        tt = t_grid + ot * dtheta
        hh = np.clip(h_grid + oh * dh, cfg.band_lo, cfg.band_hi)
        d = hh - cfg.band_lo
        u = np.log(cfg.zeta_min) + cfg.k * d
        v = tt + cfg.twist_rate_rad_per_mm * d
        acc += _raw_field(cfg, cfg.alpha + np.exp(u + 1j * v))

    return acc / len(offsets)
```

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/test_fractalvase_julia.py -v`
Expected: 9 passed.

If `test_normalised_field_is_bounded_and_uses_the_full_range` fails on `std`, raise or lower `nu_ref` in `VaseConfig` until the field has real spread, and record the value you settled on in the commit message. Do not widen the assertion.

- [ ] **Step 6: Lint and commit**

```bash
python -m ruff check fractalvase tests/test_fractalvase_julia.py
git add fractalvase/julia.py tests/test_fractalvase_julia.py
git commit -m "feat(fractalvase): Koenigs-centred Julia field with band-limiting"
```

---

## Task 3: Profile and relief envelope

**Confidence: 95 %** — closed-form functions with figures already verified in `check_slope.py`.

**Files:**
- Create: `fractalvase/profile.py`
- Create: `tests/test_fractalvase_profile.py`
- Reference: `docs/superpowers/specs/check_slope.py`

**Interfaces:**
- Consumes: `VaseConfig`.
- Produces:
  - `BREAKPOINTS: tuple[tuple[float, float], ...]` — `(z_mm, diameter_mm)`
  - `radius_at(z: np.ndarray) -> np.ndarray`
  - `smooth_radius(z: np.ndarray, window: float = 9.0) -> np.ndarray`
  - `relief_amplitude(z: np.ndarray, cfg: VaseConfig) -> np.ndarray`
  - `max_slope(cfg: VaseConfig) -> float`

- [ ] **Step 1: Write the failing test**

Create `tests/test_fractalvase_profile.py`:

```python
import numpy as np
import pytest

from fractalvase.config import DOUADY_HELIX
from fractalvase.profile import (
    BREAKPOINTS,
    max_slope,
    radius_at,
    relief_amplitude,
    smooth_radius,
)

CFG = DOUADY_HELIX


def test_breakpoints_match_spec():
    assert BREAKPOINTS[0] == (0.0, 70.0)
    assert (185.0, 116.0) in BREAKPOINTS  # widest point
    assert BREAKPOINTS[-1] == (300.0, 68.0)


def test_widest_point_is_at_the_golden_section():
    z = np.linspace(0, 300, 3001)
    widest_z = z[np.argmax(radius_at(z))]
    assert widest_z == pytest.approx(185.0, abs=1.0)
    assert widest_z / 300.0 == pytest.approx(0.617, abs=0.005)


def test_envelope_is_never_exceeded():
    z = np.linspace(0, 300, 3001)
    assert radius_at(z).max() * 2 <= 116.0 + 1e-9
    assert (radius_at(z).max() * 2 + 2 * CFG.relief_peak) <= 135.0


def test_relief_is_zero_in_the_quiet_zones():
    quiet = np.array([0.0, 20.0, 39.9, 240.1, 270.0, 300.0])
    assert np.allclose(relief_amplitude(quiet, CFG), 0.0)


def test_relief_peaks_at_the_specified_height():
    z = np.linspace(40, 240, 20001)
    a = relief_amplitude(z, CFG)
    assert a.max() == pytest.approx(CFG.relief_peak, abs=1e-6)
    assert z[np.argmax(a)] == pytest.approx(CFG.relief_peak_z, abs=0.05)


def test_relief_samples_match_spec():
    for z, expected in [(150.0, 6.4444), (185.0, 3.5000), (225.0, 0.3163)]:
        got = relief_amplitude(np.array([z]), CFG)[0]
        assert got == pytest.approx(expected, abs=1e-3)


def test_relief_has_zero_slope_at_both_band_ends():
    """Zero-slope entry is what stops a visible start line."""
    eps = 0.01
    for edge in (CFG.band_lo, CFG.band_hi):
        inside = edge + eps if edge == CFG.band_lo else edge - eps
        a = relief_amplitude(np.array([inside]), CFG)[0]
        assert a < 0.01, f"relief enters abruptly at z={edge}"


def test_smoothing_does_not_move_the_widest_point_much():
    z = np.linspace(0, 300, 3001)
    assert z[np.argmax(smooth_radius(z))] == pytest.approx(185.0, abs=6.0)


def test_combined_slope_stays_within_the_overhang_limit():
    """Profile taper + relief gradient + helical lean, composed."""
    assert max_slope(CFG) < 1.0
    assert np.degrees(np.arctan(max_slope(CFG))) < 45.0
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_fractalvase_profile.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement**

Create `fractalvase/profile.py`:

```python
"""Vase silhouette and relief envelope.

The profile is a piecewise-linear set of breakpoints, smoothed so it reads
as a vase rather than a chart. Relief A(z) is a raised cosine on both sides
of its peak: zero-valued AND zero-slope at both band ends, so ornament
emerges from the quiet zones without a visible start line.
"""

from __future__ import annotations

import numpy as np

from fractalvase.config import VaseConfig

# (z mm, diameter mm) -- spec section 3.1
BREAKPOINTS: tuple[tuple[float, float], ...] = (
    (0.0, 70.0),
    (40.0, 80.0),
    (150.0, 112.0),
    (185.0, 116.0),
    (225.0, 96.0),
    (240.0, 78.0),
    (262.0, 58.0),
    (300.0, 68.0),
)

_ZS = np.array([b[0] for b in BREAKPOINTS])
_RS = np.array([b[1] / 2.0 for b in BREAKPOINTS])


def radius_at(z: np.ndarray) -> np.ndarray:
    """Piecewise-linear radius, in mm."""
    return np.interp(np.asarray(z, dtype=float), _ZS, _RS)


def smooth_radius(z: np.ndarray, window: float = 9.0, samples: int = 13) -> np.ndarray:
    """Box-average the piecewise profile so breakpoints read as curves.

    The inner wall is built from this, never from the relief-bearing outer
    surface: an inward offset of a detailed surface self-intersects wherever
    the wall thickness exceeds the local radius of curvature.
    """
    z = np.asarray(z, dtype=float)
    offsets = np.linspace(-window, window, samples)
    stack = np.stack([radius_at(np.clip(z + d, 0.0, 300.0)) for d in offsets])
    return stack.mean(axis=0)


def relief_amplitude(z: np.ndarray, cfg: VaseConfig) -> np.ndarray:
    """A(z): raised cosine rising to relief_peak, then falling to zero."""
    z = np.asarray(z, dtype=float)
    out = np.zeros_like(z)

    lo, pk, hi = cfg.band_lo, cfg.relief_peak_z, cfg.band_hi
    rise = (z >= lo) & (z <= pk)
    fall = (z > pk) & (z <= hi)

    out[rise] = cfg.relief_peak * (1 - np.cos(np.pi * (z[rise] - lo) / (pk - lo))) / 2
    out[fall] = cfg.relief_peak * (1 + np.cos(np.pi * (z[fall] - pk) / (hi - pk))) / 2
    return out


def max_slope(cfg: VaseConfig) -> float:
    """Worst-case |grad r|, composing profile taper, relief and helical lean.

    Deliberately pessimistic: it stacks the steepest taper against the peak
    relief gradient and the twist drift at maximum radius, which do not
    co-occur. Spec section 3.4 records 0.8339 -> 39.82 degrees.
    """
    z = np.linspace(0.0, 300.0, 30001)

    seg = np.abs(np.diff(_RS) / np.diff(_ZS)).max()
    relief_grad = np.abs(np.gradient(relief_amplitude(z, cfg), z)).max()
    meridional = seg + relief_grad

    r_max = _RS.max()
    tangential = r_max * abs(cfg.twist_rate_rad_per_mm)

    return float(np.hypot(meridional, tangential))
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_fractalvase_profile.py -v`
Expected: 9 passed.

- [ ] **Step 5: Lint and commit**

```bash
python -m ruff check fractalvase tests/test_fractalvase_profile.py
git add fractalvase/profile.py tests/test_fractalvase_profile.py
git commit -m "feat(fractalvase): profile breakpoints and relief envelope"
```

---

## Task 4: The closed shell

**Confidence: 92 %** — structured-grid meshing is deterministic, but winding direction is the classic place to get an inside-out mesh. Lifted from 88 % by Step 1, which proves the winding convention on a trivial cylinder before the real surface is attempted.

**Files:**
- Create: `fractalvase/surface.py`
- Create: `tests/test_fractalvase_surface.py`

**Interfaces:**
- Consumes: `VaseConfig`, `normalised_field`, `radius_at`, `smooth_radius`, `relief_amplitude`.
- Produces:
  - `revolve_grid(radius: np.ndarray, z: np.ndarray, flip: bool = False) -> tuple[np.ndarray, np.ndarray]` — `(vertices, faces)` for an open tube; `radius` shape `(n_theta, n_z)`
  - `build_shell(cfg: VaseConfig) -> trimesh.Trimesh` — closed, watertight, genus 0

- [ ] **Step 1: Prove the winding convention on a cylinder first**

Write this throwaway check and run it before anything else. It costs a minute and prevents an inside-out mesh that only shows up at export.

```python
import numpy as np
import trimesh

from fractalvase.surface import revolve_grid

n_t, n_z = 32, 4
r = np.full((n_t, n_z), 10.0)
z = np.linspace(0.0, 20.0, n_z)
v, f = revolve_grid(r, z)
m = trimesh.Trimesh(v, f, process=False)
print("winding consistent:", m.is_winding_consistent)
# open tube: not watertight yet, but normals must already point outward
print("mean radial dot:", float(np.mean(np.einsum(
    "ij,ij->i",
    m.face_normals,
    m.triangles_center / np.linalg.norm(
        m.triangles_center[:, :2], axis=1, keepdims=True).clip(1e-9),
))))
```

Expected: `winding consistent: True`, and the mean radial dot **positive** (normals point away from the axis). If it is negative, swap the triangle vertex order in `revolve_grid` — do not paper over it with `fix_normals` later.

- [ ] **Step 2: Write the failing test**

Create `tests/test_fractalvase_surface.py`:

```python
import numpy as np
import pytest
import trimesh

from fractalvase.config import VaseConfig
from fractalvase.surface import build_shell, revolve_grid

# small grid: these tests check topology, not detail
SMALL = VaseConfig(n_theta=96, n_z=80)


def test_revolve_grid_seam_has_no_duplicate_vertices():
    n_t, n_z = 16, 5
    r = np.full((n_t, n_z), 5.0)
    z = np.linspace(0, 10, n_z)
    v, f = revolve_grid(r, z)
    assert len(v) == n_t * n_z, "seam vertex duplicated; theta must not include 2pi"


def test_revolve_grid_winding_is_outward():
    n_t, n_z = 32, 4
    r = np.full((n_t, n_z), 10.0)
    z = np.linspace(0, 20, n_z)
    m = trimesh.Trimesh(*revolve_grid(r, z), process=False)
    assert m.is_winding_consistent


def test_shell_is_a_valid_solid():
    m = build_shell(SMALL)
    assert m.is_watertight, "shell is not watertight"
    assert m.is_winding_consistent
    assert m.is_volume
    assert m.volume > 0, "mesh is inside-out"
    assert m.body_count == 1, "stray disconnected shells"


def test_shell_is_genus_zero_before_piercing():
    m = build_shell(SMALL)
    assert m.euler_number == 2, f"expected genus 0, got euler {m.euler_number}"


def test_shell_fits_the_build_envelope():
    m = build_shell(SMALL)
    x, y, z = m.extents
    assert x <= 135.0 and y <= 135.0, f"footprint {x:.1f} x {y:.1f} exceeds plate"
    assert z <= 300.0, f"height {z:.1f} exceeds plate"


def test_shell_sits_on_the_plate():
    m = build_shell(SMALL)
    assert m.bounds[0][2] == pytest.approx(0.0, abs=1e-6)


def test_shell_is_hollow_with_the_specified_wall():
    """A solid vase would have far more volume than a 2mm shell."""
    m = build_shell(SMALL)
    solid_estimate = np.pi * (58.0**2) * 300.0
    assert m.volume < 0.25 * solid_estimate, "vase appears solid, not shelled"


def test_no_degenerate_faces():
    m = build_shell(SMALL)
    areas = m.area_faces
    assert (areas > 1e-10).all(), "zero-area triangles present"
```

- [ ] **Step 3: Run it to confirm it fails**

Run: `python -m pytest tests/test_fractalvase_surface.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement**

Create `fractalvase/surface.py`:

```python
"""Structured (theta, z) grid to a closed, manifold shell.

Cheaper than marching cubes by roughly three orders of magnitude, and
manifold by construction rather than by repair. Requires the radius to be
single-valued in theta -- true for this design by the slope constraint.
"""

from __future__ import annotations

import numpy as np
import trimesh

from fractalvase.config import VaseConfig
from fractalvase.julia import normalised_field
from fractalvase.profile import radius_at, relief_amplitude, smooth_radius


def revolve_grid(
    radius: np.ndarray, z: np.ndarray, flip: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Open tube from a radius field.

    ``radius`` is ``(n_theta, n_z)``. Theta excludes 2*pi, so the seam closes
    by index wrap with no duplicate vertices to merge later. ``flip``
    reverses winding, for inward-facing surfaces.
    """
    n_theta, n_z = radius.shape
    theta = np.linspace(0.0, 2 * np.pi, n_theta, endpoint=False)

    ct, st = np.cos(theta)[:, None], np.sin(theta)[:, None]
    zz = np.broadcast_to(z[None, :], radius.shape)
    verts = np.stack(
        [(radius * ct).ravel(), (radius * st).ravel(), zz.ravel()], axis=1
    )

    i = np.arange(n_theta)[:, None]
    j = np.arange(n_z - 1)[None, :]
    i1 = (i + 1) % n_theta

    a = (i * n_z + j).ravel()
    b = (i1 * n_z + j).ravel()
    c = (i1 * n_z + j + 1).ravel()
    d = (i * n_z + j + 1).ravel()

    faces = np.concatenate(
        [np.stack([a, b, c], axis=1), np.stack([a, c, d], axis=1)], axis=0
    )
    if flip:
        faces = faces[:, ::-1]
    return verts, faces


def _outer_radius(cfg: VaseConfig) -> tuple[np.ndarray, np.ndarray]:
    """Radius field for the fractal-bearing outer surface."""
    z = np.linspace(0.0, cfg.height, cfg.n_z)
    base = radius_at(z)[None, :]
    amp = relief_amplitude(z, cfg)[None, :]

    field = np.zeros((cfg.n_theta, cfg.n_z), dtype=float)
    in_band = (z >= cfg.band_lo) & (z <= cfg.band_hi)
    band_field = normalised_field(cfg, cfg.n_theta, int(in_band.sum()))
    field[:, in_band] = band_field

    # tanh compresses the gradient so the slope clamp is satisfiable
    # without flattening the field
    return base + amp * np.tanh(1.6 * field), z


def _inner_radius(cfg: VaseConfig) -> tuple[np.ndarray, np.ndarray]:
    """Inner wall: smoothed profile offset inward. Never an offset of the
    detailed outer surface, which self-intersects at small curvature radii."""
    z = np.linspace(0.0, cfg.height, max(cfg.n_z // 3, 24))
    r = np.clip(smooth_radius(z) - cfg.wall, 0.5, None)
    return np.broadcast_to(r[None, :], (max(cfg.n_theta // 3, 48), z.size)).copy(), z


def build_shell(cfg: VaseConfig) -> trimesh.Trimesh:
    """Closed vase shell: outer, inner, rim ring, base disc."""
    r_out, z_out = _outer_radius(cfg)
    r_in, z_in = _inner_radius(cfg)

    v_out, f_out = revolve_grid(r_out, z_out)
    v_in, f_in = revolve_grid(r_in, z_in, flip=True)

    n_out_t, n_out_z = r_out.shape
    n_in_t, n_in_z = r_in.shape

    verts = [v_out, v_in]
    faces = [f_out, f_in + len(v_out)]
    off_in = len(v_out)

    # --- rim: join the top rings. Resample the coarser ring onto the finer.
    top_out = np.arange(n_out_t) * n_out_z + (n_out_z - 1)
    top_in = off_in + (
        np.round(np.arange(n_out_t) * n_in_t / n_out_t).astype(int) % n_in_t
    ) * n_in_z + (n_in_z - 1)
    nxt = np.arange(1, n_out_t + 1) % n_out_t
    rim = np.concatenate(
        [
            np.stack([top_out, top_in, top_in[nxt]], axis=1),
            np.stack([top_out, top_in[nxt], top_out[nxt]], axis=1),
        ]
    )
    faces.append(rim)

    # --- base: annulus between inner and outer bottom rings, closed by a disc
    bot_out = np.arange(n_out_t) * n_out_z
    bot_in = off_in + (
        np.round(np.arange(n_out_t) * n_in_t / n_out_t).astype(int) % n_in_t
    ) * n_in_z
    annulus = np.concatenate(
        [
            np.stack([bot_out, bot_in[nxt], bot_in], axis=1),
            np.stack([bot_out, bot_out[nxt], bot_in[nxt]], axis=1),
        ]
    )
    faces.append(annulus)

    centre_idx = sum(len(v) for v in verts)
    verts.append(np.array([[0.0, 0.0, 0.0]]))
    fan = np.stack(
        [np.full(n_out_t, centre_idx), bot_in[nxt], bot_in], axis=1
    )
    faces.append(fan)

    mesh = trimesh.Trimesh(
        np.concatenate(verts), np.concatenate(faces), process=True
    )
    mesh.merge_vertices()
    mesh.update_faces(mesh.nondegenerate_faces(height=1e-8))
    mesh.remove_unreferenced_vertices()
    trimesh.repair.fix_winding(mesh)
    trimesh.repair.fix_normals(mesh)
    return mesh
```

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/test_fractalvase_surface.py -v`
Expected: 8 passed.

If `test_shell_is_a_valid_solid` fails on `is_watertight`, the rim or base stitching has a mismatched ring. Print `trimesh.repair.broken_faces(m)` and the edge counts (`m.edges_sorted`) to find which ring, and fix the index arithmetic — do not call `fill_holes` to mask it.

- [ ] **Step 6: Lint and commit**

```bash
python -m ruff check fractalvase tests/test_fractalvase_surface.py
git add fractalvase/surface.py tests/test_fractalvase_surface.py
git commit -m "feat(fractalvase): closed manifold shell from the (theta,z) grid"
```

---

## Task 5: Pierced lattice by boolean subtraction

**Confidence: 90 %** — lifted from 72 %. `manifold3d` is a new, unproven dependency here, so Step 1 is a spike that proves the boolean path on trivial solids before any arch geometry exists. The fallback if the spike fails is named rather than improvised.

**Files:**
- Create: `fractalvase/holes.py`
- Create: `tests/test_fractalvase_holes.py`

**Interfaces:**
- Consumes: `VaseConfig`, `normalised_field`, `build_shell`.
- Produces:
  - `hole_regions(field: np.ndarray, cfg: VaseConfig, z: np.ndarray) -> list[dict]` — each `{"theta": float, "z": float, "span_theta": float, "span_z": float}`
  - `arch_prism(theta, z_c, span_t, span_z, r_out, cfg) -> trimesh.Trimesh`
  - `pierce(shell: trimesh.Trimesh, cfg: VaseConfig) -> tuple[trimesh.Trimesh, int]` — returns the pierced mesh and the hole count

- [ ] **Step 1: Spike the boolean engine before writing any arch code**

Run this exactly:

```python
import trimesh
a = trimesh.creation.box(extents=(10, 10, 10))
b = trimesh.creation.box(extents=(4, 4, 20))
c = trimesh.boolean.difference([a, b], engine="manifold")
print("engine ok:", c.is_watertight, c.is_volume, round(c.volume, 3))
assert c.is_watertight and abs(c.volume - (1000 - 160)) < 1.0
```

Expected: `engine ok: True True 840.0`

**If this fails**, stop and report. Do not improvise a different engine. The recorded fallback is decision C1-A (hand-rolled boundary stitching, gated on `euler_number`), which requires returning to the spec — it is a design change, not an implementation detail.

- [ ] **Step 2: Write the failing test**

Create `tests/test_fractalvase_holes.py`:

```python
import numpy as np
import pytest
import trimesh

from fractalvase.config import VaseConfig
from fractalvase.holes import arch_prism, hole_regions, pierce

SMALL = VaseConfig(n_theta=96, n_z=80)


def test_boolean_engine_is_available():
    a = trimesh.creation.box(extents=(10, 10, 10))
    b = trimesh.creation.box(extents=(4, 4, 20))
    c = trimesh.boolean.difference([a, b], engine="manifold")
    assert c.is_watertight
    assert c.volume == pytest.approx(840.0, abs=1.0)


def test_regions_respect_the_max_span():
    z = np.linspace(150.0, 225.0, 60)
    field = np.zeros((96, 60))
    field[10:80, 5:55] = 1.0  # one huge blob, must be split or rejected
    for reg in hole_regions(field, SMALL, z):
        assert reg["span_z"] <= SMALL.max_hole_span + 1e-6


def test_no_regions_below_threshold():
    z = np.linspace(150.0, 225.0, 60)
    field = np.full((96, 60), SMALL.pierce_threshold - 0.05)
    assert hole_regions(field, SMALL, z) == []


def test_arch_prism_is_a_valid_solid():
    p = arch_prism(0.0, 185.0, 0.15, 8.0, 58.0, SMALL)
    assert p.is_watertight
    assert p.is_volume
    assert p.volume > 0


def test_arch_apex_points_up():
    """A pointed crown is what makes the hole self-supporting."""
    p = arch_prism(0.0, 185.0, 0.15, 8.0, 58.0, SMALL)
    v = p.vertices
    top = v[:, 2].max()
    near_top = v[np.abs(v[:, 2] - top) < 0.05]
    widest = np.ptp(v[:, 1])
    assert np.ptp(near_top[:, 1]) < 0.4 * widest, "crown is flat: it will bridge"


def test_pierce_produces_a_valid_solid_with_the_expected_genus():
    from fractalvase.surface import build_shell

    shell = build_shell(SMALL)
    pierced, n = pierce(shell, SMALL)
    assert n > 0, "nothing was pierced"
    assert pierced.is_watertight
    assert pierced.is_volume
    assert pierced.volume > 0
    assert pierced.volume < shell.volume, "piercing did not remove material"
    assert pierced.body_count == 1


def test_pierced_mesh_stays_in_the_envelope():
    from fractalvase.surface import build_shell

    pierced, _ = pierce(build_shell(SMALL), SMALL)
    x, y, z = pierced.extents
    assert x <= 135.0 and y <= 135.0 and z <= 300.0
```

- [ ] **Step 3: Run it to confirm it fails**

Run: `python -m pytest tests/test_fractalvase_holes.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement**

Create `fractalvase/holes.py`:

```python
"""Pierced lattice, cut by boolean subtraction (decision C1-B).

Holes are pointed arches, not round: a round hole's crown is an unsupported
bridge, while a gothic arch is self-supporting. Each cutter is oriented from
the LOCAL surface normal, not global Z, because the helix leans features by
up to 22.63 degrees and a globally-oriented arch degrades into a bridge on
the leaning face (decision C4-A).
"""

from __future__ import annotations

import numpy as np
import trimesh
from scipy import ndimage

from fractalvase.config import VaseConfig
from fractalvase.julia import normalised_field
from fractalvase.profile import radius_at


def hole_regions(field: np.ndarray, cfg: VaseConfig, z: np.ndarray) -> list[dict]:
    """Threshold the field and reduce each connected blob to one hole.

    Wraps in theta so a blob straddling the seam is one region, not two.
    Blobs wider than max_hole_span are clipped to it rather than dropped:
    the lattice should stay open where the field says it is open.
    """
    mask = field > cfg.pierce_threshold
    if not mask.any():
        return []

    labels, n = ndimage.label(mask)
    # stitch labels across the theta seam
    for j in range(mask.shape[1]):
        a, b = labels[0, j], labels[-1, j]
        if a and b and a != b:
            labels[labels == b] = a

    dz = float(z[1] - z[0]) if z.size > 1 else 1.0
    dtheta = 2 * np.pi / field.shape[0]

    regions: list[dict] = []
    for lab in np.unique(labels):
        if lab == 0:
            continue
        ti, zi = np.nonzero(labels == lab)
        span_z = min((zi.ptp() + 1) * dz, cfg.max_hole_span)
        span_t = (ti.ptp() + 1) * dtheta
        # reject slivers that would leave sub-ligament walls
        if span_z < cfg.min_ligament or span_t * radius_at(
            np.array([z[int(zi.mean())]])
        )[0] < cfg.min_ligament:
            continue
        regions.append(
            {
                "theta": float(ti.mean() * dtheta),
                "z": float(z[int(round(zi.mean()))]),
                "span_theta": float(min(span_t, cfg.max_hole_span / max(radius_at(
                    np.array([z[int(zi.mean())]]))[0], 1e-6))),
                "span_z": float(span_z),
            }
        )
    return regions


def arch_prism(
    theta: float,
    z_c: float,
    span_theta: float,
    span_z: float,
    r_out: float,
    cfg: VaseConfig,
) -> trimesh.Trimesh:
    """A pointed-arch prism, swept radially through the wall.

    Built in a local frame with +Z along the print direction corrected for
    the helical lean, then placed on the surface at (theta, z_c).
    """
    half_w = max(span_theta * r_out / 2.0, cfg.min_ligament / 2.0)
    half_h = max(span_z / 2.0, cfg.min_ligament / 2.0)
    apex = half_w / np.tan(np.radians(cfg.arch_apex_deg))

    # 2D arch outline: flat bottom, straight sides, pointed crown
    outline = np.array(
        [
            [-half_w, -half_h],
            [half_w, -half_h],
            [half_w, half_h - apex],
            [0.0, half_h],
            [-half_w, half_h - apex],
        ]
    )
    depth = cfg.wall * 6.0  # comfortably through the wall from both sides
    prism = trimesh.creation.extrude_polygon(
        trimesh.path.polygons.Polygon(outline), height=depth
    )
    # extrude_polygon builds along +Z; lay it along the radial direction
    prism.apply_transform(
        trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    )
    prism.apply_translation([0.0, depth / 2.0, 0.0])

    # correct the crown for the local helical lean (decision C4-A)
    lean = np.arctan(r_out * abs(cfg.twist_rate_rad_per_mm))
    prism.apply_transform(
        trimesh.transformations.rotation_matrix(
            -np.sign(cfg.twist_rate_rad_per_mm) * lean, [0, 1, 0]
        )
    )

    prism.apply_translation([0.0, 0.0, z_c])
    prism.apply_transform(
        trimesh.transformations.rotation_matrix(theta, [0, 0, 1], [0, 0, 0])
    )
    prism.apply_translation(
        [r_out * np.cos(theta), r_out * np.sin(theta), 0.0]
    )
    return prism


def pierce(shell: trimesh.Trimesh, cfg: VaseConfig) -> tuple[trimesh.Trimesh, int]:
    """Cut the lattice band. Returns (mesh, hole_count)."""
    z_band = np.linspace(150.0, 225.0, max(cfg.n_z // 4, 40))
    field = normalised_field(cfg, cfg.n_theta, z_band.size)
    regions = hole_regions(field, cfg, z_band)
    if not regions:
        return shell, 0

    cutters = [
        arch_prism(
            r["theta"],
            r["z"],
            r["span_theta"],
            r["span_z"],
            float(radius_at(np.array([r["z"]]))[0]) + cfg.relief_peak,
            cfg,
        )
        for r in regions
    ]
    result = trimesh.boolean.difference([shell, *cutters], engine="manifold")
    return result, len(regions)
```

- [ ] **Step 5: Run the tests**

Run: `python -m pytest tests/test_fractalvase_holes.py -v`
Expected: 7 passed.

If regions come out in the thousands and the boolean takes minutes, raise `cfg.pierce_threshold` toward 0.75 until the count is in the low hundreds, and record the value in the commit message. Hole count is an aesthetic parameter, not a correctness one.

- [ ] **Step 6: Lint and commit**

```bash
python -m ruff check fractalvase tests/test_fractalvase_holes.py
git add fractalvase/holes.py tests/test_fractalvase_holes.py
git commit -m "feat(fractalvase): pierced lattice via manifold boolean subtraction"
```

---

## Task 6: The validation gate

**Confidence: 96 %** — assertions over a trimesh API already confirmed on this machine.

**Files:**
- Create: `fractalvase/validate.py`
- Create: `tests/test_fractalvase_validate.py`

**Interfaces:**
- Consumes: `trimesh.Trimesh`, `VaseConfig`.
- Produces: `MeshInvalid(Exception)`; `validate(mesh, cfg, n_holes) -> dict[str, object]` returning a report; raises `MeshInvalid` on any failure.

- [ ] **Step 1: Write the failing test**

Create `tests/test_fractalvase_validate.py`:

```python
import pytest
import trimesh

from fractalvase.config import VaseConfig
from fractalvase.validate import MeshInvalid, validate

CFG = VaseConfig(n_theta=96, n_z=80)


def test_a_good_solid_passes():
    m = trimesh.creation.box(extents=(10, 10, 10))
    report = validate(m, CFG, n_holes=0)
    assert report["watertight"] is True
    assert report["euler_number"] == 2


def test_inside_out_mesh_is_rejected():
    m = trimesh.creation.box(extents=(10, 10, 10))
    m.invert()
    with pytest.raises(MeshInvalid, match="volume"):
        validate(m, CFG, n_holes=0)


def test_open_mesh_is_rejected():
    m = trimesh.creation.box(extents=(10, 10, 10))
    m.update_faces(list(range(len(m.faces) - 2)))
    with pytest.raises(MeshInvalid, match="watertight"):
        validate(m, CFG, n_holes=0)


def test_two_bodies_are_rejected():
    a = trimesh.creation.box(extents=(5, 5, 5))
    b = trimesh.creation.box(extents=(5, 5, 5))
    b.apply_translation([50, 0, 0])
    with pytest.raises(MeshInvalid, match="bod"):
        validate(a + b, CFG, n_holes=0)


def test_wrong_genus_is_rejected():
    """The one cheap check that catches bad hole topology."""
    m = trimesh.creation.box(extents=(10, 10, 10))
    with pytest.raises(MeshInvalid, match="genus|euler"):
        validate(m, CFG, n_holes=7)


def test_oversize_mesh_is_rejected():
    m = trimesh.creation.box(extents=(200, 10, 10))
    with pytest.raises(MeshInvalid, match="envelope"):
        validate(m, CFG, n_holes=0)


def test_torus_with_one_hole_passes():
    t = trimesh.creation.torus(major_radius=10.0, minor_radius=3.0)
    report = validate(t, CFG, n_holes=1)
    assert report["euler_number"] == 0
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_fractalvase_validate.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement**

Create `fractalvase/validate.py`:

```python
"""The gate. Nothing reaches a slicer without passing.

House rule: a CAD error should be impossible to express or impossible to
miss. This module chooses impossible to miss -- it raises, it does not
return a warning that a caller can ignore.
"""

from __future__ import annotations

import trimesh

from fractalvase.config import VaseConfig


class MeshInvalid(Exception):
    """Raised when a mesh must not be exported."""


def validate(
    mesh: trimesh.Trimesh, cfg: VaseConfig, n_holes: int
) -> dict[str, object]:
    """Check a finished mesh. Raises MeshInvalid on the first failure."""
    problems: list[str] = []

    if not mesh.is_watertight:
        problems.append("not watertight: some edge is not shared by exactly two faces")
    if not mesh.is_winding_consistent:
        problems.append("winding is inconsistent")
    if mesh.volume <= 0:
        problems.append(f"volume is {mesh.volume:.3f}: mesh is inside-out")
    if mesh.body_count != 1:
        problems.append(f"{mesh.body_count} bodies: expected exactly 1")

    expected_euler = 2 - 2 * n_holes
    if mesh.euler_number != expected_euler:
        problems.append(
            f"euler_number {mesh.euler_number} != {expected_euler} "
            f"(genus mismatch for {n_holes} holes): hole topology is wrong"
        )

    broken = trimesh.repair.broken_faces(mesh)
    if len(broken):
        problems.append(f"{len(broken)} broken faces")

    x, y, z = mesh.extents
    if x > 135.0 or y > 135.0 or z > cfg.height:
        problems.append(
            f"outside build envelope: {x:.1f} x {y:.1f} x {z:.1f} mm"
        )

    if problems:
        raise MeshInvalid("; ".join(problems))

    return {
        "watertight": mesh.is_watertight,
        "volume_mm3": float(mesh.volume),
        "triangles": int(len(mesh.faces)),
        "euler_number": int(mesh.euler_number),
        "extents_mm": [round(float(v), 2) for v in mesh.extents],
        "holes": n_holes,
    }
```

- [ ] **Step 4: Run the tests**

Run: `python -m pytest tests/test_fractalvase_validate.py -v`
Expected: 7 passed.

- [ ] **Step 5: Lint and commit**

```bash
python -m ruff check fractalvase tests/test_fractalvase_validate.py
git add fractalvase/validate.py tests/test_fractalvase_validate.py
git commit -m "feat(fractalvase): mesh validation gate"
```

---

## Task 7: CLI, end-to-end build, and documentation sync

**Confidence: 92 %** — the only unknown is the full-resolution triangle count after the boolean, which Step 4 measures rather than assumes.

**Files:**
- Create: `fractalvase/__main__.py`
- Create: `tests/test_fractalvase_build.py`
- Modify: `fractalvase/__init__.py`
- Modify: `README.md`, `docs/README.md`

**Interfaces:**
- Consumes: everything above.
- Produces: `build_vase(cfg: VaseConfig) -> tuple[trimesh.Trimesh, dict]`; CLI `python -m fractalvase --out PATH [--preview]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_fractalvase_build.py`:

```python
import trimesh

from fractalvase import build_vase
from fractalvase.config import VaseConfig

FAST = VaseConfig(n_theta=96, n_z=80)


def test_end_to_end_build_passes_its_own_gate():
    mesh, report = build_vase(FAST)
    assert isinstance(mesh, trimesh.Trimesh)
    assert report["watertight"] is True
    assert report["triangles"] > 0
    assert report["holes"] > 0


def test_build_exports_3mf(tmp_path):
    mesh, _ = build_vase(FAST)
    out = tmp_path / "vase.3mf"
    mesh.export(out)
    assert out.exists() and out.stat().st_size > 1000


def test_build_respects_the_envelope():
    _, report = build_vase(FAST)
    x, y, z = report["extents_mm"]
    assert x <= 135.0 and y <= 135.0 and z <= 300.0
```

- [ ] **Step 2: Run it to confirm it fails**

Run: `python -m pytest tests/test_fractalvase_build.py -v`
Expected: FAIL — `ImportError: cannot import name 'build_vase'`

- [ ] **Step 3: Implement the build function and CLI**

Append to `fractalvase/__init__.py`:

```python
import trimesh

from fractalvase.holes import pierce
from fractalvase.surface import build_shell
from fractalvase.validate import validate


def build_vase(cfg: VaseConfig = DOUADY_HELIX) -> tuple[trimesh.Trimesh, dict]:
    """Shell, pierce, gate. Raises MeshInvalid rather than emitting a bad mesh."""
    shell = build_shell(cfg)
    mesh, n_holes = pierce(shell, cfg)
    return mesh, validate(mesh, cfg, n_holes)
```

and extend `__all__` to `["DOUADY_HELIX", "VaseConfig", "build_vase"]`.

Create `fractalvase/__main__.py`:

```python
"""CLI: build the vase and write a slicer-ready 3MF."""

from __future__ import annotations

import argparse
import json
import sys

from fractalvase import DOUADY_HELIX, build_vase
from fractalvase.config import VaseConfig
from fractalvase.validate import MeshInvalid


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fractalvase")
    ap.add_argument("--out", default="douady_helix.3mf", help="output path (.3mf)")
    ap.add_argument("--fast", action="store_true", help="coarse grid, for iteration")
    args = ap.parse_args(argv)

    cfg = VaseConfig(n_theta=96, n_z=80) if args.fast else DOUADY_HELIX
    try:
        mesh, report = build_vase(cfg)
    except MeshInvalid as exc:
        print(f"MESH INVALID: {exc}", file=sys.stderr)
        return 1

    mesh.export(args.out)
    report["output"] = args.out
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the real build and measure it**

Run: `python -m fractalvase --out douady_helix.3mf`

Record the reported `triangles` figure. The spec estimates ~815 k **before** the boolean, and explicitly says the post-boolean count must be measured, not assumed.

If `triangles > 1_000_000`, decimate before export by inserting this into `build_vase` after `pierce`:

```python
    if len(mesh.faces) > 1_000_000:
        mesh = mesh.simplify_quadric_decimation(face_count=900_000)
```

then re-run and re-validate. Report the final count either way.

- [ ] **Step 5: Sync the documentation**

This is a standing repo guardrail, not optional. In `README.md`, add a row to the "What ships" table:

```markdown
| `fractalvase/` | The Douady Helix vase generator: a Julia field on a Koenigs-centred log-polar grid becomes a manifold shell, pierced by boolean subtraction and gated before export |
```

In `docs/README.md`, add a line pointing at the spec and this plan under the existing docs index.

- [ ] **Step 6: Run everything**

```bash
python -m pytest tests/ -v
python -m ruff check fractalvase tests
python -m pyright fractalvase
```

Expected: all green. Pyright must be clean because `fractalvase` was added to its include list in Task 1.

- [ ] **Step 7: Commit**

```bash
git add fractalvase tests/test_fractalvase_build.py README.md docs/README.md
git commit -m "feat(fractalvase): end-to-end build, CLI, and docs sync"
```

---

## Self-Review

**Spec coverage.** §2.1 constants → Task 1. §2.2 scale ladder → Task 1. §2.3 corrected mapping and §2.3.1 normalisation → Task 2. §3.1 profile and relief → Task 3. §3.2 viewing distances → design intent, no code. §3.3 piercing rules → Task 5. §3.4 slope constraint → Task 3 (`max_slope`). §4 pipeline and triangle budget → Tasks 4, 5, 7 Step 4. §5 validation gate → Task 6. §6 scope (geometry only) → Global Constraints. §7 decisions C1-B, C4-A → Task 5; C2-A and C3-A are parameter values already in the Task 1 config.

**Placeholders.** None. Every code step carries runnable code; every "if it fails" branch names a specific action rather than "handle errors".

**Type consistency.** `VaseConfig` field and property names are used identically across Tasks 2–7. `normalised_field(cfg, n_theta, n_z, supersample)` is called with that signature in Tasks 4 and 5. `pierce` returns `(mesh, count)` in Task 5 and is unpacked that way in Task 7. `validate(mesh, cfg, n_holes)` matches between Tasks 6 and 7.

**Known soft spots, deliberately left to measurement rather than guessed:** post-boolean triangle count (Task 7 Step 4), hole count sensitivity to `pierce_threshold` (Task 5 Step 5), and `nu_ref` spread (Task 2 Step 5). Each has a stated adjustment procedure and a rule against widening the assertion instead.
