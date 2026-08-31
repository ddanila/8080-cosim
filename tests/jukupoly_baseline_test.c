#include "../cosim/i8080.h"

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define COM_ADDRESS 0x0100
#define SONG_ADDRESS 0x1800
#define STACK_RETURN 0x9bfe
#define EFFECTIVE_HZ 1700000.0
#define MAX_INSTRUCTIONS 500000000UL

typedef struct {
  uint64_t *values;
  size_t count, capacity;
  uint64_t total, minimum, maximum;
} statistics;

typedef struct {
  uint8_t memory[65536];
  uint8_t mutated[SONG_ADDRESS - COM_ADDRESS];
  size_t com_size;
  size_t pit_writes, keyboard_polls;
  uint8_t keyboard_column;
  int invalid_port;
} fixture;

typedef struct {
  uint16_t sample_loop, frame_tick, row_frames;
} manifest;

static uint8_t read_byte(void *opaque, uint16_t address) {
  return ((fixture *)opaque)->memory[address];
}

static void write_byte(void *opaque, uint16_t address, uint8_t value) {
  fixture *f = opaque;
  f->memory[address] = value;
  if (address >= COM_ADDRESS && address < COM_ADDRESS + f->com_size)
    f->mutated[address - COM_ADDRESS] = 1;
}

static uint8_t port_in(void *opaque, uint8_t port) {
  fixture *f = opaque;
  if (port != 0x05 || f->keyboard_column != 3) {
    f->invalid_port = 1;
    return 0xff;
  }
  f->keyboard_polls++;
  return 0xff;
}

static void port_out(void *opaque, uint8_t port, uint8_t value) {
  fixture *f = opaque;
  if (port == 0x04) {
    f->keyboard_column = value;
    return;
  }
  if (port != 0x19 && port != 0x1b) {
    f->invalid_port = 1;
    return;
  }
  f->pit_writes++;
}

static uint16_t word(const uint8_t *memory, uint16_t address) {
  return memory[address] | (uint16_t)memory[(uint16_t)(address + 1)] << 8;
}

static int locate_manifest(const fixture *f, manifest *result) {
  static const uint8_t magic[] = {'J', 'P', 'O', 'L', 1};
  for (uint16_t address = COM_ADDRESS;
       address + sizeof(magic) + 26 <= COM_ADDRESS + f->com_size; address++) {
    if (memcmp(&f->memory[address], magic, sizeof(magic)) != 0)
      continue;
    uint16_t at = (uint16_t)(address + sizeof(magic));
    result->sample_loop = word(f->memory, at); at += 2;
    result->frame_tick = word(f->memory, at); at += 2;
    at += 8;  /* three phase immediates and the drum pointer */
    at += 2;  /* drum frame counter */
    at += 6;  /* three channel volumes */
    at += 2;  /* slide delta */
    result->row_frames = word(f->memory, at);
    return 1;
  }
  return 0;
}

static uint8_t *read_file(const char *path, size_t *size) {
  FILE *input = fopen(path, "rb");
  if (!input) {
    perror(path);
    exit(2);
  }
  if (fseek(input, 0, SEEK_END) || ftell(input) <= 0) {
    fprintf(stderr, "cannot size %s\n", path);
    exit(2);
  }
  long length = ftell(input);
  if (fseek(input, 0, SEEK_SET)) {
    fprintf(stderr, "cannot rewind %s\n", path);
    exit(2);
  }
  *size = (size_t)length;
  uint8_t *data = malloc(*size);
  if (!data || fread(data, 1, *size, input) != *size) {
    fprintf(stderr, "cannot read %s\n", path);
    exit(2);
  }
  fclose(input);
  return data;
}

