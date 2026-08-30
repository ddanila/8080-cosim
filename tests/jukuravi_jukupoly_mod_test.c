#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LOAD_ADDRESS 0x0100
#define STACK_RETURN 0x9bfe
#define FRAME_SAMPLES 139
#define MAX_INSTRUCTIONS 150000000UL

typedef struct {
  uint8_t memory[65536];
  size_t output_count;
  int invalid_output;
} fixture;

typedef struct {
  uint16_t sample_loop, frame_tick, drum_frames;
  uint16_t volume[3];
  uint16_t volume_delta[3], pitch_delta[3], porta_target[3];
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
  if (f->output_count == 0) {
    if (port != 0x1b || value != 0x50)
      f->invalid_output = 1;
  } else if (f->output_count == 1) {
    if (port != 0x19 || value != 1)
      f->invalid_output = 1;
  } else if (port != 0x19 && port != 0x1b) {
    f->invalid_output = 1;
  } else if (port == 0x19 &&
             (value == 0 || value > 0xf0 || (value & 0x0f))) {
    /* The final silence write is the one permitted non-nibble count. */
    if (value != 1)
      f->invalid_output = 1;
  }
  f->output_count++;
}

static uint16_t word(const uint8_t *memory, uint16_t address) {
  return memory[address] | (uint16_t)memory[(uint16_t)(address + 1)] << 8;
}

static int locate_manifest(const fixture *f, size_t size, manifest *result) {
  static const uint8_t magic[] = {'J', 'P', 'O', 'L', 1};
  for (uint16_t address = LOAD_ADDRESS;
       address + sizeof(magic) + 44 <= LOAD_ADDRESS + size; address++) {
    if (memcmp(&f->memory[address], magic, sizeof(magic)) != 0)
      continue;
    uint16_t at = address + sizeof(magic);
    result->sample_loop = word(f->memory, at); at += 2;
    result->frame_tick = word(f->memory, at); at += 2;
    at += 8; /* three phase immediates and the drum PCM pointer */
    result->drum_frames = word(f->memory, at); at += 2;
    for (int channel = 0; channel < 3; channel++, at += 2)
      result->volume[channel] = word(f->memory, at);
    at += 6; /* legacy slide, row count, and score base */
    for (int channel = 0; channel < 3; channel++, at += 2)
      result->volume_delta[channel] = word(f->memory, at);
    for (int channel = 0; channel < 3; channel++, at += 2)
      result->pitch_delta[channel] = word(f->memory, at);
    for (int channel = 0; channel < 3; channel++, at += 2)
      result->porta_target[channel] = word(f->memory, at);
    return 1;
  }
  return 0;
}

