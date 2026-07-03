# Sheet-1 (p3_sheet1.png, 5150x3603) zone map for round-2 crops (orig px)
- D9/ИД7 + CS4-CS7 outputs (ROM selects?): crop (1890,540)-(2340,960)
- D2 РТ4 decode PROM (V1/V2 outs) + REV/ROE/RAM_SEL logic: crop (690,1770)-(1260,2340)
- D8 РЕ3 (top, R41 pullups, E-pin): crop (1650,240)-(2100,560)
- D10 PIC IR row (FRAME INT/TAPE RUN INT/RxRDY/TxRDY/IR7/IR6): crop (1620,2340)-(1980,2700)
- D26 PPI keyboard zone W/ X9 PIN CODES (FK/K1/K2/SHIFT/CTRL/SC0-3/AUDC/PREN/STB -> 904/903/803/507/508/511-516/540 + X2 codes on PA): crop (2880,1800)-(3510,2880)
- D27 PPI (PB/PC -> X2 codes 213-225): same column below
- Sheet note: "D2,D6,D8,D15-D22 устанавливаются в панелях" (socketed) ✓ matches photos
- IO CS decode source for D10/D26/D11/D27/PITs: NOT yet located on this sheet -- check
  D105 zone (300,745 display) and mid-left АЛ5/ЛА3 gates; possibly sheet 2.
