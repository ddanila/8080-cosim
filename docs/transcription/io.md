# Transcription — I/O subsystem (8255/8251/8253/8259)

Verified inventory. Refdes + roles **[scan-confirmed]** (I read the 8251=D11,
8259=D10, 8255=D26/D27 labels directly; I/O-agent + video-agent agree). Pin numbers
are agent-reported **[agent]** and match standard parts — to spot-check when modeled.

## Conflict resolution (the D44 / D55 question)
The tape-sweep agent **misattributed refdes**. Verified truth:
- **8251 USART = D11** (not D44). **8255 PPI = D26, D27** (not D55).
  **8259 PIC = D10**. **8253 timers = D54, D55, D57**.
- Therefore **D44 = ИЕ7 video address counter** and **D55 = 8253 timer** (the
  video/I-O agents were right; tape agent wrong). [scan-confirmed]

## Chips
| refdes | part | ports | role |
|---|---|---|---|
| **D10** | 8259 (ВН59) PIC | Sheet 1 | interrupts |
| **D11** | 8251 (ВВ51) USART | Sheet 1 | serial (the "SIO") |
| **D26** | 8255 (ВВ55) PPI | Sheet 1 | keyboard/system (FK,K0-2,SHIFT,CTRL,SC0-3,AUDIO,PREN,STB) |
| **D27** | 8255 (ВВ55) PPI | Sheet 1 | general parallel (PA/PB/PC → connectors) |
| **D54/D55/D57** | 8253 (ВИ53) PIT | Sheet 2 | H-sync / V-sync / baud+sound timing |

## Pinouts (agent-reported, std-part consistent)
- **D10 8259**: CS=1, A0=27, RD=3, WR=2, INTA=26, INT=17, SP=16, D0-7=11,10,9,8,7,6,5,4.
  IR0=18(RxRDY), IR1=19(TxRDY), IR2=20, IR3=21, IR4=22(TAPE RUN INT), IR5=23(FRAME INT), IR6=24, IR7=25.
- **D11 8251**: CS=11, C/D(A0)=12, RD=13, WR=10, RES=21, CLK=20, TxC=9, RxC=25,
  D0-7=27,28,1,2,5,6,7,8, TxRDY=15, RxRDY=14, RxD=3, RTS=23, DTR=24, DSR=22, CTS=17 (TxD pin faint).
- **D26/D27 8255**: CS=6, A0=9, A1=8, RD=5, WR=36, RES=35, D0-7=34,33,32,31,30,29,28,27.
- **D54/D55/D57 8253**: CS=21, A0=19, A1=20, RD=22, WR=23, D0-7=8,7,6,5,4,3,2,1;
  per counter CLK/GATE/OUT (0:9/11/10, 1:15/14/13, 2:18/16/17).

## I/O chip-select decoder — A4: it's a PROM (D2), not the 74138
The agent couldn't isolate a 74138 because the I/O selects are **PROM-decoded**:
- **D2 = К556РТ4 PROM** (256×4), "ROM РТ4 D2" on Sheet 1, + glue (D105 ЛА3, FFs
  D13/D30/D35). Analogous to the memory decode (D6 РТ4). [scan]
- The power-table **ИД7 = D53** (the Sheet-2 RAS/CAS decoder, already found) — not
  the I/O decoder.
- **Implication:** like the memory map, the I/O port→chip decode lives in the **PROM
  contents (off-schematic)** = the known I/O map (0x00→PIC, 0x04→PPI0, …). So the CS
  *decode* can't be wiring-traced to `scan`; only the РТ4-output→chip-CS wiring could
  be (intricate, untraced). The DID7 model instance is relabeled **D2** (РТ4 PROM).
- Same applies to the EPROM **CS4–CS7** (memory selects) — PROM/decoder-based, contents off-schematic.

## Integrated + LVS-green ✅
The HDL I/O shells now carry their **real refdes** (D26/D27→PPI, D11→USART,
D54/D55/D57→PIT, D10→PIC) + verified pinouts, wired on the data bus (DB), buffered
address (BA[1:0]), and the **I/O strobes IORD/IOWR** (from the 8238). The **banking
mode link** is modeled: D26 (8255#0) Port C bit0 → D7 (ЛА3) → PROM enable. Plus the
interrupt path (8259 INT→CPU, 8238 INTA→8259) and reset distribution.
Full board: **29 chips / 72 nets, LVS IN SYNC.**

Boundary (not yet modeled): the **ИД7 I/O chip-select decoder** (refdes/wiring
un-traced) — so per-chip CS are boundary nets; and the timer/USART **clocks**
(from the divider/baud chain). The clk-disconnect surfaced these honestly.
