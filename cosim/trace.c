#define _XOPEN_SOURCE 600

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
// IN ports return the 8255 output latch when no device owns the read.  The
// functional PIC path covers frame, 8251 RxRDY, and 8251 TxRDY interrupts.
// Optional expansion cartridge: set JUKU_CART=/path/to/image.{bin,hex}.
//
// STATUS: boots the real BIOS and draws the banner to VRAM. The long-standing
// stall was the ROM self-test checksum loop (0x042C/0x0443), NOT the keyboard.
//   - ekta37.bin (official) boots cleanly -> banner (render vram.bin at stride 40).
//   - ekta43.bin (homebrew AT-kbd) has a STALE block-1 checksum (0x000A=0xF2 but
//     bytes 0x000B..0x07FF sum to 0x57); patched at load so it boots too. All 5
//     official ekta ROMs pass block-1; only ekta43 fails (confirms our checksum).
//
// Build: cc -O2 -o trace trace.c i8080.c juk_disk.c juku_fdc.c
// Run:   ./trace /path/to/ekta43.bin [max_cycles]
// USART: JUKU_USART_PTY=auto prints a new slave path; a host-created PTY path
//        may be supplied instead. JUKU_USART_TRANSFER_CYCLES controls the
//        holding-to-shift delay; JUKU_USART_BYTE_CYCLES controls frame time.
//        JUKU_STOP_PC=ADDR stops before executing ADDR after at least
//        JUKU_STOP_PC_AFTER_USART_RX bytes (useful for network-load proofs).
//        JUKU_USART_FAULT=tx_stuck accepts each post-reset byte and then holds
//        the transmit input register full until the next 8251 reset;
//        tx_stuck_once:BYTE jams one matching write until an 8251 reset;
//        tx_not_ready_once_after:COUNT jams between completed output bytes;
//        tx_empty_low_after:COUNT holds only status bit 2 low thereafter;
//        rx_irq_delay_once_after:COUNT:CYCLES delays one RxRDY interrupt long
//        enough to model a phase-sensitive ISR/overrun boundary.
// RAM:   JUKU_RAM_FAULT=ADDR:STUCK_LOW:STUCK_HIGH injects one faulty byte
//        (ADDR=* applies the stuck masks globally);
//        JUKU_RAM_ALIAS=PAGE_A:PAGE_B maps logical PAGE_B onto PAGE_A.
//        JUKU_DRAM_RETENTION_CYCLES=N deterministically inverts a complete
//        4164 refresh row if it receives no RAM access for more than N cycles.
//        Juku presents CPU A0..A6 to DRAM MA0..MA6 while /RAS is active;
//        A7/MA7 is a column-only don't-care for 128-cycle refresh.
//        JUKU_DRAM_RETENTION_ARM_PC=ADDR delays that model until the first
//        instruction at ADDR (useful when omitted video refresh is out of
//        scope and the ROM refresh service is the subject of the test).
// EXEC:  JUKU_ROM_EXEC_RESET_AT=ADDR resets the CPU whenever a ROM fetch
//        reaches ADDR or above (used to model the physical D15 A12 boundary).
// CPU:   JUKU_CPU_A12_INCREMENT_FAULT=1 makes D1's 16-bit +1 path lose an
//        already-high A12. It covers PC, INX, LHLD/SHLD, POP, and boundaries.
// ROM:   JUKU_ROM_CONSECUTIVE_A12_LOW=1 retains the older ROM-local model.
// EXEC:  JUKU_EXEC_BYTE_FAULT=ADDR:VALUE overrides an instruction-stream byte
//        when the CPU PC has just advanced past ADDR; ordinary data reads pass.
// PIC:   JUKU_PIC_FAULT=STUCK_LOW:STUCK_HIGH faults the 8259 IMR readback.
// PPI:   JUKU_PPI_FAULT=PORT:STUCK_LOW:STUCK_HIGH faults D27 port readback.
// PIT:   JUKU_PIT_FAULT=PORT:STUCK_LOW:STUCK_HIGH faults D54/D55/D57 count reads.
// TERM:  JUKU_CONSOLE_PTY=auto|/dev/ttyN attaches an interactive terminal.
//        Characters the firmware writes through the ROM's WRCHR vector are
//        echoed to it, and bytes typed into it are queued as keystrokes for
//        the emulated key matrix, so `screen /dev/ttysNNN` drives the machine.
//        JUKU_CONSOLE_OUT_PC / JUKU_CONSOLE_IN_PC override the hooked ROM
//        vectors (defaults FFD9h/FFD3h, the EktaSoft monitor entries that
//        cpmish's BIOS CONOUT/CONIN call). This is a simulator affordance:
//        the real machine's console is its bitmap screen and key matrix.
// SPEED: JUKU_REALTIME_HZ=N paces execution to N simulated cycles per real
//        second, so wall-clock time equals machine time (use 2000000 for the
//        nominal Juku clock; "1" is accepted as shorthand for it). Unset means
//        run as fast as possible, which is the right default for tests.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>
#include "i8080.h"

static volatile sig_atomic_t terminate_requested;

static void request_termination(int signal_number) {
  (void)signal_number;
  terminate_requested = 1;
}
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
static int      fdc_bus_invert = 0;
static int      cart_enabled = 0;
static int      rom_consecutive_a12_low = 0;
static unsigned rom_read_burst_count = 0;
static int      cpu_a12_increment_fault = 0;
static int      exec_byte_fault_enabled = 0;
static uint16_t exec_byte_fault_addr = 0;
static uint8_t  exec_byte_fault_value = 0;

// --- instrumentation -------------------------------------------------------
static unsigned long out_count[256], in_count[256];
static uint8_t       out_last[256];
static int           out_seen[256], in_seen[256];
static unsigned long wpage[256];
static unsigned long mode_switches;
static unsigned long fdc_data_reads, stop_fdc_data_reads;
static unsigned long fdc_last_cyc;
static int           timing_log = 0;
static int           io_trace = 0;
static int           bank_trace = 1;
static int           ram_fault_enabled = 0;
static uint16_t      ram_fault_addr = 0;
static uint8_t       ram_fault_stuck_low = 0;
static uint8_t       ram_fault_stuck_high = 0;
static int           ram_fault_all = 0;
static int           ram_drop_write_enabled = 0;
static uint16_t      ram_drop_write_addr = 0;
static uint8_t       ram_drop_write_value = 0;
static unsigned      ram_drop_write_remaining = 0;
static int           ram_alias_enabled = 0;
static uint8_t       ram_alias_page_a = 0;
static uint8_t       ram_alias_page_b = 0;
static unsigned long dram_retention_cycles = 0;
static unsigned long dram_last_refresh[128];
static int           dram_retention_armed = 1;
static int           dram_retention_arm_pc_enabled = 0;
static uint16_t      dram_retention_arm_pc = 0;
static unsigned long dram_decay_count = 0;
static uint8_t dram_coverage_seen[128];
static unsigned dram_coverage_count = 0;
static unsigned long dram_coverage_start = 0;
static int dram_full_coverage_reported = 0;
static int           pic_fault_enabled = 0;
static uint8_t       pic_fault_stuck_low = 0;
static uint8_t       pic_fault_stuck_high = 0;
static int           ppi_fault_enabled = 0;
static uint8_t       ppi_fault_port = 0;
static uint8_t       ppi_fault_stuck_low = 0;
static uint8_t       ppi_fault_stuck_high = 0;
static int           pit_fault_enabled = 0;
static uint8_t       pit_fault_port = 0;
static uint8_t       pit_fault_stuck_low = 0;
static uint8_t       pit_fault_stuck_high = 0;

// --- minimal 8253 register/load/latch model -------------------------------
// This preserves the software-visible count-register protocol needed by the
// diagnostic ROM. It intentionally does not synthesize the three board PITs'
// distinct/cascaded clock domains; HDL remains authoritative for live timing.
typedef struct {
  uint16_t count_register;
  uint16_t write_latch;
  uint16_t output_latch;
  uint8_t access;
  uint8_t write_phase;
  uint8_t read_phase;
  uint8_t latch_valid;
  uint8_t bcd;
  uint8_t mode;
} pit_counter;

static pit_counter pit_counters[3][3];

static int is_pit_data_port(uint8_t port) {
  return port >= 0x10 && port <= 0x1A && (port & 3) != 3;
}

static pit_counter* pit_counter_for_port(uint8_t port) {
  unsigned chip = (port - 0x10) >> 2;
  unsigned channel = port & 3;
  return &pit_counters[chip][channel];
}

static void pit_write(uint8_t port, uint8_t value) {
  unsigned chip = (port - 0x10) >> 2;
  unsigned reg = port & 3;
  if (reg == 3) {
    unsigned channel = value >> 6;
    unsigned access = (value >> 4) & 3;
    if (channel >= 3) return;  // 8253 has no 8254-style read-back command
    pit_counter* counter = &pit_counters[chip][channel];
    if (access == 0) {
      // A pending latch owns the output latch until its programmed byte(s)
      // are consumed; later counter-latch commands are ignored.
      if (!counter->latch_valid) {
        counter->output_latch = counter->count_register;
        counter->latch_valid = 1;
        counter->read_phase = 0;
      }
    } else {
      counter->access = (uint8_t)access;
      counter->bcd = value & 1;
      counter->mode = (value >> 1) & 7;
      if (counter->mode > 5) counter->mode &= 3;
      counter->write_phase = 0;
      counter->read_phase = 0;
      counter->latch_valid = 0;
    }
    return;
  }

  pit_counter* counter = &pit_counters[chip][reg];
  counter->latch_valid = 0;
  counter->read_phase = 0;
  if (counter->access == 1) {
    counter->count_register = value;
  } else if (counter->access == 2) {
    counter->count_register = (uint16_t)value << 8;
  } else if (counter->access == 3) {
    if (!counter->write_phase) {
      counter->write_latch = value;
      counter->write_phase = 1;
      return;
    }
    counter->count_register = (uint16_t)(((uint16_t)value << 8) |
                                         (counter->write_latch & 0xFF));
    counter->write_phase = 0;
  }
}

static uint8_t pit_read(uint8_t port) {
  pit_counter* counter = pit_counter_for_port(port);
  uint16_t value = counter->latch_valid
      ? counter->output_latch : counter->count_register;
  uint8_t result;
  if (counter->access == 2) {
    result = (uint8_t)(value >> 8);
    counter->latch_valid = 0;
  } else if (counter->access == 3 && counter->read_phase) {
    result = (uint8_t)(value >> 8);
    counter->read_phase = 0;
    counter->latch_valid = 0;
  } else {
    result = (uint8_t)value;
    if (counter->access == 3) counter->read_phase = 1;
    else counter->latch_valid = 0;
  }
  return result;
}

