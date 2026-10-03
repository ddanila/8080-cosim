#!/usr/bin/env python3
"""Generate exact D99 trigger, timing, and remaining-pin constraints."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad" / "juku.board.json"
DATASHEET = ROOT / "ref" / "datasheets" / "sn74ls123-ti.pdf"
PINOUT = ROOT / "ref" / "datasheets" / "k155ag3-pinout.txt"
D94_IMAGE = ROOT / "ref" / "physical-proms" / "validated" / "d94_092.raw.bin"
REPORT = ROOT / "docs" / "d99-reconstruction-constraints.md"

DATASHEET_SHA256 = "abe37431fa9098d0230544c83e4490cc3e788f6be92ef23e99124047f2b59707"
D94_SHA256 = "bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0"

EXPECTED_PIN_NETS = {
    "1": "GND",
    "2": "FDC_HLD_TO_D100",
    "3": "GND",
    "4": "D99_Q1N_BOUNDARY",
    "5": "D99_Q2_BOUNDARY",
    "6": "D99_C2_TIMING",
    "7": "D99_RC2_TIMING",
    "8": "GND",
    "9": "D94_D1_D99_A2N",
    "10": "D99_B2_SHEET1_BOUNDARY",
    "11": "FDC_MOTOR_EN",
    "12": "D99_Q2N_BOUNDARY",
    "13": "D99_Q1_NC",
    "14": "D99_C1_TIMING",
    "15": "D99_RC1_TIMING",
    "16": "P5V",
}

PIN_ROLES = {
    "1": "1A_N / GND",
    "2": "1B / E12 2-3 selects HLD; physical bridge pending",
    "3": "1CLR_N / GND",
    "4": "1Q_N / constant-high boundary",
    "5": "2Q boundary",
    "6": "2Cext / C17−",
    "7": "2Rext/Cext / C17+ / R97",
    "8": "GND",
    "9": "2A_N / D94 D1",
    "10": "2B / sheet-1 boundary",
    "11": "2CLR_N / MOTOR EN",
    "12": "2Q_N boundary",
    "13": "1Q / constant-low NC",
    "14": "1Cext / C18−",
    "15": "1Rext/Cext / C18+ / R103",
    "16": "+5 V",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def chip(board: dict, ref: str) -> dict:
    for item in board["chips"]:
        if item.get("ref") == ref:
            return item
    raise SystemExit(f"missing chip {ref}")


def net_for_pin(board: dict, ref: str, pin: str) -> str | None:
    for name, net in board["nets"].items():
        if [ref, pin] in net.get("nodes", []):
            return name
    return None


def nodes(board: dict, name: str) -> set[tuple[str, str]]:
    return {tuple(node) for node in board["nets"].get(name, {}).get("nodes", [])}


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def main() -> int:
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    image = D94_IMAGE.read_bytes()
    pinout = read(PINOUT)
    devices = read(ROOT / "hdl" / "devices.v")
    tb = read(ROOT / "hdl" / "sim" / "ag3_oneshot_tb.v")

    pin_nets = {pin: net_for_pin(board, "D99", pin) for pin in EXPECTED_PIN_NETS}
    pin_map_ok = pin_nets == EXPECTED_PIN_NETS
    singleton_boundaries_ok = (
        nodes(board, "D99_Q1N_BOUNDARY") == {("D99", "4"), ("D93", "23")}
        and nodes(board, "D99_B2_SHEET1_BOUNDARY") == {("D99", "10"), ("D96", "13")}
    )
    closed_nodes_ok = (
        nodes(board, "D94_D1_D99_A2N") == {("D94", "2"), ("D99", "9"), ("R89", "1"), ("D96", "11")}
        and nodes(board, "D99_Q1_NC") == {("D99", "13")}
        and nodes(board, "D99_Q2N_BOUNDARY") == {("D99", "12"), ("D100", "9")}
        and nodes(board, "D99_Q2_BOUNDARY") == {("D99", "5"), ("D100", "7")}
        and nodes(board, "FDC_HLD_TO_D100") == {("D93", "28"), ("D100", "3"), ("D99", "2")}
        and nodes(board, "FDC_MOTOR_EN") == {("D26", "16"), ("D99", "11")}
        and nodes(board, "D99_C2_TIMING") == {("D99", "6"), ("C17", "2")}
        and nodes(board, "D99_RC2_TIMING") == {("D99", "7"), ("C17", "1"), ("R97", "1")}
        and nodes(board, "D99_C1_TIMING") == {("D99", "14"), ("C18", "2")}
        and nodes(board, "D99_RC1_TIMING") == {("D99", "15"), ("C18", "1"), ("R103", "1")}
    )
    fitted_values_ok = all(
        chip(board, ref).get("value") == value
        for ref, value in {"C17": "120 мкФ", "C18": "47 мкФ", "R97": "47к", "R103": "47к"}.items()
    )
    artifacts_ok = (
        sha256(DATASHEET) == DATASHEET_SHA256
        and sha256(D94_IMAGE) == D94_SHA256
        and len(image) == 32
    )
    pinout_ok = all(
        marker in pinout
        for marker in (
            "3   1CLR_N",
            "9   2A_N",
            "Because /CLR is physically grounded",
            "D94 D1 is open collector",
        )
    )
    hdl_ok = all(
        marker in devices
        for marker in (
            "module ag3_oneshot",
            "always @(negedge a2_n or posedge b2 or posedge clr2_n)",
            "assign q_n = ~q1_r;",
            "assign q2_n = ~q2_r;",
        )
    ) and all(
        marker in tb
        for marker in (
            "clear terminates pulse",
            "clear release trigger",
            "AG3-ONESHOT: PASS",
        )
    )

    d94_d1_ok = True
    for address, raw in enumerate(image):
        a3 = (address >> 3) & 1
        a2 = (address >> 2) & 1
        asserted = not bool(raw & 0x02)
        d94_d1_ok &= asserted == bool(a3 ^ a2)

    r_ohm = 47_000.0
    c1_f = 47e-6
    c2_f = 120e-6
    pulse1_s = 0.45 * r_ohm * c1_f
    pulse2_s = 0.45 * r_ohm * c2_f
    inhibit1_s = 0.22 * (47e6) * 1e-9
    inhibit2_s = 0.22 * (120e6) * 1e-9
    timing_math_ok = (
        abs(pulse1_s - 0.99405) < 1e-9
        and abs(pulse2_s - 2.538) < 1e-9
        and abs(inhibit1_s - 0.01034) < 1e-9
        and abs(inhibit2_s - 0.0264) < 1e-9
    )

    checks = [
        ("TI SN74LS123 PDF and validated D94 image hashes match", artifacts_ok),
        ("D99 all-pin board mapping matches the measured/source model", pin_map_ok),
        ("D99 B2 joins D96 clear; Q1_N joins D93 HLT separately from READY", singleton_boundaries_ok),
        ("D94 D1, both RC networks, and section-1 Q NC preserve exact endpoints", closed_nodes_ok),
        ("C17/C18/R97/R103 modeled values match source nominals", fitted_values_ok),
        ("Local D99 pinout records the exact clear/trigger contract", pinout_ok),
        ("AG3 HDL/test contains selected trigger, clear, and complement markers", hdl_ok),
        ("Physical D94 D1 is asserted exactly when A3 xor A2", d94_d1_ok),
        ("Nominal RC formula arithmetic matches expected results", timing_math_ok),
    ]
    passed = all(ok for _, ok in checks)
    status = "D99 TRIGGER/TIMING LOGIC CONSTRAINED / SIX SIGNAL PINS MEASUREMENT-GATED" if passed else "D99 CONSTRAINT REPORT FAILED"

    lines = [
        "# D99 trigger and timing reconstruction constraints",
        "",
        f"Status: **{status}**",
        "",
        "D99 is the target-board К155АГ3 / SN74123-compatible dual retriggerable",
        "monostable. Exact-revision sheet evidence closes both RC networks and the",
        "local trigger pins; this report converts those facts into digital and",
        "timing constraints without assigning the remote sheet-1 sources.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_d99_reconstruction_constraints.py",
        "python3 kicad/check_d99_source_paths.py",
        "sync/ag3_check.sh",
        "```",
        "",
        "The generator checks artifact hashes, JSON pin/net/value invariants, selected",
        "pinout and HDL/test text markers, all 32 D94 image rows, and nominal RC",
        "arithmetic. It does not execute the HDL test or measure installed timing.",
        "Run `sync/ag3_check.sh` separately for the device simulation.", "",
        "## Evidence checks",
        "",
        "| Check | Result |",
        "| --- | --- |",
    ]
    lines.extend(table_row([name, "PASS" if ok else "FAIL"]) for name, ok in checks)
    lines.extend(
        [
            "",
            "## Exact pin disposition",
            "",
            "| Pin | Device/board role | Board net | State |",
            "| ---: | --- | --- | --- |",
        ]
    )
    measure_pins = {"2", "4", "5", "10", "11", "12"}
    for pin in sorted(EXPECTED_PIN_NETS, key=int):
        state = "MEASURE" if pin in measure_pins else "CLOSED"
        lines.append(table_row([pin, PIN_ROLES[pin], f"`{pin_nets[pin]}`", state]))

    lines.extend(
        [
            "",
            "## Section 1 is functionally constant",
            "",
            "D99.3 `/CLR1` is physically grounded. The TI overriding-clear row",
            "therefore fixes Q1/pin13 low and `/Q1`/pin4 high regardless of A1, B1,",
            "or the R103/C18 network. Pin13 is drawing-closed NC; pin4",
            "is source-joined to D93.23/HLT and is a constant-high",
            "driver rather than a pulse source.",
            "",
            "| /CLR1 | A1_N | B1 | Q1 pin13 | /Q1 pin4 |",
            "| ---: | --- | --- | ---: | ---: |",
            "| 0 | don't care | don't care | 0 | 1 |",
            "",
            "This rules out D99 section 1 as the active raw-read conditioner and",
            "gives a direct powered-probe expectation for pin4. Original-board",
            "D99.4-to-D93.23 continuity remains unmeasured.",
            "",
            "## Section 2 access trigger",
            "",
            "D99.9 `2A_N` is owner-closed to open-collector D94 D1 with R89=6.2 kΩ",
            "to +5 V. Exhaustive inspection of all 32 physical `.092` rows gives",
            "`D1_active = A3 xor A2`, independent of A4 and BA1:BA0.",
            "",
            "| Qualified /WR A3 | IORD A2 | D94 D1 / D99 A2_N | Cycle meaning when selected |",
            "| ---: | ---: | --- | --- |",
            "| 0 | 0 | released high | neither valid direction |",
            "| 0 | 1 | asserted low | write |",
            "| 1 | 0 | asserted low | read |",
            "| 1 | 1 | released high | neither valid direction |",
            "",
            "With the still-unknown B2/pin10 and MOTOR EN `/CLR2`/pin11 both high, entry into",
            "either selected read or write state makes A2_N fall and triggers Q2 high",
            "with Q2_N low. B2 rising while A2_N is already low, or `/CLR2` rising",
            "while A2_N is low and B2 high, also triggers/retriggers exactly as the",
            "datasheet specifies. B2 low or `/CLR2` low prevents the D94 edge from",
            "starting a pulse. D94's shared enable must also be asserted; a disabled",
            "PROM releases D1 through R89.",
            "Exact sheet 3 joins B2/pin10 to D96.13 `/CLR2`, so this same",
            "unread sheet-1 conductor can both inhibit D99 section 2 and clear",
            "D96 section 2 when low. Its actual source and timing remain unproved.",
            "Overlapping sheet-3 detail frames close D99.11 `/CLR2` to the",
            "MOTOR EN continuation from D26.16. Q2/pin5 instead feeds",
            "D100 A7/pin7, whose B7 output drives -MOTOR ON. Original-board",
            "continuity and the actual motor timing remain unmeasured.",
            "",
            "## RC timing predictions",
            "",
            "Using the model/datasheet typical `tW ≈ 0.45RC` and the datasheet",
            "retrigger exclusion `0.22*Cext(pF) ns`:",
            "",
            "| Section | Source-nominal network | Nominal pulse | Early-retrigger inhibit | Functional state |",
            "| --- | --- | ---: | ---: | --- |",
            f"| 1 | R103 47 kΩ / C18 47 µF | {pulse1_s:.5f} s | {inhibit1_s * 1e3:.2f} ms | held clear; pulse suppressed |",
            f"| 2 | R97 47 kΩ / C17 120 µF | {pulse2_s:.3f} s | {inhibit2_s * 1e3:.1f} ms | conditional access pulse |",
            "",
            "The generator verifies model values, not installed resistance or capacitance.",
            "These are nominal behavioral predictions. Electrolytic tolerance, leakage,",
            "device threshold, temperature, and the actual B2/clear waveforms require",
            "powered measurement before hardware release.",
            "",
            "## Minimal closure sequence",
            "",
            "1. With D99 removed, identify the remote endpoints of pins 2, 4, 5,",
            "   10, and 12. Locate E12 posts and its installed bridge; drawing",
            "   selects 2-3 and offers Q2/pin5 on post 1. Pin10/B2 is already",
            "   source-joined to D96.13; identify",
            "   their common sheet-1 source. Confirm D99.11 continuity to D26.16.",
            "   Full sheet 3 draws Q1_N/pin4 on the rail above the distinct",
            "   D94.14-D101.7 rail and descends to D93 HLT/pin23.",
            "   Confirm D99.4-D93.23 directly on the original board.",
            "   Confirm Q2/pin5 to D100.7",
            "   and Q2_N/pin12 to D100.9 separately.",
            "2. Powered but current-limited, confirm pin4 remains high while pin13",
            "   remains low; any pulse on pin4 contradicts the grounded-clear model.",
            "3. Capture D94.2/A2_N, B2, `/CLR2`, Q2, and Q2_N together during both",
            "   selected FDC reads and writes. A falling A2_N can trigger only with",
            "   B2 and `/CLR2` high.",
            "4. Measure the section-2 pulse and retrigger interval. Treat 2.538 s and",
            "   26.4 ms as nominal targets, not pass/fail production limits.",
            "",
            "## Reconstruction boundary",
            "",
            "Derived constraints: section-1 constant outputs, the D94-D1 access equation,",
            "source-nominal RC timing, and conditional trigger behavior.",
            "Still physical: D99.4-to-D93.23 continuity, B2/pin10 source,",
            "original-board MOTOR EN continuity to `/CLR2`/pin11, Q2/pin5 to",
            "D100.7, Q2_N/pin12 to D100.9, and",
            "the installed analog timing waveform.",
        ]
    )

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
