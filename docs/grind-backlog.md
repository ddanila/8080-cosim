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
