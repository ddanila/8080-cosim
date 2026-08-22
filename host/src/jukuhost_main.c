#define _POSIX_C_SOURCE 200809L

#include "jukuhost.h"
#include "platform.h"

#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define HOST_VERSION "0.3.1-m6"
#define STOCK_TURN_GUARD_MS 10u
#define V15_EXTENSION_GUARD_MS 20u
#define V15_PROBE_REPLY_MS 25u

enum exit_code {
    EXIT_CLEAN = 0,
    EXIT_COMMAND = 2,
    EXIT_ARTIFACT = 3,
    EXIT_SERIAL = 4,
    EXIT_PROTOCOL = 5,
    EXIT_MEDIA = 6,
    EXIT_EVIDENCE = 7
};

enum run_result {
    RUN_TARGET_RESET = 100
};

struct options {
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
    int resume_disk;
    int boot_only;
    int writable;
    int verbose;
    int selftest;
};

struct host_context {
    struct options options;
    struct jh_platform_serial serial;
    FILE *log_file;
    FILE *capture_file;
    uint64_t started_ms;
    unsigned long rx_bytes;
    unsigned long tx_bytes;
    unsigned long requests;
    unsigned long retries;
    unsigned long reads;
    unsigned long read_records;
    unsigned long writes;
    unsigned long boot_restart_count;
    unsigned long reconnect_count;
    unsigned long target_reset_count;
    unsigned long serial_line_errors;
    int log_error;
    int capture_error;
    int capture_ready;
};

static int capture_record(struct host_context *host, enum jh_capture_type type,
                          uint8_t flags, const uint8_t *data, size_t length);

static void usage(FILE *file)
{
    fprintf(file,
        "usage: jukuhost CONFIG.INI\n"
        "       jukuhost --serial DEVICE --system FILE --volume FILE [options]\n"
        "\n"
        "Boot options:\n"
        "  --config FILE           explicit INI configuration\n"
        "  --serial-fd FD          inherited PTY (integration tests only)\n"
        "  --fast-stage FILE       stock-assisted JF15 or network-ROM JF16\n"
        "  --network-rom           C8 automatic/direct Fastboot V16\n"
        "  --direct-fastboot       synonym for --network-rom\n"
        "  --resume-disk           attach to an already running system\n"
        "  --boot-only             stop after a successful bootstrap\n"
        "  --timeout SECONDS       boot deadline (default 120)\n"
        "  --boot-restarts COUNT   target-reset retries (default 3)\n"
        "\n"
        "Disk and console:\n"
        "  --drive-b FILE          read-only native 800 KiB .JUK image\n"
        "  --writable              persist A: through the crash journal\n"
        "  --disk-protocol 1|2|3  default 3\n"
        "  --disk-baud RATE        default 19200\n"
        "  --read-ahead 1..8       default 3\n"
        "  --console-pty DEVICE    enable N4 remote console\n"
        "  --disk-timeout SECONDS  zero means run until stopped\n"
        "  --reconnect-timeout SEC named-device reopen deadline (default 30)\n"
        "\n"
        "Evidence:\n"
        "  --log FILE              text log (console is always used)\n"
        "  --capture FILE          CRC-protected exact-byte capture\n"
        "  --verbose               log individual disk requests\n"
        "  --selftest              run portable startup checks\n"
        "  --help                  print this summary\n"
        "  --version               print version\n");
}

static int parse_unsigned(const char *text, uint32_t minimum, uint32_t maximum,
                          uint32_t *result)
{
    char *end;
    unsigned long value;
    errno = 0;
    value = strtoul(text, &end, 10);
    if (errno != 0 || *text == '\0' || *end != '\0' ||
            value < minimum || value > maximum) return -1;
    *result = (uint32_t)value;
    return 0;
}

static int require_value(int argc, char **argv, int *index, const char **value)
{
    if (*index + 1 >= argc) return -1;
    *value = argv[++*index];
    return 0;
}

static int parse_options(int argc, char **argv, struct options *options)
{
    int index;
    memset(options, 0, sizeof(*options));
    options->timeout_seconds = 120u;
    options->boot_restarts = 3u;
    options->reconnect_timeout_seconds = 30u;
    options->disk_protocol = 3u;
    options->disk_baud = 19200u;
    options->read_ahead = 3u;
    options->reply_guard_ms = 2u;
    options->serial_fd = -1;
#ifdef JH_DOS
    if (argc == 1) {
        options->config_path = "JUKUHOST.INI";
        return 0;
    }
#endif
    for (index = 1; index < argc; ++index) {
        const char *argument = argv[index];
        const char *value;
        if (argument[0] != '-') {
            if (options->config_path != NULL || argc != 2) return -1;
            options->config_path = argument;
        } else if (strcmp(argument, "--help") == 0) {
            usage(stdout);
            return 1;
        } else if (strcmp(argument, "--version") == 0) {
            printf("jukuhost %s\n", HOST_VERSION);
            return 1;
        } else if (strcmp(argument, "--serial") == 0) {
            if (require_value(argc, argv, &index, &options->serial) != 0) return -1;
        } else if (strcmp(argument, "--config") == 0) {
            if (require_value(argc, argv, &index, &options->config_path) != 0) {
                return -1;
            }
        } else if (strcmp(argument, "--serial-fd") == 0) {
            uint32_t descriptor;
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 0u, 65535u, &descriptor) != 0) return -1;
            options->serial_fd = (int)descriptor;
        } else if (strcmp(argument, "--system") == 0) {
            if (require_value(argc, argv, &index, &options->system) != 0) return -1;
        } else if (strcmp(argument, "--fast-stage") == 0 ||
                strcmp(argument, "--fast-stage1") == 0) {
            if (require_value(argc, argv, &index, &options->fast_stage) != 0) return -1;
        } else if (strcmp(argument, "--volume") == 0) {
            if (require_value(argc, argv, &index, &options->volume) != 0) return -1;
        } else if (strcmp(argument, "--drive-b") == 0) {
            if (require_value(argc, argv, &index, &options->drive_b) != 0) return -1;
        } else if (strcmp(argument, "--console-pty") == 0) {
            if (require_value(argc, argv, &index, &options->console_pty) != 0) return -1;
        } else if (strcmp(argument, "--log") == 0) {
            if (require_value(argc, argv, &index, &options->log) != 0) return -1;
        } else if (strcmp(argument, "--capture") == 0) {
            if (require_value(argc, argv, &index, &options->capture) != 0) return -1;
        } else if (strcmp(argument, "--network-rom") == 0 ||
                strcmp(argument, "--direct-fastboot") == 0) {
            options->direct_fastboot = 1;
        } else if (strcmp(argument, "--resume-disk") == 0) {
            options->resume_disk = 1;
        } else if (strcmp(argument, "--boot-only") == 0) {
            options->boot_only = 1;
        } else if (strcmp(argument, "--writable") == 0) {
            options->writable = 1;
        } else if (strcmp(argument, "--verbose") == 0) {
            options->verbose = 1;
        } else if (strcmp(argument, "--selftest") == 0) {
            options->selftest = 1;
        } else if (strcmp(argument, "--timeout") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 1u, 86400u,
                                   &options->timeout_seconds) != 0) return -1;
        } else if (strcmp(argument, "--disk-timeout") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 0u, 86400u,
                                   &options->disk_timeout_seconds) != 0) return -1;
        } else if (strcmp(argument, "--boot-restarts") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 0u, 100u,
                                   &options->boot_restarts) != 0) return -1;
        } else if (strcmp(argument, "--reconnect-timeout") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 0u, 86400u,
                        &options->reconnect_timeout_seconds) != 0) return -1;
        } else if (strcmp(argument, "--disk-protocol") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 1u, 3u,
                                   &options->disk_protocol) != 0) return -1;
        } else if (strcmp(argument, "--disk-baud") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 2400u, 38400u,
                                   &options->disk_baud) != 0) return -1;
        } else if (strcmp(argument, "--read-ahead") == 0 ||
                strcmp(argument, "--disk-read-ahead-records") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 1u, 8u,
                                   &options->read_ahead) != 0) return -1;
        } else if (strcmp(argument, "--disk-reply-guard-ms") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 0u, 1000u,
                                   &options->reply_guard_ms) != 0) return -1;
        } else {
            fprintf(stderr, "jukuhost: unknown option: %s\n", argument);
            return -1;
        }
    }
    if (options->selftest) return argc == 2 ? 0 : -1;
    if (options->config_path != NULL) {
        if (options->serial != NULL || options->serial_fd >= 0 ||
                options->system != NULL || options->fast_stage != NULL ||
                options->volume != NULL || options->drive_b != NULL ||
                options->console_pty != NULL || options->log != NULL ||
                options->capture != NULL || options->direct_fastboot ||
                options->resume_disk || options->boot_only ||
                options->writable || options->verbose) {
            return -1;
        }
        return 0;
    }
    if ((options->serial != NULL) == (options->serial_fd >= 0) ||
            (options->volume == NULL && !options->boot_only) ||
            (!options->resume_disk && options->system == NULL)) return -1;
    if (options->resume_disk && options->boot_only) return -1;
    if (options->direct_fastboot && options->fast_stage == NULL) return -1;
    if (options->console_pty != NULL && options->disk_protocol != 3u) return -1;
    return 0;
}

