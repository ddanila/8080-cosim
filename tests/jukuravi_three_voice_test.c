#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LOAD_ADDRESS 0x0100
#define SAMPLE_LOOP  0x0123
#define EFFECTIVE_HZ 1700000.0
#define MAX_EVENTS   8192

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
  unsigned long loop_first_cycle;
  unsigned long loop_last_cycle;
  unsigned long loop_count;
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
  fixture *f = (fixture *)opaque;
  if (f->output_count >= MAX_EVENTS) {
    fprintf(stderr, "three-voice output event buffer overflow\n");
    exit(1);
  }
  f->outputs[f->output_count++] = (output_event){port, value, f->cpu->cyc};
}

static double seconds_between(unsigned long first, unsigned long second) {
  return (second - first) / EFFECTIVE_HZ;
}

static double bit_frequency(const fixture *f, uint8_t bit,
    unsigned long after, unsigned long before) {
  unsigned long first = 0, last = 0;
  size_t count = 0;
  for (size_t i = 0; i < f->output_count; i++) {
    const output_event *event = &f->outputs[i];
    if (event->port != 0x19 || event->value == 1 ||
        !(event->value & bit) || event->cycle < after ||
        event->cycle >= before)
      continue;
    if (!count)
      first = event->cycle;
    last = event->cycle;
    count++;
  }
  if (count < 2 || last == first)
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
  unsigned long first_pulse = 0, voice2_at = 0, voice3_at = 0, finished_at = 0;

  if (argc != 2) {
    fprintf(stderr, "usage: %s three-voice.com\n", argv[0]);
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
  if (size == 0 || size > 1024) {
    fprintf(stderr, "unexpected three-voice image size: %zu\n", size);
    return 2;
  }

  f.memory[0] = 0x76;       /* HLT after the CP/M-style RET. */
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

  for (unsigned long steps = 0; !cpu.halted && steps < 5000000; steps++) {
    if (cpu.pc == SAMPLE_LOOP) {
      if (!f.loop_count)
        f.loop_first_cycle = cpu.cyc;
      f.loop_last_cycle = cpu.cyc;
      f.loop_count++;
    }
    i8080_step(&cpu);
  }

  if (!cpu.halted || cpu.pc != 1 || cpu.sp != 0x9000 || !cpu.iff) {
    fprintf(stderr,
        "three-voice transient did not return cleanly: halted=%d pc=%04x "
        "sp=%04x iff=%d\n", cpu.halted, cpu.pc, cpu.sp, cpu.iff);
    return 1;
  }
  if (f.output_count < 1000 || f.outputs[0].port != 0x1b ||
      f.outputs[0].value != 0x50 || f.outputs[1].port != 0x19 ||
      f.outputs[1].value != 1 ||
      f.outputs[f.output_count - 2].port != 0x1b ||
      f.outputs[f.output_count - 2].value != 0x50 ||
      f.outputs[f.output_count - 1].port != 0x19 ||
      f.outputs[f.output_count - 1].value != 1) {
    fprintf(stderr, "three-voice PIT setup/silence sequence differs\n");
    return 1;
  }

  for (size_t i = 2; i + 2 < f.output_count; i++) {
    output_event *event = &f.outputs[i];
    if (event->port != 0x19 || (event->value & 0xc0) != 0xc0 ||
        !(event->value & 0x38) || (event->value & 0x07)) {
      fprintf(stderr, "unexpected hot-loop output %02x:%02x\n",
          event->port, event->value);
      return 1;
    }
    if (!first_pulse)
      first_pulse = event->cycle;
    if (!voice2_at && (event->value & 0x10))
      voice2_at = event->cycle;
    if (!voice3_at && (event->value & 0x08))
      voice3_at = event->cycle;
  }
  finished_at = f.outputs[f.output_count - 1].cycle;
  if (!first_pulse || !voice2_at || !voice3_at ||
      !near(seconds_between(first_pulse, voice2_at), 2.0, 0.08) ||
      !near(seconds_between(first_pulse, voice3_at), 4.0, 0.10) ||
      !near(seconds_between(first_pulse, finished_at), 9.0, 0.15)) {
    fprintf(stderr, "voice entrances differ: second=%.6f third=%.6f end=%.6f\n",
        seconds_between(first_pulse, voice2_at),
        seconds_between(first_pulse, voice3_at),
        seconds_between(first_pulse, finished_at));
    return 1;
  }

  double sample_rate = EFFECTIVE_HZ * (f.loop_count - 1) /
      (f.loop_last_cycle - f.loop_first_cycle);
  double a3 = bit_frequency(&f, 0x20, first_pulse, voice2_at);
  double cs4 = bit_frequency(&f, 0x10, voice2_at, voice3_at);
  double e4 = bit_frequency(&f, 0x08, voice3_at, finished_at);
  if (!near(sample_rate, 10500.0, 1000.0) ||
      !near(a3, 220.0, 5.0) || !near(cs4, 277.18, 7.0) ||
      !near(e4, 329.63, 8.0)) {
    fprintf(stderr,
        "three-voice rates differ: sample=%.2f A3=%.2f C#4=%.2f E4=%.2f\n",
        sample_rate, a3, cs4, e4);
    return 1;
  }

  printf("JUKURAVI-THREE-VOICE: PASS sample=%.1fHz A3=%.2fHz "
      "C#4=%.2fHz E4=%.2fHz entrances=%.3f/%.3f/%.3fs outputs=%zu\n",
      sample_rate, a3, cs4, e4,
      seconds_between(first_pulse, voice2_at),
      seconds_between(first_pulse, voice3_at),
      seconds_between(first_pulse, finished_at), f.output_count);
  return 0;
}
