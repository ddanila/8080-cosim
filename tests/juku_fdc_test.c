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
  ST_RNF = 0x10,
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
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_NOT_READY, 0, "after restore command");
  fail |= expect_intrq(&fdc, 0, "restore status acknowledgement");
  if (juku_fdc_read(&fdc, 1) != 0) {
    fprintf(stderr, "restore did not return to track 0\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 3, 12);
  juku_fdc_write(&fdc, 0, 0x12);  // seek to data register
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_NOT_READY, 0, "after seek command");
  if (juku_fdc_read(&fdc, 1) != 12) {
    fprintf(stderr, "seek did not copy data register to track\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 0, 0x50);  // step in and update the track register
  if (juku_fdc_read(&fdc, 1) != 13) {
    fprintf(stderr, "step-in/update did not increment track\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0x40);  // step in without track-register update
  if (juku_fdc_read(&fdc, 1) != 13) {
    fprintf(stderr, "step-in/no-update changed track\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0x70);  // step out and update the track register
  if (juku_fdc_read(&fdc, 1) != 12) {
    fprintf(stderr, "step-out/update did not decrement track\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0x30);  // generic step reuses the prior direction
  if (juku_fdc_read(&fdc, 1) != 11) {
    fprintf(stderr, "step/update did not preserve the step-out direction\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 1, 12);
  juku_fdc_write(&fdc, 2, 9);
  juku_fdc_write(&fdc, 0, 0xC4);  // read address, including the valid E flag
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ, "after read-address command");
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
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ, "after read-track command");
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
  for (int i = 0; i < 100; i++) (void)juku_fdc_read(&fdc, 3);
  juku_fdc_write(&fdc, 0, 0xD0);
  fail |= expect_intrq(&fdc, 0, "forced read-track D0 silence");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after forced read-track abort");

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
  fail |= expect_intrq(&fdc, 0, "D8 status acknowledgement");

  juku_fdc_write(&fdc, 1, 12);
  juku_fdc_write(&fdc, 2, 4);
  juku_fdc_write(&fdc, 0, 0x80);
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ, "after read command");

  uint8_t want[JUK_SECTOR_SIZE];
  fill_sector(want, 12, 0, 4);
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
  juku_fdc_write(&fdc, 1, 43);
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

  juku_fdc_portc(&fdc, 0x04);  // motor on, side 0
  juku_fdc_write(&fdc, 1, 12);
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
  juku_fdc_write(&fdc, 1, 8);
  juku_fdc_write(&fdc, 2, 3);
  juku_fdc_write(&fdc, 0, 0xA2);  // exact side-aware ROMBIOS variant
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY | ST_DRQ, "writable write-sector command");
  for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
    juku_fdc_write(&fdc, 3, (uint8_t)(0x5A ^ i));
  }
  fail |= expect_intrq(&fdc, 1, "write-sector completion");
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_WRITE_PROTECT, 0, "after writable sector fill");
  juku_fdc_write(&fdc, 0, 0x82);
  for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
    uint8_t got = juku_fdc_read(&fdc, 3);
    uint8_t expected = (uint8_t)(0x5A ^ i);
    if (got != expected) {
      fprintf(stderr, "write-sector readback byte %d: got 0x%02X want 0x%02X\n", i, got, expected);
      fail = 1;
      break;
    }
  }

  juku_fdc_write(&fdc, 1, 8);
  juku_fdc_write(&fdc, 2, 9);
  juku_fdc_write(&fdc, 0, 0xB2);  // side-aware multiple-record write
  for (int record = 9; record <= 10; record++) {
    for (int i = 0; i < JUK_SECTOR_SIZE; i++) {
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
    juku_fdc_write(&fdc, 0, 0x82);
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
  }

  juku_fdc_portc(&fdc, 0x00);  // motor off
  juku_fdc_write(&fdc, 0, 0xC0);
  fail |= expect_status(&fdc, ST_NOT_READY, ST_NOT_READY, "motor off read address");
  juku_fdc_write(&fdc, 0, 0xE0);
  fail |= expect_status(&fdc, ST_NOT_READY, ST_NOT_READY, "motor off read track");
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
