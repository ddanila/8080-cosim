#define _POSIX_C_SOURCE 200809L

#include "jukuhost.h"
#include "platform_posix.h"

#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#define HOST_VERSION "0.1.0-m2"

enum exit_code {
    EXIT_CLEAN = 0,
    EXIT_COMMAND = 2,
    EXIT_ARTIFACT = 3,
    EXIT_SERIAL = 4,
    EXIT_PROTOCOL = 5,
    EXIT_MEDIA = 6
};

struct options {
    const char *serial;
    const char *system;
    const char *fast_stage;
    const char *volume;
    const char *drive_b;
    const char *console_pty;
    const char *log;
    const char *capture;
    unsigned timeout_seconds;
    unsigned disk_timeout_seconds;
    unsigned disk_protocol;
    unsigned disk_baud;
    unsigned read_ahead;
    unsigned reply_guard_ms;
    int direct_fastboot;
    int resume_disk;
    int writable;
    int verbose;
};

struct host_context {
    struct options options;
    struct jh_posix_serial serial;
    FILE *log_file;
    FILE *capture_file;
    uint64_t started_ms;
    unsigned long rx_bytes;
    unsigned long tx_bytes;
    unsigned long requests;
    unsigned long retries;
    unsigned long reads;
    unsigned long writes;
};

static void usage(FILE *file)
{
    fprintf(file,
        "usage: jukuhost --serial DEVICE --system FILE --volume FILE [options]\n"
        "\n"
        "Boot options:\n"
        "  --fast-stage FILE       current JF16 bundle\n"
        "  --network-rom           C8 automatic/direct Fastboot V16\n"
        "  --direct-fastboot       synonym for --network-rom\n"
        "  --resume-disk           attach to an already running system\n"
        "  --timeout SECONDS       boot deadline (default 120)\n"
        "\n"
        "Disk and console:\n"
        "  --drive-b FILE          read-only native 800 KiB .JUK image\n"
        "  --writable              persist A: through the crash journal\n"
        "  --disk-protocol 1|2|3  default 3\n"
        "  --disk-baud RATE        default 19200\n"
        "  --read-ahead 1..8       default 3\n"
        "  --console-pty DEVICE    enable N4 remote console\n"
        "  --disk-timeout SECONDS  zero means run until stopped\n"
        "\n"
        "Evidence:\n"
        "  --log FILE              text log (console is always used)\n"
        "  --capture FILE          CRC-protected exact-byte capture\n"
        "  --verbose               log individual disk requests\n"
        "  --version               print version\n");
}

static int parse_unsigned(const char *text, unsigned minimum, unsigned maximum,
                          unsigned *result)
{
    char *end;
    unsigned long value;
    errno = 0;
    value = strtoul(text, &end, 10);
    if (errno != 0 || *text == '\0' || *end != '\0' ||
            value < minimum || value > maximum) return -1;
    *result = (unsigned)value;
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
    options->disk_protocol = 3u;
    options->disk_baud = 19200u;
    options->read_ahead = 3u;
    options->reply_guard_ms = 2u;
    for (index = 1; index < argc; ++index) {
        const char *argument = argv[index];
        const char *value;
        if (strcmp(argument, "--help") == 0) {
            usage(stdout);
            return 1;
        } else if (strcmp(argument, "--version") == 0) {
            printf("jukuhost %s\n", HOST_VERSION);
            return 1;
        } else if (strcmp(argument, "--serial") == 0) {
            if (require_value(argc, argv, &index, &options->serial) != 0) return -1;
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
        } else if (strcmp(argument, "--writable") == 0) {
            options->writable = 1;
        } else if (strcmp(argument, "--verbose") == 0) {
            options->verbose = 1;
        } else if (strcmp(argument, "--timeout") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 1u, 86400u,
                                   &options->timeout_seconds) != 0) return -1;
        } else if (strcmp(argument, "--disk-timeout") == 0) {
            if (require_value(argc, argv, &index, &value) != 0 ||
                    parse_unsigned(value, 0u, 86400u,
                                   &options->disk_timeout_seconds) != 0) return -1;
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
    if (options->serial == NULL || options->volume == NULL ||
            (!options->resume_disk && options->system == NULL)) return -1;
    if (options->direct_fastboot && options->fast_stage == NULL) return -1;
    if (options->fast_stage != NULL && !options->direct_fastboot) {
        fprintf(stderr,
            "jukuhost: legacy stock-loaded Fastboot V1-V15 is not an admitted "
            "production runtime; use stock boot or the C8 V16 network ROM\n");
        return -1;
    }
    if (options->console_pty != NULL && options->disk_protocol != 3u) return -1;
    return 0;
}

