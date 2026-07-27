# Research Findings — LLM Spatial Reasoning and CAD Generation

Synthesis of a five-agent research sweep run 2026-07-27, to ground FusionHelper's design in
evidence rather than intuition. Each agent was given a distinct lens and instructed to mark
inferences as INFERRED and to state coverage gaps rather than pad.

Confidence markers are the researching agents'. Where this project later contradicted a
finding empirically, that is noted inline — see [`probe-results.md`](probe-results.md).

---

## 1. The headline result

The interventions with the largest measured effects are not the sophisticated ones.

| Intervention | Measured effect | Source |
|---|---|---|
| **Remove an axis of reasoning; deterministic code derives it** | **+28.7 pp** (65.9% → 94.6%) | 2.5-D Decomposition, arXiv 2605.07066 |
| **Solver-feedback DOF gate before geometry** | **8.9% → 34% → 93%** fully-constrained | Autodesk Research, arXiv 2504.13178 |
| Numeric assertions vs declared spec | point-cloud distance −34% (0.155 → 0.103) | CADCodeVerify, ICLR'25 |
| Render feedback to the model | PCD −18% (0.155 → 0.127) | CADCodeVerify |
| **LLM declares constraints, solver computes coordinates** | **+1.14 CLIP points** (31.51 → 32.65) | MagicGeo, arXiv 2502.13855 |

The 2.5-D result is worth reading closely: it beat the prior state of the art by 18.3 points
**using a smaller model**, and GPT-4o-mini beat GPT-4o on the same pipeline (p<0.0001). The
pipeline mattered more than the model.

**Organising principle taken from this: make the error inexpressible rather than detectable.**
The cheap structural intervention outperformed the elaborate solver architecture by roughly
25×.

---

## 2. The nature of the deficit — representational, not bookkeeping

The initial hypothesis was that spatial errors are a *bookkeeping* failure: the model can
represent the geometry but loses track of it over a long generation. If true, externalising
state into a structured model would largely fix it.

The evidence leans the other way, and three results cut against the bookkeeping story
directly:

1. **arXiv 2603.26779** (Hayashi & Hirata) gave an MLLM an external "Imagery Module" that
   renders and rotates real 3D models — removing the memory burden entirely. Accuracy still
   capped at **62.5%**. Verbatim: *"even when the burden of maintaining and manipulating a
   holistic 3D state is outsourced, the system still fails."*
2. **arXiv 2605.02028** (Dai & Fan, 126 model variants) found exact-state preservation fails
   at an abrupt, model-dependent threshold, traced by mechanistic probing to a **finite set
   of internal states**, and explicitly unfixed by *"increasing model size, inference time
   computation, and external tool."*
3. **arXiv 2605.20448** localised occlusion failure to a specific architectural site — spatial
   information is recoverable through the ViT but *"becomes inaccessible after the visual-token
   merger."* Destroyed at encode time, not lost over a long generation.

Supporting this, **Mind's Eye** (arXiv 2604.16054, 18 MLLMs) found models show **flat
difficulty curves (0.20–0.45)** where humans *"degrade predictably from easy to hard."* A
system that had the representation but was losing track would degrade with difficulty. Flat
suggests it was never tracking.

### Measured failure modes

| Failure mode | Evidence | Confidence |
|---|---|---|
| Object orientation is the worst spatial primitive | 3DSRBench: GPT-4o **21.6%** orientation vs 59.6% location. DORI (24 models, 33,656 Qs): best closed-source 68.5% vs human 88.0%. Canonical orientation *"remains unsolved under every intervention tested"* | High |
| Mental rotation collapses; coarse answers mask it | DORI: −30% on dynamic rotational vs static pose ID; compound rotations 49.0% coarse but near-random on granular angular estimation | High |
| Occlusion reasoning collapses while visible-geometry reasoning is fine | arXiv 2605.20448: volumetric collision planning 53–97%, depth-ordered occlusion **6–45%**, reflection tracing 1–7% | High |
| Absolute/metric estimation far worse than relative | VSI-Bench: GPT-4o absolute distance **5.3%** vs relative distance 37.0% | High |
| Reasoning is the bottleneck, not perception | VSI-Bench manual review of 163 wrong answers: ~71% spatial reasoning errors, ~10% visual perception | High |
| CAD generation degrades sharply with complexity | Text2CAD-Bench: GPT-5.2 invalidity 11.1% (L1) → 20.0% (L2) → **68.0%** (L3); Claude-4.5 20.3% → 43.7% → 70.0% | High |
| **Egocentric is NOT better than allocentric** — the assumed asymmetry is backwards | ViewSpatial-Bench: camera-perspective 33.2% vs person-perspective 35.7% (allocentric slightly *higher*); both barely above the 26.33% random baseline | High |

