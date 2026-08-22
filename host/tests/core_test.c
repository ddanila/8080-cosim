#include "jukuhost.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "CORE-TEST: FAIL at %s:%d: %s\n", \
                __FILE__, __LINE__, #condition); \
        return 1; \
    } \
} while (0)

static int hex_digit(int value)
{
    if (value >= '0' && value <= '9') return value - '0';
    if (value >= 'a' && value <= 'f') return value - 'a' + 10;
    if (value >= 'A' && value <= 'F') return value - 'A' + 10;
    return -1;
}

static int fixture_hex(const char *path, const char *key,
                       uint8_t *output, size_t capacity, size_t *length)
{
    FILE *file = fopen(path, "rb");
    char line[1024];
    size_t key_length = strlen(key);
    if (file == NULL) return 0;
    while (fgets(line, sizeof(line), file) != NULL) {
        char *value;
        size_t value_length;
        size_t index;
        if (strncmp(line, key, key_length) != 0 || line[key_length] != '=') {
            continue;
        }
        value = line + key_length + 1u;
        value_length = strcspn(value, "\r\n");
        if ((value_length & 1u) != 0u || value_length / 2u > capacity) {
            fclose(file);
            return 0;
        }
        for (index = 0u; index < value_length; index += 2u) {
            int high = hex_digit((unsigned char)value[index]);
            int low = hex_digit((unsigned char)value[index + 1u]);
            if (high < 0 || low < 0) {
                fclose(file);
                return 0;
            }
            output[index / 2u] = (uint8_t)((unsigned)high << 4 | (unsigned)low);
        }
        *length = value_length / 2u;
        fclose(file);
        return 1;
    }
    fclose(file);
    return 0;
}

static int test_checksums(void)
{
    static const uint8_t text[] = "123456789";
    static const uint8_t abc[] = "abc";
    static const char abc_sha[] =
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    uint8_t range[16];
    uint8_t digest[JH_SHA256_SIZE];
    uint8_t parsed[JH_SHA256_SIZE];
    char formatted[JH_SHA256_HEX_SIZE + 1u];
    uint8_t sum1;
    uint8_t sum2;
    size_t index;
    for (index = 0u; index < sizeof(range); ++index) range[index] = (uint8_t)index;
    CHECK(jh_crc16_ccitt(text, sizeof(text) - 1u, UINT16_C(0xffff)) ==
          UINT16_C(0x29b1));
    CHECK(jh_crc16_ibm(text, sizeof(text) - 1u, 0u) == UINT16_C(0xbb3d));
    jh_fletcher16(range, sizeof(range), &sum1, &sum2);
    CHECK(sum1 == 0x78u && sum2 == 0xaau);
    jh_sha256(abc, sizeof(abc) - 1u, digest);
    jh_sha256_format(digest, formatted);
    CHECK(strcmp(formatted, abc_sha) == 0);
    CHECK(jh_sha256_parse(abc_sha, parsed) == JH_OK);
    CHECK(memcmp(parsed, digest, sizeof(digest)) == 0);
    CHECK(jh_sha256_parse("xyz", parsed) == JH_ERR_ARGUMENT);
    return 0;
}

