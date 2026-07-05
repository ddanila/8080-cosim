# Grind backlog — after the arti.ee / j3k materials sweep (2026-07-04)

## New reference materials pulled (ref/)
| file | what it is | grind value |
|---|---|---|
| `ref/schematics/es101_emaplaat.pdf` | **ДГШ5.109.006 СБ — the OFFICIAL factory assembly drawing of our board** (vector-quality; board mark 7.102.100; 310mm dim; mounting-variant notes; VT1/VT3/R73/C98 mounting details; numbered factory wires DRAWN with поз. callouts) | ★★★ replaces photo-derived placement |
| `ref/schematics/es101_nimekiri_komponendid.pdf` | ДГШ3.031.006 ВП — purchased-parts register, per-module counts (11 pp) | ★★★ every passive value cross-checkable |
| `ref/schematics/es101_klaviatuur.pdf` | keyboard unit drawings (7 pp) | ★ X9 signal cross-check |
| `ref/firmware/JUKUROM0/1.HEX, BAS0-3.HEX` | ROM dumps incl. 4× BASIC ROMs (arti.ee/roms) | ★★ ROM-socket decode story |
| (PSU toiteplokk.pdf: 403 — retry later; manuals kasutusjuhend 1-3 not pulled, part 3 = 42MB likely техописание) | | |

## New grind items (desk-doable), by leverage
1. **Placement re-base against the СБ assembly drawing** — replace ~60 approx passive/jumper
   positions (analog corner grid, E4/E5/C34, R40-45, R49-58, S3...) with drawing-true spots;
   verify all 108 D-positions + notch orientations (СБ shows them); read the E1-E14 posts.
2. **X4 → X6/X7 correction**: the video + RF outputs are TWO top-edge sockets (X6, X7) on the
   СБ, not one 4-pin header; re-refdes, re-place, split VIDEO_OUT/HF_OUT accordingly. XL1
   (near C12/E?) to identify.
3. **Factory-wire routing from the СБ**: the numbered wires are DRAWN as diagonals with поз.
   callouts (166-182 range) — cross against docs/emaplaat-harvest.md wire list + the photo
   BODGE-TRIAGE (H1/H2/H3 = likely these factory wires, not bodges!). Wires 1/2/7/14 posts
   at the right edge should be matchable now.
4. **Passive-value census vs ДГШ3.031.006 ВП** — per-module counts (e.g. 0.047µF ×3 ✓ our
   C9/C11/C14; 56pF ×4; 560pF ×2 ✓ C7...); catches wrong values and MISSING passives; also
   settles C73 trimmer (КМ-5а-П33-24пФ?) and zener types.
