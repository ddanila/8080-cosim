# VJUGA rev B — order-readiness note (TG.4)

> **SUPERSEDED ORDER TARGET (2026-08-27).** This is the preserved validation
> record for the former four-board-first proposal. Do not upload its ZIPs. The
> active target is one complete five-board system, including VGA and hardened
> TTL serial, controlled by `rev-b-five-board-order-plan.md`.

State of the four rev B B1 boards for bare-PCB fabrication. **All four boards are
historical order candidates after the 2026-08-08 regeneration and validation described below.**
TH.1–TH.4 closed the backplane hold: non-DIP footprints pinned to exact parts + a
physical-contract guard (TH.1/TH.2, D1.36), input power conditioning added (TH.3,
D1.35), and three real defects fixed along the way (SMD USB-C, reversed LED, missing
reset pull-up). **T1.10 is no longer authorized.** Last updated 2026-08-27.

## Boards

| board | size (mm) | layers | first-article build qty | notes |
|---|---|---:|---:|---|
| cpu | 100 × 70 | 2 | 1 | Z80 + clock + diag; unbuffered (D1.21) |
| mem | 100 × 60 | 2 | 1 | ROM + SRAM + GAL decode |
| io | 100 × 100 | 2 | 1 | 8251 UART + GAL; B3 parts footprinted DNP (D1.26) |
| backplane | 100 × 100 | 2 | 1 | 5 slots + power entry/reset/serial; cheap-tier layout per D1.37 |

All four pass `check_revb_drc.py --total` at **0 violations / 0 unconnected**, obey the
mechanical mating contract (`check_revb_mating.py`), and boot byte-identical to cosim in
the digital twin (`revb_tier_suite.sh`).

The table describes one assembled first-article set. A PCB vendor may impose a larger
minimum panel/order quantity; leave surplus boards unpopulated and do not treat them as
released duplicates until the first set passes T1.11.

## Physical interface and backplane BOM — pinned parts (TH.1 / D1.36)

Every backplane footprint checked against a real part's datasheet; the footprint
physical-contract guard (`check_revb_footprints.py`, TH.2) enforces through-hole pad
count, drill, and pitch so a wrong/SMD footprint can't slip through again.

**Mating interface (the contract):**
- **Per card:** 1× right-angle male 1×39 (base bus) + 1× right-angle male 1×10 (ext),
  0.1″ pitch, on the bottom (mating) edge — base row 4 mm from the edge, ext row 9 mm.
  (The 1×39/1×10 KiCad footprints are vertical, but a right-angle header has the identical
  hole pattern — the PCB is correct for either; buy right-angle.)
- **Backplane slots:** 5× (female 1×39 + female 1×10) 0.1″ SIL sockets, base x=50 /
  ext x=14.45, 16 mm pitch.

**Backplane discretes (all through-hole):**

| Ref(s) | Value / part | Footprint | Notes |
|---|---|---|---|
| J_USBC | **GCT USB4085** USB-C receptacle | `USB_C_Receptacle_GCT_USB4085` | **datasheet-verified** (GCT_usb4085.pdf): THT "Dip Type", VBUS=A4/A9/B4/B9, GND=A1/A12/B1/B12+shell, CC1=A5, CC2=B5; data pins float (power-only). 5 A VBUS rating. 0.85 mm pitch → 0.15 mm fab clearance |
| F_VBUS | Bourns **MF-R110** PTC (1.1 A hold / 2.2 A trip, 30 V) | `Fuse_Bourns_MF-RG300` | **datasheet-verified** (mf_r.pdf): 5.1 mm lead pitch = footprint pitch, 0.51 mm leads; USB VBUS branch only |
| C_BULK | 47 µF / 16 V radial electrolytic | `CP_Radial_D6.3mm_P2.50mm` | rail bulk |
| C_IN, C_RST | 100 nF disc ceramic | `C_Disc_D5.0mm_P5.00mm` | HF bypass / reset RC |
| U_RST | **DS1813-5** reset supervisor, TO-92 | `TO-92_Inline` | **datasheet-verified pinout** (ds1813.pdf p1): pad 1 = /RST, pad 2 = VCC, pad 3 = GND; open-drain with internal 5.5 kΩ pull-up |
| R_RST | 10 kΩ axial | `R_Axial_DIN0207_P7.62` | RESET_N pull-up (required for open-drain supervisor + button) |
| SW_RST | **APEM MJTP1243** 6 mm tactile (SPST, 2-terminal) | `SW_PUSH_..._APEM_MJTP1243` | reset button |
| R_M0, R_M1 | 10 kΩ axial | `R_Axial_DIN0207_P7.62` | MODE default-low pulls |
| R_INT/WAIT/NMI/BRQ | 4.7 kΩ axial | `R_Axial_DIN0207_P7.62` | wired-OR bus pull-ups |
| R_CC1, R_CC2 | 5.1 kΩ axial | `R_Axial_DIN0207_P7.62` | USB-C CC sink advertise |
| R_LED | 2.2 kΩ axial | `R_Axial_DIN0207_P7.62` | LED series |
| D_PWR | 5 mm THT LED | `LED_D5.0mm` | pad 1 = cathode → GND, pad 2 = anode |
| J_PWR | 1×2 0.1″ header | `PinHeader_1x02` | bench-supply input (unfused) |
| J_FTDI | 1×4 0.1″ header | `PinHeader_1x04` | bring-up serial console |
| JP_S5 | 2×2 0.1″ header + shunts | `PinHeader_2x02` | FTDI↔bus crossover jumper |

