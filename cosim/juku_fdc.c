#include "juku_fdc.h"

#include <string.h>


enum {
  ST_BUSY = 0x01,
  ST_DRQ = 0x02,
  ST_TRACK0_LOST = 0x04,
  ST_CRC = 0x08,
  ST_RNF = 0x10,
  ST_WRITE_FAULT = 0x20,
  ST_WRITE_PROTECT = 0x40,
  ST_NOT_READY = 0x80,
};

enum {
  DRQ_BYTE_TICKS = 64,
  WRITE_SECTOR_LEAD_TICKS = 22 * DRQ_BYTE_TICKS,
};

enum {
  WT_SCAN = 0,
  WT_ID = 1,
  WT_ID_CRC = 2,
  WT_DATA = 3,
  WT_DATA_CRC = 4,
};


static int controller_ready(const juku_fdc* fdc) {
  return fdc->ready_line && fdc->motor_on && fdc->disk && fdc->disk->fp &&
         fdc->head >= 0 && fdc->head < fdc->disk->heads;
}


static void update_not_ready(juku_fdc* fdc) {
  if (controller_ready(fdc)) fdc->status &= (uint8_t)~ST_NOT_READY;
  else fdc->status |= ST_NOT_READY;
}


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


static int is_read_track(uint8_t command) {
  return (command & 0xFB) == 0xE0;  // bit 2 is the optional 15 ms delay flag
}


static int is_type_ii_iii(uint8_t command) {
  return is_read_sector(command) || is_write_sector(command) ||
         is_read_address(command) || is_read_track(command) ||
         is_write_track(command);
}


static uint16_t crc_byte(uint16_t crc, uint8_t data) {
  crc ^= (uint16_t)data << 8;
  for (int bit = 0; bit < 8; bit++) {
    crc = (uint16_t)((crc << 1) ^ ((crc & 0x8000) ? 0x1021 : 0));
  }
  return crc;
}


static uint16_t id_crc(uint8_t track, uint8_t side, uint8_t sector) {
  uint16_t crc = 0xFFFF;
  crc = crc_byte(crc, 0xFE);  // ID address mark
  crc = crc_byte(crc, track);
  crc = crc_byte(crc, side);
  crc = crc_byte(crc, sector);
  return crc_byte(crc, 2);    // 512-byte sector length code
}


static void clear_transfer(juku_fdc* fdc) {
  fdc->buffer_pos = 0;
  fdc->buffer_len = 0;
  fdc->write_transfer = 0;
  fdc->write_track_transfer = 0;
  fdc->read_address_transfer = 0;
  fdc->read_track_transfer = 0;
  fdc->multi_record = 0;
  fdc->write_track_output_pos = 0;
  fdc->write_track_state = WT_SCAN;
  fdc->write_track_field_pos = 0;
  fdc->write_track_pending_sector = 0;
  fdc->write_track_seen = 0;
  fdc->write_track_format_error = 0;
  fdc->track_waiting_index = 0;
  fdc->write_track_preloaded = 0;
  fdc->command_delay_pending = 0;
  fdc->command_delay_ticks = 0;
  fdc->write_sector_lead_pending = 0;
  fdc->write_sector_lead_ticks = 0;
  fdc->write_sector_preloaded = 0;
  fdc->side_compare_pending = 0;
  fdc->side_compare_index_pulses = 0;
  fdc->id_search_pending = 0;
  fdc->id_search_index_pulses = 0;
  fdc->drq_ticks = 0;
  fdc->write_first_byte_pending = 0;
  fdc->type_i_pending = 0;
  fdc->type_i_ticks = 0;
  fdc->type_i_steps_remaining = 0;
  fdc->type_i_settling = 0;
  fdc->status &= (uint8_t)~(ST_BUSY | ST_DRQ);
}


static void complete_transfer(juku_fdc* fdc) {
  clear_transfer(fdc);
  fdc->intrq = 1;
}


static int load_read_sector(juku_fdc* fdc) {
  if (fdc->track != fdc->physical_track) return -1;
  int rc = juk_disk_read_sector(
      fdc->disk, fdc->physical_track, fdc->head, fdc->sector, fdc->buffer);
  if (rc != 0) return rc;
  fdc->buffer_pos = 0;
  fdc->buffer_len = JUK_SECTOR_SIZE;
  fdc->status |= ST_BUSY | ST_DRQ;
  fdc->drq_ticks = 0;
  return 0;
}


