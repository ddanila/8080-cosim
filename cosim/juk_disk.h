#ifndef JUK_DISK_H
#define JUK_DISK_H

#include <stdint.h>
#include <stdio.h>

#define JUK_TRACKS 80
#define JUK_SECTORS_PER_TRACK 10
#define JUK_SECTOR_SIZE 512
#define JUK_MFM_TRACK_SIZE 6250
#define JUK_DELETED_MARK_COUNT (JUK_TRACKS * 2 * JUK_SECTORS_PER_TRACK)
#define JUK_SINGLE_SIDED_SIZE (JUK_TRACKS * 1 * JUK_SECTORS_PER_TRACK * JUK_SECTOR_SIZE)
#define JUK_DOUBLE_SIDED_SIZE (JUK_TRACKS * 2 * JUK_SECTORS_PER_TRACK * JUK_SECTOR_SIZE)

typedef struct {
  FILE* fp;
  FILE* deleted_marks_fp;
  int heads;
  long size;
  int writable;
  // The historical raw image stores payload bytes only. Preserve data-address
  // mark type in memory, optionally backed by an explicitly attached companion
  // file, without pretending the metadata is part of the raw image.
  uint8_t deleted_data[JUK_DELETED_MARK_COUNT];
} juk_disk;

int juk_disk_open(juk_disk* disk, const char* path);
int juk_disk_open_writable(juk_disk* disk, const char* path);
int juk_disk_attach_deleted_marks(juk_disk* disk, const char* path);
void juk_disk_close(juk_disk* disk);
long juk_disk_offset(const juk_disk* disk, int track, int head, int sector);
int juk_disk_read_sector(juk_disk* disk, int track, int head, int sector, uint8_t out[JUK_SECTOR_SIZE]);
int juk_disk_write_sector(juk_disk* disk, int track, int head, int sector,
                          const uint8_t in[JUK_SECTOR_SIZE]);
int juk_disk_sector_deleted(const juk_disk* disk, int track, int head, int sector);
int juk_disk_set_sector_deleted(juk_disk* disk, int track, int head, int sector, int deleted);

#endif
