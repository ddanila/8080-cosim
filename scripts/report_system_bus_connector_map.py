#!/usr/bin/env python3
"""Guard the recovered .106.103 XP bus map and .031.011 system interconnect."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "ref/schematics/system-bus-connector-map.md"

SOURCES = {
    "ref/photos/dgsh5-106-103-e3/PXL_20260718_122444769.MP.jpg": "4cc84a693fd8c19d720f8cae342fde43fce0a78ae3862092cb45f85409658785",
    "ref/photos/dgsh5-106-103-e3/PXL_20260718_122448921.jpg": "716176af3e731cff9a3a0ef992f06580fa66b405018ee6c83273eb463216461d",
    "ref/photos/dgsh5-106-103-e3/PXL_20260718_122454044.jpg": "be0fe8cee15270f25fffb1cfba9d1e1f211304e80b6b352516a006155ae00c18",
    "ref/photos/dgsh3-031-011-e6/PXL_20260718_121242143.jpg": "ae1a33258ca2b344b0457e5800a1fb793bb09583634ca786b4dc9cdc52434b6e",
    "ref/photos/dgsh3-031-011-e6/PXL_20260718_121246801.jpg": "4403fe67089d3e0fcb51240be0dcf9f804ba8f64115962a1d5bf14e8ba3ee03a",
    "ref/photos/dgsh3-031-011-e6/PXL_20260718_121250335.jpg": "f2835d46113713fe040a1bc0ae0d398564e7425d74d4b23684553ca6ce86613a",
}

SIGNALS = {
    "132C": "DAT0", "132B": "DAT1", "131C": "DAT2", "131B": "DAT3",
    "130C": "DAT4", "130B": "DAT5", "129C": "DAT6", "129B": "DAT7",
    "124C": "ADR_LO0", "124B": "ADR_LO1", "123C": "ADR_LO2", "123B": "ADR_LO3",
    "122C": "ADR_LO4", "122B": "ADR_LO5", "121C": "ADR_LO6", "121B": "ADR_LO7",
    "120C": "ADR_HI0", "120B": "ADR_HI1", "119C": "ADR_HI2", "119B": "ADR_HI3",
    "118C": "ADR_HI4", "118B": "ADR_HI5", "117C": "ADR_HI6", "117B": "ADR_HI7",
    "109B": "IOM_N", "104C": "MRC_N", "102B": "AMWC_N", "106B": "INHIB_N",
}

CARD_P5V = {"106A", "107A", "108A", "108B", "108C"}
CARD_GND = {"101A", "102A", "103A", "104A", "124A", "125A", "126A", "127A"}
MAIN_P5V = {"101A", "102A", "103A", "107A", "108A", "108B", "108C"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    for relative, expected in SOURCES.items():
        path = ROOT / relative
        actual = digest(path)
        if actual != expected:
            raise SystemExit(f"source image changed: {relative}: {actual}")

    board = json.loads((ROOT / "kicad/juku.board.json").read_text())
    x1 = next(chip for chip in board["chips"] if chip["ref"] == "X1")
    mismatches = {
        pin: (signal, x1["pins"].get(pin))
        for pin, signal in SIGNALS.items()
        if x1["pins"].get(pin) != signal
    }
    if mismatches:
        raise SystemExit(f"XP/main-board signal map changed: {mismatches}")
    if {pin for pin, value in x1["pins"].items() if value == "P5V"} != MAIN_P5V:
        raise SystemExit("main-board X1 +5 V contact set changed; review the documented variant conflict")
    if CARD_P5V & CARD_GND:
        raise SystemExit("card transcription assigns one contact to both rails")

    rows = []
    for pin, signal in SIGNALS.items():
        label = signal.replace("DAT", "D").replace("ADR_LO", "ADR").replace("ADR_HI", "ADR")
        if signal.startswith("ADR_HI"):
            label = f"ADR{int(signal[-1]) + 8:X}"
        label = {
            "IOM_N": "IOM", "MRC_N": "MRDC", "AMWC_N": "AMWTC",
            "INHIB_N": "INHIBIT",
        }.get(signal, label)
        rows.append(f"| `{pin}` | `-{label}` | `{signal}` | PASS |")

    shared_p5v = CARD_P5V & MAIN_P5V
    conflict = CARD_GND & MAIN_P5V
    lines = [
        "# System-bus connector cross-check", "",
        "Status: **SIGNAL CORE MATCHES / POWER MAP IS A DOCUMENTED VARIANT CONFLICT**", "",
        "This reviewed transcription compares the `ДГШ5.106.103 Э3` 32 KiB",
        "memory card's `XP` edge contacts with processor-module `.009` connector",
        "`X1`, then records the `ДГШ3.031.011 Э6` terminal-level cable map.",
        "The two drawings independently agree on every exposed data, address, and",
        "listed control contact. They do **not** agree on all power contacts, so the",
        "`.106.103` card must not be treated as a drop-in `.009` expansion card.", "",
        "## Guarded primary frames", "",
    ]
    lines.extend(f"- `{path}` — SHA256 `{sha}`" for path, sha in SOURCES.items())
    lines += [
        "", "The card overview and two overlapping detail reads independently cover",
        "the XP labels. The system overview plus both details cover the complete",
        "block/cable drawing. Contact codes below use the processor repository's",
        "three-character form: card `C32` is processor `132C`, etc.", "",
        "## Shared bus signal core", "",
        "| X1/XP contact | Card label | Main-board model | Result |",
        "| --- | --- | --- | --- |",
        *rows, "",
        "The recovered card exposes ADR0 through ADRF (16 address bits), not",
        "ADR0 through ADR17. Its four shown controls are `-IOM`, `-MRDC`,",
        "`-AMWTC`, and `-INHIBIT`; these match `IOM_N`, `MRC_N`, `AMWC_N`, and",
        "`INHIB_N` at the identical contacts in `kicad/juku.board.json`.", "",
        "## Power-contact conflict", "",
        "| Drawing/model | +5 V contacts | Ground contacts |",
        "| --- | --- | --- |",
        f"| `.106.103` card | `{', '.join(sorted(CARD_P5V))}` | `{', '.join(sorted(CARD_GND))}` |",
        f"| `.109.009` processor | `{', '.join(sorted(MAIN_P5V))}` | not redrawn from the card |", "",
        f"The drawings agree on +5 V at `{', '.join(sorted(shared_p5v))}` but",
        f"conflict directly at `{', '.join(sorted(conflict))}`: the card grounds",
        "those contacts while the exact `.009` processor sheet-1 power corner",
        "labels them +5 V. The card additionally uses `106A` for +5 V. This is",
        "not resolved by signal-name inference. The `.009` drawing remains",
        "normative for the replica; no processor-board rail was changed.", "",
        "## System-level cable map (`ДГШ3.031.011 Э6`)", "",
        "| A1 E5101 connector | Conductors | Destination | Destination contact |",
        "| --- | ---: | --- | ---: |",
        "| `X1 / XP1` | 96 | A2.1 keyboard controller E4701 **or** A2.2 removable memory expander E6201 | `XP1` |",
        "| `X2` | 30 | A3 printer СМ6329.02 / К6312М | 39 |",
        "| `X4` | 23 | A4 НГМД block E6502 (`ДГШ3.065.008`) | 23 |",
        "| `X6` | 2 | A5 display МС6105.09 | 2 |", "",
        "The drawing also shows A1 `X3` contact 12 on the mains/switch harness;",
        "it does not show an `X5` signal cable. Cable callouts 4, 5, and 6 are",
        "respectively `ДГШ4.853.035`, `.042`, and `.043`; the A2 connection is",
        "the drawing's alternative position 7 rather than evidence that both A2",
        "modules are installed simultaneously.", "",
        "## Disposition", "",
        "- The main-board data/address/control model is independently corroborated.",
        "- The `.106.103` README's former ADR17 claim is corrected to ADRF.",
        "- The power conflict is a variant boundary and a bench safety warning,",
        "  not permission to merge either rail map.",
        "- A future `.106.102` drawing or backplane wiring table is required before",
        "  claiming the E6201 module shown in the system drawing is pin-compatible",
        "  with either connector map.", "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("SYSTEM-BUS-CONNECTOR-MAP: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
