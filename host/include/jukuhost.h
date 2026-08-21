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
#define JH_N3_TRACK_SIZE (UINT32_C(40) * JH_N3_RECORD_SIZE)
#define JH_N3_TRACKS 80u
#define JH_N3_NATIVE_TRACKS 160u
#define JH_N3_VOLUME_SIZE (UINT32_C(80) * JH_N3_TRACK_SIZE)
#define JH_N3_NATIVE_VOLUME_SIZE (UINT32_C(160) * JH_N3_TRACK_SIZE)
#define JH_N3_MAX_REQUEST (9u + JH_N3_RECORD_SIZE)
#define JH_N4_MAX_CONSOLE_BLOCK 32u
#define JH_SYSTEM_SIZE 0x1a00u
#define JH_SERVICE_MAX_REPLY 1063u
#define JH_SERVICE_CONSOLE_QUEUE 256u
#define JH_CAPTURE_HEADER_SIZE 16u
#define JH_CAPTURE_RECORD_OVERHEAD 16u
#define JH_JOURNAL_SIZE 276u
#define JH_BOOT_RECORD_SIZE 128u
#define JH_BOOT_MAX_FRAMES 16u
#define JH_BOOT_LOAD_ADDRESS 0x0100u
#define JH_BOOT_SYSTEM_LOAD_ADDRESS 0xb400u
#define JH_BOOT_SYSTEM_ENTRY 0xca00u
#define JH_BOOT_MAX_OUTPUT 1024u
#define JH_SHA256_SIZE 32u
#define JH_SHA256_HEX_SIZE 64u
#define JH_CONFIG_PATH_MAX 512u
#define JH_CONFIG_NAME_MAX 32u

enum jh_boot_format {
    JH_BOOT_PLAIN = 0,
    JH_BOOT_EXPLICIT = 1,
    JH_BOOT_JUKUSYS = 2,
    JH_BOOT_JUKU51 = 3,
    JH_BOOT_JUKURM1 = 4
};

enum jh_fast_state {
    JH_FAST_WAIT_READY = 0,
    JH_FAST_PROBE_STREAM = 1,
    JH_FAST_SEND_STREAM = 2,
    JH_FAST_WAIT_FINAL = 3,
    JH_FAST_COMPLETE = 4,
    JH_FAST_COMPLETE_UNCONFIRMED = 5,
    JH_FAST_FAILED = 6
};

enum jh_capture_type {
    JH_CAPTURE_RX = 1,
    JH_CAPTURE_TX = 2,
    JH_CAPTURE_EVENT = 3
};

enum jh_journal_state {
    JH_JOURNAL_EMPTY = 0,
    JH_JOURNAL_PREPARED = 1,
    JH_JOURNAL_APPLIED = 2,
    JH_JOURNAL_COMPLETE = 3
};

enum jh_session_phase {
    JH_SESSION_DISCOVERY = 0,
    JH_SESSION_STOCK_BOOT = 1,
    JH_SESSION_FASTBOOT = 2,
    JH_SESSION_NETDISK = 3,
    JH_SESSION_RECONNECT = 4,
    JH_SESSION_STOPPED = 5,
    JH_SESSION_FAILED = 6
};

