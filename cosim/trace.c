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
// IN ports return the 8255 output latch (no key). Interrupts not modelled.
//
// STATUS: boots the real BIOS and draws the banner to VRAM. The long-standing
// stall was the ROM self-test checksum loop (0x042C/0x0443), NOT the keyboard.
//   - ekta37.bin (official) boots cleanly -> banner (render vram.bin at stride 40).
//   - ekta43.bin (homebrew AT-kbd) has a STALE block-1 checksum (0x000A=0xF2 but
//     bytes 0x000B..0x07FF sum to 0x57); patched at load so it boots too. All 5
//     official ekta ROMs pass block-1; only ekta43 fails (confirms our checksum).
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

static unsigned long g_vw = 0, g_vw_limit = 0;   // video-RAM write count + optional stop limit
// --- minimal 8259 PIC (MCS-80/CALL mode) for the frame interrupt (ports 0x00/0x01) ---
static uint8_t pic_icw1 = 0, pic_icw2 = 0, pic_mask = 0xFF;  // mask: 1=masked
static int     pic_expect_icw2 = 0;

// --- keyboard (opt-in via env JUKU_KEYS): matrix scan via 8255 PortA(col)/PortB(74148) ---
// char -> (column 0-15, bit 0-7); from MAME juku COL.0..14. Uppercase via SHIFT.
static const struct { char c; uint8_t col, bit; } KMAP[] = {
  {'a',5,5},{'b',4,1},{'c',6,1},{'d',6,5},{'e',6,3},{'f',2,5},{'g',4,5},{'h',0,5},
  {'i',14,3},{'j',7,5},{'k',14,5},{'l',13,5},{'m',7,1},{'n',0,1},{'o',13,3},{'p',12,3},
  {'q',5,3},{'r',2,3},{'s',1,5},{'t',4,3},{'u',7,3},{'v',2,1},{'w',1,3},{'x',1,1},
  {'y',0,3},{'z',5,1},
  {'0',12,4},{'1',5,4},{'2',1,4},{'3',6,4},{'4',2,4},{'5',4,4},{'6',0,4},{'7',7,4},{'8',14,4},{'9',13,4},
  {' ',11,2},{'\r',8,5},{'\n',8,5},
  {'.',13,1},{',',14,1},{'/',12,1},{';',11,1},{'-',11,4},{':',10,5},
};
static const char* kbd_str = 0;     // keystrokes to "type" (0/empty = keyboard off)
static int   kbd_pos = 0, kbd_phase = 0;
static uint8_t kbd_col = 0;         // last column selected (8255 Port A write)
#define KBD_HOLD 3
#define KBD_GAP  3

// Port B (0x05) value the BIOS reads: 74148-encode the pressed key in the selected column.
// Port B value: SHIFT bits 6/7 (active-LOW: 1=released) are GLOBAL (reflect the held key's
// shift regardless of column); the 74148 code (b1-3) + GS (b0, active-low) are per-column.
#define KBD_NONE 0xCF              // no key: code=7, GS released (b0=1), SHIFT released (b6/7=1)
static uint8_t kbd_portb(void) {
  if (g_vw < 42000) return KBD_NONE;                   // wait until the banner is drawn
  char c = (kbd_str && kbd_str[kbd_pos] && kbd_phase < KBD_HOLD) ? kbd_str[kbd_pos] : 0;
  int shift = 0, col = -1, bit = -1;
  if (c) {
    char lc = c; if (c >= 'A' && c <= 'Z') { lc = (char)(c + 32); shift = 1; }
    for (unsigned i = 0; i < sizeof(KMAP)/sizeof(KMAP[0]); i++)
      if (KMAP[i].c == lc) { col = KMAP[i].col; bit = KMAP[i].bit; break; }
  }
  uint8_t pb = 0xC0;                                   // SHIFT bits released (active-low high)
  if (shift) pb &= (uint8_t)~0x40;                     // SHIFT1 held = bit6 low (active-low)
  if (c && col == kbd_col)
    pb |= (uint8_t)(((~bit) & 7) << 1);                // 74148 code in b1-3, GS active (b0=0)
  else
    pb |= 0x0F;                                        // no key here: code=7 + GS released (b0=1)
  return pb;
}
static void wb(void* u, uint16_t a, uint8_t v) {
  (void)u; unsigned idx = 0;
  if (overlay(a, &idx)) return;    // write under ROM/expcart overlay -> dropped
  ram[a] = v;
  wpage[a >> 8]++;
  if (a >= VRAM_BASE) g_vw++;      // for CI: stop+dump after N video writes (match HDL)
}

static uint8_t pin(void* u, uint8_t p) {
  (void)u;
  if (!in_seen[p]) { in_seen[p] = 1; fprintf(stderr, "[IN ] first read  port 0x%02X\n", p); }
  in_count[p]++;
  if (p == 0x05 && kbd_str && kbd_str[0]) return kbd_portb();   // 8255 Port B = keyboard 74148
  return out_last[p];              // mimic 8255 output-latch readback; 0 if never written
}

