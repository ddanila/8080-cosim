#!/usr/bin/env python3
import json
import sys


REQUIRED_REFS = {
    "U1", "U2", "U5",
    "U10", "U11", "U12", "U13", "U14", "U15", "U16", "U17",
    "U20", "U21", "U22", "U23", "U24",
    "U30", "U31", "U40", "U41", "J1", "J3", "J30", "J40", "J90", "J91", "J92",
    "U50", "U51", "R1", "R2", "R3", "R4", "R5", "C50",
    "F1", "D1", "R6", "J93", "R30", "R31",
    "R7", "R8", "R9", "R10", "R11", "R12", "R13", "R14", "R15",
    "R16", "R17", "R18", "R19", "R20", "R21", "R22", "R23",
    "D2", "D3", "D4", "D5", "D6", "D7",
    "R24", "R25", "R26", "R27", "R28", "R29",
    # Phase 3: real decode PROM sockets (Juku D6 РТ4 -> U3, D8 РЕ3 -> U4),
    # PC0/PC1 mode inverter (U6), mode jumper (J94), decode-observability
    # header (J95), PROM output pull-ups, and decoupling.
    "U3", "U4", "U6", "J94", "J95",
    "R32", "R33", "R34", "R35", "R36", "R37", "R38", "R39", "R40", "R41",
    "R42", "R43", "R44", "C26", "C27", "C28",
    # Phase 4: clock-control jumper (J96), high-address+write header (J97),
    # control-bus header (J98) -- the observability design-ins.
    "J96", "J97", "J98",
}

