#include "jukuhost.h"

#include <limits.h>
#include <string.h>

enum config_section {
    SECTION_NONE = 0,
    SECTION_HOST,
    SECTION_NETWORK,
    SECTION_SYSTEM,
    SECTION_FASTBOOT,
    SECTION_FALLBACK_SYSTEM,
    SECTION_FALLBACK_FASTBOOT,
    SECTION_DISK_A,
    SECTION_DISK_B
};

struct parse_state {
    unsigned host;
    unsigned network;
    unsigned system;
    unsigned fastboot;
    unsigned fallback_system;
    unsigned fallback_fastboot;
    unsigned disk_a;
    unsigned disk_b;
};

static int ascii_lower(int character)
{
    return character >= 'A' && character <= 'Z' ? character + ('a' - 'A') :
        character;
}

static int text_equal(const char *left, const char *right)
{
    while (*left != '\0' && *right != '\0') {
        if (ascii_lower((unsigned char)*left) !=
                ascii_lower((unsigned char)*right)) return 0;
        ++left;
        ++right;
    }
    return *left == *right;
}

static char *trim(char *text)
{
    char *end;
    while (*text == ' ' || *text == '\t') ++text;
    end = text + strlen(text);
    while (end != text && (end[-1] == ' ' || end[-1] == '\t' ||
                           end[-1] == '\r')) --end;
    *end = '\0';
    return text;
}

static int fail(struct jh_config_error *error, size_t line,
                const char *message, int result)
{
    if (error != NULL) {
        error->line = line;
        error->message = message;
    }
    return result;
}

static int copy_text(char *destination, size_t capacity, const char *value)
{
    size_t length = strlen(value);
    if (length == 0u || length >= capacity) return JH_ERR_RANGE;
    memcpy(destination, value, length + 1u);
    return JH_OK;
}

static int set_once(unsigned *seen, unsigned bit)
{
    if ((*seen & bit) != 0u) return JH_ERR_FORMAT;
    *seen |= bit;
    return JH_OK;
}

static int parse_uint64(const char *text, uint64_t minimum, uint64_t maximum,
                        uint64_t *result)
{
    uint64_t value = 0u;
    const char *cursor = text;
    if (*cursor == '\0') return JH_ERR_FORMAT;
    while (*cursor != '\0') {
        unsigned digit;
        if (*cursor < '0' || *cursor > '9') return JH_ERR_FORMAT;
        digit = (unsigned)(*cursor - '0');
        if (value > (UINT64_MAX - digit) / 10u) return JH_ERR_RANGE;
        value = value * 10u + digit;
        ++cursor;
    }
    if (value < minimum || value > maximum) return JH_ERR_RANGE;
    *result = value;
    return JH_OK;
}

static int parse_unsigned_value(const char *text, uint32_t minimum,
                                uint32_t maximum, uint32_t *result)
{
    uint64_t value;
    int parsed = parse_uint64(text, minimum, maximum, &value);
    if (parsed != JH_OK) return parsed;
    *result = (uint32_t)value;
    return JH_OK;
}

static int parse_bool(const char *text, int *result)
{
    if (text_equal(text, "yes") || text_equal(text, "true") ||
            strcmp(text, "1") == 0) {
        *result = 1;
        return JH_OK;
    }
    if (text_equal(text, "no") || text_equal(text, "false") ||
            strcmp(text, "0") == 0) {
        *result = 0;
        return JH_OK;
    }
    return JH_ERR_FORMAT;
}

static enum config_section parse_section(const char *name)
{
    if (text_equal(name, "host")) return SECTION_HOST;
    if (text_equal(name, "network")) return SECTION_NETWORK;
    if (text_equal(name, "system")) return SECTION_SYSTEM;
    if (text_equal(name, "fastboot")) return SECTION_FASTBOOT;
    if (text_equal(name, "fallback_system")) return SECTION_FALLBACK_SYSTEM;
    if (text_equal(name, "fallback_fastboot")) return SECTION_FALLBACK_FASTBOOT;
    if (text_equal(name, "disk_a")) return SECTION_DISK_A;
    if (text_equal(name, "disk_b")) return SECTION_DISK_B;
    return SECTION_NONE;
}