static int test_configuration(void)
{
    static const char hash[] =
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    static const char valid[] =
        "# portable host fixture\n"
        "[host]\n"
        "port=/dev/ttyS0\n"
        "log=JUKUHOST.LOG\n"
        "capture=JUKUHOST.CAP\n"
        "console=/dev/pts/7\n"
        "network_rom=yes\n"
        "timeout=90\n"
        "disk_timeout=0\n"
        "boot_restarts=4\n"
        "reconnect_timeout=12\n"
        "[network]\n"
        "protocol=3\n"
        "baud=19200\n"
        "read_ahead=8\n"
        "reply_guard_ms=2\n"
        "[system]\n"
        "file=SYSTEM.BIN\n"
        "size=18432\n"
        "sha256=ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\n"
        "[fastboot]\n"
        "file=FAST16.BIN\n"
        "size=7806\n"
        "sha256=ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\n"
        "[fallback_system]\n"
        "file=SYSTEM2.BIN\n"
        "size=18432\n"
        "sha256=ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\n"
        "[fallback_fastboot]\n"
        "file=FAST162.BIN\n"
        "size=7807\n"
        "sha256=ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\n"
        "[disk_a]\n"
        "base=BASE.IMG\n"
        "file=WORK.IMG\n"
        "size=409600\n"
        "sha256=ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\n"
        "geometry=juku-cpm3\n"
        "mode=snapshot\n"
        "[disk_b]\n"
        "file=APPS.JUK\n"
        "size=819200\n"
        "sha256=ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad\n"
        "geometry=juku-native\n"
        "writable=no\n";
    static const char duplicate[] =
        "[host]\nport=x\nport=y\n";
    static const char unknown[] =
        "[host]\nport=x\nfuture=surprise\n";
    struct jh_host_config config;
    struct jh_config_error error;
    char oversized[JH_CONFIG_PATH_MAX + 32u];
    char stock_fast[sizeof(valid)];
    const char *network_line;
    CHECK(jh_config_parse(valid, sizeof(valid) - 1u, &config, &error) == JH_OK);
    CHECK(strcmp(config.port, "/dev/ttyS0") == 0 && config.network_rom == 1 &&
          config.timeout_seconds == 90u && config.disk_timeout_seconds == 0u &&
          config.boot_restarts == 4u &&
          config.reconnect_timeout_seconds == 12u &&
          config.disk_protocol == 3u && config.disk_baud == 19200u &&
          config.read_ahead == 8u && config.have_fastboot &&
          config.have_fallback && config.disk_a.present &&
          config.disk_a.mode == JH_CONFIG_MEDIA_SNAPSHOT &&
          strcmp(config.disk_a.base, "BASE.IMG") == 0 &&
          config.disk_b.present &&
          config.disk_b.mode == JH_CONFIG_MEDIA_READ_ONLY &&
          memcmp(config.system.sha256, config.disk_a.sha256,
                 JH_SHA256_SIZE) == 0);
    network_line = strstr(valid, "network_rom=yes\n");
    CHECK(network_line != NULL);
    memcpy(stock_fast, valid, (size_t)(network_line - valid));
    strcpy(stock_fast + (network_line - valid),
           network_line + strlen("network_rom=yes\n"));
    CHECK(jh_config_parse(stock_fast, strlen(stock_fast), &config, &error) ==
          JH_OK);
    CHECK(config.have_fastboot && !config.network_rom);
    CHECK(jh_sha256_parse(hash, config.system.sha256) == JH_OK);
    CHECK(jh_config_parse(duplicate, sizeof(duplicate) - 1u,
                          &config, &error) == JH_ERR_FORMAT && error.line == 3u);
    CHECK(jh_config_parse(unknown, sizeof(unknown) - 1u,
                          &config, &error) == JH_ERR_UNSUPPORTED &&
          error.line == 3u);
    memset(oversized, 'x', sizeof(oversized));
    oversized[0] = '[';
    oversized[sizeof(oversized) - 1u] = '\n';
    CHECK(jh_config_parse(oversized, sizeof(oversized), &config, &error) ==
          JH_ERR_RANGE && error.line == 1u);
    return 0;
}

static int test_janet(const char *fixture)
{
    uint8_t expected[JH_JANET_MAX_FRAME];
    uint8_t encoded[JH_JANET_MAX_FRAME];
    uint8_t damaged[JH_JANET_MAX_FRAME];
    static const uint8_t truncated_data_header[] = {
        0xe4u, 0xe4u, 0x02u, 0x01u, 0x07u
    };
    uint8_t poll[JH_JANET_MAX_FRAME];
    size_t expected_length;
    size_t encoded_length;
    size_t poll_length;
    size_t index;
    size_t repeat;
    struct jh_janet_parser parser;
    struct jh_janet_frame frame;
    int result = JH_NEED_MORE;
    CHECK(fixture_hex(fixture, "janet_data_01_02_abc", expected,
                      sizeof(expected), &expected_length));
    CHECK(jh_janet_encode(1u, 2u, 7u, (const uint8_t *)"abc", 3u,
                          encoded, sizeof(encoded), &encoded_length) == JH_OK);
    CHECK(encoded_length == expected_length);
    CHECK(memcmp(encoded, expected, encoded_length) == 0);
    jh_janet_parser_init(&parser);
    CHECK(jh_janet_parser_push(&parser, 0x00u, &frame) == JH_NEED_MORE);
    CHECK(jh_janet_parser_push(&parser, 0xe4u, &frame) == JH_NEED_MORE);
    for (index = 0u; index < encoded_length; ++index) {
        result = jh_janet_parser_push(&parser, encoded[index], &frame);
    }
    CHECK(result == JH_FRAME);
    CHECK(frame.destination == 1u && frame.source == 2u && frame.control == 7u);
    CHECK(frame.payload_length == 3u && memcmp(frame.payload, "abc", 3u) == 0);

    memcpy(damaged, encoded, encoded_length);
    damaged[6] ^= 1u;
    jh_janet_parser_init(&parser);
    for (index = 0u; index < encoded_length; ++index) {
        result = jh_janet_parser_push(&parser, damaged[index], &frame);
    }
    CHECK(result == JH_ERR_CHECKSUM);
    for (index = 0u; index < encoded_length; ++index) {
        result = jh_janet_parser_push(&parser, encoded[index], &frame);
    }
    CHECK(result == JH_FRAME);

    /*
     * Physical EK37 capture: a truncated data header was immediately
     * followed by repeated directed polls.  The header consumed the next E4
     * as a length of 228; recovery must select the newest partial sync, not
     * the first complete poll buried in the rejected buffer.
     */
    CHECK(jh_janet_encode(2u, 1u, 0x0cu, NULL, 0u,
                          poll, sizeof(poll), &poll_length) == JH_OK);
    CHECK(poll_length == 6u);
    jh_janet_parser_init(&parser);
    for (index = 0u; index < sizeof(truncated_data_header); ++index) {
        result = jh_janet_parser_push(&parser, truncated_data_header[index],
                                      &frame);
    }
    CHECK(result == JH_NEED_MORE);
    result = JH_NEED_MORE;
    for (repeat = 0u; repeat < 48u && result != JH_FRAME; ++repeat) {
        for (index = 0u; index < poll_length; ++index) {
            result = jh_janet_parser_push(&parser, poll[index], &frame);
            CHECK(result == JH_NEED_MORE || result == JH_ERR_CHECKSUM ||
                  result == JH_FRAME);
            if (result == JH_FRAME) {
                break;
            }
        }
    }
    CHECK(result == JH_FRAME);
    CHECK(frame.destination == 2u && frame.source == 1u &&
          frame.control == 0x0cu && frame.payload_length == 0u);
    return 0;
}

