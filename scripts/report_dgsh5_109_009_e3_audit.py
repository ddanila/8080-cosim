#!/usr/bin/env python3
"""Generate the reviewed, diff-first ДГШ5.109.009 Э3 transcription audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTO_DIR = ROOT / "ref/photos/dgsh5-109-009-e3"
OUT = ROOT / "ref/schematics/dgsh5-109-009-e3-notes.md"

PHOTOS = {
    "PXL_20260718_101633062.jpg":"5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047",
    "PXL_20260718_101637906.jpg":"ba6f618ea610f05617cde668660a767c103116bcd55f46862a36cbe385ee26e4",
    "PXL_20260718_101641055.jpg":"86740a80fb494cdb08f4de3a120cab83e4f6638cf5885d4c83418a4a94c881a7",
    "PXL_20260718_101644861.jpg":"8b8ad8abdf5cdf8c235cc942592ebe6c0019ec8ad90ae9958267fbc154bb0e67",
    "PXL_20260718_101648508.jpg":"ef04482bdd7f15a20e132034709bb7b6dfab54d6ac9d4efe2f6510575b4aa641",
    "PXL_20260718_101754468.jpg":"effc98746807ef28dab97051ceba293f4433c0f3b39b86cbb55ddcaad24aeca4",
    "PXL_20260718_101801729.jpg":"fb91576d1b3b0161e666bfbfc0c1a3729ea8beb5e066b93c2a9428da68fcccf7",
    "PXL_20260718_101805510.jpg":"40a524d663dc4685a7093782165264524cd70780fb41638a8d1c0cbca0b36216",
    "PXL_20260718_101809608.jpg":"62ee9a1ce20ef418bbbb5e49ca8b79f2ff7d0fc317c9c9ffe1a087277067d004",
    "PXL_20260718_101813438.jpg":"13c1f0cd1f95c188ab7240ddd73f167e063962ecdd7dd9e39948c6aedbec1432",
    "PXL_20260718_101817644.jpg":"398ccfe8a2cb9050db7ac60077ab21383e64213be613504035c11ee5fc781a0b",
    "PXL_20260718_101820818.MP.jpg":"6cbeeb6efc4c235e22eec8f6a1c63312fd7649a59cccc09067e2102a94f551ea",
    "PXL_20260718_101824181.MP.jpg":"55ead8fd296762bd14a6efe80ccffc191884897153ca92702a4777c4eac40b38",
    "PXL_20260718_101827714.jpg":"960516eaf3a98d1caf5c543f9e131cea482766eb7e3e66e60655d3e4264bb7b0",
    "PXL_20260718_101901243.jpg":"1749c3eacf1635692539fa869408420e2b7e0b565f6024f3a7968e9b78aa3974",
    "PXL_20260718_101908284.jpg":"aa586c8eef859bdcaa1454e0c53378f8f45ea78454c5df76027f115efba5f652",
    "PXL_20260718_101911242.jpg":"d30b527eeef67ebc587014909b6f8ac347174f594c2bde236a7b3fcf92f0e1b8",
    "PXL_20260718_101914588.jpg":"00bea72cbc462131b2542ed22e29571069b3f181b1c1f0fddb0a80a89d0ecd99",
    "PXL_20260718_101917240.jpg":"cc5355512800c4804523f26e433c98e9218fc296da2e264e2411f6bff52ea642",
    "PXL_20260718_101921033.MP.jpg":"984eb3e02d3e11916a374c1e3be6339925e380e24ba182b00ae7120a3bf68777",
    "PXL_20260718_101924004.jpg":"d3f436ba6f5099360188914218ecbde6e995817fc762172c808be5ca9d4e1338",
    "PXL_20260718_101927794.jpg":"a31896156ad7e1bc35e59ee43223babd3d39f40f2a086152d26f76cf14c71aa9",
    "PXL_20260718_101932581.jpg":"9aba327c149b59049c6fdb5ad6d9f13d43df4810765cf8865726d9bf911bd86d",
}

MARKERS = {
    "docs/d6-physical-decode.md": ("D6.12", "D8.15", "D13.1"),
    "docs/io-decode-boundary.md": ("D6.10", "D9", "REV"),
    "docs/serial-handoff.md": ("TAPE RUN INT", "D11.16", "SYNDET"),
    "docs/d41-timing-boundary.md": ("D95.5/.6", "1 MHz"),
    "docs/memory-timing-boundary.md": ("D33.3", "D92.13", "MEMR"),
    "docs/d40-d59-d92-d95-1mhz-route.md": ("D40.11", "D59.5", "D92.2", "D95.5 + D95.6"),
    "ref/schematics/fdc-x4-ngmd-wire-map.md": ("D100 is not", "D93 DAL0-DAL7", "X4.23"),
    "ref/schematics/fdc-clock-mux-map.md": ("D95", "D93 CLK/pin 24", "D106 DOWN/pin 4"),
    "ref/schematics/fdc-recovery-counter-map.md": ("D106", "D28.9", "Q3"),
    "ref/schematics/fdc-read-clock-toggle-map.md": ("D96", "D93.26", "WREQ_N"),
    "ref/schematics/fdc-write-precomp-map.md": ("D101.9", "D100.6", "EARLY"),
    "ref/schematics/fdc-controller-static-map.md": ("D93.19", "22 `TEST`", "33 `WF/VFOE`"),
    "ref/schematics/fdc-hlt-rg-map.md": ("23 HLT", "25 RG", "E11"),
    "ref/schematics/fdc-d99-timing-map.md": ("D99", "C17", "C18"),
    "ref/schematics/fdc-irq-conditioner-map.md": ("D96.9", "D96.11", "D28.10"),
    "ref/schematics/fdc-unused-pin-dispositions.md": ("input 10 and output 9", "unused section-1 complementary Q pin 13", "unused section-1 complementary `/Q` pin 4"),
}

BOARD_NETS = {
    "FDC_MOTOR_EN": {("D26", "16"), ("D100", "7")},
    "FDC_DDEN": {("D26", "13"), ("D93", "37"), ("D95", "14")},
    "FDC_DSEL_IN": {("D26", "12"), ("D28", "1")},
    "FDC_SIDE_SEL": {("D26", "11"), ("D100", "8")},
    "FDC_CLK": {("D95", "7"), ("D93", "24")},
    "FDC_SEPARATOR_CLOCK": {("D95", "9"), ("D106", "4")},
    "FDC_RCLK": {("D96", "5"), ("D93", "26")},
    "FDC_PRECOMP_WRDATA": {("D101", "9"), ("D100", "6")},
    "D100_CONTROL_SHEET1_BOUNDARY": {("D100", "9"), ("D100", "11")},
}

def check_inputs() -> None:
    for name, expected in PHOTOS.items():
        actual = hashlib.sha256((PHOTO_DIR / name).read_bytes()).hexdigest()
        if actual != expected:
            raise SystemExit(f"photo hash mismatch: {name}")
    for relative, markers in MARKERS.items():
        text = (ROOT / relative).read_text()
        for marker in markers:
            if marker not in text:
                raise SystemExit(f"{relative} lost audit marker {marker!r}")
    board = json.loads((ROOT / "kicad/juku.board.json").read_text())
    for net, required in BOARD_NETS.items():
        entry = board["nets"][net]
        nodes = entry.get("nodes", []) if isinstance(entry, dict) else entry
        actual = {(ref, str(pin)) for ref, pin in nodes}
        if not required <= actual:
            raise SystemExit(f"board net {net} lost endpoints {sorted(required - actual)}")

def main() -> None:
    check_inputs()
    report = """# `ДГШ5.109.009 Э3` reviewed transcription and divergence audit

