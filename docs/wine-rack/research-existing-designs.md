# 3D-printed wine racks: survey of existing designs, failure modes and design language

Research date: 2026-10-03. Purpose: inform three original designs (unobtrusive / modern / decorative) for a 335 x 335 mm square opening (depth unknown), printed on a Bambu Lab H2D or H2C.

Method note: MakerWorld, Printables, Thingiverse and Medium pages were read directly in a browser (comment threads included). Cults3D, Thangs and commercial sites were only reachable through search snippets, so those entries carry less detail. Reddit threads specifically about printed wine racks failing could not be located by search; the failure-mode evidence below comes from model comment threads, the Bambu forum and material/creep literature.

---

## 0. Hard constraints that fall out of the research

| Constraint | Value | Source |
|---|---|---|
| H2D build volume | 350 x 320 x 325 mm total; **325 x 320 x 325 mm single nozzle**; 300 x 320 x 325 mm dual nozzle | [PB Tech H2D listing](https://www.pbtech.co.nz/product/PTRBAM0014/Bambu-Lab-H2D-Build-Size-350-x-320-x-325-mm-Dual-n), [MatterHackers](https://matterhackers.com/store/l/bambu-lab-h2d-3d-printer) |
| Bed diagonal (single nozzle) | sqrt(325^2 + 320^2) ~ 456 mm; a 335 mm bar fits diagonally with ~60 mm each end to spare | computed |
| Consequence | A 335 mm wide **or** 335 mm tall one-piece frame does not fit in X, Y or Z. Either print rails/bars diagonally, or split the frame into modules with dovetails. Nobody in the survey prints a full-width rack in one piece; all large racks are modular. | survey |
| Full bottle mass | ~1.5 kg (3.3 lb) | [Wine Hive page](https://makerworld.com/en/models/2382813) |
| Bottle diameters | Bordeaux 75-80 mm; Burgundy 85-90 mm; Champagne/Prosecco 88-96+ mm (one user measured Prosecco at 96.5 mm) | [Vigilant storage chart](https://education.vigilantinc.com/wine-bottle-sizes-dimensions-wine-racks), [Infinite Wine Rack comments](https://makerworld.com/en/models/52448-the-infinite-wine-rack) |
| Cell bore that actually works | 76 mm = many complaints; 80-85 mm = "most Bordeaux, some reds don't fit"; **90-93 mm = fits almost everything**; commercial Koziol uses 90 mm openings | Milumi, marcinmiszewski, Hexwine, Wine Hive, ILikon, Koziol (below) |
| Capacity reference for a 33 x 33 cm cube | IKEA KALLAX bottle insert (33 x 33 cm) holds 9 bottles in a 3 x 3 lattice | [IKEA KALLAX insert](https://ikea.com/ca/en/p/kallax-insert-for-bottles-white-80401292) |

Practical arithmetic for 335 mm: a 3 x 3 square grid gives ~111 mm pitch (9 bottles, generous 92 mm bores with ~19 mm of wall/web); a honeycomb 3-2-3 gives 8 bottles with ~105 mm hex pitch; a 4-wide square grid (84 mm pitch) is too tight for anything but Bordeaux.

---

## 1. Survey of popular / best-rated printed wine racks

### Comparison table

Counts are as shown on the page on 2026-10-03 (MakerWorld shows likes / downloads / boosts / prints; the "prints" figure is the most meaningful popularity signal).

| # | Name (designer) | Platform / URL | Structural concept | Capacity per module | Bore / pitch | Modular? Joining | Suggested settings | Print time | Popularity | Notable comments |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | The Infinite Wine Rack (dewgenenny) | [MakerWorld 52448](https://makerworld.com/en/models/52448-the-infinite-wine-rack) | Hex ring pairs (front + back ring per bottle) joined by inside/outside connectors; honeycomb grows in any direction | 1 bottle per ring pair; builds of 74 bottles reported | ~Bordeaux size at 100 %; users scale 106-115 % for Burgundy/Champagne | Yes; press-fit, no glue | PLA 0.2 mm, 2 walls, 15 % | 8.3 h for the standard plate; 3.5 kg PLA for a big build | 433 reviews, ~4.6 k prints, 381 boosts, CC BY-NC-SA | "Super stable / rigid"; WD-40 used to ease assembly; parts cracked slightly when tight on an under-calibrated printer; remixes add side/top caps ([1889733](https://makerworld.com/en/models/1889733)) and a compact triangle/diamond edge set for small cabinets ([2187434](https://makerworld.com/models/2187434)); "a shame it's hidden away" (in-cabinet use common) |
| 2 | Modular Wine Rack "Infinity Cell" (emmemodeling) | [MakerWorld 839990](https://makerworld.com/en/models/839990-modular-wine-rack-infinity-cell) | Sculpted interlocking cradle cells, stack like bricks; no supports | 1 bottle | 750 ml standard; a KALLAX-compatible profile exists | Yes; cells just rest/interlock, no positive lock | 0.2 mm, 2 walls, 8-15 % | 5.1 h per cell; a 110 mm-tall filament-saving variant 5.3 h | 98 reviews, ~2.5 k prints, 97 boosts | Repeated requests for a **locking sleeve or solid base** because cells only sit on each other; one maker modified the bottom row and added top clips; "connecting parts need more defined features"; a 1-spool build is typical |
| 3 | Wine Hive (3DJP) | [MakerWorld 2382813](https://makerworld.com/en/models/2382813) | Big hexagonal compartments (one, two, three, four-cell plates) joined by clip-in adapters; clip-in bottle mounts | 1-4 bottles per plate | Fits up to 90 mm; cell 116 x 100.5 x 130.8 mm, 4 mm perimeters | Yes; very tight clips, test piece included | PLA 0.2 mm, **3 walls + Arachne** (to avoid weak corners), 5 % infill, brim | 4 h 49 min per compartment; 72 h / 990 g full profile | 7 reviews, newer (Feb 2026) | Designer warns PLA/PETG **creep**; insists on at least one horizontal connection per layer, "do not rely on vertical connections"; a user had the corner "dune walls" collapse in PETG and ABS (overhang issue); 3-4 cell plates only print on >300 mm beds |
| 4 | Modular Wine Rack - Tool-Free Snap-Fit (Poldi5965) | [MakerWorld 3028018](https://makerworld.com/en/models/3028018-modular-wine-rack-tool-free-snap-fit-system) | Cradle modules with **conical tongue-and-groove** on every edge; 9 module types (standard, 4 edge, 4 corner) so outer faces are clean | 1 bottle; module 112 x 129 x 200 mm | Standard 750 ml | Yes; slide-in self-aligning, no glue | **PETG** "for long-term rigidity"; 0.2 mm, 2 walls, 15 % | 61 h / 1.6 kg for the 9-plate set | 4 reviews (Jul 2026) | PETG stringing/blobs on the upper slopes; designer's fix list: avoid crossing perimeters, 0.6-1.0 mm retraction, rear/aligned seam, 30-50 % fan, dry filament |
| 5 | Modular Wine Rack (masonkimbrough) | [MakerWorld 1356600](https://makerworld.com/en/models/1356600-modular-wine-rack) | Body pieces with **dovetails**, top/bottom crossbars, pins; built to fit a cabinet above a fridge, assembled inside through lattice gaps | expandable in width, depth, height | Bottles up to ~80-85 mm | Yes; dovetail + pins | PLA 0.2 mm, 2 walls, 15 %; supports on build plate only | 11.9 h / 542 g per plate; ~1.5 kg for pictured rack | 12 reviews, ~450 prints, CC BY-NC-ND | Good example of an **in-cabinet insert**; square spirits bottles fit under 80 mm; assembly video requested |
| 6 | Fridge Wine Rack (Stackable) (coverv) | [MakerWorld 2373181](https://makerworld.com/en/models/2373181-fridge-wine-rack-stackable) | Stackable cradle modules + top module; vertical stacking on a shelf | 1 bottle per module | 75 mm (v2) and 90 mm versions | Yes; corner joints, keyed so they cannot go in backwards (v2) | Clean plate, dry filament | 4.8 h (75 mm), 5.8 h (90 mm) | 162 reviews, ~1.1 k prints, 5.0 rating | v1 joints **broke when forced in backwards**; "disconnect all corners at the same time to avoid breaking joints due to the large lever arm"; a 76.8 mm bottle hit the top plate on entry even though it fit once seated (entry clearance matters); minimal white look praised |
| 7 | Hexwine - Modular Honeycomb Wine Rack Shelf (benjiz) | [MakerWorld 654957](https://makerworld.com/en/models/654957-hexwine-modular-honeycomb-wine-rack-shelf) | Thin hex plates joined by short connectors; long connectors with locking tabs give lengthwise stability (use >= 1/6 long) | 1 bottle per plate pair | Fits most 750 ml; user widened to 93 mm ID for Prosecco | Yes; press-fit, intentionally very tight | PLA 0.2 mm, **4 walls**, 15 % | 14.1 h / 600 g | 65 reviews, ~1.1 k prints, CC BY-SA | **Rubber mallet / hammer** needed; connectors oversize so hexes "stress and start to separate"; one maker's slots did not fit at all; suggestion that H2D owners get pre-joined blocks of 4 |
| 8 | Modern Wine Rack - 4 & 5 Bottle (marcinmiszewski) | [MakerWorld 2329153](https://makerworld.com/en/models/2329153-modern-wine-rack-4-5-bottle-versions) | One-piece ribbed organic block, round bores; 4-bottle fits 256 mm beds, 5-bottle for larger | 4-5 | 85 mm bore, 130 mm deep | No (not stackable) | 0.28 mm, 2 walls, 18 % adaptive cubic, no supports; PLA/PETG/ASA/matte | 10.6-13.2 h | 35 reviews, ~930 prints, 1.3 k likes | Stable with a single bottle in the top slot; some "standard looking" reds still do not fit 85 mm; A1 bed-adhesion failure on a large flat base; v2 released; ribbed texture hides layer lines |
| 9 | Wine & Glass Rack - wine stand (Milumi3D) | [MakerWorld 2374456](https://makerworld.com/en/models/2374456-wine-glass-rack-wine-stand) | One-piece X-geometry stand, ribbed side panels, 3 bottles + 4 glasses | 3 | **76 x 76 mm slots** | No | 0.28 mm, 2 walls, 10 % | 12.6-14.6 h | 64 reviews, ~1.3 k prints | Many makers: "none of my 750 ml bottles fit"; designer says 256 mm bed forced the 76 mm slot; scale 107 % workaround; PLA holds 3 bottles "without issue" |
| 10 | Stackable Bottle Holder PARAMETRIC (capze.) | [MakerWorld 46590](https://makerworld.com/en/models/46590-stackable-bottle-holder-parametric) | Cross/X cradles that stack, with a clip connector; Fusion 360 parametric file | 1 bottle per cross | Set in parameters | Yes; stacking + connectors | 0.28 mm, 3 walls, 15 % | 2.8-4.2 h per piece | 186 reviews, ~2.1 k prints | Praised for "not collapsing under its own weight"; criticised for **very heavy filament use** ("brought two rolls and a third"); overhangs not clean |
| 11 | Organic Wine & Glass Rack (iluminari3d) | [MakerWorld 2694728](https://makerworld.com/en/models/2694728-organic-wine-glass-rack-4-bottle-stand) | Topology-optimised sculptural stand, split into pieces joined by 20/25 mm square pegs; 506 x 217 x 236 mm raw | 4 + 4 glasses | - | Split for bed; pegs then seams welded with soldering iron/3D pen | PLA or PETG, 0.4 or 0.8 mm nozzle profiles, **tree supports essential, brim mandatory** | long (large) | 49 reviews | Decorative benchmark; warping at base is the designer's stated risk; sanded + painted builds shown |
| 12 | Tilted Modular Wine Rack | [MakerWorld 2251168](https://makerworld.com/en/models/2251168-tilted-modular-wine-rack) | Circle-in-square front/back frames with **double-dovetail connectors**; 8 deg tilt keeps cork wet; back frame has a neck slot that locks the bottle | 1 per cell, any M x N | Regular and large-bottle variants | Yes; dovetails, strict assembly order | Minimal supports (dovetails, label slots) | 2 x 3 rack 29.8 h | new (Jan 2026), 1 review | "No redundant stiffeners, strength from geometry and tight dovetail engagement"; explicit part-count formula; door bumpers as feet |
| 13 | Modular Wine Rack (mhparsons) | [Printables 939239](https://www.printables.com/model/939239-modular-wine-rack) | 9 part types; row pieces joined by **dovetails**, rows nest on pockets; no glue, no hardware, no supports | configurable | Up to 3.62" (92 mm, Champagne) | Yes | PLA 0.2 mm, 2 perimeters, 15 % | multi-day for big racks; "uses a ton of filament" | 586 likes, 7.9 k downloads, 8 makes, CC BY-NC | Author (230 lb) **stood on an assembly**, it held; weakest point "base of the dovetail joints"; one maker's dovetails jammed and **broke on removal** at 30 % infill -> remix with looser tolerance; "perfectly fits a little unused cupboard" |
| 14 | Modular Wine Bottle Post and Bracket System (dbadev) | [Printables 57622](https://www.printables.com/model/57622-modular-wine-bottle-post-and-bracket-system) | Three brackets + 12 dowel-like posts per bottle; brackets interlock with a jigsaw fit; bases for the floor | 1 per unit; built to 100 bottles | - | Yes | PLA, **4-5 perimeters**, 15 % gyroid | fast per part; designed for a print farm | 133 likes, 4 k downloads | Cylindrical posts needed rafts and failed adhesion -> redesigned with a **flat side facing the bottle**; earlier Thingiverse racks "took > 2 days, lots of material" |
| 15 | Modular honeycomb wine rack (ILikon) | [Thingiverse 6619687](https://www.thingiverse.com/thing:6619687) | Rings + half rings joined by H-columns and half-columns | 1 per ring | **90 mm** rings | Yes; tight press-fit, "print a test first" | PLA | - | CC BY-SA | "Designed and printed in PLA 2 years ago and everything is still holding strong" (rare long-term data point) |
| 16 | Wine rack modular stackable (Jacksy71) | [Thingiverse 2804083](https://www.thingiverse.com/thing:2804083) | Angular stackable holder | 12 bottles | 80 mm ID, 200 mm tall | Yes | - | - | - | via search snippet only |
| 17 | Modular Wine Rack (O3D) | [Thingiverse 1494484](https://www.thingiverse.com/thing:1494484) / [Cults O3D](https://cults3d.com/en/3d-model/home/modular-wine-rack-o3d) | Hex modules; "Hex Drawers" extension adds a **Voronoi hex module**, dual modules, wall mounts | 1 per module | - | Yes, stack | - | - | - | one of the few Voronoi-skinned racks; via snippets |
| 18 | Modular Wine Rack (The_Exceptional_Bruce) | [Thingiverse 3641393](https://www.thingiverse.com/thing:3641393) | Modular cells | - | - | Yes | - | - | - | "fits so tight you have to join it with a rubber mallet" (and cited by dbadev as slow/heavy) |
| 19 | Simple modular wine rack / Modular Wavy Wine & Champagne Rack / Wooden Wine Rack No Supports | [Cults tag page](https://cults3d.com/en/tags/wine+rack), [Simple](https://cults3d.com/en/3d-model/home/simple-modular-wine-rack), [Wavy](https://cults3d.com/en/3d-model/home/modular-wavy-wine-champagne-rack-scalable-and-stylish-3d-printable-design), [Wooden](https://cults3d.com/en/3d-model/home/wooden-wine-rack-no-supports) | Two-piece infinitely expandable; stacked wavy levels with spacers; wood-look support-free rack | 2-3 / level-based | - | Yes | - | - | - | Cults3D content only visible via snippets (73 models under the tag) |
| 20 | GustaVino (Gustavo Arguello) | [3DPrint.com article](https://3dprint.com/94688/3d-printed-gustavino-wine-rack/), [Hubs thread](https://www.hubs.com/talk/t/gustavino-the-best-gift-for-wine-lovers/3606) | Gaudi / bone-inspired symmetrical interlocking component; 3 pieces hold 3-4 bottles horizontally, vertically or pyramidal | 3-4 per 3 parts | - | Yes | - | - | paid (33 EUR on Cults) | The reference "organic/pretty" printed rack |
| 21 | Minimalist's wine bottle holder | [Printables 207209](https://www.printables.com/model/207209-minimalists-wine-bottle-holder) | ~5 g spacer that lets bottles stack in a pyramid (2 holders -> 6 bottles) | 3-6 | - | n/a | - | minutes | contest entry | Shows the "almost nothing" end of unobtrusive; relies on bottle-on-bottle stacking |
| 22 | Modular Wall-Mounted Wine Rack | [MakerWorld 480320](https://makerworld.com/en/models/480320) | Single-bottle wall modules with anchors, tool-free add/remove | 1 per module | standard | Yes | PLA or PETG | - | - | Wall-mount reference |
| 23 | Modular Hexagon Spray Can Rack (remix chain) | [MakerWorld 589075](https://makerworld.com/en/models/589075-modular-hexagon-spray-can-rack) | Hex cells joined by printed rods 70-100 mm; originally a wine rack by FreakErn on Thingiverse | - | - | Yes; friction fit | 0.2 mm, 2 walls, 15 % | 38 min per hex | 271 prints, CC BY-NC-SA | Shows the "two hex rings + connecting rods" pattern reused at 75 % scale |
| 24 | Peter Yang prototype write-up | [Medium](https://medium.com/@peter.yang.ux/3d-printed-prototype-modular-wine-rack-405cceacee07) | Hex cells with edge tabs | 1 | - | Yes | 10-15 % infill | 9 h for 2 cells (v1) | - | **Rectangular tabs fell apart; trapezoidal (dovetail) tabs locked**; half-height walls still held a bottle, leading to "two rings + ribs" idea |

### Stackable / cradle vs honeycomb: what the numbers say

- The most-printed racks are the honeycomb ring type (Infinite Wine Rack ~4.6 k prints) and the small per-bottle cradle type (Fridge rack ~1.1 k, Parametric ~2.1 k, Infinity Cell ~2.5 k). Both win because each part prints in 3-8 h and nothing needs supports.
- One-piece sculptural blocks (Modern Wine Rack, Milumi) get high like counts (1.3-2 k) but a lower print ratio, and their comment threads are dominated by **bottle-fit complaints** because they were sized to a 256 mm bed.
- Heavy "overbuilt" designs (Parametric cross, Printables dovetail) attract "uses a ton of filament" complaints; the Printables author explicitly says he left them heavy out of strength anxiety.

---

## 2. Reported failure modes and how remixers fixed them

| Failure mode | Evidence | Fix applied by designer / remixer |
|---|---|---|
| **Creep / sag of PLA under constant load** | Wine Hive designer: "PLA and even PETG can become brittle and creep over time"; Bambu forum: PLA under constant tension "will start to creep"; Qidi guide: PLA racks "begin to sag or bow in the center over 3-6 months", worse in warm kitchens; PLA bracket "snapped after about 2 years", reprinted in PLA+ held; research shows measurable PLA creep well below Tg | Snap-Fit rack is printed in **PETG "for long-term rigidity"**; guides recommend ASA (Tg ~100 C) or ABS-GF for sustained loads; use 4-6 wall loops rather than high infill; keep bottles supported close to the webs so spans are short; ILikon's 90 mm PLA rings "still holding strong after 2 years" shows well-proportioned PLA rings survive if stress is low. Sources: [Wine Hive](https://makerworld.com/en/models/2382813), [Bambu forum spool rack](https://forum.bambulab.com/t/printing-spool-rack-with-pla/60310), [Qidi coffee-rack guide](https://qidi3d.com/blogs/print-lab/3d-printing-coffee-bean-cellar-racks), [Bambu forum "would PETG have worked better"](https://forum.bambulab.com/t/would-petg-have-worked-better/130412), [PLA creep paper](https://arxiv.org/abs/2302.11240v2), [ILikon](https://www.thingiverse.com/thing:6619687) |
| **Press-fit / snap-fit breakage** | Infinite Wine Rack: "two parts cracked slightly" on an uncalibrated printer; Printables dovetail: jammed then **broke when pulled apart**; Hexwine: hexes "stressing and starting to separate", mallet needed; Fridge rack v1: joints broke when forced backwards; Wine Hive: "DO NOT PULL on the compartment, push clips out from inside or you rip the model apart" | Keyed joints that cannot be assembled wrong (Fridge v2); include a **tolerance test piece** (Wine Hive, ILikon); remixers loosen dovetails (prostuff1 remix of 939239); Hexwine author suggests scaling connectors down; conical tongue-and-groove self-aligns (Snap-Fit); add lead-in chamfers ("send the bevelled edge in first") |
| **Layer delamination along bottle axis / corner weakness** | Wine Hive: "3 walls and Arachne strongly suggested, otherwise weak points in the corners"; dbadev: 4-5 perimeters "especially the posts and holes to resist cracking"; CNC Kitchen: vertical coupons reach only ~50 % of flat strength | More perimeters, Arachne, fillets at hex corners; orient so the ring's hoop is in XY (print rings flat, bottle axis = Z) so hoop stress is in-plane. Sources: [Wine Hive](https://makerworld.com/en/models/2382813), [dbadev](https://www.printables.com/model/57622-modular-wine-bottle-post-and-bracket-system), [CNC Kitchen 45 deg](https://cnckitchen.com/blog/stop-printing-flat-the-45-secret-for-stronger-parts) |
| **Warping / adhesion of big flat panels** | Modern Wine Rack on A1 "coming off the bed"; Organic rack: "brim mandatory to prevent warping at the base"; dbadev: cylindrical posts needed rafts and failed | Flat side on the bed, brim/"tesa", chamfer the base, keep panel thickness consistent, or avoid big flat panels entirely (ribs/lattice). Sources: [2329153](https://makerworld.com/en/models/2329153-modern-wine-rack-4-5-bottle-versions), [2694728](https://makerworld.com/en/models/2694728-organic-wine-glass-rack-4-bottle-stand) |
| **Bottles do not fit / cannot enter** | 76 mm slots (Milumi): "none of my bottles fit"; 85 mm (Modern): some reds no; Fridge rack: 76.8 mm bottle "hits the top plate entering, fits once seated"; Infinite Wine Rack scaled 106-115 %; Hexwine widened to 93 mm | Design to **>= 90-93 mm clear bore**, flare the entry, keep the neck-end narrower if you want the bottle located (Tilted rack's neck slot) |
| **Bottles rolling / sliding out** | Tilted rack adds a back-frame neck slot; Wine Hive adds clip-in bottle mounts to centre bottles; the original "rickety" wooden rack lost bottles (dbadev's motivation) | Cradle with two contact lines per bottle, a shallow rear stop or neck slot, or a 5-8 deg rearward tilt |
| **Rack / stack tipping** | Infinity Cell: cells only rest on each other, users want a base and top clips; Wine Hive: "do not rely on only vertical connections", keep at least one horizontal tie per layer; Fridge rack: "does it stay firm with many stacked?" | A continuous base plate or frame, horizontal ties between columns, rubber door-bumper feet (Tilted rack) |
| **Overhang collapse inside cells** | Wine Hive "dune walls" collapsing in PETG/ABS | Keep internal overhangs under ~45-50 deg or print rings flat; lower layer height (Wine Hive) |
| **PETG stringing / seam blobs on sloped faces** | Snap-Fit rack | Avoid crossing perimeters, 0.6-1.0 mm retraction, aligned/rear seam, 30-50 % fan, dry the filament |
| **Excess filament / print time** | Parametric cross: 2-3 rolls for six holders; Printables dovetail "ton of filament"; early Thingiverse racks > 2 days | Thin ring-and-rib architecture (Infinite, Hexwine, Peter Yang) or 110 mm short cells (Infinity Cell filament-saving profile) |

---

## 3. Orientation and splitting strategies that worked

1. **Rings printed flat, bottle axis vertical on the bed.** Every successful honeycomb rack (Infinite Wine Rack, Hexwine, ILikon, FreakErn chain) prints its hex/round rings lying flat, so the hoop that carries the bottle is a continuous XY perimeter loop and the bottle's weight is carried in-plane; the only Z-loaded features are the short connectors. This is also the orientation that needs no supports.
2. **Cradle modules printed on their flat base** (Infinity Cell, Fridge rack, Parametric cross, Snap-Fit) with the bottle running horizontally across the bed. Here the saddle is a stack of layers loaded in bending across the layer lines; designers compensate with 3-4 walls, short spans and thick saddle walls. It works at 1.5 kg per bottle but is the design class that worries about creep and "collapsing under its own weight".
3. **Two rings + rods/ribs instead of a full tube.** The spray-can remix chain (hex ring pairs joined by 70-100 mm printed rods), Peter Yang's observation that half-height walls still held a bottle, and dbadev's brackets + posts all converge on the same material-efficient scheme: front ring, back ring, 3-4 longitudinal members.
4. **One piece vs modules.** Nobody prints a multi-bottle rack in one piece above the 256 mm class; the 5-bottle Modern rack only appeared when 300+ mm beds arrived, and the 506 mm Organic rack ships pre-split with square pegs and a "weld the seam" finish. For 335 mm the realistic options are (a) a bar/rail that is 335 mm long placed **diagonally** on the H2D bed (fits with ~60 mm to spare), or (b) a frame split into 2-3 modules joined by dovetails. Bambu Studio's Cut tool has a **Dovetail mode** (adjustable depth, width, flap/groove angle, tolerance) for exactly this: [Bambu Cut tool PDF](https://cdn.shopify.com/s/files/1/0224/5205/files/Cut_Tool.pdf), [Bambu forum on snapping joints](https://forum.bambulab.com/t/need-help-splitting-a-model-with-a-joint-for-snapping-together/182825).
5. **Dovetails beat tabs; conical beats square.** Peter Yang's rectangular tabs fell apart, trapezoidal ones locked; the Snap-Fit rack's conical tongue-and-groove self-aligns and is the only system with no "mallet" complaints; the Tilted rack uses double dovetails and gets rigidity "entirely from geometry". Print the dovetail with its slide axis vertical on the bed if possible so its flanks are smooth XY perimeters.
6. **Walls, not infill.** Consensus across designers: 3-5 perimeters at 5-15 % infill (Wine Hive 3 walls/5 %; Hexwine 4 walls; dbadev 4-5 perimeters + 15 % gyroid; Qidi guide 4-6 loops). Gyroid is preferred for isotropic strength per gram; cubic/adaptive cubic for speed. Sources: [Clever Creations infill](https://clevercreations.org/what-is-strongest-infill-pattern-cura-prusa/), [All3DP strongest infill](https://all3dp.com/2/strongest-infill-pattern/).
7. **Tilt when a load-path member must cross layers.** CNC Kitchen's test: PLA 63 MPa flat, 31 MPa vertical, 40 MPa at 45 deg; the curve is S-shaped so "a slight tilt won't fix it, aim for at least 45 deg". Useful for a diagonal 335 mm rail: laying it on the bed diagonal keeps its long axis in XY anyway. [CNC Kitchen](https://cnckitchen.com/blog/stop-printing-flat-the-45-secret-for-stronger-parts), [Bambu forum discussion](https://forum.bambulab.com/t/print-orientation-angled-3d-printing-can-make-parts-stronger/224404).
8. **Hollow vs solid ribs.** The ribbed-texture one-piece racks (Modern, Milumi) use 2 walls + low infill and rely on the ribbing both for stiffness and to hide layer lines; the 0.8 mm nozzle profiles on the Organic rack show that thick single-wall ribs print fast on an H2D. None of the surveyed racks uses internal lattice infill as the structure; they all use perimeters.
9. **Material choice.** PLA is universal in the survey and works for years when stress is low (ILikon); PETG is chosen by the designers who think about long-term rigidity (Snap-Fit, Hexwine users); ASA/ABS-GF recommended by guides for warm kitchens. On an H2D (65 C chamber) ASA or PETG-CF is painless, so the creep argument favours PETG/ASA for the load-carrying parts and PLA (matte, wood, silk) only for decorative skins.

---

## 4. Design language inspiration

### (a) Unobtrusive - disappears in a cabinet or alcove

- **In-cabinet modular insert**: masonkimbrough's dovetail rack was literally assembled inside a cabinet through the lattice gaps ([MakerWorld 1356600](https://makerworld.com/en/models/1356600-modular-wine-rack)); mhparsons' rack "perfectly fits a little unused cupboard" ([Printables 939239](https://www.printables.com/model/939239-modular-wine-rack)); the Infinite Wine Rack comment "a shame it's hidden away most of the time" ([52448](https://makerworld.com/en/models/52448-the-infinite-wine-rack)).
- **White minimal cradle in a white fridge**: Fridge Wine Rack ([2373181](https://makerworld.com/en/models/2373181-fridge-wine-rack-stackable)) - clean, matte, low profile, keyed stacking.
- **Near-nothing holders**: Minimalist's wine bottle holder, 5 g per piece, bottles form the structure ([Printables 207209](https://www.printables.com/model/207209-minimalists-wine-bottle-holder)).
- **Commercial references**: IKEA KALLAX bottle insert, a flush 33 x 33 cm 3 x 3 lattice in melamine ([IKEA](https://ikea.com/ca/en/p/kallax-insert-for-bottles-white-80401292)); Vinotemp Epicureanist **peg racks**, pairs of pegs so bottles "float" with almost no visible rack ([Vinotemp peg rack](https://www.chefsupplies.ca/products/vinotemp-epicureanist-modern-3-bottles-peg-racking-ep-peg3s)); IKEA-hack lattice inserts ([ikeahackers](https://ikeahackers.net/2016/12/ikea-kallax-wine-rack-insert.html)).
- Printable interpretation: a flush 3 x 3 (or 3-2-3) lattice of thin X-webs or peg pairs, matte black/white/wood PLA, no visible fasteners, sized to the 335 mm opening with a 2-3 mm perimeter gap; or a peg-pair wall plate that screws to the alcove back so only the bottles show.

### (b) Modern - geometric, parametric, Scandinavian/Bauhaus, hex, monochrome

- **Honeycomb heritage**: Torsten Johansson's bentwood honeycomb wine rack for AB Formtra, Sweden, 1960s, rosewood + beech ([1stdibs](https://www.1stdibs.com/furniture/dining-entertaining/serving-pieces/rosewood-beech-bentwood-wine-rack-torsten-johansson-ab-formtra/id-f_39963412), [Chairish](https://www.chairish.com/product/18597963/rosewood-beech-bentwood-wine-rack-by-torsten-johansson-for-ab-formtra)).
- **WineHive** (John Paulick): a single extruded aluminium cell with slide-in tabs that repeats into an infinite honeycomb; cells 7 x 4.5 x 4 in, matte black/brushed silver ([Coroflot](https://www.coroflot.com/johnpaulick/WineHive®-modular-wine-rack), [WineCellarHQ 20-cell](https://winecellarhq.com/products/winehive-20-cell-modular-wine-rack)). The "one part, repeated" idea is directly printable.
- **Koziol Set-Up / Honeycomb**: 10-bottle recycled thermoplastic honeycomb module, 36.4 x 35.3 x 23 cm, 90 mm openings, 1.4 kg, stackable ([Connox](https://www.connox.com/categories/kitchenware/bottle-racks/wine-rack-set-up.html), [Not A Boring Box](https://notaboringbox.co.uk/products/honeycomb-wine-bottle-rack)). Note the module is almost exactly the 335 mm square.
- **Oliver Bonas Hexagon Gold Wall Wine Rack**: wire hex chain, 5 bottles up to 3.4 in, 55 x 10 x 15 cm ([Oliver Bonas](https://www.oliverbonas.com/homeware/hexagon-gold-wall-wine-rack-252531)); similar countertop hex wire racks ([The Range](https://www.therange.co.uk/cooking-and-dining/kitchen-accessories/kitchen-storage/wine-racks/countertop-hexagon-wine-rack)).
- **Printed**: Hexwine thin plates ([654957](https://makerworld.com/en/models/654957-hexwine-modular-honeycomb-wine-rack-shelf)), Snap-Fit rack with clean edge/corner modules ([3028018](https://makerworld.com/en/models/3028018-modular-wine-rack-tool-free-snap-fit-system)), ribbed monochrome Modern Wine Rack ([2329153](https://makerworld.com/en/models/2329153-modern-wine-rack-4-5-bottle-versions)), Tilted rack's circle-in-square frames ([2251168](https://makerworld.com/en/models/2251168-tilted-modular-wine-rack)), Grasshopper parametric attractor rack (CNC-cut) ([grasshopper3d](https://www.grasshopper3d.com/photo/albums/parametric-wine-rack)).
- Printable interpretation: a 3-2-3 honeycomb of 8 identical hex frames with conical tongue-and-groove edges, or a 3 x 3 circle-in-square grid with double dovetails; monochrome matte PETG, ribbed outer faces to hide layer lines; optional two-tone edge/corner modules.

### (c) Pretty / decorative - organic, Voronoi, lattice, art-deco, wood-look, botanical, lit, two-colour

- **Organic / Gaudi**: GustaVino ([3DPrint.com](https://3dprint.com/94688/3d-printed-gustavino-wine-rack/)); iluminari3d's topology-optimised Organic rack with welded seams ([2694728](https://makerworld.com/en/models/2694728-organic-wine-glass-rack-4-bottle-stand)); Organic Tree glass rack ([2843541](https://makerworld.com/en/models/2843541-wine-glass-holder-organic-tree-rack)).
- **Voronoi**: O3D's Voronoi hex module in the Hex Drawers set ([Cults O3D](https://cults3d.com/en/3d-model/home/modular-wine-rack-o3d), [Cults 15054](https://cults3d.com/:15054)); Voronoi vase language ([Thangs KadirPCF3d](https://thangs.com/designer/KadirPCF3d/3d-model/Parametric%20Voronoi%20Decorative%20Vase-1557081), [3DPrint.com Voronoi style](https://3dprint.com/91649/voronoi-style-3d-prints/amp/)).
- **Sculptural metal to reinterpret**: Alessi Barkcellar (tree-bark-inspired stainless, Boucquillon & Maaoui) ([Zanolli](https://www.zanolli.com/en/bottle-rack-barkcellar-steel-alessi)), Alessi Noe by Iacchetti ([Connox](https://connox.com/categories/kitchenware/bottle-racks/alessi-noe-bottle-rack.html)), Michael Noll cast aluminium stacked circles ([1stdibs](https://www.1stdibs.com/furniture/dining-entertaining/barware/core-wine-rack-made-aluminium-including-corkscrew-metallic/id-f_36651572)).
- **Art deco / brass**: 1940s oak + brass wine cooler by Geraud Lafitte ([1stdibs](https://www.1stdibs.com/furniture/dining-entertaining/wine-coolers/1940s-oak-wood-brass-french-wine-cooler-geraud-lafitte-george-goulet/id-f_40952352)); mid-century wrought iron with brass details ([1stdibs wine racks](https://www.1stdibs.com/buy/wine-racks)).
- **Lit / edge glow**: KingsBottle acrylic + metal LED racks ([Complete Home](https://www.completehome.com.au/?p=76421)); Ashdeco live-edge wood with warm LED backlight ([Ashdeco](https://ashdeco.com/products/live-edge-solid-wood-led-wall-wine-rack.oembed)); Illuminated Luxury Liquor Display Shelf on MakerWorld ([2386858](https://makerworld.com/en/models/2386858-illuminated-luxury-liquor-display-shelf-led-001)); a maker who lined a rack with addressable LED strips behind printed terraced tiles (search snippet).
- **Two-colour / multi-material**: Infinity Cell "red for red, white for white" cells ([839990](https://makerworld.com/en/models/839990-modular-wine-rack-infinity-cell)); Wine Hive suggests base colour + highlight compartments; Hexwine in Indigo Purple.
- **Wood-look**: "Wooden Wine Rack / No Supports" on Cults ([link](https://cults3d.com/en/3d-model/home/wooden-wine-rack-no-supports)); the Organic rack sanded and painted; dbadev chose Prusament Mystic Brown because it reads as Burgundy.
- Printable interpretation: keep the load path in a plain PETG/ASA skeleton (rings + ribs), then hang a decorative Voronoi/botanical/deco skin on it in a second material (wood PLA, matte, translucent for LED glow) via the H2D's dual nozzle, so the pretty part never carries the bottles.

---

## 5. Licensing (passing mention)

Most surveyed MakerWorld models are "Standard Digital File License" (personal use) or CC BY-NC-SA/ND; Hexwine and ILikon are CC BY-SA; Printables 939239 is CC BY-NC; marcinmiszewski explicitly forbids selling prints; Wine Hive is MakerWorld Exclusive. Patents exist for modular wine racks and honeycomb units (e.g. [US7882967B2](https://patents.google.com/patent/US7882967), [USD701436](https://patents.google.com/patent/USD701436)). We are designing original work, not copying any of these; this is only relevant if a design were to be sold.

---

## 6. Implications for the three new designs (335 x 335 mm, H2D)

1. Target **8-9 bottles** (3 x 3 square grid at ~111 mm pitch or 3-2-3 honeycomb at ~105 mm pitch); clear bore **92 mm** with a flared entry; optionally a narrower neck-end stop.
2. Nothing one-piece. Build from **identical cells with conical tongue-and-groove or double dovetails** (self-aligning, no mallet), plus a base/frame that ties columns horizontally, or long rails printed on the bed diagonal.
3. Print rings flat (hoop in XY), 3-4 perimeters, Arachne, 10-15 % gyroid, fillets at corners; no supports.
4. Load-bearing parts in **PETG or ASA** (chamber makes this easy); PLA variants only for decorative skins. Design spans short enough that even PLA would survive (ILikon precedent) so a PLA option can be offered.
5. Ship a **tolerance test coupon**, key the joints so they cannot be assembled backwards, and add chamfers on every tongue.
6. Avoid big flat bases (warping) - ribbed or lattice bases with a brim-free chamfer; add door-bumper feet.
7. Unobtrusive = flush 3 x 3 lattice or peg pairs in matte white/black/wood; Modern = monochrome honeycomb of identical hex frames with clean edge pieces; Pretty = PETG skeleton + dual-nozzle decorative Voronoi/botanical skin, optional LED channel.

---

## Sources

MakerWorld
- https://makerworld.com/en/models/52448-the-infinite-wine-rack
- https://makerworld.com/en/models/839990-modular-wine-rack-infinity-cell
- https://makerworld.com/en/models/2382813 (Wine Hive)
- https://makerworld.com/en/models/3028018-modular-wine-rack-tool-free-snap-fit-system
- https://makerworld.com/en/models/1356600-modular-wine-rack
- https://makerworld.com/en/models/2373181-fridge-wine-rack-stackable
- https://makerworld.com/en/models/654957-hexwine-modular-honeycomb-wine-rack-shelf
- https://makerworld.com/en/models/2329153-modern-wine-rack-4-5-bottle-versions
- https://makerworld.com/en/models/2374456-wine-glass-rack-wine-stand
- https://makerworld.com/en/models/46590-stackable-bottle-holder-parametric
- https://makerworld.com/en/models/2694728-organic-wine-glass-rack-4-bottle-stand
- https://makerworld.com/en/models/2251168-tilted-modular-wine-rack
- https://makerworld.com/en/models/589075-modular-hexagon-spray-can-rack
- https://makerworld.com/en/models/480320
- https://makerworld.com/en/models/2843541-wine-glass-holder-organic-tree-rack
- https://makerworld.com/en/models/2386858-illuminated-luxury-liquor-display-shelf-led-001
- https://makerworld.com/en/search/models?keyword=wine%20rack

Printables / Thingiverse / Cults / Thangs
- https://www.printables.com/model/939239-modular-wine-rack (and /comments)
- https://www.printables.com/model/57622-modular-wine-bottle-post-and-bracket-system
- https://www.printables.com/model/207209-minimalists-wine-bottle-holder
- https://www.printables.com/model/814602-wine-rack-honeycomb-hexagonal-modular-system-wall
- https://www.printables.com/model/742172-modular-wine-stand
- https://www.thingiverse.com/thing:6619687
- https://www.thingiverse.com/thing:2804083
- https://www.thingiverse.com/thing:1494484
- https://www.thingiverse.com/thing:3641393
- https://www.thingiverse.com/thing:117023
- https://cults3d.com/en/tags/wine+rack
- https://cults3d.com/en/3d-model/home/modular-wine-rack-o3d
- https://cults3d.com/en/3d-model/home/simple-modular-wine-rack
- https://cults3d.com/en/3d-model/home/modular-wavy-wine-champagne-rack-scalable-and-stylish-3d-printable-design
- https://cults3d.com/en/3d-model/home/wooden-wine-rack-no-supports
- https://thangs.com/designer/ljhtom/3d-model/Modular%20bottle%20rack-541948
- https://thangs.com/designer/KadirPCF3d/3d-model/Parametric%20Voronoi%20Decorative%20Vase-1557081

Articles / forums / engineering
- https://medium.com/@peter.yang.ux/3d-printed-prototype-modular-wine-rack-405cceacee07
- https://3dprint.com/94688/3d-printed-gustavino-wine-rack/
- https://www.hubs.com/talk/t/gustavino-the-best-gift-for-wine-lovers/3606
- https://www.fabbaloo.com/2019/02/design-of-the-week-modular-bottle-rack
- https://www.instructables.com/3D-Modular-Wine-Rack
- https://cnckitchen.com/blog/stop-printing-flat-the-45-secret-for-stronger-parts
- https://forum.bambulab.com/t/print-orientation-angled-3d-printing-can-make-parts-stronger/224404
- https://forum.bambulab.com/t/printing-spool-rack-with-pla/60310
- https://forum.bambulab.com/t/would-petg-have-worked-better/130412
- https://forum.bambulab.com/t/need-help-splitting-a-model-with-a-joint-for-snapping-together/182825
- https://cdn.shopify.com/s/files/1/0224/5205/files/Cut_Tool.pdf
- https://qidi3d.com/blogs/print-lab/3d-printing-coffee-bean-cellar-racks
- https://arxiv.org/abs/2302.11240v2
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7764475/
- https://clevercreations.org/what-is-strongest-infill-pattern-cura-prusa/
- https://all3dp.com/2/strongest-infill-pattern/
- https://zbotic.in/3d-printing-layer-adhesion-how-to-improve-part-strength-in-the-vertical-direction/
- https://education.vigilantinc.com/wine-bottle-sizes-dimensions-wine-racks
- https://www.pbtech.co.nz/product/PTRBAM0014/Bambu-Lab-H2D-Build-Size-350-x-320-x-325-mm-Dual-n
- https://matterhackers.com/store/l/bambu-lab-h2d-3d-printer

Commercial / design references
- https://www.coroflot.com/johnpaulick/WineHive®-modular-wine-rack
- https://winecellarhq.com/products/winehive-20-cell-modular-wine-rack
- https://www.connox.com/categories/kitchenware/bottle-racks/wine-rack-set-up.html
- https://notaboringbox.co.uk/products/honeycomb-wine-bottle-rack
- https://www.oliverbonas.com/homeware/hexagon-gold-wall-wine-rack-252531
- https://www.therange.co.uk/cooking-and-dining/kitchen-accessories/kitchen-storage/wine-racks/countertop-hexagon-wine-rack
- https://www.1stdibs.com/furniture/dining-entertaining/serving-pieces/rosewood-beech-bentwood-wine-rack-torsten-johansson-ab-formtra/id-f_39963412
- https://www.chairish.com/product/18597963/rosewood-beech-bentwood-wine-rack-by-torsten-johansson-for-ab-formtra
- https://ikea.com/ca/en/p/kallax-insert-for-bottles-white-80401292
- https://ikeahackers.net/2016/12/ikea-kallax-wine-rack-insert.html
- https://www.chefsupplies.ca/products/vinotemp-epicureanist-modern-3-bottles-peg-racking-ep-peg3s
- https://www.zanolli.com/en/bottle-rack-barkcellar-steel-alessi
- https://connox.com/categories/kitchenware/bottle-racks/alessi-noe-bottle-rack.html
- https://www.1stdibs.com/furniture/dining-entertaining/barware/core-wine-rack-made-aluminium-including-corkscrew-metallic/id-f_36651572
- https://www.1stdibs.com/furniture/dining-entertaining/wine-coolers/1940s-oak-wood-brass-french-wine-cooler-geraud-lafitte-george-goulet/id-f_40952352
- https://www.completehome.com.au/?p=76421
- https://ashdeco.com/products/live-edge-solid-wood-led-wall-wine-rack.oembed
- https://www.grasshopper3d.com/photo/albums/parametric-wine-rack
- https://3dprint.com/91649/voronoi-style-3d-prints/amp/
- https://patents.google.com/patent/US7882967
- https://patents.google.com/patent/USD701436