static int test_fastboot(const char *fixture)
{
    uint8_t expected[16];
    uint8_t encoded[16];
    uint8_t artifact[136u + 256u];
    uint8_t artifact_v15[128u + 256u + 8u + 256u];
    uint8_t system_image[10240];
    uint8_t stream_tail[260];
    uint8_t extension_tail[258];
    uint8_t probe[3];
    uint8_t payload[2] = {16u, 1u};
    const uint8_t *decoded_payload;
    const uint8_t *core;
    const uint8_t *compressed;
    size_t expected_length;
    size_t encoded_length;
    size_t decoded_length;
    size_t compressed_length;
    uint16_t system_crc;
    uint16_t payload_crc;
    uint8_t kind;
    uint8_t first;
    uint8_t second;
    struct jh_fast_parser parser;
    struct jh_fast_session session;
    struct jh_fast_v15_session session_v15;
    size_t probe_length;
    size_t stream_tail_length;
    uint16_t resident_crc;
    uint16_t compressed_crc;
    int result = JH_NEED_MORE;
    size_t index;
    CHECK(fixture_hex(fixture, "fast_ready_v16", expected,
                      sizeof(expected), &expected_length));
    CHECK(jh_fast_checked_frame((uint8_t)'R', payload, sizeof(payload),
                                encoded, sizeof(encoded), &encoded_length) == JH_OK);
    CHECK(encoded_length == expected_length &&
          memcmp(encoded, expected, encoded_length) == 0);
    CHECK(jh_fast_checked_decode(encoded, encoded_length, &kind,
                                 &decoded_payload, &decoded_length) == JH_OK);
    CHECK(kind == (uint8_t)'R' && decoded_length == 2u &&
          memcmp(decoded_payload, payload, 2u) == 0);

    memset(artifact, 0, sizeof(artifact));
    artifact[3] = (uint8_t)'J';
    artifact[4] = (uint8_t)'F';
    artifact[5] = (uint8_t)'1';
    artifact[6] = (uint8_t)'6';
    artifact[7] = 1u;
    artifact[128] = (uint8_t)'Z';
    artifact[129] = (uint8_t)'G';
    artifact[130] = 0x12u;
    artifact[131] = 0x34u;
    artifact[132] = 1u;
    artifact[133] = 0u;
    for (index = 0u; index < 256u; ++index) artifact[136u + index] = (uint8_t)index;
    payload_crc = jh_crc16_ibm(artifact + 136u, 256u, 0u);
    artifact[134] = (uint8_t)(payload_crc >> 8);
    artifact[135] = (uint8_t)payload_crc;
    CHECK(jh_fast_v16_bundle(artifact, sizeof(artifact), &core, &compressed,
                             &compressed_length, &system_crc) == JH_OK);
    CHECK(core == artifact && compressed == artifact + 136u &&
          compressed_length == 256u && system_crc == UINT16_C(0x1234));
    artifact[200] ^= 1u;
    CHECK(jh_fast_v16_bundle(artifact, sizeof(artifact), &core, &compressed,
                             &compressed_length, &system_crc) == JH_ERR_CHECKSUM);
    artifact[200] ^= 1u;

    memset(system_image, 0xe5, sizeof(system_image));
    for (index = 0u; index < JH_SYSTEM_SIZE; ++index) {
        system_image[0x0200u + index] = (uint8_t)(index * 17u + 3u);
    }
    system_image[0x0200u] = 0xc3u;
    resident_crc = jh_crc16_ibm(system_image + 0x0200u, JH_SYSTEM_SIZE, 0u);
    artifact[130] = (uint8_t)(resident_crc >> 8);
    artifact[131] = (uint8_t)resident_crc;
    CHECK(jh_fast_session_init(&session, artifact, sizeof(artifact),
                               system_image, sizeof(system_image)) == JH_OK);
    CHECK(jh_fast_session_ready_timeout(&session) == JH_OK);
    CHECK(jh_fast_session_probe(&session, probe, &probe_length) == JH_OK);
    CHECK(probe_length == 2u && memcmp(probe, "JZ", 2u) == 0);
    CHECK(jh_fast_session_probe(&session, probe, &probe_length) == JH_OK);
    CHECK(probe_length == 3u && probe[0] == 0u &&
          memcmp(probe + 1u, "JZ", 2u) == 0);
    CHECK(jh_fast_session_header_ack(&session, 0xc6u) == JH_OK);
    CHECK(jh_fast_session_tail_size(&session) == sizeof(stream_tail));
    CHECK(jh_fast_session_tail(&session, stream_tail, sizeof(stream_tail),
                               &stream_tail_length) == JH_OK);
    CHECK(stream_tail_length == sizeof(stream_tail) && stream_tail[0] == 1u &&
          stream_tail[1] == 0u &&
          memcmp(stream_tail + 2u, artifact + 136u, 256u) == 0);
    CHECK(jh_fast_session_final_timeout(&session) == JH_OK &&
          session.state == JH_FAST_COMPLETE_UNCONFIRMED);

    memset(artifact_v15, 0, sizeof(artifact_v15));
    artifact_v15[3] = (uint8_t)'J';
    artifact_v15[4] = (uint8_t)'F';
    artifact_v15[5] = (uint8_t)'1';
    artifact_v15[6] = (uint8_t)'5';
    artifact_v15[7] = 1u;
    artifact_v15[9] = 0u;
    artifact_v15[10] = 1u;
    for (index = 0u; index < 256u; ++index) {
        artifact_v15[128u + index] = (uint8_t)(index * 7u + 1u);
        artifact_v15[392u + index] = (uint8_t)(index * 11u + 9u);
    }
    artifact_v15[384] = (uint8_t)'Z';
    artifact_v15[385] = (uint8_t)'F';
    artifact_v15[386] = (uint8_t)(resident_crc >> 8);
    artifact_v15[387] = (uint8_t)resident_crc;
    artifact_v15[388] = 1u;
    artifact_v15[389] = 0u;
    compressed_crc = jh_crc16_ibm(artifact_v15 + 392u, 256u, 0u);
    artifact_v15[390] = (uint8_t)(compressed_crc >> 8);
    artifact_v15[391] = (uint8_t)compressed_crc;
    CHECK(jh_fast_v15_session_init(
              &session_v15, artifact_v15, sizeof(artifact_v15),
              system_image, sizeof(system_image)) == JH_OK);
    CHECK(session_v15.core == artifact_v15 &&
          session_v15.extension == artifact_v15 + 128u &&
          session_v15.extension_length == 256u &&
          session_v15.compressed == artifact_v15 + 392u &&
          session_v15.compressed_length == 256u &&
          session_v15.compressed_crc == compressed_crc &&
          session_v15.system_crc == resident_crc);
    CHECK(jh_fast_v15_extension_tail_size(&session_v15) ==
          sizeof(extension_tail));
    CHECK(jh_fast_v15_extension_tail(
              &session_v15, extension_tail, sizeof(extension_tail),
              &stream_tail_length) == JH_OK);
    CHECK(stream_tail_length == sizeof(extension_tail) &&
          memcmp(extension_tail, artifact_v15 + 128u, 256u) == 0 &&
          extension_tail[256] == session_v15.extension_sum1 &&
          extension_tail[257] == session_v15.extension_sum2);
    artifact_v15[386] ^= 1u;
    CHECK(jh_fast_v15_session_init(
              &session_v15, artifact_v15, sizeof(artifact_v15),
              system_image, sizeof(system_image)) == JH_ERR_CHECKSUM);
    artifact_v15[386] ^= 1u;
    artifact_v15[500] ^= 1u;
    CHECK(jh_fast_v15_session_init(
              &session_v15, artifact_v15, sizeof(artifact_v15),
              system_image, sizeof(system_image)) == JH_ERR_CHECKSUM);
    artifact_v15[500] ^= 1u;
    artifact_v15[10] = 0u;
    CHECK(jh_fast_v15_session_init(
              &session_v15, artifact_v15, sizeof(artifact_v15),
              system_image, sizeof(system_image)) == JH_ERR_FORMAT);
    artifact_v15[10] = 1u;
    artifact_v15[6] = (uint8_t)'4';
    CHECK(jh_fast_v15_session_init(
              &session_v15, artifact_v15, sizeof(artifact_v15),
              system_image, sizeof(system_image)) == JH_ERR_UNSUPPORTED);

    jh_fast_parser_init(&parser);
    CHECK(jh_fast_parser_push(&parser, 0u, &kind, &first, &second) ==
          JH_NEED_MORE);
    for (index = 0u; index < expected_length; ++index) {
        result = jh_fast_parser_push(&parser, expected[index], &kind, &first,
                                     &second);
    }
    CHECK(result == JH_FRAME && kind == (uint8_t)'R' && first == 16u &&
          second == 1u);
    return 0;
}

