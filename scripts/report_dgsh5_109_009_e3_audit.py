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
    "docs/x6-a3-video-source-conflict-review.md": ("A:3", "VD3.2", "R67", "VIDEO"),
    "docs/omitted-resistor-census.md": ("R9, R10", "PXL_20260718_101754468.jpg", "four-anchor photo fit"),
    "docs/vt2-009-source-review.md": ("PXL_20260718_101927794.jpg", "PXL_20260718_101932581.jpg", "VD3 polarity discrepancy"),
    "docs/d6-physical-decode.md": ("D6.12", "D8.15", "D13.1"),
    "docs/io-decode-boundary.md": ("D6.10", "D9", "REV"),
    "docs/serial-handoff.md": ("TAPE RUN INT", "D11.16", "SYNDET"),
    "docs/d7-gates-source-review.md": ("D7.11/D105.3 output tie", "D7.3→D29.2", "separate annuli", "continuity"),
    "docs/d14-exact-source-boundary.md": ("D14.2", "D14.7", "package model", "does not identify"),
    "ref/schematics/d104-pin16-rail-conflict.json": ("pin16 +12 V", "pin15", "pin8", "blank", "owner physical rail unresolved"),
    "docs/d41-timing-boundary.md": ("D95.5/.6", "1 MHz"),
    "docs/memory-timing-boundary.md": ("D33.3", "D92.13", "MEMR"),
    "docs/d40-d59-d92-d95-1mhz-route.md": ("D40.11", "D59.5", "D92.2", "D95.5 + D95.6"),
    "docs/master-oscillator-boundary.md": ("R31=`1к`", "R32=`1,3к`", "R34", "C73 exact-revision range remains open", "older `.006`", "C4"),
    "docs/phi2ttl-d29-clock-route.md": ("R37 joins the printed `B` rail", "R36 joins `B` separately", "crosses", "without a junction"),
    "ref/photos/juku-pcb-2/r31-r32-oscillator-value-review.json": ("1K0", "1K3", "1,3к", "820"),
    "ref/photos/juku-pcb-2/r34-d40-value-review.json": ("12к", "13к", "12K", "КР531ИЕ17"),
    "ref/photos/juku-pcb-2/r33-c5-population-review.json": ("horizontal R33", "no separate fitted capacitor body", "620 ohm", "population history"),
    "ref/photos/juku-pcb-2/d34-cross-face-contact-fit.json": ("seven-contact rows", "mounting hole", "D34.6_solder", "C5/C82 holes unassigned"),
    "ref/photos/juku-pcb-2/d39-cross-face-contact-fit.json": ("seven-contact rows", "D39.7", "bounded_gap_px_approx", "C5/C82"),
    "ref/photos/juku-pcb-2/c5-c82-d39-annulus-exclusion.json": ("D39.10", "XTAL16M", "within roughly 2 px", "Exclude"),
    "ref/photos/juku-pcb-2/c5-r33-rc-node-landing-review.json": ("R33-left", "Restore the upper", "D34.6", "1110"),
    "ref/photos/juku-pcb-2/r33-d34-pin6-source-conflict.json": ("D34.6", "D34.2", "two_joints_native_reread", "Power off"),
    "ref/photos/juku-pcb-2/d34-pin2-pin6-c5-bridge-review.json": ("D34.2 B.Cu strip", "D34.2", "D34.6", "RETRACTED", "p2_sheet2.png"),
    "ref/photos/juku-pcb-2/c29-landing-pair-review.json": ("56 pF", "R35's lower lead", "D56.8", "D35.13"),
    "ref/photos/juku-pcb-2/r106-cross-date-review.json": ("510R", "910", "56 pF", "D35.13"),
    "ref/photos/juku-pcb-2/c99-assembly-photo-review.json": ("C99=160", "160 pF", "R17", "ground bar", "physical pad identity"),
    "ref/schematics/fdc-x4-ngmd-wire-map.md": ("D100 is not", "D93 DAL0-DAL7", "X4.23"),
    "ref/schematics/fdc-clock-mux-map.md": ("D95", "D93 CLK/pin 24", "D106 DOWN/pin 4"),
    "ref/schematics/fdc-recovery-counter-map.md": ("D106", "D28.9", "Q3"),
    "ref/schematics/fdc-read-clock-toggle-map.md": ("D96", "D93.26", "WREQ_N"),
    "ref/schematics/fdc-write-precomp-map.md": ("D101.9", "D100.6", "EARLY"),
    "ref/schematics/fdc-controller-static-map.md": ("D93.19", "22 `TEST`", "33 `WF/VFOE`"),
    "ref/schematics/fdc-hlt-rg-map.md": ("23 HLT", "25 RG", "E11"),
    "ref/schematics/fdc-d99-timing-map.md": ("D99", "C17", "C18"),
    "ref/schematics/fdc-irq-conditioner-map.md": ("D96.9", "D96.11", "D28.10"),
    "docs/d101-section-a-input-source-review.md": ("PXL_20260718_101633062.jpg", "D96.9", "D101.4"),
    "docs/d96-clock2-source-review.md": ("PXL_20260718_101633062.jpg", "D96.11", "D94.2", "without a filled dot"),
    "docs/d101-output-tie-photo-review.md": ("D101.7", "D101.9", "without a junction dot", "The filled dot farther right", "no visible local B.Cu bridge", "single-frame sheet-3", "D94.14↔D101.7"),
    "docs/d99-q1n-a4-conflict-photo-review.md": ("D99.4", "D94.14", "rail immediately **above**", "source therefore joins D99.4 to D93.23", "D93 HLT/pin 23", "D99.4↔D93.23", "no visible local B.Cu departure"),
    "docs/d96-d99-junction-source-review.md": ("D96.13", "D99.10", "D99.10↔D100.11"),
    "docs/d100-control-source-review.md": ("D100.9", "D100.11", "D99.10↔D100.11"),
    "ref/schematics/fdc-unused-pin-dispositions.md": ("input 10 and output 9", "unused section-1 complementary Q pin 13", "unused section-1 complementary `/Q` pin 4"),
}