static void add_statistic(statistics *stats, uint64_t value) {
  if (stats->count == stats->capacity) {
    size_t capacity = stats->capacity ? stats->capacity * 2 : 1024;
    uint64_t *values = realloc(stats->values, capacity * sizeof(*values));
    if (!values) {
      fprintf(stderr, "profile allocation failed\n");
      exit(1);
    }
    stats->values = values;
    stats->capacity = capacity;
  }
  stats->values[stats->count++] = value;
  stats->total += value;
  if (stats->count == 1 || value < stats->minimum)
    stats->minimum = value;
  if (stats->count == 1 || value > stats->maximum)
    stats->maximum = value;
}

static int compare_u64(const void *left, const void *right) {
  uint64_t a = *(const uint64_t *)left;
  uint64_t b = *(const uint64_t *)right;
  return (a > b) - (a < b);
}

static uint64_t percentile99(statistics *stats) {
  if (!stats->count)
    return 0;
  qsort(stats->values, stats->count, sizeof(*stats->values), compare_u64);
  size_t rank = (99 * stats->count + 99) / 100;
  if (!rank)
    rank = 1;
  return stats->values[rank - 1];
}

static void print_statistics(const char *name, statistics *stats) {
  double mean = stats->count ? (double)stats->total / stats->count : 0.0;
  printf("\"%s\":{\"count\":%zu,\"min\":%" PRIu64
         ",\"mean\":%.3f,\"p99\":%" PRIu64 ",\"max\":%" PRIu64 "}",
      name, stats->count, stats->minimum, mean, percentile99(stats),
      stats->maximum);
}

static void free_statistics(statistics *stats) {
  free(stats->values);
  stats->values = NULL;
}

