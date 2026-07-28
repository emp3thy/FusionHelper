"""Smoke test for the MCP client and the scratch-document lifecycle.

Opt-in, live Fusion only -- see conftest.py for the gate. Confirms both
measured envelope shapes (success and failure) and that the scratch
lifecycle's per-test `finally` layer leaves no tagged document behind.
"""
import pytest

from tests.integration.mcp_client import McpClient
from tests.integration.scratch import sweep_scratch_docs

pytestmark = pytest.mark.fusion


def test_execute_success_envelope(client: McpClient):
    res = client.execute("print('fh-smoke')")
    assert res.success
    assert "fh-smoke" in res.message


def test_execute_failure_envelope(client: McpClient):
    res = client.execute("raise RuntimeError('fh-boom')")
    assert not res.success
    assert "fh-boom" in res.error


def test_scratch_lifecycle_creates_and_tags(client: McpClient, scratch: str):
    res = client.execute("print('fh-scratch-alive')")
    assert res.success
    assert "fh-scratch-alive" in res.message


def test_no_leaked_scratch_documents(client: McpClient):
    """Runs after the tests above (pytest's default collection order is file
    order). Sweeping again and finding nothing to close confirms the
    scratch fixture's per-test `finally` already closed what
    test_scratch_lifecycle_creates_and_tags created -- zero documents
    leaked by this session."""
    result = sweep_scratch_docs(client, None)
    assert result.closed == []
