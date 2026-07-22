#!/usr/bin/env python3
"""Keep the board's assembly picture consistent with the model (no phantom parts).

The model (kicad/juku.board.json) is the source of truth for what is populated.
This guard, run KiCad-free so it works in CI, loads a built .kicad_pcb and
asserts the artwork agrees with the model, catching preview/model drift:

  1. Population consistency -- an unpopulated socket (`populated: false`) must be
     DNP AND have its chip Value hidden (so the silk/preview shows an empty
     socket, not a phantom К573РФ5 / 565РУ3Г). A modeled-populated ROM/RAM must
     be the opposite: value visible, not DNP.
  2. Decoupling scheme lock -- the .009 DRAM field fits exactly the 4 factory
     bypass caps (C38/C42/C46/C50); every `assembly_dnp` grid cap must stay DNP
     and the 4 fitted caps must not. (Answers "why are some RAM decaps missing":
     the factory fits one per every-other package -- see docs/decap-value-fidelity.md.)
  3. Socket attribute lock -- the documented-socketed parts keep `socketed: true`
     in the model.

Run: check_board_population.py [board.kicad_pcb ...]   (defaults to both boards)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FITTED_DECAPS = {"C38", "C42", "C46", "C50"}
EXPECTED_SOCKETED = {"D2", "D6", "D8"} | {f"D{n}" for n in range(15, 23)}
DEFAULT_BOARDS = ["kicad/juku.kicad_pcb", "kicad/juku_routed.kicad_pcb"]


def balanced(s, start):
    depth = 0
    for k in range(start, len(s)):
        if s[k] == "(":
            depth += 1
        elif s[k] == ")":
            depth -= 1
            if depth == 0:
                return k + 1
    raise ValueError("unbalanced s-expr")


def footprints(s):
    """Yield (ref, is_dnp, value_hidden) for each footprint in the board text."""
    idx = 0
    while True:
        j = s.find("\t(footprint ", idx)
        if j < 0:
            break
        end = balanced(s, j + 1)
        block = s[j:end]
        idx = end
        rm = re.search(r'\(property "Reference" "([^"]*)"', block)
        if not rm:
            continue
        ref = rm.group(1)
        attr = re.search(r'\(attr ([^)]*)\)', block)
        is_dnp = bool(attr) and "dnp" in attr.group(1).split()
        vhidden = False
        vm = re.search(r'\(property "Value" "', block)
        if vm:
            vprop = block[vm.start():balanced(block, vm.start())]
            vhidden = "(hide yes)" in vprop
        yield ref, is_dnp, vhidden


def load_model():
    return json.loads((ROOT / "kicad" / "juku.board.json").read_text(encoding="utf-8"))


def check_board(path, model):
    chips = {c["ref"]: c for c in model["chips"]}
    unpopulated = {r for r, c in chips.items() if c.get("populated") is False}
    # Modeled-populated ROM/RAM sockets: same socket types, minus the empty ones.
    socket_types = {"EPROM8K", "RU5"}
    populated_sockets = {r for r, c in chips.items()
                         if c.get("type") in socket_types and r not in unpopulated}
    dnp_caps = {c["ref"] for c in model["chips"] if c.get("assembly_dnp")}

    fp = {ref: (d, v) for ref, d, v in footprints(Path(path).read_text(encoding="utf-8"))}
    errors = []

    for ref in sorted(unpopulated):
        if ref not in fp:
            continue
        is_dnp, vhidden = fp[ref]
        if not vhidden:
            errors.append(f"{ref}: unpopulated in model but chip value is SHOWN "
                          f"(phantom populated part in preview)")
        if not is_dnp:
            errors.append(f"{ref}: unpopulated in model but footprint is not DNP")

    for ref in sorted(populated_sockets):
        if ref not in fp:
            continue
        is_dnp, vhidden = fp[ref]
        if vhidden:
            errors.append(f"{ref}: populated in model but chip value is HIDDEN")
        if is_dnp:
            errors.append(f"{ref}: populated in model but footprint is DNP")

    for ref in sorted(FITTED_DECAPS):
        if ref in fp and fp[ref][0]:
            errors.append(f"{ref}: fitted factory bypass cap must not be DNP")
    for ref in sorted(dnp_caps):
        if ref in fp and not fp[ref][0]:
            errors.append(f"{ref}: modeled assembly_dnp cap is not DNP on the board")

    if not errors:
        print(f"  {Path(path).name}: OK "
              f"({len(unpopulated)} empty sockets hidden+DNP, "
              f"{len(populated_sockets)} populated sockets shown, "
              f"{len(FITTED_DECAPS)} decaps fitted / {len(dnp_caps)} DNP)")
    return errors


def check_socket_attributes(model):
    got = {c["ref"] for c in model["chips"] if c.get("socketed") is True}
    errors = []
    for ref in sorted(EXPECTED_SOCKETED - got):
        errors.append(f"{ref}: documented-socketed part missing `socketed: true` in model")
    return errors


def main():
    model = load_model()
    boards = sys.argv[1:] or DEFAULT_BOARDS
    print("Juku board population/assembly consistency check:")
    all_errors = list(check_socket_attributes(model))
    for b in boards:
        if not Path(b).exists():
            all_errors.append(f"{b}: not found")
            continue
        all_errors += [f"{Path(b).name}: {e}" for e in check_board(b, model)]
    if all_errors:
        print("FAIL:")
        for e in all_errors:
            print(f"  - {e}")
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
