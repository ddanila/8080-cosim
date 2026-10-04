#!/usr/bin/env python3
"""Report footprint placement drift from the source PCB to routed variants."""

from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "kicad/juku.kicad_pcb"
ROUTED = [ROOT / "kicad/juku_routed.kicad_pcb", ROOT / "kicad/juku_routed_candidate.kicad_pcb"]
REPORT = ROOT / "docs/board-placement-parity.md"


def placements(path: Path) -> dict[str, tuple[float, float, float]]:
    board = pcbnew.LoadBoard(str(path))
    return {
        footprint.GetReference(): (
            pcbnew.ToMM(footprint.GetPosition().x),
            pcbnew.ToMM(footprint.GetPosition().y),
            footprint.GetOrientationDegrees() % 360,
        )
        for footprint in board.GetFootprints()
    }


def differs(a: tuple[float, float, float], b: tuple[float, float, float]) -> bool:
    return abs(a[0] - b[0]) > 0.01 or abs(a[1] - b[1]) > 0.01 or abs((a[2] - b[2] + 180) % 360 - 180) > 0.1


def fmt(pos: tuple[float, float, float]) -> str:
    return f"({pos[0]:.3f}, {pos[1]:.3f}) mm / {pos[2]:.1f}°"


def main() -> int:
    source = placements(SOURCE)
    lines = [
        "# Source-to-routed footprint placement parity", "",
        "This compares footprint reference, placement anchor, and rotation in the source PCB with both routed variants. Tolerance: 0.01 mm per coordinate and 0.1° by the shortest angular difference. It does not verify whether the source PCB itself matches the owner board or whether copper follows a moved footprint.", "",
        "The coordinates are KiCad footprint placement anchors, which can differ",
        "from package or pad-array centers. Footprint geometry and pad nets are not",
        "compared. A nonzero exit status reports placement gaps.", "",
        "## Command", "", "```sh", "/usr/bin/python3 kicad/report_board_placement_parity.py", "```", "",
        "| Routed PCB | Missing source refs | Extra refs | Moved/rotated refs |", "| --- | --- | --- | --- |",
    ]
    details = {}
    total_gaps = 0
    for path in ROUTED:
        routed = placements(path)
        missing = sorted(source.keys() - routed.keys())
        extra = sorted(routed.keys() - source.keys())
        changed = sorted(ref for ref in source.keys() & routed.keys() if differs(source[ref], routed[ref]))
        total_gaps += len(missing) + len(extra) + len(changed)
        lines.append(f"| `{path.relative_to(ROOT)}` | {', '.join(missing) or 'none'} | {', '.join(extra) or 'none'} | {', '.join(changed) or 'none'} |")
        for ref in changed:
            details.setdefault((ref, source[ref], routed[ref]), []).append(path.name)
    lines += ["", "## Position differences", "", "| Routed PCB | Ref | Source anchor / rotation | Routed anchor / rotation |", "| --- | --- | --- | --- |"]
    for (ref, source_pos, routed_pos), boards in details.items():
        label = "Both variants" if len(boards) == len(ROUTED) else ", ".join(f"`{name}`" for name in boards)
        lines.append(f"| {label} | `{ref}` | {fmt(source_pos)} | {fmt(routed_pos)} |")
    lines += [
        "", "## Placement evidence", "",
        "The tables report current source/routed differences. Photo qualification",
        "and routing constraints are recorded separately:", "",
        "- [D11 cross-view placement](../ref/photos/juku-pcb-2/d11-placement-crossview-audit.json)",
        "- [D12/D3 local placement](../ref/photos/juku-pcb-2/d12-d3-local-placement.json)",
        "- [R9/R10 routed collision audit](r9-r10-routed-collision-audit.md)", "",

    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Placement parity: {total_gaps} source-to-routed gaps across {len(ROUTED)} boards")
    return int(bool(total_gaps))


if __name__ == "__main__":
    raise SystemExit(main())
