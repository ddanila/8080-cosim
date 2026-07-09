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
FINDING 23 (crops s2_d44in + s2_d46 + s2_muxin re-read) -- LABEL CONVENTION: refdes sits at
the symbol BOTTOM (R row). Corrected counter output code map: D44 -> codes 1-4, D45 -> 5-8,
D46 -> 9-12, D47 -> 13-16 (CO cascades D44->D45->D46->D47). CONSEQUENCE: D42 ИР16 ins
(codes 8,7,6,5) = D45.QD-QA; D43 ins (codes 4,3,2,1) = D44.QD-QA -- the ИР16 pair latches
the VIDEO COUNTER state (char/line position), NOT D8's bank byte. The sheet-1-derived
BSEL0-7 nets are near-certainly WRONG (cross-sheet code coincidence); D8's real consumers
are sheet-1-local (RAM/ROM gate zone). D44 details: parallel ins A/B/C/D GROUNDED (preset
0); LD <- D34 ЛП5 XOR out(8); B1 <- node A; C1 <- rail from above. D47 ins <- codes 3,4,5,6
(mixed D44/D45 taps?) or an S3-bundle collision -- unresolved.
NEXT SESSION = SHEET-2 RAIL-CODE REGISTRY: bundle-aware crops of each vertical rail group
(counter->mux column, S3 column, ИР16 column, E13/E14 junctions), building a code ->
(source pin, dest pins) table BEFORE any rewiring. Then one consistent commit: D42/D43
input rewire (+BSEL removal), D50/D51 A/B mapping, S3+R40-45+E13/E14 components, G-enable
source, MA pin-order fix with va-path treatment.
FINDING 24 -- SHEET-2 RAIL-CODE REGISTRY (session 2) + ARCHITECTURE RESOLVED:
TWO vertical bundles co-run with same code numbers: (a) BA rails (codes 1-16 = A0-A15),
(b) video-counter bundle (codes 1-16 local: D44->1-4, D45->5-8, D46->9-12, D47->13-16).
MUX TABLE (code|pin, from reg_* crops):
  D48 (CPU): A1-A4 <- BA {1|2, 2|14, 3|11, 4|5}; B1-B4 <- BA {10|3, 14|13, 12|10, 11|6}
  D49 (CPU): A <- BA {5..8}; B <- BA {13|3, 15|13, 16|10, 9|6}
  D50 (vid): A1-A4 <- VA {1,2(extrap), 3|11, 4|5}; B <- VA {10|3, 14|13, 12|10, 11|6}
  D51 (vid): A <- VA {5|2, 6|14, 7|5, 8|11}; B <- VA {13|3, 15|13, 16|6(?), 9|10(?)}
  => COLUMN SCRAMBLE IDENTICAL on both pairs: col bits order {*9,*13,*11,*10 | *12,*14,*15,*8}.
  Behaviorally neutral (same cell mapping CPU & video) -- THE safe recipe for the pin-accurate
  rewire: apply drawn A/B/Y orders to ALL FOUR muxes at once + route the HDL video fetch
  through the same mapping (or permute dram va indexing equally). Earlier boot failure =
  one-sided permutation, now explained.
E13 = 4 posts: 1-3 jumpered, 2->node A(+5), 4->GND; post1 <- code 8 zone (VA7/BA7 strap --
32/64K video size?). D51.S <- separate post (E14 zone), D50.S <- wire 10 (D41.QA).
D42 ins <- VA {8,7,6,5} = D45.QD-QA; D43 ins <- VA {4,3,2,1} = D44.QD-QA (video-state latches).
STILL OPEN: G-enable sources for each pair (video-cycle alternation), D47 preset codes 3-6
namespace (S3 vs VA), D48/D49 S source, D44 C1 clock source chain.
NEXT: implement the one-commit rewire: BSEL removal + D42/D43 <- counters; S3+R40-45+E13/E14
components; all-four-mux pin-accurate A/B/Y + va-path treatment; then G/CK/LD sources.
FINDING 25 -- THE BIG REWIRE EXECUTED (one atomic commit):
- BSEL0-7 killed; D42/D43 <- VA bus (D45/D44 nibbles) per registry.
- ИЕ7 re-pinned to real 74193 (old invented pinout had D44.8/D48.10/D49.10 supply collisions).
- VA0-15 nets: counters -> ИР16 latches + D50/D51 mux A/B per drawn code|pin tables.
- All four muxes pin-accurate: drawn A/B input orders + Y->MA (4,12,9,7) on both pairs;
  CPU col map: MA{0..7} = BA{9,13,11,10,12,14,15,8}; video identical (symmetric).