static int parse_artifact(struct jh_config_artifact *artifact, unsigned *seen,
                          const char *key, const char *value)
{
    if (text_equal(key, "file")) {
        if (set_once(seen, 1u) != JH_OK) return JH_ERR_FORMAT;
        return copy_text(artifact->file, sizeof(artifact->file), value);
    }
    if (text_equal(key, "size")) {
        if (set_once(seen, 2u) != JH_OK) return JH_ERR_FORMAT;
        return parse_uint64(value, 1u, UINT32_MAX, &artifact->size);
    }
    if (text_equal(key, "sha256")) {
        if (set_once(seen, 4u) != JH_OK) return JH_ERR_FORMAT;
        return jh_sha256_parse(value, artifact->sha256);
    }
    return JH_ERR_UNSUPPORTED;
}

static int parse_media_mode(const char *value,
                            enum jh_config_media_mode *mode)
{
    if (text_equal(value, "read-only") || text_equal(value, "readonly")) {
        *mode = JH_CONFIG_MEDIA_READ_ONLY;
        return JH_OK;
    }
    if (text_equal(value, "direct")) {
        *mode = JH_CONFIG_MEDIA_DIRECT;
        return JH_OK;
    }
    if (text_equal(value, "snapshot")) {
        *mode = JH_CONFIG_MEDIA_SNAPSHOT;
        return JH_OK;
    }
    return JH_ERR_FORMAT;
}

static int parse_disk(struct jh_config_disk *disk, unsigned *seen,
                      const char *key, const char *value)
{
    if (text_equal(key, "file")) {
        if (set_once(seen, 1u) != JH_OK) return JH_ERR_FORMAT;
        return copy_text(disk->file, sizeof(disk->file), value);
    }
    if (text_equal(key, "base")) {
        if (set_once(seen, 2u) != JH_OK) return JH_ERR_FORMAT;
        return copy_text(disk->base, sizeof(disk->base), value);
    }
    if (text_equal(key, "size")) {
        if (set_once(seen, 4u) != JH_OK) return JH_ERR_FORMAT;
        return parse_uint64(value, 1u, UINT32_MAX, &disk->size);
    }
    if (text_equal(key, "sha256")) {
        if (set_once(seen, 8u) != JH_OK) return JH_ERR_FORMAT;
        return jh_sha256_parse(value, disk->sha256);
    }
    if (text_equal(key, "geometry")) {
        if (set_once(seen, 16u) != JH_OK) return JH_ERR_FORMAT;
        return copy_text(disk->geometry, sizeof(disk->geometry), value);
    }
    if (text_equal(key, "mode")) {
        if (set_once(seen, 32u) != JH_OK) return JH_ERR_FORMAT;
        return parse_media_mode(value, &disk->mode);
    }
    if (text_equal(key, "writable")) {
        int writable;
        int result;
        if (set_once(seen, 32u) != JH_OK) return JH_ERR_FORMAT;
        result = parse_bool(value, &writable);
        if (result == JH_OK) {
            disk->mode = writable ? JH_CONFIG_MEDIA_DIRECT :
                JH_CONFIG_MEDIA_READ_ONLY;
        }
        return result;
    }
    return JH_ERR_UNSUPPORTED;
}

