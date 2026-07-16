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
  STOP_PC = 0xE6C2,
  DMA_ADDR = 0x4000,
};


typedef struct {
  uint8_t ram[65536];
  uint8_t rom[ROM_SIZE];
  uint8_t out[256];
  uint8_t portc;
  unsigned fdc_commands;
  uint8_t command_log[16];
  unsigned command_writes;
  unsigned data_writes;
  uint8_t write_command;
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
  unsigned index = 0;
  int source = overlay(f, address, &index);
  if (source == 1) return f->rom[index];
  if (source == 2) return 0xFF;  // no expansion cartridge installed
  return f->ram[address];
}


static void write_byte(void* opaque, uint16_t address, uint8_t value) {
  fixture* f = opaque;
  unsigned index = 0;
  if (!overlay(f, address, &index)) f->ram[address] = value;
}


static uint8_t port_in(void* opaque, uint8_t port) {
  fixture* f = opaque;
  if (port >= 0x1C && port <= 0x1F) return juku_fdc_read(&f->fdc, port & 3);
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


int main(void) {
  char dir[] = "/tmp/rombios-fdc-write.XXXXXX";
  if (!mkdtemp(dir)) {
    perror("mkdtemp");
    return 1;
  }
  char path[256];
  snprintf(path, sizeof(path), "%s/disk.cpm", dir);

  fixture f;
  memset(&f, 0, sizeof(f));
  int fail = write_image(path) || load_rom(f.rom);
  juk_disk disk;
  if (!fail && juk_disk_open_writable(&disk, path) != 0) fail = 1;
  if (fail) {
    fprintf(stderr, "ROMBIOS FDC write: fixture setup failed\n");
    unlink(path);
    rmdir(dir);
    return 1;
  }

  juku_fdc_init(&f.fdc, &disk);
  update_portc(&f, 0x05);  // motor on, drive A, side 0, high ROM overlay
  f.fdc.track = 8;

  for (int i = 0; i < 768; i++) f.ram[DMA_ADDR + i] = (uint8_t)(0xA7 ^ i);
  f.fdc.sector = 3;
  f.ram[0xD607] = DMA_ADDR & 0xFF;
  f.ram[0xD608] = DMA_ADDR >> 8;
  f.ram[0xD609] = 0xFF;              // must be cleared by successful handler

  i8080 cpu;
  i8080_init(&cpu);
  cpu.userdata = &f;
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.pc = 0xE69F;                    // authentic ROMBIOS write command/data loop
  cpu.sp = 0xBFFE;
  cpu.b = 0x02;
  cpu.c = 0xFE;                       // type-0 loop's authentic initial BC=0x02FE
  cpu.d = 0x00;                       // command modifier
  cpu.zf = 0;                         // type 0 selects command 0xA2
  // Stop after ERRC is stored and before the monitor-service epilogue at E6C2.
  while (cpu.pc != STOP_PC && cpu.cyc < 2000000UL && !cpu.halted) i8080_step(&cpu);

  uint8_t sector[512];
  if (cpu.pc != STOP_PC) {
    fprintf(stderr, "ROMBIOS FDC write: loop did not finish (pc=%04X cyc=%lu)\n",
            cpu.pc, cpu.cyc);
    fail = 1;
  }
  if (f.ram[0xD609] != 0) {
    fprintf(stderr, "ROMBIOS FDC write: ERRC=0x%02X cyc=%lu\n",
            f.ram[0xD609], cpu.cyc);
    fail = 1;
  }
  if (f.command_writes != 1 || f.write_command != 0xA2) {
    fprintf(stderr, "ROMBIOS FDC write: command count=%u command=0x%02X\n",
            f.command_writes, f.write_command);
    fprintf(stderr, "ROMBIOS FDC write: FDC command sequence");
    for (unsigned i = 0; i < f.fdc_commands; i++) fprintf(stderr, " %02X", f.command_log[i]);
    fputc('\n', stderr);
    fail = 1;
  }
  if (f.data_writes != 512) {
    fprintf(stderr, "ROMBIOS FDC write: accepted data writes=%u\n", f.data_writes);
    fail = 1;
  }
  if (juk_disk_read_sector(&disk, 8, 0, 3, sector) != 0 ||
      memcmp(sector, &f.ram[DMA_ADDR], sizeof(sector)) != 0) {
    fprintf(stderr, "ROMBIOS FDC write: persisted sector mismatch\n");
    fail = 1;
  }

  juk_disk_close(&disk);
  unlink(path);
  rmdir(dir);
  if (fail) {
    fprintf(stderr, "ROMBIOS FDC write test: FAIL\n");
    return 1;
  }
  printf("ROMBIOS FDC write test: PASS command=0x%02X data=512 cyc=%lu\n",
         f.write_command, cpu.cyc);
  return 0;
}
