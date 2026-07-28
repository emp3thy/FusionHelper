"""Scratch-document lifecycle for the live Fusion integration suite.

Measured constraints (docs/detailed-design.md "Scratch document lifecycle"):
there is no `new`-document MCP operation, so scratch documents can only be
created from inside a script; the root component cannot be renamed, so
tagging goes through `des.attributes.add(...)` instead, which is also
enumerable across every open document.

Cleanup is HARNESS-driven, never script-driven: a script that raises never
reaches its own close call, so nothing here trusts a single close attempt.
Every caller above this module -- conftest's per-test fixture, session-end
sweep, pre-session sweep, and atexit -- calls back into
`sweep_scratch_docs`, which is the one place the close guard lives.

The close guard refuses three ways, checked in this order: never touch a
saved document, never an untagged one, never another session's tag (unless
swept in "any session" mode via tag=None, used only for the pre-session
sweep of a prior run's leaks).

Verified live 2026-07-28 against a real Fusion install: `app.documents.add`
activates the new document; `doc.products.itemByProductType('DesignProductType')`
retrieves a non-active document's design without switching focus to it;
`des.attributes.itemByName(group, name)` reads the tag back; `doc.close(False)`
closes without saving and leaves other open (saved) documents untouched.
"""
import json
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from tests.integration.mcp_client import McpClient

ATTR_GROUP = "fusionhelper"
ATTR_NAME = "scratch"
SESSION_TAG_PREFIX = "fh-test-"

_CREATED_PREFIX = "fh-scratch-created "
_SWEEP_RESULT_PREFIX = "fh-sweep-result "
_READBACK_PREFIX = "fh-scratch-tags "

# Plain (non-f-string) templates: the emitted script builds a JSON dict
# literal itself, and an f-string would need every one of those braces
# escaped. Placeholders are replaced with plain substring substitution
# instead, which is safe here because every value substituted in is
# generated internally (uuid hex, fixed literals), never user input.
_CREATE_SCRIPT_TEMPLATE = """
import adsk.core, adsk.fusion
app = adsk.core.Application.get()
doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
des = adsk.fusion.Design.cast(app.activeProduct)
des.attributes.add('__ATTR_GROUP__', '__ATTR_NAME__', '__TAG__')
print('__CREATED_PREFIX__' + '__TAG__')
"""

_SWEEP_SCRIPT_TEMPLATE = """
import json
import adsk.core, adsk.fusion
app = adsk.core.Application.get()
target_tag = __TARGET_TAG__
eligible = []
skipped = []
docs = app.documents
for i in range(docs.count):
    doc = docs.item(i)
    name = doc.name
    try:
        if doc.isSaved:
            skipped.append(name + ':saved')
            continue
        try:
            prod = doc.products.itemByProductType('DesignProductType')
        except Exception:
            prod = None
        if prod is None:
            skipped.append(name + ':no-design')
            continue
        des = adsk.fusion.Design.cast(prod)
        attr = des.attributes.itemByName('__ATTR_GROUP__', '__ATTR_NAME__')
        if attr is None:
            skipped.append(name + ':untagged')
            continue
        doctag = attr.value
        if target_tag is not None and doctag != target_tag:
            skipped.append(name + ':other-session:' + str(doctag))
            continue
        eligible.append((doc, name, doctag))
    except Exception as e:
        skipped.append(name + ':inspect-error:' + str(e))

closed = []
errors = []
for doc, name, doctag in eligible:
    try:
        doc.close(False)
        closed.append(name + ':' + str(doctag))
    except Exception as e:
        errors.append(name + ':' + str(e))

print('__SWEEP_PREFIX__' + json.dumps({'closed': closed, 'skipped': skipped, 'errors': errors}))
"""

_READBACK_SCRIPT_TEMPLATE = """
import json
import adsk.core, adsk.fusion
app = adsk.core.Application.get()
found = []
docs = app.documents
for i in range(docs.count):
    doc = docs.item(i)
    if doc.isSaved:
        continue
    try:
        prod = doc.products.itemByProductType('DesignProductType')
    except Exception:
        prod = None
    if prod is None:
        continue
    des = adsk.fusion.Design.cast(prod)
    attr = des.attributes.itemByName('__ATTR_GROUP__', '__ATTR_NAME__')
    if attr is not None:
        found.append(str(attr.value))
print('__READBACK_PREFIX__' + json.dumps(found))
"""


