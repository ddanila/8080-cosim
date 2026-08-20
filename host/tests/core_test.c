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
    uint8_t range[16];
    uint8_t sum1;
    uint8_t sum2;
    size_t index;
    for (index = 0u; index < sizeof(range); ++index) range[index] = (uint8_t)index;
    CHECK(jh_crc16_ccitt(text, sizeof(text) - 1u, UINT16_C(0xffff)) ==
          UINT16_C(0x29b1));
    CHECK(jh_crc16_ibm(text, sizeof(text) - 1u, 0u) == UINT16_C(0xbb3d));
    jh_fletcher16(range, sizeof(range), &sum1, &sum2);
    CHECK(sum1 == 0x78u && sum2 == 0xaau);
    return 0;
}

static int test_janet(const char *fixture)
{
    uint8_t expected[JH_JANET_MAX_FRAME];
    uint8_t encoded[JH_JANET_MAX_FRAME];
    uint8_t damaged[JH_JANET_MAX_FRAME];
    size_t expected_length;
    size_t encoded_length;
    size_t index;
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
    return 0;
}

static int test_fastboot(const char *fixture)
{
    uint8_t expected[16];
    uint8_t encoded[16];
    uint8_t artifact[136u + 256u];
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
    size_t offset;
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
    size_t offset;
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

int main(int argc, char **argv)
{
    const char *fixture = argc == 2 ? argv[1] :
        "tests/fixtures/jukuhost/python-era-v1.txt";
    CHECK(argc <= 2);
    CHECK(test_checksums() == 0);
    CHECK(test_janet(fixture) == 0);
    CHECK(test_bootstrap(fixture) == 0);
    CHECK(test_fastboot(fixture) == 0);
    CHECK(test_netdisk(fixture) == 0);
    CHECK(test_media() == 0);
    CHECK(test_service() == 0);
    puts("JUKUHOST-CORE-TEST: PASS (frozen vectors + parser recovery + media)");
    return 0;
}
