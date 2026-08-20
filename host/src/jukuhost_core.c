#include "jukuhost.h"

#include <string.h>

static const uint8_t n3_sector_order[40] = {
    1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28,
    33, 34, 35, 36, 5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24,
    29, 30, 31, 32, 37, 38, 39, 40
};

uint8_t jh_xor(const uint8_t *data, size_t length)
{
    uint8_t result = 0;
    size_t index;
    if (data == NULL && length != 0u) {
        return 0;
    }
    for (index = 0; index < length; ++index) {
        result = (uint8_t)(result ^ data[index]);
    }
    return result;
}

uint16_t jh_crc16_ccitt(const uint8_t *data, size_t length, uint16_t initial)
{
    uint16_t crc = initial;
    size_t index;
    unsigned bit;
    for (index = 0; index < length; ++index) {
        crc = (uint16_t)(crc ^ (uint16_t)((uint16_t)data[index] << 8));
        for (bit = 0; bit < 8u; ++bit) {
            crc = (uint16_t)((crc & UINT16_C(0x8000)) != 0u
                ? (uint16_t)((uint16_t)(crc << 1) ^ UINT16_C(0x1021))
                : (uint16_t)(crc << 1));
        }
    }
    return crc;
}

uint16_t jh_crc16_ibm(const uint8_t *data, size_t length, uint16_t initial)
{
    uint16_t crc = initial;
    size_t index;
    unsigned bit;
    for (index = 0; index < length; ++index) {
        crc = (uint16_t)(crc ^ data[index]);
        for (bit = 0; bit < 8u; ++bit) {
            crc = (uint16_t)((crc & 1u) != 0u
                ? (uint16_t)((crc >> 1) ^ UINT16_C(0xa001))
                : (uint16_t)(crc >> 1));
        }
    }
    return crc;
}

void jh_fletcher16(const uint8_t *data, size_t length,
                   uint8_t *sum1_out, uint8_t *sum2_out)
{
    unsigned sum1 = 0;
    unsigned sum2 = 0;
    size_t index;
    for (index = 0; index < length; ++index) {
        unsigned total = sum1 + data[index];
        sum1 = (total & 0xffu) + (total >> 8);
        total = sum2 + sum1;
        sum2 = (total & 0xffu) + (total >> 8);
    }
    *sum1_out = (uint8_t)sum1;
    *sum2_out = (uint8_t)sum2;
}

int jh_janet_encode(uint8_t destination, uint8_t source, uint8_t control,
                    const uint8_t *payload, size_t payload_length,
                    uint8_t *output, size_t capacity, size_t *output_length)
{
    size_t length;
    int data_frame = (control & 0x0cu) == 0x04u;
    if (output == NULL || output_length == NULL ||
            (payload == NULL && payload_length != 0u)) {
        return JH_ERR_ARGUMENT;
    }
    if ((!data_frame && payload_length != 0u) ||
            payload_length > JH_JANET_MAX_PAYLOAD) {
        return JH_ERR_FORMAT;
    }
    length = data_frame ? payload_length + 7u : 6u;
    if (capacity < length) {
        return JH_ERR_SPACE;
    }
    output[0] = 0xe4u;
    output[1] = 0xe4u;
    output[2] = destination;
    output[3] = source;
    output[4] = control;
    if (data_frame) {
        output[5] = (uint8_t)payload_length;
        if (payload_length != 0u) {
            memcpy(output + 6, payload, payload_length);
        }
    }
    output[length - 1u] = jh_xor(output, length - 1u);
    *output_length = length;
    return JH_OK;
}

void jh_janet_parser_init(struct jh_janet_parser *parser)
{
    if (parser != NULL) {
        parser->length = 0;
        parser->expected = 0;
    }
}

static void janet_resync(struct jh_janet_parser *parser)
{
    size_t index;
    for (index = 1; index + 1u < parser->length; ++index) {
        if (parser->bytes[index] == 0xe4u &&
                parser->bytes[index + 1u] == 0xe4u) {
            memmove(parser->bytes, parser->bytes + index,
                    parser->length - index);
            parser->length -= index;
            parser->expected = 0;
            return;
        }
    }
    if (parser->length != 0u &&
            parser->bytes[parser->length - 1u] == 0xe4u) {
        parser->bytes[0] = 0xe4u;
        parser->length = 1u;
    } else {
        parser->length = 0u;
    }
    parser->expected = 0u;
}

