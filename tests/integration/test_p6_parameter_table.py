"""P6 -- does a named parameter table prevent repeated literals?

docs/probe-results.md P6: four hole diameter dimensions all bound to a single
parameter `hole_d`; one edit to that parameter propagates to all four.
"""
import pytest

from tests.integration.mcp_client import McpClient, parse_fh_result
from tests.integration.probe_scripts import P6_PARAMETER_TABLE

pytestmark = pytest.mark.fusion


def test_p6_one_edit_propagates_to_all_holes(client: McpClient, scratch: str):
    res = client.execute(P6_PARAMETER_TABLE)
    assert res.success, res.error
    data = parse_fh_result(res.message)

    assert data["before_mm"] == pytest.approx([8.0, 8.0, 8.0, 8.0], abs=1e-4)
    assert data["after_mm"] == pytest.approx([13.0, 13.0, 13.0, 13.0], abs=1e-4)
