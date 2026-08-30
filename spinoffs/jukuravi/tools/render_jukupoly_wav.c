#include "../../../cosim/i8080.h"

#include <errno.h>
#include <limits.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define LOAD_ADDRESS 0x0100
#define STACK_RETURN 0x9bfe

typedef struct {
  double start;
  double end;
} pulse_interval;

typedef struct {
  uint8_t memory[65536];
  i8080 cpu;
  double cpu_hz;
  double pit_hz;
  pulse_interval *pulses;
  size_t pulse_count;
  size_t pulse_capacity;
  size_t pit_writes;
  int mode0_lsb;
  int pending_control;
  double pending_control_time;
  int allocation_failed;
} fixture;

typedef struct {
  double cpu_hz;
  double pit_hz;
  double gain;
  double lead_seconds;
  double tail_seconds;
  double dc_block_hz;
  double max_seconds;
  unsigned sample_rate;
  const char *input_path;
  const char *output_path;
} options;

static void usage(FILE *stream, const char *program) {
  fprintf(stream,
      "usage: %s [options] input.com output.wav\n"
      "\n"
      "Render Juku D57 channel-1 Mode-0 pulses emitted by a self-contained\n"
      "CP/M transient executed in the cycle-level 8080 model.\n"
      "\n"
      "options:\n"
      "  --cpu-hz HZ       effective CPU rate (default 1700000)\n"
      "  --pit-hz HZ       D57 channel-1 rate (default 2000000)\n"
      "  --sample-rate HZ  output PCM rate (default 96000)\n"
      "  --gain VALUE      linear output gain, 0..1 (default 0.95)\n"
      "  --lead SECONDS    silence before execution (default 0.25)\n"
      "  --tail SECONDS    silence after execution (default 0.25)\n"
      "  --dc-block HZ     first-order acoustic DC blocker; 0 disables\n"
      "                    it (default 20)\n"
      "  --max-seconds N   abort a non-returning transient (default 300)\n"
      "  --help            show this help\n",
      program);
}

static int parse_double(const char *text, double minimum, double maximum,
                        double *result) {
  char *end = NULL;
  errno = 0;
  double value = strtod(text, &end);
  if (errno || end == text || *end || !isfinite(value) ||
      value < minimum || value > maximum)
    return 0;
  *result = value;
  return 1;
}

static int parse_unsigned(const char *text, unsigned minimum,
                          unsigned maximum, unsigned *result) {
  char *end = NULL;
  errno = 0;
  unsigned long value = strtoul(text, &end, 10);
  if (errno || end == text || *end || value < minimum || value > maximum)
    return 0;
  *result = (unsigned)value;
  return 1;
}

static int parse_options(int argc, char **argv, options *result) {
  *result = (options){
      .cpu_hz = 1700000.0,
      .pit_hz = 2000000.0,
      .gain = 0.95,
      .lead_seconds = 0.25,
      .tail_seconds = 0.25,
      .dc_block_hz = 20.0,
      .max_seconds = 300.0,
      .sample_rate = 96000,
  };

  int positional = 0;
  for (int index = 1; index < argc; index++) {
    const char *arg = argv[index];
    if (!strcmp(arg, "--help")) {
      usage(stdout, argv[0]);
      exit(0);
    }
    if (!strncmp(arg, "--", 2)) {
      if (index + 1 >= argc) {
        fprintf(stderr, "%s requires a value\n", arg);
        return 0;
      }
      const char *value = argv[++index];
      if (!strcmp(arg, "--cpu-hz")) {
        if (!parse_double(value, 1.0, 1000000000.0, &result->cpu_hz))
          goto invalid_value;
      } else if (!strcmp(arg, "--pit-hz")) {
        if (!parse_double(value, 1.0, 1000000000.0, &result->pit_hz))
          goto invalid_value;
      } else if (!strcmp(arg, "--sample-rate")) {
        if (!parse_unsigned(value, 8000, 768000, &result->sample_rate))
          goto invalid_value;
      } else if (!strcmp(arg, "--gain")) {
        if (!parse_double(value, 0.0, 1.0, &result->gain))
          goto invalid_value;
      } else if (!strcmp(arg, "--lead")) {
        if (!parse_double(value, 0.0, 60.0, &result->lead_seconds))
          goto invalid_value;
      } else if (!strcmp(arg, "--tail")) {
        if (!parse_double(value, 0.0, 60.0, &result->tail_seconds))
          goto invalid_value;
      } else if (!strcmp(arg, "--dc-block")) {
        if (!parse_double(value, 0.0, 1000.0, &result->dc_block_hz))
          goto invalid_value;
      } else if (!strcmp(arg, "--max-seconds")) {
        if (!parse_double(value, 0.01, 86400.0, &result->max_seconds))
          goto invalid_value;
      } else {
        fprintf(stderr, "unknown option: %s\n", arg);
        return 0;
      }
      continue;

invalid_value:
      fprintf(stderr, "invalid value for %s: %s\n", arg, value);
      return 0;
    }

    if (positional == 0)
      result->input_path = arg;
    else if (positional == 1)
      result->output_path = arg;
    else {
      fprintf(stderr, "unexpected argument: %s\n", arg);
      return 0;
    }
    positional++;
  }

  if (positional != 2) {
    usage(stderr, argv[0]);
    return 0;
  }
  if (result->dc_block_hz >= result->sample_rate / 2.0) {
    fprintf(stderr, "DC blocker must be below the output Nyquist frequency\n");
    return 0;
  }
  return 1;
}

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

