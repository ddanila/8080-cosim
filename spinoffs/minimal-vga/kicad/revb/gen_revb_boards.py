#!/usr/bin/env python3
"""Generate the four rev B card board.json specs (TC.2) deterministically.

Same philosophy as the rev A flow (kicad/gen_rev_a_pcb.py): board connectivity is
generated from a spec, never hand-maintained. Inputs:
  * bus-pinout.json   -- the 39+10 backplane pinout (contract-critical)
  * cards.json        -- per-card roles (which bus signals each card touches)
  * CHIP_PINOUTS below -- accurate DIP pin->function tables for the B1 parts
Output: <card>.board.json (chips[] with ref/type/pins{pin:net}), consumed by the
connectivity checker (scripts/check_revb_boards.py) and, later, per-card LVS
(TC.4) and PCB generation (TC.5).

Scope note (like rev A, which grew its board.json incrementally): every card's
BUS CONNECTOR is generated in full from bus-pinout.json; each IC's BUS-FACING and
POWER pins are bound here. Internal-only passives/decoupling are added as TC.5
needs them. The checker validates the connector<->pinout<->roles consistency.
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

pinout = json.loads((HERE / "bus-pinout.json").read_text())
cards = json.loads((HERE / "cards.json").read_text())

# ---- accurate DIP pinouts (pin number -> net/function) ----
# Z80 DIP-40: transcribed verbatim from spinoffs/minimal-vga/kicad/rev-a-physical.board.json U1
# (rev A's authoritative Z80 mapping). BUSACK_N/NMI_N map to the rev B bus names.
Z80 = {
    "1":"A11","2":"A12","3":"A13","4":"A14","5":"A15","6":"CLK","7":"D4","8":"D3",
    "9":"D5","10":"D6","11":"VCC5","12":"D2","13":"D7","14":"D0","15":"D1","16":"INT_N",
    "17":"NMI_N","18":"HALT_N","19":"MREQ_N","20":"IORQ_N","21":"RD_N","22":"WR_N",
    "23":"BUSAK_N","24":"WAIT_N","25":"BUSRQ_N","26":"RESET_N","27":"M1_N","28":"RFSH_N",
    "29":"GND","30":"A0","31":"A1","32":"A2","33":"A3","34":"A4","35":"A5","36":"A6",
    "37":"A7","38":"A8","39":"A9","40":"A10",
}
# 27C256 DIP-28 (256Kbit EPROM), standard JEDEC pinout. A14 is the top ROM addr line;
# the low 16 KiB image lives in A0..A13 with A14 tied per the decode.
ROM_27C256 = {
    "1":"VCC5","2":"A12","3":"A7","4":"A6","5":"A5","6":"A4","7":"A3","8":"A2","9":"A1",
    "10":"A0","11":"D0","12":"D1","13":"D2","14":"GND","15":"D3","16":"D4","17":"D5",
    "18":"D6","19":"D7","20":"ROM_CE_N","21":"A10","22":"MEM_RD_N","23":"A11","24":"A9",
    "25":"A8","26":"A13","27":"A14","28":"VCC5",
}
# AS6C1008 DIP-32 (128K x 8 SRAM), standard pinout. A16 is the top address line.
SRAM_128K = {
    "1":"RAM_A16_TIE","2":"A14","3":"A12","4":"A7","5":"A6","6":"A5","7":"A4","8":"A3","9":"A2",
    "10":"A1","11":"A0","12":"D0","13":"D1","14":"D2","15":"GND","16":"RAM_CE_N",
    "17":"D3","18":"D4","19":"D5","20":"D6","21":"D7","22":"MEM_RD_N","23":"MEM_WR_N",
    "24":"A8","25":"A9","26":"A13","27":"A15","28":"RAM_A17_TIE","29":"A11","30":"RAM_OE2_TIE",
    "31":"A10","32":"VCC5",
}
# GAL22V10 DIP-24: rev B MEMORY-ONLY decode (unlike rev A U5, which also did I/O
# decode -- in rev B each card decodes its own I/O, so no IORQ_N / IO strobes here).
# Inputs: MREQ_N, RD_N, WR_N, A13-A15, MODE0, MODE1. Outputs: ROM/RAM CE + MEM strobes.
GAL22V10 = {
    # Inputs A11..A15 are needed so RAM_CE stops below the video window (0xD800) and
    # the mem card never fights the Video card on the bus (see rev-b-gal-equations.md).
    "1":"MREQ_N","2":"RD_N","3":"WR_N","4":"A13","5":"A14","6":"A15","7":"MODE0","8":"MODE1",
    "9":"A11","10":"A12","11":"DEC_SPARE0_NC","12":"GND","13":"DEC_SPARE1_NC",
    "14":"ROM_CE_N","15":"RAM_CE_N","16":"MEM_RD_N","17":"MEM_WR_N","18":"DEC_SPARE4_NC",
    "19":"DEC_SPARE5_NC","20":"DEC_SPARE6_NC","21":"DEC_SPARE7_NC","22":"DEC_SPARE8_NC","23":"DEC_SPARE9_NC","24":"VCC5",
}
# 8251 DIP-28 (USART), standard pinout. C/D = A0; chip-select + active-HIGH reset
# come from the I/O-select GAL (D1.16); TxC/RxC from the local baud oscillator;
# CTS/DSR tied active; RxRDY/TxRDY reach the (DNP until B3) PIC; other status = NC.
USART_8251 = {
    "1":"D2","2":"D3","3":"RX","4":"GND","5":"D4","6":"D5","7":"D6","8":"D7","9":"BAUDCLK",
    "10":"WR_N","11":"UART_CS_N","12":"A0","13":"RD_N","14":"SER_RXRDY","15":"SER_TXRDY",
    "16":"BAUDCLK","17":"GND","18":"DTR_N_NC","19":"SYNDET_NC","20":"GND","21":"TX","22":"TXEMPTY_NC",
    "23":"RTS_N_NC","24":"CLK","25":"IO_RESET","26":"VCC5","27":"D0","28":"D1",
}
# ATF16V8/GAL16V8 DIP-20 I/O glue (D1.16 + D1.26): IORQ_N + A2..A7 -> chip selects;
# inverts bus RESET_N to the active-HIGH IO_RESET (8251/8255); inverts the 8259 INT
# (active-HIGH) to the open-drain bus INT_N; and gates M1_N+IORQ_N to INTA_N for the
# 8259. Pins 18/19 are I/O used as inputs (M1_N, PIC_INT).
GAL16V8_IOSEL = {
    "1":"IORQ_N","2":"A2","3":"A3","4":"A4","5":"A5","6":"A6","7":"A7","8":"RESET_N",
    "9":"RD_N","10":"GND","11":"WR_N","12":"PIC_CS_N","13":"PPI_CS_N","14":"UART_CS_N",
    "15":"IO_RESET","16":"INT_N","17":"INTA_N","18":"M1_N","19":"PIC_INT","20":"VCC5",
}
# DIP-14 half-can baud oscillator: drives BAUDCLK (8251 TxC/RxC), local per D1.8.
OSC_BAUD = {"1":"OSC_EN_NC","7":"GND","8":"BAUDCLK","14":"VCC5"}

# --- B3-tier parts (D1.26): footprinted AND fully wired on the io card, but DNP so
# B3 is populate-only, no respin. ---
# 82C55 PPI DIP-40. PA0-7 = keyboard columns; PB0-3 <- 74148 encoder; PC0/PC1 = the
# memory-overlay mode bits (bus MODE0/MODE1). Ports 0x04-0x07 via PPI_CS_N.
PPI_8255 = {
    "1":"KBD_COL3","2":"KBD_COL2","3":"KBD_COL1","4":"KBD_COL0","5":"RD_N","6":"PPI_CS_N",
    "7":"GND","8":"A1","9":"A0","10":"PC7_NC","11":"PC6_NC","12":"PC5_NC","13":"PC4_NC",
    "14":"MODE0","15":"MODE1","16":"PC2_NC","17":"PC3_NC",
    "18":"KBD_ENC0","19":"KBD_ENC1","20":"KBD_ENC2","21":"KBD_ENC_GS",
    "22":"PB4_NC","23":"PB5_NC","24":"PB6_NC","25":"PB7_NC","26":"VCC5",
    "27":"D7","28":"D6","29":"D5","30":"D4","31":"D3","32":"D2","33":"D1","34":"D0",
    "35":"IO_RESET","36":"WR_N","37":"KBD_COL7","38":"KBD_COL6","39":"KBD_COL5","40":"KBD_COL4",
}
# 74148 DIP-16 priority encoder: keyboard rows I0-7 -> 3-bit + GS into 8255 Port B.
ENC_74148 = {
    "1":"KBD_ROW4","2":"KBD_ROW5","3":"KBD_ROW6","4":"KBD_ROW7","5":"KBD_ENC_GS","6":"KBD_ENC2",
    "7":"KBD_ENC1","8":"GND","9":"KBD_ENC0","10":"KBD_ROW0","11":"KBD_ROW1","12":"KBD_ROW2",
    "13":"KBD_ROW3","14":"GND","15":"KBD_ENC_EO_NC","16":"VCC5",   # pin14 EI tied active
}
# 8259-class PIC DIP-28. Ports 0x00-0x01 via PIC_CS_N. IR wiring per hdl/juku_top.v:
# ir0=FDC INTRQ, ir1=FDC DRQ, ir2=serial RxRDY, ir3=serial TxRDY, ir5=frame tick.
PIC_8259 = {
    "1":"PIC_CS_N","2":"WR_N","3":"RD_N","4":"D7","5":"D6","6":"D5","7":"D4","8":"D3",
    "9":"D2","10":"D1","11":"D0","12":"CAS0_NC","13":"CAS1_NC","14":"GND","15":"CAS2_NC",
    "16":"VCC5","17":"PIC_INT","18":"IR7_NC","19":"IR6_NC","20":"FRAME_TICK","21":"IR4_NC",
    "22":"SER_TXRDY","23":"SER_RXRDY","24":"IRQ_B","25":"IRQ_A","26":"INTA_N","27":"A0","28":"VCC5",
}
# NB (D1.21): the CPU card is UNBUFFERED in B1 (Z80 directly on the bus, RC2014
# style). The '245/'244 are a documented optional later-rev margin footprint, not
# populated, so their datapath/control logic is not part of the B1 netlist.
# DIP-14 half-can CPU clock oscillator: drives CLK (socketed, ~2-4 MHz, S1).
OSC_CPU = {"1":"OSC_EN_NC","7":"GND","8":"CLK","14":"VCC5"}

# --- Video card (B2) LVS'd logic: the 3 decode/control GALs + framebuffer SRAM get
# distinct types (unique pin tables) so the per-type LVS pinmap is unambiguous; the
# standard 74xx (counters/mux/register/shifter/buffer) live in CARD_EXTRAS and are
# verified by D1.18 completeness, exactly as the io card's discrete parts. ---
GAL22V10_HDEC = {"1":"DOTCLK","2":"HC0","3":"HC1","4":"HC2","5":"HC3","6":"HC4","7":"HC5",
    "8":"HC6","9":"HC7","10":"HC8","11":"HC9","12":"GND","13":"VID_HDEC_I13_NC","14":"H_END",
    "15":"HSYNC_N","16":"H_BLANK","17":"BYTE_TICK","18":"FI_LOAD_N","19":"SR_LOAD_N",
    "20":"SR_INH","21":"VID_HDEC_O21_NC","22":"VID_HDEC_O22_NC","23":"VID_HDEC_O23_NC","24":"VCC5"}
GAL22V10_VDEC = {"1":"H_BLANK","2":"VC0","3":"VC1","4":"VC2","5":"VC3","6":"VC4","7":"VC5",
    "8":"VC6","9":"VC7","10":"VC8","11":"VC9","12":"GND","13":"H_END","14":"V_END","15":"VSYNC_N",
    "16":"VID_VDEC_VBLANK_NC","17":"VID_VDEC_BLANK_NC","18":"ACTIVE","19":"FRAME_TOP_N",
    "20":"FRAME_TICK","21":"RB_CLK","22":"VID_VDEC_O22_NC","23":"VID_VDEC_O23_NC","24":"VCC5"}
GAL22V10_CTRL = {"1":"DOTCLK","2":"A11","3":"A12","4":"A13","5":"A14","6":"A15","7":"MREQ_N",
    "8":"RD_N","9":"WR_N","10":"MODE0","11":"MODE1","12":"GND","13":"ACTIVE","14":"WAIT_N",
    "15":"MUX_SEL","16":"D245_DIR","17":"D245_OE","18":"FB_CE_N","19":"FB_WE_N","20":"FB_OE_N",
    "21":"VID_CTRL_O21_NC","22":"VID_CTRL_O22_NC","23":"VID_CTRL_O23_NC","24":"VCC5"}
SRAM_FB = {"1":"FB_A16_TIE","2":"FB_A14_TIE","3":"SA12","4":"SA7","5":"SA6","6":"SA5","7":"SA4",
    "8":"SA3","9":"SA2","10":"SA1","11":"SA0","12":"FD0","13":"FD1","14":"FD2","15":"GND",
    "16":"FB_CE_N","17":"FD3","18":"FD4","19":"FD5","20":"FD6","21":"FD7","22":"FB_OE_N",
    "23":"FB_WE_N","24":"SA8","25":"SA9","26":"SA13","27":"FB_A15_TIE","28":"FB_A17_TIE",
    "29":"SA11","30":"FB_OE2_TIE","31":"SA10","32":"VCC5"}

CHIP_TYPES = {
    "Z80_DIP40": Z80, "EPROM_27C256": ROM_27C256, "SRAM_AS6C1008": SRAM_128K,
    "GAL22V10": GAL22V10, "USART_8251": USART_8251,
    "GAL16V8_IOSEL": GAL16V8_IOSEL, "OSC_BAUD": OSC_BAUD, "OSC_CPU": OSC_CPU,
    "PPI_8255": PPI_8255, "ENC_74148": ENC_74148, "PIC_8259": PIC_8259,
    "GAL22V10_HDEC": GAL22V10_HDEC, "GAL22V10_VDEC": GAL22V10_VDEC,
    "GAL22V10_CTRL": GAL22V10_CTRL, "SRAM_FB": SRAM_FB,
}

# Refs footprinted but Do-Not-Populate in the current tier (D1.26/D1.7): fully wired
# so a later tier is populate-only. Emitted as "dnp": true in board.json; excluded
# from LVS instance maps; still subject to D1.18 net completeness.
DNP_REFS = {
    "io": {"U4", "U5", "U6", "J_KBD"},   # 8255, 74148, 8259, keyboard header (B3)
}

# per-card populated ICs: (ref, type)
CARD_CHIPS = {
    "cpu":  [("U1", "Z80_DIP40"), ("U2", "OSC_CPU")],   # unbuffered (D1.21); U2 = clock osc
    "mem":  [("U1", "EPROM_27C256"), ("U2", "SRAM_AS6C1008"), ("U3", "GAL22V10")],
    "io":   [("U1", "USART_8251"), ("U2", "GAL16V8_IOSEL"), ("U3", "OSC_BAUD"),
             ("U4", "PPI_8255"), ("U5", "ENC_74148"), ("U6", "PIC_8259")],   # U4-U6 DNP (B3)
    "backplane": [],
    # LVS'd video logic (distinct types); the repeated 74xx are in CARD_EXTRAS.
    "video": [("U5", "GAL22V10_HDEC"), ("U6", "GAL22V10_VDEC"), ("U7", "GAL22V10_CTRL"),
              ("U21", "SRAM_FB")],
}

def cap(ref):
    """0.1uF decoupling cap: VCC5 <-> GND (power nets, LVS-exempt)."""
    return {"ref": ref, "type": "C_100N", "pins": {"1": "VCC5", "2": "GND"}}

def header(ref, mapping):
    return {"ref": ref, "type": "HDR_1xN", "pins": dict(mapping)}

def comp(ref, typ, mapping):
    return {"ref": ref, "type": typ, "pins": dict(mapping)}

# Per-card discrete extras (decoupling + S9 observability/NOP headers, TD.2-TD.5).
CARD_EXTRAS = {
    "mem": [
        cap("C1"), cap("C2"), cap("C3"),
        # J95-style decode-observability header (S9): GAL outputs to the analyzer.
        header("J_OBS", {"1": "ROM_CE_N", "2": "RAM_CE_N", "3": "MEM_RD_N", "4": "MEM_WR_N", "5": "GND"}),
        # NOP free-run plug provision (J91-style, S9): D0-D7 + GND for the resistor plug.
        header("J_NOP", {"1": "D0", "2": "D1", "3": "D2", "4": "D3", "5": "D4",
                         "6": "D5", "7": "D6", "8": "D7", "9": "GND"}),
    ],
    "io": [
        cap("C1"), cap("C2"), cap("C3"), cap("C4"),   # +2 for the DNP PPI/PIC
        # I/O-select observability (S9): also gives the B3-deferred PPI/PIC selects a
        # scope point so they are provisioned, not dangling, in B1.
        header("J_IOSEL", {"1": "UART_CS_N", "2": "PPI_CS_N", "3": "PIC_CS_N",
                           "4": "IO_RESET", "5": "GND"}),
        # Keyboard connector (B3): 8 columns (8255 PA) + 8 rows (into the 74148) + GND.
        header("J_KBD", {"1": "KBD_COL0", "2": "KBD_COL1", "3": "KBD_COL2", "4": "KBD_COL3",
                         "5": "KBD_COL4", "6": "KBD_COL5", "7": "KBD_COL6", "8": "KBD_COL7",
                         "9": "KBD_ROW0", "10": "KBD_ROW1", "11": "KBD_ROW2", "12": "KBD_ROW3",
                         "13": "KBD_ROW4", "14": "KBD_ROW5", "15": "KBD_ROW6", "16": "KBD_ROW7",
                         "17": "GND"}),
    ],
    "cpu": [
        cap("C1"), cap("C2"),
        # Control-activity observability (S9): the rev A diagnostic signals.
        header("J_DIAG", {"1": "CLK", "2": "M1_N", "3": "RFSH_N", "4": "RESET_N", "5": "GND"}),
    ],
    "backplane": [
        # +5V input: USB-C (THT, CC pulldowns advertise a 5V sink) through a resettable
        # polyfuse into the board rail (D1.35); a bench header taps VCC5 directly (unfused,
        # so the primary bring-up path can't be broken by a blown/absent fuse).
        comp("J_USBC", "USB_C_PWR", {"VBUS": "VBUS_IN", "GND": "GND", "CC1": "USB_CC1", "CC2": "USB_CC2"}),
        comp("R_CC1", "R_5K1", {"1": "USB_CC1", "2": "GND"}),
        comp("R_CC2", "R_5K1", {"1": "USB_CC2", "2": "GND"}),
        comp("F_VBUS", "PTC_1A", {"1": "VBUS_IN", "2": "VCC5"}),
        comp("J_PWR", "HDR_1x2", {"1": "VCC5", "2": "GND"}),
        # Input power conditioning (D1.35): bulk + HF bypass on the rail.
        comp("C_BULK", "C_ELEC_47U", {"1": "VCC5", "2": "GND"}),
        comp("C_IN", "C_100N", {"1": "VCC5", "2": "GND"}),
        # Reset: soldered DS1813-5 TO-92 supervisor with its DATASHEET-VERIFIED pinout
        # (pin 1 = /RST open-drain, pin 2 = VCC, pin 3 = GND; ds1813.pdf p1). Plus a
        # wired-OR pull-up (belt-and-suspenders with the DS1813's internal 5.5k, and
        # correct for any other open-drain supervisor), a power-on RC, and a manual
        # button — reset works even if U_RST is left unpopulated.
        comp("U_RST", "SUPERVISOR_3", {"1": "RESET_N", "2": "VCC5", "3": "GND"}),
        comp("R_RST", "R_10K", {"1": "RESET_N", "2": "VCC5"}),
        comp("C_RST", "C_100N", {"1": "RESET_N", "2": "GND"}),
        comp("SW_RST", "SW_PUSH", {"1": "RESET_N", "2": "GND"}),
        # MODE default pulls (S11): default mode 0 (both low) when no I/O card drives.
        comp("R_M0", "R_10K", {"1": "MODE0", "2": "GND"}),
        comp("R_M1", "R_10K", {"1": "MODE1", "2": "GND"}),
        # Wired-OR pull-ups (S4).
        comp("R_INT", "R_4K7", {"1": "INT_N", "2": "VCC5"}),
        comp("R_WAIT", "R_4K7", {"1": "WAIT_N", "2": "VCC5"}),
        comp("R_NMI", "R_4K7", {"1": "NMI_N", "2": "VCC5"}),
        comp("R_BRQ", "R_4K7", {"1": "BUSRQ_N", "2": "VCC5"}),
        # Bring-up FTDI console header + S5 crossover jumper (disconnect when the I/O
        # card's UART is present): FTDI TX -> bus RX, bus TX -> FTDI RX.
        comp("J_FTDI", "HDR_1x4", {"1": "VCC5", "2": "FTDI_TX", "3": "FTDI_RX", "4": "GND"}),
        comp("JP_S5", "JMP_2x2", {"1": "FTDI_TX", "2": "RX", "3": "TX", "4": "FTDI_RX"}),
        # Power LED. KiCad LED_D5.0mm pad 1 = cathode (K), pad 2 = anode (A) — so pad 1
        # goes to GND and pad 2 to the anode net through R_LED (was reversed).
        comp("D_PWR", "LED", {"1": "GND", "2": "LED_A"}),
        comp("R_LED", "R_2K2", {"1": "VCC5", "2": "LED_A"}),
    ],
    # ---- Video card (B2 / TI.3): TTL VGA framebuffer, per D2.1/D2.6/D2.7/D2.8. Chips
    # carry explicit per-instance pin tables (repeated types -> can't use CARD_CHIPS).
    # Signal flow: OSC->'393 counters (HC0-9/VC0-9) -> decode GALs (sync/blank/active +
    # BYTE_TICK/FI_LOAD_N) ; ROW_BASE '374 + '161 scan counters -> SI (raw index) -> '283
    # base-add (+0x1800) -> FBAxx ; mux SA = MUX_SEL ? A[13:0] : scan ; SRAM[SA]<->FD ;
    # '166 shifts FD->PIXEL ; R-DAC -> DSUB. '245 buffers the CPU data. Control GAL does
    # window decode + WAIT contention (D2.5). ----
    "video": [
        comp("U1", "OSC_25M175", {"1": "OSC_EN_NC", "7": "GND", "8": "DOTCLK", "14": "VCC5"}),
        # '393 dot/line counters (chained): HC0-9, VC0-9; MR = end-of-line/frame
        comp("U2", "TTL_393", {"1": "DOTCLK", "2": "H_END", "3": "HC0", "4": "HC1", "5": "HC2",
             "6": "HC3", "7": "GND", "8": "HC7", "9": "HC6", "10": "HC5", "11": "HC4",
             "12": "H_END", "13": "HC3", "14": "VCC5"}),
        comp("U3", "TTL_393", {"1": "HC7", "2": "H_END", "3": "HC8", "4": "HC9",
             "5": "VID_HC10_NC", "6": "VID_HC11_NC", "7": "GND", "8": "VC3", "9": "VC2",
             "10": "VC1", "11": "VC0", "12": "V_END", "13": "H_END", "14": "VCC5"}),
        comp("U4", "TTL_393", {"1": "VC3", "2": "V_END", "3": "VC4", "4": "VC5", "5": "VC6",
             "6": "VC7", "7": "GND", "8": "VID_VC11_NC", "9": "VID_VC10_NC", "10": "VC9",
             "11": "VC8", "12": "V_END", "13": "VC7", "14": "VCC5"}),
        # (U5 H-decode GAL, U6 V-decode GAL, U7 control GAL, U21 framebuffer SRAM are in
        # CARD_CHIPS with distinct types so they are LVS'd.)
        # '157 address mux (4): SA = MUX_SEL ? A[13:0](CPU) : scan. A-side = scan, B = CPU.
        comp("U8", "TTL_157", {"1": "MUX_SEL", "2": "SI0", "3": "A0", "4": "SA0", "5": "SI1",
             "6": "A1", "7": "SA1", "8": "GND", "9": "SA2", "10": "A2", "11": "SI2",
             "12": "SA3", "13": "A3", "14": "SI3", "15": "GND", "16": "VCC5"}),
        comp("U9", "TTL_157", {"1": "MUX_SEL", "2": "SI4", "3": "A4", "4": "SA4", "5": "SI5",
             "6": "A5", "7": "SA5", "8": "GND", "9": "SA6", "10": "A6", "11": "SI6",
             "12": "SA7", "13": "A7", "14": "SI7", "15": "GND", "16": "VCC5"}),
        comp("U10", "TTL_157", {"1": "MUX_SEL", "2": "SI8", "3": "A8", "4": "SA8", "5": "SI9",
             "6": "A9", "7": "SA9", "8": "GND", "9": "SA10", "10": "A10", "11": "SI10",
             "12": "SA11", "13": "A11", "14": "FBA11", "15": "GND", "16": "VCC5"}),
        comp("U11", "TTL_157", {"1": "MUX_SEL", "2": "FBA12", "3": "A12", "4": "SA12",
             "5": "FBA13", "6": "A13", "7": "SA13", "8": "GND", "9": "VID_MUX3_3Y_NC",
             "10": "VID_MUX3_3B_NC", "11": "VID_MUX3_3A_NC", "12": "VID_MUX3_4Y_NC",
             "13": "VID_MUX3_4B_NC", "14": "VID_MUX3_4A_NC", "15": "GND", "16": "VCC5"}),
        # '161 scan-index counters (4): load ROW_BASE at FI_LOAD_N, +1 at BYTE_TICK -> SI0-13
        comp("U12", "TTL_161", {"1": "RESET_N", "2": "DOTCLK", "3": "RB0", "4": "RB1",
             "5": "RB2", "6": "RB3", "7": "BYTE_TICK", "8": "GND", "9": "FI_LOAD_N",
             "10": "VCC5", "11": "SI3", "12": "SI2", "13": "SI1", "14": "SI0",
             "15": "SI_TC0", "16": "VCC5"}),
        comp("U13", "TTL_161", {"1": "RESET_N", "2": "DOTCLK", "3": "RB4", "4": "RB5",
             "5": "RB6", "6": "RB7", "7": "BYTE_TICK", "8": "GND", "9": "FI_LOAD_N",
             "10": "SI_TC0", "11": "SI7", "12": "SI6", "13": "SI5", "14": "SI4",
             "15": "SI_TC1", "16": "VCC5"}),
        comp("U14", "TTL_161", {"1": "RESET_N", "2": "DOTCLK", "3": "RB8", "4": "RB9",
             "5": "RB10", "6": "RB11", "7": "BYTE_TICK", "8": "GND", "9": "FI_LOAD_N",
             "10": "SI_TC1", "11": "SI11", "12": "SI10", "13": "SI9", "14": "SI8",
             "15": "SI_TC2", "16": "VCC5"}),
        comp("U15", "TTL_161", {"1": "RESET_N", "2": "DOTCLK", "3": "RB12", "4": "RB13",
             "5": "VID_SA3_D2_NC", "6": "VID_SA3_D3_NC", "7": "BYTE_TICK", "8": "GND",
             "9": "FI_LOAD_N", "10": "SI_TC2", "11": "VID_SA3_Q3_NC", "12": "VID_SA3_Q2_NC",
             "13": "SI13", "14": "SI12", "15": "VID_SA3_TC_NC", "16": "VCC5"}),
        # '283 base adder: framebuffer lives at SRAM 0x1800 (= the 0xD800 window's low 14
        # bits), so scanout index SI[13:11] + 3 -> FBA11-13; SI[10:0] pass straight to the
        # mux (0x1800 has no low bits; SI<=9639 so +3 on the top nibble never overflows).
        comp("U16", "TTL_283", {"11": "SI11", "10": "VCC5", "9": "FBA11", "4": "SI12",
             "6": "VCC5", "5": "FBA12", "3": "SI13", "1": "GND", "2": "FBA13", "13": "GND",
             "14": "GND", "12": "VID_ADD_S3_NC", "7": "GND", "15": "VID_ADD_C4_NC",
             "8": "GND", "16": "VCC5"}),
        # '273 row-base register (2, clearable): capture SI (=base+40 on the odd doubled
        # line) -> RB0-13; async-cleared to 0 at frame top (FRAME_TOP_N) so each frame
        # restarts at row 0.
        comp("U17", "TTL_273", {"1": "FRAME_TOP_N", "2": "RB0", "3": "SI0", "4": "SI1",
             "5": "RB1", "6": "RB2", "7": "SI2", "8": "SI3", "9": "RB3", "10": "GND",
             "11": "RB_CLK", "12": "RB4", "13": "SI4", "14": "SI5", "15": "RB5", "16": "RB6",
             "17": "SI6", "18": "SI7", "19": "RB7", "20": "VCC5"}),
        comp("U18", "TTL_273", {"1": "FRAME_TOP_N", "2": "RB8", "3": "SI8", "4": "SI9",
             "5": "RB9", "6": "RB10", "7": "SI10", "8": "SI11", "9": "RB11", "10": "GND",
             "11": "RB_CLK", "12": "RB12", "13": "SI12", "14": "SI13", "15": "RB13",
             "16": "VID_RB_Q6_NC", "17": "VID_RB_D6_NC", "18": "VID_RB_D7_NC",
             "19": "VID_RB_Q7_NC", "20": "VCC5"}),
        # '166 pixel shifter: FD0-7 -> PIXEL (load each byte, shift 1 bit / 2 dots)
        comp("U19", "TTL_166", {"1": "GND", "2": "FD0", "3": "FD1", "4": "FD2", "5": "FD3",
             "6": "SR_INH", "7": "DOTCLK", "8": "GND", "9": "RESET_N", "10": "FD4",
             "11": "FD5", "12": "FD6", "13": "FD7", "14": "PIXEL", "15": "SR_LOAD_N",
             "16": "VCC5"}),
        # '245 CPU data buffer: D0-7 (bus) <-> FD0-7 (framebuffer)
        comp("U20", "TTL_245", {"1": "D245_DIR", "2": "D0", "3": "D1", "4": "D2", "5": "D3",
             "6": "D4", "7": "D5", "8": "D6", "9": "D7", "10": "GND", "11": "FD7", "12": "FD6",
             "13": "FD5", "14": "FD4", "15": "FD3", "16": "FD2", "17": "FD1", "18": "FD0",
             "19": "D245_OE", "20": "VCC5"}),
        # (U21 framebuffer SRAM is in CARD_CHIPS as type SRAM_FB, so it is LVS'd.)
        # blanking AND: RGB must be 0 outside the active region or the monitor loses sync /
        # shows garbage. VID_PIXEL = PIXEL & ACTIVE ('08, 1 of 4 gates).
        comp("U22", "TTL_08", {"1": "PIXEL", "2": "ACTIVE", "3": "VID_PIXEL", "4": "VID_AND2A_NC",
             "5": "VID_AND2B_NC", "6": "VID_AND2Y_NC", "7": "GND", "8": "VID_AND3A_NC",
             "9": "VID_AND3B_NC", "10": "VID_AND3Y_NC", "11": "VID_AND4A_NC",
             "12": "VID_AND4B_NC", "13": "VID_AND4Y_NC", "14": "VCC5"}),
        # VGA output: DSUB-15HD + mono resistor DAC (VID_PIXEL -> R=G=B), sync direct (both
        # negative polarity for 640x480@60)
        comp("J_VGA", "DSUB15HD", {"1": "VID_R", "2": "VID_G", "3": "VID_B", "4": "VGA_ID2_NC",
             "5": "GND", "6": "GND", "7": "GND", "8": "GND", "9": "VGA_KEY_NC", "10": "GND",
             "11": "VGA_ID0_NC", "12": "VGA_SDA_NC", "13": "HSYNC_N", "14": "VSYNC_N",
             "15": "VGA_SCL_NC"}),
        comp("R_VR", "R_470", {"1": "VID_PIXEL", "2": "VID_R"}),
        comp("R_VG", "R_470", {"1": "VID_PIXEL", "2": "VID_G"}),
        comp("R_VB", "R_470", {"1": "VID_PIXEL", "2": "VID_B"}),
        cap("C1"), cap("C2"), cap("C3"), cap("C4"), cap("C5"), cap("C6"), cap("C7"),
    ],
}


def bus_connector(ref):
    """A 39+10 edge connector: pin -> bus signal, from bus-pinout.json."""
    pins = {}
    for p, sig in pinout["base"].items():
        pins[p] = sig
    for p, sig in pinout["extension"].items():
        pins[p] = sig
    return {"ref": ref, "type": "REVB_BUS_39_10", "pins": pins}


POWER_NETS = {"VCC5", "GND"}


def nets_from_chips(chips):
    """Invert chips[].pins into a nets dict (net -> nodes[[ref,pin]]), the shape
    netlist_from_board.py / sync/lvs.py consume. Power nets are flagged power:true
    so LVS drops them (HDL models have no power pins)."""
    nets = {}
    for comp in chips:
        for pinnum, net in comp["pins"].items():
            nets.setdefault(net, []).append([comp["ref"], pinnum])
    out = {}
    for net, nodes in nets.items():
        if net in POWER_NETS:
            out[net] = {"nodes": nodes, "power": True}
        else:
            out[net] = {"nodes": nodes}
    return out


def build(card):
    chips = []
    if card == "backplane":
        # 6 slots wired in parallel: same signal on pin N of every slot.
        for s in range(1, 7):
            chips.append(bus_connector(f"J_S{s}"))
        chips.extend(CARD_EXTRAS.get("backplane", []))
    else:
        chips.append(bus_connector("J_BUS"))
        for ref, typ in CARD_CHIPS[card]:
            chips.append({"ref": ref, "type": typ, "pins": dict(CHIP_TYPES[typ])})
        chips.extend(CARD_EXTRAS.get(card, []))
    # mark DNP refs (D1.26)
    dnp = DNP_REFS.get(card, set())
    for c in chips:
        if c["ref"] in dnp:
            c["dnp"] = True
    return {"card": card, "generated_by": "gen_revb_boards.py",
            "chips": chips, "nets": nets_from_chips(chips)}


def main():
    for card in ("backplane", "cpu", "mem", "io", "video"):
        out = HERE / f"{card}.board.json"
        out.write_text(json.dumps(build(card), indent=2) + "\n")
        print(f"wrote {out.relative_to(ROOT)} ({len(build(card)['chips'])} components)")


if __name__ == "__main__":
    main()
