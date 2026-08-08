#include "../cosim/juku_fdc.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

static uint8_t status_view(const juku_fdc* fdc) {
  uint8_t status = fdc->status;
  if (fdc->status_type_i) {
    status &= (uint8_t)~0x66;
    if (fdc->disk && fdc->disk->fp && !fdc->disk->writable) status |= 0x40;
    if (fdc->head_loaded && fdc->hlt_line) status |= 0x20;
    if (!fdc->tr00_line) status |= 0x04;
    if (fdc->index_line) status |= 0x02;
  }
  if (!(fdc->ready_line && fdc->motor_on && fdc->disk && fdc->disk->fp &&
        fdc->head >= 0 && fdc->head < fdc->disk->heads))
    status |= 0x80;
  else
    status &= (uint8_t)~0x80;
  return status;
}

static void print_state(unsigned index, const juku_fdc* fdc) {
  printf("STATE %u %02x %02x %02x %02x %02x %d %d %d %d\n",
         index, status_view(fdc), fdc->track, fdc->physical_track, fdc->sector,
         fdc->data, (fdc->status >> 1) & 1, fdc->intrq,
         fdc->head_loaded, fdc->step_dir_in);
}

int main(int argc, char** argv) {
  if (argc != 4) {
    fprintf(stderr, "usage: %s VECTOR_FILE DISK_IMAGE DELETED_MARKS\n", argv[0]);
    return 2;
  }
  FILE* vectors = fopen(argv[1], "r");
  if (!vectors) {
    perror(argv[1]);
    return 2;
  }
  juk_disk disk;
  if (juk_disk_open_writable(&disk, argv[2]) != 0) {
    fprintf(stderr, "could not open disk image %s\n", argv[2]);
    fclose(vectors);
    return 2;
  }
  if (juk_disk_attach_deleted_marks(&disk, argv[3]) != 0) {
    fprintf(stderr, "could not open deleted-mark metadata %s\n", argv[3]);
    juk_disk_close(&disk);
    fclose(vectors);
    return 2;
  }
  juku_fdc fdc;
  juku_fdc_init(&fdc, &disk);
  char op;
  unsigned a, b;
  unsigned index = 0;
  while (fscanf(vectors, " %c %x %x", &op, &a, &b) == 3) {
    uint8_t value = 0;
    switch (op) {
      case 'P': juku_fdc_portc(&fdc, (uint8_t)a); break;
      case 'H': juku_fdc_hlt(&fdc, a != 0); break;
      case 'T': juku_fdc_tr00(&fdc, a != 0); break;
      case 'Y': juku_fdc_ready(&fdc, a != 0); break;
      case 'I': juku_fdc_index(&fdc, a != 0); break;
      case 'W': juku_fdc_write(&fdc, (uint8_t)a, (uint8_t)b); break;
      case 'K': juku_fdc_tick(&fdc, a); break;
      case 'R':
        value = juku_fdc_read(&fdc, (uint8_t)a);
        printf("READ %u %02x\n", index, value);
        break;
      default:
        fprintf(stderr, "unknown vector operation %c at index %u\n", op, index);
        juk_disk_close(&disk);
        fclose(vectors);
        return 2;
    }
    print_state(index, &fdc);
    index++;
  }
  if (!feof(vectors)) {
    fprintf(stderr, "malformed vector file near operation %u\n", index);
    juk_disk_close(&disk);
    fclose(vectors);
    return 2;
  }
  juk_disk_close(&disk);
  fclose(vectors);
  return 0;
}
