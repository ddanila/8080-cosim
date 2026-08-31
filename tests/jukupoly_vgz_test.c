#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LOAD_ADDRESS 0x0100
#define STACK_RETURN 0x8ffe
#define FRAME_SAMPLES 143
#define EFFECTIVE_HZ 1700000.0
#define MAX_INSTRUCTIONS 100000000UL

typedef struct {
  uint8_t memory[65536];
  size_t writes;
  uint8_t first_port[2], first_value[2];
  uint8_t last_port[2], last_value[2];
  int invalid_write;
} fixture;

typedef struct {
  uint16_t sample_loop, frame_tick, drum_frames;
} manifest;

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
  fixture *f = opaque;
  if (f->writes < 2) {
    f->first_port[f->writes] = port;
    f->first_value[f->writes] = value;
  }
  f->last_port[0] = f->last_port[1];
  f->last_value[0] = f->last_value[1];
  f->last_port[1] = port;
  f->last_value[1] = value;
  if (port != 0x19 && port != 0x1b)
    f->invalid_write = 1;
  if (f->writes >= 2 && port == 0x19 && value != 1 &&
      (!value || value > 0xf0 || (value & 0x0f)))
    f->invalid_write = 1;
  f->writes++;
}

static uint16_t word(const uint8_t *memory, uint16_t address) {
  return memory[address] | (uint16_t)memory[(uint16_t)(address + 1)] << 8;
}

static int locate_manifest(const fixture *f, size_t size, manifest *result) {
  static const uint8_t magic[] = {'J', 'P', 'O', 'L', 1};
  for (uint16_t address = LOAD_ADDRESS;
       address + sizeof(magic) + 26 <= LOAD_ADDRESS + size; address++) {
    if (memcmp(&f->memory[address], magic, sizeof(magic)) != 0)
      continue;
    uint16_t at = address + sizeof(magic);
    result->sample_loop = word(f->memory, at); at += 2;
    result->frame_tick = word(f->memory, at); at += 2;
    at += 8; /* phase immediates and drum PCM pointer */
    result->drum_frames = word(f->memory, at);
    return 1;
  }
  return 0;
}

int main(int argc, char **argv) {
  fixture f = {0};
  manifest map;
  i8080 cpu;
  if (argc != 5 && argc != 6) {
    fprintf(stderr,
        "usage: %s image.com expected-frames min-seconds max-seconds "
        "[require-drums]\n",
        argv[0]);
    return 2;
  }
  char *end = NULL;
  unsigned long expected_frames = strtoul(argv[2], &end, 0);
  if (!*argv[2] || *end || !expected_frames) {
    fprintf(stderr, "invalid expected frame count: %s\n", argv[2]);
    return 2;
  }
  double min_duration = strtod(argv[3], &end);
  if (!*argv[3] || *end) {
    fprintf(stderr, "invalid minimum duration: %s\n", argv[3]);
    return 2;
  }
  double max_duration = strtod(argv[4], &end);
  if (!*argv[4] || *end || max_duration <= min_duration) {
    fprintf(stderr, "invalid maximum duration: %s\n", argv[4]);
    return 2;
  }
  int require_drums = 1;
  if (argc == 6) {
    unsigned long value = strtoul(argv[5], &end, 0);
    if (!*argv[5] || *end || value > 1) {
      fprintf(stderr, "require-drums must be 0 or 1: %s\n", argv[5]);
      return 2;
    }
    require_drums = value;
  }
  FILE *input = fopen(argv[1], "rb");
  if (!input) {
    perror(argv[1]);
    return 2;
  }
  size_t size = fread(&f.memory[LOAD_ADDRESS], 1,
      STACK_RETURN - LOAD_ADDRESS + 1, input);
  int read_error = ferror(input);
  fclose(input);
  if (read_error || size < 512 || size > STACK_RETURN - LOAD_ADDRESS ||
      !locate_manifest(&f, size, &map)) {
    fprintf(stderr, "invalid JukuPoly VGZ-reduction image: %zu bytes\n", size);
    return 2;
  }

  f.memory[0] = 0x76;
  f.memory[STACK_RETURN] = 0;
  f.memory[STACK_RETURN + 1] = 0;
  i8080_init(&cpu);
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.userdata = &f;
  cpu.pc = LOAD_ADDRESS;
  cpu.sp = STACK_RETURN;
  cpu.iff = 1;

  size_t frames = 0, samples = 0, drum_samples = 0, three_tone_samples = 0;
  uint8_t tone_mask = 0;
  for (unsigned long instructions = 0;
       !cpu.halted && instructions < MAX_INSTRUCTIONS; instructions++) {
    if (cpu.pc == map.frame_tick)
      frames++;
    if (cpu.pc == map.sample_loop) {
      uint16_t steps[3] = {
        (uint16_t)cpu.b << 8 | cpu.c,
        (uint16_t)cpu.d << 8 | cpu.e,
        cpu.sp,
      };
      int active = 0;
      for (int channel = 0; channel < 3; channel++) {
        if (steps[channel]) {
          tone_mask |= 1u << channel;
          active++;
        }
      }
      if (active == 3)
        three_tone_samples++;
      if (f.memory[map.drum_frames])
        drum_samples++;
      samples++;
    }
    i8080_step(&cpu);
  }

  if (!cpu.halted || cpu.pc != 1 || cpu.sp != STACK_RETURN + 2 || !cpu.iff) {
    fprintf(stderr,
        "VGZ reduction did not return cleanly: halted=%d pc=%04x sp=%04x iff=%d\n",
        cpu.halted, cpu.pc, cpu.sp, cpu.iff);
    return 1;
  }
  if (frames != expected_frames + 1 ||
      samples != (size_t)expected_frames * FRAME_SAMPLES) {
    fprintf(stderr, "VGZ frame count differs: frames=%zu samples=%zu\n",
        frames, samples);
    return 1;
  }
  if (tone_mask != 7 || !three_tone_samples ||
      (require_drums && !drum_samples)) {
    fprintf(stderr, "VGZ sources missing: tones=%02x simultaneous=%zu drum=%zu\n",
        tone_mask, three_tone_samples, drum_samples);
    return 1;
  }
  if (f.invalid_write || f.writes < 1000 ||
      f.first_port[0] != 0x1b || f.first_value[0] != 0x50 ||
      f.first_port[1] != 0x19 || f.first_value[1] != 1 ||
      f.last_port[0] != 0x1b || f.last_value[0] != 0x50 ||
      f.last_port[1] != 0x19 || f.last_value[1] != 1) {
    fprintf(stderr, "VGZ PIT output differs: invalid=%d writes=%zu\n",
        f.invalid_write, f.writes);
    return 1;
  }
  double duration = cpu.cyc / EFFECTIVE_HZ;
  if (duration < min_duration || duration > max_duration) {
    fprintf(stderr, "VGZ cycle duration differs: %.3f s\n", duration);
    return 1;
  }
  printf("JUKUPOLY-VGZ: PASS bytes=%zu frames=%zu duration=%.3fs "
         "tones=3 simultaneous=%zu drum-samples=%zu writes=%zu\n",
      size, frames - 1, duration, three_tone_samples, drum_samples, f.writes);
  return 0;
}