enum jh_session_event {
    JH_SESSION_STOCK_REQUEST = 1,
    JH_SESSION_STOCK_COMPLETE = 2,
    JH_SESSION_FAST_READY = 3,
    JH_SESSION_FAST_COMPLETE = 4,
    JH_SESSION_FAST_UNCONFIRMED = 5,
    JH_SESSION_DISK_REQUEST = 6,
    JH_SESSION_SERIAL_LOST = 7,
    JH_SESSION_SERIAL_REOPENED = 8,
    JH_SESSION_TARGET_RESET = 9,
    JH_SESSION_STOP = 10,
    JH_SESSION_FATAL = 11
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

enum jh_config_media_mode {
    JH_CONFIG_MEDIA_READ_ONLY = 0,
    JH_CONFIG_MEDIA_DIRECT = 1,
    JH_CONFIG_MEDIA_SNAPSHOT = 2
};

struct jh_config_artifact {
    char file[JH_CONFIG_PATH_MAX];
    uint64_t size;
    uint8_t sha256[JH_SHA256_SIZE];
};

struct jh_config_disk {
    char file[JH_CONFIG_PATH_MAX];
    char base[JH_CONFIG_PATH_MAX];
    char geometry[JH_CONFIG_NAME_MAX];
    uint64_t size;
    uint8_t sha256[JH_SHA256_SIZE];
    enum jh_config_media_mode mode;
    int present;
};

struct jh_host_config {
    char port[JH_CONFIG_PATH_MAX];
    char log[JH_CONFIG_PATH_MAX];
    char capture[JH_CONFIG_PATH_MAX];
    char console[JH_CONFIG_PATH_MAX];
    struct jh_config_artifact system;
    struct jh_config_artifact fastboot;
    struct jh_config_artifact fallback_system;
    struct jh_config_artifact fallback_fastboot;
    struct jh_config_disk disk_a;
    struct jh_config_disk disk_b;
    uint32_t timeout_seconds;
    uint32_t disk_timeout_seconds;
    uint32_t boot_restarts;
    uint32_t reconnect_timeout_seconds;
    uint32_t disk_protocol;
    uint32_t disk_baud;
    uint32_t read_ahead;
    uint32_t reply_guard_ms;
    int network_rom;
    int have_fastboot;
    int have_fallback;
};

struct jh_config_error {
    size_t line;
    const char *message;
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

struct jh_capture_record {
    enum jh_capture_type type;
    uint8_t flags;
    uint64_t milliseconds;
    const uint8_t *payload;
    size_t payload_length;
};

struct jh_media_transaction {
    enum jh_journal_state state;
    uint32_t sequence;
    uint32_t offset;
    uint8_t before[JH_N3_RECORD_SIZE];
    uint8_t after[JH_N3_RECORD_SIZE];
};

struct jh_session {
    enum jh_session_phase phase;
    int direct_fastboot;
    int fastboot_enabled;
    int fastboot_unconfirmed;
    unsigned boot_count;
    unsigned reconnect_count;
    unsigned reset_count;
};

struct jh_n3_parser {
    uint8_t bytes[JH_N3_MAX_REQUEST];
    size_t length;
    size_t expected;
};

struct jh_media {
    uint8_t *bytes;
    void *context;
    int (*read_offset)(void *context, uint32_t offset,
                       uint8_t record[JH_N3_RECORD_SIZE]);
    int (*write_offset)(void *context, uint32_t offset,
                        const uint8_t record[JH_N3_RECORD_SIZE]);
    uint32_t size;
    unsigned tracks;
    int writable;
};

struct jh_sha256_state {
    uint32_t state[8];
    uint64_t bits;
    uint8_t block[64];
    size_t used;
};

struct jh_boot_image {
    size_t length;
    uint16_t load_address;
    uint16_t entry;
    enum jh_boot_format format;
};

enum jh_boot_event_kind {
    JH_BOOT_EVENT_NONE = 0,
    JH_BOOT_EVENT_REQUEST = 1,
    JH_BOOT_EVENT_PROGRESS = 2,
    JH_BOOT_EVENT_COMPLETE = 3,
    JH_BOOT_EVENT_IGNORED = 4,
    JH_BOOT_EVENT_RETRY = 5
};

struct jh_boot_output {
    uint8_t bytes[JH_BOOT_MAX_OUTPUT];
    size_t length;
    unsigned frame_count;
    size_t frame_lengths[JH_BOOT_MAX_FRAMES];
    enum jh_boot_event_kind event;
    size_t completed_records;
};

struct jh_boot_session {
    const uint8_t *image;
    size_t image_length;
    uint16_t load_address;
    uint16_t entry;
    uint8_t required_client;
    uint8_t required_server;
    uint8_t client;
    uint8_t server;
    int compact_execute;
    int request_seen;
    int start_pending;
    int advance_pending;
    int completion_pending;
    int awaiting_ack;
    int complete;
    size_t next_message;
    unsigned ack_count;
    unsigned reject_count;
    unsigned sent_frames;
};

struct jh_fast_parser {
    uint8_t bytes[5];
    size_t length;
};

struct jh_fast_session {
    const uint8_t *compressed;
    size_t compressed_length;
    uint16_t compressed_crc;
    uint16_t system_crc;
    enum jh_fast_state state;
    unsigned header_probes;
    unsigned header_acks;
    int ready_seen;
};

struct jh_fast_v15_session {
    const uint8_t *core;
    const uint8_t *extension;
    const uint8_t *compressed;
    size_t extension_length;
    size_t compressed_length;
    uint16_t compressed_crc;
    uint16_t system_crc;
    uint8_t extension_sum1;
    uint8_t extension_sum2;
};

uint8_t jh_xor(const uint8_t *data, size_t length);
uint16_t jh_crc16_ccitt(const uint8_t *data, size_t length, uint16_t initial);
uint16_t jh_crc16_ibm(const uint8_t *data, size_t length, uint16_t initial);
uint32_t jh_crc32(const uint8_t *data, size_t length, uint32_t initial);
void jh_sha256(const uint8_t *data, size_t length,
               uint8_t output[JH_SHA256_SIZE]);
void jh_sha256_init(struct jh_sha256_state *state);
void jh_sha256_update(struct jh_sha256_state *state,
                      const uint8_t *data, size_t length);
void jh_sha256_final(struct jh_sha256_state *state,
                     uint8_t output[JH_SHA256_SIZE]);
int jh_sha256_parse(const char *text, uint8_t output[JH_SHA256_SIZE]);
void jh_sha256_format(const uint8_t digest[JH_SHA256_SIZE],
                      char output[JH_SHA256_HEX_SIZE + 1u]);
int jh_config_parse(const char *text, size_t length,
                    struct jh_host_config *config,
                    struct jh_config_error *error);
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
int jh_fast_v15_session_init(struct jh_fast_v15_session *session,
                             const uint8_t *artifact, size_t artifact_length,
                             const uint8_t *system, size_t system_length);
size_t jh_fast_v15_extension_tail_size(
    const struct jh_fast_v15_session *session);
int jh_fast_v15_extension_tail(const struct jh_fast_v15_session *session,
                               uint8_t *output, size_t capacity,
                               size_t *output_length);
void jh_fast_parser_init(struct jh_fast_parser *parser);
int jh_fast_parser_push(struct jh_fast_parser *parser, uint8_t value,
                        uint8_t *kind, uint8_t *first, uint8_t *second);
int jh_fast_session_init(struct jh_fast_session *session,
                         const uint8_t *artifact, size_t artifact_length,
                         const uint8_t *system, size_t system_length);
int jh_fast_session_ready(struct jh_fast_session *session,
                          uint8_t kind, uint8_t version, uint8_t rate_flag);
int jh_fast_session_ready_timeout(struct jh_fast_session *session);
int jh_fast_session_probe(struct jh_fast_session *session,
                          uint8_t output[3], size_t *output_length);
int jh_fast_session_header_ack(struct jh_fast_session *session, uint8_t value);
size_t jh_fast_session_tail_size(const struct jh_fast_session *session);
int jh_fast_session_tail(struct jh_fast_session *session,
                         uint8_t *output, size_t capacity,
                         size_t *output_length);
int jh_fast_session_final(struct jh_fast_session *session,
                          uint8_t kind, uint8_t sequence, uint8_t status);
int jh_fast_session_final_timeout(struct jh_fast_session *session);

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
int jh_boot_session_init(struct jh_boot_session *session,
                         const uint8_t *image, size_t image_length,
                         uint16_t load_address, uint16_t entry,
                         uint8_t required_client, uint8_t required_server,
                         int compact_execute);
int jh_boot_session_input(struct jh_boot_session *session,
                          const struct jh_janet_frame *incoming,
                          struct jh_boot_output *output);

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
                        uint32_t *offset);
const uint8_t *jh_n3_sector_order(void);

int jh_media_init(struct jh_media *media, uint8_t *bytes, uint32_t size,
                  unsigned tracks, int writable);
int jh_media_init_backend(struct jh_media *media, void *context,
                          uint32_t size, unsigned tracks, int writable,
                          int (*read_offset)(void *, uint32_t, uint8_t *),
                          int (*write_offset)(void *, uint32_t,
                                              const uint8_t *));
int jh_media_read_offset(const struct jh_media *media, uint32_t offset,
                         uint8_t record[JH_N3_RECORD_SIZE]);
int jh_media_write_offset(struct jh_media *media, uint32_t offset,
                          const uint8_t record[JH_N3_RECORD_SIZE]);
int jh_media_read(const struct jh_media *media, unsigned track,
                  unsigned sector, uint8_t record[JH_N3_RECORD_SIZE]);
int jh_media_write(struct jh_media *media, unsigned track, unsigned sector,
                   const uint8_t record[JH_N3_RECORD_SIZE]);
int jh_native_image_to_volume(const uint8_t *image, uint32_t image_length,
                              uint8_t *volume, uint32_t volume_capacity);

int jh_service_init(struct jh_service *service, struct jh_media *drive_a,
                    struct jh_media *drive_b, unsigned protocol_version,
                    unsigned read_ahead_records, int console_enabled);
int jh_service_console_input(struct jh_service *service,
                             const uint8_t *data, size_t length);
int jh_service_is_duplicate(const struct jh_service *service,
                            const struct jh_n3_request *request);
int jh_service_handle(struct jh_service *service,
                      const struct jh_n3_request *request,
                      const uint8_t clock_value[5],
                      struct jh_service_event *event);

int jh_capture_header(uint64_t started_milliseconds, uint8_t flags,
                      uint8_t output[JH_CAPTURE_HEADER_SIZE]);
int jh_capture_header_decode(const uint8_t *input, size_t length,
                             uint64_t *started_milliseconds, uint8_t *flags);
int jh_capture_encode(enum jh_capture_type type, uint8_t flags,
                      uint64_t milliseconds, const uint8_t *payload,
                      size_t payload_length, uint8_t *output, size_t capacity,
                      size_t *output_length);
int jh_capture_decode(const uint8_t *input, size_t length,
                      struct jh_capture_record *record,
                      size_t *consumed);

int jh_media_transaction_prepare(struct jh_media_transaction *transaction,
                                 const struct jh_media *media,
                                 unsigned track, unsigned sector,
                                 const uint8_t after[JH_N3_RECORD_SIZE],
                                 uint32_t sequence);
int jh_media_transaction_apply(struct jh_media_transaction *transaction,
                               struct jh_media *media);
int jh_media_transaction_commit(struct jh_media_transaction *transaction);
int jh_media_transaction_recover(struct jh_media_transaction *transaction,
                                 struct jh_media *media);
int jh_journal_encode(const struct jh_media_transaction *transaction,
                      uint8_t output[JH_JOURNAL_SIZE]);
int jh_journal_decode(const uint8_t *input, size_t length,
                      struct jh_media_transaction *transaction);

int jh_session_init(struct jh_session *session, int direct_fastboot,
                    int fastboot_enabled);
int jh_session_advance(struct jh_session *session,
                       enum jh_session_event event);
const char *jh_session_phase_name(enum jh_session_phase phase);
const char *jh_result_name(int result);

#ifdef __cplusplus
}
#endif

#endif
