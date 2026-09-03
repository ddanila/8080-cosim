#include "jukuwin_config.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum section {
    SECTION_NONE = 0,
    SECTION_JUKU,
    SECTION_DRIVE_A,
    SECTION_DRIVE_B,
    SECTION_EVIDENCE
};

static int ascii_equal(const char *left, const char *right)
{
    while (*left != '\0' && *right != '\0') {
        unsigned char a = (unsigned char)*left++;
        unsigned char b = (unsigned char)*right++;
        if (a >= (unsigned char)'A' && a <= (unsigned char)'Z') {
            a = (unsigned char)(a - (unsigned char)'A' + (unsigned char)'a');
        }
        if (b >= (unsigned char)'A' && b <= (unsigned char)'Z') {
            b = (unsigned char)(b - (unsigned char)'A' + (unsigned char)'a');
        }
        if (a != b) return 0;
    }
    return *left == '\0' && *right == '\0';
}

static char *trim(char *text)
{
    char *end;
    while (*text == ' ' || *text == '\t') ++text;
    end = text + strlen(text);
    while (end != text && (end[-1] == ' ' || end[-1] == '\t')) --end;
    *end = '\0';
    return text;
}

static int set_error(struct jh_jukuwin_config_error *error, size_t line,
                     const char *message)
{
    if (error != NULL) {
        size_t length = strlen(message);
        if (length >= sizeof(error->message)) {
            length = sizeof(error->message) - 1u;
        }
        error->line = line;
        memcpy(error->message, message, length);
        error->message[length] = '\0';
    }
    return JH_ERR_FORMAT;
}

static int copy_value(char *target, size_t capacity, const char *value,
                      struct jh_jukuwin_config_error *error, size_t line)
{
    size_t length = strlen(value);
    if (length >= capacity) return set_error(error, line, "value is too long");
    memcpy(target, value, length + 1u);
    return JH_OK;
}

static int parse_boolean(const char *value, int *result)
{
    if (ascii_equal(value, "yes")) *result = 1;
    else if (ascii_equal(value, "no")) *result = 0;
    else return JH_ERR_FORMAT;
    return JH_OK;
}

void jh_jukuwin_config_init(struct jh_jukuwin_config *config)
{
    if (config == NULL) return;
    memset(config, 0, sizeof(*config));
    config->mode = JH_JUKUWIN_MODE_C11;
    memcpy(config->serial, "auto", 5u);
    config->auto_listen = 1;
    config->drive_a_mode = JH_JUKUWIN_DRIVE_A_SNAPSHOT;
    memcpy(config->evidence_directory, "logs", 5u);
    config->capture = 1;
    config->keep_sessions = 20u;
}

static int parse_section(const char *line, enum section *section)
{
    if (ascii_equal(line, "[juku]")) *section = SECTION_JUKU;
    else if (ascii_equal(line, "[drive_a]")) *section = SECTION_DRIVE_A;
    else if (ascii_equal(line, "[drive_b]")) *section = SECTION_DRIVE_B;
    else if (ascii_equal(line, "[evidence]")) *section = SECTION_EVIDENCE;
    else return JH_ERR_FORMAT;
    return JH_OK;
}

