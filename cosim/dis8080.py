#!/usr/bin/env python3
# Minimal but complete Intel 8080 disassembler.
# Usage: dis8080.py <rom.bin> <start_hex> <count> [base_hex]
#   base_hex = address the file's byte 0 maps to (default 0x0000)
import sys

R = ["B", "C", "D", "E", "H", "L", "M", "A"]
RP = ["B", "D", "H", "SP"]          # for LXI/DAD/INX/DCX
PP = ["B", "D", "H", "PSW"]         # for PUSH/POP
CC = ["NZ", "Z", "NC", "C", "PO", "PE", "P", "M"]
ALU = ["ADD", "ADC", "SUB", "SBB", "ANA", "XRA", "ORA", "CMP"]
ALUI = ["ADI", "ACI", "SUI", "SBI", "ANI", "XRI", "ORI", "CPI"]

# fixed/irregular single-byte and special opcodes
FIXED = {
    0x00: "NOP", 0x07: "RLC", 0x0F: "RRC", 0x17: "RAL", 0x1F: "RAR",
    0x27: "DAA", 0x2F: "CMA", 0x37: "STC", 0x3F: "CMC", 0x76: "HLT",
    0xC9: "RET", 0xE9: "PCHL", 0xEB: "XCHG", 0xE3: "XTHL", 0xF9: "SPHL",
    0xFB: "EI", 0xF3: "DI",
    0x02: "STAX B", 0x12: "STAX D", 0x0A: "LDAX B", 0x1A: "LDAX D",
}

def decode(mem, pc, base):
    def b(o): return mem[pc - base + o]
    op = b(0)
    d8 = lambda: b(1)
    d16 = lambda: b(1) | (b(2) << 8)
    # fixed
    if op in FIXED: return FIXED[op], 1
    # 3-byte absolute
    if op == 0xC3: return f"JMP  ${d16():04X}", 3
    if op == 0xCD: return f"CALL ${d16():04X}", 3
    if op == 0x32: return f"STA  ${d16():04X}", 3
    if op == 0x3A: return f"LDA  ${d16():04X}", 3
    if op == 0x22: return f"SHLD ${d16():04X}", 3
    if op == 0x2A: return f"LHLD ${d16():04X}", 3
    # 2-byte port/imm
    if op == 0xD3: return f"OUT  ${d8():02X}", 2
    if op == 0xDB: return f"IN   ${d8():02X}", 2
    # MOV r,r (0x40-0x7F, 0x76 handled above)
    if 0x40 <= op <= 0x7F:
        return f"MOV  {R[(op>>3)&7]},{R[op&7]}", 1
    # ALU A,r (0x80-0xBF)
    if 0x80 <= op <= 0xBF:
        return f"{ALU[(op>>3)&7]:<4} {R[op&7]}", 1
    # INR/DCR r
    if (op & 0xC7) == 0x04: return f"INR  {R[(op>>3)&7]}", 1
    if (op & 0xC7) == 0x05: return f"DCR  {R[(op>>3)&7]}", 1
    # MVI r,d8
    if (op & 0xC7) == 0x06: return f"MVI  {R[(op>>3)&7]},${d8():02X}", 2
    # LXI rp,d16
    if (op & 0xCF) == 0x01: return f"LXI  {RP[(op>>4)&3]},${d16():04X}", 3
    # DAD rp
    if (op & 0xCF) == 0x09: return f"DAD  {RP[(op>>4)&3]}", 1
    # INX/DCX rp
    if (op & 0xCF) == 0x03: return f"INX  {RP[(op>>4)&3]}", 1
    if (op & 0xCF) == 0x0B: return f"DCX  {RP[(op>>4)&3]}", 1
    # PUSH/POP
    if (op & 0xCF) == 0xC5: return f"PUSH {PP[(op>>4)&3]}", 1
    if (op & 0xCF) == 0xC1: return f"POP  {PP[(op>>4)&3]}", 1
    # conditional jmp/call/ret
    if (op & 0xC7) == 0xC2: return f"J{CC[(op>>3)&7]:<3} ${d16():04X}", 3
    if (op & 0xC7) == 0xC4: return f"C{CC[(op>>3)&7]:<3} ${d16():04X}", 3
    if (op & 0xC7) == 0xC0: return f"R{CC[(op>>3)&7]}", 1
    # immediate ALU
    if (op & 0xC7) == 0xC6: return f"{ALUI[(op>>3)&7]:<4} ${d8():02X}", 2
    # RST n
    if (op & 0xC7) == 0xC7: return f"RST  {(op>>3)&7}", 1
    return f"DB   ${op:02X}", 1

def main():
    rom = open(sys.argv[1], "rb").read()
    start = int(sys.argv[2], 16)
    count = int(sys.argv[3])
    base = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0
    pc = start
    for _ in range(count):
        off = pc - base
        if off < 0 or off >= len(rom): break
        txt, n = decode(rom, pc, base)
        raw = " ".join(f"{rom[off+i]:02X}" for i in range(n) if off + i < len(rom))
        print(f"  {pc:04X}: {raw:<9} {txt}")
        pc += n

if __name__ == "__main__":
    main()
