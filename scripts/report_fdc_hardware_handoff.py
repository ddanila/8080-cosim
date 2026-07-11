#!/usr/bin/env python3
"""Generate the FDC physical-handoff wiring report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
LOCAL_PACKAGE_REPORT = ROOT / "docs" / "photo-registration" / "local-packages" / "report.json"
REPORT = ROOT / "docs" / "fdc-hardware-handoff.md"


def load_board() -> dict:
    return json.loads(BOARD_JSON.read_text(encoding="utf-8"))


def chip(board: dict, ref: str) -> dict:
    for item in board["chips"]:
        if item.get("ref") == ref:
            return item
    return {}


def net(board: dict, name: str) -> dict:
    return board["nets"].get(name, {})


def has_node(board: dict, name: str, ref: str, pin: str) -> bool:
    return [ref, pin] in net(board, name).get("nodes", [])


def endpoint_summary(nodes: list[list[str]]) -> str:
    if not nodes:
        return "-"
    rendered = [f"{ref}.{pin}" for ref, pin in nodes]
    if len(rendered) <= 8:
        return ", ".join(rendered)
    return ", ".join(rendered[:8]) + f", ... (+{len(rendered) - 8})"


def table_row(values: list[object]) -> str:
    escaped = [str(value).replace("|", "/") if value not in (None, "") else "-" for value in values]
    return "| " + " | ".join(escaped) + " |"


def status(ok: bool, uncertain: bool = False) -> str:
    if ok and uncertain:
        return "OWNER-VERIFY"
    if ok:
        return "WIRED"
    return "MISSING"


def main() -> int:
    board = load_board()
    local_report = json.loads(LOCAL_PACKAGE_REPORT.read_text(encoding="utf-8"))
    d93 = chip(board, "D93")
    d100 = chip(board, "D100")
    d10 = chip(board, "D10")
    d9 = chip(board, "D9")

    failures: list[str] = []
    if d93.get("type") != "VG93_FDC":
        failures.append("D93 is not typed as VG93_FDC")
    if d100.get("type") != "BUF8287":
        failures.append("D100 is not typed as BUF8287")
    if d10.get("type") != "PIC8259":
        failures.append("D10 is not typed as PIC8259")
    if d9.get("type") != "IO_DEC138":
        failures.append("D9 is not typed as IO_DEC138")

    d93_component_fits = [
        item for item in local_report.get("fits", [])
        if item.get("refdes") == "D93" and item.get("side") == "component"
    ]
    d93_solder_fits = [
        item for item in local_report.get("fits", [])
        if item.get("refdes") == "D93" and item.get("side") == "solder"
    ]
    d93_socket_fits_ok = (
        len(d93_component_fits) == 1
        and d93_component_fits[0].get("image", "").endswith("PXL_20260710_202708344.jpg")
        and d93_component_fits[0].get("model") == "similarity"
        and max((check.get("error_px", 999) for check in d93_component_fits[0].get("checks", [])), default=999) <= 8
        and len(d93_solder_fits) == 1
        and d93_solder_fits[0].get("image", "").endswith("PXL_20260710_200506061.jpg")
        and d93_solder_fits[0].get("model") == "similarity_reflected"
        and max((check.get("error_px", 999) for check in d93_solder_fits[0].get("checks", [])), default=999) <= 8
    )
    if not d93_socket_fits_ok:
        failures.append("D93 two-sided socket package fits are absent or invalid")
    d93_solder_pins = d93_solder_fits[0].get("projected_pins", {}) if d93_solder_fits else {}

    rows: list[list[object]] = []

    for bit in range(8):
        db_name = f"DB{bit}"
        dal_name = f"FDC_DAL{bit}"
        d100_a = str(bit + 1)
        d100_b = str(19 - bit)
        d93_dal = str(7 + bit)
        db_ok = has_node(board, db_name, "D100", d100_a)
        dal_ok = has_node(board, dal_name, "D100", d100_b) and has_node(
            board, dal_name, "D93", d93_dal
        )
        if not db_ok:
            failures.append(f"{db_name} lacks D100.{d100_a}")
        if not dal_ok:
            failures.append(f"{dal_name} lacks D100.{d100_b} and D93.{d93_dal}")
        rows.append(
            [
                f"`{db_name}` / `{dal_name}`",
                status(db_ok and dal_ok),
                f"`D100.{d100_a}` <-> system DB; `D100.{d100_b}` <-> `D93.{d93_dal}`",
                "scan + WD1793/8287 datasheets",
            ]
        )

    control_checks = [
        (
            "`FDC_RE_N` / `FDC_CS_N` / `FDC_WE_N`",
            "D94 D0-D2 private controls to D93 RE/CS/WE",
            [("FDC_RE_N", "D94", "1"), ("FDC_RE_N", "D93", "4"),
             ("FDC_CS_N", "D94", "2"), ("FDC_CS_N", "D93", "3"),
             ("FDC_WE_N", "D94", "3"), ("FDC_WE_N", "D93", "2")],
            False,
            "two-sided local fits + continuous component copper",
        ),
        (
            "`BA0` / `BA1`",
            "register select to D93 A0/A1",
            [("BA0", "D93", "5"), ("BA1", "D93", "6")],
            False,
            "scan",
        ),
        (
            "`FDC_DDEN`",
            "density control to D93 DDEN",
            [("FDC_DDEN", "D93", "37"), ("FDC_DDEN", "D26", "13")],
            True,
            "MAME-derived PC4; cross-check on hardware",
        ),
        (
            "`FDC_INTRQ`",
            "D93 INTRQ to PIC IR0",
            [("FDC_INTRQ", "D93", "39"), ("FDC_INTRQ", "D10", "18")],
            True,
            "MAME-era assumption; owner continuity required",
        ),
        (
            "`FDC_DRQ`",
            "D93 DRQ to PIC IR1",
            [("FDC_DRQ", "D93", "38"), ("FDC_DRQ", "D10", "19")],
            True,
            "MAME-era assumption; owner continuity required",
        ),
    ]
    for name, purpose, endpoints, owner_verify, evidence in control_checks:
        ok = all(has_node(board, net_name, ref, pin) for net_name, ref, pin in endpoints)
        if not ok:
            failures.append(f"{name} missing expected endpoint")
        rows.append([name, status(ok, owner_verify), purpose, evidence])

    unresolved = [
        (
            "D93.19 `MR_N`",
            "MISSING" if not any(has_node(board, n, "D93", "19") for n in board["nets"]) else "WIRED",
            "master reset source",
            "photo with ВГ93 removed from its socket plus solder fit localizes the pad/departure; source remains unproved",
        ),
        (
            "D93.24 `CLK`",
            "MISSING" if not any(has_node(board, n, "D93", "24") for n in board["nets"]) else "WIRED",
            "1 MHz FDC clock rail",
            "photo with ВГ93 removed from its socket plus solder fit localizes the pad/fanout; clock source remains unproved",
        ),
        (
            "D100.9 `OE_N`",
            "MISSING" if not any(has_node(board, n, "D100", "9") for n in board["nets"]) else "WIRED",
            "8287 output-enable gating",
            "not netted in board JSON; owner continuity item",
        ),
        (
            "D100.11 `T`",
            "MISSING" if not any(has_node(board, n, "D100", "11") for n in board["nets"]) else "WIRED",
            "8287 direction gating",
            "not netted in board JSON; owner continuity item",
        ),
    ]

    lines = [
        "# FDC hardware handoff",
        "",
        "Status: **BUS-SIDE GUARDED / OWNER CONTINUITY REQUIRED**",
        "",
        "This generated report narrows the physical floppy-controller handoff to",
        "the exact board points that still need owner or bench evidence. It does",
        "not claim D93 interrupt mapping or D100 enable/direction gating are",
        "hardware-verified; it separates the wired bus-side facts from the",
        "remaining continuity asks.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_fdc_hardware_handoff.py",
        "```",
        "",
        "## Source",
        "",
        f"- Board JSON: `{BOARD_JSON.relative_to(ROOT)}`",
        "- D93 package: `КР1818ВГ93` / WD1793-compatible FDC",
        "- D100 package: `КР580ВА87` / Intel 8287-compatible bus transceiver",
        "",
        "## Photograph Applicability",
        "",
        "The July owner-photo batches under `ref/photos/juku-pcb-2/` clearly show a",
        "populated КР1818ВГ93, add an overlapping 3x3 solder-side grid, and include",
        "a later component-side view with the known КР1818ВГ93 temporarily removed",
        "from its socket to expose the footprint copper. The board is therefore",
        "applicable physical evidence for the",
        "FDC handoff. The grids are registered and D94/D93 have package-local fits.",
        "The guarded D93 component fit specifically uses `PXL_20260710_202708344.jpg`,",
        "taken with the known КР1818ВГ93 removed from its socket. It exposes all 40",
        "contacts and the pin-40 end marking. A reflected solder fit then lands on the",
        "actual joints; together they localize MR_N/pin19 and CLK/pin24 without",
        "claiming their far destinations.",
        "Continuous copper promotes the private D94.1/.2/.3 to D93.4/.3/.2 control",
        "nets; no photographed branch supports the former global I/O-rail assumption.",
        "",
        "## Bus-Side Handoff Checks",
        "",
        "| Net / path | Status | Endpoint / purpose | Evidence boundary |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(table_row(row) for row in rows)
    lines.extend(
        [
            "",
            "## D93 Source-Risk Pad Review",
            "",
            "The two-sided package fits make the controller-end pad identity exact.",
            "The available photographs do not show an unbroken path from these pads",
            "to the modeled remote endpoints.",
            "",
            "| Signal | D93 pin | Solder-image coordinate | Photograph result |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for signal, pin, remote in (
        ("`FDC_DDEN`", "37", "D26.13 / D6.15"),
        ("`FDC_DRQ`", "38", "D10.19"),
        ("`FDC_INTRQ`", "39", "D10.18"),
    ):
        point = d93_solder_pins.get(pin)
        coordinate = f"`({point[0]:.3f}, {point[1]:.3f}) px`" if point else "MISSING"
        if point is None:
            failures.append(f"D93 solder fit lacks pin {pin}")
        lines.append(table_row([
            signal,
            pin,
            coordinate,
            f"pad and local copper identified; no photographed unbroken path to {remote}",
        ]))
    lines.extend(
        [
            "",
            "## Remaining Owner Continuity Points",
            "",
            "| Pin | Status | Needed fact | Current boundary |",
            "| --- | --- | --- | --- |",
        ]
    )
    lines.extend(table_row(row) for row in unresolved)

    fdc_nets = {
        name: item
        for name, item in sorted(board["nets"].items())
        if name.startswith("FDC_") or name in {"CS_FDC", "IORD", "IOWR"}
    }
    lines.extend(
        [
            "",
            "## Netted FDC Endpoints",
            "",
            "| Net | Source | Endpoints |",
            "| --- | --- | --- |",
        ]
    )
    for name, item in fdc_nets.items():
        lines.append(table_row([f"`{name}`", item.get("src", "-"), f"`{endpoint_summary(item.get('nodes', []))}`"]))

    lines.extend(
        [
            "",
            "## Disposition",
            "",
            "- The system data bus, D100 B-side, D93 DAL bus, register select, and",
            "  private D94-to-D93 RE/CS/WE controls are present in board JSON and",
            "  guarded by this report. Functional I/O decode into D94 remains blocked",
            "  on pin 15, D3-D7 destinations, and the `.092` truth table.",
            "- Before real FDC bring-up, continuity-check D93.39/38 to D10.18/19 to",
            "  confirm INTRQ/DRQ ordering, then identify D93.19, D93.24, D100.9, and",
            "  D100.11.",
            "- Keep `docs/fdc-readiness.md` as the HDL/media behavior guard; this",
            "  report is only the physical-board handoff checklist.",
            "",
        ]
    )

    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if failures:
        print("Hard wiring failures:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
