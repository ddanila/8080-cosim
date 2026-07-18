# VJUGA rev B — order-readiness note (TG.4)

State of the four rev B boards for fabrication. **All four boards are order-safe.**
TH.1–TH.4 closed the backplane hold: non-DIP footprints pinned to exact parts + a
physical-contract guard (TH.1/TH.2, D1.36), input power conditioning added (TH.3,
D1.35), and three real defects fixed along the way (SMD USB-C, reversed LED, missing
reset pull-up). **T1.10 (placing the order) is now a purchasing decision.** Last
updated 2026-07-18.

## Boards

| board | size (mm) | layers | qty | notes |
|---|---|---:|---:|---|
| cpu | 100 × 70 | 2 | 1 | Z80 + clock + diag; unbuffered (D1.21) |
| mem | 100 × 60 | 2 | 1 | ROM + SRAM + GAL decode |
| io | 100 × 100 | 2 | 1 | 8251 UART + GAL; B3 parts footprinted DNP (D1.26) |
| backplane | 100 × 120 | 2 | 1 | 6 slots + power entry/reset/serial; grown past 100×100 per D1.31/D1.35 (one-off) |

All four pass `check_revb_drc.py --total` at **0 violations / 0 unconnected**, obey the
mechanical mating contract (`check_revb_mating.py`), and boot byte-identical to cosim in
the digital twin (`revb_tier_suite.sh`).

## BOM — pinned to exact parts (TH.1 / D1.36)

Every backplane footprint checked against a real part's datasheet; the footprint
physical-contract guard (`check_revb_footprints.py`, TH.2) enforces through-hole pad
count, drill, and pitch so a wrong/SMD footprint can't slip through again.

**Mating interface (the contract):**
- **Per card:** 1× right-angle male 1×39 (base bus) + 1× right-angle male 1×10 (ext),
  0.1″ pitch, on the bottom (mating) edge — base row 4 mm from the edge, ext row 9 mm.
  (The 1×39/1×10 KiCad footprints are vertical, but a right-angle header has the identical
  hole pattern — the PCB is correct for either; buy right-angle.)
- **Backplane slots:** 6× (female 1×39 + female 1×10) 0.1″ SIL sockets, base x=50 /
  ext x=14.45, 16 mm pitch.

**Backplane discretes (all through-hole):**

| Ref(s) | Value / part | Footprint | Notes |
|---|---|---|---|
| J_USBC | **GCT USB4085** USB-C receptacle | `USB_C_Receptacle_GCT_USB4085` | fully THT (16 signal + 4 shield pins); power-only wiring, data pins float. 0.85 mm pitch → needs 0.15 mm fab clearance |
| F_VBUS | Bourns **MF-R110** PTC (1.1 A hold / 2.2 A trip) | `Fuse_Bourns_MF-RG300` | in the USB VBUS branch only; verify lead pitch vs footprint at purchase |
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

`kicad/revb/export_fab.sh` writes Gerbers + Excellon drill per board to
`fab/minimal-vga/revb/package/<card>/` (untracked, D1.25) and zips each. SHA256 of a
representative export (regenerable — KiCad embeds timestamps, so re-exports differ; the
board `.kicad_pcb` is the source of truth, content-checked):

| package | sha256 (snapshot) |
|---|---|
| mem.zip | 87f7a2d124ec8ecdc76cb8df02d4a7a79d49fb7b3a920b30b3d06036201f98e3 |
| io.zip | 9ea98eab72d5f0edb9f8b1a26266f4de70d1ac5b9b2b65a6c84bc0d21b0df78b |
| cpu.zip | 180a8f88ad9cde1612df43b3eaffbc23ca14997a985121a0c294defe7fdba226 |
| backplane.zip | 48dd20c3e423138cea605593d9a441a0d07f6ef5cf15e0f4116225a24884f74c |

> **Fab capability:** the USB-C connector (0.85 mm pitch) needs **0.15 mm (6 mil) min
> clearance** at that footprint — standard for JLCPCB/PCBWay etc.; the rest of the board
> is 0.2 mm. Re-exported 2026-07-18 after the pre-order audit fixed the DIP-28 width bug
> and the backplane order-safety issues (TH.1–TH.4). Footprints are now machine-checked
> for DIP row spacing (`PKG_WIDTH`) and non-DIP through-hole/drill/pitch (`PKG_PHYS`).

## Open risks to weigh before ordering

- **USB-C fab clearance:** needs 0.15 mm at the connector (standard cheap-fab capability,
  noted above). Fine-pitch USB-C is also a bit fiddly to hand-solder (flux + fine iron);
  an all-through-hole part (GCT USB4085) was chosen to keep it possible.
- **Reset supervisor — resolved:** the DS1813-5 TO-92 pinout is now datasheet-verified
  (ds1813.pdf: 1=/RST, 2=VCC, 3=GND) and soldered down with that mapping; the earlier
  header workaround is gone. The pull-up + RC + button still give a working reset if
  U_RST is left unpopulated. (Buy the **DS1813-5** specifically — the pinmap is committed
  to copper for that part.)
- **F_VBUS polyfuse lead pitch:** confirm the ordered MF-R110 matches the
  `Fuse_Bourns_MF-RG300` footprint pitch before soldering (guarded for drill, not exact
  pitch since PTC lead spacing varies).

- **Keying is convention-only (D1.32b):** a reversed card can seat (centred base is
  symmetric). Mitigation is silk/orientation marks + care, not a mechanical block. The
  blocking-post option (D1.32a) is held in reserve for after bench experience.
- **Backplane is 100 × 115** — past the 100×100 cheap-tier cliff. Deliberate (D1.31:
  grow the one-off backplane rather than drop slots or cramp the pitch). Cards stay
  ≤100×100.
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
