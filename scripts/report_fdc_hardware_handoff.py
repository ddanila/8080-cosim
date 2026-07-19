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
BUS_POLARITY_REPORT = ROOT / "docs" / "fdc-bus-polarity.md"
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
    "kp12-component-R92-2": ("R92", "2", "2564.000", "1314.000", "FDC_DDEN"),
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
    if (
        not BUS_POLARITY_REPORT.is_file()
        or "Status: **FIRMWARE PROFILES PROVED / PHYSICAL D100 ATTRIBUTION RETIRED / TARGET EPROM DUMPS PENDING**"
        not in BUS_POLARITY_REPORT.read_text(encoding="utf-8")
    ):
        failures.append("firmware-profile/direct-D93-bus audit is absent or stale")
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
    d96_toggle_closed = (
        {"D96.2", "D96.6"}
        == {f"{ref}.{pin}" for ref, pin in net(board, "D96_TOGGLE_FEEDBACK").get("nodes", [])}
        and all(has_node(board, "WREQ_N", "D96", pin) for pin in ("1", "4"))
        and all(["D96", pin] in board.get("no_connects", []) for pin in ("9", "10", "11", "12", "13"))
    )
    if not d96_toggle_closed:
        failures.append("sheet-3 D96 read-clock toggle wiring is absent")
    exact_revision_nc = {
        ("D28", pin) for pin in ("10", "11", "12", "13")
    } | {("D97", "13"), ("D98", "9"), ("D98", "10"), ("D102", "4")}
    actual_nc = {tuple(item) for item in board.get("no_connects", [])}
    if not exact_revision_nc <= actual_nc:
        failures.append("sheet-3 D28/D97/D98/D102 unused-pin dispositions are absent")
    if not d99_section1_excluded:
        failures.append("D99 section-1 grounded-clear/test-landing constraint is absent")
    rclk_closed = (
        has_node(board, "SEP_D106_Q3", "D106", "7")
        and has_node(board, "SEP_D106_Q3", "D28", "9")
        and has_node(board, "SEP_D28_CLK", "D28", "8")
        and has_node(board, "SEP_D28_CLK", "D96", "3")
        and has_node(board, "FDC_RCLK", "D96", "5")
        and has_node(board, "FDC_RCLK", "D93", "26")
    )
    if not rclk_closed:
        failures.append("factory-proved D106-D28-D96-D93 recovered-clock chain is absent")
    d106_closed = (
        {"D106.1", "D106.5", "D106.9", "D106.10", "D106.15", "R78.1"}
        == {f"{ref}.{pin}" for ref, pin in net(board, "D106_PRESET_HIGH").get("nodes", [])}
        and has_node(board, "P5V", "R78", "2")
        and has_node(board, "FDC_SEPARATOR_CLOCK", "D106", "4")
        and has_node(board, "FDC_RAW_READ", "D106", "11")
        and has_node(board, "GND", "D106", "14")
        and all(["D106", pin] in board.get("no_connects", []) for pin in ("2", "3", "6", "12", "13"))
    )
    if not d106_closed:
        failures.append("sheet-3 D106 recovery-counter wiring is absent")
    kp12_resistor_closed = (
        has_node(board, "FDC_DDEN", "D95", "14")
        and has_node(board, "FDC_DDEN", "R92", "2")
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
    if (
        not has_node(board, "GND", "D93", "20")
        or not has_node(board, "P5V", "D93", "21")
        or not has_node(board, "P12V", "D93", "40")
    ):
        failures.append("D93 measured ground, +5 V, or +12 V supply is absent")
    if (
        ["D94", "5"] not in board.get("no_connects", [])
        or not has_node(board, "D93_1_OPEN_STUB", "D93", "1")
    ):
        failures.append("D94.5 no-connect / D93.1 open-stub correction is absent")
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
        d93_dal = str(7 + bit)
        db_ok = has_node(board, db_name, "D93", d93_dal)
        if not db_ok:
            failures.append(f"{db_name} lacks D93.{d93_dal}")
        rows.append(
            [
                f"`{db_name}`",
                status(db_ok),
                f"system DB directly to `D93.{d93_dal}`",
                "factory `.009` sheet 1 + WD1793 datasheet",
            ]
        )

    control_checks = [
        (
            "`FDC_RE_N` / `FDC_CS_N` / `FDC_WE_N`",
            "D94 D2/D3 to D93 RE/WE with R88/R87 pull-ups; D94 enable pin15 to D93 CS; D94 D1 to D99.9/R89",
            [("FDC_RE_N", "D94", "3"), ("FDC_RE_N", "D93", "4"),
             ("FDC_CS_N", "D94", "15"), ("FDC_CS_N", "D93", "3"),
             ("D94_D1_D99_A2N", "D94", "2"), ("D94_D1_D99_A2N", "D99", "9"),
             ("FDC_WE_N", "D94", "4"), ("FDC_WE_N", "D93", "2")],
            False,
            "direct owner continuity for all three controls and corrected D1 destination",
        ),
        (
            "D94.5 no-connect / `D93_1_OPEN_STUB`",
            "D94 output D4 is a PCB no-connect; D93.1 owns the short open stub",
            [("D93_1_OPEN_STUB", "D93", "1")],
            False,
            "owner continuity plus full-resolution exposed-socket photograph recheck",
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
            "D10.22 `IR4`",
            endpoint_state(board, "D10", "22"),
            "stale tape-run continuation disposition",
            "exact .009 sheet 1 labels (3) TAPE RUN INT, but replacement FDC sheet 3 has no matching continuation; ekta37 mask 0xDF keeps IR4 masked",
        ),
        (
            "D93.22/.23/.25/.33",
            group_state(board, "D93", ("22", "23", "25", "33")),
            "TEST strap, head-load timing, read-gate, and WF/VFOE separator control",
            "primary FD179X-01 contract and two-sided socket fits localize the four pads; their remote sources remain unproved",
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
            "source-selected 1/2 MHz FDC clock rail",
            "recovered .009 sheet 3 closes D95.7 to D93.24; FM/MFM and 5-inch/8-inch select D40's traced 1/2 MHz divider rails independently of the D106 separator clock",
        ),
        (
            "D100.9/.11 continuation `1`",
            "BOUNDARY",
            "shared drive-output-buffer control source",
            "factory sheet proves pins 9/11 joined; upstream continuation remains untraced",
        ),
    ]

    lines = [
        "# FDC hardware handoff",
        "",
        "Status: **BUS-SIDE GUARDED / OWNER CONTINUITY REQUIRED**",
        "",
        "This generated report narrows the physical floppy-controller handoff to",
        "the exact board points that still need owner or bench evidence. It does",
        "not claim D93 interrupt mapping or the remaining support inputs are",
        "hardware-verified; it separates the",
        "wired bus-side facts from the remaining continuity asks.",
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
        "Chip-removed owner continuity supersedes the mirrored photograph reading:",
        "D94.3/.15/.4 drive D93.4/.3/.2, while D94.2 reaches D99.9/R89.",
        "The old D94.1/.2/.3 photograph rows retain registration value only.",
        "",
        "## Manufacturer Counter/Separator Constraint",
        "",
        "Western Digital's June-1980 application note Figure 11 shows a minimal",
        "FD1791/FD1793 counter/separator made from exactly these logic families:",
        "",
        "| Reference function | Manufacturer device | Juku family match | State |",
        "| --- | --- | --- | --- |",
        table_row(["raw-read pulse conditioner", "74123", "D97/D99/D102 К155АГ3", "D97/D102 source-closed; D99 section 1 excluded and section 2 unidentified"]),
        table_row(["recovery counter", "74LS193", "D106 К555ИЕ7", "package family matched"]),
        table_row(["read-clock toggle", "74LS74", "D96 КМ555ТМ2", "sheet-3 toggle source-closed; section 2 unused"]),
        "",
        "The manufacturer topology was useful as a search constraint, but the",
        "recovered Juku sheet is now authoritative for the actual wiring.",
        "",
        "D96.8 (/Q2) reaches a proved isolated component-side test landing, and",
        "sheet 3 omits the rest of section 2. Sheet 3 directly closes section 1",
        "as the active toggle: /Q pin6 feeds D pin2, D28.8 clocks pin3, Q pin5",
        "drives D93.26 RCLK, and WREQ_N drives both asynchronous controls.",
        "Exact-revision sheet 3 also omits both unused D28 inverter sections",
        "(pins 10-13), D98 buffer pair 4 (pins 9/10), D97 Q/pin13, and D102",
        "/Q pin4. They are guarded intentional no-connects rather than continuity",
        "requests. D99.3",
        "(/CLR1) is physically grounded and D99.2 (B1) reaches another isolated",
        "test landing, excluding D99 section 1 as the active raw-read conditioner.",
        "Only D99 and D101 still retain open support-device functional pins.",
        "",
        "The Juku",
        "cluster contains two К555КП12 muxes and three К155АГ3 one-shots, whereas",
        "Figure 11 contains no mux and only one half of a single 74123. The owner",
        "photos identify the packages but the recovered Juku sheet, not the generic",
        "reference circuit, closes D95, D106, and D96 completely.",
        "",
        "## Soviet VG93 Circuit Cross-Check",
        "",
        "The original 1986 КР1818ВГ93 paper confirms that this is the actual Soviet",
        "controller device and publishes its pin contract; it does not publish an",
        "external separator schematic. A later technical-history reconstruction",
        "collects period VG93 support circuits. Its Figure 16 shows a second",
        "useful comparison circuit, but its preset and clear straps are not reused",
        "where the primary Juku sheet differs.",
        "",
        "Factory `.009` sheet 1 resolves the apparent crossing: D106.7 reaches",
        "D28.9, D28.8 clocks D96.3, and D96.5 supplies D93.26 RCLK. The older",
        "photograph-only interpretation of a direct D106.7-D93.26 net is retired.",
        "Recovered sheet 3 proves D97.4/D93.27 RAW READ also drives D106.11 /LOAD,",
        "while D106.14 CLR is grounded; the older photo-only D106.14-D93.33 and",
        "hidden-handoff meter candidates are retired. Sheet 3 also proves D93.24 is driven",
        "by D95.7 from the selected 1/2 MHz rail, while D95.9 independently supplies",
        "D106.4 with selected 4/8 MHz; D106 Q3 is not a D93.24 source.",
        "See `ref/schematics/fdc-clock-mux-map.md` and",
        "`ref/schematics/fdc-recovery-counter-map.md` plus",
        "`ref/schematics/fdc-read-clock-toggle-map.md` for the exact tables.",
        "",
        "Recovered `.009` Э3 sheet 3 now closes Juku's write-precompensation chain:",
        "D93.31 drives D97.10; D97 and D102 provide three delay taps to D101.10/.11/.12;",
        "D93.17 EARLY and D93.18 LATE select them on D101.2/.14; D101.9 then drives",
        "D100.6. The associated C16/C19/C20/C22 timing networks and R100/R102/R108",
        "+5 V rail are also closed. Direct target copper remains authoritative for",
        "D101.4-R92-R99, D101.7-D94.14/R88, and physical R86=4.7 kΩ on C19.2/D97.6;",
        "these override the electrical sheet's duplicated R99 reference, conflicting",
        "R86=470 annotation, and tied-D101 drafting. See",
        "`ref/schematics/fdc-write-precomp-map.md` for the exact source hierarchy and",
        "`ref/schematics/fdc-unused-pin-dispositions.md` for the omitted outputs.",
        "",
        "### Superseded separator raw-crop candidates",
        "",
        "All coordinates below are validated local-package fits in",
        "`PXL_20260710_200506061.jpg`. The negative result prevents topology-only",
        "promotion before the primary sheet was recovered. Sheet 3 now resolves",
        "these candidates directly, so the rows are retained only as audit history.",
        "",
        "| Endpoint | Solder coordinate | Candidate peer | Disposition |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(table_row(row) for row in separator_rows)
    lines.extend([
        "",
        "### Superseded D106 static-strap raw-crop candidates",
        "",
        "The same calibrated tile was exhausted for the six remaining IE7 setup",
        "checks. The photograph alone could not close them, but sheet 3 now proves",
        "R78 pulls pins 15/1/10/9 and UP/pin5 high, D95.9 clocks DOWN/pin4,",
        "RAW READ loads pin11, and CLR/pin14 is grounded. These rows are no longer",
        "meter requests.",
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
        "landings. A second target-board angle directly reads R92=`1К3` and",
        "R99=`4К7`, corroborated by the registered July view. These values and",
        "visible links are modeled; the mux select/output paths remain open.",
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
            "- The direct system-data-bus to D93 DAL route, register select, and",
            "  private D94-to-D93 RE/CS/WE controls are present in board JSON and",
            "  guarded by this report. All D94 A0-A4 inputs and the private D93",
            "  controls are owner-mapped; remaining decode boundaries are the upstream",
            "  pin-15 enable source, pull-up identities, D3-D7 destinations, and the",
            "  recorded D29.4/IORD recheck. The `.092` table is physically captured.",
            "- Before real FDC bring-up, continuity-check D93.39/38 to D10.18/19 to",
            "  confirm INTRQ/DRQ ordering, then identify D93.19. D93.24 is now",
            "  source-closed through D95's selected 1/2 MHz clock section. First dump",
            "  D15/D16 and identify its guarded CMA/NOP profile; the recovered direct",
            "  D93 bus means physical D100 is not the profile selector. Separately trace",
            "  shared D100.9/.11 continuation `1`; D100.6's selected write-data input",
            "  is already source-closed through D101.9. See",
            "  `docs/fdc-bus-polarity.md`.",
            "  D10 CAS0-2 are source-proved NC, IR2/IR3 are source-connected, and",
            "  SP/EN pin16 is source-proved at +5 V. Only the stale tape IR4",
            "  continuation remains a Tier-3 continuity boundary; ROM mask 0xDF",
            "  keeps it disabled in the runnable configuration.",
            "- Trace only the still-open D93.22/.23/.25/.33 functions and the D99/D101",
            "  support-device boundaries; D93.15-.18/.26-.32/.34-.36 are source-closed.",
            "  D28/D95-D98/D102/D106 are source-closed; only physical waveform quality",
            "  remains a bring-up check. D93.40 to `P12V` is already owner-confirmed.",
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
