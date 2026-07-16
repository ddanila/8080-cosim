#define _POSIX_C_SOURCE 200809L

#include "../cosim/i8080.h"
#include "../cosim/juku_fdc.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>


enum {
  ROM_SIZE = 0x4000,
  VRAM_BASE = 0xD800,
  VRAM_BYTES = 40 * 241,
  RETURN_PC = 0xB123,
  DMA_ADDR = 0x4000,
  SECOND_DMA_ADDR = 0x4100,
  THIRD_DMA_ADDR = 0x4200,
  FOURTH_DMA_ADDR = 0x4300,
  SCRATCH_ADDR = 0x5000,
  CACHE_READ_ADDR = 0x5100,
  SECOND_CACHE_READ_ADDR = 0x5200,
  UNTOUCHED_CACHE_READ_ADDR = 0x5300,
  FOURTH_CACHE_READ_ADDR = 0x5400,
  RAM_DISK_BANKS = 6,
  RAM_DISK_WINDOW = 0x8000,
  RAM_DISK_TRACKS = RAM_DISK_BANKS * 2,
  RAM_DISK_ENDPOINTS = 2,
  BIOS_CONST = 0xCA06,
  BIOS_CONIN = 0xCA09,
  BIOS_CONOUT = 0xCA0C,
  BIOS_LIST = 0xCA0F,
  BIOS_PUNCH = 0xCA12,
  BIOS_READER = 0xCA15,
  BIOS_HOME = 0xCA18,
  BIOS_SELDSK = 0xCA1B,
  BIOS_SETTRK = 0xCA1E,
  BIOS_SETSEC = 0xCA21,
  BIOS_SETDMA = 0xCA24,
  BIOS_READ = 0xCA27,
  BIOS_WRITE = 0xCA2A,
  BIOS_LISTST = 0xCA2D,
  BIOS_SECTRAN = 0xCA30,
};


static const uint8_t RAMDISK_SIGNATURE[] = {
  0x0F, 'R', 'a', 'm', 'D', 'i', 's', 'k', 0x00, 0xD3, 0xF9, 0x73,
};


typedef struct {
  uint8_t ram[65536];
  uint8_t ramdisk[RAM_DISK_BANKS][RAM_DISK_WINDOW];
  uint8_t rom[ROM_SIZE];
  uint8_t out[256];
  uint8_t portc;
  unsigned monitor_trampoline_entries;
  unsigned vram_writes;
  int keyboard_held;
  int keyboard_shift;
  uint8_t keyboard_col;
  uint8_t keyboard_bit;
  uint8_t keyboard_active_value;
  unsigned keyboard_reads;
  unsigned keyboard_active_reads;
  unsigned fdc_commands;
  uint8_t command_log[16];
  unsigned command_writes;
  unsigned data_writes;
  unsigned write_protect_status_reads;
  uint8_t write_command;
  unsigned ram_bank;
  int ramdisk_present;
  juku_fdc fdc;
} fixture;


static int overlay(const fixture* f, uint16_t address, unsigned* index) {
  switch (f->portc & 3) {
    case 0:
      if (address <= 0x3FFF) {
        *index = address;
        return 1;
      }
      break;
    case 1:
      if (address >= 0xD800) {
        *index = 0x1800u + address - 0xD800u;
        return 1;
      }
      break;
    case 2:
      if (address >= 0x4000 && address <= 0xBFFF) return 2;
      if (address >= 0xD800) {
        *index = 0x1800u + address - 0xD800u;
        return 1;
      }
      break;
  }
  return 0;
}


static uint8_t read_byte(void* opaque, uint16_t address) {
  fixture* f = opaque;
  if (address == 0xD7E7) f->monitor_trampoline_entries++;
  unsigned index = 0;
  int source = overlay(f, address, &index);
  if (source == 1) return f->rom[index];
  if (source == 2) return 0xFF;  // no expansion cartridge installed
  if (address >= 0x4000 && address <= 0xBFFF && f->ram_bank < RAM_DISK_BANKS) {
    if (!f->ramdisk_present) return 0xFF;
    return f->ramdisk[f->ram_bank][address - 0x4000];
  }
  return f->ram[address];
}


static void write_byte(void* opaque, uint16_t address, uint8_t value) {
  fixture* f = opaque;
  unsigned index = 0;
  if (overlay(f, address, &index)) return;
  if (address >= VRAM_BASE && address < VRAM_BASE + VRAM_BYTES) {
    f->vram_writes++;
  }
  if (address >= 0x4000 && address <= 0xBFFF && f->ram_bank < RAM_DISK_BANKS) {
    if (f->ramdisk_present) {
      f->ramdisk[f->ram_bank][address - 0x4000] = value;
    }
  } else {
    f->ram[address] = value;
  }
}


static uint8_t port_in(void* opaque, uint8_t port) {
  fixture* f = opaque;
  if (port == 0x05 && f->keyboard_held) {
    uint8_t value = 0xC0;             // both active-low SHIFT inputs released
    if (f->keyboard_shift) value &= (uint8_t)~0x40;
    if ((f->out[0x04] & 0x0F) == f->keyboard_col) {
      value |= (uint8_t)(((~f->keyboard_bit) & 7) << 1);
      f->keyboard_active_value = value;
      f->keyboard_active_reads++;
    } else {
      value |= 0x0F;                  // 74148 GS released outside key column
    }
    f->keyboard_reads++;
    return value;
  }
  if (port >= 0x1C && port <= 0x1F) {
    uint8_t value = juku_fdc_read(&f->fdc, port & 3);
    if (port == 0x1C && (value & 0x40)) f->write_protect_status_reads++;
    return value;
  }
  return f->out[port];
}


static void update_portc(fixture* f, uint8_t value) {
  f->portc = value;
  f->out[0x06] = value;
  juku_fdc_portc(&f->fdc, value);
}


static void port_out(void* opaque, uint8_t port, uint8_t value) {
  fixture* f = opaque;
  f->out[port] = value;
  if (port >= 0x1C && port <= 0x1F) {
    if (port == 0x1C && f->fdc_commands < sizeof(f->command_log)) {
      f->command_log[f->fdc_commands++] = value;
    }
    if (port == 0x1C && (value & 0xE0) == 0xA0) {
      f->command_writes++;
      f->write_command = value;
    }
    if (port == 0x1F && f->fdc.write_transfer) f->data_writes++;
    juku_fdc_write(&f->fdc, port & 3, value);
  } else if (port == 0x04 && (value & 0x20)) {
    f->ram_bank = f->ramdisk_present ? (((value & 7) - 1u) & 7u) : 6u;
  } else if (port == 0x06) {
    update_portc(f, value);
  } else if (port == 0x07) {
    if (value & 0x80) update_portc(f, 0);
    else {
      unsigned bit = (value >> 1) & 7;
      uint8_t next = value & 1 ? (uint8_t)(f->portc | (1u << bit))
                               : (uint8_t)(f->portc & ~(1u << bit));
      update_portc(f, next);
    }
  }
}


