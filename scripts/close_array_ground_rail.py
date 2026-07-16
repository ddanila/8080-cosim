#!/usr/bin/env python3
"""Close the native sheet-2 DRAM rail-E ground connection in board artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
PCBS = (
    ROOT / "kicad" / "juku.kicad_pcb",
    ROOT / "kicad" / "juku_routed.kicad_pcb",
    ROOT / "kicad" / "juku_routed_candidate.kicad_pcb",
)


def net_span(text: str, name: str) -> tuple[int, int]:
    start = text.index(f'  "{name}": {{')
    next_key = re.search(r'^  "[^"]+": \{', text[start + 1 :], re.MULTILINE)
    end = start + 1 + next_key.start() if next_key else len(text)
    return start, end


def node_content(block: str, name: str) -> tuple[int, int, str]:
    marker = '   "nodes": [\n'
    start = block.index(marker) + len(marker)
    end = block.rindex("\n   ]")
    return start, end, block[start:end]


def replace_node_content(text: str, name: str, transform) -> str:
    start, end = net_span(text, name)
    block = text[start:end]
    node_start, node_end, content = node_content(block, name)
    block = block[:node_start] + transform(content) + block[node_end:]
    return text[:start] + block + text[end:]


def append_node_content(text: str, name: str, addition: str) -> str:
    return replace_node_content(text, name, lambda content: content + ",\n" + addition)


def remove_last_node(text: str, name: str, ref: str, pin: str) -> str:
    target = f'    [\n     "{ref}",\n     "{pin}"\n    ]'

    def remove(content: str) -> str:
        suffix = ",\n" + target
        if not content.endswith(suffix):
            raise SystemExit(f"{name}: expected {ref}.{pin} as final node")
        return content[: -len(suffix)]

    return replace_node_content(text, name, remove)


def remove_net(text: str, name: str) -> str:
    start, end = net_span(text, name)
    if end == len(text):
        raise SystemExit(f"{name}: cannot remove final net safely")
    return text[:start] + text[end:]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected one exact source phrase, found {text.count(old)}")
    return text.replace(old, new)


def merge_pcb_net(path: Path, source: str, destination: str) -> None:
    text = path.read_text()
    source_match = re.search(rf'^\s*\(net (\d+) "{re.escape(source)}"\)$', text, re.MULTILINE)
    destination_match = re.search(
        rf'^\s*\(net (\d+) "{re.escape(destination)}"\)$', text, re.MULTILINE
    )
    if not source_match or not destination_match:
        raise SystemExit(f"{path}: missing {source} or {destination} net declaration")
    source_id, destination_id = source_match.group(1), destination_match.group(1)
    declaration = source_match.group(0) + "\n"
    text = text.replace(declaration, "", 1)
    text = text.replace(f'(net {source_id} "{source}")', f'(net {destination_id} "{destination}")')
    text = text.replace(f"(net {source_id})", f"(net {destination_id})")
    text = text.replace(f'(net_name "{source}")', f'(net_name "{destination}")')
    if source in text:
        raise SystemExit(f"{path}: residual {source} text after merge")
    path.write_text(text)


def assign_c34_pcb(path: Path, target_net: str) -> bool:
    text = path.read_text()
    target = re.search(
        rf'^\s*\(net (\d+) "{re.escape(target_net)}"\)$', text, re.MULTILINE
    )
    if not target:
        raise SystemExit(f"{path}: missing {target_net} declaration")
    starts = [match.start() for match in re.finditer(r'^\s*\(footprint\s', text, re.MULTILINE)]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        block = text[start:end]
        if '(property "Reference" "C34"' not in block:
            continue
        pad_start = block.find('(pad "1"')
        pad_end = block.find('\n\t\t)', pad_start)
        if pad_start < 0 or pad_end < 0:
            raise SystemExit(f"{path}: cannot isolate C34 pad 1")
        pad = block[pad_start:pad_end]
        if '(net ' in pad and f'"{target_net}")' in pad:
            return False
        updated, count = re.subn(
            r'\(net \d+ "[^"]+"\)',
            f'(net {target.group(1)} "{target_net}")',
            pad,
            count=1,
        )
        if count != 1:
            raise SystemExit(f"{path}: C34 pad 1 lacks one net assignment")
        block = block[:pad_start] + updated + block[pad_end:]
        path.write_text(text[:start] + block + text[end:])
        return True
    raise SystemExit(f"{path}: C34 footprint not found")


def apply() -> None:
    text = BOARD.read_text()
    board = json.loads(text)
    nets = board["nets"]
    source_nodes = nets["RAIL_E"]["nodes"]
    if len(source_nodes) != 75:
        raise SystemExit(f"RAIL_E endpoint count changed: {len(source_nodes)} != 75")
    if set(map(tuple, source_nodes)) & set(map(tuple, nets["GND"]["nodes"])):
        raise SystemExit("RAIL_E and GND unexpectedly share an endpoint")

    source_start, source_end = net_span(text, "RAIL_E")
    _, _, source_content = node_content(text[source_start:source_end], "RAIL_E")
    text = append_node_content(text, "GND", source_content)
    text = remove_last_node(text, "RAIL_H", "C34", "1")
    text = append_node_content(text, "P5V", '    [\n     "C34",\n     "1"\n    ]')
    text = remove_net(text, "RAIL_E")

    text = text.replace("RAIL_G<->RAIL_E", "RAIL_G<->GND")
    text = text.replace("RAIL_E<->RAIL_H", "GND<->RAIL_H")
    text = replace_once(
        text,
        "RAIL_H to ground bypass; connected nets RAIL_H/GND carry crop evidence",
        "native sheet-2 C34 bypass from grounded rail E to +5 V rail F; connected nets GND/P5V carry direct crop evidence",
        "C34 provenance",
    )
    text = replace_once(
        text,
        'traced sheet-2 power corner (crop b3_pwr_corner) + array read: E5 -> \\"-5V\\" array pin-1 rail (РУ3 VBB; РУ5 = NC); C54-72 bypass to rail E, C34 to F(~GND)',
        'native sheet-2 power corner: E5 -> \\"-5V\\" array pin-1 rail H (РУ3 VBB; РУ5 = NC); C54-C72 bypass H to grounded rail E',
        "RAIL_H provenance",
    )
    text = replace_once(
        text,
        "scan; sheet-1 arrow-A rail ties address-buffer direction pins D4.11/D107.11 and PIC master strap D10.16 high",
        "scan; sheet-1 arrow-A rail ties address-buffer direction pins D4.11/D107.11 and PIC master strap D10.16 high; native sheet-2 power corner continues +5 V rail A to rail F and C34.1",
        "P5V provenance",
    )
    text = replace_once(
        text,
        "two independent component photographs plus the factory position-159 detail show uninterrupted copper from D32.4 GND to D14.1",
        "two independent component photographs plus the factory position-159 detail show uninterrupted copper from D32.4 GND to D14.1; native sheet-2 power corner directly grounds rail E, including all DRAM pin-16 and strobe-pulldown endpoints",
        "GND provenance",
    )
    # Remaining occurrences are passive-provenance phrases such as
    # "connected nets RAS/RAIL_E". The electrical net no longer exists.
    text = text.replace("RAIL_E", "GND")
    BOARD.write_text(text)
    json.loads(text)
    for pcb in PCBS:
        merge_pcb_net(pcb, "RAIL_E", "GND")


def repair_pcbs() -> None:
    repaired = []
    for pcb in PCBS:
        if "RAIL_E" in pcb.read_text():
            merge_pcb_net(pcb, "RAIL_E", "GND")
            repaired.append(pcb.relative_to(ROOT).as_posix())
    if assign_c34_pcb(PCBS[0], "P5V"):
        repaired.append(PCBS[0].relative_to(ROOT).as_posix() + " C34.1")
    print("Repaired PCB rail names: " + (", ".join(repaired) if repaired else "none"))


def check() -> None:
    board = json.loads(BOARD.read_text())
    nets = board["nets"]
    failures = []
    if "RAIL_E" in nets:
        failures.append("RAIL_E remains a separate board net")
    if "RAIL_E" in BOARD.read_text():
        failures.append("board provenance retains the retired RAIL_E name")
    ground = set(map(tuple, nets["GND"]["nodes"]))
    expected_ground = {
        *((f"D{ref}", "16") for ref in range(60, 92)),
        *((f"C{ref}", "2") for ref in range(35, 54)),
        *((f"C{ref}", "1") for ref in range(54, 73)),
        *((ref, "2") for ref in ("R53", "R54", "R55", "R56", "R58")),
    }
    missing = expected_ground - ground
    if missing:
        failures.append(f"grounded rail-E endpoints missing: {sorted(missing)}")
    if ("C34", "1") not in set(map(tuple, nets["P5V"]["nodes"])):
        failures.append("C34.1 is not on sheet-2 rail F / P5V")
    if ("C34", "1") in set(map(tuple, nets["RAIL_H"]["nodes"])):
        failures.append("C34.1 incorrectly remains on -5 V rail H")
    if ("C34", "2") not in ground:
        failures.append("C34.2 is not on sheet-2 rail E / GND")
    for pcb in PCBS:
        pcb_text = pcb.read_text()
        if "RAIL_E" in pcb_text:
            failures.append(f"{pcb.relative_to(ROOT)} retains RAIL_E")
        starts = [match.start() for match in re.finditer(r'^\s*\(footprint\s', pcb_text, re.MULTILINE)]
        c34 = ""
        for index, start in enumerate(starts):
            end = starts[index + 1] if index + 1 < len(starts) else len(pcb_text)
            block = pcb_text[start:end]
            if '(property "Reference" "C34"' in block:
                c34 = block
                break
        pad_start = c34.find('(pad "1"')
        pad_end = c34.find('\n\t\t)', pad_start)
        if pcb == PCBS[0] and (pad_start < 0 or '"P5V")' not in c34[pad_start:pad_end]):
            failures.append(f"{pcb.relative_to(ROOT)} C34.1 is not on P5V")
    if failures:
        raise SystemExit("\n".join(failures))
    print("ARRAY-GROUND-RAIL: PASS (75 rail-E endpoints on GND; C34 spans GND/P5V)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="perform the one-time source correction")
    parser.add_argument(
        "--repair-pcbs",
        action="store_true",
        help="apply the net-only correction to any lagging tracked PCB",
    )
    args = parser.parse_args()
    if args.apply:
        apply()
    if args.repair_pcbs:
        repair_pcbs()
    check()


if __name__ == "__main__":
    main()
