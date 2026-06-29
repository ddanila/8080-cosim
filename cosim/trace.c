// Traced 8080 boot harness for the Juku E5104 (ekta43.bin).
//
// Memory model is now faithful to MAME's ussr/juku.cpp (BSD-3, ref/mame_juku.cpp):
//   - 64 KB DRAM base (m_ram)
//   - a 4-way "memory view" overlays ROM, selected by 8255#0 Port C bits[1:0]
//     (I/O port 0x06, or via 8255 BSR on the control port 0x07):
//        mode 0 (reset): ROM 0x0000..0x3FFF  (region maincpu +0x0000)
//        mode 1:         ROM 0xD800..0xFFFF  (region maincpu +0x1800), rest RAM
//        mode 2:         expcart 0x4000..0xBFFF + ROM 0xD800..0xFFFF
//        mode 3:         all RAM
//   - video reads DRAM at 0xD800, stride = WIDTH/8 = 40 bytes/line (320x241 mono)
//
// All IN ports return 0x00 (no key / not ready). Interrupts are NOT modelled yet.
//
// Build: cc -O2 -o trace trace.c i8080.c
// Run:   ./trace /path/to/ekta43.bin [max_cycles]

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "i8080.h"

#define MEM_SIZE   0x10000u
#define ROM_SIZE   0x4000u          // 16 KB
#define VRAM_BASE  0xD800u
#define VID_STRIDE 40               // WIDTH(320)/8
#define VID_LINES  241

static uint8_t rom[ROM_SIZE];
static uint8_t ram[MEM_SIZE];
static int     mode = 0;            // memory view 0..3 (reset = 0)
static uint8_t portc = 0;           // 8255#0 Port C output latch

// --- instrumentation -------------------------------------------------------
static unsigned long out_count[256], in_count[256];
static uint8_t       out_last[256];
static int           out_seen[256], in_seen[256];
static unsigned long wpage[256];
static unsigned long mode_switches;

static void set_mode(int m) {
  if (m != mode) {
    fprintf(stderr, "[BANK] mode %d -> %d  (portC=0x%02X)\n", mode, m, portc);
    mode = m;
    mode_switches++;
  }
}

// is address a served by a ROM/expansion overlay in the current mode?
// out: *src = 0 RAM, 1 maincpu ROM (returns rom index in *idx), 2 expcart (empty)
static int overlay(uint16_t a, unsigned* idx) {
  switch (mode) {
    case 0: if (a <= 0x3FFF) { *idx = a; return 1; } return 0;
    case 1: if (a >= 0xD800) { *idx = 0x1800 + (a - 0xD800); return 1; } return 0;
    case 2: if (a >= 0x4000 && a <= 0xBFFF) return 2;
            if (a >= 0xD800) { *idx = 0x1800 + (a - 0xD800); return 1; } return 0;
    default: return 0;            // mode 3: all RAM
  }
}

static uint8_t rb(void* u, uint16_t a) {
  (void)u; unsigned idx = 0;
  int ov = overlay(a, &idx);
  if (ov == 1) return rom[idx];
  if (ov == 2) return 0xFF;        // no expansion cartridge present
  return ram[a];
}

static void wb(void* u, uint16_t a, uint8_t v) {
  (void)u; unsigned idx = 0;
  if (overlay(a, &idx)) return;    // write under ROM/expcart overlay -> dropped
  ram[a] = v;
  wpage[a >> 8]++;
}

static uint8_t pin(void* u, uint8_t p) {
  (void)u;
  if (!in_seen[p]) { in_seen[p] = 1; fprintf(stderr, "[IN ] first read  port 0x%02X\n", p); }
  in_count[p]++;
  return out_last[p];              // mimic 8255 output-latch readback; 0 if never written
}