int main(int argc, char **argv) {
  if (argc != 5 && argc != 6) {
    fprintf(stderr,
        "usage: %s JUKEBOX.COM SONG.JPS PLAYER-START-HEX LABEL "
        "[PREPARE-HEX]\n", argv[0]);
    return 2;
  }

  char *end = NULL;
  unsigned long entry = strtoul(argv[3], &end, 16);
  if (!*argv[3] || *end || entry < COM_ADDRESS || entry >= SONG_ADDRESS) {
    fprintf(stderr, "invalid player entry address: %s\n", argv[3]);
    return 2;
  }
  unsigned long prepare = 0;
  if (argc == 6) {
    end = NULL;
    prepare = strtoul(argv[5], &end, 16);
    if (!*argv[5] || *end || prepare < COM_ADDRESS || prepare >= SONG_ADDRESS) {
      fprintf(stderr, "invalid player prepare address: %s\n", argv[5]);
      return 2;
    }
  }

  fixture f = {0};
  size_t song_size;
  uint8_t *com = read_file(argv[1], &f.com_size);
  uint8_t *song = read_file(argv[2], &song_size);
  if (f.com_size >= SONG_ADDRESS - COM_ADDRESS || song_size >= 0x8000 ||
      song_size < 16 || memcmp(song, "JPS", 3) != 0 ||
      (song[3] != 1 && song[3] != 2) ||
      word(song, 4) != song_size) {
    fprintf(stderr, "invalid player or JPS fixture size\n");
    return 2;
  }
  memcpy(&f.memory[COM_ADDRESS], com, f.com_size);
  memcpy(&f.memory[SONG_ADDRESS], song, song_size);
  free(com);
  free(song);

  manifest map;
  if (!locate_manifest(&f, &map)) {
    fprintf(stderr, "JukuPoly test manifest not found\n");
    return 2;
  }

  f.memory[0] = 0x76;
  f.memory[STACK_RETURN] = 0;
  f.memory[STACK_RETURN + 1] = 0;
  if (prepare) {
    f.memory[STACK_RETURN - 2] = (uint8_t)entry;
    f.memory[STACK_RETURN - 1] = (uint8_t)(entry >> 8);
  }

  i8080 cpu;
  i8080_init(&cpu);
  cpu.read_byte = read_byte;
  cpu.write_byte = write_byte;
  cpu.port_in = port_in;
  cpu.port_out = port_out;
  cpu.userdata = &f;
  cpu.pc = (uint16_t)(prepare ? prepare : entry);
  cpu.sp = (uint16_t)(prepare ? STACK_RETURN - 2 : STACK_RETURN);
  cpu.iff = 1;

  statistics frame = {0}, sample_loop = {0};
  statistics idle_boundary = {0}, row_boundary = {0};
  unsigned long last_frame_cycle = 0, last_sample_cycle = 0;
  unsigned long pending_boundary_cycle = 0;
  size_t frame_entries = 0, sample_entries = 0;
  int have_frame = 0, have_sample = 0, crossed_frame = 0;
  int pending_boundary = 0, pending_row = 0;

  unsigned long instructions;
  for (instructions = 0;
       !cpu.halted && instructions < MAX_INSTRUCTIONS; instructions++) {
    if (cpu.pc == map.frame_tick) {
      if (have_frame)
        add_statistic(&frame, cpu.cyc - last_frame_cycle);
      last_frame_cycle = cpu.cyc;
      have_frame = 1;
      frame_entries++;
      crossed_frame = 1;
      pending_boundary = 1;
      pending_boundary_cycle = cpu.cyc;
      pending_row = f.memory[map.row_frames] == 0;
    }

    if (cpu.pc == map.sample_loop) {
      if (pending_boundary) {
        statistics *target = pending_row ? &row_boundary : &idle_boundary;
        add_statistic(target, cpu.cyc - pending_boundary_cycle);
        pending_boundary = 0;
      }
      if (have_sample && !crossed_frame)
        add_statistic(&sample_loop, cpu.cyc - last_sample_cycle);
      last_sample_cycle = cpu.cyc;
      have_sample = 1;
      crossed_frame = 0;
      sample_entries++;
    }

    i8080_step(&cpu);
  }

  uint8_t frame_samples = f.memory[SONG_ADDRESS + 6];
  if (!cpu.halted || cpu.pc != 1 || cpu.sp != STACK_RETURN + 2 || !cpu.iff ||
      f.invalid_port || !frame.count || frame_entries != frame.count + 1 ||
      sample_entries != frame.count * frame_samples ||
      !sample_loop.count || !row_boundary.count) {
    fprintf(stderr,
        "baseline run failed: halted=%d pc=%04x sp=%04x iff=%d invalid=%d "
        "frames=%zu/%zu samples=%zu frame-samples=%u loops=%zu rows=%zu\n",
        cpu.halted, cpu.pc, cpu.sp, cpu.iff, f.invalid_port, frame_entries,
        frame.count, sample_entries, frame_samples, sample_loop.count,
        row_boundary.count);
    return 1;
  }

  size_t mutated = 0;
  for (size_t index = 0; index < f.com_size; index++)
    mutated += f.mutated[index] != 0;

  double seconds = frame.total / EFFECTIVE_HZ;
  double music_hz = frame.count * EFFECTIVE_HZ / frame.total;
  double sample_hz = sample_entries * EFFECTIVE_HZ / frame.total;
  printf("{\"label\":\"%s\",\"com_bytes\":%zu,\"jps_bytes\":%zu,"
         "\"frames\":%zu,\"frame_samples\":%u,\"duration_seconds\":%.6f,"
         "\"music_frame_hz\":%.6f,\"effective_sample_hz\":%.6f,"
         "\"pit_writes\":%zu,\"keyboard_polls\":%zu,"
         "\"mutated_player_bytes\":%zu,",
      argv[4], f.com_size, song_size, frame.count, frame_samples, seconds,
      music_hz, sample_hz, f.pit_writes, f.keyboard_polls, mutated);
  print_statistics("sample_loop_cycles", &sample_loop);
  putchar(',');
  print_statistics("frame_cycles", &frame);
  putchar(',');
  print_statistics("idle_boundary_cycles", &idle_boundary);
  putchar(',');
  print_statistics("row_boundary_cycles", &row_boundary);
  puts("}");

  free_statistics(&frame);
  free_statistics(&sample_loop);
  free_statistics(&idle_boundary);
  free_statistics(&row_boundary);
  return 0;
}
