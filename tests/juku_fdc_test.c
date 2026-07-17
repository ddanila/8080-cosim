#define _POSIX_C_SOURCE 200809L

#include "../cosim/juku_fdc.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>


enum {
  ST_BUSY = 0x01,
  ST_DRQ = 0x02,
  ST_TRACK0 = 0x04,
  ST_LOST_DATA = 0x04,
  ST_RNF = 0x10,
  ST_HEAD_LOADED = 0x20,
  ST_RECORD_TYPE = 0x20,
  ST_WRITE_FAULT = 0x20,
  ST_WRITE_PROTECT = 0x40,
  ST_NOT_READY = 0x80,
};


static void fill_sector(uint8_t buf[JUK_SECTOR_SIZE], int track, int head, int sector) {
  memset(buf, 0, JUK_SECTOR_SIZE);
  buf[0] = (uint8_t)track;
  buf[1] = (uint8_t)head;
  buf[2] = (uint8_t)sector;
  for (int i = 3; i < JUK_SECTOR_SIZE; i++) {
    buf[i] = (uint8_t)(track + (head << 5) + sector + i);
  }
}


static uint16_t test_crc_byte(uint16_t crc, uint8_t data) {
  crc ^= (uint16_t)data << 8;
  for (int bit = 0; bit < 8; bit++) {
    crc = (uint16_t)((crc << 1) ^ ((crc & 0x8000) ? 0x1021 : 0));
  }
  return crc;
}


static void build_expected_track(uint8_t out[JUK_MFM_TRACK_SIZE], int track, int head) {
  unsigned pos = 0;
  for (int i = 0; i < 32; i++) out[pos++] = 0x4E;
  for (int sector = 1; sector <= JUK_SECTORS_PER_TRACK; sector++) {
    uint8_t data[JUK_SECTOR_SIZE];
    fill_sector(data, track, head, sector);
    for (int i = 0; i < 12; i++) out[pos++] = 0x00;
    uint16_t crc = 0xFFFF;
    for (int i = 0; i < 3; i++) {
      out[pos++] = 0xA1;
      crc = test_crc_byte(crc, 0xA1);
    }
    const uint8_t id[] = {0xFE, (uint8_t)track, (uint8_t)head, (uint8_t)sector, 2};
    for (size_t i = 0; i < sizeof(id); i++) {
      out[pos++] = id[i];
      crc = test_crc_byte(crc, id[i]);
    }
    out[pos++] = (uint8_t)(crc >> 8);
    out[pos++] = (uint8_t)crc;
    for (int i = 0; i < 22; i++) out[pos++] = 0x4E;
    for (int i = 0; i < 12; i++) out[pos++] = 0x00;
    crc = 0xFFFF;
    for (int i = 0; i < 3; i++) {
      out[pos++] = 0xA1;
      crc = test_crc_byte(crc, 0xA1);
    }
    out[pos++] = 0xFB;
    crc = test_crc_byte(crc, 0xFB);
    for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
      out[pos++] = data[i];
      crc = test_crc_byte(crc, data[i]);
    }
    out[pos++] = (uint8_t)(crc >> 8);
    out[pos++] = (uint8_t)crc;
    for (int i = 0; i < 35; i++) out[pos++] = 0x4E;
  }
  while (pos < JUK_MFM_TRACK_SIZE) out[pos++] = 0x4E;
}


static void append_format_byte(
    uint8_t out[JUK_MFM_TRACK_SIZE], size_t* input_pos,
    size_t* output_pos, uint8_t value) {
  out[(*input_pos)++] = value;
  *output_pos += value == 0xF7 ? 2u : 1u;
}


static size_t build_format_stream(
    uint8_t out[JUK_MFM_TRACK_SIZE], int track, int head,
    int deleted_sector, size_t* first_sector_end) {
  size_t input_pos = 0;
  size_t output_pos = 0;
  for (int i = 0; i < 32; i++) {
    append_format_byte(out, &input_pos, &output_pos, 0x4E);
  }
  for (int sector = 1; sector <= JUK_SECTORS_PER_TRACK; sector++) {
    for (int i = 0; i < 12; i++) append_format_byte(out, &input_pos, &output_pos, 0x00);
    for (int i = 0; i < 3; i++) append_format_byte(out, &input_pos, &output_pos, 0xF5);
    const uint8_t id[] = {0xFE, (uint8_t)track, (uint8_t)head, (uint8_t)sector, 2, 0xF7};
    for (size_t i = 0; i < sizeof(id); i++) {
      append_format_byte(out, &input_pos, &output_pos, id[i]);
    }
    for (int i = 0; i < 22; i++) append_format_byte(out, &input_pos, &output_pos, 0x4E);
    for (int i = 0; i < 12; i++) append_format_byte(out, &input_pos, &output_pos, 0x00);
    for (int i = 0; i < 3; i++) append_format_byte(out, &input_pos, &output_pos, 0xF5);
    append_format_byte(
        out, &input_pos, &output_pos, sector == deleted_sector ? 0xF8 : 0xFB);
    for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
      append_format_byte(out, &input_pos, &output_pos, (uint8_t)(0x30 + sector));
    }
    append_format_byte(out, &input_pos, &output_pos, 0xF7);
    if (sector == 1 && first_sector_end) *first_sector_end = input_pos;
    for (int i = 0; i < 35; i++) append_format_byte(out, &input_pos, &output_pos, 0x4E);
  }
  while (output_pos < JUK_MFM_TRACK_SIZE) {
    append_format_byte(out, &input_pos, &output_pos, 0x4E);
  }
  return output_pos == JUK_MFM_TRACK_SIZE ? input_pos : 0;
}


