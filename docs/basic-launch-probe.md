# BASIC launch probe

Status: **BASIC RAM EXECUTION REACHED**

This probe exercises the configured monitor/removable-memory BASIC
command with `JUKU_KEYS=B`. By default it checks Monitor 3.3 with both
`roms/jbasic11.bin` and the legacy `ref/firmware/BAS0-3.HEX` image,
plus the EktaSoft 3.43m #0037 ROM used by the main boot guard. It complements
`sync/basic_cart_check.sh`,
which already proves the cartridge window wiring independently.

## Command

```sh
sync/basic_launch_probe.py
```

Environment overrides:

- `BASIC_LAUNCH_KEYS` default `B`
- `BASIC_LAUNCH_ROM` default unset (runs `jmon33.bin` and `ekta37.bin`)
- `BASIC_LAUNCH_CART` default unset (runs `jbasic11.bin` plus legacy `BAS0-3.HEX`; with `BASIC_LAUNCH_ROM`, both default cartridges are probed against that ROM)
- `BASIC_LAUNCH_REPORT` default `docs/basic-launch-probe.md`
- `BASIC_LAUNCH_MAX_CYCLES` default `120000000`
- `BASIC_LAUNCH_FRAME_CYCLES` default unset (`jmon33`: `200000`, `ekta37`: `40000`)

## Cartridge compatibility signals

| Cartridge | Bytes | SHA1 | First bytes | Entry jump | Strings |
| --- | ---: | --- | --- | --- | --- |
| `jbasic11.bin` | `8192` | `27e40395e8b49e2f9febf2b23773fbfe251befcf` | `c3 07 01 ba dc 00 20 c3` | `0x0107` | `BASIC`: 0x04A8; `READY`: 0x0471; `ERROR`: 0x0464 |
| `BAS0-3.HEX` | `8192` | `3d96ba589aa21d44412efb099a144fbe23a2f52f` | `c3 07 01 ba dc 00 20 c3` | `0x0107` | `BASIC`: 0x04A8; `READY`: 0x0471; `ERROR`: 0x0464 |

Compatibility notes:

- `ref/mame_juku.cpp` records Monitor 3.3 as `Monitor/Bootstrap 3.3 \w JBASIC`
  and the local source contains the compatibility warning that it does not
  seem compatible with the JBASIC expansion cartridge: PASS.
- The BASIC images do contain `BASIC`, `READY`, and `ERROR` strings, but their
  first instruction is an absolute `JMP 0x0107`; that is not a direct
  `0x4000`-window entry point by itself.
- Baltijets doc 003 acceptance notes mention BASIC launch from the removable
  32K memory expander with command `A`, expecting a BASIC banner and `READY`.
  That is a separate compatibility target from Monitor 3.3's current `B` path.
- `docs/vendored-disk-catalog.md` records a second BASIC lead independent of
  the removable-memory cartridge path: the vendored EKDOS boot disk
  `media/disks/JUKU1.CPM` contains `JBASIC.COM`, and `JUKPROG2.CPM` contains
  `JBASIC.COM` plus BASIC compiler/runtime support files.
- `docs/basic-disk-extraction.md` preserves `JUKPROG2_JBASIC.COM` as the
  best directory-backed disk BASIC executable candidate and a separate
  `JUKU1_JBASIC_raw_candidate.COM` with `BASIC`/`READY`/`ERROR` strings.

## Evidence

| Monitor | ROM | Cartridge | Frame cycles | Infra | Cart overlay reads | PC in `0x4000..0xBFFF` | Mode-1 PC cycles | Mode-2 PC cycles | `0x00` opcode cycles | RAM writes | RAM first/last write | RAM first/last write PCs | RAM nonzero bytes | RAM byte sum | Visible pixels | Stop PC | Mode | VRAM SHA256 |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| jmon33 | `roms/jmon33.bin` | `jbasic11.bin` | `200000` | PASS | `8196` | `17881962` | `17881962` | `0` | `17881962` | `1636` | `0x8AD2..0x8AD2` | `0xF008..0xF008` | `0` | `0` | `0` | `0x9B6A` | `1` | `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d` |
| jmon33 | `roms/jmon33.bin` | `BAS0-3.HEX` | `200000` | PASS | `8196` | `17881962` | `17881962` | `0` | `17881962` | `1636` | `0x8AD2..0x8AD2` | `0xF008..0xF008` | `0` | `0` | `0` | `0x9B6A` | `1` | `559eb05d39a8e243be3e4b051e94f6572a487cc6f90c4847f333d61fe887b28d` |
| ekta37 | `roms/ekta37.bin` | `jbasic11.bin` | `40000` | PASS | `0` | `0` | `0` | `0` | `0` | `0` | `0x0000..0x0000` | `0x0000..0x0000` | `0` | `0` | `16555` | `0xFED4` | `0` | `1a178175b438c9d5b6ef20febe467efb58657646bd9ee6622349bcfa359eed9f` |

## Disposition

- `jmon33` with `jbasic11.bin` reads the BASIC cartridge and executes in `0x4000..0xBFFF`; `17881962` of those PC cycles are in RAM/ROM mode 1 and `0` are in cartridge overlay mode 2. `17881962` PC cycles fetch a `0x00` opcode there. The RAM window saw `1636` accepted writes, `0` of them nonzero, from PC range `0xF008` to `0xF008` over addresses `0x8AD2`..`0x8AD2`, ending with `0` nonzero bytes and byte sum `0`. The captured framebuffer has `0` visible pixels.
  The write PC is sampled after opcode fetch; in the high-ROM `jmon33.bin` mapping, `0xF008` is the byte after the `MOV M,A` at `0xF007` in the local copy/clear loop.
- `jmon33` with `BAS0-3.HEX` reads the BASIC cartridge and executes in `0x4000..0xBFFF`; `17881962` of those PC cycles are in RAM/ROM mode 1 and `0` are in cartridge overlay mode 2. `17881962` PC cycles fetch a `0x00` opcode there. The RAM window saw `1636` accepted writes, `0` of them nonzero, from PC range `0xF008` to `0xF008` over addresses `0x8AD2`..`0x8AD2`, ending with `0` nonzero bytes and byte sum `0`. The captured framebuffer has `0` visible pixels.
  The write PC is sampled after opcode fetch; in the high-ROM `jmon33.bin` mapping, `0xF008` is the byte after the `MOV M,A` at `0xF007` in the local copy/clear loop.
- `ekta37` with `jbasic11.bin` does not select the cartridge overlay in this run.
- The current evidence is therefore a compatibility boundary, not just a
  missing prompt: the tested Monitor 3.3 path reads the media but does not
  execute the cartridge overlay as live BASIC code.
- The remaining BASIC work is a user-visible BASIC prompt oracle and HDL-side
  coverage of the correct launch path. The disk-side `JBASIC.COM` evidence now
  gives a concrete EKDOS command target in addition to the still-unresolved
  monitor/removable-memory pairing.
