#!/usr/bin/env python3
"""Generate the FDC physical-handoff wiring report."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
LOCAL_PACKAGE_REPORT = ROOT / "docs" / "photo-registration" / "local-packages" / "report.json"
PHOTO_ENDPOINTS = ROOT / "ref" / "photos" / "juku-pcb-2" / "endpoints.csv"
REPORT = ROOT / "docs" / "fdc-hardware-handoff.md"
APPLICATION_NOTE = ROOT / "ref" / "wd1772-vg93" / "fd179x-application-notes-jun1980.pdf"
D93_DRIVE_PINS = {
    "15": "STEP", "16": "DIRC", "17": "EARLY", "18": "LATE",
    "22": "TEST", "23": "HLT", "25": "RG", "26": "RCLK",
    "27": "RAW_READ", "28": "HLD", "29": "TG43", "30": "WG",
    "31": "WDATA", "32": "READY", "33": "WF_VFOE", "34": "TR00",
    "35": "INDEX", "36": "WPRT", "40": "VDD_12V",
}
D93_POWER_PINS = {"1": "NC_BACK_BIAS", "20": "VSS_GND", "21": "VCC_5V", "40": "VDD_12V"}
SEPARATOR_PROBES = {
    ("D106", "11"): ("1016.633", "2084.087", "D93.27"),
    ("D93", "27"): ("1555.311", "2091.306", "D106.11"),
    ("D106", "14"): ("1017.546", "1946.087", "D93.33"),
    ("D93", "33"): ("1557.244", "1809.072", "D106.14"),
}
D106_STATIC_PROBES = {
    "15": ("1017.851", "1900.087", "HIGH", "P5V"),
    "1": ("1156.155", "1855.000", "HIGH", "P5V"),
    "5": ("1154.937", "2039.000", "HIGH", "P5V"),
    "10": ("1016.329", "2130.087", "LOW", "GND"),
    "9": ("1016.024", "2176.087", "LOW", "GND"),
    "4": ("1155.242", "1993.000", "RECOVERY CLOCK", "CLOCK SOURCE"),
}
KP12_RESISTOR_ENDPOINTS = {
    "kp12-component-R92-1": ("R92", "1", "2341.000", "1317.000", "D101_D02_R92_R99"),
    "kp12-component-R92-2": ("R92", "2", "2564.000", "1314.000", "D95_A0_R92"),
    "kp12-component-R99-1": ("R99", "1", "2064.000", "1370.000", "GND"),
    "kp12-component-R99-2": ("R99", "2", "2287.000", "1367.000", "D101_D02_R92_R99"),
}


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


def endpoint_state(board: dict, ref: str, pin: str) -> str:
    if [ref, pin] in board.get("no_connects", []):
        return "NC"
    for record in board["nets"].values():
        nodes = record.get("nodes", [])
        if [ref, pin] in nodes:
            return "CONNECTED" if len(nodes) > 1 else "BOUNDARY"
    return "MISSING"


def group_state(board: dict, ref: str, pins: tuple[str, ...]) -> str:
    states = {endpoint_state(board, ref, pin) for pin in pins}
    if "MISSING" in states:
        return "MISSING"
    if "BOUNDARY" in states:
        return "BOUNDARY"
    if "NC" in states:
        return "DISPOSITIONED"
    return "CONNECTED"


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


def separator_probe_observations() -> tuple[list[list[str]], bool]:
    """Guard the reviewed negative same-layer evidence for two separator candidates."""
    matched: dict[tuple[str, str], dict[str, str]] = {}
    with PHOTO_ENDPOINTS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row.get("refdes", ""), row.get("pin", ""))
            if key in SEPARATOR_PROBES and row.get("endpoint_id", "").startswith("seed-solder-"):
                matched[key] = row
    rows: list[list[str]] = []
    ok = set(matched) == set(SEPARATOR_PROBES)
    for key, (x, y, peer) in SEPARATOR_PROBES.items():
        row = matched.get(key, {})
        guarded = (
            row.get("image") == "ref/photos/juku-pcb-2/PXL_20260710_200506061.jpg"
            and row.get("x_px") == x
            and row.get("y_px") == y
            and row.get("confidence") == "local-package-fit"
            and row.get("review_state") == "measurement"
            and "uninterrupted same-layer path" in row.get("note", "")
            and peer in row.get("note", "")
        )
        ok &= guarded
        rows.append([
            f"{key[0]}.{key[1]}",
            f"({row.get('x_px', '-')}, {row.get('y_px', '-')})",
            peer,
            "DIRECT PATH REJECTED / LAYER HANDOFF OPEN" if guarded else "EVIDENCE MISSING",
        ])
    return rows, ok


def d106_static_probe_observations() -> tuple[list[list[str]], bool]:
    """Guard the reviewed photo limits for D106 straps and its clock input."""
    matched: dict[str, dict[str, str]] = {}
    with PHOTO_ENDPOINTS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            pin = row.get("pin", "")
            if (
                row.get("refdes") == "D106"
                and pin in D106_STATIC_PROBES
                and row.get("endpoint_id", "").startswith("seed-solder-")
            ):
                matched[pin] = row
    rows: list[list[str]] = []
    ok = set(matched) == set(D106_STATIC_PROBES)
    for pin, (x, y, expected, anchor) in D106_STATIC_PROBES.items():
        row = matched.get(pin, {})
        note = row.get("note", "")
        rail_obscured = pin in {"9", "10"}
        guarded = (
            row.get("image") == "ref/photos/juku-pcb-2/PXL_20260710_200506061.jpg"
            and row.get("x_px") == x
            and row.get("y_px") == y
            and row.get("confidence") == "local-package-fit"
            and row.get("review_state") == "measurement"
            and anchor in note
            and (("unproved" in note) if not rail_obscured else ("not continuity" in note))
            and (("rail-obscured" in note) if rail_obscured else ("local" in note))
        )
        ok &= guarded
        photo_result = (
            f"RAIL-OBSCURED / {anchor} UNPROVED"
            if rail_obscured
            else f"LOCAL COPPER ONLY / {anchor} UNPROVED"
        )
        rows.append([
            f"D106.{pin}",
            expected,
            f"({row.get('x_px', '-')}, {row.get('y_px', '-')})",
            photo_result if guarded else "EVIDENCE MISSING",
            f"continuity to a known {anchor} anchor",
        ])
    return rows, ok


def kp12_resistor_observations() -> tuple[list[list[str]], bool]:
    """Guard the accepted component-copper evidence for the R92/R99 ladder."""
    matched: dict[str, dict[str, str]] = {}
    with PHOTO_ENDPOINTS.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            endpoint_id = row.get("endpoint_id", "")
            if endpoint_id in KP12_RESISTOR_ENDPOINTS:
                matched[endpoint_id] = row
    rows: list[list[str]] = []
    ok = set(matched) == set(KP12_RESISTOR_ENDPOINTS)
    for endpoint_id, (ref, pin, x, y, candidate_net) in KP12_RESISTOR_ENDPOINTS.items():
        row = matched.get(endpoint_id, {})
        guarded = (
            row.get("image") == "ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg"
            and row.get("refdes") == ref
            and row.get("pin") == pin
            and row.get("x_px") == x
            and row.get("y_px") == y
            and row.get("candidate_net") == candidate_net
            and row.get("confidence") == "registration+unique-hole-snap"
            and row.get("review_state") == "accepted"
            and "uninterrupted copper" in row.get("note", "")
        )
        ok &= guarded
        rows.append([
            f"{ref}.{pin}",
            f"({row.get('x_px', '-')}, {row.get('y_px', '-')})",
            candidate_net,
            "ACCEPTED TARGET COPPER" if guarded else "EVIDENCE MISSING",
        ])
    return rows, ok


def main() -> int:
    board = load_board()
    local_report = json.loads(LOCAL_PACKAGE_REPORT.read_text(encoding="utf-8"))
    d93 = chip(board, "D93")
    d100 = chip(board, "D100")
    d10 = chip(board, "D10")
    d9 = chip(board, "D9")
    failures: list[str] = []
    separator_rows, separator_probe_guarded = separator_probe_observations()
    if not separator_probe_guarded:
        failures.append("D106/D93 separator negative photo evidence is missing or stale")
    static_probe_rows, static_probe_guarded = d106_static_probe_observations()
    if not static_probe_guarded:
        failures.append("D106 static-strap/clock photo evidence is missing or stale")
    kp12_rows, kp12_probe_guarded = kp12_resistor_observations()
    if not kp12_probe_guarded:
        failures.append("KP12 R92/R99 component-copper evidence is missing or stale")

    reference_family_checks = {
        "74193 counter": chip(board, "D106").get("type") == "IE7_CTR",
        "74LS74 flip-flop": chip(board, "D96").get("type") == "TM2_DFF",
        "74123 one-shot family": all(
            chip(board, ref).get("type") == "AG3_ONESHOT"
            for ref in ("D97", "D99", "D102")
        ),
    }
    if not APPLICATION_NOTE.is_file():
        failures.append("FD179X June-1980 application note is absent")
    if not all(reference_family_checks.values()):
        failures.append("Juku FDC cluster no longer matches the Figure-11 logic families")
    d96_section2_excluded = (
        has_node(board, "D96_Q2_N_TEST_LANDING", "D96", "8")
        and endpoint_state(board, "D96", "8") == "BOUNDARY"
    )
    d99_section1_excluded = (
        has_node(board, "GND", "D99", "3")
        and has_node(board, "D99_B_TEST_LANDING", "D99", "2")
        and endpoint_state(board, "D99", "2") == "BOUNDARY"
    )
    if not d96_section2_excluded:
        failures.append("D96 section-2 isolated-/Q constraint is absent")
    if not d99_section1_excluded:
        failures.append("D99 section-1 grounded-clear/test-landing constraint is absent")
    rclk_closed = has_node(board, "FDC_RCLK", "D106", "7") and has_node(
        board, "FDC_RCLK", "D93", "26"
    )
    if not rclk_closed:
        failures.append("photo-proved D106.7-to-D93.26 recovered-clock net is absent")
    kp12_resistor_closed = (
        has_node(board, "D95_A0_R92", "D95", "14")
        and has_node(board, "D95_A0_R92", "R92", "2")
        and has_node(board, "D101_D02_R92_R99", "D101", "4")
        and has_node(board, "D101_D02_R92_R99", "R92", "1")
        and has_node(board, "D101_D02_R92_R99", "R99", "2")
        and has_node(board, "GND", "R99", "1")
        and has_node(board, "GND", "D101", "8")
    )
    if not kp12_resistor_closed:
        failures.append("photo-proved KP12 R92/R99 ladder nets are absent")

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
            group_state(board, "D10", ("12", "13", "15", "20", "21", "22")),
            "8259 CAS0-2 and IR2-IR4 dispositions",
            "standard КР580ВН59 contract and affine package fit are proved; CAS0-2 pins12/13/15 are explicit NCs, IR2/IR3 connect directly to D11 RXRDY/TXRDY, and only IR4 remains an off-sheet boundary",
        ),
        (
            "D93.15-.18/.22/.23/.25-.36",
            group_state(board, "D93", tuple(pin for pin in D93_DRIVE_PINS if pin != "40")),
            "step/precompensation, separator, head-load, drive status, and write interface",
            "primary FD179X-01 contract and two-sided socket fits are proved; target-board support circuit remains untraced",
        ),
        (
            "D93.40 `VDD_12V`",
            endpoint_state(board, "D93", "40"),
            "+12 V controller supply continuity",
            "primary datasheet requires +12 V; corrected two-sided fits identify pin 40; generated geometry ranks D14.8 and D32.8 as the closest proved P12V meter anchors, but continuity remains unproved",
        ),
        (
            "D93.19 `MR_N`",
            endpoint_state(board, "D93", "19"),
            "master reset source",
            "photo with the physical КР1818ВГ93 temporarily removed from its socket plus solder fit localizes the pad/departure; source remains unproved",
        ),
        (
            "D93.24 `CLK`",
            endpoint_state(board, "D93", "24"),
            "1 MHz FDC clock rail",
            "corrected D93 fit identifies pin24 and local westbound copper; both WD and Soviet VG93 references keep this main controller clock separate from the D106 recovered-clock path, but its upstream source remains unproved",
        ),
        (
            "D100.9 `OE_N`",
            endpoint_state(board, "D100", "9"),
            "8287 output-enable gating",
            "singleton D100_OE_BOUNDARY in board JSON; owner continuity item",
        ),
        (
            "D100.11 `T`",
            endpoint_state(board, "D100", "11"),
            "8287 direction gating",
            "singleton D100_T_BOUNDARY in board JSON; owner continuity item",
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
        "- Primary application source: `ref/wd1772-vg93/fd179x-application-notes-jun1980.pdf`",
        "- Primary Soviet device source: Kovalenko et al., `БИС контроллера КР1818ВГ93 для накопителя на гибком диске`, МПСС 1986 No. 3, pp. 3-8",
        "- Historical circuit comparison: `https://atmturbo.nedopc.com/articles/kontroller_diskovoda_shemotehnika_210224.html`",
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
        "## Manufacturer Counter/Separator Constraint",
        "",
        "Western Digital's June-1980 application note Figure 11 shows a minimal",
        "FD1791/FD1793 counter/separator made from exactly these logic families:",
        "",
        "| Reference function | Manufacturer device | Juku family match | State |",
        "| --- | --- | --- | --- |",
        table_row(["raw-read pulse conditioner", "74123", "D97/D99/D102 К155АГ3", "D99 section 1 excluded; remaining section not identified"]),
        table_row(["recovery counter", "74LS193", "D106 К555ИЕ7", "package family matched"]),
        table_row(["read-clock toggle", "74LS74", "D96 КМ555ТМ2", "section 2 excluded; target RCLK copper bypasses D96"]),
        "",
        "The reference topology makes the following continuity checks high-value:",
        "D106.3 (Q0) to D96.3 (CLK), D96.2 (D) to D96.6 (/Q), D96.5 (Q) to",
        "D93.26 (RCLK), and one AG3 /Q output jointly to D93.27 (RAW READ) and",
        "D106.11 (/LOAD). It also suggests checking D106 preset inputs",
        "15/1 high and 10/9 low, CU pin5 high, CD pin4 to the recovery clock,",
        "and CLR pin14 inactive.",
        "",
        "Existing Juku photo constraints narrow, but do not close, that mapping.",
        "D96.8 (/Q2) reaches a proved isolated component-side test landing, so",
        "section 2 cannot supply the reference circuit's required /Q-to-D feedback;",
        "D96 section 1 (pins 2/3/5/6) is the only physically available WD-toggle",
        "section, but the target RCLK closure below proves that Juku did not use it",
        "for that output. D99.3",
        "(/CLR1) is physically grounded and D99.2 (B1) reaches another isolated",
        "test landing, excluding D99 section 1 as the active raw-read conditioner.",
        "The remaining AG3 sections still require continuity identification.",
        "",
        "Except for the separately photo-proved Q3-to-RCLK path below, these are",
        "**reference candidates, not promoted Juku nets**. The Juku",
        "cluster contains two К555КП12 muxes and three К155АГ3 one-shots, whereas",
        "Figure 11 contains no mux and only one half of a single 74123. The owner",
        "photos identify the packages but do not prove the candidate paths end to",
        "end; in particular D106 pins 9/10 are rail-obscured. Continuity or a",
        "Juku-specific electrical sheet remains required before board-JSON changes.",
        "",
        "## Soviet VG93 Circuit Cross-Check",
        "",
        "The original 1986 КР1818ВГ93 paper confirms that this is the actual Soviet",
        "controller device and publishes its pin contract; it does not publish an",
        "external separator schematic. A later technical-history reconstruction",
        "collects period VG93 support circuits. Its Figure 16 shows a second",
        "high-value candidate that uses a К155ИЕ7-class counter without a ТМ2",
        "toggle: raw read loads the counter at pin 11, a 4 MHz recovery clock enters",
        "pin 4, pin 5 is held high, and Q3/pin 7 supplies VG93 RCLK/pin 26. The",
        "parallel inputs are strapped 15/1 high and 10/9 low, while pin 14 is",
        "controlled by WF/VFOE/pin 33.",
        "",
        "The target board now chooses this branch: corrected independent package",
        "fits place D106.7 and D93.26 on one uninterrupted solder-side trace in",
        "`PXL_20260710_200506061.jpg`. This excludes the Western Figure-11",
        "D96-toggle output as Juku's RCLK source, though D96 may have another role.",
        "Calibrated review of the same raw solder tile finds no uninterrupted",
        "same-layer path for D106.11-D93.27 or D106.14-D93.33. This rejects a",
        "direct visible merge, not cross-layer continuity: both pairs remain meter",
        "tests for hidden handoffs. In both references",
        "D93.24 is the controller's separate",
        "main clock input; D106 Q3 must not be treated as a candidate for D93.24.",
        "",
        "The same historical comparison also shows a К555КП12-class write",
        "precompensation selector: VG93 pins 18/17 reach mux select pins 2/14, mux",
        "pin 1 is enabled low, and mux output pin 7 proceeds through an inverter to",
        "drive write data. Juku's D95 and D101 match the mux family, but the source",
        "of their delay taps and the output inverter are not identified. Target-board",
        "component copper now closes D95.14-R92.2, D101.4-R92.1-R99.2, and",
        "R99.1-D101.8/GND, bounding part of the passive ladder without proving the",
        "historical VG93 select assignment. Check the remaining select candidates",
        "against D93.18/.17 and both pin-7 destinations. If either approaches",
        "D28.5/.6, continuity must override the legacy-sheet NC assumption; the",
        "current photographs do not prove that reuse.",
        "",
        "D106.7-D93.26 and the three passive-ladder links above are promoted from",
        "target-board copper. The remaining Soviet-reference paths are guarded",
        "candidates, not Juku continuity.",
        "",
        "### Separator candidate raw-crop disposition",
        "",
        "All coordinates below are validated local-package fits in",
        "`PXL_20260710_200506061.jpg`. The negative result prevents topology-only",
        "promotion while preserving the exact cross-layer continuity request.",
        "",
        "| Endpoint | Solder coordinate | Candidate peer | Disposition |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(table_row(row) for row in separator_rows)
    lines.extend([
        "",
        "### D106 static straps and clock raw-crop disposition",
        "",
        "The same calibrated tile was exhausted for the six remaining IE7 setup",
        "checks. Pins 9/10 project beneath crossing rail metal, so apparent overlap",
        "is not continuity. Pins 15/1/5 and pin 4 have identifiable local joints or",
        "departures, but none remains visibly unbroken to a known power or clock",
        "anchor. These are therefore bounded meter probes, not inferred straps.",
        "",
        "| Endpoint | Reference expectation | Solder coordinate | Photograph result | Required proof |",
        "| --- | --- | --- | --- | --- |",
    ])
    lines.extend(table_row(row) for row in static_probe_rows)
    lines.extend([
        "",
        "### KP12 passive-network component-copper disposition",
        "",
        "The calibrated component tile fixes all four factory-identified R92/R99",
        "landings. These visible links are modeled; resistor values and the mux",
        "select/output paths remain open.",
        "",
        "| Endpoint | Component coordinate | Modeled net | Disposition |",
        "| --- | --- | --- | --- |",
    ])
    lines.extend(table_row(row) for row in kp12_rows)
    lines.extend([
        "",
        "## Bus-Side Handoff Checks",
        "",
        "| Net / path | Status | Endpoint / purpose | Evidence boundary |",
        "| --- | --- | --- | --- |",
    ])
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
        ("`FDC_DDEN`", "37", "D26.13 (D6.15 explicitly excluded by continuity)", None),
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
            "  on A0-A4/pins 10-14, pin 15, and D3-D7 destinations; the `.092`",
            "  truth table itself is physically captured.",
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
