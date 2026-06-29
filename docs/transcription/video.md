# Transcription — Video subsystem (Sheet 2)

Source: background agent sweep, **cross-checked against the scan**. Treat agent
findings as **to-verify** unless marked [verified]. (The agent also claimed a ГФ24
8224 clock — **WRONG**, see below — so verify the rest too.)

## ⚠️ Correction: NO 8224 (re-verified on scan) [verified]
The agent reported a "ГФ24 (8224) clock gen". Re-checking the scan: the clock is a
**discrete crystal oscillator** — Z1 + C73 (4/20 trimmer) + **ЛН1 inverters (D59)** —
NOT an 8224. Confirms the earlier finding; the 8224 stays removed from the model.
(Classic convention-inference error — exactly what scan-verification catches.)

## Video chips (agent-reported, to-verify)
| refdes | marking | role |
|---|---|---|
| D44–D47 | ИЕ7/СТ16 (74193-class) | **video address counter** chain (parallel-loadable; LOAD presets at frame start) |
| D48–D50 | КП14 (quad 2:1 mux) | **address MUX**: video-counter addr vs μP addr → DRAM |
| D52 | КП11 (quad 2:1 mux, tri-state) | extra address-mux stage (VIDEO ADDRESS / μP ADDRESS) |
| D53 | ИД7 (74138) | bank / RAS-CAS select decoder (Y0–Y3 via R49–R52 100Ω) |
| D54, D55, D57 | ВИ53 (8253) | **sync/timing**: D54 HOR RTR, D55 VER RTR/VERT SYNC, D57 BAUD/SOUND/2MHz |
| D58 + RG | ИР82 (8282) | data-bus octal latches (nets 31–38) — NOT a pixel shifter |
| D38, D39 | ЛА1/ЛН1 | LOAD pulse generation (presets video counters) |
| D33, D37 | ЛН1/ЛА3 | gate DRAM data-out → VIDEO (via RAM OUT EN + MRD) |

## Dataflow (agent-reported, to-verify)
- Video address = cascaded ИЕ7 counters (D44→D47), preset via LOAD; muxed with CPU
  address by D48–D50/D52 → the РУ5 array's multiplexed A0–A7. **This is the address
  mux that drives our РУ5 model's `MA`/RAS/CAS boundary nets** (connect once verified).
- **No parallel-to-serial shifter**: framebuffer DRAMs are 1-bit-wide, so video is
  read out **serially** — DRAM `DO` gated (D33/D37, by RAM OUT EN + MRD) straight to
  the VIDEO net. Plausible but to-verify.
- Output: VIDEO → connector X601 (pin 3); RF/HF output via VT1 (KT972) → X701.

## To verify next (against scan)
1. Confirm D44–D47 counter chain + LOAD/preset.
2. Confirm address mux D48–D52 select + which address bits → MA.
3. Confirm D53 role (bank select vs RAS/CAS) — then wire the РУ5 MA/RAS/CAS.
4. Confirm the serial video readout path (D33/D37 gating).
