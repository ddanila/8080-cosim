# РЕ3 firmware decode — the 4000-BFFF window pager (2026-07-03)

Cross-referencing the factory programming tables (ref/firmware/, owner's scans) with the
RomBios manual's memory-paging documentation ("окно внешней памяти по адресам 4000...BFFF",
directive `P XX`) yields a clean decode:

## Retired hypothesis: ДГШ 5.106.117 → D8 (sheet-1 РЕ3, feeds D9)
Address inputs **A4..A0 = BA15..BA11** (each table row = 2 KB of address space). Content:
| table addr | memory range | value | asserted output (active-low) |
|---|---|---|---|
| 00-07 | 0000-3FFF | FF | none (resident ROM region -- D6/РТ4 handles it) |
| 08-0B | 4000-5FFF | 07 | **D3** |
| 0C-0F | 6000-7FFF | 0B | **D2** |
| 10-13 | 8000-9FFF | 0D | **D1** |
| 14-17 | A000-BFFF | 0E | **D0** |
| 18-1F | C000-FFFF | FF | none (RAM/video) |
D7-D4 are additionally driven low across the whole 4000-BFFF window (a window-active group /
bank-enable strobes). So D8 = **four 8K bank selects over the documented external-memory
window**; D9 (ИД7) downstream turns bank state into the 8 EPROM socket selects (D15-D22 = 4
pairs) and CS4-CS7 peripheral selects. This also explains the 8 per-socket ROM programming
drawings (.041-.043/.087-.091).

## Retired hypothesis: ДГШ 5.106.113 → D94 (FDC-revision РЕ3)
Same address convention; content = four **2K-granular** active-low selects over A000-BFFF only
(A000-A7FF / A800-AFFF / B000-B7FF / B800-BFFF). This was an early role-derived
assignment, now superseded by the reconciliation below: D94 is the .009-added
`ДГШ5.106.092` PROM, and `.113/.117` belong to the `.106.103` family.

## Model status
- `re3_prom` (devices.v) is now a boot-validated reconstructed D8 `.039`
  fallback, not the scanned `.117` table.
- `re3_prom_092` is the inert D94 placeholder. It deliberately exports no
  burnable image until `ДГШ5.106.092` is dumped or recovered from the Baltijets
  programming disk.
- The functional IO/ROM decode still runs on sim-only selects; flipping to full structural
  decode needs the D8->D9 coupling verified (beeper) plus the D9 enable polarity.

## RECONCILIATION GRIND (owner: "the dumps are correct") — impossibility proof + reassignment
Attempted to make .117-as-D8 work under EVERY freedom: tag permutation, row-address bijection
(incl. bit inversions), population choice. Invariants that kill it:
- .117's value multiset = 16xFF + 4x each 07/0B/0D/0E; every non-FF value asserts FIVE rails
  (one of D0-D3 + all of D4-D7). FF rows assert none. A fetch needs exactly one driver.
- => the D4-D7-tag sockets are empty in every working config, and no addressing puts a
  2-chip 16K BIOS at 0000-3FFF (+D800-FFFF high map) out of four one-of-four rows. The
  closest attempt (invert A3: non-FF rows land on 0000-3FFF + C000-FFFF) needs FOUR chips
  with duplicated halves -- contradicts the 2-chip BIOS. Same argument kills .113 harder.
CONCLUSION: .117/.113 are correct factory programs THAT DO NOT BELONG TO D8/D94:
- The .006 ВП itself lists the module's single РЕ3 as programmed part ДГШ5.106.039 (D8);
  the .009 ПЭЗ adds .092 (D94). We do NOT have those two tables.
- The scanned .113/.117 carry перв. примен. ДГШ5.106.103 = a different assembly family.
  Their shape (FF idle + one-cold walk, 4-dwell vs single-fire) reads naturally as a
  TIMING/PHASE PROM pair -- prime candidate: the socketed "V3-gating" timing РЕ3 (photo,
  8904) and its .103-family siblings.
- The README's "revised set superseding .039/.092" line was our assumption -- retired.
=> D8's true content (.039) remains undumped; the MAME-derived prediction in re3_prom stays
the model. The .117 window alignment with 4000-BFFF 8K banks is either lineage or
coincidence -- the .039 dump decides. Deciders unchanged: dump D8's seated chip; dump the
two board-#2 EPROMs; continuity D8.5 <-> leftmost socket pin 20.
