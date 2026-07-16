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
// Optional expansion cartridge: set JUKU_CART=/path/to/image.{bin,hex}.
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
#include "juk_disk.h"
#include "juku_fdc.h"

#define MEM_SIZE   0x10000u
#define ROM_SIZE   0x4000u          // 16 KB
#define CART_SIZE  0x8000u          // 32 KB expansion window at 0x4000..0xBFFF
#define VRAM_BASE  0xD800u
#define VID_STRIDE 40               // WIDTH(320)/8
#define VID_LINES  241

static uint8_t rom[ROM_SIZE];
static uint8_t cart[CART_SIZE];
static uint8_t ram[MEM_SIZE];
static int     mode = 0;            // memory view 0..3 (reset = 0)
static uint8_t portc = 0;           // 8255#0 Port C output latch
static juk_disk disk;
static juku_fdc fdc;
static int      fdc_enabled = 0;
static int      cart_enabled = 0;

// --- instrumentation -------------------------------------------------------
static unsigned long out_count[256], in_count[256];
static uint8_t       out_last[256];
static int           out_seen[256], in_seen[256];
static unsigned long wpage[256];
static unsigned long mode_switches;
static unsigned long fdc_data_reads, stop_fdc_data_reads;
static int           timing_log = 0;
static int           io_trace = 0;

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

