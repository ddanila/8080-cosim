#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define COM_ADDRESS 0x0100
#define STACK_RETURN 0x9bfe
#define EXPECTED_FRAMES 18
#define MAX_INSTRUCTIONS 3000000UL
#define PHASE_INCREMENT 7955

typedef struct {
  uint8_t memory[65536];
  size_t pit_writes;
  int invalid_port;
} fixture;

typedef struct {
  uint16_t step[3], flags[3], delta[3];
  uint16_t phase, sample_loop, frame_tick, prepare_frame;
} manifest;

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
  static const uint8_t magic[] = {'J', 'V', 'I', 'B', 1};
  for (uint16_t address = COM_ADDRESS;
       address + sizeof(magic) + 26 <= COM_ADDRESS + size; address++) {
    if (memcmp(&f->memory[address], magic, sizeof(magic)) != 0)
      continue;
    uint16_t at = (uint16_t)(address + sizeof(magic));
    for (size_t channel = 0; channel < 3; channel++, at += 2)
      map->step[channel] = word(f->memory, at);
    for (size_t channel = 0; channel < 3; channel++, at += 2)
      map->flags[channel] = word(f->memory, at);
    for (size_t channel = 0; channel < 3; channel++, at += 2)
      map->delta[channel] = word(f->memory, at);
    map->phase = word(f->memory, at); at += 2;
    map->sample_loop = word(f->memory, at); at += 2;
    map->frame_tick = word(f->memory, at); at += 2;
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

static uint16_t temporary_step(uint16_t base, unsigned peak,
                               uint16_t phase, int enabled) {
  if (!enabled || !base)
    return base;
  unsigned position = phase >> 13;
  unsigned magnitude = peak;
  if (position == 0 || position == 4)
    magnitude = 0;
  else if (position != 2 && position != 6)
    magnitude /= 2;
  return (uint16_t)(position & 4 ? base - magnitude : base + magnitude);
}

static int check_frame(const fixture *f, const manifest *map,
                       const i8080 *cpu, size_t frame) {
  static const uint16_t bases[3][3] = {
    {4096, 8192, 12288},
    {4100, 0, 12288},
    {4100, 0, 12288},
  };
  static const unsigned peaks[3][3] = {
    {1, 256, 0},
    {7, 0, 16},
    {7, 0, 0},
  };
  size_t stage = frame < 6 ? 0 : frame < 12 ? 1 : 2;
  uint16_t phase = (uint16_t)(frame * PHASE_INCREMENT);
  uint16_t actual[3] = {
    (uint16_t)cpu->b << 8 | cpu->c,
    (uint16_t)cpu->d << 8 | cpu->e,
    cpu->sp,
  };
  for (size_t channel = 0; channel < 3; channel++) {
    uint16_t base = word(f->memory, map->step[channel]);
    int enabled = !!(f->memory[map->flags[channel]] & 0x40);
    uint8_t encoded = f->memory[map->delta[channel]];
    uint16_t expected = temporary_step(
        bases[stage][channel], peaks[stage][channel], phase,
        peaks[stage][channel] != 0);
    uint8_t expected_encoded = peaks[stage][channel]
        ? (uint8_t)(peaks[stage][channel] - 1) : 0;
    if (base != bases[stage][channel] ||
        enabled != (peaks[stage][channel] != 0) ||
        encoded != expected_encoded || actual[channel] != expected) {
      fprintf(stderr,
          "vibrato mismatch frame=%zu channel=%zu phase=%04x "
          "base=%u/%u enabled=%d/%d delta=%u/%u step=%u/%u\n",
          frame, channel + 1, phase, base, bases[stage][channel],
          enabled, peaks[stage][channel] != 0, encoded, expected_encoded,
          actual[channel], expected);
      return 0;
    }
  }
  uint16_t expected_phase = (uint16_t)((frame + 1) * PHASE_INCREMENT);
  if (word(f->memory, map->phase) != expected_phase) {
    fprintf(stderr, "vibrato phase mismatch frame=%zu actual=%04x expected=%04x\n",
        frame, word(f->memory, map->phase), expected_phase);
    return 0;
  }
  return 1;
}

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s VIBRATO.COM\n", argv[0]);
    return 2;
  }
  fixture f = {0};
  size_t image_size = load(argv[1], &f.memory[COM_ADDRESS]);
  manifest map;
  if (!locate_manifest(&f, image_size, &map)) {
    fprintf(stderr, "vibrato runtime manifest not found\n");
    return 2;
  }
  for (size_t channel = 0; channel < 3; channel++) {
    f.memory[map.step[channel]] = 0x77;
    f.memory[(uint16_t)(map.step[channel] + 1)] = 0x77;
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
  int initial_bases_cleared = 0;
  unsigned long instructions;
  for (instructions = 0;
       !cpu.halted && instructions < MAX_INSTRUCTIONS; instructions++) {
    if (cpu.pc == map.frame_tick) {
      if (!frames && !initial_bases_cleared) {
        if (word(f.memory, map.step[0]) || word(f.memory, map.step[1]) ||
            word(f.memory, map.step[2])) {
          fprintf(stderr, "vibrato init retained a prior song base step\n");
          return 1;
        }
        initial_bases_cleared = 1;
      }
      awaiting_sample = 1;
    }
    if (cpu.pc == map.sample_loop && awaiting_sample) {
      if (frames >= EXPECTED_FRAMES || !check_frame(&f, &map, &cpu, frames))
        return 1;
      frames++;
      awaiting_sample = 0;
    }
    i8080_step(&cpu);
  }

  uint16_t final_phase = (uint16_t)(EXPECTED_FRAMES * PHASE_INCREMENT);
  if (!cpu.halted || cpu.pc != 1 || cpu.sp != STACK_RETURN + 2 ||
      !cpu.iff || f.invalid_port || !initial_bases_cleared ||
      frames != EXPECTED_FRAMES ||
      word(f.memory, map.phase) != final_phase ||
      f.memory[map.prepare_frame] != 0xc3 || f.pit_writes < 100) {
    fprintf(stderr,
        "vibrato execution mismatch: halted=%d pc=%04x sp=%04x iff=%d "
        "invalid=%d init-clear=%d frames=%zu phase=%04x/%04x "
        "opcode=%02x pit=%zu "
        "instructions=%lu\n",
        cpu.halted, cpu.pc, cpu.sp, cpu.iff, f.invalid_port,
        initial_bases_cleared, frames,
        word(f.memory, map.phase), final_phase,
        f.memory[map.prepare_frame], f.pit_writes, instructions);
    return 1;
  }
  printf("JUKUPOLY-VIBRATO: PASS frames=%zu phase=%04x "
         "shape=0/+half/+full/+half/0/-half/-full/-half "
         "deltas=1/256 legato release reuse-clear immutable-base "
         "pit-writes=%zu\n",
      frames, final_phase, f.pit_writes);
  return 0;
}
