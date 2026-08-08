#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

enum { PROGRAM = 0x2000 };

typedef struct fixture {
  uint8_t mem[65536];
  unsigned vector_index;
  uint16_t written[4];
  unsigned write_count;
} fixture;

static uint8_t baseline(uint16_t address) {
  return (uint8_t)(((uint32_t)address * 37u + 0x5Au) & 0xFFu);
}

static uint8_t read_byte(void* userdata, uint16_t address) {
  return ((fixture*)userdata)->mem[address];
}

static void write_byte(void* userdata, uint16_t address, uint8_t value) {
  fixture* f = userdata;
  f->mem[address] = value;
  if (f->write_count < sizeof(f->written) / sizeof(f->written[0])) {
    f->written[f->write_count++] = address;
  }
  printf("WRITE %u %04x %02x\n", f->vector_index, address, value);
}

static uint8_t port_in(void* userdata, uint8_t port) {
  (void)userdata;
  return (uint8_t)(port ^ 0xA5u);
}

static void port_out(void* userdata, uint8_t port, uint8_t value) {
  fixture* f = userdata;
  printf("IOOUT %u %02x %02x\n", f->vector_index, port, value);
}

static uint8_t pack_flags(const i8080* cpu) {
  return (uint8_t)((cpu->sf << 7) | (cpu->zf << 6) | (cpu->hf << 4) |
                   (cpu->pf << 2) | 0x02 | cpu->cf);
}

int main(int argc, char** argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s VECTOR_FILE\n", argv[0]);
    return 2;
  }
  FILE* vectors = fopen(argv[1], "r");
  if (!vectors) {
    perror(argv[1]);
    return 2;
  }
  fixture* f = calloc(1, sizeof(*f));
  if (!f) {
    fclose(vectors);
    return 2;
  }
  for (unsigned address = 0; address < 65536; address++) {
    f->mem[address] = baseline((uint16_t)address);
  }

  unsigned index, opcode, flags, op1, op2, a, bc, de, hl, sp, iff;
  unsigned mem_hl, stack_lo, stack_hi;
  unsigned count = 0;
  while (fscanf(vectors, " %x %x %x %x %x %x %x %x %x %x %x %x %x %x",
                &index, &opcode, &flags, &op1, &op2, &a, &bc, &de, &hl, &sp,
                &iff, &mem_hl, &stack_lo, &stack_hi) == 14) {
    f->vector_index = index;
    f->write_count = 0;
    f->mem[PROGRAM] = (uint8_t)opcode;
    f->mem[PROGRAM + 1] = (uint8_t)op1;
    f->mem[PROGRAM + 2] = (uint8_t)op2;
    f->mem[hl] = (uint8_t)mem_hl;
    f->mem[sp] = (uint8_t)stack_lo;
    f->mem[(uint16_t)(sp + 1)] = (uint8_t)stack_hi;

    i8080 cpu;
    i8080_init(&cpu);
    cpu.read_byte = read_byte;
    cpu.write_byte = write_byte;
    cpu.port_in = port_in;
    cpu.port_out = port_out;
    cpu.userdata = f;
    cpu.pc = PROGRAM;
    cpu.sp = (uint16_t)sp;
    cpu.a = (uint8_t)a;
    cpu.b = (uint8_t)(bc >> 8);
    cpu.c = (uint8_t)bc;
    cpu.d = (uint8_t)(de >> 8);
    cpu.e = (uint8_t)de;
    cpu.h = (uint8_t)(hl >> 8);
    cpu.l = (uint8_t)hl;
    cpu.sf = (flags >> 4) & 1;
    cpu.zf = (flags >> 3) & 1;
    cpu.hf = (flags >> 2) & 1;
    cpu.pf = (flags >> 1) & 1;
    cpu.cf = flags & 1;
    cpu.iff = iff & 1;
    i8080_step(&cpu);
    printf("RESULT %u %02x %02x %04x %04x %04x %04x %04x %02x %u %u\n",
           index, opcode, cpu.a, ((unsigned)cpu.b << 8) | cpu.c,
           ((unsigned)cpu.d << 8) | cpu.e, ((unsigned)cpu.h << 8) | cpu.l,
           cpu.sp, cpu.pc, pack_flags(&cpu), cpu.iff, cpu.halted);

    f->mem[PROGRAM] = baseline(PROGRAM);
    f->mem[PROGRAM + 1] = baseline(PROGRAM + 1);
    f->mem[PROGRAM + 2] = baseline(PROGRAM + 2);
    f->mem[hl] = baseline((uint16_t)hl);
    f->mem[sp] = baseline((uint16_t)sp);
    f->mem[(uint16_t)(sp + 1)] = baseline((uint16_t)(sp + 1));
    for (unsigned written = 0; written < f->write_count; written++) {
      f->mem[f->written[written]] = baseline(f->written[written]);
    }
    count++;
  }
  if (!feof(vectors)) {
    fprintf(stderr, "malformed vector file after %u cases\n", count);
    free(f);
    fclose(vectors);
    return 2;
  }
  free(f);
  fclose(vectors);
  return 0;
}
