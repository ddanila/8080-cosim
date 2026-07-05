#!/usr/bin/env python3
import json
import sys


REQUIRED_REFS = {
    "U1", "U2", "U3", "U4", "U5",
    "U10", "U11", "U12", "U13", "U14", "U15", "U16", "U17",
    "U20", "U21", "U22", "U23", "U24", "U25",
    "U30", "U31", "U40", "U41", "J1", "J3", "J30", "J40", "J90", "J91", "J92",
    "U50", "U51", "R1", "R2", "R3", "R4", "R5", "C50",
    "F1", "D1", "R6", "J93", "R30", "R31",
    "R7", "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15",
    "R16", "R17", "R18", "R19", "R20", "R21", "R22", "R23",
    "D2", "D3", "D4", "D5", "D6", "D7",
    "R24", "R25", "R26", "R27", "R28", "R29",
}

REQUIRED_NETS = {
    "A0", "A15", "D0", "D7",
    "MREQ_N", "IORQ_N", "RD_N", "WR_N", "RFSH_N", "WAIT_N", "RESET_N", "CLK",
    "ROM_CE_N", "MEM_RD_N", "MEM_WR_N", "IO_RD_N", "IO_WR_N", "PPI_CS_N",
    "DRAM_A0", "DRAM_A7", "RAS_N", "CAS_N", "DRAM_WE_N", "REFRESH_TICK",
    "KBD_COL0", "KBD_ROW0_N", "KBD_GS_N",
    "VIDEO_REQ", "VIDEO_ACK", "HSYNC_N", "VSYNC_N", "PIXEL",
    "VGA_R", "VGA_G", "VGA_B", "OSC_OE_N", "VCC", "GND",
    "VCC_RAW", "PWR_OK", "USB_CC1", "USB_CC2",
    "KBD_COL0_DRV", "KBD_COL7_DRV",
    "LED_PWR_A", "LED_PWR_OK_A", "LED_CLK_A",
    "LED_RESET_A", "LED_M1_A", "LED_RFSH_A",
}

REQUIRED_PIN_BINDINGS = {
    "U1": {
        "6": "CLK", "11": "VCC", "19": "MREQ_N", "20": "IORQ_N",
        "21": "RD_N", "22": "WR_N", "24": "WAIT_N", "26": "RESET_N",
        "28": "RFSH_N", "29": "GND", "30": "A0", "40": "A10",
    },
    "U2": {
        "10": "A0", "14": "GND", "20": "CE_N", "22": "OE_N",
        "27": "WE_N", "28": "VCC",
    },
    "U10": {
        "2": "DIN", "3": "WE_N", "4": "RAS_N", "8": "VCC",
        "14": "DOUT", "15": "CAS_N", "16": "GND",
    },
    "U30": {
        "5": "RD_N", "6": "CS_N", "7": "GND", "8": "A1",
        "9": "A0", "26": "VCC", "34": "D0", "35": "RESET", "36": "WR_N",
    },
    "U50": {"1": "OE_N", "7": "GND", "8": "CLK", "14": "VCC"},
    "U51": {"1": "GND", "2": "RESET_N", "3": "VCC"},
}


