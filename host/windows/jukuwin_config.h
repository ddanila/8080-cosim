#ifndef JUKUWIN_CONFIG_H
#define JUKUWIN_CONFIG_H

#include <stddef.h>
#include <stdint.h>

#include "jukuhost.h"

#define JH_JUKUWIN_SERIAL_MAX 16u
#define JH_JUKUWIN_SERIAL_ID_MAX 256u

enum jh_jukuwin_mode {
    JH_JUKUWIN_MODE_C11 = 0,
    JH_JUKUWIN_MODE_STOCK = 1
};

enum jh_jukuwin_drive_a_mode {
    JH_JUKUWIN_DRIVE_A_SNAPSHOT = 0,
    JH_JUKUWIN_DRIVE_A_READ_ONLY = 1
};

struct jh_jukuwin_config {
    enum jh_jukuwin_mode mode;
    char serial[JH_JUKUWIN_SERIAL_MAX];
    char serial_id[JH_JUKUWIN_SERIAL_ID_MAX];
    int auto_listen;
    char drive_a_image[JH_CONFIG_PATH_MAX];
    enum jh_jukuwin_drive_a_mode drive_a_mode;
    char drive_a_working[JH_CONFIG_PATH_MAX];
    char drive_b_image[JH_CONFIG_PATH_MAX];
    char evidence_directory[JH_CONFIG_PATH_MAX];
    int capture;
    int verbose;
    uint32_t keep_sessions;
};

struct jh_jukuwin_config_error {
    size_t line;
    char message[128];
};

void jh_jukuwin_config_init(struct jh_jukuwin_config *config);
int jh_jukuwin_config_parse(const char *text, size_t length,
                            struct jh_jukuwin_config *config,
                            struct jh_jukuwin_config_error *error);
int jh_jukuwin_config_format(const struct jh_jukuwin_config *config,
                             char *output, size_t capacity,
                             size_t *output_length);
int jh_jukuwin_config_validate(const struct jh_jukuwin_config *config,
                               struct jh_jukuwin_config_error *error);
int jh_jukuwin_resolve_path(const char *config_path, const char *input,
                            char *output, size_t capacity);
int jh_jukuwin_default_working_path(const char *base, char *output,
                                    size_t capacity);

#endif