- va-treatment: dram_64kx1 un-permutes the raw row byte internally (row_lin) -- mem[] stays
  CPU-linear, tbs + video port untouched. BOOT byte-identical THROUGH the real scrambled path.
- S3(DIP-6)+R40-45+E13 as real components; S3.3-6 -> D47 presets; E13 strap 1-3, 2=+5, 4=GND.
- 189 matched nets; 248 total; boot PASS all 6 stages.
Positions: S3 (63.5,182.4) [emaplaat S3 box -- NOTE: S1 reset button had squatted this spot;
S1 needs its real bracket-edge position next]; E13 (104,188); R40-45 row approx.
FINDING 26 -- SOURCE CHASES (crops s2_d44clk, s2_sg2):
- D44.UP <- long rail "4" from the top-left oscillator/divider zone (mesh tap; exact emitter
  queued). D34 ЛП5 + C5 560pF beside it = the LD-pulse RC generator.
- E14 (4 posts, at D51): 2=+5, 4=GND, post3 -> D50/D51 G (tied) = THE VIDEO-MUX ENABLE STRAP.
  Netted VID_MUX_G {E14.3, D50.15, D51.15}; HDL tri1 boundary (strap-default disabled) --
  boot stays identical while the real jumper is now first-class.
- E1 (posts at DRAM edge): 1=+5(node A), 2=MA rail 28 (MA7) = the 32K/64K DRAM-size strap.
  P5V += E1.1; MA7 += E1.2.
- R54/R55/R56/R58 5.1k pullups -> rail "E" (DRAM DO bus pullups?); sheet-1 arrivals bundle
  at bottom: -CS4, A8, A9... (CS4 route confirmed).
- STILL OPEN: D48/D49.S exact source (kept phi1 [assumed]), D48/D49.G rail source, rail-4
  emitter, E13.1 connection, D45/D46 preset rows, E14.1.
190 matched nets; 176 footprints; boot PASS.
GRIND-A CLOSEOUT SLICES (2026-07-04):
SLICE 1 ✓ D44.UP <- PST CLK = D59 ring section 3->4 (buffered crystal osc out). The "rail 4"
label = source-pin-4 convention. OSC net += D59.3; new PST_CLK net; ln1_osc grew i3/o4.
SLICE 2 ✓ E13 = CPU-mux G strap (at D48; posts: 1-3 strapped, 2=+5, 4=GND, 3 -> D48/D49.G).
Net CPU_MUX_G; HDL tri0 boundary (strap-enabled default). Symmetric with E14 (video pair).
D48/D49.S feed = a vertical at x~2050 from below [phi1 semantics; exact rail queued].
SLICE 3 ✓ D44+D45 preset nibbles GROUNDED (drawn); LD shared rail = D34 ЛП5 XOR-RC-XOR
pulse gen (D34.1=+5, C5 560pF RC). D34 promoted to netted chip (LP5_XOR); net CTR_LD
{D34.8, D44.11, D45.11}; counters now LOAD via the real D34 path (tri0 RC boundary).
S3_1/S3_2 -> D46 presets [likely; D46 preset rows still unread].
REMAINING LOOSE ENDS (for the freeze review): D48/D49.S exact rail; D46 preset rows;
E14.1/E13.1 rail IDs; D34 sect-1 inputs (4,5); D42/D43 CK/LD (still DOTCLK16M/VID_LD
[assumed]); R54-58 rail-E pullup zone; counter R (reset) rail source.
LEFTOVER SESSION (post-grind-C):
- D94 `.113` assignment from this session was later retired: D94 is the
  .009-added `ДГШ5.106.092` PROM, still dump/programming-disk pending.
