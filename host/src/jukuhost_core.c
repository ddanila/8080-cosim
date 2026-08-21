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

static int fast_v15_bundle(const uint8_t *artifact, size_t artifact_length,
                           const uint8_t **core, const uint8_t **extension,
                           size_t *extension_length,
                           const uint8_t **compressed,
                           size_t *compressed_length,
                           uint16_t *compressed_crc, uint16_t *system_crc)
{
    size_t extension_size;
    size_t payload_offset;
    size_t declared_length;
    uint16_t declared_crc;
    const uint8_t *descriptor;
    const uint8_t *payload;
    if (artifact == NULL || core == NULL || extension == NULL ||
            extension_length == NULL || compressed == NULL ||
            compressed_length == NULL || compressed_crc == NULL ||
            system_crc == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (artifact_length <= 136u || artifact[3] != (uint8_t)'J' ||
            artifact[4] != (uint8_t)'F' || artifact[5] != (uint8_t)'1' ||
            artifact[6] != (uint8_t)'5') {
        return JH_ERR_UNSUPPORTED;
    }
    if (artifact[7] != 1u || artifact[8] != 0u) return JH_ERR_FORMAT;
    extension_size = (size_t)artifact[9] | (size_t)artifact[10] << 8;
    if (extension_size < 256u || extension_size > 640u ||
            extension_size > artifact_length - 136u) {
        return JH_ERR_FORMAT;
    }
    payload_offset = 128u + extension_size;
    descriptor = artifact + payload_offset;
    if (descriptor[0] != (uint8_t)'Z' || descriptor[1] != (uint8_t)'F') {
        return JH_ERR_FORMAT;
    }
    *system_crc = (uint16_t)((uint16_t)descriptor[2] << 8) | descriptor[3];
    declared_length = (size_t)((unsigned)descriptor[4] << 8) | descriptor[5];
    declared_crc = (uint16_t)((uint16_t)descriptor[6] << 8) | descriptor[7];
    payload = descriptor + 8u;
    if (declared_length < 256u || declared_length >= 0x2800u ||
            artifact_length != payload_offset + 8u + declared_length) {
        return JH_ERR_FORMAT;
    }
    if (jh_crc16_ibm(payload, declared_length, 0u) != declared_crc) {
        return JH_ERR_CHECKSUM;
    }
    *core = artifact;
    *extension = artifact + 128u;
    *extension_length = extension_size;
    *compressed = payload;
    *compressed_length = declared_length;
    *compressed_crc = declared_crc;
    return JH_OK;
}

void jh_fast_parser_init(struct jh_fast_parser *parser)
{
    if (parser != NULL) parser->length = 0u;
}

int jh_fast_parser_push(struct jh_fast_parser *parser, uint8_t value,
                        uint8_t *kind, uint8_t *first, uint8_t *second)
{
    if (parser == NULL || kind == NULL || first == NULL || second == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (parser->length == 0u) {
        if (value == (uint8_t)'J') parser->bytes[parser->length++] = value;
        return JH_NEED_MORE;
    }
    if (parser->length >= sizeof(parser->bytes)) parser->length = 0u;
    parser->bytes[parser->length++] = value;
    if (parser->length < sizeof(parser->bytes)) return JH_NEED_MORE;
    if (jh_xor(parser->bytes, sizeof(parser->bytes)) == 0u) {
        *kind = parser->bytes[1];
        *first = parser->bytes[2];
        *second = parser->bytes[3];
        parser->length = 0u;
        return JH_FRAME;
    }
    if (parser->bytes[4] == (uint8_t)'J') {
        parser->bytes[0] = (uint8_t)'J';
        parser->length = 1u;
    } else {
        parser->length = 0u;
    }
    return JH_ERR_CHECKSUM;
}

static int fast_extract_system(const uint8_t *image, size_t image_length,
                               const uint8_t **system, size_t *system_length)
{
    static const uint8_t rm_magic[8] = {
        'J', 'U', 'K', 'U', 'R', 'M', '1', 0x1a
    };
    size_t index;
    if (image_length >= sizeof(rm_magic) &&
            memcmp(image, rm_magic, sizeof(rm_magic)) == 0) {
        uint16_t size;
        uint16_t expected_crc;
        if (image_length < 0x0200u) return JH_ERR_FORMAT;
        size = (uint16_t)(image[12] | (uint16_t)((uint16_t)image[13] << 8));
        expected_crc = (uint16_t)(image[14] |
            (uint16_t)((uint16_t)image[15] << 8));
        if (size == 0u || size % 128u != 0u || image_length != 0x0200u + size) {
            return JH_ERR_FORMAT;
        }
        if (jh_crc16_ibm(image + 0x0200u, size, 0u) != expected_crc) {
            return JH_ERR_CHECKSUM;
        }
        *system = image + 0x0200u;
        *system_length = size;
        return JH_OK;
    }
    if (image_length != 10240u || image[0x0200u] != 0xc3u) {
        return JH_ERR_FORMAT;
    }
    for (index = 0u; index < 0x0200u; ++index) {
        if (image[index] != 0xe5u) return JH_ERR_FORMAT;
    }
    *system = image + 0x0200u;
    *system_length = JH_SYSTEM_SIZE;
    return JH_OK;
}

int jh_fast_v15_session_init(struct jh_fast_v15_session *session,
                             const uint8_t *artifact, size_t artifact_length,
                             const uint8_t *system_image,
                             size_t system_image_length)
{
    const uint8_t *system;
    size_t system_length;
    int result;
    if (session == NULL || system_image == NULL) return JH_ERR_ARGUMENT;
    memset(session, 0, sizeof(*session));
    result = fast_v15_bundle(
        artifact, artifact_length, &session->core, &session->extension,
        &session->extension_length, &session->compressed,
        &session->compressed_length, &session->compressed_crc,
        &session->system_crc);
    if (result != JH_OK) return result;
    result = fast_extract_system(system_image, system_image_length, &system,
                                 &system_length);
    if (result != JH_OK) return result;
    if (jh_crc16_ibm(system, system_length, 0u) != session->system_crc) {
        return JH_ERR_CHECKSUM;
    }
    jh_fletcher16(session->extension, session->extension_length,
                  &session->extension_sum1, &session->extension_sum2);
    return JH_OK;
}

size_t jh_fast_v15_extension_tail_size(
    const struct jh_fast_v15_session *session)
{
    return session == NULL ? 0u : session->extension_length + 2u;
}

int jh_fast_v15_extension_tail(const struct jh_fast_v15_session *session,
                               uint8_t *output, size_t capacity,
                               size_t *output_length)
{
    size_t length;
    if (session == NULL || output == NULL || output_length == NULL) {
        return JH_ERR_ARGUMENT;
    }
    length = jh_fast_v15_extension_tail_size(session);
    if (capacity < length) return JH_ERR_SPACE;
    memcpy(output, session->extension, session->extension_length);
    output[session->extension_length] = session->extension_sum1;
    output[session->extension_length + 1u] = session->extension_sum2;
    *output_length = length;
    return JH_OK;
}

int jh_fast_session_init(struct jh_fast_session *session,
                         const uint8_t *artifact, size_t artifact_length,
                         const uint8_t *system_image, size_t system_image_length)
{
    const uint8_t *core;
    const uint8_t *compressed;
    const uint8_t *system;
    size_t compressed_length;
    size_t system_length;
    uint16_t system_crc;
    int result;
    if (session == NULL || system_image == NULL) return JH_ERR_ARGUMENT;
    result = jh_fast_v16_bundle(artifact, artifact_length, &core, &compressed,
                                &compressed_length, &system_crc);
    if (result != JH_OK) return result;
    result = fast_extract_system(system_image, system_image_length, &system,
                                 &system_length);
    if (result != JH_OK) return result;
    if (jh_crc16_ibm(system, system_length, 0u) != system_crc) {
        return JH_ERR_CHECKSUM;
    }
    (void)core;
    memset(session, 0, sizeof(*session));
    session->compressed = compressed;
    session->compressed_length = compressed_length;
    session->compressed_crc = jh_crc16_ibm(compressed, compressed_length, 0u);
    session->system_crc = system_crc;
    session->state = JH_FAST_WAIT_READY;
    return JH_OK;
}

int jh_fast_session_ready(struct jh_fast_session *session,
                          uint8_t kind, uint8_t version, uint8_t rate_flag)
{
    if (session == NULL) return JH_ERR_ARGUMENT;
    if (session->state != JH_FAST_WAIT_READY) return JH_ERR_FORMAT;
    if (kind != (uint8_t)'R' || version != 16u || rate_flag != 1u) {
        return JH_ERR_UNSUPPORTED;
    }
    session->ready_seen = 1;
    session->state = JH_FAST_PROBE_STREAM;
    return JH_OK;
}

int jh_fast_session_ready_timeout(struct jh_fast_session *session)
{
    if (session == NULL) return JH_ERR_ARGUMENT;
    if (session->state != JH_FAST_WAIT_READY) return JH_ERR_FORMAT;
    session->state = JH_FAST_PROBE_STREAM;
    return JH_OK;
}

int jh_fast_session_probe(struct jh_fast_session *session,
                          uint8_t output[3], size_t *output_length)
{
    if (session == NULL || output == NULL || output_length == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (session->state != JH_FAST_PROBE_STREAM) return JH_ERR_FORMAT;
    if (session->header_probes == 0u) {
        output[0] = (uint8_t)'J';
        output[1] = (uint8_t)'Z';
        *output_length = 2u;
    } else {
        output[0] = 0u;
        output[1] = (uint8_t)'J';
        output[2] = (uint8_t)'Z';
        *output_length = 3u;
    }
    ++session->header_probes;
    return JH_OK;
}

int jh_fast_session_header_ack(struct jh_fast_session *session, uint8_t value)
{
    if (session == NULL) return JH_ERR_ARGUMENT;
    if (session->state != JH_FAST_PROBE_STREAM) return JH_ERR_FORMAT;
    if (value != 0xc6u) return JH_ERR_UNSUPPORTED;
    ++session->header_acks;
    session->state = JH_FAST_SEND_STREAM;
    return JH_OK;
}

size_t jh_fast_session_tail_size(const struct jh_fast_session *session)
{
    return session == NULL ? 0u : session->compressed_length + 4u;
}

int jh_fast_session_tail(struct jh_fast_session *session,
                         uint8_t *output, size_t capacity,
                         size_t *output_length)
{
    size_t length;
    if (session == NULL || output == NULL || output_length == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (session->state != JH_FAST_SEND_STREAM) return JH_ERR_FORMAT;
    length = session->compressed_length + 4u;
    if (capacity < length) return JH_ERR_SPACE;
    output[0] = (uint8_t)(session->compressed_length >> 8);
    output[1] = (uint8_t)session->compressed_length;
    memcpy(output + 2u, session->compressed, session->compressed_length);
    output[length - 2u] = (uint8_t)(session->compressed_crc >> 8);
    output[length - 1u] = (uint8_t)session->compressed_crc;
    *output_length = length;
    session->state = JH_FAST_WAIT_FINAL;
    return JH_OK;
}

int jh_fast_session_final(struct jh_fast_session *session,
                          uint8_t kind, uint8_t sequence, uint8_t status)
{
    if (session == NULL) return JH_ERR_ARGUMENT;
    if (session->state != JH_FAST_WAIT_FINAL) return JH_ERR_FORMAT;
    if (kind != (uint8_t)'A' || sequence != 0u) return JH_ERR_UNSUPPORTED;
    session->state = status == 0u ? JH_FAST_COMPLETE : JH_FAST_FAILED;
    return status == 0u ? JH_OK : JH_ERR_FORMAT;
}

int jh_fast_session_final_timeout(struct jh_fast_session *session)
{
    if (session == NULL) return JH_ERR_ARGUMENT;
    if (session->state != JH_FAST_WAIT_FINAL || session->header_acks == 0u) {
        return JH_ERR_FORMAT;
    }
    session->state = JH_FAST_COMPLETE_UNCONFIRMED;
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
        memset(request->arguments, 0, sizeof(request->arguments));
    } else {
        memcpy(request->arguments, parser->bytes + 4,
               sizeof(request->arguments));
    }
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
                        uint32_t *offset)
{
    if (offset == NULL) return JH_ERR_ARGUMENT;
    if (track >= tracks || sector == 0u || sector > 40u) return JH_ERR_RANGE;
    *offset = (uint32_t)track * JH_N3_TRACK_SIZE +
        (uint32_t)(sector - 1u) * JH_N3_RECORD_SIZE;
    return JH_OK;
}

const uint8_t *jh_n3_sector_order(void)
{
    return n3_sector_order;
}
