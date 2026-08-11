# Juku ROM monitor command reference

Status: hand-written analysis, 2026-08-11. Byte-verified against the pinned
images; semantics decoded from the ekta37 handlers and applied to the
EktaSoft family (identical rebuilds); jmon33 shares the command set but its
handlers are not independently decoded. All handler labels live in the
[`../disasm/`](../disasm/README.md) control files.

## The boot screen is a monitor prompt

After the banner/configuration screen, the ROM waits at a command prompt —
nothing boots without input (a keyless cosim boot idles indefinitely, and
the CI boot automation must type `TDD` to reach EKDOS). The command set is
a classic machine-code monitor, dispatched through a `[letter][address]`
table that every EktaSoft image and Monitor 3.3 carry identically:

| Command | Decoded behavior (from ekta37 handler code) |
| --- | --- |
| `F` | fill memory range with a byte |
| `D` | hex-dump memory range, 8 bytes per line |
| `S` | substitute/examine memory interactively |
| `X` | examine/modify saved registers |
| `G` | go/execute, restoring saved registers (optional address) |
| `M` | move/copy memory block |
| `C` | compare memory blocks, listing differences |
| `E` | console echo until Ctrl-C (`03h`) |
| `K` | search memory range for a byte value |
| `T` | **load system** — prints the boot-source prompt (below) |
| `B` | vector-region stub in the vendored builds (BASIC extension slot; semantics unverified) |
| `R` | read block: parses an address range, invokes monitor service `12h` |
| `W` | write block: parses an address range, invokes monitor service `21h` |
| `P` | select console/output device (mode byte; parallel printer per banner) |
| `A` | switches device mode, operates on the `4000h` region (plausibly application/cartridge start; unverified) |

`R`/`W` funnel into a service dispatcher (`MON_SERVICE` label per image)
that takes a command code in `A` — the same dispatcher the EKDOS30.ASM
monitor contract reaches through the `FF50h+` vectors.

## The T command and the boot-source prompt

`T` prints `System from <D>isk, <N>et ?` (or `<T>ape` on the 2.43 line)
and dispatches the reply through a second `[key][address]` table directly
after the prompt text:

| Image | Table (ROM) | `D` | Second source |
| --- | --- | --- | --- |
| ekta24 | `1976h` | `FF50h` | `N` -> `EA93h` (NetBios) |
| ekta31 | `1976h` | `FF50h` | `N` -> `EAA1h` (NetBios) |
| ekta32 | `197Dh` | `FF50h` | `T` -> `EC2Ch` (TapeBios) |
| ekta35 | `1983h` | `FF50h` | `N` -> `EAAEh` (NetBios) |
| ekta37 | `1977h` | `FF50h` | `N` -> `EAA2h` (NetBios) |
| ekta43 | `197Eh` | `FF50h` | `T` -> `EC2Dh` (TapeBios) |

`D` is universal: every build jumps to **`FF50h`** — the monitor cold/boot
vector documented in `EKDOS30.ASM` (`ROM EQU 0FF50H`), which enters the
Bootstrap (`v4.1` on these builds) and its `System disk type (D/S/8) ?`
prompt. Hence the canonical boot choreography `T`, `D`, `D`.

## Monitor family

jmon33 carries the same 15-letter table at ROM `3C55h` (runtime `FC55h`);
its `T` enters the Bootstrap v3.3 block at ROM `2000h`. The other handlers
are labeled but not independently decoded. **jmon22 shows no intact
command table anywhere in its dump** — its siblings place the table in the
address range covered by jmon22's unstable blocks 6-7, so the missing
table is consistent with (though not proof of) the known read damage; see
[`jmon22-reconstruction.md`](jmon22-reconstruction.md).

## Reproduction

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
