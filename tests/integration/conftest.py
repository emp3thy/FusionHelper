"""Pytest wiring for the opt-in, live-Fusion integration suite.

Gate: every test here needs a real Fusion 360 process with the MCP server
listening (recommended endpoint: http://127.0.0.1:27182/mcp). Set
FUSION_MCP_URL to opt in; if it is unset, or the endpoint fails to respond
to `initialize`, the whole suite skips. CI never sets the variable, so the
default run always skips these tests.

Cleanup is HARNESS-driven, never script-driven, because a script that raises
never reaches its own cleanup (docs/detailed-design.md "Scratch document
lifecycle"). Four layers, in the order they run:
  1. pre-session sweep -- any fusionhelper/scratch tag, catches a previous
     run's leaks (e.g. a Ctrl-C that skipped this session's own atexit)
  2. per-test `finally`, via the `scratch` fixture / scratch_doc() -- this
     session's tag only
  3. session-end sweep -- this session's tag, belt-and-braces alongside
     every test's own per-test `finally`
  4. atexit -- if pytest itself is interrupted before session teardown runs
"""
import atexit
import contextlib
import os
from collections.abc import Iterator

import pytest

from tests.integration.mcp_client import McpClient
from tests.integration.scratch import new_session_tag, scratch_doc, sweep_scratch_docs

DEFAULT_URL = "http://127.0.0.1:27182/mcp"
SESSION_TAG = new_session_tag()


def _best_effort_sweep(client: McpClient, tag: str) -> None:
    """atexit only: a last resort if pytest is interrupted before the
    session fixture's own teardown runs. Never let a cleanup failure here
    raise out of an atexit handler and mask whatever actually happened."""
    with contextlib.suppress(Exception):
        sweep_scratch_docs(client, tag)


@pytest.fixture(scope="session")
def client() -> Iterator[McpClient]:
    url = os.environ.get("FUSION_MCP_URL")
    if not url:
        pytest.skip("FUSION_MCP_URL not set; the live-Fusion suite is opt-in "
                     f"(recommended: {DEFAULT_URL})")
    c = McpClient(url)
    try:
        c.initialize()
    except Exception as e:
        pytest.skip(f"Fusion MCP endpoint at {url} did not initialize: {e}")

    sweep_scratch_docs(c, None)   # layer 1: pre-session sweep of prior leaks
    atexit.register(_best_effort_sweep, c, SESSION_TAG)   # layer 4

    yield c

    sweep_scratch_docs(c, SESSION_TAG)   # layer 3: session-end sweep


@pytest.fixture
def scratch(client: McpClient) -> Iterator[str]:
    """One tagged scratch document per test, closed in `finally` (layer 2)."""
    with scratch_doc(client, SESSION_TAG) as tag:
        yield tag
