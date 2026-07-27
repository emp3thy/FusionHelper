# FusionHelper — Documentation

Read in this order.

| Document | What it is |
|---|---|
| [`superpowers/specs/2026-07-27-fusionhelper-design.md`](superpowers/specs/2026-07-27-fusionhelper-design.md) | **The design.** What we're building and why. Start here. |
| [`detailed-design.md`](detailed-design.md) | **The implementation-level design.** Every component, the reconciled interfaces between them, and the build order. Read after the spec. |
| [`probe-results.md`](probe-results.md) | **The evidence.** Eight probes run against a live Fusion install. Every design decision traces to one of these. |
| [`fusion-api-notes.md`](fusion-api-notes.md) | **The working reference.** Verified Fusion API behaviour, traps, and recipes. Keep this open while implementing. |
| [`research-findings.md`](research-findings.md) | **The literature.** LLM spatial-reasoning and CAD-generation research, prior art, and the reasoning behind the architecture. |

Written artefacts, not yet wired together:

| Path | What |
|---|---|
| `skills/fusion-design/reference/` | The skill's reference bundle — 740 lines |
| `design/verify/fh_verify.py` | The verification block — 995 lines |
| `design/verify/test_fh_verify_offline.py` | 43 offline assertions, passing without Fusion |

## In one paragraph

Claude Code can generate Fusion 360 Python that runs without error and produces geometry that
is wrong — parts misaligned, dimensions drifting, models that look parametric and die on the
first edit. Critically, **Fusion does not object**: a bracket 40 mm out of position and
embedded in a plate reports zero errors. FusionHelper is a Claude Code **skill** plus a small
Python **library** that makes those errors either impossible to express (named parameters and
datums instead of computed coordinates) or impossible to miss (a pre-flight static gate and a
numeric verification block on every generated script). It is **not** an MCP server — Autodesk
already ships one, and it works.

## The one-line summary of the evidence

Making errors *inexpressible* beat making them *detectable* by roughly 25× in the research,
and probe P5 showed why: the same bracket built with raw coordinates versus named datums was
identical at build time and 40 mm apart after one parameter edit — with no error raised either
way.
