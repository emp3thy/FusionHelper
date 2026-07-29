"""P4 -- do index-picked faces break where named/durable references survive?

docs/probe-results.md P4: a topological edit (chamfer, face count 6 -> 7)
breaks an index pick's identity, while `entityToken` and a geometric
predicate both survive and correctly re-locate the top face.
"""
import pytest

from tests.integration.mcp_client import McpClient, parse_fh_result
from tests.integration.probe_scripts import P4_DURABLE_REFERENCES

pytestmark = pytest.mark.fusion


def test_p4_index_pick_breaks_entitytoken_survives(client: McpClient, scratch: str):
    res = client.execute(P4_DURABLE_REFERENCES)
    assert res.success, res.error
    data = parse_fh_result(res.message)

    assert data["face_count_before"] == 6
    assert data["face_count_after"] == 7

    # Index-pick identity changed: the face now at the pre-chamfer top index
    # is no longer the top face.
    assert data["index_face_still_top_after"] is False

    # entityToken round-trips and still resolves to the top face.
    assert data["entity_token_resolved"] is True
    assert data["entity_token_still_top"] is True

    # The geometric predicate finds the top face again, at a different index.
    assert data["predicate_found_new_index"] is True
    assert data["top_index_after"] != data["top_index_before"]
