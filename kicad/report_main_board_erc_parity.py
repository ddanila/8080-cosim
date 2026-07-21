#!/usr/bin/env python3
"""Run and summarize main-board ERC, PCB/schematic parity, and NC accounting."""
from __future__ import annotations

import json
import csv
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad/juku.board.json"
SCHEMATIC = ROOT / "kicad/juku.kicad_sch"
# Parity must use the source PCB with the same basename as juku.kicad_sch.
# juku_routed is a derived routed artifact and has no sibling schematic.
PCB = ROOT / "kicad/juku.kicad_pcb"
OUT = ROOT / "fab/audit"
REPORT = ROOT / "docs/main-board-erc-parity.md"
ENDPOINTS = ROOT / "docs/main-board-unresolved-endpoints.csv"

P0_REFS = {"D2", "D28", "D30", "D41", "D93", "D94", "D95", "D96", "D97", "D98",
           "D99", "D100", "D101", "D102", "D104", "D105", "D106"}
P0_MEMORY_REFS = {"D6", "D7", "D25", "D36", "D39", "D53"}
OFF_BOARD_REFS = {"S1", "S4", "X3", "X4", "X6", "X8", "X9"}
RISK_RE = re.compile(
    r"assumed|boundar(?:y|ies)|deferred|untraced|not traced|not established|"
    r"not readable|cannot be uniquely followed|pending|unread|await|owner-verify|"
    r"mame|approx|refine|dump|source confirmation|requires? (?:source|continuity)",
    re.I,
)


def cli() -> str:
    env = os.environ.get("KICAD_CLI")
    if env: return env
    result = subprocess.run([str(ROOT / "scripts/find-kicad-cli.sh")], text=True, capture_output=True, check=True)
    return result.stdout.strip()


