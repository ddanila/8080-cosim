#!/usr/bin/env python3
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


CHECKER_PATH = Path(__file__).with_name("check_rev_a_physical.py")


def load_checker():
    spec = importlib.util.spec_from_file_location("check_rev_a_physical", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def build_report(board_json):
    checker = load_checker()
    spec = json.loads(board_json.read_text())
    refs = {chip["ref"] for chip in spec["chips"]}
    nets = spec["nets"]
    no_connects = {tuple(item) for item in spec.get("no_connects", [])}
    pin_index = {(chip["ref"], pin) for chip in spec["chips"] for pin in chip["pins"]}

    failures = []
    missing_refs = sorted(checker.REQUIRED_REFS - refs)
    missing_nets = sorted(checker.REQUIRED_NETS - set(nets))
    if missing_refs:
        failures.append("Missing required refs: " + ", ".join(missing_refs))
    if missing_nets:
        failures.append("Missing required nets: " + ", ".join(missing_nets))

    binding_rows = []
    chips = {chip["ref"]: chip for chip in spec["chips"]}
    binding_failures = 0
    for ref, expected in sorted(checker.REQUIRED_PIN_BINDINGS.items()):
        pins = chips.get(ref, {}).get("pins", {})
        for pin, expected_name in sorted(expected.items(), key=lambda item: int(item[0])):
            actual_name = pins.get(pin)
            ok = actual_name == expected_name
            if not ok:
                binding_failures += 1
                failures.append(f"{ref}.{pin}: expected {expected_name}, got {actual_name}")
            binding_rows.append((ref, pin, expected_name, actual_name or "-", "PASS" if ok else "FAIL"))

    endpoint_owner = {}
    unknown_endpoints = []
    double_owned = []
    for net, entry in nets.items():
        for ref, pin in nodes(entry):
            endpoint = (ref, pin)
            if endpoint not in pin_index:
                unknown_endpoints.append(f"{net}: {ref}.{pin}")
            owner = endpoint_owner.setdefault(endpoint, net)
            if owner != net:
                double_owned.append(f"{ref}.{pin}: {owner} and {net}")

    no_connect_conflicts = sorted(
        f"{ref}.{pin} also connected to {endpoint_owner[(ref, pin)]}"
        for ref, pin in no_connects
        if (ref, pin) in endpoint_owner
    )
    unknown_no_connects = sorted(
        f"{ref}.{pin}" for ref, pin in no_connects if (ref, pin) not in pin_index
    )

    if unknown_endpoints:
        failures.append("Unknown net endpoints: " + "; ".join(unknown_endpoints))
    if double_owned:
        failures.append("Pins connected to multiple nets: " + "; ".join(double_owned))
    if no_connect_conflicts:
        failures.append("No-connect pins also connected: " + "; ".join(no_connect_conflicts))
    if unknown_no_connects:
        failures.append("Unknown no-connect pins: " + "; ".join(unknown_no_connects))

    type_counts = Counter(chip["type"] for chip in spec["chips"])
    endpoint_count = sum(len(nodes(entry)) for entry in nets.values())
    unowned_pins = sorted(pin_index - set(endpoint_owner) - no_connects)

    status = "NOT READY" if failures else "READY"
    lines = [
        "# Rev A source-model readiness",
        "",
        f"Source: `{board_json}`",
        f"Status: **{status}**",
        "",
        "This report summarizes the generated physical source model before KiCad",
        "schematic/PCB export. It uses the same required ref/net/pin-binding policy",
        "as `check_rev_a_physical.py` and records no-connect coverage explicitly.",
        "",
        "## Summary",
        "",
        f"- Chips/refs: {len(refs)}",
        f"- Nets: {len(nets)}",
        f"- Net endpoints: {endpoint_count}",
        f"- Explicit no-connect pins: {len(no_connects)}",
        f"- Required refs missing: {len(missing_refs)}",
        f"- Required nets missing: {len(missing_nets)}",
        f"- Required pin-binding failures: {binding_failures}",
        f"- Unknown net endpoints: {len(unknown_endpoints)}",
        f"- Multi-net pin conflicts: {len(double_owned)}",
        f"- No-connect conflicts: {len(no_connect_conflicts)}",
        f"- Unknown no-connect pins: {len(unknown_no_connects)}",
        f"- Unowned pins without explicit no-connect: {len(unowned_pins)}",
        "",
        "## Chip Types",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ]
    for typ, count in sorted(type_counts.items()):
        lines.append(table_row([typ, count]))

    lines.extend(
        [
            "",
            "## Required Pin Bindings",
            "",
            "| Ref | Pin | Expected net | Actual net | Status |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in binding_rows:
        lines.append(table_row(row))

    lines.extend(["", "## Explicit No-Connect Pins", ""])
    if no_connects:
        for ref, pin in sorted(no_connects):
            lines.append(f"- `{ref}.{pin}`")
    else:
        lines.append("No explicit no-connect pins.")

    if unowned_pins:
        lines.extend(["", "## Unowned Pins Without No-Connect", ""])
        for ref, pin in unowned_pins:
            lines.append(f"- `{ref}.{pin}`")

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), status


def main():
    board_json = Path(sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.board.json")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "fab/minimal-vga")
    report, status = build_report(board_json)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "source-model-readiness.md"
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