- ppi0_pc declaration-order boot break fixed (the grind-C commit was transiently red).
- D53 zone read (crops c1_d53/c1_d53b): selects A<-E2.2, B<-E3.2 ✓ (beeper nets confirmed),
  C+G2 grounded (netted), G1<-above-rail, G3<-left-rail [queued]. Outputs Y0-Y3 -> R49-52
  (100R series) -> strobe rails {14,13,12,11} -> R53-56 5.1k pullups -> rail E.
  **RAS = Y3 -> rail 11 ✓ (our net verified). CAS CORRECTION: DRAM C <- rail 15 which is NOT
  a D53 output -- bank-gated CAS from the D92 ЛЕ4 NOR zone [next read]. CAS/CAS0-2 provenance
  downgraded accordingly.**
- D52 (5th КП14) verified: G grounded (always on), S <- В/А long rail, outs -> E2/E3 ✓.
- R49-R56 added as placed netless parts (series/pullup chain; nets pending).
ASSUMED CENSUS AT FREEZE-REVIEW START: 16 nets (list in git; 5 clock-mesh, 4 CAS-family,
2 FDC-IRQ, REV/RAM_SEL pair, M5V, PIT_BAUD, RAM_RD_OE-continuity).
BITE 1 (crop b1_le4): CAS BANK-GATING STRUCTURE READ: D92 ЛЕ4 = 3x 3-in NOR, outs 12/8/6,
input codes sect1{2,13,1} sect2{11,10,9} sect3{3,4,5}; + D39 sect(4,5->6) = the 4th gate ->
four bank-CAS drivers = NOR(cas strobe rail, bank select). Bank selects almost certainly the
mem-mode latch bits (MAME mode[3]=fall-through-RAM ✓ semantics). REMAINING for full rewire:
the out->bank-row (CAS0-3) assignment + rail-15 continuity + the bank-select rail IDs --
ONE more read session (crop right/below of b1_le4 where outs 12/8/6 travel to the array).
Bites 2 (RAM SEL arrival) and 3 (mesh details) untouched -- queued.

BITE 2 (crops b2_*: ramsel_wide, d92_left/right3x, above_d39, d39out3_4x, d52_zoom/feeds,
d53g_zoom, r49_rails, rails1516_up, chain_west, ramsel_junction, g1_trace, d46_presets)
== the D92/D39/D52/D53 RAM-strobe cluster, read end-to-end. SUPERSEDES the bite-1 guess:
D92's outputs do NOT drive bank CAS rails -- they stay inside the cluster.

D92 ЛЕ4 (7427 3x 3-NOR) = CPU-RAM-access detector, cross-coupled:
  sect A (2,13,1 -> 12): 13 <- "-MRD" (wire 11 ✓ = our W11_D7_D92), 1 <- "-RAM OUT EN"
    (wire 13 ✓ = W13_D13_D92), 2 <- gate-T. out12 -> own pin 11.        [read strobe NOR]
  sect C (3,4,5 -> 6): 4 <- "-MWR" (wire 19 junction; = MEMW net), 5 <- "-RAM SEL"
    (<- D6.11 RAM_N per the "(1)" sheet-1 label), 3 <- gate-T. out6 -> own pins 9+10 (tied).
  sect B (11,10,9 -> 8) = NOR(read, write) = "no CPU RAM access" -> D39.5.
  gate-T = D92.2 = D92.3 = D39.1 common vertical, continues NE at ~(715,1885) [pending].