static void host_log(struct host_context *host, const char *level,
                     const char *format, ...)
{
    char message[1024];
    va_list arguments;
    unsigned long elapsed = (unsigned long)(jh_posix_milliseconds() -
                                             host->started_ms);
    va_start(arguments, format);
    (void)vsnprintf(message, sizeof(message), format, arguments);
    va_end(arguments);
    printf("%08lu %-5s %s\n", elapsed, level, message);
    fflush(stdout);
    if (host->log_file != NULL) {
        fprintf(host->log_file, "%08lu %-5s %s\n", elapsed, level, message);
        fflush(host->log_file);
    }
}

static int capture_record(struct host_context *host, enum jh_capture_type type,
                          const uint8_t *data, size_t length)
{
    uint8_t *encoded;
    size_t encoded_length;
    int result;
    if (host->capture_file == NULL) return 0;
    encoded = (uint8_t *)malloc(length + JH_CAPTURE_RECORD_OVERHEAD);
    if (encoded == NULL) return -1;
    result = jh_capture_encode(type, 0u,
        jh_posix_milliseconds() - host->started_ms, data, length, encoded,
        length + JH_CAPTURE_RECORD_OVERHEAD, &encoded_length);
    if (result != JH_OK ||
            fwrite(encoded, 1u, encoded_length, host->capture_file) !=
            encoded_length) {
        free(encoded);
        return -1;
    }
    free(encoded);
    return 0;
}

static int host_write(struct host_context *host, const uint8_t *data,
                      size_t length)
{
    if (jh_posix_serial_write(&host->serial, data, length, 10000u) != 0) {
        return -1;
    }
    host->tx_bytes += (unsigned long)length;
    return capture_record(host, JH_CAPTURE_TX, data, length);
}

