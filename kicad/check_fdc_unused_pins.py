#!/usr/bin/env python3
"""Guard exact-revision sheet-3 no-connect dispositions in the FDC cluster."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = json.loads((ROOT / "kicad/juku.board.json").read_text(encoding="utf-8"))
HDL = (ROOT / "hdl/juku_top.v").read_text(encoding="utf-8")
DEVICES = (ROOT / "hdl/devices.v").read_text(encoding="utf-8")
LVS_MAP = json.loads((ROOT / "sync/map.json").read_text(encoding="utf-8"))
NETS = {
    name: {f"{ref}.{pin}" for ref, pin in item.get("nodes", [])}
    for name, item in BOARD["nets"].items()
}

EXPECTED_NC = {
    "D97.13", "D98.9", "D98.10", "D102.4", "D96.13",
}
actual_nc = {f"{ref}.{pin}" for ref, pin in BOARD.get("no_connects", [])}
missing = EXPECTED_NC - actual_nc
if missing:
    raise SystemExit(f"FDC UNUSED: no-connects missing {sorted(missing)}")

connected = {
    node: name
    for name, nodes in NETS.items()
    for node in EXPECTED_NC & nodes
}
if connected:
    raise SystemExit(f"FDC UNUSED: NC pins returned to nets: {connected}")

EXPECTED_USED = {
    "D98_Y1_D28_READY": {"D98.3", "D28.5"},
    "FDC_READY": {"D28.6", "D93.23", "D93.32", "R84.1"},
    "FDC_RAW_READ": {"D97.4", "D93.27", "D106.11"},
    "PRECOMP_TAP_3": {"D102.13", "D101.12"},
    "FDC_INTRQ": {"D93.39", "D28.13", "R93.1"},
    "FDC_DRQ": {"D93.38", "D28.11", "R94.1"},
    "FDC_IRQ_CONDITIONED_N": {"D28.10", "D28.12", "D96.10", "D96.12", "R95.1"},
}
for name, expected in EXPECTED_USED.items():
    if NETS.get(name) != expected:
        raise SystemExit(
            f"FDC UNUSED: {name} {sorted(NETS.get(name, set()))} != {sorted(expected)}"
        )
if {f"D28.{pin}" for pin in ("5", "6", "10", "11", "12", "13")} & actual_nc:
    raise SystemExit("FDC UNUSED: live D28 READY/IRQ conditioner pins are marked NC")

obsolete = {
    "D28_A5_BOUNDARY", "D28_Y5_BOUNDARY", "D28_Y6_BOUNDARY", "D28_A6_BOUNDARY",
    "D97_Q1_BOUNDARY", "D98_Y4_BOUNDARY", "D98_A4_BOUNDARY",
    "D102_Q1N_BOUNDARY",
}
returned = obsolete & NETS.keys()
if returned:
    raise SystemExit(f"FDC UNUSED: obsolete boundaries returned: {sorted(returned)}")

sources = {
    "PXL_20260718_101633062.jpg": "5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047",
    "PXL_20260718_101641055.jpg": "86740a80fb494cdb08f4de3a120cab83e4f6638cf5885d4c83418a4a94c881a7",
    "PXL_20260718_101648508.jpg": "ef04482bdd7f15a20e132034709bb7b6dfab54d6ac9d4efe2f6510575b4aa641",
}
photo_dir = ROOT / "ref/photos/dgsh5-109-009-e3"
for name, expected in sources.items():
    payload = (photo_dir / name).read_bytes()
    if payload.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
        pointer = payload.decode("ascii")
        match = re.search(r"^oid sha256:([0-9a-f]{64})$", pointer, re.MULTILINE)
        actual = match.group(1) if match else "invalid-lfs-pointer"
    else:
        actual = hashlib.sha256(payload).hexdigest()
    if actual != expected:
        raise SystemExit(f"FDC UNUSED: source hash changed for {name}: {actual}")

pcb = (ROOT / "kicad/juku.kicad_pcb").read_text(encoding="utf-8")


def pad_net(ref: str, pin: str) -> str | None:
    ref_pos = pcb.index(f'(property "Reference" "{ref}"')
    footprint = pcb[pcb.rfind("\n\t(footprint", 0, ref_pos):pcb.find("\n\t(footprint", ref_pos)]
    match = re.search(
        rf'\n\t\t\(pad "{pin}"[\s\S]*?(?=\n\t\t\(pad|\n\t\t\(embedded_fonts)',
        footprint,
    )
    if not match:
        raise SystemExit(f"FDC UNUSED: source PCB missing {ref}.{pin}")
    net_match = re.search(r'\n\t\t\t\(net \d+ "([^"]+)"\)', match.group())
    return net_match.group(1) if net_match else None


for node in sorted(EXPECTED_NC):
    ref, pin = node.split(".")
    actual = pad_net(ref, pin)
    if actual is not None:
        raise SystemExit(f"FDC UNUSED: source PCB {node} still has net {actual!r}")
for node, expected in {
    "D28.5": "D98_Y1_D28_READY", "D28.6": "FDC_READY",
    "D28.10": "FDC_IRQ_CONDITIONED_N", "D28.11": "FDC_DRQ",
    "D28.12": "FDC_IRQ_CONDITIONED_N", "D28.13": "FDC_INTRQ",
}.items():
    ref, pin = node.split(".")
    actual = pad_net(ref, pin)
    if actual != expected:
        raise SystemExit(f"FDC UNUSED: source PCB {node} net {actual!r} != {expected!r}")

for ref in ("D28", "D98"):
    if LVS_MAP["instances"].get(ref) != f"U_{ref}":
        raise SystemExit(f"FDC UNUSED: {ref} is outside LVS scope")
for marker, text in {
    "module ln3_oc_inv": DEVICES,
    "module lp11_buf": DEVICES,
    "ln3_oc_inv U_D28": HDL,
    "lp11_buf U_D98": HDL,
    ".a5(fdc_drq), .y5(d96_irq_conditioned_boundary)": HDL,
    ".a6(fdc_intrq), .y6(d96_irq_conditioned_boundary)": HDL,
    ".a4(1'bz), .y4()": HDL,
}.items():
    if marker not in text:
        raise SystemExit(f"FDC UNUSED: structural HDL marker missing: {marker}")

print("FDC UNUSED: PASS — D28 IRQ gates restored; D98 buffer 4 and complementary D97/D102 outputs remain omitted")
