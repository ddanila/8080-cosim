#include "jukuhost.h"

#include <string.h>

#define SYSTEM_PREFIX 0x0200u
#define RAM51_SYSTEM_SIZE 0x1e00u
#define RAM51_LOAD_ADDRESS 0xb000u
#define RAM51_ENTRY 0xc600u
#define SYSTEM_STAGING_ADDRESS 0x0180u

static const uint8_t ram_system_magic[8] = {
    'J', 'U', 'K', 'U', 'R', 'M', '1', 0x1a
};
static const uint8_t ram51_magic[8] = {
    'J', 'U', 'K', 'U', '5', '1', 0x1a, 0x00
};

static int pad_plain(const uint8_t *input, size_t input_length,
                     uint16_t load_address, uint8_t *output,
                     size_t output_capacity, struct jh_boot_image *prepared,
                     enum jh_boot_format format, uint16_t entry)
{
    size_t padded;
    if (input_length == 0u) return JH_ERR_FORMAT;
    if (input_length > SIZE_MAX - (JH_BOOT_RECORD_SIZE - 1u)) {
        return JH_ERR_RANGE;
    }
    padded = (input_length + JH_BOOT_RECORD_SIZE - 1u) /
        JH_BOOT_RECORD_SIZE * JH_BOOT_RECORD_SIZE;
    if (padded > output_capacity || padded > 0x10000u - load_address) {
        return JH_ERR_SPACE;
    }
    memcpy(output, input, input_length);
    memset(output + input_length, 0, padded - input_length);
    prepared->length = padded;
    prepared->load_address = load_address;
    prepared->entry = entry;
    prepared->format = format;
    return JH_OK;
}

static int system_bootstrap(const uint8_t *system, size_t system_length,
                            uint16_t target, uint16_t entry,
                            int disable_interrupts, uint8_t *output,
                            size_t output_capacity,
                            struct jh_boot_image *prepared,
                            enum jh_boot_format format)
{
    uint8_t stub[23];
    size_t stub_length = disable_interrupts ? 23u : 22u;
    size_t index = 0u;
    uint16_t loop = (uint16_t)(JH_BOOT_LOAD_ADDRESS +
        (disable_interrupts ? 10u : 9u));
    if (system_length == 0u || system_length % JH_BOOT_RECORD_SIZE != 0u ||
            system_length > 0x10000u - target ||
            JH_BOOT_RECORD_SIZE + system_length > output_capacity) {
        return JH_ERR_RANGE;
    }
    if (disable_interrupts) stub[index++] = 0xf3u;
    stub[index++] = 0x21u;
    stub[index++] = (uint8_t)SYSTEM_STAGING_ADDRESS;
    stub[index++] = (uint8_t)(SYSTEM_STAGING_ADDRESS >> 8);
    stub[index++] = 0x11u;
    stub[index++] = (uint8_t)target;
    stub[index++] = (uint8_t)(target >> 8);
    stub[index++] = 0x01u;
    stub[index++] = (uint8_t)system_length;
    stub[index++] = (uint8_t)(system_length >> 8);
    stub[index++] = 0x7eu;
    stub[index++] = 0x12u;
    stub[index++] = 0x23u;
    stub[index++] = 0x13u;
    stub[index++] = 0x0bu;
    stub[index++] = 0x78u;
    stub[index++] = 0xb1u;
    stub[index++] = 0xc2u;
    stub[index++] = (uint8_t)loop;
    stub[index++] = (uint8_t)(loop >> 8);
    stub[index++] = 0xc3u;
    stub[index++] = (uint8_t)entry;
    stub[index++] = (uint8_t)(entry >> 8);
    if (index != stub_length) return JH_ERR_FORMAT;
    memcpy(output, stub, stub_length);
    memset(output + stub_length, 0, JH_BOOT_RECORD_SIZE - stub_length);
    memcpy(output + JH_BOOT_RECORD_SIZE, system, system_length);
    prepared->length = JH_BOOT_RECORD_SIZE + system_length;
    prepared->load_address = JH_BOOT_LOAD_ADDRESS;
    prepared->entry = JH_BOOT_LOAD_ADDRESS;
    prepared->format = format;
    return JH_OK;
}