static int host_read(struct host_context *host, uint8_t *data, size_t capacity,
                     unsigned timeout_ms)
{
    int received = jh_posix_serial_read(&host->serial, data, capacity, timeout_ms);
    if (received > 0) {
        host->rx_bytes += (unsigned long)received;
        if (capture_record(host, JH_CAPTURE_RX, data, (size_t)received) != 0) {
            return -1;
        }
    }
    return received;
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
    uint64_t deadline = jh_posix_milliseconds() +
        (uint64_t)host->options.timeout_seconds * 1000u;
    int received;
    int result;
    size_t index;
    prepared_bytes = (uint8_t *)malloc(65536u);
    if (prepared_bytes == NULL) return EXIT_ARTIFACT;
    result = jh_boot_prepare(system, system_length, 0, 0u, 0u, prepared_bytes,
                             65536u, &prepared);
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
    while (!session.complete && !jh_posix_stop_requested() &&
            jh_posix_milliseconds() < deadline) {
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
                if (output.length != 0u &&
                        host_write(host, output.bytes, output.length) != 0) {
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
    host_log(host, "INFO", "stock bootstrap complete: sent=%u ACK=%u REJ=%u",
             session.sent_frames, session.ack_count, session.reject_count);
    free(prepared_bytes);
    return EXIT_CLEAN;
}

static int wait_fast_frame(struct host_context *host,
                           struct jh_fast_parser *parser, unsigned timeout_ms,
                           uint8_t *kind, uint8_t *first, uint8_t *second)
{
    uint8_t incoming[256];
    uint64_t deadline = jh_posix_milliseconds() + timeout_ms;
    while (!jh_posix_stop_requested() && jh_posix_milliseconds() < deadline) {
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
    result = wait_fast_frame(host, &parser, 3000u, &kind, &first, &second);
    if (result < 0) return EXIT_SERIAL;
    if (result == 1 && kind == (uint8_t)'R' && first == 16u && second == 1u) {
        (void)jh_fast_session_ready(&session, kind, first, second);
        host_log(host, "INFO", "Fastboot V16 ready marker received");
    } else {
        (void)jh_fast_session_ready_timeout(&session);
        host_log(host, "WARN", "V16 ready marker missed; probing resident stream scanner");
    }
    for (attempt = 0u; attempt < 32u; ++attempt) {
        uint64_t deadline;
        int ack = 0;
        if (jh_fast_session_probe(&session, probe, &probe_length) != JH_OK ||
                host_write(host, probe, probe_length) != 0) return EXIT_SERIAL;
        deadline = jh_posix_milliseconds() + 25u;
        while (jh_posix_milliseconds() < deadline && !ack) {
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
    }
    if (session.state != JH_FAST_SEND_STREAM) {
        host_log(host, "ERROR", "V16 stream header not acknowledged after 32 probes");
        return EXIT_PROTOCOL;
    }
    jh_posix_sleep(host->options.reply_guard_ms);
    tail = (uint8_t *)malloc(jh_fast_session_tail_size(&session));
    if (tail == NULL) return EXIT_ARTIFACT;
    result = jh_fast_session_tail(&session, tail,
        jh_fast_session_tail_size(&session), &tail_length);
    if (result != JH_OK || host_write(host, tail, tail_length) != 0) {
        free(tail);
        return EXIT_SERIAL;
    }
    free(tail);
    result = wait_fast_frame(host, &parser, 1000u, &kind, &first, &second);
    if (result < 0) return EXIT_SERIAL;
    if (result == 1 && kind == (uint8_t)'A' && first == 0u) {
        if (jh_fast_session_final(&session, kind, first, second) != JH_OK) {
            host_log(host, "ERROR", "V16 target status=%u", second);
            return EXIT_PROTOCOL;
        }
        host_log(host, "INFO", "Fastboot V16 complete: %lu compressed bytes",
                 (unsigned long)session.compressed_length);
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
    if (epoch == (time_t)-1 || localtime_r(&current, &current_tm) == NULL) return -1;
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
    if (epoch == (time_t)-1 || localtime_r(&epoch, &target_tm) == NULL) return -1;
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
    if (jh_posix_load_file(journal_path, &bytes, &length) != 0) {
        return errno == ENOENT ? 0 : -1;
    }
    if (jh_journal_decode(bytes, length, &transaction) != JH_OK ||
            jh_media_transaction_recover(&transaction, media) != JH_OK ||
            jh_posix_pwrite_record(host->options.volume, transaction.offset,
                                   media->bytes + transaction.offset,
                                   JH_N3_RECORD_SIZE) != 0 ||
            jh_posix_remove_file(journal_path) != 0) {
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
            jh_posix_write_file(journal_path, encoded, sizeof(encoded), 1) != 0 ||
            jh_media_transaction_apply(&transaction, media) != JH_OK ||
            jh_posix_pwrite_record(host->options.volume, transaction.offset,
                                   transaction.after, JH_N3_RECORD_SIZE) != 0 ||
            jh_media_transaction_commit(&transaction) != JH_OK ||
            jh_journal_encode(&transaction, encoded) != JH_OK ||
            jh_posix_write_file(journal_path, encoded, sizeof(encoded), 1) != 0 ||
            jh_posix_remove_file(journal_path) != 0) return -1;
    return 0;
}

static int run_disk(struct host_context *host, uint8_t *volume,
                    uint8_t *drive_b_bytes)
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
    uint64_t started = jh_posix_milliseconds();
    uint64_t next_ready = started;
    time_t clock_offset = 0;
    int console_fd = -1;
    int synchronized = host->options.resume_disk;
    uint32_t write_sequence = 1u;
    int result;
    if (host->options.console_pty != NULL) ready_marker[3] = '4';
    else if (host->options.disk_protocol == 2u) ready_marker[3] = '2';
    else if (host->options.disk_protocol == 1u) ready_marker[2] = 0u;
    if (jh_media_init(&drive_a, volume, JH_N3_VOLUME_SIZE, JH_N3_TRACKS,
                      host->options.writable) != JH_OK) return EXIT_MEDIA;
    if (drive_b_bytes != NULL &&
            jh_media_init(&drive_b, drive_b_bytes, JH_N3_NATIVE_VOLUME_SIZE,
                          JH_N3_NATIVE_TRACKS, 0) != JH_OK) return EXIT_MEDIA;
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
            drive_b_bytes == NULL ? NULL : &drive_b,
            host->options.disk_protocol, host->options.read_ahead,
            host->options.console_pty != NULL) != JH_OK) return EXIT_COMMAND;
    if (host->options.console_pty != NULL) {
        console_fd = jh_posix_open_console(host->options.console_pty);
        if (console_fd < 0) return EXIT_SERIAL;
    }
    jh_n3_parser_init(&parser);
    host_log(host, "INFO", "serving A: %s, %u baud 8O1, N%u%s",
        host->options.writable ? "writable+journal" : "read-only",
        host->options.disk_baud, host->options.disk_protocol,
        drive_b_bytes != NULL ? ", read-only native B:" : "");
    while (!jh_posix_stop_requested() &&
            (host->options.disk_timeout_seconds == 0u ||
             jh_posix_milliseconds() - started <
                (uint64_t)host->options.disk_timeout_seconds * 1000u)) {
        uint64_t now = jh_posix_milliseconds();
        int received;
        size_t index;
        if (!synchronized && now >= next_ready) {
            size_t marker_length = host->options.disk_protocol == 1u ? 2u : 4u;
            if (host_write(host, ready_marker, marker_length) != 0) {
                result = EXIT_SERIAL;
                goto done;
            }
            next_ready = now + 250u;
        }
        if (console_fd >= 0) {
            ssize_t console_received = read(console_fd, incoming, 256u);
            if (console_received > 0 && jh_service_console_input(
                    &service, incoming, (size_t)console_received) != JH_OK) {
                host_log(host, "WARN", "N4 input queue full; input deferred");
            }
        }
        received = host_read(host, incoming, sizeof(incoming), 50u);
        if (received < 0) {
            host_log(host, "ERROR", "disk serial read: %s", strerror(errno));
            result = EXIT_SERIAL;
            goto done;
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
                jh_posix_sleep(host->options.reply_guard_ms);
            }
            if (host_write(host, event.reply, event.reply_length) != 0) {
                result = EXIT_SERIAL;
                goto done;
            }
            if (event.console_output_length != 0u && console_fd >= 0 &&
                    write(console_fd, event.console_output,
                          event.console_output_length) < 0 &&
                    errno != EAGAIN) {
                result = EXIT_SERIAL;
                goto done;
            }
            if (event.time_set_requested) {
                (void)apply_clock_set(event.time_set, &clock_offset);
            }
            if (request.operation >= JH_N3_READ &&
                    request.operation <= JH_N3_READ_AHEAD) ++host->reads;
            if ((request.operation == JH_N3_WRITE ||
                    request.operation == JH_N3_WRITE_V3) &&
                    event.reply[3] == 0u && !event.duplicate) ++host->writes;
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
    }
    result = EXIT_CLEAN;
done:
    if (console_fd >= 0) (void)close(console_fd);
    return result;
}

int main(int argc, char **argv)
{
    struct host_context host;
    uint8_t *system = NULL;
    uint8_t *fast_stage = NULL;
    uint8_t *volume = NULL;
    uint8_t *drive_b_image = NULL;
    uint8_t *drive_b = NULL;
    size_t system_length = 0u;
    size_t fast_stage_length = 0u;
    size_t volume_length = 0u;
    size_t drive_b_length = 0u;
    uint8_t capture_header[JH_CAPTURE_HEADER_SIZE];
    int parsed;
    int result = EXIT_CLEAN;
    memset(&host, 0, sizeof(host));
    host.serial.fd = -1;
    parsed = parse_options(argc, argv, &host.options);
    if (parsed > 0) return EXIT_CLEAN;
    if (parsed < 0) {
        usage(stderr);
        return EXIT_COMMAND;
    }
    host.started_ms = jh_posix_milliseconds();
    if (host.options.log != NULL) {
        host.log_file = fopen(host.options.log, "w");
        if (host.log_file == NULL) {
            fprintf(stderr, "jukuhost: cannot open log: %s\n", strerror(errno));
            return EXIT_COMMAND;
        }
    }
    if (host.options.capture != NULL) {
        host.capture_file = fopen(host.options.capture, "wb");
        if (host.capture_file == NULL ||
                jh_capture_header(host.started_ms, 0u, capture_header) != JH_OK ||
                fwrite(capture_header, 1u, sizeof(capture_header),
                       host.capture_file) != sizeof(capture_header)) {
            host_log(&host, "ERROR", "cannot initialize capture");
            result = EXIT_COMMAND;
            goto cleanup;
        }
    }
    host_log(&host, "INFO", "start version=%s port=%s", HOST_VERSION,
             host.options.serial);
    if (jh_posix_load_file(host.options.volume, &volume, &volume_length) != 0 ||
            volume_length != JH_N3_VOLUME_SIZE) {
        host_log(&host, "ERROR", "A: must be exactly %u bytes",
                 (unsigned)JH_N3_VOLUME_SIZE);
        result = EXIT_ARTIFACT;
        goto cleanup;
    }
    if (host.options.system != NULL &&
            jh_posix_load_file(host.options.system, &system, &system_length) != 0) {
        host_log(&host, "ERROR", "cannot load system: %s", strerror(errno));
        result = EXIT_ARTIFACT;
        goto cleanup;
    }
    if (host.options.fast_stage != NULL &&
            jh_posix_load_file(host.options.fast_stage, &fast_stage,
                               &fast_stage_length) != 0) {
        host_log(&host, "ERROR", "cannot load Fastboot artifact: %s",
                 strerror(errno));
        result = EXIT_ARTIFACT;
        goto cleanup;
    }
    if (host.options.drive_b != NULL) {
        if (jh_posix_load_file(host.options.drive_b, &drive_b_image,
                               &drive_b_length) != 0 ||
                drive_b_length != JH_N3_NATIVE_VOLUME_SIZE) {
            host_log(&host, "ERROR", "B: must be a native 800 KiB image");
            result = EXIT_ARTIFACT;
            goto cleanup;
        }
        drive_b = (uint8_t *)malloc(JH_N3_NATIVE_VOLUME_SIZE);
        if (drive_b == NULL || jh_native_image_to_volume(
                drive_b_image, drive_b_length, drive_b,
                JH_N3_NATIVE_VOLUME_SIZE) != JH_OK) {
            result = EXIT_ARTIFACT;
            goto cleanup;
        }
    }
    jh_posix_install_signals();
    if (jh_posix_serial_open(&host.serial, host.options.serial,
            host.options.resume_disk ? host.options.disk_baud :
            host.options.direct_fastboot ? 19200u : 9600u,
            host.options.direct_fastboot ? 'N' : 'O') != 0) {
        host_log(&host, "ERROR", "cannot configure serial: %s", strerror(errno));
        result = EXIT_SERIAL;
        goto cleanup;
    }
    host_log(&host, "INFO", "serial applied=%u 8%c1 flow=none",
             host.serial.baud, host.serial.parity);
    if (!host.options.resume_disk) {
        result = host.options.direct_fastboot ?
            run_fastboot(&host, fast_stage, fast_stage_length,
                         system, system_length) :
            run_stock_boot(&host, system, system_length);
        if (result != EXIT_CLEAN) goto cleanup;
        if (jh_posix_serial_configure(&host.serial, host.options.disk_baud,
                                      'O') != 0) {
            host_log(&host, "ERROR", "cannot switch to disk framing: %s",
                     strerror(errno));
            result = EXIT_SERIAL;
            goto cleanup;
        }
    } else if (host.serial.parity != 'O' &&
            jh_posix_serial_configure(&host.serial, host.options.disk_baud,
                                      'O') != 0) {
        result = EXIT_SERIAL;
        goto cleanup;
    }
    result = run_disk(&host, volume, drive_b);
cleanup:
    host_log(&host, result == EXIT_CLEAN ? "INFO" : "ERROR",
        "stop exit=%d rx=%lu tx=%lu requests=%lu reads=%lu writes=%lu retries=%lu",
        result, host.rx_bytes, host.tx_bytes, host.requests, host.reads,
        host.writes, host.retries);
    jh_posix_serial_close(&host.serial);
    if (host.capture_file != NULL) {
        fflush(host.capture_file);
        fclose(host.capture_file);
    }
    if (host.log_file != NULL) fclose(host.log_file);
    free(drive_b);
    free(drive_b_image);
    free(volume);
    free(fast_stage);
    free(system);
    return result;
}
