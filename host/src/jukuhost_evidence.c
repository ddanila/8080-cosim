#include "jukuhost.h"

#include <string.h>

static void put_u16le(uint8_t *output, uint16_t value)
{
    output[0] = (uint8_t)value;
    output[1] = (uint8_t)(value >> 8);
}

static void put_u32le(uint8_t *output, uint32_t value)
{
    output[0] = (uint8_t)value;
    output[1] = (uint8_t)(value >> 8);
    output[2] = (uint8_t)(value >> 16);
    output[3] = (uint8_t)(value >> 24);
}

static void put_u64le(uint8_t *output, uint64_t value)
{
    unsigned index;
    for (index = 0u; index < 8u; ++index) {
        output[index] = (uint8_t)(value >> (index * 8u));
    }
}

static uint16_t get_u16le(const uint8_t *input)
{
    return (uint16_t)(input[0] | (uint16_t)((uint16_t)input[1] << 8));
}

static uint32_t get_u32le(const uint8_t *input)
{
    return (uint32_t)input[0] | (uint32_t)input[1] << 8 |
        (uint32_t)input[2] << 16 | (uint32_t)input[3] << 24;
}

static uint64_t get_u64le(const uint8_t *input)
{
    uint64_t result = 0u;
    unsigned index;
    for (index = 0u; index < 8u; ++index) {
        result |= (uint64_t)input[index] << (index * 8u);
    }
    return result;
}

uint32_t jh_crc32(const uint8_t *data, size_t length, uint32_t initial)
{
    uint32_t crc = initial ^ UINT32_C(0xffffffff);
    size_t index;
    unsigned bit;
    for (index = 0u; index < length; ++index) {
        crc ^= data[index];
        for (bit = 0u; bit < 8u; ++bit) {
            crc = (crc & 1u) != 0u
                ? (crc >> 1) ^ UINT32_C(0xedb88320)
                : crc >> 1;
        }
    }
    return crc ^ UINT32_C(0xffffffff);
}

int jh_capture_header(uint64_t started_milliseconds, uint8_t flags,
                      uint8_t output[JH_CAPTURE_HEADER_SIZE])
{
    if (output == NULL) return JH_ERR_ARGUMENT;
    memcpy(output, "JHCAP1", 6u);
    output[6] = 1u;
    output[7] = flags;
    put_u64le(output + 8u, started_milliseconds);
    return JH_OK;
}