REQUIRED_NETS = {
    "A0", "A15", "D0", "D7",
    "MREQ_N", "IORQ_N", "RD_N", "WR_N", "RFSH_N", "WAIT_N", "RESET_N", "CLK",
    "ROM_CE_N", "MEM_RD_N", "MEM_WR_N", "IO_RD_N", "IO_WR_N", "PPI_CS_N",
    "DECODE_WAIT_N",
    "DRAM_A0", "DRAM_A7", "RAS_N", "CAS_N", "DRAM_WE_N", "REFRESH_TICK",
    "KBD_COL0", "KBD_ROW0_N", "KBD_GS_N",
    "VIDEO_REQ", "VIDEO_ACK", "HSYNC_N", "VSYNC_N", "BLANK_N", "PIX_LOAD_N", "PIXEL",
    "VGA_R", "VGA_G", "VGA_B", "OSC_OE_N", "VCC", "GND",
    "VCC_RAW", "PWR_OK", "USB_CC1", "USB_CC2",
    "KBD_COL0_DRV", "KBD_COL7_DRV",
    "LED_PWR_A", "LED_PWR_OK_A", "LED_CLK_A",
    "LED_RESET_A", "LED_M1_A", "LED_RFSH_A",
    # Phase 3 decode nets: РТ4 decode outputs into the GAL, mode select,
    # inverted Port C mode bits, and the РЕ3 readback byte.
    "MODE_B", "PC0", "PC1", "PC0_N", "PC1_N",
    "DEC_ROM_N", "DEC_RAM_N", "DEC_REV", "DEC_ROE_N", "REV_OUT",
    "RE3_D0", "RE3_D1", "RE3_D2", "RE3_D3", "RE3_D4", "RE3_D5", "RE3_D6", "RE3_D7",
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
    "U5": {
        "12": "GND", "13": "DEC_ROE_N", "14": "ROM_CE_N",
        "15": "RAM_CE_N", "16": "PPI_CS_N", "17": "MEM_RD_N",
        "18": "MEM_WR_N", "19": "IO_RD_N", "20": "IO_WR_N",
        "21": "REV_OUT", "22": "DECODE_WAIT_N", "23": "SPARE_N",
        "24": "VCC",
    },
    # GAL22V10 pin 13 is the twelfth input/OE; only pins 14-23 are output
    # macrocells. U24 uses seven functional outputs plus three registered state
    # bits. U24.18 is the sole WAIT_N driver; U5.22 only feeds U24.13.
    "U24": {
        "1": "CLK", "2": "RESET_N", "3": "RAM_CE_N",
        "4": "MEM_RD_N", "5": "MEM_WR_N", "6": "RFSH_OBS_N",
        "7": "VIDEO_REQ", "8": "REFRESH_Q0", "9": "REFRESH_Q1",
        "10": "REFRESH_Q2", "11": "REFRESH_Q3", "12": "GND",
        "13": "DECODE_WAIT_N", "14": "RAS_N", "15": "CAS_N",
        "16": "DRAM_WE_N", "17": "ADDRMUX_SEL", "18": "CPU_WAIT_N",
        "19": "VIDEO_ACK", "20": "REFRESH_TICK", "21": "STATE0",
        "22": "STATE1", "23": "STATE2", "24": "VCC",
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
    # Real decode PROM sockets (function-label pinout from the vendored
    # datasheets: К556РТ4 82S126-class, К155РЕ3 SN74188-class).
    "U3": {
        "5": "A0", "6": "A1", "7": "A2", "4": "A3", "3": "A4", "2": "A5",
        "1": "A6", "15": "A7", "12": "O1", "11": "O2", "10": "O3", "9": "O4",
        "13": "CE1_N", "14": "CE2_N", "8": "GND", "16": "VCC",
    },
    "U4": {
        "10": "A0", "11": "A1", "12": "A2", "13": "A3", "14": "A4",
        "15": "CE_N", "1": "O1", "9": "O8", "8": "GND", "16": "VCC",
    },
    "U6": {"1": "1A", "2": "1Y", "3": "2A", "4": "2Y", "7": "GND", "14": "VCC"},
}

# Twin contract: the RT4/RE3 socket connectivity must match the addressing the
# verified Verilog twin (hdl/vjuga_juku_top.v) drives -- see decode_prom /
# re3_prom in ../../hdl/devices.v. If this drifts, the board no longer models
# the chip the simulation validates.
DECODE_SOCKET_CONTRACT = [
    # РТ4 (U3) address: a[0..4]=A15,A14,A13,A12,A11 ; a[5]=/PC0 a[6]=/PC1 a[7]=0
    ("A15", ["U3", "5"]), ("A14", ["U3", "6"]), ("A13", ["U3", "7"]),
    ("A12", ["U3", "4"]), ("A11", ["U3", "3"]),
    ("PC0_N", ["U3", "2"]), ("PC1_N", ["U3", "1"]), ("GND", ["U3", "15"]),
    # РТ4 both chip-enables tied active (enabled whenever socketed)
    ("GND", ["U3", "13"]), ("GND", ["U3", "14"]),
    # РТ4 outputs O1..O4 = rom_n/ram_n/rev/roe_n feed the GAL decode inputs
    ("DEC_ROM_N", ["U3", "12"]), ("DEC_RAM_N", ["U3", "11"]),
    ("DEC_REV", ["U3", "10"]), ("DEC_ROE_N", ["U3", "9"]),
    ("DEC_ROM_N", ["U5", "9"]), ("DEC_RAM_N", ["U5", "10"]),
    ("DEC_REV", ["U5", "11"]), ("DEC_ROE_N", ["U5", "13"]),
    ("MODE_B", ["U5", "8"]),
    # РЕ3 (U4) address A[15:11], /CE from ROM select
    ("A11", ["U4", "10"]), ("A12", ["U4", "11"]), ("A13", ["U4", "12"]),
    ("A14", ["U4", "13"]), ("A15", ["U4", "14"]), ("ROM_CE_N", ["U4", "15"]),
    # 8255 Port C bits 0-1 (mode output) -> inverter -> РТ4 /PC0,/PC1
    ("PC0", ["U30", "14"]), ("PC1", ["U30", "15"]),
    ("PC0", ["U6", "1"]), ("PC1", ["U6", "3"]),
    ("PC0_N", ["U6", "2"]), ("PC1_N", ["U6", "4"]),
]


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

    # 74HCT157 pin 15 is the active-low output enable. Both address muxes must
    # be held enabled, not left on the former two-pin floating island.
    if "ADDRMUX_OE_N" in nets:
        errors.append("ADDRMUX_OE_N: retired floating mux-enable net still present")
    for ref in ("U20", "U21"):
        if [ref, "15"] not in nodes(nets["GND"]):
            errors.append(f"{ref}.15: active-low mux enable must be tied to GND")

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
    for net, endpoint in (
        ("BLANK_N", ["U40", "5"]),
        ("BLANK_N", ["J40", "7"]),
        ("PIX_LOAD_N", ["U40", "11"]),
        ("PIX_LOAD_N", ["U41", "15"]),
        ("GND", ["U40", "12"]),
    ):
        if endpoint not in nodes(nets[net]):
            errors.append(f"{endpoint[0]}.{endpoint[1]}: not connected to {net}")

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

    for net, endpoint in DECODE_SOCKET_CONTRACT:
        if net not in nets or endpoint not in nodes(nets[net]):
            errors.append(f"decode-socket contract: {endpoint[0]}.{endpoint[1]} not on {net}")

    timing_contract = (
        ("DECODE_WAIT_N", ["U5", "22"]),
        ("DECODE_WAIT_N", ["U24", "13"]),
        ("RAS_N", ["U24", "14"]),
        ("CAS_N", ["U24", "15"]),
        ("DRAM_WE_N", ["U24", "16"]),
        ("ADDRMUX_SEL", ["U24", "17"]),
        ("WAIT_N", ["U24", "18"]),
        ("VIDEO_ACK", ["U24", "19"]),
        ("REFRESH_TICK", ["U24", "20"]),
    )
    for net, endpoint in timing_contract:
        if net not in nets or endpoint not in nodes(nets[net]):
            errors.append(f"U24 timing contract: {endpoint[0]}.{endpoint[1]} not on {net}")
    if ["U5", "22"] in nodes(nets["WAIT_N"]):
        errors.append("U5.22 and U24.18 must not contend as WAIT_N outputs")

    # Phase 4 observability contract: the analyzer/single-step captures depend on
    # A8-A15 + MEM_WR_N being on J97 (Profile FB high half + write clock), the
    # Z80 control bus being on J98, and the clock-control jumper grounding
    # OSC_OE_N (so the UNO rig can drive CLK). See docs/phase4-bench-bringup.md.
    observability = (
        [(f"A{8 + i}", ["J97", str(i + 1)]) for i in range(8)]
        + [("MEM_WR_N", ["J97", "9"]), ("GND", ["J97", "10"])]
        + [("MREQ_N", ["J98", "1"]), ("IORQ_N", ["J98", "2"]), ("RD_N", ["J98", "3"]),
           ("WR_N", ["J98", "4"]), ("M1_N", ["J98", "5"]), ("RFSH_N", ["J98", "6"]),
           ("WAIT_N", ["J98", "7"]), ("GND", ["J98", "8"])]
        + [("OSC_OE_N", ["J96", "1"]), ("GND", ["J96", "2"])]
    )
    for net, endpoint in observability:
        if net not in nets or endpoint not in nodes(nets[net]):
            errors.append(f"observability contract: {endpoint[0]}.{endpoint[1]} not on {net}")

    if errors:
        print("Rev A physical spec check: FAIL")
        for error in errors:
            print(f"  {error}")
        return 1

    print(f"Rev A physical spec check: PASS ({len(refs)} refs, {len(nets)} nets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