static int test_bootstrap(const char *fixture)
{
    uint8_t raw[JH_BOOT_RECORD_SIZE];
    uint8_t frame[JH_JANET_MAX_FRAME];
    uint8_t expected[JH_JANET_MAX_FRAME];
    uint8_t *jukusys = (uint8_t *)malloc(10240u);
    uint8_t *prepared_bytes = (uint8_t *)malloc(8192u);
    struct jh_boot_image prepared;
    size_t frame_length;
    size_t expected_length;
    size_t index;
    static const uint8_t stub_prefix[] = {
        0x21u, 0x80u, 0x01u, 0x11u, 0x00u, 0xb4u,
        0x01u, 0x00u, 0x1au, 0x7eu, 0x12u, 0x23u, 0x13u,
        0x0bu, 0x78u, 0xb1u, 0xc2u, 0x09u, 0x01u,
        0xc3u, 0x00u, 0xcau
    };
    CHECK(jukusys != NULL && prepared_bytes != NULL);
    for (index = 0u; index < sizeof(raw); ++index) raw[index] = (uint8_t)index;
    CHECK(jh_boot_frame_count(sizeof(raw), 0) == 8u);
    for (index = 0u; index < 8u; ++index) {
        char key[32];
        CHECK(snprintf(key, sizeof(key), "boot_raw_frame_%u",
                       (unsigned)index) > 0);
        CHECK(fixture_hex(fixture, key, expected, sizeof(expected),
                          &expected_length));
        CHECK(jh_boot_frame_at(raw, sizeof(raw), JH_BOOT_LOAD_ADDRESS,
                               JH_BOOT_LOAD_ADDRESS, 1u, 2u, 0, index,
                               frame, sizeof(frame), &frame_length) == JH_OK);
        CHECK(frame_length == expected_length &&
              memcmp(frame, expected, frame_length) == 0);
    }
    memset(jukusys, 0xe5, 10240u);
    for (index = 0u; index < JH_SYSTEM_SIZE; ++index) {
        jukusys[0x0200u + index] = (uint8_t)(index * 73u + 19u);
    }
    jukusys[0x0200u] = 0xc3u;
    CHECK(jh_boot_prepare(jukusys, 10240u, 0, 0u, 0u, prepared_bytes,
                          8192u, &prepared) == JH_OK);
    CHECK(prepared.format == JH_BOOT_JUKUSYS && prepared.length == 0x1a80u &&
          prepared.load_address == 0x0100u && prepared.entry == 0x0100u);
    CHECK(memcmp(prepared_bytes, stub_prefix, sizeof(stub_prefix)) == 0);
    CHECK(memcmp(prepared_bytes + 128u, jukusys + 0x0200u,
                 JH_SYSTEM_SIZE) == 0);
    CHECK(jh_boot_prepare(raw, 127u, 0, 0u, 0u, prepared_bytes, 8192u,
                          &prepared) == JH_OK);
    CHECK(prepared.format == JH_BOOT_PLAIN && prepared.length == 128u &&
          prepared_bytes[127] == 0u);
    free(prepared_bytes);
    free(jukusys);
    return 0;
}

