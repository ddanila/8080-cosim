# FDC quadrant scaffold (grind C, 2026-07-04)
The .009 revision's floppy subsystem, netted to the extent the desk sources allow.

## Netted (this pass)
- **D93 КР1818ВГ93** (WD1793 pinout): CS(3) <- D9.Y7 [the sheet-3 CS7 delta: io 0x1C],
  RE(4) <- IORD, WE(2) <- IOWR, A0/A1 <- BA0/BA1, DAL0-7 <- D100 B-side,
  DDEN(37) <- D26.PC4 [MAME], INTRQ(39) -> D10.IR0 [assumed], DRQ(38) -> D10.IR1 [assumed].
- **D100 КР580ВА87** (8287): A-side <- DB0-7, B-side -> FDC_DAL0-7. OE/T gating [assumed
  boundary -- likely CS_FDC + IORD-derived].
- **D94 К155РЕ3** (`ДГШ5.106.092`, dump pending): A0-A4 <- BA11-15 (same
  convention as D8); enable/output destinations and contents remain unknown
  [owner/programming disk]. Do not use the scanned `.113` table here; later
  reconciliation identifies `.113/.117` as `.106.103`-family evidence, not D94.
- HDL: inert stubs (never drive DAL/DB/IRQ) -- boot stays byte-identical; connectivity
  is the deliverable. PIC grew ir0/ir1 structural inputs.

## Factory FDD-cable evidence from Baltijets doc 009
`ref/baltijets-tech-docs/009 FDDs.pdf` confirms the external FDD unit uses a
standard Shugart-style 34-pin signal map:

| Signal | Pin |
|---|---:|
| INDEX | 8 |
| SEL0 | 10 |
| SEL1 | 12 |
| MOTOR ON | 16 |
| DIR | 18 |
| STEP | 20 |
| WRITE DATA | 22 |
| WRITE GATE | 24 |
| TRACK 0 | 26 |
| WRITE PROTECT | 28 |
| READ DATA | 30 |
| SIDE SELECT | 32 |
| READY | 34 |

Odd pins 1,3,5,7 / 9,11,13,15 / 17,19,21,23 / 25,27,29,31,33 are ground.
Drive power is +12 V on drive X1 pin 1, ground on pins 2/3, and +5 V on pin 4.
The drawing labels the drive as `НГМД ЕС 5323.01`.

## EKDOS media acquisition gate
The target media is tracked in `docs/ekdos-media-acquisition.md`: the factory
`JUKU-1` / `ДГШ5.106.105` EKDOS boot disk, now vendored as the MAME/Juku
raw-geometry image `media/disks/JUKU1.CPM`.

## Current EKDOS boot-path probe
`sync/ekdos_fdc_probe.py` drives the factory sequence from Baltijets doc 003:
`ROMBIOS 3.43` -> `*` -> `<T>, <D>, <D>` toward the `JUKU-1` EKDOS boot.
The current report is `docs/ekdos-fdc-probe.md`.

Current cosim result:

- ROMBIOS reaches the FDC path.
- WD1793 command/status port `0x1C` is written 6 times and polled millions of
  times.
- With no `EKDOS_PROBE_DISK` image selected, the data port `0x1F` is read 512 times,
  matching the first sector transfer size at the legacy register-echo boundary.
- Setting `EKDOS_PROBE_DISK=/path/to/image` passes that image through to
  `JUKU_DISK` and fails the report explicitly if the image is not a supported
  raw Juku disk size.
- Disk-backed runs now also require a left-margin EKDOS `A>` prompt bitmap in
  VRAM. The vendored `media/disks/J3KUTIL4.JUK` museum utility disk reaches
  `52K EKDOS 2.30` and `A>` in cosim.
- A stronger run with `https://arti.ee/juku/tarkvara/JUKU1.7Z` extracts the
  vendored `media/disks/JUKU1.CPM`
  (`SHA256 859b627d1439c4137f62b5f977ea7d99202e6874fc48c8b818341a38a0f8cd27`)
  and reaches `A>` through the factory `TDD` path.
- The HDL `juku_top` prompt path is now guarded in `docs/fdc-readiness.md`.

## Raw disk sector backend
`cosim/juk_disk.c` implements the raw MAME `FLOPPY_JUKU_FORMAT` geometry:
80 tracks, 10 sectors per track, 512-byte sectors, sector IDs 1-10, and either
one 409600-byte side or two 819200-byte sides. `sync/juk_disk_check.sh`
validates CHS-to-offset reads with synthetic disk images. See
`docs/juk-disk-format.md`.

## Disk-backed WD1793 cosim model
`cosim/juku_fdc.c` provides the first disk-backed WD1793 read-sector model for
the twin. The model maps the MAME/Juku FDC register window as command/status at
`0x1C`, track at `0x1D`, sector at `0x1E`, and data at `0x1F`. Port C follows
the MAME-derived FDC controls: PC2 motor enable, PC5 drive select, and PC6
side/head select.

The read-sector command class (`0x80`) loads one 512-byte sector through
`cosim/juk_disk.c` and streams it through the data register. The minimal model
also completes the ROMBIOS type-I restore/seek setup commands synchronously, so
an attached disk image can reach real sector transfers instead of sticking busy
before the first read. It is enabled when `JUKU_DISK=/path/to/image` is
set, preserving the default no-disk probe behavior. `sync/juk_disk_check.sh`
guards both the raw disk loader and this minimal FDC model with synthetic
images.

## HDL WD1793 synthetic-sector guard
`sync/fdc_check.sh` now guards the first HDL-side WD1793 behavior slice in
`hdl/devices.v`: restore, seek, Type-I step/step-in/step-out track updates,
read-sector, BUSY/DRQ status, side-select stream changes, motor-off NOT READY
behavior, and vendored `JUKU1.CPM` sector bytes. The guard is documented in
`docs/fdc-readiness.md`.

## Physical board handoff
`scripts/report_fdc_hardware_handoff.py` generates `docs/fdc-hardware-handoff.md`.
It guards the current board-JSON FDC handoff without promoting owner-only facts:
D93/D100 data-bus wiring, register select, I/O strobes, and CS7 decode are wired;
D93 INTRQ/DRQ ordering, D93 MR/CLK, and D100 OE/T remain owner-continuity points.

## Not netted (owner-session territory)
Support logic: D95/D101 (КП12 muxes -- drive/side select fanout?), D97/D99/D102 (АГ3
one-shots -- step/precomp timing), D96 (ТМ2), D28 (ЛН3), D98 (ЛП11 + the wires-17/18
reset chain), D106 (ИЕ7), D107? no -- D106 counter; the drive cable connector (X4/X5,
DB-26HD per photo); MR source; 1 MHz CLK rail; D100 OE/T; VT2/VT4 analog (write
precomp/pump).

## Owner measurement list (FDC)
1. D93.39/38 -> D10.18/19 (IR0/IR1) -- confirm which is INTRQ vs DRQ.
2. D93.19 (MR) source; D93.24 (CLK) rail (expect 1 MHz mesh tap).
3. D100.9/11 (OE/T) gating logic.
4. D94 output destinations (8 lines).
5. КП12/АГ3 pin wiring; processor-board/bracket mapping from the .009 board to
   the now-known 34-pin FDD unit signals.
6. Wires 17/18: D98.7 -> 220R -> reset switch chain.