5. **ROM-socket decode from the BASIC ROMs**: 8 sockets D15-D22, dumps now local (JUKUROM0/1
   = the 16K BIOS ✓ have; BAS0-3 = the +32K BASIC set) — disassemble entry/banking to pin the
   per-socket CS map (closes the "code-1 rail at D15.CS" and the eprom_socket cs_n gaps, and
   possibly REV's real role).
6. **Mounting-variant notes on the СБ** (items 3: варианты IIa/IIб/VIIa...) — transcribe;
   they encode footprint orientation/lead-forming per part family (silk/assembly fidelity).
7. **Manuals** (arti.ee): Russian 3-part kasutusjuhend — part 3 (42MB) likely contains the
   техническое описание (theory of operation, timing diagrams, adjustment procedure) =
   answers for the RAS/CAS/refresh timing questions and the RF can alignment. Pull + mine.
8. **j3k / community**: j3k.infoaed.ee (EKDOS docs, MAME notes, disk-format docs → FDC
   subsystem verification); ELFA + zx-pk forum threads linked from there = possible owner
   measurements (FDC wiring, IRQ mapping) that could close FDC_INTRQ/FDC_DRQ WITHOUT
   waiting for our own board measurements.

## Unchanged owner-territory list
REV final pin, RAM_RD_OE continuity, FDC_INTRQ/DRQ, D8.E/D103.LD/D47.LD wire junctions,
rail-15/E-strap continuities, PIT "SOUND" source pin, D36.12/13 driver (one hop),
PHI2TTL sheet-1 pin, "14" tap on the 16MHz rail.

## СБ grind session 1 (2026-07-04) — banked
- **Calibration**: СБ 200-DPI render: board edges L=1670 R=6581 T=1242 B=5457 px -> 15.84
  px/mm (310.0 x 266.1 ✓). mm = (px-left|top)/15.84.
- **REVISION CAVEAT (important)**: this СБ = board 7.102.100 = the ДГШ5.109.006 TAPE revision.
  Our board = 7.102.158 (.009 FDC). Central/left/power zones shared; the top-right quadrant
  (D93-D106, R78-R92, C16-C22, E10, S4, X5) is TAPE-era there — verify our FDC quadrant
  against the PHOTOS, not this СБ.
- **X4 -> X6/X7 applied**: X7 = video socket (x~258.5, top edge, contacts 601/602), X6 = RF
  socket (x~288, top edge, поз.18 ring, 701/702). X5 = third top socket (tape-era DIN?) — not
  netted. XL1 = likely the filled coax/mount pad in the VT zone [pending].
- **Analog cluster re-based to the real zone (mid-right x260-300 y95-125)**: VT4 (265.0,98.4),
  R73 trimmer w/ special mount (281.9,102.7), VT3 (294.6,105.6), VT2 (280.5,124.8), VD3
  (298.6,118.2) read precisely; R62-77/C9-15/L1 grid moved into the zone (improved approx —
  exact spots need a СБ detail read + photo check).
- **Factory wires CONFIRMED DRAWN on the СБ**: diagonals with end-number labels — wires 5, 6
  (X6/X7 area -> S4 zone), wires 3, 4 (RF/VT zone, one crossing R73's mount circle), wire 11
  span matches the harvest. The photo "bodge" wires (H1-H3, BODGE-TRIAGE.md) are therefore
  FACTORY wiring items with поз. numbers (166-182 range) — full endpoint table = next СБ pass.
- **Parts register page 1 (caps) spot-checks**: 0.047µF x3 ✓ (C9/C11/C14), 56pF x4 (C29,C13+2
  [find]), 560pF x2 ✓ (C7+1), 0.15µF x20 (bypass fleet), 24pF П33 x1 (C73 zone), 910пФ/220пФ/
  150пФ/160пФ singles [locate]. Full census = next pass (pages 2-11: R/D/VT/L).

## СБ grind session 2 — power corner + posts
- Shared-zone AUTHORITY CONFIRMED: R19 (44.5,220.2 vs ours 44.4,220.7), VD5, C73 (58.3,241.4
  vs 58,241.5), Z, X8 (x~24, pins 62/61/60/59), R4 -- all match photo-derived spots ≤1.5mm.
  The .100 СБ is authoritative for shared zones of the .158.
- FIXED from СБ: E4 (42.9,226.5), E5 (50.5,226.1) [were 38,247/38,242]; E2 (61.6,215.5),
  E3 (54.6,215.5) [were mis-entered at x 217.5 -- D52 itself was already right at 58.3].
- Wire posts read: "2" = (252.7,199.9), "1" = (252.7,205.2) with ⊗ symbols, flanking R60.
  Harvest y's (219.9/227.6) differ ~20mm -- re-derive the harvest y-formula against СБ [queued].
- NEW parts seen on СБ, absent from board.json (census additions pending wiring reads):
  VT1 (250.5,218.9) + VD4 + R90/R91 (beeper/reset cluster), R48, R60, C92 (29.9,215.0),
  C93 (22.5,240), C94 (analog zone), C96/C98 (mesh zone), D105 (~35,190), D107?, X5 socket.
- C34 not yet located on the СБ [queued]; XL1 = the coax mount pad near VT zone [queued].

## Census pass 1 — МЛТ-0.125 resistors (ВП лист 5, ДГШ5.109.006 column)
33R x1 (R72 ✓) | 75R x4 (**candidates R49-R52 — see flag**) | 100R x3 (**FLAG: we model 5x100:
R49-52+R77; either R49-52 = 75R and the r49_rails "100" glyph reads are wrong, or the .009
differs — re-crop the ladder values + check photos**) | 200R x2 | 270R x1 | 300R x1 (R76 ✓)
| 330R x1 (R35 ✓) | 430R x2 (R65+R74 ✓✓) | 620R x1 | 820R x1 | 910R x1 (R106 ✓) | 1k x20
(pullup fleet ✓) | 1.2k x1 (R32 ✓) | 1.5k x1 | 2k x12. NB: no 360R on this page — the HDL
"R36/R37 360" phase pullups need a value re-read [flag]. Remaining ВП pages (2-4, 6-11:
caps cont., >2.4k resistors, diodes/transistors/L/switches) = census pass 2.

## Census pass 2 (ВП листы 5-7) + ladder flag resolution
- R49-52 re-read at 5x: unambiguous "100" x4 on the Э3 -> the Э3 and the ВП (100R x3, 75R x4)
  CONTRADICT each other. OWNER ITEM: measure the RAS-ladder series R's (75 vs 100).
- **R73 = СП3-22б-0.125 4.7k TRIMMER x1 ✓** (matches the СБ special mount + the drawn arrow);
  footprint switched to a trimpot stand-in.
- **VD3 + VD5 = КС147Г x2 ✓** (both zeners, as modeled); **КД522А x2 = VD1/VD4** (reset/beeper
  diodes; census additions pending wiring).
- **МЛТ-0.25-360R x2 = R36/R37 ✓** (phase pullups vindicated, 0.25W series); 0.25W also: 470R
  x1 (R19 ✓), 8.2R x1 [locate], 120R x1, 360R x2.
- MLT-0.125 (.006 column) cont.: 3k x3, 4.7k x1, **5.1k x9** (7 identified: R53-56,R58,R64,
  R71 -> 2 gaps), 10k x2, **12k x12** (R61 + 11 [gaps!]), 20k x4 (R47 +3), 33k x4 (R59 +3),
  130k x1, 1.8M x1 (osc bias). Pages 8-11 (VT/L/switches/connectors) = pass 3.

## Census pass 3 (ВП лист 8) — semiconductors/misc for .109.006
**VT1 = КТ972А x1** (Darlington beeper driver; part+place added, wiring pending);
**VT2/VT3 = КТ315Г x2 ✓; VT4 = КТ325ВМ x1 ✓** (transistor census complete and consistent).
S1 = кнопка КМ1-1 ✓; microswitches ВДМ1-2 + ВДМ1-6 (S4 added at СБ spot + a second switch
[locate]); **Панель ОНП-НИ-6-16 x3 = three DIP-16 sockets** (РЕ3 PROMs D6/D8 socketed + 1);
speaker = 0.05ГД2 in ДГШ5.884.001 (external unit). Module decode: 087.009 = PSU (КТ828/
КУ202/КД105 rows), 104.015 = keyboard (20x ВМ16-4 key blocks), 884.001 = speaker.
(Earlier "087.009 keyboard" guesses in pass-1 notes -> PSU.) Pages 9-11 = pass 4 (caps
cont/connectors/sockets); L1 not yet found in the register [locate].

## Census pass 4 (ВП лист 9) — connectors/sockets for .109.006
Панель РС-28-8 x8 = ALL EIGHT ROM sockets (D15-D22, 28-pin ✓); **Розетка СР50-73ФВ x2 =
X6/X7 coax ✓✓**; РГ1Н-1-1/-3/-4 x3 = DIN sockets (X5 + 2 [identify; tape-era?]); МРН14-1
розетка x1 = X9 keyboard (14 contacts ✓ our pad row; вилка on the keyboard side ✓).
**FLAG: Резонатор РК170ББ-14ГС-16000к-В = the crystal Z1 is 16 MHz** — reconcile the clock
story (D56 "16MHz astable" vs crystal-sourced 16MHz; D59/D40 divider chain frequencies).
Remaining register pages 2-4,10-11 (caps cont., ferrites, misc) = final pass [queued].

## ROM-socket decode pass 1 (crops rom_cs_zone, d8_outs + .117 content)
- .117 rows 0x00-0x07 = FF -> the D8 pager NEVER selects in 0000-3FFF: D15/D16 BIOS CE story
  (D6 ROM/REV) SURVIVES; the pager drives only the 4000-BFFF window sockets.
- D8 (РЕ3) output pins mapped: D1..D7 = pins 2,3,4,5,6,7,9 (D0 = pin 1, not drawn/unused);
  every output = an open-circle WIRE junction (the R21-28 1k pullup rail zone).
- ROM CS reads: **D17.CS <- code-3 rail [edge], D19.CS <- code-5, D21.CS <- code-7**; evens
  presumed 4/6/8 [adjacent, unread]. OE pins all on common MEMR ✓ (already netted).
- AMBIGUITY BLOCKING THE NETS: two code sets in the zone — D9's Y0-Y3 = codes 1-4 (io-decode)
  vs the D8-output rails; D15.CS "code 1 + wire circle" could be either set. Need ONE careful
  read of the code labels ON the D8-output/R21-28 rails (between D8 and the sockets) to pin
  the D8-output -> socket map; then net ROM_CS17..22 + rewire eprom_socket .cs_n in HDL.
- .117 window values 07/0B/0D/0E = one-cold in bits 3..0 with upper nibble 0 — the bit ->
  drawn-D-number order also needs that read (dump bit order vs D1-D7 labels).

## ROM-socket decode pass 2 (crop d8_rail_codes) — correction
- D15's left side read precisely: address rows coded 1-10 = BA0-BA9 (standard code convention);
  **the earlier "code-1 rail at D15.CS" was a MIS-ASSOCIATION with the A0 row** (and the
  "codes 3/5/7" at D17/D19/D21 CS were likely their A2/A4/A6 row codes). No D9.Y0 conflict --
  that ambiguity is void. R21-28 1k -> "A" (+5V) pullup arrow confirmed drawn.
- D15.CS (pin 20, wire circle) <- the un-coded horizontal from the D6-ROM-line direction ✓
  consistent with the current HDL (cs_n = rom_sel_n); D15.DE (22, dot) <- from below-left.
- REMAINING: the per-socket CS pairing = follow the SEVEN un-coded horizontals from D8's
  outputs (pins 2-9) east to the socket CS pins -- pure line-following, one careful session;
  then net ROM_CS17..22 and rewire eprom_socket .cs_n in HDL (boot-inert, sockets empty).

## ROM-socket decode pass 3 (crop romcs_leg1) — the D8 output-code set + a real puzzle
- **D8 outputs have their OWN code rails**: D1(pin2)->code 6, D2(3)->7, D3(4)->8, D4(5)->1,
  D5(6)->2, D6(7)->3, D7(9)->4 [D0(1)->5 presumed, cut off]. Same numerals 1-4 as D9's
  Y-codes = the two-set reuse, now both sides read.
- **The "1"-labeled horizontal runs into D15.CS** (drawn, unambiguous). D9.Y0=CS_PIC can't be
  it -> drawn evidence says **D15.CS <- D8.D4 (pin 5)**.
- **PUZZLE (blocks rewiring)**: .117 dump rows 0x00-0x07 = FF would then never select the
  BIOS socket -> boot impossible. Candidates: dump bit-order/polarity vs drawn D-numbering
  (РЕ3 OC fuse semantics), row addressing offset, or a third line-set.
- **NEXT-SESSION EXPERIMENT (empirical resolution)**: wire U_D15.cs_n = d8_d[4] (and try the
  bit permutations) in a scratch branch and run boot_check with the real .117 content — the
  cosim decides which reading is physical. Also line-follow codes 2,3,4,6,7,8 to the
  remaining sockets (D16-D22) to complete the map before/with the experiment.

## РЕ3 BLOCKER RESOLVED (local Д1 tables + web research)
1. **The hex files ARE the factory programming tables verbatim** (ДГШ5.106.113Д1 page read:
   matches re3_dgsh5.106.113.hex byte-for-byte) — no dump-polarity/artifact escape hatch.
2. **К155РЕ3 fact (chipinfo.ru): unprogrammed = ALL ZEROS; burning fuses writes 1s.**
   => FF rows = deliberately fully-burned "deselect" rows (outputs HIGH = CS inactive);
   window rows 07/0B/0D/0E = burn only the 1s: one-cold in D3..D0 = active-low selects for
   the FOUR BASIC-bank sockets: **D3(code 8)=4000, D2(7)=6000, D1(6)=8000, D0(5)=A000**;
   D4-D7 left unburned (=0/LOW in window rows) => **CANNOT be wired to ROM CEs** (would
   multi-select/fight) — their code rails 1-4 go elsewhere or n.c. [line-follow to verify].
3. => the "code-1 -> D15.CS" reading was a passing-rail mis-association (2nd such catch);
   **D15/D16 stay on D6 ROM/REV** — consistent with the factory data AND the working boot.
4. Residual: line-follow codes 5/6/7/8 to pin the physical socket order (which of D17-D22 =
   which bank); optional empirical referee = boot_check with candidate wirings.
5. Community: zx-pk.ru thread 27298 (Juku E5101) found — mine for owner measurements [queued].

## ROM-socket decode COMPLETE (window map netted)
Riser-label reads (romcs_band/band2): **D19.CS <- code 5 (D8.D0) = A000; D20 <- 6 (D1) =
8000; D21 <- 7 (D2) = 6000; D22 <- 8 (D3) = 4000** -> nets ROM_CS_{4000,6000,8000,A000}
added, eprom_socket .cs_n wired (boot-inert, sockets empty in sim). Socket rows: top =
D15,D17,D19,D21; bottom = D16,D18,D20,D22. BAS0-3 dumps map: BAS0->D22(4000), BAS1->D21,
BAS2->D20, BAS3->D19 [by file order, verify vs labels/photos]. D17/D18 = the expansion
pair: CS likely D8.D4/D5 (codes 1/2) which stock .117 holds LOW throughout the window --
SAFE ONLY WHILE EMPTY, which is exactly how the board ships [feed read queued; the "code
1 -> D15.CS" mis-association fully explained]. LVS 214 IN SYNC.

## Census pass 5 (ВП лист 2) + boot verification
- Boot 6/6 byte-identical with the ROM window CS wiring in (empirically inert ✓ as designed).
- C12 = КТ-1 2.2pF ✓, C15 = КТ-1 3.3pF ✓, C73 = КТ4-21Б 4/20pF ✓; **КТ4-21Б-1/5pF trimmer
  x1 = the "1/5" glyph in the RF can (was mis-attached to L1 turns) — refdes to locate,
  likely the tank trimmer; L1 note corrected.**
- Bypass fleet is MIXED: 0.15µF x20 + 0.22µF x16 + 0.47µF x17 (our C35-C72 modeled uniform;
  per-position values = census pass 6 vs СБ/photos).
- Tantalums (.006): 10µF x1, 47µF x2, 1µF x2, 22µF x2 (C31-33/C9x family values).
- К155-series page: ЛА3 x1, ЛА18 x1, **ЛН5 x2 (a SECOND ЛН5 exists — locate; D35 + ?)**;
  IC census continues pages 3-4 [queued].
- zx-pk thread 27298 mined: collector-oriented (ROM dump requests, museum contacts) — no
  hardware measurements; arvutimuuseum.ee = contact for dumps/disks. Low priority.

## ROM-socket decode FINAL: all eight CEs are D8 rails; BIOS pair = D15/D16 positions
Crops d17_cs/d18_cs/romfeed_top/romdec_above/trunk_vert/tee_zone/pivot_pixel/cs_de_full:
- **The D8-output group line** (heavy vertical at x~2346, R21-R28 1k pullup ladder on top,
  E6/E7 jumpers in the +5V feed): entry tags **D4->1, D5->2, D6->3, D7->4, D0->5, D1->6,
  D2->7, D3->8**; tag-taps land on the socket CS risers: **D15<-1, D16<-2, D17<-3, D18<-4**
  (D19-D22 <- 5-8 as already netted, connectivity unchanged ✓). The pivotal T-junction and
  the "1"-tap into "20 o CS" verified at 7x; DE (22) is a separate vertical from below.
- **D9 (ИД7) io-decode identity SURVIVES**: its own group line (x~2312, tags 1-4 on Y0-Y3)
  descends to the io zone; Y4-Y7 are the named exports **CS4(2), CS5(2), CS6(2), CS7(3)** --
  CS7 to sheet 3 matches the existing CS_FDC net (io 1C -> ВГ93). Pass-2's "un-coded
  horizontal from D6-ROM" was the mis-read (it followed the DE feed), pass-3 was right.
- **D8.E_N <- D6.ROM_N** (the "12 ROM" junction rail + R11 1k) => D6 answers WHEN (mode-aware
  region via A5-A7 = mode bits, A0-A4 = BA15-BA11), D8 answers WHICH CHIP. Chip-internal
  BA12..BA0 auto-offsets the high map (CPU D800 ≡ chip 1800) -- no extra logic needed.
- **Consequence: neither factory РЕ3 table can be our D8's content.** Both .113 and .117
  leave D4-D7 unburned (OC = permanently asserted): fine only for a BIOS-less expansion-cart
  config. Our board boots from the BIOS pair sitting in the two leftmost field positions
  (photo board #2: 2x ST M2764AF1; six positions beyond are empty holes) = D15/D16 per the
  СБ row order. **Predicted D8 dump** (banked in hdl re3_prom, derived from MAME modes):
  rows 00-03=EF, 04-07=DF, 08-0B=F7, 0C-0F=FB, 10-13=FD, 14-17=FE, 18-1A=FF, 1B=EF,
  1C-1F=DF. Dump the socketed chip to confirm [OWNER, high value].
- Netlist: ROM_SEL rewired {D6.12, D8.15}; REV detached from D16.20 (destination = new chase);
  +4 nets ROM_CS_D15/D16 (D8.5/6) + ROM_CS_EXP17/18 (D8.7/9). HDL: U_D8.e_n <- rom_sel_n,
  content = predicted table; U_D15/16.cs_n <- d8_d[4]/[5]; U_D17/18 <- d8_d[6]/[7];
  decode_prom.rom_n re-semanticized to region enable (equivalence by construction).
  **LVS 217 IN SYNC.**
- NEW CHASES OPENED: (a) REV true destination; (b) D9 input feeds -- drawn selects = trunk
  tags 11/12/13 (BA10-12 as netted ✓) but enables are pins 4+5 BRIDGED <- one line + pin 6
  <- another (scan has IORD->5, IOWR->6, pin 4 n.c. -- pinmap 4:G1 also contradicts the real
  74138 4:G2A_N/5:G2B_N/6:G1); (c) DE rail source (drawn vertical from below: MEMR per
  pass-1 vs ROE per old scan note -- follow it down).

## Census pass 6 (ВП листы 3-4: the IC pages)
For ДГШ5.109.006 (column "на изделие"):
- **К573РФ5 (2Kx8) x8, programming docs ДГШ5.106.040...047** = the .006-era ROM field:
  all EIGHT sockets populated with 2716-class chips, one factory program each (16K total).
  Our .009 board replaces this with 2764-class sockets + 2x M2764 BIOS (photo) -- and our Э3
  sheets draw the 28-pin pinout (A12 on pin 2), i.e. the sheets ARE the .009-side revision.
- **565РУ3Г x32** (16Kx1, 4 banks x 8 = 64K) -- confirms the E4/E5 power-jumper decode
  (+12/-5 for РУ3) as the .006 shipping config; .009 = 8x РУ5 instead.
- **К155РЕ3 x1** (-> programmed part .106.039 = D8). D94 (.092) is NOT in the .006 ВП --
  it arrives with the .009 FDC revision. And the scanned tables .113/.117 carry перв. примен.
  **.106.103** (neither .039 nor .092) => they document a THIRD config's chips; reinforces
  today's conclusion that neither table is our D8's content.
- **К561 CMOS cluster x9: ИЕ11, ИМ1, ИР9, ЛА7, ЛН2 x2, ЛП2, ТМ2, ТВ1** -- none modeled;
  almost certainly the sheet-3 tape/serial subsystem [flag: model gap, low priority for
  the .009 twin since the tape section was superseded by FDC].
- КР580 set: ИК80А x1 (D1), ИР82 x1, **ВА86 x3, ВА87 x3**, **ВИ53 x3** (3 PITs = MAME ✓),
  ВК38 x1, ВН59 x1 (D10), **ВВ51А x2** (2 USARTs = MAME ✓), ВВ55А x2 (D26/D27) [cross-check
  our BOM counts vs ВА86/ВА87 x3+x3].
- К531: ИД7 x1 (D53 ✓), ИЕ17 x1 (D40 ✓ photo), КП14 x4, ЛА1 x1 (photo ✓), ЛА12 x1, ЛН1 x2;
  К555: ИД7 x1 (**= D9 only -- no second 555ИД7, consistent with the ROM-decode finding**),
  АГ3 x1, ИЕ7 x4 (D44-47 ✓), ИЕ10 x1, ИР16 x3, КП14 x1 (+531 x4 = 5 muxes total), ЛА3 x3,
  ЛЕ4 x1 (the decapped one), ЛП5 x1, ТЛ2 x1, ТМ2 x1; К554СА3А x1; КР556РТ4 x2
  (**programming docs .106.037/.038 = D2/D6** ✓).
- Resistors section begins: МЛТ-0,125 20Ом 5% x1 [pages 5+ = passives, already passed 1-5].

## DE-rail chase closed (crops de_rail_follow/de_rail_west)
One vertical (x~2505) feeds both socket rows' DE/OE pins, cornering west at y~1400 into a
long horizontal. The west read is inconclusive at pixel level, but electrics force the
answer: CE (D8, pure address decode) and D6.ROE (address+mode PROM, no strobe input) carry
no read qualification, so OE must bring the read strobe -- during CPU writes into the ROM
region an OE without MEMR would make the EPROMs fight the write data on the buffered bus.
**OE = common MEMR stands** (pass-1 ✓, netlist unchanged); the old scan note "OE <- ROE"
is retired. REV destination + D9 input feeds remain open chases.

## IO-decode cluster FINAL (chases "REV destination" + "D9 inputs" closed together)
Crops d9_inputs/d9_v3_follow/v3_junction/r17_west/d7_feed_origins/rc_stack:
- **REV (D6.10, rail code 2) -> D9 pins 4+5 bridged** (G2A_N+G2B_N) = the io-decoder's REGION
  enable. Reconstructed column: low for BA13-15=000 (ports 00-1F via the 8080 A8-15 port
  mirror), mode-independent. Ports >=20 are genuinely blocked on this board (MAME's 0x80
  mouse must live on the expansion bus).
- **D9.G1 (V3, pin 6) <- R17 200R + C99 160pF <- D7.11**, the ЛА3 section 12,13->11 wired as
  a strobe-NAND on IORD/IOWR (either strobe -> high; 12/13 order assumed): an RC-deglitched
  "io cycle active" enable. The old scan's D9 enables (IORD->5/IOWR->6) and MEM_MODE0->D7.13
  are refuted-assumed; the scan's PROM_EN link D7.11->D6.14 likewise (D6's V1/V2 feed = open
  chase; modeled always-enabled).
- **D6's pins 2,1,15 are the MODE BUNDLE (tags 1,2,3 <- PPI Port C), not BA10/BA9/BA8** --
  the banking mode enters the РТ4 as ADDRESS bits. Nets MEM_MODE0/1 rewired (tag<->PC-bit
  order assumed; tag 3 source unread). decode_prom now takes mode via a[10:8]; the old
  v_en_n mode hack retired (equivalence by construction).
- **Rail 3 (D6.9) is named "-RAM OUT EN"** (not "ROM output enable"): -> D13.1 (К555ТЛ2 hex
  Schmitt inverter -- symbol + census; the dual-4-NAND ТЛ1-shaped model retired) -> D13.2 =
  RAMOUTEN -> sheet-2 D37.4 (export "(2)" code 12). Factory wire W13 (D13.1<->D92.1) merged
  into the ROE net. RAMOUTEN column modeled permissive (= old tri1 behavior) pending РТ4 dump.
- R13/R14 1k = pullups for the REV/-RAMOUTEN OC rails (R11/R12 cover ROM/RAM) [pullup nets
  not yet added]. C99's far plate destination unread [chase]. R17/C99 added to board + PCB
  (approx spot, СБ pending). **LVS 219 IN SYNC.**

## 16 MHz reconciliation (analytical) + sheet-1 identity + bus corner
- **Z1 = РК170ББ-14ГС-16000к = 16 MHz is THE frequency reference** (photo: РК-171 8903).
  CPU: OSC -> D40 ИЕ7, QC = /8 = 2.0 MHz Φ1/Φ2 ✓ (divider ratios consistent only with 16M).
  D56 = the module's ONLY АГ3 (census x1) = 74LS123-class one-shot pair -- it cannot be an
  independent stable "16MHz astable"; read as a pulse-shaper/duty-controller retriggered off
  the crystal rail in the dot-clock path (DOTCLK16M = D56.4 -> D42/D43 ИР16 + D103). Its
  trigger-input feed = one sheet-2 crop [queued]. "2M" labeled line = OSC/8 ✓; "1.23M" ~ 16M/13
  [check the exact divisor when the PIT lines get read].
- **Title block read (s1_bottomband): our schematic IS ДГШ5.109.006 Э3 "Модуль процессора",
  лист 1 из 3**, doc stamp 1167; note "Микросхемы D2,D6,D8,D15...D22 устанавливаются в
  панелях" ✓ = exactly the socketed set. So the .006 Э3 already draws the 28-pin/2764-class
  sockets -- the РФ5-х8 census row is the CONFIG of the .006 build, not a different PCB;
  earlier "sheets are .009-side" note softened accordingly.
- **Sheet-1 right side = the expansion-bus corner: D23/D24/D25 (ВА87 x3 ✓ census) buffer
  BA/DB onto X1 as a Multibus-style set**: -ADR0..F (contacts 122C-117B), -DAT0..7 (132C-129B),
  -INHIB 106B, CCLCK 111C, -IO/M 109B?, -MWC 104B, -MRC 104C, -AMWC 102B, -IORC/-IOWC --
  MAME's "mouse at port 0x80 = Multibus expansion" comment now grounded in copper. D7's other
  ЛА3 sections gate the D25 T/E enables [pin reads queued]. X1 pin-out table = a future
  systematic read for the connector nets.
- Beeper cluster (VT1/VD4/R48/R60/R90/R91): NOT on sheet 1 -- the SOUND path lives on sheet 2
  (PIT -> shaper -> VT1 Darlington -> edge contact -> ДГШ5.884.001 speaker unit) [queued:
  sheet-2 read].

## РЕ3-dump tension sharpened (owner: dumps held correct)
Owner position: the .113/.117 tables ARE the correct РЕ3 contents. Accepting that as a
constraint and re-verifying the trunk at 8x (crop trunk_dots: all eight D8 rows enter the
group line; taps at all eight CS risers hold):
- .117 selects NOTHING at 0000-3FFF (rows 00-07 = FF) and gangs D4-D7 across the whole
  window -- invariant under any row/bit permutation. So with .117 in D8, NO field socket can
  host the BIOS, and D15-D18 are empty parallel-expansion positions.
- The weak link is then the ASSUMPTION "board #2's two M2764s = the BIOS pair in D15/D16":
  board #2 is a donor (DRAM stripped, caps cut); parked chips prove little. If those EPROMs
  are not the BIOS, everything reconciles -- except WHERE the 16K monitor lives becomes the
  new open question (MAME needs it at 0000; no other 28-pin positions seen on the board).
- HDL note: re3_prom keeps the boot-working reconstructed table for the sim (a select at
  0000 is required to boot at all); it is the piece the physical checks will overwrite.
DECIDERS (one measurement each): (1) dump board #2's two EPROMs (monitor vs BASIC vs other);
(2) continuity D8.5 (D4) <-> leftmost-socket pin 20; (3) dump the РЕ3 seated in D8.

## Reconciliation grind DONE: .113/.117 are correct -- and they are not D8/D94's programs
Full write-up in docs/re3-decode.md. Impossibility proven for .117-as-D8 under every tag
permutation, row-address bijection, and population choice (every non-FF value asserts five
rails; no reading yields a 2-chip 16K BIOS map). Factory paper trail agrees: the .006 ВП
assigns D8 = ДГШ5.106.039, the .009 ПЭЗ adds D94 = .092; the scanned .113/.117 belong to the
.106.103 family (наиболее вероятно the V3-gating timing РЕ3 pair -- their FF-idle one-cold-walk
shape is a phase-generator pattern). README/re3-decode/HDL comments corrected; D94's .113
stand-in retired (outputs inert pending .092 dump). LVS 219 IN SYNC, boot 6/6.

## Sheet-2 read batch (300dpi render; crops s2_*)
- **No РЕ3 exists on sheet 2.** The board's three DIP-16 sockets = D2/D6/D8 -> the photographed
  "V3-gating timing PROM" (8904) IS D8 itself; the .113/.117 (.103-family) home is off-module
  (keyboard/peripheral candidate). Yesterday's "V3-РЕ3" candidate retracted.
- **Beeper cluster TRACED + netted**: SOUND = D57.OUT1 (pin 13) -> bundle tag 10 -> R90 2k ->
  VT1 КТ972 base (VD4 + R91 1k clamp to the AVDC rail); emitter-follower (C -> +5V rail A),
  E -> R48 8.2Ом -> speaker edge contact -> ДГШ5.884.001. R60 is NOT beeper: it is the
  FRAME INT 5.1k pullup (right-edge export to sheet 1). AVDC/SPKR far ends queued.
- **PIT2 (D57) rows read**: CLK1 <- "2M" rail tag 8 = D40.Q2 (CONFIRMS the existing
  D40Q2_D33 net); CLK2 <- "1.23M" tag 13 (FRAME_INT endpoint was mame-assumed -> detached;
  net CLK_123M added); G1/G2 -> +5V ✓ (matched existing); OUT0 -> "BAUD R." tag 9 ✓
  (existing PIT_BAUD); OUT2 -> "SYNC B." tag 12 (new net, destination queued).
- **1.23M mechanism closed**: D103 (ИЕ10) divides the 16M crystal rail by 13 (CO -> D33
  inverter -> rail) = 1.2308 MHz — the "1.23M" label exactly.
- **D56 story corrected**: two LONG one-shots (R47 20k/C7 560pF ~5us; R59 33k/C8 15nF
  ~220us), R61 12k = CLR pullup. It CANNOT be a "16MHz astable" — the 16MHz label belongs
  to the passing crystal rail. DOTCLK16M's "D56.4 source" attribution now suspect
  [re-read queued]; D56 trigger feeds queued (likely H-timing one-shots).
- **C12 = КТ4-21Б-1/5pF trimmer** in the L1 RF tank (type fixed); census pass-5 off-by-one:
  the 2.2pF КТ-1 is C11. C15 3.3pF ✓ unchanged.
- ЛН5 tally sheet-2: D35 covers clock pair + right-side export drivers (PDF/FRAME INT/
  SYNC B.R via R39 12k/R60 5.1k) = one chip suffices; **second К155ЛН5 must be sheet 3**.
- Bonus: D58 = ИР82 RAM->bus latch ✓; array chip previously glimpsed as "D94" is D91 ✓;
  E1 strap = D51.Q4 -> MA7 (tag 28) ✓; VIDEO -> contacts 601/602, HF -> 701/702.

## #12 leftovers session (sheet-2 finishers + sheet-3 recon)
- **SYNC_B destination traced**: D57.OUT2 ("SYNC B.", tag 12) wraps around into D56 section-2
  trigger A (pin 10) -> the PIT-timed ~5us one-shot = sync/blank pulse shaper. Net updated
  {D57.17, D56.10}. D56 section-2 B (pin 9) and section-1 B (pin 1) on tied stubs [level
  assumed high]; **R61 12k = CLR_N pullup** (pin 3 solid; pin 11 joins the same row
  [probable]); RC parts netted: R47 20k + C7 560pF (pins 7/6), R59 33k + C8 15nF (15/14),
  Rext far ends -> +5V per АГ3 canon. Section-1 trigger A (pin 2) <- vertical from the
  D54/D55 sync-chain zone [one hop unread]. LVS 314 IN SYNC, boot 6/6.
- **Sheet-3 recon (tape subsystem, .006)**: the К561 CMOS cluster census gap CLOSES here --
  the sheet's own IC table lists К561 ТМ2/ЛА7/ЛП2/ЛН2/ИР9/ТВ1/ИМ1/ИЕ11 + К554СА3 + КР580ВВ51.
  Drawn refdes: **D93 = tape ВВ51** (второй USART), **D94 = К561ЛН2** (hex inverter, sections
  D94.1-6), D95 ЛП2, D96 ЛА7, D97 ТВ1, D98 ТМ2 x2, D99/D100 ИР9, D101 ИМ1, D102 ИЕ11,
  D106 СА3; tape lines -> contacts 501/502/503/504/407/408 (SYNC/REC.DATA/DATA IN/CNTR
  CHECK/TAPE RUN), TAPE RUN INT -> (1). The .009 FDC revision REUSES D93/D94 refdes for
  ВГ93/РЕ3 -- our model's D93=ВГ93/D94=РЕ3(.092) stays correct for our .158 board; the
  drawn .006 sheet 3 is the tape-variant reference [its full netting = out of scope for
  the .009 twin; bank as reference].
- **Second-ЛН5 hunt result**: no ЛН5 symbol on sheets 2/3 beyond D35; sheet-3's TTL table
  entry reads К155ЛП8. The ВП "ЛН5 x2" row needs one re-crop (nk-02) -- possible glyph
  confusion [queued in #13 cycle].

## #13 cycle, part 1 (census closure + pullups + SB-true beeper spots)
- **ЛН5 question CLOSED**: ВП page 2 re-read (typed, unambiguous): К155ЛА3 x1, К155ЛА18 x1,
  **К155ЛН5 x2** — and NO ЛП8 anywhere in the ВП => sheet-3's handwritten table entry I read
  as "ЛП8" is ЛН5. **ЛН5 #2 = a sheet-3 tape-zone chip** (OC recorder-line drivers); the .009
  revision replaces that zone with the FDC, so it is likely NOT populated on our board — the
  .009 twin BOM stays as-is. Page-2 bonus: cap rows match pass-5 exactly (bypass 0.22x16 +
  0.47x17, both КТ4-21Б trimmers x1, the К53 tantalum set, КР140УД1208 = PSU, К155ИВ1 = kbd).
- **R11-R14 1k pullups netted** on the four D6 OC rails: R11->ROM_SEL, R12->RAM_SEL,
  R13->REV, R14->ROE (R13/R14 pairing order assumed — labels flank the twin verticals);
  all far ends -> P5V. Parts + approx spots added.
- **R60 5.1k = FRAME_INT pullup** netted (+P5V); SB-true spot (253.9, 202.7) between wire
  posts 2/1 (post positions re-validated the SB calibration to <0.5mm).
- **Beeper cluster SB-true placements** (crop sb_beeper): VT1 body (247.8,213.8) [old spot
  was the label text], R48 (245.1,207.4), R90/VD4/R91 vertical row at y=216.1
  (x = 251.6/254.1/256.4). PCB regen: 237 footprints, outline-overlap PASS.
- CARRY-OVER to next cycle: the systematic СБ wire-endpoint table, per-position bypass map,
  X1 pin-out table, DOTCLK16M bend re-read, D56 sect-1 trigger hop, AVDC/SPKR far ends,
  CLK_123M rail netting, C99 far plate, D6 V1/V2 feed, mode tag-3, D25 T/E gates,
  SB-true spots for R17/C99 + D56 RC group + R11-R14.

## #13 part 2: the three methodical reads (X1 verified / bypass blocked / wires carried)
- **X1 pin-out table: DONE as a verification pass.** The 300dpi sheet-1 re-read matches the
  existing scan netting LINE FOR LINE (ADR0-F_N -> 124C..117B, DAT0-7_N -> 132C..129B,
  MRC/MWC/IORC/IOWC/AMWC/INHIB/CCLCK/IOM contacts, D23/D24/D25/D29 pin numbers) -- 34 nets
  upgrade from scan-assumed to traced-verified. NEW data netted: the power-contact map:
  +5V -> X1 101A/102A/103A + 107A/108A/108B/108C, X2 227/229/230, X9 5/6 (also drawn:
  X3 307/308, X4 408 -- skipped, X3 pin-scheme mismatch [note]); +12V -> X1 131A/132A;
  -12V -> X1 110A/111A. The -5V generator (M12V -> R19 470R + VD5 zener) was already traced.
  D29 confirmed as the 4th buffer (ВА86, control set). LVS 314 IN SYNC.
- **Bypass per-position map: BLOCKED with evidence.** The Э3 draws the decaps as per-rail
  GROUPS (C35...C53 rail G, C54...C72 rail E, C74...C91 + C94...C98 rail A) with no values;
  the СБ shows positions only; the ВП gives totals (0.15x20 / 0.22x16 / 0.47x17). Group
  sizes (19/19/18+5) do not align 1:1 with value counts -> per-position values need the СБ
  спецификация page or macro photos of the discs [OWNER/materials item]. Modeling stays
  uniform; electrically irrelevant for the netlist.
- **СБ wire-endpoint table: carried** -- the one true desk leftover (a full session of
  systematic поз.-callout sweeping; wires 3/4/5/6/11 done previously).

## #8 + #10 leftovers session (SB-true sweep, part 1)
- **Analog corner SB-true** (crop sb_analog): C12 trimmer (254.6,95.6), C11 (264.9,92.0),
  C14 (272.2,102.3), C15 (253.8,104.0), R72/R74/R75/R85/R65/C94 exact; VT2/VT3/VT4/R73/VD3
  refined (<3mm deltas). **D40 = (258.0,125.6)** (was 140.9 -- clock/video corner sits higher).
- **Decode cluster SB-true** (crop sb_decode): **D8 (89.5,102.4) HORIZONTAL, D9 (114.0,103.0)
  HORIZONTAL, D2 (78.9,126.1)** -- the old photo-derived spots were ~15mm south + wrong
  rotation (the known y-drift, now resolved: the misassociation was in the photo pass, the
  SB formula is consistent -- beeper-post cross-check <0.5mm). R17 (111.4,116.1) + C99
  (105.1,119.8) SB-true; C35/C54 = decap column anchors (119.4/130.5, 119.8).
- **CONSEQUENCE: the photographed top-center socketed РЕ3 (~225,43 mm, 8904) is NOT D8**
  (D8 lives at 89,102). It is a separate socketed РЕ3 that the .006 СБ does not place =
  almost certainly the **.009-added D94** (.092 program per ПЭЗ). If its dump matches .113,
  the owner's tables snap into place as D94's (and the "V3-gating" survey guess referred to
  this chip). Owner: dump BOTH РЕ3 sockets (top-center = D94 candidate, decode-cluster = D8).
- **Factory-wire callouts spotted while sweeping**: wire 4 endpoint x-mark (285.0,112.2),
  wire 3 flag (280.3,115.9) -- both at R73's trimmer circle (the drawn diagonal wire crosses
  it); wire 11 endpoint arrow (263.1,113.3). Wire-table sweep continues [remaining bands].
- PCB regen: 237 footprints, outline-overlap PASS.

## Task #14: PIT cascade (the last mame-src cluster) TRACED
D54/D55 row reads (crops s2_d54/s2_d55): the drawn cascade matches the MAME-derived wiring
EXACTLY -- PIT_HCHAIN (D54.OUT0 -> D54.G1+G2 + D55.CLK0), PIT_HSYNC_DSL (D54.OUT2 "H.SYNC
DSL" -> D55.CLK1+CLK2), PIT_VCHAIN (D55.OUT0 -> D55.G1+G2): all three upgraded mame->traced.
FRAME_INT's drawn name = "VER RTR" (D55.OUT1). G0 gates -> +5V (netted). NEW: PIT0_CLK1M
{D54.9,15,18} <- rail labeled 1MHz [source east unread; 16M/16 tap candidate]. D54.OUT1 =
"HOR RTR" export ✓. Remaining #14 residue: RAM_RD_OE crop, SPKR/AVDC/CLK_123M far ends,
D56 sect-1 trigger, DOTCLK16M bend, C99 plate, D6 V1/V2, mode tag-3, buffer E-gates, LOAD_PRE.

## #14 continued: RAM_RD_OE chain traced
Crop s2_d37_d58: "(1) RAM OUT EN." arrives from sheet 1 -> D37.4 ✓ (net RAM_OUT_EN exact);
"(1) -MRD" -> D33 sect 3->4 -> D37.5 ✓ (HDL wiring exact); D37.6 riser ascends toward
D58.OE [pin landing = one crop, 95%]. RAM_RD_OE upgraded scan->traced. Remaining #14:
SPKR/AVDC/CLK_123M far ends, D56 sect-1 trigger, DOTCLK16M bend, C99 plate, D6 V1/V2,
mode tag-3, buffer E-gates, LOAD_PRE, PIT0_CLK1M rail source.

## Loop iteration: RAM_RD_OE landing confirmed
Crop s2_d58_oe: the D37.6 riser corners east into D58.OE (pin 9) — RAM_RD_OE fully traced
(was the "rail continuity assumed" item). Same frame re-validates the beeper SOUND tag-10
arrival -> R90. D58 rows also read: STB=11, D7/D8 data rows ✓ ИР82 pinout consistent.

## Loop iteration: SPKR + AVDC far ends closed
Crop s2_spkr_edge: AVDC = R91 -> "(1)" cross-sheet export (sheet-1 arrival = one text hunt);
SPKR = R48 -> wire post 1, post 2 = GND return (the SB posts flanking R60 at 252.7/205.2 and
252.7/199.9) -- speaker unit solders to posts directly. Both srcs upgraded.

## Loop iteration: the /13 divider fully netted (CLK_123M closed)
Crop s2_d103: **1.23MHz rail = D103.QD (pin 11)** -> tag 13 -> D57.CLK2; **CO (15) -> D33
sect 1->2 -> LD_N (9)** = the preset-reload loop (C/D preset inputs tied at the stub) —
16MHz/13 = 1.2308MHz ✓. Nets CLK_123M {D103.11, D57.18}, D103_CO, D103_LD added; ln1_dual
gained the 1->2 section; U_D103 q/co/load wired. LVS 317 IN SYNC.

## Loop iteration: D56 section-1 trigger = SYNC B. (shared feed)
Triangulated (crops s2_a_rows/s2_pin2_corner + earlier s2_d56_north): the SYNC B. wrap's
down-leg feeds BOTH A-triggers -- pin 10 (sect-2 5us shaper) and pin 2 (sect-1 ~220us
retriggerable one-shot = missing-pulse detector deriving V-scale timing from the H-rate
train). SYNC_B net += D56.2. D56's trigger story is now complete: SYNC B. in, R61 CLR
pullup, R47/C7 + R59/C8 timing, Q/Q_N outputs [destinations = DOTCLK16M bend re-read, next].

## Loop iteration: DOTCLK16M split (bend re-read)
Crop s2_dotclk_bend: D56.Q_N (pin 4) corners SOUTH at x~6074 (destination = chase); the
"16MHz" rail is a SEPARATE horizontal entering a bundle with TAG 14 -> it (not D56) clocks
D103 + the ИР16 shifters. Old DOTCLK16M net split into XTAL16M {D103.2, D42.9, D43.9}
(= OSC continuation, merge pending one tag read) + D56_QN {D56.4} (single, chase). The
"D56 16MHz astable" story is now fully retired at net level too.

## Loop iteration: C99 far plate
Crop s1_c99_east (300dpi): C99 160pF east lead ends at an ambiguous junction structure
(~sheet 4335, 2120-2500 at 300dpi) — the print breaks up; candidates = GND return (electrically
standard for the deglitch) vs the RAMOUTEN export line. Netted to GND [flagged]; a continuity
beep on the physical board settles it in seconds [owner, low priority].

## Loop iteration: D6 V-feed hunt + mode tag-3
- **Mode-bundle tag 3 -> D6.15 read directly** (crop s1_d6_ven2 row "3|15|A7") -> net
  MEM_MODE2 {D26.16, D6.15} added (PC-bit order assumed, same level as MODE0/1); HDL a[8]
  now = ppi0_pc[2] (declaration hoisted; formulas ignore a[8] -> behavior unchanged).
- **D6.V1/V2 feed**: bracket (13+14 bridged) fed by a west line that CROSSES the mode bundle
  cleanly and corners up toward tag boxes ("12"?/"9") heading further west -- candidate
  source = D2 (the second РТ4) outputs = a two-level PROM decode cascade [one crop short;
  chase queued]. Bonus: D4 buffer EN = tied stub, T -> GND arrow (crop s1_d6_ven).

## Loop iteration: D6 input rows triple-confirmed; V-feed narrowed
Crop s1_ven_corner (300dpi @3.2x): D4's B-side = BA8-BA11 entering the BA bundle with tags
9/10/11/12 (tag N = BA(N-1) convention re-verified); drawn "12|...|3" row = BA11 -> D6.3 ✓
(net already had it); mode rows "1->2, 2->1, 3->15" all drawn ✓✓ (MEM_MODE0/1/2 confirmed).
**D6.V1/V2 feed**: the west line runs from a long vertical at sheet x~2664 (300dpi), crossing
the mode bundle cleanly, east to the V-bracket junction. The vertical's top terminus
(~2664, 1280-1300) = next crop; an address bit is electrically implausible for a РТ4 CS —
expect a control rail or a D4-row tee [one crop to close].

## Loop iteration: D6 V1/V2 feed — BLOCKED (print quality), documented
Five crops triangulated: the V-bracket feed runs west from (3028,1620)/300dpi, crosses the
mode bundle cleanly, corners up at x~2664 = the channel of the BA9-13 sub-bundle trunk
(D4's high-nibble B-rows enter it with tags 10-14, double tag boxes = bundle-to-bundle
pass-through). Whether the V-feed is a sub-bundle member (electrically odd for a РТ4 CS)
or a control wire sharing the channel does not resolve at this scan's quality.
=> BLOCKED-on-materials: paper original or board continuity (D6 pins 13/14 <-> candidates)
[owner]. Model keeps D6 always-enabled (boot-verified equivalent). Item (a) closed.

## Loop iteration: D23/D24 E-gates read — hard-enabled
Crop s1_egates1: both address buffers drawn with T (11) <- "A" +5V arrow and E (9) <- GND
symbol directly — permanently enabled, no gate drivers. Netted (power rails, LVS-exempt).
D25 (data buffer) E-gate = next crop (must be gated for bus turnaround).

## Loop iteration: D25/D29 enables read; D25.T gated by D7 sect3
Crop s1_egates2: D25 (data ВА87) E (9) -> GND like D23/D24; **T (11) <- D7 ЛА3 section
(pins 5,4 -> 6)** = the bus-turnaround control (section inputs = next hop west, unread).
D29's T <- +5V arrow visible (E row cut off — assume GND like siblings [next crop if needed]).
Netted D25_T {D7.6, D25.11} + GND += D25.9; HDL sect3 wired (inputs tied so y3=1 = transmit,
preserving the old fixed-T boot behavior). LVS IN SYNC, boot 6/6.

## Loop iteration: LOAD_PRE confirm -> one-inversion CORRECTION (net LOAD_VID split)
Full pixel-trace of the load-strobe chain (crops s2_shifter_ld, s2_d38_load, s2_load_tag2,
s2_d42ld_tag + programmatic line scans):
- **Source confirmed**: D38 ЛА1 sect2 (ins 5,4,2,1 -> out 6) -> D59.13 direct wire; D59 ЛН1
  sect 13->12 output carries the handwritten label **"LOAD"**.
- **LOAD routing traced end-to-end**: D59.12 -> east y3640 -> up x2371 -> west y~3412 ->
  enters the LEFT-EDGE bundle (x~688) as **rail 6** (neighbors: rail 5 above, rail 4 below).
- **Shifter side re-read (tag|pin)**: D42/D43 left column has TWO bundles — inner (data,
  tags 7/6/5 -> pins 4/3/2 = C/B/A) and OUTER control bundle: **LD = tag 6 (pin 6), G = tag 8
  (pin 8), CK = tag 3 (pin 9), DS = tag 1 (pin 1)**. The numbers read as "tags" in the first
  crop were PIN numbers; the true tags sit at the bundle exits.
- => rail 6 is fed by **D59.12 (post-inverter)**, not D38.6. The earlier array read put
  D42.6/D43.6 one inversion early. **Correction**: LOAD_PRE = {D38.6, D59.13} (traced);
  new net **LOAD_VID = {D59.12, D42.6, D43.6}** (traced); HDL U_D42/U_D43 .ld moved to
  D59's o12. LVS IN SYNC (227 nets), boot check pending this iteration.
- Side reads banked: the y3232 westbound line (x2977 riser, D37.10 junction dot at x1805,
  bottom corner east at y3949) is a SEPARATE unnamed signal — candidate for the G/ctrl-rail-8
  or CK chase later. D59 sect 11->10 output heads west at y~3277 [consumer unread].
- **VID_HI_LD still driverless**: D46.11/D47.11 common vertical (x~3318) spans exactly
  D46.LD..D47.LD (y 1165..2902); its top dead-ends in the D44/D45 box gap (candidate join to
  the D44-bottom bus horizontal at y~1150, print gap ~9px — unresolvable at this scan).
  Driver stays "likely D59.12" (engineering read: all-counter reload), NOT netted.
