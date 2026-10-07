# Juku ROM monitor command reference

Byte-verified against the pinned images; semantics decoded from the ekta37
handlers and applied to the EktaSoft family by their shared command structure.
The images differ in code and handler addresses; jmon33 shares the command set but its
handlers are not independently decoded. All handler labels live in the
[`../disasm/`](../disasm/README.md) control files.

## The boot screen is a monitor prompt

The stock EktaSoft ROMs wait at a command prompt after the banner/configuration
screen. Their cosim disk-boot guards type `TDD` to reach EKDOS. Enhanced
JukuNet ROMs have a separate automatic-boot contract; see
[machine deployment status](machine-deployment-status.md).
The stock command set is
a classic machine-code monitor, dispatched through a `[letter][address]`
table. Every EktaSoft image and Monitor 3.3 carries the same command letters;
handler addresses vary:

| Command | Decoded behavior (from ekta37 handler code) |
| --- | --- |
| `F` | fill memory range with a byte |
| `D` | hex-dump memory range in eight-byte address rows; first and last rows may be partial |
| `S` | substitute/examine memory interactively |
| `X` | examine/modify saved registers |
| `G` | go/execute, restoring saved registers (optional address) |
| `M` | move/copy memory block |
| `C` | compare memory blocks, listing differences |
| `E` | console echo until Ctrl-C (`03h`) |
| `K` | list memory locations whose byte differs from a supplied value |
| `T` | **load system** — prints the boot-source prompt (below) |
| `B` | vector-region stub in ekta37 (BASIC extension slot; semantics unverified) |
| `R` | read block: parses an address range, invokes monitor service `12h` |
| `W` | write block: parses an address range, invokes monitor service `21h` |
| `P` | select console/output device (mode byte; parallel printer per banner) |
| `A` | switches device mode, operates on the `4000h` region (plausibly application/cartridge start; unverified) |

`R`/`W` funnel into a service dispatcher (`MON_SERVICE` label per image)
that takes a command code in `A` — the same dispatcher the EKDOS30.ASM
monitor contract reaches through the `FF50h+` vectors.

In ekta37, `D`, `F`, `K`, `M`, and `C` process the start address before
comparing it with the end address, so the end is inclusive. `M` copies bytes
forward in ascending source-address order; an overlapping destination above
the source can overwrite bytes that have not yet been copied. These details
are decoded from the handlers, not independently exercised on hardware.

## The T command and the boot-source prompt

`T` prints `System from <D>isk, <N>et ?` (or `<T>ape` on the 2.43 line)
and dispatches the reply through a second `[key][address]` table directly
after the prompt text:

| Image | Table (ROM) | `D` | Second source |
| --- | --- | --- | --- |
| ekta24 | `19C4h` | `FF50h` | `N` -> `EA93h` (NetBios) |
| ekta31 | `19C4h` | `FF50h` | `N` -> `EAA1h` (NetBios) |
| ekta32 | `19CDh` | `FF50h` | `T` -> `EC2Ch` (TapeBios) |
| ekta35 | `19D1h` | `FF50h` | `N` -> `EAAEh` (NetBios) |
| ekta37 | `19C5h` | `FF50h` | `N` -> `EAA2h` (NetBios) |
| ekta43 | `19CEh` | `FF50h` | `T` -> `EC2Dh` (TapeBios) |

`D` is universal: every build jumps to **`FF50h`** — the monitor cold/boot
vector documented in `EKDOS30.ASM` (`ROM EQU 0FF50H`), which enters the
Bootstrap (`v4.1` on these builds) and its `System disk type (D/S/8) ?`
prompt. Hence the canonical boot choreography `T`, `D`, `D`.

## Monitor family

jmon33 carries the same 15-letter table at ROM `3C55h` (runtime `FC55h`);
its `T` enters the Bootstrap v3.3 block at ROM `2000h`. Its `B` entry points
to runtime `EE29h` (ROM `2E29h`), unlike ekta37’s `FF9Bh` stub; shared
command letters do not prove identical behavior. The other handlers are
labeled but not independently decoded. **jmon22 shows no intact
command table anywhere in its dump** — its siblings place the table in the
address range covered by jmon22's unstable blocks 6-7, so the missing
table is consistent with (though not proof of) the known read damage; see
[`jmon22-reconstruction.md`](jmon22-reconstruction.md).

## Reproduction

Run from the repository root with Python 3 and the retained ROM binaries.
This prints ekta37’s two dispatch tables; it does not execute the handlers
or qualify command semantics on other images. The boot table contains a
second source key `N` or `T` according to the image above, so do not send a
`N` to select tape on a TapeBios ROM; its second source key is `T`.

```sh
python3 - <<'EOF'
rom = open("roms/ekta37.bin","rb").read()
i = 0x1977
while rom[i] != 0x00:
    print(chr(rom[i]), f"{rom[i+1] | (rom[i+2] << 8):04X}")
    i += 3
i = 0x19C5
while rom[i] != 0x00:
    print("T-key", chr(rom[i]), f"{rom[i+1] | (rom[i+2] << 8):04X}")
    i += 3
EOF
```
