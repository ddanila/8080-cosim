#ifndef JUKU_FDC_H
#define JUKU_FDC_H

#include <stdint.h>

#include "juk_disk.h"

typedef struct {
  juk_disk* disk;
  int enabled;
  int head;
  int drive;
  int motor_on;
  uint8_t status;
  uint8_t track;
  uint8_t sector;
  uint8_t data;
  uint8_t command;
  int step_dir_in;
  uint8_t buffer[JUK_MFM_TRACK_SIZE];
  unsigned buffer_pos;
  unsigned buffer_len;
  int write_transfer;
  int write_track_transfer;
  int read_address_transfer;
  int read_track_transfer;
  int multi_record;
  unsigned write_track_output_pos;
  int write_track_state;
  unsigned write_track_field_pos;
  uint8_t write_track_id[4];
  int write_track_pending_sector;
  uint16_t write_track_seen;
  int write_track_format_error;
  int intrq;
} juku_fdc;

void juku_fdc_init(juku_fdc* fdc, juk_disk* disk);
void juku_fdc_portc(juku_fdc* fdc, uint8_t portc);
uint8_t juku_fdc_read(juku_fdc* fdc, uint8_t reg);
void juku_fdc_write(juku_fdc* fdc, uint8_t reg, uint8_t data);

#endif
