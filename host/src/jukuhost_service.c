#include "jukuhost.h"

#include <string.h>

static int request_equal(const struct jh_n3_request *left,
                         const struct jh_n3_request *right)
{
    return left->operation == right->operation &&
        left->sequence == right->sequence && left->drive == right->drive &&
        left->track == right->track && left->sector == right->sector &&
        memcmp(left->arguments, right->arguments, 4u) == 0 &&
        left->payload_length == right->payload_length &&
        memcmp(left->payload, right->payload, left->payload_length) == 0;
}

int jh_service_is_duplicate(const struct jh_service *service,
                            const struct jh_n3_request *request)
{
    return service != NULL && request != NULL && service->have_last_request &&
        request_equal(&service->last_request, request);
}

static int directory_sector(unsigned sector)
{
    const uint8_t *order = jh_n3_sector_order();
    unsigned index;
    for (index = 0u; index < 32u; ++index) {
        if (order[index] == sector) return 1;
    }
    return 0;
}

static int sector_order_index(unsigned sector, unsigned *result)
{
    const uint8_t *order = jh_n3_sector_order();
    unsigned index;
    for (index = 0u; index < 40u; ++index) {
        if (order[index] == sector) {
            *result = index;
            return JH_OK;
        }
    }
    return JH_ERR_RANGE;
}

static int valid_bcd(uint8_t value, unsigned maximum)
{
    unsigned high = value >> 4;
    unsigned low = value & 0x0fu;
    unsigned decoded = high * 10u + low;
    return high <= 9u && low <= 9u && decoded <= maximum;
}

static int valid_time_set(const uint8_t value[4])
{
    unsigned days = (unsigned)value[0] | (unsigned)value[1] << 8;
    return days != 0u && valid_bcd(value[2], 23u) && valid_bcd(value[3], 59u);
}

int jh_service_init(struct jh_service *service, struct jh_media *drive_a,
                    struct jh_media *drive_b, unsigned protocol_version,
                    unsigned read_ahead_records, int console_enabled)
{
    if (service == NULL || drive_a == NULL) return JH_ERR_ARGUMENT;
    if (protocol_version < 1u || protocol_version > 3u ||
            read_ahead_records == 0u || read_ahead_records > 8u) {
        return JH_ERR_RANGE;
    }
    memset(service, 0, sizeof(*service));
    service->drive_a = drive_a;
    service->drive_b = drive_b;
    service->protocol_version = protocol_version;
    service->read_ahead_records = read_ahead_records;
    service->console_enabled = console_enabled != 0;
    return JH_OK;
}

int jh_service_console_input(struct jh_service *service,
                             const uint8_t *data, size_t length)
{
    if (service == NULL || (data == NULL && length != 0u)) {
        return JH_ERR_ARGUMENT;
    }
    if (length > sizeof(service->console_input) - service->console_input_length) {
        return JH_ERR_SPACE;
    }
    memcpy(service->console_input + service->console_input_length, data, length);
    service->console_input_length += length;
    return JH_OK;
}

static struct jh_media *select_media(struct jh_service *service, uint8_t drive)
{
    if (drive == 0u) return service->drive_a;
    if (drive == 1u) return service->drive_b;
    return NULL;
}

static int raw_reply(struct jh_service_event *event, uint8_t sequence,
                     uint8_t status, const uint8_t *payload, size_t length)
{
    return jh_n3_reply(sequence, status, payload, length, event->reply,
                       sizeof(event->reply), &event->reply_length);
}