### What the evidence does *not* show

- **Per-step error compounding across transform chains is not directly measured anywhere.**
  Plausible by analogy; treat as INFERRED, not established.
- **No benchmark exists for holding one named dimension stable across many references in a
  long generation** — which is one of the two originally-stated failure modes. Confirmed
  independently by two agents. Unmeasured.
- **No benchmark for solid-model topology counting** (faces, edges, holes of a B-rep).
- *"Give it a 3D tool and the deficit goes away"* is contradicted twice (2603.26779, 2605.02028).

---

## 3. Text beats images, and verbose reasoning hurts

**SpatialEval** (arXiv 2406.14852, NeurIPS'24) tested identical spatial content across
modalities:

| Model | Text (TQA) | Image (VQA) |
|---|---|---|
| Claude 3 Opus | **0.957** | 0.455 |
| GPT-4V | **0.923** | 0.668 |
| GPT-4o | **0.986** | 0.833 |

The paper's own mechanism: *"VLM architectures attempt to translate the vision input into
the language space and all reasoning is then performed in the language domain, so this
automatic translation path is worse than a human-provided translation to text."* Renders do
not give the model geometry — they give it a lossy auto-transcription, after which it reasons
in language anyway.

Corroborating evidence that render-feedback to the model is dominated wherever symbolic
checks exist:

- **FloorplanQA**: adding rendered images alongside structured symbolic layouts gave
  *"no consistent advantage over symbolic input alone."*
- **CADCodeVerify**: 4-view render feedback reached PCD 0.127; the same paper's *numeric*
  solver feedback reached **0.103** — nearly double the effect, from text.
- **3DCodeBench**: an agentic harness lifted executability 0.716 → 0.995 (+27.9 pp) while
  conditional shape metrics moved **−0.010**. Loops fix crashes, not geometry.

**Verbose spatial deliberation actively hurts.** VSI-Bench: Zero-Shot CoT **−4%**,
Self-Consistency+CoT −1.1%, Tree-of-Thoughts **−4%**. The paper states linguistic prompting
techniques *"are harmful for spatial reasoning."*

> **This reproduced during the project itself.** A rendered iso view of the user's model was
> read as two interpenetrating bodies; the numeric read-back showed a single joined body with
> zero interference. The render misled, the numbers did not. See `probe-results.md`.

**Design consequence:** renders are for the human, who is checking *intent* — the one thing
assertions structurally cannot do. Do not spend design effort on view counts, wireframe vs
shaded, or burned-in dimension annotations for the model's benefit; the only evidenced
distinction is 1-view vs many, and the one N-sweep that exists was flat (varying by ≤0.012).

---

## 4. Constrained output — the CRANE shape

Constraining the output format is a genuine lever with a documented backfire.

- **Strict format constraints degraded reasoning accuracy by up to 27 percentage points** on
  math benchmarks (EMNLP 2024). Mechanism: the schema forces the answer field to be emitted
  before chain-of-thought completes.
- **CRANE** (ICML 2025, arXiv 2502.09061) is the fix and proves the general point: strict
  grammars reduce reasoning, but *augmenting* the grammar to permit free reasoning between
  delimiters preserves it — **up to +10 pp over both strict-constrained and unconstrained**
  decoding.
- **AIDL** independently saw valid-program rate drop **94% → 64%** when constraints were added,
  while quality rose. Constraining the output space has a real robustness cost.

**Design consequence:** never force the declaration format as a whole-output grammar. Reason
in prose, emit the typed block between delimiters, validate the block.

---

## 5. Prior art

### Text-to-CAD systems

| System | Generates | Reusable? | Limitation |
|---|---|---|---|
| **Text2CAD** (NeurIPS'24) | DeepCAD command sequence | No | Invalidity 2% but Chamfer 234–270 and **near-zero IoU** — reliably emits code that is geometrically wrong |
| **Zoo / KittyCAD Text-to-CAD** | KCL → B-rep | No (closed ecosystem) | **Non-determinism is the headline flaw** — *"the same prompt can produce noticeably different geometry on different runs"*; their newer, more powerful model is *less* reliable at emitting valid KCL |
| **CAD-GPT / CAD-MLLM / CAD-Coder** | Command sequences | No | Same representation ceiling; none handle multi-part assemblies or mating |
| **Adam** (YC W25) | OpenSCAD | Marginal | Mesh output, no parametric control |
| **CADGenBench** (HuggingFace, 87★, Apache-2.0) | Benchmark + scoring engine | **Yes — metrics** | Tool-agnostic; submission is a STEP file |
| **build123d-mcp** (pzfreo, Apache-2.0) | build123d in a sandboxed session | **Yes — design template** | Not Fusion; headless only |

### The critical representation ablation

**Text2CAD-Bench** ran the same models generating CadQuery **Python** versus OpenSCAD-style
**command sequences**. DeepSeek's L1 invalidity went **13.3% → 67.3%** on the switch to
command sequences.

**Python-code-as-representation is worth roughly a 5× reduction in invalid output.** This
generalises (INFERRED) to Fusion's Python API, and argues for driving Fusion via generated
scripts rather than a fine-grained verb-per-tool MCP surface — which is what FusionHelper does.

Relatedly, **procedural descriptions beat appearance descriptions**: Text2CAD-Bench L3
Chamfer 82.94 under procedural-sequence prompts vs 93.46 under geometric/appearance prompts.

### Consistent real-world failure reports

- **Coordinate-frame confusion is the #1 named cause.** Models mix Y-up and Z-up and rotate
  about the wrong axis; Euler order *"is easy to get backwards."* Independently, the
  FirePlace/Prompt2Craft line reports *"the main cause of failure in 3D generation is the
  collision validation step, with common errors including misplacement and incorrect
  orientation of parts."*
- **The ecosystem disagrees about which axis is up.** AuraFriday's Fusion MCP (111★) ships a
  best-practices doc stating *"Y-axis: Height (UP/vertical)"*; rahayesj's ships one stating
  Z is up. Both are field-derived. → **verified directly for this project; see
  `fusion-api-notes.md`.**
- **Units.** Every Fusion MCP repo independently flags this as the top error source: the
  Fusion API is always **centimetres**, users always think millimetres. → **confirmed on this
  machine** (7.52 API cm = 75.2 UI mm).
- **No feedback path from geometry back to code**, the most-upvoted substantive HN complaint:
  *"you can't easily go from geometry back to code. When an LLM generates OpenSCAD and the
  output is wrong, you're staring at an STL with no way to point at a face and say 'this edge
  should be 2mm shorter.'"*
- **Silent success is the dangerous mode.** *"Geometry that looks right but won't print is the
  silent killer."* A boolean that produces no change because the bodies don't intersect
  returns *success*. → **reproduced in probe P5.**
- **Visual verification is the most fragile link in practice.** All 7 open issues on
  ndoo/fusion360-mcp-bridge are the same bug: screenshot capture broken against Fusion
  2702/2704. Verification should be primarily numeric, with rendering secondary.
- **The ceiling is exactly this project's target domain.** HN: the loop works for *"jigs,
  brackets, adapters, small fixtures"* but *"hits a ceiling quickly. Anything beyond simple
  parametric primitives becomes painful (complex geometry, precise interfaces, assemblies,
  tolerances/fit)."*

### Reuse candidates

**CADGenBench scoring engine** — four axes mapping onto the failures FusionHelper targets:
validity (watertight closed manifold), shape similarity (surface-distance F1, volume IoU),
**interface match** (mating correctness via keep-in/keep-out sub-volumes), and **topology
match** via **Betti numbers** (b0 > 1 immediately catches the floating-disconnected-part bug).

**build123d-mcp** is the strongest evidence the general approach works: on the public
CADGenBench leaderboard it raised the *same model's* score **0.360 → 0.457** and CAD validity
**88% → 100%**. Its doctrine, verbatim, and adopted here: *"Prefer `measure()` over
`render_view()` for verifying geometry — numbers are unambiguous."*

**faust-machines/fusion360-mcp-server** (MIT, 81 tools) is the cleanest Fusion MCP —
uniquely among them it already has `check_interference` (11 code hits, vs 0 in AuraFriday,
ndoo and JustusBraitinger). Its `hints.py` maps regex → `error_kind` → remediation hints for
`PROFILE_NOT_CLOSED`, `SELF_INTERSECTION`, `BOOLEAN_NO_OP`, `REGEN_FAILED` — a good model for
FusionHelper's error table.

### Geometry kernels (evaluated, then found unnecessary)

| | Boolean intersection volume | Min distance | Headless PNG on Windows |
|---|---|---|---|
| **build123d** | `Shape.intersect(..., include_touched=False)` → `.volume` | `distance_to_with_closest_points()` (BRepExtrema) | Yes, VTK in-process |
| **CadQuery** | `Shape.intersect()` → `Shape.Volume()` | `Shape.distance()` | Yes, same VTK path |
| **OCP / pythonOCC** | `BRepAlgoAPI_Common` + `BRepGProp` | `BRepExtrema_DistShapeShape` | Wire VTK yourself |
| **trimesh** | Needs manifold3d/Blender backend | Needs `python-fcl` | Weakest on Windows |

build123d was the recommendation had a kernel been needed. **It was not** — Fusion's own
solver and interference API cover every requirement. See the spec's *Why no external geometry
kernel*.

---

## 6. Delivery vehicle analysis

| Vehicle | Serves procedure? | Serves tool access? | Images to model? | Context cost |
|---|---|---|---|---|
| **Skill** | **Yes — best.** Body injected once and **persists for the session** | Indirectly, via bundled scripts run through Bash | Yes (script writes PNG → `Read`) | Name+description at startup; body on invoke; bundled files cost **zero** until read |
| **MCP server** | Weak — only tool names/descriptions, nothing that persists | Yes — best; only vehicle reaching a resident process | Yes, `image` content block | 50 tools ≈ 10–20K tokens/turn; selection degrades past 30–50 tools |
| Plugin | Inherits both | Inherits both | Inherits both | Same as its parts |
| Library + CLI | **No** | Cannot reach a live Fusion session without a bridge | Yes | Cleanest — only stdout enters context |

**The decisive property**, from Anthropic's skills documentation: *"the rendered SKILL.md
content enters the conversation as a single message and stays there for the rest of the
session… Claude Code does not re-read the skill file on later turns, so write guidance that
should apply throughout a task as standing instructions."*

The problem being solved is **drift over a long session**. A skill body is the only vehicle
whose text remains resident throughout. An MCP tool description is not.

Also relevant: **PLAN-VALIDATE-EXECUTE is a named Anthropic skills pattern** (analyse →
create plan → validate → execute → verify, with an explicit "if validation fails, return to
step N" loop). FusionHelper's workflow is a documented pattern, not an invention.

### Token economics

- Anthropic's tool-search doc: *"50 tools can use 10-20K tokens… Tool selection accuracy
  degrades with more than 30-50 tools loaded at once."*
- Code-execution-with-MCP: presenting tools as code on a filesystem took a worked example
  from **150,000 tokens → 2,000 tokens (98.7% saving)**, chiefly by keeping intermediate data
  out of context.
- Skills best-practices: *"Utility scripts can be executed through bash without loading their
  full contents into context. Only the script's output consumes tokens."*

**Design consequence: design the return payloads, not just the tool count.** A verification
result reading `"12 checks passed, 1 failed: bracket_A overlaps plate_B by 3.2mm on -Z"` costs
~40 tokens; returning the B-rep costs ~8,000. Intermediate geometry must never round-trip
through context.

### Image mechanics — verified, not assumed

Two routes exist. Both were tested rather than taken on trust, because stale GitHub issues
(#18588, #30925, #31208) claim images from external MCP servers are stringified into text
rather than seen as vision.

- **Route A** — script writes a PNG, Claude `Read`s it. Verified working on this machine.
- **Route B** — MCP tool returns an `image` content block (base64 `data`, `mimeType`; no
  `data:` prefix; SVG unsupported and has crashed sessions per issue #28279).
  **Verified working with Autodesk's Fusion MCP** — a viewport screenshot arrived as a genuine
  vision block. Issue #31208 does not apply to this server.

Useful adjunct: `structuredContent` can ride *alongside* an image block, so a render and the
numeric state behind it can return in one round-trip.

### The strongest counter-argument to the chosen design

Recorded because it is right and may yet matter:

> **Procedure in a skill is advisory.** Claude can read "verify before emitting" and then not
> verify — the exact failure mode the project exists to fix. An MCP server could make it
> *structurally impossible*: `emit_geometry` hard-refuses unless a matching validated-layout
> hash exists. Enforcement beats instruction. Skill persistence also cuts both ways — injected
> once and never re-read, that early message competes with tens of thousands of tokens of
> newer chatter as the session grows. **If you only build one, build the gate.**

FusionHelper's answer: the transport is Autodesk's MCP, which we do not control and should
not fork, so a hard gate means building and maintaining a proxy. The pre-flight gate is a
mandated library call whose output is unmissable in the transcript. If advisory discipline
proves insufficient in practice, the escalation is a wrapper refusing to call
`fusion_mcp_execute` without a passing pre-flight result — a v2 decision, on evidence.

---

## 7. Interventions assessed but not adopted

| Intervention | Why not |
|---|---|
| Render feedback **to the model** as a loop stage | Dominated wherever symbolic verification exists. Kept for the human. |
| Optimising view count / wireframe vs shaded / annotated dimensions for the model | Only 1-vs-many is evidenced; the one N-sweep was flat (≤0.012) and measured input conditioning, not verification |
| Strict schema-forced geometry output | −27 pp on reasoning. Use the CRANE shape or not at all. |
| External constraint solver as the spine | +1.14 CLIP points, and Fusion provides both things it was for |
| SMT / exact rational solving as the spine | Fillets, chamfers, counterbores, dowel circles, hinge axes, draft and mitres all leave the linear regime immediately. Worth ~20 lines on an axis-aligned bounding-box layer and nothing beyond. |
| Autonomous clarification loops | The one CAD study that measured `askBack` found it **hurt**: 22/60 vs 26/60 |
| Self-critique without external signal | Self-Correction Blind Spot: models fix errors in external content and systematically miss identical errors in their own |
| Multi-agent role-splitting per se | ArtiCAD and ASSEMCAD both ship 4-agent architectures *and* introduce a new representation simultaneously; neither isolates the split. The representation is the plausible active ingredient. |

**"Fully constrained" must not be read as "correct."** The Autodesk paper reaches 93%
fully-constrained and still names design alignment as open. It is a necessary-condition check;
surfacing it as a quality score would mislead. → **independently confirmed in probe P1**, where
a model rebuilt correctly while never being fully constrained.

---

## 8. The residual — autoformalization

The uncapped error term in this design, stated plainly because the product must state it too.

Constraint declaration **relocates** the failure; it does not delete it. Writing
`coincident(bracket.back_face, plate.top_face)` requires knowing which face is the back face,
that it is the one that should mate, and that "coincident" rather than "offset 2 mm" is the
right relation. That is spatial reasoning. What the architecture removes is *arithmetic and
transform composition* — a distinct, measured, large failure class. What it does not remove is
*relational judgement*.

Measured autoformalization rates:

| Domain | Success rate |
|---|---|
| Kinematics problems → formal constraints (arXiv 2509.21840) | **62.5%** |
| Codex on MATH | 25.3% |
| Cyber-physical systems | 70% |
| Semantic-consistency pipelines | 81.74% |
| MagicGeo, textbook geometry diagrams, with verification loop | **98.7%** (94.7% without) |

At MagicGeo's *best case* of 98.7% per-formalization accuracy, a 40-constraint assembly has
0.987^40 ≈ **59%** chance of being wholly correct. And a silently wrong constraint is worse
than a visibly wrong coordinate, because the solver faithfully realises it and every
downstream check passes.

The best measured handles on this gap are all weak: VQA-style render-back (−18% PCD),
redundant LLM-written postconditions (caught **1 in 8** real bugs on Defects4J), and
human-in-loop clarification (TiCoder ~40% → 84%, but human-driven). Intent Formalization
(arXiv 2603.17150) states it directly: *"if the specification misses intent, verified code can
still be wrong."*

**Hence the product's honest claim: this model matches the description you gave, built
correctly and editably. Not: this is the part you wanted.**

---

## Sources

**Spatial reasoning benchmarks and mechanisms**
- arXiv [2406.14852](https://arxiv.org/abs/2406.14852) — SpatialEval (NeurIPS'24)
- arXiv [2412.14171](https://arxiv.org/abs/2412.14171) — Thinking in Space / VSI-Bench
- arXiv [2505.21649](https://arxiv.org/html/2505.21649v7) — DORI
- arXiv [2505.21500](https://arxiv.org/html/2505.21500v2) — ViewSpatial-Bench
- arXiv [2603.26779](https://arxiv.org/abs/2603.26779) — Limits of Spatial Imagery Reasoning
- arXiv [2605.02028](https://arxiv.org/abs/2605.02028) — Language models fail at extended rule following
- arXiv [2605.20448](https://arxiv.org/html/2605.20448) — Do VLMs Understand 3D Scenes?
- arXiv [2604.16054](https://arxiv.org/html/2604.16054v1) — Mind's Eye
- arXiv [2510.04401](https://arxiv.org/abs/2510.04401) — VLMCountBench

**Interventions**
- arXiv [2605.07066](https://arxiv.org/html/2605.07066) — 2.5-D Decomposition
- arXiv [2504.13178](https://arxiv.org/abs/2504.13178) — Autodesk, design alignment / DOF gate
- arXiv [2502.13855](https://arxiv.org/html/2502.13855v1) — MagicGeo
- arXiv [2502.09819](https://arxiv.org/html/2502.09819) — AIDL
- arXiv [2410.05340](https://arxiv.org/html/2410.05340v2) — CADCodeVerify
- arXiv [2606.09278](https://arxiv.org/html/2606.09278v1) — PyGeoX
- arXiv [2502.09061](https://arxiv.org/html/2502.09061v3) — CRANE
- arXiv [2509.21840](https://arxiv.org/pdf/2509.21840) — Can LLMs Autoformalize Kinematics?
- arXiv [2603.17150](https://arxiv.org/html/2603.17150v1) — Intent Formalization
- arXiv [2606.01057](https://arxiv.org/html/2606.01057v1) — 3DCodeBench
- arXiv [2412.02193](https://arxiv.org/html/2412.02193) — LayoutVLM

**CAD generation**
- arXiv [2605.18430](https://arxiv.org/html/2605.18430v1) — Text2CAD-Bench
- arXiv [2606.31252](https://arxiv.org/html/2606.31252v1) — Embodied CAD
- arXiv [2607.05123](https://arxiv.org/abs/2607.05123) — ASSEMCAD
- arXiv [2604.10992](https://arxiv.org/abs/2604.10992) — ArtiCAD

**Prior art / repos**
- [huggingface/cadgenbench](https://github.com/huggingface/cadgenbench)
- [pzfreo/build123d-mcp](https://github.com/pzfreo/build123d-mcp)
- [faust-machines/fusion360-mcp-server](https://github.com/faust-machines/fusion360-mcp-server)
- [rahayesj/ClaudeFusion360MCP](https://github.com/rahayesj/ClaudeFusion360MCP) — `docs/SPATIAL_AWARENESS.md`
- [AuraFriday/Fusion-360-MCP-Server](https://github.com/AuraFriday/Fusion-360-MCP-Server)
- [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp)
- [autodesk-platform-services](https://github.com/autodesk-platform-services) — official APS MCP repos

**Field reports**
- [HN: Ask HN — professional-level CAD models](https://news.ycombinator.com/item?id=46888906)
- [Why LLMs fail at OpenSCAD code generation](https://dev.to/alanwest/why-llms-fail-at-openscad-code-generation-and-how-to-fix-it-2bel)
- [ModelRift OpenSCAD LLM benchmark](https://modelrift.com/blog/openscad-llm-benchmark/)

**Anthropic documentation**
- [Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Custom tools / content blocks](https://code.claude.com/docs/en/agent-sdk/custom-tools)
- [Tool search](https://code.claude.com/docs/en/agent-sdk/tool-search)
- [Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp)

### Sourcing caveats

- 3DSRBench and SepSeq figures come from search snippets, not full page reads.
- ASSEMCAD and ArtiCAD publish no numbers; mechanism only, from abstracts.
- Autodesk 2504.13178's 8.9/34/93% figures come from the abstract; the results tables would
  not extract.
- CAD-Assistant (ICCV 2025) was inaccessible (403).
- `forums.autodesk.com` returned 403 to every fetch attempt; forum-derived claims are from
  search extracts rather than full reads.
- No head-to-head experiment exists anywhere comparing "solver replaces reasoning" against
  "tool assists reasoning" as philosophies. The distinction is named in four papers; nobody
  has run it. **FusionHelper is that experiment.**