D39 sect3 (1,2->3): 2 <- rail 1 [pending]; out3 -> rail 4 [fanout pending] AND own pin 4.
D39 sect4 (4,5->6): NAND(sect3, D92.8) -> long dogleg (y1973, x717 down, y2322) -> D52.1 B/A.
D52 КП14 #5: A1/A2 <- µP ADDRESS bundle codes 8,9 = BA7/BA8; B1/B2 <- VIDEO ADDRESS bundle
  codes 8,9 = VA7/VA8 (bundle labels read literally on the sheet); G(15) grounded;
  Q1->E2.1, Q2->E3.1 ✓. => D53 A/B = address bit 7/8 of whichever side owns the cycle.
D53 ИД7: G2 grounded ✓, G1 <- line from NW [pending], G3 <- long west line [pending -- was
  wrongly assumed = RAM_SEL; detached]. Y0-Y3 -> R49-52 (100R) -> rails 14/13/12/11, each
  with R53-56 5.1k pullup -> rail E. Rail 11 = RAS ✓ (all 32 R pins). Rails 14/13/12 =
  expansion-bank CAS strobes [bank-column taps pending array read].
**CAS RESOLVED (populated bank): rail 15 = D36.11 (ЛА12 = 7437 buffer NAND, ins 12=13 tied,
  west source line pending) -> R57 (series) -> rail 15; R58 5.1k pullup -> rail E; taps:
  DRAM C (D84-91), D36.1 (strobe-chain feedback), "VIDEO CYCLE" branch to grid (2,3).**
Strobe chain: D36(2,1->3) ins: 2<-rail 17, 1<-rail 15(=CAS feedback); out3 -> D33.11 ->
  D33.10 -> D36.10; D36(10,9->8): 9 [pending], out8 -> rail 16 [dests pending; WE-shape?].
Rail E identity RESOLVED: E = the strobe-termination 5.1k pullup rail (R53-58 common).
D46/D47: common LD vertical (netted VID_HI_LD); driver = D59 sect 13->12 output labeled
  "LOAD" [likely, path not continuously traced]. D46.R + D47.R grounded ✓ (.clr ties ✓).
  D46 presets: code 2 -> pin 9 (D) [read], code 1 -> pin 10 (C) [row-adjacency assumed]
  = S3.2/S3.1 -> the D46 pair, completing the S3 -> D46/D47 preset picture.
  D47.DOWN (pin 4) <- arrow labeled "A" (off-region; D46.DOWN presumably same) [pending].
NETTED: RAM_SEL={D6.11,D92.5}; MEMW+=D92.4; D92_RD_NOR/D92_WR_NOR/D92_NOACC/D39_MEMCYC/
  D92_GATE_T/VID_CPU_SEL; D52 ins on BA7/BA8/VA7/VA8 + GND; CAS rewired (D53.13 out;
  D36.1/R57/R58 in) + CAS_PRE/D36_CAS_IN/D36_D33/D33_D36; RAS through real R52 (+R56);
  D53 Y-ladder + RAIL14/13/12 + RAIL_E; S3_1/S3_2 += D46 presets; VID_HI_LD.
  HDL: la3_gate 4th section, la12_gate 4 sections, ln1_dual 11->10, net_boundary cell
  (series-R / unresolved-feed LVS separator), D52 real ins (inert: E2/E3 are 2-3), D53.g
  behind boundary. LVS 209 nets IN SYNC; boot 6/6 (pending this run).
ASSUMED CENSUS after bite 2: RAM_SEL, CAS resolved; CAS0-2 upgraded to partially traced
  (sources = rails 14/13/12 via Y0-2, only the rail->bank-column assignment pending).
OWNER-TERRITORY items added: rail-15 continuity at the array; rail 14/13/12 -> bank columns;
  D53 G1+G3 feeds; D36.9 + D36.12/13 sources; rail 16 dests; rails 1/4/17 + gate-T; "A" line.

