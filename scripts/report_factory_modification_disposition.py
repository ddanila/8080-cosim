#!/usr/bin/env python3
"""Guard the unresolved electrical disposition of factory Вид В modifications."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.board.json"
BODGE = ROOT / "ref/photos/juku-pcb-2/BODGE-TRIAGE.md"
PHOTO_DIR = ROOT / "ref/photos/dgsh5-109-009-sb"
REPORT = ROOT / "docs/factory-modification-disposition.md"
AFFECTED = {
    "D56": "АГ3 timing area: multiple drawn cuts/patches around the package fanout",
    "D15": "EPROM area: Разрезать is on the auxiliary vertical trace between its second/third shown vias, aligned roughly between the eighth/ninth visible package-pad levels; position-159 patch detail is separate",
    "D14": "АП2 serial-driver area: position-159 leader enters a five-hole auxiliary/left field beside the four-pad package row; three long replacement traces and one right-row dogleg are drawn, but mirrored pin numbering is not proved",
    "D11": "8251 USART area: detail shows one 14-pad package column plus a four-hole auxiliary field and a position-159 bridge; a held-out-validated solder fit localizes the visible reworked copper beside D11 pins 4-6, but the obscured bridge endpoints remain unproved",
}


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    chips = {chip["ref"]: chip for chip in board["chips"]}
    bodge = BODGE.read_text(encoding="utf-8")
    detail_photos = [
        PHOTO_DIR / "PXL_20260711_114626340.jpg",
        PHOTO_DIR / "PXL_20260711_114633498.jpg",
        PHOTO_DIR / "PXL_20260711_114638730.MP.jpg",
    ]
    guard_ok = (
        all(ref in chips for ref in AFFECTED)
        and all(path.exists() and path.stat().st_size > 1_000_000 for path in detail_photos)
        and all(ref in bodge for ref in AFFECTED)
        and "Factory solder-side cuts and patches" in bodge
    )
    status = "FACTORY MODIFICATIONS GUARDED / PAD MAPPING REQUIRED" if guard_ok else "FACTORY MODIFICATION GUARD FAILED"

    lines = [
        "# Factory modification disposition",
        "",
        "Status date: **2026-07-11**.",
        "",
        f"Status: **{status}**",
        "",
        "The `ДГШ5.109.009 СБ` Вид В detail proves that positions 150/159",
        "modify copper around D56, D15, D14, and D11. The unnumbered detail",
        "mixes mounting-side context with solder-side artwork, so it does not",
        "yet prove package pin numbers or final net partitions. The generated",
        "clean PCB may be electrically equivalent, but equivalence is unproved.",
        "",
        "| Ref | Factory operation locality | Current disposition | Closure evidence |",
        "| --- | --- | --- | --- |",
    ]
    for ref, detail in AFFECTED.items():
        lines.append(row([
            ref,
            detail,
            "DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped",
            "registered two-sided copper overlay plus pad/via continuity (the acquired sheets 2-5 wire table covers wires/cables only, not cut pads)",
        ]))
    lines += [
        "",
        "## Guarded evidence",
        "",
        "- `PXL_20260711_114626340.jpg`: full Вид В and all four local details.",
        "- `PXL_20260711_114633498.jpg`: enlarged D15 Разрезать operation.",
        "- `PXL_20260711_114638730.MP.jpg`: full-resolution positions 150/159 context.",
        "- `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`: factory-versus-owner disposition.",
        "",
        "## Release rule",
        "",
        "Do not release or reroute the board on netlist equivalence alone. For each",
        "of D56/D15/D14/D11, identify the modified pad/via pair(s), the cut original",
        "segment, and the replacement connection; then prove the final source-PCB",
        "net partition matches the factory result.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if guard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
