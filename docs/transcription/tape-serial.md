# Transcription — Tape & Serial subsystem (Sheet 3, parts of Sheet 1)

Source: background agent sweep. **ALL to-verify** — and note the reliability caveat
below. These are *leads* (what exists + plausible roles), not verified truth.

## ⚠️ Reliability caveat — agents conflict on refdes
The video-sweep and tape-sweep agents **disagree on refdes assignments**:
- **D44**: tape says 8251 USART; video says ИЕ7 counter.
- **D55**: tape says 8255 PPI; video says 8253 timer.
Refdes are unique per board, so at least one agent misread each. **Do not treat any
agent refdes/pin as truth until re-read on the scan.** The scan is the only authority.

## Components (agent-reported, to-verify)
| refdes? | marking | role |
|---|---|---|
| D44? / D23? | ВВ51 (8251A USART) | serial TX/RX engine; pinout CS=11,C/D=12,RD=13,WR=10,CLK=20,TxC=9,RxC=25, data 27,28,1,2,4,6,7,8, RxD=3,CTS=17,DSR=22,RTS=23,DTR=24,TxRDY=15,RxRDY=14 (TxD pin ambiguous) |
| D40? | ВН59 (8259 PIC) | interrupts: RxRDY/TxRDY/TAPE RUN INT/FRAME INT |
| D26, D55? | ВВ55 (8255 PPI) | tape transport buttons, SHIFT/CTRL/AUDC |
| **D106** | К554СА3 | **tape input comparator** (DATA IN slicer) — Vcc14/GND6 |
| D102 | К561ИЕ11 | baud-rate counter |
| D101 | К561ИМ1 | baud-rate divisor adder |
| D99, D100 | К561ИР9 | baud-rate divider shift regs |
| D87/D88 | ТВ1/ТМ2 | clock-recovery FFs (RxC/SYNDET) |
| D95/D96/D94 | ЛП2/ЛА7/ЛН2 | tape modulation + baud logic |

## Dataflow (agent-reported, to-verify)
- **Tape IN**: DATA IN (conn pin 504) → C16(1µF) → R82(5.1K) → bias net → К554СА3
  (D106) comparator (R86 1М8 hysteresis) → sliced DATA IN → clock-recovery FFs → USART RxC.
- **Tape OUT**: USART TxD + modulator (ЛН2/ЛП2 XOR) → R79(10K) → RC (C20 0.022µF, R80 1K)
  → C22(1µF) → REC.DATA (conn pin 502); SYNC=501.
- **Tape transport** (via 8255): FF=401, REC=402, PLAY=403, RN=404, STOP=405.
- **Serial X3 (RS-232)**: SIN=304, CTS=305, DSR=306 (in via buffer); SOUT=308, RTS=310,
  DTR=311, TTL SOUT=303, PULL UP=301 (out via АП2 buffers).
- **Baud gen**: ИМ1 adder (divisor) → ИЕ11 counter (clk SYNC B.R.) → ИР9 dividers → BAUD RATE → USART TxC/RxC. TAPE RUN=408 gates it.

## To verify (against scan) — resolve conflicts FIRST
1. **D44 and D55 true identities** (counter vs USART; timer vs PPI) — re-read refdes on scan.
2. The 8251 refdes + pinout, the СА3 (D106) input network, the baud-gen chain.
3. Connector pin assignments (X2/X3/X4, 2xx/3xx/4xx/5xx).
