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
        uint8_t start[8] = {3u, 5u, 0u, 0u, 0u, 0u, 0u, 0u};
        start[3] = (uint8_t)entry;
        start[4] = (uint8_t)(entry >> 8);
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
        uint8_t end[8] = {3u, 6u, 0u, 0u, 0u, 0u, 0u, 0u};
        end[3] = (uint8_t)entry;
        end[4] = (uint8_t)(entry >> 8);
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

int jh_boot_session_init(struct jh_boot_session *session,
                         const uint8_t *image, size_t image_length,
                         uint16_t load_address, uint16_t entry,
                         uint8_t required_client, uint8_t required_server,
                         int compact_execute)
{
    if (session == NULL || image == NULL) return JH_ERR_ARGUMENT;
    if (jh_boot_frame_count(image_length, compact_execute) == 0u ||
            image_length > 0x10000u - load_address ||
            (required_client == 0u) != (required_server == 0u)) {
        return JH_ERR_RANGE;
    }
    memset(session, 0, sizeof(*session));
    session->image = image;
    session->image_length = image_length;
    session->load_address = load_address;
    session->entry = entry;
    session->required_client = required_client;
    session->required_server = required_server;
    session->compact_execute = compact_execute != 0;
    return JH_OK;
}

static int boot_append_encoded(struct jh_boot_output *output,
                               const uint8_t *frame, size_t frame_length)
{
    if (frame_length > sizeof(output->bytes) - output->length) {
        return JH_ERR_SPACE;
    }
    memcpy(output->bytes + output->length, frame, frame_length);
    output->length += frame_length;
    ++output->frame_count;
    return JH_OK;
}

static int boot_append_short(struct jh_boot_output *output,
                             uint8_t destination, uint8_t source,
                             uint8_t control)
{
    uint8_t frame[JH_JANET_MAX_FRAME];
    size_t length;
    int result = jh_janet_encode(destination, source, control, NULL, 0u,
                                 frame, sizeof(frame), &length);
    return result == JH_OK ? boot_append_encoded(output, frame, length) : result;
}

static int boot_append_transfer(struct jh_boot_session *session,
                                struct jh_boot_output *output,
                                size_t index)
{
    uint8_t frame[JH_JANET_MAX_FRAME];
    size_t length;
    int result = jh_boot_frame_at(
        session->image, session->image_length, session->load_address,
        session->entry, session->client, session->server,
        session->compact_execute, index, frame, sizeof(frame), &length);
    return result == JH_OK ? boot_append_encoded(output, frame, length) : result;
}

static int identity_allowed(const struct jh_boot_session *session,
                            const struct jh_janet_frame *incoming)
{
    return incoming->source != 0u && incoming->destination != 0u &&
        (session->required_client == 0u ||
         incoming->source == session->required_client) &&
        (session->required_server == 0u ||
         incoming->destination == session->required_server);
}

static int ready_turn(const struct jh_boot_session *session,
                      const struct jh_janet_frame *incoming)
{
    return incoming->source == session->client &&
        ((incoming->destination == 0u && incoming->control == 0u) ||
         (incoming->destination == session->server &&
          incoming->control == 0x0cu));
}

