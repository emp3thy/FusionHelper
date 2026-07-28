"""P8 -- does a parameter sweep surface errored features?

docs/probe-results.md P8: each parameter driven to an extreme, then the
timeline scanned for unhealthy features. Only the plate-narrower-than-the-
hole-pattern configuration (`plate_w` shrunk) produces a reference failure;
the other three extremes (`hole_d` too large twice, `plate_t` very thin) are
constructible and Fusion stays silent. `unhealthy == []` is asserted for
those three deliberately (asserted-silence, same rationale as P5): a future
Fusion that starts complaining about them is news, not noise.
"""
import pytest

from tests.integration.mcp_client import McpClient, parse_fh_result
from tests.integration.probe_scripts import P8_PARAMETER_SWEEP

pytestmark = pytest.mark.fusion


def test_p8_sweep_catches_only_reference_failure(client: McpClient, scratch: str):
    res = client.execute(P8_PARAMETER_SWEEP)
    assert res.success, res.error
    data = parse_fh_result(res.message)

    assert data["hole_d_30mm"] == []
    assert data["hole_d_60mm"] == []
    assert data["plate_t_0.4mm"] == []

    narrow_plate = data["plate_w_30mm"]
    assert len(narrow_plate) >= 1
    assert any("HoleCuts" in bad["name"] for bad in narrow_plate)
    assert any("Reference Failures" in bad["msg"] for bad in narrow_plate)