static int parse_host(struct jh_host_config *config, unsigned *seen,
                      const char *key, const char *value)
{
    if (text_equal(key, "port")) {
        if (set_once(seen, 1u) != JH_OK) return JH_ERR_FORMAT;
        return copy_text(config->port, sizeof(config->port), value);
    }
    if (text_equal(key, "log")) {
        if (set_once(seen, 2u) != JH_OK) return JH_ERR_FORMAT;
        return copy_text(config->log, sizeof(config->log), value);
    }
    if (text_equal(key, "capture")) {
        if (set_once(seen, 4u) != JH_OK) return JH_ERR_FORMAT;
        return copy_text(config->capture, sizeof(config->capture), value);
    }
    if (text_equal(key, "console")) {
        if (set_once(seen, 8u) != JH_OK) return JH_ERR_FORMAT;
        return copy_text(config->console, sizeof(config->console), value);
    }
    if (text_equal(key, "network_rom")) {
        if (set_once(seen, 16u) != JH_OK) return JH_ERR_FORMAT;
        return parse_bool(value, &config->network_rom);
    }
    if (text_equal(key, "timeout")) {
        if (set_once(seen, 32u) != JH_OK) return JH_ERR_FORMAT;
        return parse_unsigned_value(value, 1u, 86400u,
                                    &config->timeout_seconds);
    }
    if (text_equal(key, "disk_timeout")) {
        if (set_once(seen, 64u) != JH_OK) return JH_ERR_FORMAT;
        return parse_unsigned_value(value, 0u, 86400u,
                                    &config->disk_timeout_seconds);
    }
    if (text_equal(key, "boot_restarts")) {
        if (set_once(seen, 128u) != JH_OK) return JH_ERR_FORMAT;
        return parse_unsigned_value(value, 0u, 100u,
                                    &config->boot_restarts);
    }
    if (text_equal(key, "reconnect_timeout")) {
        if (set_once(seen, 256u) != JH_OK) return JH_ERR_FORMAT;
        return parse_unsigned_value(value, 0u, 86400u,
                                    &config->reconnect_timeout_seconds);
    }
    return JH_ERR_UNSUPPORTED;
}

static int parse_network(struct jh_host_config *config, unsigned *seen,
                         const char *key, const char *value)
{
    if (text_equal(key, "protocol")) {
        if (set_once(seen, 1u) != JH_OK) return JH_ERR_FORMAT;
        return parse_unsigned_value(value, 1u, 3u, &config->disk_protocol);
    }
    if (text_equal(key, "baud")) {
        if (set_once(seen, 2u) != JH_OK) return JH_ERR_FORMAT;
        return parse_unsigned_value(value, 300u, 115200u, &config->disk_baud);
    }
    if (text_equal(key, "read_ahead")) {
        if (set_once(seen, 4u) != JH_OK) return JH_ERR_FORMAT;
        return parse_unsigned_value(value, 1u, 8u, &config->read_ahead);
    }
    if (text_equal(key, "reply_guard_ms")) {
        if (set_once(seen, 8u) != JH_OK) return JH_ERR_FORMAT;
        return parse_unsigned_value(value, 0u, 1000u,
                                    &config->reply_guard_ms);
    }
    return JH_ERR_UNSUPPORTED;
}

static int parse_key(struct jh_host_config *config, struct parse_state *state,
                     enum config_section section, const char *key,
                     const char *value)
{
    switch (section) {
    case SECTION_HOST:
        return parse_host(config, &state->host, key, value);
    case SECTION_NETWORK:
        return parse_network(config, &state->network, key, value);
    case SECTION_SYSTEM:
        return parse_artifact(&config->system, &state->system, key, value);
    case SECTION_FASTBOOT:
        return parse_artifact(&config->fastboot, &state->fastboot, key, value);
    case SECTION_FALLBACK_SYSTEM:
        return parse_artifact(&config->fallback_system,
                              &state->fallback_system, key, value);
    case SECTION_FALLBACK_FASTBOOT:
        return parse_artifact(&config->fallback_fastboot,
                              &state->fallback_fastboot, key, value);
    case SECTION_DISK_A:
        return parse_disk(&config->disk_a, &state->disk_a, key, value);
    case SECTION_DISK_B:
        return parse_disk(&config->disk_b, &state->disk_b, key, value);
    default:
        return JH_ERR_FORMAT;
    }
}

