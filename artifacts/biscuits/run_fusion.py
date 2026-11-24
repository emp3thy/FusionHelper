"""Execute a bundled artifact in the open Fusion over its MCP port and
save the full stdout/error to a sibling .log file."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests" / "integration"))
from mcp_client import McpClient  # noqa: E402

path = Path(sys.argv[1])
c = McpClient("http://127.0.0.1:27182/mcp")
c.initialize()
r = c.execute(path.read_text(encoding="utf-8"))
log = path.with_suffix(".log")
log.write_text("SUCCESS=%s\n--- message ---\n%s\n--- error ---\n%s\n" % (r.success, r.message, r.error), encoding="utf-8")
print("SUCCESS", r.success)
text = r.message if r.success else r.error
for line in text.splitlines():
    if line.startswith(("FH ", "FH_VERDICT1", "FH_CHECK1")) or "Error" in line or "error" in line[:40]:
        print(line[:400])
print("log:", log)
