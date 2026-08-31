/* Host-only bridge from a timed JukuPoly OPL stream to Nuked OPL3.
 *
 * Nuked OPL3 is an unmodified LGPL-2.1-or-later submodule.  This bridge is
 * independent project code and is never linked into an 8080 target image.
 */

#include "opl3.h"

#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  uint32_t sample;
  uint16_t register_address;
  uint8_t value;
} timed_write;

static uint16_t read_u16(FILE *input, int *ok) {
  int low = fgetc(input), high = fgetc(input);
  if (low == EOF || high == EOF) {
    *ok = 0;
    return 0;
  }
  return (uint16_t)(low | high << 8);
}

static uint32_t read_u32(FILE *input, int *ok) {
  uint32_t result = 0;
  for (unsigned shift = 0; shift < 32; shift += 8) {
    int value = fgetc(input);
    if (value == EOF) {
      *ok = 0;
      return 0;
    }
    result |= (uint32_t)value << shift;
  }
  return result;
}

static int write_i16le(FILE *output, int16_t value) {
  uint16_t bits = (uint16_t)value;
  return fputc(bits & 0xff, output) != EOF &&
         fputc(bits >> 8, output) != EOF;
}

static timed_write *read_stream(const char *path, uint32_t *total_samples,
                                uint32_t *sample_rate, size_t *write_count) {
  FILE *input = fopen(path, "rb");
  if (!input) {
    perror(path);
    exit(2);
  }
  uint8_t magic[4];
  int ok = fread(magic, 1, sizeof(magic), input) == sizeof(magic);
  *total_samples = read_u32(input, &ok);
  *sample_rate = read_u32(input, &ok);
  uint32_t count = read_u32(input, &ok);
  if (!ok || memcmp(magic, "JOP\1", 4) != 0 || !*total_samples ||
      *sample_rate < 8000 || *sample_rate > 192000 || count > 100000000) {
    fprintf(stderr, "invalid JukuPoly OPL oracle stream header\n");
    exit(2);
  }
  timed_write *writes = calloc(count ? count : 1, sizeof(*writes));
  if (!writes) {
    fprintf(stderr, "cannot allocate OPL write stream\n");
    exit(2);
  }
  uint32_t previous_sample = 0;
  for (uint32_t index = 0; index < count; index++) {
    writes[index].sample = read_u32(input, &ok);
    writes[index].register_address = read_u16(input, &ok);
    int value = fgetc(input), reserved = fgetc(input);
    if (value == EOF || reserved != 0)
      ok = 0;
    writes[index].value = (uint8_t)value;
    if (!ok || writes[index].sample < previous_sample ||
        writes[index].sample >= *total_samples ||
        writes[index].register_address > 0x1ff) {
      fprintf(stderr, "invalid timed OPL write at index %u\n", index);
      exit(2);
    }
    previous_sample = writes[index].sample;
  }
  if (fgetc(input) != EOF) {
    fprintf(stderr, "trailing bytes in OPL oracle stream\n");
    exit(2);
  }
  fclose(input);
  *write_count = count;
  return writes;
}

static void write_probe(FILE *output, const opl3_chip *chip,
                        unsigned channel_number, uint32_t sample) {
  const opl3_channel *channel = &chip->channel[channel_number];
  const opl3_slot *modulator = channel->slotz[0];
  const opl3_slot *carrier = channel->slotz[1];
  fprintf(output,
      "%" PRIu32 ",%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u,%u\n",
      sample, channel->f_num, channel->block,
      (unsigned)(modulator->key != 0 || carrier->key != 0),
      modulator->eg_rout, carrier->eg_rout,
      modulator->eg_out, carrier->eg_out, channel->con,
      modulator->eg_gen, carrier->eg_gen,
      chip->vibpos, chip->tremolopos, chip->tremolo);
}

int main(int argc, char **argv) {
  if (argc != 5) {
    fprintf(stderr,
        "usage: %s STREAM.jop OUTPUT.s16le PROBES.csv CHANNEL\n", argv[0]);
    return 2;
  }
  char *end = NULL;
  errno = 0;
  unsigned long channel_number = strtoul(argv[4], &end, 10);
  if (errno || !*argv[4] || *end || channel_number > 17) {
    fprintf(stderr, "invalid OPL channel: %s\n", argv[4]);
    return 2;
  }

  uint32_t total_samples, sample_rate;
  size_t write_count;
  timed_write *writes = read_stream(
      argv[1], &total_samples, &sample_rate, &write_count);
  FILE *pcm = fopen(argv[2], "wb");
  FILE *probes = fopen(argv[3], "w");
  if (!pcm || !probes) {
    perror(!pcm ? argv[2] : argv[3]);
    return 2;
  }
  fputs("sample,f_number,block,key,modulator_attenuation,"
        "carrier_attenuation,modulator_output_attenuation,"
        "carrier_output_attenuation,connection,"
        "modulator_stage,carrier_stage,"
        "vibrato_phase,tremolo_phase,tremolo_value\n", probes);

  opl3_chip chip;
  OPL3_Reset(&chip, sample_rate);
  uint32_t probe_step = sample_rate / 50;
  if (!probe_step)
    probe_step = 1;
  size_t write_at = 0;
  uint32_t first_nonzero = total_samples, last_nonzero = 0;
  unsigned peak = 0;
  size_t nonzero = 0;

  for (uint32_t sample = 0; sample <= total_samples; sample++) {
    while (write_at < write_count && writes[write_at].sample == sample) {
      OPL3_WriteReg(&chip, writes[write_at].register_address,
                    writes[write_at].value);
      write_at++;
    }
    if (sample % probe_step == 0 || sample == total_samples)
      write_probe(probes, &chip, (unsigned)channel_number, sample);
    if (sample == total_samples)
      break;

    int16_t output[2];
    OPL3_GenerateResampled(&chip, output);
    if (!write_i16le(pcm, output[0]) || !write_i16le(pcm, output[1])) {
      fprintf(stderr, "cannot write oracle PCM\n");
      return 2;
    }
    unsigned left = output[0] < 0 ? (unsigned)-(int)output[0]
                                   : (unsigned)output[0];
    unsigned right = output[1] < 0 ? (unsigned)-(int)output[1]
                                    : (unsigned)output[1];
    unsigned amplitude = left > right ? left : right;
    if (amplitude) {
      if (!nonzero)
        first_nonzero = sample;
      last_nonzero = sample;
      nonzero++;
      if (amplitude > peak)
        peak = amplitude;
    }
  }

  if (write_at != write_count || fclose(pcm) || fclose(probes)) {
    fprintf(stderr, "oracle stream did not finish cleanly\n");
    return 2;
  }
  printf("JUKUPOLY-OPL-ORACLE: PASS samples=%" PRIu32
         " writes=%zu nonzero=%zu first=%" PRIu32 " last=%" PRIu32
         " peak=%u channel=%lu\n",
      total_samples, write_count, nonzero, first_nonzero, last_nonzero,
      peak, channel_number);
  free(writes);
  return 0;
}