static int test_boot_session(void)
{
    uint8_t image[JH_BOOT_RECORD_SIZE];
    struct jh_boot_session session;
    struct jh_boot_output output;
    struct jh_janet_frame incoming;
    size_t index;
    for (index = 0u; index < sizeof(image); ++index) image[index] = (uint8_t)index;
    CHECK(jh_boot_session_init(&session, image, sizeof(image), 0x0100u,
                               0x0100u, 0u, 0u, 0) == JH_OK);
    memset(&incoming, 0, sizeof(incoming));
    incoming.destination = 2u;
    incoming.source = 1u;
    incoming.control = 0x0cu;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(output.frame_count == 1u && output.length == 6u &&
          session.request_seen == 0);
    incoming.control = 7u;
    incoming.payload_length = 2u;
    incoming.payload[0] = 3u;
    incoming.payload[1] = 4u;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(output.event == JH_BOOT_EVENT_REQUEST && output.frame_count == 1u &&
          session.client == 1u && session.server == 2u);
    incoming.control = 0x0cu;
    incoming.payload_length = 0u;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(output.frame_count == 1u && session.awaiting_ack &&
          session.next_message == 1u);
    /* A stock client can resume polling instead of issuing an explicit REJ
     * when the response followed the destination-zero handover too quickly.
     * Preserve the message index and resend the exact checked transfer. */
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(output.event == JH_BOOT_EVENT_RETRY && output.frame_count == 2u &&
          output.frame_lengths[0] == 6u && session.awaiting_ack &&
          session.next_message == 1u && session.reject_count == 1u);
    incoming.destination = 2u;
    incoming.source = 1u;
    incoming.control = 0x08u;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(session.advance_pending && !session.awaiting_ack);
    incoming.control = 0x0cu;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(output.frame_count == 2u && session.next_message == 2u);
    incoming.control = 0x08u;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(session.advance_pending);
    incoming.control = 0x0cu;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(session.next_message == 3u);
    incoming.control = 0x09u;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(output.frame_count == 2u && session.reject_count == 2u &&
          session.next_message == 3u);
    incoming.control = 0x08u;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(session.advance_pending);
    incoming.control = 0x0cu;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(session.next_message == 4u);
    incoming.control = 0x08u;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(output.completed_records == 1u && session.next_message == 5u &&
          session.awaiting_ack);
    incoming.control = 0x08u;
    CHECK(jh_boot_session_input(&session, &incoming, &output) == JH_OK);
    CHECK(output.event == JH_BOOT_EVENT_COMPLETE && output.frame_count == 7u &&
          session.complete && session.next_message == 8u);
    return 0;
}

