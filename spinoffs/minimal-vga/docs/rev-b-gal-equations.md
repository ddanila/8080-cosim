# VJUGA rev B — five-GAL release contract

Status: **R5.P1 + R5.V3 implemented and reproducibly compiled 2026-08-28**.

The authoritative sources and generated programming artifacts are in
`pld/revb/`. The selected first-article identities are Microchip
`ATF22V10C-15PU` for Memory U3 and Video U5/U6/U7, and `ATF16V8B-15PU` for I/O
U2. Their generic GAL22V10/GAL16V8 JEDEC maps are
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

## Video U5/U6/U7 — timing, frame divider and arbitration

`video-hdec-u5.pld` decodes the complete 0..799 horizontal sequence: active
dots 0..639, negative sync 656..751 and asynchronous clear at 800. Each
16-dot byte has a four-dot `FETCH` window at phases 12..15, followed by the
phase-0 shifter load and one-dot visible-region `BYTE_TICK`. Dot 784 reloads
the scan counter from row base; dot 640 emits `RB_STROBE`.

`video-vdec-u6.pld` decodes lines 0..524, negative sync 490..491, active lines
0..479 and clear at 525. Its pin 1 is the ATF22V10 global clock, driven once per
line by `RB_STROBE`. Three registered macrocells implement the self-recovering
sequence 0,1,2,3,4,5,0 at line 524; all other line clocks hold state. Thus
`FRAME_TICK` is high for about 25.4 us on line 524 of every sixth VGA frame,
9.99 Hz nominal. A CPU-clock change requires replacing this modulo-N equation,
rebuilding U6 and rerunning both equation and integrated-boot gates.

`video-ctrl-u7.pld` owns D800-FFFF only in modes 0 and 3. Scanout owns address,
SRAM OE and framebuffer data during `FETCH`; outside it, a selected CPU read or
write owns the path. A collision enables a constant-low tri-state macrocell on
`WAIT_N`, giving an open-drain output against the backplane pull-up. OE and WE
cannot assert for the CPU until `FETCH` falls, and reset disables both owners.
An unconnected U7 pin 23 supplies internal `CPUACC` feedback only.

The checker evaluates every distinguishable input: all 1024 H/V counter states,
all eight divider states, reset polarities, all 32 address classes, four modes,
read/write/idle cycles and both fetch phases. Simulation additionally forces a
real FETCH collision, proves the write lands, checks exact six-frame spacing,
and boots EKTA through the TTL card byte-identically to cosim.

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
| Video H-decode U5 | `224e88c3c76a585ed1893665e7333883a6d0fbfebc9dd4bcef8b1d5d43045153` | 5892 | 81ED |
| Video V-decode U6 | `4884fb645b412a51159560886341c17630aff165e492e08ed0008ed32305675f` | 5892 | 1DA2 |
| Video control U7 | `0668bcd86c9e7bb59e3e4b99576794c14ac3a676086a89bffd20a260ca3a5d95` | 5892 | 8809 |

The build regenerates `.jed`, `.pin`, `.fus` and `.chp` in a temporary directory
and byte-compares them with the tracked artifacts. The checker independently
matches every PLD pin to the generated board models, evaluates the complete
Memory and I/O oracles, and exhausts the Video equations and registered state.

## Programming and readback

1. Remove the GAL from VJUGA and select the exact target (`ATF22V10C` or
   `ATF16V8B`) in a programmer that explicitly supports it. Never program
   in-circuit.
2. Match board/reference and file exactly: Memory U3 `memory-u3.jed`, I/O U2
   `io-u2.jed`, Video U5 `video-hdec-u5.jed`, Video U6 `video-vdec-u6.jed`, or
   Video U7 `video-ctrl-u7.jed`. Load only that file; leave security/fuse-lock
   disabled for the first article. Run blank check, program, programmer verify,
   then save a readback JEDEC if the programmer supports it.
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