BOARD_NETS = {
    "P12V": {("R37", "1"), ("R36", "1")},
    "PHI1_D35": {("D35", "10"), ("R37", "2")},
    "PHI2_D35": {("D35", "12"), ("R36", "2")},
    "D40QA": {("D40", "14"), ("R46", "1")},
    "D33_CLK_RC": {("R46", "2"), ("C6", "1"), ("D33", "9")},
    "PHI2_POST_R35": {("D35", "13"), ("R35", "2"), ("R106", "1"), ("C29", "1")},
    "GND": {("C6", "2"), ("C29", "2"), ("R106", "2")},
    "INT7_RAW": {("X1", "113B"), ("D3", "13"), ("R9", "1")},
    "AMW_N": {("D7", "3"), ("D29", "2")},
    "V3_RC": {("R17", "1"), ("C99", "1"), ("D9", "6")},
    "INT6_RAW": {("X1", "113C"), ("D3", "1"), ("R10", "1")},
    "VT2_BASE": {("R62", "2"), ("R63", "2"), ("R64", "1"), ("VT2", "3")},
    "VIDEO_OUT": {("VT2", "1"), ("R65", "1")},
    "FDC_MOTOR_EN": {("D26", "16"), ("D99", "11")},
    "D99_Q2_BOUNDARY": {("D99", "5"), ("D100", "7")},
    "FDC_HLD_TO_D100": {("D93", "28"), ("D100", "3"), ("D99", "2")},
    "FDC_DDEN": {("D26", "13"), ("D93", "37"), ("D95", "14")},
    "FDC_DSEL_IN": {("D26", "12"), ("D28", "1")},
    "FDC_SIDE_SEL": {("D26", "11"), ("D100", "8")},
    "FDC_CLK": {("D95", "7"), ("D93", "24")},
    "FDC_SEPARATOR_CLOCK": {("D95", "9"), ("D106", "4")},
    "FDC_RCLK": {("D96", "5"), ("D93", "26")},
    "FDC_PRECOMP_WRDATA": {("D101", "9"), ("D100", "6")},
    "D99_Q1N_BOUNDARY": {("D99", "4"), ("D93", "23")},
    "D100_CONTROL_SHEET1_BOUNDARY": {("D100", "11")},
    "D99_Q2N_BOUNDARY": {("D99", "12"), ("D100", "9")},
    "D101_D02_R92_R99": {("D96", "9"), ("D101", "3"), ("D101", "4"), ("D101", "5"), ("D101", "6"), ("R92", "1"), ("R99", "2")},
    "D94_D1_D99_A2N": {("D94", "2"), ("D96", "11"), ("D99", "9"), ("R89", "1")},
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
    for retired in ("D96_IRQ_Q_SHEET1_BOUNDARY", "D96_IRQ_CLOCK_SHEET1_BOUNDARY"):
        if retired in board["nets"]:
            raise SystemExit(f"retired D96 sheet-3 boundary returned: {retired}")
    for net, required in BOARD_NETS.items():
        entry = board["nets"][net]
        nodes = entry.get("nodes", []) if isinstance(entry, dict) else entry
        actual = {(ref, str(pin)) for ref, pin in nodes}
        if not required <= actual:
            raise SystemExit(f"board net {net} lost endpoints {sorted(required - actual)}")
    for net, forbidden in {
        "PHI1_D35": {("R36", "2"), ("D35", "12")},
        "PHI2_D35": {("R37", "2"), ("D35", "10")},
        "P12V": {("R36", "2"), ("R37", "2")},
        "FDC_PRECOMP_WRDATA": {("D101", "7")},
        "FDC_READY": {("D93", "23"), ("D99", "4")},
    }.items():
        actual = {(ref, str(pin)) for ref, pin in board["nets"][net]["nodes"]}
        if actual & forbidden:
            raise SystemExit(f"board net {net} merged forbidden phase endpoints {sorted(actual & forbidden)}")
    d101_q0 = {name for name, entry in board["nets"].items()
               if ("D101", "7") in {(ref, str(pin)) for ref, pin in entry["nodes"]}}
    if len(d101_q0) != 1 or "FDC_PRECOMP_WRDATA" in d101_q0:
        raise SystemExit(f"D101.7/Q0 and D101.9/Q1 must remain on separate modeled nets: {sorted(d101_q0)}")

def main() -> None:
    check_inputs()
    report = """# `ДГШ5.109.009 Э3` reviewed transcription and divergence audit

Status: **REVIEWED / DIFF-FIRST TRANSCRIPTION COMPLETE**

This is the index and disposition record for the recovered three-sheet FDC-era
processor schematic. The generator verifies all 23 owner-frame hashes, required prose markers in
the linked evidence records, and selected canonical JSON endpoint invariants.
It does not reread image content or check every source-board connection. It does
not duplicate hundreds of unchanged `.006` wires into a second hand-maintained
netlist: per the exploitation plan, sheets 1–2 are audited by subsystem and
only new/divergent evidence is transcribed in full; sheet 3 is the wholesale
replacement circuit and is covered pin-by-pin by the linked maps.

Regenerate with:

```sh
python3 scripts/report_dgsh5_109_009_e3_audit.py
```

The generator preserves the existing remaining-boundaries section, which is
maintained from source and owner-photo reviews.

## Drawing identity and coverage

| sheet | frames | reviewed disposition |
| ---: | ---: | --- |
| 1 | 1 overview + 8 overlapping details | CPU, bus, decode PROMs, ROM, PIC/PPI/PIT/USART, serial and inter-sheet continuations reviewed against `.006` and the board model. Exact-revision continuations into sheet 3 are adopted; one unmatched tape interrupt continuation remains explicitly unresolved. |
| 2 | 1 overview + 8 overlapping details | DRAM, video, timing and analog boundary reviewed against `.006` and the board model. No wholesale functional replacement is present; native reads correct individual inferred nets and values listed below. |
| 3 | 1 overview + 4 overlapping details | Complete VG93 floppy controller, clock/data separator, write precompensation, drive buffers/status and X4 interface transcribed. This sheet replaces the `.006` tape subsystem rather than supplementing it. |

The detail tiles cover every circuit region. The faint sheet-2 overview is a
layout oracle only; its eight native detail frames are the pin-level evidence.

## Sheets 1–2 divergence audit

| region | `.009` result and source-model disposition | evidence artifact |
| --- | --- | --- |
| D6/D8/D13 memory decode | Direct D6.12→R11→D8.15 and D6.9→R14→D13.1; no hidden inverter. Physical PROM truth and owner continuity agree. | `docs/d6-physical-decode.md` |
| low-I/O decode | D6.10 `REV` enables tied D9 inputs through the exact 1 kΩ pull-up branch. | `docs/io-decode-boundary.md` |
| sheet-1 D7 outputs | Exact sheet 1 draws D7.3 to D29.2. The other detail labels its lower pin-3 gate D105 and shows D105.3 turning north near (1398,3360), while D7.11 runs east separately near y3590. Keep D7.11/PROM_EN and D105.3/qualified /WR separate. | `docs/d7-gates-source-review.md` |
| sheet-1 D104 supply | The exact power table assigns К170УП2 pin15 to +5 V and pin8 to ground but leaves its +12 V cell blank; the preserved device pinout calls pin16 a +12 V supply. Two owner front views hide pin16's trace under cable. A D11-local cross-face fit registers pin16 near (2710,1480) in 200506061 without proving its rail. D104.16 remains a rail-assignment hold pending owner continuity. | `ref/schematics/d104-pin16-rail-conflict.json` |
| sheet-1 C99 decode RC | Exact sheet 1 draws C99=`160` (nominal 160 pF by the native convention) from R17.1/D9.6 to ground. Assembly places it horizontally left of R17. May and July owner photos show no distinct body. The corrected D9-local fit matches the two bare front candidates to separate solder joints within about 5–7 px; a third joint matches R17 lower and has a visible short B.Cu link to the right C99 candidate. The left solder candidate photo-traces to D2.14, grounded on exact sheet 1. Front-to-back same-hole identities, owner ground continuity, and population remain physical checks. | `ref/photos/juku-pcb-2/c99-assembly-photo-review.json` |
| D26 floppy controls | PC2/PC4/PC5/PC6 continue as MOTOR EN, FM/MFM, D_SEL and S.SEL. PC3 is the 5/8-inch clock selection. | `ref/schematics/fdc-x4-ngmd-wire-map.md` |
| direct FDC host bus | Sheet-1 D0–D7 bundle continues directly to D93.7–.14; the inference-era D100 DAL transceiver is disproved. | `docs/fdc-bus-polarity.md` |
| serial/PIC | RxRDY→IR2, shared TxC/RxC baud path, SYNDET switch path and X3/X5/X6 handoff are source-closed. IR4 still says `(3) TAPE RUN INT`, but replacement sheet 3 has no mate; it remains an unmatched source boundary. D14.2/.7 package roles are known, but no traceable D14 wire appears in the photographed serial circuit fields. | `docs/serial-handoff.md`; `docs/d14-exact-source-boundary.md` |
| sheet-2 memory read | Native `-MRD` arrivals close D33.3 and D92.13 onto MEMR, including the factory W11 continuation. | `docs/memory-timing-boundary.md` |
| sheet-2 clocks | Native labels plus owner continuity close D40.11 onto the D59.5 mux-enable source, tied D92.2/.3 timing inputs, and the sheet-3 D95.5/.6 1 MHz continuation. The source, HDL, schematic and checked routed endpoints preserve that single-driver net and keep D92 off the separate `PHI2TTL` rail. Whole-board routing release remains held. | `docs/d40-d59-d92-d95-1mhz-route.md` |
| sheet-2 phase pull-ups | Exact `PXL_20260718_101911242.jpg` shows R37 and R36 as separate 360-ohm branches from rail `B` (+12 V) to D35.10/Ф1 and D35.12/Ф2. The R36 feed crosses Ф1 without a junction; the audit guards both modeled phase nets against merging. Physical pad continuity remains open. | `docs/phi2ttl-d29-clock-route.md` |
| sheet-2 D33 clock input | Exact `PXL_20260718_101908284.jpg` prints R46=`200` from D40.14 to D33.9, with C6=`56` from that input node to the return symbol. The model and guarded nets preserve the branch; the native bare-value convention gives C6 nominal 56 pF. | `docs/native-capacitor-values.md` |
| sheet-2 D35 pulse shaper | Exact sheet 2 draws R35=330 Ω from PHI2TTL to D35.13/C29/R106, C29 marked bare `56` (nominal 56 pF by the native convention), and R106=910 Ω to ground. Owner May/July photos instead show a 510R-marked body at R106 and no distinct C29 body. The two-face owner photos support an upper C29-position joint on the R35-lower/R106-upper node and a middle candidate toward a D56.8-grounded rail. The physical D35.13 continuation, actual capacitor population and installed resistor value remain open. | `ref/photos/juku-pcb-2/c29-landing-pair-review.json`; `ref/photos/juku-pcb-2/r106-cross-date-review.json` |
| sheet-2 D34 pulse-shaper population | Both `.006` and exact `.009` sheet 2 give R33=`620` and C5=`560`, drawn between D34.6 and D34.2/R33. The factory assembly labels R33 above D39/D34 and C5 in their gap. May and July owner views show the R33-position body but no distinct C5 body at its drawn height. D34/D39 rows are registered across both faces; one D39.10/XTAL16M annulus is excluded. A short visible B.Cu strip joins D34.2 to the upper R33-left gap joint near front (3098,2345)/solder (1110,2007). Native crop separates the lower joint near (3098,2395)/(1110,2057), whose front trace reaches D34.6. The pair aligns with the factory C5 outline and source terminal roles, making it a strong C5 pad candidate; same-hole continuity and population history remain open. | `ref/photos/juku-pcb-2/r33-c5-population-review.json`; `ref/photos/juku-pcb-2/d34-cross-face-contact-fit.json`; `ref/photos/juku-pcb-2/d39-cross-face-contact-fit.json`; `ref/photos/juku-pcb-2/c5-c82-d39-annulus-exclusion.json`; `ref/photos/juku-pcb-2/d34-pin2-pin6-c5-bridge-review.json` |
| sheet-2 oscillator attributes | Native `.009` detail `PXL_20260718_101908284.jpg` prints R31=`1к`, R32=`1,3к`, and D40 pull-up R34=`12к`, agreeing with owner bodies `1K0`, `1K3`, and `12K`; older `.006` prints 820 ohms, 1,2к, and 13к. Exact `.009` draws C73 without a range, while older `.006` says 4/20; C73's procurement value remains open. | `docs/master-oscillator-boundary.md` |
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
| D97/D102/D101 write precompensation | `fdc-write-precomp-map.md`, `docs/d101-section-a-input-source-review.md`, `docs/d101-output-tie-photo-review.md` |
| D99 one-shot timing | `fdc-d99-timing-map.md`, `docs/d99-q1n-a4-conflict-photo-review.md` |
| DRQ/INTRQ conditioner | `fdc-irq-conditioner-map.md`, `docs/d96-clock2-source-review.md` |
| exact-revision unused pins | `fdc-unused-pin-dispositions.md` |

Together these maps account for every functional D93 pin, all D95/D96/D98/D100/
D106 pins used by sheet 3, both D99 timing networks, and the locally drawn
D28/D97/D101/D102 sections. Drawing-internal R86/R94/R99 reference conflicts
are explicitly overridden only where registered target-board evidence is
stronger.

## Remaining boundaries after transcription

- D96.9 Q2 runs to the joined D101 A0-A3 inputs in the full sheet-3
  overview; D96.11 reaches the D94.2/D99.9/R89.1 island there. Both physical
  branches need continuity checks. D100.9 joins D99.12 Q2_N, while D100.11
  has an unresolved sheet-1 control continuation.
- D99.10 shares D96.13 and an unread sheet-1 continuation. D99.4 is drawn
  to D93.23/HLT, separate from owner-closed D94.14/D101.7. Original-board
  D99.4-to-D93.23 continuity remains unmeasured. D101.1 is source-joined to D26.38 on
  the `IMDRG` sheet-1/sheet-3 continuation; physical continuity is pending.
  Sheet 3 joins D101 section-A inputs pins3/4/5/6 at marked dots; owner
  imagery independently closes pin4 to R92/R99, while physical continuity
  of D96.9 and pins3/5/6 to that island remains unmeasured.
- X4.2–.5 retain revision/cable disposition because target sheet 3 omits them;
  X4.1–.6 are grouped returns on the НГМД side but unseen cable conductors are
  not invented.
- The factory sheet's reset label polarity and physical FDC clock/analog edge
  quality remain bring-up measurements, not missing transcription.

These are external-evidence boundaries. All source-visible `.009` corrections
are represented or explicitly dispositioned; this audit supplies no authority
to fabricate while the separate P0 connectivity and routing gates remain open.
"""
    # The boundary ledger receives source and owner-photo findings after the
    # generated census. Keep those reviewed additions when refreshing the
    # census and divergence table.
    boundary_heading = "\n## Remaining boundaries after transcription\n"
    if OUT.exists():
        existing = OUT.read_text()
        if boundary_heading in existing and boundary_heading in report:
            report = report.split(boundary_heading, 1)[0] + boundary_heading + existing.split(boundary_heading, 1)[1]
    OUT.write_text(report)
    print(f".009 E3 audit: {len(PHOTOS)} photo hashes, {len(MARKERS)} reviewed evidence artifacts, {len(BOARD_NETS)} board nets")

if __name__ == "__main__":
    main()
