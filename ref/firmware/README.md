# К155РЕ3 factory programming tables (owner's scans, 2026-07)
Source: `Juku_К155РЕ3_firmware.pdf` — two «Микросхема» drawings with their Д1 programming tables:
- **ДГШ 5.106.113** (изм. 2, 15.11.90): all FF except addr 14h-17h = `07 0B 0D 0E`
- **ДГШ 5.106.117** (изм. 1, 28.07.89): addr 08h-0Bh=`07`, 0Ch-0Fh=`0B`, 10h-13h=`0D`, 14h-17h=`0E`
Both «перв. примен. ДГШ 5.106.103» — i.e. they belong to the .106.103 assembly FAMILY, which is
NOT the processor module's set: the .006 ВП lists D8's programmed part as ДГШ5.106.039 and the
.009 ПЭЗ adds .092 for D94. Neither table is printed in this owner scan;
validated physical `.039` and `.092` captures are preserved separately under
`ref/physical-proms/validated/`.
Content semantics: low nibble is ONE-COLD (0111/1011/1101/1110) — four active-low selects.
.117 steps them with 4-address dwell across the 08-17h window; .113 fires each once at 14-17h.
The earlier role-based assignment D8↔.117 / D94↔.113 is retired. The guarded
inspection in `docs/re3-firmware-inspection.md` shows that no
permutation/addressing/population reading lets .117 or .113 boot a
2-chip BIOS machine from D8, and the factory paper trail assigns D8=.039 / D94=.092. The
.113/.117 shape (FF idle + one-cold walk) reads as a timing/phase PROM pair — candidate home:
the socketed timing РЕ3 (photo, 8904) and the .103 family.

**2026-07 tracing and dump update: NEITHER scanned table is our board's D8.**
Sheet-1 tracing shows all eight ROM-socket CEs hang on D8
(tags D4..D7→D15..D18, D0..D3→D19..D22, E̅←D6.ROM̅), and the board boots
from a BIOS pair populated in D15/D16. Both scanned tables leave D4-D7
unburned (К155РЕ3 unprogrammed = 0 = OC asserted), so they fit only a
BIOS-less expansion-cart configuration. The earlier mode-map reconstruction
was useful as a falsifiable fallback, but three independent matching physical
`.039` reads now provide the authoritative D8 table and differ from that
fallback at 19 of 32 addresses. D94 `.092` likewise has three independent
matching physical reads. `ref/physical-proms/README.md` records their hashes,
raw/asserted polarity, and alias accounting.
