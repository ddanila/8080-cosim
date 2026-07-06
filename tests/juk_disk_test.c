#define _POSIX_C_SOURCE 200809L

#include "../cosim/juk_disk.h"

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>


static void fill_sector(uint8_t buf[JUK_SECTOR_SIZE], int track, int head, int sector) {
  memset(buf, 0, JUK_SECTOR_SIZE);
  buf[0] = (uint8_t)track;
  buf[1] = (uint8_t)head;
  buf[2] = (uint8_t)sector;
  buf[3] = (uint8_t)(track ^ (head << 4) ^ sector);
}


static int write_image(const char* path, int heads) {
  FILE* fp = fopen(path, "wb");
  if (!fp) {
    perror(path);
    return 1;
  }
  uint8_t buf[JUK_SECTOR_SIZE];
  for (int track = 0; track < JUK_TRACKS; track++) {
    for (int head = 0; head < heads; head++) {
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


static int expect_sector(juk_disk* disk, int track, int head, int sector) {
  uint8_t got[JUK_SECTOR_SIZE];
  uint8_t want[JUK_SECTOR_SIZE];
  fill_sector(want, track, head, sector);
  int rc = juk_disk_read_sector(disk, track, head, sector, got);
  if (rc != 0) {
    fprintf(stderr, "read_sector(%d,%d,%d) failed: %d\n", track, head, sector, rc);
    return 1;
  }
  if (memcmp(got, want, JUK_SECTOR_SIZE) != 0) {
    fprintf(stderr, "sector mismatch at T%d H%d S%d\n", track, head, sector);
    return 1;
  }
  return 0;
}


static int check_image(const char* path, int heads) {
  juk_disk disk;
  int rc = juk_disk_open(&disk, path);
  if (rc != 0) {
    fprintf(stderr, "juk_disk_open(%s) failed: %d\n", path, rc);
    return 1;
  }
  int fail = 0;
  if (disk.heads != heads) {
    fprintf(stderr, "%s: expected %d heads, got %d\n", path, heads, disk.heads);
    fail = 1;
  }
  fail |= expect_sector(&disk, 0, 0, 1);
  fail |= expect_sector(&disk, 0, 0, 10);
  fail |= expect_sector(&disk, 12, 0, 4);
  fail |= expect_sector(&disk, 79, heads - 1, 10);
  if (heads == 2) {
    fail |= expect_sector(&disk, 0, 1, 1);
    fail |= expect_sector(&disk, 43, 1, 7);
  }
  if (juk_disk_offset(&disk, -1, 0, 1) >= 0) fail = 1;
  if (juk_disk_offset(&disk, 80, 0, 1) >= 0) fail = 1;
  if (juk_disk_offset(&disk, 0, heads, 1) >= 0) fail = 1;
  if (juk_disk_offset(&disk, 0, 0, 0) >= 0) fail = 1;
  if (juk_disk_offset(&disk, 0, 0, 11) >= 0) fail = 1;
  juk_disk_close(&disk);
  return fail;
}


int main(void) {
  char dir[] = "/tmp/juk-disk-test.XXXXXX";
  if (!mkdtemp(dir)) {
    perror("mkdtemp");
    return 1;
  }
  char ss[256];
  char ds[256];
  snprintf(ss, sizeof(ss), "%s/single.juk", dir);
  snprintf(ds, sizeof(ds), "%s/double.juk", dir);

  int fail = 0;
  fail |= write_image(ss, 1);
  fail |= write_image(ds, 2);
  fail |= check_image(ss, 1);
  fail |= check_image(ds, 2);

  unlink(ss);
  unlink(ds);
  rmdir(dir);
  if (fail) {
    fprintf(stderr, "JUK disk loader test: FAIL\n");
    return 1;
  }
  puts("JUK disk loader test: PASS");
  return 0;
}
