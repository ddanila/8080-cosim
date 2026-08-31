#include "../cosim/i8080.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define COM_ADDRESS 0x0100
#define SONG_ADDRESS 0x1800
#define STACK_RETURN 0x9bfe
#define BIOS_CONIN 0xf006
#define BIOS_CONOUT 0xf009
#define MAX_OUTPUT 32768
#define MAX_INSTRUCTIONS 30000000UL

typedef struct {
  uint8_t memory[65536];
  uint8_t *song;
  size_t song_size, song_offset;
  uint16_t dma;
  const char *input;
  size_t input_at;
  char output[MAX_OUTPUT];
  size_t output_at;
  size_t pit_writes, keyboard_polls, abort_after;
  uint8_t keyboard_column;
  int invalid_port, opened, selected_track;
} fixture;

static uint8_t read_byte(void *opaque, uint16_t address) {
  return ((fixture *)opaque)->memory[address];
}

static void write_byte(void *opaque, uint16_t address, uint8_t value) {
  ((fixture *)opaque)->memory[address] = value;
}

static uint8_t port_in(void *opaque, uint8_t port) {
  fixture *f = opaque;
  if (port != 0x05 || f->keyboard_column != 3) {
    f->invalid_port = 1;
    return 0xff;
  }
  f->keyboard_polls++;
  if (f->abort_after && f->keyboard_polls >= f->abort_after &&
      f->keyboard_polls < f->abort_after + 3)
    return 0x06;              /* Escape: column 3, encoder input 4 */
  return 0xff;
}

static void port_out(void *opaque, uint8_t port, uint8_t value) {
  fixture *f = opaque;
  if (port == 0x04) {
    f->keyboard_column = value;
    return;
  }
  if (port != 0x19 && port != 0x1b)
    f->invalid_port = 1;
  f->pit_writes++;
}

static uint16_t word(const uint8_t *memory, uint16_t address) {
  return memory[address] | (uint16_t)memory[(uint16_t)(address + 1)] << 8;
}

static void emit(fixture *f, uint8_t value) {
  if (f->output_at + 1 >= MAX_OUTPUT) {
    fprintf(stderr, "library console output overflow\n");
    exit(1);
  }
  f->output[f->output_at++] = (char)value;
  f->output[f->output_at] = '\0';
}

static void bdos_return(i8080 *cpu, fixture *f) {
  cpu->pc = word(f->memory, cpu->sp);
  cpu->sp += 2;
}

static void emulate_bdos(i8080 *cpu, fixture *f) {
  uint16_t de = (uint16_t)cpu->d << 8 | cpu->e;
  switch (cpu->c) {
    case 1:
      if (!f->input[f->input_at]) {
        fprintf(stderr, "library requested unexpected console input\n");
        exit(1);
      }
      cpu->a = (uint8_t)f->input[f->input_at++];
      emit(f, cpu->a);
      break;
    case 2:
      emit(f, cpu->e);
      break;
    case 9:
      for (uint16_t at = de; f->memory[at] != '$'; at++)
        emit(f, f->memory[at]);
      break;
    case 15: {
      int game = f->selected_track <= 23 ? 1 : 2;
      int local = game == 1 ? f->selected_track : f->selected_track - 23;
      uint8_t expected[11] = {
        'D', (uint8_t)('0' + game), 'T',
        (uint8_t)('0' + local / 10), (uint8_t)('0' + local % 10),
        ' ', ' ', ' ', 'J', 'P', 'S'
      };
      if (f->memory[de] != 2 ||
          memcmp(&f->memory[de + 1], expected, sizeof(expected)) != 0) {
        fprintf(stderr, "library opened an unexpected FCB name\n");
        exit(1);
      }
      f->song_offset = 0;
      f->opened = 1;
      cpu->a = 0;
      break;
    }
    case 16:
      cpu->a = 0;
      break;
    case 20:
      if (!f->opened) {
        fprintf(stderr, "library read before opening its song\n");
        exit(1);
      }
      if (f->song_offset >= f->song_size) {
        cpu->a = 1;
      } else {
        size_t count = f->song_size - f->song_offset;
        if (count > 128)
          count = 128;
        memset(&f->memory[f->dma], 0, 128);
        memcpy(&f->memory[f->dma], f->song + f->song_offset, count);
        f->song_offset += 128;
        cpu->a = 0;
      }
      break;
    case 26:
      f->dma = de;
      cpu->a = 0;
      break;
    default:
      fprintf(stderr, "unexpected BDOS function %u\n", cpu->c);
      exit(1);
  }
  bdos_return(cpu, f);
}

