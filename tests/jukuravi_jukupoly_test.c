#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LOAD_ADDRESS 0x0100
#define EFFECTIVE_HZ 1700000.0
#define EXPECTED_FRAMES 369
#define FRAME_SAMPLES 144
#define MAX_EVENTS 100000

typedef struct {
  uint8_t port;
  uint8_t value;
  unsigned long cycle;
} output_event;

typedef struct {
  uint8_t memory[65536];
  i8080 *cpu;
  output_event outputs[MAX_EVENTS];
  size_t output_count;
} fixture;

typedef struct {
  uint16_t sample_loop, frame_tick;
  uint16_t phase[3], drum_pointer, drum_frames;
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
    fprintf(stderr, "JukuPoly output event buffer overflow\n");
    exit(1);
  }
  f->outputs[f->output_count++] = (output_event){port, value, f->cpu->cyc};
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

static double event_frequency(size_t count, unsigned long first,
                              unsigned long last) {
  if (count < 2 || first == last)
    return 0.0;
  return EFFECTIVE_HZ * (count - 1) / (last - first);
}

static int near(double actual, double wanted, double tolerance) {
  return actual >= wanted - tolerance && actual <= wanted + tolerance;
}

int main(int argc, char **argv) {
  fixture f = {0};
  i8080 cpu;
  FILE *input;
  size_t size;
  manifest map;
  unsigned long first_sample_cycle = 0, last_first_row_sample_cycle = 0;
  unsigned long first_wrap[3] = {0}, last_wrap[3] = {0};
  size_t first_row_samples = 0, wraps[3] = {0};
  size_t frame_entries = 0, sample_entries = 0;
  size_t drum_active_samples = 0, simultaneous_samples = 0;
  uint16_t previous_phase[3] = {0};
  uint8_t previous_volume[3] = {0};
  int have_previous_phase = 0, have_previous_volume = 0;
  int saw_attack_step = 0, saw_decay_step = 0, saw_slide = 0;
  uint16_t first_slide_step = 0, last_slide_step = 0;

  if (argc != 2) {
    fprintf(stderr, "usage: %s jukupoly.com\n", argv[0]);
    return 2;
  }
  input = fopen(argv[1], "rb");
  if (!input) {
    perror(argv[1]);
    return 2;
  }
  size = fread(&f.memory[LOAD_ADDRESS], 1,
      sizeof(f.memory) - LOAD_ADDRESS, input);
  fclose(input);
  if (size < 512 || size > 16384 || !locate_manifest(&f, size, &map)) {
    fprintf(stderr, "invalid JukuPoly image or missing manifest: %zu bytes\n", size);
    return 2;
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

  for (unsigned long instructions = 0;
       !cpu.halted && instructions < 10000000; instructions++) {
    if (cpu.pc == map.frame_tick) {
      frame_entries++;
      uint8_t volumes[3];
      for (int channel = 0; channel < 3; channel++)
        volumes[channel] = f.memory[map.volume[channel]];
      if (have_previous_volume) {
        for (int channel = 0; channel < 3; channel++) {
          if ((uint8_t)(previous_volume[channel] + 1) == volumes[channel])
            saw_attack_step = 1;
          if ((uint8_t)(volumes[channel] + 1) == previous_volume[channel])
            saw_decay_step = 1;
        }
      }
      memcpy(previous_volume, volumes, sizeof(volumes));
      have_previous_volume = 1;
    }
    if (cpu.pc == map.sample_loop) {
      uint16_t phase[3] = {
        word(f.memory, map.phase[0]), word(f.memory, map.phase[1]),
        word(f.memory, map.phase[2]),
      };
      uint16_t steps[3] = {
        (uint16_t)cpu.b << 8 | cpu.c,
        (uint16_t)cpu.d << 8 | cpu.e,
        cpu.sp,
      };
      uint16_t drum_at = word(f.memory, map.drum_pointer);
      uint8_t drum_value = f.memory[drum_at];
      int tone_will_wrap = 0;
      for (int channel = 0; channel < 3; channel++)
        tone_will_wrap |= (uint32_t)phase[channel] + steps[channel] > 0xffff;
      if (f.memory[map.drum_frames]) {
        drum_active_samples++;
        if (steps[0] && steps[1] && steps[2] && drum_value && tone_will_wrap)
          simultaneous_samples++;
      }
      if (word(f.memory, map.slide_delta)) {
        if (!saw_slide)
          first_slide_step = steps[0];
        last_slide_step = steps[0];
        saw_slide = 1;
      }

      sample_entries++;
      if (frame_entries <= 9) {
        if (!first_sample_cycle)
          first_sample_cycle = cpu.cyc;
        last_first_row_sample_cycle = cpu.cyc;
        first_row_samples++;
        if (have_previous_phase) {
          for (int channel = 0; channel < 3; channel++) {
            if (phase[channel] < previous_phase[channel]) {
              if (!wraps[channel])
                first_wrap[channel] = cpu.cyc;
              last_wrap[channel] = cpu.cyc;
              wraps[channel]++;
            }
          }
        }
      }
      memcpy(previous_phase, phase, sizeof(phase));
      have_previous_phase = 1;
    }
    i8080_step(&cpu);
  }

  if (!cpu.halted || cpu.pc != 1 || cpu.sp != 0x9000 || !cpu.iff) {
    fprintf(stderr,
        "JukuPoly did not return cleanly: halted=%d pc=%04x sp=%04x iff=%d\n",
        cpu.halted, cpu.pc, cpu.sp, cpu.iff);
    return 1;
  }
  if (sample_entries != (size_t)EXPECTED_FRAMES * FRAME_SAMPLES ||
      frame_entries != EXPECTED_FRAMES + 1) {
    fprintf(stderr, "JukuPoly frame count differs: frames=%zu samples=%zu\n",
        frame_entries, sample_entries);
    return 1;
  }
  if (f.output_count < 1000 || f.outputs[0].port != 0x1b ||
      f.outputs[0].value != 0x50 || f.outputs[1].port != 0x19 ||
      f.outputs[1].value != 1 ||
      f.outputs[f.output_count - 2].port != 0x1b ||
      f.outputs[f.output_count - 2].value != 0x50 ||
      f.outputs[f.output_count - 1].port != 0x19 ||
      f.outputs[f.output_count - 1].value != 1) {
    fprintf(stderr, "JukuPoly PIT setup/silence sequence differs\n");
    return 1;
  }
  for (size_t index = 2; index + 2 < f.output_count; index++) {
    output_event *event = &f.outputs[index];
    if (event->port != 0x19 || !event->value || event->value > 0xf0 ||
        event->value & 0x0f) {
      fprintf(stderr, "unexpected JukuPoly pulse %02x:%02x\n",
          event->port, event->value);
      return 1;
    }
  }

  double sample_rate = event_frequency(first_row_samples, first_sample_cycle,
                                        last_first_row_sample_cycle);
  double pitch[3];
  for (int channel = 0; channel < 3; channel++)
    pitch[channel] = event_frequency(
        wraps[channel], first_wrap[channel], last_wrap[channel]);
  double duration = cpu.cyc / EFFECTIVE_HZ;
  if (!near(sample_rate, 7200.0, 1200.0) ||
      !near(pitch[0], 261.63, 25.0) || !near(pitch[1], 196.0, 20.0) ||
      !near(pitch[2], 65.41, 8.0) || !near(duration, 7.5, 1.5)) {
    fprintf(stderr,
        "JukuPoly timing differs: sample=%.2f pitches=%.2f/%.2f/%.2f "
        "duration=%.3f\n",
        sample_rate, pitch[0], pitch[1], pitch[2], duration);
    return 1;
  }
  if (!drum_active_samples || simultaneous_samples < 20 ||
      !saw_attack_step || !saw_decay_step || !saw_slide ||
      first_slide_step == last_slide_step) {
    fprintf(stderr,
        "JukuPoly features missing: drum=%zu simultaneous=%zu attack=%d "
        "decay=%d slide=%d steps=%u/%u\n",
        drum_active_samples, simultaneous_samples, saw_attack_step,
        saw_decay_step, saw_slide, first_slide_step, last_slide_step);
    return 1;
  }

  printf(
      "JUKUPOLY: PASS sample=%.1fHz pitches=%.2f/%.2f/%.2fHz "
      "duration=%.3fs frames=%zu pulses=%zu simultaneous=%zu\n",
      sample_rate, pitch[0], pitch[1], pitch[2], duration,
      frame_entries - 1, f.output_count - 4, simultaneous_samples);
  return 0;
}