int jh_boot_session_input(struct jh_boot_session *session,
                          const struct jh_janet_frame *incoming,
                          struct jh_boot_output *output)
{
    uint8_t acknowledged[JH_JANET_MAX_FRAME];
    size_t acknowledged_length;
    size_t frame_count;
    size_t data_frame_count;
    size_t acknowledged_index;
    int result;
    if (session == NULL || incoming == NULL || output == NULL) {
        return JH_ERR_ARGUMENT;
    }
    memset(output, 0, sizeof(*output));
    if (session->complete) return JH_OK;
    if (!session->request_seen && identity_allowed(session, incoming) &&
            incoming->control == 0x0cu) {
        return boot_append_short(output, incoming->source,
                                 incoming->destination, 0x0cu);
    }
    if (session->request_seen && incoming->destination == session->server &&
            incoming->source == session->client &&
            incoming->control == 0x0cu && session->start_pending) {
        result = boot_append_transfer(session, output, 0u);
        if (result != JH_OK) return result;
        session->next_message = 1u;
        session->awaiting_ack = 1;
        session->start_pending = 0;
        ++session->sent_frames;
        output->event = JH_BOOT_EVENT_PROGRESS;
        return JH_OK;
    }
    if (session->request_seen && ready_turn(session, incoming) &&
            session->completion_pending) {
        result = boot_append_short(output, 0u, session->server, 0u);
        if (result != JH_OK) return result;
        session->complete = 1;
        ++session->sent_frames;
        output->event = JH_BOOT_EVENT_COMPLETE;
        return JH_OK;
    }
    if (session->request_seen && ready_turn(session, incoming) &&
            session->advance_pending) {
        result = boot_append_short(output, 0u, session->server, 0u);
        if (result == JH_OK) {
            result = boot_append_transfer(session, output, session->next_message);
        }
        if (result != JH_OK) return result;
        ++session->next_message;
        session->sent_frames += 2u;
        session->awaiting_ack = 1;
        session->advance_pending = 0;
        return JH_OK;
    }
    if (!session->request_seen && identity_allowed(session, incoming) &&
            (incoming->control & 0x0cu) == 0x04u &&
            incoming->payload_length >= 2u &&
            incoming->payload[0] == 3u && incoming->payload[1] == 4u) {
        session->client = incoming->source;
        session->server = incoming->destination;
        session->request_seen = 1;
        session->start_pending = 1;
        result = boot_append_short(output, session->client, session->server,
                                   0x08u);
        if (result != JH_OK) return result;
        ++session->sent_frames;
        output->event = JH_BOOT_EVENT_REQUEST;
        return JH_OK;
    }
    if (session->request_seen && session->awaiting_ack &&
            incoming->destination == session->server &&
            incoming->source == session->client &&
            incoming->control == 0x08u) {
        session->awaiting_ack = 0;
        ++session->ack_count;
        acknowledged_index = session->next_message - 1u;
        frame_count = jh_boot_frame_count(session->image_length,
                                          session->compact_execute);
        result = jh_boot_frame_at(
            session->image, session->image_length, session->load_address,
            session->entry, session->client, session->server,
            session->compact_execute, acknowledged_index,
            acknowledged, sizeof(acknowledged), &acknowledged_length);
        if (result != JH_OK) return result;
        data_frame_count = session->image_length / JH_BOOT_RECORD_SIZE * 3u;
        if (acknowledged_index >= 1u &&
                acknowledged_index <= data_frame_count &&
                acknowledged_length >= 7u && acknowledged[6] == 9u) {
            output->completed_records = acknowledged_index / 3u;
            output->event = JH_BOOT_EVENT_PROGRESS;
        }
        if (session->next_message == frame_count) {
            session->completion_pending = 1;
        } else if (acknowledged_length >= 8u &&
                acknowledged[6] == 3u && acknowledged[7] == 6u) {
            while (session->next_message < frame_count) {
                result = boot_append_short(output, 0u, session->server, 0u);
                if (result == JH_OK) {
                    result = boot_append_transfer(session, output,
                                                  session->next_message);
                }
                if (result != JH_OK) return result;
                ++session->next_message;
                session->sent_frames += 2u;
            }
            result = boot_append_short(output, 0u, session->server, 0u);
            if (result != JH_OK) return result;
            ++session->sent_frames;
            session->complete = 1;
            output->event = JH_BOOT_EVENT_COMPLETE;
        } else if (acknowledged_length >= 7u && acknowledged[6] == 9u) {
            result = boot_append_short(output, 0u, session->server, 0u);
            if (result == JH_OK) {
                result = boot_append_transfer(session, output,
                                              session->next_message);
            }
            if (result != JH_OK) return result;
            ++session->next_message;
            session->sent_frames += 2u;
            session->awaiting_ack = 1;
        } else {
            session->advance_pending = 1;
        }
        return JH_OK;
    }
    if (session->request_seen && session->awaiting_ack &&
            incoming->destination == session->server &&
            incoming->source == session->client &&
            incoming->control == 0x09u) {
        ++session->reject_count;
        result = boot_append_short(output, 0u, session->server, 0u);
        if (result == JH_OK) {
            result = boot_append_transfer(session, output,
                                          session->next_message - 1u);
        }
        if (result != JH_OK) return result;
        session->sent_frames += 2u;
        return JH_OK;
    }
    if (session->request_seen) output->event = JH_BOOT_EVENT_IGNORED;
    return JH_OK;
}
