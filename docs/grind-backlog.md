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