static FILE *rdtrace_fp = NULL;         // optional memory-read trace (JUKU_RDTRACE=path)
static unsigned long rdtrace_limit = 0; // stop tracing after N reads (JUKU_RDTRACE_LIMIT; 0 = unbounded)
static unsigned long rdtrace_n = 0;
static uint8_t rb(void* u, uint16_t a) {
  (void)u; unsigned idx = 0;
  uint8_t v;
  int ov = overlay(a, &idx);
  if (ov == 1) v = rom[idx];
  else if (ov == 2) v = cart_enabled ? cart[a - 0x4000] : 0xFF;
  else v = ram[a];
  if (rdtrace_fp) {
    fprintf(rdtrace_fp, "%04x %02x\n", a, v);
    if (rdtrace_limit && ++rdtrace_n >= rdtrace_limit) { fclose(rdtrace_fp); rdtrace_fp = NULL; }
  }
  return v;
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
static int   kbd_enabled = 0;
static uint8_t kbd_col = 0;         // last column selected (8255 Port A write)
static unsigned long kbd_start_vram = 42000;
static int kbd_hold_frames = 3;
static int kbd_gap_frames = 3;
#define KBD_HOLD 3
#define KBD_GAP  3

static int vram_pixel(int x, int y) {
  if (x < 0 || x >= VID_STRIDE * 8 || y < 0 || y >= VID_LINES) return 0;
  uint8_t byte = ram[VRAM_BASE + y * VID_STRIDE + (x >> 3)];
  return (byte >> (7 - (x & 7))) & 1;
}

static int ekdos_prompt_visible(void) {
  static const char* pattern[] = {
    "................",
    "....#......#....",
    "...#.#......#...",
    "..#...#......#..",
    "..#...#.......#.",
    "..#####......#..",
    "..#...#.....#...",
    "..#...#....#....",
    "................",
    "................",
  };
  const int ph = (int)(sizeof(pattern) / sizeof(pattern[0]));
  const int pw = 16;
  for (int y = 0; y <= VID_LINES - ph; y++) {
    for (int x = 0; x < 3; x++) {
      int ok = 1;
      for (int dy = 0; dy < ph && ok; dy++) {
        for (int dx = 0; dx < pw; dx++) {
          if (vram_pixel(x + dx, y + dy) != (pattern[dy][dx] == '#')) {
            ok = 0;
            break;
          }
        }
      }
      if (ok) return 1;
    }
  }
  return 0;
}

// Port B (0x05) value the BIOS reads: 74148-encode the pressed key in the selected column.
// Port B value: SHIFT bits 6/7 (active-LOW: 1=released) are GLOBAL (reflect the held key's
// shift regardless of column); the 74148 code (b1-3) + GS (b0, active-low) are per-column.
#define KBD_NONE 0xCF              // no key: code=7, GS released (b0=1), SHIFT released (b6/7=1)
static uint8_t kbd_portb(void) {
  if (g_vw < kbd_start_vram) return KBD_NONE;          // default waits until the ekta37 banner is drawn
  char c = (kbd_str && kbd_str[kbd_pos] && kbd_phase < kbd_hold_frames) ? kbd_str[kbd_pos] : 0;
  if (c == '|') return KBD_NONE;                       // prompt wait marker, not a typed key
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
  // The paging PROM controls read sources; /MEMW still reaches the populated
  // DRAM bank.  Monitor 3.7 relies on this write-behind behavior while its low
  // ROM overlay is active to build a return frame in the underlying page-zero
  // RAM before restoring the caller's mapping.
  ram[a] = v;
  wpage[a >> 8]++;
  if (a >= VRAM_BASE) {            // for CI: stop+dump after N video writes (match HDL)
    if (g_vw == 0) {
      unsigned long cyc = u ? ((i8080*)u)->cyc : 0;
      fprintf(stderr, "[VRAM] first video write @0x%04X cyc=%lu\n", a, cyc);
    }
    g_vw++;
  }
}

static uint8_t pin(void* u, uint8_t p) {
  if (!in_seen[p]) { in_seen[p] = 1; fprintf(stderr, "[IN ] first read  port 0x%02X\n", p); }
  if (timing_log && in_count[p] == 0) {
    i8080* cpu = (i8080*)u;
    fprintf(stderr, "[IOT] first IN  port 0x%02X cyc=%lu pc=%04X g_vw=%lu\n",
            p, cpu ? cpu->cyc : 0, cpu ? cpu->pc : 0, g_vw);
  }
  in_count[p]++;
  uint8_t value;
  if (p == 0x05 && kbd_enabled) value = kbd_portb();             // 8255 Port B = keyboard 74148
  else if (fdc_enabled && p >= 0x1C && p <= 0x1F) {
    value = juku_fdc_read(&fdc, p & 3);
    if (p == 0x1F) fdc_data_reads++;
  }
  else value = out_last[p];              // mimic 8255 output-latch readback; 0 if never written
  if (io_trace) {
    i8080* cpu = (i8080*)u;
    fprintf(stderr, "[IOSEQ] IN  port=0x%02X value=0x%02X cyc=%lu pc=%04X g_vw=%lu count=%lu\n",
            p, value, cpu ? cpu->cyc : 0, cpu ? cpu->pc : 0, g_vw, in_count[p]);
  }
  return value;
}

static void pout(void* u, uint8_t p, uint8_t v) {
  if (!out_seen[p]) { out_seen[p] = 1; fprintf(stderr, "[OUT] first write port 0x%02X = 0x%02X\n", p, v); }
  if (timing_log && out_count[p] == 0) {
    i8080* cpu = (i8080*)u;
    fprintf(stderr, "[IOT] first OUT port 0x%02X val=0x%02X cyc=%lu pc=%04X g_vw=%lu\n",
            p, v, cpu ? cpu->cyc : 0, cpu ? cpu->pc : 0, g_vw);
  }
  out_count[p]++;
  out_last[p] = v;
  if (io_trace) {
    i8080* cpu = (i8080*)u;
    fprintf(stderr, "[IOSEQ] OUT port=0x%02X value=0x%02X cyc=%lu pc=%04X g_vw=%lu count=%lu\n",
            p, v, cpu ? cpu->cyc : 0, cpu ? cpu->pc : 0, g_vw, out_count[p]);
  }
  if (fdc_enabled && p >= 0x1C && p <= 0x1F) juku_fdc_write(&fdc, p & 3, v);

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
    if (fdc_enabled) juku_fdc_portc(&fdc, portc);
    set_mode(portc & 0b11);
  } else if (p == 0x07) {          // 8255 control port
    if (v & 0x80) {                // mode-set command: outputs reset to 0
      portc = 0;
      if (fdc_enabled) juku_fdc_portc(&fdc, portc);
      set_mode(0);
    } else {                       // bit set/reset on Port C
      int bit = (v >> 1) & 7;
      if (v & 1) portc |= (1u << bit); else portc &= ~(1u << bit);
      if (fdc_enabled) juku_fdc_portc(&fdc, portc);
      set_mode(portc & 0b11);
    }
  }
}

static uint8_t sum_block(const uint8_t* r) {   // block-1 checksum (0x000B..0x07FF)
  unsigned s = 0; for (int i = 0x0B; i < 0x800; i++) s += r[i]; return s & 0xFF;
}

