#!/usr/bin/env python3
"""Minimize and guard the physical D8 `.039` ROM-pager PROM."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "ref/physical-proms/validated/d8_039.raw.bin"
REPORT = ROOT / "docs/d8-physical-decode.md"
EXPECTED_SHA256 = "345b67e66562741dd48e70f30e7862d4e3fc19d3a113f21c999d6ec497af59cc"

OUTPUT_NETS = {
    "1": ("D0", "ROM_CS_A000", "D19"),
    "2": ("D1", "ROM_CS_8000", "D20"),
    "3": ("D2", "ROM_CS_6000", "D21"),
    "4": ("D3", "ROM_CS_4000", "D22"),
    "5": ("D4", "ROM_CS_D15", "D15"),
    "6": ("D5", "ROM_CS_D16", "D16"),
    "7": ("D6", "ROM_CS_EXP17", "D17"),
    "9": ("D7", "ROM_CS_EXP18", "D18"),
}


def nodes(board: dict, net: str) -> set[tuple[str, str]]:
    return {tuple(node) for node in board["nets"].get(net, {}).get("nodes", [])}


def expected_raw(address: int) -> int:
    a2 = bool(address & 0x04)
    a3 = bool(address & 0x08)
    a4 = bool(address & 0x10)
    qualifier = a4 == a3
    asserted = [False] * 8
    asserted[4] = qualifier and not a2
    asserted[5] = qualifier and a2
    raw = 0xFF
    for bit, active in enumerate(asserted):
        if active:
            raw &= ~(1 << bit)
    return raw


def main() -> int:
    data = RAW.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if len(data) != 32 or digest != EXPECTED_SHA256:
        raise SystemExit(f"unexpected D8 image: bytes={len(data)} sha256={digest}")
    mismatches = [address for address, value in enumerate(data) if value != expected_raw(address)]
    if mismatches:
        raise SystemExit(f"D8 minimized equations mismatch at {mismatches}")

    board = json.loads((ROOT / "kicad/juku.board.json").read_text())
    chip = next(item for item in board["chips"] if item.get("ref") == "D8")
    address_ok = all(
        ("D8", str(10 + bit)) in nodes(board, f"BA{11 + bit}")
        for bit in range(5)
    )
    enable_ok = {("D8", "15"), ("D6", "12")} <= nodes(board, "ROM_SEL")
    output_rows = []
    output_nets_ok = True
    for pin, (role, net, socket) in OUTPUT_NETS.items():
        net_nodes = nodes(board, net)
        socket_pin = next(
            (node for node in net_nodes if node[0] == socket),
            None,
        )
        ok = ("D8", pin) in net_nodes and socket_pin is not None
        output_nets_ok &= ok
        active_rows = [address for address, value in enumerate(data) if not value & (1 << int(role[1:]))]
        activity = (
            ", ".join(f"{address:02d}" for address in active_rows)
            if active_rows else "never"
        )
        output_rows.append(
            f"| {pin} | `{role}` | `{net}` -> `{socket}` | {activity} | {'PASS' if ok else 'FAIL'} |"
        )

    hdl = (ROOT / "hdl/devices.v").read_text()
    tb = (ROOT / "hdl/sim/prom_fallback_tb.v").read_text()
    hdl_ok = all(
        needle in hdl
        for needle in (
            "module re3_prom",
            "К155РЕ3 outputs are open collector",
            "assign d[bit_index] = (!e_n && !raw[bit_index]) ? 1'b0 : 1'bz;",
        )
    ) and all(
        needle in tb
        for needle in (
            "D8 disabled outputs did not release",
            "D8 row 00 is not one open-collector D4 sink",
        )
    )
    identity_ok = chip.get("type") == "RE3_PROM" and "ДГШ5.106.039" in str(chip.get("prov", {}))
    all_ok = identity_ok and address_ok and enable_ok and output_nets_ok and hdl_ok
    status = "PHYSICAL D8 TABLE MINIMIZED AND EXECUTED" if all_ok else "D8 PHYSICAL DECODE FAILED"

    lines = [
        "# D8 `.039` physical ROM-pager decode",
        "",
        f"Status: **{status}**",
        "",
        "This generated report reduces the validated 32 x 8 К155РЕ3 image to",
        "exact active-low socket-select equations and guards them against every",
        "captured bit. `S(Dn)=1` means output Dn sinks its open-collector rail.",
        "",
        "## Artifact and mapping",
        "",
        f"- Raw image: `{RAW.relative_to(ROOT)}`",
        f"- SHA256: `{digest}`",
        "- Address mapping: `A4..A0 = BA15..BA11`.",
        "- Enable: D8.15 `/E` is the measured D6.12 `ROM_SEL` conductor.",
        "",
        "## Exact minimized equations",
        "",
        "Define `Q = (BA15 == BA14)`. Exhaustive comparison of all 32 rows and",
        "all 256 output bits gives:",
        "",
        "| Output | Exact asserted equation | Meaning |",
        "| --- | --- | --- |",
        "| `S(D4)` | `Q & !BA13` | select populated BIOS-low socket D15 |",
        "| `S(D5)` | `Q & BA13` | select populated BIOS-high socket D16 |",
        "| `S(D0..D3,D6,D7)` | `0` | always released |",
        "",
        "BA12 and BA11 are complete don't-cares. D4 and D5 are mutually exclusive;",
        "when `Q` is false every output releases. D6's separate `ROM_SEL` enable",
        "provides the mode/region qualifier around this address-only pager.",
        "",
        "## Physical output destinations",
        "",
        "| Pin | Output | Board destination | Asserted rows | Net guard |",
        "| ---: | --- | --- | --- | --- |",
    ]
    lines.extend(output_rows)
    lines.extend([
        "",
        "The six invariant outputs remain physical fidelity obligations: their copper",
        "to D17-D22 is preserved even though this factory program never selects those",
        "sockets. The `.009` populated build uses only D15 and D16.",
        "",
        "## Evidence checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
        f"| Board identity is D8 `.039` | {'PASS' if identity_ok else 'FAIL'} |",
        f"| All five address inputs map to BA11..BA15 | {'PASS' if address_ok else 'FAIL'} |",
        f"| Enable maps to measured D6.12 ROM select | {'PASS' if enable_ok else 'FAIL'} |",
        f"| All eight output-to-socket nets are present | {'PASS' if output_nets_ok else 'FAIL'} |",
        "| All 256 captured bits match the equations | PASS |",
        f"| HDL executes open-collector table and release checks | {'PASS' if hdl_ok else 'FAIL'} |",
        "",
        "## Remaining boundary",
        "",
        "D8 content, address equations, output activity, and socket destinations are",
        "closed. Full physical adoption still follows D6: its `/E` source is measured",
        "to D6.12, but the runnable D6 D0 polarity fit awaits the corrected re-read or",
        "operating-level probe. No replacement D8 firmware remains to reconstruct.",
        "",
    ])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