static void host_log(struct host_context *host, const char *level,
                     const char *format, ...)
{
    char message[1024];
    uint8_t capture_flags = 1u;
    va_list arguments;
    unsigned long elapsed = (unsigned long)(jh_platform_milliseconds() -
                                             host->started_ms);
    va_start(arguments, format);
    (void)vsnprintf(message, sizeof(message), format, arguments);
    va_end(arguments);
    printf("%08lu %-5s %s\n", elapsed, level, message);
    fflush(stdout);
    if (strcmp(level, "WARN") == 0) capture_flags = 2u;
    else if (strcmp(level, "ERROR") == 0) capture_flags = 3u;
    if (host->log_file != NULL && !host->log_error &&
            (fprintf(host->log_file, "%08lu %-5s %s\n", elapsed, level,
                     message) < 0 || fflush(host->log_file) != 0)) {
        host->log_error = 1;
        fprintf(stderr, "jukuhost: log write failed: %s\n", strerror(errno));
    }
    if (host->capture_ready && !host->capture_error) {
        if (capture_record(host, JH_CAPTURE_EVENT, capture_flags,
                           (const uint8_t *)message, strlen(message)) != 0) {
            host->capture_error = 1;
            fprintf(stderr, "jukuhost: capture event write failed: %s\n",
                    strerror(errno));
        } else if (capture_flags != 1u ||
                strncmp(message, "start ", 6u) == 0 ||
                strncmp(message, "serial ", 7u) == 0 ||
                strncmp(message, "phase=", 6u) == 0 ||
                strncmp(message, "media write ", 12u) == 0 ||
                strncmp(message, "stop ", 5u) == 0) {
            if (fflush(host->capture_file) != 0) {
                host->capture_error = 1;
                fprintf(stderr, "jukuhost: capture flush failed: %s\n",
                        strerror(errno));
            }
        }
    }
}

static int path_is_absolute(const char *path)
{
    return path[0] == '/' || path[0] == '\\' ||
        (path[0] != '\0' && path[1] == ':');
}

static int resolve_path(const char *config_path, char *path, size_t capacity)
{
    const char *slash;
    const char *backslash;
    const char *separator;
    size_t directory_length;
    size_t path_length;
    char resolved[JH_CONFIG_PATH_MAX];
    if (path[0] == '\0' || path_is_absolute(path)) return 0;
    slash = strrchr(config_path, '/');
    backslash = strrchr(config_path, '\\');
    separator = slash == NULL ? backslash : backslash == NULL ? slash :
        slash > backslash ? slash : backslash;
    /* A configuration in the current directory needs no prefix. Besides
       being simpler, this avoids ./NAME on DOS C libraries that accept the
       file for reading but reject that spelling when creating it. */
    if (separator == NULL) return 0;
    directory_length = (size_t)(separator - config_path);
    path_length = strlen(path);
    if (directory_length + 1u + path_length >= sizeof(resolved) ||
            capacity > sizeof(resolved)) return -1;
    memcpy(resolved, config_path, directory_length);
    resolved[directory_length] = '/';
    memcpy(resolved + directory_length + 1u, path, path_length + 1u);
    memcpy(path, resolved, directory_length + 1u + path_length + 1u);
    return 0;
}

static int resolve_config_paths(const char *path, struct jh_host_config *config)
{
    char *paths[10];
    size_t index;
    paths[0] = config->log;
    paths[1] = config->capture;
    paths[2] = config->system.file;
    paths[3] = config->fastboot.file;
    paths[4] = config->fallback_system.file;
    paths[5] = config->fallback_fastboot.file;
    paths[6] = config->disk_a.file;
    paths[7] = config->disk_a.base;
    paths[8] = config->disk_b.file;
    paths[9] = config->disk_b.base;
    for (index = 0u; index < sizeof(paths) / sizeof(paths[0]); ++index) {
        if (resolve_path(path, paths[index], JH_CONFIG_PATH_MAX) != 0) return -1;
    }
    return 0;
}

static int configure_from_file(const char *path, struct options *options,
                               struct jh_host_config *config)
{
    uint8_t *bytes = NULL;
    size_t length = 0u;
    struct jh_config_error error;
    int parsed;
    if (jh_platform_load_file(path, &bytes, &length) != 0) {
        fprintf(stderr, "jukuhost: cannot read configuration %s: %s\n",
                path, strerror(errno));
        return -1;
    }
    parsed = jh_config_parse((const char *)bytes, length, config, &error);
    free(bytes);
    if (parsed != JH_OK) {
        fprintf(stderr, "jukuhost: %s:%lu: %s\n", path,
                (unsigned long)error.line,
                error.message == NULL ? jh_result_name(parsed) : error.message);
        return -1;
    }
    if (resolve_config_paths(path, config) != 0) {
        fprintf(stderr, "jukuhost: resolved configuration path is too long\n");
        return -1;
    }
    options->serial = config->port;
    options->system = config->system.file;
    options->system_identity = &config->system;
    options->fast_stage = config->have_fastboot ? config->fastboot.file : NULL;
    options->fast_stage_identity = config->have_fastboot ?
        &config->fastboot : NULL;
    options->fallback_system = config->have_fallback ?
        config->fallback_system.file : NULL;
    options->fallback_fast_stage = config->have_fallback ?
        config->fallback_fastboot.file : NULL;
    options->fallback_system_identity = config->have_fallback ?
        &config->fallback_system : NULL;
    options->fallback_fast_stage_identity = config->have_fallback ?
        &config->fallback_fastboot : NULL;
    options->volume = config->disk_a.file;
    options->volume_identity = &config->disk_a;
    options->drive_b = config->disk_b.present ? config->disk_b.file : NULL;
    options->drive_b_identity = config->disk_b.present ? &config->disk_b : NULL;
    options->console_pty = config->console[0] == '\0' ? NULL : config->console;
    options->log = config->log[0] == '\0' ? NULL : config->log;
    options->capture = config->capture[0] == '\0' ? NULL : config->capture;
    options->timeout_seconds = config->timeout_seconds;
    options->disk_timeout_seconds = config->disk_timeout_seconds;
    options->boot_restarts = config->boot_restarts;
    options->reconnect_timeout_seconds = config->reconnect_timeout_seconds;
    options->disk_protocol = config->disk_protocol;
    options->disk_baud = config->disk_baud;
    options->read_ahead = config->read_ahead;
    options->reply_guard_ms = config->reply_guard_ms;
    options->direct_fastboot = config->network_rom;
    options->writable = config->disk_a.mode != JH_CONFIG_MEDIA_READ_ONLY;
    return 0;
}

static int portable_selftest(void)
{
    static const uint8_t input[] = "abc";
    static const char expected[] =
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    uint8_t digest[JH_SHA256_SIZE];
    char formatted[JH_SHA256_HEX_SIZE + 1u];
    jh_sha256(input, sizeof(input) - 1u, digest);
    jh_sha256_format(digest, formatted);
    if (strcmp(formatted, expected) != 0 ||
            jh_crc16_ibm((const uint8_t *)"123456789", 9u, 0u) != 0xbb3du) {
        fprintf(stderr, "jukuhost selftest: FAIL\n");
        return EXIT_PROTOCOL;
    }
    printf("jukuhost %s selftest: PASS\n", HOST_VERSION);
    return EXIT_CLEAN;
}

static int verify_identity(struct host_context *host, const char *label,
                           const uint8_t *bytes, size_t length,
                           const struct jh_config_artifact *identity,
                           int warning)
{
    uint8_t digest[JH_SHA256_SIZE];
    char actual[JH_SHA256_HEX_SIZE + 1u];
    char expected[JH_SHA256_HEX_SIZE + 1u];
    if (identity == NULL) return 0;
    jh_sha256(bytes, length, digest);
    if ((uint64_t)length == identity->size &&
            memcmp(digest, identity->sha256, sizeof(digest)) == 0) {
        jh_sha256_format(digest, actual);
        host_log(host, "INFO", "%s identity size=%lu sha256=%s", label,
                 (unsigned long)length, actual);
        return 0;
    }
    jh_sha256_format(digest, actual);
    jh_sha256_format(identity->sha256, expected);
    host_log(host, warning ? "WARN" : "ERROR",
        "%s identity mismatch expected-size=%lu actual-size=%lu "
        "expected-sha256=%s actual-sha256=%s", label,
        (unsigned long)identity->size, (unsigned long)length, expected, actual);
    return -1;
}