static int write_image(const char* path) {
  FILE* fp = fopen(path, "wb");
  if (!fp) {
    perror(path);
    return 1;
  }
  uint8_t buf[JUK_SECTOR_SIZE];
  for (int track = 0; track < JUK_TRACKS; track++) {
    for (int head = 0; head < 2; head++) {
      for (int sector = 1; sector <= JUK_SECTORS_PER_TRACK; sector++) {
        fill_sector(buf, track, head, sector);
        if (fwrite(buf, 1, sizeof(buf), fp) != sizeof(buf)) {
          perror("fwrite");
          fclose(fp);
          return 1;
        }
      }
    }
  }
  if (fclose(fp) != 0) {
    perror("fclose");
    return 1;
  }
  return 0;
}


static int expect_status(juku_fdc* fdc, uint8_t mask, uint8_t value, const char* label) {
  uint8_t status = juku_fdc_read(fdc, 0);
  if ((status & mask) != value) {
    fprintf(stderr, "%s: status 0x%02X mask 0x%02X expected 0x%02X\n", label, status, mask, value);
    return 1;
  }
  return 0;
}


static int expect_intrq(const juku_fdc* fdc, int value, const char* label) {
  if (fdc->intrq != value) {
    fprintf(stderr, "%s: INTRQ %d expected %d\n", label, fdc->intrq, value);
    return 1;
  }
  return 0;
}


static void seek_track(juku_fdc* fdc, uint8_t track) {
  juku_fdc_write(fdc, 3, track);
  juku_fdc_write(fdc, 0, 0x10);
  juku_fdc_tick(fdc, 10000000);
}


static void pulse_index(juku_fdc* fdc) {
  juku_fdc_index(fdc, 0);
  juku_fdc_index(fdc, 1);
  juku_fdc_index(fdc, 0);
}