static int write_image(const char* path) {
  FILE* fp = fopen(path, "wb");
  if (!fp) return 1;
  uint8_t zero[512] = {0};
  for (int i = 0; i < 80 * 2 * 10; i++) {
    if (fwrite(zero, 1, sizeof(zero), fp) != sizeof(zero)) {
      fclose(fp);
      return 1;
    }
  }
  return fclose(fp) != 0;
}


static int load_rom(uint8_t rom[ROM_SIZE]) {
  static const uint8_t frame_vector[] = {0xCD, 0x9F, 0xD7};
  static const uint8_t ramdisk_vector[] = {0xC3, 0xB3, 0xE9};
  static const uint8_t consta_entry[] = {0xCD, 0x5B, 0xD8};
  static const uint8_t rdchr_entry[] = {0xC3, 0xD9, 0xD9};
  static const uint8_t wrchr_entry[] = {0xC3, 0xE3, 0xD9};
  static const uint8_t printch_entry[] = {0xC3, 0xF1, 0xD7};
  FILE* fp = fopen("roms/ekta37.bin", "rb");
  if (!fp) return 1;
  size_t got = fread(rom, 1, ROM_SIZE, fp);
  int failed = got != ROM_SIZE || fclose(fp) != 0 ||
               memcmp(&rom[0x3ED4], frame_vector, sizeof(frame_vector)) != 0 ||
               memcmp(&rom[0x3F5C], ramdisk_vector, sizeof(ramdisk_vector)) != 0 ||
               memcmp(&rom[0x3F98], consta_entry, sizeof(consta_entry)) != 0 ||
               memcmp(&rom[0x3FD3], rdchr_entry, sizeof(rdchr_entry)) != 0 ||
               memcmp(&rom[0x3FD9], wrchr_entry, sizeof(wrchr_entry)) != 0 ||
               memcmp(&rom[0x3FEE], printch_entry, sizeof(printch_entry)) != 0 ||
               memcmp(&rom[0x29A7], RAMDISK_SIGNATURE,
                      sizeof(RAMDISK_SIGNATURE)) != 0;
  return failed;
}


static int load_boot_ram(uint8_t ram[65536], const char* path) {
  static const uint8_t expected_trampoline[] = {
    0xF5, 0xDB, 0x06, 0xE6, 0xFC, 0xB4, 0xD3, 0x06, 0xF1, 0xC9,
  };
  static const uint16_t exercised_vectors[] = {
    BIOS_CONST, BIOS_CONIN, BIOS_CONOUT, BIOS_LIST,
    BIOS_PUNCH, BIOS_READER, BIOS_HOME,
    BIOS_SELDSK, BIOS_SETTRK,
    BIOS_SETSEC, BIOS_SETDMA,
    BIOS_READ, BIOS_WRITE, BIOS_LISTST, BIOS_SECTRAN,
  };
  FILE* fp = fopen(path, "rb");
  if (!fp) return 1;
  size_t got = fread(ram, 1, 65536, fp);
  int failed = got != 65536 || fclose(fp) != 0 ||
               memcmp(&ram[0xD7E7], expected_trampoline,
                      sizeof(expected_trampoline)) != 0 ||
               ram[0xD7F1] != 0xC3 || ram[0xD7F2] != 0xA2 ||
               ram[0xD7F3] != 0xE2 ||
               ram[0xCA36] != 2;       // NoofRamDisk / RDNO
  for (unsigned i = 0;
       i < sizeof(exercised_vectors) / sizeof(exercised_vectors[0]); i++) {
    if (ram[exercised_vectors[i]] != 0xC3) failed = 1;
  }
  uint16_t punch_target = (uint16_t)(ram[BIOS_PUNCH + 1] |
                                     (ram[BIOS_PUNCH + 2] << 8));
  uint16_t reader_target = (uint16_t)(ram[BIOS_READER + 1] |
                                      (ram[BIOS_READER + 2] << 8));
  if (punch_target != reader_target || punch_target == UINT16_MAX ||
      ram[punch_target] != 0xAF || ram[punch_target + 1] != 0xC9) {
    failed = 1;
  }
  return failed;
}


static int run_rwfloppy_type(
    fixture* f, uint8_t request, uint8_t write_type, uint8_t logical_sector,
    uint16_t dma, unsigned long* total_cycles) {
  f->ram[0xD61D] = logical_sector;
  f->ram[0xD62E] = dma & 0xFF;
  f->ram[0xD62F] = dma >> 8;

  i8080 cpu;
  i8080_init(&cpu);
  cpu.userdata = f;
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.pc = 0xFF59;                    // public ROMBIOS RWFLOPPY entry -> E80B
  cpu.sp = 0xD2FC;                    // EKDOS STAK, outside RAM-disk window
  cpu.a = request;
  cpu.c = write_type;
  f->ram[cpu.sp] = RETURN_PC & 0xFF;
  f->ram[cpu.sp + 1] = RETURN_PC >> 8;
  while (cpu.pc != RETURN_PC && cpu.cyc < 2000000UL && !cpu.halted) i8080_step(&cpu);
  *total_cycles += cpu.cyc;
  if (cpu.pc == RETURN_PC) return 0;
  fprintf(stderr,
          "ROMBIOS RWFLOPPY: request=0x%02X sector=%u did not return "
          "(pc=%04X cyc=%lu TYP=%02X current=%02X)\n",
          request, logical_sector, cpu.pc, cpu.cyc, f->ram[0xD600], f->ram[0xD614]);
  return 1;
}


static int run_rwfloppy(
    fixture* f, uint8_t request, uint8_t logical_sector, uint16_t dma,
    unsigned long* total_cycles) {
  return run_rwfloppy_type(f, request, 0, logical_sector, dma, total_cycles);
}