static int load_verified(struct host_context *host, const char *label,
                         const char *path,
                         const struct jh_config_artifact *identity,
                         uint8_t **bytes, size_t *length, int warning)
{
    if (jh_platform_load_file(path, bytes, length) != 0) {
        host_log(host, warning ? "WARN" : "ERROR", "cannot load %s %s: %s",
                 label, path, strerror(errno));
        return -1;
    }
    if (verify_identity(host, label, *bytes, *length, identity, warning) != 0) {
        free(*bytes);
        *bytes = NULL;
        *length = 0u;
        return -1;
    }
    return 0;
}

static int verify_disk_path(struct host_context *host, const char *label,
                            const char *path,
                            const struct jh_config_disk *identity)
{
    uint8_t digest[JH_SHA256_SIZE];
    char actual[JH_SHA256_HEX_SIZE + 1u];
    char expected[JH_SHA256_HEX_SIZE + 1u];
    uint32_t size;
    if (identity == NULL) return 0;
    if (jh_platform_file_identity(path, &size, digest) != 0) {
        host_log(host, "ERROR", "cannot read %s %s: %s", label, path,
                 strerror(errno));
        return -1;
    }
    jh_sha256_format(digest, actual);
    jh_sha256_format(identity->sha256, expected);
    if ((uint64_t)size != identity->size ||
            memcmp(digest, identity->sha256, sizeof(digest)) != 0) {
        host_log(host, "ERROR", "%s identity mismatch expected-size=%lu "
            "actual-size=%lu expected-sha256=%s actual-sha256=%s", label,
            (unsigned long)identity->size, (unsigned long)size, expected,
            actual);
        return -1;
    }
    host_log(host, "INFO", "%s identity size=%lu sha256=%s", label,
             (unsigned long)size, actual);
    return 0;
}

static int capture_record(struct host_context *host, enum jh_capture_type type,
                          uint8_t flags, const uint8_t *data, size_t length)
{
    uint8_t *encoded;
    size_t encoded_length;
    int result;
    if (host->capture_file == NULL) return 0;
    encoded = (uint8_t *)malloc(length + JH_CAPTURE_RECORD_OVERHEAD);
    if (encoded == NULL) return -1;
    result = jh_capture_encode(type, flags,
        jh_platform_milliseconds() - host->started_ms, data, length, encoded,
        length + JH_CAPTURE_RECORD_OVERHEAD, &encoded_length);
    if (result != JH_OK ||
            fwrite(encoded, 1u, encoded_length, host->capture_file) !=
            encoded_length) {
        if (result != JH_OK) errno = EIO;
        free(encoded);
        return -1;
    }
    free(encoded);
    return 0;
}

static int host_write(struct host_context *host, const uint8_t *data,
                      size_t length)
{
    if (jh_platform_serial_write(&host->serial, data, length, 10000u) != 0) {
        return -1;
    }
    host->tx_bytes += (unsigned long)length;
    if (capture_record(host, JH_CAPTURE_TX, 0u, data, length) != 0) {
        host->capture_error = 1;
        return -1;
    }
    return 0;
}

static int host_write_boot_output(struct host_context *host,
                                  const struct jh_boot_output *output,
                                  unsigned turn_guard_ms)
{
    size_t position = 0u;
    unsigned index;
    if (output == NULL || output->frame_count > JH_BOOT_MAX_FRAMES) return -1;
    if (turn_guard_ms == 0u) return host_write(host, output->bytes,
                                               output->length);
    for (index = 0u; index < output->frame_count; ++index) {
        size_t length = output->frame_lengths[index];
        const uint8_t *frame;
        if (length == 0u || length > output->length - position) return -1;
        frame = output->bytes + position;
        if (host_write(host, frame, length) != 0) return -1;
        position += length;
        if (length == 6u && frame[0] == 0xe4u && frame[1] == 0xe4u &&
                frame[2] == 0u && frame[4] == 0u) {
            if (jh_platform_serial_drain(&host->serial) != 0) return -1;
            jh_platform_sleep(turn_guard_ms);
        }
    }
    return position == output->length ? 0 : -1;
}

static int host_read(struct host_context *host, uint8_t *data, size_t capacity,
                     unsigned timeout_ms)
{
    int received = jh_platform_serial_read(&host->serial, data, capacity, timeout_ms);
    if (received > 0) {
        host->rx_bytes += (unsigned long)received;
        if (capture_record(host, JH_CAPTURE_RX, 0u, data,
                           (size_t)received) != 0) {
            host->capture_error = 1;
            return -1;
        }
    }
    return received;
}

static int reconnect_serial(struct host_context *host, unsigned baud,
                            char parity)
{
    uint64_t deadline;
    int original_error = errno;
    int last_error = original_error;
    if (host->capture_error || host->log_error ||
            host->options.serial == NULL ||
            host->options.reconnect_timeout_seconds == 0u) {
        errno = original_error;
        return -1;
    }
    host_log(host, "WARN", "serial link lost (%s); reopening %s for %u 8%c1",
             strerror(original_error), host->options.serial, baud, parity);
    host_log(host, "INFO", "phase=reconnect");
    host->serial_line_errors += host->serial.line_errors;
    jh_platform_serial_close(&host->serial);
    deadline = jh_platform_milliseconds() +
        (uint64_t)host->options.reconnect_timeout_seconds * 1000u;
    while (!jh_platform_stop_requested() &&
            jh_platform_milliseconds() < deadline) {
        if (jh_platform_serial_open(&host->serial, host->options.serial,
                                 baud, parity) == 0) {
            ++host->reconnect_count;
            host_log(host, "INFO", "serial reconnected count=%lu applied=%u 8%c1",
                     host->reconnect_count, host->serial.baud,
                     host->serial.parity);
            host_log(host, "INFO", "phase=netdisk");
            return 0;
        }
        last_error = errno;
        jh_platform_sleep(250u);
    }
    errno = last_error;
    host_log(host, "ERROR", "serial reopen timed out after %lu seconds: %s",
             (unsigned long)host->options.reconnect_timeout_seconds,
             strerror(errno));
    return -1;
}

static int capture_request(struct host_context *host,
                           const struct jh_n3_request *request,
                           const struct jh_service_event *event)
{
    char message[256];
    size_t request_bytes = request->operation == JH_N4_CONSOLE_OUT_BLOCK ?
        6u + request->payload_length : 9u + request->payload_length;
    unsigned records = 0u;
    int length;
    if (request->operation >= JH_N3_READ &&
            request->operation <= JH_N3_READ_AHEAD &&
            event->reply[3] == 0u) {
        records = request->operation == JH_N3_READ_AHEAD ?
            event->reply[4] : 1u;
    }
    length = snprintf(message, sizeof(message),
        "request op=%02X seq=%02X drive=%u track=%u sector=%u status=%u "
        "records=%u request-bytes=%lu reply-bytes=%lu duplicate=%u",
        request->operation, request->sequence, request->drive, request->track,
        request->sector, event->reply[3], records,
        (unsigned long)request_bytes, (unsigned long)event->reply_length,
        event->duplicate ? 1u : 0u);
    if (length < 0 || (size_t)length >= sizeof(message) ||
            capture_record(host, JH_CAPTURE_EVENT, 1u,
                           (const uint8_t *)message, (size_t)length) != 0) {
        host->capture_error = host->capture_file != NULL;
        return host->capture_file == NULL ? 0 : -1;
    }
    return 0;
}

