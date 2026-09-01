#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define COM_ADDRESS 0x0100
#define STACK_RETURN 0x9bfe
#define EXPECTED_FRAMES 18
#define MAX_INSTRUCTIONS 3000000UL

typedef struct {
  uint8_t memory[65536];
  size_t pit_writes;
  int invalid_port;
} fixture;

typedef struct {
  uint16_t step[3], flags[3], delta[3];
  uint16_t phase, sample_loop, frame_tick, invalid_packet;
  uint16_t song_pointer, song_cursor;
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
  static const uint8_t magic[] = {'J', 'V', 'P', 'R', 1};
  for (uint16_t address = COM_ADDRESS;
       address + sizeof(magic) + 30 <= COM_ADDRESS + size; address++) {
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
    map->invalid_packet = word(f->memory, at); at += 2;
    map->song_pointer = word(f->memory, at); at += 2;
    map->song_cursor = word(f->memory, at);
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

static int check_frame(const fixture *f, const manifest *map, size_t frame) {
  static const uint16_t expected_steps[3][3] = {
    {4096, 8192, 12288},
    {4100, 0, 12288},
    {4100, 0, 12288},
  };
  static const uint8_t expected_enabled[3][3] = {
    {1, 1, 0},
    {1, 0, 1},
    {1, 0, 0},
  };
  static const uint8_t expected_delta[3][3] = {
    {0, 255, 0},
    {6, 0, 15},
    {6, 0, 0},
  };
  size_t stage = frame < 6 ? 0 : frame < 12 ? 1 : 2;
  for (size_t channel = 0; channel < 3; channel++) {
    uint16_t step = word(f->memory, map->step[channel]);
    uint8_t enabled = !!(f->memory[map->flags[channel]] & 0x40);
    uint8_t delta = f->memory[map->delta[channel]];
    if (step != expected_steps[stage][channel] ||
        enabled != expected_enabled[stage][channel] ||
        delta != expected_delta[stage][channel]) {
      fprintf(stderr,
          "vibrato parser mismatch frame=%zu channel=%zu "
          "step=%u/%u enabled=%u/%u delta=%u/%u\n",
          frame, channel + 1, step, expected_steps[stage][channel],
          enabled, expected_enabled[stage][channel],
          delta, expected_delta[stage][channel]);
      return 0;
    }
  }
  if (word(f->memory, map->phase) != 0) {
    fprintf(stderr, "parser-only slice advanced vibrato phase at frame %zu\n",
        frame);
    return 0;
  }
  return 1;
}

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s VIBRATO-PARSER.COM\n", argv[0]);
    return 2;
  }
  fixture f = {0};
  size_t image_size = load(argv[1], &f.memory[COM_ADDRESS]);
  manifest map;
  if (!locate_manifest(&f, image_size, &map)) {
    fprintf(stderr, "vibrato parser manifest not found\n");
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
    if (cpu.pc == map.invalid_packet) {
      fprintf(stderr,
          "vibrato parser rejected packet: song=%04x cursor=%04x "
          "flags=%02x\n",
          word(f.memory, map.song_pointer), word(f.memory, map.song_cursor),
          f.memory[map.flags[0]]);
      return 1;
    }
    if (cpu.pc == map.frame_tick)
      awaiting_sample = 1;
    if (cpu.pc == map.sample_loop && awaiting_sample) {
      if (frames >= EXPECTED_FRAMES || !check_frame(&f, &map, frames))
        return 1;
      frames++;
      awaiting_sample = 0;
    }
    i8080_step(&cpu);
  }

  if (!cpu.halted || cpu.pc != 1 || cpu.sp != STACK_RETURN + 2 ||
      !cpu.iff || f.invalid_port || frames != EXPECTED_FRAMES ||
      f.pit_writes < 100) {
    fprintf(stderr,
        "vibrato parser execution mismatch: halted=%d pc=%04x sp=%04x "
        "iff=%d invalid=%d frames=%zu pit=%zu instructions=%lu\n",
        cpu.halted, cpu.pc, cpu.sp, cpu.iff, f.invalid_port, frames,
        f.pit_writes, instructions);
    return 1;
  }
  printf("JUKUPOLY-VIBRATO-PARSER: PASS frames=%zu "
         "conditional-deltas=1/256 legato-update release-clear "
         "phase-inactive pit-writes=%zu\n", frames, f.pit_writes);
  return 0;
}