int jh_janet_parser_push(struct jh_janet_parser *parser, uint8_t value,
                         struct jh_janet_frame *frame)
{
    size_t payload_length;
    if (parser == NULL || frame == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (parser->length == 0u) {
        if (value != 0xe4u) {
            return JH_NEED_MORE;
        }
        parser->bytes[parser->length++] = value;
        return JH_NEED_MORE;
    }
    if (parser->length == 1u && value != 0xe4u) {
        parser->length = value == 0xe4u ? 1u : 0u;
        return JH_NEED_MORE;
    }
    if (parser->length >= sizeof(parser->bytes)) {
        janet_resync(parser);
        return JH_ERR_SPACE;
    }
    parser->bytes[parser->length++] = value;
    if (parser->length == 5u) {
        parser->expected = (value & 0x0cu) == 0x04u ? 0u : 6u;
    } else if (parser->length == 6u && parser->expected == 0u) {
        parser->expected = 7u + value;
    }
    if (parser->expected == 0u || parser->length < parser->expected) {
        return JH_NEED_MORE;
    }
    if (jh_xor(parser->bytes, parser->length) != 0u) {
        janet_resync(parser);
        return JH_ERR_CHECKSUM;
    }
    frame->destination = parser->bytes[2];
    frame->source = parser->bytes[3];
    frame->control = parser->bytes[4];
    payload_length = parser->length == 6u ? 0u : parser->bytes[5];
    frame->payload_length = payload_length;
    if (payload_length != 0u) {
        memcpy(frame->payload, parser->bytes + 6, payload_length);
    }
    parser->length = 0u;
    parser->expected = 0u;
    return JH_FRAME;
}

int jh_fast_checked_frame(uint8_t kind, const uint8_t *payload,
                          size_t payload_length, uint8_t *output,
                          size_t capacity, size_t *output_length)
{
    size_t length = payload_length + 3u;
    if (output == NULL || output_length == NULL ||
            (payload == NULL && payload_length != 0u)) {
        return JH_ERR_ARGUMENT;
    }
    if (capacity < length) {
        return JH_ERR_SPACE;
    }
    output[0] = (uint8_t)'J';
    output[1] = kind;
    if (payload_length != 0u) {
        memcpy(output + 2, payload, payload_length);
    }
    output[length - 1u] = jh_xor(output, length - 1u);
    *output_length = length;
    return JH_OK;
}

int jh_fast_checked_decode(const uint8_t *frame, size_t length,
                           uint8_t *kind, const uint8_t **payload,
                           size_t *payload_length)
{
    if (frame == NULL || kind == NULL || payload == NULL ||
            payload_length == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (length < 3u || frame[0] != (uint8_t)'J') {
        return JH_ERR_FORMAT;
    }
    if (jh_xor(frame, length) != 0u) {
        return JH_ERR_CHECKSUM;
    }
    *kind = frame[1];
    *payload = frame + 2;
    *payload_length = length - 3u;
    return JH_OK;
}

int jh_fast_v16_bundle(const uint8_t *artifact, size_t artifact_length,
                       const uint8_t **core, const uint8_t **compressed,
                       size_t *compressed_length, uint16_t *system_crc)
{
    size_t declared_length;
    uint16_t declared_crc;
    const uint8_t *descriptor;
    const uint8_t *payload;
    if (artifact == NULL || core == NULL || compressed == NULL ||
            compressed_length == NULL || system_crc == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (artifact_length <= 136u || artifact[3] != (uint8_t)'J' ||
            artifact[4] != (uint8_t)'F' || artifact[5] != (uint8_t)'1' ||
            artifact[6] != (uint8_t)'6') {
        return JH_ERR_UNSUPPORTED;
    }
    if (artifact[7] != 1u || artifact[8] != 0u || artifact[9] != 0u ||
            artifact[10] != 0u) {
        return JH_ERR_FORMAT;
    }
    descriptor = artifact + 128u;
    if (descriptor[0] != (uint8_t)'Z' || descriptor[1] != (uint8_t)'G') {
        return JH_ERR_FORMAT;
    }
    *system_crc = (uint16_t)((uint16_t)descriptor[2] << 8) | descriptor[3];
    declared_length = (size_t)((unsigned)descriptor[4] << 8) | descriptor[5];
    declared_crc = (uint16_t)((uint16_t)descriptor[6] << 8) | descriptor[7];
    payload = descriptor + 8u;
    if (declared_length < 256u || declared_length >= 0x2800u ||
            artifact_length != 136u + declared_length) {
        return JH_ERR_FORMAT;
    }
    if (jh_crc16_ibm(payload, declared_length, 0u) != declared_crc) {
        return JH_ERR_CHECKSUM;
    }
    *core = artifact;
    *compressed = payload;
    *compressed_length = declared_length;
    return JH_OK;
}

static int n3_supported(uint8_t operation)
{
    return (operation >= JH_N3_READ && operation <= JH_N3_WRITE_V3) ||
        (operation >= JH_N4_CONSOLE_POLL &&
         operation <= JH_N4_CONSOLE_OUT_BLOCK);
}

void jh_n3_parser_init(struct jh_n3_parser *parser)
{
    if (parser != NULL) {
        parser->length = 0u;
        parser->expected = 0u;
    }
}

static void n3_resync(struct jh_n3_parser *parser)
{
    size_t index;
    for (index = 1u; index + 1u < parser->length; ++index) {
        if (parser->bytes[index] == (uint8_t)'J' &&
                parser->bytes[index + 1u] == (uint8_t)'D') {
            memmove(parser->bytes, parser->bytes + index,
                    parser->length - index);
            parser->length -= index;
            parser->expected = 0u;
            return;
        }
    }
    parser->length = parser->length != 0u &&
        parser->bytes[parser->length - 1u] == (uint8_t)'J' ? 1u : 0u;
    if (parser->length != 0u) {
        parser->bytes[0] = (uint8_t)'J';
    }
    parser->expected = 0u;
}

int jh_n3_parser_push(struct jh_n3_parser *parser, uint8_t value,
                      struct jh_n3_request *request)
{
    uint8_t operation;
    if (parser == NULL || request == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (parser->length == 0u) {
        if (value == (uint8_t)'J') {
            parser->bytes[parser->length++] = value;
        }
        return JH_NEED_MORE;
    }
    if (parser->length == 1u && value != (uint8_t)'D') {
        parser->length = value == (uint8_t)'J' ? 1u : 0u;
        return JH_NEED_MORE;
    }
    if (parser->length >= sizeof(parser->bytes)) {
        n3_resync(parser);
        return JH_ERR_SPACE;
    }
    parser->bytes[parser->length++] = value;
    if (parser->length == 3u) {
        operation = value;
        if (!n3_supported(operation)) {
            n3_resync(parser);
            return JH_ERR_UNSUPPORTED;
        }
        parser->expected = operation == JH_N4_CONSOLE_OUT_BLOCK ? 0u :
            9u + (operation == JH_N3_WRITE || operation == JH_N3_WRITE_V3
                  ? JH_N3_RECORD_SIZE : 0u);
    } else if (parser->length == 5u && parser->bytes[2] ==
            JH_N4_CONSOLE_OUT_BLOCK) {
        if (value == 0u || value > JH_N4_MAX_CONSOLE_BLOCK) {
            n3_resync(parser);
            return JH_ERR_RANGE;
        }
        parser->expected = 6u + value;
    }
    if (parser->expected == 0u || parser->length < parser->expected) {
        return JH_NEED_MORE;
    }
    if (jh_xor(parser->bytes, parser->length) != 0u) {
        n3_resync(parser);
        return JH_ERR_CHECKSUM;
    }
    request->operation = parser->bytes[2];
    request->sequence = parser->bytes[3];
    if (request->operation == JH_N4_CONSOLE_OUT_BLOCK) {
        request->drive = 0u;
        request->track = 0u;
        request->sector = 0u;
        request->payload_length = parser->bytes[4];
        memcpy(request->payload, parser->bytes + 5, request->payload_length);
    } else {
        request->drive = parser->bytes[4];
        request->track = (uint16_t)(parser->bytes[5] |
            (uint16_t)((uint16_t)parser->bytes[6] << 8));
        request->sector = parser->bytes[7];
        request->payload_length = request->operation == JH_N3_WRITE ||
            request->operation == JH_N3_WRITE_V3 ? JH_N3_RECORD_SIZE : 0u;
        if (request->payload_length != 0u) {
            memcpy(request->payload, parser->bytes + 8,
                   request->payload_length);
        }
    }
    parser->length = 0u;
    parser->expected = 0u;
    return JH_FRAME;
}

int jh_n3_reply(uint8_t sequence, uint8_t status,
                const uint8_t *payload, size_t payload_length,
                uint8_t *output, size_t capacity, size_t *output_length)
{
    size_t length = 5u + payload_length;
    if (output == NULL || output_length == NULL ||
            (payload == NULL && payload_length != 0u)) {
        return JH_ERR_ARGUMENT;
    }
    if (capacity < length) {
        return JH_ERR_SPACE;
    }
    output[0] = (uint8_t)'D';
    output[1] = (uint8_t)'J';
    output[2] = sequence;
    output[3] = status;
    if (payload_length != 0u) {
        memcpy(output + 4, payload, payload_length);
    }
    output[length - 1u] = jh_xor(output, length - 1u);
    *output_length = length;
    return JH_OK;
}

int jh_n3_reply_v3(uint8_t sequence, uint8_t status, uint8_t records,
                   const uint8_t *payload, size_t payload_length,
                   uint8_t *output, size_t capacity, size_t *output_length)
{
    size_t body_length = 5u + payload_length;
    uint16_t crc;
    if (output == NULL || output_length == NULL ||
            (payload == NULL && payload_length != 0u)) {
        return JH_ERR_ARGUMENT;
    }
    if (capacity < body_length + 2u) {
        return JH_ERR_SPACE;
    }
    output[0] = (uint8_t)'D';
    output[1] = (uint8_t)'J';
    output[2] = sequence;
    output[3] = status;
    output[4] = records;
    if (payload_length != 0u) {
        memcpy(output + 5, payload, payload_length);
    }
    crc = jh_crc16_ibm(output, body_length, 0u);
    output[body_length] = (uint8_t)(crc >> 8);
    output[body_length + 1u] = (uint8_t)crc;
    *output_length = body_length + 2u;
    return JH_OK;
}

int jh_n3_encode_record(const uint8_t record[JH_N3_RECORD_SIZE],
                        int deleted_directory, uint8_t *output,
                        size_t capacity, size_t *output_length)
{
    size_t index;
    size_t prefix;
    uint8_t fill;
    int uniform = 1;
    if (record == NULL || output == NULL || output_length == NULL) {
        return JH_ERR_ARGUMENT;
    }
    for (index = 1u; index < JH_N3_RECORD_SIZE; ++index) {
        if (record[index] != record[0]) {
            uniform = 0;
            break;
        }
    }
    if (uniform) {
        if (capacity < 2u) return JH_ERR_SPACE;
        output[0] = 1u;
        output[1] = record[0];
        *output_length = 2u;
        return JH_OK;
    }
    if (deleted_directory) {
        int deleted = 1;
        for (index = 0u; index < JH_N3_RECORD_SIZE; index += 32u) {
            if (record[index] != 0xe5u) {
                deleted = 0;
                break;
            }
        }
        if (deleted) {
            if (capacity < 1u) return JH_ERR_SPACE;
            output[0] = 2u;
            *output_length = 1u;
            return JH_OK;
        }
    }
    fill = record[JH_N3_RECORD_SIZE - 1u];
    prefix = JH_N3_RECORD_SIZE - 1u;
    while (prefix != 0u && record[prefix - 1u] == fill) {
        --prefix;
    }
    if (prefix + 3u < JH_N3_RECORD_SIZE + 1u) {
        if (capacity < prefix + 3u) return JH_ERR_SPACE;
        output[0] = 3u;
        output[1] = (uint8_t)prefix;
        if (prefix != 0u) memcpy(output + 2, record, prefix);
        output[prefix + 2u] = fill;
        *output_length = prefix + 3u;
        return JH_OK;
    }
    if (capacity < JH_N3_RECORD_SIZE + 1u) return JH_ERR_SPACE;
    output[0] = 0u;
    memcpy(output + 1, record, JH_N3_RECORD_SIZE);
    *output_length = JH_N3_RECORD_SIZE + 1u;
    return JH_OK;
}

int jh_n3_record_offset(unsigned track, unsigned sector, unsigned tracks,
                        size_t *offset)
{
    if (offset == NULL) return JH_ERR_ARGUMENT;
    if (track >= tracks || sector == 0u || sector > 40u) return JH_ERR_RANGE;
    *offset = (size_t)track * JH_N3_TRACK_SIZE +
        (size_t)(sector - 1u) * JH_N3_RECORD_SIZE;
    return JH_OK;
}

const uint8_t *jh_n3_sector_order(void)
{
    return n3_sector_order;
}
