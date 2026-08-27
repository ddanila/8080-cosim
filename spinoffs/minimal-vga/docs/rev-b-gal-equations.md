# VJUGA rev B — Memory and I/O GAL release contract

Status: **R5.P1 implemented and reproducibly compiled 2026-08-28**.

The authoritative sources and generated programming artifacts are in
`pld/revb/`. Both devices use purely combinatorial logic. The selected first-
article identities are Microchip `ATF22V10C-15PU` for Memory U3 and
`ATF16V8B-15PU` for I/O U2; their generic GAL22V10/GAL16V8 JEDEC maps are
compiled by pinned Galette 0.3.0 revision
`af529870729b1da8794b002cd522f5bf2d53f230` with Rust 1.85.0.

## Memory U3 — full four-mode overlay

| Pin | Signal | Dir | Pin | Signal | Dir |
|---:|---|---|---:|---|---|
| 1 | `MREQ_N` | in | 13 | NC | in |
| 2 | `RD_N` | in | 14 | `ROM_CE_N` | out |
| 3 | `WR_N` | in | 15 | `RAM_CE_N` | out |
| 4–6 | A13–A15 | in | 16 | `MEM_RD_N` | out |
| 7–8 | MODE0–MODE1 | in | 17 | `MEM_WR_N` | out |
| 9–10 | A11–A12 | in | 18–23 | NC | out |
| 11 | NC | in | 24/12 | VCC/GND | power |

`memory-u3.pld` implements the complete machine map, not the former mode-0-only
bring-up shortcut:

| Mode | ROM | Memory-card SRAM | Other owner |
|---:|---|---|---|
| 0 | 0000–3FFF | 4000–D7FF | Video D800–FFFF |
| 1 | D800–FFFF | 0000–D7FF | — |
| 2 | D800–FFFF | 0000–3FFF, C000–D7FF | empty cartridge 4000–BFFF |
| 3 | — | 0000–D7FF | Video D800–FFFF |

The eight SRAM product terms fit pin 15's ten-term macrocell. The exhaustive
checker evaluates every address in all four modes, proves ROM/SRAM exclusion,
and confirms the D800 ownership boundary. `revb_mem_card.v` uses the same full
map; its old mode-0-only internal decode is retired.

The physical 27C256 receives CPU A0–A14 directly. Therefore the 16 KiB source
image is duplicated into both halves of `ekta37_z80-27c256.bin`: mode-0 reads
the lower copy, while D800–FFFF reads physical 5800–7FFF and obtains the intended
source 1800–3FFF bytes from the upper copy.

## I/O U2 — complex-mode-safe pinout

| Pin | Signal | Dir | Pin | Signal | Dir |
|---:|---|---|---:|---|---|
| 1 | `IORQ_N` | in | 11 | `PIC_INT` | in |
| 2–7 | A2–A7 | in | 12 | `PIC_CS_N` | out |
| 8 | `RESET_N` | in | 13 | `PPI_CS_N` | out |
| 9 | `M1_N` | in | 14 | `UART_CS_N` | out |
| 10 | GND | power | 15 | `IO_RESET` | out |
|  |  |  | 16 | `INT_N` | open-drain output |
|  |  |  | 17 | `INTA_N` | out |
|  |  |  | 18–19 | NC | I/O/output |
|  |  |  | 20 | VCC | power |

The earlier board draft put `PIC_INT` on pin 19. That cannot compile in
ATF16V8 complex mode because pins 12 and 19 are output-only. U2 does not need
RD/WR to form any equation, so `M1_N` and `PIC_INT` now use dedicated array
inputs 9 and 11. `INT_N` drives zero only while `PIC_INT` is asserted and is
otherwise high impedance, preserving the backplane's wired-OR interrupt rule.
The select windows are PIC 00–03, PPI 04–07 and UART 08–0B; peripheral A0/A1
choose registers inside each four-port window. `IO_RESET` is active-high and
`INTA_N` asserts only while both `M1_N` and `IORQ_N` are low.

## Rebuild and verification

Install the pinned compiler once, then reproduce all tracked outputs:

```sh
spinoffs/minimal-vga/pld/revb/bootstrap_galette.sh
spinoffs/minimal-vga/pld/revb/build_revb_gals.sh
python3 spinoffs/minimal-vga/roms/build_revb_rom.py --check
```

`manifest.json` freezes each source/output SHA-256, byte count, JEDEC fuse count
and JEDEC checksum. The checked release values are:

| Device | JEDEC SHA-256 | QF | JEDEC checksum |
|---|---|---:|---|
| Memory U3 | `dbbe74d99400718f2d743b7e02a33291dc1efac68805ea0dd75830b84d06d363` | 5892 | 6806 |
| I/O U2 | `703412427efff890ebfc0e7d430b4a7cf016f3abdc9ad2f90bc3d9aac980e6e7` | 2194 | 3676 |

The build regenerates `.jed`, `.pin`, `.fus` and `.chp` in a temporary directory
and byte-compares them with the tracked artifacts. The checker independently
matches every PLD pin to `mem.board.json`/`io.board.json`, evaluates the full
Memory address oracle, exercises all 256 I/O ports, checks reset and acknowledge
polarity, and confirms the interrupt output's low/Hi-Z contract.

## Programming and readback

1. Remove the GAL from VJUGA and select the exact target (`ATF22V10C` or
   `ATF16V8B`) in a programmer that explicitly supports it. Never program
   in-circuit.
2. Load the matching `.jed`; leave security/fuse-lock disabled for the first
   article. Run blank check, program, programmer verify, then save a readback
   JEDEC if the programmer supports it.
3. Power-cycle the programmer, read again, and compare the readback fuse count
   and checksum with the table/manifest. Record device marking, programmer,
   software version and result in `rev-b-b1-bench-log.md`.
4. With power removed, insert the verified parts with pin 1 matching the socket
   and silkscreen. Run the observation-header decode checks before fitting the
   remaining cards.

Programmer verify is required but does not replace the independent readback and
bench decode checks.

## Primary sources

- [Microchip ATF22V10C product/datasheet](https://www.microchip.com/en-us/product/atf22v10c)
- [Microchip ATF16V8B product/datasheet](https://www.microchip.com/en-us/product/ATF16V8B)
- [Galette source and file-format documentation](https://github.com/simon-frankau/galette)
- [Rustup manual installation and archive checksums](https://rust-lang.github.io/rustup/devel/installation/other.html)
