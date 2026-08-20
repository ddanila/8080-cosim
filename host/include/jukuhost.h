#ifndef JUKUHOST_H
#define JUKUHOST_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define JH_JANET_MAX_PAYLOAD 255u
#define JH_JANET_MAX_FRAME (JH_JANET_MAX_PAYLOAD + 7u)
#define JH_N3_RECORD_SIZE 128u
#define JH_N3_TRACK_SIZE (40u * JH_N3_RECORD_SIZE)
#define JH_N3_TRACKS 80u
#define JH_N3_NATIVE_TRACKS 160u
#define JH_N3_VOLUME_SIZE (JH_N3_TRACKS * JH_N3_TRACK_SIZE)
#define JH_N3_NATIVE_VOLUME_SIZE (JH_N3_NATIVE_TRACKS * JH_N3_TRACK_SIZE)
#define JH_N3_MAX_REQUEST (9u + JH_N3_RECORD_SIZE)
#define JH_N4_MAX_CONSOLE_BLOCK 32u
#define JH_SYSTEM_SIZE 0x1a00u
#define JH_SERVICE_MAX_REPLY 1063u
#define JH_SERVICE_CONSOLE_QUEUE 256u
#define JH_BOOT_RECORD_SIZE 128u
#define JH_BOOT_LOAD_ADDRESS 0x0100u
#define JH_BOOT_SYSTEM_LOAD_ADDRESS 0xb400u
#define JH_BOOT_SYSTEM_ENTRY 0xca00u

enum jh_boot_format {
    JH_BOOT_PLAIN = 0,
    JH_BOOT_EXPLICIT = 1,
    JH_BOOT_JUKUSYS = 2,
    JH_BOOT_JUKU51 = 3,
    JH_BOOT_JUKURM1 = 4
};

enum jh_result {
    JH_OK = 0,
    JH_FRAME = 1,
    JH_NEED_MORE = 2,
    JH_ERR_ARGUMENT = -1,
    JH_ERR_SPACE = -2,
    JH_ERR_CHECKSUM = -3,
    JH_ERR_FORMAT = -4,
    JH_ERR_RANGE = -5,
    JH_ERR_READ_ONLY = -6,
    JH_ERR_UNSUPPORTED = -7
};

enum jh_n3_operation {
    JH_N3_READ = 0x11,
    JH_N3_WRITE = 0x12,
    JH_N3_READ_COMPACT = 0x13,
    JH_N3_READ_AHEAD = 0x14,
    JH_N3_WRITE_V3 = 0x15,
    JH_N4_CONSOLE_POLL = 0x20,
    JH_N4_CONSOLE_OUT = 0x21,
    JH_N4_TIME_GET = 0x22,
    JH_N4_TIME_SET = 0x23,
    JH_N4_STATUS_REPORT = 0x24,
    JH_N4_DIAG_REPORT = 0x25,
    JH_N4_CAPABILITY_QUERY = 0x26,
    JH_N4_BOOT_REPORT = 0x27,
    JH_N4_CONSOLE_OUT_BLOCK = 0x28
};

struct jh_janet_frame {
    uint8_t destination;
    uint8_t source;
    uint8_t control;
    size_t payload_length;
    uint8_t payload[JH_JANET_MAX_PAYLOAD];
};

struct jh_janet_parser {
    uint8_t bytes[JH_JANET_MAX_FRAME];
    size_t length;
    size_t expected;
};

struct jh_n3_request {
    uint8_t operation;
    uint8_t sequence;
    uint8_t drive;
    uint16_t track;
    uint8_t sector;
    uint8_t arguments[4];
    size_t payload_length;
    uint8_t payload[JH_N3_RECORD_SIZE];
};

struct jh_service_event {
    uint8_t reply[JH_SERVICE_MAX_REPLY];
    size_t reply_length;
    uint8_t console_output[JH_N4_MAX_CONSOLE_BLOCK];
    size_t console_output_length;
    uint8_t time_set[4];
    int time_set_requested;
    uint8_t report_operation;
    uint8_t report_arguments[4];
    int duplicate;
};

struct jh_service {
    struct jh_media *drive_a;
    struct jh_media *drive_b;
    unsigned protocol_version;
    unsigned read_ahead_records;
    int console_enabled;
    uint8_t console_input[JH_SERVICE_CONSOLE_QUEUE];
    size_t console_input_length;
    struct jh_n3_request last_request;
    int have_last_request;
    uint8_t last_reply[JH_SERVICE_MAX_REPLY];
    size_t last_reply_length;
};

