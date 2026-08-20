#ifndef JUKUHOST_PLATFORM_POSIX_H
#define JUKUHOST_PLATFORM_POSIX_H

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

struct jh_posix_serial {
    int fd;
    int pseudo_terminal;
    char path[512];
    unsigned baud;
    char parity;
};

uint64_t jh_posix_milliseconds(void);
void jh_posix_sleep(unsigned milliseconds);
int jh_posix_serial_open(struct jh_posix_serial *serial, const char *path,
                         unsigned baud, char parity);
int jh_posix_serial_adopt(struct jh_posix_serial *serial, int fd,
                          const char *description, unsigned baud, char parity);
int jh_posix_serial_configure(struct jh_posix_serial *serial, unsigned baud,
                              char parity);
void jh_posix_serial_close(struct jh_posix_serial *serial);
int jh_posix_serial_read(struct jh_posix_serial *serial, uint8_t *output,
                         size_t capacity, unsigned timeout_ms);
int jh_posix_serial_write(struct jh_posix_serial *serial, const uint8_t *data,
                          size_t length, unsigned timeout_ms);
int jh_posix_serial_drain(struct jh_posix_serial *serial);
int jh_posix_set_raw(int fd);
int jh_posix_open_console(const char *path);
int jh_posix_stop_requested(void);
void jh_posix_install_signals(void);
int jh_posix_load_file(const char *path, uint8_t **data, size_t *length);
int jh_posix_write_file(const char *path, const uint8_t *data, size_t length,
                        int sync_data);
int jh_posix_pwrite_record(const char *path, uint32_t offset,
                           const uint8_t *data, size_t length);
int jh_posix_remove_file(const char *path);

#endif