static int assign_value(struct jh_jukuwin_config *config,
                        enum section section, const char *key,
                        const char *value, uint32_t seen[5],
                        struct jh_jukuwin_config_error *error, size_t line)
{
    uint32_t bit = 0u;
    int result = JH_OK;
    switch (section) {
    case SECTION_JUKU:
        if (ascii_equal(key, "mode")) {
            bit = 1u;
            if (ascii_equal(value, "c11")) config->mode = JH_JUKUWIN_MODE_C11;
            else if (ascii_equal(value, "stock")) {
                config->mode = JH_JUKUWIN_MODE_STOCK;
            } else return set_error(error, line, "mode must be c11 or stock");
        } else if (ascii_equal(key, "serial")) {
            bit = 2u;
            result = copy_value(config->serial, sizeof(config->serial), value,
                                error, line);
        } else if (ascii_equal(key, "serial_id")) {
            bit = 4u;
            result = copy_value(config->serial_id, sizeof(config->serial_id),
                                value, error, line);
        } else if (ascii_equal(key, "auto_listen")) {
            bit = 8u;
            result = parse_boolean(value, &config->auto_listen);
            if (result != JH_OK) {
                return set_error(error, line, "auto_listen must be yes or no");
            }
        } else return set_error(error, line, "unknown key in [juku]");
        break;
    case SECTION_DRIVE_A:
        if (ascii_equal(key, "image")) {
            bit = 1u;
            result = copy_value(config->drive_a_image,
                sizeof(config->drive_a_image), value, error, line);
        } else if (ascii_equal(key, "mode")) {
            bit = 2u;
            if (ascii_equal(value, "snapshot")) {
                config->drive_a_mode = JH_JUKUWIN_DRIVE_A_SNAPSHOT;
            } else if (ascii_equal(value, "read-only")) {
                config->drive_a_mode = JH_JUKUWIN_DRIVE_A_READ_ONLY;
            } else {
                return set_error(error, line,
                                 "drive A mode must be snapshot or read-only");
            }
        } else if (ascii_equal(key, "working")) {
            bit = 4u;
            result = copy_value(config->drive_a_working,
                sizeof(config->drive_a_working), value, error, line);
        } else return set_error(error, line, "unknown key in [drive_a]");
        break;
    case SECTION_DRIVE_B:
        if (ascii_equal(key, "image")) {
            bit = 1u;
            result = copy_value(config->drive_b_image,
                sizeof(config->drive_b_image), value, error, line);
        } else return set_error(error, line, "unknown key in [drive_b]");
        break;
    case SECTION_EVIDENCE:
        if (ascii_equal(key, "directory")) {
            bit = 1u;
            result = copy_value(config->evidence_directory,
                sizeof(config->evidence_directory), value, error, line);
        } else if (ascii_equal(key, "capture")) {
            bit = 2u;
            result = parse_boolean(value, &config->capture);
            if (result != JH_OK) {
                return set_error(error, line, "capture must be yes or no");
            }
        } else if (ascii_equal(key, "verbose")) {
            bit = 4u;
            result = parse_boolean(value, &config->verbose);
            if (result != JH_OK) {
                return set_error(error, line, "verbose must be yes or no");
            }
        } else if (ascii_equal(key, "keep_sessions")) {
            char *end;
            unsigned long count;
            bit = 8u;
            count = strtoul(value, &end, 10);
            if (*value == '\0' || *end != '\0' || count > 10000u) {
                return set_error(error, line,
                                 "keep_sessions must be 0 through 10000");
            }
            config->keep_sessions = (uint32_t)count;
        } else return set_error(error, line, "unknown key in [evidence]");
        break;
    default:
        return set_error(error, line, "key appears before a section");
    }
    if (result != JH_OK) return result;
    if ((seen[(unsigned)section] & bit) != 0u) {
        return set_error(error, line, "duplicate key");
    }
    seen[(unsigned)section] |= bit;
    return JH_OK;
}

int jh_jukuwin_config_parse(const char *text, size_t length,
                            struct jh_jukuwin_config *config,
                            struct jh_jukuwin_config_error *error)
{
    struct jh_jukuwin_config parsed;
    enum section section = SECTION_NONE;
    uint32_t seen[5] = {0u, 0u, 0u, 0u, 0u};
    size_t position = 0u;
    size_t line_number = 0u;
    if (text == NULL || config == NULL) return JH_ERR_ARGUMENT;
    if (error != NULL) memset(error, 0, sizeof(*error));
    jh_jukuwin_config_init(&parsed);
    while (position < length) {
        char buffer[512];
        char *line;
        char *equals;
        size_t start = position;
        size_t line_length;
        ++line_number;
        while (position < length && text[position] != '\n') {
            unsigned char value = (unsigned char)text[position];
            if (value == 0u || value >= 128u) {
                return set_error(error, line_number,
                                 "configuration must be ASCII text");
            }
            ++position;
        }
        line_length = position - start;
        if (position < length) ++position;
        if (line_length != 0u && text[start + line_length - 1u] == '\r') {
            --line_length;
        }
        if (line_length >= sizeof(buffer)) {
            return set_error(error, line_number, "line is too long");
        }
        memcpy(buffer, text + start, line_length);
        buffer[line_length] = '\0';
        line = trim(buffer);
        if (*line == '\0' || *line == '#' || *line == ';') continue;
        if (*line == '[') {
            if (parse_section(line, &section) != JH_OK) {
                return set_error(error, line_number, "unknown section");
            }
            continue;
        }
        equals = strchr(line, '=');
        if (equals == NULL) {
            return set_error(error, line_number, "expected key=value");
        }
        *equals = '\0';
        if (*trim(line) == '\0') {
            return set_error(error, line_number, "key is empty");
        }
        if (assign_value(&parsed, section, trim(line), trim(equals + 1),
                         seen, error, line_number) != JH_OK) {
            return JH_ERR_FORMAT;
        }
    }
    *config = parsed;
    return JH_OK;
}

