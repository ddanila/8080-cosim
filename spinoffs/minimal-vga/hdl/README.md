# HDL integration

Status: **REAL-ROM BOOT AND SYNTHETIC SMOKE PASS / HARDWARE DESIGN HOLD**.

Two independent spin-off tops boot the patched real Juku `ekta37` firmware:
`juku_boot_top.vhd` runs it on T80, while `vjuga_juku_top.v` runs it on tv80
through the shared К565РУ5, D6 К556РТ4, and D8 К155РЕ3 models. Both framebuffer
results match the main cosim oracle after 6000 video writes. This is simulation
evidence, not a release of the stale Rev-A copper.

The VHDL smoke top directly instantiates `T80se` from the `external/T80`
submodule with `Mode => 0` (Z80), `IOWait => 1` and `CLKEN => '1'`.
Local logic handles ROM, I/O and the shared DRAM sequencer; an independent
counter supplies refresh requests instead of Z80 `RFSH_n`.

The Verilog tv80 twin and modular Rev B models are separate maintained paths;
see [simulation checks](../sim/README.md) for their entry points and scope.

## Source Order

For VHDL tools, compile T80 in this order:

1. `external/T80/T80_Pack.vhd`
2. `external/T80/T80_ALU.vhd`
3. `external/T80/T80_MCode.vhd`
4. `external/T80/T80_Reg.vhd`
5. `external/T80/T80.vhd`
6. `external/T80/T80se.vhd`

The file list is also captured in `t80-vhdl.files`.

With GHDL, use `-fsynopsys`; T80 uses Synopsys-era IEEE packages.
Run from the repository root:

```sh
(
  set -e
  tmp=$(mktemp -d)
  trap 'rm -rf -- "$tmp"' EXIT
  cd spinoffs/minimal-vga/hdl
  while IFS= read -r f; do
    ghdl -a --workdir="$tmp" --std=08 -fsynopsys "$f"
  done < t80-vhdl.files
  ghdl -e --workdir="$tmp" --std=08 -fsynopsys T80se
)
```

## Synthetic smoke top

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
completes at least one frame. It also requires nonzero CPU wait and video-read
counters. The VGA counters run independently; this test does not check a
scanned-out pixel image.

The RAM path goes through an explicit DRAM sequencer:

- CPU requests latch address and write data.
- The sequencer presents row address, asserts `RAS`, presents column address,
  asserts `CAS`, then completes the cycle.
- Memory reads are wait-stated until the sequencer has latched read data.
- Periodic refresh uses the same RAS-side timing path and is generated
  independently of Z80 `RFSH`.
- Periodic video fetches arbitrate for the same DRAM sequencer and count
  synthetic sequential reads starting at `0x8000`; they are not bounded to
  the Juku framebuffer window.

This is a functional timing scaffold. It does not establish the original
Juku shared-DRAM slot schedule or propagation delays. See the root
[video-slot audit](../../../docs/video-slot-timing-audit.md) for that boundary.