static int host_write_disk_reply(struct host_context *host,
                                 const struct jh_n3_request *request,
                                 const struct jh_service_event *event)
{
    size_t position;
    size_t record_index;
    if (request->operation != JH_N3_READ_AHEAD || event->reply_length < 7u ||
            event->reply[3] != 0u) {
        return host_write(host, event->reply, event->reply_length);
    }
    if (host_write(host, event->reply, 5u) != 0) return -1;
    position = 5u;
    for (record_index = 0u; record_index < event->reply[4]; ++record_index) {
        size_t encoded_length;
        size_t chunk_length;
        uint8_t encoding;
        unsigned drain_ms;
        if (position + 4u > event->reply_length - 2u) return -1;
        encoding = event->reply[position + 3u];
        if (encoding == 0u) encoded_length = 1u + JH_N3_RECORD_SIZE;
        else if (encoding == 1u) encoded_length = 2u;
        else if (encoding == 2u) encoded_length = 1u;
        else if (encoding == 3u) {
            if (position + 5u > event->reply_length - 2u) return -1;
            encoded_length = (size_t)event->reply[position + 4u] + 3u;
        } else return -1;
        chunk_length = 3u + encoded_length;
        if (position + chunk_length > event->reply_length - 2u ||
                host_write(host, event->reply + position, chunk_length) != 0) {
            return -1;
        }
        /* Match the proven Python-era rule: allow already queued 8O1 bytes
         * to leave the driver, then give the 8080 decoder four milliseconds
         * before the next descriptor can reach its one-byte USART. */
        drain_ms = (unsigned)((((record_index == 0u ? 5u : 0u) +
                                chunk_length) * 11000u +
                               host->options.disk_baud - 1u) /
                              host->options.disk_baud) + 4u;
        jh_platform_sleep(drain_ms);
        position += chunk_length;
    }
    if (position != event->reply_length - 2u) return -1;
    return host_write(host, event->reply + position, 2u);
}

static int run_stock_boot(struct host_context *host, const uint8_t *system,
                          size_t system_length)
{
    uint8_t *prepared_bytes;
    uint8_t incoming[4096];
    struct jh_boot_image prepared;
    struct jh_boot_session session;
    struct jh_janet_parser parser;
    struct jh_janet_frame frame;
    uint64_t deadline = jh_platform_milliseconds() +
        (uint64_t)host->options.timeout_seconds * 1000u;
    int received;
    int result;
    size_t index;
    size_t prepared_capacity;
    unsigned turn_guard_ms = 0u;
    if (system_length > SIZE_MAX - JH_BOOT_RECORD_SIZE) {
        host_log(host, "ERROR", "stock system is too large for this host");
        return EXIT_ARTIFACT;
    }
    prepared_capacity = system_length + JH_BOOT_RECORD_SIZE;
    prepared_bytes = (uint8_t *)malloc(prepared_capacity);
    if (prepared_bytes == NULL) {
        host_log(host, "ERROR", "not enough memory to prepare stock system");
        return EXIT_ARTIFACT;
    }
    result = jh_boot_prepare(system, system_length, 0, 0u, 0u, prepared_bytes,
                             prepared_capacity, &prepared);
    if (result != JH_OK) {
        host_log(host, "ERROR", "system preparation failed: %s",
                 jh_result_name(result));
        free(prepared_bytes);
        return EXIT_ARTIFACT;
    }
    result = jh_boot_session_init(&session, prepared_bytes, prepared.length,
        prepared.load_address, prepared.entry, 0u, 0u, 0);
    if (result != JH_OK) {
        free(prepared_bytes);
        return EXIT_ARTIFACT;
    }
    jh_janet_parser_init(&parser);
    host_log(host, "INFO", "waiting for stock Janet request: %lu bytes, "
             "load=%04X entry=%04X", (unsigned long)prepared.length,
             prepared.load_address, prepared.entry);
    while (!session.complete && !jh_platform_stop_requested() &&
            jh_platform_milliseconds() < deadline) {
        received = host_read(host, incoming, sizeof(incoming), 100u);
        if (received < 0) {
            host_log(host, "ERROR", "serial read during stock boot: %s",
                     strerror(errno));
            free(prepared_bytes);
            return EXIT_SERIAL;
        }
        for (index = 0u; index < (size_t)received; ++index) {
            result = jh_janet_parser_push(&parser, incoming[index], &frame);
            if (result == JH_FRAME) {
                struct jh_boot_output output;
                result = jh_boot_session_input(&session, &frame, &output);
                if (result != JH_OK) {
                    free(prepared_bytes);
                    return EXIT_PROTOCOL;
                }
                if (output.event == JH_BOOT_EVENT_RETRY) {
                    unsigned previous = turn_guard_ms;
                    turn_guard_ms = turn_guard_ms == 0u ? 2u :
                        turn_guard_ms < 5u ? 5u : STOCK_TURN_GUARD_MS;
                    if (turn_guard_ms != previous) {
                        host_log(host, "WARN", "stock client resumed polling; "
                            "turnaround guard increased to %u ms",
                            turn_guard_ms);
                    }
                }
                if (output.length != 0u && host_write_boot_output(
                        host, &output, turn_guard_ms) != 0) {
                    free(prepared_bytes);
                    return EXIT_SERIAL;
                }
                if (output.event == JH_BOOT_EVENT_REQUEST) {
                    host_log(host, "INFO", "Janet request accepted: %02X -> %02X",
                             session.server, session.client);
                } else if (output.completed_records != 0u) {
                    host_log(host, "INFO", "Janet bootstrap %lu/%lu records",
                        (unsigned long)output.completed_records,
                        (unsigned long)(prepared.length / JH_BOOT_RECORD_SIZE));
                }
            }
        }
    }
    if (!session.complete) {
        host_log(host, "ERROR", "stock bootstrap timed out");
        free(prepared_bytes);
        return EXIT_PROTOCOL;
    }
    host_log(host, "INFO", "stock bootstrap complete: sent=%u ACK=%u REJ=%u "
             "turn-guard=%u-ms", session.sent_frames, session.ack_count,
             session.reject_count, turn_guard_ms);
    free(prepared_bytes);
    return EXIT_CLEAN;
}

static int wait_fast_frame(struct host_context *host,
                           struct jh_fast_parser *parser, unsigned timeout_ms,
                           uint8_t *kind, uint8_t *first, uint8_t *second)
{
    uint8_t incoming[256];
    uint64_t deadline = jh_platform_milliseconds() + timeout_ms;
    while (!jh_platform_stop_requested() && jh_platform_milliseconds() < deadline) {
        int received = host_read(host, incoming, sizeof(incoming), 25u);
        size_t index;
        if (received < 0) return -1;
        for (index = 0u; index < (size_t)received; ++index) {
            int result = jh_fast_parser_push(parser, incoming[index], kind,
                                             first, second);
            if (result == JH_FRAME) return 1;
        }
    }
    return 0;
}

static int fast_probe_raw(struct host_context *host, uint8_t first,
                          uint8_t second, uint8_t acknowledgement,
                          uint64_t deadline, unsigned maximum,
                          unsigned *probe_count)
{
    uint8_t probe[3];
    uint8_t incoming[256];
    unsigned count = 0u;
    while (!jh_platform_stop_requested() &&
            jh_platform_milliseconds() < deadline &&
            (maximum == 0u || count < maximum)) {
        size_t length = count == 0u ? 2u : 3u;
        size_t index;
        uint64_t reply_deadline;
        probe[0] = count == 0u ? first : 0u;
        probe[1] = count == 0u ? second : first;
        probe[2] = second;
        for (index = 0u; index < length; ++index) {
            if (host_write(host, probe + index, 1u) != 0) return -1;
            if (index + 1u < length) jh_platform_sleep(1u);
        }
        ++count;
        reply_deadline = jh_platform_milliseconds() + V15_PROBE_REPLY_MS;
        if (reply_deadline > deadline) reply_deadline = deadline;
        while (!jh_platform_stop_requested() &&
                jh_platform_milliseconds() < reply_deadline) {
            int received = host_read(host, incoming, sizeof(incoming), 5u);
            if (received < 0) return -1;
            for (index = 0u; index < (size_t)received; ++index) {
                if (incoming[index] == acknowledgement) {
                    if (probe_count != NULL) *probe_count += count;
                    return 1;
                }
            }
        }
    }
    if (probe_count != NULL) *probe_count += count;
    return 0;
}