int jh_jukuwin_config_validate(const struct jh_jukuwin_config *config,
                               struct jh_jukuwin_config_error *error)
{
    const char *serial;
    char *end;
    unsigned long number;
    if (config == NULL) return JH_ERR_ARGUMENT;
    if (error != NULL) memset(error, 0, sizeof(*error));
    serial = config->serial;
    if (!ascii_equal(serial, "auto")) {
        if (!((serial[0] == 'C' || serial[0] == 'c') &&
              (serial[1] == 'O' || serial[1] == 'o') &&
              (serial[2] == 'M' || serial[2] == 'm'))) {
            return set_error(error, 0u, "serial must be auto or COM1..COM256");
        }
        number = strtoul(serial + 3, &end, 10);
        if (*serial == '\0' || *end != '\0' || number < 1u || number > 256u) {
            return set_error(error, 0u, "serial must be auto or COM1..COM256");
        }
    }
    if (config->drive_a_image[0] == '\0') {
        return set_error(error, 0u, "drive A image is required");
    }
    if (config->drive_a_mode == JH_JUKUWIN_DRIVE_A_SNAPSHOT &&
            config->drive_a_working[0] != '\0' &&
            ascii_equal(config->drive_a_image, config->drive_a_working)) {
        return set_error(error, 0u,
                         "snapshot working image must differ from its base");
    }
    if (config->evidence_directory[0] == '\0') {
        return set_error(error, 0u, "evidence directory is required");
    }
    return JH_OK;
}

int jh_jukuwin_config_format(const struct jh_jukuwin_config *config,
                             char *output, size_t capacity,
                             size_t *output_length)
{
    int written;
    const char *mode;
    const char *drive_mode;
    if (config == NULL || output == NULL || output_length == NULL) {
        return JH_ERR_ARGUMENT;
    }
    mode = config->mode == JH_JUKUWIN_MODE_STOCK ? "stock" : "c11";
    drive_mode = config->drive_a_mode == JH_JUKUWIN_DRIVE_A_READ_ONLY ?
        "read-only" : "snapshot";
    written = snprintf(output, capacity,
        "[juku]\n"
        "mode=%s\n"
        "serial=%s\n"
        "serial_id=%s\n"
        "auto_listen=%s\n\n"
        "[drive_a]\n"
        "image=%s\n"
        "mode=%s\n"
        "working=%s\n\n"
        "[drive_b]\n"
        "image=%s\n\n"
        "[evidence]\n"
        "directory=%s\n"
        "capture=%s\n"
        "verbose=%s\n"
        "keep_sessions=%lu\n",
        mode, config->serial, config->serial_id,
        config->auto_listen ? "yes" : "no", config->drive_a_image,
        drive_mode, config->drive_a_working, config->drive_b_image,
        config->evidence_directory, config->capture ? "yes" : "no",
        config->verbose ? "yes" : "no",
        (unsigned long)config->keep_sessions);
    if (written < 0 || (size_t)written >= capacity) return JH_ERR_SPACE;
    *output_length = (size_t)written;
    return JH_OK;
}

static int path_is_absolute(const char *path)
{
    return path[0] == '/' || path[0] == '\\' ||
        (path[0] != '\0' && path[1] == ':');
}

int jh_jukuwin_resolve_path(const char *config_path, const char *input,
                            char *output, size_t capacity)
{
    const char *slash;
    const char *backslash;
    const char *separator;
    size_t directory_length;
    size_t input_length;
    if (config_path == NULL || input == NULL || output == NULL) {
        return JH_ERR_ARGUMENT;
    }
    input_length = strlen(input);
    if (path_is_absolute(input)) {
        if (input_length >= capacity) return JH_ERR_SPACE;
        memcpy(output, input, input_length + 1u);
        return JH_OK;
    }
    slash = strrchr(config_path, '/');
    backslash = strrchr(config_path, '\\');
    separator = slash == NULL ? backslash : backslash == NULL ? slash :
        slash > backslash ? slash : backslash;
    if (separator == NULL) {
        if (input_length >= capacity) return JH_ERR_SPACE;
        memcpy(output, input, input_length + 1u);
        return JH_OK;
    }
    directory_length = (size_t)(separator - config_path);
    if (directory_length + 1u + input_length >= capacity) return JH_ERR_SPACE;
    memcpy(output, config_path, directory_length);
    output[directory_length] = '\\';
    memcpy(output + directory_length + 1u, input, input_length + 1u);
    return JH_OK;
}

int jh_jukuwin_default_working_path(const char *base, char *output,
                                    size_t capacity)
{
    const char *slash;
    const char *backslash;
    const char *dot;
    size_t stem_length;
    size_t suffix_length;
    static const char addition[] = "-WORK";
    if (base == NULL || output == NULL || base[0] == '\0') {
        return JH_ERR_ARGUMENT;
    }
    slash = strrchr(base, '/');
    backslash = strrchr(base, '\\');
    dot = strrchr(base, '.');
    if (dot == NULL || (slash != NULL && dot < slash) ||
            (backslash != NULL && dot < backslash)) {
        dot = base + strlen(base);
    }
    stem_length = (size_t)(dot - base);
    suffix_length = strlen(dot);
    if (stem_length + sizeof(addition) - 1u + suffix_length >= capacity) {
        return JH_ERR_SPACE;
    }
    memcpy(output, base, stem_length);
    memcpy(output + stem_length, addition, sizeof(addition) - 1u);
    memcpy(output + stem_length + sizeof(addition) - 1u, dot,
           suffix_length + 1u);
    return JH_OK;
}