static int test_netdisk(const char *fixture)
{
    uint8_t request_bytes[JH_N3_MAX_REQUEST];
    uint8_t reply[256];
    uint8_t expected[256];
    uint8_t encoded[256];
    uint8_t record[JH_N3_RECORD_SIZE];
    uint8_t deleted[JH_N3_RECORD_SIZE];
    size_t request_length;
    size_t reply_length;
    size_t expected_length;
    size_t encoded_length;
    uint32_t offset;
    size_t index;
    struct jh_n3_parser parser;
    struct jh_n3_request request;
    int result = JH_NEED_MORE;
    CHECK(fixture_hex(fixture, "n3_read_req", request_bytes,
                      sizeof(request_bytes), &request_length));
    jh_n3_parser_init(&parser);
    for (index = 0u; index < request_length; ++index) {
        result = jh_n3_parser_push(&parser, request_bytes[index], &request);
    }
    CHECK(result == JH_FRAME);
    CHECK(request.operation == JH_N3_READ && request.sequence == 0x22u &&
          request.drive == 0u && request.track == 2u && request.sector == 1u);
    for (index = 0u; index < 8u; ++index) record[index] = (uint8_t)index;
    CHECK(jh_n3_reply(0x22u, 0u, record, 8u, reply, sizeof(reply),
                      &reply_length) == JH_OK);
    CHECK(fixture_hex(fixture, "n3_read_reply_8", expected,
                      sizeof(expected), &expected_length));
    CHECK(reply_length == expected_length &&
          memcmp(reply, expected, reply_length) == 0);

    memset(record, 0xa5, sizeof(record));
    CHECK(jh_n3_encode_record(record, 0, encoded, sizeof(encoded),
                              &encoded_length) == JH_OK);
    CHECK(fixture_hex(fixture, "n3_encode_fill", expected,
                      sizeof(expected), &expected_length));
    CHECK(encoded_length == expected_length &&
          memcmp(encoded, expected, encoded_length) == 0);
    for (index = 0u; index < sizeof(deleted); ++index) deleted[index] = (uint8_t)index;
    for (index = 0u; index < sizeof(deleted); index += 32u) deleted[index] = 0xe5u;
    CHECK(jh_n3_encode_record(deleted, 1, encoded, sizeof(encoded),
                              &encoded_length) == JH_OK);
    CHECK(encoded_length == 1u && encoded[0] == 2u);
    CHECK(jh_n3_record_offset(2u, 1u, JH_N3_TRACKS, &offset) == JH_OK);
    CHECK(offset == 10240u);
    CHECK(jh_n3_record_offset(160u, 1u, JH_N3_NATIVE_TRACKS, &offset) ==
          JH_ERR_RANGE);
    CHECK(jh_n3_sector_order()[4] == 9u && jh_n3_sector_order()[39] == 40u);
    return 0;
}

static int test_media(void)
{
    uint8_t *image = (uint8_t *)malloc(JH_N3_NATIVE_VOLUME_SIZE);
    uint8_t *volume = (uint8_t *)malloc(JH_N3_NATIVE_VOLUME_SIZE);
    uint8_t record[JH_N3_RECORD_SIZE];
    struct jh_media media;
    unsigned physical_track;
    CHECK(image != NULL && volume != NULL);
    for (physical_track = 0u; physical_track < JH_N3_NATIVE_TRACKS;
         ++physical_track) {
        memset(image + (size_t)physical_track * JH_N3_TRACK_SIZE,
               (int)physical_track, JH_N3_TRACK_SIZE);
    }
    CHECK(jh_native_image_to_volume(image, JH_N3_NATIVE_VOLUME_SIZE,
                                    volume, JH_N3_NATIVE_VOLUME_SIZE) == JH_OK);
    CHECK(volume[0] == 0u);
    CHECK(volume[(79u * JH_N3_TRACK_SIZE)] == 158u);
    CHECK(volume[(80u * JH_N3_TRACK_SIZE)] == 1u);
    CHECK(volume[(159u * JH_N3_TRACK_SIZE)] == 159u);
    CHECK(jh_media_init(&media, volume, JH_N3_NATIVE_VOLUME_SIZE,
                        JH_N3_NATIVE_TRACKS, 0) == JH_OK);
    CHECK(jh_media_read(&media, 159u, 40u, record) == JH_OK);
    CHECK(record[0] == 159u);
    CHECK(jh_media_write(&media, 159u, 40u, record) == JH_ERR_READ_ONLY);
    free(volume);
    free(image);
    return 0;
}

