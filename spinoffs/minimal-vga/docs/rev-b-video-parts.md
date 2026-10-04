# VJUGA rev B Video exact parts — R5.V4

Status: **PASS / FROZEN 2026-08-28.** This is the mechanical parts contract used
by the R5.V5 layout. The exact MPNs, drawings, supplier links and dated stock
snapshot are retained in [`video-parts.json`](../kicad/revb/video-parts.json).
Recheck availability before purchase; this guide does not authorize an order.

## No-substitution parts

| Function | Exact MPN | Frozen package / reason |
|---|---|---|
| VGA output | **NorComp `200-015-213L537`** | Female HD15, right-angle THT, board locks, 4-40 flange. The manufacturer layout is an unusual 7+8 solder-tail pattern; neither generic KiCad 5+5+5 footprint matches. |
| Pixel clock | **ECS `ECS-100A-251.7`** | 25.175 MHz, 5 V TTL, full DIP-14 four-lead can; pins 1 NC, 7 case/GND, 8 output, 14 +5 V. |
| Framebuffer | **Alliance `AS6C1008-55PCN`** | 128Kx8, 55 ns, 32-PDIP, 15.24 mm rows. |
| U5/U6/U7 | **Microchip `ATF22V10C-15PU`** | 5 V EEPLD, 24-PDIP, 7.62 mm rows; exactly the device targeted by the reproducible JEDECs. |
| Card base bus | **Samtec `TSW-139-08-S-S-RA`** | 1x39, 2.54 mm, right-angle male, 5.84 mm mating post, 2.29 mm solder tail, 30 microinch gold. |
| Card extension bus | **Samtec `TSW-110-08-S-S-RA`** | Same construction, 1x10. |
| Backplane base sockets | **Samtec `SSW-139-01-S-S`** | 1x39 vertical female, 2.54 mm, 30 microinch gold, 8.51 mm body. |
| Backplane extension sockets | **Samtec `SSW-110-01-S-S`** | Same construction, 1x10. |
| Video bulk capacitor | **Panasonic `ECA-1HM470`** | 47 uF/50 V polarized radial, 6.3 x 12.2 mm, 2.50 mm lead pitch. |

Substitution requires checking the drawing, changing the MPN and footprint together,
rerunning the negative controls, and repeating R5.V6. Similar-looking HD15 connectors
are specifically not drop-in substitutes.

## Socket set

All U1-U23 packages are socketed for first-article repair and GAL iteration. The
oscillator's standard four corner pins fit the 14-position grid. The selected open-frame
TE Diplomate sockets are:

| Package | Quantity | Socket MPN |
|---|---:|---|
| DIP-14 / oscillator grid, 7.62 mm rows | 6 | `1-2199298-3` |
| DIP-16, 7.62 mm rows | 10 | `1-2199298-4` |
| DIP-20, 7.62 mm rows | 3 | `1-2199298-6` |
| DIP-24, 7.62 mm rows | 3 | `1-2199298-8` |
| DIP-32, 15.24 mm rows | 1 | `1-2199300-2` |

The checker derives these quantities from `video.board.json`; a socket cannot disappear
from the purchasing list when a package changes.

## VGA land-pattern decision

The checked-in `VJUGA.pretty/NorComp_200-015-213L537.kicad_mod` transcribes NorComp
drawing `200-015-213LYYY` revision 5:

- 15 signal holes at 0.70 mm with 1.00 mm pads (0.15 mm annular ring), arranged as
  the drawing's staggered 7+8 solder-tail rows; a local 0.15 mm clearance is required
  to escape the 1.524 mm same-row pitch while ordinary card routing remains 0.20 mm;
- 1.50 mm row separation, 0.762 mm stagger, and 10.668 mm total X span;
- two 2.10 mm NPTH board-lock holes on 16.00 mm centres, tangent to the specified
  edge as drawn; the selected hardware has no separate electrical shell terminal;
- PCB edge 2.50 mm from the top signal row and mating face 5.80 mm beyond that edge;
- 30.81 mm shell width plus a 0.25 mm courtyard clearance.

The existing generic KiCad HD15 candidates use three PCB rows and different mounting
geometry. The footprint self-test deliberately feeds one of those candidates to the
guard and requires rejection.

## Bus placement consequence

Every card uses Samtec right-angle male headers; backplane slots use vertical
female sockets. Mating posts face out through the card edge, the base
header is front-side, and the shorter extension header is back-side so their bodies do
not occupy the same volume. Corresponding backplane rotations preserve pin numbering.
The PCB generator anchors connector **pad-row centres** to `mating.json`; centring an
asymmetric right-angle body would otherwise move the mating row several millimetres.

## Power contract and machine gate

`ECS-100A-251.7` may draw 70 mA in its 25.175 MHz band. The Video budget is
686 mA and the complete five-card budget is 1655 mA, leaving 345 mA / 17.25%
headroom against the 2 A design limit. The barrel jack is the sole power input;
USB-TTL is data-only. Supply receipt limits and routed voltage-drop evidence
are in the [five-card power contract](rev-b-five-card-power.md).

## Verification

The parts checker pins 14 part groups, derives the 23-socket quantities, checks
selected package/connector geometry against library footprints, and reconciles
the oscillator current with the power model. Its two negative controls alter
the socket quantity and VGA footprint selection. It checks that sourcing fields
are present, but does not fetch drawings or confirm live inventory. Routed
placement and assembled clearances are covered by the separate
[PCB](rev-b-video-pcb.md) and [mating](rev-b-mating-report.md) checks.

Run from the repository root with the KiCad footprint library installed:

```sh
. spinoffs/minimal-vga/kicad/revb/env.sh
for card in mem io cpu backplane video; do
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_footprints.py "$card"
done
python3 spinoffs/minimal-vga/kicad/revb/check_revb_footprints.py video --self-test
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_parts.py --self-test
```

`check_revb_footprints.py` resolves and **rewrites** `footprints.<card>.json`;
review any resulting diff. It exits successfully with `SKIP` if
`KICAD_FOOTPRINTS` is unavailable. The Video parts checker requires those maps
and the relevant library files; missing files fail verification.

Primary drawings: [NorComp 200-series HD15](https://content.norcomp.net/rohspdfs/Connectors/2YY/200-015-213LYYY.pdf),
[ECS-100X oscillator](https://ecsxtal.com/store/pdf/ECF-100X.pdf),
[Alliance AS6C1008](https://www.alliancememory.com/wp-content/uploads/pdf/AS6C1008_Mar_2023V1.2.pdf),
[Microchip ATF22V10C](https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/doc0735.pdf),
[Samtec TSW](https://www.samtec.com/products/tsw),
[Samtec SSW](https://www.samtec.com/products/ssw), and
[TE DIP sockets](https://www.te.com/content/dam/te-com/documents/consumer-devices/global/dip-socket-en.pdf).
