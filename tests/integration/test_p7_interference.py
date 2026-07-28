"""P7 -- does `analyzeInterference` report clash volume?

docs/probe-results.md P7: run against the P5 model immediately after the
parameter edit, where the raw-coordinate bracket has become embedded in the
plate. `analyzeInterference` correctly reports one clash of 3.2 cm3 and
attributes the pair.
"""
import pytest

from tests.integration.mcp_client import McpClient, parse_fh_result
from tests.integration.probe_scripts import P7_INTERFERENCE

pytestmark = pytest.mark.fusion


def test_p7_interference_detects_embedded_bracket(client: McpClient, scratch: str):
    res = client.execute(P7_INTERFERENCE)
    assert res.success, res.error
    data = parse_fh_result(res.message)

    assert data["count"] == 1
    clash = data["clashes"][0]
    assert clash["volume_cm3"] == pytest.approx(3.2, abs=1e-3)
    assert clash["a"] and clash["b"]  # pair attributed, not blank
