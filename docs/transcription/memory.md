# Transcription — Memory subsystem (Sheet 1, right)

Confidence tags as in `cpu-core.md`: **[scan]** read off the drawing, **[?]** to verify.

## Headline: the memory map is a decode PROM, not an 8255 "memory_view"
MAME abstracts banking as a 4-mode `memory_view` selected by 8255#0 Port C. The
**real board decodes the map with a bipolar PROM**:

- **D6 = К556РТ4** (256×4 bipolar PROM), the address-map / bank decoder. [scan]
  - **Inputs = the high address byte A8–A15** (traced): [scan]
    PROM A0(pin5)←A15, A1(6)←A14, A2(7)←A13, A3(4)←A12, A4(3)←A11,
    A5(2)←A10, A6(1)←A9, A7(15)←A8. ⇒ map decoded at **256-byte page** resolution.
  - Outputs: **ROM** = D0/pin12, **RAM** = D1/pin11, **REV** = D2/pin10,
    **ROE** = D3/pin9 (ROM output enable). Pull-ups R11, R12 (1k) on ROM/RAM. [scan]
  - Enables **V1=13, V2=14** (tied together) ← driven by gate **D7 (ЛА3)** output
    pin 11. [scan] So the banking path is: **mode/control → D7 (ЛА3) → PROM V1/V2
    enable → switches the decode map** (RAM-under-ROM). D7 inputs (pins 12,13) =
    the mode + a strobe — **trace next** [?] to confirm the 8255 Port C link.
  - NB: **D7 is a ЛА3 gate**, not the low-byte address buffer (the CPU-core spec's
    "D7" buffer placeholder was renamed **DLB**; the low buffer's real refdes is TBD).
- The map *truth table* lives in the **PROM contents** — NOT on the schematic.
  That's why the effective map (ROM@0x0000 in mode 0, RAM-under-ROM, etc.) had to
  be recovered from the **emulator trace / MAME**, and they agree. The schematic
  gives the *mechanism*; the emulator gives the *contents*.
- Implication: the 8255 Port C "mode" is an **input to this PROM** (combined with
  address), not a direct view-switch. Reconciles with MAME's behavioral result.

## Memory chip inventory
Socketed chips (Sheet 1 note): **D2, D6, D8, D15…D22**. [scan]
- **D6** = К556РТ4 decode PROM (above).
- **D2, D8** = ROM/EPROM (socketed) — types/role TBD [?].
- **D15–D22** = EPROM array, **8K×8 (К573РФ4-class, 2764 pinout)** [scan]:
  A0=10, A1=9, A2=8, A3=7, A4=6, A5=5, A6=4, A7=3, A8=25, A9=24, A10=21, A11=23,
  A12=2; **CS=20, OE=22**; D0–D7. Address ← buffered bus, data → DB, CS ← decode
  selects, OE ← ROE. R21–R28 (1k) bus pack. [scan]
- **RAM**: К565РУ5 (64K×1 DRAM) array, **refdes from D60** (Sheet 2). [scan]
  One chip per data bit; multiplexed address A0–A7 = pins 6,12,13,5,10,7,11,9;
  **RAS=R, CAS=15, WE=3, DIN=2, DOUT=14**. Shared RAS/CAS/WE + multiplexed
  address (μP-vs-video mux) across the array; per-chip DOUT/DIN = one bus bit.
  20 chips ⇒ bank/video split (exact bit↔chip↔bank mapping to trace).

## A5 hardening — address mux + video counters (scan)
- **КП14 muxes D48/D49**: A-inputs = μP address (BA), B-inputs = video counters,
  Q-outputs → РУ5 muxed address (MA); select via the E13 strap. [scan]
- **ИЕ7 counters D44–D46** cascade (CO chain) → mux B-inputs (video address). [scan]
- Flipped to `scan` (bit-parallel per КП14/ИЕ7 datasheet): **BA0–7** (μP-addr → mux),
  **MA0–7** (mux → РУ5), **VCTRLO/HI**, **CO0–2**. Provenance **47 → 74/99**.
- Remaining DRAM piece: **RAS/CAS** (reported D53 ИД7 + R49–R52, not personally
  confirmed) + the РУ5 RAS/CAS-gating/refresh — intricate DRAM-controller timing.

## Boundaries closed (full model)
- **Full 20-chip РУ5 array** modeled: bank0 D60–67 + bank1 D68–75 (on DB) + video
  plane D76–79 (on VD). Bank/video org assumed; all share the muxed MA + RAS/CAS.
- **Address mux closed**: D48/D49 (КП14) drive MA; D53 (ИД7) drives RAS/CAS;
  video counters D44–47 (ИЕ7) feed the mux. No more MA/RAS/CAS boundary.
- **Clock** (D59/D35/D38) → CPU Φ1/Φ2 + 8238 STSTB; **I/O decoder** (ИД7 DID7) →
  all I/O chip-selects. New chips scan-identified; their pinouts/decode wiring are
  placeholder/assumed (provenance-tagged). Full board: **52 chips, 99 nets, IN SYNC.**

## Banking mechanism — summary (scan)
```
A8..A15 ──► D6 (К556РТ4 PROM) ──► ROM / RAM / REV / ROE selects
                  ▲ V1,V2 (enable)
                  │
        D7 (ЛА3 gate) ◄── 8238 (D5) control outputs (MRD/MWR/IORD region) + mode line
```
So RAM-under-ROM banking is **PROM-decode gated by D7**, combining the 256-byte
page decode with read/write strobes (and the mode). This is the real mechanism
behind MAME's behavioral 4-mode `memory_view`. D7 (ЛА3) has ≥2 NAND sections
(pins 12,13→11 drives the PROM enable; 9,10→8 another). Exact mode-bit cross-sheet
route from the 8255 Port C still to trace [?].

## Modeled in HDL + LVS-green (option A outcome)
`hdl/juku_top.v` now instantiates the memory chips: **decode_prom (D6)**,
**la3_gate (D7)**, **8× eprom_8k (D15–D22)**, **ram_64k (DRAM, abstracting the
РУ5 array)**, wired to the buffered BA bus / system DB bus / decode selects.
Board spec + map extended to match → **LVS IN SYNC, 15 chips / 57 nets**.

Provenance: **28/57 scan-grounded** (CPU-core internals + decode mechanism: D6
PROM in/out, D7→PROM_EN), **29/57 assumed** (buffered-bus bit-order, EPROM/DRAM
bus + chip-selects not individually traced; DRAM abstracted). The structure is
verified; the bus wiring is the harden-later target.

## A2 hardening — EPROM bus (scan)
- EPROM array (D15, D17, …) = **2764-class** (A0–A12, D0–D7, CS=20, OE=22). [scan]
- **Address** A0–A12 ← buffered bus straight (series pack **R21–R28 1K** on the low
  lines); **data** D0–D7 ↔ DB straight. ⇒ `BA8–12` flipped to **scan**. [scan]
- **Chip-selects = CS4 / CS5 / CS6 / CS7** (4 lines, cross-sheet `(2)(3)` — from the
  memory decoder, not a single ROM line); **OE ← ROE** (from D6). [scan]
- **8238 (D5) data pins → standard 8228 datasheet** (D0=15…D7=11; DB0=14…DB7=12);
  control already matched the scan. CPU-side `DC` + system `DB` nets now grounded.
- **РУ5 bit-order confirmed on scan**: D60→DB0, D61→DB1, … (read the `DØ/DB1/DB2`
  labels on the DO pins) — bit-sliced, one chip per DB bit. ⇒ **`DB0–7` flipped to scan.**
- **A2 done** (memory address+data buses): provenance **36 → 44/99**.
- *Remaining (cross-sheet, folds into the decoder trace A4):* the EPROM **chip-selects
  CS4/CS5/CS6/CS7** come from a decoder on another sheet — `ROM_SEL`/`ROE` stay `assumed`.

## TODO (next passes)
1. Trace D6 (РТ4) input lines: which buffered address bits + the Port C mode bit.
2. Identify ROM/EPROM refdes + their CS/OE ← ROM/ROE; data → DB bus.
3. РУ5 DRAM array: address mux (μP vs video address — see Sheet 2 "VIDEO ADDRESS /
   μP ADDRESS"), RAS/CAS, WE ← RAM/MWR.
4. Model the decode PROM in HDL (as a chip with its select outputs) + LVS;
   keep the PROM *contents* sourced from the emulator-derived map.

## Physical board ground-truth (from the owner + the juku3000 archive)
Confirmed against the **real PCB** + the `juku3000` documentation archive (full ES101
schematic set, assembly/placement drawing ДГШ5.109.006 СБ, component list ДГШ3.031.006 ВП,
286-page service manual):
- **ROM: 8 sockets on the board, 2 populated** — **2× M2764** (8K×8) = the 16 KB BIOS.
  (Our model's 8 EPROM = the 8 sockets; only D15/D16-equivalent are populated.)
- **RAM: 32 sockets (4 banks × 8), 8 populated** — **8× К565РУ5Г** = one 64K×8 bank = the
  real 64 KB. The other 24 are bank-expansion sockets (→ up to 256 KB), unsoldered.
- **There is NO separate video-RAM plane.** The earlier "video plane D76–D79" was an
  assumption — video reads the *same* 64 KB bank via the КП14 µP/video mux. (Model's
  D68–D79 are unpopulated sockets, not a plane.)
- **Four small decode/timing PROM-class parts remain relevant:** **2× К556РТ4**
  (D6 memory decode plus D2 bus-arbitration/wait PROM, dump pending) **+ 2×
  К155РЕ3** (ROM paging/timing-state PROMs, including D8 and D94). D6 and D8 have
  boot-validated reconstructed fallbacks; D2, D94, and video/DRAM timing truth
  remain **pending a PROM dump / programming-disk table**. See
  `reconstructed-prom-fallbacks.md` and `dram-video-timing.md`.
- **Implication:** the functional model should converge to the *populated* set (2 ROM +
  8 RAM, one bank); the 8/32 sockets + expansion are a Phase-B (PCB) layout fact. A
  deliberate restructure (reduce over-modeled memory, add the ~42 still-unmodeled glue/
  bus/video chips toward the real 76) is the next structural pass.
