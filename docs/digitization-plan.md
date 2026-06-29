# Digitizing the processor-module schematic

The schematic (`ref/schematics/`) is a **raster scan** → no reliable automatic
netlist extraction. We transcribe it by hand — but we are not tracing blind:
the **LVS checker + HDL model verify every connection**, turning transcription
into a self-checking process. That feedback loop is the whole point of the project.

## Method (transcribe → generate → LVS → resolve)

1. **Source of truth** = the scan. Read via the high-res PNGs; zoom per region.
2. **Transcribe** into a structured board spec (`kicad/juku.board.json`):
   components `{refdes, gost, western, pins:{number:signal}}` and `nets`.
   Build it **incrementally, one subsystem at a time**.
3. **Generate** a KiCad schematic from the spec (`kicad/gen_kicad_sch.py`) →
   `kicad-cli` netlist.
4. **LVS** the transcribed netlist against the structural HDL (`hdl/`):
   - match → transcription and model agree;
   - mismatch → investigate. Either a **transcription error** (fix the spec) or a
     **genuine ES101↔E5104 difference** (the schematic wins; update `hdl/` +
     `docs/hardware-map.md` to match the real board).
5. Repeat per subsystem until the netlist is complete and LVS-clean.
6. Scan stays the visual reference. A tidy graphical schematic (proper symbols +
   footprints for a real PCB) is a later, optional pass in the KiCad GUI.

## Suggested order (most-grounded first)
1. **CPU core** — `КР580ВМ80` + `ГФ24` clock + `ВК38`(8238) bus control + reset;
   address/data buses; `БА86`(8286) buffers.
2. **Memory** — ROM/EPROM array, `РУ5` DRAM array, address decode + the 4-mode
   bank logic (verify against MAME's PortC[1:0] scheme).
3. **I/O** — `ВВ55`×2 (8255), `ВВ51` (8251), `ВИ53`×3 (8253), `ВИ59` (8259) + I/O decode.
4. **Video** — address/sync generation, video shift-out.
5. **Tape / serial** — `СА3` comparator path, baud-rate, connectors.

## ГОСТ → Western part reference (refine during transcription)
| ГОСТ marking | Western | Role |
|---|---|---|
| КР580ВМ80А | i8080A | CPU |
| КР580ГФ24 | i8224 | clock generator (Φ1/Φ2, RESET, RDY) |
| КР580ВК38 (БК38) | i8238 | system controller (DBIN/WR → MEMR/MEMW/IOR/IOW) |
| КР580ВА86/ВА87 (БА86/БА87) | i8286/8287 | octal bus transceiver (bus buffers) |
| КР580ВВ51А | i8251 | USART |
| КР580ВВ55А | i8255 | PPI |
| КР580ВИ53 | i8253 | programmable interval timer |
| КР580ВН59А (ВИ59) | i8259 | interrupt controller |
| КР580ИР82 | i8282 | octal latch |
| К565РУ5 | (4164-class) | 64K×1 DRAM |
| К573РФ.. | EPROM | ROM/EPROM |
| К555ИЕ7 | 74193 | 4-bit up/down counter |
| К555ИЕ10/ИЕ11 | 74161/160 | binary counters |
| К555ТМ2 / К561ТМ2 | 7474 | dual D flip-flop |
| К555ЛА3 / К561ЛА3 | 7400 | quad 2-in NAND |
| К555ЛН1 / ЛН2 | 7404 | hex inverter |
| К555ЛИ1 | 7408 | quad 2-in AND |
| К555ИД7 | 74138 | 3→8 decoder (chip selects) |
| К561ИР9 | 74198-class | parallel/shift register |
| К554СА3 | (LM311-class) | comparator (tape input) |

## Notes
- This is only the **processor module**; a full Juku has further modules
  (video/keyboard/FDC). arti.ee likely hosts them — mirror later if needed. This
  module already covers CPU+ROM+RAM+8251/8255/8253/8259+video+tape, i.e. most of it.
- Power/ground per chip is given in the on-sheet power tables (bottom-right of each
  sheet) — use those, don't infer.