static int read_ahead(struct jh_service *service,
                      const struct jh_n3_request *request,
                      struct jh_media *media, struct jh_service_event *event)
{
    uint8_t descriptors[8u * (3u + JH_N3_RECORD_SIZE + 1u)];
    uint8_t record[JH_N3_RECORD_SIZE];
    uint8_t encoded[JH_N3_RECORD_SIZE + 1u];
    size_t descriptor_length = 0u;
    size_t encoded_length;
    unsigned order_index;
    unsigned track = request->track;
    unsigned records = 0u;
    int result;
    if (media == NULL || service->protocol_version != 3u ||
            sector_order_index(request->sector, &order_index) != JH_OK) {
        return jh_n3_reply_v3(request->sequence, 1u, 0u, NULL, 0u,
                              event->reply, sizeof(event->reply),
                              &event->reply_length);
    }
    while (records < service->read_ahead_records && track < media->tracks) {
        unsigned sector = jh_n3_sector_order()[order_index];
        result = jh_media_read(media, track, sector, record);
        if (result != JH_OK) break;
        result = jh_n3_encode_record(record,
            track == 2u && directory_sector(sector), encoded,
            sizeof(encoded), &encoded_length);
        if (result != JH_OK) return result;
        descriptors[descriptor_length++] = (uint8_t)track;
        descriptors[descriptor_length++] = (uint8_t)(track >> 8);
        descriptors[descriptor_length++] = (uint8_t)sector;
        memcpy(descriptors + descriptor_length, encoded, encoded_length);
        descriptor_length += encoded_length;
        ++records;
        ++order_index;
        if (order_index == 40u) {
            order_index = 0u;
            ++track;
        }
    }
    return jh_n3_reply_v3(request->sequence, 0u, (uint8_t)records,
                          descriptors, descriptor_length, event->reply,
                          sizeof(event->reply), &event->reply_length);
}

