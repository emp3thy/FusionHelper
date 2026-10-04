# Instructions for each wine-rack designer agent

You are one of three designers. Work in C:\Users\gethi\sources\FusionHelper.
Do not ask the user anything; make and state your assumptions. Do not commit.
Do not touch files belonging to the other two designers.

## Read first (in this order)
1. docs/wine-rack/design-brief.md  (the constraints - every number in it binds)
2. the four research reports in docs/wine-rack/ (skim; dig where your design needs it)
3. skills/fusion-design/SKILL.md (the ten rules; the gate cites them)
4. fusionhelper/buildkit.py (the helper API you build with) and
   artifacts/spinner-scripts/or3_build.py as an example author script
5. skills/fusion-design/reference/api-recipes.md - only the sections you need

## Deliverable A - Fusion build script (fusion-design skill, buildkit workflow)
- Author script: artifacts/wine-rack/<slug>_author.py importing
  `from fusionhelper.buildkit import *`, no stub of your own.
- Parameter table first (snake_case user parameters: space_w, fit_gap, rack_d,
  slot_clear, pitch, wall_t, cell count etc.), named datums, no raw coordinates,
  createByString only, every dimension bound to a parameter expression, no
  index topology picks, no try/except, no document save.
- Model the rack as its printable MODULES (the bodies that go on the plate),
  laid out in one document, with the joints modelled (dovetail / conical
  tongue / keyed) at the clearances in the brief. Each module must fit the H2D
  single-nozzle bed (325 x 320 x 325) in the orientation you intend to print it,
  or on the diagonal if you say so. Keep the body count sane (chunk loops,
  adsk.doEvents() per ~20 mutations).
- Bundle: `python -m fusionhelper.bundle artifacts/wine-rack/<slug>_author.py`
  then gate: `python -m fusionhelper.preflight artifacts/wine-rack/<slug>_author.bundled.py`
  Run the gate as its own command and check the exit code explicitly (never
  through a pipe). Fix until exit 0, budget 3 fix rounds; if still failing,
  say exactly what fails. Exit 3 is an environment problem - report, do not
  edit the script.
- The Fusion MCP is NOT available in this session: do not try to execute in
  Fusion. Say in your report that execution/verification is pending.

## Deliverable B - design page (HTML artifact file)
Write artifacts/wine-rack/<slug>.html. The file is published by the lead with
the Artifact tool, which wraps it in a document skeleton, so:
- NO <!doctype>, <html>, <head> or <body> tags. Start with `<title>` (a 2-4
  word product-style name for the design, no colon/dash explainer) then
  `<style>`, then the content.
- Inline all CSS and JS. External resources allowed ONLY: Google Fonts
  stylesheet links (with fallback stacks) and scripts from cdnjs.cloudflare.com.
  No images from the web; draw everything as inline SVG (to scale, mm units,
  explicit fills, theme-token colours) or canvas. No iframes, no print button.
- Theme tokens: define every colour on bare `:root` (light), then redefine
  under `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {... color-scheme: dark} }`
  and again under `:root[data-theme="dark"] {...}`. `body { background: var(--bg); color: var(--fg) }`.
  No literal colours in component rules.
- Responsive to 400 px wide, 16 px side gutter set once on body, no
  horizontal page scroll (tables/diagrams in their own overflow-x:auto box).
  Page complete at rest (nothing hidden behind scroll triggers).
- Design it as a real page with a deliberate identity that matches your
  design direction (type pairing, palette, layout). Avoid the generic
  AI look (cream + serif + terracotta, Inter/Space Grotesk, emoji headers,
  purple gradients, everything centred, rounded cards everywhere).
- Content the maker needs, in this rough order:
  1. Name, one-line pitch, hero drawing (front elevation in the 335 opening
     with bottles drawn at real diameters).
  2. Concept and why it belongs to your direction.
  3. Views: front, side/section showing the two support points vs bottle
     centre of gravity, cell detail with the clear diameter and flare,
     exploded module/joint diagram.
  4. Bottle compatibility table (Bordeaux / Burgundy / Champagne / Alsace /
     magnum - fits / tight / no) and capacity.
  5. Module and plate plan: list every printed part, its size, orientation on
     the bed, count, which plate, est. grams and hours (use the brief's rates),
     totals.
  6. Joints and tolerances, with the tolerance coupon.
  7. Filament recommendation (primary + alternative), colours, and print
     settings (nozzle, layer, walls, infill, plate, temps, drying, brim).
  8. Assembly steps and how it is retained in the opening.
  9. Parameter table from the build script (name, default, what it drives).
  10. Risks and open questions (depth unknown, creep, fit coupon first).
- Keep prose tight. Numbers in tables.

## Deliverable C - design note
docs/wine-rack/<slug>-design.md: a 1-2 page markdown note with the parameter
table, module list, joint spec, filament choice, and decisions with reasons.

## Report back
Reply with: design name, 5-line pitch, the three file paths, the bundled
script path, the preflight exit code (and findings if not 0), capacity,
total grams/hours, filament pick, and the top 3 risks.
