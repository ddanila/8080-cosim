// make_z80_rom: produce a Z80-executable variant of the Juku ekta37 ROM.
//
// The Juku firmware is 8080 code. A stock Z80 mis-decodes the bytes the 8080
// treats as no-ops / alternate encodings, so VJUGA otherwise has to run its T80
// core in 8080 mode. This tool patches ONLY the bytes the boot actually FETCHES
// AS OPCODES (via a trace over the same memory map cosim uses) and swaps each
// for a length-preserving equivalent that both CPUs decode identically:
//
//   8080 undocumented NOPs  0x08/10/18/20/28/30/38 -> 0x00 (NOP)
//   8080 alt JMP            0xCB                    -> 0xC3 (JMP)
//   8080 alt CALL           0xDD/0xED/0xFD          -> 0xCD (CALL)
//   8080 alt RET            0xD9                    -> 0xC9 (RET)
//
// Same length + same 8080 behavior => the 8080 boot is byte-for-byte unchanged
// (verified: cosim on the patched ROM draws the identical framebuffer), while a
// real Z80 now follows the same control flow. Operand/data bytes are never
// touched because only opcode-fetch addresses are patched.
//
// The ROM self-tests block-1 (0x000B..0x07FF) against the stored checksum at
// 0x000A; the opcode patches change that block, so the tool also recomputes and
// restores rom[0x000A] (0x000A is outside the summed range). Verified against
// cosim to 200M cycles: no other checksummed block is disturbed.
//
// Build/run from repo root:
//   cc -O2 -I cosim -o /tmp/mkz80 spinoffs/minimal-vga/tools/make_z80_rom.c cosim/i8080.c
//   /tmp/mkz80 roms/ekta37.bin spinoffs/minimal-vga/roms/ekta37_z80.bin

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "i8080.h"

static uint8_t rom[16384];
static uint8_t ram[65536];
static uint8_t out_last[256];
static int mode = 0;
static uint8_t portc = 0;
static unsigned long g_vw = 0;
static uint8_t patched[65536];   // opcode-fetch addresses we need to patch (rom space)

#define VRAM_BASE 0xD800u

// Faithful to cosim/trace.c overlay()/rb()/wb()/pout().
static int overlay(uint16_t a, unsigned* idx) {
  switch (mode) {
    case 0: if (a <= 0x3FFF) { *idx = a; return 1; } return 0;
    case 1: if (a >= 0xD800) { *idx = 0x1800 + (a - 0xD800); return 1; } return 0;
    case 2: if (a >= 0x4000 && a <= 0xBFFF) return 2;
            if (a >= 0xD800) { *idx = 0x1800 + (a - 0xD800); return 1; } return 0;
    default: return 0;
  }
}
static uint8_t rb(void* u, uint16_t a) {
  (void)u; unsigned idx = 0; int ov = overlay(a, &idx);
  if (ov == 1) return rom[idx];
  if (ov == 2) return 0xFF;      // empty expansion cart
  return ram[a];
}
static void wb(void* u, uint16_t a, uint8_t v) {
  (void)u; unsigned idx = 0;
  if (overlay(a, &idx)) return;  // write under overlay -> dropped
  ram[a] = v;
  if (a >= VRAM_BASE) g_vw++;
}
static uint8_t pin(void* u, uint8_t p) { (void)u; return out_last[p]; }  // 8255 latch, no key/fdc
static void pout(void* u, uint8_t p, uint8_t v) {
  (void)u; out_last[p] = v;
  if (p == 0x06) { portc = v; mode = portc & 3; }
  else if (p == 0x07) {
    if (v & 0x80) { portc = 0; mode = 0; }
    else { int b = (v >> 1) & 7; if (v & 1) portc |= (1u << b); else portc &= ~(1u << b); mode = portc & 3; }
  }
}

// Which ROM opcode bytes diverge between 8080 and Z80, and the safe swap.
static int z80_safe(uint8_t op, uint8_t* repl) {
  switch (op) {
    case 0x08: case 0x10: case 0x18: case 0x20: case 0x28: case 0x30: case 0x38:
      *repl = 0x00; return 1;      // undocumented NOP -> NOP
    case 0xCB: *repl = 0xC3; return 1;   // alt JMP  -> JMP
    case 0xDD: case 0xED: case 0xFD: *repl = 0xCD; return 1;   // alt CALL -> CALL
    case 0xD9: *repl = 0xC9; return 1;   // alt RET  -> RET
    default: return 0;
  }
}

int main(int argc, char** argv) {
  if (argc < 3) { fprintf(stderr, "usage: %s in.bin out.bin [vw_target] [max_cyc]\n", argv[0]); return 2; }
  unsigned long vw_target = argc > 3 ? strtoul(argv[3], 0, 0) : 6000;
  unsigned long max_cyc   = argc > 4 ? strtoul(argv[4], 0, 0) : 50000000UL;

  FILE* f = fopen(argv[1], "rb");
  if (!f) { perror("open rom"); return 1; }
  if (fread(rom, 1, sizeof(rom), f) != sizeof(rom)) { fprintf(stderr, "rom must be 16384 bytes\n"); return 1; }
  fclose(f);

  i8080 cpu;
  i8080_init(&cpu);
  cpu.read_byte = rb; cpu.write_byte = wb; cpu.port_in = pin; cpu.port_out = pout;
  cpu.userdata = &cpu;

  // Trace the boot; record every ROM address fetched as a divergent opcode.
  unsigned long npatch = 0, nfetch = 0;
  while (g_vw < vw_target && cpu.cyc < max_cyc && !cpu.halted) {
    uint16_t pc = cpu.pc;
    // opcode fetch happens at pc; resolve it through the SAME overlay as the CPU
    unsigned idx = 0; int ov = overlay(pc, &idx);
    if (ov == 1) {                          // opcode comes from ROM -> patchable
      uint8_t op = rom[idx], repl;
      if (z80_safe(op, &repl) && !patched[idx]) {
        patched[idx] = 1; npatch++;
        fprintf(stderr, "patch rom[0x%04X]: 0x%02X -> 0x%02X (pc=0x%04X mode=%d)\n", idx, op, repl, pc, mode);
        rom[idx] = repl;                    // apply in place; 8080 behavior identical
      }
    }
    nfetch++;
    i8080_step(&cpu);
  }
  fprintf(stderr, "boot reached %lu video writes in %lu cyc; %lu opcode steps; %lu opcode bytes patched\n",
          g_vw, cpu.cyc, nfetch, npatch);
  if (g_vw < vw_target) { fprintf(stderr, "WARNING: video-write target not reached\n"); }

  // The ROM self-test sums block-1 (0x000B..0x07FF) and compares it to the stored
  // checksum byte at 0x000A (a mismatch stalls the boot, as the homebrew ekta43
  // ROM does). Our opcode patches all fall inside block-1, so recompute and store
  // the checksum. 0x000A is outside the summed range, so this does not cascade.
  {
    unsigned s = 0; int i;
    for (i = 0x0B; i < 0x800; i++) s += rom[i];
    uint8_t oldck = rom[0x0A], newck = (uint8_t)(s & 0xFF);
    if (newck != oldck) {
      fprintf(stderr, "block-1 checksum rom[0x000A]: 0x%02X -> 0x%02X (restored after patch)\n", oldck, newck);
      rom[0x0A] = newck;
    }
  }

  FILE* o = fopen(argv[2], "wb");
  if (!o) { perror("open out"); return 1; }
  fwrite(rom, 1, sizeof(rom), o);
  fclose(o);
  printf("wrote %s (%lu bytes patched for Z80)\n", argv[2], npatch);
  return 0;
}