static int run_stock_fastboot(struct host_context *host,
                              const uint8_t *artifact,
                              size_t artifact_length,
                              const uint8_t *system, size_t system_length)
{
    struct jh_fast_v15_session session;
    struct jh_fast_parser parser;
    uint8_t *extension_tail = NULL;
    uint8_t kind = 0u;
    uint8_t first = 0u;
    uint8_t second = 0u;
    size_t extension_tail_length = 0u;
    uint64_t deadline;
    unsigned extension_probes = 0u;
    unsigned stream_probes = 0u;
    unsigned extension_retries = 0u;
    int result;

    result = jh_fast_v15_session_init(&session, artifact, artifact_length,
                                      system, system_length);
    if (result != JH_OK) {
        host_log(host, "ERROR", "stock-assisted V15 artifact/system "
                 "validation failed: %s", jh_result_name(result));
        return EXIT_ARTIFACT;
    }
    host_log(host, "INFO", "stock-assisted V15 core: 128 bytes at 9600 8O1; "
             "adaptive turn-guard=0/2/5/10 ms");
    result = run_stock_boot(host, session.core, JH_BOOT_RECORD_SIZE);
    if (result != EXIT_CLEAN) return result;
    if (jh_platform_serial_drain(&host->serial) != 0) return EXIT_SERIAL;
    jh_platform_sleep(50u);
    if (jh_platform_serial_configure(&host->serial, 19200u, 'N') != 0) {
        host_log(host, "ERROR", "cannot enter V15 19200 8N1: %s",
                 strerror(errno));
        return EXIT_SERIAL;
    }
    host_log(host, "INFO", "phase=fastboot-v15 serial=19200 8N1; "
             "waiting adaptively for the acknowledged core");
    deadline = jh_platform_milliseconds() +
        (uint64_t)host->options.timeout_seconds * 1000u;
    extension_tail = (uint8_t *)malloc(
        jh_fast_v15_extension_tail_size(&session));
    if (extension_tail == NULL) return EXIT_ARTIFACT;
    if (jh_fast_v15_extension_tail(
            &session, extension_tail,
            jh_fast_v15_extension_tail_size(&session),
            &extension_tail_length) != JH_OK) {
        free(extension_tail);
        return EXIT_ARTIFACT;
    }

    for (;;) {
        int acknowledged = fast_probe_raw(
            host, 0xa5u, 0x3au, 0xc5u, deadline, 0u, &extension_probes);
        if (acknowledged < 0) {
            free(extension_tail);
            return EXIT_SERIAL;
        }
        if (acknowledged == 0) {
            host_log(host, "ERROR", "V15 core did not acknowledge before "
                     "the boot deadline after %u probes", extension_probes);
            free(extension_tail);
            return EXIT_PROTOCOL;
        }
        host_log(host, "INFO", "V15 core acknowledged after %u probes",
                 extension_probes);
        jh_platform_sleep(V15_EXTENSION_GUARD_MS);
        if (host_write(host, extension_tail, extension_tail_length) != 0 ||
                jh_platform_serial_drain(&host->serial) != 0) {
            free(extension_tail);
            return EXIT_SERIAL;
        }
        jh_fast_parser_init(&parser);
        result = wait_fast_frame(host, &parser, 750u,
                                 &kind, &first, &second);
        if (result < 0) {
            free(extension_tail);
            return EXIT_SERIAL;
        }
        if (result == 1 && kind == (uint8_t)'R' && first == 15u &&
                second == 1u) {
            host_log(host, "INFO", "Fastboot V15 extension ready");
        } else {
            host_log(host, "WARN", "V15 extension ready marker missed; "
                     "probing its overlap-safe stream scanner");
        }
        result = fast_probe_raw(host, (uint8_t)'J', (uint8_t)'Z', 0xc6u,
                                deadline, 64u, &stream_probes);
        if (result < 0) {
            free(extension_tail);
            return EXIT_SERIAL;
        }
        if (result == 1) break;
        ++extension_retries;
        ++host->retries;
        host_log(host, "WARN", "V15 stream scanner absent after %u probes; "
                 "resynchronizing the downloaded extension (retry %u)",
                 stream_probes, extension_retries);
        if (jh_platform_milliseconds() >= deadline) {
            free(extension_tail);
            return EXIT_PROTOCOL;
        }
    }
    free(extension_tail);
    host_log(host, "INFO", "V15 stream header acknowledged after %u probes",
             stream_probes);
    jh_platform_sleep(V15_EXTENSION_GUARD_MS);
    if (host_write(host, session.compressed, session.compressed_length) != 0 ||
            jh_platform_serial_drain(&host->serial) != 0) {
        return EXIT_SERIAL;
    }
    jh_fast_parser_init(&parser);
    result = wait_fast_frame(host, &parser, 1500u,
                             &kind, &first, &second);
    if (result < 0) return EXIT_SERIAL;
    if (result == 1 && kind == (uint8_t)'A' && first == 0u) {
        if (second != 0u) {
            host_log(host, "ERROR", "Fastboot V15 target status=%u", second);
            return EXIT_PROTOCOL;
        }
        host_log(host, "INFO", "Fastboot V15 complete: %lu compressed bytes, "
                 "CRC16/IBM=%04X, extension-retries=%u",
                 (unsigned long)session.compressed_length,
                 session.system_crc, extension_retries);
    } else {
        host_log(host, "WARN", "V15 final reply not seen; no resend, "
                 "NetDisk will confirm the fully drained stream");
    }
    return EXIT_CLEAN;
}

static int run_fastboot(struct host_context *host, const uint8_t *artifact,
                        size_t artifact_length, const uint8_t *system,
                        size_t system_length)
{
    struct jh_fast_session session;
    struct jh_fast_parser parser;
    uint8_t kind = 0u;
    uint8_t first = 0u;
    uint8_t second = 0u;
    uint8_t probe[3];
    uint8_t incoming[256];
    uint8_t *tail;
    size_t probe_length;
    size_t tail_length;
    uint64_t boot_deadline = jh_platform_milliseconds() +
        (uint64_t)host->options.timeout_seconds * 1000u;
    int result;
    unsigned attempt;
    result = jh_fast_session_init(&session, artifact, artifact_length, system,
                                  system_length);
    if (result != JH_OK) {
        host_log(host, "ERROR", "V16 artifact/system validation failed: %s",
                 jh_result_name(result));
        return EXIT_ARTIFACT;
    }
    jh_fast_parser_init(&parser);
    result = wait_fast_frame(host, &parser,
        host->options.timeout_seconds < 3u ?
            host->options.timeout_seconds * 1000u : 3000u,
        &kind, &first, &second);
    if (result < 0) return EXIT_SERIAL;
    if (result == 1 && kind == (uint8_t)'R' && first == 16u && second == 1u) {
        (void)jh_fast_session_ready(&session, kind, first, second);
        host_log(host, "INFO", "Fastboot V16 ready marker received");
    } else {
        (void)jh_fast_session_ready_timeout(&session);
        host_log(host, "WARN", "V16 ready marker missed; probing resident stream scanner");
    }
    for (attempt = 0u; !jh_platform_stop_requested() &&
            jh_platform_milliseconds() < boot_deadline; ++attempt) {
        uint64_t deadline;
        int ack = 0;
        size_t probe_index;
        if (jh_fast_session_probe(&session, probe, &probe_length) != JH_OK) {
            return EXIT_PROTOCOL;
        }
        /* The overlap-safe header is deliberately tiny. Pace its bytes so a
         * simulator PTY relay cannot collapse them onto the one-byte 8251
         * receive register; real UARTs naturally provide this spacing. */
        for (probe_index = 0u; probe_index < probe_length; ++probe_index) {
            if (host_write(host, probe + probe_index, 1u) != 0) {
                return EXIT_SERIAL;
            }
            if (probe_index + 1u < probe_length) jh_platform_sleep(1u);
        }
        deadline = jh_platform_milliseconds() + 25u;
        while (jh_platform_milliseconds() < deadline && !ack) {
            int received = host_read(host, incoming, sizeof(incoming), 5u);
            size_t index;
            if (received < 0) return EXIT_SERIAL;
            for (index = 0u; index < (size_t)received; ++index) {
                if (incoming[index] == 0xc6u) {
                    ack = 1;
                    break;
                }
            }
        }
        if (ack) {
            if (jh_fast_session_header_ack(&session, 0xc6u) != JH_OK) {
                return EXIT_PROTOCOL;
            }
            break;
        }
        if ((attempt + 1u) % 32u == 0u) {
            ++host->retries;
            if (attempt == 31u || (attempt + 1u) % 1024u == 0u) {
                host_log(host, "WARN",
                    "V16 target absent; resident probe attempts=%u",
                    attempt + 1u);
            }
        }
    }
    if (session.state != JH_FAST_SEND_STREAM) {
        host_log(host, "ERROR",
                 "V16 stream header not acknowledged before boot deadline "
                 "after %u probes", attempt);
        return EXIT_PROTOCOL;
    }
    jh_platform_sleep(host->options.reply_guard_ms);
    tail = (uint8_t *)malloc(jh_fast_session_tail_size(&session));
    if (tail == NULL) return EXIT_ARTIFACT;
    result = jh_fast_session_tail(&session, tail,
        jh_fast_session_tail_size(&session), &tail_length);
    if (result != JH_OK || host_write(host, tail, tail_length) != 0) {
        free(tail);
        return EXIT_SERIAL;
    }
    free(tail);
    if (jh_platform_serial_drain(&host->serial) != 0) {
        return EXIT_SERIAL;
    }
    result = wait_fast_frame(host, &parser, 1000u, &kind, &first, &second);
    if (result < 0) return EXIT_SERIAL;
    if (result == 1 && kind == (uint8_t)'A' && first == 0u) {
        if (jh_fast_session_final(&session, kind, first, second) != JH_OK) {
            host_log(host, "ERROR", "V16 target status=%u", second);
            return EXIT_PROTOCOL;
        }
        host_log(host, "INFO", "Fastboot V16 complete: %lu compressed bytes",
                 (unsigned long)session.compressed_length);
    } else if (result == 1 && kind == (uint8_t)'R' && first == 16u &&
            second == 1u) {
        host_log(host, "WARN", "target reset detected during V16 stream");
        return RUN_TARGET_RESET;
    } else {
        if (jh_fast_session_final_timeout(&session) != JH_OK) {
            return EXIT_PROTOCOL;
        }
        host_log(host, "WARN", "V16 final reply not seen; no resend, NetDisk will confirm");
    }
    return EXIT_CLEAN;
}