## Power budget (re-checked against the final BOM)

Unchanged from the bus contract's B1-population estimate: **~712 mA** worst-case, **~47 %**
of a 1.5 A USB-C source (under the 60 % / 0.9 A headroom rule). The backplane discretes
(reset supervisor ~5 mA, power LED ~2 mA, pull-ups + CC resistors ≈ 1 mA each) are
negligible. The new **F_VBUS polyfuse (MF-R110, 1.1 A hold / 2.2 A trip)** sits comfortably
above the 712 mA draw and below the USB budget — it protects the USB host from a board
short without nuisance-tripping. Bench-supply (J_PWR, unfused) remains the safe primary
bring-up input (no PD negotiation — don't assume the full 1.5 A from an arbitrary host).

## Fab package

`kicad/revb/export_fab.sh` first requires PCB content checks and total DRC 0/0, then
writes the exact seven production Gerbers (two copper, two mask, two silk, outline) plus
Gerber job and Excellon drill per board to `fab/minimal-vga/revb/package/<card>/`
(untracked, D1.25) and zips each. `check_revb_package.py` verifies the exact file set,
safe archive paths, ZIP/export byte identity, two-layer job metadata and dimensions,
Gerber X2 markers, Excellon tools/hits, and writes `manifest.json` + `SHA256SUMS`.
The final `check_revb_package.py --require-recorded` gate also requires the current
hashes in this note and the order/bench record. Fresh package hashes from the
2026-08-08 pre-order run are:

| package | sha256 (snapshot) |
|---|---|
| mem.zip | 898308402f75ef4864ce598b2ef2177763199e8c972e8fd37b3c2dcb68bf7408 |
| io.zip | 5cafb5b686e9904dbb7a86848c8618171f3a2fc02a5c79760bd3084c7e422de4 |
| cpu.zip | cc5f1d58906125625247d93cd7c686f0ca6afbb966e5b952aabc5f2b9a9ccc70 |
| backplane.zip | 692ef44f186f987fa339644f528cf621435bd180f7a7f4ca01df6e27d9ca84a1 |

> **Fab capability:** the USB-C connector (0.85 mm pitch) needs **0.15 mm (6 mil) min
> clearance** at that footprint — standard for JLCPCB/PCBWay etc.; the rest of the board
> is 0.2 mm. Re-exported with KiCad 9.0.8 on 2026-08-08 after fresh generation/routing.
> Footprints are machine-checked for DIP row spacing (`PKG_WIDTH`) and non-DIP
> through-hole/drill/pitch (`PKG_PHYS`); the negative self-test proves that the known
> wrong 300-mil DIP-28 and SMD USB-C alternatives are rejected.

## Open risks to weigh before ordering

**Every backplane part is datasheet-verified** (footprints cross-checked against the
manufacturer drawings — DS1813, USB4085, MF-R110 fetched 2026-07-18); no
name-matched-only backplane part remains. The B1 logic ICs must be bought to the DIP
width/class recorded in the board specs and footprint guard. Remaining items are
inherent, not open geometry questions:

- **USB-C fab clearance:** needs 0.15 mm at the connector (standard cheap-fab capability,
  noted above). Fine-pitch USB-C is also a bit fiddly to hand-solder (flux + fine iron);
  the all-through-hole GCT USB4085 was chosen to keep it possible.
- **Buy the exact parts named in the BOM** — the footprints are committed to copper for
  these specific MPNs (esp. DS1813-5's pinout and the USB4085 / MF-R110 geometry).

- **Keying is convention-only (D1.32b):** a reversed card can seat (centred base is
  symmetric). Mitigation is silk/orientation marks + care, not a mechanical block. The
  blocking-post option (D1.32a) is held in reserve for after bench experience.
- **Five slots, no spare:** D1.37 traded the unused sixth expansion slot for a
  100×100 cheap-tier backplane. The complete planned CPU/Memory/I/O/Video/FDC system
  fits, but another simultaneous card would require a second/revised backplane.
- **Slot pitch 16 mm** is tighter than mainline RC2014 (~20 mm). FreeCAD clearance is a
  conservative 4.16 mm; confirm on the bench (T1.11) before committing to many boards.
- **Routing is freerouting-stochastic** (D1.33/D1.34): the pipeline reliably *reaches*
  0/0 but does not reproduce byte-identical copper; the `.kicad_pcb` is the artifact of
  record. The backplane routes fully via freerouting (D1.34 — the locked bus-column
  pre-routes were retired: the specctra roundtrip mangled them; the clean-slate board
  routes 0/0 on attempt 1).
- **Digital twin does not cover signal integrity / bus timing** — VJUGA is slow (few
  MHz), low risk, but this is a bench-validated assumption, not a proven one.

## What ordering unblocks

T1.11 bench bring-up (hardware-blocked): populate cpu/mem/io per the DNP staging,
flash the bring-up ROM, and confirm the banner / RAM-PASS TX stream against the twin.
Record the vendor preview and every staged result in `rev-b-b1-bench-log.md`.