static int test_service(void)
{
    uint8_t *a_bytes = (uint8_t *)calloc(1u, JH_N3_VOLUME_SIZE);
    uint8_t *b_bytes = (uint8_t *)calloc(1u, JH_N3_NATIVE_VOLUME_SIZE);
    struct jh_media drive_a;
    struct jh_media drive_b;
    struct jh_service service;
    struct jh_service_event event;
    struct jh_n3_request request;
    uint8_t clock_value[5] = {1u, 0u, 0x12u, 0x34u, 0x56u};
    uint32_t offset;
    size_t index;
    CHECK(a_bytes != NULL && b_bytes != NULL);
    CHECK(jh_media_init(&drive_a, a_bytes, JH_N3_VOLUME_SIZE,
                        JH_N3_TRACKS, 1) == JH_OK);
    CHECK(jh_media_init(&drive_b, b_bytes, JH_N3_NATIVE_VOLUME_SIZE,
                        JH_N3_NATIVE_TRACKS, 0) == JH_OK);
    CHECK(jh_service_init(&service, &drive_a, &drive_b, 3u, 3u, 1) == JH_OK);

    memset(&request, 0, sizeof(request));
    request.operation = JH_N3_WRITE_V3;
    request.sequence = 1u;
    request.track = 2u;
    request.sector = 1u;
    request.payload_length = JH_N3_RECORD_SIZE;
    memset(request.payload, 0xa5, sizeof(request.payload));
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.reply_length == 7u && event.reply[3] == 0u);
    CHECK(jh_n3_record_offset(2u, 1u, JH_N3_TRACKS, &offset) == JH_OK);
    CHECK(a_bytes[offset] == 0xa5u);
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.duplicate == 1);

    request.operation = JH_N3_READ_COMPACT;
    request.sequence = 2u;
    request.payload_length = 0u;
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.reply_length == 6u && event.reply[3] == 2u &&
          event.reply[4] == 0xa5u);

    request.operation = JH_N3_READ_AHEAD;
    request.sequence = 3u;
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.reply_length >= 7u && event.reply[3] == 0u &&
          event.reply[4] == 3u);
    CHECK(jh_crc16_ibm(event.reply, event.reply_length - 2u, 0u) ==
          (uint16_t)((uint16_t)event.reply[event.reply_length - 2u] << 8 |
                     event.reply[event.reply_length - 1u]));

    request.operation = JH_N4_CAPABILITY_QUERY;
    request.sequence = 4u;
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.reply_length == 9u && event.reply[3] == 0u &&
          event.reply[4] == 3u && event.reply[5] == 3u &&
          event.reply[7] == 2u);

    CHECK(jh_service_console_input(&service, (const uint8_t *)"X", 1u) == JH_OK);
    request.operation = JH_N4_CONSOLE_POLL;
    request.sequence = 5u;
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.reply[3] == 2u && event.reply[4] == (uint8_t)'X' &&
          service.console_input_length == 0u);
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.duplicate == 1 && event.reply[4] == (uint8_t)'X');

    memset(&request, 0, sizeof(request));
    request.operation = JH_N4_CONSOLE_OUT_BLOCK;
    request.sequence = 6u;
    request.payload_length = 3u;
    memcpy(request.payload, "ABC", 3u);
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.console_output_length == 3u &&
          memcmp(event.console_output, "ABC", 3u) == 0);

    memset(&request, 0, sizeof(request));
    request.operation = JH_N4_TIME_SET;
    request.sequence = 7u;
    request.arguments[0] = 1u;
    request.arguments[2] = 0x23u;
    request.arguments[3] = 0x59u;
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.time_set_requested == 1 && event.reply[3] == 0u);
    request.sequence = 8u;
    request.arguments[2] = 0x24u;
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.time_set_requested == 0 && event.reply[3] == 1u);

    for (index = 0u; index < JH_N3_RECORD_SIZE; ++index) {
        request.payload[index] = (uint8_t)index;
    }
    request.operation = JH_N3_WRITE;
    request.sequence = 9u;
    request.drive = 1u;
    request.track = 159u;
    request.sector = 40u;
    request.payload_length = JH_N3_RECORD_SIZE;
    CHECK(jh_service_handle(&service, &request, clock_value, &event) == JH_OK);
    CHECK(event.reply[3] == 1u);
    free(b_bytes);
    free(a_bytes);
    return 0;
}