static void append_pulse(fixture *f, double start, double end) {
  if (end <= start || f->allocation_failed)
    return;

  if (f->pulse_count && start <= f->pulses[f->pulse_count - 1].end) {
    if (end > f->pulses[f->pulse_count - 1].end)
      f->pulses[f->pulse_count - 1].end = end;
    return;
  }

  if (f->pulse_count == f->pulse_capacity) {
    size_t capacity = f->pulse_capacity ? f->pulse_capacity * 2 : 4096;
    if (capacity < f->pulse_capacity ||
        capacity > SIZE_MAX / sizeof(*f->pulses)) {
      f->allocation_failed = 1;
      return;
    }
    pulse_interval *grown = realloc(f->pulses, capacity * sizeof(*f->pulses));
    if (!grown) {
      f->allocation_failed = 1;
      return;
    }
    f->pulses = grown;
    f->pulse_capacity = capacity;
  }
  f->pulses[f->pulse_count++] = (pulse_interval){start, end};
}

static void port_out(void *opaque, uint8_t port, uint8_t value) {
  fixture *f = opaque;
  double now = f->cpu.cyc / f->cpu_hz;

  if (port == 0x1b) {
    /* D57 channel 1, LSB-only, binary Mode 0. The control write takes OUT1
       low; the following count write supplies its terminal-count time. */
    f->mode0_lsb = value == 0x50;
    f->pending_control = f->mode0_lsb;
    f->pending_control_time = now;
    f->pit_writes++;
    return;
  }
  if (port != 0x19 || !f->mode0_lsb)
    return;

  unsigned count = value ? value : 256;
  double start = f->pending_control ? f->pending_control_time : now;
  append_pulse(f, start, now + count / f->pit_hz);
  f->pending_control = 0;
  f->pit_writes++;
}

static int load_and_run(fixture *f, const options *opts, double *run_seconds) {
  FILE *input = fopen(opts->input_path, "rb");
  if (!input) {
    perror(opts->input_path);
    return 0;
  }
  size_t maximum = STACK_RETURN - LOAD_ADDRESS;
  size_t size = fread(&f->memory[LOAD_ADDRESS], 1, maximum + 1, input);
  int read_error = ferror(input);
  fclose(input);
  if (read_error) {
    fprintf(stderr, "failed to read %s\n", opts->input_path);
    return 0;
  }
  if (!size || size > maximum) {
    fprintf(stderr, "CP/M transient must contain 1..%zu bytes\n", maximum);
    return 0;
  }

  f->memory[0] = 0x76; /* HLT after the CP/M-style RET to address zero. */
  f->memory[STACK_RETURN] = 0;
  f->memory[STACK_RETURN + 1] = 0;
  f->cpu_hz = opts->cpu_hz;
  f->pit_hz = opts->pit_hz;

  i8080_init(&f->cpu);
  f->cpu.read_byte = read_byte;
  f->cpu.write_byte = write_byte;
  f->cpu.port_in = port_in;
  f->cpu.port_out = port_out;
  f->cpu.userdata = f;
  f->cpu.pc = LOAD_ADDRESS;
  f->cpu.sp = STACK_RETURN;
  f->cpu.iff = 1;

  double maximum_cycles = opts->max_seconds * opts->cpu_hz;
  while (!f->cpu.halted && f->cpu.cyc < maximum_cycles &&
         !f->allocation_failed)
    i8080_step(&f->cpu);

  if (f->allocation_failed) {
    fprintf(stderr, "out of memory while collecting pulse intervals\n");
    return 0;
  }
  if (!f->cpu.halted || f->cpu.pc != 1) {
    fprintf(stderr,
        "transient did not return within %.3f s: halted=%d pc=%04x cycles=%lu\n",
        opts->max_seconds, f->cpu.halted, f->cpu.pc, f->cpu.cyc);
    return 0;
  }
  if (!f->pulse_count || f->pit_writes < 2) {
    fprintf(stderr, "transient emitted no D57 channel-1 Mode-0 pulses\n");
    return 0;
  }
  *run_seconds = f->cpu.cyc / opts->cpu_hz;
  return 1;
}

static int write_u16le(FILE *output, uint16_t value) {
  uint8_t bytes[2] = {(uint8_t)value, (uint8_t)(value >> 8)};
  return fwrite(bytes, 1, sizeof(bytes), output) == sizeof(bytes);
}

static int write_u32le(FILE *output, uint32_t value) {
  uint8_t bytes[4] = {
      (uint8_t)value,
      (uint8_t)(value >> 8),
      (uint8_t)(value >> 16),
      (uint8_t)(value >> 24),
  };
  return fwrite(bytes, 1, sizeof(bytes), output) == sizeof(bytes);
}

