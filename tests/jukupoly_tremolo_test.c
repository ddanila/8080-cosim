#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define COM_ADDRESS 0x0100
#define STACK_RETURN 0x9bfe
#define EXPECTED_FRAMES 200
#define MAX_INSTRUCTIONS 20000000UL
#define PHASE_INCREMENT 4850

typedef struct {
  uint8_t memory[65536];
  size_t pit_writes;
  int invalid_port;
} fixture;

typedef struct {
  uint16_t sample_loop, frame_tick;
  uint16_t prepared[3], base[3], flags[3];
  uint16_t phase, prepare_frame;
} manifest;

static const uint8_t tables[4][16] = {
  {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  {0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0},
  {0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0},
  {0, 0, 1, 1, 2, 2, 3, 3, 3, 3, 2, 2, 1, 1, 0, 0},
};

static uint8_t read_byte(void *opaque, uint16_t address) {
  return ((fixture *)opaque)->memory[address];
}

static void write_byte(void *opaque, uint16_t address, uint8_t value) {
  ((fixture *)opaque)->memory[address] = value;
}

static uint8_t port_in(void *opaque, uint8_t port) {
  (void)port;
  ((fixture *)opaque)->invalid_port = 1;
  return 0xff;
}

static void port_out(void *opaque, uint8_t port, uint8_t value) {
  fixture *f = opaque;
  (void)value;
  if (port != 0x19 && port != 0x1b)
    f->invalid_port = 1;
  else
    f->pit_writes++;
}

static uint16_t word(const uint8_t *memory, uint16_t address) {
  return memory[address] | (uint16_t)memory[(uint16_t)(address + 1)] << 8;
}

static int locate_manifest(const fixture *f, size_t size, manifest *map) {
  static const uint8_t magic[] = {'J', 'T', 'R', 'E', 1};
  for (uint16_t address = COM_ADDRESS;
       address + sizeof(magic) + 26 <= COM_ADDRESS + size; address++) {
    if (memcmp(&f->memory[address], magic, sizeof(magic)) != 0)
      continue;
    uint16_t at = (uint16_t)(address + sizeof(magic));
    map->sample_loop = word(f->memory, at); at += 2;
    map->frame_tick = word(f->memory, at); at += 2;
    for (size_t channel = 0; channel < 3; channel++, at += 2)
      map->prepared[channel] = word(f->memory, at);
    for (size_t channel = 0; channel < 3; channel++, at += 2)
      map->base[channel] = word(f->memory, at);
    for (size_t channel = 0; channel < 3; channel++, at += 2)
      map->flags[channel] = word(f->memory, at);
    map->phase = word(f->memory, at); at += 2;
    map->prepare_frame = word(f->memory, at);
    return 1;
  }
  return 0;
}

static size_t load(const char *path, uint8_t *destination) {
  FILE *input = fopen(path, "rb");
  if (!input) {
    perror(path);
    exit(2);
  }
  if (fseek(input, 0, SEEK_END))
    exit(2);
  long length = ftell(input);
  if (length <= 0 || length >= 0x1700 || fseek(input, 0, SEEK_SET))
    exit(2);
  if (fread(destination, 1, (size_t)length, input) != (size_t)length)
    exit(2);
  fclose(input);
  return (size_t)length;
}

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s TREMOLO.COM\n", argv[0]);
    return 2;
  }
  fixture f = {0};
  size_t image_size = load(argv[1], &f.memory[COM_ADDRESS]);
  manifest map;
  if (!locate_manifest(&f, image_size, &map)) {
    fprintf(stderr, "tremolo manifest not found\n");
    return 2;
  }
  f.memory[0] = 0x76;
  f.memory[STACK_RETURN] = 0;
  f.memory[STACK_RETURN + 1] = 0;

  i8080 cpu;
  i8080_init(&cpu);
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.userdata = &f;
  cpu.pc = COM_ADDRESS;
  cpu.sp = STACK_RETURN;
  cpu.iff = 1;

  size_t frames = 0;
  int awaiting_sample = 0;
  unsigned long instructions;
  for (instructions = 0;
       !cpu.halted && instructions < MAX_INSTRUCTIONS; instructions++) {
    if (cpu.pc == map.frame_tick)
      awaiting_sample = 1;
    if (cpu.pc == map.sample_loop && awaiting_sample) {
      if (frames >= EXPECTED_FRAMES) {
        fprintf(stderr, "too many tremolo frames\n");
        return 1;
      }
      uint16_t phase = (uint16_t)(frames * PHASE_INCREMENT);
      unsigned index = phase >> 12;
      for (unsigned channel = 0; channel < 3; channel++) {
        uint8_t expected = (uint8_t)(15 - tables[channel + 1][index]);
        uint8_t actual = f.memory[map.prepared[channel]];
        if (actual != expected) {
          fprintf(stderr,
              "tremolo mismatch frame=%zu channel=%u phase=%04x "
              "actual=%u expected=%u\n",
              frames, channel + 1, phase, actual, expected);
          return 1;
        }
      }
      frames++;
      awaiting_sample = 0;
    }
    i8080_step(&cpu);
  }

  uint16_t final_phase = (uint16_t)(EXPECTED_FRAMES * PHASE_INCREMENT);
  if (!cpu.halted || cpu.pc != 1 || cpu.sp != STACK_RETURN + 2 ||
      !cpu.iff || f.invalid_port || frames != EXPECTED_FRAMES ||
      word(f.memory, map.phase) != final_phase ||
      f.memory[map.prepare_frame] != 0xc3 || f.pit_writes < 100) {
    fprintf(stderr,
        "tremolo execution mismatch: halted=%d pc=%04x sp=%04x iff=%d "
        "invalid=%d frames=%zu phase=%04x/%04x opcode=%02x pit=%zu "
        "instructions=%lu\n",
        cpu.halted, cpu.pc, cpu.sp, cpu.iff, f.invalid_port, frames,
        word(f.memory, map.phase), final_phase,
        f.memory[map.prepare_frame], f.pit_writes, instructions);
    return 1;
  }
  for (unsigned channel = 0; channel < 3; channel++) {
    if (f.memory[map.base[channel]] != 15 ||
        (f.memory[map.flags[channel]] & 0x30) != (channel + 1) * 0x10) {
      fprintf(stderr, "tremolo corrupted envelope state on channel %u\n",
          channel + 1);
      return 1;
    }
  }
  printf("JUKUPOLY-TREMOLO: PASS frames=%zu phase=%04x "
         "depths=1/2/3 envelope-base=15 prepared-exact pit-writes=%zu\n",
      frames, final_phase, f.pit_writes);
  return 0;
}