static uint8_t bcd(unsigned value)
{
    return (uint8_t)(((value / 10u) << 4) | value % 10u);
}

static int clock_value(time_t offset, uint8_t output[5])
{
    time_t current = time(NULL) + offset;
    struct tm epoch_tm;
    struct tm current_tm;
    time_t epoch;
    long days;
    memset(&epoch_tm, 0, sizeof(epoch_tm));
    epoch_tm.tm_year = 78;
    epoch_tm.tm_mon = 0;
    epoch_tm.tm_mday = 1;
    epoch_tm.tm_isdst = -1;
    epoch = mktime(&epoch_tm);
    {
        struct tm *converted = localtime(&current);
        if (epoch == (time_t)-1 || converted == NULL) return -1;
        current_tm = *converted;
    }
    days = (long)((current - epoch) / (24 * 60 * 60)) + 1L;
    if (days < 1L || days > 65535L) return -1;
    output[0] = (uint8_t)days;
    output[1] = (uint8_t)((unsigned long)days >> 8);
    output[2] = bcd((unsigned)current_tm.tm_hour);
    output[3] = bcd((unsigned)current_tm.tm_min);
    output[4] = bcd((unsigned)current_tm.tm_sec);
    return 0;
}

static int apply_clock_set(const uint8_t encoded[4], time_t *offset)
{
    struct tm epoch_tm;
    struct tm target_tm;
    time_t epoch;
    time_t target;
    unsigned days = (unsigned)encoded[0] | (unsigned)encoded[1] << 8;
    unsigned hour = (unsigned)(encoded[2] >> 4) * 10u + (encoded[2] & 15u);
    unsigned minute = (unsigned)(encoded[3] >> 4) * 10u + (encoded[3] & 15u);
    memset(&epoch_tm, 0, sizeof(epoch_tm));
    epoch_tm.tm_year = 78;
    epoch_tm.tm_mon = 0;
    epoch_tm.tm_mday = 1;
    epoch_tm.tm_isdst = -1;
    epoch = mktime(&epoch_tm);
    {
        struct tm *converted = localtime(&epoch);
        if (epoch == (time_t)-1 || converted == NULL) return -1;
        target_tm = *converted;
    }
    target_tm.tm_mday += (int)days - 1;
    target_tm.tm_hour = (int)hour;
    target_tm.tm_min = (int)minute;
    target_tm.tm_sec = 0;
    target_tm.tm_isdst = -1;
    target = mktime(&target_tm);
    if (target == (time_t)-1) return -1;
    *offset = target - time(NULL);
    return 0;
}

static int recover_journal(struct host_context *host, struct jh_media *media,
                           const char *journal_path)
{
    uint8_t *bytes;
    size_t length;
    struct jh_media_transaction transaction;
    if (jh_platform_load_file(journal_path, &bytes, &length) != 0) {
        return errno == ENOENT ? 0 : -1;
    }
    if (jh_journal_decode(bytes, length, &transaction) != JH_OK ||
            jh_media_transaction_recover(&transaction, media) != JH_OK ||
            jh_platform_remove_file(journal_path) != 0) {
        free(bytes);
        return -1;
    }
    host_log(host, "WARN", "recovered interrupted media transaction");
    free(bytes);
    return 0;
}

static int persist_write(struct host_context *host, struct jh_media *media,
                         const struct jh_n3_request *request,
                         const char *journal_path, uint32_t sequence)
{
    struct jh_media_transaction transaction;
    uint8_t encoded[JH_JOURNAL_SIZE];
    int result = jh_media_transaction_prepare(&transaction, media,
        request->track, request->sector, request->payload, sequence);
    if (result != JH_OK) return result == JH_ERR_READ_ONLY ? 0 : -1;
    if (jh_journal_encode(&transaction, encoded) != JH_OK ||
            jh_platform_write_file(journal_path, encoded, sizeof(encoded), 1) != 0 ||
            jh_media_transaction_apply(&transaction, media) != JH_OK ||
            jh_media_transaction_commit(&transaction) != JH_OK ||
            jh_journal_encode(&transaction, encoded) != JH_OK ||
            jh_platform_write_file(journal_path, encoded, sizeof(encoded), 1) != 0 ||
            jh_platform_remove_file(journal_path) != 0) return -1;
    host_log(host, "INFO", "media write seq=%lu track=%u sector=%u",
             (unsigned long)sequence, request->track, request->sector);
    return 0;
}

