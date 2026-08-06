# Fidget Spinner Competitor Scan (downloaded corpus)

Mesh analysis of 30 downloaded designs in `fidgetspinners/` (trimesh: bbox,
mass at 100% PLA, bore estimate = min radial vertex distance, rim ratio =
Iz / uniform-disc Iz of same mass+radius, dominant angular symmetry via FFT).
Full per-part table: scratchpad `corpus_scan.txt` (session-local); headline
rows reproduced here.

## Headline numbers per design

| Design | Dims (mm) | Mass (PLA) | Rim ratio | Sym | Notes |
|---|---|---|---|---|---|
| Custom Gyro4Twist | 55x55x16 | 39 g | 0.93 | 4 | one-piece |
| Fidgit Spinner | 77x70x5 | 11 g | 0.77 | 3 | classic tri-arm, thin |
| FloW Arcspin | 66x62x16.5 | 38.5 g | 0.77 | 5 | 5-fold, centre-heavy |
| FloW SpinDot v3 | 32x32x30 | 21.5 g | 0.66 | 12 | compact top |
| G-Man Geometric Core | 85x85x14 | 48 g | 1.04 | 6 | print-in-place journal ~17 mm |
| G-Man Geometric Razor | 82x82x14 | 43 g | 1.04 | 12 | same family |
| G-Man Square Fragment | 90x90x14 | 47 g | 1.10 | 12 | same family |
| G-Man HD Planetary Blade | 85x85x14 | 39 g | 0.96 | 6 | gears |
| G-Man Planetary Gears | 82-89x12 | 31-46 g | 1.09-1.19 | 6-10 | ring gear ID ~33 mm |
| Gun Toy Spinner | multi | ~24 g | mixed | - | novelty |
| Gyro Fidget Rings | 53-67x4 | 8-14 g | 1.05-1.08 | 8-12 | thin nested rings |
| Helix Space Rocket | 41x37x73 | ~20 g | 0.62-0.90 | 3 | vortex top, tall |
| Impossible Passthrough | 50x58x72 | 30-39 g | 0.55-0.70 | 6 | illusion piece |
| Keychain Spinner | 32x57x6 | 5 g | 0.52 | 2 | tiny bar |
| Med Dahlia | 128x128x179 | 72 g | 0.45 | 8 | large sculpture |
| Planetary Screw Gear | 83x83x21 | 25.5 g ring | 1.69 ring | 10 | herringbone PiP |
| Pop-On Cap Propeller | up to 450 | ~30 g | 0.99 | 6 | bottle-cap novelty |
| PiP Planetary Gear Spinner | 85x85x15 | 61 g | 1.08 | 3 | one-print gears |
| Smooth | 45x45x9 | 14.5 g | 0.96 | 9 | bearingless disc |
| Bearing Shuriken | 166x192x10 | 107 g | 0.59 | 12 | oversized novelty |
| Squspi ball | multi small | - | - | - | ball puzzle |
| Tactile Fidget Rings | 40x40x13 | 16 g | 0.96-0.97 | 7-12 | spinning rings |
| Thor's Hammer | 24x24x24 | 8 g | 0.86 | 4 | keyswitch clicker |
| Triple Helix Gear | 30-64 | 2-8 g | 0.89-1.06 | 6 | gear cage |
| Vega (ring set) | 22-27x8.6 | 0.5-0.6 g/ring | 1.65-1.71 | 12 | pure rings - highest rim ratio |
| Vortex Ball | 50x50x90 | 82 g | 0.87 | 8 | twist toy |
| Wave Gyro HD | 90x89x14 | 68 g | 0.98 | 4 | heavy quad |
| Daisy fidget | 67x67x8 | 22 g | 0.85 | 4 | flower disc |
| Magic spinning top | 73x73x41+13 | 13 g | 0.89-1.12 | 3 | two-piece top |
| Kunai | - | - | - | - | zip had no mesh files |

## What the corpus says

- Size/mass conventions confirmed: flat spinners cluster 55-90 mm dia,
  12-16 mm thick, 30-70 g at 100% PLA - our research digest's numbers hold.
- Rim ratio separates the field: gear/ring designs reach 1.0-1.2 (pure rings
  1.65-1.7, the theoretical rim-weighting ideal); sculpture/novelty designs
  sit at 0.45-0.7 and will feel dead. Steel-nut rim loading (our builds) buys
  what plastic alone cannot: Pentaroule's 5 nuts at 19.5 mm triple its Iz.
- Print-in-place planetary gears are saturated: 4 of 30 designs. The G-Man
  ~17 mm bore family is a printed journal, not a 608 seat - bearingless
  spinners are a big corpus fraction.
- Whitespace confirmed for the two builds: zero constant-width silhouettes
  (only Arcspin is even 5-fold), zero asymmetric-but-balanced designs. Judges'
  uniqueness scores for Pentaroule 60 and Counterfeit Comet stand.

## Reconciliation with `fidgetspinners/ANALYSIS.md` (leaderboard context)

`fidgetspinners/ANALYSIS.md` + `scan_report.json` identify the corpus as the
MakerWorld top-30 leaderboard (likes + boosts, Aug 2026). Their headline
findings, which this geometric scan corroborates:

- **Print-in-place, zero hardware is the #1 shared trait** — the majority
  ship one STL that spins off the plate (G-Man filenames literally encode
  tuned PiP clearances). Only Thor's Hammer uses a bearing.
- Dominant form factor: palm flat disc 40-90 mm, median ~67 mm; mass at rim.
- Two mechanism families own the chart: planetary gear trains (9 models) and
  nested gyro rings (7 models); rest are vortex/twist and novelty kinetic.
- Motion must be GIF-legible; variant breadth feeds the ranking flywheel.
- Their formula: "flat, rim-weighted, rotationally symmetric print-in-place
  mechanism, 40-90 mm, that photographs as motion."

Implication for our builds: Pentaroule 60 and Counterfeit Comet use a real
608 bearing + steel nuts — better spin physics than any PiP journal, but
against the leaderboard meta they carry hardware friction (buy a bearing,
pause-insert nuts). If MakerWorld traction ever matters, a bearingless
print-in-place variant (printed journal like the G-Man ~17 mm bore family)
is the obvious derivative; the constant-width and CoM-nulled silhouettes
remain the differentiators either way.
