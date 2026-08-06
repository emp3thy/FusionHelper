"""ORRERY mk2 shared geometry - involute tooth SPACES and helpers.

Gears are built as a plain cylinder at the TIP radius with one tooth
space cut and circular-patterned x N. That is ~10 API calls instead of
the ~400 a full outline needs, which is what blew the MCP client timeout
(and a timed-out request re-runs, duplicating geometry).
"""
import math

MODULE = 0.10          # cm  (1.0 mm)
PANG = math.radians(20)
BACKLASH = 0.020       # cm  (0.20 mm) - generous, printed gears

# ---- gear train (cm) -------------------------------------------------
SUN_N, SUN_RP = 20, 1.00
PL_N, PL_RP = 10, 0.50
RING_N, RING_RP = 40, 2.00
N_PLANET = 6           # (SUN_N + RING_N) / N_PLANET = 10, an integer
STATION_R = SUN_RP + PL_RP          # 1.50
SUN_TIP, SUN_ROOT = 1.10, 0.875
PL_TIP, PL_ROOT = 0.60, 0.375
RING_TIP, RING_ROOT = 1.90, 2.125

# ---- retention band: planets pinched between sun and ring ------------
BAND_Z = (0.50, 0.56, 0.62)         # 45-deg cones either side of a land
SUN_BAND = 0.83
PL_BAND = 0.66
RING_BAND = 2.17

GEAR_TOP = 1.10
H = 1.45


def _inv(a):
    return math.tan(a) - a


def _psi(N, rp, r, internal):
    """Half tooth angle at radius r."""
    rb = rp * math.cos(PANG)
    ap = math.acos(min(1.0, rb / rp))
    ar = math.acos(min(1.0, rb / max(r, rb)))
    psi_p = math.pi / (2 * N) - BACKLASH / (2 * rp)
    if internal:
        return psi_p - _inv(ap) + _inv(ar)
    return psi_p + _inv(ap) - _inv(ar)


def tooth_space(N, rp, r_tip, r_root, internal):
    """One space, centred on +X, as a closed point list."""
    half = math.pi / N
    lo, hi = (r_tip, r_root) if internal else (r_root, r_tip)
    rs = [lo, (lo + hi) / 2, hi]
    pts = []
    for r in rs:
        a = half - _psi(N, rp, r, internal)
        pts.append((r * math.cos(a), r * math.sin(a)))
    for r in reversed(rs):
        a = -(half - _psi(N, rp, r, internal))
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts
