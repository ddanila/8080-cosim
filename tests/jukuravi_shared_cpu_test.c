#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  uint8_t memory[65536];
} fixture;

static uint8_t read_byte(void *opaque, uint16_t address) {
  return ((fixture *)opaque)->memory[address];
}

static void write_byte(void *opaque, uint16_t address, uint8_t value) {
  ((fixture *)opaque)->memory[address] = value;
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

static int run_case(const uint8_t *program, size_t size, int inject_fault) {
  fixture f = {0};
  i8080 cpu;

  memcpy(&f.memory[0x4000], program, size);
  f.memory[0x0000] = 0x76; /* HLT after the loader-style return. */
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
  cpu.fault_a12_increment_high_loss = inject_fault;

  for (unsigned steps = 0; !cpu.halted && steps < 20000; steps++)
    i8080_step(&cpu);

  if (!cpu.halted || cpu.sp != 0x4e00) {
    fprintf(stderr, "shared CPU diagnostic did not return with restored SP\n");
    return 1;
  }
  if (f.memory[0x4e00] != (inject_fault ? 0x02 : 0x00)) {
    fprintf(stderr, "shared CPU result was %02x, fault=%d\n",
        f.memory[0x4e00], inject_fault);
    return 1;
  }
  return 0;
}

int main(int argc, char **argv) {
  uint8_t program[1024];
  FILE *input;
  size_t size;

  if (argc != 2) {
    fprintf(stderr, "usage: %s shared-cpu-4000.bin\n", argv[0]);
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
    fprintf(stderr, "unexpected shared CPU diagnostic size\n");
    return 2;
  }

  if (run_case(program, size, 0) || run_case(program, size, 1))
    return 1;
  puts("JUKURAVI-SHARED-CPU: PASS (clean and D1/A12 fault paths)");
  return 0;
}
