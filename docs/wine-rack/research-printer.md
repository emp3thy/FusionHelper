# Printer constraints: Bambu Lab H2D / H2C for a 335 mm wine rack

Research date: 2026-10-03. Official bambulab.com spec pages and wiki.bambulab.com returned 403/402 to the fetch tool, so official numbers are taken from retailer pages that mirror the Bambu spec sheet (Core Electronics, 3DPros, B&H), the official forum reveal thread, and independent reviews (Tom's Hardware, VoxelMatters, Fauxhammer). Where sources disagree or are silent, that is called out explicitly.

---

## 1. Bambu Lab H2D

### 1.1 Spec table

| Item | Value | Source |
|---|---|---|
| Build volume, single-nozzle mode | **325 x 320 x 325 mm** (X x Y x Z) | [Core Electronics spec mirror](https://core-electronics.com.au/bambu-lab-h2d-3d-printer-machine-only.html), [PB Tech](https://www.pbtech.co.nz/product/PTRBAM0014/Bambu-Lab-H2D-Build-Size-350-x-320-x-325-mm-Dual-n) |
| Build volume, dual-nozzle mode (overlap zone both nozzles reach) | **300 x 320 x 325 mm** | same |
| "Total" volume (union of both nozzles' reach) | 350 x 320 x 325 mm — only usable if both nozzles carry the *same* filament | [Bambu forum: real printable area](https://forum.bambulab.com/t/the-real-printable-area-of-h2d/191416), [Fauxhammer H2S/H2D/H2C](https://www.fauxhammer.com/reviews/bambu-h2s-vs-h2d-vs-h2c-review-why-spending-more-can-actually-get-you-less/) |
| Nozzle reach detail | Left nozzle cannot reach the last ~25 mm on the right; right nozzle cannot reach the last ~25 mm on the left | Fauxhammer |
| Max print height | 325 mm | spec mirrors |
| Heatbed | 120 °C max; ships with **Textured PEI plate** (gold). Bambu Studio lists only Textured PEI and Smooth PEI for H2D; Cool Plate / SuperTack are not listed for H2D | [Core Electronics](https://core-electronics.com.au/bambu-lab-h2d-3d-printer-machine-only.html), [forum: what plate comes with H2D](https://forum.bambulab.com/t/what-build-plate-comes-w-h2d/158830), [forum: two plate types](https://forum.bambulab.com/t/why-does-my-h2d-only-show-two-possible-build-plate-types/172971) |
| Chamber | **Actively heated, up to 65 °C**; heater does not engage below a 40 °C setpoint | Core Electronics; [forum chamber-temp thread](https://forum.bambulab.com/t/desired-chamber-temperature/147004) |
| Hotend max temp | 350 °C | spec mirrors |
| Nozzle sizes | 0.2 (stainless), 0.4 / 0.6 / 0.8 (hardened steel); 0.4 ships. High-Flow variants in 0.4 / 0.6 / 0.8 | [Bambu store H2D hotend](https://us.store.bambulab.com/en/products/bambu-hotend-h2d), [HF hotend](https://us.store.bambulab.com/collections/bambu-hotends/products/bambu-high-flow-hotend-h2d) |
| Max toolhead speed / accel | 1000 mm/s, 20 000 mm/s² | [H2D Pro spec PDF](https://m3.tuc.gr/media/xgxnc4i3/τεχνικο-φυλλαδιο-bambu-lab-h2d-pro.pdf), [3DWithUs](https://3dwithus.com/?p=34092) |
| Max volumetric flow (standard hotend 0.4) | 40 mm³/s headline; Bambu profile caps: PLA Basic 24, PLA Matte 28, PETG HF 24 mm³/s | [Bambu store hotend page](https://us.store.bambulab.com/en/products/bambu-hotend-h2d) |
| Max volumetric flow (High-Flow hotend) | 65 mm³/s headline; profile caps 0.4 HF: PLA Basic 40, PLA Matte 48, PETG HF 32; 0.6 HF and 0.8 HF: 40 mm³/s | [Bambu store HF hotend](https://us.store.bambulab.com/collections/bambu-hotends/products/bambu-high-flow-hotend-h2d) |
| AMS compatibility | AMS 2 Pro and AMS HT (and legacy AMS); up to 4 x AMS 2 Pro + 8 x AMS HT + external = 25 slots | [Memory Express listing](https://www.memoryexpress.com/Products/MX00133664), [Additive-X](https://www.additive-x.com/shop/bambu-lab-h2d-ams-combo-3d-printer.html) |
| External size / weight | 492 x 514 x 626 mm, ~31 kg | Core Electronics |
| Variants | H2D Laser Full Combo (10 W / 40 W laser); H2D Pro (2026) and X2D exist with the same build volume | [Bambu store H2D Pro](https://uk.store.bambulab.com/products/h2d-pro) |

### 1.2 Practical usable area (the numbers that matter for a 335 mm part)

- A front strip x 18-240 mm, y 0-15 mm is the **extrusion-calibration / purge-line region**. Bambu Studio's arrange has an "avoid extrusion calibration region" option; objects can still be placed there but the first-layer purge line will be drawn under them, so budget a few mm margin at the front for critical parts ([printago arrange flag docs](https://printago.io/slicer-cli/avoid-extrusion-cali-region), [Bambu wiki auto-arranging](https://wiki.bambulab.com/en/software/bambu-studio/auto-arranging)).
- Multi-colour prints need a **prime tower** on the plate (not required for single colour); one forum user computed ~290 x 280 mm effective area for a worst-case multi-material job ([forum](https://forum.bambulab.com/t/the-real-printable-area-of-h2d/191416)).
- Brims/skirts eat 3-8 mm per side.

### 1.3 Can a 335 mm part be printed in one piece?

**Axis-aligned: no.** 335 > 325 (single nozzle X), 335 > 320 (Y), 335 > 325 (Z). The largest axis-aligned square is **320 x 320 mm**; the largest square at *any* rotation is also 320 mm (rotating a square only increases its bounding box), so a 335 x 335 mm flat panel cannot be printed in one piece on either machine.

**Diagonally: yes, for bars/rails up to ~120 mm wide.** Computed by sweeping the rotation angle for a rectangle of length L and width w inside the bed rectangle (constraint: L·cosθ + w·sinθ ≤ X and L·sinθ + w·cosθ ≤ Y):

| Bed mode | Bed (X x Y) | Diagonal | Max width of a 335 mm bar | Max width of a 345 mm bar |
|---|---|---|---|---|
| H2D single-nozzle | 325 x 320 | 456 mm | **~121 mm** | ~111 mm |
| H2D dual-nozzle overlap | 300 x 320 | 439 mm | ~104 mm | ~94 mm |
| H2C right (Vortek) nozzle | ~305 x 320 | 442 mm | ~107 mm | ~97 mm |

Max bar length vs width, H2D single-nozzle bed (325 x 320):

| Bar width | 20 mm | 40 mm | 60 mm | 80 mm | 100 mm | 120 mm | 150 mm |
|---|---|---|---|---|---|---|---|
| Max length | 436 | 416 | 396 | 376 | 356 | 336 | 325 (axis-aligned) |

Subtract ~10 mm from these for brim/skirt and the front calibration strip: **design rule: a 335 mm rail should be ≤ ~110 mm wide to print diagonally on the H2D in single-nozzle mode, ≤ ~95 mm in dual-nozzle mode.** Diagonal placement puts the long axis at ~45° to X/Y; Bambu Studio auto-arrange only tries 0/45/90/135°, so rotate manually and verify in the plate view. Long diagonal flat parts also sit on the least-flat region of the bed (users report H2D bed-temperature non-uniformity at the edges, [forum](https://forum.bambulab.com/t/what-to-do-about-the-h2d-heated-bed-temperature-uniformity-problem/156593?page=18)), so use a brim.

**Tall orientation: no.** Z is 325 mm; a 335 mm upright cannot be printed standing. A 320 mm upright is the practical limit.

---

## 2. Bambu Lab H2C

### 2.1 What it is

- **Confirmed real.** Announced **18 Nov 2025** via the official forum reveal; UK shipping "around 04 Dec 2025"; US MSRP **$2 399** (H2C AMS Combo; ~$400 more than H2D). Reviews published Dec 2025 - Apr 2026 ([official reveal thread](https://forum.bambulab.com/t/bambu-h2c-the-full-reveal-is-here/209312), [Tom's Hardware review](https://www.tomshardware.com/3d-printing/bambu-lab-h2c-review), [VoxelMatters review](https://www.voxelmatters.com/voxelmatters-review-bambu-labs-h2c-is-possibly-the-coolest-desktop-3d-printer-ever/), [Bambu store](https://us.store.bambulab.com/products/h2c)).
- **Vortek Hotend Change System**: same H2 chassis as H2D, but the right-hand position on the carriage is a hotend swapper fed from a **rack of up to 6 induction-heated hotends** plus **1 fixed left nozzle** = 7 nozzles. Only the hotend is swapped (not a whole toolhead), so the build volume loss is small. Induction heating brings a swapped nozzle to PLA temperature in **~8 s**. Up to **24 materials** in one print via parallel AMS units (4 x AMS 2 Pro or 8 x AMS HT) ([VoxelMatters](https://www.voxelmatters.com/voxelmatters-review-bambu-labs-h2c-is-possibly-the-coolest-desktop-3d-printer-ever/), [3DPros](https://3dpros.com/printers/bambu-lab-h2c), [Gigaparts comparison](https://www.gigaparts.com/open-box-bambu-lab-h2c-ams-combo-3d-printer.html)).
- Tom's Hardware's verdict: "saves plastic ... but it's not quite a tool changer" — colour changes are about twice as fast as an AMS purge but slower than a true multi-toolhead changer.

### 2.2 Spec table

| Item | H2C | H2D | Source |
|---|---|---|---|
| Total build volume | **330 x 320 x 325 mm** | 350 x 320 x 325 | [Bambu store](https://us.store.bambulab.com/products/h2c), [Core Electronics H2C](https://core-electronics.com.au/bambu-lab-h2c-ams-combo.html) |
| Left (fixed) nozzle reach | ~325 mm wide (same as H2D single nozzle) | 325 | Fauxhammer |
| Right (Vortek) nozzle reach | **~305 mm** wide (loses ~25 mm on left + the rack costs it reach on the right) | 325 | Fauxhammer |
| Dual-nozzle overlap | **~300 x 320 x 325 mm** | 300 x 320 x 325 | Tom's Hardware, Fauxhammer |
| Max Z | 325 mm | 325 mm | spec mirrors |
| Chamber | 65 °C active, auto venting | 65 °C active | 3DPros, Core Electronics |
| Bed / plate | 120 °C; Textured PEI; a "SuperTack ProPlate H2C" accessory exists | 120 °C | 3DPros, [Spool3D](https://spool3d.ca/bambu-lab-supertack-proplate-h2c/) |
| Nozzle sizes (Vortek induction hotends) | 0.2 SS; 0.4 / 0.6 / 0.8 HS, standard and high-flow. Profile caps: 0.2 = 2, 0.4 std 25, 0.6 std 30, 0.8 std 30, HF 0.4/0.6/0.8 = 40 mm³/s. **Mixed nozzle diameters in one job not currently supported** (0.4 std + 0.4 HF is OK) | 0.2/0.4/0.6/0.8 | [West3D listing](https://west3d.com/products/bambu-h2-and-p2-series-high-flow-hotend-nozzle-standard-and-high-flow-various-sizes-and-models-oem-bambu-lab-hot-end-copy), reveal thread |
| Speed / accel | 1000 mm/s, 20 000 mm/s² | same | 3DPros |
| Footprint | 492 x 514 x 626 mm (identical to H2D) | same | 3DPros |

### 2.3 Relevance to large flat or tall parts

- **Single-colour large part on the left nozzle: identical to H2D** (325 x 320 x 325). No penalty.
- **Anything that must use a Vortek (right) hotend** has ~305 mm of X instead of 325 mm. A 335 mm diagonal bar on the right nozzle is limited to ~107 mm width (vs ~121 mm on the left nozzle).
- **Multi-colour large part**: all colours that go through the Vortek rack are confined to the ~300 x 320 overlap zone (same as H2D dual-nozzle mode), so a diagonal 335 mm rail with a second colour must be ≤ ~95-100 mm wide.
- Z is the same 325 mm, so tall-part limits are unchanged.
- **Uncertainty note**: the 305 mm right-nozzle figure is from one independent review (Fauxhammer); Bambu's own pages quote only the 330 total and (per Tom's Hardware) 300 for dual. Treat 300 x 320 as the safe multi-colour design envelope on both machines.

---

## 3. Large-part best practices on H2D / H2C

### 3.1 Warping mitigation

| Material | Plate | Bed temp | Chamber | Notes |
|---|---|---|---|---|
| PLA | Textured PEI (ships with printer), clean with dish soap + warm water, scrub the texture valleys | ~55-65 °C (Bambu PLA on textured PEI: 65 °C) | **Do not heat**. Open door / lift glass top, exhaust on, so the chamber stays cool and avoids heat creep on multi-hour prints | AUX fan can warp medium/large PLA parts: turn it down/off in the filament profile for big footprints ([forum](https://forum.bambulab.com/t/h2d-layer-problem-beginner/192218)) |
| PETG / PETG-HF | Textured PEI; thin glue-stick layer as *release agent* (PETG over-bonds to PEI) | 70-80 °C | Door closed is fine; chamber heater off | Minimal part cooling; H2D PETG profiles improved in Studio 2.1.0 (retraction for 0.4/0.6/0.8) ([forum](https://forum.bambulab.com/t/bambulab-h2d-severe-petg-printing-issues/172331)); corner lift on large flat PETG-HF is a known complaint — use 5-8 mm brim and lower aux fan ([forum](https://forum.bambulab.com/t/large-flat-print-in-petg-hf-getting-slight-warping-at-the-corners/157833)) |
| ABS / ASA | Textured PEI or Engineering Plate; glue dab on corners | 90-100 °C | **Chamber 50-65 °C** — this is what the H2 chamber heater is for | Siraya Tech large-format ABS guide on H2D: stable chamber "dramatically reduced warping" on long prints ([Siraya Tech](https://siraya.tech/blogs/news/the-perfect-match-conquering-large-scale-abs-3d-printing-with-bambu-labs-h2d-and-siraya-techs-fibreheart-abs-ht-hf)) |

General warping rules from the forum/blog consensus ([3DPrintingSpace warping guide](https://3dprintingspace.com/t/how-to-stop-3d-print-warping-and-lifting-corners-pla-petg-and-abs-fixes/10425)):
- **Brim is the single most effective anti-warp tool**: 5 mm brim, and reduce brim-object gap (0.05-0.1 mm) rather than widening beyond 5-8 mm.
- Avoid large solid first layers with sharp corners; add 2-3 mm radii or small "mouse ears" at corners.
- For a 335 x 335 footprint of PLA, the bigger threat is heat-creep/clogging from a warm chamber over 20+ hours, not warping; keep the chamber ventilated.

### 3.2 First-layer tips for big footprints
- Wash the plate; do not rely on IPA alone for textured PEI.
- Keep the H2D's automatic bed-levelling and flow-dynamics calibration enabled; a 15 mm front strip is used for the calibration lines.
- First layer height defaults to 50 % of nozzle diameter (0.2 mm for 0.4; 0.3 mm for 0.6) ([Bambu wiki layer height](https://wiki.bambulab.com/en/software/bambu-studio/layer-height)).
- Elephant-foot compensation: Bambu's P1S/X1 0.2 mm profile default is **0.15 mm**; typical tuning range 0.1-0.2 mm; use a lower bed temp (-5 to -10 °C) if the foot persists ([Bambu wiki](https://wiki.bambulab.com/en/software/bambu-studio/parameter/elephant-foot), [forum](https://forum.bambulab.com/t/elephant-foot-even-with-0-25mm-compensation/149836)).
- Prefer a **0.5-1.0 mm 45° chamfer on bottom edges** over a fillet: a chamfer removes the elephant-foot flare and prints cleanly; a bottom fillet creates a near-horizontal first-layer overhang that prints badly.

### 3.3 Layer heights and nozzles for large decorative parts

| Nozzle | Studio layer range | Suggested for a wine rack | Why |
|---|---|---|---|
| 0.4 std | 0.08-0.28 mm | 0.2 mm (0.16 for visible curved surfaces) | best surface finish; slowest |
| 0.4 HF | 0.08-0.28 mm | 0.2-0.24 mm | ~1.6x flow of std for the same finish |
| 0.6 std / HF | up to ~0.42-0.48 mm (80 % of diameter) | **0.3 mm** (0.36 with HF) | 1.5x extrusion width -> fewer perimeters for the same wall; strong, fast; visibly coarser layer lines on sloped surfaces |
| 0.8 | up to ~0.56 mm | 0.4 mm | structural furniture only |

Forum consensus: switching to 0.6 **without** raising layer height saves little because the printer is already flow-limited; the saving comes from 0.3+ mm layers and fewer walls ([forum .4 vs .6](https://forum.bambulab.com/t/4-vs-6-nozzle/31179), [forum confused over nozzle size](https://forum.bambulab.com/t/confused-over-nozzle-size-print-time/83455)).

### 3.4 Bambu Studio features for a multi-part assembly
- **Cut tool** ([Bambu wiki](https://wiki.bambulab.com/en/software/bambu-studio/cut-tool), [PDF](https://cdn.shopify.com/s/files/1/0224/5205/files/Cut_Tool.pdf)): planar cut at any angle/position; **connectors**: Plug, Dowel, Snap, with tolerance (common starting value 0.1 mm; many users use 0.2 mm) and X-Y hole compensation; **Dovetail mode** adds a mortise/tenon on the cut face with Depth, Width, Flap angle, Groove angle and Tolerance. Limitation: **one dovetail per cut** ([forum request](https://forum.bambulab.com/t/dovetails-in-bambu-studio/123308), [connectors thread](https://forum.bambulab.com/t/don-t-know-how-to-setup-connectors-in-bambu-studio/35745)). For a furniture-grade rack, model joints in CAD rather than relying on the slicer cut.
- **Plates management** ([wiki](https://wiki.bambulab.com/en/software/bambu-studio/plates_management)): drag objects between plates; each plate slices/prints as its own job; per-plate arrange icon.
- **Auto-arrange** ([wiki](https://wiki.bambulab.com/en/software/bambu-studio/auto-arranging)): libnest2d packing, spacing parameter, optional auto-rotate (0/45/90/135° only), "avoid extrusion calibration region", "allow multiple materials on same plate". Objects that don't fit spill onto new plates.
- Dual-nozzle filament grouping ([wiki](https://wiki.bambulab.com/en/software/bambu-studio/manual/dual-nozzles-slicing-filament-grouping)): set AMS-to-nozzle mapping, sync, and Studio groups filaments to minimise flushing.

---

## 4. Multi-colour / multi-material options

| Option | Hardware | Waste | Time cost | Best use for a rack |
|---|---|---|---|---|
| **H2D two colours, one per nozzle** | 2 filaments, external spools or AMS mapped one per nozzle | **Near-zero purge** — only a small prime tower to re-pressurise the idle nozzle ([Fauxhammer](https://www.fauxhammer.com/reviews/bambu-h2s-vs-h2d-vs-h2c-review-why-spending-more-can-actually-get-you-less/), [wiki filament grouping](https://wiki.bambulab.com/en/software/bambu-studio/manual/dual-nozzles-slicing-filament-grouping)) | Nozzle switch takes seconds; the big cost is that the part must sit in the **300 x 320 overlap zone** and the prime tower takes plate space | Two-tone accents (e.g. contrasting end-caps, inlaid lettering) with negligible waste |
| H2D 3+ colours | AMS 2 Pro / AMS HT feeding each nozzle | Normal AMS purge ("poop") for the third+ colour; Studio groups colours across the two nozzles to minimise it | Each AMS change ~1-2 min + purge; many changes per layer on a 335 mm part can double the print time | Avoid on a big rack unless the extra colours are confined to a few layers |
| **H2C Vortek** | 1 fixed + up to 6 swappable hotends; up to 24 slots via AMS | **Zero purge on hotend swaps** (each hotend keeps its own colour); "up to 58 %" less waste than single-nozzle AMS per VoxelMatters, "up to 95 %" in retailer copy; initial load purge still happens. Colours beyond 7 fall back to AMS purging | ~8 s induction heat + a few seconds mechanical swap; Tom's Hardware: ~2x faster than AMS, slower than a true toolchanger | Up to 7 colours with little waste; all Vortek colours confined to ~300 x 320 |
| AMS 2 Pro | 4 slots, heated/dried to 65 °C, RFID | n/a | n/a | Standard supply; needed for auto spool swap on 2 kg jobs (set backup spools of the same colour) |
| AMS HT | 1 slot, dries to 85 °C, for high-temp / engineering filaments | n/a | n/a | Not needed for PLA/PETG decor |
| Filament Track Switch | distribution module routing AMS to either nozzle | — | — | Future H2D firmware feature, not yet shipping for H2D ([3dstisk listing](https://3dstisk.com/produkt/bambu-lab-filament-track-switch/)) |

Takeaway for aesthetics: **two-colour designs are "free" on both machines** (H2D: one colour per nozzle; H2C: fixed + one Vortek hotend). Three to seven colours are cheap only on the H2C. Any design relying on a second colour loses 25 mm of X (300 mm max in the overlap zone).

---

## 5. Printability rules of thumb (designer must respect)

| Rule | Value | Notes / source |
|---|---|---|
| Max unsupported overhang | **45° from vertical** safe for PLA and PETG; PLA can do ~55-60° with good cooling, PETG gets ugly past ~50° | Bambu Studio's auto-support threshold default is 30° (angle to horizontal, i.e. supports when the face is flatter than 30°); [Bambu wiki overhang](https://wiki.bambulab.com/en/filament-acc/filament/print-quality/overhang), [SelfCAD 45° rule](https://www.selfcad.com/blog/what-is-the-45-degree-rule-in-3d-printing-a-complete-guide) |
| Max clean bridge | **≤ 30 mm** for a crisp underside; up to ~50-60 mm acceptable where the underside is hidden; longer needs supports or a chamfer/arch | [printpal design guide](https://printpal.io/docs/3d-printing-design-guide) |
| Min wall thickness (0.4 nozzle) | 0.8 mm cosmetic (2 walls), **1.6 mm default**, **2.4-3.2 mm load-bearing** (6-8 walls); for 0.6 nozzle use multiples of ~0.6 mm: 1.8 / 2.4 / 3.0 mm | printpal |
| Bottle-shelf structural walls for a wine rack | 3-4 mm walls, 4-5 perimeters, 20-30 % gyroid/grid infill; bottle load ~1.5 kg each | design judgement from the wall rule above |
| Bed-side edges | **Chamfer 0.5-1 mm x 45°**, not a fillet; a bottom fillet is a shallow first-layer overhang | see 3.2 |
| Elephant-foot compensation | 0.15 mm Bambu default (0.2 mm profile); tune 0.1-0.2; clearance-critical holes near the bed need +0.1-0.2 mm extra | [Bambu wiki](https://wiki.bambulab.com/en/software/bambu-studio/parameter/elephant-foot) |
| Round holes | print **~0.3-0.5 mm undersize**; design vertical holes +0.4 mm as first estimate; square holes are better | [3DPrinterly shrinkage](https://3dprinterly.com/pla-abs-petg-shrinkage-compensation-in-3d-printing/), [Ultimaker thread](https://community.ultimaker.com/topic/21552-dimensional-accuracy-problem-with-holes/) |
| Shrinkage | PLA ~0.2-0.3 % (good brands); PETG ~0.2-0.3 % (use 0.3 % for parts > 200 mm); over 335 mm that is ~0.7-1.0 mm total | 3DPrinterly; [Manufacturing Technology 2026 PLA/PETG study](https://mt.ujep.cz/artkey/mft-202602-0008_3d-printing-8211-dimensional-accuracy-and-stability-of-pla-and-petg-prints-using-the-fdm-technology.php) |
| Fit clearances, Bambu-class printers (per side, XY) | **Press/interference**: 0 to +0.05 mm; **push-fit / snap**: 0.05-0.10 mm; **slip / sliding**: 0.20 mm; **loose / rotating**: 0.30-0.50 mm. H2D Pro guide suggests 0 / 0.1 / 0.15 / 0.2 mm test steps | printpal; [MakerWorld tolerance test (H2D)](https://makerworld.com/models/2236614), [MakerWorld clearance test](https://makerworld.com/models/2330729) |
| Sliding dovetail / rail joints | **0.20-0.30 mm per side**; below 0.2 mm layer ridges act as interference; add **1-2° taper** along the slide so it locks at the end; dovetail flank angle 10-15° (Studio default is adjustable) | [Siraya Tech joints guide](https://siraya.tech/blogs/news/3d-print-joints), [Markforged joinery](https://markforged.com/blog/joinery-onyx), [Qidi interlocking guide](https://qidi3d.com/en-br/blogs/news/how-to-3d-print-interlocking-parts-and-assemblies) |
| Joining parts bigger than the bed | Put joints where loads are compressive; orient dovetails so the slide direction is along layers (not pulling layers apart); use dowels/plugs (Studio connectors, 0.1-0.2 mm tolerance) for alignment plus glue (CA or PETG-compatible epoxy); stagger joints between layers of the rack so no single plane is a hinge; calibrate with a 20 mm test coupon before printing the 2 kg parts | Studio cut tool wiki; design judgement |
| Z accuracy | layer-quantised: make mating heights multiples of layer height (0.2 or 0.3 mm) | general |

---

## 6. Print-time and material estimates (335 x 335 footprint rack, 1.5-2 kg)

Method: volume = mass / 1.24 g/cm³ (PLA) → 1.21-1.61 million mm³. Real average flow on large parts is ~50-65 % of the profile cap (outer walls, first layer, accel/decel, travel, bridging). Profile caps from the Bambu store pages (section 1.1). These are estimates, not measurements; Bambu Studio's slice-time estimate is usually within ±10 % on H2D.

| Setup | Profile cap (PLA Basic) | Assumed real average | 1.5 kg | 2.0 kg |
|---|---|---|---|---|
| 0.4 std nozzle, 0.2 mm layers | 24 mm³/s | 12-15 mm³/s | **22-28 h** | **30-37 h** |
| 0.4 High-Flow, 0.2-0.24 mm | 40 mm³/s | 18-22 mm³/s | 15-19 h | 20-25 h |
| 0.6 std nozzle, 0.3 mm layers | 30 mm³/s | 18-24 mm³/s | **14-19 h** | **19-25 h** |
| 0.6 High-Flow, 0.36 mm layers | 40 mm³/s | 24-30 mm³/s | 11-14 h | 15-19 h |

Cross-checks: a forum user's 11 h (0.4/0.2) part dropped to 6 h at 0.6/0.3 with fewer walls (~45 % saving) ([forum](https://forum.bambulab.com/t/4-vs-6-nozzle/31179)); a 550 % cube sliced at 0.4/0.2 = 8 h 09 vs 0.6/0.3 = 9 h 13 (no gain) vs 0.6/0.42 = 7 h 47 — i.e. you must raise layer height to benefit ([forum](https://forum.bambulab.com/t/confused-over-nozzle-size-print-time/83455)). Retailer copy for a third-party 0.6 HF nozzle claims a full 1 kg spool in 4 h 27 on an H2D at max draft settings — treat as an upper bound, not a decorative-quality figure.

Material: 1.5-2 kg = **2 x 1 kg spools** (AMS 2 Pro backup-spool mapping needed for a single long job), plus **5-10 %** for brims, prime tower and purge (two-colour dual-nozzle), or **15-30 %** extra if a third colour is purged through the AMS. Split across plates, each ≤ 325 x 320 part of ~0.4-0.7 kg is a 6-12 h plate at 0.6/0.3 — four to six plates total is a realistic plan.

---

## Sources

Official / Bambu:
- https://bambulab.com/en-us/h2d/specs (403 to fetch tool; mirrored by retailers below)
- https://bambulab.com/en-us/h2c/specs (403)
- https://us.store.bambulab.com/products/h2c
- https://us.store.bambulab.com/en/products/bambu-hotend-h2d
- https://us.store.bambulab.com/collections/bambu-hotends/products/bambu-high-flow-hotend-h2d
- https://uk.store.bambulab.com/products/h2d-pro
- https://forum.bambulab.com/t/bambu-h2c-the-full-reveal-is-here/209312
- https://wiki.bambulab.com/en/software/bambu-studio/cut-tool and https://cdn.shopify.com/s/files/1/0224/5205/files/Cut_Tool.pdf
- https://wiki.bambulab.com/en/software/bambu-studio/auto-arranging
- https://wiki.bambulab.com/en/software/bambu-studio/plates_management
- https://wiki.bambulab.com/en/software/bambu-studio/manual/dual-nozzles-slicing-filament-grouping
- https://wiki.bambulab.com/en/software/bambu-studio/parameter/elephant-foot
- https://wiki.bambulab.com/en/software/bambu-studio/layer-height
- https://wiki.bambulab.com/en/filament-acc/filament/print-quality/overhang

Spec mirrors / retailers:
- https://core-electronics.com.au/bambu-lab-h2d-3d-printer-machine-only.html
- https://core-electronics.com.au/bambu-lab-h2c-ams-combo.html
- https://www.pbtech.co.nz/product/PTRBAM0014/Bambu-Lab-H2D-Build-Size-350-x-320-x-325-mm-Dual-n
- https://3dpros.com/printers/bambu-lab-h2c
- https://simplyprint.io/compatibility/bambu-lab-h2c
- https://www.gigaparts.com/open-box-bambu-lab-h2c-ams-combo-3d-printer.html
- https://west3d.com/products/bambu-h2-and-p2-series-high-flow-hotend-nozzle-standard-and-high-flow-various-sizes-and-models-oem-bambu-lab-hot-end-copy
- https://www.memoryexpress.com/Products/MX00133664
- https://m3.tuc.gr/media/xgxnc4i3/τεχνικο-φυλλαδιο-bambu-lab-h2d-pro.pdf
- https://3dstisk.com/produkt/bambu-lab-filament-track-switch/
- https://spool3d.ca/bambu-lab-supertack-proplate-h2c/

Reviews:
- https://www.tomshardware.com/3d-printing/bambu-lab-h2c-review
- https://www.voxelmatters.com/voxelmatters-review-bambu-labs-h2c-is-possibly-the-coolest-desktop-3d-printer-ever/
- https://www.fauxhammer.com/reviews/bambu-h2s-vs-h2d-vs-h2c-review-why-spending-more-can-actually-get-you-less/
- https://makers101.com/bambu-lab-h2c/
- https://3dwithus.com/?p=34092
- https://www.hackster.io/news/the-maker-s-toolbox-bambu-lab-h2c-3d-printer-review-8d2e610d5b5f

Community threads (Bambu forum):
- https://forum.bambulab.com/t/the-real-printable-area-of-h2d/191416
- https://forum.bambulab.com/t/why-does-my-h2d-only-show-two-possible-build-plate-types/172971
- https://forum.bambulab.com/t/what-build-plate-comes-w-h2d/158830
- https://forum.bambulab.com/t/desired-chamber-temperature/147004
- https://forum.bambulab.com/t/h2d-helps-with-fan-glass-etc-adjustments-for-pla-and-petg/191694
- https://forum.bambulab.com/t/h2d-layer-problem-beginner/192218
- https://forum.bambulab.com/t/large-flat-print-in-petg-hf-getting-slight-warping-at-the-corners/157833
- https://forum.bambulab.com/t/bambulab-h2d-severe-petg-printing-issues/172331
- https://forum.bambulab.com/t/what-to-do-about-the-h2d-heated-bed-temperature-uniformity-problem/156593?page=18
- https://forum.bambulab.com/t/elephant-foot-even-with-0-25mm-compensation/149836
- https://forum.bambulab.com/t/dovetails-in-bambu-studio/123308
- https://forum.bambulab.com/t/don-t-know-how-to-setup-connectors-in-bambu-studio/35745
- https://forum.bambulab.com/t/4-vs-6-nozzle/31179
- https://forum.bambulab.com/t/confused-over-nozzle-size-print-time/83455
- https://forum.bambulab.com/t/h2d-testing-max-volumetric-flow/171549
- https://forum.bambulab.com/t/improving-dimensional-accuracy-on-bambu-lab-h2d-with-petg-hf/159931

Design rules:
- https://printpal.io/docs/3d-printing-design-guide
- https://printago.io/slicer-cli/avoid-extrusion-cali-region
- https://www.selfcad.com/blog/what-is-the-45-degree-rule-in-3d-printing-a-complete-guide
- https://siraya.tech/blogs/news/3d-print-joints
- https://markforged.com/blog/joinery-onyx
- https://qidi3d.com/en-br/blogs/news/how-to-3d-print-interlocking-parts-and-assemblies
- https://3dprinterly.com/pla-abs-petg-shrinkage-compensation-in-3d-printing/
- https://community.ultimaker.com/topic/21552-dimensional-accuracy-problem-with-holes/
- https://mt.ujep.cz/artkey/mft-202602-0008_3d-printing-8211-dimensional-accuracy-and-stability-of-pla-and-petg-prints-using-the-fdm-technology.php
- https://makerworld.com/models/2236614 and https://makerworld.com/models/2330729 (tolerance tests)
- https://3dprintingspace.com/t/how-to-stop-3d-print-warping-and-lifting-corners-pla-petg-and-abs-fixes/10425
- https://siraya.tech/blogs/news/the-perfect-match-conquering-large-scale-abs-3d-printing-with-bambu-labs-h2d-and-siraya-techs-fibreheart-abs-ht-hf
