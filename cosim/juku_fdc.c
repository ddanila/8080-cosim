#include "juku_fdc.h"

#include <string.h>


enum {
  ST_BUSY = 0x01,
  ST_DRQ = 0x02,
  ST_RNF = 0x10,
  ST_WRITE_PROTECT = 0x40,
  ST_NOT_READY = 0x80,
};


static int is_read_sector(uint8_t command) {
  return (command & 0xE0) == 0x80;
}


static int is_type_i(uint8_t command) {
  return (command & 0x80) == 0x00;
}


static int is_write_sector(uint8_t command) {
  return (command & 0xE0) == 0xA0;
}


static int is_write_track(uint8_t command) {
  return (command & 0xF0) == 0xF0;
}


static int is_read_address(uint8_t command) {
  return (command & 0xFB) == 0xC0;  // bit 2 is the optional 15 ms delay flag
}


static uint16_t id_crc_byte(uint16_t crc, uint8_t data) {
  crc ^= (uint16_t)data << 8;
  for (int bit = 0; bit < 8; bit++) {
    crc = (uint16_t)((crc << 1) ^ ((crc & 0x8000) ? 0x1021 : 0));
  }
  return crc;
}


static uint16_t id_crc(uint8_t track, uint8_t side, uint8_t sector) {
  uint16_t crc = 0xFFFF;
  crc = id_crc_byte(crc, 0xFE);  // ID address mark
  crc = id_crc_byte(crc, track);
  crc = id_crc_byte(crc, side);
  crc = id_crc_byte(crc, sector);
  return id_crc_byte(crc, 2);    // 512-byte sector length code
}


static void clear_transfer(juku_fdc* fdc) {
  fdc->buffer_pos = 0;
  fdc->buffer_len = 0;
  fdc->write_transfer = 0;
  fdc->read_address_transfer = 0;
  fdc->multi_record = 0;
  fdc->status &= (uint8_t)~(ST_BUSY | ST_DRQ);
}


static void complete_transfer(juku_fdc* fdc) {
  clear_transfer(fdc);
  fdc->intrq = 1;
}


static int load_read_sector(juku_fdc* fdc) {
  int rc = juk_disk_read_sector(fdc->disk, fdc->track, fdc->head, fdc->sector, fdc->buffer);
  if (rc != 0) return rc;
  fdc->buffer_pos = 0;
  fdc->buffer_len = JUK_SECTOR_SIZE;
  fdc->status |= ST_BUSY | ST_DRQ;
  return 0;
}


