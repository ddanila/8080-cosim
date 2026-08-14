#!/usr/bin/env python3
import sys

REGISTERS = ["B", "C", "D", "E", "H", "L", "M", "A"]
REGISTER_PAIRS = ["B", "D", "H", "SP"]
STACK_PAIRS = ["B", "D", "H", "PSW"]
CONDITIONS = ["NZ", "Z", "NC", "C", "PO", "PE", "P", "M"]
REGISTER_ALU = ["ADD", "ADC", "SUB", "SBB", "ANA", "XRA", "ORA", "CMP"]
IMMEDIATE_ALU = ["ADI", "ACI", "SUI", "SBI", "ANI", "XRI", "ORI", "CPI"]

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
    if op in FIXED: return FIXED[op], 1
    if op == 0xC3: return f"JMP  ${d16():04X}", 3
    if op == 0xCD: return f"CALL ${d16():04X}", 3
    if op == 0x32: return f"STA  ${d16():04X}", 3
    if op == 0x3A: return f"LDA  ${d16():04X}", 3
    if op == 0x22: return f"SHLD ${d16():04X}", 3
    if op == 0x2A: return f"LHLD ${d16():04X}", 3
    if op == 0xD3: return f"OUT  ${d8():02X}", 2
    if op == 0xDB: return f"IN   ${d8():02X}", 2
    if 0x40 <= op <= 0x7F:
        return f"MOV  {REGISTERS[(op>>3)&7]},{REGISTERS[op&7]}", 1
    if 0x80 <= op <= 0xBF:
        return f"{REGISTER_ALU[(op>>3)&7]:<4} {REGISTERS[op&7]}", 1
    if (op & 0xC7) == 0x04: return f"INR  {REGISTERS[(op>>3)&7]}", 1
    if (op & 0xC7) == 0x05: return f"DCR  {REGISTERS[(op>>3)&7]}", 1
    if (op & 0xC7) == 0x06: return f"MVI  {REGISTERS[(op>>3)&7]},${d8():02X}", 2
    if (op & 0xCF) == 0x01: return f"LXI  {REGISTER_PAIRS[(op>>4)&3]},${d16():04X}", 3
    if (op & 0xCF) == 0x09: return f"DAD  {REGISTER_PAIRS[(op>>4)&3]}", 1
    if (op & 0xCF) == 0x03: return f"INX  {REGISTER_PAIRS[(op>>4)&3]}", 1
    if (op & 0xCF) == 0x0B: return f"DCX  {REGISTER_PAIRS[(op>>4)&3]}", 1
    if (op & 0xCF) == 0xC5: return f"PUSH {STACK_PAIRS[(op>>4)&3]}", 1
    if (op & 0xCF) == 0xC1: return f"POP  {STACK_PAIRS[(op>>4)&3]}", 1
    if (op & 0xC7) == 0xC2: return f"J{CONDITIONS[(op>>3)&7]:<3} ${d16():04X}", 3
    if (op & 0xC7) == 0xC4: return f"C{CONDITIONS[(op>>3)&7]:<3} ${d16():04X}", 3
    if (op & 0xC7) == 0xC0: return f"R{CONDITIONS[(op>>3)&7]}", 1
    if (op & 0xC7) == 0xC6: return f"{IMMEDIATE_ALU[(op>>3)&7]:<4} ${d8():02X}", 2
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