static int side_compare_mismatch(const juku_fdc* fdc, uint8_t command) {
  return (command & 0x02) && (((command >> 3) & 1) != (fdc->head & 1));
}


static void begin_read_sector(juku_fdc* fdc, uint8_t command) {
  clear_transfer(fdc);
  fdc->status_type_i = 0;
  fdc->head_loaded = 1;
  fdc->status &= (uint8_t)~(
      ST_TRACK0_LOST | ST_CRC | ST_RNF | ST_WRITE_FAULT | ST_WRITE_PROTECT | ST_NOT_READY);
  if (!fdc->ready_line || !fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  if (fdc->track != fdc->physical_track ||
      juk_disk_offset(fdc->disk, fdc->physical_track, fdc->head, fdc->sector) < 0) {
    fdc->id_search_pending = 1;
    fdc->status |= ST_BUSY;
    return;
  }
  fdc->multi_record = (command & 0x10) != 0;
  if (side_compare_mismatch(fdc, command)) {
    fdc->side_compare_pending = 1;
    fdc->status |= ST_BUSY;
    return;
  }
  if (load_read_sector(fdc) != 0) {
    fdc->status |= ST_RNF;
    complete_transfer(fdc);
  }
}


static unsigned type_i_rate_ticks(uint8_t command) {
  static const unsigned rates[4] = {6000, 12000, 20000, 30000};
  return rates[command & 3];
}


static void type_i_step_once(juku_fdc* fdc) {
  const uint8_t command = fdc->type_i_command;
  if ((command & 0xF0) == 0x00) {        // restore
    fdc->step_dir_in = 0;
    if (fdc->physical_track != 0) fdc->physical_track--;
    if (fdc->track != 0) fdc->track--;
  } else if ((command & 0xF0) == 0x10) { // seek
    if (fdc->step_dir_in) {
      if (fdc->physical_track != 0xFF) fdc->physical_track++;
      if (fdc->track != 0xFF) fdc->track++;
    } else {
      if (fdc->physical_track != 0) fdc->physical_track--;
      if (fdc->track != 0) fdc->track--;
    }
  } else {
    if (fdc->step_dir_in && fdc->physical_track != 0xFF) fdc->physical_track++;
    else if (!fdc->step_dir_in && fdc->physical_track != 0) fdc->physical_track--;
    if (command & 0x10) {
      if (fdc->step_dir_in && fdc->track != 0xFF) fdc->track++;
      else if (!fdc->step_dir_in && fdc->track != 0) fdc->track--;
    }
  }
}


static void complete_type_i(juku_fdc* fdc) {
  const uint8_t command = fdc->type_i_command;
  if ((command & 0xF0) == 0x00) {
    fdc->track = 0;
    fdc->physical_track = 0;
  } else if ((command & 0xF0) == 0x10) {
    fdc->track = fdc->data;
  }
  if ((command & 0x04) &&
      (fdc->track != fdc->physical_track || fdc->physical_track >= JUK_TRACKS)) {
    fdc->status |= ST_RNF;  // Type-I meaning: SEEK ERROR
  }
  complete_transfer(fdc);
}


static void finish_type_i_motion(juku_fdc* fdc) {
  if (fdc->type_i_command & 0x04) {
    fdc->head_loaded = 1;
    fdc->type_i_settling = 1;
    fdc->type_i_ticks = 30000;  // 15 ms at the FD1793's nominal 2 MHz clock
  } else {
    complete_type_i(fdc);
  }
}


static void begin_type_i(juku_fdc* fdc, uint8_t command) {
  clear_transfer(fdc);
  fdc->status_type_i = 1;
  fdc->head_loaded = (command & 0x08) != 0;
  fdc->status &= (uint8_t)~(ST_CRC | ST_RNF | ST_NOT_READY);
  if (!fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  update_not_ready(fdc);
  fdc->type_i_command = command;
  fdc->type_i_rate_ticks = type_i_rate_ticks(command);
  if ((command & 0xF0) == 0x00) {
    fdc->type_i_steps_remaining = fdc->physical_track;
  } else if ((command & 0xF0) == 0x10) {
    const int delta = (int)fdc->data - (int)fdc->track;
    fdc->step_dir_in = delta >= 0;
    fdc->type_i_steps_remaining = (unsigned)(delta >= 0 ? delta : -delta);
  } else {
    if ((command & 0xE0) == 0x40) fdc->step_dir_in = 1;
    else if ((command & 0xE0) == 0x60) fdc->step_dir_in = 0;
    fdc->type_i_steps_remaining = 1;
  }
  fdc->type_i_pending = 1;
  fdc->status |= ST_BUSY;
  if (fdc->type_i_steps_remaining) {
    type_i_step_once(fdc);
    fdc->type_i_steps_remaining--;
    fdc->type_i_ticks = fdc->type_i_rate_ticks;
  } else {
    finish_type_i_motion(fdc);
  }
}


static void arm_write_sector_record(juku_fdc* fdc) {
  fdc->buffer_pos = 0;
  fdc->buffer_len = JUK_SECTOR_SIZE;
  fdc->write_transfer = 1;
  fdc->write_first_byte_pending = 1;
  fdc->write_sector_lead_pending = 1;
  fdc->write_sector_lead_ticks = WRITE_SECTOR_LEAD_TICKS;
  fdc->write_sector_preloaded = 0;
  fdc->status |= ST_BUSY | ST_DRQ;
  fdc->drq_ticks = 0;
}


static void begin_write_sector(juku_fdc* fdc, uint8_t command) {
  clear_transfer(fdc);
  fdc->status_type_i = 0;
  fdc->head_loaded = 1;
  fdc->status &= (uint8_t)~(
      ST_TRACK0_LOST | ST_CRC | ST_RNF | ST_WRITE_FAULT | ST_WRITE_PROTECT | ST_NOT_READY);
  if (!fdc->ready_line || !fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  if (!fdc->disk->writable) {
    fdc->status |= ST_WRITE_PROTECT;
    complete_transfer(fdc);
    return;
  }
  if (fdc->track != fdc->physical_track ||
      juk_disk_offset(fdc->disk, fdc->physical_track, fdc->head, fdc->sector) < 0) {
    fdc->id_search_pending = 1;
    fdc->status |= ST_BUSY;
    return;
  }
  fdc->multi_record = (command & 0x10) != 0;
  if (side_compare_mismatch(fdc, command)) {
    fdc->side_compare_pending = 1;
    fdc->status |= ST_BUSY;
    return;
  }
  arm_write_sector_record(fdc);
}


static void begin_read_address(juku_fdc* fdc) {
  clear_transfer(fdc);
  fdc->status_type_i = 0;
  fdc->head_loaded = 1;
  fdc->status &= (uint8_t)~(
      ST_TRACK0_LOST | ST_CRC | ST_RNF | ST_WRITE_FAULT | ST_WRITE_PROTECT | ST_NOT_READY);
  if (!fdc->ready_line || !fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  if (fdc->physical_track >= JUK_TRACKS || fdc->head < 0 || fdc->head >= fdc->disk->heads) {
    fdc->status |= ST_RNF;
    complete_transfer(fdc);
    return;
  }

  // A flat sector image has no rotational position. Use the first sector ID
  // after index as the deterministic representation of the next ID field.
  const uint8_t address_sector = 1;
  const uint16_t crc = id_crc(fdc->physical_track, (uint8_t)fdc->head, address_sector);
  fdc->buffer[0] = fdc->physical_track;
  fdc->buffer[1] = (uint8_t)fdc->head;
  fdc->buffer[2] = address_sector;
  fdc->buffer[3] = 2;
  fdc->buffer[4] = (uint8_t)(crc >> 8);
  fdc->buffer[5] = (uint8_t)crc;
  fdc->buffer_pos = 0;
  fdc->buffer_len = 6;
  fdc->read_address_transfer = 1;
  fdc->status |= ST_BUSY | ST_DRQ;
  fdc->drq_ticks = 0;
}


static void track_byte(juku_fdc* fdc, unsigned* pos, uint8_t value) {
  if (*pos < JUK_MFM_TRACK_SIZE) fdc->buffer[*pos] = value;
  (*pos)++;
}


static void track_crc_byte(juku_fdc* fdc, unsigned* pos, uint16_t* crc, uint8_t value) {
  track_byte(fdc, pos, value);
  *crc = crc_byte(*crc, value);
}


static void begin_read_track(juku_fdc* fdc) {
  clear_transfer(fdc);
  fdc->status_type_i = 0;
  fdc->head_loaded = 1;
  fdc->status &= (uint8_t)~(
      ST_TRACK0_LOST | ST_CRC | ST_RNF | ST_WRITE_FAULT | ST_WRITE_PROTECT | ST_NOT_READY);
  if (!fdc->ready_line || !fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  if (fdc->physical_track >= JUK_TRACKS || fdc->head < 0 || fdc->head >= fdc->disk->heads) {
    fdc->status |= ST_RNF;
    complete_transfer(fdc);
    return;
  }

  // Reconstruct the one-revolution MFM byte stream used by MAME's Juku raw
  // image format: 2000 ns cells, 6250 decoded bytes, and 32/22/35-byte gaps.
  // The raw image itself contains sector payloads only, so physical gap bytes
  // and rotational phase cannot be recovered from it.
  unsigned pos = 0;
  for (int i = 0; i < 32; i++) track_byte(fdc, &pos, 0x4E);
  for (int sector_id = 1; sector_id <= JUK_SECTORS_PER_TRACK; sector_id++) {
    uint8_t sector_data[JUK_SECTOR_SIZE];
    if (juk_disk_read_sector(
            fdc->disk, fdc->physical_track, fdc->head, sector_id, sector_data) != 0) {
      fdc->status |= ST_RNF;
      complete_transfer(fdc);
      return;
    }

    for (int i = 0; i < 12; i++) track_byte(fdc, &pos, 0x00);
    uint16_t crc = 0xFFFF;
    for (int i = 0; i < 3; i++) track_crc_byte(fdc, &pos, &crc, 0xA1);
    track_crc_byte(fdc, &pos, &crc, 0xFE);
    track_crc_byte(fdc, &pos, &crc, fdc->physical_track);
    track_crc_byte(fdc, &pos, &crc, (uint8_t)fdc->head);
    track_crc_byte(fdc, &pos, &crc, (uint8_t)sector_id);
    track_crc_byte(fdc, &pos, &crc, 2);
    track_byte(fdc, &pos, (uint8_t)(crc >> 8));
    track_byte(fdc, &pos, (uint8_t)crc);
    for (int i = 0; i < 22; i++) track_byte(fdc, &pos, 0x4E);

    for (int i = 0; i < 12; i++) track_byte(fdc, &pos, 0x00);
    crc = 0xFFFF;
    for (int i = 0; i < 3; i++) track_crc_byte(fdc, &pos, &crc, 0xA1);
    track_crc_byte(fdc, &pos, &crc, 0xFB);
    for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
      track_crc_byte(fdc, &pos, &crc, sector_data[i]);
    }
    track_byte(fdc, &pos, (uint8_t)(crc >> 8));
    track_byte(fdc, &pos, (uint8_t)crc);
    for (int i = 0; i < 35; i++) track_byte(fdc, &pos, 0x4E);
  }
  while (pos < JUK_MFM_TRACK_SIZE) track_byte(fdc, &pos, 0x4E);
  if (pos != JUK_MFM_TRACK_SIZE) {
    fdc->status |= ST_RNF;
    complete_transfer(fdc);
    return;
  }

  fdc->buffer_pos = 0;
  fdc->buffer_len = pos;
  fdc->read_track_transfer = 1;
  fdc->track_waiting_index = 1;
  fdc->status |= ST_BUSY;
  fdc->drq_ticks = 0;
}


static void accept_write_byte(juku_fdc* fdc, uint8_t data) {
  if (!fdc->write_transfer || fdc->buffer_pos >= fdc->buffer_len) return;
  if (fdc->write_sector_lead_pending) {
    fdc->write_sector_preload = data;
    fdc->write_sector_preloaded = 1;
    fdc->write_first_byte_pending = 0;
    fdc->status &= (uint8_t)~ST_DRQ;
    fdc->drq_ticks = 0;
    return;
  }
  fdc->write_first_byte_pending = 0;
  fdc->drq_ticks = 0;
  fdc->buffer[fdc->buffer_pos++] = data;
  if (fdc->buffer_pos < fdc->buffer_len) return;
  int rc = juk_disk_write_sector(
      fdc->disk, fdc->physical_track, fdc->head, fdc->sector, fdc->buffer);
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
  if (juk_disk_offset(fdc->disk, fdc->physical_track, fdc->head, fdc->sector) < 0) {
    complete_transfer(fdc);
    fdc->status |= ST_RNF;
    return;
  }
  arm_write_sector_record(fdc);
}


static uint8_t write_track_decoded_byte(uint8_t data) {
  if (data == 0xF5) return 0xA1;
  if (data == 0xF6) return 0xC2;
  return data;
}


static void finish_write_track_sector(juku_fdc* fdc) {
  if (fdc->write_track_pending_sector < 1 ||
      fdc->write_track_pending_sector > JUK_SECTORS_PER_TRACK) {
    fdc->write_track_format_error = 1;
    return;
  }
  if (juk_disk_write_sector(
          fdc->disk, fdc->physical_track, fdc->head,
          fdc->write_track_pending_sector, fdc->buffer) != 0) {
    fdc->status |= ST_WRITE_PROTECT;
    fdc->write_track_format_error = 1;
    return;
  }
  const uint16_t sector_bit = (uint16_t)1u << (fdc->write_track_pending_sector - 1);
  if (fdc->write_track_seen & sector_bit) fdc->write_track_format_error = 1;
  fdc->write_track_seen |= sector_bit;
  fdc->write_track_pending_sector = 0;
}


static void accept_write_track_byte(juku_fdc* fdc, uint8_t data) {
  if (!fdc->write_track_transfer) return;

  // Write Track raises DRQ with the command so software can preload the Data
  // Register, but consumes that byte only at the next rising index edge.
  if (fdc->track_waiting_index) {
    fdc->write_track_preload = data;
    fdc->write_track_preloaded = 1;
    fdc->write_first_byte_pending = 0;
    fdc->status &= (uint8_t)~ST_DRQ;
    fdc->drq_ticks = 0;
    return;
  }

  fdc->write_first_byte_pending = 0;
  fdc->drq_ticks = 0;

  fdc->write_track_output_pos += data == 0xF7 ? 2u : 1u;
  const uint8_t decoded = write_track_decoded_byte(data);

  switch (fdc->write_track_state) {
    case WT_ID:
      if (data == 0xF7) {
        fdc->write_track_format_error = 1;
        fdc->write_track_state = WT_SCAN;
        fdc->write_track_field_pos = 0;
      } else {
        fdc->write_track_id[fdc->write_track_field_pos++] = decoded;
        if (fdc->write_track_field_pos == 4) {
          fdc->write_track_state = WT_ID_CRC;
        }
      }
      break;

    case WT_ID_CRC:
      if (data == 0xF7 &&
          fdc->write_track_id[0] == fdc->physical_track &&
          fdc->write_track_id[1] == (uint8_t)fdc->head &&
          fdc->write_track_id[2] >= 1 &&
          fdc->write_track_id[2] <= JUK_SECTORS_PER_TRACK &&
          fdc->write_track_id[3] == 2) {
        fdc->write_track_pending_sector = fdc->write_track_id[2];
      } else {
        fdc->write_track_format_error = 1;
        fdc->write_track_pending_sector = 0;
      }
      fdc->write_track_state = WT_SCAN;
      fdc->write_track_field_pos = 0;
      break;

    case WT_DATA:
      if (data == 0xF7) {
        fdc->write_track_format_error = 1;
        fdc->write_track_state = WT_SCAN;
        fdc->write_track_field_pos = 0;
      } else {
        fdc->buffer[fdc->write_track_field_pos++] = decoded;
        if (fdc->write_track_field_pos == JUK_SECTOR_SIZE) {
          fdc->write_track_state = WT_DATA_CRC;
        }
      }
      break;

    case WT_DATA_CRC:
      if (data == 0xF7) finish_write_track_sector(fdc);
      else fdc->write_track_format_error = 1;
      fdc->write_track_state = WT_SCAN;
      fdc->write_track_field_pos = 0;
      break;

    default:
      if (data == 0xF5) {
        fdc->write_track_field_pos++;
      } else {
        const unsigned sync_count = fdc->write_track_field_pos;
        fdc->write_track_field_pos = 0;
        if (sync_count >= 3 && data == 0xFE) {
          fdc->write_track_state = WT_ID;
        } else if (sync_count >= 3 && data == 0xFB &&
                   fdc->write_track_pending_sector != 0) {
          fdc->write_track_state = WT_DATA;
        } else if (sync_count >= 3 && data == 0xF8) {
          // The sector-only backend cannot preserve a deleted-data mark.
          fdc->write_track_format_error = 1;
          fdc->write_track_pending_sector = 0;
        }
      }
      break;
  }

  if (fdc->write_track_output_pos >= JUK_MFM_TRACK_SIZE) {
    if (fdc->write_track_output_pos != JUK_MFM_TRACK_SIZE ||
        fdc->write_track_state != WT_SCAN ||
        fdc->write_track_seen != 0x03FF ||
        fdc->write_track_format_error) {
      fdc->status |= ST_WRITE_FAULT;
    }
    complete_transfer(fdc);
  }
}


static void begin_write_track(juku_fdc* fdc) {
  clear_transfer(fdc);
  fdc->status_type_i = 0;
  fdc->head_loaded = 1;
  fdc->status &= (uint8_t)~(
      ST_TRACK0_LOST | ST_CRC | ST_RNF | ST_WRITE_FAULT | ST_WRITE_PROTECT | ST_NOT_READY);
  if (!fdc->ready_line || !fdc->disk || !fdc->disk->fp || !fdc->motor_on) {
    fdc->status |= ST_NOT_READY;
    complete_transfer(fdc);
    return;
  }
  if (!fdc->disk->writable) {
    fdc->status |= ST_WRITE_PROTECT;
    complete_transfer(fdc);
    return;
  }
  if (fdc->physical_track >= JUK_TRACKS || fdc->head < 0 || fdc->head >= fdc->disk->heads) {
    fdc->status |= ST_RNF;
    complete_transfer(fdc);
    return;
  }
  fdc->write_track_transfer = 1;
  fdc->track_waiting_index = 1;
  fdc->write_first_byte_pending = 1;
  fdc->write_track_state = WT_SCAN;
  fdc->write_track_pending_sector = 0;
  fdc->status |= ST_BUSY | ST_DRQ;
  fdc->drq_ticks = 0;
}


static void start_type_ii_iii(juku_fdc* fdc, uint8_t command) {
  if (is_read_sector(command)) begin_read_sector(fdc, command);
  else if (is_write_sector(command)) begin_write_sector(fdc, command);
  else if (is_read_address(command)) begin_read_address(fdc);
  else if (is_read_track(command)) begin_read_track(fdc);
  else if (is_write_track(command)) begin_write_track(fdc);
}


static void begin_type_ii_iii(juku_fdc* fdc, uint8_t command) {
  const int write_command = is_write_sector(command) || is_write_track(command);
  if (!(command & 0x04) || !fdc->ready_line || !fdc->disk || !fdc->disk->fp ||
      !fdc->motor_on ||
      (write_command && !fdc->disk->writable)) {
    start_type_ii_iii(fdc, command);
    return;
  }
  clear_transfer(fdc);
  fdc->status_type_i = 0;
  fdc->head_loaded = 1;
  fdc->status &= (uint8_t)~(
      ST_TRACK0_LOST | ST_CRC | ST_RNF | ST_WRITE_FAULT | ST_WRITE_PROTECT | ST_NOT_READY);
  fdc->command_delay_pending = 1;
  fdc->command_delay_ticks = 30000;  // E=1: 15 ms at the nominal 2 MHz clock
  fdc->command_delay_command = command;
  fdc->status |= ST_BUSY;
}


static void advance_read_byte(juku_fdc* fdc) {
  fdc->buffer_pos++;
  fdc->drq_ticks = 0;
  if (fdc->buffer_pos < fdc->buffer_len) return;

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


static void miss_drq_byte(juku_fdc* fdc) {
  if (!(fdc->status & ST_BUSY) || !(fdc->status & ST_DRQ)) return;
  fdc->status |= ST_TRACK0_LOST;  // Type-II/III meaning: LOST DATA
  fdc->drq_ticks = 0;

  if (fdc->write_transfer) {
    if (fdc->write_first_byte_pending) {
      complete_transfer(fdc);
    } else {
      accept_write_byte(fdc, 0x00);
    }
  } else if (fdc->write_track_transfer) {
    if (fdc->write_first_byte_pending) {
      complete_transfer(fdc);
    } else {
      accept_write_track_byte(fdc, 0x00);
    }
  } else if (fdc->buffer_pos < fdc->buffer_len) {
    // The next assembled byte overwrites the unserviced Data Register.  The
    // byte-level backend represents that by discarding the current byte.
    advance_read_byte(fdc);
  }
}


void juku_fdc_tick(juku_fdc* fdc, unsigned ticks) {
  while (ticks) {
    if (fdc->type_i_pending) {
      if (ticks < fdc->type_i_ticks) {
        fdc->type_i_ticks -= ticks;
        return;
      }
      ticks -= fdc->type_i_ticks;
      fdc->type_i_ticks = 0;
      if (fdc->type_i_settling) {
        complete_type_i(fdc);
      } else if (fdc->type_i_steps_remaining) {
        type_i_step_once(fdc);
        fdc->type_i_steps_remaining--;
        fdc->type_i_ticks = fdc->type_i_rate_ticks;
      } else {
        finish_type_i_motion(fdc);
      }
    } else if (fdc->command_delay_pending) {
      if (ticks < fdc->command_delay_ticks) {
        fdc->command_delay_ticks -= ticks;
        return;
      }
      ticks -= fdc->command_delay_ticks;
      fdc->command_delay_ticks = 0;
      fdc->command_delay_pending = 0;
      start_type_ii_iii(fdc, fdc->command_delay_command);
    } else if (fdc->write_sector_lead_pending) {
      if (ticks < fdc->write_sector_lead_ticks) {
        fdc->write_sector_lead_ticks -= ticks;
        return;
      }
      ticks -= fdc->write_sector_lead_ticks;
      fdc->write_sector_lead_ticks = 0;
      if (!fdc->write_sector_preloaded) {
        fdc->write_sector_lead_pending = 0;
        fdc->status |= ST_TRACK0_LOST;
        complete_transfer(fdc);
      } else {
        const uint8_t first_byte = fdc->write_sector_preload;
        fdc->write_sector_lead_pending = 0;
        fdc->status |= ST_DRQ;
        accept_write_byte(fdc, first_byte);
      }
    } else if (!fdc->track_waiting_index &&
               (fdc->status & (ST_BUSY | ST_DRQ)) == (ST_BUSY | ST_DRQ)) {
      const unsigned remaining = DRQ_BYTE_TICKS - fdc->drq_ticks;
      if (ticks < remaining) {
        fdc->drq_ticks += ticks;
        return;
      }
      ticks -= remaining;
      miss_drq_byte(fdc);
    } else {
      return;
    }
  }
}


void juku_fdc_init(juku_fdc* fdc, juk_disk* disk) {
  memset(fdc, 0, sizeof(*fdc));
  fdc->disk = disk;
  fdc->enabled = disk && disk->fp;
  fdc->step_dir_in = 1;
  fdc->sector = 1;
  fdc->status_type_i = 1;
  fdc->ready_line = 1;
  fdc->status = ST_NOT_READY;
}


void juku_fdc_portc(juku_fdc* fdc, uint8_t portc) {
  fdc->motor_on = (portc >> 2) & 1;
  fdc->head = (portc >> 6) & 1;
  fdc->drive = (portc >> 5) & 1;
  update_not_ready(fdc);
}


void juku_fdc_ready(juku_fdc* fdc, int ready) {
  ready = ready != 0;
  if (!fdc->ready_line && ready && (fdc->force_interrupt_mask & 0x01)) {
    fdc->intrq = 1;
  }
  if (fdc->ready_line && !ready && (fdc->force_interrupt_mask & 0x02)) {
    fdc->intrq = 1;
  }
  fdc->ready_line = ready;
  update_not_ready(fdc);
}


void juku_fdc_index(juku_fdc* fdc, int index) {
  index = index != 0;
  if (!fdc->index_line && index) {
    const int started_track = fdc->track_waiting_index;
    const int searched_side = fdc->side_compare_pending;
    const int searched_id = fdc->id_search_pending;
    if (fdc->force_interrupt_mask & 0x04) fdc->intrq = 1;
    if (fdc->track_waiting_index) {
      fdc->track_waiting_index = 0;
      if (fdc->write_track_transfer) {
        if (!fdc->write_track_preloaded) {
          fdc->status |= ST_TRACK0_LOST;
          complete_transfer(fdc);
        } else {
          const uint8_t first_byte = fdc->write_track_preload;
          fdc->status |= ST_DRQ;
          accept_write_track_byte(fdc, first_byte);
        }
      } else if (fdc->read_track_transfer) {
        fdc->status |= ST_DRQ;
        fdc->drq_ticks = 0;
      }
    } else if (fdc->side_compare_pending) {
      if (++fdc->side_compare_index_pulses >= 5) {
        fdc->status |= ST_RNF;
        complete_transfer(fdc);
      }
    } else if (fdc->id_search_pending) {
      if (++fdc->id_search_index_pulses >= 4) {
        fdc->status |= ST_RNF;
        complete_transfer(fdc);
      }
    }
    if (!started_track && !searched_side && !searched_id &&
        !(fdc->status & ST_BUSY) && fdc->head_loaded) {
      if (++fdc->idle_index_pulses >= 15) {
        fdc->head_loaded = 0;
        fdc->idle_index_pulses = 0;
      }
    }
  }
  fdc->index_line = index;
}


uint8_t juku_fdc_read(juku_fdc* fdc, uint8_t reg) {
  switch (reg & 3) {
    case 0: {
      uint8_t status = fdc->status;
      if (fdc->status_type_i) {
        status &= (uint8_t)~(ST_WRITE_PROTECT | ST_WRITE_FAULT | ST_TRACK0_LOST | ST_DRQ);
        if (fdc->disk && fdc->disk->fp && !fdc->disk->writable) status |= ST_WRITE_PROTECT;
        if (fdc->head_loaded) status |= ST_WRITE_FAULT;
        if (fdc->physical_track == 0) status |= ST_TRACK0_LOST;
        if (fdc->index_line) status |= ST_DRQ;
      }
      if (!(fdc->force_interrupt_mask & 0x08)) fdc->intrq = 0;
      return status;
    }
    case 1:
      return fdc->track;
    case 2:
      return fdc->sector;
    default:
      if ((fdc->status & ST_DRQ) && fdc->buffer_pos < fdc->buffer_len) {
        fdc->data = fdc->buffer[fdc->buffer_pos];
        advance_read_byte(fdc);
        return fdc->data;
      }
      fdc->status &= (uint8_t)~ST_DRQ;
      return fdc->data;
  }
}


void juku_fdc_write(juku_fdc* fdc, uint8_t reg, uint8_t data) {
  switch (reg & 3) {
    case 0: {
      const int was_busy = (fdc->status & ST_BUSY) != 0;
      fdc->command = data;
      if ((data & 0xF0) != 0xD0 || was_busy) fdc->idle_index_pulses = 0;
      fdc->intrq = 0;
      fdc->force_interrupt_mask = 0;
      if (is_type_i(data)) begin_type_i(fdc, data);
      else if ((data & 0xF0) == 0xD0) {
        clear_transfer(fdc);
        if (!was_busy) fdc->status_type_i = 1;
        fdc->force_interrupt_mask = data & 0x0F;
        fdc->intrq = (data & 0x08) != 0;
      }
      else if (is_type_ii_iii(data)) begin_type_ii_iii(fdc, data);
      else {
        fdc->status_type_i = 0;
        fdc->head_loaded = 1;
        fdc->status &= (uint8_t)~(ST_RNF | ST_DRQ);
        fdc->status |= ST_BUSY;
      }
      break;
    }
    case 1:
      fdc->track = data;
      break;
    case 2:
      fdc->sector = data;
      break;
    default:
      fdc->data = data;
      if (fdc->write_track_transfer) accept_write_track_byte(fdc, data);
      else accept_write_byte(fdc, data);
      break;
  }
}