Status: **REVIEWED / DIFF-FIRST TRANSCRIPTION COMPLETE**

This is the index and disposition record for the recovered three-sheet FDC-era
processor schematic. It checksum-pins all 23 owner frames and guards the
already reviewed pin-level transcriptions against the source board. It does
not duplicate hundreds of unchanged `.006` wires into a second hand-maintained
netlist: per the exploitation plan, sheets 1–2 are audited by subsystem and
only new/divergent evidence is transcribed in full; sheet 3 is the wholesale
replacement circuit and is covered pin-by-pin by the linked maps.

## Drawing identity and coverage

| sheet | frames | reviewed disposition |
| ---: | ---: | --- |
| 1 | 1 overview + 8 overlapping details | CPU, bus, decode PROMs, ROM, PIC/PPI/PIT/USART, serial and inter-sheet continuations reviewed against `.006` and the board model. Exact-revision continuations into sheet 3 are adopted; one stale tape interrupt label remains explicitly unresolved. |
| 2 | 1 overview + 8 overlapping details | DRAM, video, timing and analog boundary reviewed against `.006` and the board model. No wholesale functional replacement is present; native reads correct individual inferred nets and values listed below. |
| 3 | 1 overview + 4 overlapping details | Complete VG93 floppy controller, clock/data separator, write precompensation, drive buffers/status and X4 interface transcribed. This sheet replaces the `.006` tape subsystem rather than supplementing it. |

The detail tiles cover every circuit region. The faint sheet-2 overview is a
layout oracle only; its eight native detail frames are the pin-level evidence.

## Sheets 1–2 divergence audit