static int has_suffix(const char* path, const char* suffix) {
  size_t plen = strlen(path), slen = strlen(suffix);
  return plen >= slen && strcmp(path + plen - slen, suffix) == 0;
}

static size_t load_image(const char* path, uint8_t* dst, size_t cap, int fill) {
  memset(dst, fill, cap);
  FILE* f = fopen(path, "r");
  if (!f) { perror(path); exit(1); }
  size_t n = 0;
  if (has_suffix(path, ".hex")) {
    unsigned byte;
    while (n < cap && fscanf(f, "%x", &byte) == 1)
      dst[n++] = (uint8_t)byte;
  } else {
    fclose(f);
    f = fopen(path, "rb");
    if (!f) { perror(path); exit(1); }
    n = fread(dst, 1, cap, f);
  }
  fclose(f);
  return n;
}

static void dump_checkpoint(const char* prefix, const i8080* cpu) {
  if (!prefix || !prefix[0]) return;

  char ram_path[1024];
  char state_path[1024];
  snprintf(ram_path, sizeof(ram_path), "%s.ram", prefix);
  snprintf(state_path, sizeof(state_path), "%s.state", prefix);

  FILE* ram_out = fopen(ram_path, "wb");
  if (!ram_out) {
    perror(ram_path);
    exit(1);
  }
  fwrite(ram, 1, sizeof(ram), ram_out);
  fclose(ram_out);

  FILE* state_out = fopen(state_path, "w");
  if (!state_out) {
    perror(state_path);
    exit(1);
  }
  fprintf(state_out, "pc=%04X\n", cpu->pc);
  fprintf(state_out, "sp=%04X\n", cpu->sp);
  fprintf(state_out, "a=%02X\n", cpu->a);
  fprintf(state_out, "b=%02X\n", cpu->b);
  fprintf(state_out, "c=%02X\n", cpu->c);
  fprintf(state_out, "d=%02X\n", cpu->d);
  fprintf(state_out, "e=%02X\n", cpu->e);
  fprintf(state_out, "h=%02X\n", cpu->h);
  fprintf(state_out, "l=%02X\n", cpu->l);
  fprintf(state_out, "sf=%u\n", cpu->sf ? 1 : 0);
  fprintf(state_out, "zf=%u\n", cpu->zf ? 1 : 0);
  fprintf(state_out, "hf=%u\n", cpu->hf ? 1 : 0);
  fprintf(state_out, "pf=%u\n", cpu->pf ? 1 : 0);
  fprintf(state_out, "cf=%u\n", cpu->cf ? 1 : 0);
  fprintf(state_out, "iff=%u\n", cpu->iff ? 1 : 0);
  fprintf(state_out, "halted=%u\n", cpu->halted ? 1 : 0);
  fprintf(state_out, "interrupt_pending=%u\n", cpu->interrupt_pending ? 1 : 0);
  fprintf(state_out, "interrupt_vector=%02X\n", cpu->interrupt_vector);
  fprintf(state_out, "interrupt_delay=%02X\n", cpu->interrupt_delay);
  fprintf(state_out, "cyc=%lu\n", cpu->cyc);
  fprintf(state_out, "vram_writes=%lu\n", g_vw);
  fprintf(state_out, "mode=%d\n", mode);
  fprintf(state_out, "portc=%02X\n", portc);
  fprintf(state_out, "mode_switches=%lu\n", mode_switches);
  fprintf(state_out, "kbd_pos=%d\n", kbd_pos);
  fprintf(state_out, "kbd_phase=%d\n", kbd_phase);
  fprintf(state_out, "kbd_col=%02X\n", kbd_col);
  fprintf(state_out, "pic_icw1=%02X\n", pic_icw1);
  fprintf(state_out, "pic_icw2=%02X\n", pic_icw2);
  fprintf(state_out, "pic_mask=%02X\n", pic_mask);
  fprintf(state_out, "pic_expect_icw2=%d\n", pic_expect_icw2);
  fprintf(state_out, "fdc_enabled=%d\n", fdc_enabled);
  fprintf(state_out, "fdc_head=%d\n", fdc.head);
  fprintf(state_out, "fdc_drive=%d\n", fdc.drive);
  fprintf(state_out, "fdc_motor_on=%d\n", fdc.motor_on);
  fprintf(state_out, "fdc_status=%02X\n", fdc.status);
  fprintf(state_out, "fdc_track=%02X\n", fdc.track);
  fprintf(state_out, "fdc_sector=%02X\n", fdc.sector);
  fprintf(state_out, "fdc_data=%02X\n", fdc.data);
  fprintf(state_out, "fdc_command=%02X\n", fdc.command);
  fprintf(state_out, "fdc_buffer_pos=%u\n", fdc.buffer_pos);
  fprintf(state_out, "fdc_buffer_len=%u\n", fdc.buffer_len);
  fprintf(state_out, "fdc_data_reads=%lu\n", fdc_data_reads);
  for (int p = 0; p < 256; p++) {
    if (out_count[p] || in_count[p] || out_last[p])
      fprintf(state_out, "port_%02X=last:%02X,out:%lu,in:%lu\n",
              p, out_last[p], out_count[p], in_count[p]);
  }
  fclose(state_out);
  fprintf(stderr, "[CHECKPOINT] wrote %s and %s\n", ram_path, state_path);
}