ARRAY READ (crops arr_topleft/topright/seam/col1_locator) == the DRAM array pin-code system,
read directly. The rail map that falls out:
  rails 21-28 = MA0-7 (muxed address, A0-A7 pins 6/12/13/5/10/7/11/9 ✓ our MA nets)
  rails 31-38 = DI (= DB inter-sheet codes ✓), rails 1-8 = DO (RDO bus ✓)
  rail 11 = bank-0 RAS (D60-67) <- R52 <- D53.Y3      rail 12 = bank-1 RAS (D68-75) <- R51 <- Y2
  rail 13 = bank-2 RAS (D76-83) <- R50 <- Y1          rail 14 = bank-3 RAS (D84-91) <- R49 <- Y0
  rail 15 = CAS, SHARED by all 32 C pins              rail 16 = W, SHARED by all 32 W pins
**STRUCTURE INVERTED vs all prior guesses: R is per-bank (bank select by RAS decode via the D53
ladder), C and W are common. Former assumed nets CAS0/1/2 DISSOLVED -- they never existed.
The populated bank D84-91 = rail 14 = D53.Y0 (sim scaffold re-homed; boot byte-identical).**
W rail (16) driver = D36.8 (strobe-chain write leg; D36.9 qualifier line pending). MEMW no
longer touches the DRAMs directly -- it keeps the CPU-side strobe + D7.2/D92.4 taps; sim
carries we_n = MEMW through a net_boundary (documented in W_RAIL16 src; D36 pin 8 pinmap-omitted).
D42/D43 = PIXEL SHIFT REGISTERS (3rd, geometry-anchored reading of the zone): parallel ins =
DO rails (D42=RDO7-4, D43=RDO3-0; D67.DO enters D42.D directly on the sheet), D43.Q->D42.DS ✓,
CK = ctrl-rail 3 (dot clock; DOTCLK16M taps confirmed), LD = ctrl-rail 6 = D38.6 -> D59.13
(LOAD_PRE; ex-assumed VID_LD net RESOLVED and merged), G <- ctrl-rail 8 [pending],
Q -> D37 inverter -> analog video mix. Finding-24's VA-tap reading = the reused-code trap.
ASSUMED CENSUS after array read: RESOLVED this session: RAM_SEL, CAS, CAS0/1/2 (dissolved),
VID_LD, RAS (fully traced per-bank). Remaining: PHI2TTL, D39Y, DOTCLK16M (D56/D103 end),
REV, M5V_DERIVED, PIT_BAUD, RAM_RD_OE (continuity), FDC_INTRQ, FDC_DRQ.

BITE 3 (crops b3_*): clock-mesh + PIT + power-corner reads.
- **PHI2TTL RESOLVED**: gate-T = Ф2TTL! The D35 pin-13 node (R35 330 + C29 56p + R106 910 RC
  shaper; passives not yet placed) = the "Ф2TTL" rail at y~1296 -> D39.1 + D92.2/3 (the D92
  strobe NORs are Φ2-gated) + "(1)" exit to sheet 1 [sheet-1 pin = D13 zone, pending].
  D35 sect 13->12 = the OC MOS-level Φ2 driver (out 12 = Ф2, code 14, R36 360 pullup, ->(1)).
- **D39Y RESOLVED**: drawn D39.11 -> D38.10+13 (tied NAND ins; d39_d38 + gatet_up2 agree).
- **DOTCLK16M half-resolved**: D56 АГ3 = 16MHz astable (2 one-shots cross-coupled, R47 20k/C7
  560p + R59 33k/C8 15n); output leg = sect-1 Q_N (pin 4; pin 13 was a MAME guess, not drawn);
  16MHz rail -> D103.2 CK confirmed. D42/43 CK taps already confirmed (array read).
- **Rail "A" = +5V** (power corner "A <- +5V"): D46/D47 DOWN pins, D57 G1/G2 (PIT gates), and
  R61 12k -> D56.3 CLR are all +5 ties. VID_CTR_DOWN dissolved into P5V; HDL 1'b1 ties correct.
