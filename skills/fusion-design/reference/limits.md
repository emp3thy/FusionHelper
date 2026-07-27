# Limits — what these checks do not prove

Read this before telling the user a model is correct. These limits are stated in the
product, not hidden, and the wording at the bottom is the wording to use.

## Contents

- [Everything is checked against what was declared](#everything-is-checked-against-what-was-declared)
- [Autoformalization is the uncapped error term](#autoformalization-is-the-uncapped-error-term)
- [Fusion tolerates absurd-but-constructible geometry](#fusion-tolerates-absurd-but-constructible-geometry)
- [A parameter sweep catches reference failures, not absurdity](#a-parameter-sweep-catches-reference-failures-not-absurdity)
- [isFullyConstrained is a risk indicator, not a correctness gate](#isfullyconstrained-is-a-risk-indicator-not-a-correctness-gate)
- [Renders go to the human](#renders-go-to-the-human)
- [The honest claim](#the-honest-claim)

## Everything is checked against what was declared

Every check in this system verifies the model against the declaration block. **A
wrong-but-consistent declaration passes all of them.** If the parameter table says a bracket
is 40 mm wide and it should have been 50 mm, nothing here objects. Every dimension will be
bound, every sketch fully constrained, every clearance met, the timeline healthy, and the
part wrong.

This is not a gap to be closed by adding more checks of the same kind. It is the boundary of
what an oracle built from the declaration can do, and it is why **R8** forbids editing the
declaration to make a check pass — doing so destroys the only ground truth in the system and
leaves a green result meaning nothing at all.

## Autoformalization is the uncapped error term

Declaring constraints **relocates** the failure; it does not delete it. Writing
`coincident(bracket.back_face, plate.top_face)` requires knowing which face is the back face,
that it is the one that should mate, and that "coincident" rather than "offset 2 mm" is the
right relation. That is spatial reasoning, and it stays.

What the architecture removes is arithmetic and transform composition — a distinct, measured,
large failure class. What it does not remove is relational judgement.

Measured autoformalization rates across domains:

| Domain | Success rate |
|---|---|
| Kinematics problems → formal constraints | 62.5% |
| Codex on MATH | 25.3% |
| Cyber-physical systems | 70% |
| Semantic-consistency pipelines | 81.74% |
| Textbook geometry diagrams, with a verification loop | 98.7% (94.7% without) |

At the *best case* of 98.7% per-formalization accuracy, a 40-constraint assembly has
0.987^40 ≈ **59%** chance of being wholly correct.

And a silently wrong constraint is worse than a visibly wrong coordinate, because the solver
faithfully realises it and every downstream check passes.

The best measured handles on this gap are all weak: render-back to the model (−18% point-cloud
distance), redundant model-written postconditions (caught 1 real bug in 8 on Defects4J), and
human-in-the-loop clarification (~40% → 84%, but human-driven). Which is why the render goes
to the human.

## Fusion tolerates absurd-but-constructible geometry

Fusion's own health reporting is an incomplete oracle. It reports *reference* failures —
geometry it cannot construct — not geometry that is constructible and wrong.

Measured, on a live install:

- A bracket **40 mm off the plate edge and 8 mm embedded in the plate it sits on**:
  `timeline features=8  UNHEALTHY=0`. Zero errors, zero warnings.
- **60 mm holes on an 80 mm plate**: healthy.
- **A 0.4 mm plate thickness**: healthy.

The defect in the first case is entirely silent and would survive a visual check from an
unlucky angle. This is the whole reason the independent numeric checks exist and are
mandatory: interference caught exactly the defect the timeline was silent about, reporting a
3.2 cm³ clash with the pair correctly attributed.

**Never report a healthy timeline as a pass.**

## A parameter sweep catches reference failures, not absurdity

Driving each parameter to an extreme and scanning the timeline caught **1 of 4** extreme
configurations:

| Configuration | Result |
|---|---|
| `hole_d = 30 mm` | healthy |
| `hole_d = 60 mm` (holes exceed sensible spacing on an 80 mm plate) | healthy |
| `plate_t = 0.4 mm` | healthy |
| `plate_w = 30 mm` (plate narrower than the hole pattern) | **ERRORED** — reference failures |

When it does fire, the message is specific enough to act on: it names the feature and the
cause. But three of four absurd configurations passed.

Geometry that is constructible but absurd needs **separate assertions against declared
intent** — minimum wall thickness, edge distance, clearance. Those come from the declaration
block, not from Fusion.

## isFullyConstrained is a risk indicator, not a correctness gate

A generated model **rebuilt correctly on a parameter edit even though its sketch was never
fully constrained** — width, depth and thickness all rebuilt to the expected values, zero
unhealthy timeline features.

The flag is a usable, machine-checkable signal and it transitions cleanly at exactly the
point the last degree of freedom is removed. It is a necessary-condition check. It is not a
quality score, and surfacing it as one would mislead: the strongest published result in this
area reaches 93% fully-constrained and still names design alignment as an open problem.

Report it as a risk indicator. Do not report "fully constrained" as "correct".

## Renders go to the human

On identical spatial content, symbolic input measured roughly twice as accurate as image
input for frontier models — 0.957 versus 0.455 on one model, with the same ordering across
every model tested. The mechanism is that a vision model translates the image into language
space and reasons there anyway, so a render is a lossy auto-transcription, not geometry.

**This reproduced during this project.** A rendered iso view of a single joined body was read
as two interpenetrating parts; the numeric read-back showed one body with zero interference.
The render misled, the numbers did not.

Corroborating: adding rendered images alongside symbolic layouts gave *"no consistent
advantage over symbolic input alone"*; render feedback reached 0.127 point-cloud distance
where numeric feedback from the same paper reached 0.103; and an agentic harness lifted
executability by 27.9 pp while conditional shape metrics moved −0.010. Loops fix crashes, not
geometry.

Renders remain valuable for the one thing assertions structurally cannot do: catching **"this
is the wrong object entirely."** That is intent-checking, and it is the human's job.

So: show renders to the user. Do not use them to decide whether geometry is right. **If a
render and the numbers disagree, the numbers are right.**

## The honest claim

Do not present a green checklist as proof of correctness. Report:

> This model matches the description you gave. It is built correctly and it stays editable.

Never:

> This is the part you wanted.

Show the parameter table alongside the renders, so the user can check the one thing you
cannot.