int main(int argc, char **argv) {
  fixture f = {0};
  manifest map;
  i8080 cpu;
  if (argc != 3) {
    fprintf(stderr, "usage: %s tdk-robots.com expected-frames\n", argv[0]);
    return 2;
  }
  unsigned long expected_frames = strtoul(argv[2], NULL, 0);
  if (!expected_frames) {
    fprintf(stderr, "expected frame count must be nonzero\n");
    return 2;
  }

  FILE *input = fopen(argv[1], "rb");
  if (!input) {
    perror(argv[1]);
    return 2;
  }
  size_t maximum = STACK_RETURN - LOAD_ADDRESS;
  size_t size = fread(&f.memory[LOAD_ADDRESS], 1, maximum + 1, input);
  int read_error = ferror(input);
  fclose(input);
  if (read_error || size < 512 || size > maximum ||
      !locate_manifest(&f, size, &map)) {
    fprintf(stderr, "invalid or oversized JukuPoly MOD image: %zu bytes\n", size);
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

  size_t frame_entries = 0, sample_entries = 0;
  uint8_t tone_mask = 0, largest_drum_frames = 0;
  int saw_volume_slide = 0, saw_pitch_slide = 0, saw_portamento = 0;
  int moved_volume_slide = 0, moved_pitch_slide = 0, moved_portamento = 0;
  uint16_t previous_step[3] = {0};
  uint8_t previous_volume[3] = {0};
  uint8_t previous_volume_slide[3] = {0};
  uint16_t previous_pitch_slide[3] = {0}, previous_portamento[3] = {0};
  int have_previous_frame = 0;
  for (unsigned long instructions = 0;
       !cpu.halted && instructions < MAX_INSTRUCTIONS; instructions++) {
    if (cpu.pc == map.frame_tick) {
      frame_entries++;
      uint8_t drum_frames = f.memory[map.drum_frames];
      uint16_t step[3] = {
        (uint16_t)cpu.b << 8 | cpu.c,
        (uint16_t)cpu.d << 8 | cpu.e,
        cpu.sp,
      };
      if (drum_frames > largest_drum_frames)
        largest_drum_frames = drum_frames;
      for (int channel = 0; channel < 3; channel++) {
        uint8_t volume = f.memory[map.volume[channel]];
        uint8_t volume_slide = f.memory[map.volume_delta[channel]];
        uint16_t pitch_slide = word(f.memory, map.pitch_delta[channel]);
        uint16_t portamento = word(f.memory, map.porta_target[channel]);
        if (have_previous_frame) {
          moved_volume_slide |= previous_volume_slide[channel] &&
              volume != previous_volume[channel];
          moved_pitch_slide |= previous_pitch_slide[channel] &&
              step[channel] != previous_step[channel];
          moved_portamento |= previous_portamento[channel] &&
              step[channel] != previous_step[channel];
        }
        saw_volume_slide |= volume_slide != 0;
        saw_pitch_slide |= pitch_slide != 0;
        saw_portamento |= portamento != 0;
        previous_step[channel] = step[channel];
        previous_volume[channel] = volume;
        previous_volume_slide[channel] = volume_slide;
        previous_pitch_slide[channel] = pitch_slide;
        previous_portamento[channel] = portamento;
      }
      have_previous_frame = 1;
    }
    if (cpu.pc == map.sample_loop) {
      uint16_t steps[3] = {
        (uint16_t)cpu.b << 8 | cpu.c,
        (uint16_t)cpu.d << 8 | cpu.e,
        cpu.sp,
      };
      for (int channel = 0; channel < 3; channel++)
        if (steps[channel])
          tone_mask |= 1u << channel;
      sample_entries++;
    }
    i8080_step(&cpu);
  }

  if (!cpu.halted || cpu.pc != 1 || cpu.sp != STACK_RETURN + 2 || !cpu.iff) {
    fprintf(stderr,
        "MOD player did not return cleanly: halted=%d pc=%04x sp=%04x iff=%d\n",
        cpu.halted, cpu.pc, cpu.sp, cpu.iff);
    return 1;
  }
  if (frame_entries != expected_frames + 1 ||
      sample_entries != expected_frames * FRAME_SAMPLES) {
    fprintf(stderr, "MOD frame count differs: frames=%zu samples=%zu\n",
        frame_entries, sample_entries);
    return 1;
  }
  if (f.invalid_output || f.output_count < 1000 || tone_mask != 7) {
    fprintf(stderr, "MOD output differs: invalid=%d writes=%zu tones=%02x\n",
        f.invalid_output, f.output_count, tone_mask);
    return 1;
  }
  if (!saw_volume_slide || !moved_volume_slide ||
      !saw_pitch_slide || !moved_pitch_slide ||
      (expected_frames > 3000 && (!saw_portamento || !moved_portamento)) ||
      largest_drum_frames < 40) {
    fprintf(stderr,
        "MOD features missing: volume-slide=%d/%d pitch-slide=%d/%d "
        "porta=%d/%d pcm=%u\n",
        saw_volume_slide, moved_volume_slide, saw_pitch_slide,
        moved_pitch_slide, saw_portamento, moved_portamento,
        largest_drum_frames);
    return 1;
  }

  printf("JUKUPOLY-MOD: PASS bytes=%zu frames=%zu tones=3 "
         "volume-slide=1 pitch-slide=1 porta=%d pcm-frames=%u writes=%zu\n",
      size, frame_entries - 1, saw_portamento, largest_drum_frames,
      f.output_count);
  return 0;
}
