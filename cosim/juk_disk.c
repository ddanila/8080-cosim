#include "juk_disk.h"

#include <errno.h>
#include <string.h>


static long file_size(FILE* fp) {
  long here = ftell(fp);
  if (here < 0) return -1;
  if (fseek(fp, 0, SEEK_END) != 0) return -1;
  long size = ftell(fp);
  if (size < 0) return -1;
  if (fseek(fp, here, SEEK_SET) != 0) return -1;
  return size;
}


static int open_mode(juk_disk* disk, const char* path, int writable) {
  memset(disk, 0, sizeof(*disk));
  FILE* fp = fopen(path, writable ? "r+b" : "rb");
  if (!fp) return -errno;

  long size = file_size(fp);
  if (size == JUK_SINGLE_SIDED_SIZE) disk->heads = 1;
  else if (size == JUK_DOUBLE_SIDED_SIZE) disk->heads = 2;
  else {
    fclose(fp);
    return -EINVAL;
  }

  disk->fp = fp;
  disk->size = size;
  disk->writable = writable;
  return 0;
}


int juk_disk_open(juk_disk* disk, const char* path) {
  return open_mode(disk, path, 0);
}


int juk_disk_open_writable(juk_disk* disk, const char* path) {
  return open_mode(disk, path, 1);
}


void juk_disk_close(juk_disk* disk) {
  if (disk->fp) fclose(disk->fp);
  memset(disk, 0, sizeof(*disk));
}


long juk_disk_offset(const juk_disk* disk, int track, int head, int sector) {
  if (!disk || !disk->fp) return -1;
  if (track < 0 || track >= JUK_TRACKS) return -1;
  if (head < 0 || head >= disk->heads) return -1;
  if (sector < 1 || sector > JUK_SECTORS_PER_TRACK) return -1;
  long logical_sector =
      ((long)track * disk->heads + head) * JUK_SECTORS_PER_TRACK + (sector - 1);
  return logical_sector * JUK_SECTOR_SIZE;
}


static long metadata_index(const juk_disk* disk, int track, int head, int sector) {
  if (!disk || !disk->fp) return -1;
  if (track < 0 || track >= JUK_TRACKS) return -1;
  if (head < 0 || head >= disk->heads) return -1;
  if (sector < 1 || sector > JUK_SECTORS_PER_TRACK) return -1;
  return ((long)track * 2 + head) * JUK_SECTORS_PER_TRACK + (sector - 1);
}


int juk_disk_read_sector(juk_disk* disk, int track, int head, int sector, uint8_t out[JUK_SECTOR_SIZE]) {
  long offset = juk_disk_offset(disk, track, head, sector);
  if (offset < 0) return -EINVAL;
  if (fseek(disk->fp, offset, SEEK_SET) != 0) return -errno;
  size_t got = fread(out, 1, JUK_SECTOR_SIZE, disk->fp);
  if (got != JUK_SECTOR_SIZE) return ferror(disk->fp) ? -EIO : -EINVAL;
  return 0;
}


int juk_disk_write_sector(juk_disk* disk, int track, int head, int sector,
                          const uint8_t in[JUK_SECTOR_SIZE]) {
  if (!disk || !disk->fp || !disk->writable) return -EROFS;
  long offset = juk_disk_offset(disk, track, head, sector);
  if (offset < 0) return -EINVAL;
  if (fseek(disk->fp, offset, SEEK_SET) != 0) return -errno;
  size_t put = fwrite(in, 1, JUK_SECTOR_SIZE, disk->fp);
  if (put != JUK_SECTOR_SIZE) return -EIO;
  if (fflush(disk->fp) != 0) return -errno;
  return 0;
}


int juk_disk_sector_deleted(const juk_disk* disk, int track, int head, int sector) {
  long index = metadata_index(disk, track, head, sector);
  if (index < 0) return -EINVAL;
  return disk->deleted_data[index] != 0;
}


int juk_disk_set_sector_deleted(juk_disk* disk, int track, int head, int sector, int deleted) {
  if (!disk || !disk->writable) return -EROFS;
  long index = metadata_index(disk, track, head, sector);
  if (index < 0) return -EINVAL;
  disk->deleted_data[index] = deleted != 0;
  return 0;
}
