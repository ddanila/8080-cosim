#ifndef JUKUHOST_PLATFORM_H
#define JUKUHOST_PLATFORM_H

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#include "jukuhost.h"

struct jh_platform_serial {
    int fd;
    int pseudo_terminal;
    char path[512];
    unsigned baud;
    char parity;
    unsigned base_port;
    unsigned fifo_depth;
    unsigned line_errors;
    uint64_t tx_ready_ms;
    unsigned saved_lcr;
    unsigned saved_ier;
    unsigned saved_mcr;
    unsigned saved_divisor;
    int opened;
};

struct jh_platform_console {
    int fd;
    FILE *file;
    uint64_t ready_ms;
};

struct jh_platform_media {
    FILE *file;
    uint32_t size;
    int writable;
    int native_order;
};

uint64_t jh_platform_milliseconds(void);
void jh_platform_sleep(unsigned milliseconds);
const char *jh_platform_name(void);
const char *jh_platform_timer_name(void);
unsigned jh_platform_timer_resolution_ms(void);
uint32_t jh_platform_available_memory(void);
int jh_platform_serial_open(struct jh_platform_serial *serial, const char *path,
                         unsigned baud, char parity);
int jh_platform_serial_adopt(struct jh_platform_serial *serial, int fd,
                          const char *description, unsigned baud, char parity);
int jh_platform_serial_configure(struct jh_platform_serial *serial, unsigned baud,
                              char parity);
void jh_platform_serial_close(struct jh_platform_serial *serial);
int jh_platform_serial_read(struct jh_platform_serial *serial, uint8_t *output,
                         size_t capacity, unsigned timeout_ms);
int jh_platform_serial_write(struct jh_platform_serial *serial, const uint8_t *data,
                          size_t length, unsigned timeout_ms);
int jh_platform_serial_drain(struct jh_platform_serial *serial);
int jh_platform_console_open(struct jh_platform_console *console,
                             const char *path);
int jh_platform_console_read(struct jh_platform_console *console,
                             uint8_t *output, size_t capacity);
int jh_platform_console_write(struct jh_platform_console *console,
                              const uint8_t *data, size_t length);
void jh_platform_console_close(struct jh_platform_console *console);
void jh_platform_idle(void);
int jh_platform_stop_requested(void);
void jh_platform_install_signals(void);
int jh_platform_load_file(const char *path, uint8_t **data, size_t *length);
int jh_platform_write_file(const char *path, const uint8_t *data, size_t length,
                        int sync_data);
int jh_platform_remove_file(const char *path);
int jh_platform_file_identity(const char *path, uint32_t *size,
                              uint8_t digest[JH_SHA256_SIZE]);
int jh_platform_copy_file(const char *source, const char *target);
int jh_platform_media_open(struct jh_platform_media *media, const char *path,
                           uint32_t expected_size, int writable,
                           int native_order);
void jh_platform_media_close(struct jh_platform_media *media);
int jh_platform_media_read(void *context, uint32_t offset,
                           uint8_t record[JH_N3_RECORD_SIZE]);
int jh_platform_media_write(void *context, uint32_t offset,
                            const uint8_t record[JH_N3_RECORD_SIZE]);

#endif
