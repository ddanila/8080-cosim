#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  uint8_t memory[65536];
  int data_fault;
  int address_alias;
  int retention_fault;
  int retention_phase;
  int retention_armed;
} fixture;

static uint16_t map_address(fixture *f, uint16_t address) {
  if (f->address_alias && address == 0x5080)
    return 0x5000;
  return address;
}

static uint8_t read_byte(void *opaque, uint16_t address) {
  fixture *f = opaque;
  address = map_address(f, address);
  if (f->retention_fault && f->retention_phase && f->retention_armed &&
      address == 0x5000) {
    f->retention_armed = 0;
    return (uint8_t)(f->memory[address] ^ 0x04);
  }
  return f->memory[address];
}

static void write_byte(void *opaque, uint16_t address, uint8_t value) {
  fixture *f = opaque;
  if (address == 0x4e01)
    f->retention_phase = 1;
  address = map_address(f, address);
  if (f->data_fault && address == 0x5080 && value == 0xff)
    value = 0xfe;
  f->memory[address] = value;
  if (f->retention_fault && f->retention_phase && address == 0x5000 &&
      (value == 0x00 || value == 0xff))
    f->retention_armed = 1;
}

static uint8_t port_in(void *opaque, uint8_t port) {
  (void)opaque;
  (void)port;
  return 0xff;
}

static void port_out(void *opaque, uint8_t port, uint8_t value) {
  (void)opaque;
  (void)port;
  (void)value;
}

static int run_case(const uint8_t *program, size_t size, int data_fault,
                    int address_alias, int retention_fault) {
  fixture f = {0};
  uint8_t original[256];
  i8080 cpu;

  memcpy(&f.memory[0x4000], program, size);
  for (unsigned i = 0; i < sizeof(original); i++)
    original[i] = f.memory[0x5000 + i] = (uint8_t)(i ^ 0x5a);

  /* A loader CALL supplies the wrapper's return address. */
  f.memory[0x0000] = 0x76; /* HLT */
  f.memory[0x4dfe] = 0x00;
  f.memory[0x4dff] = 0x00;

  i8080_init(&cpu);
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.userdata = &f;
  cpu.pc = 0x4000;
  cpu.sp = 0x4dfe;
  f.data_fault = data_fault;
  f.address_alias = address_alias;
  f.retention_fault = retention_fault;

  for (unsigned steps = 0; !cpu.halted && steps < 100000; steps++)
    i8080_step(&cpu);

  if (!cpu.halted) {
    fprintf(stderr, "shared diagnostic did not return\n");
    return 1;
  }
  if (memcmp(&f.memory[0x5000], original, sizeof(original)) != 0) {
    fprintf(stderr, "shared diagnostic did not restore the test page\n");
    return 1;
  }
  if ((f.memory[0x4e00] != 0) != data_fault ||
      (f.memory[0x4e01] != 0) != address_alias ||
      (f.memory[0x4e02] != 0) != retention_fault) {
    fprintf(stderr,
        "shared diagnostic results data=%02x address=%02x retention=%02x "
        "expected=%d/%d/%d\n",
        f.memory[0x4e00], f.memory[0x4e01], f.memory[0x4e02],
        data_fault, address_alias, retention_fault);
    return 1;
  }
  {
    uint8_t checksum = 0;
    for (unsigned i = 0; i < sizeof(original); i++)
      checksum = (uint8_t)(checksum +
          f.memory[map_address(&f, (uint16_t)(0x5000 + i))]);
    if (f.memory[0x4e03] != checksum) {
      fprintf(stderr, "shared diagnostic checksum was %02x, expected %02x\n",
          f.memory[0x4e03], checksum);
      return 1;
    }
  }
  return 0;
}

int main(int argc, char **argv) {
  uint8_t program[256];
  FILE *input;
  size_t size;

  if (argc != 2) {
    fprintf(stderr, "usage: %s shared-memory-4000.bin\n", argv[0]);
    return 2;
  }
  input = fopen(argv[1], "rb");
  if (!input) {
    perror(argv[1]);
    return 2;
  }
  size = fread(program, 1, sizeof(program), input);
  fclose(input);
  if (size == 0 || size == sizeof(program)) {
    fprintf(stderr, "unexpected shared diagnostic size\n");
    return 2;
  }

  if (run_case(program, size, 0, 0, 0) ||
      run_case(program, size, 1, 0, 0) ||
      run_case(program, size, 0, 1, 0) ||
      run_case(program, size, 0, 0, 1))
    return 1;
  puts("JUKURAVI-SHARED-MEMORY: PASS "
       "(restore, data, address, retention and checksum paths)");
  return 0;
}
