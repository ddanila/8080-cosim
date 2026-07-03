# HDL integration

The first CPU target is the VHDL T80 core from the `external/T80` submodule.

Use `T80se` first:

- `Mode => 0` for Z80 mode.
- `IOWait => 1` for standard I/O cycle timing.
- `CLKEN => '1'` for the first simple simulation.
- Keep `RFSH_n` visible, but do not use it as the primary DRAM refresh source.

The planned top-level shape is:

```text
T80se
  -> z80_native_adapter
  -> mem_io_request
  -> ROM / DRAM timing / keyboard / VGA bridge
```

`z80_native_adapter` is deliberately disposable. The later option-2 adapter
should replace it with Z80-to-Juku/8080-style cycle generation without changing
the DRAM timing or VGA bridge blocks.

## Source Order

For VHDL tools, compile T80 in this order:

1. `external/T80/T80_Pack.vhd`
2. `external/T80/T80_ALU.vhd`
3. `external/T80/T80_MCode.vhd`
4. `external/T80/T80_Reg.vhd`
5. `external/T80/T80.vhd`
6. `external/T80/T80se.vhd`

The file list is also captured in `t80-vhdl.files`.

With GHDL, use `-fsynopsys`; T80 uses Synopsys-era IEEE packages:

```sh
tmp=$(mktemp -d)
cd spinoffs/minimal-vga/hdl
while IFS= read -r f; do
  ghdl -a --workdir="$tmp" --std=08 -fsynopsys "$f"
done < t80-vhdl.files
ghdl -e --workdir="$tmp" --std=08 -fsynopsys T80se
```

## First Smoke Top

`z80_minimal_top.vhd` instantiates `T80se` and runs a built-in synthetic ROM:

```asm
LD A,0x42
LD (0x8000),A
LD A,(0x8000)
OUT (0x10),A
IN A,(0x20)
HALT
```

The testbench checks that the 4164-style bit-sliced RAM bank and IO both observe
`0x42`, that a keyboard-style IO read occurs, that the independent refresh
counter ticks without relying on Z80 `RFSH`, and that the VGA timing block
completes at least one frame.

The RAM path now goes through an explicit DRAM sequencer:

- CPU requests latch address and write data.
- The sequencer presents row address, asserts `RAS`, presents column address,
  asserts `CAS`, then completes the cycle.
- Memory reads are wait-stated until the sequencer has latched read data.
- Periodic refresh uses the same RAS-side timing path and is generated
  independently of Z80 `RFSH`.
- Periodic video fetches arbitrate for the same DRAM sequencer and count
  successful reads from the framebuffer window.

This is still a functional timing scaffold, not the final transistor-level Juku
timing PROM behavior.
