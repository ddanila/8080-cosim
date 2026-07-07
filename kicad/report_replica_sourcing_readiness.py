#!/usr/bin/env python3
import csv
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = ROOT / "docs" / "replica-dual-config-bom.csv"
DEFAULT_MD = ROOT / "docs" / "replica-sourcing-readiness.md"


LONG_LEAD_TYPES = {
    "CPU8080",
    "SYS8238",
    "USART8251",
    "PPI8255",
    "PIT8253",
    "PIC8259",
    "BUF8286",
    "BUF8287",
    "VABUS",
    "IR82",
    "VG93_FDC",
    "RU5",
    "DEC_PROM",
    "RE3_PROM",
    "RE3_PROM_113",
    "EPROM8K",
    "EXPANSION_CONN",
    "SERIAL_CONN",
    "POWER_CONN",
    "KBD_CONN",
    "PAR_CONN",
}


BUY_EARLY_TYPES = {
    "CPU8080",
    "SYS8238",
    "USART8251",
    "PPI8255",
    "PIT8253",
    "PIC8259",
    "BUF8286",
    "BUF8287",
    "VABUS",
    "IR82",
    "VG93_FDC",
    "RU5",
    "XTAL",
}


PROGRAM_TYPES = {"DEC_PROM", "RE3_PROM", "RE3_PROM_113", "EPROM8K"}


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value not in (None, "") else "-" for value in values) + " |"


def load_rows(path):
    with path.open(newline="") as fp:
        return list(csv.DictReader(fp))


def int_field(row, name):
    return int(row.get(name) or 0)


def filtered(rows, predicate):
    return [row for row in rows if predicate(row)]


def sort_key(row):
    return (row["action"], row["type"], row.get("value", ""), row.get("refs", ""))