static int run_ramdisk_select(
    fixture* f, uint8_t* result, unsigned long* total_cycles) {
  i8080 cpu;
  i8080_init(&cpu);
  cpu.userdata = f;
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.pc = 0xFF5C;                    // public ROMBIOS RAMDISKSEL -> E9B3
  cpu.sp = 0xD2FC;                    // EKDOS STAK, outside RAM-disk window
  cpu.a = 0;
  cpu.b = 0x5A;
  cpu.c = 0xA6;
  f->ram[cpu.sp] = RETURN_PC & 0xFF;
  f->ram[cpu.sp + 1] = RETURN_PC >> 8;
  while (cpu.pc != RETURN_PC && cpu.cyc < 2000000UL && !cpu.halted) i8080_step(&cpu);
  *total_cycles += cpu.cyc;
  *result = cpu.a;
  if (cpu.pc == RETURN_PC && cpu.b == 0x5A && cpu.c == 0xA6) return 0;
  fprintf(stderr,
          "ROMBIOS RAMDISKSEL: did not preserve ABI "
          "(pc=%04X bc=%02X%02X cyc=%lu)\n",
          cpu.pc, cpu.b, cpu.c, cpu.cyc);
  return 1;
}


static int run_bios_entry(
    fixture* f, uint16_t entry, uint8_t b, uint8_t c, uint16_t de,
    uint8_t* result_a, uint16_t* result_hl, unsigned long* total_cycles,
    const char* name) {
  i8080 cpu;
  i8080_init(&cpu);
  cpu.userdata = f;
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.pc = entry;
  cpu.sp = 0xD6F8;                    // caller stack; DoFunction owns STAK
  cpu.a = 0xA5;                       // expose routines that must clear A
  cpu.b = b;
  cpu.c = c;
  cpu.d = de >> 8;
  cpu.e = de & 0xFF;
  f->ram[cpu.sp] = RETURN_PC & 0xFF;
  f->ram[cpu.sp + 1] = RETURN_PC >> 8;
  while (cpu.pc != RETURN_PC && cpu.cyc < 2000000UL && !cpu.halted) i8080_step(&cpu);
  *total_cycles += cpu.cyc;
  if (result_a) *result_a = cpu.a;
  if (result_hl) *result_hl = (uint16_t)((cpu.h << 8) | cpu.l);
  if (cpu.pc == RETURN_PC) return 0;
  fprintf(stderr,
          "EKDOS %s: entry=%04X did not return (pc=%04X hl=%02X%02X cyc=%lu)\n",
          name, entry, cpu.pc, cpu.h, cpu.l, cpu.cyc);
  return 1;
}


static int run_bios_conin(
    fixture* f, uint8_t* result, unsigned* frame_interrupts,
    unsigned long* total_cycles) {
  enum { FRAME_CYCLES = 200000 };
  i8080 cpu;
  i8080_init(&cpu);
  cpu.userdata = f;
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.pc = BIOS_CONIN;
  cpu.sp = 0xD6F8;
  cpu.a = 0xA5;
  cpu.iff = 1;                         // prompt checkpoint runs with EI
  f->ram[cpu.sp] = RETURN_PC & 0xFF;
  f->ram[cpu.sp + 1] = RETURN_PC >> 8;
  unsigned long next_frame = FRAME_CYCLES;
  while (cpu.pc != RETURN_PC && cpu.cyc < 2000000UL && !cpu.halted) {
    i8080_step(&cpu);
    if (cpu.cyc >= next_frame) {
      next_frame += FRAME_CYCLES;
      if (cpu.iff) {
        write_byte(f, (uint16_t)(cpu.sp - 1), cpu.pc >> 8);
        write_byte(f, (uint16_t)(cpu.sp - 2), cpu.pc & 0xFF);
        cpu.sp -= 2;
        cpu.iff = 0;
        cpu.pc = 0xFED4;               // PIC IR5 frame service vector
        (*frame_interrupts)++;
      }
    }
  }
  *total_cycles += cpu.cyc;
  *result = cpu.a;
  if (cpu.pc == RETURN_PC) return 0;
  fprintf(stderr,
          "EKDOS CONIN: did not return (pc=%04X cyc=%lu frames=%u reads=%u)\n",
          cpu.pc, cpu.cyc, *frame_interrupts, f->keyboard_reads);
  return 1;
}


static int run_bios_seldsk(
    fixture* f, uint8_t drive, uint16_t* dph, unsigned long* total_cycles) {
  return run_bios_entry(f, BIOS_SELDSK, 0, drive, 0, NULL, dph,
                        total_cycles, "SELDSK");
}


static int run_bios_home_case(
    fixture* f, uint8_t dirty, uint8_t expected_active,
    unsigned long* total_cycles) {
  f->ram[0xD61B] = 0x5A;              // SEKTRK
  f->ram[0xD623] = 0xA5;              // HSTACT
  f->ram[0xD624] = dirty;             // HSTWRT
  int fail = run_bios_entry(f, BIOS_HOME, 0, 0, 0, NULL, NULL,
                            total_cycles, "HOME");
  if (f->ram[0xD61B] != 0 || f->ram[0xD623] != expected_active ||
      f->ram[0xD624] != dirty) {
    fprintf(stderr,
            "EKDOS HOME: dirty=%u track=%02X active=%02X/%02X dirty-after=%02X\n",
            dirty, f->ram[0xD61B], f->ram[0xD623], expected_active,
            f->ram[0xD624]);
    fail = 1;
  }
  return fail;
}


static int run_bios_ram_io(
    fixture* f, int write, uint8_t write_type, uint8_t track,
    uint8_t sector, uint16_t dma, unsigned long* total_cycles) {
  uint8_t result = 0xFF;
  int fail = 0;
  fail |= run_bios_entry(f, BIOS_SETTRK, 0, track, 0, NULL, NULL,
                         total_cycles, "SETTRK");
  fail |= run_bios_entry(f, BIOS_SETSEC, 0, sector, 0, NULL, NULL,
                         total_cycles, "SETSEC");
  fail |= run_bios_entry(f, BIOS_SETDMA, dma >> 8, dma & 0xFF, 0, NULL, NULL,
                         total_cycles, "SETDMA");
  if (f->ram[0xD61B] != track || f->ram[0xD61D] != sector ||
      f->ram[0xD62E] != (dma & 0xFF) || f->ram[0xD62F] != (dma >> 8)) {
    fprintf(stderr,
            "EKDOS BIOS setters: track=%u/%u sector=%u/%u dma=%02X%02X/%04X\n",
            f->ram[0xD61B], track, f->ram[0xD61D], sector,
            f->ram[0xD62F], f->ram[0xD62E], dma);
    fail = 1;
  }
  fail |= run_bios_entry(f, write ? BIOS_WRITE : BIOS_READ,
                         0, write ? write_type : 0, 0, &result, NULL,
                         total_cycles, write ? "WRITE" : "READ");
  if (result != 0) {
    fprintf(stderr, "EKDOS BIOS %s: track=%u sector=%u result=%02X\n",
            write ? "WRITE" : "READ", track, sector, result);
    fail = 1;
  }
  return fail;
}