static void pout(void* u, uint8_t p, uint8_t v) {
  (void)u;
  if (!out_seen[p]) { out_seen[p] = 1; fprintf(stderr, "[OUT] first write port 0x%02X = 0x%02X\n", p, v); }
  out_count[p]++;
  out_last[p] = v;

  // 8255#0 Port C controls the memory view (ports 0x04..0x07)
  if (p == 0x06) {                 // direct write to Port C
    portc = v;
    set_mode(portc & 0b11);
  } else if (p == 0x07) {          // 8255 control port
    if (v & 0x80) {                // mode-set command: outputs reset to 0
      portc = 0;
      set_mode(0);
    } else {                       // bit set/reset on Port C
      int bit = (v >> 1) & 7;
      if (v & 1) portc |= (1u << bit); else portc &= ~(1u << bit);
      set_mode(portc & 0b11);
    }
  }
}

int main(int argc, char** argv) {
  const char* rom_path = argc > 1 ? argv[1] : "ekta43.bin";
  unsigned long max_cyc = argc > 2 ? strtoul(argv[2], 0, 0) : 50000000UL;

  FILE* f = fopen(rom_path, "rb");
  if (!f) { perror(rom_path); return 1; }
  size_t n = fread(rom, 1, ROM_SIZE, f);
  fclose(f);
  fprintf(stderr, "loaded %zu bytes of ROM from %s\n", n, rom_path);

  i8080 cpu;
  i8080_init(&cpu);
  cpu.userdata = 0;
  cpu.read_byte = rb; cpu.write_byte = wb;
  cpu.port_in = pin;  cpu.port_out = pout;
  cpu.pc = 0x0000;

  unsigned long last_write_total = 0, writes_total, idle_cyc = 0;
  static uint32_t pchist[MEM_SIZE];

  while (cpu.cyc < max_cyc && !cpu.halted) {
    pchist[cpu.pc]++;
    i8080_step(&cpu);
    if ((cpu.cyc & 0xFFFFF) == 0) {
      writes_total = 0;
      for (int i = 0; i < 256; i++) writes_total += wpage[i];
      if (writes_total == last_write_total) {
        idle_cyc += 0x100000;
        if (idle_cyc > 4UL * 0x100000) {
          fprintf(stderr, "\n*** settled: no RAM writes ~4M cycles (idle at prompt?) ***\n");
          break;
        }
      } else { idle_cyc = 0; last_write_total = writes_total; }
    }
  }

  fprintf(stderr, "\nstopped pc=0x%04X cyc=%lu halted=%d iff=%d mode=%d switches=%lu\n",
          cpu.pc, cpu.cyc, cpu.halted, cpu.iff, mode, mode_switches);

  printf("\n==== OUT ports ====\n");
  for (int p = 0; p < 256; p++)
    if (out_count[p]) printf("  0x%02X : %8lu  last=0x%02X\n", p, out_count[p], out_last[p]);
  printf("\n==== IN ports ====\n");
  for (int p = 0; p < 256; p++)
    if (in_count[p]) printf("  0x%02X : %8lu reads\n", p, in_count[p]);

  printf("\n==== hottest PCs ====\n");
  for (int top = 0; top < 10; top++) {
    uint32_t best = 0; int bi = -1;
    for (int i = 0; i < (int)MEM_SIZE; i++) if (pchist[i] > best) { best = pchist[i]; bi = i; }
    if (bi < 0 || !best) break;
    printf("  0x%04X : %u\n", bi, best); pchist[bi] = 0;
  }

  printf("\n==== RAM write density (pages >0) ====\n");
  for (int pg = 0; pg < 256; pg++)
    if (wpage[pg]) printf("  0x%02X00 : %8lu\n", pg, wpage[pg]);

  // dump the video framebuffer (DRAM @ 0xD800) regardless of CPU bank
  FILE* o = fopen("vram.bin", "wb");
  if (o) { fwrite(&ram[VRAM_BASE], 1, (size_t)VID_STRIDE * VID_LINES, o); fclose(o);
           printf("\nwrote vram.bin (%d bytes, %dx%d @ 0x%04X)\n",
                  VID_STRIDE * VID_LINES, VID_STRIDE * 8, VID_LINES, VRAM_BASE); }
  return 0;
}