static int test_evidence_and_recovery(void)
{
    static const uint8_t text[] = "123456789";
    uint8_t capture_header[JH_CAPTURE_HEADER_SIZE];
    uint8_t capture[64];
    uint8_t journal[JH_JOURNAL_SIZE];
    uint8_t media_bytes[JH_N3_TRACK_SIZE];
    uint8_t after[JH_N3_RECORD_SIZE];
    struct jh_capture_record record;
    struct jh_media media;
    struct jh_media_transaction transaction;
    struct jh_media_transaction decoded;
    uint64_t started;
    uint8_t flags;
    size_t capture_length;
    size_t consumed;
    CHECK(jh_crc32(text, sizeof(text) - 1u, 0u) == UINT32_C(0xcbf43926));
    CHECK(jh_capture_header(UINT64_C(0x0102030405060708), 0x5au,
                            capture_header) == JH_OK);
    CHECK(jh_capture_header_decode(capture_header, sizeof(capture_header),
                                   &started, &flags) == JH_OK);
    CHECK(started == UINT64_C(0x0102030405060708) && flags == 0x5au);
    CHECK(jh_capture_encode(JH_CAPTURE_TX, 1u, 1234u,
                            (const uint8_t *)"ABC", 3u, capture,
                            sizeof(capture), &capture_length) == JH_OK);
    CHECK(jh_capture_decode(capture, capture_length - 1u, &record, &consumed) ==
          JH_NEED_MORE);
    CHECK(jh_capture_decode(capture, capture_length, &record, &consumed) == JH_OK);
    CHECK(consumed == capture_length && record.type == JH_CAPTURE_TX &&
          record.flags == 1u && record.milliseconds == 1234u &&
          record.payload_length == 3u && memcmp(record.payload, "ABC", 3u) == 0);
    capture[12] ^= 1u;
    CHECK(jh_capture_decode(capture, capture_length, &record, &consumed) ==
          JH_ERR_CHECKSUM);

    memset(media_bytes, 0, sizeof(media_bytes));
    memset(after, 0xa5, sizeof(after));
    CHECK(jh_media_init(&media, media_bytes, sizeof(media_bytes), 1u, 1) ==
          JH_ERR_RANGE);
    media.bytes = media_bytes;
    media.context = NULL;
    media.read_offset = NULL;
    media.write_offset = NULL;
    media.size = sizeof(media_bytes);
    media.tracks = 1u;
    media.writable = 1;
    CHECK(jh_media_transaction_prepare(&transaction, &media, 0u, 1u, after,
                                       7u) == JH_OK);
    CHECK(jh_journal_encode(&transaction, journal) == JH_OK);
    CHECK(jh_journal_decode(journal, sizeof(journal), &decoded) == JH_OK);
    CHECK(jh_media_transaction_recover(&decoded, &media) == JH_OK);
    CHECK(media_bytes[0] == 0u && decoded.state == JH_JOURNAL_EMPTY);

    CHECK(jh_media_transaction_apply(&transaction, &media) == JH_OK);
    CHECK(media_bytes[0] == 0xa5u);
    CHECK(jh_journal_encode(&transaction, journal) == JH_OK);
    CHECK(jh_journal_decode(journal, sizeof(journal), &decoded) == JH_OK);
    CHECK(jh_media_transaction_recover(&decoded, &media) == JH_OK);
    CHECK(media_bytes[0] == 0u);

    CHECK(jh_media_transaction_prepare(&transaction, &media, 0u, 1u, after,
                                       8u) == JH_OK);
    CHECK(jh_media_transaction_apply(&transaction, &media) == JH_OK);
    CHECK(jh_media_transaction_commit(&transaction) == JH_OK);
    CHECK(jh_journal_encode(&transaction, journal) == JH_OK);
    memset(media_bytes, 0, sizeof(media_bytes));
    CHECK(jh_journal_decode(journal, sizeof(journal), &decoded) == JH_OK);
    CHECK(jh_media_transaction_recover(&decoded, &media) == JH_OK);
    CHECK(media_bytes[0] == 0xa5u);
    journal[20] ^= 1u;
    CHECK(jh_journal_decode(journal, sizeof(journal), &decoded) ==
          JH_ERR_CHECKSUM);
    return 0;
}

static int test_session(void)
{
    struct jh_session session;
    CHECK(jh_session_init(&session, 1, 1) == JH_OK);
    CHECK(session.phase == JH_SESSION_FASTBOOT);
    CHECK(jh_session_advance(&session, JH_SESSION_FAST_READY) == JH_OK);
    CHECK(jh_session_advance(&session, JH_SESSION_FAST_UNCONFIRMED) == JH_OK);
    CHECK(session.phase == JH_SESSION_NETDISK && session.fastboot_unconfirmed);
    CHECK(jh_session_advance(&session, JH_SESSION_DISK_REQUEST) == JH_OK);
    CHECK(!session.fastboot_unconfirmed && session.boot_count == 1u);
    CHECK(jh_session_advance(&session, JH_SESSION_SERIAL_LOST) == JH_OK);
    CHECK(session.phase == JH_SESSION_RECONNECT && session.reconnect_count == 1u);
    CHECK(jh_session_advance(&session, JH_SESSION_SERIAL_REOPENED) == JH_OK);
    CHECK(session.phase == JH_SESSION_DISCOVERY);
    CHECK(jh_session_advance(&session, JH_SESSION_TARGET_RESET) == JH_OK);
    CHECK(session.phase == JH_SESSION_FASTBOOT && session.reset_count == 1u);
    CHECK(strcmp(jh_session_phase_name(session.phase), "fastboot") == 0);
    CHECK(strcmp(jh_result_name(JH_ERR_CHECKSUM), "checksum") == 0);
    CHECK(jh_session_advance(&session, JH_SESSION_STOP) == JH_OK);
    CHECK(jh_session_advance(&session, JH_SESSION_FAST_READY) == JH_ERR_FORMAT);

    CHECK(jh_session_init(&session, 0, 0) == JH_OK);
    CHECK(jh_session_advance(&session, JH_SESSION_STOCK_REQUEST) == JH_OK);
    CHECK(jh_session_advance(&session, JH_SESSION_STOCK_COMPLETE) == JH_OK);
    CHECK(session.phase == JH_SESSION_NETDISK && session.boot_count == 1u);
    return 0;
}

int main(int argc, char **argv)
{
    const char *fixture = argc == 2 ? argv[1] :
        "tests/fixtures/jukuhost/python-era-v1.txt";
    CHECK(argc <= 2);
    CHECK(test_checksums() == 0);
    CHECK(test_configuration() == 0);
    CHECK(test_janet(fixture) == 0);
    CHECK(test_bootstrap(fixture) == 0);
    CHECK(test_boot_session() == 0);
    CHECK(test_fastboot(fixture) == 0);
    CHECK(test_netdisk(fixture) == 0);
    CHECK(test_media() == 0);
    CHECK(test_service() == 0);
    CHECK(test_evidence_and_recovery() == 0);
    CHECK(test_session() == 0);
    puts("JUKUHOST-CORE-TEST: PASS (frozen vectors + parser recovery + media)");
    return 0;
}