Next: crop D9 zone first (decode conflict), then D26 (X9 grounding).
FINDING: D9 = DC symbol, sel ins pins 1,2,3 <- driver pins 11,12,13 (NOT РЕ3 outs -- those are
inputs on РЕ3; РТ4 outs = 9-12 partial match only). D8_D0-D2 nets confirmed SUSPECT. V1=4,V2=5
tied (& enable), V3=6, E=15 top. Outputs 0-7 = pins 15,14,13,12,11,10,9,7 -> right w/ codes.
Driver chip = in crop s1_d9drv.png (left of D9).
RESOLUTION (crop s1_d9drv.png): the chip driving the ИД7 selects is **D6 РТ4** (A0-A7 on
5,6,7,4,3,2,1,15; V1=13,V2=14 tied enable; outs D0=12->net"ROM"(1K pullups, up to РЕ3 zone),
D1=11, D2=10 ("REV"), D3=9 ("ROE")). So board.json D8_D0/D1/D2 nets are WRONG refdes -- should
be D6 outputs -> D9.1/2/3 (exact out-pin->sel-pin mapping needs one cleaner crop: first crop
showed labels 11,12,13 at D9 pins 1,2,3; D6 outs are 12,11,10,9 -- verify which three).
ALSO: sheet-1's D9/ИД7 outputs 0-3 go via a resistor box, 4-7 -> CS4-CS7 rails (ROM bank
selects?) -- reconcile with our CS_D10/CS_D26.. IO-select nets (moved from 'old D2 misassign').
Check whether IO CS decode is actually D9 outs 0-6 (pins 15..9) and CS4-7 = ROM banks on the
SAME decoder or a second decode stage. Next crops: D9 outputs' destinations (right of
(2340,540)-(2800,960)); D6 V1/V2 enable source (pins 13,14 <- wires from left).
Then: rewire board.json (D8_Dx -> D6_Dx nets), flip io_dec138/rom decode HDL accordingly,
LVS+boot, commit. Then D26/X9 harvest (codes crop (2880,1800)-(3510,2880)).
FINDING 2 (crop s1_d9out.png): sheet-1 D9/ИД7 outputs = the 8 EPROM SOCKET SELECTS:
locals -> D15-D18 CS(pin 20; OE 22 tied to CS on D15) via R21-R28 1K pullups (the 8x pack we
placed at (79-98,104-112) -- physical corroboration), CS4(2) CS5(2) CS6(2) CS7(3) cross-sheet
for D19-D22. => our board.json CS_D10/CS_D26/CS_D11/CS_D27/CS_D54/CS_D55/CS_D57 nets on
D9.7-14 are POSSIBLY MISATTRIBUTED (that's 7 more outputs than the chip has left). To find:
the real IO-select decode source (D10.CS wire origin; check mid-left D105/D103 gate zone and
whether an ИД7 section or РТ4/РЕ3 output drives the peripheral CS pins). Also verify: does
BOM-x1 К555ИД7 mean sheet's ROM decoder = board D9, and IO selects come from elsewhere
(D8 РЕ3 .117? second half of something?). NEXT CROPS: D10 CS origin (trace left from D10.1);
D6 V1/V2 enable source; then D26/X9 codes harvest (2880,1800)-(3510,2880).
CHECK (crop s1_d10cs.png): D10 ВН59 IR pin row verified = our netting (25:IR7 24:IR6 23:IR5
22:IR4 18:IR0 19:IR1 21:IR3 20:IR2), D0-D7=11..4 ✓, D11 below w/ CS=11 ✓. D10.CS(pin 1) row is
just ABOVE this crop -- next crop (1450,2100)-(2050,2350) to catch the CS pin + trace the select
rail left to its source chip (candidates: D105/D103 gate pair at display~(300-330,745) =
orig ~(900-990,2235)). IO-select source still UNRESOLVED.
FINDING 3 (crop s1_cssrc.png): D10.CS(1) is fed from a horizontal rail out of a TOP-LEFT
bundle of ~7 select rails (the peripheral CS bus). Left neighbor: **D105 К155ЛА3 (&) output
pin 6** joins this zone (IO-select qualifier gate?). D10.INT(17) exits right on its own rail.
The select-bus origin is ABOVE: next crop (1200,1700)-(2050,2100) to find the decoder that
sources the 7 CS rails (candidate: D2 РТ4 V1/V2/V3 second decode, or ИД7 second use).
SIDE FINDS (crop s1_csbus.png, orig (1200,1650)-(2050,2100)): wire-post "WR 19 (2)" = beeper
wire 19 (MEMW, ВК38-26<->ЛА3-2) drawn here ✓; D35 ЛН5 sect 1->2 = "-WAIT" -> jumper post
E8-1 (WAIT config jumper! new). Select-bus origin NOT in this crop -- the 7 rails come from
higher: next crop the D2 РТ4 zone (690,1770)-(1260,2340) and the area directly above
(1200,1200)-(2050,1700). Rails labeled 6/5 pass through vertically.
FINDING 4 (crop s1_csbus2.png, orig (1200,1200)-(2050,1700)): D5 (ВК38) strobe fan-out with
WIRE NUMBERS: INTA(23)->wire5, I/DRD(25)->wire4, I/OWR(27)->wire3, MRD(24)->wire1, MWR(26)->wire2
(long DASHED run right = монтажный провод convention on this sheet!). This decodes the numbered
timing wires 1-5 = MRD/MWR/IOWR/IORD/INTA. => D38 sect-2 LOAD-chain inputs ("timing wires
4/2/1/15" boundaries in HDL) are now identifiable: IORD, MWR, MRD + wire15.
Gates: D7 ЛА3 sect (9,10 -> 8) out joins rail 8/7 zone; D105 ЛА3 sect (1,2 -> 3) with in-2 fed
from D13 ТЛ2 out-4 node, in-1 from the MWR row; D105 sect (12,13 tied -> 11) = inverter off
wire-1 (MRD). Rails "7"/"8" here relate to beeper wires 7/8 (ВМ80-22<->ЛН5-10, ВК38-1<->ЛА1-8).
NEXT: D2 РТ4 V1/V2/V3 decode zone crop (690,1770)-(1260,2340) for the 7-rail IO CS bus source.
FINDING 5 (crop s1_d2rt4.png): D2 РТ4 = A0-A7 on 5,6,7,4,3,2,1,15 (same as D6); V1(13)/V2(14)
tied to GND (always enabled); only output drawn in this zone = D0 (pin 12) heading up-right.
More D105 ЛА3 sections here: (9,10->8) -> (4,5->..) chain; net arrow "H". IO CS source NOT at
D2 either -> read it off the D26/D10 CS pins directly (peripheral column crops).
FINDING 6 -- X9 KEYBOARD INTERFACE COMPLETE (crop s1_d26a.png): D26 ВВ55А:
RD=5 WR=36 RES=35 D0-7=34..27 ✓ (matches board.json). Port rows (pin, signal, wire-post, X9 code):
 B0=18 FK   p55 ->904 | B1=19 K0 p57 ->902 | B2=20 K1 p56 ->903 | B3=21 K2 p58 ->901
 B4=22 ->(cut, ?905/906) | B5=23 CONTRDAT p50 ->909 [OWNER-MEASURED ✓] | B6=24 SHIFT p52 ->907
 B7=25 CTRL p51 ->908 | A0=4 SC0 p48 ->911 | A1=3 SC1 p47 ->912 | A2=2 SC2 p46 ->913
 A3=1 SC3 p45 ->914 | A4=40 AUDC ->(2) | A6=38 PREN ->(3) | A7=37 STB p49 ->910
X9 codes 90x/91x = X9 pins 1-14. Posts 45-58 = numbered wire links (keyboard bundle).
MAME cross-check: SC=column select, K0-2=key code, FK=pressed/valid, all ✓.
FINDING 7 (crops s1_d9sel + s1_d8zone): DEFINITIVE partial reads of the decode cluster:
- D9 selects: pin1 <- src-pin 11, pin2 <- src 12, pin3 <- src 13 (labels certain).
  D6.11 = net "RAM"; D6.12 = net "ROM" (also -> R11/R12 1K pullups -> D8.E pin 15).
  So D9.1<-RAM(D6.11), D9.2<-ROM(D6.12) plausible; src 13 = third select, candidate ИР16
  QA=13 (mode-latch bit from D26 PC0/PC1 -> D42/D43?). NOT D8 outputs -> the D8_D0/D1/D2
  board nets stay WRONG and should become: D6_RAM {D6.11, D9.1}, D6_ROM {D6.12, D9.2,
  D8.15, R11, R12}, MODE13 {?.13, D9.3}.
- D8 РЕ3 address inputs: A0=10<-src12, A1=11<-src13, A2=12<-src14, A3=13<-src15, A4=14<-src16.
  Source = a buffer with outs 12-16 (ВА87 B-outs = 12..19 -> would be BA8-BA12, NOT our
  modeled BA11-15!). VERIFY next: crop left of the vertical rail to ID the buffer chip +
  its input side. If A0-A4 = BA8-12, re-decode .117 (window pager interpretation may shift
  by 3 bits; boot unaffected -- sim uses mem_mode view).
- REINTERPRETATION of finding 2: the CS4(2)/CS5(2)/CS6(2)/CS7(3) cross-sheet rails are most
  likely IO selects Y4-Y7 -> D54/D55/D57(sheet2)/FDC-or-tape(sheet3) -- matching our existing
  CS_D54/55/57 nets -- while the R21-28 rails belong to the parallel EPROM column. The 7-rail
  bundle feeding D10.CS etc = D9 outs Y0-Y3+ after all. Our board D9 IO-CS nets likely OK.
  Remaining: confirm D9's E/V1/V2 gating (IORD/IOWR qualified how?) + the src-13 chip.
FINDING 8 -- D27 = X2 PARALLEL PORT, complete (crops s1_d26b/s1_d27c/s1_x2pc):
PA0-7 (pins 4,3,2,1,40,39,38,37) -> X2 codes 208,206,201,202,204,203,205,207 (PA1/PA5 digit
pair uncertain: both read ~206; 203 assigned to PA5 by elimination)
PB0-7 (18..25) -> 221,223,225,226,224,222,220,218
PC0-7 (14,15,16,17,13,12,11,10) -> 213,215,217,219,211,212,209,210
IMPLEMENTED: X2 connector + 24 nets; ppi_8255 grew a real pc[7:0] port (portc_lo retired);
mem_mode now = D26 pc[1:0]. LVS IN SYNC (169 core + 45 connector-boundary), boot PASS.
Remaining sheet-1 threads: D26 B4 row destination (contrdat pair), D6 RAM/REV/ROE net
destinations, D8 РЕ3 output side (bank selects -> sheet 2), wires 17/18 reset chain zone,
D9 E/V1/V2 gating source.
FINDING 9 -- WIRE 12 RESOLVED (crop s1_d9en2 + ТЛ2=74LS13 pinout): "RAM OUT EN" = a sheet-2
RAM-control rail; wire 12 distributes it to TWO LOADS on sheet 1: D13.2 (ТЛ2 sect-A input) and
D37.4 (ЛА3 B3 input) -- both ends of the owner's measured wire are inputs; the driver lives on
sheet 2 (RAM SEL / -RAM OUT EN family, posts 12/13 drawn). Net renamed W12_D13_D37 ->
RAM_OUT_EN {D13.2, D37.4} wire_link. HDL: shared undriven boundary wire. Related: "-RAM OUT EN"
rail (post 13) matches beeper wire 13 = D13.1 <-> D92.1 (W13 net already correct); R13/R14 1K =
the RC on D13.1. D9.V3 <- rail 6. LVS IN SYNC, boot PASS.
Round-2 remaining: D6 V1/V2 enable source, D8 РЕ3 output destinations (sheet 2), D26 B4 row,
wires 17/18 reset switch chain, D9 E/V1/V2 exact gating (E<-top rail, V3<-rail 6).
FINDING 10 (crop s1_d8out): D8 РЕ3 outputs D0-D7 (pins 1,2,3,4,5,6,7,9) each carry an
R21-R28 1K pullup to node-A (+5V rail) -- the R-pack beside D8 = its OUTPUT pullups (earlier
"EPROM CS pullups" attribution superseded; physical placement (79-98,104-112) beside D8 ✓).
The 8 outputs head to a consumer with input pins 5,6,7,8,1,2,3,4 (per-row dest labels).
HYPOTHESIS: the ИР16 latch pair D42/D43 (74-series parallel inputs live on pins 4-7) = the
bank-select LATCH chain (D37 LATCH gates + RAM SEL family). VERIFY next: follow the vertical
bus from (2330,620) down; crop (2300,620)-(2700,1100). Right edge of crop = D10's pin ladder
(rail-code | pin table) for reference.
D10 dest-pin table fragment (rail->pin): 13->2? 17->23, 11->21, 10->24, 9->25, 8->3, 7->4,
6->5, 5->6, 4->7, 3->8, 2->9, 1->10 [record; decode later].
FINDING 10b (crop s1_d8bus): the "dest table" right of D8 = D15 EPROM ADDRESS LADDER
(rail 13->A12 pin2, 17->A11 p23, 11->A10 p21, 10->A9 p24, 9->A8 p25, 8->A7 p3, 7->A6 p4,
6->A5 p5, 5->A4 p6, 4->A3 p7, 3->A2 p8, 2->A1 p9, 1->A0 p10). CONFIRMS rail-code system:
rail N = A(N-1), board-wide. EPROM symbol has A0-A12 + CS=20/OE=22 = 8K part (2764-class,
DIP-28) ✓ our EPROM8K model. NOTE the A11 rail code is 17 (not 12!) at the EPROM -- the
address rail codes 1-16 map A0-A15 but 17 appears for A11 here: RE-VERIFY the D9-select rail
codes 11/12/13 against this table (11->A10 ✓, 12->A11? but EPROM shows 17->A11 -- the code
12 = A11 assignment from finding 7 needs one confirming crop; A10/A11/A12 vs possible
A10/A12/A13 shifts the port-mirror mapping).
D8 consumer re-read: D8.D0-D7 -> consumer pins 1-8 consecutive = ВА86/87 A-side profile
(bank-select byte buffered) -- candidate D29/ВА87 spare half or sheet-2 buffer. Unresolved.

## SHEET 2 (round 2 continued)
FINDING 11 -- RAM OUT EN driver chain CONFIRMED on sheet 2 (crop s2_ramouten): -MRD(1) ->
D33 ЛН1 3->4 -> D37.5; RAM OUT EN(1) -> D37.4; D37 sect(4,5->6). EXACTLY our HDL model
(.i3(memr_n)->o4; .a3/.b3). Triple agreement: beeper + sheet-1 + sheet-2.
FINDING 12 -- D37.6 -> D58.9 (ИР82 OE) [rail continuity assumed]: net RAM_RD_OE added.
POLARITY INSIGHT: OE active during READS -> D58 = RAM READ-data latch (РУ5 DO -> DB), not
the write latch as modeled; role revision queued (direction flip touches DRAM datapath).
D58 sheet pins verified: D1-8=1..8, Q=12..19, STB=11<-rail5, OE=9<-rail8 ✓ our dict.
FINDING 13 -- audio output driver (crop s2_d37dest): rail 10 (SOUND, PIT D57.OUT1) -> R90 2k
-> VD4 -> R91 1k + VT1 КТ972 (darlington), emitter R48 -> speaker; AVDC(=AUDC, D26.PA4) level
input at right edge; matches emaplaat VT1/R90/R91/VD4/R48 cluster at (245-252,220-246) ✓
and MAME speaker chain ✓. Wire posts 1/2 nearby = speaker feed pair? (beeper wires 1/2 zone).
Sheet-2 rails at D58: STB<-rail5, OE<-rail8, audio<-rail10 (vertical bundle x~4340-4380).
NEXT sheet-2 targets: S3 DIP-switch bank (53.1-53.6) + R40-R46 pullups zone (video mode
config); D42/D43 ИР16 zone top-right (bank-select latches, D8-consumer candidate); PIT
TIMER blocks pin-verify vs MAME cascade; DRAM DO/DI bus vs D58 direction; power-pin table
bottom-left (per-type VCC/GND pins for LVS power nets).
FINDING 14 -- D8 CONSUMER = D42/D43 ИР16 BANK-SELECT LATCHES (crop s2_ir16), hypothesis
CONFIRMED: D8.D0-D3 -> rails 5,6,7,8 -> D42.A-D (pins 2-5); D8.D4-D7 -> rails 1,2,3,4 ->
D43.A-D; D43.QD(10) -> D42.DS(1) cascade; D42.QD(10) -> D37 pins 12+13 (tied) -> 11 ->
R38 1k -> node A (exactly our modeled D37 sect-1). Old DB/video-shift wiring of D42/D43
was [assumed] -- superseded; 10 nets rewired (8x BSEL + D42_Q + D43_DS). CK(9)/LD(6)/G(8)
sources still to trace (kept on DOTCLK16M/VID_LD nets meanwhile). LVS IN SYNC, boot PASS.
FINDING 15 -- DRAM DATAPATH FLIPPED (crop s2_d60 + overview wire table): the model had D58
REVERSED. Sheet-2 truth: РУ5 DI pins sit DIRECTLY on DB (DI rails 31-38 = the DB0-7
inter-sheet wire codes); РУ5 DO pins (14) form a separate read bus (rails 1-8) into D58
ИР82 D-ins; D58.Q -> DB, OE-gated by the D37 read strobe (RAM_RD_OE). Implemented: 8x RDO
nets (DO bus + D58.D), DI pins + D58.Q merged into DB nets, WD0-7 nets retired; ir82_latch
now OE-gates its Q (z when disabled); ram_out_en rail = tri1 (its R-pullup). D60 block also
pin-verifies MA rails 21-28, R=rail11, C=15, W=16, DI=31.
BOOT NOTE: the flipped datapath boots the REAL ekta37 ROM byte-identical through the real
read path (DRAM DO -> ИР82 -> DB gated by D37) -- deepest datapath validation yet.
LVS IN SYNC. Remaining nearby: rails 31-38 driver side (which ВА87 pushes DB toward DI
during writes -- likely none needed, DI pins are plain loads), D58.STB source (rail 5).
FINDING 16 -- PIT PIN-VERIFY CLEAN (crop s2_pit1): D54 ВИ53 drawn pins = exactly the 8253
pinout used for the MAME cascade nets (CS21 A0/A1=19/20 RD22 WR23 D0-7=8..1, CLK/G/OUT =
9/11/10, 15/14/13, 18/16/17). Data ins <- rails 31-38 = DB codes (third confirmation).
All 7 cascade nets + PIT bus pins now factory-drawing-verified.
FINDING 17 -- LATCH/LOAD CHAIN FACTORY-VERIFIED (crop s2_latch): D41 ИР16 QA(13) -> wire-post
10 rail [= beeper W10_QA_SEL {D41.13, D50.1} ✓]; QB(12) -> D37.1 (sect-2 in, = .a2(d41_qb) ✓);
D37 sect2 out(3) -> D33.13 [= LATCH_PRE ✓]; D38 ЛА1 sect2 (ins pins 5,4,2,1 <- timing wires
{15?,IORD(4),MWR(2),MRD(1)}) out(6) -> D59.13 [= LOAD_PRE ✓]. D41.G(8) <- node-A pullup rail;
D41.CK(9)/DS(1) sources partially visible (left rails, IDs pending); D41 A-D ins <- rails
2,3,4,5(?) pending. Four nets verified, zero corrections needed in this zone.
FINDING 18 (crops s2_s3 + s2_s3dest): S3 = 6x DIP to GND, outs via R40-R45 13k pullups ->
the КП14 mux B-inputs (static video-address config component, NOT counter presets). D50/D51
КП14 pin-verified = our 74S258 map (A=2,14,5,11; B=3,13,10,6; S=1<-wire10 ✓; G=15; Q=4,12,9,7).
CONFLICT TO RESOLVE: D50 Q1-Q4 -> MA rails 21-24, D51 Q1-Q4 -> MA rails 25-28 (DIRECT MA
drivers!) -- our model has D48/D49 driving MA. Verify D48/D49's drawn role (CPU/video addr
first stage?) before rewiring the mux tree. S3 needs a real component (DIP-6 + R40-R45) in
board.json once the mux input mapping is read precisely.
FINDING 19 (crop s2_d48) -- MA BUS IS SHARED TRI-STATE: D48/D49 (CPU addr) AND D50/D51
(video addr) all drive MA rails 21-28; КП14=74S258 tri-states via G. D50/D51 promoted to
netted chips on the MA nets (HDL: disabled-enable boundaries; boot identical); W10 now
LVS-covered (U_D50.SEL <- U_D41.QA). D48/D49 G tied pairwise; G sources = the video-cycle
alternation [unread].
PIN-ORDER CAUTION: sheet draws Y->MA as pins 4,12,9,7 per mux; model keeps consistent
4,7,9,12 on BOTH pairs. A permutation experiment broke boot via the va-path asymmetry --
the line order can only be corrected together with the mux INPUT rail read (A/B pin ->
BA/counter rails) and a va-path treatment. QUEUED: full mux-tree input read (D44-D47
counters -> D50/D51 A ins; S3 -> B ins; D48/D49 A/B <- BA rails).
FINDING 20 (crop s2_muxin): D44/D45 ИЕ7 = 74193 EXACT (A,B,C,D ins=15,1,10,9; LD=11; R=14;
UP=5; DOWN=4<-node A; outs QA-QD=3,2,6,7; CO=12 -> next.UP(5) cascade). Counter outputs ->
video-address rails (5,6,7,8 then 9,10,11,12...) -> D50/D51 A-inputs. E13 = 4-post jumper,
post-4 grounded (video config). D46/D47 below continue the chain.
CAUTION -- RAIL-NUMBER TANGLE: sheet-2 rails 5-8 here (counter outs) vs finding-14's D42
input rails 8,7,6,5 (attributed to D8 bank byte from the SHEET-1 read). Wire numbers may be
sheet-local; the D8->D42/D43 BSEL nets could actually be counter->D42 connections (or vice
versa). RESOLVE by reading the E13 junction zone + the vertical rail bundle between D44-47,
D42/43, and the D50/D51 inputs before trusting BSEL0-7. (Nets left as-is, flagged.)
FINDING 21 (crop s2_e13 -- landed on PIT column): D54 control rows: CS(21)<-"6", A0(19)<-"2",
A1(20)<-"3", RD(22)<-"4", WR(23)<-"5"; DB rails 31-38 again ✓. The small per-row numbers fit
NEITHER the global wire table (1-5=MRD/MWR/IOWR/IORD/INTA: RD<-4=IORD ✓ but WR<-5=INTA ✗)
NOR the rail-code system (A0<-rail2=A1 ✗). Possible source-pin convention (CS <- pin 6 of
D105 ЛА3? -- would touch the D9-CS attribution!). RESOLVE NEXT SESSION: cross-reference
sheet-1's D9 Y-output row codes (s1_d9en2) + D105 outputs vs these arrival codes; also
D55/D57 CS rows for the pattern. Until then CS_D5x nets stay as-is.
Also pending: E13 junction re-crop (missed left), D46/D47 rows, power-pin table.

## LARGE GRIND A: video subsystem completion (2026-07-04)
FINDING 22 -- NOTATION CRACKED + D9 Y-PIN REVERSAL BUG FIXED (crop x_d9outs): the per-row
number pairs at chip outputs = "Y-index | pin". 74138 Y pins DESCEND (Y0=15..Y7=7); our D9
pins dict had them ASCENDING (7=Y0..15=Y7) -- every IO CS net sat on the wrong physical pin,
reversed as a block. Sheet: Y4(11) Y5(10) Y6(9) -> CS4/CS5/CS6 (sheet 2 = the three PITs ✓
MAME order), Y7(7) -> CS7 (sheet 3, tape-USART / FDC on .009). Fixed in pins dict + map +
7 nets; LVS IN SYNC, boot PASS (logical order unchanged -- this was PHYSICAL-pin-only, i.e.
exactly the class of bug only the PCB copper would have suffered).
Y3(12) -> dest "4" = CS_D27 route [check]; CS7 free pin = D9.7 for the FDC scaffold.