int main(int argc, char** argv) {
  const char* rom_path = argc > 1 ? argv[1] : "ekta43.bin";
  unsigned long max_cyc = argc > 2 ? strtoul(argv[2], 0, 0) : 50000000UL;
  g_vw_limit            = argc > 3 ? strtoul(argv[3], 0, 0) : 0UL;   // 0 = no video-write limit
  unsigned long frame_cyc = argc > 4 ? strtoul(argv[4], 0, 0) : 0UL; // frame-interrupt period (cycles); 0 = off
  const char* checkpoint_cyc_env = getenv("JUKU_CHECKPOINT_CYC");
  unsigned long checkpoint_cyc = (checkpoint_cyc_env && checkpoint_cyc_env[0]) ? strtoul(checkpoint_cyc_env, 0, 0) : 0UL;
  unsigned long next_frame = frame_cyc;
  kbd_str = getenv("JUKU_KEYS");     // keystrokes to type (needs frame interrupt on); unset = keyboard off
  const char* kbd_enabled_env = getenv("JUKU_KEYBOARD_ENABLE");
  kbd_enabled = (kbd_str && kbd_str[0]) ||
                (kbd_enabled_env && kbd_enabled_env[0] && strcmp(kbd_enabled_env, "0") != 0);
  const char* kbd_start_vram_env = getenv("JUKU_KEY_START_VRAM");
  if (kbd_start_vram_env && kbd_start_vram_env[0]) kbd_start_vram = strtoul(kbd_start_vram_env, 0, 0);
  const char* kbd_hold_env = getenv("JUKU_KEY_HOLD_FRAMES");
  if (kbd_hold_env && kbd_hold_env[0]) kbd_hold_frames = atoi(kbd_hold_env);
  const char* kbd_gap_env = getenv("JUKU_KEY_GAP_FRAMES");
  if (kbd_gap_env && kbd_gap_env[0]) kbd_gap_frames = atoi(kbd_gap_env);
  if (kbd_hold_frames < 1) kbd_hold_frames = KBD_HOLD;
  if (kbd_gap_frames < 1) kbd_gap_frames = KBD_GAP;
  const char* stop_fdc_data_reads_env = getenv("JUKU_STOP_FDC_DATA_READS");
  if (stop_fdc_data_reads_env && stop_fdc_data_reads_env[0])
    stop_fdc_data_reads = strtoul(stop_fdc_data_reads_env, 0, 0);
  const char* rdtrace_path = getenv("JUKU_RDTRACE");
  if (rdtrace_path && rdtrace_path[0]) {
    rdtrace_fp = fopen(rdtrace_path, "w");
    if (!rdtrace_fp) fprintf(stderr, "JUKU_RDTRACE=%s could not be opened for writing\n", rdtrace_path);
    const char* rdtrace_limit_env = getenv("JUKU_RDTRACE_LIMIT");
    if (rdtrace_limit_env && rdtrace_limit_env[0]) rdtrace_limit = strtoul(rdtrace_limit_env, 0, 0);
  }
  const char* cart_path = getenv("JUKU_CART");
  timing_log = getenv("JUKU_TRACE_TIMING") && getenv("JUKU_TRACE_TIMING")[0] &&
               strcmp(getenv("JUKU_TRACE_TIMING"), "0") != 0;
  io_trace = getenv("JUKU_TRACE_IO") && getenv("JUKU_TRACE_IO")[0] &&
             strcmp(getenv("JUKU_TRACE_IO"), "0") != 0;
  if (cart_path && cart_path[0]) {
    size_t cn = load_image(cart_path, cart, CART_SIZE, 0xFF);
    cart_enabled = 1;
    fprintf(stderr, "loaded %zu bytes of expansion cartridge from %s\n", cn, cart_path);
  } else {
    memset(cart, 0xFF, sizeof(cart));
  }
  const char* disk_path = getenv("JUKU_DISK");
  if (disk_path && disk_path[0]) {
    const char* writable_env = getenv("JUKU_DISK_WRITABLE");
    int disk_writable = writable_env && writable_env[0] && strcmp(writable_env, "0") != 0;
    int rc = disk_writable ? juk_disk_open_writable(&disk, disk_path)
                           : juk_disk_open(&disk, disk_path);
    if (rc != 0) {
      fprintf(stderr, "JUKU_DISK=%s could not be opened as a raw Juku disk image (rc=%d)\n", disk_path, rc);
      return 2;
    }
    juku_fdc_init(&fdc, &disk);
    fdc_enabled = 1;
    fprintf(stderr, "loaded JUKU disk image %s (%ld bytes, %d side%s, %s)\n",
            disk_path, disk.size, disk.heads, disk.heads == 1 ? "" : "s",
            disk_writable ? "writable" : "read-only");
  }

  size_t n = load_image(rom_path, rom, ROM_SIZE, 0x00);
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
  cpu.userdata = &cpu;
  cpu.read_byte = rb; cpu.write_byte = wb;
  cpu.port_in = pin;  cpu.port_out = pout;
  cpu.pc = 0x0000;

  unsigned long last_write_total = 0, writes_total, idle_cyc = 0;
  static uint32_t pchist[MEM_SIZE];

  int chk_logs = 0;
  while (cpu.cyc < max_cyc && (!cpu.halted || frame_cyc) &&
         !(g_vw_limit && g_vw >= g_vw_limit) &&
         !(checkpoint_cyc && cpu.cyc >= checkpoint_cyc) &&
         !(stop_fdc_data_reads && fdc_data_reads >= stop_fdc_data_reads)) {
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
        static int irq_n = 0;
        if (irq_n++ < 3) fprintf(stderr, "[IRQ] taken #%d g_vw=%lu cyc=%lu pc=%04X icw1=%02X icw2=%02X mask=%02X vec=%04X\n",
            irq_n, g_vw, cpu.cyc, cpu.pc, pic_icw1, pic_icw2, pic_mask,
            ((uint16_t)pic_icw2<<8)|(pic_icw1&0xE0)|(5u<<2));
        uint16_t vec = ((uint16_t)pic_icw2 << 8) | (pic_icw1 & 0xE0) | (5u << 2);
        if (cpu.halted) cpu.halted = 0;              // interrupt wakes a HLT
        wb(0, (uint16_t)(cpu.sp - 1), cpu.pc >> 8);  // CALL: push PC, jump to vector
        wb(0, (uint16_t)(cpu.sp - 2), cpu.pc & 0xFF);
        cpu.sp -= 2; cpu.iff = 0; cpu.pc = vec;
      }
      // advance the typed-keystroke state once per frame (HOLD pressed, GAP released)
      if (kbd_str && kbd_str[kbd_pos] && g_vw >= kbd_start_vram) {
        if (kbd_str[kbd_pos] == '|') {
          if (ekdos_prompt_visible()) {
            fprintf(stderr, "[KBD] prompt wait marker consumed at g_vw=%lu cyc=%lu pos=%d\n",
                    g_vw, cpu.cyc, kbd_pos);
            kbd_phase = 0;
            kbd_pos++;
          }
        } else if (++kbd_phase >= kbd_hold_frames + kbd_gap_frames) {
          kbd_phase = 0;
          kbd_pos++;
        }
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
  if (stop_fdc_data_reads && fdc_data_reads >= stop_fdc_data_reads)
    fprintf(stderr, "[FDC] stopped after %lu data reads at cyc=%lu pc=%04X g_vw=%lu\n",
            fdc_data_reads, cpu.cyc, cpu.pc, g_vw);

  dump_checkpoint(getenv("JUKU_CHECKPOINT_PREFIX"), &cpu);

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
  if (fdc_enabled) juk_disk_close(&disk);
  return 0;
}