static int run_disk(struct host_context *host,
                    struct jh_platform_media *volume,
                    struct jh_platform_media *drive_b_file)
{
    struct jh_media drive_a;
    struct jh_media drive_b;
    struct jh_service service;
    struct jh_n3_parser parser;
    struct jh_n3_request request;
    struct jh_service_event event;
    uint8_t incoming[4096];
    uint8_t time_encoded[5];
    uint8_t ready_marker[4] = {'N', 'R', 'N', '3'};
    char journal_path[1024];
    uint64_t started = jh_platform_milliseconds();
    uint64_t next_ready = started;
    time_t clock_offset = 0;
    struct jh_platform_console console;
    int console_open = 0;
    int synchronized = host->options.resume_disk;
    uint32_t write_sequence = 1u;
    int result;
    if (host->options.console_pty != NULL) ready_marker[3] = '4';
    else if (host->options.disk_protocol == 2u) ready_marker[3] = '2';
    else if (host->options.disk_protocol == 1u) ready_marker[2] = 0u;
    if (jh_media_init_backend(&drive_a, volume, JH_N3_VOLUME_SIZE,
            JH_N3_TRACKS, host->options.writable, jh_platform_media_read,
            jh_platform_media_write) != JH_OK) return EXIT_MEDIA;
    if (drive_b_file != NULL && jh_media_init_backend(
            &drive_b, drive_b_file, JH_N3_NATIVE_VOLUME_SIZE,
            JH_N3_NATIVE_TRACKS, 0, jh_platform_media_read,
            jh_platform_media_write) != JH_OK) return EXIT_MEDIA;
    if (snprintf(journal_path, sizeof(journal_path), "%s.jhj",
                 host->options.volume) >= (int)sizeof(journal_path)) {
        return EXIT_MEDIA;
    }
    if (host->options.writable &&
            recover_journal(host, &drive_a, journal_path) != 0) {
        host_log(host, "ERROR", "unsafe or unreadable media journal");
        return EXIT_MEDIA;
    }
    if (jh_service_init(&service, &drive_a,
            drive_b_file == NULL ? NULL : &drive_b,
            host->options.disk_protocol, host->options.read_ahead,
            host->options.console_pty != NULL) != JH_OK) return EXIT_COMMAND;
    console.fd = -1;
    console.file = NULL;
    console.ready_ms = 0u;
    if (host->options.console_pty != NULL) {
        if (jh_platform_console_open(&console, host->options.console_pty) != 0) {
            return EXIT_SERIAL;
        }
        console_open = 1;
    }
    jh_n3_parser_init(&parser);
    host_log(host, "INFO", "serving A: %s, %lu baud 8O1, N%lu%s",
        host->options.writable ? "writable+journal" : "read-only",
        (unsigned long)host->options.disk_baud,
        (unsigned long)host->options.disk_protocol,
        drive_b_file != NULL ? ", read-only native B:" : "");
    while (!jh_platform_stop_requested() &&
            (host->options.disk_timeout_seconds == 0u ||
             jh_platform_milliseconds() - started <
                (uint64_t)host->options.disk_timeout_seconds * 1000u)) {
        uint64_t now = jh_platform_milliseconds();
        int received;
        int recovered = 0;
        size_t index;
        if (!synchronized && now >= next_ready) {
            size_t marker_length = host->options.disk_protocol == 1u ? 2u : 4u;
            if (host_write(host, ready_marker, marker_length) != 0) {
                if (jh_platform_stop_requested()) {
                    result = EXIT_CLEAN;
                    goto done;
                }
                if (reconnect_serial(host, host->options.disk_baud, 'O') != 0) {
                    result = EXIT_SERIAL;
                    goto done;
                }
                jh_n3_parser_init(&parser);
                synchronized = 0;
                next_ready = jh_platform_milliseconds();
                continue;
            }
            next_ready = now + 250u;
        }
        if (console_open) {
            int console_received = jh_platform_console_read(
                &console, incoming, 256u);
            if (console_received > 0 && jh_service_console_input(
                    &service, incoming, (size_t)console_received) != JH_OK) {
                host_log(host, "WARN", "N4 input queue full; input deferred");
            }
        }
        received = host_read(host, incoming, sizeof(incoming), 50u);
        if (received < 0) {
            if (reconnect_serial(host, host->options.disk_baud, 'O') != 0) {
                host_log(host, "ERROR", "disk serial read: %s",
                         strerror(errno));
                result = EXIT_SERIAL;
                goto done;
            }
            jh_n3_parser_init(&parser);
            synchronized = 0;
            next_ready = jh_platform_milliseconds();
            continue;
        }
        for (index = 0u; index < (size_t)received; ++index) {
            int parsed = jh_n3_parser_push(&parser, incoming[index], &request);
            if (parsed == JH_ERR_CHECKSUM || parsed == JH_ERR_UNSUPPORTED ||
                    parsed == JH_ERR_RANGE) {
                ++host->retries;
                continue;
            }
            if (parsed != JH_FRAME) continue;
            synchronized = 1;
            ++host->requests;
            if (!jh_service_is_duplicate(&service, &request) &&
                    (request.operation == JH_N3_WRITE ||
                     request.operation == JH_N3_WRITE_V3) &&
                    request.drive == 0u && host->options.writable) {
                if (persist_write(host, &drive_a, &request, journal_path,
                                  write_sequence++) != 0) {
                    host_log(host, "ERROR", "persistent A: transaction failed");
                    result = EXIT_MEDIA;
                    goto done;
                }
            }
            if (clock_value(clock_offset, time_encoded) != 0) {
                memset(time_encoded, 0, sizeof(time_encoded));
            }
            if (jh_service_handle(&service, &request, time_encoded, &event) !=
                    JH_OK) {
                result = EXIT_PROTOCOL;
                goto done;
            }
            if (event.duplicate) ++host->retries;
            if (host->options.reply_guard_ms != 0u) {
                jh_platform_sleep(host->options.reply_guard_ms);
            }
            if (host_write_disk_reply(host, &request, &event) != 0) {
                if (jh_platform_stop_requested()) {
                    result = EXIT_CLEAN;
                    goto done;
                }
                if (reconnect_serial(host, host->options.disk_baud, 'O') != 0) {
                    result = EXIT_SERIAL;
                    goto done;
                }
                jh_n3_parser_init(&parser);
                synchronized = 0;
                next_ready = jh_platform_milliseconds();
                recovered = 1;
                break;
            }
            if (event.console_output_length != 0u && console_open &&
                    jh_platform_console_write(&console, event.console_output,
                                              event.console_output_length) != 0) {
                result = EXIT_SERIAL;
                goto done;
            }
            if (event.time_set_requested) {
                (void)apply_clock_set(event.time_set, &clock_offset);
            }
            if (request.operation >= JH_N3_READ &&
                    request.operation <= JH_N3_READ_AHEAD) {
                ++host->reads;
                host->read_records += request.operation == JH_N3_READ_AHEAD &&
                    event.reply[3] == 0u ? event.reply[4] : 1u;
            }
            if ((request.operation == JH_N3_WRITE ||
                    request.operation == JH_N3_WRITE_V3) &&
                    event.reply[3] == 0u && !event.duplicate) ++host->writes;
            if (capture_request(host, &request, &event) != 0) {
                result = EXIT_EVIDENCE;
                goto done;
            }
            if (host->options.verbose &&
                    request.operation >= JH_N3_READ &&
                    request.operation <= JH_N3_WRITE_V3) {
                host_log(host, "INFO", "disk op=%02X seq=%02X drive=%u "
                    "track=%u sector=%u status=%u%s", request.operation,
                    request.sequence, request.drive, request.track,
                    request.sector, event.reply[3],
                    event.duplicate ? " duplicate" : "");
            }
        }
        if (recovered) continue;
        jh_platform_idle();
    }
    result = EXIT_CLEAN;
done:
    if (console_open) jh_platform_console_close(&console);
    return result;
}

static int load_boot_artifacts(struct host_context *host, uint8_t **system,
                               size_t *system_length, uint8_t **fast_stage,
                               size_t *fast_stage_length)
{
    int have_fallback = host->options.fallback_system != NULL;
    int loaded = load_verified(host, "system", host->options.system,
        host->options.system_identity, system, system_length,
        have_fallback) == 0;
    if (loaded && host->options.fast_stage != NULL) {
        loaded = load_verified(host, "Fastboot", host->options.fast_stage,
            host->options.fast_stage_identity, fast_stage, fast_stage_length,
            have_fallback) == 0;
    }
    if (loaded) return 0;
    free(*system);
    free(*fast_stage);
    *system = NULL;
    *fast_stage = NULL;
    *system_length = 0u;
    *fast_stage_length = 0u;
    if (!have_fallback) {
        host_log(host, "ERROR", "no valid boot artifact slot remains");
        return -1;
    }
    host_log(host, "WARN", "primary boot slot rejected; trying fallback");
    if (load_verified(host, "fallback system", host->options.fallback_system,
            host->options.fallback_system_identity, system, system_length,
            0) != 0 ||
            load_verified(host, "fallback Fastboot",
                host->options.fallback_fast_stage,
                host->options.fallback_fast_stage_identity, fast_stage,
                fast_stage_length, 0) != 0) {
        free(*system);
        free(*fast_stage);
        *system = NULL;
        *fast_stage = NULL;
        host_log(host, "ERROR", "fallback boot slot rejected");
        return -1;
    }
    host->options.system = host->options.fallback_system;
    host->options.fast_stage = host->options.fallback_fast_stage;
    host->options.system_identity = host->options.fallback_system_identity;
    host->options.fast_stage_identity =
        host->options.fallback_fast_stage_identity;
    host_log(host, "INFO", "fallback boot slot selected");
    return 0;
}

static int open_disk_media(struct host_context *host,
                           struct jh_platform_media *volume,
                           struct jh_platform_media *drive_b,
                           int *have_drive_b)
{
    const struct jh_config_disk *identity = host->options.volume_identity;
    uint8_t ignored_digest[JH_SHA256_SIZE];
    uint32_t size;
    *have_drive_b = 0;
    if (identity != NULL && identity->mode == JH_CONFIG_MEDIA_SNAPSHOT) {
        int saved;
        if (verify_disk_path(host, "A: snapshot base", identity->base,
                             identity) != 0) {
            host_log(host, "ERROR", "invalid A: snapshot base");
            return -1;
        }
        if (jh_platform_file_identity(identity->file, &size,
                                      ignored_digest) == 0) {
            if (size != JH_N3_VOLUME_SIZE) {
                host_log(host, "ERROR", "A: snapshot working copy has wrong size");
                return -1;
            }
            host_log(host, "INFO", "A: resumed snapshot working copy %s",
                     identity->file);
        } else {
            saved = errno;
            if (saved != ENOENT ||
                    jh_platform_copy_file(identity->base, identity->file) != 0) {
                host_log(host, "ERROR", "cannot create A: snapshot %s: %s",
                         identity->file,
                         strerror(saved == ENOENT ? errno : saved));
                return -1;
            }
            host_log(host, "INFO", "A: created snapshot working copy %s",
                     identity->file);
        }
    } else if (verify_disk_path(host, "A:", host->options.volume,
                                identity) != 0) {
        return -1;
    }
    if (jh_platform_media_open(volume, host->options.volume,
            JH_N3_VOLUME_SIZE, host->options.writable, 0) != 0) {
        host_log(host, "ERROR", "A: must be a valid %lu-byte image",
                 (unsigned long)JH_N3_VOLUME_SIZE);
        return -1;
    }
    if (host->options.drive_b == NULL) return 0;
    if (verify_disk_path(host, "B:", host->options.drive_b,
                         host->options.drive_b_identity) != 0 ||
            jh_platform_media_open(drive_b, host->options.drive_b,
                JH_N3_NATIVE_VOLUME_SIZE, 0, 1) != 0) {
        host_log(host, "ERROR", "B: must be a valid native 800 KiB image");
        jh_platform_media_close(volume);
        return -1;
    }
    *have_drive_b = 1;
    return 0;
}

