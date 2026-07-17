#!/usr/bin/env python3
"""Build the VJUGA rev B minimum-tier bring-up ROM (revb_bringup.bin).

Self-contained two-pass 8080 assembler (no external toolchain) — see
docs/rev-b-execution-guide.md T1.1. The image is org 0x0000, 8080-subset opcodes
only (so cosim is its oracle), 16 KiB, with a trailing checksum byte at 0x3FFF
chosen so the whole ROM sums to 0 mod 256.

Behavior on the minimum tier (CPU + Memory + I/O-UART, no Video):
  * init the 8251 USART (ports 0x08 data / 0x09 ctl-status) with TxEN so, by the
    documented cosim coincidence (execution-guide D1.2), the TxRDY poll (status
    bit0) reads ready off the command-word latch;
  * print a banner;
  * walking-pattern + address-in-cell RAM test over 0x4000..0xD6FF (top page
    0xD700..0xD7FF reserved for stack + vars, so the test never clobbers the
    return stack); print "RAM PASS" or "RAM FAIL @hhhh";
  * verify the ROM checksum; print "ROM OK" / "ROM BAD";
  * a tiny serial monitor: A=set addr, D=dump 16, W=write byte, G=go. (Interactive
    path is exercised on the bench, T1.11; cosim reaches only the quiet wait loop.)
"""
import sys, pathlib

# ---- registers / register pairs ----
R = {'B':0,'C':1,'D':2,'E':3,'H':4,'L':5,'M':6,'A':7}
RP = {'B':0,'D':1,'H':2,'SP':3}          # LXI/INX/DCX/DAD
RPP = {'B':0,'D':1,'H':2,'PSW':3}        # PUSH/POP

class Asm:
    def __init__(self):
        self.items = []   # ('label',name) | ('bytes',[..]) | ('ref16',op,label)
        self.labels = {}
    def label(self, n): self.items.append(('label', n))
    def b(self, *bs): self.items.append(('bytes', list(bs)))
    def ref(self, op, label): self.items.append(('ref16', op, label))   # op + 2-byte little-endian label addr
    def string(self, s):
        self.items.append(('bytes', [ord(c) for c in s] + [0]))
    # --- instruction helpers ---
    def DI(self): self.b(0xF3)
    def HLT(self): self.b(0x76)
    def RET(self): self.b(0xC9)
    def RZ(self): self.b(0xC8)
    def PCHL(self): self.b(0xE9)
    def LXI(self, rp, v): self.b(0x01 | RP[rp]<<4, v & 0xFF, (v>>8)&0xFF)
    def LXIl(self, rp, label): self.ref(0x01 | RP[rp]<<4, label)  # LXI with label addr
    def MVI(self, r, v): self.b(0x06 | R[r]<<3, v & 0xFF)
    def MOV(self, d, s): self.b(0x40 | R[d]<<3 | R[s])
    def INX(self, rp): self.b(0x03 | RP[rp]<<4)
    def DCR(self, r): self.b(0x05 | R[r]<<3)
    def ADD(self, r): self.b(0x80 | R[r])
    def ORA(self, r): self.b(0xB0 | R[r])
    def CMP(self, r): self.b(0xB8 | R[r])
    def XRA(self, r): self.b(0xA8 | R[r])
    def ANI(self, v): self.b(0xE6, v & 0xFF)
    def CPI(self, v): self.b(0xFE, v & 0xFF)
    def SUI(self, v): self.b(0xD6, v & 0xFF)
    def IN(self, p): self.b(0xDB, p & 0xFF)
    def OUT(self, p): self.b(0xD3, p & 0xFF)
    def PUSH(self, rp): self.b(0xC5 | RPP[rp]<<4)
    def POP(self, rp): self.b(0xC1 | RPP[rp]<<4)
    def LHLD(self, a): self.b(0x2A, a & 0xFF, (a>>8)&0xFF)
    def SHLD(self, a): self.b(0x22, a & 0xFF, (a>>8)&0xFF)
    def JMP(self, l): self.ref(0xC3, l)
    def JZ(self, l): self.ref(0xCA, l)
    def JNZ(self, l): self.ref(0xC2, l)
    def JC(self, l): self.ref(0xDA, l)
    def CALL(self, l): self.ref(0xCD, l)
    # assemble
    def assemble(self, size=16384):
        # pass 1: addresses
        addr = 0
        for it in self.items:
            if it[0] == 'label': self.labels[it[1]] = addr
            elif it[0] == 'bytes': addr += len(it[1])
            elif it[0] == 'ref16': addr += 3
        # pass 2: emit
        out = bytearray()
        for it in self.items:
            if it[0] == 'bytes': out += bytes(it[1])
            elif it[0] == 'ref16':
                _, op, label = it
                a = self.labels[label]
                out += bytes([op, a & 0xFF, (a>>8)&0xFF])
        if len(out) > size-1:
            raise SystemExit(f"program {len(out)} bytes exceeds {size-1}")
        out += bytes(size-1-len(out))          # pad to size-1
        s = sum(out) & 0xFF
        out += bytes([(-s) & 0xFF])            # checksum byte at size-1 -> total % 256 == 0
        return bytes(out)

