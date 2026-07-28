"""P1 -- does a generated script build a genuinely parametric model?

docs/probe-results.md P1: a plate with three named parameters, edited after
build (plate_w 60->80mm, plate_t 5->8mm), rebuilds to bbox=(8.0,4.0,0.8) with
zero unhealthy timeline features.
"""
import pytest

from tests.integration.mcp_client import McpClient, parse_fh_result
from tests.integration.probe_scripts import P1_PARAMETRIC

pytestmark = pytest.mark.fusion


def test_p1_parametric_rebuild(client: McpClient, scratch: str):
    res = client.execute(P1_PARAMETRIC)
    assert res.success, res.error
    data = parse_fh_result(res.message)

    assert data["before"] == pytest.approx([6.0, 4.0, 0.5], abs=1e-4)
    assert data["after"] == pytest.approx([8.0, 4.0, 0.8], abs=1e-4)
    assert data["unhealthy"] == 0