def new_session_tag() -> str:
    return SESSION_TAG_PREFIX + uuid.uuid4().hex


def _create_script(tag: str) -> str:
    return (_CREATE_SCRIPT_TEMPLATE
            .replace("__ATTR_GROUP__", ATTR_GROUP)
            .replace("__ATTR_NAME__", ATTR_NAME)
            .replace("__CREATED_PREFIX__", _CREATED_PREFIX)
            .replace("__TAG__", tag))


def _sweep_script(tag: str | None) -> str:
    target_expr = "None" if tag is None else repr(tag)
    return (_SWEEP_SCRIPT_TEMPLATE
            .replace("__ATTR_GROUP__", ATTR_GROUP)
            .replace("__ATTR_NAME__", ATTR_NAME)
            .replace("__SWEEP_PREFIX__", _SWEEP_RESULT_PREFIX)
            .replace("__TARGET_TAG__", target_expr))


def _readback_script() -> str:
    return (_READBACK_SCRIPT_TEMPLATE
            .replace("__ATTR_GROUP__", ATTR_GROUP)
            .replace("__ATTR_NAME__", ATTR_NAME)
            .replace("__READBACK_PREFIX__", _READBACK_PREFIX))


def read_scratch_tags(client: McpClient) -> list[str]:
    """Read the fusionhelper/scratch attribute value off every unsaved
    document currently open, independent of any particular session's tag.

    Exists because the sweep-based leak check alone cannot catch a silent
    tagging failure: if `create_scratch_doc` created a document but the
    `attributes.add` call silently didn't stick, a tag-scoped sweep would
    never find that document either, so "nothing left to sweep" would look
    identical to "the tag was never written". This reads the attribute back
    directly and lets the caller assert its value, not just its absence.
    """
    res = client.execute(_readback_script())
    if not res.success:
        raise RuntimeError(f"scratch tag read-back failed: {res.error}")
    for line in reversed(res.message.splitlines()):
        if line.startswith(_READBACK_PREFIX):
            return json.loads(line[len(_READBACK_PREFIX):])
    raise RuntimeError(f"no {_READBACK_PREFIX!r} line found in: {res.message!r}")


def create_scratch_doc(client: McpClient, tag: str) -> None:
    """Create a new scratch document and tag it. Raises on any script
    failure -- the caller must not treat an unconfirmed creation as safe to
    proceed, since a false negative here would leave nothing for the sweep
    layers to find and close."""
    res = client.execute(_create_script(tag))
    if not res.success:
        raise RuntimeError(f"scratch doc creation failed: {res.error}")


@dataclass
class SweepResult:
    closed: list[str]
    skipped: list[str]
    errors: list[str]


def sweep_scratch_docs(client: McpClient, tag: str | None) -> SweepResult:
    """Close every unsaved, tagged scratch document matching `tag`.

    tag=None sweeps ANY fusionhelper/scratch-tagged document regardless of
    which session created it -- used only for the pre-session sweep of a
    prior run's leaks. All other layers pass the current session's tag.

    tag=None is therefore unsafe to call while another pytest session is
    concurrently running this suite against the same Fusion instance: it
    cannot distinguish "a prior session's leak" from "another session's
    document in active use" and will close both. Concurrent sessions against
    one Fusion process are unsupported; see conftest.py's module docstring.
    """
    res = client.execute(_sweep_script(tag))
    if not res.success:
        raise RuntimeError(f"scratch sweep failed: {res.error}")
    for line in reversed(res.message.splitlines()):
        if line.startswith(_SWEEP_RESULT_PREFIX):
            data = json.loads(line[len(_SWEEP_RESULT_PREFIX):])
            return SweepResult(**data)
    raise RuntimeError(f"no {_SWEEP_RESULT_PREFIX!r} line found in: {res.message!r}")


@contextmanager
def scratch_doc(client: McpClient, session_tag: str) -> Iterator[str]:
    """Create one scratch document tagged with `session_tag`, yield the tag,
    then sweep it in `finally`.

    This is the per-test cleanup layer. It intentionally calls the same
    `sweep_scratch_docs` the session-end and pre-session layers use, rather
    than closing only the document just created, so a document leaked by an
    earlier failure under the same tag is also caught here instead of
    surviving to the next layer.
    """
    create_scratch_doc(client, session_tag)
    try:
        yield session_tag
    finally:
        sweep_scratch_docs(client, session_tag)