SP_TOP   = 0xD780
CURADDR  = 0xD7F0
RAM_LO   = 0x4000
RAM_HIPG = 0xD7      # test stops when H reaches 0xD7 (i.e. 0x4000..0xD6FF)

a = Asm()
# ---- reset / init ----
a.label('start')
a.DI()
a.LXI('SP', SP_TOP)
# 8251 canonical reset: 3x null, internal-reset 0x40, mode, command
a.MVI('A',0x00); a.OUT(0x09); a.OUT(0x09); a.OUT(0x09)
a.MVI('A',0x40); a.OUT(0x09)          # internal reset
a.MVI('A',0x4E); a.OUT(0x09)          # mode: 8N1, x16
a.MVI('A',0x37); a.OUT(0x09)          # command: TxEN|RxEN|RTS|DTR|ErrReset
a.LXIl('H','msg_banner'); a.CALL('puts')
a.CALL('ramtest')
a.CALL('romsum')
a.LXI('H', RAM_LO); a.SHLD(CURADDR)   # default monitor address
a.LXIl('H','msg_ready'); a.CALL('puts')
# ---- monitor ----
a.label('monitor')
a.CALL('getchar')
a.CPI(0x41); a.JZ('cmd_addr')    # 'A'
a.CPI(0x44); a.JZ('cmd_dump')    # 'D'
a.CPI(0x57); a.JZ('cmd_write')   # 'W'
a.CPI(0x47); a.JZ('cmd_go')      # 'G'
a.JMP('monitor')

# ---- RAM test ----
a.label('ramtest')
a.MVI('B',0xA5); a.CALL('fillverify')
a.MVI('B',0x5A); a.CALL('fillverify')
a.CALL('addrverify')
a.LXIl('H','msg_rampass'); a.CALL('puts')
a.RET()

a.label('fillverify')            # B = pattern
a.LXI('H', RAM_LO)
a.label('fv_w')
a.MOV('M','B'); a.INX('H'); a.MOV('A','H'); a.CPI(RAM_HIPG); a.JNZ('fv_w')
a.LXI('H', RAM_LO)
a.label('fv_r')
a.MOV('A','M'); a.CMP('B'); a.JNZ('ram_fail')
a.INX('H'); a.MOV('A','H'); a.CPI(RAM_HIPG); a.JNZ('fv_r')
a.RET()

a.label('addrverify')            # write low byte of address to each cell
a.LXI('H', RAM_LO)
a.label('av_w')
a.MOV('A','L'); a.MOV('M','A'); a.INX('H'); a.MOV('A','H'); a.CPI(RAM_HIPG); a.JNZ('av_w')
a.LXI('H', RAM_LO)
a.label('av_r')
a.MOV('A','M'); a.CMP('L'); a.JNZ('ram_fail')
a.INX('H'); a.MOV('A','H'); a.CPI(RAM_HIPG); a.JNZ('av_r')
a.RET()

a.label('ram_fail')              # HL = failing address
a.PUSH('H')
a.LXIl('H','msg_ramfail'); a.CALL('puts')
a.POP('H')
a.MOV('A','H'); a.CALL('puthex')
a.MOV('A','L'); a.CALL('puthex')
a.CALL('crlf')
a.label('halt_spin')
a.JMP('halt_spin')

# ---- ROM checksum ----
a.label('romsum')
a.LXI('H',0x0000); a.XRA('A'); a.MOV('B','A')
a.label('rs_l')
a.MOV('A','B'); a.ADD('M'); a.MOV('B','A')
a.INX('H'); a.MOV('A','H'); a.CPI(0x40); a.JNZ('rs_l')
a.MOV('A','B'); a.ORA('A'); a.JNZ('rs_bad')
a.LXIl('H','msg_romok'); a.CALL('puts'); a.RET()
a.label('rs_bad')
a.LXIl('H','msg_rombad'); a.CALL('puts'); a.RET()

