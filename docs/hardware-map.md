# Juku E5104 behavioral hardware map

This is the concise software-visible map used by the emulator and digital-twin
tests. The pinned MAME reference is `ref/mame_juku.cpp`; current runnable
behavior is implemented in `cosim/trace.c` and `hdl/juku_top.v`. The endpoint model is
`kicad/juku.board.json`. MAME is a behavioral oracle, not proof of every PCB
connection.

## CPU and memory

- CPU: КР580ВМ80А / Intel 8080-compatible, reset at `0x0000`.
- Physical `.158/.009` target: 32 К565РУ5 socket positions in four banks, with
  D84-D91 populated for one 64 KiB byte-wide bank. D60-D83 are empty expansion
  sockets in the target configuration.
- The CPU sees a four-mode ROM/RAM view selected by 8255 #0 Port C bits 1:0.

| Mode | Overlay | Remaining address space |
| ---: | --- | --- |
| 0 | BIOS ROM at `0000-3FFF` | RAM |
| 1 | BIOS ROM at `D800-FFFF` | RAM at `0000-D7FF` |
| 2 | cartridge at `4000-BFFF`, BIOS at `D800-FFFF` | other addresses are RAM |
| 3 | none | all RAM |

Mode 0 reads the low BIOS overlay while writes to `0x0000..0x3FFF` reach
underlying RAM. The `ekta37.bin` (RomBios 3.43m) low-stack dispatcher uses this behavior for
its return frame at `0x00E4..0x00E5`, then restores the caller's mapping. The high BIOS and cartridge windows remain write-protected overlays;
allowing high-ROM writes corrupts the independently guarded Monitor 3.3 idle
framebuffer. `hdl/sim/mem_decode_tb.v`, the Monitor 3.3 oracle, and the default
EKDOS WBOOT reload guard preserve this asymmetric contract.

The repository BIOS is 16 KiB across D15/D16. The physical ROM-pager PROM D8
uses the validated `.039` table recovered from three matching reads, including
a power-cycled capture. The older behavioral reconstruction remains under
`ref/reconstructed-proms/` as historical comparison evidence only.

## Video

- Monochrome framebuffer base: `0xD800` in shared DRAM.
- Guarded runnable geometry: 320 x 241 pixels, 40 bytes per line, most
  significant bit first.
- The current runnable HDL uses an abstract second DRAM read port. The physical
  D42/D43 serializers and part of the arbitration mesh are structural, but the
  exact shared-memory slot schedule remains unresolved. D41 package
  connectivity is source-closed; source closure does not establish its dynamic
  arbitration schedule or every remote timing-bundle connection. D94 `.092` is constrained as FDC control,
  not video-slot timing. See `video-slot-timing-audit.md`.

## I/O map

| Ports | Device | Main role |
| --- | --- | --- |
| `00-01` | 8259 PIC | interrupts |
| `04-07` | 8255 PPI #0 | keyboard, beeper, memory mode, floppy control |
| `08-0B` | 8251 USART #0 | serial/tape-era interface |
| `0C-0F` | 8255 PPI #1 | auxiliary parallel I/O |
| `10-13` | 8253 PIT #0 | horizontal timing counters |
| `14-17` | 8253 PIT #1 | vertical timing and frame interrupt |
| `18-1B` | 8253 PIT #2 | baud/audio timing |
| `1C-1F` | КР1818ВГ93 / WD1793 | floppy controller |
| `80` | MAME mouse expansion | optional reference interface; no mouse emulation in cosim |

The table describes address assignments, not complete device emulation. Cosim
implements selected PPI/PIC register behavior and peripheral paths needed by
its guards; otherwise it returns the port’s last output byte (initially zero),
with `F0-F3` explicitly returning `FF` for absent expansion hardware. In
particular, the `80` entry comes from MAME and has no cosim mouse handler.
The HDL has structural PPI instances; its passing tests cover their exercised
behavior rather than the complete peripheral contract.

The physical I/O select device is D9 К555ИД7. D2 is a separate `.037`
bus/wait PROM and must not be described as the I/O decoder.

## Interrupt and keyboard behavior

- The source circuit connects PIT vertical timing through D35 to 8259 IR5.
- D11 RxRDY/TxRDY feed PIC IR2/IR3. The source model assigns IR0 to X2.214
  and IR1 to X2.218/D27 PB7; see [serial handoff](serial-handoff.md).
- S4 selects IR6 between buffered expansion INT6 and USART SYNDET; HDL fixes
  it to INT6. Expansion INT7 feeds IR7 through D3. See
  [the S4 boundary](s4-interrupt-boundary.md). MAME's optional mouse uses IR6,
  but that reference behavior does not establish replica wiring or a cosim
  mouse implementation.
- Keyboard scanning uses 8255 #0: Port A selects/strobes a column and Port B
  returns encoded key state. This behavior is runnable in the HDL tests.

The runnable interrupt models cover different subsets. Cosim's minimal PIC
services USART RxRDY/TxRDY on IR2/IR3 and a CPU-cycle-scheduled frame event on
IR5, subject to the mask and CPU interrupt-enable state. Its frame period is
a simulation argument, not derived from the PIT counters.

In HDL, `pic_8259` stores two bus-visible register bytes but does not service
its wired interrupt inputs. The separate `intr_ctl` helper snoops PIC writes
and injects a three-byte CALL during INTA for the simulation-only `frame_tick`
input. The physical `frame_int` and USART ready nets do not trigger that helper.
`sync/inta_bus_check.sh` checks one IR5 CALL sequence against cosim; it does not
qualify a complete 8259 or PIT-to-CPU interrupt path.

## Physical-design boundary

The Monitor first-write guard and mapped-endpoint LVS comparison are runnable
checks. Recorded full-prompt evidence has a separate
[Verilator compatibility limitation](../sync/README.md#simulator-compatibility).
Neither result releases the PCB for fabrication.

Physical D2 contents and the measured D2/D30/D105/D13 WAIT/READY handoff are
adopted in the source model and HDL. The source-closed `H` contact is
X1.107B (`-BLOCK`), pulled up by R1 2 kΩ; see the
[D105 handoff](d105-h-boundary.md) for its selected routed-pad checks.
Local route/package checks cover that cluster, not the entire board.
See [manufacturing readiness](replica-manufacturing-readiness.md), the
[gap ledger](board-fidelity-gap-ledger.md), and [project plan](../PLAN.md) for
current routing, functional-pin, sourcing and construction holds.