static int write_wav_header(FILE *output, unsigned sample_rate,
                            uint32_t frames) {
  uint32_t data_bytes = frames * 2;
  return fwrite("RIFF", 1, 4, output) == 4 &&
      write_u32le(output, 36 + data_bytes) &&
      fwrite("WAVEfmt ", 1, 8, output) == 8 &&
      write_u32le(output, 16) &&
      write_u16le(output, 1) &&
      write_u16le(output, 1) &&
      write_u32le(output, sample_rate) &&
      write_u32le(output, sample_rate * 2) &&
      write_u16le(output, 2) &&
      write_u16le(output, 16) &&
      fwrite("data", 1, 4, output) == 4 &&
      write_u32le(output, data_bytes);
}

static int render_wav(const fixture *f, const options *opts,
                      double run_seconds, double *duration_result,
                      double *peak_result) {
  double duration = opts->lead_seconds + run_seconds + opts->tail_seconds;
  double last_pulse = opts->lead_seconds + f->pulses[f->pulse_count - 1].end;
  if (duration < last_pulse + opts->tail_seconds)
    duration = last_pulse + opts->tail_seconds;
  double frame_count_f = ceil(duration * opts->sample_rate);
  if (frame_count_f > (UINT32_MAX - 36U) / 2U) {
    fprintf(stderr, "WAV would exceed the classic RIFF size limit\n");
    return 0;
  }
  uint32_t frames = (uint32_t)frame_count_f;

  FILE *output = fopen(opts->output_path, "wb");
  if (!output) {
    perror(opts->output_path);
    return 0;
  }
  if (!write_wav_header(output, opts->sample_rate, frames)) {
    fprintf(stderr, "failed to write WAV header to %s\n", opts->output_path);
    fclose(output);
    return 0;
  }

  const double sample_period = 1.0 / opts->sample_rate;
  const double dc_coefficient = opts->dc_block_hz > 0.0
      ? exp(-2.0 * 3.14159265358979323846 * opts->dc_block_hz /
            opts->sample_rate)
      : 0.0;
  double previous_input = 0.0;
  double previous_output = 0.0;
  double peak = 0.0;
  size_t pulse_index = 0;
  int16_t block[4096];
  size_t block_count = 0;

  for (uint32_t frame = 0; frame < frames; frame++) {
    double sample_start = frame * sample_period - opts->lead_seconds;
    double sample_end = sample_start + sample_period;
    while (pulse_index < f->pulse_count &&
           f->pulses[pulse_index].end <= sample_start)
      pulse_index++;

    double active = 0.0;
    for (size_t at = pulse_index;
         at < f->pulse_count && f->pulses[at].start < sample_end; at++) {
      double overlap_start = f->pulses[at].start > sample_start
          ? f->pulses[at].start : sample_start;
      double overlap_end = f->pulses[at].end < sample_end
          ? f->pulses[at].end : sample_end;
      if (overlap_end > overlap_start)
        active += overlap_end - overlap_start;
    }
    double input = active / sample_period;
    if (input > 1.0)
      input = 1.0;
    double sample = opts->dc_block_hz > 0.0
        ? input - previous_input + dc_coefficient * previous_output
        : input;
    previous_input = input;
    previous_output = sample;
    sample *= opts->gain;
    if (fabs(sample) > peak)
      peak = fabs(sample);
    if (sample > 1.0)
      sample = 1.0;
    else if (sample < -1.0)
      sample = -1.0;
    long pcm = lround(sample * 32767.0);
    block[block_count++] = (int16_t)pcm;

    if (block_count == sizeof(block) / sizeof(block[0]) || frame + 1 == frames) {
      for (size_t index = 0; index < block_count; index++) {
        if (!write_u16le(output, (uint16_t)block[index])) {
          fprintf(stderr, "failed while writing %s\n", opts->output_path);
          fclose(output);
          return 0;
        }
      }
      block_count = 0;
    }
  }

  if (fclose(output)) {
    perror(opts->output_path);
    return 0;
  }
  *duration_result = frames / (double)opts->sample_rate;
  *peak_result = peak;
  return 1;
}

int main(int argc, char **argv) {
  options opts;
  if (!parse_options(argc, argv, &opts))
    return 2;

  fixture f = {0};
  double run_seconds;
  if (!load_and_run(&f, &opts, &run_seconds)) {
    free(f.pulses);
    return 1;
  }

  double wav_seconds, peak;
  if (!render_wav(&f, &opts, run_seconds, &wav_seconds, &peak)) {
    free(f.pulses);
    return 1;
  }

  printf("JUKUPOLY-WAV: PASS run=%.3fs wav=%.3fs cpu=%.0fHz pit=%.0fHz "
         "rate=%uHz writes=%zu intervals=%zu peak=%.3f output=%s\n",
      run_seconds, wav_seconds, opts.cpu_hz, opts.pit_hz, opts.sample_rate,
      f.pit_writes, f.pulse_count, peak, opts.output_path);
  free(f.pulses);
  return 0;
}