static void pit_init(void) {
  for (unsigned chip = 0; chip < 3; ++chip)
    for (unsigned channel = 0; channel < 3; ++channel)
      pit_counters[chip][channel].access = 3;
}

static uint8_t apply_ram_fault(uint16_t address, uint8_t value) {
  if (!ram_fault_enabled || (!ram_fault_all && address != ram_fault_addr))
    return value;
  return (uint8_t)((value & (uint8_t)~ram_fault_stuck_low) |
                   ram_fault_stuck_high);
}

static uint16_t map_ram_address(uint16_t address) {
  if (ram_alias_enabled && (address >> 8) == ram_alias_page_b)
    return (uint16_t)(((uint16_t)ram_alias_page_a << 8) | (address & 0xFF));
  return address;
}

static uint8_t dram_row_from_address(uint16_t address) {
  /*
   * D48/D49 select CPU A0..A7 in the populated-bank /RAS phase and A8..A15
   * for /CAS.  MK4564/2164-class 128-cycle refresh uses physical MA0..MA6;
   * MA7 (pin 9) is irrelevant.  The inverting KP14 mux changes row polarity,
   * but not which logical addresses share a row, so normalize it away here.
   */
  return (uint8_t)(address & 0x7F);
}

static void dram_touch(i8080* cpu, uint16_t physical_address) {
  if (!dram_retention_cycles || !dram_retention_armed || !cpu) return;
  uint8_t row = dram_row_from_address(physical_address);
  if (!dram_coverage_count ||
      cpu->cyc - dram_coverage_start > dram_retention_cycles) {
    memset(dram_coverage_seen, 0, sizeof(dram_coverage_seen));
    dram_coverage_count = 0;
    dram_coverage_start = cpu->cyc;
  }
  if (!dram_coverage_seen[row]) {
    dram_coverage_seen[row] = 1;
    dram_coverage_count++;
    if (dram_coverage_count == 128 && !dram_full_coverage_reported) {
      dram_full_coverage_reported = 1;
      fprintf(stderr,
              "[DRAM] observed all 128 refresh rows in %lu cycles at cyc=%lu\n",
              cpu->cyc - dram_coverage_start, cpu->cyc);
    }
  }
  unsigned long age = cpu->cyc - dram_last_refresh[row];
  if (age > dram_retention_cycles) {
    for (unsigned address = 0; address < MEM_SIZE; address++)
      if (dram_row_from_address((uint16_t)address) == row)
        ram[address] ^= 0xFF;
    dram_decay_count++;
    if (dram_decay_count <= 32)
      fprintf(stderr,
              "[DRAM] decayed refresh row=%02X age=%lu cyc=%lu count=%lu\n",
              row, age, cpu->cyc, dram_decay_count);
  }
  dram_last_refresh[row] = cpu->cyc;
}

// --- minimal 8251 USART + PTY transport (opt-in via JUKU_USART_PTY) -------
// The diagnostic-ROM path needs only the asynchronous 8-bit mode/command
// sequence, RxRDY, and separate TxRDY/TxEMPTY transitions around a one-byte
// transmit holding register and shifter. The PTY is deliberately byte-oriented:
// attaching it represents a connected harness with active CTS; baud recovery
// belongs to the Nano/host protocol, while this model preserves the
// firmware-visible ready transitions.
typedef struct {
  int fd;
  int enabled;
  int expect_mode;
  uint8_t mode_word;
  uint8_t command;
  uint8_t rx_data;
  uint8_t rx_errors;
  uint8_t tx_data;
  uint8_t tx_shift_data;
  int rx_ready;
  int tx_holding_full;
  int tx_busy;
  int fault_tx_stuck;
  int fault_tx_stuck_permanent;
  int fault_tx_stuck_once_enabled;
  int fault_tx_stuck_once_fired;
  uint8_t fault_tx_stuck_once_value;
  int fault_tx_not_ready_once_after_enabled;
  unsigned long fault_tx_not_ready_once_after;
  int fault_tx_empty_low_after_enabled;
  unsigned long fault_tx_empty_low_after;
  int fault_rx_irq_delay_once_enabled;
  int fault_rx_irq_delay_once_fired;
  unsigned long fault_rx_irq_delay_once_after;
  unsigned long fault_rx_irq_delay_cycles;
  unsigned long fault_rx_irq_delay_until;
  unsigned long fault_tx_stuck_once_recoveries;
  unsigned long tx_transfer_cyc;
  unsigned long tx_complete_cyc;
  unsigned long rx_next_cyc;
  unsigned long transfer_cycles;
  unsigned long byte_cycles;
  unsigned long tx_bytes;
  unsigned long rx_bytes;
} juku_usart;

static juku_usart usart = {
  .fd = -1,
  .expect_mode = 1,
  .transfer_cycles = 16,
  .byte_cycles = 256,
};
static int usart_pit_clock = 0;
static unsigned long usart_pit_cpu_hz = 0;
static unsigned long usart_pit_divisor = 0;
static int usart_pit_clock_valid = 1;
static int usart_tx_irq_armed = 0;
static int usart_tx_irq_level = 0, usart_rx_irq_level = 0;
static int usart_tx_irq_pending = 0, usart_rx_irq_pending = 0;

static unsigned long pit_effective_divisor(const pit_counter* counter) {
  unsigned long raw = counter->count_register;
  if (!counter->bcd) return raw ? raw : 65536UL;
  unsigned long divisor = 0, place = 1;
  for (unsigned shift = 0; shift < 16; shift += 4) {
    divisor += ((raw >> shift) & 0x0F) * place;
    place *= 10;
  }
  return divisor ? divisor : 10000UL;
}

static void usart_update_pit_timing(void) {
  if (!usart_pit_clock || !usart_pit_divisor) return;
  pit_counter* baud_counter = &pit_counters[2][0];
  if ((baud_counter->mode == 2 || baud_counter->mode == 3) &&
      usart_pit_divisor < 2) {
    usart_pit_clock_valid = 0;
    fprintf(stderr,
            "[USART] invalid D57 mode=%u divisor=%lu; no periodic baud clock\n",
            baud_counter->mode, usart_pit_divisor);
    return;
  }
  unsigned factor;
  switch (usart.mode_word & 3) {
    case 1: factor = 1; break;
    case 2: factor = 16; break;
    case 3: factor = 64; break;
    default: return;  /* synchronous mode */
  }
  unsigned data_bits = 5 + ((usart.mode_word >> 2) & 3);
  unsigned wire_bits_x2 = 2 * (1 + data_bits);
  if (usart.mode_word & 0x10) wire_bits_x2 += 2;  /* parity */
  switch ((usart.mode_word >> 6) & 3) {
    case 1: wire_bits_x2 += 2; break;  /* one stop bit */
    case 2: wire_bits_x2 += 3; break;  /* 1.5 stop bits */
    case 3: wire_bits_x2 += 4; break;  /* two stop bits */
    default: return;
  }
  if (usart_pit_cpu_hz)
    usart.byte_cycles =
        (usart_pit_cpu_hz * wire_bits_x2 * factor * usart_pit_divisor * 13UL) /
        (2UL * 16000000UL);
  else
    usart.byte_cycles =
        (2000000UL * wire_bits_x2 * factor * usart_pit_divisor * 13UL) /
        (2UL * 16000000UL);
  if (!usart.byte_cycles) usart.byte_cycles = 1;
  usart_pit_clock_valid = 1;
  fprintf(stderr,
          "[USART] D57 divisor=%lu -> byte_cycles=%lu x%u mode=%02X\n",
          usart_pit_divisor, usart.byte_cycles, factor, usart.mode_word);
}

static void usart_update_irq_edges(void) {
  int tx_level = usart.enabled && usart_tx_irq_armed &&
                 (usart.command & 0x01) && !usart.fault_tx_stuck &&
                 !usart.tx_holding_full;
  int rx_level = usart.enabled && (usart.command & 0x04) && usart.rx_ready;
  if (tx_level && !usart_tx_irq_level) usart_tx_irq_pending = 1;
  if (rx_level && !usart_rx_irq_level) usart_rx_irq_pending = 1;
  usart_tx_irq_level = tx_level;
  usart_rx_irq_level = rx_level;
}

static int env_enabled(const char* value) {
  return value && value[0] && strcmp(value, "0") != 0;
}

static int set_raw_tty(int fd) {
  struct termios tty;
  if (tcgetattr(fd, &tty) != 0) return -1;
  tty.c_iflag &= (tcflag_t)~(IGNBRK | BRKINT | PARMRK | ISTRIP |
                             INLCR | IGNCR | ICRNL | IXON);
  tty.c_oflag &= (tcflag_t)~OPOST;
  tty.c_lflag &= (tcflag_t)~(ECHO | ECHONL | ICANON | ISIG | IEXTEN);
  tty.c_cflag &= (tcflag_t)~(CSIZE | PARENB);
  tty.c_cflag |= CS8 | CLOCAL | CREAD;
  tty.c_cc[VMIN] = 0;
  tty.c_cc[VTIME] = 0;
  return tcsetattr(fd, TCSANOW, &tty);
}

