#!/usr/bin/env python3
"""Regenerate a temporary board and compare every source footprint pad."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "kicad/juku.board.json"
SOURCE = ROOT / "kicad/juku.kicad_pcb"
GENERATOR = ROOT / "kicad/gen_kicad_pcb.py"


def pads(board: pcbnew.BOARD) -> dict[str, dict[str, pcbnew.PAD]]:
    return {
        fp.GetReference(): {pad.GetNumber(): pad for pad in fp.Pads()}
        for fp in board.GetFootprints()
    }


def signature(pad: pcbnew.PAD) -> tuple[object, ...]:
    pos = pad.GetPosition()
    size = pad.GetSize()
    drill = pad.GetDrillSize()
    return (
        pos.x, pos.y, pad.GetNetname(), size.x, size.y,
        drill.x, drill.y, pad.GetShape(), pad.GetAttribute(),
        pad.GetLayerSet().FmtBin(),
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="juku-generator-pad-parity-") as directory:
        generated = Path(directory) / "generated.kicad_pcb"
        result = subprocess.run(
            [sys.executable, str(GENERATOR), str(SPEC), str(generated)],
            cwd=ROOT, text=True, capture_output=True,
        )
        if result.returncode:
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            return result.returncode
        source_pads = pads(pcbnew.LoadBoard(str(SOURCE)))
        generated_pads = pads(pcbnew.LoadBoard(str(generated)))

    failures = []
    for ref in sorted(source_pads.keys() | generated_pads.keys()):
        if ref not in source_pads or ref not in generated_pads:
            failures.append(f"{ref}: footprint exists on only one board")
            continue
        old, new = source_pads[ref], generated_pads[ref]
        if old.keys() != new.keys():
            failures.append(f"{ref}: pad-number sets differ")
            continue
        for number in sorted(old):
            old_sig, new_sig = signature(old[number]), signature(new[number])
            fields = ("x", "y", "net", "size_x", "size_y", "drill_x", "drill_y", "shape", "attribute", "layers")
            differences = [
                f"{name} {left!r}->{right!r}"
                for index, (name, left, right) in enumerate(zip(fields, old_sig, new_sig))
                if (abs(left - right) > 1000 if index < 2 else left != right)
            ]  # 1 µm position tolerance absorbs KiCad integer rounding.
            if differences:
                failures.append(f"{ref}.{number}: {', '.join(differences)}")
    for failure in failures[:50]:
        print("FAIL:", failure)
    if len(failures) > 50:
        print(f"... {len(failures) - 50} further mismatches")
    if failures:
        return 1
    total = sum(len(ref_pads) for ref_pads in source_pads.values())
    print(f"SOURCE GENERATOR PAD PARITY: PASS — {len(source_pads)} footprints, {total} pads")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