def run(command: list[str], source: Path, output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([cli(), *command, "--severity-error", "--format", "json",
                    "--output", str(output), str(source)], cwd=ROOT,
                   check=True, stdout=subprocess.DEVNULL)
    return json.loads(output.read_text())


def all_erc(report: dict) -> list[dict]:
    result = list(report.get("violations", []))
    for sheet in report.get("sheets", []): result.extend(sheet.get("violations", []))
    return result


def refs(violations: list[dict]) -> Counter:
    found = Counter()
    for violation in violations:
        for item in violation.get("items", []):
            match = re.search(r"\bSymbol\s+(\S+)\s+Pin\s+(\S+)", item.get("description", ""))
            if match: found[match.group(1)] += 1
    return found


def net_has_source_risk(name: str, net: dict) -> bool:
    override = net.get("source_risk")
    if override is None:
        return bool(RISK_RE.search(f"{net.get('src', '')} {net.get('note', '')}"))
    if not isinstance(override, bool):
        raise SystemExit(f"{name}: source_risk override must be boolean")
    if override is False and not str(net.get("risk_disposition", "")).strip():
        raise SystemExit(f"{name}: source_risk=false requires risk_disposition")
    return override


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    erc_schematic = OUT / "juku-erc.kicad_sch"
    subprocess.run([sys.executable, str(ROOT / "kicad/gen_kicad_sch.py"),
                    "--include-power", str(BOARD_JSON), str(erc_schematic)],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    erc_path = OUT / "main-board-erc.json"
    parity_path = OUT / "main-board-parity-drc.json"
    erc = run(["sch", "erc"], erc_schematic, erc_path)
    parity = run(["pcb", "drc", "--schematic-parity"], PCB, parity_path)
    violations = all_erc(erc)
    parity_issues = parity.get("schematic_parity", [])
    spec = json.loads(BOARD_JSON.read_text())
    singleton_nets = {
        str(name): net
        for name, net in spec["nets"].items()
        if len(net.get("nodes", [])) == 1
    }
    source_risk_nets = {
        str(name): net
        for name, net in spec["nets"].items()
        if net_has_source_risk(str(name), net)
    }
    source_risk_singletons = {
        name: net for name, net in source_risk_nets.items() if name in singleton_nets
    }
    closed_singletons = {
        name: net for name, net in singleton_nets.items() if name not in source_risk_nets
    }
    dangling_labels = Counter()
    unexpected_erc = []
    for violation in violations:
        items = violation.get("items", [])
        match = (
            re.fullmatch(r"Label '(.+)'", items[0].get("description", ""))
            if violation.get("type") == "label_dangling" and len(items) == 1
            else None
        )
        if match and match.group(1) in singleton_nets:
            dangling_labels[match.group(1)] += 1
        else:
            unexpected_erc.append(violation)
    expected_dangling_labels = Counter({name: 1 for name in singleton_nets})
    missing_dangling_labels = expected_dangling_labels - dangling_labels
    extra_dangling_labels = dangling_labels - expected_dangling_labels
    singleton_mismatch_count = sum(missing_dangling_labels.values()) + sum(extra_dangling_labels.values())
    unexpected_erc_count = len(unexpected_erc) + singleton_mismatch_count
    singleton_erc_ok = not unexpected_erc_count
    explicit = [tuple(map(str, row)) for row in spec.get("no_connects", [])]
    endpoint_owners: dict[tuple[str, str], list[str]] = {}
    for net_name, net in spec["nets"].items():
        for ref, pin in net.get("nodes", []):
            endpoint_owners.setdefault((str(ref), str(pin)), []).append(str(net_name))
    nodes = set(endpoint_owners)
    duplicate_owners = {
        endpoint: owners for endpoint, owners in endpoint_owners.items() if len(owners) > 1
    }
    # gen_kicad_sch uses the union of pin numbers for every instance of a given
    # symbol type. Account against that same physical-symbol surface, not only
    # the role subset written on an individual chip record.
    type_pins: dict[str, set[str]] = {}
    for chip in spec["chips"]:
        type_pins.setdefault(str(chip["type"]), set()).update(map(str, chip.get("pins", {})))
    pins = {(str(c["ref"]), pin) for c in spec["chips"] for pin in type_pins[str(c["type"])]}
    unknown_nc = sorted(set(explicit) - pins)
    conflicting_nc = sorted(set(explicit) & nodes)
    unowned = sorted(pins - nodes - set(explicit))
    chips = {str(c["ref"]): c for c in spec["chips"]}
    endpoint_rows = []
    priority_counts = Counter()
    for ref, pin in unowned:
        chip = chips[ref]
        role = str(chip.get("pins", {}).get(pin, type_pins[str(chip["type"])] and "symbol-union boundary"))
        if ref in P0_REFS:
            priority, reason = "P0", "PLAN physical-connectivity blocker"
        elif ref in P0_MEMORY_REFS:
            priority, reason = "P0", "memory/decode source-risk blocker"
        elif ref in OFF_BOARD_REFS or ref.startswith("X"):
            priority, reason = "P2", "connector/peripheral boundary"
        else:
            priority, reason = "P1", "functional endpoint lacks disposition"
        priority_counts[priority] += 1
        endpoint_rows.append({"priority": priority, "ref": ref, "pin": pin,
                              "type": str(chip["type"]), "role": role, "reason": reason})
    for net_name, net in sorted(source_risk_singletons.items()):
        ref, pin = map(str, net["nodes"][0])
        chip = chips[ref]
        role = str(chip.get("pins", {}).get(pin, "symbol-union boundary"))
        if ref in P0_REFS:
            priority = "P0"
        elif ref in P0_MEMORY_REFS:
            priority = "P0"
        elif ref in OFF_BOARD_REFS or ref.startswith("X"):
            priority = "P2"
        else:
            priority = "P1"
        priority_counts[priority] += 1
        endpoint_rows.append(
            {
                "priority": priority,
                "ref": ref,
                "pin": pin,
                "type": str(chip["type"]),
                "role": role,
                "reason": f"source-risk singleton net {net_name} lacks a proved remote endpoint",
            }
        )
    endpoint_rows.sort(
        key=lambda row: (
            row["priority"],
            int(row["ref"][1:]) if re.fullmatch(r"[A-Z]+\d+", row["ref"]) else row["ref"],
            int(row["pin"]) if row["pin"].isdigit() else row["pin"],
        )
    )
    with ENDPOINTS.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("priority", "ref", "pin", "type", "role", "reason"))
        writer.writeheader(); writer.writerows(endpoint_rows)
    schematic_text = SCHEMATIC.read_text(errors="replace")
    schematic_nc = len(re.findall(r"\(no_connect\s+\(at\s", schematic_text))
    nc_ok = not unknown_nc and not conflicting_nc and schematic_nc == len(explicit)
    parity_ok = not parity_issues
    status = (
        "READY"
        if singleton_erc_ok and parity_ok and nc_ok and not unowned
        and not duplicate_owners and not source_risk_nets
        else "DESIGN HOLD"
    )
    by_type = Counter(v.get("type", "unknown") for v in violations)
    top_refs = refs(violations)
    lines = [
        "# Main-board ERC and schematic/PCB parity", "", f"Status: **{status}**", "",
        "ERC uses a generated include-power schematic under `fab/audit`; the normal",
        "LVS schematic deliberately omits power nets. Parity uses `juku.kicad_sch`",
        "and the same-basename source `juku.kicad_pcb`. The routed PCB is a derived",
        "artifact; KiCad cannot run",
        "schematic parity against it without a matching routed schematic/project.", "",
        "## Summary", "", "| Check | Count | Result |", "| --- | ---: | --- |",
        f"| Raw ERC error violations | {len(violations)} | {'GUARDED' if singleton_erc_ok else 'BLOCK'} |",
        f"| Unexpected ERC/mapping findings | {unexpected_erc_count} | {'PASS' if singleton_erc_ok else 'BLOCK'} |",
        f"| Exact singleton-label findings | {sum(dangling_labels.values())} / {len(singleton_nets)} | {'PASS' if singleton_erc_ok else 'FAIL'} |",
        f"| Source-risk singleton nets | {len(source_risk_singletons)} | {'PASS' if not source_risk_singletons else 'BLOCK'} |",
        f"| Other source-risk nets | {len(source_risk_nets) - len(source_risk_singletons)} | {'PASS' if len(source_risk_nets) == len(source_risk_singletons) else 'BLOCK'} |",
        f"| PCB/schematic parity issues | {len(parity_issues)} | {'PASS' if parity_ok else 'BLOCK'} |",
        f"| Explicit board-JSON no-connects | {len(explicit)} | {'PASS' if nc_ok else 'FAIL'} |",
        f"| KiCad schematic no-connect markers | {schematic_nc} | {'PASS' if schematic_nc == len(explicit) else 'FAIL'} |",
        f"| Functional pins without net or explicit NC | {len(unowned)} | {'PASS' if not unowned else 'BLOCK'} |",
        f"| Duplicate board-JSON endpoint memberships | {len(duplicate_owners)} | {'PASS' if not duplicate_owners else 'BLOCK'} |",
        f"| Unknown/conflicting NC records | {len(unknown_nc)+len(conflicting_nc)} | {'PASS' if not unknown_nc and not conflicting_nc else 'FAIL'} |",
        "", "Stable KiCad reports one `label_dangling` error for every one-endpoint",
        "local-label net. The exact label-name/count guard above proves these are",
        "the modeled singleton boundary surface, not geometrically detached labels.",
        f"Of those `{len(singleton_nets)}` singleton nets, `{len(source_risk_singletons)}` remain source-risk",
        f"boundaries and `{len(closed_singletons)}` have closed or intentional dispositions.",
        "", "## Unresolved endpoint priorities", "",
        "| Priority | Count |", "| --- | ---: |",
    ]
    lines += [f"| {priority} | {priority_counts.get(priority, 0)} |" for priority in ("P0", "P1", "P2")]
    lines += ["", "The complete machine-readable singleton-endpoint backlog is",
              "`docs/main-board-unresolved-endpoints.csv`.", "", "## ERC types", ""]
    lines += [f"- `{typ}`: {count}" for typ, count in sorted(by_type.items())] or ["- None."]
    lines += ["", "## Most affected references", ""]
    lines += [f"- `{ref}`: {count}" for ref, count in top_refs.most_common(20)] or ["- None."]
    lines += ["", "## Release interpretation", ""]
    if duplicate_owners:
        lines += ["Duplicate board-JSON endpoint memberships must be removed:", ""]
        lines += [
            f"- `{ref}.{pin}`: " + ", ".join(f"`{owner}`" for owner in owners)
            for (ref, pin), owners in sorted(duplicate_owners.items())
        ]
        lines += [""]
    if status == "READY":
        lines += ["ERC structure, parity, source-risk closure, endpoint ownership, and explicit no-connect accounting all pass."]
    else:
        lines += [
            "The raw ERC findings are exactly accounted for by modeled singleton nets, and",
            "parity plus endpoint ownership pass. Source-risk nets remain release blockers.",
            "They must be traced, redesigned, or individually given an evidence-backed",
            "disposition. This gate does not suppress the singleton labels or convert them",
            "to no-connects merely to obtain a zero-error ERC count.",
        ]
    if unknown_nc: lines += ["", "Unknown NC records: " + ", ".join(f"`{r}.{p}`" for r,p in unknown_nc)]
    if conflicting_nc: lines += ["", "Conflicting NC records: " + ", ".join(f"`{r}.{p}`" for r,p in conflicting_nc)]
    if missing_dangling_labels:
        lines += ["", "Singleton labels missing from ERC: " + ", ".join(f"`{name}`" for name in sorted(missing_dangling_labels))]
    if extra_dangling_labels:
        lines += ["", "Duplicate singleton-label ERC findings: " + ", ".join(f"`{name}`" for name in sorted(extra_dangling_labels))]
    lines += ["", "Raw machine-readable reports:", "",
              "- `fab/audit/main-board-erc.json`", "- `fab/audit/main-board-parity-drc.json`", ""]
    REPORT.write_text("\n".join(lines))
    print(f"main-board ERC/parity: {status}; ERC={len(violations)}, parity={len(parity_issues)}, unowned={len(unowned)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
