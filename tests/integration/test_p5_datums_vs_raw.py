"""P5 -- datums + parameters vs raw coordinates. The decisive probe.

docs/probe-results.md P5: the same bracket built twice, once at raw
coordinates and once via a named datum with every dimension parameter-bound.
After a plate resize, the datum bracket stays exactly aligned (0.0mm on both
axes) while the raw-coordinate bracket drifts 40mm off the plate's edge and
8mm into it -- with Fusion reporting zero unhealthy timeline features either
way. `unhealthy == 0` is asserted deliberately: if a future Fusion starts
flagging this, that is news worth failing loudly for.
"""
import pytest

from tests.integration.mcp_client import McpClient, parse_fh_result
from tests.integration.probe_scripts import P5_DATUMS_VS_RAW

pytestmark = pytest.mark.fusion


def test_p5_datum_bracket_stays_aligned_raw_bracket_drifts(client: McpClient, scratch: str):
    res = client.execute(P5_DATUMS_VS_RAW)
    assert res.success, res.error
    data = parse_fh_result(res.message)

    assert data["bracketB_offset_x_mm"] == pytest.approx(0.0, abs=1e-4)
    assert data["bracketB_offset_z_mm"] == pytest.approx(0.0, abs=1e-4)

    assert data["bracketA_offset_x_mm"] == pytest.approx(40.0, abs=1e-4)
    assert data["bracketA_offset_z_mm"] == pytest.approx(8.0, abs=1e-4)

    # Asserted-silence: Fusion's own health reporting stayed clean even
    # though BracketA is now embedded in the plate.
    assert data["unhealthy"] == 0
