#!/usr/bin/env python3
"""Generate the FDC physical-handoff wiring report."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
LOCAL_PACKAGE_REPORT = ROOT / "docs" / "photo-registration" / "local-packages" / "report.json"
REPORT = ROOT / "docs" / "fdc-hardware-handoff.md"
D93_DRIVE_PINS = {
    "15": "STEP", "16": "DIRC", "17": "EARLY", "18": "LATE",
    "22": "TEST", "23": "HLT", "25": "RG", "26": "RCLK",
    "27": "RAW_READ", "28": "HLD", "29": "TG43", "30": "WG",
    "31": "WDATA", "32": "READY", "33": "WF_VFOE", "34": "TR00",
    "35": "INDEX", "36": "WPRT", "40": "VDD_12V",
}
D93_POWER_PINS = {"1": "NC_BACK_BIAS", "20": "VSS_GND", "21": "VCC_5V", "40": "VDD_12V"}


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
    if not all(d93.get("pins", {}).get(pin) == role for pin, role in D93_DRIVE_PINS.items()):
        failures.append("D93 full FD1793 drive-interface pin contract is absent or incorrect")
    if not all(d93.get("pins", {}).get(pin) == role for pin, role in D93_POWER_PINS.items()):
        failures.append("D93 full FD1793 power/back-bias pin contract is absent or incorrect")
    if not has_node(board, "GND", "D93", "20") or not has_node(board, "P5V", "D93", "21"):
        failures.append("D93 traced ground or +5 V supply is absent")
    if ["D93", "1"] not in board.get("no_connects", []):
        failures.append("D93 internal back-bias pin 1 is not explicitly NC")
    if d100.get("type") != "BUF8287":
        failures.append("D100 is not typed as BUF8287")
    if d100.get("pins", {}).get("10") != "VSS_GND" or d100.get("pins", {}).get("20") != "VCC_5V":
        failures.append("D100 power-pin contract is absent or incorrect")
    if not has_node(board, "GND", "D100", "10") or not has_node(board, "P5V", "D100", "20"):
        failures.append("D100 traced ground or +5 V supply is absent")
    if d10.get("type") != "PIC8259":
        failures.append("D10 is not typed as PIC8259")
    if d10.get("pins", {}).get("14") != "VSS_GND" or d10.get("pins", {}).get("28") != "VCC_5V":
        failures.append("D10 power-pin contract is absent or incorrect")
    if not has_node(board, "GND", "D10", "14") or not has_node(board, "P5V", "D10", "28"):
        failures.append("D10 traced ground or +5 V supply is absent")
    if d9.get("type") != "IO_DEC138":
        failures.append("D9 is not typed as IO_DEC138")

    d10_component_fits = [
        item for item in local_report.get("fits", [])
        if item.get("refdes") == "D10" and item.get("side") == "component"
    ]
    d10_photo_fit_ok = (
        len(d10_component_fits) == 1
        and d10_component_fits[0].get("image", "").endswith("PXL_20260710_200415237.jpg")
        and d10_component_fits[0].get("model") == "affine"
        and max((check.get("error_px", 999) for check in d10_component_fits[0].get("checks", [])), default=999) <= 8
    )
    if not d10_photo_fit_ok:
        failures.append("D10 КР580ВН59 component-side package fit is absent or invalid")
    d10_component_pins = d10_component_fits[0].get("projected_pins", {}) if d10_component_fits else {}

    d93_component_fits = [
        item for item in local_report.get("fits", [])
        if item.get("refdes") == "D93" and item.get("side") == "component"
    ]
    d93_solder_fits = [
        item for item in local_report.get("fits", [])
        if item.get("refdes") == "D93" and item.get("side") == "solder"
    ]
    d93_solder_pins = d93_solder_fits[0].get("projected_pins", {}) if d93_solder_fits else {}
    d93_socket_fits_ok = (
        len(d93_component_fits) == 1
        and d93_component_fits[0].get("image", "").endswith("PXL_20260710_202708344.jpg")
        and d93_component_fits[0].get("model") == "affine"
        and max((check.get("error_px", 999) for check in d93_component_fits[0].get("checks", [])), default=999) <= 8
        and len(d93_solder_fits) == 1
        and d93_solder_fits[0].get("image", "").endswith("PXL_20260710_200506061.jpg")
        and d93_solder_fits[0].get("model") == "similarity_reflected"
        and max((check.get("error_px", 999) for check in d93_solder_fits[0].get("checks", [])), default=999) <= 8
        and d93_solder_pins.get("1", [0, 0])[0] > d93_solder_pins.get("40", [9999, 0])[0] + 200
        and d93_solder_pins.get("20", [0, 0])[0] > d93_solder_pins.get("21", [9999, 0])[0] + 200
        and d93_solder_pins.get("1", [0, 9999])[1] < d93_solder_pins.get("20", [0, 0])[1]
        and d93_solder_pins.get("40", [0, 9999])[1] < d93_solder_pins.get("21", [0, 0])[1]
    )
    if not d93_socket_fits_ok:
        failures.append("D93 two-sided socket package fits are absent or invalid")
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
            "D10.12/.13/.15/.20/.21/.22",
            "MISSING" if any(
                not any(has_node(board, name, "D10", pin) for name in board["nets"])
                for pin in ("12", "13", "15", "20", "21", "22")
            ) else "WIRED",
            "8259 CAS0-2 and IR2-IR4 dispositions",
            "standard КР580ВН59 contract and affine package fit are proved; SP/EN pin16 is separately source-proved high, while these destinations or intentional NC states are not",
        ),
        (
            "D93.15-.18/.22/.23/.25-.36",
            "MISSING" if any(
                not any(has_node(board, name, "D93", pin) for name in board["nets"])
                for pin in D93_DRIVE_PINS if pin != "40"
            ) else "WIRED",
            "step/precompensation, separator, head-load, drive status, and write interface",
            "primary FD179X-01 contract and two-sided socket fits are proved; target-board support circuit remains untraced",
        ),
        (
            "D93.40 `VDD_12V`",
            "MISSING" if not any(has_node(board, name, "D93", "40") for name in board["nets"]) else "WIRED",
            "+12 V controller supply continuity",
            "primary datasheet requires +12 V; corrected two-sided fits identify pin 40; generated geometry ranks D14.8 and D32.8 as the closest proved P12V meter anchors, but continuity remains unproved",
        ),
        (
            "D93.19 `MR_N`",
            "MISSING" if not any(has_node(board, n, "D93", "19") for n in board["nets"]) else "WIRED",
            "master reset source",
            "photo with the physical КР1818ВГ93 temporarily removed from its socket plus solder fit localizes the pad/departure; source remains unproved",
        ),
        (
            "D93.24 `CLK`",
            "MISSING" if not any(has_node(board, n, "D93", "24") for n in board["nets"]) else "WIRED",
            "1 MHz FDC clock rail",
            "corrected D93 fit identifies pin24 and local westbound copper; D106 Q3 is a functional /16 candidate, but its package body and rail-obscured solder end prevent a proved connection or upstream clock source",
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
        "- Primary pin source: `ref/wd1772-vg93/fd179x-01-datasheet.pdf`",
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
            "The D10 affine fit independently localizes the КР580ВН59 interrupt-input",
            "contacts at the other end of the modeled DRQ/INTRQ nets.",
            "",
            "| Signal | D93 pin | D93 solder coordinate | Remote component coordinate | Photograph result |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for signal, pin, remote, remote_pin in (
        ("`FDC_DDEN`", "37", "D26.13 / D6.15", None),
        ("`FDC_DRQ`", "38", "D10.19", "19"),
        ("`FDC_INTRQ`", "39", "D10.18", "18"),
    ):
        point = d93_solder_pins.get(pin)
        coordinate = f"`({point[0]:.3f}, {point[1]:.3f}) px`" if point else "MISSING"
        if point is None:
            failures.append(f"D93 solder fit lacks pin {pin}")
        remote_point = d10_component_pins.get(remote_pin) if remote_pin else None
        remote_coordinate = (
            f"`D10.{remote_pin} ({remote_point[0]:.3f}, {remote_point[1]:.3f}) px`"
            if remote_point else "not locally fitted"
        )
        if remote_pin and remote_point is None:
            failures.append(f"D10 component fit lacks pin {remote_pin}")
        lines.append(table_row([
            signal,
            pin,
            coordinate,
            remote_coordinate,
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
            "  D100.11. Disposition D10 CAS0-2 and IR2-IR4 as connected or intentional",
            "  NCs; SP/EN pin16 is already source-proved and modeled at +5 V.",
            "- Trace every restored D93 drive-interface pin through D28/D95-D99/",
            "  D101/D102/D106, and prove D93.40 to `P12V`; start with the nearest",
            "  proved anchors D14.8/D32.8, then confirm against A60.1 or X8.3.",
            "  Pin 40 is a power-safety",
            "  blocker, not an optional functional refinement.",
            "  The existing photographs have been exhausted for this path: they prove",
            "  local copper but not an unbroken connection to a known +12 V node.",
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
