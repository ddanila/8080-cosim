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
};


typedef struct {
  uint8_t ram[65536];
  uint8_t ramdisk[RAM_DISK_BANKS][RAM_DISK_WINDOW];
  uint8_t rom[ROM_SIZE];
  uint8_t out[256];
  uint8_t portc;
  unsigned monitor_trampoline_entries;
  unsigned fdc_commands;
  uint8_t command_log[16];
  unsigned command_writes;
  unsigned data_writes;
  unsigned write_protect_status_reads;
  uint8_t write_command;
  unsigned ram_bank;
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
    return f->ramdisk[f->ram_bank][address - 0x4000];
  }
  return f->ram[address];
}


static void write_byte(void* opaque, uint16_t address, uint8_t value) {
  fixture* f = opaque;
  unsigned index = 0;
  if (overlay(f, address, &index)) return;
  if (address >= 0x4000 && address <= 0xBFFF && f->ram_bank < RAM_DISK_BANKS) {
    f->ramdisk[f->ram_bank][address - 0x4000] = value;
  } else {
    f->ram[address] = value;
  }
}


static uint8_t port_in(void* opaque, uint8_t port) {
  fixture* f = opaque;
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
    f->ram_bank = ((value & 7) - 1u) & 7u;
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
  FILE* fp = fopen("roms/ekta37.bin", "rb");
  if (!fp) return 1;
  size_t got = fread(rom, 1, ROM_SIZE, fp);
  int failed = got != ROM_SIZE || fclose(fp) != 0;
  return failed;
}


static int load_boot_ram(uint8_t ram[65536], const char* path) {
  static const uint8_t expected_trampoline[] = {
    0xF5, 0xDB, 0x06, 0xE6, 0xFC, 0xB4, 0xD3, 0x06, 0xF1, 0xC9,
  };
  FILE* fp = fopen(path, "rb");
  if (!fp) return 1;
  size_t got = fread(ram, 1, 65536, fp);
  int failed = got != 65536 || fclose(fp) != 0 ||
               memcmp(&ram[0xD7E7], expected_trampoline, sizeof(expected_trampoline)) != 0;
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
  unsigned long unallocated_cycles = 0;
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
  f.ram[0xCA36] = 2;
  f.ram[0xD61A] = 2;
  f.ram[0xD61C] = 0;
  for (int i = 0; i < 128; i++) {
    f.ram[DMA_ADDR + i] = (uint8_t)(0x31 ^ (i * 3));
    f.ram[SECOND_DMA_ADDR + i] = (uint8_t)(0xB4 + i * 5);
  }
  f.ram[0xD61B] = 2;
  fail |= run_rwfloppy(&f, 0x12, 37, DMA_ADDR, &ramdisk_cycles);
  f.ram[0xD61B] = 3;
  fail |= run_rwfloppy(&f, 0x12, 37, SECOND_DMA_ADDR, &ramdisk_cycles);
  memset(&f.ram[CACHE_READ_ADDR], 0x5A, 128);
  memset(&f.ram[SECOND_CACHE_READ_ADDR], 0x5A, 128);
  f.ram[0xD61B] = 2;
  fail |= run_rwfloppy(&f, 0x11, 37, CACHE_READ_ADDR, &ramdisk_cycles);
  f.ram[0xD61B] = 3;
  fail |= run_rwfloppy(&f, 0x11, 37, SECOND_CACHE_READ_ADDR, &ramdisk_cycles);
  const unsigned ramdisk_record_offset = (37u >> 1) * 256u + 128u;
  if (memcmp(&f.ram[CACHE_READ_ADDR], &f.ram[DMA_ADDR], 128) != 0 ||
      memcmp(&f.ram[SECOND_CACHE_READ_ADDR], &f.ram[SECOND_DMA_ADDR], 128) != 0 ||
      memcmp(&f.ramdisk[1][ramdisk_record_offset], &f.ram[DMA_ADDR], 128) != 0 ||
      memcmp(&f.ramdisk[1][0x4000 + ramdisk_record_offset],
             &f.ram[SECOND_DMA_ADDR], 128) != 0) {
    fprintf(stderr, "ROMBIOS RWFLOPPY: RAM-disk mapping mismatch\n");
    fail = 1;
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
         "ramdisk-tracks=2 no-fdc=1 "
         "wp-retries=10 wp-status-reads=%u wp-error-masked=1 "
         "trampoline=%u cyc=%lu\n",
         successful_write_command, f.write_protect_status_reads,
         successful_trampolines,
         successful_cycles + unallocated_cycles + ramdisk_cycles + protect_cycles);
  return 0;
}
