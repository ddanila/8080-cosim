# Transcription — Tape & Serial subsystem (Sheet 3, parts of Sheet 1)

Source: background agent sweep. **ALL to-verify** — and note the reliability caveat
below. These are *leads* (what exists + plausible roles), not verified truth.

## ⚠️ RESOLVED — this agent misread the refdes (see io.md)
Scan-verified truth: **8251 USART = D11**, **8255 PPI = D26/D27**, **8259 = D10**,
**8253 timers = D54/D55/D57**. So this agent's "D44 = USART" and "D55 = PPI" are
**WRONG** (D44 = ИЕ7 counter, D55 = 8253 timer). The agent's *roles/dataflow* below
are useful leads, but **ignore its refdes** — trust `io.md` for the I/O chips. The
non-conflicting parts (СА3 tape comparator D106, baud-gen ИМ1/ИЕ11/ИР9) still to-verify.

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

## VERIFIED on scan ✅
- **D106 = К554СА3** tape-input comparator (W/W/E pins 3/4/2; R86 1М8 hysteresis;
  DATA IN=504, 503); input net C16/R82/R84 confirmed. ✓
- **TWO 8251 USARTs**: **D11** (I/O subsystem, verified earlier) **and D23** (Sheet 3,
  the RS-232 serial one: RES=21, CLK=20, RxC=25, TxD=19, RTS=23, DTR=24, TxRDY=15,
  RxRDY=14, DSR=22, SD=16). Matches MAME's two SIO devices. (The agent's "8251=D44"
  was wrong; the real USARTs are D11 and D23.) ✓
- CNTR CHECK → 407 via ЛН2 (D94), R78 20k. ✓
Baud-gen chain (ИМ1/ИЕ11/ИР9) roles plausible; exact divisor wiring still to-trace.
