#ifndef JUKUHOST_RUNNER_H
#define JUKUHOST_RUNNER_H

#include <stddef.h>
#include <stdint.h>

#include "jukuhost.h"

#ifdef __cplusplus
extern "C" {
#endif

#define JH_HOST_VERSION "0.3.1-m7"

enum jh_host_exit {
    JH_HOST_EXIT_CLEAN = 0,
    JH_HOST_EXIT_COMMAND = 2,
    JH_HOST_EXIT_ARTIFACT = 3,
    JH_HOST_EXIT_SERIAL = 4,
    JH_HOST_EXIT_PROTOCOL = 5,
    JH_HOST_EXIT_MEDIA = 6,
    JH_HOST_EXIT_EVIDENCE = 7
};

struct jh_host_options {
    const char *config_path;
    const char *serial;
    const char *system;
    const char *fast_stage;
    const char *volume;
    const char *drive_b;
    const char *console_pty;
    const char *log;
    const char *capture;
    const char *fallback_system;
    const char *fallback_fast_stage;
    const uint8_t *system_bytes;
    size_t system_length;
    const uint8_t *fast_stage_bytes;
    size_t fast_stage_length;
    const struct jh_config_artifact *system_identity;
    const struct jh_config_artifact *fast_stage_identity;
    const struct jh_config_artifact *fallback_system_identity;
    const struct jh_config_artifact *fallback_fast_stage_identity;
    const struct jh_config_disk *volume_identity;
    const struct jh_config_disk *drive_b_identity;
    int serial_fd;
    uint32_t timeout_seconds;
    uint32_t disk_timeout_seconds;
    uint32_t boot_restarts;
    uint32_t reconnect_timeout_seconds;
    uint32_t disk_protocol;
    uint32_t disk_baud;
    uint32_t read_ahead;
    uint32_t reply_guard_ms;
    int direct_fastboot;
    int recover_session;
    int resume_disk;
    int boot_only;
    int writable;
    int verbose;
    int selftest;
    int console_enabled;
};

struct jh_host_summary {
    int result;
    unsigned long rx_bytes;
    unsigned long tx_bytes;
    unsigned long requests;
    unsigned long retries;
    unsigned long reads;
    unsigned long read_records;
    unsigned long writes;
    unsigned long boot_restarts;
    unsigned long reconnects;
    unsigned long target_resets;
    unsigned long serial_line_errors;
};

struct jh_host_hooks {
    void *context;
    int (*stop_requested)(void *context);
    void (*log)(void *context, unsigned long elapsed_ms,
                const char *level, const char *message);
    void (*state)(void *context, const char *state);
    void (*progress)(void *context, unsigned completed, unsigned total);
    void (*activity)(void *context, const struct jh_host_summary *summary);
    int (*console_read)(void *context, uint8_t *output, size_t capacity);
    int (*console_write)(void *context, const uint8_t *data, size_t length);
    int (*resolve_serial)(void *context, const char *configured,
                          char *output, size_t capacity);
};

void jh_host_options_init(struct jh_host_options *options);
int jh_host_run(const struct jh_host_options *options,
                const struct jh_host_hooks *hooks,
                struct jh_host_summary *summary);
int jh_host_selftest(void);
int jh_host_cli_main(int argc, char **argv);

#ifdef __cplusplus
}
#endif

#endif