static int set_nonblocking(int fd) {
  int flags = fcntl(fd, F_GETFL, 0);
  return flags < 0 ? -1 : fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

// Open a PTY ("auto": create one and print its slave path) or an existing
// device, returning the fd. Callers own it: the USART binds it to the 8251
// model, the interactive console keeps it as a terminal.
static int open_serial_endpoint(const char* setting, const char* tag) {
  int fd;
  if (strcmp(setting, "auto") == 0) {
    fd = posix_openpt(O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd < 0 || grantpt(fd) != 0 || unlockpt(fd) != 0) {
      if (fd >= 0) close(fd);
      return -1;
    }
    char* slave_name = ptsname(fd);
    if (!slave_name) {
      close(fd);
      return -1;
    }
    int slave = open(slave_name, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (slave < 0 || set_raw_tty(slave) != 0) {
      if (slave >= 0) close(slave);
      close(fd);
      return -1;
    }
    close(slave);
    fprintf(stderr, "[%s] PTY slave=%s\n", tag, slave_name);
  } else {
    fd = open(setting, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd < 0 || set_raw_tty(fd) != 0) {
      if (fd >= 0) close(fd);
      return -1;
    }
    fprintf(stderr, "[%s] attached PTY=%s\n", tag, setting);
  }
  if (set_nonblocking(fd) != 0) {
    close(fd);
    return -1;
  }
  return fd;
}

static int usart_open_transport(const char* setting) {
  if (!setting || !setting[0]) return 0;
  int fd = open_serial_endpoint(setting, "USART");
  if (fd < 0) return -1;
  usart.fd = fd;
  usart.enabled = 1;
  return 0;
}

static void usart_reset(void) {
  if (usart.fault_tx_stuck && !usart.fault_tx_stuck_permanent) {
    usart.fault_tx_stuck_once_recoveries++;
    fprintf(stderr, "[USART] one-shot TxRDY stall cleared by 8251 reset\n");
  }
  /* A reset empties the transmitter.  A configured permanent stall becomes
     active only after the next data write fills the holding register. */
  usart.fault_tx_stuck = 0;
  usart.expect_mode = 1;
  usart.mode_word = 0;
  usart.command = 0;
  usart.rx_ready = 0;
  usart.rx_errors = 0;
  usart.tx_holding_full = 0;
  usart.tx_busy = 0;
  usart_tx_irq_armed = 0;
  usart_tx_irq_level = usart_rx_irq_level = 0;
  usart_tx_irq_pending = usart_rx_irq_pending = 0;
}

static void usart_poll(unsigned long cyc) {
  if (!usart.enabled) return;
  if (usart_pit_clock && !usart_pit_clock_valid) return;
  if (usart.tx_busy && cyc >= usart.tx_complete_cyc) {
    ssize_t written = write(usart.fd, &usart.tx_shift_data, 1);
    if (written == 1) {
      usart.tx_busy = 0;
      usart.tx_bytes++;
      if (usart.tx_holding_full)
        usart.tx_transfer_cyc = cyc + usart.transfer_cycles;
    } else if (written < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EIO) {
      perror("JUKU USART PTY write");
      exit(2);
    }
  }
  if (!usart.fault_tx_stuck && usart.tx_holding_full && !usart.tx_busy &&
      cyc >= usart.tx_transfer_cyc) {
    usart.tx_shift_data = usart.tx_data;
    usart.tx_holding_full = 0;
    usart.tx_busy = 1;
    usart.tx_complete_cyc = cyc + usart.byte_cycles;
  }
  /* The serial line keeps shifting while the receive data register is full.
     Do not let the host PTY become an impossible extra FIFO: at each complete
     character time, consume the next wire byte.  If firmware has not read the
     previous byte, latch OE and discard the newcomer. */
  if ((usart.command & 0x04) && cyc >= usart.rx_next_cyc) {
    uint8_t value;
    ssize_t received = read(usart.fd, &value, 1);
    if (received == 1) {
      if (usart.rx_ready) {
        usart.rx_errors |= 0x10;
      } else {
        usart.rx_data = value;
        usart.rx_ready = 1;
      }
      usart.rx_bytes++;
      usart.rx_next_cyc = cyc + usart.byte_cycles;
    } else if (received < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EIO) {
      perror("JUKU USART PTY read");
      exit(2);
    }
  }
  usart_update_irq_edges();
}

static uint8_t usart_status(void) {
  if (usart.fault_tx_not_ready_once_after_enabled &&
      !usart.fault_tx_stuck_once_fired &&
      usart.tx_bytes >= usart.fault_tx_not_ready_once_after) {
    usart.fault_tx_stuck = 1;
    usart.fault_tx_stuck_once_fired = 1;
    fprintf(stderr,
            "[USART] injected one-shot TxRDY stall after byte=%lu\n",
            usart.tx_bytes);
  }
  uint8_t tx_ready = (usart.fault_tx_stuck || usart.tx_holding_full) ? 0 : 0x01;
  uint8_t tx_empty = (!usart.fault_tx_stuck && !usart.tx_holding_full &&
                      !usart.tx_busy) ? 0x04 : 0;
  if (usart.fault_tx_empty_low_after_enabled &&
      usart.tx_bytes >= usart.fault_tx_empty_low_after)
    tx_empty = 0;
  return (uint8_t)(tx_ready | tx_empty | (usart.rx_ready ? 0x02 : 0) |
                   usart.rx_errors);
}

static uint8_t usart_read(int control, unsigned long cyc) {
  usart_poll(cyc);
  if (control) return usart_status();
  uint8_t value = usart.rx_data;
  usart.rx_ready = 0;
  usart_update_irq_edges();
  return value;
}

static void usart_write(int control, uint8_t value, unsigned long cyc) {
  usart_poll(cyc);
  if (control) {
    if (usart.expect_mode) {
      usart.mode_word = value;
      usart.expect_mode = 0;
      usart_update_pit_timing();
    } else if (value & 0x40) {
      usart_reset();
    } else {
      uint8_t old_command = usart.command;
      usart.command = value;
      if ((old_command & 0x01) && !(value & 0x01)) {
        // NetBios deliberately drops and raises TxEN when a complete frame is
        // queued.  Treat that as the interrupt arm/ack boundary; the initial
        // 8251 enable occurs before its transmit descriptor is initialized.
        usart_tx_irq_armed = 1;
        usart_tx_irq_pending = 0;
      }
      /* ER (bit 4) resets PE/OE/FE error latches; it does not consume the
         receive data register or clear RxRDY.  Preserving an unread byte is
         essential across half-duplex TxEN turnarounds. */
      if (value & 0x10) usart.rx_errors = 0;
    }
  } else if ((usart.command & 0x01) && !usart.tx_holding_full) {
    usart.tx_data = value;
    usart.tx_holding_full = 1;
    if (usart.fault_tx_stuck_permanent)
      usart.fault_tx_stuck = 1;
    if (usart.fault_tx_stuck_once_enabled &&
        !usart.fault_tx_stuck_once_fired &&
        value == usart.fault_tx_stuck_once_value) {
      usart.fault_tx_stuck = 1;
      usart.fault_tx_stuck_once_fired = 1;
      fprintf(stderr,
              "[USART] injected one-shot TxRDY stall on data=%02X at byte=%lu\n",
              value, usart.tx_bytes);
    }
    if (!usart.tx_busy)
      usart.tx_transfer_cyc = cyc + usart.transfer_cycles;
  }
  usart_update_irq_edges();
}

static void set_mode(int m) {
  if (m != mode) {
    if (bank_trace)
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
static FILE *bustrace_fp = NULL;         // CPU-visible bus events (JUKU_BUS_TRACE=path)
static unsigned long bustrace_limit = 0; // stop after N events (JUKU_BUS_TRACE_LIMIT; 0 = unbounded)
static unsigned long bustrace_n = 0;

static void trace_bus_event(const char* kind, uint16_t address, uint8_t data) {
  if (!bustrace_fp) return;
  fprintf(bustrace_fp, "%s %04x %02x\n", kind, address, data);
  if (bustrace_limit && ++bustrace_n >= bustrace_limit) {
    fclose(bustrace_fp);
    bustrace_fp = NULL;
  }
}

static uint8_t rb(void* u, uint16_t a) {
  i8080* cpu = (i8080*)u;
  uint16_t physical_a = a;
  unsigned idx = 0;
  uint8_t v;
  int ov = overlay(physical_a, &idx);
  if (ov == 1) {
    unsigned ordinal = ++rom_read_burst_count;
    if (rom_consecutive_a12_low && ordinal >= 2) idx &= ~0x1000u;
    v = rom[idx];
  }
  else if (ov == 2) {
    rom_read_burst_count = 0;
    v = cart_enabled ? cart[physical_a - 0x4000] : 0xFF;
  }
  else {
    rom_read_burst_count = 0;
    uint16_t mapped = map_ram_address(physical_a);
    dram_touch(cpu, mapped);
    v = apply_ram_fault(physical_a, ram[mapped]);
  }
  if (exec_byte_fault_enabled && a == exec_byte_fault_addr && cpu &&
      (cpu->pc == a || cpu->pc == (uint16_t)(a + 1)))
    v = exec_byte_fault_value;
  if (rdtrace_fp) {
    fprintf(rdtrace_fp, "%04x %02x\n", a, v);
    if (rdtrace_limit && ++rdtrace_n >= rdtrace_limit) { fclose(rdtrace_fp); rdtrace_fp = NULL; }
  }
  trace_bus_event("MR", a, v);
  return v;
}

static unsigned long g_vw = 0, g_vw_limit = 0;   // video-RAM write count + optional stop limit
// --- minimal 8259 PIC (MCS-80/CALL mode) for the frame interrupt (ports 0x00/0x01) ---
static uint8_t pic_icw1 = 0, pic_icw2 = 0, pic_mask = 0xFF;  // mask: 1=masked
static int     pic_expect_icw2 = 0;

// --- keyboard (opt-in via env JUKU_KEYS): matrix scan via 8255 PortA(col)/PortB(74148) ---
// char -> (column 0-14, encoded row bit, SHIFT); independently transcribed from
// factory keyboard drawing ДГШ5.104.015 Э3.  Its scan lines 1..15 are columns
// 0..14 here.  Uppercase letters reuse the lowercase entry with SHIFT below.
static const struct { char c; uint8_t col, bit, shift; } KMAP[] = {
  {'a',5,5,0},{'b',4,1,0},{'c',6,1,0},{'d',6,5,0},{'e',6,3,0},{'f',2,5,0},{'g',4,5,0},{'h',0,5,0},
  {'i',14,3,0},{'j',7,5,0},{'k',14,5,0},{'l',13,5,0},{'m',7,1,0},{'n',0,1,0},{'o',13,3,0},{'p',12,3,0},
  {'q',5,3,0},{'r',2,3,0},{'s',1,5,0},{'t',4,3,0},{'u',7,3,0},{'v',2,1,0},{'w',1,3,0},{'x',1,1,0},
  {'y',0,3,0},{'z',5,1,0},
  {'0',12,4,0},{'1',5,4,0},{'2',1,4,0},{'3',6,4,0},{'4',2,4,0},{'5',4,4,0},{'6',0,4,0},{'7',7,4,0},{'8',14,4,0},{'9',13,4,0},
  {'!',5,4,1},{'"',1,4,1},{'#',6,4,1},{'$',2,4,1},{'%',4,4,1},{'&',0,4,1},{'\'',7,4,1},
  {'(',14,4,1},{')',13,4,1},{'_',12,4,1},
  {' ',11,2,0},{'\r',8,5,0},{'\n',8,5,0},{'\t',3,3,0},{'\b',13,2,0},{'\033',3,4,0},
  {'.',13,1,0},{'>',13,1,1},{',',14,1,0},{'<',14,1,1},{'/',12,1,0},{'?',12,1,1},
  {';',11,1,0},{'+',11,1,1},{'-',11,4,0},{'=',11,4,1},{':',10,5,0},{'*',10,5,1},
  {'[',9,3,0},{']',8,3,0},{'\\',11,3,0},{'^',11,3,1},
};
// Interactive console (JUKU_CONSOLE_PTY): typed bytes are appended to this
// queue and consumed by the ordinary keystroke machinery, so an operator at a
// terminal and a scripted JUKU_KEYS string drive the matrix the same way.
#define CONSOLE_QUEUE 4096
static int console_fd = -1;
static char console_queue[CONSOLE_QUEUE];
static int console_len = 0;
// Default to the routine the WRCHR vector (FFD9h) jumps to rather than the
// vector itself: the ROM's own printing calls it directly, so hooking the
// target shows the boot banner and monitor output as well as CP/M's.
static uint16_t console_out_pc = 0xD9E3;   // EktaSoft console char-out, A = char
static uint16_t console_in_pc = 0xFFD3;    // ROM RDCHR: entered when reading

static const char* kbd_str = 0;     // keystrokes to "type" (0/empty = keyboard off)
static int   kbd_pos = 0, kbd_phase = 0;
static int   kbd_enabled = 0;
static uint8_t kbd_col = 0;         // last column selected (8255 Port A write)
static unsigned long kbd_start_vram = 42000;
static int kbd_hold_frames = 3;
static int kbd_gap_frames = 3;
static int kbd_trace = 0;
#define KBD_HOLD 3
#define KBD_GAP  3

// Drain anything the operator typed into the console PTY onto the key queue.
// Newlines become carriage returns because the ROM's key matrix speaks CR.
static void console_poll(void) {
  if (console_fd < 0) return;
  char buffer[256];
  ssize_t got = read(console_fd, buffer, sizeof(buffer));
  if (got <= 0) return;
  for (ssize_t i = 0; i < got; i++) {
    char c = buffer[i] == '\n' ? '\r' : buffer[i];
    if (c == 0x7F) c = '\b';                       // terminal DEL -> backspace
    if (console_len + 2 >= CONSOLE_QUEUE) {
      // Compact: drop what the matrix has already consumed.
      if (kbd_pos > 0 && kbd_pos <= console_len) {
        memmove(console_queue, console_queue + kbd_pos,
                (size_t)(console_len - kbd_pos));
        console_len -= kbd_pos;
        kbd_pos = 0;
      } else {
        return;                                    // full and nothing consumed
      }
    }
    console_queue[console_len++] = c;
    console_queue[console_len] = 0;
  }
  kbd_str = console_queue;
  kbd_enabled = 1;
}

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
#define KBD_NONE 0xCF              // no key: encoder + -FK released, SHIFT/CTRL released
static uint8_t kbd_portb(const i8080* cpu) {
  // ROM 1209h..123Bh selects eight configuration positions and samples PB5.
  // Model the source-closed, unstrapped/onboard-serial setting as released
  // high only in that scan; ordinary keyboard-idle remains the established
  // drawing-derived 0xCF value.
  int config_scan = cpu && cpu->pc >= 0x1209 && cpu->pc <= 0x123B;
  uint8_t idle = (uint8_t)(KBD_NONE | (config_scan ? 0x20 : 0));
  if (g_vw < kbd_start_vram) return idle;              // default waits until the ekta37 banner is drawn
  char c = (kbd_str && kbd_str[kbd_pos] && kbd_phase < kbd_hold_frames) ? kbd_str[kbd_pos] : 0;
  if (c == '|') return idle;                           // prompt wait marker, not a typed key
  int shift = 0, col = -1, bit = -1;
  if (c) {
    char lc = c; if (c >= 'A' && c <= 'Z') { lc = (char)(c + 32); shift = 1; }
    for (unsigned i = 0; i < sizeof(KMAP)/sizeof(KMAP[0]); i++)
      if (KMAP[i].c == lc) { col = KMAP[i].col; bit = KMAP[i].bit; shift |= KMAP[i].shift; break; }
  }
  uint8_t pb = (uint8_t)(0xC0 | (config_scan ? 0x20 : 0));
  if (shift) pb &= (uint8_t)~0x40;                     // SHIFT1 held = bit6 low (active-low)
  if (c && col == kbd_col)
    pb |= (uint8_t)(((~bit) & 7) << 1);                // 74148 code in b1-3, GS active (b0=0)
  else
    pb |= 0x0F;                                        // no key here: code=7 + GS released (b0=1)
  if (kbd_trace && c && col == kbd_col)
    fprintf(stderr,
            "[KBD] scan char=%02X pos=%d phase=%d col=%d pb=%02X pc=%04X cyc=%lu\n",
            (unsigned char)c, kbd_pos, kbd_phase, col, pb,
            cpu ? cpu->pc : 0, cpu ? cpu->cyc : 0);
  return pb;
}
static void wb(void* u, uint16_t a, uint8_t v) {
  rom_read_burst_count = 0;
  trace_bus_event("MW", a, v);
  unsigned idx = 0;
  int ov = overlay(a, &idx);
  // Monitor 3.7's low-ROM dispatcher writes its return frame behind page-zero
  // ROM. High-ROM and cartridge windows remain read-only overlays; allowing
  // those writes corrupts the independently guarded Monitor 3.3 framebuffer.
  if (ov && !(mode == 0 && a <= 0x3FFF)) return;
  if (ram_drop_write_enabled && ram_drop_write_remaining &&
      a == ram_drop_write_addr && v == ram_drop_write_value) {
    ram_drop_write_remaining--;
    fprintf(stderr,
            "[RAM] dropped write address=0x%04X value=0x%02X remaining=%u\n",
            a, v, ram_drop_write_remaining);
    return;
  }
  uint16_t mapped = map_ram_address(a);
  dram_touch((i8080*)u, mapped);
  ram[mapped] = apply_ram_fault(a, v);
  wpage[a >> 8]++;
  if (a >= VRAM_BASE) {            // for CI: stop+dump after N video writes (match HDL)
    if (g_vw == 0) {
      unsigned long cyc = u ? ((i8080*)u)->cyc : 0;
      fprintf(stderr, "[VRAM] first video write @0x%04X cyc=%lu\n",
              a, cyc);
    }
    g_vw++;
  }
}

static int take_pic_irq(i8080* cpu, unsigned irq, const char* source,
                        unsigned long* log_count) {
  if (!cpu || irq > 7 || !cpu->iff || (pic_mask & (1u << irq))) return 0;

  uint16_t vec = ((uint16_t)pic_icw2 << 8) | (pic_icw1 & 0xE0) | (irq << 2);
  if ((*log_count)++ < 3)
    fprintf(stderr,
            "[IRQ] %s #%lu g_vw=%lu cyc=%lu pc=%04X irq=%u "
            "icw1=%02X icw2=%02X mask=%02X vec=%04X\n",
            source, *log_count, g_vw, cpu->cyc, cpu->pc, irq,
            pic_icw1, pic_icw2, pic_mask, vec);

  // The 8259 supplies an MCS-80 CALL over three INTA cycles.  The functional
  // cosim performs the resulting call directly while retaining those bus
  // events for the unified trace contract.
  trace_bus_event("IA", 0, 0xCD);
  trace_bus_event("IA", 0, (uint8_t)vec);
  trace_bus_event("IA", 0, (uint8_t)(vec >> 8));
  if (cpu->halted) cpu->halted = 0;
  wb(0, (uint16_t)(cpu->sp - 1), cpu->pc >> 8);
  wb(0, (uint16_t)(cpu->sp - 2), cpu->pc & 0xFF);
  cpu->sp -= 2;
  cpu->iff = 0;
  cpu->pc = vec;
  return 1;
}

static void sync_fdc_time(i8080* cpu) {
  if (!fdc_enabled || !cpu || cpu->cyc <= fdc_last_cyc) return;
  juku_fdc_tick(&fdc, (unsigned)(cpu->cyc - fdc_last_cyc));
  fdc_last_cyc = cpu->cyc;
}

static uint8_t pin(void* u, uint8_t p) {
  rom_read_burst_count = 0;
  i8080* cpu = (i8080*)u;
  sync_fdc_time(cpu);
  if (!in_seen[p]) { in_seen[p] = 1; fprintf(stderr, "[IN ] first read  port 0x%02X\n", p); }
  if (timing_log && in_count[p] == 0) {
    fprintf(stderr, "[IOT] first IN  port 0x%02X cyc=%lu pc=%04X g_vw=%lu\n",
            p, cpu ? cpu->cyc : 0, cpu ? cpu->pc : 0, g_vw);
  }
  in_count[p]++;
  uint8_t value;
  if (p == 0x05 && kbd_enabled) value = kbd_portb(cpu);          // 8255 Port B = keyboard 74148/config scan
  else if (usart.enabled && p >= 0x08 && p <= 0x0B)
    value = usart_read(p & 1, cpu ? cpu->cyc : 0);
  else if (fdc_enabled && p >= 0x1C && p <= 0x1F) {
    value = juku_fdc_read(&fdc, p & 3);
    if (fdc_bus_invert) value = (uint8_t)~value;
    if (p == 0x1F) fdc_data_reads++;
  }
  else if (is_pit_data_port(p)) value = pit_read(p);
  // Optional expansion hardware occupies F0h-F3h in some software paths.
  // With no card installed the Multibus data lines float high; returning the
  // generic zero-valued output latch here traps NetBios forever in its F1h
  // ready poll before it can initialize the onboard 8251 serial link.
  else if (p >= 0xF0 && p <= 0xF3) value = 0xFF;
  else value = out_last[p];              // mimic 8255 output-latch readback; 0 if never written
  if (p == 0x01 && pic_fault_enabled)
    value = (uint8_t)((value & (uint8_t)~pic_fault_stuck_low) |
                      pic_fault_stuck_high);
  if (p == ppi_fault_port && ppi_fault_enabled)
    value = (uint8_t)((value & (uint8_t)~ppi_fault_stuck_low) |
                      ppi_fault_stuck_high);
  if (p == pit_fault_port && pit_fault_enabled)
    value = (uint8_t)((value & (uint8_t)~pit_fault_stuck_low) |
                      pit_fault_stuck_high);
  if (io_trace) {
    fprintf(stderr, "[IOSEQ] IN  port=0x%02X value=0x%02X cyc=%lu pc=%04X g_vw=%lu count=%lu\n",
            p, value, cpu ? cpu->cyc : 0, cpu ? cpu->pc : 0, g_vw, in_count[p]);
  }
  trace_bus_event("IR", p, value);
  return value;
}

static void pout(void* u, uint8_t p, uint8_t v) {
  rom_read_burst_count = 0;
  trace_bus_event("IW", p, v);
  i8080* cpu = (i8080*)u;
  sync_fdc_time(cpu);
  if (!out_seen[p]) { out_seen[p] = 1; fprintf(stderr, "[OUT] first write port 0x%02X = 0x%02X\n", p, v); }
  if (timing_log && out_count[p] == 0) {
    fprintf(stderr, "[IOT] first OUT port 0x%02X val=0x%02X cyc=%lu pc=%04X g_vw=%lu\n",
            p, v, cpu ? cpu->cyc : 0, cpu ? cpu->pc : 0, g_vw);
  }
  out_count[p]++;
  out_last[p] = v;
  if (io_trace) {
    fprintf(stderr, "[IOSEQ] OUT port=0x%02X value=0x%02X cyc=%lu pc=%04X g_vw=%lu count=%lu\n",
            p, v, cpu ? cpu->cyc : 0, cpu ? cpu->pc : 0, g_vw, out_count[p]);
  }
  if (fdc_enabled && p >= 0x1C && p <= 0x1F) {
    juku_fdc_write(&fdc, p & 3, fdc_bus_invert ? (uint8_t)~v : v);
    /* The instruction-granular cosim has no model of the Juku's I/O wait
     * states.  As in rombios_fdc_write_test, start the 512-byte firmware
     * stream immediately; the controller-level test retains and checks the
     * exact WD1793 write lead-in timing. */
    const uint8_t fdc_value = fdc_bus_invert ? (uint8_t)~v : v;
    if (p == 0x1C && (fdc_value & 0xE0) == 0xA0)
      fdc.write_sector_lead_pending = 0;
  }
  if (usart.enabled && p >= 0x08 && p <= 0x0B)
    usart_write(p & 1, v, cpu ? cpu->cyc : 0);
  if (p >= 0x10 && p <= 0x1B) {
    pit_write(p, v);
    if (usart_pit_clock && p == 0x18 && v) {
      /* D57 CLK0 is 16 MHz / 13.  Preserve the PIT's BCD interpretation and
         recompute after either the count or the 8251 x1/x16/x64 mode changes. */
      usart_pit_divisor =
          pit_effective_divisor(&pit_counters[2][0]);
      usart_update_pit_timing();
    }
  }

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
  fprintf(state_out, "rom_consecutive_a12_low=%d\n",
          rom_consecutive_a12_low);
  fprintf(state_out, "rom_read_burst_count=%u\n", rom_read_burst_count);
  fprintf(state_out, "cpu_a12_increment_fault=%d\n",
          cpu_a12_increment_fault);
  fprintf(state_out, "exec_byte_fault_enabled=%d\n", exec_byte_fault_enabled);
  fprintf(state_out, "exec_byte_fault_addr=%04X\n", exec_byte_fault_addr);
  fprintf(state_out, "exec_byte_fault_value=%02X\n", exec_byte_fault_value);
  fprintf(state_out, "ram_fault_enabled=%d\n", ram_fault_enabled);
  fprintf(state_out, "ram_fault_addr=%04X\n", ram_fault_addr);
  fprintf(state_out, "ram_fault_stuck_low=%02X\n", ram_fault_stuck_low);
  fprintf(state_out, "ram_fault_stuck_high=%02X\n", ram_fault_stuck_high);
  fprintf(state_out, "ram_fault_all=%d\n", ram_fault_all);
  fprintf(state_out, "ram_alias_enabled=%d\n", ram_alias_enabled);
  fprintf(state_out, "ram_alias_page_a=%02X\n", ram_alias_page_a);
  fprintf(state_out, "ram_alias_page_b=%02X\n", ram_alias_page_b);
  fprintf(state_out, "dram_retention_cycles=%lu\n", dram_retention_cycles);
  fprintf(state_out, "dram_decay_count=%lu\n", dram_decay_count);
  fprintf(state_out, "dram_coverage_count=%u\n", dram_coverage_count);
  fprintf(state_out, "dram_full_coverage_reported=%d\n",
          dram_full_coverage_reported);
  fprintf(state_out, "kbd_pos=%d\n", kbd_pos);
  fprintf(state_out, "kbd_phase=%d\n", kbd_phase);
  fprintf(state_out, "kbd_col=%02X\n", kbd_col);
  fprintf(state_out, "pic_icw1=%02X\n", pic_icw1);
  fprintf(state_out, "pic_icw2=%02X\n", pic_icw2);
  fprintf(state_out, "pic_mask=%02X\n", pic_mask);
  fprintf(state_out, "pic_expect_icw2=%d\n", pic_expect_icw2);
  fprintf(state_out, "pic_fault_enabled=%d\n", pic_fault_enabled);
  fprintf(state_out, "pic_fault_stuck_low=%02X\n", pic_fault_stuck_low);
  fprintf(state_out, "pic_fault_stuck_high=%02X\n", pic_fault_stuck_high);
  fprintf(state_out, "ppi1_control=%02X\n", out_last[0x0F]);
  fprintf(state_out, "ppi1_pa_latch=%02X\n", out_last[0x0C]);
  fprintf(state_out, "ppi1_pb_latch=%02X\n", out_last[0x0D]);
  fprintf(state_out, "ppi1_pc_latch=%02X\n", out_last[0x0E]);
  fprintf(state_out, "ppi_fault_enabled=%d\n", ppi_fault_enabled);
  fprintf(state_out, "ppi_fault_port=%02X\n", ppi_fault_port);
  fprintf(state_out, "ppi_fault_stuck_low=%02X\n", ppi_fault_stuck_low);
  fprintf(state_out, "ppi_fault_stuck_high=%02X\n", ppi_fault_stuck_high);
  fprintf(state_out, "pit_fault_enabled=%d\n", pit_fault_enabled);
  fprintf(state_out, "pit_fault_port=%02X\n", pit_fault_port);
  fprintf(state_out, "pit_fault_stuck_low=%02X\n", pit_fault_stuck_low);
  fprintf(state_out, "pit_fault_stuck_high=%02X\n", pit_fault_stuck_high);
  fprintf(state_out, "fdc_enabled=%d\n", fdc_enabled);
  fprintf(state_out, "fdc_bus_invert=%d\n", fdc_bus_invert);
  fprintf(state_out, "fdc_head=%d\n", fdc.head);
  fprintf(state_out, "fdc_drive=%d\n", fdc.drive);
  fprintf(state_out, "fdc_motor_on=%d\n", fdc.motor_on);
  fprintf(state_out, "fdc_status=%02X\n", fdc.status);
  fprintf(state_out, "fdc_track=%02X\n", fdc.track);
  fprintf(state_out, "fdc_physical_track=%02X\n", fdc.physical_track);
  fprintf(state_out, "fdc_sector=%02X\n", fdc.sector);
  fprintf(state_out, "fdc_data=%02X\n", fdc.data);
  fprintf(state_out, "fdc_command=%02X\n", fdc.command);
  fprintf(state_out, "fdc_buffer_pos=%u\n", fdc.buffer_pos);
  fprintf(state_out, "fdc_buffer_len=%u\n", fdc.buffer_len);
  fprintf(state_out, "fdc_drq_ticks=%u\n", fdc.drq_ticks);
  fprintf(state_out, "fdc_write_first_byte_pending=%d\n", fdc.write_first_byte_pending);
  fprintf(state_out, "fdc_data_reads=%lu\n", fdc_data_reads);
  fprintf(state_out, "usart_enabled=%d\n", usart.enabled);
  fprintf(state_out, "usart_mode=%02X\n", usart.mode_word);
  fprintf(state_out, "usart_command=%02X\n", usart.command);
  fprintf(state_out, "usart_status=%02X\n", usart_status());
  fprintf(state_out, "usart_tx_holding_full=%d\n", usart.tx_holding_full);
  fprintf(state_out, "usart_tx_shift_busy=%d\n", usart.tx_busy);
  fprintf(state_out, "usart_fault_tx_stuck=%d\n", usart.fault_tx_stuck);
  fprintf(state_out, "usart_fault_tx_stuck_permanent=%d\n", usart.fault_tx_stuck_permanent);
  fprintf(state_out, "usart_fault_tx_stuck_once_enabled=%d\n", usart.fault_tx_stuck_once_enabled);
  fprintf(state_out, "usart_fault_tx_stuck_once_fired=%d\n", usart.fault_tx_stuck_once_fired);
  fprintf(state_out, "usart_fault_tx_stuck_once_value=%02X\n", usart.fault_tx_stuck_once_value);
  fprintf(state_out, "usart_fault_tx_not_ready_once_after_enabled=%d\n", usart.fault_tx_not_ready_once_after_enabled);
  fprintf(state_out, "usart_fault_tx_not_ready_once_after=%lu\n", usart.fault_tx_not_ready_once_after);
  fprintf(state_out, "usart_fault_tx_empty_low_after_enabled=%d\n", usart.fault_tx_empty_low_after_enabled);
  fprintf(state_out, "usart_fault_tx_empty_low_after=%lu\n", usart.fault_tx_empty_low_after);
  fprintf(state_out, "usart_fault_tx_stuck_once_recoveries=%lu\n", usart.fault_tx_stuck_once_recoveries);
  fprintf(state_out, "usart_tx_bytes=%lu\n", usart.tx_bytes);
  fprintf(state_out, "usart_rx_bytes=%lu\n", usart.rx_bytes);
  fprintf(state_out, "usart_rx_next_cyc=%lu\n", usart.rx_next_cyc);
  fprintf(state_out, "usart_tx_irq_armed=%d\n", usart_tx_irq_armed);
  fprintf(state_out, "usart_tx_irq_pending=%d\n", usart_tx_irq_pending);
  fprintf(state_out, "usart_rx_irq_pending=%d\n", usart_rx_irq_pending);
  fprintf(state_out, "usart_rx_irq_delay_once_enabled=%d\n",
          usart.fault_rx_irq_delay_once_enabled);
  fprintf(state_out, "usart_rx_irq_delay_once_fired=%d\n",
          usart.fault_rx_irq_delay_once_fired);
  fprintf(state_out, "usart_rx_irq_delay_once_after=%lu\n",
          usart.fault_rx_irq_delay_once_after);
  fprintf(state_out, "usart_rx_irq_delay_cycles=%lu\n",
          usart.fault_rx_irq_delay_cycles);
  for (int p = 0; p < 256; p++) {
    if (out_count[p] || in_count[p] || out_last[p])
      fprintf(state_out, "port_%02X=last:%02X,out:%lu,in:%lu\n",
              p, out_last[p], out_count[p], in_count[p]);
  }
  fclose(state_out);
  fprintf(stderr, "[CHECKPOINT] wrote %s and %s\n", ram_path, state_path);
}

int main(int argc, char** argv) {
  signal(SIGTERM, request_termination);
  signal(SIGINT, request_termination);
  pit_init();
  const char* rom_path = argc > 1 ? argv[1] : "ekta43.bin";
  unsigned long max_cyc = argc > 2 ? strtoul(argv[2], 0, 0) : 50000000UL;
  g_vw_limit            = argc > 3 ? strtoul(argv[3], 0, 0) : 0UL;   // 0 = no video-write limit
  unsigned long frame_cyc = argc > 4 ? strtoul(argv[4], 0, 0) : 0UL; // frame-interrupt period (cycles); 0 = off
  const char* checkpoint_cyc_env = getenv("JUKU_CHECKPOINT_CYC");
  unsigned long checkpoint_cyc = (checkpoint_cyc_env && checkpoint_cyc_env[0]) ? strtoul(checkpoint_cyc_env, 0, 0) : 0UL;
  const char* stop_pc_env = getenv("JUKU_STOP_PC");
  const char* stop_pc_rx_env = getenv("JUKU_STOP_PC_AFTER_USART_RX");
  int stop_pc_enabled = 0;
  unsigned long stop_pc = 0, stop_pc_after_usart_rx = 0;
  if (stop_pc_env && stop_pc_env[0]) {
    char* end = NULL;
    stop_pc = strtoul(stop_pc_env, &end, 0);
    if (!end || *end || stop_pc > 0xFFFF) {
      fprintf(stderr, "invalid JUKU_STOP_PC=%s (expected 0..0xFFFF)\n",
              stop_pc_env);
      return 2;
    }
    stop_pc_enabled = 1;
    if (stop_pc_rx_env && stop_pc_rx_env[0]) {
      end = NULL;
      stop_pc_after_usart_rx = strtoul(stop_pc_rx_env, &end, 0);
      if (!end || *end) {
        fprintf(stderr,
                "invalid JUKU_STOP_PC_AFTER_USART_RX=%s "
                "(expected byte count)\n",
                stop_pc_rx_env);
        return 2;
      }
    }
  }
  const char* rom_exec_reset_env = getenv("JUKU_ROM_EXEC_RESET_AT");
  unsigned long rom_exec_reset_at = 0;
  unsigned long rom_exec_resets = 0;
  if (rom_exec_reset_env && rom_exec_reset_env[0]) {
    char* end = NULL;
    rom_exec_reset_at = strtoul(rom_exec_reset_env, &end, 0);
    if (!end || *end || rom_exec_reset_at == 0 || rom_exec_reset_at > 0x3FFF) {
      fprintf(stderr,
              "invalid JUKU_ROM_EXEC_RESET_AT=%s (expected 1..0x3FFF)\n",
              rom_exec_reset_env);
      return 2;
    }
  }
  const char* stop_keys_done_env = getenv("JUKU_STOP_KEYS_DONE");
  int stop_keys_done = stop_keys_done_env && stop_keys_done_env[0] &&
                       strcmp(stop_keys_done_env, "0") != 0;
  const char* disable_settle_env = getenv("JUKU_DISABLE_SETTLE");
  int disable_settle = env_enabled(disable_settle_env);
  const char* stop_prompt_rx_env = getenv("JUKU_STOP_PROMPT_AFTER_USART_RX");
  unsigned long stop_prompt_after_rx = stop_prompt_rx_env && stop_prompt_rx_env[0]
      ? strtoul(stop_prompt_rx_env, NULL, 0) : 0;
  int stop_prompt_hit = 0;
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
  kbd_trace = getenv("JUKU_TRACE_KBD") && getenv("JUKU_TRACE_KBD")[0] &&
              strcmp(getenv("JUKU_TRACE_KBD"), "0") != 0;
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
  const char* bustrace_path = getenv("JUKU_BUS_TRACE");
  if (bustrace_path && bustrace_path[0]) {
    bustrace_fp = fopen(bustrace_path, "w");
    if (!bustrace_fp) {
      fprintf(stderr, "JUKU_BUS_TRACE=%s could not be opened for writing\n", bustrace_path);
      return 2;
    }
    const char* bustrace_limit_env = getenv("JUKU_BUS_TRACE_LIMIT");
    if (bustrace_limit_env && bustrace_limit_env[0])
      bustrace_limit = strtoul(bustrace_limit_env, NULL, 0);
  }
  const char* cart_path = getenv("JUKU_CART");
  timing_log = getenv("JUKU_TRACE_TIMING") && getenv("JUKU_TRACE_TIMING")[0] &&
               strcmp(getenv("JUKU_TRACE_TIMING"), "0") != 0;
  io_trace = getenv("JUKU_TRACE_IO") && getenv("JUKU_TRACE_IO")[0] &&
               strcmp(getenv("JUKU_TRACE_IO"), "0") != 0;
  const char* bank_trace_env = getenv("JUKU_TRACE_BANK");
  if (bank_trace_env && bank_trace_env[0])
    bank_trace = strcmp(bank_trace_env, "0") != 0;
  const char* usart_pty = getenv("JUKU_USART_PTY");
  const char* usart_fault = getenv("JUKU_USART_FAULT");
  const char* usart_transfer_cycles = getenv("JUKU_USART_TRANSFER_CYCLES");
  const char* usart_byte_cycles = getenv("JUKU_USART_BYTE_CYCLES");
  const char* usart_pit_clock_env = getenv("JUKU_USART_PIT_CLOCK");
  const char* usart_pit_cpu_hz_env = getenv("JUKU_USART_PIT_CPU_HZ");
  const char* ram_fault = getenv("JUKU_RAM_FAULT");
  const char* rom_consecutive_a12_low_env =
      getenv("JUKU_ROM_CONSECUTIVE_A12_LOW");
  const char* cpu_a12_increment_fault_env =
      getenv("JUKU_CPU_A12_INCREMENT_FAULT");
  const char* exec_byte_fault = getenv("JUKU_EXEC_BYTE_FAULT");
  const char* ram_drop_write = getenv("JUKU_RAM_DROP_WRITE");
  const char* ram_alias = getenv("JUKU_RAM_ALIAS");
  const char* dram_retention = getenv("JUKU_DRAM_RETENTION_CYCLES");
  const char* dram_retention_arm_pc_env =
      getenv("JUKU_DRAM_RETENTION_ARM_PC");
  const char* pic_fault = getenv("JUKU_PIC_FAULT");
  const char* ppi_fault = getenv("JUKU_PPI_FAULT");
  const char* pit_fault = getenv("JUKU_PIT_FAULT");
  if (exec_byte_fault && exec_byte_fault[0]) {
    unsigned address, value;
    char trailing;
    if (sscanf(exec_byte_fault, "%x:%x%c", &address, &value, &trailing) != 2 ||
        address > 0xFFFF || value > 0xFF) {
      fprintf(stderr,
              "invalid JUKU_EXEC_BYTE_FAULT=%s (expected ADDR:VALUE)\n",
              exec_byte_fault);
      return 2;
    }
    exec_byte_fault_enabled = 1;
    exec_byte_fault_addr = (uint16_t)address;
    exec_byte_fault_value = (uint8_t)value;
    fprintf(stderr, "[EXEC] byte fault address=0x%04X value=0x%02X\n",
            exec_byte_fault_addr, exec_byte_fault_value);
  }
  rom_consecutive_a12_low =
      rom_consecutive_a12_low_env && rom_consecutive_a12_low_env[0] &&
      strcmp(rom_consecutive_a12_low_env, "0") != 0;
  if (rom_consecutive_a12_low)
    fprintf(stderr, "[ROM] consecutive-read A12-low fault enabled\n");
  cpu_a12_increment_fault =
      cpu_a12_increment_fault_env && cpu_a12_increment_fault_env[0] &&
      strcmp(cpu_a12_increment_fault_env, "0") != 0;
  if (cpu_a12_increment_fault)
    fprintf(stderr, "[CPU] A12 increment-retention fault enabled\n");
  if (usart_transfer_cycles && usart_transfer_cycles[0]) {
    usart.transfer_cycles = strtoul(usart_transfer_cycles, 0, 0);
    if (!usart.transfer_cycles) usart.transfer_cycles = 1;
  }
  if (usart_byte_cycles && usart_byte_cycles[0]) {
    usart.byte_cycles = strtoul(usart_byte_cycles, 0, 0);
    if (!usart.byte_cycles) usart.byte_cycles = 1;
  }
  usart_pit_clock = env_enabled(usart_pit_clock_env);
  if (usart_pit_cpu_hz_env && usart_pit_cpu_hz_env[0]) {
    char* end = NULL;
    errno = 0;
    usart_pit_cpu_hz = strtoul(usart_pit_cpu_hz_env, &end, 0);
    if (errno || !end || *end || !usart_pit_cpu_hz) {
      fprintf(stderr, "invalid JUKU_USART_PIT_CPU_HZ=%s\n",
              usart_pit_cpu_hz_env);
      return 2;
    }
  }
  if (usart_fault && usart_fault[0]) {
    if (strcmp(usart_fault, "tx_stuck") == 0) {
      usart.fault_tx_stuck_permanent = 1;
    } else if (strncmp(usart_fault, "tx_stuck_once:", 14) == 0) {
      unsigned value;
      char trailing;
      if (sscanf(usart_fault, "tx_stuck_once:%x%c", &value, &trailing) != 1 ||
          value > 0xFF) {
        fprintf(stderr,
                "unknown JUKU_USART_FAULT=%s "
                "(expected tx_stuck or tx_stuck_once:BYTE)\n",
                usart_fault);
        return 2;
      }
      usart.fault_tx_stuck_once_enabled = 1;
      usart.fault_tx_stuck_once_value = (uint8_t)value;
    } else if (strncmp(usart_fault, "tx_not_ready_once_after:", 24) == 0) {
      unsigned long count;
      char trailing;
      if (sscanf(usart_fault, "tx_not_ready_once_after:%lu%c", &count, &trailing) != 1) {
        fprintf(stderr,
                "unknown JUKU_USART_FAULT=%s (expected tx_stuck, "
                "tx_stuck_once:BYTE, or tx_not_ready_once_after:COUNT)\n",
                usart_fault);
        return 2;
      }
      usart.fault_tx_not_ready_once_after_enabled = 1;
      usart.fault_tx_not_ready_once_after = count;
    } else if (strncmp(usart_fault, "rx_irq_delay_once_after:", 24) == 0) {
      unsigned long count, delay;
      char trailing;
      if (sscanf(usart_fault, "rx_irq_delay_once_after:%lu:%lu%c",
                 &count, &delay, &trailing) != 2 || !delay) {
        fprintf(stderr,
                "unknown JUKU_USART_FAULT=%s (expected "
                "rx_irq_delay_once_after:COUNT:CYCLES)\n",
                usart_fault);
        return 2;
      }
      usart.fault_rx_irq_delay_once_enabled = 1;
      usart.fault_rx_irq_delay_once_after = count;
      usart.fault_rx_irq_delay_cycles = delay;
    } else {
      unsigned long count;
      char trailing;
      if (sscanf(usart_fault, "tx_empty_low_after:%lu%c", &count, &trailing) != 1) {
        fprintf(stderr,
                "unknown JUKU_USART_FAULT=%s (expected tx_stuck, "
                "tx_stuck_once:BYTE, tx_not_ready_once_after:COUNT, "
                "rx_irq_delay_once_after:COUNT:CYCLES, or "
                "tx_empty_low_after:COUNT)\n",
                usart_fault);
        return 2;
      }
      usart.fault_tx_empty_low_after_enabled = 1;
      usart.fault_tx_empty_low_after = count;
    }
  }
  if (pic_fault && pic_fault[0]) {
    unsigned stuck_low, stuck_high;
    char trailing;
    if (sscanf(pic_fault, "%x:%x%c", &stuck_low, &stuck_high, &trailing) != 2 ||
        stuck_low > 0xFF || stuck_high > 0xFF || (stuck_low & stuck_high)) {
      fprintf(stderr,
              "invalid JUKU_PIC_FAULT=%s (expected STUCK_LOW:STUCK_HIGH)\n",
              pic_fault);
      return 2;
    }
    pic_fault_enabled = 1;
    pic_fault_stuck_low = (uint8_t)stuck_low;
    pic_fault_stuck_high = (uint8_t)stuck_high;
    fprintf(stderr, "[PIC] IMR fault stuck-low=0x%02X stuck-high=0x%02X\n",
            pic_fault_stuck_low, pic_fault_stuck_high);
  }
  if (ppi_fault && ppi_fault[0]) {
    unsigned port, stuck_low, stuck_high;
    char trailing;
    if (sscanf(ppi_fault, "%x:%x:%x%c", &port, &stuck_low, &stuck_high,
               &trailing) != 3 ||
        port < 0x0C || port > 0x0E || stuck_low > 0xFF ||
        stuck_high > 0xFF || (stuck_low & stuck_high)) {
      fprintf(stderr,
              "invalid JUKU_PPI_FAULT=%s "
              "(expected PORT:STUCK_LOW:STUCK_HIGH, PORT=0C..0E)\n",
              ppi_fault);
      return 2;
    }
    ppi_fault_enabled = 1;
    ppi_fault_port = (uint8_t)port;
    ppi_fault_stuck_low = (uint8_t)stuck_low;
    ppi_fault_stuck_high = (uint8_t)stuck_high;
    fprintf(stderr,
            "[PPI] D27 port 0x%02X fault stuck-low=0x%02X stuck-high=0x%02X\n",
            ppi_fault_port, ppi_fault_stuck_low, ppi_fault_stuck_high);
  }
  if (pit_fault && pit_fault[0]) {
    unsigned port, stuck_low, stuck_high;
    char trailing;
    if (sscanf(pit_fault, "%x:%x:%x%c", &port, &stuck_low, &stuck_high,
               &trailing) != 3 || port < 0x10 || port > 0x1A ||
        (port & 3) == 3 || stuck_low > 0xFF || stuck_high > 0xFF ||
        (stuck_low & stuck_high)) {
      fprintf(stderr,
              "invalid JUKU_PIT_FAULT=%s "
              "(expected PORT:STUCK_LOW:STUCK_HIGH, "
              "PORT=10..12/14..16/18..1A)\n",
              pit_fault);
      return 2;
    }
    pit_fault_enabled = 1;
    pit_fault_port = (uint8_t)port;
    pit_fault_stuck_low = (uint8_t)stuck_low;
    pit_fault_stuck_high = (uint8_t)stuck_high;
    fprintf(stderr,
            "[PIT] port 0x%02X fault stuck-low=0x%02X stuck-high=0x%02X\n",
            pit_fault_port, pit_fault_stuck_low, pit_fault_stuck_high);
  }
  if (ram_fault && ram_fault[0]) {
    unsigned address, stuck_low, stuck_high;
    char trailing;
    int parsed;
    if (ram_fault[0] == '*' && ram_fault[1] == ':') {
      parsed = sscanf(ram_fault + 2, "%x:%x%c", &stuck_low, &stuck_high,
                      &trailing);
      address = 0;
      ram_fault_all = 1;
    } else {
      parsed = sscanf(ram_fault, "%x:%x:%x%c", &address, &stuck_low,
                      &stuck_high, &trailing);
    }
    if (parsed != (ram_fault_all ? 2 : 3) || address > 0xFFFF ||
        stuck_low > 0xFF || stuck_high > 0xFF ||
        (stuck_low & stuck_high)) {
      fprintf(stderr,
              "invalid JUKU_RAM_FAULT=%s "
              "(expected ADDR:STUCK_LOW:STUCK_HIGH or *:STUCK_LOW:STUCK_HIGH)\n",
              ram_fault);
      return 2;
    }
    ram_fault_enabled = 1;
    ram_fault_addr = (uint16_t)address;
    ram_fault_stuck_low = (uint8_t)stuck_low;
    ram_fault_stuck_high = (uint8_t)stuck_high;
    if (ram_fault_all)
      fprintf(stderr, "[RAM] global fault stuck-low=0x%02X stuck-high=0x%02X\n",
              ram_fault_stuck_low, ram_fault_stuck_high);
    else
      fprintf(stderr,
              "[RAM] fault address=0x%04X stuck-low=0x%02X stuck-high=0x%02X\n",
              ram_fault_addr, ram_fault_stuck_low, ram_fault_stuck_high);
  }
  if (ram_drop_write && ram_drop_write[0]) {
    unsigned address, value, count;
    char trailing;
    if (sscanf(ram_drop_write, "%x:%x:%u%c", &address, &value, &count,
               &trailing) != 3 || address > 0xFFFF || value > 0xFF || !count) {
      fprintf(stderr,
              "invalid JUKU_RAM_DROP_WRITE=%s (expected ADDR:VALUE:COUNT)\n",
              ram_drop_write);
      return 2;
    }
    ram_drop_write_enabled = 1;
    ram_drop_write_addr = (uint16_t)address;
    ram_drop_write_value = (uint8_t)value;
    ram_drop_write_remaining = count;
    fprintf(stderr,
            "[RAM] will drop %u write(s) address=0x%04X value=0x%02X\n",
            count, ram_drop_write_addr, ram_drop_write_value);
  }
  if (ram_alias && ram_alias[0]) {
    unsigned page_a, page_b;
    char trailing;
    if (sscanf(ram_alias, "%x:%x%c", &page_a, &page_b, &trailing) != 2 ||
        page_a > 0xFF || page_b > 0xFF || page_a == page_b) {
      fprintf(stderr, "invalid JUKU_RAM_ALIAS=%s (expected distinct PAGE_A:PAGE_B)\n",
              ram_alias);
      return 2;
    }
    ram_alias_enabled = 1;
    ram_alias_page_a = (uint8_t)page_a;
    ram_alias_page_b = (uint8_t)page_b;
    fprintf(stderr, "[RAM] alias logical page 0x%02X -> physical page 0x%02X\n",
            ram_alias_page_b, ram_alias_page_a);
  }
  if (dram_retention && dram_retention[0]) {
    char* end = NULL;
    errno = 0;
    dram_retention_cycles = strtoul(dram_retention, &end, 0);
    if (errno || !end || *end || !dram_retention_cycles) {
      fprintf(stderr,
              "invalid JUKU_DRAM_RETENTION_CYCLES=%s (expected positive integer)\n",
              dram_retention);
      return 2;
    }
    fprintf(stderr, "[DRAM] retention limit=%lu cycles across 128 rows\n",
            dram_retention_cycles);
    if (dram_retention_arm_pc_env && dram_retention_arm_pc_env[0]) {
      unsigned address;
      char trailing;
      if (sscanf(dram_retention_arm_pc_env, "%x%c", &address, &trailing) != 1 ||
          address > 0xFFFF) {
        fprintf(stderr,
                "invalid JUKU_DRAM_RETENTION_ARM_PC=%s (expected address)\n",
                dram_retention_arm_pc_env);
        return 2;
      }
      dram_retention_arm_pc_enabled = 1;
      dram_retention_arm_pc = (uint16_t)address;
      dram_retention_armed = 0;
      fprintf(stderr, "[DRAM] retention waits for pc=0x%04X\n",
              dram_retention_arm_pc);
    }
  }
  if (env_enabled(usart_pty) && usart_open_transport(usart_pty) != 0) {
    fprintf(stderr, "JUKU_USART_PTY=%s could not be opened: %s\n", usart_pty, strerror(errno));
    return 2;
  }
  const char* fdc_bus_invert_env = getenv("JUKU_FDC_BUS_INVERT");
  fdc_bus_invert = fdc_bus_invert_env && fdc_bus_invert_env[0] &&
                   strcmp(fdc_bus_invert_env, "0") != 0;
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
    const char* deleted_marks_path = getenv("JUKU_DISK_DELETED_MARKS");
    if (deleted_marks_path && deleted_marks_path[0]) {
      rc = juk_disk_attach_deleted_marks(&disk, deleted_marks_path);
      if (rc != 0) {
        fprintf(stderr, "JUKU_DISK_DELETED_MARKS=%s could not be attached (rc=%d)\n",
                deleted_marks_path, rc);
        juk_disk_close(&disk);
        return 2;
      }
    }
    juku_fdc_init(&fdc, &disk);
    fdc_enabled = 1;
    fprintf(stderr, "loaded JUKU disk image %s (%ld bytes, %d side%s, %s, FDC bus %s)\n",
            disk_path, disk.size, disk.heads, disk.heads == 1 ? "" : "s",
            disk_writable ? "writable" : "read-only",
            fdc_bus_invert ? "inverting" : "non-inverting");
    if (deleted_marks_path && deleted_marks_path[0])
      fprintf(stderr, "loaded JUKU deleted-record metadata %s\n", deleted_marks_path);
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
  cpu.fault_a12_increment_high_loss = cpu_a12_increment_fault;
  cpu.userdata = &cpu;
  cpu.read_byte = rb; cpu.write_byte = wb;
  cpu.port_in = pin;  cpu.port_out = pout;
  cpu.pc = 0x0000;

  unsigned long last_write_total = 0, writes_total, idle_cyc = 0;
  unsigned long usart_rx_irq_count = 0, usart_tx_irq_count = 0;
  unsigned long frame_irq_count = 0;
  static uint32_t pchist[MEM_SIZE];

  // Optional interactive console (JUKU_CONSOLE_PTY).
  const char* console_env = getenv("JUKU_CONSOLE_PTY");
  if (console_env && console_env[0]) {
    console_fd = open_serial_endpoint(console_env, "TERM");
    if (console_fd < 0) {
      fprintf(stderr, "JUKU_CONSOLE_PTY=%s could not be opened\n", console_env);
      return 2;
    }
    const char* out_pc = getenv("JUKU_CONSOLE_OUT_PC");
    const char* in_pc = getenv("JUKU_CONSOLE_IN_PC");
    if (out_pc && out_pc[0]) console_out_pc = (uint16_t)strtoul(out_pc, NULL, 0);
    if (in_pc && in_pc[0]) console_in_pc = (uint16_t)strtoul(in_pc, NULL, 0);
    (void)console_in_pc;
    kbd_enabled = 1;
    // Scripted JUKU_KEYS and an operator's typing share one queue: the script
    // plays first, then whatever is typed is appended behind it. A run with no
    // script drops the "wait for the banner" gate, since an operator chooses
    // when to type.
    console_queue[0] = 0;
    console_len = 0;
    if (kbd_str && kbd_str[0]) {
      for (const char* c = kbd_str; *c && console_len + 1 < CONSOLE_QUEUE; c++)
        console_queue[console_len++] = *c;
      console_queue[console_len] = 0;
    } else {
      kbd_start_vram = 0;
    }
    kbd_str = console_queue;
    kbd_pos = 0;
    fprintf(stderr, "[TERM] console attached; WRCHR hook=%04X\n",
            console_out_pc);
  }

  // Optional real-time pacing (JUKU_REALTIME_HZ). Sleeps whenever simulated
  // time has run ahead of wall-clock time, so a session takes as long as it
  // would on the machine. Checked on a coarse cycle interval and only slept
  // when the lead exceeds one slice, which keeps the syscall rate low; the
  // pacer never speeds a slow host up, so it cannot mask a lagging model.
  const char* realtime_env = getenv("JUKU_REALTIME_HZ");
  unsigned long realtime_hz = 0;
  if (realtime_env && realtime_env[0]) {
    char* endptr = NULL;
    realtime_hz = strtoul(realtime_env, &endptr, 0);
    if (endptr == realtime_env || (endptr && *endptr) || realtime_hz == 0) {
      fprintf(stderr,
              "invalid JUKU_REALTIME_HZ=%s (expected a positive cycle rate)\n",
              realtime_env);
      return 2;
    }
    if (realtime_hz == 1) realtime_hz = 2000000UL;   // nominal Juku clock
    fprintf(stderr, "[SPEED] pacing to %lu cycles/second\n", realtime_hz);
  }
  const unsigned long realtime_slice = 2000;   // ~1 ms of machine time at 2 MHz
  unsigned long realtime_next = realtime_slice;
  struct timespec realtime_start;
  if (realtime_hz) clock_gettime(CLOCK_MONOTONIC, &realtime_start);

  int chk_logs = 0;
  while (cpu.cyc < max_cyc && (!cpu.halted || frame_cyc) &&
         !(g_vw_limit && g_vw >= g_vw_limit) &&
         !(checkpoint_cyc && cpu.cyc >= checkpoint_cyc) &&
         !(stop_pc_enabled && usart.rx_bytes >= stop_pc_after_usart_rx &&
           cpu.pc == stop_pc) &&
         !(stop_keys_done && kbd_str && !kbd_str[kbd_pos]) &&
         !stop_prompt_hit &&
         !terminate_requested &&
         !(stop_fdc_data_reads && fdc_data_reads >= stop_fdc_data_reads)) {
    if (dram_retention_arm_pc_enabled && !dram_retention_armed &&
        cpu.pc == dram_retention_arm_pc) {
      dram_retention_armed = 1;
      for (unsigned row = 0; row < 128; row++)
        dram_last_refresh[row] = cpu.cyc;
      memset(dram_coverage_seen, 0, sizeof(dram_coverage_seen));
      dram_coverage_count = 0;
      dram_coverage_start = cpu.cyc;
      dram_full_coverage_reported = 0;
      fprintf(stderr, "[DRAM] retention armed at pc=0x%04X cyc=%lu\n",
              cpu.pc, cpu.cyc);
    }
    if (rom_exec_reset_at && mode == 0 && cpu.pc >= rom_exec_reset_at &&
        cpu.pc < 0x4000) {
      rom_exec_resets++;
      if (rom_exec_resets <= 32)
        fprintf(stderr,
                "[EXEC] reset #%lu at ROM pc=%04X boundary=%04lX cyc=%lu\n",
                rom_exec_resets, cpu.pc, rom_exec_reset_at, cpu.cyc);
      cpu.pc = 0;
      cpu.iff = 0;
      cpu.halted = 0;
      set_mode(0);
    }
    pchist[cpu.pc]++;
    if (cpu.pc == 0x03E0 && chk_logs < 12)            // checksum entry: HL=ptr, DE=count
      fprintf(stderr, "[CHK] entry HL=%04X DE=%04X mode=%d\n",
              (cpu.h<<8)|cpu.l, (cpu.d<<8)|cpu.e, mode);
    if (cpu.pc == 0x03E6 && chk_logs++ < 12)           // compare: A=stored, B=computed
      fprintf(stderr, "[CHK] cmp computed=%02X stored=%02X %s\n",
              cpu.b, cpu.a, cpu.b==cpu.a ? "OK" : "**MISMATCH**");
    if (console_fd >= 0) {
      // The firmware's console character is in A when it enters the ROM's
      // WRCHR vector; mirror it to the terminal verbatim. The firmware sends
      // its own CR/LF pairs, so synthesising a newline here would double every
      // line break. The same routine runs at its banked address in modes 1/2
      // and at its ROM-file address in mode 0, so accept either.
      if (cpu.pc == console_out_pc ||
          (console_out_pc >= 0xC000 && cpu.pc == (uint16_t)(console_out_pc - 0xC000))) {
        char out = (char)cpu.a;
        ssize_t ignored = write(console_fd, &out, 1);
        (void)ignored;
      }
      if ((cpu.cyc & 0x3FF) == 0) console_poll();
    }
    if (realtime_hz && cpu.cyc >= realtime_next) {
      realtime_next = cpu.cyc + realtime_slice;
      struct timespec now;
      clock_gettime(CLOCK_MONOTONIC, &now);
      double elapsed = (double)(now.tv_sec - realtime_start.tv_sec) +
                       (double)(now.tv_nsec - realtime_start.tv_nsec) / 1e9;
      double due = (double)cpu.cyc / (double)realtime_hz;
      double lead = due - elapsed;
      if (lead > 0.0005) {                     // only sleep a worthwhile lead
        struct timespec nap;
        nap.tv_sec = (time_t)lead;
        nap.tv_nsec = (long)((lead - (double)nap.tv_sec) * 1e9);
        nanosleep(&nap, NULL);
      }
    }
    i8080_step(&cpu);
    sync_fdc_time(&cpu);
    usart_poll(cpu.cyc);
    // D11 RxRDY and TxRDY directly drive D10/PIC IR2 and IR3.  NetBios is
    // interrupt-driven, so status-register emulation alone cannot put its
    // queued request onto the wire.
    if (usart_rx_irq_pending &&
        usart.fault_rx_irq_delay_once_enabled &&
        !usart.fault_rx_irq_delay_once_fired &&
        usart.rx_bytes >= usart.fault_rx_irq_delay_once_after) {
      usart.fault_rx_irq_delay_once_fired = 1;
      usart.fault_rx_irq_delay_until =
          cpu.cyc + usart.fault_rx_irq_delay_cycles;
      fprintf(stderr,
              "[USART] delaying one RxRDY IRQ after byte=%lu until cyc=%lu\n",
              usart.rx_bytes, usart.fault_rx_irq_delay_until);
    }
    if (usart_rx_irq_pending &&
        (!usart.fault_rx_irq_delay_once_fired ||
         cpu.cyc >= usart.fault_rx_irq_delay_until) &&
        take_pic_irq(&cpu, 2, "USART RxRDY", &usart_rx_irq_count))
      usart_rx_irq_pending = 0;
    if (usart_tx_irq_pending &&
        take_pic_irq(&cpu, 3, "USART TxRDY", &usart_tx_irq_count))
      usart_tx_irq_pending = 0;
    // --- frame interrupt: 8253 VER-RTR -> 8259 IR5 -> CPU (MCS-80 CALL to the ICW vector) ---
    if (frame_cyc && cpu.cyc >= next_frame) {
      next_frame += frame_cyc;
      int frame_taken = take_pic_irq(&cpu, 5, "frame", &frame_irq_count);
      if (kbd_trace && kbd_str && kbd_str[kbd_pos])
        fprintf(stderr,
                "[KBD] frame char=%02X pos=%d phase=%d irq=%s iff=%d mask=%02X "
                "pc=%04X cyc=%lu g_vw=%lu\n",
                (unsigned char)kbd_str[kbd_pos], kbd_pos, kbd_phase,
                frame_taken ? "taken" : "blocked", cpu.iff, pic_mask,
                cpu.pc, cpu.cyc, g_vw);
      if (stop_prompt_after_rx && usart.rx_bytes >= stop_prompt_after_rx &&
          ekdos_prompt_visible())
        stop_prompt_hit = 1;
      // Scripted key contacts follow physical frame time. They may be sampled
      // either by the monitor's frame ISR or by a RAM-resident polling BIOS;
      // PIC masking must not freeze a real key contact in time.
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
    if (!disable_settle && (cpu.cyc & 0xFFFFF) == 0) {
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
  if (stop_keys_done && kbd_str && !kbd_str[kbd_pos])
    fprintf(stderr, "[KBD] stopped after completing scripted input at cyc=%lu pc=%04X g_vw=%lu\n",
            cpu.cyc, cpu.pc, g_vw);
  if (stop_pc_enabled && usart.rx_bytes >= stop_pc_after_usart_rx &&
      cpu.pc == stop_pc)
    fprintf(stderr,
            "[EXEC] stopped before pc=%04lX after %lu USART receive bytes\n",
            stop_pc, usart.rx_bytes);
  if (stop_prompt_hit)
    fprintf(stderr, "[EXEC] stopped at A> prompt after %lu USART receive bytes\n",
            usart.rx_bytes);

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

  FILE* o = fopen("vram.bin", "wb");
  if (o) { fwrite(&ram[VRAM_BASE], 1, (size_t)VID_STRIDE * VID_LINES, o); fclose(o);
           printf("\nwrote vram.bin (%d bytes, %dx%d @ 0x%04X)\n",
                  VID_STRIDE * VID_LINES, VID_STRIDE * 8, VID_LINES, VRAM_BASE); }
  if (fdc_enabled) juk_disk_close(&disk);
  if (usart.fd >= 0) close(usart.fd);
  if (rdtrace_fp) fclose(rdtrace_fp);
  if (bustrace_fp) fclose(bustrace_fp);
  return 0;
}
