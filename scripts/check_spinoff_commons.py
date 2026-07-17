#!/usr/bin/env python3
"""Shared-commons guard: keep spin-off consumers in step with the root facts.

Single source of truth is ref/juku-machine-facts.json (see docs/spinoff-commons.md).
This guard (a) validates that file's internal consistency and (b) verifies every
spin-off consumer that exists restates the canonical values, not divergent ones.
A root fact change that is not propagated then fails here instead of silently
drifting. Missing consumers (not yet created in the current phase) are skipped,
not failed, so the guard is green from the moment the facts file lands.

Patterned on scripts/check_documentation_consistency.py.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS_PATH = ROOT / "ref/juku-machine-facts.json"


def read(path: str) -> str:
    target = ROOT / path
    return target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""


def main() -> int:
    failures: list[str] = []
    checked: list[str] = []
    skipped: list[str] = []

    if not FACTS_PATH.exists():
        print("Shared-commons check failed:")
        print(f"- missing facts file: {FACTS_PATH.relative_to(ROOT)}")
        return 1
    try:
        facts = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print("Shared-commons check failed:")
        print(f"- facts file is invalid JSON: {exc}")
        return 1

    # ---- (a) internal consistency of the facts file itself ----
    fb = facts.get("framebuffer", {})
    if fb.get("bytes") != fb.get("cols", 0) * fb.get("rows", 0):
        failures.append(
            f"framebuffer bytes ({fb.get('bytes')}) != cols*rows "
            f"({fb.get('cols')}*{fb.get('rows')})"
        )
    if int(str(fb.get("base_addr_hex", "0x0")), 16) != fb.get("base_addr"):
        failures.append("framebuffer base_addr and base_addr_hex disagree")
    for section in ("framebuffer", "io_ports", "pic_wiring", "timing", "memory_overlay_modes"):
        if section not in facts:
            failures.append(f"facts file missing required section: {section}")
        elif "provenance" not in facts[section]:
            failures.append(f"facts section {section!r} has no provenance")

    # ---- canonical strings every consumer must restate verbatim ----
    ports = facts.get("io_ports", {})
    canon: list[tuple[str, str]] = [
        ("framebuffer base", fb.get("base_addr_hex", "")),
        ("framebuffer bytes", str(fb.get("bytes", ""))),
        ("framebuffer geometry", f"{fb.get('cols')}×{fb.get('rows')}"),  # 40×241
        ("frame IRQ period", str(facts.get("timing", {}).get("frame_irq_period_cycles", ""))),
        ("PIC A0=0 port", ports.get("pic_a0_0", {}).get("port_hex", "")),
        ("PIC A0=1 port", ports.get("pic_a0_1", {}).get("port_hex", "")),
        ("8255 Port A", ports.get("ppi_port_a", {}).get("port_hex", "")),
        ("8255 Port B", ports.get("ppi_port_b", {}).get("port_hex", "")),
        ("8255 Port C", ports.get("ppi_port_c", {}).get("port_hex", "")),
        ("8255 control", ports.get("ppi_control", {}).get("port_hex", "")),
        ("UART data port", ports.get("uart_data", {}).get("port_hex", "")),
        ("UART ctl port", ports.get("uart_ctl", {}).get("port_hex", "")),
        ("FDC ports", ports.get("fdc", {}).get("ports_hex", "")),
    ]

    # ---- (b) consumers: docs that must restate the canon ----
    doc_consumers = {
        "bus contract": "spinoffs/minimal-vga/docs/rev-b-bus-contract.md",
    }
    for label, path in doc_consumers.items():
        text = read(path)
        if not text:
            skipped.append(path)
            continue
        checked.append(path)
        for name, value in canon:
            if value and value not in text:
                failures.append(f"{path} ({label}) omits canonical {name}: {value!r}")

    # ---- (b) consumers: rev B HDL must define the framebuffer base as the canonical
    # value. Check the FB_BASE localparam specifically (not every 0xD8xx address, which
    # legitimately appears as framebuffer-window addresses in card logic and TBs).
    revb_dir = ROOT / "spinoffs/minimal-vga/hdl/revb"
    if revb_dir.is_dir():
        base_hex = fb.get("base_addr_hex", "0xD800")[2:].upper()  # "D800"
        fb_base_re = re.compile(r"FB_BASE\s*=\s*16'h([0-9A-Fa-f]{4})")
        for vfile in sorted(revb_dir.glob("*.v")):
            vtext = vfile.read_text(encoding="utf-8", errors="replace")
            rel = str(vfile.relative_to(ROOT))
            checked.append(rel)
            for lit in fb_base_re.findall(vtext):
                if lit.upper() != base_hex:
                    failures.append(
                        f"{rel} defines FB_BASE=16'h{lit} != canonical 16'h{base_hex}"
                    )
    else:
        skipped.append(str(revb_dir.relative_to(ROOT)) + "/ (not created yet)")

    if failures:
        print("Shared-commons check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        f"Shared-commons consistent; facts OK; "
        f"checked {len(checked)} consumer(s); skipped {len(skipped)} not-yet-present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