int jh_capture_header_decode(const uint8_t *input, size_t length,
                             uint64_t *started_milliseconds, uint8_t *flags)
{
    if (input == NULL || started_milliseconds == NULL || flags == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (length < JH_CAPTURE_HEADER_SIZE) return JH_NEED_MORE;
    if (memcmp(input, "JHCAP1", 6u) != 0 || input[6] != 1u) {
        return JH_ERR_FORMAT;
    }
    *flags = input[7];
    *started_milliseconds = get_u64le(input + 8u);
    return JH_OK;
}

int jh_capture_encode(enum jh_capture_type type, uint8_t flags,
                      uint64_t milliseconds, const uint8_t *payload,
                      size_t payload_length, uint8_t *output, size_t capacity,
                      size_t *output_length)
{
    size_t length;
    uint32_t crc;
    if (output == NULL || output_length == NULL ||
            (payload == NULL && payload_length != 0u)) {
        return JH_ERR_ARGUMENT;
    }
    if (type < JH_CAPTURE_RX || type > JH_CAPTURE_EVENT
#if SIZE_MAX > UINT16_MAX
            || payload_length > UINT16_MAX
#endif
            ) {
        return JH_ERR_RANGE;
    }
    length = JH_CAPTURE_RECORD_OVERHEAD + payload_length;
    if (capacity < length) return JH_ERR_SPACE;
    output[0] = (uint8_t)type;
    output[1] = flags;
    put_u16le(output + 2u, (uint16_t)payload_length);
    put_u64le(output + 4u, milliseconds);
    if (payload_length != 0u) memcpy(output + 12u, payload, payload_length);
    crc = jh_crc32(output, 12u + payload_length, 0u);
    put_u32le(output + 12u + payload_length, crc);
    *output_length = length;
    return JH_OK;
}

int jh_capture_decode(const uint8_t *input, size_t length,
                      struct jh_capture_record *record,
                      size_t *consumed)
{
    size_t payload_length;
    size_t record_length;
    uint32_t expected_crc;
    if (input == NULL || record == NULL || consumed == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (length < JH_CAPTURE_RECORD_OVERHEAD) return JH_NEED_MORE;
    if (input[0] < JH_CAPTURE_RX || input[0] > JH_CAPTURE_EVENT) {
        return JH_ERR_FORMAT;
    }
    payload_length = get_u16le(input + 2u);
    record_length = JH_CAPTURE_RECORD_OVERHEAD + payload_length;
    if (length < record_length) return JH_NEED_MORE;
    expected_crc = get_u32le(input + 12u + payload_length);
    if (jh_crc32(input, 12u + payload_length, 0u) != expected_crc) {
        return JH_ERR_CHECKSUM;
    }
    record->type = (enum jh_capture_type)input[0];
    record->flags = input[1];
    record->milliseconds = get_u64le(input + 4u);
    record->payload = input + 12u;
    record->payload_length = payload_length;
    *consumed = record_length;
    return JH_OK;
}

int jh_media_transaction_prepare(struct jh_media_transaction *transaction,
                                 const struct jh_media *media,
                                 unsigned track, unsigned sector,
                                 const uint8_t after[JH_N3_RECORD_SIZE],
                                 uint32_t sequence)
{
    uint32_t offset;
    int result;
    if (transaction == NULL || media == NULL || after == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (!media->writable) return JH_ERR_READ_ONLY;
    result = jh_n3_record_offset(track, sector, media->tracks, &offset);
    if (result != JH_OK || offset > media->size ||
            media->size - offset < JH_N3_RECORD_SIZE) {
        return JH_ERR_RANGE;
    }
    transaction->state = JH_JOURNAL_PREPARED;
    transaction->sequence = sequence;
    transaction->offset = offset;
    if (jh_media_read_offset(media, offset, transaction->before) != JH_OK) {
        return JH_ERR_RANGE;
    }
    memcpy(transaction->after, after, JH_N3_RECORD_SIZE);
    return JH_OK;
}

int jh_media_transaction_apply(struct jh_media_transaction *transaction,
                               struct jh_media *media)
{
    if (transaction == NULL || media == NULL) return JH_ERR_ARGUMENT;
    if (transaction->state != JH_JOURNAL_PREPARED || !media->writable ||
            transaction->offset > media->size ||
            media->size - transaction->offset < JH_N3_RECORD_SIZE) {
        return JH_ERR_FORMAT;
    }
    if (jh_media_write_offset(media, transaction->offset,
                              transaction->after) != JH_OK) {
        return JH_ERR_FORMAT;
    }
    transaction->state = JH_JOURNAL_APPLIED;
    return JH_OK;
}

int jh_media_transaction_commit(struct jh_media_transaction *transaction)
{
    if (transaction == NULL) return JH_ERR_ARGUMENT;
    if (transaction->state != JH_JOURNAL_APPLIED) return JH_ERR_FORMAT;
    transaction->state = JH_JOURNAL_COMPLETE;
    return JH_OK;
}

int jh_media_transaction_recover(struct jh_media_transaction *transaction,
                                 struct jh_media *media)
{
    if (transaction == NULL || media == NULL) return JH_ERR_ARGUMENT;
    if (transaction->state == JH_JOURNAL_EMPTY) return JH_OK;
    if (transaction->offset > media->size ||
            media->size - transaction->offset < JH_N3_RECORD_SIZE) {
        return JH_ERR_RANGE;
    }
    if (transaction->state == JH_JOURNAL_PREPARED ||
            transaction->state == JH_JOURNAL_APPLIED) {
        if (jh_media_write_offset(media, transaction->offset,
                                  transaction->before) != JH_OK) {
            return JH_ERR_FORMAT;
        }
    } else if (transaction->state == JH_JOURNAL_COMPLETE) {
        if (jh_media_write_offset(media, transaction->offset,
                                  transaction->after) != JH_OK) {
            return JH_ERR_FORMAT;
        }
    } else {
        return JH_ERR_FORMAT;
    }
    transaction->state = JH_JOURNAL_EMPTY;
    return JH_OK;
}

int jh_journal_encode(const struct jh_media_transaction *transaction,
                      uint8_t output[JH_JOURNAL_SIZE])
{
    uint32_t crc;
    if (transaction == NULL || output == NULL) return JH_ERR_ARGUMENT;
    if (transaction->state < JH_JOURNAL_PREPARED ||
            transaction->state > JH_JOURNAL_COMPLETE) {
        return JH_ERR_FORMAT;
    }
    memcpy(output, "JHJR1", 5u);
    output[5] = 1u;
    output[6] = (uint8_t)transaction->state;
    output[7] = 0u;
    put_u32le(output + 8u, transaction->sequence);
    put_u32le(output + 12u, transaction->offset);
    memcpy(output + 16u, transaction->before, JH_N3_RECORD_SIZE);
    memcpy(output + 144u, transaction->after, JH_N3_RECORD_SIZE);
    crc = jh_crc32(output, JH_JOURNAL_SIZE - 4u, 0u);
    put_u32le(output + JH_JOURNAL_SIZE - 4u, crc);
    return JH_OK;
}

int jh_journal_decode(const uint8_t *input, size_t length,
                      struct jh_media_transaction *transaction)
{
    uint32_t expected_crc;
    if (input == NULL || transaction == NULL) return JH_ERR_ARGUMENT;
    if (length < JH_JOURNAL_SIZE) return JH_NEED_MORE;
    if (length != JH_JOURNAL_SIZE || memcmp(input, "JHJR1", 5u) != 0 ||
            input[5] != 1u || input[7] != 0u ||
            input[6] < JH_JOURNAL_PREPARED ||
            input[6] > JH_JOURNAL_COMPLETE) {
        return JH_ERR_FORMAT;
    }
    expected_crc = get_u32le(input + JH_JOURNAL_SIZE - 4u);
    if (jh_crc32(input, JH_JOURNAL_SIZE - 4u, 0u) != expected_crc) {
        return JH_ERR_CHECKSUM;
    }
    transaction->state = (enum jh_journal_state)input[6];
    transaction->sequence = get_u32le(input + 8u);
    transaction->offset = get_u32le(input + 12u);
    memcpy(transaction->before, input + 16u, JH_N3_RECORD_SIZE);
    memcpy(transaction->after, input + 144u, JH_N3_RECORD_SIZE);
    return JH_OK;
}
