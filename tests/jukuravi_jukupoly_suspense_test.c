#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LOAD_ADDRESS 0x0100
#define EFFECTIVE_HZ 1700000.0
#define FRAME_SAMPLES 144
#define SMOKE_FRAMES 450
#define MAX_EVENTS 100000

typedef struct {
  uint8_t port, value;
} output_event;

typedef struct {
  uint8_t memory[65536];
  i8080 *cpu;
  output_event outputs[MAX_EVENTS];
  size_t output_count;
} fixture;

typedef struct {
  uint16_t sample_loop, frame_tick, phase[3], drum_pointer, drum_frames;
  uint16_t volume[3], slide_delta, row_frames, song_rows;
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
  if (f->output_count >= MAX_EVENTS) {
    fprintf(stderr, "JukuPoly Suspense output event buffer overflow\n");
    exit(1);
  }
  f->outputs[f->output_count++] = (output_event){port, value};
}

static uint16_t word(const uint8_t *memory, uint16_t address) {
  return memory[address] | (uint16_t)memory[(uint16_t)(address + 1)] << 8;
}

static void put_word(uint8_t *memory, uint16_t address, uint16_t value) {
  memory[address] = value & 0xff;
  memory[(uint16_t)(address + 1)] = value >> 8;
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
    for (int channel = 0; channel < 3; channel++, at += 2)
      result->phase[channel] = word(f->memory, at);
    result->drum_pointer = word(f->memory, at); at += 2;
    result->drum_frames = word(f->memory, at); at += 2;
    for (int channel = 0; channel < 3; channel++, at += 2)
      result->volume[channel] = word(f->memory, at);
    result->slide_delta = word(f->memory, at); at += 2;
    result->row_frames = word(f->memory, at); at += 2;
    result->song_rows = word(f->memory, at);
    return 1;
  }
  return 0;
}

static uint16_t row_at_frame(const fixture *f, uint16_t first,
                             unsigned wanted_frame) {
  uint16_t at = first;
  unsigned frame = 0;
  while (frame <= wanted_frame) {
    uint8_t duration = f->memory[at++];
    uint8_t flags = f->memory[at++];
    if (flags & 0x80)
      break;
    if (frame == wanted_frame)
      return at - 2;
    for (unsigned flag = 1; flag <= 4; flag <<= 1) {
      if (!(flags & flag))
        continue;
      uint16_t step = word(f->memory, at);
      at += 2;
      if (step & 0x7fff)
        at += 2;
    }
    if (flags & 0x08)
      at += 2;
    if (flags & 0x10)
      at += 2;
    frame += duration;
    if (frame > wanted_frame)
      break;
  }
  return 0;
}

int main(int argc, char **argv) {
  fixture f = {0};
  manifest map;
  i8080 cpu;
  if (argc < 2 || argc > 3) {
    fprintf(stderr, "usage: %s suspense.com [start-frame]\n", argv[0]);
    return 2;
  }
  unsigned start_frame = argc == 3 ? (unsigned)strtoul(argv[2], NULL, 0) : 2400;
  FILE *input = fopen(argv[1], "rb");
  if (!input) {
    perror(argv[1]);
    return 2;
  }
  size_t size = fread(&f.memory[LOAD_ADDRESS], 1,
      sizeof(f.memory) - LOAD_ADDRESS, input);
  fclose(input);
  if (size < 512 || size > 49152 || !locate_manifest(&f, size, &map)) {
    fprintf(stderr, "invalid JukuPoly Suspense image: %zu bytes\n", size);
    return 2;
  }
  uint16_t selected_row = row_at_frame(&f, map.song_rows, start_frame);
  if (!selected_row) {
    fprintf(stderr, "no JukuPoly row at frame %u\n", start_frame);
    return 1;
  }

  f.memory[0] = 0x76;
  f.memory[0x8ffe] = 0;
  f.memory[0x8fff] = 0;
  i8080_init(&cpu);
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.userdata = &f;
  cpu.pc = LOAD_ADDRESS;
  cpu.sp = 0x8ffe;
  cpu.iff = 1;
  f.cpu = &cpu;

  size_t frames = 0, samples = 0, drum_samples = 0;
  uint8_t active_mask = 0;
  unsigned long first_sample_cycle = 0, last_sample_cycle = 0;
  int redirected = 0, complete = 0;
  for (unsigned long instructions = 0; instructions < 10000000; instructions++) {
    if (cpu.pc == map.frame_tick) {
      if (!redirected) {
        /* song_pointer precedes song_cursor and row_frames in the ABI-v1 image. */
        put_word(f.memory, map.row_frames - 4, selected_row);
        f.memory[map.row_frames] = 0;
        redirected = 1;
      } else if (frames == SMOKE_FRAMES) {
        complete = 1;
        break;
      }
      frames++;
    }
    if (cpu.pc == map.sample_loop) {
      uint16_t steps[3] = {
        (uint16_t)cpu.b << 8 | cpu.c,
        (uint16_t)cpu.d << 8 | cpu.e,
        cpu.sp,
      };
      for (int channel = 0; channel < 3; channel++)
        if (steps[channel])
          active_mask |= 1u << channel;
      if (f.memory[map.drum_frames])
        drum_samples++;
      if (!first_sample_cycle)
        first_sample_cycle = cpu.cyc;
      last_sample_cycle = cpu.cyc;
      samples++;
    }
    i8080_step(&cpu);
  }

  if (!complete || frames != SMOKE_FRAMES ||
      samples != (size_t)SMOKE_FRAMES * FRAME_SAMPLES) {
    fprintf(stderr, "Suspense smoke window incomplete: frames=%zu samples=%zu\n",
        frames, samples);
    return 1;
  }
  if (active_mask != 0x07 || !drum_samples) {
    fprintf(stderr, "Suspense sources missing: tones=%02x drum=%zu\n",
        active_mask, drum_samples);
    return 1;
  }
  if (f.output_count < 1000 || f.outputs[0].port != 0x1b ||
      f.outputs[0].value != 0x50 || f.outputs[1].port != 0x19 ||
      f.outputs[1].value != 1) {
    fprintf(stderr, "Suspense PIT setup or pulse count differs\n");
    return 1;
  }
  for (size_t index = 2; index < f.output_count; index++) {
    if (f.outputs[index].port != 0x19 || !f.outputs[index].value ||
        f.outputs[index].value > 0xf0 || (f.outputs[index].value & 0x0f)) {
      fprintf(stderr, "unexpected Suspense pulse %02x:%02x\n",
          f.outputs[index].port, f.outputs[index].value);
      return 1;
    }
  }
  double sample_rate = EFFECTIVE_HZ * (samples - 1) /
      (last_sample_cycle - first_sample_cycle);
  if (sample_rate < 6000.0 || sample_rate > 8000.0) {
    fprintf(stderr, "Suspense sample rate differs: %.1f Hz\n", sample_rate);
    return 1;
  }
  printf("JUKUPOLY-SUSPENSE: PASS window=%.3f-%.3fs sample=%.1fHz "
         "tones=3 drum-samples=%zu pulses=%zu\n",
      start_frame / 50.0, (start_frame + SMOKE_FRAMES) / 50.0,
      sample_rate, drum_samples, f.output_count - 2);
  return 0;
}