# ---- serial primitives ----
a.label('puts')                  # HL -> zero-terminated string
a.MOV('A','M'); a.ORA('A'); a.RZ()
a.CALL('putc'); a.INX('H'); a.JMP('puts')

a.label('putc')                  # A = char
a.PUSH('PSW')
a.label('pc_wait')
a.IN(0x09); a.ANI(0x01); a.JZ('pc_wait')     # TxRDY (cosim: TxEN latch bit0)
a.POP('PSW'); a.OUT(0x08); a.RET()

a.label('getchar')               # -> A = char
a.IN(0x09); a.ANI(0x02); a.JZ('getchar')     # RxRDY
a.IN(0x08); a.RET()

a.label('puthex')                # A = byte -> two hex chars
a.PUSH('PSW')
a.MOV('B','A')
# high nibble: 4x (A = A>>? ) -- use rotate-free: divide by 16 via 4 right shifts using ADD? easier: repeated RRC
# implement RRC inline (0x0F)
a.b(0x0F); a.b(0x0F); a.b(0x0F); a.b(0x0F)    # RRC x4 -> nibble swap
a.ANI(0x0F); a.CALL('nib2asc'); a.CALL('putc')
a.MOV('A','B'); a.ANI(0x0F); a.CALL('nib2asc'); a.CALL('putc')
a.POP('PSW'); a.RET()

a.label('nib2asc')               # A (0..15) -> ascii
a.CPI(0x0A); a.JC('n2a_dig')
a.SUI(0x0A); a.b(0xC6, ord('A'))   # ADI 'A'  (A-10 + 'A')
a.RET()
a.label('n2a_dig')
a.b(0xC6, ord('0'))                # ADI '0'
a.RET()

a.label('crlf')
a.MVI('A',0x0D); a.CALL('putc'); a.MVI('A',0x0A); a.CALL('putc'); a.RET()

# ---- monitor helpers ----
a.label('getnib')                # -> A = 0..15
a.CALL('getchar'); a.SUI(0x30); a.CPI(0x0A); a.JC('gn_done'); a.SUI(0x07)
a.label('gn_done')
a.ANI(0x0F); a.RET()

a.label('get2hex')               # -> A = byte
a.CALL('getnib')
a.ADD('A'); a.ADD('A'); a.ADD('A'); a.ADD('A')   # <<4
a.MOV('C','A'); a.CALL('getnib'); a.ANI(0x0F); a.ADD('C'); a.RET()

a.label('get4hex')               # -> HL
a.CALL('get2hex'); a.MOV('H','A'); a.CALL('get2hex'); a.MOV('L','A'); a.RET()

a.label('cmd_addr')
a.CALL('get4hex'); a.SHLD(CURADDR); a.JMP('monitor')

a.label('cmd_dump')
a.LHLD(CURADDR)
a.MOV('A','H'); a.CALL('puthex'); a.MOV('A','L'); a.CALL('puthex')
a.MVI('A',0x3A); a.CALL('putc'); a.MVI('A',0x20); a.CALL('putc')
a.MVI('C',16)
a.label('cd_l')
a.MOV('A','M'); a.CALL('puthex'); a.MVI('A',0x20); a.CALL('putc')
a.INX('H'); a.DCR('C'); a.JNZ('cd_l')
a.SHLD(CURADDR); a.CALL('crlf'); a.JMP('monitor')

a.label('cmd_write')
a.CALL('get2hex'); a.MOV('B','A')
a.LHLD(CURADDR); a.MOV('M','B'); a.INX('H'); a.SHLD(CURADDR); a.JMP('monitor')

a.label('cmd_go')
a.LHLD(CURADDR); a.PCHL()

# ---- strings ----
a.label('msg_banner');  a.string("VJUGA rev B bring-up\r\n")
a.label('msg_rampass'); a.string("RAM PASS\r\n")
a.label('msg_ramfail'); a.string("RAM FAIL @")
a.label('msg_romok');   a.string("ROM OK\r\n")
a.label('msg_rombad');  a.string("ROM BAD\r\n")
a.label('msg_ready');   a.string("READY\r\n")

img = a.assemble(16384)
out = pathlib.Path(__file__).with_name('revb_bringup.bin')
out.write_bytes(img)
print(f"wrote {out} ({len(img)} bytes), entry=0x0000, checksum byte=0x{img[-1]:02X}, total%256={sum(img)&0xFF}")