int jh_service_handle(struct jh_service *service,
                      const struct jh_n3_request *request,
                      const uint8_t clock_value[5],
                      struct jh_service_event *event)
{
    struct jh_media *media;
    uint8_t record[JH_N3_RECORD_SIZE];
    uint8_t capabilities[4];
    uint8_t status = 0u;
    int result = JH_OK;
    if (service == NULL || request == NULL || event == NULL) {
        return JH_ERR_ARGUMENT;
    }
    memset(event, 0, sizeof(*event));
    if (jh_service_is_duplicate(service, request)) {
        memcpy(event->reply, service->last_reply, service->last_reply_length);
        event->reply_length = service->last_reply_length;
        event->duplicate = 1;
        return JH_OK;
    }
    media = select_media(service, request->drive);
    switch (request->operation) {
    case JH_N3_READ:
        status = (uint8_t)(jh_media_read(media, request->track,
            request->sector, record) == JH_OK ? 0u : 1u);
        result = raw_reply(event, request->sequence, status,
                           status == 0u ? record : NULL,
                           status == 0u ? sizeof(record) : 0u);
        break;
    case JH_N3_READ_COMPACT:
        if (service->protocol_version < 2u || media == NULL ||
                jh_media_read(media, request->track, request->sector, record) !=
                JH_OK) {
            result = raw_reply(event, request->sequence, 1u, NULL, 0u);
            break;
        }
        if (memcmp(record, record + 1u, JH_N3_RECORD_SIZE - 1u) == 0) {
            status = 2u;
            result = raw_reply(event, request->sequence, status, record, 1u);
        } else if (request->track == 2u &&
                directory_sector(request->sector)) {
            size_t directory_index;
            int deleted = 1;
            for (directory_index = 0u;
                 directory_index < JH_N3_RECORD_SIZE;
                 directory_index += 32u) {
                if (record[directory_index] != 0xe5u) {
                    deleted = 0;
                    break;
                }
            }
            status = deleted ? 3u : 0u;
            result = raw_reply(event, request->sequence, status,
                               deleted ? NULL : record,
                               deleted ? 0u : sizeof(record));
        } else {
            result = raw_reply(event, request->sequence, 0u, record,
                               sizeof(record));
        }
        break;
    case JH_N3_READ_AHEAD:
        result = read_ahead(service, request, media, event);
        break;
    case JH_N3_WRITE:
    case JH_N3_WRITE_V3:
        if (request->operation == JH_N3_WRITE_V3 &&
                service->protocol_version != 3u) {
            status = 1u;
        } else {
            status = (uint8_t)(jh_media_write(media, request->track,
                request->sector, request->payload) == JH_OK ? 0u : 1u);
        }
        if (request->operation == JH_N3_WRITE_V3) {
            result = jh_n3_reply_v3(request->sequence, status, 0u, NULL, 0u,
                                    event->reply, sizeof(event->reply),
                                    &event->reply_length);
        } else {
            result = raw_reply(event, request->sequence, status, NULL, 0u);
        }
        break;
    case JH_N4_CONSOLE_POLL:
        if (!service->console_enabled) status = 1u;
        else if (service->console_input_length != 0u) status = 2u;
        result = raw_reply(event, request->sequence, status,
            status == 2u ? service->console_input : NULL,
            status == 2u ? 1u : 0u);
        if (result == JH_OK && status == 2u) {
            memmove(service->console_input, service->console_input + 1u,
                    --service->console_input_length);
        }
        break;
    case JH_N4_CONSOLE_OUT:
        status = (uint8_t)(service->console_enabled ? 0u : 1u);
        result = raw_reply(event, request->sequence, status, NULL, 0u);
        if (result == JH_OK && status == 0u) {
            event->console_output[0] = request->arguments[0];
            event->console_output_length = 1u;
        }
        break;
    case JH_N4_CONSOLE_OUT_BLOCK:
        status = (uint8_t)(service->console_enabled &&
            service->protocol_version == 3u ? 0u : 1u);
        result = raw_reply(event, request->sequence, status, NULL, 0u);
        if (result == JH_OK && status == 0u) {
            memcpy(event->console_output, request->payload,
                   request->payload_length);
            event->console_output_length = request->payload_length;
        }
        break;
    case JH_N4_TIME_GET:
        status = (uint8_t)(service->protocol_version == 3u &&
            clock_value != NULL ? 0u : 1u);
        result = raw_reply(event, request->sequence, status,
                           status == 0u ? clock_value : NULL,
                           status == 0u ? 5u : 0u);
        break;
    case JH_N4_TIME_SET:
        status = (uint8_t)(service->protocol_version == 3u &&
            valid_time_set(request->arguments) ? 0u : 1u);
        result = raw_reply(event, request->sequence, status, NULL, 0u);
        if (result == JH_OK && status == 0u) {
            memcpy(event->time_set, request->arguments, 4u);
            event->time_set_requested = 1;
        }
        break;
    case JH_N4_STATUS_REPORT:
    case JH_N4_DIAG_REPORT:
    case JH_N4_BOOT_REPORT:
        status = (uint8_t)(service->protocol_version == 3u ? 0u : 1u);
        result = raw_reply(event, request->sequence, status, NULL, 0u);
        if (result == JH_OK && status == 0u) {
            event->report_operation = request->operation;
            memcpy(event->report_arguments, request->arguments, 4u);
        }
        break;
    case JH_N4_CAPABILITY_QUERY:
        status = (uint8_t)(service->protocol_version == 3u ? 0u : 1u);
        capabilities[0] = (uint8_t)service->protocol_version;
        capabilities[1] = (uint8_t)service->read_ahead_records;
        capabilities[2] = (uint8_t)((service->console_enabled ? 0x41u : 0u) |
            0x02u | 0x04u | 0x08u |
            (service->drive_b != NULL ? 0x10u : 0u) |
            (service->drive_a->writable ? 0x20u : 0u));
        capabilities[3] = service->drive_b != NULL ? 2u : 1u;
        result = raw_reply(event, request->sequence, status,
                           status == 0u ? capabilities : NULL,
                           status == 0u ? sizeof(capabilities) : 0u);
        break;
    default:
        return JH_ERR_UNSUPPORTED;
    }
    if (result != JH_OK) return result;
    service->last_request = *request;
    memcpy(service->last_reply, event->reply, event->reply_length);
    service->last_reply_length = event->reply_length;
    service->have_last_request = 1;
    return JH_OK;
}
