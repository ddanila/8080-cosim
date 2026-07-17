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
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_NOT_READY, 0, "after restore command");
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
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after read-address drain");
  if (juku_fdc_read(&fdc, 2) != 12) {
    fprintf(stderr, "read-address did not load track address into sector register\n");
    fail = 1;
  }

  juku_fdc_write(&fdc, 2, 7);
  juku_fdc_write(&fdc, 0, 0xC0);
  (void)juku_fdc_read(&fdc, 3);
  (void)juku_fdc_read(&fdc, 3);
  juku_fdc_write(&fdc, 0, 0xD0);  // force interrupt aborts the partial ID field
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after forced read-address abort");
  if (juku_fdc_read(&fdc, 2) != 7) {
    fprintf(stderr, "aborted read-address changed sector register\n");
    fail = 1;
  }
  juku_fdc_write(&fdc, 0, 0xC1);  // reserved low bit is not Read Address
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, ST_BUSY, "reserved type-III opcode");
  juku_fdc_write(&fdc, 0, 0xD0);

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
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ, 0, "after sector drain");

  juku_fdc_write(&fdc, 0, 0xFD);  // write track against read-only raw-image shim
  fail |= expect_status(&fdc, ST_BUSY | ST_DRQ | ST_WRITE_PROTECT, ST_WRITE_PROTECT, "after write-track command");

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