int main(int argc, char** argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s boot-initialized.ram\n", argv[0]);
    return 2;
  }
  char dir[] = "/tmp/rombios-fdc-write.XXXXXX";
  if (!mkdtemp(dir)) {
    perror("mkdtemp");
    return 1;
  }
  char path[256];
  snprintf(path, sizeof(path), "%s/disk.cpm", dir);

  fixture f;
  memset(&f, 0, sizeof(f));
  f.ram_bank = 6;                    // monitor normal-RAM bank
  f.ramdisk_present = 1;
  int fail = write_image(path) || load_rom(f.rom) || load_boot_ram(f.ram, argv[1]);
  juk_disk disk;
  if (!fail && juk_disk_open_writable(&disk, path) != 0) fail = 1;
  if (fail) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: fixture setup failed\n");
    unlink(path);
    rmdir(dir);
    return 1;
  }

  uint8_t baseline[512];
  for (int i = 0; i < 512; i++) baseline[i] = (uint8_t)(0x6B + i * 5);
  if (juk_disk_write_sector(&disk, 8, 0, 3, baseline) != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: baseline-sector setup failed\n");
    juk_disk_close(&disk);
    unlink(path);
    rmdir(dir);
    return 1;
  }

  juku_fdc_init(&f.fdc, &disk);
  update_portc(&f, 0x05);  // motor on, drive A, side 0, high ROM overlay
  f.fdc.track = 8;

  for (int i = 0; i < 128; i++) {
    f.ram[DMA_ADDR + i] = (uint8_t)(0xA7 ^ i);
    f.ram[SECOND_DMA_ADDR + i] = (uint8_t)(0x3C + i);
    f.ram[THIRD_DMA_ADDR + i] = (uint8_t)(0xD5 ^ (i * 3));
  }
  f.ram[0xD600] = 0;                 // drive-A disk type: select command 0xA2
  f.ram[0xD601] = 0;                 // drive A
  f.ram[0xD602] = 8;                 // requested logical track
  f.ram[0xD604] = 3;                 // requested sector
  f.ram[0xD607] = DMA_ADDR & 0xFF;
  f.ram[0xD608] = DMA_ADDR >> 8;
  f.ram[0xD609] = 0xFF;              // must be cleared by successful handler
  f.ram[0xD610] = 80;                // tracks per side for selected drive
  f.ram[0xD611] = 0;                 // seek-rate bits
  f.ram[0xD614] = 0;                 // currently selected drive
  f.ram[0xD615] = 8;                 // remembered physical track for drive A
  f.ram[0xCA36] = 2;                 // EKDOS RAM-disk number; drive A is physical
  f.ram[0xD61A] = 0;                 // EKDOS selected drive
  f.ram[0xD61B] = 8;                 // EKDOS logical track low
  f.ram[0xD61C] = 0;                 // EKDOS logical track high
  memset(&f.ram[0xD61E], 0, 0xD62E - 0xD61E); // cold EKDOS cache state
  f.ram[0xD62A] = 10;                // EKDOS VIARV retry count
  unsigned long total_cycles = 0;
  fail |= run_rwfloppy(&f, 0x12, 9, DMA_ADDR,
                       &total_cycles); // cold partial write prereads host sector 3
  fail |= run_rwfloppy(&f, 0x12, 10, SECOND_DMA_ADDR,
                       &total_cycles); // coalesce second record
  fail |= run_rwfloppy(&f, 0x12, 12, THIRD_DMA_ADDR,
                       &total_cycles); // coalesce fourth record
  memset(&f.ram[CACHE_READ_ADDR], 0x5A, 128);
  memset(&f.ram[SECOND_CACHE_READ_ADDR], 0x5A, 128);
  memset(&f.ram[UNTOUCHED_CACHE_READ_ADDR], 0x5A, 128);
  memset(&f.ram[FOURTH_CACHE_READ_ADDR], 0x5A, 128);
  fail |= run_rwfloppy(&f, 0x11, 9, CACHE_READ_ADDR,
                       &total_cycles); // first cache-hit offset
  fail |= run_rwfloppy(&f, 0x11, 10, SECOND_CACHE_READ_ADDR,
                       &total_cycles); // second cache-hit offset
  fail |= run_rwfloppy(&f, 0x11, 11, UNTOUCHED_CACHE_READ_ADDR,
                       &total_cycles); // untouched third offset
  fail |= run_rwfloppy(&f, 0x11, 12, FOURTH_CACHE_READ_ADDR,
                       &total_cycles); // fourth cache-hit offset
  if (f.fdc_commands != 1 || f.command_log[0] != 0x80) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: cache hit issued FDC command(s)");
    for (unsigned i = 0; i < f.fdc_commands; i++) fprintf(stderr, " %02X", f.command_log[i]);
    fputc('\n', stderr);
    fail = 1;
  }
  if (memcmp(&f.ram[CACHE_READ_ADDR], &f.ram[DMA_ADDR], 128) != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: first cache-hit record mismatch\n");
    fail = 1;
  }
  if (memcmp(&f.ram[SECOND_CACHE_READ_ADDR], &f.ram[SECOND_DMA_ADDR], 128) != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: second cache-hit record mismatch\n");
    fail = 1;
  }
  if (memcmp(&f.ram[UNTOUCHED_CACHE_READ_ADDR], baseline + 256, 128) != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: untouched cache record changed\n");
    fail = 1;
  }
  if (memcmp(&f.ram[FOURTH_CACHE_READ_ADDR],
             &f.ram[THIRD_DMA_ADDR], 128) != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: fourth cache-hit record mismatch\n");
    fail = 1;
  }
  if (f.ram[0xD624] != 1) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: cache hit lost dirty state HSTWRT=%02X\n",
            f.ram[0xD624]);
    fail = 1;
  }
  fail |= run_rwfloppy(&f, 0x11, 13, SCRATCH_ADDR,
                       &total_cycles); // flush, then load host sector 4

  uint8_t sector[512];
  if (f.ram[0xD609] != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: ERRC=0x%02X cyc=%lu\n",
            f.ram[0xD609], total_cycles);
    fail = 1;
  }
  if (f.command_writes != 1 || f.write_command != 0xA2) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: command count=%u command=0x%02X\n",
            f.command_writes, f.write_command);
    fprintf(stderr, "ROMBIOS RWFLOPPY: FDC command sequence");
    for (unsigned i = 0; i < f.fdc_commands; i++) fprintf(stderr, " %02X", f.command_log[i]);
    fputc('\n', stderr);
    fail = 1;
  }
  if (f.fdc_commands != 3 || f.command_log[0] != 0x80 ||
      f.command_log[1] != 0xA2 || f.command_log[2] != 0x80) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: unexpected FDC command sequence");
    for (unsigned i = 0; i < f.fdc_commands; i++) fprintf(stderr, " %02X", f.command_log[i]);
    fputc('\n', stderr);
    fail = 1;
  }
  if (f.data_writes != 512) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: accepted data writes=%u\n", f.data_writes);
    fail = 1;
  }
  if (f.monitor_trampoline_entries < 2) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: monitor trampoline entries=%u\n",
            f.monitor_trampoline_entries);
    fail = 1;
  }
  uint8_t expected[512];
  memcpy(expected, baseline, sizeof(expected));
  memcpy(expected, &f.ram[DMA_ADDR], 128);
  memcpy(expected + 128, &f.ram[SECOND_DMA_ADDR], 128);
  memcpy(expected + 384, &f.ram[THIRD_DMA_ADDR], 128);
  if (juk_disk_read_sector(&disk, 8, 0, 3, sector) != 0 ||
      memcmp(sector, expected, sizeof(sector)) != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: persisted sector mismatch\n");
    fail = 1;
  }

  uint8_t successful_write_command = f.write_command;
  unsigned successful_trampolines = f.monitor_trampoline_entries;
  unsigned long successful_cycles = total_cycles;
  unsigned long auxiliary_cycles = 0;
  unsigned long console_status_cycles = 0;
  unsigned long console_input_cycles = 0;
  unsigned long console_output_cycles = 0;
  unsigned long unallocated_cycles = 0;
  unsigned long home_cycles = 0;
  unsigned long list_status_cycles = 0;
  unsigned long list_output_cycles = 0;
  unsigned long seldsk_cycles = 0;
  unsigned long sectran_cycles = 0;
  unsigned long ramdisk_cycles = 0;
  unsigned long protect_cycles = 0;

  f.fdc_commands = 0;
  memset(f.command_log, 0, sizeof(f.command_log));
  f.command_writes = 0;
  f.data_writes = 0;
  f.write_command = 0;
  memset(&f.ram[0xD61E], 0, 0xD62E - 0xD61E);
  f.ram[0xD62A] = 10;
  f.ram[0xD609] = 0xFF;
  for (int i = 0; i < 128; i++) {
    f.ram[DMA_ADDR + i] = (uint8_t)(0x11 + i);
    f.ram[SECOND_DMA_ADDR + i] = (uint8_t)(0x72 ^ i);
    f.ram[THIRD_DMA_ADDR + i] = (uint8_t)(0xC4 + i * 3);
    f.ram[FOURTH_DMA_ADDR + i] = (uint8_t)(0xE9 ^ (i * 5));
  }
  fail |= run_rwfloppy_type(&f, 0x12, 2, 17, DMA_ADDR, &unallocated_cycles);
  fail |= run_rwfloppy(&f, 0x12, 18, SECOND_DMA_ADDR, &unallocated_cycles);
  fail |= run_rwfloppy(&f, 0x12, 19, THIRD_DMA_ADDR, &unallocated_cycles);
  fail |= run_rwfloppy(&f, 0x12, 20, FOURTH_DMA_ADDR, &unallocated_cycles);
  if (f.fdc_commands != 0 || f.ram[0xD625] != 28 || f.ram[0xD624] != 1) {
    fprintf(stderr,
            "ROMBIOS RWFLOPPY: unallocated cache commands=%u UNACNT=%u HSTWRT=%u\n",
            f.fdc_commands, f.ram[0xD625], f.ram[0xD624]);
    fail = 1;
  }
  fail |= run_rwfloppy(&f, 0x11, 21, SCRATCH_ADDR, &unallocated_cycles);
  if (f.fdc_commands != 2 || f.command_log[0] != 0xA2 ||
      f.command_log[1] != 0x80 || f.command_writes != 1 ||
      f.data_writes != 512 || f.ram[0xD609] != 0) {
    fprintf(stderr,
            "ROMBIOS RWFLOPPY: unallocated flush commands=%u writes=%u data=%u ERRC=%02X\n",
            f.fdc_commands, f.command_writes, f.data_writes, f.ram[0xD609]);
    fail = 1;
  }
  uint8_t unallocated_expected[512];
  memcpy(unallocated_expected, &f.ram[DMA_ADDR], 128);
  memcpy(unallocated_expected + 128, &f.ram[SECOND_DMA_ADDR], 128);
  memcpy(unallocated_expected + 256, &f.ram[THIRD_DMA_ADDR], 128);
  memcpy(unallocated_expected + 384, &f.ram[FOURTH_DMA_ADDR], 128);
  if (juk_disk_read_sector(&disk, 8, 0, 5, sector) != 0 ||
      memcmp(sector, unallocated_expected, sizeof(sector)) != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: unallocated sector mismatch\n");
    fail = 1;
  }

  f.fdc_commands = 0;
  memset(f.command_log, 0, sizeof(f.command_log));
  f.command_writes = 0;
  f.data_writes = 0;
  f.write_command = 0;
  uint8_t ramdisk_result = 0;
  uint8_t normal_ram_byte = f.ram[DMA_ADDR];
  f.ramdisk_present = 0;
  uint16_t absent_dph = 0xFFFF;
  fail |= run_bios_seldsk(&f, 2, &absent_dph, &seldsk_cycles);
  if (absent_dph != 0 || f.ram[0xD61A] != 2 || f.ram_bank != 6 ||
      f.ram[DMA_ADDR] != normal_ram_byte) {
    fprintf(stderr,
            "EKDOS SELDSK: absent drive-C dph=%04X selected=%u "
            "final-bank=%u normal=%02X/%02X\n",
            absent_dph, f.ram[0xD61A], f.ram_bank,
            f.ram[DMA_ADDR], normal_ram_byte);
    fail = 1;
  }
  fail |= run_ramdisk_select(&f, &ramdisk_result, &ramdisk_cycles);
  if (ramdisk_result != 0xFF || f.ram_bank != 6 ||
      f.ram[DMA_ADDR] != normal_ram_byte) {
    fprintf(stderr,
            "ROMBIOS RAMDISKSEL: absent result=%02X final-bank=%u normal=%02X/%02X\n",
            ramdisk_result, f.ram_bank, f.ram[DMA_ADDR], normal_ram_byte);
    fail = 1;
  }

  f.ramdisk_present = 1;
  memset(f.ramdisk[0], 0xA5, RAM_DISK_WINDOW);
  fail |= run_ramdisk_select(&f, &ramdisk_result, &ramdisk_cycles);
  int format_ok = ramdisk_result == 0 &&
                  memcmp(f.ramdisk[0], RAMDISK_SIGNATURE,
                         sizeof(RAMDISK_SIGNATURE)) == 0;
  for (unsigned i = sizeof(RAMDISK_SIGNATURE); format_ok && i < 0x20; i++) {
    if (f.ramdisk[0][i] != 0) format_ok = 0;
  }
  for (unsigned i = 0; format_ok && i < 63; i++) {
    if (f.ramdisk[0][0x20 + i * 0x20] != 0xE5) format_ok = 0;
  }
  if (!format_ok) {
    fprintf(stderr, "ROMBIOS RAMDISKSEL: initial format mismatch result=%02X\n",
            ramdisk_result);
    fail = 1;
  }

  f.ramdisk[0][0x21] = 0x6C;
  fail |= run_ramdisk_select(&f, &ramdisk_result, &ramdisk_cycles);
  if (ramdisk_result != 0 || f.ramdisk[0][0x21] != 0x6C ||
      f.ram_bank != 6 || f.fdc_commands != 0) {
    fprintf(stderr,
            "ROMBIOS RAMDISKSEL: reopen result=%02X retained=%02X "
            "final-bank=%u fdc=%u\n",
            ramdisk_result, f.ramdisk[0][0x21], f.ram_bank, f.fdc_commands);
    fail = 1;
  }

  uint16_t dph0 = 0;
  uint16_t dph1 = 0;
  uint16_t dph2 = 0;
  uint16_t invalid_dph = 0xFFFF;
  fail |= run_bios_seldsk(&f, 0, &dph0, &seldsk_cycles);
  fail |= run_bios_seldsk(&f, 1, &dph1, &seldsk_cycles);
  fail |= run_bios_seldsk(&f, 3, &invalid_dph, &seldsk_cycles);
  if (invalid_dph != 0 || f.ram[0xD61A] != 1) {
    fprintf(stderr, "EKDOS SELDSK: invalid drive dph=%04X selected=%u\n",
            invalid_dph, f.ram[0xD61A]);
    fail = 1;
  }
  fail |= run_bios_seldsk(&f, 2, &dph2, &seldsk_cycles);
  uint16_t ram_dpb = 0;
  int dph_layout_ok = dph2 <= UINT16_MAX - 11u;
  if (dph_layout_ok) {
    ram_dpb = (uint16_t)(f.ram[dph2 + 10] | (f.ram[dph2 + 11] << 8));
  }
  static const uint8_t expected_ram_dpb[] = {
    0x80, 0x00, 0x03, 0x07, 0x00, 0xBF, 0x00, 0x3F,
    0x00, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x00,
  };
  int dpb_layout_ok = ram_dpb != 0 &&
                      ram_dpb <= UINT16_MAX - sizeof(expected_ram_dpb) + 1u;
  if (dph0 == 0 || dph1 != dph0 + 16 || dph2 != dph0 + 32 ||
      !dph_layout_ok || !dpb_layout_ok ||
      f.ram[0xD61A] != 2 || f.ram[dph2] != 0 || f.ram[dph2 + 1] != 0 ||
      memcmp(&f.ram[ram_dpb], expected_ram_dpb, sizeof(expected_ram_dpb)) != 0) {
    fprintf(stderr,
            "EKDOS SELDSK: DPH/DPB mismatch dph=%04X/%04X/%04X "
            "ram-dpb=%04X selected=%u\n",
            dph0, dph1, dph2, ram_dpb, f.ram[0xD61A]);
    fail = 1;
  }

  uint8_t saved_track = f.ram[0xD61B];
  uint8_t saved_host_active = f.ram[0xD623];
  uint8_t saved_host_dirty = f.ram[0xD624];
  fail |= run_bios_home_case(&f, 0, 0, &home_cycles);
  fail |= run_bios_home_case(&f, 1, 0xA5, &home_cycles);
  f.ram[0xD61B] = saved_track;
  f.ram[0xD623] = saved_host_active;
  f.ram[0xD624] = saved_host_dirty;

  uint8_t list_status = 0xFF;
  fail |= run_bios_entry(&f, BIOS_LISTST, 0, 0, 0, &list_status, NULL,
                         &list_status_cycles, "LISTST");
  if (list_status != 0) {
    fprintf(stderr, "EKDOS LISTST: result=%02X expected=00\n", list_status);
    fail = 1;
  }

  static const struct {
    uint16_t entry;
    const char* name;
  } unavailable_auxiliary[] = {
    {BIOS_PUNCH, "PUNCH"},
    {BIOS_READER, "READER"},
  };
  for (unsigned i = 0;
       i < sizeof(unavailable_auxiliary) / sizeof(unavailable_auxiliary[0]); i++) {
    uint8_t result = 0xFF;
    fail |= run_bios_entry(&f, unavailable_auxiliary[i].entry,
                           0, 0x5A, 0, &result, NULL,
                           &auxiliary_cycles, unavailable_auxiliary[i].name);
    if (result != 0) {
      fprintf(stderr, "EKDOS %s: result=%02X expected=00\n",
              unavailable_auxiliary[i].name, result);
      fail = 1;
    }
  }

  uint8_t saved_keyboard_column = f.out[0x04];
  uint8_t saved_keyboard_input = f.out[0x05];
  f.out[0x05] = 0xCF;                 // no key: released 74148/shift inputs
  uint8_t console_status = 0xFF;
  unsigned console_trampolines_before = f.monitor_trampoline_entries;
  fail |= run_bios_entry(&f, BIOS_CONST, 0, 0, 0, &console_status, NULL,
                         &console_status_cycles, "CONST");
  f.out[0x04] = saved_keyboard_column;
  f.out[0x05] = saved_keyboard_input;
  if (console_status != 0 ||
      f.monitor_trampoline_entries <= console_trampolines_before) {
    fprintf(stderr,
            "EKDOS CONST: result=%02X expected=00 trampolines=%u/%u\n",
            console_status, f.monitor_trampoline_entries,
            console_trampolines_before);
    fail = 1;
  }

  f.keyboard_held = 1;
  f.keyboard_shift = 1;
  f.keyboard_col = 4;                 // T key in the target keyboard matrix
  f.keyboard_bit = 3;
  f.keyboard_reads = 0;
  f.keyboard_active_reads = 0;
  f.keyboard_active_value = 0;
  uint8_t console_input = 0;
  unsigned conin_frame_interrupts = 0;
  unsigned conin_trampolines_before = f.monitor_trampoline_entries;
  fail |= run_bios_conin(&f, &console_input, &conin_frame_interrupts,
                         &console_input_cycles);
  f.keyboard_held = 0;
  if (console_input != 'T' || f.keyboard_reads != 34 ||
      f.keyboard_active_reads != 2 || f.keyboard_active_value != 0x88 ||
      conin_frame_interrupts != 2 ||
      f.monitor_trampoline_entries <= conin_trampolines_before) {
    fprintf(stderr,
            "EKDOS CONIN: result=%02X expected=%02X frames=%u reads=%u "
            "active=%u/%02X "
            "trampolines=%u/%u\n",
            console_input, 'T', conin_frame_interrupts,
            f.keyboard_reads, f.keyboard_active_reads, f.keyboard_active_value,
            f.monitor_trampoline_entries, conin_trampolines_before);
    fail = 1;
  }

  static const uint8_t glyph_cell_c[10] = {
    0x00, 0x1C, 0x22, 0x20, 0x20, 0x20, 0x22, 0x1C, 0x00, 0x00,
  };
  enum { CONOUT_GLYPH_BASE = 0xE2F2 };
  int conout_fixture_ok = f.ram[0xD49F] == 2 && f.ram[0xD4A0] == 0xF2;
  for (unsigned row = 0; row < sizeof(glyph_cell_c); row++) {
    if (f.ram[CONOUT_GLYPH_BASE + row * 40] != 0) conout_fixture_ok = 0;
  }
  unsigned conout_vram_before = f.vram_writes;
  unsigned conout_trampolines_before = f.monitor_trampoline_entries;
  fail |= run_bios_entry(&f, BIOS_CONOUT, 0, 'C', 0, NULL, NULL,
                         &console_output_cycles, "CONOUT");
  int conout_glyph_ok = 1;
  for (unsigned row = 0; row < sizeof(glyph_cell_c); row++) {
    if (f.ram[CONOUT_GLYPH_BASE + row * 40] != glyph_cell_c[row]) {
      conout_glyph_ok = 0;
    }
  }
  if (!conout_fixture_ok || !conout_glyph_ok || f.ram[0xD49F] != 3 ||
      f.ram[0xD4A0] != 0xF3 || f.vram_writes - conout_vram_before != 10 ||
      f.monitor_trampoline_entries <= conout_trampolines_before) {
    fprintf(stderr,
            "EKDOS CONOUT: fixture=%u glyph=%u cursor=%02X/%02X "
            "writes=%u trampolines=%u/%u\n",
            conout_fixture_ok, conout_glyph_ok, f.ram[0xD49F], f.ram[0xD4A0],
            f.vram_writes - conout_vram_before, f.monitor_trampoline_entries,
            conout_trampolines_before);
    fail = 1;
  }

  uint8_t saved_usart_data = f.out[0x0C];
  uint8_t saved_usart_status = f.out[0x0E];
  f.out[0x0C] = 0;
  f.out[0x0E] = 0x08;                 // USART transmitter ready
  fail |= run_bios_entry(&f, BIOS_LIST, 0, 'L', 0, NULL, NULL,
                         &list_output_cycles, "LIST");
  uint8_t listed_character = f.out[0x0C];
  f.out[0x0C] = saved_usart_data;
  f.out[0x0E] = saved_usart_status;
  if (listed_character != 'L') {
    fprintf(stderr, "EKDOS LIST: output=%02X expected=%02X\n",
            listed_character, 'L');
    fail = 1;
  }

  static const uint8_t expected_translation[40] = {
    1, 2, 3, 4, 9, 10, 11, 12,
    17, 18, 19, 20, 25, 26, 27, 28,
    33, 34, 35, 36, 5, 6, 7, 8,
    13, 14, 15, 16, 21, 22, 23, 24,
    29, 30, 31, 32, 37, 38, 39, 40,
  };
  uint16_t floppy_xlt = (uint16_t)(f.ram[dph0] | (f.ram[dph0 + 1] << 8));
  for (unsigned sector_index = 0; sector_index < 40; sector_index++) {
    uint16_t translated = 0xFFFF;
    fail |= run_bios_entry(&f, BIOS_SECTRAN, 0, (uint8_t)sector_index,
                           floppy_xlt, NULL, &translated,
                           &sectran_cycles, "SECTRAN");
    if (translated != expected_translation[sector_index]) {
      fprintf(stderr,
              "EKDOS SECTRAN: index=%u translated=%04X expected=%02X xlt=%04X\n",
              sector_index, translated, expected_translation[sector_index],
              floppy_xlt);
      fail = 1;
    }
  }
  static const uint8_t ram_identity_sectors[] = {0, 127};
  for (unsigned i = 0; i < sizeof(ram_identity_sectors); i++) {
    uint16_t translated = 0xFFFF;
    uint8_t sector_index = ram_identity_sectors[i];
    fail |= run_bios_entry(&f, BIOS_SECTRAN, 0, sector_index, 0,
                           NULL, &translated, &sectran_cycles, "SECTRAN");
    if (translated != sector_index) {
      fprintf(stderr,
              "EKDOS SECTRAN: null-table index=%u translated=%04X\n",
              sector_index, translated);
      fail = 1;
    }
  }

  static const uint8_t endpoint_sector[RAM_DISK_ENDPOINTS] = {0, 127};
  uint8_t ramdisk_expected[RAM_DISK_TRACKS][RAM_DISK_ENDPOINTS][128];
  for (unsigned track = 0; track < RAM_DISK_TRACKS; track++) {
    for (unsigned endpoint = 0; endpoint < RAM_DISK_ENDPOINTS; endpoint++) {
      for (unsigned i = 0; i < 128; i++) {
        ramdisk_expected[track][endpoint][i] =
            (uint8_t)(0x3D ^ track * 19u ^ endpoint * 0xA7u ^ i * 5u);
      }
      memcpy(&f.ram[DMA_ADDR], ramdisk_expected[track][endpoint], 128);
      fail |= run_bios_ram_io(&f, 1, endpoint ? 2 : 0, (uint8_t)track,
                              endpoint_sector[endpoint], DMA_ADDR,
                              &ramdisk_cycles);
    }
  }
  for (unsigned track = 0; track < RAM_DISK_TRACKS; track++) {
    for (unsigned endpoint = 0; endpoint < RAM_DISK_ENDPOINTS; endpoint++) {
      uint8_t sector_number = endpoint_sector[endpoint];
      unsigned record_offset = (sector_number >> 1) * 256u +
                               (sector_number & 1u) * 128u;
      unsigned bank_offset = (track & 1u) * 0x4000u + record_offset;
      memset(&f.ram[CACHE_READ_ADDR], 0x5A, 128);
      fail |= run_bios_ram_io(&f, 0, 0, (uint8_t)track, sector_number,
                              CACHE_READ_ADDR, &ramdisk_cycles);
      if (memcmp(&f.ram[CACHE_READ_ADDR], ramdisk_expected[track][endpoint], 128) != 0 ||
          memcmp(&f.ramdisk[track >> 1][bank_offset],
                 ramdisk_expected[track][endpoint], 128) != 0) {
        fprintf(stderr,
                "ROMBIOS RWFLOPPY: RAM-disk mapping mismatch "
                "track=%u sector=%u bank=%u offset=%04X\n",
                track, sector_number, track >> 1, bank_offset);
        fail = 1;
      }
    }
  }
  if (f.fdc_commands != 0 || f.ram_bank != 6) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: RAM-disk FDC commands=%u final-bank=%u\n",
            f.fdc_commands, f.ram_bank);
    fail = 1;
  }
  f.ram[0xD61A] = 0;
  f.ram[0xD61B] = 8;

  juk_disk_close(&disk);
  if (juk_disk_open(&disk, path) != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: read-only reopen failed\n");
    fail = 1;
  } else {
    f.monitor_trampoline_entries = 0;
    f.fdc_commands = 0;
    memset(f.command_log, 0, sizeof(f.command_log));
    f.command_writes = 0;
    f.data_writes = 0;
    f.write_protect_status_reads = 0;
    f.write_command = 0;
    memset(&f.ram[0xD61E], 0, 0xD62E - 0xD61E);
    f.ram[0xD62A] = 10;
    f.ram[0xD609] = 0xFF;
    for (int i = 0; i < 128; i++) {
      f.ram[DMA_ADDR + i] = (uint8_t)(0x5E ^ (i * 7));
    }
    juku_fdc_init(&f.fdc, &disk);
    update_portc(&f, 0x05);
    f.fdc.track = 8;

    fail |= run_rwfloppy(&f, 0x12, 9, DMA_ADDR, &protect_cycles);
    fail |= run_rwfloppy(&f, 0x11, 13, SCRATCH_ADDR, &protect_cycles);
    if (f.ram[0xD609] != 0) {
      fprintf(stderr, "ROMBIOS RWFLOPPY: final read did not mask ERRC=0x%02X\n",
              f.ram[0xD609]);
      fail = 1;
    }
    int commands_ok = f.fdc_commands == 12 && f.command_log[0] == 0x80 &&
                      f.command_log[11] == 0x80;
    for (unsigned i = 1; commands_ok && i < 11; i++) {
      if (f.command_log[i] != 0xA2) commands_ok = 0;
    }
    if (!commands_ok) {
      fprintf(stderr, "ROMBIOS RWFLOPPY: write-protect command sequence");
      for (unsigned i = 0; i < f.fdc_commands; i++) {
        fprintf(stderr, " %02X", f.command_log[i]);
      }
      fputc('\n', stderr);
      fail = 1;
    }
    if (f.command_writes != 10 || f.data_writes != 0) {
      fprintf(stderr,
              "ROMBIOS RWFLOPPY: protected write commands=%u accepted-bytes=%u\n",
              f.command_writes, f.data_writes);
      fail = 1;
    }
    if (f.write_protect_status_reads < 10) {
      fprintf(stderr, "ROMBIOS RWFLOPPY: too few WRITE PROTECT status reads=%u\n",
              f.write_protect_status_reads);
      fail = 1;
    }
    if (juk_disk_read_sector(&disk, 8, 0, 3, sector) != 0 ||
        memcmp(sector, expected, sizeof(sector)) != 0) {
      fprintf(stderr, "ROMBIOS RWFLOPPY: read-only media changed\n");
      fail = 1;
    }
    juk_disk_close(&disk);
  }
  unlink(path);
  rmdir(dir);
  if (fail) {
    fprintf(stderr, "ROMBIOS RWFLOPPY write test: FAIL\n");
    return 1;
  }
  printf("ROMBIOS RWFLOPPY write test: PASS command=0x%02X record-size=128 "
         "cold-write=1 records-written=3 cache-hit=512 data=512 "
         "unallocated=4 no-preread=1 "
         "ramdisk-select=absent/format/reopen ramdisk-banks=6 "
         "const=no-key conin=shift-T conout=glyph-C list=usart-L "
         "aux=punch+reader-unimplemented "
         "home=clean+dirty "
         "listst=not-ready "
         "seldsk=0/1/2/invalid "
         "bios-rw=public/types0+2 "
         "sectran=40+2 ramdisk-tracks=12 endpoints=24 no-fdc=1 "
         "wp-retries=10 wp-status-reads=%u wp-error-masked=1 "
         "trampoline=%u cyc=%lu\n",
         successful_write_command, f.write_protect_status_reads,
         successful_trampolines,
         successful_cycles + auxiliary_cycles + console_status_cycles +
         console_input_cycles + console_output_cycles +
         list_output_cycles + unallocated_cycles +
         home_cycles + list_status_cycles +
         seldsk_cycles + sectran_cycles +
         ramdisk_cycles + protect_cycles);
  return 0;
}