struct jh_n3_parser {
    uint8_t bytes[JH_N3_MAX_REQUEST];
    size_t length;
    size_t expected;
};

struct jh_media {
    uint8_t *bytes;
    size_t size;
    unsigned tracks;
    int writable;
};

struct jh_boot_image {
    size_t length;
    uint16_t load_address;
    uint16_t entry;
    enum jh_boot_format format;
};

uint8_t jh_xor(const uint8_t *data, size_t length);
uint16_t jh_crc16_ccitt(const uint8_t *data, size_t length, uint16_t initial);
uint16_t jh_crc16_ibm(const uint8_t *data, size_t length, uint16_t initial);
void jh_fletcher16(const uint8_t *data, size_t length,
                   uint8_t *sum1, uint8_t *sum2);

int jh_janet_encode(uint8_t destination, uint8_t source, uint8_t control,
                    const uint8_t *payload, size_t payload_length,
                    uint8_t *output, size_t capacity, size_t *output_length);
void jh_janet_parser_init(struct jh_janet_parser *parser);
int jh_janet_parser_push(struct jh_janet_parser *parser, uint8_t value,
                         struct jh_janet_frame *frame);

int jh_fast_checked_frame(uint8_t kind, const uint8_t *payload,
                          size_t payload_length, uint8_t *output,
                          size_t capacity, size_t *output_length);
int jh_fast_checked_decode(const uint8_t *frame, size_t length,
                           uint8_t *kind, const uint8_t **payload,
                           size_t *payload_length);
int jh_fast_v16_bundle(const uint8_t *artifact, size_t artifact_length,
                       const uint8_t **core, const uint8_t **compressed,
                       size_t *compressed_length, uint16_t *system_crc);

int jh_boot_prepare(const uint8_t *input, size_t input_length,
                    int explicit_addresses, uint16_t explicit_load,
                    uint16_t explicit_entry, uint8_t *output,
                    size_t output_capacity, struct jh_boot_image *prepared);
size_t jh_boot_frame_count(size_t image_length, int compact_execute);
int jh_boot_frame_at(const uint8_t *image, size_t image_length,
                     uint16_t load_address, uint16_t entry,
                     uint8_t client, uint8_t server, int compact_execute,
                     size_t frame_index, uint8_t *output, size_t capacity,
                     size_t *output_length);

void jh_n3_parser_init(struct jh_n3_parser *parser);
int jh_n3_parser_push(struct jh_n3_parser *parser, uint8_t value,
                      struct jh_n3_request *request);
int jh_n3_reply(uint8_t sequence, uint8_t status,
                const uint8_t *payload, size_t payload_length,
                uint8_t *output, size_t capacity, size_t *output_length);
int jh_n3_reply_v3(uint8_t sequence, uint8_t status, uint8_t records,
                   const uint8_t *payload, size_t payload_length,
                   uint8_t *output, size_t capacity, size_t *output_length);
int jh_n3_encode_record(const uint8_t record[JH_N3_RECORD_SIZE],
                        int deleted_directory, uint8_t *output,
                        size_t capacity, size_t *output_length);
int jh_n3_record_offset(unsigned track, unsigned sector, unsigned tracks,
                        size_t *offset);
const uint8_t *jh_n3_sector_order(void);

int jh_media_init(struct jh_media *media, uint8_t *bytes, size_t size,
                  unsigned tracks, int writable);
int jh_media_read(const struct jh_media *media, unsigned track,
                  unsigned sector, uint8_t record[JH_N3_RECORD_SIZE]);
int jh_media_write(struct jh_media *media, unsigned track, unsigned sector,
                   const uint8_t record[JH_N3_RECORD_SIZE]);
int jh_native_image_to_volume(const uint8_t *image, size_t image_length,
                              uint8_t *volume, size_t volume_capacity);

int jh_service_init(struct jh_service *service, struct jh_media *drive_a,
                    struct jh_media *drive_b, unsigned protocol_version,
                    unsigned read_ahead_records, int console_enabled);
int jh_service_console_input(struct jh_service *service,
                             const uint8_t *data, size_t length);
int jh_service_handle(struct jh_service *service,
                      const struct jh_n3_request *request,
                      const uint8_t clock_value[5],
                      struct jh_service_event *event);

#ifdef __cplusplus
}
#endif

#endif
