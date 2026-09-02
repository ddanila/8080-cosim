#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define COM_ADDRESS 0x0100
#define STACK_RETURN 0x9bfe
#define MAX_FRAMES 64
#define MAX_INSTRUCTIONS 5000000UL

typedef struct {
  uint8_t memory[65536];
  size_t pit_writes;
  int invalid_port;
} fixture;

typedef struct {
  uint16_t sample_loop, frame_tick, volume, volume2, volume3;
  uint16_t target, mask, step, sustain;
  uint16_t decay_mask, release_mask, stage, flags;
  uint16_t step2, stage2, step3, stage3;
} manifest;

static uint8_t read_byte(void *opaque, uint16_t address) {
  return ((fixture *)opaque)->memory[address];
}

static void write_byte(void *opaque, uint16_t address, uint8_t value) {
  /* Mode-1 Juku maps the high BIOS ROM at D800h-FFFFh.  Keep that overlay
   * write-protected so a standalone player cannot accidentally use wrapped
   * SP=0000h as a call stack; the flat-RAM fixture previously hid that bug. */
  if (address >= 0xd800)
    return;
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
  static const uint8_t magic[] = {'J', 'P', 'O', 'L', 1};
  for (uint16_t address = COM_ADDRESS;
       address + sizeof(magic) + 50 <= COM_ADDRESS + size; address++) {
    if (memcmp(&f->memory[address], magic, sizeof(magic)) != 0)
      continue;
    uint16_t at = (uint16_t)(address + sizeof(magic));
    map->sample_loop = word(f->memory, at); at += 2;
    map->frame_tick = word(f->memory, at); at += 2;
    at += 10;  /* three phase immediates plus drum pointer/counter */
    map->volume = word(f->memory, at); at += 2;
    map->volume2 = word(f->memory, at); at += 2;
    map->volume3 = word(f->memory, at); at += 2;
    at += 6;   /* slide, row_frames, song rows */
    map->target = word(f->memory, at); at += 2;
    map->mask = word(f->memory, at); at += 2;
    map->step = word(f->memory, at); at += 2;
    map->sustain = word(f->memory, at); at += 2;
    map->decay_mask = word(f->memory, at); at += 2;
    map->release_mask = word(f->memory, at); at += 2;
    map->stage = word(f->memory, at); at += 2;
    map->flags = word(f->memory, at); at += 2;
    map->step2 = word(f->memory, at); at += 2;
    map->stage2 = word(f->memory, at); at += 2;
    map->step3 = word(f->memory, at); at += 2;
    map->stage3 = word(f->memory, at);
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

int main(int argc, char **argv) {
  if (argc != 2) {
    fprintf(stderr, "usage: %s ENVELOPE.COM\n", argv[0]);
    return 2;
  }
  fixture f = {0};
  size_t image_size = load(argv[1], &f.memory[COM_ADDRESS]);
  manifest map;
  if (!locate_manifest(&f, image_size, &map)) {
    fprintf(stderr, "enhanced manifest not found\n");
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

  uint8_t volumes[MAX_FRAMES], stages[MAX_FRAMES];
  uint8_t volumes2[MAX_FRAMES], stages2[MAX_FRAMES];
  uint8_t volumes3[MAX_FRAMES], stages3[MAX_FRAMES];
  size_t frames = 0;
  int awaiting_sample = 0;
  unsigned long instructions;
  for (instructions = 0;
       !cpu.halted && instructions < MAX_INSTRUCTIONS; instructions++) {
    if (cpu.pc == map.frame_tick)
      awaiting_sample = 1;
    if (cpu.pc == map.sample_loop && awaiting_sample) {
      if (frames >= MAX_FRAMES) {
        fprintf(stderr, "too many envelope frames\n");
        return 1;
      }
      volumes[frames] = f.memory[map.volume];
      stages[frames] = f.memory[map.stage];
      volumes2[frames] = f.memory[map.volume2];
      stages2[frames] = f.memory[map.stage2];
      volumes3[frames] = f.memory[map.volume3];
      stages3[frames] = f.memory[map.stage3];
      frames++;
      awaiting_sample = 0;
    }
    i8080_step(&cpu);
  }

  uint8_t expected_volume[46];
  for (size_t frame = 0; frame < sizeof(expected_volume); frame++)
    expected_volume[frame] = frame < 16 ? (uint8_t)(15 - frame) : 0;
  if (!cpu.halted || cpu.pc != 1 || cpu.sp != STACK_RETURN + 2 ||
      !cpu.iff || f.invalid_port || frames != sizeof(expected_volume) ||
      memcmp(volumes, expected_volume, sizeof(expected_volume)) != 0) {
    fprintf(stderr,
        "envelope execution mismatch: halted=%d pc=%04x sp=%04x iff=%d "
        "invalid=%d frames=%zu instructions=%lu\n",
        cpu.halted, cpu.pc, cpu.sp, cpu.iff, f.invalid_port, frames,
        instructions);
    fprintf(stderr, "volumes:");
    for (size_t i = 0; i < frames; i++)
      fprintf(stderr, " %u", volumes[i]);
    fputc('\n', stderr);
    return 1;
  }
  if (stages[0] != 2 || stages[5] != 2 || stages[6] != 4 ||
      stages[14] != 4 || stages[15] != 0 || f.memory[map.step] ||
      f.memory[(uint16_t)(map.step + 1)] || f.memory[map.target] ||
      f.memory[map.mask] || f.memory[map.sustain] != 8 ||
      f.memory[map.decay_mask] || f.memory[map.release_mask] ||
      f.memory[map.flags] != 9 || f.pit_writes < 10) {
    fprintf(stderr,
        "enhanced envelope state mismatch: stages=%u/%u/%u/%u/%u "
        "step=%u target=%u mask=%u sustain=%u decay=%u release=%u "
        "flags=%u pit=%zu\n",
        stages[0], stages[5], stages[6], stages[14], stages[15],
        word(f.memory, map.step), f.memory[map.target], f.memory[map.mask],
        f.memory[map.sustain], f.memory[map.decay_mask],
        f.memory[map.release_mask], f.memory[map.flags], f.pit_writes);
    return 1;
  }
  if (volumes2[0] != 0 || stages2[0] != 1 || volumes2[12] != 12 ||
      stages2[12] != 2 || volumes2[23] != 6 || stages2[23] != 4 ||
      volumes2[35] != 0 || stages2[35] != 0 || f.memory[map.step2] ||
      volumes3[0] != 10 || stages3[0] != 3 || stages3[15] != 3 ||
      stages3[16] != 4 || !f.memory[map.step3]) {
    fprintf(stderr, "multi-stage/EGT envelope state mismatch\n");
    return 1;
  }
  printf("JUKUPOLY-ENVELOPE: PASS frames=%zu attack=immediate "
         "decay=15..10 release=9..0 percussive-auto-release "
         "keyed-sustain step-cleared pit-writes=%zu\n",
      frames, f.pit_writes);
  return 0;
}
