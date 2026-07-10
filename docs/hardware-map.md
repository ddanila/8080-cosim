# Juku E5104 behavioral hardware map

Status date: 2026-07-10.

This is the concise software-visible map used by the emulator and digital-twin
tests. The pinned source is `ref/mame_juku.cpp`; the physical endpoint model is
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

The repository BIOS is 16 KiB across D15/D16. The physical ROM-pager PROM D8
is not dumped; a behaviorally reconstructed table is exported under
`ref/reconstructed-proms/` and explicitly labeled as reconstructed.

## Video

- Monochrome framebuffer base: `0xD800` in shared DRAM.
- Guarded runnable geometry: 320 x 241 pixels, 40 bytes per line, most
  significant bit first.
- The current runnable HDL uses an abstract second DRAM read port. The physical
  D42/D43 serializers and part of the arbitration mesh are structural, but the
  exact shared-memory slot timing remains blocked on D94 `.092` and other
  timing continuity. See `video-slot-timing-audit.md`.

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
| `80` | mouse interface | optional mouse input |

The physical I/O select device is D9 К555ИД7. D2 is a separate `.037`
bus/wait PROM and must not be described as the I/O decoder.

## Interrupt and keyboard behavior

- PIT vertical timing feeds the frame interrupt path into the 8259.
- USART-ready and expansion/mouse inputs occupy additional 8259 lines; exact
  physical switch/routing boundaries are recorded by the generated reports.
- Keyboard scanning uses 8255 #0: Port A selects/strobes a column and Port B
  returns encoded key state. This behavior is runnable in the HDL tests.

## Physical-design boundary

The digital twin reaches Monitor and EKDOS prompts, and the modeled endpoints
pass structural comparison. That does not release the current PCB for
fabrication: D2 signal connectivity/content, D94 enable/output/content, and 11
official IC footprints without pin models remain open design items. That group
includes D30 READY support, the D105 wait gate, and FDC support logic. `PLAN.md`
is the living release checklist.
