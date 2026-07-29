"""P2 -- does `isFullyConstrained` work as a gate?

docs/probe-results.md P2: the flag transitions False -> True at exactly the
point the last degree of freedom is removed, across five recipe steps (rect
drawn, origin pinned, H/V applied, width dim, depth dim).
"""
import pytest

from tests.integration.mcp_client import McpClient, parse_fh_result
from tests.integration.probe_scripts import P2_ISFULLYCONSTRAINED

pytestmark = pytest.mark.fusion


def test_p2_isfullyconstrained_gate(client: McpClient, scratch: str):
    res = client.execute(P2_ISFULLYCONSTRAINED)
    assert res.success, res.error
    data = parse_fh_result(res.message)

    assert data["sequence"] == [False, False, False, False, True]