static int validate(struct jh_host_config *config,
                    const struct parse_state *state)
{
    if ((state->host & 1u) == 0u || state->system != 7u ||
            (state->disk_a & (1u | 4u | 8u | 16u | 32u)) !=
                (1u | 4u | 8u | 16u | 32u)) {
        return JH_ERR_FORMAT;
    }
    if (state->fastboot != 0u && state->fastboot != 7u) return JH_ERR_FORMAT;
    config->have_fastboot = state->fastboot == 7u;
    if (config->network_rom && !config->have_fastboot) return JH_ERR_FORMAT;
    if ((state->fallback_system == 0u) !=
            (state->fallback_fastboot == 0u) ||
            (state->fallback_system != 0u &&
             (state->fallback_system != 7u || state->fallback_fastboot != 7u))) {
        return JH_ERR_FORMAT;
    }
    config->have_fallback = state->fallback_system == 7u;
    config->disk_a.present = 1;
    if (config->disk_a.mode == JH_CONFIG_MEDIA_SNAPSHOT) {
        if ((state->disk_a & 2u) == 0u) return JH_ERR_FORMAT;
    } else if ((state->disk_a & 2u) != 0u) return JH_ERR_FORMAT;
    if (state->disk_b != 0u) {
        if (state->disk_b != (1u | 4u | 8u | 16u | 32u) ||
                config->disk_b.mode != JH_CONFIG_MEDIA_READ_ONLY) {
            return JH_ERR_FORMAT;
        }
        config->disk_b.present = 1;
    }
    if (!text_equal(config->disk_a.geometry, "juku-cpm3") ||
            (config->disk_b.present &&
             !text_equal(config->disk_b.geometry, "juku-native"))) {
        return JH_ERR_UNSUPPORTED;
    }
    if (config->console[0] != '\0' && config->disk_protocol != 3u) {
        return JH_ERR_FORMAT;
    }
    return JH_OK;
}

int jh_config_parse(const char *text, size_t length,
                    struct jh_host_config *config,
                    struct jh_config_error *error)
{
    char line[JH_CONFIG_PATH_MAX];
    struct parse_state state;
    enum config_section section = SECTION_NONE;
    size_t position = 0u;
    size_t line_number = 0u;
    if (text == NULL || config == NULL) return JH_ERR_ARGUMENT;
    memset(config, 0, sizeof(*config));
    memset(&state, 0, sizeof(state));
    config->timeout_seconds = 120u;
    config->boot_restarts = 3u;
    config->reconnect_timeout_seconds = 30u;
    config->disk_protocol = 3u;
    config->disk_baud = 19200u;
    config->read_ahead = 3u;
    config->reply_guard_ms = 2u;
    while (position < length) {
        size_t start = position;
        size_t line_length;
        char *content;
        char *separator;
        int parsed;
        while (position < length && text[position] != '\n') {
            if (text[position] == '\0') {
                return fail(error, line_number + 1u,
                            "NUL byte in configuration", JH_ERR_FORMAT);
            }
            ++position;
        }
        line_length = position - start;
        if (position < length) ++position;
        ++line_number;
        if (line_length >= sizeof(line)) {
            return fail(error, line_number, "configuration line too long",
                        JH_ERR_RANGE);
        }
        memcpy(line, text + start, line_length);
        line[line_length] = '\0';
        content = trim(line);
        if (*content == '\0' || *content == '#' || *content == ';') continue;
        if (*content == '[') {
            size_t content_length = strlen(content);
            if (content_length < 3u || content[content_length - 1u] != ']') {
                return fail(error, line_number, "malformed section",
                            JH_ERR_FORMAT);
            }
            content[content_length - 1u] = '\0';
            section = parse_section(trim(content + 1u));
            if (section == SECTION_NONE) {
                return fail(error, line_number, "unknown section",
                            JH_ERR_UNSUPPORTED);
            }
            continue;
        }
        separator = strchr(content, '=');
        if (separator == NULL) {
            return fail(error, line_number, "missing equals sign",
                        JH_ERR_FORMAT);
        }
        *separator = '\0';
        content = trim(content);
        separator = trim(separator + 1u);
        if (*content == '\0' || *separator == '\0') {
            return fail(error, line_number, "empty key or value",
                        JH_ERR_FORMAT);
        }
        parsed = parse_key(config, &state, section, content, separator);
        if (parsed != JH_OK) {
            return fail(error, line_number,
                parsed == JH_ERR_UNSUPPORTED ? "unknown key" :
                parsed == JH_ERR_RANGE ? "value out of range" :
                "invalid or duplicate value", parsed);
        }
    }
    if (line_number == 0u) return fail(error, 0u, "empty configuration",
                                       JH_ERR_FORMAT);
    {
        int result = validate(config, &state);
        if (result != JH_OK) {
            return fail(error, line_number, "missing or inconsistent fields",
                        result);
        }
    }
    if (error != NULL) {
        error->line = 0u;
        error->message = NULL;
    }
    return JH_OK;
}