static void emulate_bios_console(i8080 *cpu, fixture *f) {
  if (cpu->pc == BIOS_CONIN) {
    if (!f->input[f->input_at]) {
      fprintf(stderr, "library requested unexpected BIOS console input\n");
      exit(1);
    }
    cpu->a = (uint8_t)f->input[f->input_at++];
  } else if (cpu->pc == BIOS_CONOUT) {
    emit(f, cpu->c);
  } else {
    fprintf(stderr, "unexpected BIOS console address %04x\n", cpu->pc);
    exit(1);
  }
  bdos_return(cpu, f);
}

static uint8_t *read_file(const char *path, size_t *size) {
  FILE *input = fopen(path, "rb");
  if (!input) {
    perror(path);
    exit(2);
  }
  if (fseek(input, 0, SEEK_END) || (*size = (size_t)ftell(input)) == 0 ||
      fseek(input, 0, SEEK_SET)) {
    fprintf(stderr, "cannot size %s\n", path);
    exit(2);
  }
  uint8_t *data = malloc(*size);
  if (!data || fread(data, 1, *size, input) != *size) {
    fprintf(stderr, "cannot read %s\n", path);
    exit(2);
  }
  fclose(input);
  return data;
}

int main(int argc, char **argv) {
  if (argc < 3 || argc > 4 ||
      (argc == 4 && strcmp(argv[3], "abort") != 0 &&
       (atoi(argv[3]) < 1 || atoi(argv[3]) > 44))) {
    fprintf(stderr, "usage: %s JUKEBOX.COM SONG.JPS [abort|TRACK]\n", argv[0]);
    return 2;
  }
  fixture f = {0};
  f.selected_track = 1;
  if (argc == 4 && strcmp(argv[3], "abort") == 0)
    f.abort_after = 5;
  else if (argc == 4)
    f.selected_track = atoi(argv[3]);
  size_t com_size;
  uint8_t *com = read_file(argv[1], &com_size);
  f.song = read_file(argv[2], &f.song_size);
  if (com_size >= SONG_ADDRESS - COM_ADDRESS || f.song_size > 0x8000 ||
      f.song_size < 16 || memcmp(f.song, "JPS\1", 4) != 0) {
    fprintf(stderr, "invalid library fixture sizes or JPS header\n");
    return 2;
  }
  memcpy(&f.memory[COM_ADDRESS], com, com_size);
  free(com);
  f.memory[0] = 0x76;
  f.memory[1] = 0x00;           /* page-zero WBOOT target = F000h */
  f.memory[2] = 0xf0;
  f.memory[STACK_RETURN] = 0;
  f.memory[STACK_RETURN + 1] = 0;
  f.dma = 0x80;
  char input[8];
  snprintf(input, sizeof(input), "%02d\rQ", f.selected_track);
  f.input = input;

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

  unsigned long instructions;
  for (instructions = 0;
       !cpu.halted && instructions < MAX_INSTRUCTIONS; instructions++) {
    if (cpu.pc == 5)
      emulate_bdos(&cpu, &f);
    else if (cpu.pc == BIOS_CONIN || cpu.pc == BIOS_CONOUT)
      emulate_bios_console(&cpu, &f);
    else
      i8080_step(&cpu);
  }
  char selected_line[32];
  snprintf(selected_line, sizeof(selected_line), "%02d ", f.selected_track);
  const char *required[] = {
    "JukuPoly DOOM library",
    selected_line,
    "Loading disk song",
    "JukuPoly stopped",
  };
  for (size_t i = 0; i < sizeof(required) / sizeof(required[0]); i++) {
    if (!strstr(f.output, required[i])) {
      fprintf(stderr, "library output lacks %s\n--- output ---\n%s\n",
          required[i], f.output);
      return 1;
    }
  }
  const char *result = f.abort_after ? "Track stopped" : "Track finished";
  if (!strstr(f.output, result)) {
    fprintf(stderr, "library output lacks %s\n--- output ---\n%s\n",
        result, f.output);
    return 1;
  }
  if (!cpu.halted || cpu.pc != 1 || cpu.sp != STACK_RETURN + 2 || !cpu.iff ||
      f.invalid_port || f.pit_writes < (f.abort_after ? 10 : 100) || !f.opened ||
      (f.abort_after ? f.keyboard_polls != f.abort_after + 3
                     : f.keyboard_polls < 300) ||
      f.input[f.input_at]) {
    fprintf(stderr,
        "library did not finish cleanly: halted=%d pc=%04x sp=%04x iff=%d "
        "ports=%zu key-polls=%zu invalid=%d input=%s instructions=%lu\n",
        cpu.halted, cpu.pc, cpu.sp, cpu.iff, f.pit_writes,
        f.keyboard_polls, f.invalid_port, f.input + f.input_at, instructions);
    return 1;
  }
  printf("JUKUPOLY-LIBRARY: PASS mode=%s com=%zu jps=%zu pit-writes=%zu "
         "key-polls=%zu output=%zu\n",
      f.abort_after ? "abort" : "complete", com_size, f.song_size,
      f.pit_writes, f.keyboard_polls, f.output_at);
  free(f.song);
  return 0;
}
