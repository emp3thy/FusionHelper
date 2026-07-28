"""Smoke test for the MCP client and the scratch-document lifecycle.

Opt-in, live Fusion only -- see conftest.py for the gate. Confirms both
measured envelope shapes (success and failure) and that the scratch
lifecycle's per-test `finally` layer leaves no tagged document behind.
"""
import pytest

from tests.integration.mcp_client import McpClient
from tests.integration.scratch import (
    create_scratch_doc,
    new_session_tag,
    read_scratch_tags,
    sweep_scratch_docs,
)

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

    # Independent read-back: confirms the tag was actually written, not just
    # that the leak check later finds nothing to sweep (which a silently
    # failed tag write would also produce).
    assert read_scratch_tags(client) == [scratch]


def test_no_leaked_scratch_documents(client: McpClient):
    """Runs after the tests above (pytest's default collection order is file
    order). Sweeping again and finding nothing to close confirms the
    scratch fixture's per-test `finally` already closed what
    test_scratch_lifecycle_creates_and_tags created -- zero documents
    leaked by this session."""
    result = sweep_scratch_docs(client, None)
    assert result.closed == []


def test_pre_session_sweep_closes_prior_leak(client: McpClient):
    """Regression for conftest.py's layer 1 (pre-session sweep): create a
    scratch document directly, bypassing the `scratch` fixture's own
    `finally` cleanup, to simulate a prior session's Ctrl-C leak. Then run
    the same sweep_scratch_docs(client, None) call the pre-session fixture
    uses and confirm it actually closes the leaked document, verified by an
    independent tag read-back rather than trusting the sweep's own report.
    """
    tag = new_session_tag()
    create_scratch_doc(client, tag)
    result = sweep_scratch_docs(client, None)
    assert any(entry.endswith(f":{tag}") for entry in result.closed), result.closed
    assert read_scratch_tags(client) == []
