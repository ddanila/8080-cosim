# К155РЕ3 factory programming tables (owner's scans, 2026-07)
Source: `Juku_К155РЕ3_firmware.pdf` — two «Микросхема» drawings with their Д1 programming tables:
- **ДГШ 5.106.113** (изм. 2, 15.11.90): all FF except addr 14h-17h = `07 0B 0D 0E`
- **ДГШ 5.106.117** (изм. 1, 28.07.89): addr 08h-0Bh=`07`, 0Ch-0Fh=`0B`, 10h-13h=`0D`, 14h-17h=`0E`
Both «перв. примен. ДГШ 5.106.103»; these are the REVISED РЕ3 set superseding the originals
(.039 = D8, .092 = D94 per the official ДГШ5.109.009 ПЭЗ BOM).
Content semantics: low nibble is ONE-COLD (0111/1011/1101/1110) — four active-low selects.
.117 steps them with 4-address dwell across the 08-17h window; .113 fires each once at 14-17h.
Assignment D8↔.117 / D94↔.113 is ASSUMED (role-based) until verified against the chips' own
socket positions — the physical dumps will settle it.
