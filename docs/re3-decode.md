# РЕ3 firmware decode — the 4000-BFFF window pager (2026-07-03)

Cross-referencing the factory programming tables (ref/firmware/, owner's scans) with the
RomBios manual's memory-paging documentation ("окно внешней памяти по адресам 4000...BFFF",
directive `P XX`) yields a clean decode:

## ДГШ 5.106.117 → D8 (sheet-1 РЕ3, feeds D9)
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

## ДГШ 5.106.113 → D94 (FDC-revision РЕ3)
Same address convention; content = four **2K-granular** active-low selects over A000-BFFF only
(A000-A7FF / A800-AFFF / B000-B7FF / B800-BFFF). The FDC-era fine decode of the top window
quarter (FDC buffer / EKDOS region -- wiring is board-only, pending dump/beeper).

## Model status
- `re3_prom` (devices.v) carries the .117 table; D8.A0-A4 rewired to BA11-15 (board.json +
  juku_top) -- the earlier BA2-4 guess is corrected.
- The functional IO/ROM decode still runs on sim-only selects; flipping to full structural
  decode needs the D8->D9 coupling verified (beeper) plus the D9 enable polarity.
- Assignment .117=D8 / .113=D94 is role-derived (window-pager must feed the ROM CS chain =
  sheet-1 D8); the physical dumps will confirm.