int jh_boot_prepare(const uint8_t *input, size_t input_length,
                    int explicit_addresses, uint16_t explicit_load,
                    uint16_t explicit_entry, uint8_t *output,
                    size_t output_capacity, struct jh_boot_image *prepared)
{
    size_t index;
    if (input == NULL || output == NULL || prepared == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (explicit_addresses) {
        return pad_plain(input, input_length, explicit_load, output,
                         output_capacity, prepared, JH_BOOT_EXPLICIT,
                         explicit_entry);
    }
    if (input_length >= sizeof(ram_system_magic) &&
            memcmp(input, ram_system_magic, sizeof(ram_system_magic)) == 0) {
        uint16_t load;
        uint16_t entry;
        uint16_t resident_size;
        uint16_t resident_crc;
        if (input_length < SYSTEM_PREFIX) return JH_ERR_FORMAT;
        load = (uint16_t)(input[8] | (uint16_t)((uint16_t)input[9] << 8));
        entry = (uint16_t)(input[10] | (uint16_t)((uint16_t)input[11] << 8));
        resident_size = (uint16_t)(input[12] |
            (uint16_t)((uint16_t)input[13] << 8));
        resident_crc = (uint16_t)(input[14] |
            (uint16_t)((uint16_t)input[15] << 8));
        if (resident_size == 0u || resident_size % JH_BOOT_RECORD_SIZE != 0u ||
                input_length != SYSTEM_PREFIX + resident_size) {
            return JH_ERR_FORMAT;
        }
        if (jh_crc16_ibm(input + SYSTEM_PREFIX, resident_size, 0u) !=
                resident_crc) {
            return JH_ERR_CHECKSUM;
        }
        return system_bootstrap(input + SYSTEM_PREFIX, resident_size, load,
                                entry, 1, output, output_capacity, prepared,
                                JH_BOOT_JUKURM1);
    }
    if (input_length == 10240u &&
            memcmp(input, ram51_magic, sizeof(ram51_magic)) == 0) {
        return system_bootstrap(input + SYSTEM_PREFIX, RAM51_SYSTEM_SIZE,
                                RAM51_LOAD_ADDRESS, RAM51_ENTRY, 0, output,
                                output_capacity, prepared, JH_BOOT_JUKU51);
    }
    if (input_length == 10240u && input[SYSTEM_PREFIX] == 0xc3u) {
        for (index = 0u; index < SYSTEM_PREFIX; ++index) {
            if (input[index] != 0xe5u) break;
        }
        if (index == SYSTEM_PREFIX) {
            return system_bootstrap(input + SYSTEM_PREFIX, JH_SYSTEM_SIZE,
                                    JH_BOOT_SYSTEM_LOAD_ADDRESS,
                                    JH_BOOT_SYSTEM_ENTRY, 0, output,
                                    output_capacity, prepared,
                                    JH_BOOT_JUKUSYS);
        }
    }
    return pad_plain(input, input_length, JH_BOOT_LOAD_ADDRESS, output,
                     output_capacity, prepared, JH_BOOT_PLAIN,
                     JH_BOOT_LOAD_ADDRESS);
}

size_t jh_boot_frame_count(size_t image_length, int compact_execute)
{
    if (image_length == 0u || image_length % JH_BOOT_RECORD_SIZE != 0u) {
        return 0u;
    }
    return 1u + (image_length / JH_BOOT_RECORD_SIZE) * 3u + 1u +
        (compact_execute ? 1u : 3u);
}

int jh_boot_frame_at(const uint8_t *image, size_t image_length,
                     uint16_t load_address, uint16_t entry,
                     uint8_t client, uint8_t server, int compact_execute,
                     size_t frame_index, uint8_t *output, size_t capacity,
                     size_t *output_length)
{
    uint8_t payload[64];
    size_t records;
    size_t data_frames;
    size_t record_index;
    size_t fragment;
    size_t offset;
    size_t payload_length;
    uint16_t address;
    if (image == NULL || output == NULL || output_length == NULL) {
        return JH_ERR_ARGUMENT;
    }
    records = image_length / JH_BOOT_RECORD_SIZE;
    if (image_length == 0u || image_length % JH_BOOT_RECORD_SIZE != 0u ||
            image_length > 0x10000u - load_address ||
            frame_index >= jh_boot_frame_count(image_length, compact_execute)) {
        return JH_ERR_RANGE;
    }
    if (frame_index == 0u) {
        const uint8_t start[8] = {
            3u, 5u, 0u, (uint8_t)entry, (uint8_t)(entry >> 8), 0u, 0u, 0u
        };
        return jh_janet_encode(client, server, 7u, start, sizeof(start),
                               output, capacity, output_length);
    }
    data_frames = records * 3u;
    if (frame_index <= data_frames) {
        size_t relative = frame_index - 1u;
        record_index = relative / 3u;
        fragment = relative % 3u;
        offset = record_index * JH_BOOT_RECORD_SIZE;
        address = (uint16_t)(load_address + offset);
        if (fragment == 0u) {
            payload[0] = 2u;
            payload[1] = 2u;
            payload[2] = 0u;
            payload[3] = (uint8_t)address;
            payload[4] = (uint8_t)(address >> 8);
            payload[5] = 0u;
            payload[6] = 0u;
            payload[7] = 0u;
            memcpy(payload + 8u, image + offset, 56u);
            payload_length = 64u;
        } else if (fragment == 1u) {
            payload[0] = 4u;
            memcpy(payload + 1u, image + offset + 56u, 63u);
            payload_length = 64u;
        } else {
            payload[0] = 9u;
            memcpy(payload + 1u, image + offset + 119u, 9u);
            payload_length = 10u;
        }
        return jh_janet_encode(client, server, 7u, payload, payload_length,
                               output, capacity, output_length);
    }
    if (frame_index == data_frames + 1u) {
        const uint8_t end[8] = {
            3u, 6u, 0u, (uint8_t)entry, (uint8_t)(entry >> 8), 0u, 0u, 0u
        };
        return jh_janet_encode(client, server, 7u, end, sizeof(end),
                               output, capacity, output_length);
    }
    fragment = frame_index - (data_frames + 2u);
    if (compact_execute) {
        const uint8_t execute[2] = {3u, 0x0fu};
        return jh_janet_encode(client, server, 7u, execute, sizeof(execute),
                               output, capacity, output_length);
    }
    memset(payload, 0, sizeof(payload));
    if (fragment == 0u) {
        payload[0] = 2u;
        payload[1] = 0x0fu;
        payload_length = 64u;
    } else if (fragment == 1u) {
        payload[0] = 4u;
        payload_length = 64u;
    } else if (fragment == 2u) {
        payload[0] = 9u;
        payload_length = 2u;
    } else {
        return JH_ERR_RANGE;
    }
    return jh_janet_encode(client, server, 7u, payload, payload_length,
                           output, capacity, output_length);
}