int main(int argc, char **argv)
{
    struct host_context host;
    struct jh_host_config config;
    uint8_t *system = NULL;
    uint8_t *fast_stage = NULL;
    struct jh_platform_media volume;
    struct jh_platform_media drive_b;
    size_t system_length = 0u;
    size_t fast_stage_length = 0u;
    int media_open = 0;
    int have_drive_b = 0;
    uint8_t capture_header[JH_CAPTURE_HEADER_SIZE];
    int parsed;
    int result = EXIT_CLEAN;
    memset(&host, 0, sizeof(host));
    memset(&volume, 0, sizeof(volume));
    memset(&drive_b, 0, sizeof(drive_b));
    host.serial.fd = -1;
    parsed = parse_options(argc, argv, &host.options);
    if (parsed > 0) return EXIT_CLEAN;
    if (parsed < 0) {
        usage(stderr);
        return EXIT_COMMAND;
    }
    if (host.options.selftest) return portable_selftest();
    if (host.options.config_path != NULL && configure_from_file(
            host.options.config_path, &host.options, &config) != 0) {
        return EXIT_COMMAND;
    }
    host.started_ms = jh_platform_milliseconds();
    if (host.options.log != NULL) {
        host.log_file = fopen(host.options.log, "w");
        if (host.log_file == NULL) {
            fprintf(stderr, "jukuhost: cannot open log: %s\n", strerror(errno));
            return EXIT_EVIDENCE;
        }
    }
    if (host.options.capture != NULL) {
        host.capture_file = fopen(host.options.capture, "wb");
        if (host.capture_file == NULL ||
                jh_capture_header(host.started_ms, 0u, capture_header) != JH_OK ||
                fwrite(capture_header, 1u, sizeof(capture_header),
                       host.capture_file) != sizeof(capture_header) ||
                fflush(host.capture_file) != 0) {
            host_log(&host, "ERROR", "cannot initialize capture");
            result = EXIT_EVIDENCE;
            goto cleanup;
        }
        host.capture_ready = 1;
    }
    host_log(&host, "INFO", "start version=%s port=%s", HOST_VERSION,
             host.options.serial != NULL ? host.options.serial : "inherited-fd");
    host_log(&host, "INFO", "platform=%s timer=%s resolution-ms=%u "
             "available-memory=%lu", jh_platform_name(),
             jh_platform_timer_name(),
             jh_platform_timer_resolution_ms(),
             (unsigned long)jh_platform_available_memory());
    if (host.options.config_path != NULL) {
        host_log(&host, "INFO", "configuration=%s", host.options.config_path);
    }
    host_log(&host, "INFO", "phase=artifact-validation");
    if (host.log_error || host.capture_error) {
        result = EXIT_EVIDENCE;
        goto cleanup;
    }
    if (!host.options.boot_only && open_disk_media(
            &host, &volume, &drive_b, &have_drive_b) != 0) {
        result = EXIT_ARTIFACT;
        goto cleanup;
    }
    media_open = !host.options.boot_only;
    if (!host.options.resume_disk && load_boot_artifacts(
            &host, &system, &system_length, &fast_stage,
            &fast_stage_length) != 0) {
        result = EXIT_ARTIFACT;
        goto cleanup;
    }
    jh_platform_install_signals();
    {
        unsigned initial_baud = host.options.resume_disk ?
            host.options.disk_baud : host.options.direct_fastboot ? 19200u : 9600u;
        char initial_parity = host.options.direct_fastboot ? 'N' : 'O';
        host_log(&host, "INFO", "phase=serial-open requested=%u 8%c1 flow=none",
                 initial_baud, initial_parity);
        int opened = host.options.serial_fd >= 0 ?
            jh_platform_serial_adopt(&host.serial, host.options.serial_fd,
                                  "/dev/pts/inherited", initial_baud,
                                  initial_parity) :
            jh_platform_serial_open(&host.serial, host.options.serial,
                                 initial_baud, initial_parity);
        if (opened != 0) {
            host_log(&host, "ERROR", "cannot configure serial: %s",
                     strerror(errno));
            result = EXIT_SERIAL;
            goto cleanup;
        }
    }
    host_log(&host, "INFO", "serial applied=%u 8%c1 flow=none",
             host.serial.baud, host.serial.parity);
    if (host.serial.base_port != 0u) {
        host_log(&host, "INFO", "serial hardware base=%04X fifo-depth=%u",
                 host.serial.base_port, host.serial.fifo_depth);
    }
    if (!host.options.resume_disk) {
        const char *boot_phase = host.options.direct_fastboot ? "fastboot" :
            host.options.fast_stage != NULL ? "stock-fastboot" : "stock-boot";
        host_log(&host, "INFO", "phase=%s", boot_phase);
        for (;;) {
            result = host.options.direct_fastboot ?
                run_fastboot(&host, fast_stage, fast_stage_length,
                             system, system_length) :
                host.options.fast_stage != NULL ?
                run_stock_fastboot(&host, fast_stage, fast_stage_length,
                                   system, system_length) :
                run_stock_boot(&host, system, system_length);
            if (jh_platform_stop_requested()) {
                result = EXIT_CLEAN;
                goto cleanup;
            }
            if (result != RUN_TARGET_RESET) break;
            ++host.target_reset_count;
            if (host.boot_restart_count >= host.options.boot_restarts) {
                host_log(&host, "ERROR",
                    "target-reset recovery exhausted after %lu restarts",
                    host.boot_restart_count);
                result = EXIT_PROTOCOL;
                break;
            }
            ++host.boot_restart_count;
            host_log(&host, "WARN", "restarting complete bootstrap %lu/%lu",
                     host.boot_restart_count,
                     (unsigned long)host.options.boot_restarts);
            host_log(&host, "INFO", "phase=%s", boot_phase);
            if (jh_platform_serial_configure(&host.serial,
                    host.options.direct_fastboot ? 19200u : 9600u,
                    host.options.direct_fastboot ? 'N' : 'O') != 0) {
                result = EXIT_SERIAL;
                break;
            }
        }
        if (result != EXIT_CLEAN) goto cleanup;
        if (host.options.boot_only) goto cleanup;
        if (jh_platform_serial_configure(&host.serial, host.options.disk_baud,
                                      'O') != 0) {
            host_log(&host, "ERROR", "cannot switch to disk framing: %s",
                     strerror(errno));
            result = EXIT_SERIAL;
            goto cleanup;
        }
    } else if (host.serial.parity != 'O' &&
            jh_platform_serial_configure(&host.serial, host.options.disk_baud,
                                      'O') != 0) {
        result = EXIT_SERIAL;
        goto cleanup;
    }
    host_log(&host, "INFO", "phase=netdisk");
    result = run_disk(&host, &volume, have_drive_b ? &drive_b : NULL);
cleanup:
    if (result == EXIT_CLEAN && (host.log_error || host.capture_error)) {
        result = EXIT_EVIDENCE;
    }
    host_log(&host, "INFO", "phase=%s",
             result == EXIT_CLEAN ? "stopped" : "failed");
    host_log(&host, result == EXIT_CLEAN ? "INFO" : "ERROR",
        "stop exit=%d rx=%lu tx=%lu requests=%lu reads=%lu records=%lu "
        "writes=%lu "
        "retries=%lu boot-restarts=%lu target-resets=%lu reconnects=%lu "
        "uart-errors=%lu available-memory=%lu",
        result, host.rx_bytes, host.tx_bytes, host.requests, host.reads,
        host.read_records, host.writes, host.retries, host.boot_restart_count,
        host.target_reset_count, host.reconnect_count,
        host.serial_line_errors + host.serial.line_errors,
        (unsigned long)jh_platform_available_memory());
    if (result == EXIT_CLEAN && (host.log_error || host.capture_error)) {
        result = EXIT_EVIDENCE;
        fprintf(stderr, "jukuhost: required evidence stream failed\n");
    }
    jh_platform_serial_close(&host.serial);
    if (host.capture_file != NULL) {
        fflush(host.capture_file);
        fclose(host.capture_file);
    }
    if (host.log_file != NULL) fclose(host.log_file);
    if (media_open) {
        if (have_drive_b) jh_platform_media_close(&drive_b);
        jh_platform_media_close(&volume);
    }
    free(fast_stage);
    free(system);
    return result;
}