def build_report(rows):
    action_counts = Counter()
    action_positions = Counter()
    for row in rows:
        action_counts[row["action"]] += 1
        action_positions[row["action"]] += int_field(row, "populate_now")

    buy_early = filtered(
        rows,
        lambda row: row["type"] in BUY_EARLY_TYPES and int_field(row, "populate_now") > 0,
    )
    long_lead = filtered(
        rows,
        lambda row: row["type"] in LONG_LEAD_TYPES and int_field(row, "populate_now") > 0,
    )
    programming = filtered(
        rows,
        lambda row: row["type"] in PROGRAM_TYPES and int_field(row, "populate_now") > 0,
    )
    review_blocked = filtered(
        rows,
        lambda row: row["action"] in {"mechanical-review", "circuit-review"} and int_field(row, "populate_now") > 0,
    )

    programming_blocked = bool(programming)
    review_blockers = bool(review_blocked)
    status = "SOURCING READY / PROGRAMMING BLOCKED" if programming_blocked else "SOURCING READY"

    lines = [
        "# Replica sourcing readiness",
        "",
        f"Status: **{status}**",
        "",
        "Source: `docs/replica-dual-config-bom.csv`.",
        "",
        "This report turns the WS-E dual-config BOM into an ordering and acceptance",
        "gate. It is not a vendor cart: prices, live stock, and seller trust must be",
        "checked at order time. It defines what can be sourced early, what needs",
        "bench acceptance, and what must wait for PROM/media truth or mechanical",
        "review before being treated as build-ready.",
        "",
        "## Summary",
        "",
        f"- BOM lines: {len(rows)}",
        f"- Populate-now component positions: {sum(int_field(row, 'populate_now') for row in rows)}",
        f"- Long-lead/source-early lines: {len(long_lead)}",
        f"- Programming/dump-gated lines: {len(programming)}",
        f"- Mechanical/circuit-review lines: {len(review_blocked)}",
        f"- Order posture: {'do not treat as a complete kit until the gated rows below are closed' if programming_blocked or review_blockers else 'functional kit rows are source-ready'}",
        "",
        "## Action Totals",
        "",
        "| Action | BOM lines | Populate-now positions |",
        "| --- | ---: | ---: |",
    ]
    for action in sorted(action_counts):
        lines.append(table_row([action, action_counts[action], action_positions[action]]))

    lines.extend(
        [
            "",
            "## Buy Early / Acceptance-Test First",
            "",
            "| Type | Authentic part | Functional substitute | Populate now | Refs | Acceptance note |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    acceptance_notes = {
        "CPU8080": "Run in a known-good 8080 tester or minimal NOP/ROM-fetch jig before seating.",
        "SYS8238": "Verify pin-compatible 8228/8238 behavior; check MEMR/IO strobes in a socketed bring-up.",
        "USART8251": "Socket; loopback test after clock/reset are proven.",
        "PPI8255": "Socket; verify keyboard/Port C mode bits against twin during bring-up.",
        "PIT8253": "Socket; verify programmed divisors and video-sync outputs.",
        "PIC8259": "Socket; verify frame interrupt vectoring before FDC IRQs.",
        "BUF8286": "Continuity/orientation check; verify no bus fight during first ROM fetch.",
        "BUF8287": "Continuity/orientation check; verify direction/OE before attaching FDC data path.",
        "VABUS": "Continuity/orientation check on expansion bus transceivers.",
        "IR82": "Verify latch polarity around DRAM write-data path.",
        "VG93_FDC": "Prefer socket; WD1793 drop-in acceptable for functional config.",
        "RU5": "Buy spares; run 4164/565RU5 tester before installation.",
        "XTAL": "Verify 16 MHz oscillation and load-cap fit before debugging timing.",
    }
    for row in sorted(buy_early, key=sort_key):
        lines.append(
            table_row(
                [
                    row["type"],
                    row["authentic_part"],
                    row["functional_substitute"],
                    row["populate_now"],
                    row["populated_refs"] or row["refs"],
                    acceptance_notes.get(row["type"], "Socket and verify in staged bring-up."),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Programming / Dump Gate",
            "",
            "These rows are required for a complete functional kit, but their contents",
            "must come from the Baltijets programming disk, an owner dump, or the",
            "boot-validated reconstructed tables in that preference order.",
            "",
            "| Type | Authentic part | Populate now | Refs | Gate |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    gate_notes = {
        "DEC_PROM": "Need D2/D6 RT4 maps or accepted reconstructed decode tables before programming.",
        "EPROM8K": "Program D15/D16 for the .009 build; leave D17-D22 empty unless authentic-completeness build is chosen.",
        "RE3_PROM": "Need D8 RE3 dump/table or accepted reconstructed table.",
        "RE3_PROM_113": "Need D94/FDC-era RE3 dump/table or accepted reconstructed table.",
    }
    for row in sorted(programming, key=sort_key):
        lines.append(
            table_row(
                [
                    row["type"],
                    row["authentic_part"],
                    row["populate_now"],
                    row["populated_refs"] or row["refs"],
                    gate_notes.get(row["type"], "Program only after content provenance is decided."),
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Review Before Buying Blind",
            "",
            "These rows should not be converted directly into a vendor cart. They need",
            "exact mechanical fit, interface-voltage, circuit-role, or value confirmation",
            "against drawings/board photos before ordering final quantities.",
            "",
            "| Action | Type | Authentic part | Populate now | Refs | Note |",
            "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in sorted(review_blocked, key=sort_key):
        lines.append(
            table_row(
                [
                    row["action"],
                    row["type"] + (f" {row['value']}" if row.get("value") else ""),
                    row["authentic_part"],
                    row["populate_now"],
                    row["populated_refs"] or row["refs"],
                    row["functional_substitute"],
                ]
            )
        )

    lines.extend(
        [
            "",
            "## Minimum Acceptance Ladder",
            "",
            "1. Inventory received parts against `docs/replica-dual-config-bom.csv` by type and refdes group.",
            "2. Test DRAM and CPU-family spares before installation; reject intermittent or hot-running parts.",
            "3. Program or dump PROM/EPROM rows only after provenance is recorded; keep checksums with the programmer log.",
            "4. Install sockets first, then passives/connectors, then power-rail checks with no ICs seated.",
            "5. Carry `docs/replica-bringup-verification-points.md` into the private build record and close its source-risk nets as they are reached.",
            "6. Seat only the clock/reset/ROM-fetch minimum set first; compare bus behavior against `sync/boot_check.sh` and cosim traces.",
            "7. Add RAM, video, keyboard, and FDC in staged groups, never as one full-board power-on.",
            "",
            "## Related Gates",
            "",
            "- `docs/replica-dual-config-bom.md` / `.csv`: source-of-truth BOM split.",
            "- `docs/replica-parts-inventory-template.md`: received-parts, acceptance-test, and PROM/EPROM programming evidence template.",
            "- `docs/replica-bringup-verification-points.md`: source-risk net checklist to carry into assembly and staged bring-up.",
            "- `docs/prom-dump-procedure.md`: PROM/EPROM dump and programming provenance.",
            "- `docs/community-prom-media-request.md`: owner/community request for PROMs and `JUKU-1` media.",
            "- `docs/replica-fab-drc-disposition.md`: fabrication review posture before board order.",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MD
    rows = load_rows(csv_path)
    report = build_report(rows)
    out_path.write_text(report)
    print(report)
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