- **PIT_BAUD upgraded**: D57.OUT0 -> "BAUD R." labeled line -> pin 9 = D11 TxC (drawn);
  D11.25 RxC fork [assumed at UART end]. Other named PIT lines: SOUND(->10), SYNC B.(->12),
  1.23M(->13), 2M(->8) -- destinations queued. D55.OUT2 -> "VERT.SYNC.DE..." ✓ cascade story.
- **POWER-LETTER SYSTEM (power corner, QUEUED REWORK)**: A=+5V, B=+12V, D=-5V(from connector),
  E4 jumper: +12(B)/+5(A) -> rail G="+12/5V" -> array VDD; E5 jumper: -5V(D) -> rail H -> array
  VBB; E = array ground rail (one-point strap to GND); C35-53 = G<->E bypass group, C54-72 =
  E<->H group, C34 = H<->F. **= the РУ3(16K,+12/-5/+5) vs РУ5(64K,+5) POPULATION OPTION** --
  explains 4 banks, E2/E3 strobe-source jumpers, and means array power pins + C35-72 caps must
  be re-netted through E4/E5 (currently plain P5V/GND) before routing. M5V_DERIVED: -5V arrives
  from the connector here; the D1/R19/VD5 sheet-1 derivation guess needs its own read.
- REV: not reached this session (needs the sheet-1 D6 zone read) -- next on the table.
ASSUMED CENSUS after bite 3: resolved PHI2TTL, D39Y, VID_LD(+array), PIT_BAUD; DOTCLK16M now
half-traced (D56.4 read-90%). Remaining: DOTCLK16M(residual), REV, M5V_DERIVED, RAM_RD_OE
(continuity), FDC_INTRQ, FDC_DRQ + the queued power-rail rework.
- REV (bite-3 tail, crop b3_rev_zone): D6 РТ4 outputs drawn+labeled: D0(12)="ROM", D1(11)="RAM"
  (= -RAM SEL ✓ closes the D92.5 story from the source side), D2(10)="REV", D3(9)="ROE (2)";
  all OC with 1k pullups (R11..). REV line heads east toward gate rows 12/13 [dest pending];
  D16.20 end still assumed. ROE crosses to sheet 2.

CHASE SESSION (items 1-4; crops c4_*):
1. ARRAY POWER REWORK LANDED: RAIL_G {E4.2 + DRAM pin-8 x32 + C35-53.1} (+12/5V option),
   RAIL_E grew {DRAM pin-16 x32 + cap commons} (array ground, one-point GND strap = net-tie
   at layout, deferred), RAIL_H {E5.2 + DRAM pin-1 x32 + C54-72.2 + C34.1} (-5V VBB option);
   E4(3-pad)/E5(2-pad)/C34 added + placed near X8 power entry [positions approx]. E1 (MA7 vs
   +5 on pin 9) was already correctly netted -- the РУ3/РУ5 option is now fully modeled.
