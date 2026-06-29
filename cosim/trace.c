// Traced 8080 boot harness for the Juku (ekta43.bin).
//
// Goal: run the ROM from reset and DISCOVER the machine empirically --
//   - which I/O ports it touches (OUT = control, IN = status/keyboard)
//   - where in RAM it writes heavily (the video framebuffer)
//   - whether it tries to write into the ROM region (=> ROM/RAM banking)
//
// We assume as little as possible:
//   ROM: 0x0000..0x3FFF (16K, read-only here; writes are LOGGED not applied)
//   RAM: 0x4000..0xFFFF (read/write)
//   All IN ports return 0x00 ("no key / not ready") so the banner prints and
//   the machine should come to rest at the boot prompt instead of running off.
//
// Build: cc -O2 -o trace trace.c i8080.c
// Run:   ./trace /path/to/ekta43.bin [max_cycles]

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "i8080.h"

#define ROM_END   0x4000u          // ROM occupies [0, ROM_END)
#define MEM_SIZE  0x10000u

static uint8_t mem[MEM_SIZE];

// --- instrumentation -------------------------------------------------------
static unsigned long out_count[256], in_count[256];
static uint8_t       out_last[256];
static int           out_seen[256], in_seen[256];
static unsigned long wpage[256];          // writes per 256-byte page (RAM)
static unsigned long rom_write_attempts;  // writes aimed at ROM region
static uint16_t      rom_write_lo = 0xFFFF, rom_write_hi = 0;

static uint8_t rb(void* u, uint16_t a) {
  (void)u;
  return mem[a];
}

static void wb(void* u, uint16_t a, uint8_t v) {
  (void)u;
  if (a < ROM_END) {                       // write into ROM region: notable
    rom_write_attempts++;
    if (a < rom_write_lo) rom_write_lo = a;
    if (a > rom_write_hi) rom_write_hi = a;
    return;                                 // do NOT apply (ROM is read-only)
  }
  mem[a] = v;
  wpage[a >> 8]++;
}

static uint8_t pin(void* u, uint8_t p) {
  (void)u;
  if (!in_seen[p]) { in_seen[p] = 1; fprintf(stderr, "[IN ] first read  port 0x%02X\n", p); }
  in_count[p]++;
  return 0x00;                             // no key pressed / not ready
}

static void pout(void* u, uint8_t p, uint8_t v) {
  (void)u;
  if (!out_seen[p]) { out_seen[p] = 1; fprintf(stderr, "[OUT] first write port 0x%02X = 0x%02X\n", p, v); }
  out_count[p]++;
  out_last[p] = v;
}

int main(int argc, char** argv) {
  const char* rom_path = argc > 1 ? argv[1] : "ekta43.bin";
  unsigned long max_cyc = argc > 2 ? strtoul(argv[2], 0, 0) : 50000000UL;

  FILE* f = fopen(rom_path, "rb");
  if (!f) { perror(rom_path); return 1; }
  size_t n = fread(mem, 1, MEM_SIZE, f);
  fclose(f);
  fprintf(stderr, "loaded %zu bytes from %s\n", n, rom_path);

  i8080 cpu;
  i8080_init(&cpu);
  cpu.userdata = 0;
  cpu.read_byte = rb;
  cpu.write_byte = wb;
  cpu.port_in = pin;
  cpu.port_out = pout;
  cpu.pc = 0x0000;

  // Detect "settled at prompt": a long stretch with no RAM writes while we keep
  // hitting IN ports => the ROM is idling in its key-wait loop.
  unsigned long last_write_total = 0, writes_total = 0;
  unsigned long idle_cyc = 0;
  static uint32_t pchist[MEM_SIZE];

  while (cpu.cyc < max_cyc && !cpu.halted) {
    pchist[cpu.pc]++;
    i8080_step(&cpu);

    writes_total = 0;
    // cheap: recompute only occasionally
    if ((cpu.cyc & 0xFFFFF) == 0) {        // ~every 1M cycles
      for (int i = 0; i < 256; i++) writes_total += wpage[i];
      if (writes_total == last_write_total) {
        idle_cyc += 0x100000;
        if (idle_cyc > 4UL * 0x100000) {   // ~4M cycles with zero new writes
          fprintf(stderr, "\n*** settled: no RAM writes for ~4M cycles "
                          "(banner likely done, idling at prompt) ***\n");
          break;
        }
      } else {
        idle_cyc = 0;
        last_write_total = writes_total;
      }
    }
  }

  fprintf(stderr, "\nstopped at pc=0x%04X cyc=%lu halted=%d iff(int.enabled)=%d\n",
          cpu.pc, cpu.cyc, cpu.halted, cpu.iff);

  // hottest PCs = the loop it's stuck in
  printf("\n==== hottest PCs (the spin loop) ====\n");
  for (int top = 0; top < 12; top++) {
    uint32_t best = 0; int bi = -1;
    for (int i = 0; i < (int)MEM_SIZE; i++) if (pchist[i] > best) { best = pchist[i]; bi = i; }
    if (bi < 0 || best == 0) break;
    printf("  pc=0x%04X : %u hits\n", bi, best);
    pchist[bi] = 0;
  }

  // ---- report ----
  printf("\n==== OUT ports (control) ====\n");
  for (int p = 0; p < 256; p++)
    if (out_count[p]) printf("  port 0x%02X : %8lu writes, last=0x%02X\n", p, out_count[p], out_last[p]);

  printf("\n==== IN ports (status/keyboard) ====\n");
  for (int p = 0; p < 256; p++)
    if (in_count[p]) printf("  port 0x%02X : %8lu reads\n", p, in_count[p]);

  printf("\n==== ROM-region write attempts ====\n");
  if (rom_write_attempts)
    printf("  %lu writes aimed at 0x%04X..0x%04X  => ROM/RAM BANKING likely!\n",
           rom_write_attempts, rom_write_lo, rom_write_hi);
  else
    printf("  none (ROM region never written -- simple map holds)\n");

  printf("\n==== RAM write density (256-byte pages, >0) ====\n");
  unsigned long max_run_writes = 0; int run_lo = -1, best_lo = -1, best_hi = -1;
  unsigned long run_writes = 0; int prev = -2;
  for (int pg = 0; pg < 256; pg++) {
    if (wpage[pg]) {
      printf("  0x%02X00-0x%02XFF : %8lu\n", pg, pg, wpage[pg]);
      if (pg != prev + 1) { run_lo = pg; run_writes = 0; }
      run_writes += wpage[pg];
      if (run_writes > max_run_writes) { max_run_writes = run_writes; best_lo = run_lo; best_hi = pg; }
      prev = pg;
    }
  }
  if (best_lo >= 0)
    printf("\n  heaviest contiguous write region: 0x%02X00..0x%02XFF (%lu writes)"
           "  <-- VRAM candidate\n", best_lo, best_hi, max_run_writes);

  // dump the VRAM candidate so we can try to render the banner next
  if (best_lo >= 0) {
    char path[256];
    snprintf(path, sizeof path, "vram_%02X00-%02XFF.bin", best_lo, best_hi);
    FILE* o = fopen(path, "wb");
    if (o) {
      fwrite(&mem[best_lo << 8], 1, (size_t)((best_hi - best_lo + 1) << 8), o);
      fclose(o);
      printf("  wrote %s (%d bytes)\n", path, (best_hi - best_lo + 1) << 8);
    }
  }
  return 0;
}