int main(void) {
  char dir[] = "/tmp/juku-fdc-test.XXXXXX";
  if (!mkdtemp(dir)) {
    perror("mkdtemp");
    return 1;
  }
  char path[256];
  snprintf(path, sizeof(path), "%s/disk.juk", dir);

  int fail = write_image(path);
  juk_disk disk;
  if (juk_disk_open(&disk, path) != 0) {
    fprintf(stderr, "failed to open synthetic disk\n");
    fail = 1;
  }

  juku_fdc fdc;
  juku_fdc_init(&fdc, &disk);
  juku_fdc_portc(&fdc, 0x04);  // motor on, drive 0, side 0
  juku_fdc_write(&fdc, 1, 22);
  juku_fdc_write(&fdc, 0, 0x02);  // restore, as ROMBIOS issues before reading
  fail |= expect_intrq(&fdc, 1, "restore completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_TRACK0 | ST_WRITE_PROTECT | ST_NOT_READY,
                        ST_TRACK0 | ST_WRITE_PROTECT, "after restore command");
  fail |= expect_intrq(&fdc, 0, "restore status acknowledgement");
  if (juku_fdc_read(&fdc, 1) != 0) {
    fprintf(stderr, "restore did not return to track 0\n");
    fail = 1;
  }

  juku_fdc_tr00(&fdc, 1);
  fail |= expect_status(&fdc, ST_TRACK0, 0, "inactive TR00 status");
  juku_fdc_write(&fdc, 0, 0x00);
  juku_fdc_tick(&fdc, 255u * 6000u);
  fail |= expect_intrq(&fdc, 1, "restore 255-step completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_RNF | ST_TRACK0,
                        ST_RNF, "restore stuck-TR00 seek error");

  fdc.track = 5;
  fdc.physical_track = 5;
  juku_fdc_write(&fdc, 0, 0x00);
  if (fdc.physical_track != 4 || fdc.type_i_steps_remaining != 254) {
    fprintf(stderr, "restore did not issue its first TR00-seeking step\n");
    fail = 1;
  }
  juku_fdc_tick(&fdc, 5999);
  juku_fdc_tr00(&fdc, 0);
  juku_fdc_tick(&fdc, 1);
  fail |= expect_intrq(&fdc, 1, "restore TR00 assertion completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_RNF | ST_TRACK0,
                        ST_TRACK0, "restore TR00 assertion status");
  if (fdc.track != 0 || fdc.physical_track != 0) {
    fprintf(stderr, "restore TR00 assertion did not zero track state\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 0, 0x08);  // restore with head-load flag
  fail |= expect_status(&fdc, ST_TRACK0 | ST_HEAD_LOADED,
                        ST_TRACK0 | ST_HEAD_LOADED, "restore head-load status");
  for (int pulse = 0; pulse < 7; pulse++) {
    juku_fdc_index(&fdc, 0);
    juku_fdc_index(&fdc, 1);
  }
  juku_fdc_write(&fdc, 0, 0xD4);  // arming an idle event does not leave idle
  for (int pulse = 0; pulse < 7; pulse++) {
    juku_fdc_index(&fdc, 0);
    juku_fdc_index(&fdc, 1);
  }
  if (!fdc.head_loaded || fdc.idle_index_pulses != 14) {
    fprintf(stderr, "head unloaded before 15 idle index pulses\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 2, 1);
  juku_fdc_write(&fdc, 0, 0x80);  // a new busy command resets the idle count
  for (int pulse = 0; pulse < 15; pulse++) {
    juku_fdc_index(&fdc, 0);
    juku_fdc_index(&fdc, 1);
  }
  if (!fdc.head_loaded || fdc.idle_index_pulses != 0) {
    fprintf(stderr, "busy index pulses affected head unload state\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0xD0);
  for (int pulse = 0; pulse < 14; pulse++) {
    juku_fdc_index(&fdc, 0);
    juku_fdc_index(&fdc, 1);
  }
  if (!fdc.head_loaded) {
    fprintf(stderr, "head unloaded before 15 post-command idle index pulses\n");
    fail = 1;
  }
  juku_fdc_index(&fdc, 0);
  juku_fdc_index(&fdc, 1);
  if (fdc.head_loaded || fdc.idle_index_pulses != 0) {
    fprintf(stderr, "head did not unload on the 15th idle index pulse\n");
    fail = 1;
  }
  juku_fdc_index(&fdc, 0);
  juku_fdc_write(&fdc, 0, 0x08);
  juku_fdc_write(&fdc, 0, 0x00);  // restore explicitly unloads the head
  fail |= expect_status(&fdc, ST_TRACK0 | ST_HEAD_LOADED,
                        ST_TRACK0, "restore head-unload status");

  const unsigned type_i_rates[4] = {6000, 12000, 20000, 30000};
  for (unsigned rate = 0; rate < 4; rate++) {
    juku_fdc_write(&fdc, 0, (uint8_t)rate);  // zero-step restore exposes r1:r0
    if (fdc.type_i_rate_ticks != type_i_rates[rate]) {
      fprintf(stderr, "Type-I rate %u mapped to %u ticks, expected %u\n",
              rate, fdc.type_i_rate_ticks, type_i_rates[rate]);
      fail = 1;
    }
  }

  juku_fdc_write(&fdc, 3, 12);
  juku_fdc_write(&fdc, 0, 0x12);  // seek to data register
  fail |= expect_status(&fdc, ST_BUSY, ST_BUSY, "seek timing begins busy");
  juku_fdc_tick(&fdc, 10000000);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_NOT_READY, 0, "after seek command");
  if (juku_fdc_read(&fdc, 1) != 12) {
    fprintf(stderr, "seek did not copy data register to track\n");
    fail = 1;
  }

  juku_fdc_hlt(&fdc, 0);
  juku_fdc_write(&fdc, 0, 0x14);  // zero-step seek, verify after settle and HLT
  juku_fdc_tick(&fdc, 30000);
  fail |= expect_status(&fdc, ST_BUSY | ST_RNF | ST_HEAD_LOADED, ST_BUSY,
                        "Type-I verify waits for HLT");
  if (!fdc.type_i_hlt_pending || fdc.intrq) {
    fprintf(stderr, "Type-I verify did not enter the HLT wait\n");
    fail = 1;
  }
  juku_fdc_hlt(&fdc, 1);
  fail |= expect_intrq(&fdc, 1, "Type-I verify HLT completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_RNF | ST_HEAD_LOADED, ST_HEAD_LOADED,
                        "matching Type-I verify after HLT");

  juku_fdc_write(&fdc, 0, 0x44);  // step in, no register update, verify
  fail |= expect_status(&fdc, ST_BUSY, ST_BUSY, "step/verify timing begins busy");
  if (fdc.physical_track != 13 || fdc.type_i_settling) {
    fprintf(stderr, "step pulse/motion was not issued before its rate delay\n");
    fail = 1;
  }
  juku_fdc_tick(&fdc, 5999);
  if (fdc.physical_track != 13 || fdc.type_i_settling || !(fdc.status & ST_BUSY)) {
    fprintf(stderr, "3 ms step delay completed before 6000 controller ticks\n");
    fail = 1;
  }
  juku_fdc_tick(&fdc, 1);
  if (fdc.physical_track != 13 || !fdc.type_i_settling || !(fdc.status & ST_BUSY)) {
    fprintf(stderr, "step did not enter 15 ms verify settle at tick 6000\n");
    fail = 1;
  }
  juku_fdc_tick(&fdc, 29999);
  fail |= expect_status(&fdc, ST_BUSY | ST_RNF, ST_BUSY,
                        "verify before 15 ms settle boundary");
  juku_fdc_tick(&fdc, 1);
  if (fdc.physical_track != 13 || juku_fdc_read(&fdc, 1) != 12) {
    fprintf(stderr, "verified no-update step did not separate physical/register tracks\n");
    fail = 1;
  }
  fail |= expect_intrq(&fdc, 1, "Type-I valid-ID mismatch completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_RNF | ST_HEAD_LOADED,
                        ST_RNF | ST_HEAD_LOADED, "Type-I verify seek error");
  seek_track(&fdc, 14);
  if (fdc.physical_track != 15 || juku_fdc_read(&fdc, 1) != 14) {
    fprintf(stderr, "seek did not preserve the physical/register track offset\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 2, 1);
  juku_fdc_write(&fdc, 0, 0x80);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF,
                        ST_BUSY, "read-sector missing-ID search");
  for (int i = 0; i < 3; i++) pulse_index(&fdc);
  fail |= expect_intrq(&fdc, 0, "missing-ID search before fourth revolution");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF,
                        ST_BUSY, "missing-ID search before fourth-revolution status");
  pulse_index(&fdc);
  fail |= expect_intrq(&fdc, 1, "missing-ID fourth-revolution completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF,
                        ST_RNF, "read-sector missing-ID fourth-revolution RNF");

  seek_track(&fdc, 80);
  juku_fdc_write(&fdc, 0, 0x14);
  juku_fdc_tick(&fdc, 30000);
  fail |= expect_status(&fdc, ST_BUSY | ST_RNF, ST_BUSY,
                        "Type-I missing-ID verify search");
  for (int i = 0; i < 3; i++) pulse_index(&fdc);
  fail |= expect_intrq(&fdc, 0, "Type-I missing-ID before fourth revolution");
  pulse_index(&fdc);
  fail |= expect_intrq(&fdc, 1, "Type-I missing-ID fourth-revolution completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_RNF, ST_RNF,
                        "Type-I missing-ID seek error");
  juku_fdc_write(&fdc, 0, 0x00);  // RESTORE is what physically recalibrates track zero
  juku_fdc_tick(&fdc, 10000000);
  seek_track(&fdc, 12);

  juku_fdc_write(&fdc, 0, 0x50);  // step in and update the track register
  juku_fdc_tick(&fdc, 10000000);
  if (juku_fdc_read(&fdc, 1) != 13) {
    fprintf(stderr, "step-in/update did not increment track\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0x40);  // step in without track-register update
  juku_fdc_tick(&fdc, 10000000);
  if (juku_fdc_read(&fdc, 1) != 13) {
    fprintf(stderr, "step-in/no-update changed track\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0x70);  // step out and update the track register
  juku_fdc_tick(&fdc, 10000000);
  if (juku_fdc_read(&fdc, 1) != 12) {
    fprintf(stderr, "step-out/update did not decrement track\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0x30);  // generic step reuses the prior direction
  juku_fdc_tick(&fdc, 10000000);
  if (juku_fdc_read(&fdc, 1) != 11) {
    fprintf(stderr, "step/update did not preserve the step-out direction\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 0, 0x00);
  juku_fdc_tick(&fdc, 10000000);
  juku_fdc_write(&fdc, 3, 4);
  juku_fdc_write(&fdc, 0, 0x10);
  if (fdc.track != 1 || fdc.physical_track != 1 || !(fdc.status & ST_BUSY)) {
    fprintf(stderr, "timed seek did not issue its first step immediately\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0xD0);
  if (fdc.track != 1 || fdc.physical_track != 1 || (fdc.status & ST_BUSY) || fdc.intrq) {
    fprintf(stderr, "D0 did not silently retain partial Type-I motion\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0x00);
  juku_fdc_tick(&fdc, 10000000);
  seek_track(&fdc, 12);
  juku_fdc_hlt(&fdc, 0);
  juku_fdc_write(&fdc, 0, 0xC0);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY,
                        "read-address waits for HLT");
  if (!fdc.command_hlt_pending || fdc.intrq) {
    fprintf(stderr, "Type-III command did not enter the HLT wait\n");
    fail = 1;
  }
  juku_fdc_hlt(&fdc, 1);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ,
                        "read-address starts after HLT");
  juku_fdc_write(&fdc, 0, 0xD0);

  juku_fdc_hlt(&fdc, 0);
  juku_fdc_write(&fdc, 2, 9);
  juku_fdc_write(&fdc, 0, 0xC4);  // read address, including the valid E flag
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY,
                        "read-address E-delay begins busy");
  juku_fdc_tick(&fdc, 29999);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY,
                        "read-address before 15 ms E-delay boundary");
  juku_fdc_tick(&fdc, 1);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY,
                        "read-address waits for HLT after E-delay");
  if (!fdc.command_hlt_pending) {
    fprintf(stderr, "E-delayed Type-III command skipped the HLT wait\n");
    fail = 1;
  }
  juku_fdc_hlt(&fdc, 1);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ,
                        "read-address after E-delay and HLT");
  static const uint8_t address_id[] = {12, 0, 1, 2, 0xBD, 0xB3};
  for (size_t i = 0; i < sizeof(address_id); i++) {
    uint8_t got = juku_fdc_read(&fdc, 3);
    if (got != address_id[i]) {
      fprintf(stderr, "read-address byte %zu: got 0x%02X want 0x%02X\n", i, got, address_id[i]);
      fail = 1;
    }
    if (i < sizeof(address_id) - 1 && juku_fdc_read(&fdc, 2) != 9) {
      fprintf(stderr, "read-address changed sector register before completion\n");
      fail = 1;
    }
  }
  fail |= expect_intrq(&fdc, 1, "read-address completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after read-address drain");
  fail |= expect_intrq(&fdc, 0, "read-address status acknowledgement");
  if (juku_fdc_read(&fdc, 2) != 12) {
    fprintf(stderr, "read-address did not load track address into sector register\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 2, 7);
  juku_fdc_write(&fdc, 0, 0xE4);  // Read Track, including the valid E flag
  juku_fdc_tick(&fdc, 30000);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY,
                        "read-track waiting for first index");
  const unsigned read_track_pos_before_index = fdc.buffer_pos;
  (void)juku_fdc_read(&fdc, 3);
  if (fdc.buffer_pos != read_track_pos_before_index) {
    fprintf(stderr, "read-track exposed data before the first index edge\n");
    fail = 1;
  }
  pulse_index(&fdc);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ,
                        "read-track started at first index");
  uint8_t expected_track[JUK_MFM_TRACK_SIZE];
  build_expected_track(expected_track, 12, 0);
  for (int i = 0; i < JUK_MFM_TRACK_SIZE; i++) {
    uint8_t got = juku_fdc_read(&fdc, 3);
    if (got != expected_track[i]) {
      fprintf(stderr, "read-track byte %d: got 0x%02X want 0x%02X\n",
              i, got, expected_track[i]);
      fail = 1;
    }
  }
  fail |= expect_intrq(&fdc, 1, "read-track completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF, 0, "after read-track drain");
  fail |= expect_intrq(&fdc, 0, "read-track status acknowledgement");
  if (juku_fdc_read(&fdc, 2) != 7) {
    fprintf(stderr, "read-track changed sector register\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 0, 0xE0);
  pulse_index(&fdc);
  for (int i = 0; i < 100; i++) (void)juku_fdc_read(&fdc, 3);
  juku_fdc_write(&fdc, 0, 0xD0);
  fail |= expect_intrq(&fdc, 0, "forced read-track D0 silence");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after forced read-track abort");

  juku_fdc_write(&fdc, 0, 0xC4);
  juku_fdc_tick(&fdc, 100);
  juku_fdc_write(&fdc, 0, 0xD0);
  juku_fdc_tick(&fdc, 30000);
  fail |= expect_intrq(&fdc, 0, "D0 during E-delay remains silent");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "D0 cancels E-delay");

  juku_fdc_write(&fdc, 2, 7);
  juku_fdc_write(&fdc, 0, 0xC0);
  (void)juku_fdc_read(&fdc, 3);
  (void)juku_fdc_read(&fdc, 3);
  juku_fdc_write(&fdc, 0, 0xD0);  // force interrupt aborts the partial ID field
  fail |= expect_intrq(&fdc, 0, "D0 silent force interrupt");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after forced read-address abort");
  if (juku_fdc_read(&fdc, 2) != 7) {
    fprintf(stderr, "aborted read-address changed sector register\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0xC1);  // reserved low bit is not Read Address
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY, "reserved type-III opcode");
  juku_fdc_write(&fdc, 0, 0xD8);
  fail |= expect_intrq(&fdc, 1, "D8 immediate force interrupt");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after immediate force interrupt");
  fail |= expect_intrq(&fdc, 1, "D8 remains asserted after status read");
  juku_fdc_write(&fdc, 0, 0xD0);
  fail |= expect_intrq(&fdc, 0, "D0 disarms D8 immediate interrupt");

  juku_fdc_ready(&fdc, 0);
  juku_fdc_write(&fdc, 0, 0xD1);
  fail |= expect_intrq(&fdc, 0, "D1 arms without immediate interrupt");
  juku_fdc_ready(&fdc, 1);
  fail |= expect_intrq(&fdc, 1, "D1 not-ready to ready interrupt");
  fail |= expect_status(&fdc, 0, 0, "D1 status acknowledgement");
  fail |= expect_intrq(&fdc, 0, "D1 status read clears interrupt");
  juku_fdc_ready(&fdc, 0);
  juku_fdc_ready(&fdc, 1);
  fail |= expect_intrq(&fdc, 1, "D1 remains armed for another ready transition");
  (void)juku_fdc_read(&fdc, 0);

  juku_fdc_write(&fdc, 0, 0xD2);
  juku_fdc_ready(&fdc, 0);
  fail |= expect_intrq(&fdc, 1, "D2 ready to not-ready interrupt");
  (void)juku_fdc_read(&fdc, 0);
  fail |= expect_intrq(&fdc, 0, "D2 status read clears interrupt");
  juku_fdc_ready(&fdc, 1);
  juku_fdc_ready(&fdc, 0);
  fail |= expect_intrq(&fdc, 1, "D2 remains armed for another not-ready transition");
  (void)juku_fdc_read(&fdc, 0);

  juku_fdc_write(&fdc, 2, 1);
  juku_fdc_write(&fdc, 0, 0x80);
  fail |= expect_intrq(&fdc, 1, "READY-low read-sector completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_NOT_READY, ST_NOT_READY,
                        "READY-low read-sector status");
  fail |= expect_intrq(&fdc, 0, "READY-low read-sector acknowledgement");
  juku_fdc_write(&fdc, 0, 0xC0);
  fail |= expect_intrq(&fdc, 1, "READY-low read-address completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_NOT_READY, ST_NOT_READY,
                        "READY-low read-address status");

  juku_fdc_write(&fdc, 3, 1);
  juku_fdc_write(&fdc, 0, 0x10);
  fail |= expect_status(&fdc, ST_BUSY | ST_NOT_READY, ST_BUSY | ST_NOT_READY,
                        "READY-low Type-I execution");
  juku_fdc_tick(&fdc, 10000000);
  fail |= expect_intrq(&fdc, 1, "READY-low Type-I completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_NOT_READY, ST_NOT_READY,
                        "READY-low Type-I completion status");
  if (juku_fdc_read(&fdc, 1) != 1) {
    fprintf(stderr, "READY-low Type-I seek did not update track register\n");
    fail = 1;
  }
  juku_fdc_ready(&fdc, 1);
  fail |= expect_status(&fdc, ST_NOT_READY, 0, "READY-high status recovery");

  juku_fdc_index(&fdc, 0);
  juku_fdc_write(&fdc, 0, 0xD4);
  fail |= expect_intrq(&fdc, 0, "D4 arms without immediate interrupt");
  juku_fdc_index(&fdc, 1);
  fail |= expect_intrq(&fdc, 1, "D4 index interrupt");
  fail |= expect_status(&fdc, ST_DRQ, ST_DRQ, "D4 Type-I index status");
  juku_fdc_index(&fdc, 0);
  juku_fdc_index(&fdc, 1);
  fail |= expect_intrq(&fdc, 1, "D4 remains armed for another index pulse");
  (void)juku_fdc_read(&fdc, 0);
  juku_fdc_write(&fdc, 0, 0xC1);
  juku_fdc_index(&fdc, 0);
  juku_fdc_index(&fdc, 1);
  fail |= expect_intrq(&fdc, 0, "non-force command disarms D4 index interrupt");
  juku_fdc_write(&fdc, 0, 0xD0);

  seek_track(&fdc, 12);
  juku_fdc_write(&fdc, 2, 4);
  juku_fdc_write(&fdc, 0, 0x80);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ, "after read command");

  uint8_t want[JUK_SECTOR_SIZE];
  fill_sector(want, 12, 0, 4);
  juku_fdc_tick(&fdc, 63);
  fail |= expect_status(&fdc, ST_LOST_DATA, 0, "read before one-byte deadline");
  juku_fdc_tick(&fdc, 1);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_LOST_DATA,
                        ST_BUSY | ST_DRQ | ST_LOST_DATA, "read lost-data deadline");
  if (juku_fdc_read(&fdc, 3) != want[1]) {
    fprintf(stderr, "read lost-data overwrite did not expose byte 1\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0xD0);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_LOST_DATA,
                        ST_LOST_DATA, "read lost-data abort preserves status");

  juku_fdc_write(&fdc, 2, 4);
  juku_fdc_write(&fdc, 0, 0x80);
  for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
    uint8_t got = juku_fdc_read(&fdc, 3);
    if (got != want[i]) {
      fprintf(stderr, "side 0 byte %d: got 0x%02X want 0x%02X\n", i, got, want[i]);
      fail = 1;
      break;
    }
  }
  fail |= expect_intrq(&fdc, 1, "read-sector completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after sector drain");
  fail |= expect_intrq(&fdc, 0, "read-sector status acknowledgement");

  juku_fdc_write(&fdc, 0, 0xFD);  // write track against read-only raw-image shim
  fail |= expect_intrq(&fdc, 1, "write-track rejection completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_WRITE_PROTECT, ST_WRITE_PROTECT, "after write-track command");
  fail |= expect_intrq(&fdc, 0, "write-track status acknowledgement");

  juku_fdc_write(&fdc, 0, 0xA0);  // ROMBIOS write-sector command is also protected by default
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_WRITE_PROTECT, ST_WRITE_PROTECT, "read-only write-sector command");

  juku_fdc_portc(&fdc, 0x44);  // motor on, drive 0, side 1
  seek_track(&fdc, 43);
  juku_fdc_write(&fdc, 2, 7);
  juku_fdc_write(&fdc, 0, 0x80);
  fill_sector(want, 43, 1, 7);
  for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
    uint8_t got = juku_fdc_read(&fdc, 3);
    if (got != want[i]) {
      fprintf(stderr, "side 1 byte %d: got 0x%02X want 0x%02X\n", i, got, want[i]);
      fail = 1;
      break;
    }
  }
  juku_fdc_write(&fdc, 0, 0x82);  // C=1/S=0 mismatches the side-1 ID field
  fail |= expect_intrq(&fdc, 0, "side-compare mismatch search begins silently");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF,
                        ST_BUSY, "side-compare mismatch search");
  for (int i = 0; i < 4; i++) pulse_index(&fdc);
  fail |= expect_intrq(&fdc, 0, "side-compare mismatch before fifth index");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF,
                        ST_BUSY, "side-compare mismatch before fifth index status");
  pulse_index(&fdc);
  fail |= expect_intrq(&fdc, 1, "side-compare mismatch fifth-index completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF,
                        ST_RNF, "side-compare mismatch fifth-index status");

  juku_fdc_portc(&fdc, 0x04);  // motor on, side 0
  seek_track(&fdc, 12);
  juku_fdc_write(&fdc, 2, 9);
  juku_fdc_write(&fdc, 0, 0x92);  // multiple-record read
  for (int record = 9; record <= 10; record++) {
    fill_sector(want, 12, 0, record);
    for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
      uint8_t got = juku_fdc_read(&fdc, 3);
      if (got != want[i]) {
        fprintf(stderr, "multi-read sector %d byte %d: got 0x%02X want 0x%02X\n",
                record, i, got, want[i]);
        fail = 1;
        break;
      }
    }
  }
  fail |= expect_intrq(&fdc, 1, "multi-read end-of-track completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF | ST_WRITE_PROTECT,
                        ST_RNF, "multi-read end of track");
  if (juku_fdc_read(&fdc, 2) != 11) {
    fprintf(stderr, "multi-read did not advance sector register past track end\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 2, 8);
  juku_fdc_write(&fdc, 0, 0x90);
  for (int i = 0; i < JUK_SECTOR_SIZE + 17; i++) (void)juku_fdc_read(&fdc, 3);
  juku_fdc_write(&fdc, 0, 0xD0);
  fail |= expect_intrq(&fdc, 0, "forced multi-read D0 silence");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "forced multi-read abort");
  if (juku_fdc_read(&fdc, 2) != 9) {
    fprintf(stderr, "forced multi-read did not preserve the current sector\n");
    fail = 1;
  }

  juk_disk_close(&disk);
  if (juk_disk_open_writable(&disk, path) != 0) {
    fprintf(stderr, "failed to reopen synthetic disk writable\n");
    fail = 1;
  }
  juku_fdc_init(&fdc, &disk);
  juku_fdc_portc(&fdc, 0x44);  // motor on, side 1
  seek_track(&fdc, 8);
  juku_fdc_write(&fdc, 2, 3);

  juku_fdc_write(&fdc, 2, 11);
  juku_fdc_write(&fdc, 0, 0xAA);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF,
                        ST_BUSY, "write-sector missing-ID search");
  for (int i = 0; i < 3; i++) pulse_index(&fdc);
  fail |= expect_intrq(&fdc, 0, "write missing-ID before fourth revolution");
  pulse_index(&fdc);
  fail |= expect_intrq(&fdc, 1, "write missing-ID fourth-revolution completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF,
                        ST_RNF, "write missing-ID fourth-revolution RNF");
  juku_fdc_write(&fdc, 2, 3);

  uint8_t baseline[JUK_SECTOR_SIZE];
  if (juk_disk_read_sector(&disk, 8, 1, 3, baseline) != 0) {
    fprintf(stderr, "failed to capture write-timeout baseline\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0xAA);
  juku_fdc_tick(&fdc, 1407);
  fail |= expect_intrq(&fdc, 0, "write-sector lead-in before boundary");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_LOST_DATA,
                        ST_BUSY | ST_DRQ, "write-sector lead-in before boundary status");
  if (fdc.buffer_pos != 0) {
    fprintf(stderr, "write-sector lead-in modified buffer before boundary\n");
    fail = 1;
  }
  juku_fdc_tick(&fdc, 1);
  fail |= expect_intrq(&fdc, 1, "first write-byte timeout completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_LOST_DATA,
                        ST_LOST_DATA, "first write-byte timeout status");
  uint8_t after_timeout[JUK_SECTOR_SIZE];
  if (juk_disk_read_sector(&disk, 8, 1, 3, after_timeout) != 0 ||
      memcmp(baseline, after_timeout, sizeof(baseline)) != 0) {
    fprintf(stderr, "first write-byte timeout modified media\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 0, 0xAA);
  juku_fdc_write(&fdc, 3, 0xA5);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY,
                        "write-sector first-byte preload hold");
  juku_fdc_tick(&fdc, 1408);
  juku_fdc_tick(&fdc, 64);  // missed second byte is written as zero
  for (int i = 2; i < JUK_SECTOR_SIZE; i++) juku_fdc_write(&fdc, 3, (uint8_t)i);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_LOST_DATA,
                        ST_LOST_DATA, "subsequent write-byte zero substitution");
  if (juk_disk_read_sector(&disk, 8, 1, 3, after_timeout) != 0 ||
      after_timeout[0] != 0xA5 || after_timeout[1] != 0x00) {
    fprintf(stderr, "write lost-data substitution did not persist A5,00\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 2, 3);
  juku_fdc_write(&fdc, 0, 0xAA);  // C=1/S=1 matches the side-1 ID field
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ, "writable write-sector command");
  juku_fdc_write(&fdc, 3, 0x5A);
  juku_fdc_tick(&fdc, 1408);
  for (int i = 1; i < JUK_SECTOR_SIZE; i++) {
    juku_fdc_write(&fdc, 3, (uint8_t)(0x5A ^ i));
  }
  fail |= expect_intrq(&fdc, 1, "write-sector completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_WRITE_PROTECT, 0, "after writable sector fill");
  juku_fdc_write(&fdc, 0, 0x8A);
  for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
    uint8_t got = juku_fdc_read(&fdc, 3);
    uint8_t expected = (uint8_t)(0x5A ^ i);
    if (got != expected) {
      fprintf(stderr, "write-sector readback byte %d: got 0x%02X want 0x%02X\n", i, got, expected);
      fail = 1;
      break;
    }
  }

  // Write Sector a0 selects F8, and a later Read Sector reports that address
  // mark as RECORD TYPE without changing the payload contract.
  juku_fdc_write(&fdc, 0, 0xAB);  // C=1/S=1, deleted-data address mark
  juku_fdc_write(&fdc, 3, 0xD5);
  juku_fdc_tick(&fdc, 1408);
  for (int i = 1; i < JUK_SECTOR_SIZE; i++) {
    juku_fdc_write(&fdc, 3, (uint8_t)(0xD5 ^ i));
  }
  fail |= expect_status(&fdc, ST_RECORD_TYPE, 0,
                        "deleted write-sector has no write fault");
  juku_fdc_write(&fdc, 0, 0x8A);
  for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
    uint8_t got = juku_fdc_read(&fdc, 3);
    if (got != (uint8_t)(0xD5 ^ i)) {
      fprintf(stderr, "deleted-sector readback byte %d got 0x%02X\n", i, got);
      fail = 1;
      break;
    }
  }
  fail |= expect_status(&fdc, ST_RECORD_TYPE, ST_RECORD_TYPE,
                        "deleted read-sector record type");

  seek_track(&fdc, 8);
  juku_fdc_write(&fdc, 2, 9);
  juku_fdc_write(&fdc, 0, 0xBB);  // C=1/S=1 deleted multiple-record write
  for (int record = 9; record <= 10; record++) {
    juku_fdc_write(&fdc, 3, (uint8_t)(record == 9 ? 0xA0 : 0x50));
    juku_fdc_tick(&fdc, 1408);
    for (int i = 1; i < JUK_SECTOR_SIZE; i++) {
      juku_fdc_write(&fdc, 3, (uint8_t)((record == 9 ? 0xA0 : 0x50) ^ i));
    }
  }
  fail |= expect_intrq(&fdc, 1, "multi-write end-of-track completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_RNF, ST_RNF, "multi-write end of track");
  if (juku_fdc_read(&fdc, 2) != 11) {
    fprintf(stderr, "multi-write did not advance sector register past track end\n");
    fail = 1;
  }
  for (int record = 9; record <= 10; record++) {
    juku_fdc_write(&fdc, 2, (uint8_t)record);
    juku_fdc_write(&fdc, 0, 0x8A);
    for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
      uint8_t got = juku_fdc_read(&fdc, 3);
      uint8_t expected = (uint8_t)((record == 9 ? 0xA0 : 0x50) ^ i);
      if (got != expected) {
        fprintf(stderr, "multi-write readback sector %d byte %d: got 0x%02X want 0x%02X\n",
                record, i, got, expected);
        fail = 1;
        break;
      }
    }
    fail |= expect_status(&fdc, ST_RECORD_TYPE, ST_RECORD_TYPE,
                          "deleted multi-write readback record type");
  }

  uint8_t format_stream[JUK_MFM_TRACK_SIZE];
  size_t first_sector_end = 0;
  size_t format_len = build_format_stream(format_stream, 8, 1, 4, &first_sector_end);
  if (format_len != 6230 || first_sector_end == 0) {
    fprintf(stderr, "write-track fixture length %zu first-sector-end %zu\n",
            format_len, first_sector_end);
    fail = 1;
  }
  seek_track(&fdc, 8);
  juku_fdc_write(&fdc, 2, 10);
  juku_fdc_write(&fdc, 0, 0xF4);
  juku_fdc_tick(&fdc, 100000);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_LOST_DATA,
                        ST_BUSY | ST_DRQ, "write-track preload window before index");
  pulse_index(&fdc);
  fail |= expect_intrq(&fdc, 1, "missing write-track preload at index completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_LOST_DATA,
                        ST_LOST_DATA, "missing write-track preload at index status");

  juku_fdc_write(&fdc, 0, 0xF4);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY,
                        "write-track E-delay begins busy");
  juku_fdc_tick(&fdc, 30000);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ,
                        "writable write-track preload request");
  juku_fdc_write(&fdc, 3, format_stream[0]);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY,
                        "write-track first-byte preload");
  pulse_index(&fdc);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ,
                        "write-track starts at index");
  for (size_t i = 1; i < format_len; i++) juku_fdc_write(&fdc, 3, format_stream[i]);
  fail |= expect_intrq(&fdc, 1, "write-track completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_WRITE_FAULT | ST_WRITE_PROTECT,
                        0, "after writable track format");
  fail |= expect_intrq(&fdc, 0, "write-track status acknowledgement");
  if (juku_fdc_read(&fdc, 2) != 10) {
    fprintf(stderr, "write-track changed sector register\n");
    fail = 1;
  }
  for (int sector = 1; sector <= JUK_SECTORS_PER_TRACK; sector++) {
    uint8_t got[JUK_SECTOR_SIZE];
    if (juk_disk_read_sector(&disk, 8, 1, sector, got) != 0) {
      fprintf(stderr, "write-track direct readback failed for sector %d\n", sector);
      fail = 1;
      continue;
    }
    for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
      if (got[i] != (uint8_t)(0x30 + sector)) {
        fprintf(stderr, "write-track sector %d byte %d got 0x%02X\n", sector, i, got[i]);
        fail = 1;
        break;
      }
    }
  }

  juku_fdc_write(&fdc, 2, 4);
  juku_fdc_write(&fdc, 0, 0x8A);
  for (int i = 0; i < JUK_SECTOR_SIZE; i++) (void)juku_fdc_read(&fdc, 3);
  fail |= expect_status(&fdc, ST_RECORD_TYPE, ST_RECORD_TYPE,
                        "write-track F8 record type");
  juku_fdc_write(&fdc, 0, 0xE0);
  pulse_index(&fdc);
  for (int i = 0; i <= 2432; i++) {
    uint8_t got = juku_fdc_read(&fdc, 3);
    if (i == 1918 && got != 0xF8) {
      fprintf(stderr, "read-track sector-4 deleted mark got 0x%02X\n", got);
      fail = 1;
    } else if (i == 2431 && got != 0xB8) {
      fprintf(stderr, "read-track sector-4 deleted CRC1 got 0x%02X\n", got);
      fail = 1;
    } else if (i == 2432 && got != 0x81) {
      fprintf(stderr, "read-track sector-4 deleted CRC2 got 0x%02X\n", got);
      fail = 1;
    }
  }
  juku_fdc_write(&fdc, 0, 0xD0);

  format_len = build_format_stream(format_stream, 9, 1, 0, &first_sector_end);
  seek_track(&fdc, 9);
  juku_fdc_write(&fdc, 0, 0xF0);
  juku_fdc_write(&fdc, 3, format_stream[0]);
  pulse_index(&fdc);
  for (size_t i = 1; i < first_sector_end; i++) juku_fdc_write(&fdc, 3, format_stream[i]);
  juku_fdc_write(&fdc, 0, 0xD0);
  fail |= expect_intrq(&fdc, 0, "forced write-track D0 silence");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after forced write-track abort");
  uint8_t partial[JUK_SECTOR_SIZE];
  if (juk_disk_read_sector(&disk, 9, 1, 1, partial) != 0) {
    fprintf(stderr, "partial write-track sector 1 readback failed\n");
    fail = 1;
  } else {
    for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
      if (partial[i] != 0x31) {
        fprintf(stderr, "partial write-track sector 1 byte %d got 0x%02X\n", i, partial[i]);
        fail = 1;
        break;
      }
    }
  }
  fill_sector(want, 9, 1, 2);
  if (juk_disk_read_sector(&disk, 9, 1, 2, partial) != 0 ||
      memcmp(partial, want, JUK_SECTOR_SIZE) != 0) {
    fprintf(stderr, "partial write-track modified unfinished sector 2\n");
    fail = 1;
  }

  fill_sector(want, 10, 1, 1);
  seek_track(&fdc, 10);
  juku_fdc_write(&fdc, 0, 0xF0);
  juku_fdc_write(&fdc, 3, 0x4E);
  pulse_index(&fdc);
  for (int i = 1; i < JUK_MFM_TRACK_SIZE; i++) juku_fdc_write(&fdc, 3, 0x4E);
  fail |= expect_intrq(&fdc, 1, "unrepresentable write-track completion");
  fail |= expect_status(&fdc, ST_WRITE_FAULT, ST_WRITE_FAULT,
                        "unrepresentable write-track status");
  if (juk_disk_read_sector(&disk, 10, 1, 1, partial) != 0 ||
      memcmp(partial, want, JUK_SECTOR_SIZE) != 0) {
    fprintf(stderr, "unrepresentable write-track changed flat-image sector\n");
    fail = 1;
  }

  juku_fdc_portc(&fdc, 0x00);  // motor off
  juku_fdc_write(&fdc, 0, 0xC0);
  fail |= expect_status(&fdc, ST_NOT_READY, ST_NOT_READY, "motor off read address");
  juku_fdc_write(&fdc, 0, 0xE0);
  fail |= expect_status(&fdc, ST_NOT_READY, ST_NOT_READY, "motor off read track");
  juku_fdc_write(&fdc, 0, 0xF0);
  fail |= expect_status(&fdc, ST_NOT_READY, ST_NOT_READY, "motor off write track");
  juku_fdc_write(&fdc, 0, 0x80);
  fail |= expect_status(&fdc, ST_NOT_READY, ST_NOT_READY, "motor off read");

  juk_disk_close(&disk);
  unlink(path);
  rmdir(dir);
  if (fail) {
    fprintf(stderr, "Juku FDC model test: FAIL\n");
    return 1;
  }
  puts("Juku FDC model test: PASS");
  return 0;
}
