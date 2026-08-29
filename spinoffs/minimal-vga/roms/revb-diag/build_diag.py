#!/usr/bin/env python3
"""Build DIAG/VJUGA: layered POST with no stack before RAM passes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_BIN = HERE.parent / "diag_vjuga.bin"
DEFAULT_MAP = HERE.parent / "diag_vjuga.map.json"

R = {"B": 0, "C": 1, "D": 2, "E": 3, "H": 4, "L": 5, "M": 6, "A": 7}
RP = {"B": 0, "D": 1, "H": 2, "SP": 3}
RPP = {"B": 0, "D": 1, "H": 2, "PSW": 3}


class Asm:
    def __init__(self) -> None:
        self.items: list[tuple] = []
        self.labels: dict[str, int] = {}
        self.trace: list[dict[str, object]] = []

    def label(self, name: str) -> None: self.items.append(("label", name))
    def b(self, mnemonic: str, *values: int) -> None: self.items.append(("bytes", mnemonic, list(values)))
    def ref(self, mnemonic: str, opcode: int, label: str) -> None: self.items.append(("ref16", mnemonic, opcode, label))
    def string(self, value: str) -> None: self.items.append(("bytes", "DB", [ord(c) for c in value] + [0]))

    def DI(self): self.b("DI", 0xF3)
    def HLT(self): self.b("HLT", 0x76)
    def RET(self): self.b("RET", 0xC9)
    def LXI(self, rp, value): self.b(f"LXI {rp}", 0x01 | RP[rp] << 4, value & 0xFF, value >> 8)
    def LXIl(self, rp, label): self.ref(f"LXI {rp}", 0x01 | RP[rp] << 4, label)
    def MVI(self, reg, value): self.b(f"MVI {reg}", 0x06 | R[reg] << 3, value & 0xFF)
    def MOV(self, dst, src): self.b(f"MOV {dst},{src}", 0x40 | R[dst] << 3 | R[src])
    def INX(self, rp): self.b(f"INX {rp}", 0x03 | RP[rp] << 4)
    def DCX(self, rp): self.b(f"DCX {rp}", 0x0B | RP[rp] << 4)
    def DCR(self, reg): self.b(f"DCR {reg}", 0x05 | R[reg] << 3)
    def ADD(self, reg): self.b(f"ADD {reg}", 0x80 | R[reg])
    def ORA(self, reg): self.b(f"ORA {reg}", 0xB0 | R[reg])
    def CMP(self, reg): self.b(f"CMP {reg}", 0xB8 | R[reg])
    def XRA(self, reg): self.b(f"XRA {reg}", 0xA8 | R[reg])
    def ANI(self, value): self.b("ANI", 0xE6, value & 0xFF)
    def CPI(self, value): self.b("CPI", 0xFE, value & 0xFF)
    def IN(self, port): self.b(f"IN {port:02X}", 0xDB, port & 0xFF)
    def OUT(self, port): self.b(f"OUT {port:02X}", 0xD3, port & 0xFF)
    def PUSH(self, rp): self.b(f"PUSH {rp}", 0xC5 | RPP[rp] << 4)
    def POP(self, rp): self.b(f"POP {rp}", 0xC1 | RPP[rp] << 4)
    def JMP(self, label): self.ref("JMP", 0xC3, label)
    def JZ(self, label): self.ref("JZ", 0xCA, label)
    def JNZ(self, label): self.ref("JNZ", 0xC2, label)
    def JNC(self, label): self.ref("JNC", 0xD2, label)
    def CALL(self, label): self.ref("CALL", 0xCD, label)

    def assemble(self, size: int = 16384) -> tuple[bytes, dict[str, int], list[dict[str, object]]]:
        address = 0
        for item in self.items:
            if item[0] == "label": self.labels[item[1]] = address
            elif item[0] == "bytes": address += len(item[2])
            else: address += 3
        output = bytearray()
        for item in self.items:
            if item[0] == "label": continue
            start = len(output)
            if item[0] == "bytes":
                _, mnemonic, values = item
                output.extend(v & 0xFF for v in values)
            else:
                _, mnemonic, opcode, label = item
                target = self.labels[label]
                output.extend((opcode, target & 0xFF, target >> 8))
            self.trace.append({"address": start, "mnemonic": mnemonic, "bytes": list(output[start:])})
        if len(output) > size - 1:
            raise ValueError(f"DIAG program is {len(output)} bytes; limit {size - 1}")
        output.extend(bytes(size - 1 - len(output)))
        output.append((-sum(output)) & 0xFF)
        return bytes(output), self.labels, self.trace


def build(ram_high_page: int = 0xD7) -> tuple[bytes, dict[str, object]]:
    a = Asm()
    # Before stack_ready every path is inline: ROM, RAM-data and RAM-address.
    a.label("start")
    a.DI(); a.MVI("A", 0x10); a.OUT(0x20)

    a.MVI("A", 0x20); a.OUT(0x20)
    a.LXI("H", 0x0000); a.LXI("B", 0x4000); a.XRA("A"); a.MOV("D", "A")
    a.label("rom_loop")
    a.MOV("A", "D"); a.ADD("M"); a.MOV("D", "A"); a.INX("H"); a.DCX("B")
    a.MOV("A", "B"); a.ORA("C"); a.JNZ("rom_loop")
    a.MOV("A", "D"); a.ORA("A"); a.JNZ("rom_fail")
    a.MVI("A", 0x21); a.OUT(0x20)

    a.MVI("A", 0x30); a.OUT(0x20)
    for suffix, pattern in (("a5", 0xA5), ("5a", 0x5A)):
        a.MVI("B", pattern); a.LXI("H", 0x4000)
        a.label(f"data_write_{suffix}")
        a.MOV("M", "B"); a.INX("H"); a.MOV("A", "H"); a.CPI(ram_high_page); a.JNZ(f"data_write_{suffix}")
        a.LXI("H", 0x4000)
        a.label(f"data_read_{suffix}")
        a.MOV("A", "M"); a.CMP("B"); a.JNZ("ram_data_fail")
        a.INX("H"); a.MOV("A", "H"); a.CPI(ram_high_page); a.JNZ(f"data_read_{suffix}")
    a.MVI("A", 0x31); a.OUT(0x20)

    a.MVI("A", 0x40); a.OUT(0x20); a.LXI("H", 0x4000)
    a.label("address_write")
    a.MOV("A", "L"); a.MOV("M", "A"); a.INX("H"); a.MOV("A", "H"); a.CPI(ram_high_page); a.JNZ("address_write")
    a.LXI("H", 0x4000)
    a.label("address_read")
    a.MOV("A", "M"); a.CMP("L"); a.JNZ("ram_address_fail")
    a.INX("H"); a.MOV("A", "H"); a.CPI(ram_high_page); a.JNZ("address_read")
    a.MVI("A", 0x41); a.OUT(0x20)

    a.label("stack_ready")
    a.LXI("SP", 0xD780)
    a.MVI("A", 0x50); a.OUT(0x20)
    a.MVI("A", 0x15); a.OUT(0x1B); a.MVI("A", 4); a.OUT(0x18)
    a.XRA("A"); a.OUT(0x1B); a.IN(0x18); a.ORA("A"); a.JZ("pit_fail"); a.CPI(5); a.JNC("pit_fail")
    a.MVI("A", 0x51); a.OUT(0x20)

    # Audible proof after PIT register/count proof.
    a.MVI("A", 0x76); a.OUT(0x1B); a.MVI("A", 0xEE); a.OUT(0x19); a.MVI("A", 0x13); a.OUT(0x19)
    a.LXI("B", 12000); a.label("tone_delay"); a.DCX("B"); a.MOV("A", "B"); a.ORA("C"); a.JNZ("tone_delay")
    a.MVI("A", 0x50); a.OUT(0x1B); a.MVI("A", 1); a.OUT(0x19)

    a.MVI("A", 0x60); a.OUT(0x20)
    a.XRA("A"); a.OUT(0x09); a.OUT(0x09); a.OUT(0x09)
    a.MVI("A", 0x40); a.OUT(0x09); a.MVI("A", 0x4E); a.OUT(0x09); a.MVI("A", 0x37); a.OUT(0x09)
    # The idle initialized 8251 status is exactly TxEMPTY|TxRDY = 05h.
    # Testing only those set bits would let an absent/open-bus FFh read pass.
    a.IN(0x09); a.CPI(0x05); a.JNZ("usart_fail")
    a.MVI("A", 0x61); a.OUT(0x20); a.LXIl("H", "msg_serial"); a.CALL("puts")

    a.MVI("A", 0x70); a.OUT(0x20)
    a.MVI("A", 0x9B); a.OUT(0x0F); a.MVI("A", 0x82); a.OUT(0x07); a.MVI("A", 0x0E); a.OUT(0x07)
    a.MVI("A", 0xD6); a.OUT(0x00); a.MVI("A", 0xFE); a.OUT(0x01); a.MVI("A", 0xFF); a.OUT(0x01)
    a.MVI("A", 0x71); a.OUT(0x20); a.LXIl("H", "msg_io"); a.CALL("puts")

    a.MVI("A", 0x80); a.OUT(0x20); a.LXI("H", 0xD800); a.MVI("B", 40); a.MVI("A", 0xAA)
    a.label("vga_pattern")
    a.MOV("M", "A"); a.INX("H"); a.DCR("B"); a.JNZ("vga_pattern")
    a.LXI("B", 20000); a.label("frame_wait"); a.DCX("B"); a.MOV("A", "B"); a.ORA("C"); a.JNZ("frame_wait")
    a.MVI("A", 0x81); a.OUT(0x20); a.LXIl("H", "msg_vga"); a.CALL("puts")
    a.MVI("A", 0xFF); a.OUT(0x20); a.LXIl("H", "msg_ready"); a.CALL("puts")
    a.label("ready_loop"); a.JMP("ready_loop")

    # Early failures intentionally have no stack, PIT tone, or serial helper.
    a.label("rom_fail"); a.MVI("A", 0x2F); a.OUT(0x20); a.JMP("early_halt")
    a.label("ram_data_fail"); a.MVI("A", 0x3F); a.OUT(0x20); a.JMP("early_halt")
    a.label("ram_address_fail"); a.MVI("A", 0x4F); a.OUT(0x20)
    a.label("early_halt"); a.HLT(); a.JMP("early_halt")
    a.label("pit_fail"); a.MVI("A", 0x5F); a.OUT(0x20); a.JMP("late_halt")
    a.label("usart_fail"); a.MVI("A", 0x6F); a.OUT(0x20); a.JMP("late_halt")
    a.label("late_halt"); a.HLT(); a.JMP("late_halt")

    a.label("puts")
    a.MOV("A", "M"); a.ORA("A"); a.JZ("puts_done"); a.CALL("putc"); a.INX("H"); a.JMP("puts")
    a.label("puts_done"); a.RET()
    a.label("putc")
    a.PUSH("PSW"); a.label("putc_wait"); a.IN(0x09); a.ANI(1); a.JZ("putc_wait")
    a.POP("PSW"); a.OUT(0x08); a.RET()

    a.label("msg_serial"); a.string("D57 USART PASS\r\n")
    a.label("msg_io"); a.string("PPI PIC PASS\r\n")
    a.label("msg_vga"); a.string("VGA PATTERN PASS\r\n")
    a.label("msg_ready"); a.string("DIAG READY\r\n")

    image, labels, trace = a.assemble()
    stack_ready = labels["stack_ready"]
    forbidden = [row for row in trace if row["address"] < stack_ready and
                 (str(row["mnemonic"]).startswith(("CALL", "PUSH", "POP")) or row["mnemonic"] == "LXI SP")]
    if forbidden:
        raise ValueError(f"stack/helper opcode before RAM pass: {forbidden}")
    metadata: dict[str, object] = {
        "schema": 1,
        "role": "DIAG/VJUGA",
        "image_bytes": len(image),
        "sha256": hashlib.sha256(image).hexdigest(),
        "whole_image_additive8": sum(image) & 0xFF,
        "ram_range": f"4000h-{ram_high_page - 1:02X}FFh",
        "stack_ready_address": stack_ready,
        "first_stack_instruction": next(row for row in trace if row["address"] >= stack_ready),
        "early_forbidden_instructions": forbidden,
        "labels": labels,
        "instruction_trace": trace,
        "expected_post_sequence": ["10", "20", "21", "30", "31", "40", "41", "50", "51", "60", "61", "70", "71", "80", "81", "FF"]
    }
    return image, metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--ram-high-page", type=lambda s: int(s, 0), default=0xD7)
    args = parser.parse_args()
    image, metadata = build(args.ram_high_page)
    encoded = json.dumps(metadata, indent=2) + "\n"
    if args.check:
        if not DEFAULT_BIN.exists() or DEFAULT_BIN.read_bytes() != image:
            raise SystemExit("diag_vjuga.bin is stale")
        if not DEFAULT_MAP.exists() or DEFAULT_MAP.read_text() != encoded:
            raise SystemExit("diag_vjuga.map.json is stale")
    else:
        DEFAULT_BIN.write_bytes(image)
        DEFAULT_MAP.write_text(encoded)
    print(f"DIAG/VJUGA: PASS {len(image)} bytes sha256={metadata['sha256']} stack@{metadata['stack_ready_address']:04X}h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
