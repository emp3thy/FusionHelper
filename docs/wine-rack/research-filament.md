# Filament selection for a 3D-printed wine rack (Bambu Lab H2D / H2C)

Research date: 2026-10-03. Scope: a rack holding 9-12 full 750 ml bottles (1.2-1.6 kg each, so 12-20 kg sustained static load for years), indoors at room temperature, possibly near a kitchen oven or on a sunny windowsill. Longest part ~335 mm. Printer: Bambu Lab H2D or H2C.

Framing: a wine rack is a **creep** problem (slow, permanent deformation under a load that is far below the material's breaking strength), not a strength problem. Every common filament is strong enough to hold 20 kg in a sensible geometry; the question is which one is still straight in five years, and which one survives a hot kitchen or a sunny window.

---

## 0. Executive summary

| Design goal | Filament pick | Why |
|---|---|---|
| (a) Best overall structural | **Bambu PETG-CF** (PET-CF if budget allows; PETG HF as cheap fallback) | ~40% stiffer than PETG HF, HDT 74 °C, low warping, no chamber heat needed, prints on the stock textured PEI plate with the stock hardened 0.4 mm nozzle. Creep is proportional to stress/modulus, so the stiffness gain directly cuts sag. |
| (b) Looks-first ("pretty") | **Polymaker Panchroma Marble** or **Bambu PLA Marble** (stone); **Bambu PLA Wood** / **Fiberlogy FiberWood** (wood); **Bambu PETG Translucent** for lit designs | PLA-based decorative filaments give the best furniture finish but creep worst, so over-build (6+ walls, 40%+ gyroid) and keep them away from oven and sun; or print a PETG-CF structural core with decorative PLA cladding. |
| (c) Unobtrusive matte / neutral | **Bambu ASA** (naturally matte, neutral greys/whites/blacks, HDT 100 °C, UV-stable) or **Prusament PETG Matte / Polymaker Panchroma Matte PLA** if you want zero-fuss printing | ASA is the only option that is matte, creep-resistant, heat-resistant and UV-stable at once; cost is warping risk on a 335 mm part (needs the 65 °C chamber preheated). |
| (d) Modern (matte black / white / CF) | **Bambu PETG-CF black** (soft sheen, nearly invisible layer lines) or **PET-CF** for the stiffest black; **ASA white** or **PETG HF white** for white | CF filaments hide layer lines better than anything else and are the stiffest options; avoid PLA-CF for the structure despite its matte look (HDT 55 °C, PLA creep). |

Universal print settings for a load-bearing furniture piece: 0.4 mm nozzle at 0.2 mm layers (or 0.6 mm nozzle at 0.3 mm for CF), **5-6 walls**, **30-40% gyroid or cubic infill**, 5-6 top/bottom layers, orient parts so bottle load is carried in-plane (XY) rather than across layer lines, generous fillets at every load path, no thin cantilevers. Keep working stress in the plastic below roughly 10% of yield for a multi-year life.

Critical geometry note: the H2D single-nozzle build area is **325 × 320 × 325 mm** (350 mm is only the combined reach of both nozzles) and the H2C is **305 × 320 × 325 mm**. A 335 mm part therefore does not fit along any axis in single-nozzle mode; it must be printed diagonally on the plate, printed in dual-nozzle mode with the slicer's extended-X allowance, or split into joined modules. See section 4.

---

## 1. Creep and long-term static load (the crux)

### 1.1 What the evidence says

**Independent / academic**

- Dogan (2022), *Strojniški vestnik - J. Mech. Eng.* 68(7-8):451-460, tested 3D-printed ABS, CPE (co-polyester, PETG-class), PLA, Tough PLA, PC and nylon at 25/40/60 °C and 10/20 MPa under ASTM D2990 procedures. Material, temperature and load all significantly changed creep. A secondary summary of the paper ranks creep resistance **PC (best) > ABS/ASA (moderate) > nylon (large elongation, no rupture) > PLA (worst)**, and notes that **load was a stronger driver of creep than temperature** in the 25-60 °C window. [sv-jme article page](https://www.sv-jme.eu/article/short-term-creep-behavior-of-different-polymers-used-in-additive-manufacturing-under-different-thermal-and-loading-conditions/), [summary at Ryan Dynamics](https://www.ryandynamics.com.au/insight/materialcreep/)
- Waseem et al. (2020), tensile creep of printed PLA at 25 °C under a constant **15 MPa (~30% of UTS)**: specimens crept to rupture in about **2.1 h** even at the optimum settings (0.1 mm layers, 100% infill, hexagonal infill). This shows how aggressive PLA creep is at room temperature when stress is a meaningful fraction of yield. [PMC7764475](https://pmc.ncbi.nlm.nih.gov/articles/PMC7764475/)
- Fischbach & Weinberg, flexural creep of printed PLA: "non-negligible creep over long periods can be observed even at temperatures well below the glass transition temperature", and physical aging shifts the creep curves. [arXiv 2302.11240](https://arxiv.org/abs/2302.11240)
- J. Mater. Eng. Perform. (2024) comparison of printed PAHT-CF, PC and PLA: **highest stage-II creep resistance PAHT-CF, then PC, then PLA**; same order for flexural modulus. [Springer](https://link.springer.com/10.1007/s11665-024-09144-9)
- Short-fibre carbon reinforcement of PETG raises stiffness and dimensional stability; Polymaker markets Fiberon PETG-rCF08 specifically for "low creep", and Bambu markets PET-CF on "creep and warping resistance". [3DJake Fiberon PETG-rCF08](https://www.3djake.ch/en-CH/polymaker/fiberon-petg-rcf08-black), [Bambu PET-CF](https://eu.store.bambulab.com/fr/products/pet-cf)

**Practical / community**

- Bambu forum, "PLA vs PETG HF deformation under load": PLA cable clips lost all tension in a 35-40 °C environment; consensus that PLA shows "exceptional high creeping, completely loosing tension after short time", PETG HF "behaves much much better" and only "creeps slightly after some time"; "for anything with load, PETG is the way to go". One nuance: PLA deflects less on day one because it is stiffer, then creeps past PETG. [forum thread](https://forum.bambulab.com/t/pla-vs-petg-hf-deformation-under-load/212834)
- Bambu forum, "Printing spool rack with PLA": warnings that PLA "will start to creep" under constant load; PETG recommended. [forum thread](https://forum.bambulab.com/t/printing-spool-rack-with-pla/60310)
- Qidi engineering blog on PETG wall brackets: "PETG exhibits noticeable creep at room temperature when loaded above 30% of its yield strength for extended periods"; a bracket at 40% of yield "may look perfect on day one, but it will gradually sag over several months"; recommends a **4-5x safety factor** for permanently loaded brackets. [Qidi](https://qidi3d.com/blogs/print-lab/petg-strength-wall-mounted-brackets)
- General creep-design guidance: use the **creep (apparent) modulus** at the design life rather than the short-term modulus, and apply a material factor of safety of 3-5 to yield for long-term loads. [Penn State design notes](https://sites.esm.psu.edu/courses/emch13/design/design-tech/materials/plastics2.html), [Plastics Technology](https://ptonline.com/columns/the-effects-of-stress)

### 1.2 Property table (Bambu Lab TDS values unless noted; XY direction)

| Material (Bambu) | Bending modulus (MPa) | HDT 0.45 MPa (°C) | Vicat (°C) | Tensile (MPa) | Creep tendency at 20-35 °C | Source |
|---|---|---|---|---|---|---|
| PLA Basic | 2750 ± 160 | 57 | ~60 | ~35 | **Worst** of the group; stiff on day 1, then creeps; already near Tg at 35-40 °C | [TDS via Additive-X](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/494/product_id/2236) |
| PLA Matte | 2360 ± 250 | ~57 | 63 | - | PLA creep plus weaker layer bonding | [TDS](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/513/product_id/2261) |
| PLA Wood | 2780 ± 120 | 57 | - | 26 ± 5 | PLA creep; low tensile strength | [TDS](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/1045/product_id/2935) |
| PLA Marble | - | - | 57 | - | PLA creep | [Bambu/3D Universe](https://shop3duniverse.com/collections/filament/products/bambu-lab-pla-marble-1-75mm-1kg) |
| PLA Tough+ | 2140 | - | - | - | PLA creep, less stiff (traded for 80.6 kJ/m² impact) | [Bambu store](https://eu.store.bambulab.com/pl/products/pla-tough-upgrade) |
| PLA-CF | 3950 (Z 2260) | 55 | - | 38 (Z 26) | Stiffer so less initial deflection, but PLA matrix still creeps and HDT is the lowest listed | [3D Universe / TDS](https://shop3duniverse.com/collections/filament/products/bambu-lab-pla-cf-carbon-fiber-reinforced-pla-1-75mm-1kg) |
| PETG Basic | 1670 | 69 | - | - | Moderate; much better than PLA at holding tension | [TDS](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/580/product_id/2330) |
| PETG HF | 2050 ± 120 | 69 | 70 | - | Moderate; keep below ~30% of yield | [TDS](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/596/product_id/2346) |
| PETG Translucent | - | - | 78 | - | As PETG | [Stemfinity listing](https://stemfinity.com/collections/technology/products/bambu-lab-petg-translucent) |
| PETG-CF | 2910 ± 260 (Z 1560) | 74 | - | 35 (Z 29) | **Low-moderate**: ~40% stiffer than PETG HF, fibres restrain creep | [PETG-CF TDS](https://polyalkemi.no/wp-content/uploads/2023/08/Bambu_PETG-CF_Technical_Data_Sheet_V2.pdf) |
| PET-CF | 5320 ± 270 (Z 2210) | 205 | - | 74 (Z 35) | **Low**; Bambu markets it on creep resistance and low moisture uptake | [PET-CF TDS](https://polyalkemi.no/wp-content/uploads/2023/11/Bambu_PET-CF_Technical_Data_Sheet_V2.pdf) |
| ABS | 1880 ± 110 | 87 | - | - | Moderate (Dogan: "reasonable for moderate loads") | [TDS](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/566/product_id/2315) |
| ASA | 1920 ± 130 | 100 | 106 | 37 ± 3 | Moderate, better than PETG above 30 °C | [ASA TDS](https://polyalkemi.no/wp-content/uploads/2024/01/Bambu_ASA_Technical_Data_Sheet.pdf) |
| PC | 2310 ± 70 | 117 | 119 | 55 ± 4 | **Best unfilled** (Dogan: top creep resistance) | [PC TDS](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/591/product_id/2340) |
| PAHT-CF | 4230 ± 210 | 194 | - | - | **Best overall** in the 2024 study, but absorbs 0.88% water at 55% RH and softens as it does | [Bambu PAHT-CF](https://eu.store.bambulab.com/en-fi/products/paht-cf) |
| PA6-CF | 5460 ± 280 | 186 | - | - | Very stiff dry; nylon creep rises sharply with moisture | [Filament2Print](https://filament2print.com/en/filaments/3669-pa6-cf-bambu-lab.html) |

Notes on reading the table:
- Z (across-layer) modulus and strength for the CF materials are roughly half of XY. Orient the rack so bottle weight is carried in the XY plane of each part.
- Creep strain for a given load scales inversely with modulus and rises steeply as the service temperature approaches Tg/HDT. PLA at 35 °C in a kitchen is only ~20 °C below its HDT; ASA/PC at 35 °C are 65-80 °C below theirs.
- No manufacturer publishes a creep modulus for these filaments. The practical rule, consistent with all sources above, is: for PLA keep long-term stress under ~10% of yield; for PETG/ASA/ABS under ~20-25%; for PC/CF-PET/PET-CF under ~30%. For a wine rack with 20 kg spread over a few hundred mm² of shelf/ cradle cross-section the nominal stress is well under 1 MPa, so the real risk is local bending at thin cradle arms, cantilevers and layer-line-loaded joints, not gross crushing.

### 1.3 Verdict on creep

1. **PET-CF, PAHT-CF, PC** - the lowest-creep options. PAHT-CF loses that advantage in a humid kitchen; PC is the best unfilled plastic but the hardest to print at this size.
2. **PETG-CF, ASA, ABS** - comfortably adequate for a 12-20 kg rack with sensible geometry; PETG-CF is the stiffest and easiest to print of the three.
3. **PETG HF / PETG Basic** - adequate if walls are generous; expect a small amount of settling in the first months.
4. **PLA family (Basic, Matte, Wood, Marble, Silk, Tough+, PLA-CF)** - will creep. PLA-CF's higher modulus reduces day-one deflection but the matrix is still PLA with the lowest HDT on the list. Use PLA only for decorative or lightly loaded elements, or over-build heavily.

---

## 2. Heat and UV (oven-adjacent, windowsill)

| Material | HDT 0.45 MPa | UV behaviour | Oven-adjacent kitchen (30-50 °C surface) | Sunny windowsill (dark part can exceed 50 °C) |
|---|---|---|---|---|
| PLA / PLA blends | 55-57 °C | Degrades "within months in sunlight"; biodegradable, embrittles | Marginal; PLA "softens at just 60 °C", deforms in a 60 °C dishwasher "like ice cream" | **No** - both heat and UV are problems |
| PETG / PETG HF | 69 °C | Moderate; yellows over time; "sufficient for shaded or seasonal items" | OK | Marginal for multi-summer direct sun |
| PETG-CF / PET-CF | 74 / 205 °C | As PETG matrix (yellowing hidden by black fill) | OK / excellent | Better than PETG; PET-CF fine |
| ABS | 87 °C | Poor: butadiene phase chalks, loses 50-70% impact over 12-18 months in sun | OK | No |
| ASA | 100 °C | **Best**: polyacrylate rubber, "minimal changes in colour and structure" after years outdoors, no chalking | OK | **Yes** |
| PC | 117 °C | Poor unprotected: yellowness index +5-15/year, micro-cracking | OK | No (yellows), unless painted/coated |
| PAHT-CF / PA6-CF | 186-194 °C | Good in black CF grades | OK (moisture is the issue, not heat) | Yes |

Sources: [3DPut strength/heat/UV test](https://3dput.com/pla-vs-petg-vs-asa-which-filament-is-actually-strongest/), [Qidi ASA vs PETG sunlight](https://qidi3d.com/blogs/print-lab/asa-vs-petg-filament-direct-sunlight), [3DPrinterly UV](https://3dprinterly.com/is-pla-uv-resistant-including-abs-petg-more/), [3DJake outdoor filaments guide](https://www.3djake.com/info/guide/outdoor-ready-filaments-for-weather-resistant-3d-prints), [3DXTech ASA vs ABS](https://www.3dxtech.com/blogs/featured/asa-filament-vs-abs-outdoor-uv-parts), [Boxumold ABS vs PC outdoor](https://boxumold.com/comparisons/abs-vs-pc-for-outdoor-use), [Qidi dishwasher clips](https://qidi3d.com/blogs/print-lab/3d-print-dishwasher-rack-clips-petg-guide), [JLC3DP PLA temperature resistance](https://jlc3dp.com/blog/pla-temperature-resistance)

Annealing note: PLA can be annealed (30 min at ~100 °C raises HDT from ~56 °C to ~108 °C, and HTPLA grades reach 140 °C+), but standard PLA shrinks 3-5% unpredictably and warps during annealing, which is unworkable for a 335 mm furniture part. Not recommended here. [Siddament annealing guide](https://siddament.com.au/blogs/filament-guide-au/annealing-pla-for-strength), [Protopasta HTPLA](https://proto-pasta.com/blogs/applications/anneal-htpla-cf-for-a-truly-durable-fiddle)

---

## 3. Aesthetics: furniture-like finishes

### 3.1 Finish families

| Finish family | Layer-line visibility | Seam hiding | Colour range | Structural penalty | Notes |
|---|---|---|---|---|---|
| **Matte PLA** (Bambu PLA Matte, Polymaker Panchroma Matte (ex-PolyTerra), Sunlu Matte, eSun Matte) | Low - matte "cleverly conceals layer lines" | Good | Very wide, many muted "furniture" tones | Matte fillers cut layer adhesion sharply (Bambu forum: "really weak layer bonding"; tests report ~1/3 the layer adhesion of glossy PLA). Bambu PLA Matte modulus 2360 vs 2750 MPa | Beautiful but the worst structural PLA; use more walls |
| **Wood-fill PLA** (Bambu PLA Wood: Black Walnut, Rosewood, Classic Birch; Polymaker Panchroma Wood Brown; Fiberlogy FiberWood natural/brown/black/white) | Low - matte, slightly rough, wood-powder texture | Good | Wood tones; FiberWood can be **sanded and stained** | PLA creep; Bambu PLA Wood tensile only 26 MPa; wood fills are abrasive-ish and can clog 0.2 mm nozzles (0.4 fine) | Closest to real furniture look; FiberWood is "less brittle than other wood-like materials" and smells of wood; 750 g spools |
| **Marble / stone PLA** (Bambu PLA Marble; Polymaker Panchroma Marble in Marble White, Slate Grey, Brick, Limestone, Sandstone) | Low - speckle pattern breaks up lines | Good | Stone tones | PLA creep; Bambu PLA Marble Vicat 57 °C | Best "stone look"; Panchroma Marble is matte-stone and widely stocked in UK (123-3D £15-19) |
| **Galaxy / Sparkle PLA** (Bambu) | Low - "shimmer helps mask layer lines" | Good | Jewel tones | PLA creep | Glossy sparkle, more "decor" than "furniture" |
| **Silk PLA** | Low (gloss hides lines) but shows seams | Poor | Metallic brights | Brittle, "notoriously" weak layer bonding, rigidity "less than half of regular PLA" | **Avoid** for anything loaded |
| **PLA-CF** (Bambu) | Very low - "matte finish with almost invisible layer lines" | Excellent | Black, plus a few dark colours | PLA creep, HDT 55 °C | Looks best of the PLAs; keep for decorative parts |
| **PETG-CF** (Bambu) | Very low - "soft reflection, minimal layer lines, delicate texture"; a satin/shiny finish rather than matte | Excellent | Black, Titan Grey, Indigo Blue, Brick Red, Malachite Green | None - this is the structural pick | Modern engineered look |
| **PET-CF** (Bambu) | Very low, matte-satin black | Excellent | Black only | None | Stiffest, most expensive |
| **ASA** (Bambu, Polymaker PolyLite) | Low-moderate - ASA prints naturally matte | Fair | Neutral greys, white, black, a few colours | None | Best "quiet, matte, could-be-injection-moulded" look |
| **PETG HF** (Bambu) | Moderate - glossy, shows lines and seams more | Fair | Wide | None | Choose a dark or matte-ish colour to hide lines |
| **PETG Translucent / clear** (Bambu PETG Translucent; Polymaker PolyLite PETG Transparent; eSun PETG Clear; Fiberlogy PCTG transparent; Bambu/Polymaker PC Transparent) | Lines visible as internal refraction; reads as frosted glass unless printed slowly at 0.1 mm | Fair | Clear plus tinted translucents | None (PETG) | Best for **lit designs**: Bambu PETG Translucent is "crystal clear" with Vicat 78 °C; PLA Translucent is frosted and diffuses light but is PLA |

Sources: [Polymaker Panchroma Matte (layer lines)](https://www.3djake.com/polymaker/panchroma-pla-matte-cotton-white), [Sunlu Matte](https://www.3djake.com/sunlu/pla-matt-white), [Bambu forum PLA Matte weak bonding](https://forum.bambulab.com/t/bl-pla-matte-black-really-weak-layer-bonding/112806), [Bambu PLA Wood TDS](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/1045/product_id/2935), [Polymaker PolyTerra/Panchroma Wood](https://www.3djake.com/polymaker/polyterra-pla-wood-brown), [Fiberlogy FiberWood](https://fiberlogy.com/en/product/fiberwood-filament-s2/), [Polymaker Panchroma Marble](https://polymaker.it.com/product/panchromatm-marble-pla/), [Bambu PLA Marble](https://shop3duniverse.com/collections/filament/products/bambu-lab-pla-marble-1-75mm-1kg), [Bambu Galaxy](https://3dprintingcanada.com/a/p/products/purple-bambu-lab-pla-galaxy-filament-175mm-1kg), [Silk PLA problems](https://all3dp.com/4/all-shine-no-snaps-new-polymaker-filament-solves-silk-plas-biggest-flaws/), [Tom's 3D silk review](https://toms3d.org/?p=1675), [Bambu PLA-CF finish](https://shop3duniverse.com/collections/filament/products/bambu-lab-pla-cf-carbon-fiber-reinforced-pla-1-75mm-1kg), [Bambu PETG-CF finish](https://www.3dprintergear.com.au/bambu-lab-petg-cf), [Bambu PETG Translucent guide](https://grandavehousing.calpoly.edu/news/bambu-labs-translucent-petg-a), [Bambu forum transparent PETG tips](https://forum.bambulab.com/t/transparent-petg-basic-any-tips/33191?page=5), [3DJake transparent filament range](https://www.3djake.ch/de-CH/filament/3d-drucker-filament-transparent)

### 3.2 Named picks by look

- **Wood look**: Bambu PLA Wood (Black Walnut is the most convincing dark wood; Classic Birch for light), Polymaker Panchroma Wood Brown (matte, prints like plain PLA), Fiberlogy FiberWood (can be sanded and stained like real wood, which is the trick for a genuinely furniture-grade finish). All are PLA: decorative use or over-built.
- **Stone look**: Polymaker Panchroma Marble (five stone colours, matte), Bambu PLA Marble (white/grey speckle). Also PLA: same caveat.
- **Clear / lit**: Bambu PETG Translucent (clear, plus tinted colours; print 0.1 mm layers, 265-270 °C, slow, 0.6-0.8 mm nozzle reduces internal line count, dry first), Polymaker PolyLite PETG Transparent, Fiberlogy PCTG Pure Transparent (tougher, clearer, 70-75 °C HDT class). Bambu PC Transparent is clearer and far more heat resistant but warps and yellows under UV.
- **Modern matte black**: Bambu PETG-CF Black (satin) or PET-CF (matte); PLA-CF for pure matte if decorative only.
- **Modern white**: Bambu ASA White (matte) or PETG HF White (gloss); white PLA Matte is lovely but is the weakest option of all.

### 3.3 Seam and surface tips that matter more than the filament

Set the seam to "aligned" and tuck it on an inside corner; use 5+ walls so any surface defect has material behind it; print the visible face up or outward (top surfaces ironed at 0.2 mm look like injection moulding on matte materials); 0.6 mm nozzle at 0.3 mm layers on CF/wood/marble fills gives a more uniform, less "striped" look than a 0.4 mm nozzle at 0.2 mm.

---

## 4. Printability on H2D / H2C

### 4.1 Machine facts

| Item | H2D | H2C |
|---|---|---|
| Build volume, single nozzle | **325 × 320 × 325 mm** (350 × 320 × 325 combined across both nozzles; 300 mm X in dual-nozzle mode) | **305 × 320 × 325 mm** (300 mm X dual) |
| Stock nozzle | **0.4 mm hardened steel, standard-flow** (community-confirmed: "It comes with the non-HF hardened steel nozzles"); hardened 0.2/0.4/0.6/0.8 available, tungsten-carbide optional | 0.2/0.4/0.6/0.8 mm hotends, up to 7 hot-swappable hotends; material not stated in launch coverage, same hotend family as H2D |
| Max nozzle temp | 350 °C | 350 °C |
| Chamber | Active heating to **65 °C** | Active heating to 65 °C |
| Plate in box | Textured PEI plate (gold) | Textured PEI plate |

Sources: [H2D build volume (3DKoda)](https://pood.3dkoda.com/en/?p=18036), [MatterHackers H2D](https://matterhackers.com/store/l/bambu-lab-h2d-3d-printer), [Bambu forum: H2D default nozzles](https://forum.bambulab.com/t/h2d-default-nozzles/182139), [Bambu forum: what build plate comes with H2D](https://forum.bambulab.com/t/what-build-plate-comes-w-h2d/158830), [H2C launch (3D Printing Industry)](https://3dprintingindustry.com/news/bambu-lab-launches-the-new-h2c-multi-material-3d-printer-technical-specifications-and-pricing-246509), [Bambu H2D hotend (hardened steel)](https://www.makerpoint.nl/en-gb/3d-printing/accessories/hotends/bambu-lab-h2d-hotend-with-hardened-steel-nozzle-0-210000007020)

**The 335 mm part problem.** A 335 mm length exceeds X (325 mm H2D / 305 mm H2C), Y (320 mm) and Z (325 mm) in single-nozzle mode. Options: (1) lay the part diagonally (the H2D plate diagonal is ~456 mm, so a 335 mm × ~90 mm part fits at ~45°); (2) use dual-nozzle mode on the H2D where the combined reach is 350 mm in X, but only if the slicer lets a single object span the two nozzles' zones (it normally does not; the 350 mm is total envelope, not one-object reach); (3) split into two or three modules joined by dovetails, bolts or threaded inserts, which also makes the rack packable and lets you print visible faces up. Option 3 is the robust answer and also shrinks the warping risk for ASA/PC.

### 4.2 Per-material print notes

| Material | Nozzle / bed | Plate | Chamber | Dry before print | Warping risk for a 300+ mm part | Hardened nozzle |
|---|---|---|---|---|---|---|
| PLA (all variants) | 190-230 °C / 35-45 °C (Cool Plate) or 55-65 °C textured PEI | Textured PEI or Cool Plate SuperTack | None; door open/top vented so the chamber stays < 35 °C | 50 °C / 8 h if it has been open a while; Bambu lists 50-55 °C 8 h for Marble/Translucent | Very low | Not needed (Wood/Marble/Galaxy are mildly abrasive; the stock hardened nozzle is fine) |
| PLA-CF | 190-230 °C / 35-45 °C | Textured PEI | None | 55 °C / 8 h | Very low | Yes - stock 0.4 hardened is tested "low clogging risk"; 0.6 recommended |
| PETG HF / Translucent | 240-270 °C / 65-75 °C | Textured PEI (glue stick on smooth PEI or it tears the coating) | None, keep lid vented; chamber 30-40 °C helps clarity on translucent | **65 °C / 8 h** (PETG is hygroscopic; moisture = stringing, haze, 15-20% impact loss) | Low-moderate; corners can lift on big footprints - use a 5-8 mm brim or brim ears, 15-40% infill, more walls rather than more infill | Not needed |
| PETG-CF | 240-270 °C / 65-75 °C | Textured PEI | None | **65 °C / 8 h** (or AMS 2 Pro / AMS HT) | Low (fibres reduce shrinkage) | Yes - stock hardened 0.4 OK; 0.6 "recommended to further reduce the risk of clogging" |
| PET-CF | 260-290 °C / 80-90 °C | Textured PEI or Engineering | Warm chamber helps | 80 °C / 8-12 h | Low | Yes |
| ABS | 240-270 °C / 90-100 °C | Textured PEI + glue | **Yes** - preheat chamber to 50-60 °C before starting | 80 °C / 8 h | **High** on a 300 mm part; brim, chamber preheat, lower infill | Not needed |
| ASA | 240-270 °C / 90-100 °C | Textured PEI + glue | **Yes** - TDS says 45-60 °C; community: wait for 50-60 °C before starting | 80 °C / 8 h | **High**; same mitigations as ABS, plus gyroid infill, 0 mm brim gap | Not needed |
| PC | 260-280 °C / 90-110 °C with glue | Engineering or Textured PEI with glue | **Yes** - 45-60 °C, preheat; "requires a closed enclosure" | 80 °C / 8 h | **Very high**; large PC parts warp and crack; split the model | Not needed |
| PAHT-CF / PA6-CF | 270-300 °C / 80-100 °C | Engineering / PEI + glue (PAHT-CF has damaged plates) | Yes, 60 °C+ | **80 °C / 12 h**, store < 20% RH, print from AMS HT; parts absorb moisture after printing | Moderate | Yes; 0.6 recommended |

Sources: [Bambu filament guide material table](https://wiki.bambulab.com/en/general/filament-guide-material-table), [Bambu filament guide PDF](https://cdn1.bambulab.com/filament/a5e185aed14e6/filament-guide-en-4.pdf), [Bambu drying guide](https://wiki.bambulab.com/en/filament-acc/filament/dry-filament), [Printpal drying table](https://printpal.io/wiki/filament-drying-guide), [PETG-CF printing guide](https://grandavehousing.calpoly.edu/news/bambu-lab-petg-cf-your), [Bambu ASA TDS (chamber 45-60 °C)](https://polyalkemi.no/wp-content/uploads/2024/01/Bambu_ASA_Technical_Data_Sheet.pdf), [Bambu PC TDS](https://www.additive-x.com/shop/mpattachments/file/viewonline/id/591/product_id/2340), [Bambu forum ABS/ASA warping tips](https://forum.bambulab.com/t/no-fuss-abs-asa-tips-and-tricks-to-minimize-warping/148751), [Bambu forum PC warping](https://forum.bambulab.com/t/polycarbonate-warping-issue/19597), [Bambu forum PETG warping P1S](https://forum.bambulab.com/t/petg-warping-on-a-new-p1s/85455), [Bambu forum PAHT-CF plates](https://forum.bambulab.com/t/unable-to-print-with-bambu-paht-cf-it-destroys-the-printing-plates/21250), [Bambu PAHT-CF page](https://eu.store.bambulab.com/en-fi/products/paht-cf), [Bambu hardened nozzle / CF guidance](https://www.makerlab.ph/products/bambu-hotend-with-hardened-steel-nozzle-0-4-mm-for-h2d-fah023)

Bambu-specific profiles: every Bambu filament ships with an RFID tag that auto-loads the matching Bambu Studio system preset (e.g. "Bambu PETG-CF @BBL H2D 0.4 nozzle"), including chamber temperature targets for ABS/ASA/PC/PA on the H2D/H2C. Third-party filaments use the "Generic PETG/ASA/PC" presets; Polymaker and Prusament have vendor profiles in Bambu Studio/OrcaSlicer. For CF materials select the "0.6 nozzle" preset if you fit a 0.6 mm hardened hotend.

---

## 5. Contact with labels (no food contact needed)

Bottles are sealed, so food safety is irrelevant. The only contact concern is the paper label resting on the rack. All of the rigid filaments considered (PLA, PETG, PETG-CF, PET-CF, ABS, ASA, PC, PA-CF) are unplasticised glassy polymers with no migrating plasticiser at room temperature; none is known to stain paper. The materials that *do* carry migrating plasticisers are flexible ones (plasticised PVC; some "flexible PLA" grades; some TPU compounds), which are not candidates here. Two mild cautions: silk PLA and some matte/"tough" PLA blends contain undisclosed additives and have shown surface bloom on long storage, so avoid silk for label-contact surfaces; and wood-fill PLA can transfer colour when damp, so do not use it in a cellar-humid spot. Filamentive's EN 71-3 certified PLA and PLA Matte are an option if certified non-leaching matters. Sources: [PVC plasticiser migration study](https://asep.lib.cas.cz/arl-cav/en/detail-cav_un_epca-0558889-Substantial-drop-of-plasticizer-migration-from-polyvinyl-chloride-catheters-using-coextruded-thermo), [Filamentive EN 71-3](https://all3dp.com/6/filamentives-pla-and-pla-matte-filaments-are-now-en-71-3-compliant/), [PLA/plasticiser research](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6213132/)

---

## 6. Cost (UK, inc. VAT, October 2026) and cost of a 1.5-2 kg rack

| Filament | Price per 1 kg spool | Volume price | Source |
|---|---|---|---|
| Bambu PLA Basic / PLA Matte / PETG HF / PETG Translucent | from £17.99 | refill 4+ £13.99, 6+ £11.99; store-wide "buy 4 save 25%, buy 6 save 30%" | [Bambu UK store](https://uk.store.bambulab.com/en/collections/bambu-lab-3d-printer-filament) |
| Bambu PLA Wood / PLA Marble | £22.99 | | [Bambu UK store](https://uk.store.bambulab.com/en/collections/bambu-lab-3d-printer-filament) |
| Bambu PLA Tough+ / PLA Silk+ | £21.99 / £20.99 | | [Bambu UK store](https://uk.store.bambulab.com/en/collections/bambu-lab-3d-printer-filament) |
| Bambu ABS | £20.99 (refill £17.99) | 4+ £16.99 | [Bambu UK store](https://uk.store.bambulab.com/en/pages/bambu-filament) |
| Bambu ASA | £27.99 | | [Bambu UK ASA](https://uk.store.bambulab.com/collections/asa) |
| Bambu PC | £36.99 | | [Bambu UK fiber/engineering](https://uk.store.bambulab.com/en/collections/fiber-reinforced) |
| Bambu PLA-CF / PETG-CF | from £28.99 | | [Bambu UK fiber reinforced](https://uk.store.bambulab.com/en/collections/fiber-reinforced) |
| Bambu ASA-CF | £33.99 | | same |
| Bambu PET-CF | from £41.99 | | same |
| Bambu PAHT-CF | from £45.99 | | same |
| Polymaker Panchroma Marble PLA | £15-19 | | [123-3D](https://www.123-3d.co.uk/Polymaker-Panchroma-PLA-Marble-filament-White-1-75mm-1-kg-CA04005-i11960.html) |
| Polymaker PolyLite PETG | £18.75-27.96 | | [PriceRunner](https://www.pricerunner.com/pl/1426-3207793577/3D-Printing/Polymaker-PolyLite-PETG-Yellow-1.75mm-Compare-Prices) |
| Polymaker PolyLite ASA | £37.99 (5 kg £128) | | [123-3D](https://www.123-3d.co.uk/Polymaker-PolyLite-ASA-filament-1-75mm-Black-5-kg-PM70991-i9840.html) |
| Prusament PETG | £36.80 (2 kg £49.99) | | [123-3D](https://www.123-3d.co.uk/Prusament-Filament-PETG-Prusa-Orange-1kg-1-75mm-i11212-t7392.html), [123-3D 2 kg](https://www.123-3d.co.uk/Prusa-Prusament-PETG-Signal-White-2kg-NFC-i15441.html) |
| Prusament PC Blend | ~€51 / 0.9 kg, €90 / 2 kg | | [Prusa forum pricing](https://forum.prusa3d.com/forum/english-forum-general-discussion-announcements-and-releases/prusament-filament-pricing-is-strange/) |
| Sunlu PETG | ~£23 (often less on Amazon multipacks) | | [PriceRunner](https://www.pricerunner.com/pl/1426-3550861465/3D-Printing/Sunlu-PETG-Filament-1.75mm-Less-Stringing-1kg-Spool-Compare-Prices) |
| eSun PETG | £16-24 (refill £16.30) | | [123-3D](https://123-3d.co.uk/eSun-black-PETG-Refill-filament-1-75mm-1kg-PETGRefill175B1-i8254-t140466.html) |
| Fiberlogy PCTG | £28.50-29.50 (0.75 kg) | | [PriceRunner](https://www.pricerunner.com/pl/1426-3547780930/3D-Printing/Fiberlogy-PCTG-Graphite-1.75-mm-Compare-Prices) |
| Fiberlogy FiberWood | 750 g spools, ~€20-25 EU | | [3DJake](https://www.3djake.com/fiberlogy/fiberwood-natural) |

**Rack cost (1.5-2 kg of filament, i.e. two 1 kg spools; add ~10% for brims, purge and a failed first part):**

| Choice | Two spools | Notes |
|---|---|---|
| PETG HF (Bambu) | ~£36 (or ~£28 with refills in a 4-pack) | Cheapest structural option |
| PETG-CF (Bambu) | ~£58 | Recommended structural pick |
| ASA (Bambu) | ~£56 | |
| PC (Bambu) | ~£74 | |
| PET-CF (Bambu) | ~£84 | |
| PAHT-CF (Bambu) | ~£92 | |
| PLA Wood / Marble (Bambu) | ~£46 | |
| Panchroma Marble (Polymaker) | ~£30-38 | |
| Hybrid: 1 kg PETG-CF structure + 1 kg decorative PLA skin | ~£47-52 | Best looks-per-pound |

---

## 7. Ranked recommendations with print settings

Settings common to all four (furniture-grade, load-bearing):
- Layer height 0.2 mm with the stock 0.4 mm hardened nozzle; 0.28-0.3 mm with a 0.6 mm hardened nozzle for CF/wood/marble (faster, fewer clogs, more uniform surface).
- **Walls: 5-6** (≥ 2.4 mm wall thickness); walls carry the load, not infill.
- **Infill: 30-40% gyroid or cubic** (isotropic); going above 50% adds internal stress and warping without useful stiffness. Use 100% / solid modifiers only at bolt bosses and cradle contact pads.
- **Top/bottom: 5-6 layers**, ironing on the visible top face for matte materials.
- Orientation: print cradles and shelves so bottle load acts in the XY plane; never hang 20 kg across layer lines. Fillet every internal corner (R ≥ 3 mm); the Qidi data suggests 30-40% effective strength gain from geometry alone.
- Target working stress < 10% of yield (PLA) or < 20-25% (PETG/ASA/CF-PETG) for a multi-year life; add a 4-5x safety factor on short-term strength.
- Split the 335 mm span into modules or print diagonally (section 4.1).

### (a) Best overall structural choice: **Bambu PETG-CF** (runner-up: PET-CF; budget: PETG HF)
- Why: highest stiffness-to-hassle ratio. 2910 MPa bending modulus (vs 2050 PETG HF), HDT 74 °C, low shrinkage so a 300+ mm footprint prints flat on the stock textured PEI without a heated chamber, uses the stock hardened 0.4 mm nozzle, dries at 65 °C in an AMS 2 Pro. ASA beats it on heat/UV; PC and PET-CF beat it on creep; but neither is as easy at this size.
- Settings: 0.4 hardened nozzle, 0.2 mm (or 0.6 nozzle, 0.3 mm), 250-260 °C, bed 70 °C textured PEI, 5-6 walls, 35% gyroid, 6 top/bottom, no part cooling beyond profile default, 8 mm brim, chamber lid closed but unheated. Dry 65 °C / 8 h first.
- Upgrade path: if the rack will sit in direct sun or beside the oven, switch to **ASA** (chamber 60 °C preheat, glue, split the long part) or to **PET-CF** (HDT 205 °C, 5320 MPa) with a 0.6 mm hardened nozzle.

### (b) Best looks-first choice for a "pretty" design: **Polymaker Panchroma Marble (stone) or Bambu PLA Wood / Fiberlogy FiberWood (wood)**; **Bambu PETG Translucent** if lit
- Why: these give the most convincing furniture surface straight off the plate; FiberWood can be sanded and stained to match real timber. PETG Translucent is the clearest easy-print material and is PETG, so it also carries load acceptably.
- Caveat: wood/marble are PLA (HDT 57 °C, worst creep). Mitigate by: keeping it away from the oven and out of direct sun; printing a hidden PETG-CF spine/cradle and cladding it in the decorative PLA; or over-building the PLA (6-8 walls, 40-50% gyroid, short spans, no cantilevers).
- Settings (PLA Wood/Marble): 0.4 or 0.6 hardened nozzle, 0.2-0.3 mm, 210-220 °C, bed 45-55 °C, 6-8 walls, 40% gyroid, ironing on, chamber vented. Dry 55 °C / 8 h.
- Settings (PETG Translucent, for clarity): 0.1 mm layers, 265-270 °C, slow (≤ 60 mm/s outer walls), 3-4 walls, 100% infill or hollow with 2-3 mm walls, smooth PEI + glue, dry 65 °C / 8 h.

### (c) Best unobtrusive matte / neutral: **Bambu ASA** (easy alternative: Prusament PETG Matte or Polymaker Panchroma Matte PLA)
- Why: ASA prints naturally matte in neutral greys, whites and blacks, has HDT 100 °C, is the only candidate that will not yellow in a window, and creeps less than PETG at kitchen temperatures. The cost is printability: a 300 mm ASA part on the H2D needs the chamber preheated to 55-60 °C, glue on textured PEI, a wide brim, and ideally splitting into modules.
- Settings: 0.4 hardened nozzle, 0.2 mm, 260 °C, bed 95-100 °C, chamber 60 °C (preheat 15 min with aux fan on), 5-6 walls, 30% gyroid, brim 10 mm with 0 mm gap, part cooling ≤ 30%. Dry 80 °C / 8 h.
- If you prefer zero drama, print in **Prusament PETG Matte Black** or **Bambu PETG HF** in a dark colour (gloss shows lines, dark hides them), same settings as (a) minus the CF.

### (d) Best for a "modern" design (matte black / white / CF): **Bambu PETG-CF Black** (or PET-CF for the stiffest, most matte black); **ASA White** or **PETG HF White** for white
- Why: CF filaments have the least visible layer lines of anything printable ("almost invisible layer lines" for PLA-CF, "soft reflection, minimal layer lines" for PETG-CF) and are the stiffest. PLA-CF looks the most matte but is PLA underneath (HDT 55 °C): use it only for non-loaded trim. For white, ASA gives a dead-matte lab-equipment look and heat/UV immunity; PETG HF White is glossier but trivial to print.
- Settings: as (a) for PETG-CF; for PET-CF use a 0.6 hardened nozzle, 0.3 mm, 280 °C, bed 85 °C, chamber 50 °C, dry 80 °C / 12 h. For ASA White as (c).

---

## 8. Sources

Creep and mechanical data
- Dogan, O. (2022) "Short-term Creep Behavior of Different Polymers Used in Additive Manufacturing under Different Thermal and Loading Conditions", Strojniški vestnik 68(7-8):451-460. https://www.sv-jme.eu/article/short-term-creep-behavior-of-different-polymers-used-in-additive-manufacturing-under-different-thermal-and-loading-conditions/ ; repository record https://repozitorij.uni-lj.si/IzpisGradiva.php?id=139817 ; summary https://www.ryandynamics.com.au/insight/materialcreep/
- Waseem et al. (2020) PLA tensile creep RSM study. https://pmc.ncbi.nlm.nih.gov/articles/PMC7764475/
- Fischbach & Weinberg, physical aging and flexural creep of printed PLA. https://arxiv.org/abs/2302.11240
- PAHT-CF / PC / PLA creep and flexural comparison, J. Mater. Eng. Perform. 2024. https://link.springer.com/10.1007/s11665-024-09144-9
- Bambu forum: PLA vs PETG HF deformation under load. https://forum.bambulab.com/t/pla-vs-petg-hf-deformation-under-load/212834
- Bambu forum: printing a spool rack with PLA. https://forum.bambulab.com/t/printing-spool-rack-with-pla/60310
- Qidi: PETG for wall-mounted brackets (30% of yield creep threshold, 4-5x safety factor). https://qidi3d.com/blogs/print-lab/petg-strength-wall-mounted-brackets
- Penn State plastics design notes (creep modulus, material factor of safety). https://sites.esm.psu.edu/courses/emch13/design/design-tech/materials/plastics2.html
- Plastics Technology, "The Effects of Stress". https://ptonline.com/columns/the-effects-of-stress
- 3DPut PLA/PETG/ASA test data. https://3dput.com/pla-vs-petg-vs-asa-which-filament-is-actually-strongest/
- Load-bearing print settings (walls vs infill, gyroid/cubic). https://evezone.evetech.co.za/build-lab/how-to-print-brackets-and-mounts-that-actually-hold-weight
- Wine/bottle rack design notes on MakerWorld (3 walls + Arachne, PETG for weight). https://makerworld.com/models/2382813 ; https://makerworld.com/en/models/1364896-bottle-rack

Bambu Lab technical data sheets and product pages
- PLA Basic TDS. https://www.additive-x.com/shop/mpattachments/file/viewonline/id/494/product_id/2236
- PLA Matte TDS. https://www.additive-x.com/shop/mpattachments/file/viewonline/id/513/product_id/2261
- PLA Wood TDS. https://www.additive-x.com/shop/mpattachments/file/viewonline/id/1045/product_id/2935
- PLA Marble. https://shop3duniverse.com/collections/filament/products/bambu-lab-pla-marble-1-75mm-1kg
- PLA Tough+. https://eu.store.bambulab.com/pl/products/pla-tough-upgrade
- PLA-CF. https://shop3duniverse.com/collections/filament/products/bambu-lab-pla-cf-carbon-fiber-reinforced-pla-1-75mm-1kg
- PETG Basic TDS. https://www.additive-x.com/shop/mpattachments/file/viewonline/id/580/product_id/2330
- PETG HF TDS. https://www.additive-x.com/shop/mpattachments/file/viewonline/id/596/product_id/2346
- PETG Translucent. https://stemfinity.com/collections/technology/products/bambu-lab-petg-translucent
- PETG-CF TDS. https://polyalkemi.no/wp-content/uploads/2023/08/Bambu_PETG-CF_Technical_Data_Sheet_V2.pdf
- PET-CF TDS. https://polyalkemi.no/wp-content/uploads/2023/11/Bambu_PET-CF_Technical_Data_Sheet_V2.pdf ; product page https://eu.store.bambulab.com/fr/products/pet-cf
- ABS TDS. https://www.additive-x.com/shop/mpattachments/file/viewonline/id/566/product_id/2315
- ASA TDS. https://polyalkemi.no/wp-content/uploads/2024/01/Bambu_ASA_Technical_Data_Sheet.pdf
- PC TDS. https://www.additive-x.com/shop/mpattachments/file/viewonline/id/591/product_id/2340
- PAHT-CF. https://eu.store.bambulab.com/en-fi/products/paht-cf ; https://shop3duniverse.com/collections/carbon-fiber-filaments/products/bambu-lab-paht-cf-high-temperature-nylon-carbon-fiber-1-75mm-black
- PA6-CF. https://filament2print.com/en/filaments/3669-pa6-cf-bambu-lab.html
- Filament guide material table. https://wiki.bambulab.com/en/general/filament-guide-material-table ; PDF https://cdn1.bambulab.com/filament/a5e185aed14e6/filament-guide-en-4.pdf
- Drying guide. https://wiki.bambulab.com/en/filament-acc/filament/dry-filament ; https://printpal.io/wiki/filament-drying-guide
- PETG-CF printing guide. https://grandavehousing.calpoly.edu/news/bambu-lab-petg-cf-your
- PETG Translucent guide. https://grandavehousing.calpoly.edu/news/bambu-labs-translucent-petg-a ; forum tips https://forum.bambulab.com/t/transparent-petg-basic-any-tips/33191?page=5
- PETG-CF finish description. https://www.3dprintergear.com.au/bambu-lab-petg-cf
- PLA Galaxy. https://3dprintingcanada.com/a/p/products/purple-bambu-lab-pla-galaxy-filament-175mm-1kg

Printer facts (H2D / H2C)
- H2D build volume breakdown. https://pood.3dkoda.com/en/?p=18036 ; https://matterhackers.com/store/l/bambu-lab-h2d-3d-printer
- H2D default nozzles (hardened steel, non-HF). https://forum.bambulab.com/t/h2d-default-nozzles/182139
- H2D hotend with hardened steel nozzle. https://www.makerpoint.nl/en-gb/3d-printing/accessories/hotends/bambu-lab-h2d-hotend-with-hardened-steel-nozzle-0-210000007020 ; CF nozzle guidance https://www.makerlab.ph/products/bambu-hotend-with-hardened-steel-nozzle-0-4-mm-for-h2d-fah023
- H2D included build plate. https://forum.bambulab.com/t/what-build-plate-comes-w-h2d/158830
- H2C launch specs. https://3dprintingindustry.com/news/bambu-lab-launches-the-new-h2c-multi-material-3d-printer-technical-specifications-and-pricing-246509
- ABS/ASA warping tips. https://forum.bambulab.com/t/no-fuss-abs-asa-tips-and-tricks-to-minimize-warping/148751 ; https://forum.bambulab.com/t/large-asa-prints-warping/26454?page=2
- PC warping. https://forum.bambulab.com/t/polycarbonate-warping-issue/19597 ; https://forum.bambulab.com/t/problems-printing-with-pc/82743
- PETG warping / plate choice. https://forum.bambulab.com/t/petg-warping-on-a-new-p1s/85455 ; https://bambuhub.net/warping-bed-adhesion
- PAHT-CF plate damage. https://forum.bambulab.com/t/unable-to-print-with-bambu-paht-cf-it-destroys-the-printing-plates/21250

Heat and UV
- Qidi ASA vs PETG in sunlight. https://qidi3d.com/blogs/print-lab/asa-vs-petg-filament-direct-sunlight
- 3DPrinterly UV resistance. https://3dprinterly.com/is-pla-uv-resistant-including-abs-petg-more/
- 3DJake outdoor filaments. https://www.3djake.com/info/guide/outdoor-ready-filaments-for-weather-resistant-3d-prints
- 3DXTech ASA vs ABS. https://www.3dxtech.com/blogs/featured/asa-filament-vs-abs-outdoor-uv-parts
- PC vs ABS outdoor (yellowing rates). https://boxumold.com/comparisons/abs-vs-pc-for-outdoor-use
- PLA in dishwashers/kitchens. https://qidi3d.com/blogs/print-lab/3d-print-dishwasher-rack-clips-petg-guide ; https://3dprinterly.com/3d-printing-filament-dishwasher-microwave-safe/
- PLA temperature resistance. https://jlc3dp.com/blog/pla-temperature-resistance
- Annealing PLA. https://siddament.com.au/blogs/filament-guide-au/annealing-pla-for-strength ; https://proto-pasta.com/blogs/applications/anneal-htpla-cf-for-a-truly-durable-fiddle

Aesthetics (third-party)
- Polymaker Panchroma Matte (layer-line concealment). https://www.3djake.com/polymaker/panchroma-pla-matte-cotton-white
- Polymaker PolyTerra/Panchroma Wood. https://www.3djake.com/polymaker/polyterra-pla-wood-brown
- Polymaker Panchroma Marble. https://polymaker.it.com/product/panchromatm-marble-pla/ ; UK price https://www.123-3d.co.uk/Polymaker-Panchroma-PLA-Marble-filament-White-1-75mm-1-kg-CA04005-i11960.html
- Fiberlogy FiberWood. https://fiberlogy.com/en/product/fiberwood-filament-s2/ ; https://www.3djake.com/fiberlogy/fiberwood-natural
- Fiberlogy PCTG. https://www.3djake.com/reviews/fiberlogy/pctg-black
- Sunlu Matte PLA. https://www.3djake.com/sunlu/pla-matt-white ; eSun Matte https://www.3djake.ch/en-CH/esun/pla-matte-light-blue-1
- Matte PLA weak layer bonding. https://forum.bambulab.com/t/bl-pla-matte-black-really-weak-layer-bonding/112806
- Silk PLA flaws. https://all3dp.com/4/all-shine-no-snaps-new-polymaker-filament-solves-silk-plas-biggest-flaws/ ; https://toms3d.org/?p=1675 ; https://forum.bambulab.com/t/silk-filaments-seem-brittle/42849
- Transparent filament range. https://www.3djake.ch/de-CH/filament/3d-drucker-filament-transparent
- Polymaker Fiberon PETG-rCF08 (low creep). https://www.3djake.ch/en-CH/polymaker/fiberon-petg-rcf08-black

Pricing
- Bambu UK store filament collection. https://uk.store.bambulab.com/en/collections/bambu-lab-3d-printer-filament ; fiber reinforced https://uk.store.bambulab.com/en/collections/fiber-reinforced ; ASA https://uk.store.bambulab.com/collections/asa ; volume discount https://uk.store.bambulab.com/pages/promotions/filament-volume-discount ; ABS https://uk.store.bambulab.com/en/pages/bambu-filament
- Prusament PETG UK. https://www.123-3d.co.uk/Prusament-Filament-PETG-Prusa-Orange-1kg-1-75mm-i11212-t7392.html ; 2 kg https://www.123-3d.co.uk/Prusa-Prusament-PETG-Signal-White-2kg-NFC-i15441.html ; PC Blend https://forum.prusa3d.com/forum/english-forum-general-discussion-announcements-and-releases/prusament-filament-pricing-is-strange/
- Polymaker PolyLite ASA UK. https://www.123-3d.co.uk/Polymaker-PolyLite-ASA-filament-1-75mm-Black-5-kg-PM70991-i9840.html
- Polymaker PolyLite PETG UK. https://www.pricerunner.com/pl/1426-3207793577/3D-Printing/Polymaker-PolyLite-PETG-Yellow-1.75mm-Compare-Prices
- Sunlu PETG UK. https://www.pricerunner.com/pl/1426-3550861465/3D-Printing/Sunlu-PETG-Filament-1.75mm-Less-Stringing-1kg-Spool-Compare-Prices
- eSun PETG UK. https://123-3d.co.uk/eSun-black-PETG-Refill-filament-1-75mm-1kg-PETGRefill175B1-i8254-t140466.html
- Fiberlogy PCTG UK. https://www.pricerunner.com/pl/1426-3547780930/3D-Printing/Fiberlogy-PCTG-Graphite-1.75-mm-Compare-Prices

Label contact
- PVC plasticiser migration. https://asep.lib.cas.cz/arl-cav/en/detail-cav_un_epca-0558889-Substantial-drop-of-plasticizer-migration-from-polyvinyl-chloride-catheters-using-coextruded-thermo
- Filamentive EN 71-3 PLA. https://all3dp.com/6/filamentives-pla-and-pla-matte-filaments-are-now-en-71-3-compliant/
- PLA plasticiser blends research. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6213132/