| region | `.009` result and source-model disposition | evidence artifact |
| --- | --- | --- |
| D6/D8/D13 memory decode | Direct D6.12→R11→D8.15 and D6.9→R14→D13.1; no hidden inverter. Physical PROM truth and owner continuity agree. | `docs/d6-physical-decode.md` |
| low-I/O decode | D6.10 `REV` enables tied D9 inputs through the exact 1 kΩ pull-up branch. | `docs/io-decode-boundary.md` |
| D26 floppy controls | PC2/PC4/PC5/PC6 continue as MOTOR EN, FM/MFM, D_SEL and S.SEL. PC3 is the 5/8-inch clock selection. | `ref/schematics/fdc-x4-ngmd-wire-map.md` |
| direct FDC host bus | Sheet-1 D0–D7 bundle continues directly to D93.7–.14; the inference-era D100 DAL transceiver is disproved. | `docs/fdc-bus-polarity.md` |
| serial/PIC | RxRDY→IR2, shared TxC/RxC baud path, SYNDET switch path and X3/X5/X6 handoff are source-closed. IR4 still says `(3) TAPE RUN INT`, but replacement sheet 3 has no mate; it remains a stale-sheet boundary, not an invented FDC IRQ. | `docs/serial-handoff.md` |
| sheet-2 memory read | Native `-MRD` arrivals close D33.3 and D92.13 onto MEMR, including the factory W11 continuation. | `docs/memory-timing-boundary.md` |
| sheet-2 clocks | Native labels plus owner continuity close D40.11 onto the D59.5 mux-enable source, tied D92.2/.3 timing inputs, and the sheet-3 D95.5/.6 1 MHz continuation. The source, HDL, schematic, and zero-open routed boards now preserve that single-driver net and keep D92 off the separate `PHI2TTL` rail. | `docs/d40-d59-d92-d95-1mhz-route.md` |
| sheet-2 analog/video | Populated non-RF video path is retained; `.006` RF-only parts are absent from the `.009` target. Exact `.009` C94 and several passive attributes remain honest photo/measurement boundaries. | `docs/video-analog-boundary.md` |

No further sheet-1/2 difference is promoted merely because a continuation mark
looks similar. Owner continuity outranks both revisions, and unresolved hidden
front-copper routes remain measurement asks.

## Sheet 3 complete circuit index

| circuit | reviewed transcription |
| --- | --- |
| D93 host/static/strap pins | `docs/fdc-bus-polarity.md`, `fdc-controller-static-map.md`, `fdc-hlt-rg-map.md` |
| X4 outputs and drive inputs | `fdc-x4-ngmd-wire-map.md` |
| D95 controller/separator clocks | `fdc-clock-mux-map.md` |
| D106 recovery counter | `fdc-recovery-counter-map.md` |
| D96 read-clock toggle | `fdc-read-clock-toggle-map.md` |
| D97/D102/D101 write precompensation | `fdc-write-precomp-map.md` |
| D99 one-shot timing | `fdc-d99-timing-map.md` |
| DRQ/INTRQ conditioner | `fdc-irq-conditioner-map.md` |
| exact-revision unused pins | `fdc-unused-pin-dispositions.md` |

Together these maps account for every functional D93 pin, all D95/D96/D98/D100/
D106 pins used by sheet 3, both D99 timing networks, and the locally drawn
D28/D97/D101/D102 sections. Drawing-internal R86/R94/R99 reference conflicts
are explicitly overridden only where registered target-board evidence is
stronger.

## Remaining boundaries after transcription

- D96.9 and D96.11 leave through distinct sheet-1 continuations whose remote
  endpoints are not uniquely visible; D100.9/.11 share a third unresolved
  sheet-1 control continuation. They require continuity, not schematic guesswork.
- D99.10 and the other remote D99 section pins remain traced only to sheet
  boundaries. D101.1/.3/.5/.6 remain the exact open precomp-support endpoints.
- X4.2–.5 retain revision/cable disposition because target sheet 3 omits them;
  X4.1–.6 are grouped returns on the НГМД side but unseen cable conductors are
  not invented.
- The factory sheet's reset label polarity and physical FDC clock/analog edge
  quality remain bring-up measurements, not missing transcription.

These are external-evidence boundaries. All source-visible `.009` corrections
are represented or explicitly dispositioned; this audit supplies no authority
to fabricate while the separate P0 connectivity and routing gates remain open.
"""
    OUT.write_text(report)
    print(f".009 E3 audit: {len(PHOTOS)} photo hashes, {len(MARKERS)} reviewed evidence artifacts, {len(BOARD_NETS)} board nets")

if __name__ == "__main__":
    main()