static void begin_read_sector(juku_fdc* fdc, int multi_record) {
  clear_transfer(fdc);
  fdc->status &= (uint8_t)~(ST_RNF | ST_WRITE_PROTECT | ST_NOT_READY);
  if (!fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  if (load_read_sector(fdc) != 0) {
    fdc->status |= ST_RNF;
    complete_transfer(fdc);
    return;
  }
  fdc->multi_record = multi_record;
}


static void finish_type_i(juku_fdc* fdc, uint8_t command) {
  clear_transfer(fdc);
  fdc->status &= (uint8_t)~(ST_RNF | ST_WRITE_PROTECT | ST_NOT_READY);
  if (!fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  if ((command & 0xF0) == 0x00) {        // restore
    fdc->track = 0;
  } else if ((command & 0xF0) == 0x10) { // seek
    fdc->step_dir_in = fdc->data >= fdc->track;
    fdc->track = fdc->data;
  } else if ((command & 0xE0) == 0x20) { // step in the previous direction
    if (command & 0x10) {
      if (fdc->step_dir_in && fdc->track != 0xFF) fdc->track++;
      else if (!fdc->step_dir_in && fdc->track != 0) fdc->track--;
    }
  } else if ((command & 0xE0) == 0x40) { // step in
    fdc->step_dir_in = 1;
    if ((command & 0x10) && fdc->track != 0xFF) fdc->track++;
  } else if ((command & 0xE0) == 0x60) { // step out
    fdc->step_dir_in = 0;
    if ((command & 0x10) && fdc->track != 0) fdc->track--;
  }
  complete_transfer(fdc);
}


static void begin_write_sector(juku_fdc* fdc, int multi_record) {
  clear_transfer(fdc);
  fdc->status &= (uint8_t)~(ST_RNF | ST_WRITE_PROTECT | ST_NOT_READY);
  if (!fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  if (!fdc->disk->writable) {
    fdc->status |= ST_WRITE_PROTECT;
    complete_transfer(fdc);
    return;
  }
  if (juk_disk_offset(fdc->disk, fdc->track, fdc->head, fdc->sector) < 0) {
    fdc->status |= ST_RNF;
    complete_transfer(fdc);
    return;
  }
  fdc->buffer_pos = 0;
  fdc->buffer_len = JUK_SECTOR_SIZE;
  fdc->write_transfer = 1;
  fdc->multi_record = multi_record;
  fdc->status |= ST_BUSY | ST_DRQ;
}


static void begin_read_address(juku_fdc* fdc) {
  clear_transfer(fdc);
  fdc->status &= (uint8_t)~(ST_RNF | ST_WRITE_PROTECT | ST_NOT_READY);
  if (!fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  if (fdc->track >= JUK_TRACKS || fdc->head < 0 || fdc->head >= fdc->disk->heads) {
    fdc->status |= ST_RNF;
    complete_transfer(fdc);
    return;
  }

  // A flat sector image has no rotational position. Use the first sector ID
  // after index as the deterministic representation of the next ID field.
  const uint8_t address_sector = 1;
  const uint16_t crc = id_crc(fdc->track, (uint8_t)fdc->head, address_sector);
  fdc->buffer[0] = fdc->track;
  fdc->buffer[1] = (uint8_t)fdc->head;
  fdc->buffer[2] = address_sector;
  fdc->buffer[3] = 2;
  fdc->buffer[4] = (uint8_t)(crc >> 8);
  fdc->buffer[5] = (uint8_t)crc;
  fdc->buffer_pos = 0;
  fdc->buffer_len = 6;
  fdc->read_address_transfer = 1;
  fdc->status |= ST_BUSY | ST_DRQ;
}


static void accept_write_byte(juku_fdc* fdc, uint8_t data) {
  if (!fdc->write_transfer || fdc->buffer_pos >= fdc->buffer_len) return;
  fdc->buffer[fdc->buffer_pos++] = data;
  if (fdc->buffer_pos < fdc->buffer_len) return;
  int rc = juk_disk_write_sector(
      fdc->disk, fdc->track, fdc->head, fdc->sector, fdc->buffer);
  if (rc != 0) {
    complete_transfer(fdc);
    fdc->status |= ST_WRITE_PROTECT;
    return;
  }
  if (!fdc->multi_record) {
    complete_transfer(fdc);
    return;
  }

  fdc->sector++;
  if (juk_disk_offset(fdc->disk, fdc->track, fdc->head, fdc->sector) < 0) {
    complete_transfer(fdc);
    fdc->status |= ST_RNF;
    return;
  }
  fdc->buffer_pos = 0;
  fdc->buffer_len = JUK_SECTOR_SIZE;
  fdc->write_transfer = 1;
  fdc->status |= ST_BUSY | ST_DRQ;
}


static void reject_write_track(juku_fdc* fdc) {
  clear_transfer(fdc);
  fdc->status &= (uint8_t)~(ST_RNF | ST_NOT_READY);
  if (!fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  fdc->status |= ST_WRITE_PROTECT;
  complete_transfer(fdc);
}


void juku_fdc_init(juku_fdc* fdc, juk_disk* disk) {
  memset(fdc, 0, sizeof(*fdc));
  fdc->disk = disk;
  fdc->enabled = disk && disk->fp;
  fdc->step_dir_in = 1;
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
    case 0: {
      uint8_t status = fdc->status;
      fdc->intrq = 0;
      return status;
    }
    case 1:
      return fdc->track;
    case 2:
      return fdc->sector;
    default:
      if (fdc->buffer_pos < fdc->buffer_len) {
        fdc->data = fdc->buffer[fdc->buffer_pos++];
        if (fdc->buffer_pos >= fdc->buffer_len) {
          if (fdc->read_address_transfer) {
            fdc->sector = fdc->buffer[0];
            complete_transfer(fdc);
          } else if (fdc->multi_record) {
            fdc->sector++;
            if (load_read_sector(fdc) != 0) {
              complete_transfer(fdc);
              fdc->status |= ST_RNF;
            }
          } else {
            complete_transfer(fdc);
          }
        }
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
      fdc->intrq = 0;
      if (is_read_sector(data)) begin_read_sector(fdc, (data & 0x10) != 0);
      else if (is_type_i(data)) finish_type_i(fdc, data);
      else if ((data & 0xF0) == 0xD0) {
        clear_transfer(fdc);
        fdc->intrq = (data & 0x08) != 0;  // D0 terminates silently; D8 is immediate
      }
      else if (is_write_sector(data)) begin_write_sector(fdc, (data & 0x10) != 0);
      else if (is_read_address(data)) begin_read_address(fdc);
      else if (is_write_track(data)) reject_write_track(fdc);
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
      accept_write_byte(fdc, data);
      break;
  }
}