def nodes(entry):
    return entry["nodes"] if isinstance(entry, dict) else entry


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "spinoffs/minimal-vga/kicad/rev-a-physical.board.json"
    spec = json.load(open(path))
    refs = {chip["ref"] for chip in spec["chips"]}
    nets = spec["nets"]

    errors = []
    missing_refs = sorted(REQUIRED_REFS - refs)
    if missing_refs:
        errors.append(f"missing refs: {', '.join(missing_refs)}")

    missing_nets = sorted(REQUIRED_NETS - set(nets))
    if missing_nets:
        errors.append(f"missing nets: {', '.join(missing_nets)}")

    chips = {chip["ref"]: chip for chip in spec["chips"]}
    for ref, expected in REQUIRED_PIN_BINDINGS.items():
        pins = chips.get(ref, {}).get("pins", {})
        for pin, name in expected.items():
            if pins.get(pin) != name:
                errors.append(f"{ref}.{pin}: expected {name}, got {pins.get(pin)}")

    pin_index = {(chip["ref"], pin) for chip in spec["chips"] for pin in chip["pins"]}
    endpoint_owner = {}
    for net, entry in nets.items():
        for ref, pin in nodes(entry):
            if (ref, pin) not in pin_index:
                errors.append(f"{net}: unknown endpoint {ref}.{pin}")
            owner = endpoint_owner.setdefault((ref, pin), net)
            if owner != net:
                errors.append(f"{ref}.{pin}: connected to both {owner} and {net}")

    for ref in [f"U{n}" for n in range(10, 18)]:
        for net in ("RAS_N", "CAS_N", "DRAM_WE_N", "VCC", "GND"):
            pin = {
                "RAS_N": "4",
                "CAS_N": "15",
                "DRAM_WE_N": "3",
                "VCC": "8",
                "GND": "16",
            }[net]
            if [ref, pin] not in nodes(nets[net]):
                errors.append(f"{ref}: not connected to {net}")

    decouplers = [ref for ref in refs if ref.startswith("C") and ref != "C50"]
    if len(decouplers) < 25:
        errors.append(f"expected at least 25 decouplers, got {len(decouplers)}")
    for ref in decouplers:
        if [ref, "1"] not in nodes(nets["VCC"]):
            errors.append(f"{ref}: not connected to VCC")
        if [ref, "2"] not in nodes(nets["GND"]):
            errors.append(f"{ref}: not connected to GND")

    pixel_nodes = nodes(nets["PIXEL"])
    for pin in ("1", "2", "3"):
        if ["J40", pin] in pixel_nodes:
            errors.append(f"J40.{pin}: RGB output must go through a resistor, not directly to PIXEL")
    for ref, net, pin in (("R1", "VGA_R", "1"), ("R2", "VGA_G", "2"), ("R3", "VGA_B", "3")):
        if [ref, "1"] not in pixel_nodes:
            errors.append(f"{ref}.1: not connected to PIXEL")
        if [ref, "2"] not in nodes(nets[net]):
            errors.append(f"{ref}.2: not connected to {net}")
        if ["J40", pin] not in nodes(nets[net]):
            errors.append(f"J40.{pin}: not connected to {net}")

    if ["J1", "1"] in nodes(nets["VCC"]):
        errors.append("J1.1: ATX +5V must enter VCC through F1, not directly")
    for net, endpoint in (
        ("VCC_RAW", ["J1", "1"]),
        ("VCC_RAW", ["F1", "1"]),
        ("VCC", ["F1", "2"]),
        ("VCC", ["D1", "1"]),
        ("GND", ["D1", "2"]),
        ("VCC_RAW", ["J1", "1"]),
        ("GND", ["J1", "2"]),
        ("VCC_RAW", ["J3", "A9"]),
        ("VCC_RAW", ["J3", "B9"]),
        ("GND", ["J3", "A12"]),
        ("GND", ["J3", "B12"]),
        ("GND", ["J3", "S1"]),
        ("USB_CC1", ["J3", "A5"]),
        ("USB_CC2", ["J3", "B5"]),
        ("USB_CC1", ["R30", "1"]),
        ("USB_CC2", ["R31", "1"]),
        ("GND", ["R30", "2"]),
        ("GND", ["R31", "2"]),
        ("VCC", ["R6", "1"]),
        ("PWR_OK", ["R6", "2"]),
        ("VCC", ["J93", "1"]),
        ("GND", ["J93", "2"]),
        ("PWR_OK", ["J93", "3"]),
        ("VCC_RAW", ["J93", "4"]),
    ):
        if endpoint not in nodes(nets[net]):
            errors.append(f"{endpoint[0]}.{endpoint[1]}: not connected to {net}")

    ppi_col_pins = ["4", "3", "2", "1", "40", "39", "38", "37"]
    for i, ppi_pin in enumerate(ppi_col_pins):
        drv = f"KBD_COL{i}_DRV"
        col = f"KBD_COL{i}"
        ref = f"R{16 + i}"
        if ["U30", ppi_pin] not in nodes(nets[drv]):
            errors.append(f"U30.{ppi_pin}: not connected to {drv}")
        if [ref, "1"] not in nodes(nets[drv]):
            errors.append(f"{ref}.1: not connected to {drv}")
        if [ref, "2"] not in nodes(nets[col]):
            errors.append(f"{ref}.2: not connected to {col}")
        if ["U30", ppi_pin] in nodes(nets[col]):
            errors.append(f"U30.{ppi_pin}: keyboard column must pass through {ref}")

    for i in range(8):
        row = f"KBD_ROW{i}_N"
        ref = f"R{7 + i}"
        if [ref, "1"] not in nodes(nets["VCC"]):
            errors.append(f"{ref}.1: keyboard row pullup not connected to VCC")
        if [ref, "2"] not in nodes(nets[row]):
            errors.append(f"{ref}.2: keyboard row pullup not connected to {row}")
    if ["R15", "1"] not in nodes(nets["KBD_EN_N"]):
        errors.append("R15.1: not connected to KBD_EN_N")
    if ["R15", "2"] not in nodes(nets["GND"]):
        errors.append("R15.2: not connected to GND")

    diagnostic_leds = (
        ("D2", "R24", "VCC", "LED_PWR_A", "GND", None),
        ("D3", "R25", "PWR_OK", "LED_PWR_OK_A", "GND", "GND"),
        ("D4", "R26", "CLK", "LED_CLK_A", "GND", "GND"),
        ("D5", "R27", "RESET_N", "LED_RESET_A", "GND", "GND"),
        ("D6", "R28", "VCC", "LED_M1_A", "M1_N", None),
        ("D7", "R29", "VCC", "LED_RFSH_A", "RFSH_N", None),
    )
    for led, resistor, source, led_anode, led_cathode, _ in diagnostic_leds:
        if [resistor, "1"] not in nodes(nets[source]):
            errors.append(f"{resistor}.1: diagnostic LED source not connected to {source}")
        if [resistor, "2"] not in nodes(nets[led_anode]):
            errors.append(f"{resistor}.2: not connected to {led_anode}")
        if [led, "2"] not in nodes(nets[led_anode]):
            errors.append(f"{led}.2: not connected to {led_anode}")
        if [led, "1"] not in nodes(nets[led_cathode]):
            errors.append(f"{led}.1: not connected to {led_cathode}")

    if errors:
        print("Rev A physical spec check: FAIL")
        for error in errors:
            print(f"  {error}")
        return 1

    print(f"Rev A physical spec check: PASS ({len(refs)} refs, {len(nets)} nets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