static void pout(void* u, uint8_t p, uint8_t v) {
  (void)u;
  if (!out_seen[p]) { out_seen[p] = 1; fprintf(stderr, "[OUT] first write port 0x%02X = 0x%02X\n", p, v); }
  out_count[p]++;
  out_last[p] = v;

  if (p == 0x04) kbd_col = v & 0x0F;   // 8255 Port A low nibble = keyboard column select

  // 8259 PIC programming (port 0x00 = A0=0, port 0x01 = A0=1)
  if (p == 0x00) { if (v & 0x10) { pic_icw1 = v; pic_expect_icw2 = 1; } }   // ICW1
  else if (p == 0x01) {
    if (pic_expect_icw2) { pic_icw2 = v; pic_expect_icw2 = 0; }             // ICW2 (vector hi)
    else pic_mask = v;                                                       // OCW1 (mask)
  }

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

static uint8_t sum_block(const uint8_t* r) {   // block-1 checksum (0x000B..0x07FF)
  unsigned s = 0; for (int i = 0x0B; i < 0x800; i++) s += r[i]; return s & 0xFF;
}

int main(int argc, char** argv) {
  const char* rom_path = argc > 1 ? argv[1] : "ekta43.bin";
  unsigned long max_cyc = argc > 2 ? strtoul(argv[2], 0, 0) : 50000000UL;
  g_vw_limit            = argc > 3 ? strtoul(argv[3], 0, 0) : 0UL;   // 0 = no video-write limit
  unsigned long frame_cyc = argc > 4 ? strtoul(argv[4], 0, 0) : 0UL; // frame-interrupt period (cycles); 0 = off
  unsigned long next_frame = frame_cyc;
  kbd_str = getenv("JUKU_KEYS");     // keystrokes to type (needs frame interrupt on); unset = keyboard off

  FILE* f = fopen(rom_path, "rb");
  if (!f) { perror(rom_path); return 1; }
  size_t n = fread(rom, 1, ROM_SIZE, f);
  fclose(f);
  fprintf(stderr, "loaded %zu bytes of ROM from %s\n", n, rom_path);

  // ekta43.bin (homebrew AT-kbd mod) has a STALE block-1 checksum: bytes
  // 0x000B..0x07FF sum to 0x57 but the stored checksum at 0x000A is 0xF2, so the
  // ROM self-test fails and retries forever. Patch the stored byte to boot.
  if (rom[0x0A] == 0xF2 && (sum_block(rom) == 0x57)) {
    rom[0x0A] = 0x57;
    fprintf(stderr, "[PATCH] ekta43 block-1 checksum 0x000A: 0xF2 -> 0x57 (stale homebrew checksum)\n");
  }

  i8080 cpu;
  i8080_init(&cpu);
  cpu.userdata = 0;
  cpu.read_byte = rb; cpu.write_byte = wb;
  cpu.port_in = pin;  cpu.port_out = pout;
  cpu.pc = 0x0000;

  unsigned long last_write_total = 0, writes_total, idle_cyc = 0;
  static uint32_t pchist[MEM_SIZE];

  int chk_logs = 0;
  while (cpu.cyc < max_cyc && (!cpu.halted || frame_cyc) && !(g_vw_limit && g_vw >= g_vw_limit)) {
    pchist[cpu.pc]++;
    if (cpu.pc == 0x03E0 && chk_logs < 12)            // checksum entry: HL=ptr, DE=count
      fprintf(stderr, "[CHK] entry HL=%04X DE=%04X mode=%d\n",
              (cpu.h<<8)|cpu.l, (cpu.d<<8)|cpu.e, mode);
    if (cpu.pc == 0x03E6 && chk_logs++ < 12)           // compare: A=stored, B=computed
      fprintf(stderr, "[CHK] cmp computed=%02X stored=%02X %s\n",
              cpu.b, cpu.a, cpu.b==cpu.a ? "OK" : "**MISMATCH**");
    i8080_step(&cpu);
    // --- frame interrupt: 8253 VER-RTR -> 8259 IR5 -> CPU (MCS-80 CALL to the ICW vector) ---
    if (frame_cyc && cpu.cyc >= next_frame) {
      next_frame += frame_cyc;
      if (cpu.iff && !(pic_mask & 0x20)) {           // IFF set + IR5 unmasked
        uint16_t vec = ((uint16_t)pic_icw2 << 8) | (pic_icw1 & 0xE0) | (5u << 2);
        if (cpu.halted) cpu.halted = 0;              // interrupt wakes a HLT
        wb(0, (uint16_t)(cpu.sp - 1), cpu.pc >> 8);  // CALL: push PC, jump to vector
        wb(0, (uint16_t)(cpu.sp - 2), cpu.pc & 0xFF);
        cpu.sp -= 2; cpu.iff = 0; cpu.pc = vec;
      }
      // advance the typed-keystroke state once per frame (HOLD pressed, GAP released)
      if (kbd_str && kbd_str[kbd_pos] && g_vw >= 42000) {
        if (++kbd_phase >= KBD_HOLD + KBD_GAP) { kbd_phase = 0; kbd_pos++; }
      }
    }
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
