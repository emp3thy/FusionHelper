"""P3 -- what is the safe constraint-then-dimension sequence?

docs/probe-results.md P3: three over-constraint attempts against an already
fully-constrained sketch each raise, all *before* mutating -- the sketch is
left fully constrained and healthy, and the three failure modes carry
distinguishable messages that can drive different remediation.
"""
import pytest

from tests.integration.mcp_client import McpClient, parse_fh_result
from tests.integration.probe_scripts import P3_OVERCONSTRAINT

pytestmark = pytest.mark.fusion


def test_p3_overconstraint_is_failsafe(client: McpClient, scratch: str):
    res = client.execute(P3_OVERCONSTRAINT)
    assert res.success, res.error
    data = parse_fh_result(res.message)

    messages = data["messages"]
    assert "Already has same dimension" in messages["redundant_dimension"]
    assert "already been applied" in messages["redundant_constraint"]
    assert "VCS_SKETCH_SOLVING_FAILED" in messages["conflicting_constraint"]

    # The three failure classes are distinguishable from each other, not just
    # non-empty -- a generator remediation table needs to tell them apart.
    assert len({messages["redundant_dimension"],
                messages["redundant_constraint"],
                messages["conflicting_constraint"]}) == 3

    assert data["fully_constrained_after"] is True
    assert data["sketch_health_state"] == 0
    assert data["unhealthy_timeline_features"] == 0