2. REV: drops S at x~1848 to y~680, runs E into the ROM-socket CS/OE region (= ROM gating,
   NOT video). Exact pin unresolved (D15.CS shows a code-1 rail + open-circle wire junction;
   D15.DE fed from a west line at REV's y). D16.20 still assumed. OWNER-TERRITORY candidate.
   Bonus reads: D9 Y0-3 -> coded rails 1-4, Y4-7 -> "CS4(2)/CS5(2)/CS6(2)/CS7(3)" labeled
   exits ✓; D8 A-rows coded 12-15; D8.E(15) fed via an open-circle WIRE junction [owner item].
3. M5V RESOLVED (traced): X8 has NO -5V pin; M12V -> R19 470R -> "-5B" node, VD5 zener to
   GND (drawn exactly as netted); feeds CPU VBB D1.11 + rail D -> E5 -> array VBB option.
4. D52 codes RE-CONFIRMED at 5x: 8 and 9 (not 15/16) -> BA7/8 vs VA7/8 stands.
   **D53 G-FEEDS RESOLVED (crop c4_g3_src, exact y-matches): G1(6, active-high) <- D39.6 =
   VID_CPU_SEL (memory-cycle qualifier); G2A_N(4) <- Ф2TTL (strobe window); G2B_N(5)=GND ✓.**
   HDL: real G pins wired for connectivity; DRAM-enable semantics moved to SIM-ONLY
   ram_en_sim leg (lvs.py contract, like SACTIVE/CAS_SIM) -- boot byte-identical.
   Still queued: D36.9 + D36.12/13 west sources, rail-16 fanout check, PIT line dests
   (SOUND->pin10 / SYNC B.->pin12 / 2M->pin8 / 1.23M->pin13 far ends).

GRIND SESSION items 1-6 (crops an_*, t6_*, t7_*):
1. ANALOG CORNER NETTED (was the last un-netted subsystem): D34 ЛП5 = SYNC (9,10->8) + SIG
   (12,13->11) XOR outs -> R62/R63 -> VT2 emitter-follower = composite VIDEO -> X4.3 (contact
   601); SOUND -> R66 1k -> VD3 КС147 clamp -> R67 -> R68 -> VT3 base (+R69<-SIG, R70/R71
   bias, C13); VT3/VT4 RF modulator can (R72 33 supply, R73 4.7k adj, R74/R75, C9-C15, L1
   tunable 1/5-turn tap) -> R76 300 -> HF -> X4.5 (contact 701), R77 100 load. 28 parts +
   14 nets + placements added [positions/joints approx -- refine vs photos]. X4 = video/RF
   connector (socket type pending). CTR_LD SECTION SLIP FIXED: LP5 sect(1,2->3) -> D34.3
   (pin 8 = the SYNC out; old pinmap had impossible 1,2->8). PIT "SOUND" source pin pending.
   Re-confirmed drawn: RAM_OUT_EN -> D37.4, -MRD -> D33.3->4 -> D37.5, D37.6 -> D58.OE dir.
2. D36.9 <- "(1) WR" = MEMW (y-match) -> the W-strobe = NAND(WR, CAS-delay) -> rail 16 ✓
   closes the write-chain logic. D36.12/13 driver = a mesh-bundle vertical from the D40
   divider zone (crosses Ф2TTL without a dot; one hop from closure) [pending]. D38 sect-2
   ins = unlabeled long rails [boundary]; D41 parallel ins off-crop [boundary]. Bonus: W10
   (D41.13 -> wire 10 -> D50.1) drawn-confirmed. D103.11 = 1.23MHz divider out; D103.CO ->
   D33.1->2 (all six D33 sections now accounted); D103.LD <- wire junction [owner item].
3-5. S3_1 code-1 glyph READ (adjacency confirmed); D56.4 -> 16MHz bend CONFIRMED (DOTCLK16M
   fully traced; one "14" far-end tap unidentified); PHI2TTL sheet-1 arrival pin NOT chased
   (label hunt on sheet 1 = poor ROI) -> owner/queued.
6. WIRE CROSS-CHECK (emaplaat harvest vs schematic reads): confirmed both-ways: 9 (SYNC),
   10 (QA->D50.sel ✓ drawn), 11 (-MRD ✓ drawn), 12 (RAM OUT EN), 13 (-RAM OUT EN -> D92 ✓
   drawn), 19 (-MWR junction ✓ drawn), 8 (STSTB). Schematic-side wire junctions NOT yet in
   the harvest: D15.CS open-circle ("1"-coded rail), D8.E, D103.LD, D47.LD -- these are the
   3rd-layer wires the owner should verify. Wires 14+7, 2, 1 posts harvested at the right
   edge (251,195-228) -- endpoints not yet schematic-matched [queued].
ASSUMED CENSUS after this session: REV (dest), RAM_RD_OE (continuity), FDC_INTRQ, FDC_DRQ
+ soft items (SOUND source pin, D36.12/13 driver, "14" tap, D38/D41 ins, PIT line far ends).
