#include "juku_fdc.h"

#include <string.h>


enum {
  ST_BUSY = 0x01,
  ST_DRQ = 0x02,
  ST_RNF = 0x10,
  ST_NOT_READY = 0x80,
};


static int is_read_sector(uint8_t command) {
  return (command & 0xE0) == 0x80;
}


static int is_type_i(uint8_t command) {
  return (command & 0x80) == 0x00;
}


static void clear_transfer(juku_fdc* fdc) {
  fdc->buffer_pos = 0;
  fdc->buffer_len = 0;
  fdc->status &= (uint8_t)~(ST_BUSY | ST_DRQ);
}


static void begin_read_sector(juku_fdc* fdc) {
  clear_transfer(fdc);
  fdc->status &= (uint8_t)~(ST_RNF | ST_NOT_READY);
  if (!fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    return;
  }
  int rc = juk_disk_read_sector(fdc->disk, fdc->track, fdc->head, fdc->sector, fdc->buffer);
  if (rc != 0) {
    fdc->status |= ST_RNF;
    return;
  }
  fdc->buffer_pos = 0;
  fdc->buffer_len = JUK_SECTOR_SIZE;
  fdc->status |= ST_BUSY | ST_DRQ;
}


static void finish_type_i(juku_fdc* fdc, uint8_t command) {
  clear_transfer(fdc);
  fdc->status &= (uint8_t)~(ST_RNF | ST_NOT_READY);
  if (!fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    return;
  }
  if ((command & 0xF0) == 0x00) {        // restore
    fdc->track = 0;
  } else if ((command & 0xF0) == 0x10) { // seek
    fdc->track = fdc->data;
  }
}


void juku_fdc_init(juku_fdc* fdc, juk_disk* disk) {
  memset(fdc, 0, sizeof(*fdc));
  fdc->disk = disk;
  fdc->enabled = disk && disk->fp;
  fdc->sector = 1;
  fdc->status = fdc->enabled ? 0 : ST_NOT_READY;
}


void juku_fdc_portc(juku_fdc* fdc, uint8_t portc) {
  fdc->motor_on = (portc >> 2) & 1;
  fdc->head = (portc >> 6) & 1;
  fdc->drive = (portc >> 5) & 1;
  if (fdc->disk && fdc->head >= fdc->disk->heads) fdc->status |= ST_NOT_READY;
  else fdc->status &= (uint8_t)~ST_NOT_READY;
}


uint8_t juku_fdc_read(juku_fdc* fdc, uint8_t reg) {
  switch (reg & 3) {
    case 0:
      return fdc->status;
    case 1:
      return fdc->track;
    case 2:
      return fdc->sector;
    default:
      if (fdc->buffer_pos < fdc->buffer_len) {
        fdc->data = fdc->buffer[fdc->buffer_pos++];
        if (fdc->buffer_pos >= fdc->buffer_len) clear_transfer(fdc);
        return fdc->data;
      }
      fdc->status &= (uint8_t)~ST_DRQ;
      return fdc->data;
  }
}


void juku_fdc_write(juku_fdc* fdc, uint8_t reg, uint8_t data) {
  switch (reg & 3) {
    case 0:
      fdc->command = data;
      if (is_read_sector(data)) begin_read_sector(fdc);
      else if (is_type_i(data)) finish_type_i(fdc, data);
      else if ((data & 0xF0) == 0xD0) clear_transfer(fdc);  // force interrupt
      else {
        fdc->status &= (uint8_t)~(ST_RNF | ST_DRQ);
        fdc->status |= ST_BUSY;
      }
      break;
    case 1:
      fdc->track = data;
      break;
    case 2:
      fdc->sector = data;
      break;
    default:
      fdc->data = data;
      break;
  }
}
